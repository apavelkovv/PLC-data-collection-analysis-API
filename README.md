# PLC Data Collection & Analysis API

## Описание
REST API для сбора телеметрии с PLC, управления экспериментами и аутентификации.

## Технологии
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL
- Alembic
- Docker / Docker Compose

## Установка и запуск

1. Клонируйте репозиторий
2. Скопируйте `.env.example` в `.env` и настройте при необходимости
3. Запустите Docker Compose:
   ```bash
   docker-compose up -d