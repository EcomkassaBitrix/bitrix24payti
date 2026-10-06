'''
Business: Создание платежа Payti и отправка чека на фискализацию
Args: event с httpMethod, body (member_id, PAYMENT_ID, dealid, secret_code), context с request_id
Returns: HTTP response с payment_url или ошибкой
'''

import json
import os
import uuid
import requests
import psycopg2
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class PaymentRequest:
    member_id: str
    PAYMENT_ID: int
    PAYSYSTEM_ID: int
    dealid: int
    secret_code: str
    amount: float
    client_email: str

def get_db_connection():
    dsn = os.environ.get('DATABASE_URL')
    return psycopg2.connect(dsn)

def get_user_settings(member_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = '''
        SELECT ecom_login, ecom_pass, ecom_kassa_id, token_ecom_kassa,
               payment_object, payment_method, company_email, company_sno,
               company_inn, company_payment_address, vat_order, webhook_url
        FROM users WHERE member_id = %s
    '''
    cur.execute(query, (member_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return None
    
    return {
        'ecom_login': row[0],
        'ecom_pass': row[1],
        'ecom_kassa_id': row[2],
        'token_ecom_kassa': row[3],
        'payment_object': row[4],
        'payment_method': row[5],
        'company_email': row[6],
        'company_sno': row[7],
        'company_inn': row[8],
        'company_payment_address': row[9],
        'vat_order': row[10],
        'webhook_url': row[11]
    }

def get_ecomkassa_token(login: str, password: str) -> Optional[str]:
    try:
        response = requests.post(
            'https://api.ecomkassa.ru/login',
            json={'login': login, 'password': password},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
    except:
        pass
    return None

def create_bill(member_id: str, payment_id: int, paysystem_id: int, deal_id: int, external_id: str, secret: str) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = '''
        INSERT INTO bills (member_id, payment_id, paysystem_id, deal_id, external_id, secret, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        RETURNING id
    '''
    cur.execute(query, (member_id, payment_id, paysystem_id, deal_id, external_id, secret))
    bill_id = cur.fetchone()[0]
    
    conn.commit()
    cur.close()
    conn.close()
    
    return bill_id

def cleanup_old_logs():
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = '''
        DELETE FROM integration_logs 
        WHERE created_at < NOW() - INTERVAL '30 days'
    '''
    cur.execute(query)
    deleted_count = cur.rowcount
    
    conn.commit()
    cur.close()
    conn.close()
    
    return deleted_count

def log_integration(log_type: str, member_id: str, deal_id: str, external_id: str, 
                    request_data: str, response_data: str, status: str, error_message: str = None):
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = '''
        INSERT INTO integration_logs (log_type, member_id, deal_id, external_id, 
                                      request_data, response_data, status, error_message)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    '''
    cur.execute(query, (log_type, member_id, deal_id, external_id, 
                        request_data, response_data, status, error_message))
    
    conn.commit()
    cur.close()
    conn.close()

def create_ecomkassa_payment(settings: Dict[str, Any], payment_data: PaymentRequest, external_id: str, callback_url: str) -> Dict[str, Any]:
    token = settings.get('token_ecom_kassa')
    if not token:
        token = get_ecomkassa_token(settings['ecom_login'], settings['ecom_pass'])
        if not token:
            raise Exception('Failed to get EcomKassa token')
    
    receipt = {
        'email': payment_data.client_email or settings['company_email'],
        'taxation': settings['company_sno'] or 'usn_income',
        'inn': settings['company_inn'],
        'payment_address': settings['company_payment_address'],
        'items': [{
            'name': f'Оплата по сделке #{payment_data.dealid}',
            'price': payment_data.amount,
            'quantity': 1,
            'sum': payment_data.amount,
            'tax': settings['vat_order'] or 'vat20',
            'payment_method': settings['payment_method'] or 'full_prepayment',
            'payment_object': settings['payment_object'] or 'service'
        }]
    }
    
    payload = {
        'kassaid': settings['ecom_kassa_id'],
        'token': token,
        'external_id': external_id,
        'amount': payment_data.amount,
        'description': f'Оплата по сделке #{payment_data.dealid}',
        'receipt': receipt,
        'callback_url': callback_url
    }
    
    log_integration('ecomkassa_request', payment_data.member_id, str(payment_data.dealid), 
                   external_id, json.dumps(payload), '', 'sent')
    
    response = requests.post(
        'https://api.ecomkassa.ru/api/v1/queue',
        json=payload,
        timeout=15
    )
    
    response_data = response.json() if response.status_code == 200 else response.text
    
    if response.status_code != 200:
        log_integration('ecomkassa_response', payment_data.member_id, str(payment_data.dealid), 
                       external_id, '', str(response_data), 'error', f'HTTP {response.status_code}')
        raise Exception(f'EcomKassa API error: {response.text}')
    
    log_integration('ecomkassa_response', payment_data.member_id, str(payment_data.dealid), 
                   external_id, '', json.dumps(response_data), 'success')
    
    return response_data

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    cleanup_old_logs()
    
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Member-Id, X-Secret-Code',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    try:
        body_data = json.loads(event.get('body', '{}'))
        
        member_id = body_data.get('member_id')
        payment_id = body_data.get('PAYMENT_ID')
        paysystem_id = body_data.get('PAYSYSTEM_ID')
        deal_id = body_data.get('dealid')
        secret_code = body_data.get('secret_code')
        amount = body_data.get('amount')
        client_email = body_data.get('client_email')
        
        if not all([member_id, payment_id, deal_id, secret_code, amount]):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing required fields'}),
                'isBase64Encoded': False
            }
        
        settings = get_user_settings(member_id)
        if not settings:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'User settings not found'}),
                'isBase64Encoded': False
            }
        
        if settings.get('secret_code') and settings['secret_code'] != secret_code:
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Invalid secret code'}),
                'isBase64Encoded': False
            }
        
        external_id = f'bitrix24_payment_{uuid.uuid4().hex[:12]}'
        bill_secret = uuid.uuid4().hex
        
        callback_url = f'https://your-domain.com/backend/callback?external_id={external_id}&secret={bill_secret}'
        
        payment_request = PaymentRequest(
            member_id=member_id,
            PAYMENT_ID=payment_id,
            PAYSYSTEM_ID=paysystem_id,
            dealid=deal_id,
            secret_code=secret_code,
            amount=float(amount),
            client_email=client_email
        )
        
        ecom_response = create_ecomkassa_payment(settings, payment_request, external_id, callback_url)
        
        bill_id = create_bill(member_id, payment_id, paysystem_id, deal_id, external_id, bill_secret)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'payment_url': ecom_response.get('payment_url'),
                'payment_id': ecom_response.get('payment_id'),
                'external_id': external_id,
                'bill_id': bill_id
            }),
            'isBase64Encoded': False
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }