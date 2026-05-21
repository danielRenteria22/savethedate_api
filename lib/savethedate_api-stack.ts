import * as path from "path";
import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigw from "aws-cdk-lib/aws-apigateway";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as lambdaEventSources from "aws-cdk-lib/aws-lambda-event-sources";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";

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
		//  2.5. DynamoDB Table                                                 //
		// ------------------------------------------------------------------ //
		const invitationsTable = new dynamodb.Table(this, "InvitationsTable", {
			tableName: "invitations-table",
			partitionKey: { name: "PK", type: dynamodb.AttributeType.STRING },
			sortKey: { name: "SK", type: dynamodb.AttributeType.STRING },
			billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
			removalPolicy: cdk.RemovalPolicy.DESTROY,
		});

		// ------------------------------------------------------------------ //
		//  2.6. SQS Queue for Invitations                                      //
		// ------------------------------------------------------------------ //
		const invitationDLQ = new sqs.Queue(this, "InvitationDLQ", {
			queueName: "invitation-dlq",
			retentionPeriod: cdk.Duration.days(14)
		});

		const invitationQueue = new sqs.Queue(this, "InvitationQueue", {
			queueName: "invitation-queue",
			visibilityTimeout: cdk.Duration.seconds(90),
			deadLetterQueue: {
				queue: invitationDLQ,
				maxReceiveCount: 3
			}
		});

		// ------------------------------------------------------------------ //
		//  3. Shared Lambda environment variables                              //
		// ------------------------------------------------------------------ //
		const twilioSecretName = "twilio-credentials";
		
		const commonEnv: Record<string, string> = {
			USER_POOL_ID: userPool.userPoolId,
			CLIENT_ID: userPoolClient.userPoolClientId,
			REGION: this.region,
			TABLE_NAME: invitationsTable.tableName,
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

		// --- Admin Authorizer -----------------------------------------------
		const adminAuthorizerFn = new lambda.Function(this, "AdminAuthorizerFunction", {
			...defaultLambdaProps,
			functionName: "cognito-admin-authorizer",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas/authorizer")),
			handler: "admin.handler",
			timeout: cdk.Duration.seconds(10),
		});

		// --- User Authorizer ------------------------------------------------
		const userAuthorizerFn = new lambda.Function(this, "UserAuthorizerFunction", {
			...defaultLambdaProps,
			functionName: "cognito-user-authorizer",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas/authorizer")),
			handler: "user.handler",
			timeout: cdk.Duration.seconds(10),
		});

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

		// --- Create Event Lambda (admin group only) ------------------------
		const createEventFn = new lambda.Function(this, "CreateEventFunction", {
			...defaultLambdaProps,
			functionName: "create-event",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas/")),
			handler: "create_event.index.handler",
		});

		createEventFn.addToRolePolicy(
			new iam.PolicyStatement({
				actions: [
					"cognito-idp:AdminCreateUser",
					"cognito-idp:AdminSetUserPassword",
					"cognito-idp:AdminAddUserToGroup",
				],
				resources: [userPool.userPoolArn],
			})
		);

		// --- List Events Lambda (admin group only) -------------------------
		const listEventsFn = new lambda.Function(this, "ListEventsFunction", {
			...defaultLambdaProps,
			functionName: "list-events",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "list_events.index.handler",
		});

		// --- Update Event Lambda (admin group only) ------------------------
		const updateEventFn = new lambda.Function(this, "UpdateEventFunction", {
			...defaultLambdaProps,
			functionName: "update-event",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "update_event.index.handler",
		});

		// --- Delete Event Lambda (admin group only) ------------------------
		const deleteEventFn = new lambda.Function(this, "DeleteEventFunction", {
			...defaultLambdaProps,
			functionName: "delete-event",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "delete_event.index.handler",
		});

		deleteEventFn.addToRolePolicy(
			new iam.PolicyStatement({
				actions: ["cognito-idp:AdminDeleteUser"],
				resources: [userPool.userPoolArn],
			})
		);

		// Grant DynamoDB permissions to relevant Lambdas
		invitationsTable.grantReadWriteData(publicFn);
		invitationsTable.grantReadWriteData(adminFn);
		invitationsTable.grantReadWriteData(createEventFn);
		invitationsTable.grantReadWriteData(listEventsFn);
		invitationsTable.grantReadWriteData(updateEventFn);
		invitationsTable.grantReadWriteData(deleteEventFn);

		// --- Guest Management Lambdas (user group) --------------------------
		const addGuestFn = new lambda.Function(this, "AddGuestFunction", {
			...defaultLambdaProps,
			functionName: "add-guest",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "add_guest.index.handler",
		});

		const listGuestsFn = new lambda.Function(this, "ListGuestsFunction", {
			...defaultLambdaProps,
			functionName: "list-guests",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "list_guests.index.handler",
		});

		const updateGuestFn = new lambda.Function(this, "UpdateGuestFunction", {
			...defaultLambdaProps,
			functionName: "update-guest",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "update_guest.index.handler",
		});

		const deleteGuestFn = new lambda.Function(this, "DeleteGuestFunction", {
			...defaultLambdaProps,
			functionName: "delete-guest",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "delete_guest.index.handler",
		});

		invitationsTable.grantReadWriteData(addGuestFn);
		invitationsTable.grantReadWriteData(listGuestsFn);
		invitationsTable.grantReadWriteData(updateGuestFn);
		invitationsTable.grantReadWriteData(deleteGuestFn);

		// --- Checkin Guest Lambda (user group) -------------------------------
		const checkinGuestFn = new lambda.Function(this, "CheckinGuestFunction", {
			...defaultLambdaProps,
			functionName: "checkin-guest",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "checkin_guest.index.handler",
		});

		invitationsTable.grantReadWriteData(checkinGuestFn);

		// --- Update My Event Lambda (user group) ----------------------------
		const updateMyEventFn = new lambda.Function(this, "UpdateMyEventFunction", {
			...defaultLambdaProps,
			functionName: "update-my-event",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "update_my_event.index.handler",
		});

		invitationsTable.grantReadWriteData(updateMyEventFn);

		// --- Get My Event Lambda (user group) -------------------------------
		const getMyEventFn = new lambda.Function(this, "GetMyEventFunction", {
			...defaultLambdaProps,
			functionName: "get-my-event",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "get_my_event.index.handler",
		});

		invitationsTable.grantReadData(getMyEventFn);

		// --- Confirm Attendance Lambda (public) -----------------------------
		const confirmAttendanceFn = new lambda.Function(this, "ConfirmAttendanceFunction", {
			...defaultLambdaProps,
			functionName: "confirm-attendance",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "confirm_attendance.index.handler",
		});

		invitationsTable.grantReadWriteData(confirmAttendanceFn);

		// --- Get Invitation Lambda (public) ---------------------------------
		const getInvitationFn = new lambda.Function(this, "GetInvitationFunction", {
			...defaultLambdaProps,
			functionName: "get-invitation",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "get_invitation.index.handler",
		});

		invitationsTable.grantReadData(getInvitationFn);

		// --- Send Invitation Lambda (user group) ----------------------------
		const sendInvitationFn = new lambda.Function(this, "SendInvitationFunction", {
			...defaultLambdaProps,
			functionName: "send-invitation",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "send_invitation.index.handler",
			environment: {
				...commonEnv,
				QUEUE_URL: invitationQueue.queueUrl
			}
		});

		invitationQueue.grantSendMessages(sendInvitationFn);
		invitationsTable.grantReadWriteData(sendInvitationFn);

		// --- Send All Invitations Lambda (user group) -----------------------
		const sendAllInvitationsFn = new lambda.Function(this, "SendAllInvitationsFunction", {
			...defaultLambdaProps,
			functionName: "send-all-invitations",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "send_all_invitations.index.handler",
			environment: {
				...commonEnv,
				QUEUE_URL: invitationQueue.queueUrl
			}
		});

		invitationQueue.grantSendMessages(sendAllInvitationsFn);
		invitationsTable.grantReadWriteData(sendAllInvitationsFn);

		// --- Twilio Callback Lambda (public) --------------------------------
		const twilioCallbackFn = new lambda.Function(this, "TwilioCallbackFunction", {
			...defaultLambdaProps,
			functionName: "twilio-callback",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "twilio_callback.index.handler",
		});

		invitationsTable.grantReadWriteData(twilioCallbackFn);

		// --- Process Invitation Lambda (SQS consumer) -----------------------
		const processInvitationFn = new lambda.Function(this, "ProcessInvitationFunction", {
			...defaultLambdaProps,
			functionName: "process-invitation",
			code: lambda.Code.fromAsset(path.join(__dirname, "../lambdas")),
			handler: "process_invitation.index.handler",
			timeout: cdk.Duration.seconds(60),
			environment: {
				...commonEnv,
				TWILIO_SECRET_NAME: twilioSecretName,
				CALLBACK_URL: "" // Will be set after API creation
			}
		});

		processInvitationFn.addEventSource(new lambdaEventSources.SqsEventSource(invitationQueue, {
			batchSize: 10,
			reportBatchItemFailures: true
		}));

		invitationsTable.grantReadWriteData(processInvitationFn);

		processInvitationFn.addToRolePolicy(
			new iam.PolicyStatement({
				actions: ["secretsmanager:GetSecretValue"],
				resources: [`arn:aws:secretsmanager:${this.region}:${this.account}:secret:${twilioSecretName}-*`]
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

		// Admin token authorizer — requires admin group
		const adminAuthorizer = new apigw.TokenAuthorizer(this, "AdminAuthorizer", {
			handler: adminAuthorizerFn,
			identitySource: "method.request.header.Authorization",
			resultsCacheTtl: cdk.Duration.minutes(5),
		});

		// User token authorizer — requires user group
		const userAuthorizer = new apigw.TokenAuthorizer(this, "UserAuthorizer", {
			handler: userAuthorizerFn,
			identitySource: "method.request.header.Authorization",
			resultsCacheTtl: cdk.Duration.minutes(5),
		});

		const adminMethodOptions: apigw.MethodOptions = {
			authorizationType: apigw.AuthorizationType.CUSTOM,
			authorizer: adminAuthorizer,
		};

		const userMethodOptions: apigw.MethodOptions = {
			authorizationType: apigw.AuthorizationType.CUSTOM,
			authorizer: userAuthorizer,
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

		// ---- /confirm  (public, no authorizer) -----------------------------
		api.root
			.addResource("confirm")
			.addMethod("POST", new apigw.LambdaIntegration(confirmAttendanceFn), {
				authorizationType: apigw.AuthorizationType.NONE,
			});

		// ---- /api/data  (user group required) ------------------------------
		const apiResource = api.root.addResource("api");
		apiResource
			.addResource("data")
			.addMethod("GET", new apigw.LambdaIntegration(publicFn), userMethodOptions);

		// ---- /api/{event_id}/{confirmation_code}  (public, no authorizer) --
		const invitationEventResource = apiResource.addResource("{event_id}");
		invitationEventResource
			.addResource("{confirmation_code}")
			.addMethod("GET", new apigw.LambdaIntegration(getInvitationFn), {
				authorizationType: apigw.AuthorizationType.NONE,
			});

		// ---- /api/admin/users  (admin group only) --------------------------
		const adminResource = apiResource.addResource("admin");
		adminResource
			.addResource("users")
			.addMethod("GET", new apigw.LambdaIntegration(adminFn), adminMethodOptions);

		// ---- /api/admin/event  (admin group only) --------------------------
		const eventResource = adminResource.addResource("event");
		eventResource.addMethod("POST", new apigw.LambdaIntegration(createEventFn), adminMethodOptions);
		eventResource.addMethod("GET", new apigw.LambdaIntegration(listEventsFn), adminMethodOptions);

		const eventSubdomainResource = eventResource.addResource("{subdomain}");
		eventSubdomainResource.addMethod("PUT", new apigw.LambdaIntegration(updateEventFn), adminMethodOptions);
		eventSubdomainResource.addMethod("DELETE", new apigw.LambdaIntegration(deleteEventFn), adminMethodOptions);

		// ---- /host/guests  (user group) ------------------------------------
		const hostResource = api.root.addResource("host");
		const guestsResource = hostResource.addResource("guests");
		guestsResource.addMethod("POST", new apigw.LambdaIntegration(addGuestFn), userMethodOptions);
		guestsResource.addMethod("GET", new apigw.LambdaIntegration(listGuestsFn), userMethodOptions);

		const guestIdResource = guestsResource.addResource("{guest_id}");
		guestIdResource.addMethod("PUT", new apigw.LambdaIntegration(updateGuestFn), userMethodOptions);
		guestIdResource.addMethod("DELETE", new apigw.LambdaIntegration(deleteGuestFn), userMethodOptions);

		// ---- /host/checkin  (user group) ------------------------------------
		hostResource
			.addResource("checkin")
			.addMethod("POST", new apigw.LambdaIntegration(checkinGuestFn), userMethodOptions);

		// ---- /host/event  (user group) -------------------------------------
		const hostEventResource = hostResource.addResource("event");
		hostEventResource.addMethod("PUT", new apigw.LambdaIntegration(updateMyEventFn), userMethodOptions);
		hostEventResource.addMethod("GET", new apigw.LambdaIntegration(getMyEventFn), userMethodOptions);

		// ---- /host/send-invitation  (user group) ---------------------------
		hostResource
			.addResource("send-invitation")
			.addMethod("POST", new apigw.LambdaIntegration(sendInvitationFn), userMethodOptions);

		// ---- /host/send-all-invitations  (user group) ----------------------
		hostResource
			.addResource("send-all-invitations")
			.addMethod("POST", new apigw.LambdaIntegration(sendAllInvitationsFn), userMethodOptions);

		// ---- /callback/twilio  (public, no authorizer) ---------------------
		const callbackResource = api.root.addResource("callback");
		callbackResource
			.addResource("twilio")
			.addMethod("POST", new apigw.LambdaIntegration(twilioCallbackFn), {
				authorizationType: apigw.AuthorizationType.NONE,
			});

		// Update process invitation Lambda with callback URL
		processInvitationFn.addEnvironment("CALLBACK_URL", `${api.url}callback/twilio`);

		// ------------------------------------------------------------------ //
		//  7. Stack outputs                                                    //
		// ------------------------------------------------------------------ //
		new cdk.CfnOutput(this, "UserPoolId", { value: userPool.userPoolId });
		new cdk.CfnOutput(this, "UserPoolClientId", { value: userPoolClient.userPoolClientId });
		new cdk.CfnOutput(this, "ApiUrl", { value: api.url });
		new cdk.CfnOutput(this, "LoginEndpoint", { value: `${api.url}auth/login` });
		new cdk.CfnOutput(this, "TableName", { value: invitationsTable.tableName });
		new cdk.CfnOutput(this, "InvitationQueueUrl", { value: invitationQueue.queueUrl });
		new cdk.CfnOutput(this, "TwilioCallbackUrl", { value: `${api.url}callback/twilio` });
	}
}
