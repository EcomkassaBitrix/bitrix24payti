# Payti — интеграция Bitrix24

White-label сервис платежей и фискализации для Bitrix24 (API совместим с исходной интеграцией).

## Состав

- **Frontend** — Vite + React (API Monitor)
- **Backend** — Python handlers: `pay`, `callback`, `settings`
- **DB** — PostgreSQL (миграции в `db_migrations/`)

## Быстрый старт (локально)

```bash
# Frontend
npm install
npm run dev

# Backend — см. docs/DEPLOY-VPS.md
```

## Документация

- [Деплой на VPS для начинающих](docs/DEPLOY-VPS.md)

## Важно

Внешний платёжный API (`api.ecomkassa.ru`) и схема БД **не менялись** — меняется только брендинг (название Payti, UI, favicon).
