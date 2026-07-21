import json
import os
import csv
import io
import base64
import unicodedata
from utils.guest_dao import GuestBuilder, GuestDAO
from utils.response import cors_response

table_name = os.environ['TABLE_NAME']


def normalize_string(s: str) -> str:
    if not s:
        return ""
    nkfd = unicodedata.normalize('NFKD', str(s))
    return "".join([c for c in nkfd if not unicodedata.combining(c)]).strip().lower()


def extract_csv_from_multipart(raw_body: str) -> str:
    if not raw_body:
        return ""
    if 'Content-Disposition:' in raw_body or '----------------' in raw_body:
        # If body is wrapped in multipart form-data, strip multipart boundary headers
        parts = raw_body.split('\r\n\r\n')
        if len(parts) < 2:
            parts = raw_body.split('\n\n')
        if len(parts) >= 2:
            csv_part = parts[1]
            lines = csv_part.splitlines()
            clean_lines = [line for line in lines if not line.startswith('----------------')]
            return '\n'.join(clean_lines)
    return raw_body


def parse_guests_from_csv(csv_content: str, subdomain: str):
    csv_content = extract_csv_from_multipart(csv_content)
    f = io.StringIO(csv_content.strip())
    reader = csv.DictReader(f)
    
    guests_to_create = []
    errors = []
    
    for row_idx, raw_row in enumerate(reader, start=2):  # Header is row 1
        if not raw_row:
            continue
            
        row = {}
        for k, v in raw_row.items():
            if k is not None:
                val = v.strip() if isinstance(v, str) else v
                row[normalize_string(k)] = val
                
        first_name = row.get('nombre') or row.get('first_name') or row.get('firstname') or ''
        last_name = row.get('apellido') or row.get('apellidos') or row.get('last_name') or row.get('lastname') or ''
        full_name = row.get('name') or row.get('nombre_completo') or row.get('full_name') or row.get('nombre completo')
        
        if not full_name:
            full_name = f"{first_name} {last_name}".strip()
            
        if not full_name:
            errors.append({'row': row_idx, 'error': 'Missing guest name'})
            continue

        raw_phone_code = (
            row.get('codigo pais') or row.get('codigo_pais') or 
            row.get('phone_code') or row.get('codigo') or 
            row.get('pais') or '52'
        )
        phone_code = str(raw_phone_code).strip()
        if not phone_code:
            phone_code = '+52'
        elif not phone_code.startswith('+'):
            phone_code = f"+{phone_code}"
            
        phone_number = str(
            row.get('whatsapp') or row.get('phone_number') or 
            row.get('telefono') or row.get('celular') or ''
        ).strip()
        
        if not phone_number:
            errors.append({'row': row_idx, 'error': f'Missing phone number for {full_name}'})
            continue

        raw_num_guests = (
            row.get('no. pases recepcion') or row.get('no. pases') or 
            row.get('no pases recepcion') or row.get('pases recepcion') or 
            row.get('pases') or row.get('num_guests') or row.get('invitados') or '1'
        )
        try:
            num_guests = int(raw_num_guests)
            if num_guests < 1:
                num_guests = 1
        except (ValueError, TypeError):
            num_guests = 1

        table = (
            row.get('no. mesa') or row.get('no mesa') or 
            row.get('mesa') or row.get('table') or None
        )
        if table is not None:
            table = str(table).strip()
            if not table:
                table = None

        civil_inv = str(row.get('civil') or row.get('civil_wedding_invitation') or row.get('boda civil') or '').strip().lower() in ['true', '1', 'si', 'yes']
        after_inv = str(row.get('after_party') or row.get('after_party_invitation') or row.get('after') or row.get('fiesta') or '').strip().lower() in ['true', '1', 'si', 'yes']

        builder = GuestBuilder()\
            .event_id(subdomain)\
            .name(full_name)\
            .phone_code(phone_code)\
            .phone_number(phone_number)\
            .num_guests(num_guests)\
            .civil_wedding_invitation(civil_inv)\
            .after_party_invitation(after_inv)

        if table:
            builder = builder.table(table)

        guest_data = builder.build()
        guests_to_create.append(guest_data)

    return guests_to_create, errors


def parse_guests_from_dict_list(guests_list: list, subdomain: str):
    guests_to_create = []
    errors = []
    
    for idx, item in enumerate(guests_list, start=1):
        if not isinstance(item, dict):
            errors.append({'index': idx, 'error': 'Item is not a dictionary'})
            continue
            
        name = item.get('name') or item.get('nombre')
        if not name or not str(name).strip():
            errors.append({'index': idx, 'error': 'Missing name'})
            continue
            
        phone_code = str(item.get('phone_code') or item.get('codigo_pais') or '+52').strip()
        if phone_code and not phone_code.startswith('+'):
            phone_code = f"+{phone_code}"
            
        phone_number = str(item.get('phone_number') or item.get('whatsapp') or item.get('telefono') or '').strip()
        if not phone_number:
            errors.append({'index': idx, 'error': f'Missing phone number for {name}'})
            continue
            
        try:
            num_guests = int(item.get('num_guests', 1))
            if num_guests < 1:
                num_guests = 1
        except (ValueError, TypeError):
            num_guests = 1
            
        builder = GuestBuilder()\
            .event_id(subdomain)\
            .name(str(name).strip())\
            .phone_code(phone_code)\
            .phone_number(phone_number)\
            .num_guests(num_guests)
            
        if 'civil_wedding_invitation' in item:
            builder = builder.civil_wedding_invitation(bool(item['civil_wedding_invitation']))
        if 'after_party_invitation' in item:
            builder = builder.after_party_invitation(bool(item['after_party_invitation']))
        if 'table' in item and item['table'] is not None:
            table_str = str(item['table']).strip()
            if table_str:
                builder = builder.table(table_str)
                
        guest_data = builder.build()
        guests_to_create.append(guest_data)
        
    return guests_to_create, errors


def handler(event, context):
    try:
        subdomain = event['requestContext']['authorizer'].get('username')
        if not subdomain:
            return cors_response(401, {'error': 'Unauthorized: missing user domain context'})

        body_raw = event.get('body', '')
        if event.get('isBase64Encoded', False):
            body_raw = base64.b64decode(body_raw).decode('utf-8')

        guests_to_create = []
        errors = []

        is_json = False
        parsed_json = None
        if isinstance(body_raw, str) and body_raw.strip().startswith(('{', '[')):
            try:
                parsed_json = json.loads(body_raw)
                is_json = True
            except Exception:
                is_json = False

        if is_json and parsed_json is not None:
            if isinstance(parsed_json, dict) and ('csv' in parsed_json or 'csv_content' in parsed_json):
                csv_str = parsed_json.get('csv') or parsed_json.get('csv_content') or ''
                guests_to_create, errors = parse_guests_from_csv(csv_str, subdomain)
            elif isinstance(parsed_json, dict) and 'guests' in parsed_json and isinstance(parsed_json['guests'], list):
                guests_to_create, errors = parse_guests_from_dict_list(parsed_json['guests'], subdomain)
            elif isinstance(parsed_json, list):
                guests_to_create, errors = parse_guests_from_dict_list(parsed_json, subdomain)
            else:
                return cors_response(400, {'error': 'Invalid JSON body structure. Expected {"csv": "..."}, {"guests": [...]}, or a list of guests.'})
        else:
            if not isinstance(body_raw, str) or not body_raw.strip():
                return cors_response(400, {'error': 'Empty request body'})
            guests_to_create, errors = parse_guests_from_csv(body_raw, subdomain)

        if not guests_to_create:
            return cors_response(400, {
                'error': 'No valid guests found in request payload',
                'errors': errors
            })

        dao = GuestDAO(table_name)
        created_guests = dao.create_guests_batch(guests_to_create)

        return cors_response(201, {
            'message': 'Batch guest creation successful',
            'created_count': len(created_guests),
            'guests': created_guests,
            'errors': errors
        })

    except Exception as e:
        return cors_response(500, {'error': str(e)})
