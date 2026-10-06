import { APILog, PerformanceDataPoint, StatusDataPoint } from './types';

export const mockLogs: APILog[] = [
  { 
    id: '1', 
    timestamp: '2025-10-31 14:23:45', 
    method: 'POST', 
    endpoint: '/api/v1/queue', 
    status: 200, 
    duration: 487, 
    size: '4.8 KB', 
    source: 'ecomkassa',
    request: {
      headers: { 
        'Content-Type': 'application/json',
        'User-Agent': 'Bitrix24-Payti-Integration/1.0'
      },
      body: { 
        kassaid: '987654',
        token: 'ek_token_***',
        external_id: 'bitrix24_payment_12345',
        amount: 15000,
        description: 'Оплата по сделке #12345',
        receipt: {
          email: 'client@example.com',
          taxation: 'usn_income',
          inn: '7707083893',
          payment_address: 'www.example.com',
          items: [{
            name: 'Консультация по маркетингу',
            price: 15000,
            quantity: 1,
            sum: 15000,
            tax: 'vat20',
            tax_sum: 2500,
            payment_method: 'full_prepayment',
            payment_object: 'service'
          }]
        },
        callback_url: 'https://example.bitrix24.ru/ecomkassa/callback.php?secret=abc123'
      }
    },
    response: {
      headers: { 
        'Content-Type': 'application/json',
        'X-Request-Id': 'req_ek_abc123'
      },
      body: { 
        success: true,
        payment_id: 'pay_xyz789',
        external_id: 'bitrix24_payment_12345',
        payment_url: 'https://pay.ecomkassa.ru/pay_xyz789',
        status: 'pending'
      }
    }
  },
  { 
    id: '2', 
    timestamp: '2025-10-31 14:23:42', 
    method: 'GET', 
    endpoint: '/rest/sale.paysystem.pay.payment', 
    status: 200, 
    duration: 234, 
    size: '2.1 KB', 
    source: 'bitrix',
    request: {
      headers: { 
        'Accept': 'application/json'
      },
      body: null
    },
    response: {
      headers: { 
        'Content-Type': 'application/json'
      },
      body: { 
        result: {
          payment: {
            ID: '456',
            PAID: 'Y',
            DATE_PAID: '2025-10-31T14:23:42Z',
            PAY_SYSTEM_ID: '10',
            SUM: '15000.00',
            CURRENCY: 'RUB'
          }
        },
        time: {
          start: 1730382222.100,
          finish: 1730382222.334,
          duration: 0.234
        }
      }
    }
  },
  { 
    id: '3', 
    timestamp: '2025-10-31 14:23:38', 
    method: 'POST', 
    endpoint: '/login', 
    status: 200, 
    duration: 892, 
    size: '1.2 KB', 
    source: 'ecomkassa',
    request: {
      headers: { 
        'Content-Type': 'application/json'
      },
      body: { 
        login: 'portal@example.com',
        password: '***'
      }
    },
    response: {
      headers: { 
        'Content-Type': 'application/json',
        'Set-Cookie': 'session_id=***; HttpOnly; Secure'
      },
      body: { 
        success: true,
        access_token: 'ek_token_abc123xyz',
        token_type: 'bearer',
        expires_in: 3600
      }
    }
  },
  { 
    id: '4', 
    timestamp: '2025-10-31 14:23:35', 
    method: 'GET', 
    endpoint: '/rest/crm.deal.productrows.get', 
    status: 200, 
    duration: 178, 
    size: '5.7 KB', 
    source: 'bitrix',
    request: {
      headers: { 
        'Accept': 'application/json'
      },
      body: null
    },
    response: {
      headers: { 
        'Content-Type': 'application/json'
      },
      body: { 
        result: [
          {
            ID: '1',
            OWNER_ID: '12345',
            OWNER_TYPE: 'D',
            PRODUCT_ID: '567',
            PRODUCT_NAME: 'Консультация по маркетингу',
            PRICE: '15000.00',
            PRICE_EXCLUSIVE: '12500.00',
            PRICE_NETTO: '12500.00',
            PRICE_BRUTTO: '15000.00',
            QUANTITY: '1',
            TAX_RATE: '20',
            TAX_INCLUDED: 'Y'
          }
        ],
        total: 1,
        time: {
          start: 1730382215.100,
          finish: 1730382215.278,
          duration: 0.178
        }
      }
    }
  },
  { 
    id: '5', 
    timestamp: '2025-10-31 14:23:30', 
    method: 'GET', 
    endpoint: '/rest/crm.deal.get', 
    status: 200, 
    duration: 156, 
    size: '8.3 KB', 
    source: 'bitrix',
    request: {
      headers: { 
        'Accept': 'application/json'
      },
      body: null
    },
    response: {
      headers: { 
        'Content-Type': 'application/json'
      },
      body: { 
        result: {
          ID: '12345',
          TITLE: 'Сделка с ООО "Рога и Копыта"',
          STAGE_ID: 'NEW',
          OPPORTUNITY: '15000.00',
          CURRENCY_ID: 'RUB',
          CONTACT_ID: '789',
          COMPANY_ID: '234',
          UF_CRM_CLIENT_EMAIL: 'client@example.com',
          UF_CRM_CLIENT_PHONE: '+79991234567'
        },
        time: {
          start: 1730382210.100,
          finish: 1730382210.256,
          duration: 0.156
        }
      }
    }
  },
  { 
    id: '6', 
    timestamp: '2025-10-31 14:23:28', 
    method: 'GET', 
    endpoint: '/callback.php', 
    status: 200, 
    duration: 312, 
    size: '0.5 KB', 
    source: 'ecomkassa',
    request: {
      headers: { 
        'User-Agent': 'Payti-Callback/1.0'
      },
      body: null
    },
    response: {
      headers: { 
        'Content-Type': 'text/html; charset=UTF-8'
      },
      body: { 
        message: 'Payment processed successfully',
        payment_marked: true,
        bitrix_response: 'OK'
      }
    }
  },
  { 
    id: '7', 
    timestamp: '2025-10-31 14:23:25', 
    method: 'POST', 
    endpoint: '/api/v1/queue', 
    status: 400, 
    duration: 234, 
    size: '0.6 KB', 
    source: 'ecomkassa',
    request: {
      headers: { 
        'Content-Type': 'application/json'
      },
      body: { 
        kassaid: '987654',
        token: 'invalid_token',
        external_id: 'bitrix24_payment_error',
        amount: 5000
      }
    },
    response: {
      headers: { 
        'Content-Type': 'application/json'
      },
      body: { 
        success: false,
        error: 'INVALID_TOKEN',
        message: 'Токен авторизации недействителен или истек'
      }
    }
  },
  { 
    id: '8', 
    timestamp: '2025-10-31 14:23:20', 
    method: 'GET', 
    endpoint: '/rest/crm.deal.fields', 
    status: 200, 
    duration: 145, 
    size: '12.4 KB', 
    source: 'bitrix',
    request: {
      headers: { 
        'Accept': 'application/json'
      },
      body: null
    },
    response: {
      headers: { 
        'Content-Type': 'application/json',
        'Cache-Control': 'max-age=3600'
      },
      body: { 
        result: {
          ID: { type: 'integer', isRequired: false, isReadOnly: true },
          TITLE: { type: 'string', isRequired: true, isReadOnly: false },
          OPPORTUNITY: { type: 'double', isRequired: false, isReadOnly: false },
          CURRENCY_ID: { type: 'crm_currency', isRequired: false, isReadOnly: false },
          STAGE_ID: { type: 'crm_status', isRequired: false, isReadOnly: false }
        },
        time: {
          start: 1730382200.100,
          finish: 1730382200.245,
          duration: 0.145
        }
      }
    }
  },
  { 
    id: '9', 
    timestamp: '2025-10-31 14:23:15', 
    method: 'POST', 
    endpoint: '/api/v1/queue', 
    status: 500, 
    duration: 1456, 
    size: '0.9 KB', 
    source: 'ecomkassa',
    request: {
      headers: { 
        'Content-Type': 'application/json'
      },
      body: { 
        kassaid: '987654',
        token: 'ek_token_***',
        external_id: 'bitrix24_payment_999',
        amount: -1000,
        receipt: {
          email: 'invalid-email',
          items: []
        }
      }
    },
    response: {
      headers: { 
        'Content-Type': 'application/json'
      },
      body: { 
        success: false,
        error: 'VALIDATION_ERROR',
        message: 'Сумма должна быть положительной, email некорректен, список товаров пуст',
        errors: [
          { field: 'amount', message: 'Amount must be positive' },
          { field: 'receipt.email', message: 'Invalid email format' },
          { field: 'receipt.items', message: 'Items array cannot be empty' }
        ]
      }
    }
  },
  { 
    id: '10', 
    timestamp: '2025-10-31 14:23:10', 
    method: 'GET', 
    endpoint: '/rest/crm.contact.get', 
    status: 404, 
    duration: 89, 
    size: '0.3 KB', 
    source: 'bitrix',
    request: {
      headers: { 
        'Accept': 'application/json'
      },
      body: null
    },
    response: {
      headers: { 
        'Content-Type': 'application/json'
      },
      body: { 
        error: 'NOT_FOUND',
        error_description: 'Контакт не найден'
      }
    }
  },
];

export const performanceData: PerformanceDataPoint[] = [
  { time: '14:20', avg: 245, p95: 580 },
  { time: '14:21', avg: 312, p95: 720 },
  { time: '14:22', avg: 289, p95: 650 },
  { time: '14:23', avg: 398, p95: 1100 },
  { time: '14:24', avg: 267, p95: 590 },
];

export const statusData: StatusDataPoint[] = [
  { name: '2xx', count: 3542 },
  { name: '3xx', count: 127 },
  { name: '4xx', count: 289 },
  { name: '5xx', count: 67 },
];
