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

## Пошаговый запуск проекта

### 0. Требования к окружению

- Python 3.11+ (разработка велась на 3.13). На Windows удобнее использовать `py` launcher.
- Node.js 18+ (вместе с npm) для фронтенда.
- PostgreSQL 15+ с доступом к локальному суперпользователю (например, `postgres`).
- Git (при клонировании репозитория), PowerShell или Bash.

Дополнительно убедись, что в `PATH` есть:

- `python`/`py` и `pip`;
- `psql` (CLI клиент PostgreSQL);
- `npm`.

### 1. Клонируй репозиторий

```bash
git clone <repo-url>
cd project_db-main1
```

### 2. Подготовь PostgreSQL и выдай права

1. Подключись к PostgreSQL под суперпользователем (`psql -U postgres` или PgAdmin).
2. Создай БД и роль, выдай все права на БД и схему `public`:

```sql
CREATE DATABASE retail_db;
CREATE USER retail_user WITH PASSWORD 'qweqwe';
GRANT ALL PRIVILEGES ON DATABASE retail_db TO retail_user;
GRANT ALL ON SCHEMA public TO retail_user;
ALTER DATABASE retail_db OWNER TO retail_user; -- опционально, но упрощает поддержку
```

> Если БД уже существовала, удостоверься, что роль `retail_user` может создавать таблицы (`GRANT CREATE ON SCHEMA public`). Настройки подключения заданы в `backend/core/settings.py`.

### 3. Настрой backend

```powershell
cd backend
py -m venv .venv            # python -m venv .venv если нет launcher'а
.\.venv\Scripts\activate    # или source .venv/bin/activate на Linux/macOS
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Пакет `psycopg2-binary` уже включён, поэтому дополнительных билд-инструментов ставить не нужно.

### 4. Прогони миграции и заполни БД

```powershell
python manage.py bootstrap_data          # применит миграции и загрузит seed, если БД пустая
# либо принудительная перезаливка:
python manage.py bootstrap_data --force
```

Что делает команда:

- запускает `migrate`;
- проверяет наличие записей в `references_country`;
- если данных нет — подхватывает `seed.json` (по умолчанию лежит в корне репозитория);
- при наличии данных выводит предупреждение и завершает работу (поэтому `--force` полезен для сброса).

В seed уже заведён суперпользователь `director` с паролем `Password123`.

### 5. Запусти backend-сервер

```powershell
python manage.py runserver 0.0.0.0:8000
```

- API доступно по `http://127.0.0.1:8000`.
- Админка — `http://127.0.0.1:8000/admin/` (логин `director`, пароль `Password123`).
- Для остановки нажми `Ctrl+C` в терминале.

### 6. Настрой и запусти frontend

```powershell
cd ../frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173   # можно опустить параметры, если достаточно localhost
```

Vite поднимет SPA на `http://localhost:5173` (в логе также будет ссылка вида `http://<LAN-IP>:5173/` для доступа с других устройств сети).

### 7. Проверь связку

1. Убедись, что backend слушает порт `8000`, а frontend — `5173`.
2. Открой SPA (`http://localhost:5173`), проверь, что данные подтягиваются из API.
3. Зайди в Django Admin, чтобы подтвердить, что фикстура загрузилась.

### 8. Рекомендуемые доп. утилиты

- **Task Scheduler / cron** — для автоматизации команд `close_work_sessions` и `generate_attendance_report` (подробности ниже).
- **pgAdmin** — для визуальной работы с БД.
- **Postman / HTTPie** — для тестирования API.

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

## Обмен данными с ГК

Справочные данные теперь можно синхронизировать как через API, так и через команды управления.

### Импорт пакета от ГК

```bash
cd backend
python manage.py import_master_data path/to/master_data.json
```

`master_data.json` — JSON с ключами вроде `countries`, `manufacturers`, `products`, `suppliers`, `storage_locations`, `contracts`, `contract_items`, `departments`, `positions`, `roles`, `employees`. Каждый раздел синхронизируется по уникальным кодам/полям (например, страны по `code`, товары по `sku`, сотрудники по `username`).

Через API: `POST /api/hq-sync-jobs/` c телом `{"payload_type": "full", "direction": "inbound", "payload": {...}}`. Запрос создаёт задачу и сразу применяет данные, а ответ содержит статусы и сводку.

### Экспорт локального слепка

```bash
cd backend
python manage.py export_master_data --dataset full --output export.json
```

Поддерживаются датасеты `full`, `products`, `suppliers`, `contracts`, `employees` и т.д. (см. `integration.services.MasterDataExportService`). Команда сохранит JSON и зафиксирует запись об отправке в журнале обмена.

Через API: `GET /api/hq/export/?dataset=full` вернёт текущий слепок и создаст запись о выдаче. Отдельный журнал доступен по эндпоинту `GET /api/hq-sync-jobs/`.

## Приёмка и движение товара

В `inventory` добавлены специализированные сущности и endpoints, которые закрывают регламент из ТЗ.

- `POST /api/receiving-orders/` — создаём заказ на приёмку (ссылка на контракт, склад, дату и т.д.). Поле `code` можно задавать вручную либо использовать генератор на фронте.
- `POST /api/receiving-orders/{id}/start/` — переводит заказ в работу, фиксирует фактическое время прибытия.
- `PATCH /api/receiving-items/{id}/` — указываем реальные параметры партии: количество, даты, зону хранения, цены. Поле `status` переводит позицию в `accepted`, `waiting_hq` или `rejected`.
- `POST /api/receiving-orders/{id}/complete/` — проверяет, что все позиции обработаны, создаёт партии (`ProductBatch`) и приходы (`StockOperation`), увеличивает остатки на соответствующей зоне.
- `POST /api/receiving-discrepancies/` — фиксирует расхождения и, при необходимости, отмечает отправку в ГК (`reported_to_hq`, `hq_ticket`). Решение директора/ГК записывается в `decision`, `decided_by`, `decided_at`.
- `POST /api/product-batches/{id}/move/` — упрощённый сервис перемещения между зонами (склад → торговый зал и т.п.).
- `POST /api/stock-items/{id}/place/` — разложение товаров по полкам/паллетам. Эндпоинт принимает массив `placements` с `shelf_id`, `quantity` и опциональной заметкой.

Все операции логируются в `StockOperation`, а размещение на полках — в `StockPlacement`. Это позволяет прозрачно отслеживать путь товара от ворот до конкретной полки торгового зала.

## Ценообразование и приказ 08:00

1. **Кандидаты цен**. Все потенциальные цены (из ГК, поставщиков, аналитики, локальные расчёты) заносятся в `PriceList` c источником `source`. Для каждого товара/торговой точки может существовать несколько активных записей на одну дату.

2. **Ограничения**.  
   - Точечные лимиты задаются через `PriceRestriction` (наценка, изменение в сутки, флаг автоуценки).  
   - Групповые лимиты для категорий (например, «детское питание» ≤15 % наценки) задаются через `PriceCategoryLimit`.  
   - Значения по умолчанию: 1000 % наценка и 90 % изменения цены в сутки.

3. **Автоприказ**. Директор запускает `POST /api/price-commands/run_daily/` (если дата не передана — берётся сегодня). Сервис:
   - для каждого товара выбирает минимальный прайс среди кандидатов;
   - проверяет ограничения по наценке/изменению цены (уценки с `allow_auto_markdown` могут выйти за лимит суточного изменения);
   - подбирает купон (`Coupon`) по ближайшему сроку годности партии;
   - формирует `PriceCommand` и `PriceCommandItem`, активируя выбранный прайс;
   - если ни одна цена не подходит, записывает причину в `StopListEntry` для передачи в ГК.

4. **Печать ценников.** После выполнения приказа `POST /api/price-commands/{id}/print_labels/` фиксирует момент отправки ценников и купонов в печать (обязательно указывать тип ценника — белый/жёлтый/акционный).

5. **Контроль продаж.** Продажи разрешены только при наличии выполненного приказа на текущую дату. Проверить можно запросом `GET /api/price-commands/?scheduled_for=YYYY-MM-DD&status=executed`.

## Кадровый учёт и отчёты

- **Расписание.** Создай шаблон (`ScheduleTemplate`) с суточными интервалами и привяжи его к сотруднику через `POST /api/employee-schedules/` (по умолчанию — 40 часов в неделю).
- **Быстрый старт.** Команда `python manage.py setup_schedules` создаёт типовые шаблоны («Кладовщик», «Продавец», «Товаровед», «Директор магазина») и назначает их всем активным сотрудникам.
- **Сессии работы.** При входе пользователя в систему создаётся `WorkSession`. Команда `python manage.py close_work_sessions` или API `POST /api/work-sessions/close_overdue/` автоматически закрывает смены, которые не были завершены до полуночи (грейс 5 минут).
- **Отчёт 1 раз в неделю.** В 08:00 понедельника запусти `python manage.py generate_attendance_report` или `POST /api/attendance-reports/generate_weekly/`. Сервис:
  - рассчитывает ожидаемые часы на основании расписания;
  - суммирует фактические WorkSession за неделю;
  - применяет допуск ±30 минут (настраивается) и выдаёт статусы «переработка»/«недоработка»;
  - создаёт строки `AttendanceReportLine` с возможностью корректировки директором (`PATCH /api/attendance-report-lines/{id}/` – поля `approved_hours`, `adjustment_reason`).
- **Подтверждение директором.** После проверки директор отправляет отчёт в работу `POST /api/attendance-reports/{id}/submit/`, а затем подтверждает `POST /api/attendance-reports/{id}/approve/` (с опциональным комментарием). После подтверждения данные доступны для ГК.
- **Отпуска и больничные.** `LeaveRequest` хранит дедлайн подачи документов (7 дней после окончания больничного). Поле `requires_documents` подсказывает, если подтверждение не загружено вовремя, чтобы директор мог пометить дни как недоработку.

### Автоматизация регламентов

**Windows Task Scheduler**

1. Открой `Планировщик заданий` → «Создать задачу…».
2. Для дневного закрытия смен:
   - Триггер: ежедневно, 00:05.
   - Действие: `Program/script` — `C:\Python313\python.exe` (или твой путь)
   - `Add arguments` — `"C:\Users\olegl\OneDrive\Рабочий стол\project_bd\backend\manage.py" close_work_sessions`.
3. Для недельного отчёта:
   - Триггер: еженедельно, понедельник 08:00.
   - Действие: `python "...\manage.py" generate_attendance_report`.

**Linux/macOS cron**

```cron
5 0 * * * /usr/bin/python3 /path/project_bd/backend/manage.py close_work_sessions
0 8 * * MON /usr/bin/python3 /path/project_bd/backend/manage.py generate_attendance_report
```

Убедись, что виртуальная среда активируется (при необходимости заверни команды в shell-скрипт, который сначала вызывает `source .venv/bin/activate`).
backend/   # Django проект + фикстуры
frontend/  # React SPA
seed.json  # основная фикстура
README.md  # этот файл
```

Теперь любой разработчик может клонировать проект, запустить `python manage.py bootstrap_data`, и получить полностью заполненную БД без ручных операций. Если нужно раскидать проект по собственному репозиторию, достаточно следовать разделу «Как выложить на GitHub».

Проверка покрытия ТЗ
Справочники и обмен с ГК — реализованы приложения references, staff, inventory, pricing, integration: модели карточек товаров (все требуемые атрибуты), сотрудников с документами, должностей и ставок, контрагентов/контактных лиц, мест хранения, договоров, грузовиков и т.д. Команда bootstrap_data + сервис MasterDataSyncService/MasterDataExportService обеспечивают загрузку/выгрузку базовых справочников между ТТ и ГК.
Приёмка и движение товара — покрыто моделью ReceivingOrder (этапы плана → фактическое прибытие), ReceivingItem, ReceivingDiscrepancy, сервисом ReceivingWorkflowService и API /api/receiving-orders/*. Есть фиксация несоответствий, создание партий, автоматическая регистрация складских операций, распределение по зонам/полкам, списания, ежемесячные инвентаризации (InventorySession).
Ценообразование / приказ 08:00 — сделаны PriceList c источниками, PriceRestriction и PriceCategoryLimit, сервис DailyPriceCommandService, API POST /api/price-commands/run_daily/, подбор купонов, печать ценников и стоп-лист. Ограничения по наценкам/изменениям цены соблюдаются, уценки с причиной “автоуценка” допускают превышение только по дневному лимиту.
Интеграция (слепок БД и стоп-листы) — GET /api/hq/export/, POST /api/hq-sync-jobs/, стоп-лист формируется автоматически, выгружается для ГК.
Кадровый контур — расписания (ScheduleTemplate, EmployeeSchedule), автозакрытие смен (close_work_sessions), еженедельный отчёт (generate_attendance_report, API attendance-reports/generate_weekly|submit|approve), допуск ±30 минут, контроль отпусков/больничных (LeaveRequest.requires_documents), роли и доступы. Отдельные команды для регламентов документированы в README.
Фронтенд/UX — все страницы (товары, склад, ценообразование, кадры, отчёты) доступны из SPA; применён стеклянный стиль, что не входит в ТЗ, но улучшает визуализацию.
Что ещё проверить вручную
Данные в проде соответствуют seed’у: 3 кладовщика, 4 продавца, 2 товароведа, директор — нужно убедиться, что фикстура seed.json содержит именно их (структура поддерживает).
Скрипты (cron / Task Scheduler) нужно реально завести в окружении, README содержит точные команды; без этого регламенты не запустятся автоматически.
Для “слепка БД за день до открытия” предусмотрен GET /api/hq/export/?dataset=full; при необходимости можно добавить автоматизацию (cron + upload).