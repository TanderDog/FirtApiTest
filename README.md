# FirtApiTest

Учебный FastAPI-проект: страница с пользователями + страница с котировками акций MOEX

## Стек

- FastAPI + Jinja2 (SSR-шаблоны)
- PostgreSQL (asyncpg, без ORM)
- httpx — запросы к MOEX ISS API
- Poetry — управление зависимостями
- Docker Compose — поднятие БД

## Структура
app/
    main.py — роуты
    database.py — работа с БД (users)
    config.py — настройки из .env (pydantic-settings)
    schemas.py — Pydantic-модели
    calculations.py — расчёты (дельта/проценты)
    migrate.py — применение SQL-миграций
    stocks/ — всё про акции (репозиторий, MOEX API, координатор)
migrations/ — SQL-файлы миграций БД
templates/ — HTML-шаблоны
