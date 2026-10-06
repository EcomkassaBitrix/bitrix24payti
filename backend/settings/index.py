'''
Business: Управление настройками интеграции Payti для аккаунтов Bitrix24
Args: event с httpMethod, body для POST/PUT, queryStringParameters для GET, context с request_id
Returns: HTTP response с настройками или статусом операции
'''

import json
import os
import uuid
import psycopg2
from typing import Dict, Any, Optional

def get_db_connection():
    dsn = os.environ.get('DATABASE_URL')
    return psycopg2.connect(dsn)

def get_settings(member_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = '''
        SELECT id, member_id, secret_code, ecom_login, ecom_kassa_id, 
               payment_object, payment_method, email_def_check,
               vat_100, vat_shipment, vat_order,
               company_email, company_sno, company_inn, company_payment_address,
               webhook_url, created_at, updated_at
        FROM users WHERE member_id = %s
    '''
    cur.execute(query, (member_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return None
    
    return {
        'id': row[0],
        'member_id': row[1],
        'secret_code': row[2],
        'ecom_login': row[3],
        'ecom_kassa_id': row[4],
        'payment_object': row[5],
        'payment_method': row[6],
        'email_def_check': row[7],
        'vat_100': row[8],
        'vat_shipment': row[9],
        'vat_order': row[10],
        'company_email': row[11],
        'company_sno': row[12],
        'company_inn': row[13],
        'company_payment_address': row[14],
        'webhook_url': row[15],
        'created_at': row[16].isoformat() if row[16] else None,
        'updated_at': row[17].isoformat() if row[17] else None
    }

def create_settings(data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()
    
    secret_code = data.get('secret_code') or uuid.uuid4().hex
    
    query = '''
        INSERT INTO users (
            member_id, secret_code, ecom_login, ecom_pass, ecom_kassa_id,
            payment_object, payment_method, email_def_check,
            vat_100, vat_shipment, vat_order,
            company_email, company_sno, company_inn, company_payment_address,
            webhook_url
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, member_id, secret_code
    '''
    
    cur.execute(query, (
        data['member_id'],
        secret_code,
        data.get('ecom_login'),
        data.get('ecom_pass'),
        data.get('ecom_kassa_id'),
        data.get('payment_object'),
        data.get('payment_method'),
        data.get('email_def_check'),
        data.get('vat_100'),
        data.get('vat_shipment'),
        data.get('vat_order'),
        data.get('company_email'),
        data.get('company_sno'),
        data.get('company_inn'),
        data.get('company_payment_address'),
        data.get('webhook_url')
    ))
    
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'id': row[0],
        'member_id': row[1],
        'secret_code': row[2]
    }

def update_settings(member_id: str, data: Dict[str, Any]) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = '''
        UPDATE users SET
            ecom_login = COALESCE(%s, ecom_login),
            ecom_pass = COALESCE(%s, ecom_pass),
            ecom_kassa_id = COALESCE(%s, ecom_kassa_id),
            payment_object = COALESCE(%s, payment_object),
            payment_method = COALESCE(%s, payment_method),
            email_def_check = COALESCE(%s, email_def_check),
            vat_100 = COALESCE(%s, vat_100),
            vat_shipment = COALESCE(%s, vat_shipment),
            vat_order = COALESCE(%s, vat_order),
            company_email = COALESCE(%s, company_email),
            company_sno = COALESCE(%s, company_sno),
            company_inn = COALESCE(%s, company_inn),
            company_payment_address = COALESCE(%s, company_payment_address),
            webhook_url = COALESCE(%s, webhook_url),
            updated_at = CURRENT_TIMESTAMP
        WHERE member_id = %s
    '''
    
    cur.execute(query, (
        data.get('ecom_login'),
        data.get('ecom_pass'),
        data.get('ecom_kassa_id'),
        data.get('payment_object'),
        data.get('payment_method'),
        data.get('email_def_check'),
        data.get('vat_100'),
        data.get('vat_shipment'),
        data.get('vat_order'),
        data.get('company_email'),
        data.get('company_sno'),
        data.get('company_inn'),
        data.get('company_payment_address'),
        data.get('webhook_url'),
        member_id
    ))
    
    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    
    return affected > 0

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Member-Id',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    try:
        if method == 'GET':
            params = event.get('queryStringParameters', {}) or {}
            member_id = params.get('member_id')
            
            if not member_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'member_id is required'}),
                    'isBase64Encoded': False
                }
            
            settings = get_settings(member_id)
            
            if not settings:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Settings not found'}),
                    'isBase64Encoded': False
                }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(settings),
                'isBase64Encoded': False
            }
        
        elif method == 'POST':
            body_data = json.loads(event.get('body', '{}'))
            member_id = body_data.get('member_id')
            
            if not member_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'member_id is required'}),
                    'isBase64Encoded': False
                }
            
            existing = get_settings(member_id)
            if existing:
                return {
                    'statusCode': 409,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Settings already exist for this member_id'}),
                    'isBase64Encoded': False
                }
            
            result = create_settings(body_data)
            
            return {
                'statusCode': 201,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'message': 'Settings created successfully',
                    'data': result
                }),
                'isBase64Encoded': False
            }
        
        elif method == 'PUT':
            body_data = json.loads(event.get('body', '{}'))
            member_id = body_data.get('member_id')
            
            if not member_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'member_id is required'}),
                    'isBase64Encoded': False
                }
            
            success = update_settings(member_id, body_data)
            
            if not success:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Settings not found'}),
                    'isBase64Encoded': False
                }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'message': 'Settings updated successfully'
                }),
                'isBase64Encoded': False
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Method not allowed'}),
                'isBase64Encoded': False
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
