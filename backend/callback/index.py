'''
Business: Обработка callback от платёжного API (Payti) после оплаты и обновление статуса в Bitrix24
Args: event с httpMethod, queryStringParameters (external_id, secret), context с request_id
Returns: HTTP response с результатом обработки
'''

import json
import os
import requests
import psycopg2
from typing import Dict, Any, Optional

def get_db_connection():
    dsn = os.environ.get('DATABASE_URL')
    return psycopg2.connect(dsn)

def get_bill_by_external_id(external_id: str, secret: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = '''
        SELECT b.id, b.member_id, b.payment_id, b.paysystem_id, b.deal_id, b.status,
               u.webhook_url
        FROM bills b
        JOIN users u ON b.member_id = u.member_id
        WHERE b.external_id = %s AND b.secret = %s
    '''
    cur.execute(query, (external_id, secret))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return None
    
    return {
        'id': row[0],
        'member_id': row[1],
        'payment_id': row[2],
        'paysystem_id': row[3],
        'deal_id': row[4],
        'status': row[5],
        'webhook_url': row[6]
    }

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

def update_bill_status(bill_id: int, status: str):
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = '''
        UPDATE bills 
        SET status = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE id = %s
    '''
    cur.execute(query, (status, bill_id))
    conn.commit()
    cur.close()
    conn.close()

def mark_payment_as_paid_bitrix24(payment_id: int, webhook_url: str, member_id: str, deal_id: int, external_id: str) -> bool:
    try:
        url = f'{webhook_url}/rest/sale.paysystem.pay.payment'
        params = {'ID': payment_id}
        
        log_integration('bitrix24_request', member_id, str(deal_id), external_id, 
                       f'{url}?ID={payment_id}', '', 'sent')
        
        response = requests.get(url, params=params, timeout=10)
        
        log_integration('bitrix24_response', member_id, str(deal_id), external_id, 
                       '', str(response.status_code), 'success' if response.status_code == 200 else 'error')
        
        return response.status_code == 200
    except Exception as e:
        log_integration('bitrix24_response', member_id, str(deal_id), external_id, 
                       '', '', 'error', str(e))
        return False

def call_custom_webhook(webhook_url: str, deal_id: int, member_id: str, external_id: str) -> bool:
    try:
        url = webhook_url.replace('{{ID}}', str(deal_id))
        
        log_integration('webhook_request', member_id, str(deal_id), external_id, 
                       url, '', 'sent')
        
        response = requests.get(url, timeout=10)
        
        log_integration('webhook_response', member_id, str(deal_id), external_id, 
                       '', str(response.status_code), 'success' if response.status_code == 200 else 'error')
        
        return response.status_code == 200
    except Exception as e:
        log_integration('webhook_response', member_id, str(deal_id), external_id, 
                       '', '', 'error', str(e))
        return False

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    cleanup_old_logs()
    
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method not in ['GET', 'POST']:
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    try:
        params = event.get('queryStringParameters', {}) or {}
        external_id = params.get('external_id')
        secret = params.get('secret')
        
        if not external_id or not secret:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Missing external_id or secret'}),
                'isBase64Encoded': False
            }
        
        bill = get_bill_by_external_id(external_id, secret)
        
        if not bill:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Bill not found or invalid secret'}),
                'isBase64Encoded': False
            }
        
        if bill['status'] == 'paid':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'Payment already processed'}),
                'isBase64Encoded': False
            }
        
        log_integration('callback_received', bill['member_id'], str(bill['deal_id']), external_id, 
                       json.dumps(params), '', 'processing')
        
        success = False
        
        if bill['webhook_url'] and '{{ID}}' in bill['webhook_url']:
            success = call_custom_webhook(bill['webhook_url'], bill['deal_id'], bill['member_id'], external_id)
        elif bill['payment_id']:
            bitrix_webhook = bill.get('webhook_url', '').split('/rest/')[0]
            if bitrix_webhook:
                success = mark_payment_as_paid_bitrix24(bill['payment_id'], bitrix_webhook, 
                                                        bill['member_id'], bill['deal_id'], external_id)
        
        if success:
            update_bill_status(bill['id'], 'paid')
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'message': 'Payment processed successfully',
                    'payment_marked': True,
                    'external_id': external_id
                }),
                'isBase64Encoded': False
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'error': 'Failed to mark payment in Bitrix24',
                    'external_id': external_id
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