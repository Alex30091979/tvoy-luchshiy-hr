# SEO AI Agent — Твой лучший HR (MVP)

Микросервисная система для ежедневной генерации **одной** SEO-статьи под B2B (средний бизнес): Москва 70%, РФ 30%. Темы: подбор офисных специалистов (бухгалтеры, HR, юристы, маркетинг, ассистенты, менеджеры по продажам).

- **Оригинальные тексты**: SERP используется только для анализа структуры/интента, контент генерируется заново.
- **Режимы**: AUTO (автопубликация) и SEMI (черновик + ручное утверждение). Переключение через настройки.
- **Dry-run**: генерация без публикации (по умолчанию включён).

## Стек

- Python 3.12, FastAPI, PostgreSQL, Redis
- Очередь: RQ
- Docker Compose для локального запуска
- Общая библиотека: `libs/common` (конфиг, логи, модели, клиенты, миграции)

## Как запустить

1. Клонировать репозиторий и перейти в каталог проекта.  
   **Важно для Windows:** если при сборке появляется ошибка `x-docker-expose-session-sharedkey contains value with non-printable ASCII characters`, скопируйте проект в путь **только из латиницы** (например `C:\projects\seo-agent`) и запускайте `docker compose` оттуда — путь с кириллицей («Мой диск», «Твой лучший HR» и т.п.) может ломать gRPC Docker Desktop.  
   В PowerShell копирование из текущей папки проекта:
   ```powershell
   New-Item -ItemType Directory -Force -Path C:\projects\seo-agent | Out-Null; Copy-Item -Path .\* -Destination C:\projects\seo-agent -Recurse -Force; cd C:\projects\seo-agent
   ```

2. Запустить все сервисы:
   ```bash
   docker compose up -d --build
   ```

3. Применить миграции и seed (один раз после первого запуска Postgres):
   ```bash
   docker compose run --rm orchestrator-api alembic -c alembic.ini upgrade head
   docker compose run --rm orchestrator-api python -c "from libs.common.seed_data import run_seed; run_seed()"
   ```
   В PowerShell вторую команду лучше задать так (один вызов, без лишних кавычек):
   ```powershell
   docker compose run --rm orchestrator-api python -c "from libs.common.seed_data import run_seed; run_seed()"
   ```
   (У сервиса `orchestrator-api` в compose уже задан `DATABASE_URL_SYNC` для доступа к Postgres.)

4. Админка и API:
   - **Главная**: http://localhost:8000/
   - **OpenAPI**: http://localhost:8000/docs
   - **Health**: http://localhost:8000/health

## Проверка Docker: контейнеры, образы и файлы

Убедиться, что в Docker подняты нужные сервисы и в образе есть нужные файлы:

**1. Список контейнеров и их статус**
```bash
docker compose ps
```
или
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```
Должны быть контейнеры: `postgres`, `redis`, `orchestrator-api`, `scheduler-worker`, `serp-intel`, `content-gen`, `seo-optimizer`, `quality-gate`, `publisher-tilda`, `indexer`, `analytics-tracker`, `linkbuilding`, `cases-gen`. Статус — `Up` (или `running`).

**2. Список образов**
```bash
docker images
```
Должен быть образ проекта (имя папки или `seo-ai-agent`, в зависимости от того, как compose назвал build).

**3. Файлы и процессы внутри контейнера**

Проверить, что в образе скопированы каталоги и конфиг:
```bash
docker compose run --rm orchestrator-api ls -la /app
docker compose run --rm orchestrator-api ls -la /app/libs
docker compose run --rm orchestrator-api ls -la /app/services
```
Ожидаемо в `/app`: `libs`, `services`, `scripts`, `alembic.ini`. В `libs` — `common` с подпапками `models`, `migrations`, `clients`, `schemas` и т.д.

Проверить, что процесс запущен и слушает порт (после `docker compose up -d`):
```bash
docker compose exec orchestrator-api ps aux
```
или зайти в контейнер и посмотреть процессы вручную:
```bash
docker compose exec orchestrator-api sh
# внутри: ps aux, ls /app, exit
```

**4. Логи контейнеров**
```bash
docker compose logs orchestrator-api
docker compose logs scheduler-worker
docker compose logs postgres
```

**5. Сеть и переменные**
```bash
docker compose exec orchestrator-api env | findstr DATABASE
docker network ls
docker network inspect <имя_сети_проекта>
```
Имя сети обычно `..._default` (по имени папки проекта).

## Как проверить генерацию

1. Запустить ежедневную задачу (dry-run, без публикации):
   ```bash
   curl -X POST http://localhost:8000/jobs/run_daily -H "Content-Type: application/json" -d "{\"dry_run\": true}"
   ```
   Ответ: `{"id": 1, "status": "pending", "rq_job_id": "..."}`.

2. Подождать 10–30 секунд. Проверить статус джоба:
   ```bash
   curl http://localhost:8000/jobs/1
   ```
   Ожидаемо: `status: "completed"`, в `result` — `article_id`, `cluster_id`, `published: false` (dry-run).

3. Посмотреть статью:
   ```bash
   curl http://localhost:8000/articles/1
   ```
   Должны быть поля: `title`, `slug`, `status` (pending_approval при SEMI/dry-run), `draft_markdown`, `final_markdown`, `meta_title`, `meta_description`, `quality_scores`.

4. Утвердить статью (перевод в approved/published):
   ```bash
   curl -X POST http://localhost:8000/articles/1/approve -H "Content-Type: application/json" -d "{\"publish\": true}"
   ```

## Где смотреть логи

- **Orchestrator API**: `docker compose logs -f orchestrator-api`
- **Scheduler worker (пайплайн)**: `docker compose logs -f scheduler-worker`
- **Остальные сервисы**: `docker compose logs -f serp-intel`, `content-gen`, `seo-optimizer`, `quality-gate`, `publisher-tilda`, и т.д.

## Сервисы и порты

| Сервис            | Порт (host) | Описание                          |
|-------------------|------------|-----------------------------------|
| orchestrator-api   | 8000       | Настройки, кластеры, статьи, очередь, админка |
| scheduler-worker   | —          | RQ worker, выполняет daily pipeline |
| serp-intel        | 8001       | Анализ SERP (структура/интент), заглушка |
| content-gen       | 8002       | Генерация черновика по brief, заглушка |
| seo-optimizer     | 8003       | Семантика, meta, FAQ, schema      |
| quality-gate      | 8004       | Проверка спама/уникальности       |
| publisher-tilda   | 8005       | Публикация в Tilda (draft/publish), заглушка |
| indexer           | 8006       | GSC/Яндекс (моки)                 |
| analytics-tracker | 8007       | Каркас под показы/клики/позиции   |
| linkbuilding      | 8008       | Реестр площадок + план ссылок    |
| cases-gen         | 8009       | Каркас кейса для заполнения человеком |

У каждого сервиса есть **GET /health**.

## API (минимально)

- **POST /jobs/run_daily** — поставить в очередь ежедневный пайплайн (тело: `{"dry_run": true/false}`).
- **GET/POST /settings** — настройки (в т.ч. `publish_mode`, `dry_run`, `daily_token_quota`).
- **CRUD /clusters** — кластеры и ключевые слова.
- **GET /articles**, **GET /articles/{id}**, **POST /articles/{id}/approve** — статьи и утверждение.

## Настройки (ключи в БД или env)

- `publish_mode`: `auto` | `semi`
- `dry_run`: в env или в настройках — не публиковать даже при auto.
- `daily_token_quota`: лимит токенов в день (пока простая квота, подсчёт токенов — заглушка).

Все внешние интеграции (SERP, LLM, антиплагиат, Tilda, GSC, Яндекс) сделаны через **интерфейсы + заглушки** — MVP запускается без ключей.

## Update Engine (через 6 месяцев)

Заложены таблицы и контракты; интерфейсы для обновления статей пока не реализованы (можно добавить `JobType.UPDATE_ARTICLE` и отдельный пайплайн).

## Event flow (D)

Пайплайн логирует события: `job.created` → `serp.analyzed` → `content.drafted` → `seo.enriched` → `quality.passed` / `quality.failed` → при успехе: `tilda.published` (AUTO) или `tilda.drafted` (SEMI) → далее можно добавить `url.index_requested`, `tracking.scheduled`.

## Админ-терминал (E)

Страница **/admin**: переключатель AUTO/SEMI, лимит статей/день, доля Москва/РФ, список кластеров (вкл/выкл), очередь задач + статус, список статей (draft/published) + кнопка «Опубликовать», просмотр quality-report по последней статье. Настройки сохраняются в БД и применяются без перезапуска (runtime_settings).

## Переменные окружения (F)

См. **.env.example**. Основные: `DB_URL` / `DATABASE_URL_SYNC`, `REDIS_URL`, `MODE` (AUTO|SEMI), `MOSCOW_SHARE`, `ARTICLES_PER_DAY`; опционально ключи API: `SERP_API_KEY`, `LLM_API_KEY`, `ANTI_PLAGIAT_API_KEY`, `TILDA_PUBLIC_KEY`, `TILDA_SECRET_KEY`, `TILDA_PROJECT_ID`. Логи: `LOG_JSON=true` для структурированного JSON (удобно для прод и ротации логов через Docker/systemd).

## Логи: структура и ротация

Логи пишутся в stdout в виде структурированных событий (structlog). При `LOG_JSON=true` вывод в JSON. Ротацию и сбор логов обеспечивает среда (Docker, systemd, или отдельный агент).

## Seed данные

После миграций и seed в БД будут:
- 10 кластеров Москва + 10 кластеров РФ с ключевыми словами;
- настройки по умолчанию: `publish_mode=semi`, `dry_run=true`, `daily_token_quota=100000`, `articles_per_day=1`, `moscow_share=0.7`.

## Устранение неполадок (Docker)

- **Ошибка:** `failed to dial gRPC ... header key "x-docker-expose-session-sharedkey" contains value with non-printable ASCII characters`  
  Часто из‑за **пути к проекту с кириллицей** (например «Мой диск», «Твой лучший HR»). Решение: скопировать проект в папку с путём только из латиницы. В PowerShell (из каталога проекта):
  ```powershell
  New-Item -ItemType Directory -Force -Path C:\projects\seo-agent | Out-Null
  Copy-Item -Path .\* -Destination C:\projects\seo-agent -Recurse -Force
  cd C:\projects\seo-agent
  docker compose up -d --build
  ```

- **Сборка обрывается без явной ошибки**  
  Перезапустить Docker Desktop и повторить `docker compose up -d --build`.

## Git: удалённый репозиторий и коммиты

**Подключить GitHub/GitLab (один раз):**

1. Создайте пустой репозиторий на GitHub или GitLab (без README, без .gitignore).
2. Подставьте его URL в команды и выполните из корня проекта:
   ```bash
   git remote add origin https://github.com/USER/REPO.git
   git branch -M main
   git push -u origin main
   ```
   Или для SSH: `git remote add origin git@github.com:USER/REPO.git`

**Локальные коммиты:**
   ```bash
   git add .
   git status
   git commit -m "Описание изменений"
   git push
   ```
