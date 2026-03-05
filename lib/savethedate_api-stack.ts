import * as path from "path";
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigw from "aws-cdk-lib/aws-apigateway";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";

export class SavethedateApiStack extends cdk.Stack {
	constructor(scope: Construct, id: string, props?: cdk.StackProps) {
		super(scope, id, props);


		// ------------------------------------------------------------------ //
		//  1. Cognito User Pool                                                //
		// ------------------------------------------------------------------ //
		const userPool = new cognito.UserPool(this, "UserPool", {
			userPoolName: "my-app-user-pool",
			selfSignUpEnabled: true,
			signInAliases: { email: true, username: true },
			autoVerify: { email: true },
			passwordPolicy: {
				minLength: 8,
				requireUppercase: true,
				requireLowercase: true,
				requireDigits: true,
				requireSymbols: false,
			},
			accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
			removalPolicy: cdk.RemovalPolicy.DESTROY, // change to RETAIN in prod
		});

		const userPoolClient = userPool.addClient("AppClient", {
			userPoolClientName: "my-app-client",
			generateSecret: false,
			authFlows: {
				userPassword: true,   // USER_PASSWORD_AUTH
				userSrp: true,        // USER_SRP_AUTH
			},
			accessTokenValidity: cdk.Duration.hours(24),
			idTokenValidity: cdk.Duration.hours(1),
			refreshTokenValidity: cdk.Duration.days(30),
		});

		// ------------------------------------------------------------------ //
		//  2. Cognito Groups                                                   //
		// ------------------------------------------------------------------ //
		new cognito.CfnUserPoolGroup(this, "AdminGroup", {
			userPoolId: userPool.userPoolId,
			groupName: "admin",
			description: "Administrator users",
		});

		new cognito.CfnUserPoolGroup(this, "UsersGroup", {
			userPoolId: userPool.userPoolId,
			groupName: "users",
			description: "Regular users",
		});

		// ------------------------------------------------------------------ //
		//  3. Shared Lambda environment variables                              //
		// ------------------------------------------------------------------ //
		const commonEnv: Record<string, string> = {
			USER_POOL_ID: userPool.userPoolId,
			CLIENT_ID: userPoolClient.userPoolClientId,
			REGION: this.region,
		};

		// ------------------------------------------------------------------ //
		//  4. Lambda Layer                                                     //
		// ------------------------------------------------------------------ //
		const requirementsLayer = new lambda.LayerVersion(this, "RequirementsLayer", {
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas"), {
				bundling: {
					image: lambda.Runtime.PYTHON_3_12.bundlingImage,
					command: [
						"bash", "-c",
						"pip install -r requirements.txt -t /asset-output/python --platform manylinux2014_x86_64 --only-binary=:all:"
					],
				},
			}),
			compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
		});

		// ------------------------------------------------------------------ //
		//  5. Lambda Functions                                                 //
		// ------------------------------------------------------------------ //
		const pythonRuntime = lambda.Runtime.PYTHON_3_12;
		const defaultLambdaProps = {
			runtime: pythonRuntime,
			handler: "index.handler",
			timeout: cdk.Duration.seconds(15),
			logRetention: logs.RetentionDays.ONE_WEEK,
			environment: commonEnv,
			layers: [requirementsLayer],
		};

		// --- Login Lambda (public — no auth) --------------------------------
		const loginFn = new lambda.Function(this, "LoginFunction", {
			...defaultLambdaProps,
			functionName: "cognito-login",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas/login")),
		});

		loginFn.addToRolePolicy(
			new iam.PolicyStatement({
				actions: ["cognito-idp:InitiateAuth"],
				resources: [userPool.userPoolArn],
			})
		);

		// --- Lambda Authorizer ----------------------------------------------
		const authorizerFn = new lambda.Function(this, "AuthorizerFunction", {
			...defaultLambdaProps,
			functionName: "cognito-authorizer",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas/authorizer")),
			timeout: cdk.Duration.seconds(10),
		});

		authorizerFn.addToRolePolicy(
			new iam.PolicyStatement({
				actions: [
					"cognito-idp:GetUser",
					"cognito-idp:AdminListGroupsForUser",
				],
				resources: [userPool.userPoolArn],
			})
		);

		// --- Public endpoint Lambda (any authenticated user) ----------------
		const publicFn = new lambda.Function(this, "PublicFunction", {
			...defaultLambdaProps,
			functionName: "cognito-public-endpoint",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas/public_endpoint")),
		});

		// --- Admin endpoint Lambda (admin group only) -----------------------
		const adminFn = new lambda.Function(this, "AdminFunction", {
			...defaultLambdaProps,
			functionName: "cognito-admin-endpoint",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas/admin_endpoint")),
		});

		adminFn.addToRolePolicy(
			new iam.PolicyStatement({
				actions: ["cognito-idp:ListUsers"],
				resources: [userPool.userPoolArn],
			})
		);

		// --- Change Password Lambda (first-time users) ----------------------
		const changePasswordFn = new lambda.Function(this, "ChangePasswordFunction", {
			...defaultLambdaProps,
			functionName: "cognito-change-password",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas/change_password")),
		});

		changePasswordFn.addToRolePolicy(
			new iam.PolicyStatement({
				actions: ["cognito-idp:RespondToAuthChallenge"],
				resources: [userPool.userPoolArn],
			})
		);

		// ------------------------------------------------------------------ //
		//  6. API Gateway                                                      //
		// ------------------------------------------------------------------ //
		const api = new apigw.RestApi(this, "Api", {
			restApiName: "my-app-api",
			description: "API protected by Cognito JWT",
			defaultCorsPreflightOptions: {
				allowOrigins: apigw.Cors.ALL_ORIGINS,
				allowMethods: apigw.Cors.ALL_METHODS,
				allowHeaders: ["Content-Type", "Authorization"],
			},
			deployOptions: {
				stageName: "v1",
			},
		});

		// Lambda token authorizer — caches policy for 5 minutes
		const tokenAuthorizer = new apigw.TokenAuthorizer(this, "TokenAuthorizer", {
			handler: authorizerFn,
			identitySource: "method.request.header.Authorization",
			resultsCacheTtl: cdk.Duration.minutes(5),
		});

		const authorizedMethodOptions: apigw.MethodOptions = {
			authorizationType: apigw.AuthorizationType.CUSTOM,
			authorizer: tokenAuthorizer,
		};

		// ---- /auth/login  (public, no authorizer) --------------------------
		const authResource = api.root.addResource("auth");
		authResource
			.addResource("login")
			.addMethod("POST", new apigw.LambdaIntegration(loginFn), {
				authorizationType: apigw.AuthorizationType.NONE,
			});

		// ---- /auth/change-password  (first-time password setup) ------------
		authResource
			.addResource("change-password")
			.addMethod("POST", new apigw.LambdaIntegration(changePasswordFn), {
				authorizationType: apigw.AuthorizationType.NONE,
			});

		// ---- /api/data  (any authenticated user) ---------------------------
		const apiResource = api.root.addResource("api");
		apiResource
			.addResource("data")
			.addMethod("GET", new apigw.LambdaIntegration(publicFn), authorizedMethodOptions);

		// ---- /api/admin/users  (admin group only) --------------------------
		apiResource
			.addResource("admin")
			.addResource("users")
			.addMethod("GET", new apigw.LambdaIntegration(adminFn), authorizedMethodOptions);

		// ------------------------------------------------------------------ //
		//  7. Stack outputs                                                    //
		// ------------------------------------------------------------------ //
		new cdk.CfnOutput(this, "UserPoolId", { value: userPool.userPoolId });
		new cdk.CfnOutput(this, "UserPoolClientId", { value: userPoolClient.userPoolClientId });
		new cdk.CfnOutput(this, "ApiUrl", { value: api.url });
		new cdk.CfnOutput(this, "LoginEndpoint", { value: `${api.url}auth/login` });
	}
}
