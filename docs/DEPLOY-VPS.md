# Деплой Payti на VPS (для начинающего DevOps)

Инструкция рассчитана на чистый Ubuntu 22.04 / 24.04 (1–2 CPU, 2 GB RAM достаточно для старта).

## 1. Что понадобится

- VPS с доступом по SSH (root или sudo)
- Домен (например `payti.example.com`) → A-запись на IP сервера
- Репозиторий: `https://github.com/EcomkassaBitrix/bitrix24payti`
- PostgreSQL (можно на том же VPS)
- Переменные окружения для backend (логин/пароль платёжного API, `DATABASE_URL` и т.д.)

## 2. Подключение к серверу

```bash
ssh root@ВАШ_IP
# или
ssh user@ВАШ_IP
```

Обновите систему:

```bash
sudo apt update && sudo apt upgrade -y
```

## 3. Базовые пакеты

```bash
sudo apt install -y git curl nginx postgresql postgresql-contrib python3 python3-pip python3-venv
```

Node.js 20 (для сборки фронта):

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node -v
npm -v
```

## 4. PostgreSQL

```bash
sudo -u postgres psql -c "CREATE USER payti WITH PASSWORD 'СИЛЬНЫЙ_ПАРОЛЬ';"
sudo -u postgres psql -c "CREATE DATABASE payti OWNER payti;"
```

Примените миграцию схемы (после клонирования в шаге 5):

```bash
sudo -u postgres psql -d payti -f /var/www/payti/db_migrations/V0001__create_ecomkassa_bitrix_tables.sql
```

Строка подключения:

```text
DATABASE_URL=postgresql://payti:СИЛЬНЫЙ_ПАРОЛЬ@127.0.0.1:5432/payti
```

## 5. Код проекта

```bash
sudo mkdir -p /var/www
sudo git clone -b main https://github.com/EcomkassaBitrix/bitrix24payti.git /var/www/payti
cd /var/www/payti
```

Если репозиторий private — используйте PAT:

```bash
sudo git clone -b main https://ВАШ_GITHUB_USER:ТОКЕН@github.com/EcomkassaBitrix/bitrix24payti.git /var/www/payti
```

## 6. Frontend (сборка статики)

```bash
cd /var/www/payti
sudo npm ci
sudo npm run build
# результат обычно в dist/
ls dist
```

Nginx будет отдавать `dist/` как статику.

## 7. Backend (Python)

Handlers:

- `backend/pay/` — создание платежа
- `backend/callback/` — callback после оплаты
- `backend/settings/` — настройки интеграции

```bash
cd /var/www/payti/backend
sudo python3 -m venv /var/www/payti/venv
sudo /var/www/payti/venv/bin/pip install -U pip
sudo /var/www/payti/venv/bin/pip install -r pay/requirements.txt
sudo /var/www/payti/venv/bin/pip install -r callback/requirements.txt
sudo /var/www/payti/venv/bin/pip install -r settings/requirements.txt
sudo /var/www/payti/venv/bin/pip install uvicorn fastapi pydantic requests psycopg2-binary
```

Окружение:

```bash
sudo mkdir -p /etc/payti
sudo nano /etc/payti/env
```

Пример:

```bash
DATABASE_URL=postgresql://payti:СИЛЬНЫЙ_ПАРОЛЬ@127.0.0.1:5432/payti
```

```bash
sudo chmod 600 /etc/payti/env
```

Точные имена переменных — в `backend/*/index.py` (`os.environ.get(...)`).

Пример systemd (замените `app:app` на вашу точку входа):

```bash
sudo nano /etc/systemd/system/payti-api.service
```

```ini
[Unit]
Description=Payti API
After=network.target postgresql.service

[Service]
Type=simple
EnvironmentFile=/etc/payti/env
WorkingDirectory=/var/www/payti/backend
ExecStart=/var/www/payti/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
Restart=on-failure
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now payti-api
sudo systemctl status payti-api
```

## 8. Nginx

```bash
sudo nano /etc/nginx/sites-available/payti
```

```nginx
server {
    listen 80;
    server_name payti.example.com;

    root /var/www/payti/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -sf /etc/nginx/sites-available/payti /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 9. HTTPS (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d payti.example.com
```

## 10. Bitrix24

В настройках приложения / платёжной системы укажите HTTPS URL вашего домена, callback и учётные данные платёжного API.

**API на выходе тот же** — меняется только бренд в UI.

## 11. Обновление

```bash
cd /var/www/payti
sudo git pull origin main
sudo npm ci
sudo npm run build
sudo systemctl restart payti-api
sudo systemctl reload nginx
```

## 12. Типовые проблемы

| Симптом | Что проверить |
|---------|----------------|
| 502 Bad Gateway | `systemctl status payti-api`, порт 8000, env |
| Белый экран | файлы в `dist/`, `root` в nginx |
| Ошибка БД | `DATABASE_URL`, миграция |
| Callback не приходит | HTTPS, firewall 80/443, URL в кабинете |

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## 13. Безопасность

- Не храните токены и пароли в git
- `chmod 600` на `/etc/payti/env`
- Только HTTPS снаружи
- Отдельный пользователь БД без superuser
