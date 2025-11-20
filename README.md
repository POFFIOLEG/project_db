# Retail Operations Toolkit

Полноценный pet-проект для учета справочников, сотрудников, товарных остатков, прайс-листов и расписаний. Репозиторий содержит:

- `backend/` — Django + DRF API, PostgreSQL в качестве БД.
- `frontend/` — Vite + React SPA для работы с API.

## Как выложить на GitHub

```bash
git init
git add .
git commit -m "Initial retail toolkit"
git remote add origin <ваш-репозиторий>
git push -u origin main
```

Далее можно работать как обычно (`git status`, `git add`, `git commit`, `git push`).

## Что нужно для запуска

- Python 3.11+ (разработка велась на 3.13).
- Node.js 18+ для фронтенда.
- PostgreSQL 15+ с доступом к локальному серверу.

Переменные подключения уже зашиты в `backend/core/settings.py`:

| Setting  | Value        |
|----------|--------------|
| NAME     | `retail_db`  |
| USER     | `retail_user`|
| PASSWORD | `qweqwe`     |
| HOST     | `127.0.0.1`  |
| PORT     | `5432`       |

Создай базу и пользователя заранее (через PgAdmin или `psql`):

```sql
CREATE DATABASE retail_db;
CREATE USER retail_user WITH PASSWORD 'qweqwe';
GRANT ALL PRIVILEGES ON DATABASE retail_db TO retail_user;
```

## Быстрый старт backend + автозаполнение БД

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # или source .venv/bin/activate в Linux/Mac
python -m pip install -r requirements.txt
python manage.py bootstrap_data
python manage.py runserver
```

Команда `bootstrap_data`:

- применяет все миграции;
- проверяет, есть ли данные (`references_country`);
- если БД пуста — автоматически загружает `seed.json`;
- если данные уже есть, команда завершится предупреждением (можно принудительно загрузить повторно через `python manage.py bootstrap_data --force`).

Пароли пользователей из фикстуры: `Password123`.

## Фронтенд

```bash
cd frontend
npm install
npm run dev
```

По умолчанию Vite поднимет dev-сервер на `http://localhost:5173`, API слушает `http://127.0.0.1:8000`.

## Проверка после клонирования

1. Клонируй репозиторий.
2. Создай БД и пользователя PostgreSQL.
3. Выполни `python manage.py bootstrap_data`.
4. Зайди в Django admin (`python manage.py runserver`, затем `http://127.0.0.1:8000/admin/`). Пользователь `director` уже является суперпользователем (пароль `Password123`).

## Что делать, если нужно полностью перезаписать данные

```bash
python manage.py flush --no-input
python manage.py bootstrap_data --force
```

## Структура репозитория

```
backend/   # Django проект + фикстуры
frontend/  # React SPA
seed.json  # основная фикстура
README.md  # этот файл
```

Теперь любой разработчик может клонировать проект, запустить `python manage.py bootstrap_data`, и получить полностью заполненную БД без ручных операций. Если нужно раскидать проект по собственному репозиторию, достаточно следовать разделу «Как выложить на GitHub».

