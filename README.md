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

**Где работать с кодом:** основной каталог проекта — `...\Твой лучший HR.SEO-накрутка`. Сборку Docker на Windows из этой папки может ломать путь с кириллицей; тогда копируйте проект в папку только с латиницей (см. ниже) и запускайте `docker compose` оттуда. Исходный код и git по‑прежнему ведите в основной папке.

1. Клонировать репозиторий (или открыть существующий каталог) и перейти в каталог проекта.  
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

## Рабочий каталог и репозитории

**Основной код всегда хранится здесь:**
- `C:\Users\a.ramensky\Мой диск\Google_Scripts\Твой лучший HR.SEO-накрутка` — единственный источник правды: в этой папке правки, коммиты и история.

**GitHub и GitLab** — для деплоя и защиты авторского права (бэкап, даты коммитов):
- Все изменения делайте в папке выше, коммитьте и пушите в удалённые репозитории.
- Деплой: на сервере или в CI делают `git clone` из GitHub/GitLab и собирают/запускают проект; локально для Docker при необходимости клонируют в каталог с путём только из латиницы (например `C:\Projects\seo-agent`).

**Типовой цикл работы:**
   ```bash
   cd "C:\Users\a.ramensky\Мой диск\Google_Scripts\Твой лучший HR.SEO-накрутка"
   git add .
   git status
   git commit -m "Описание изменений"
   git push origin main
   ```
   При добавлении GitLab как второго remote:
   ```bash
   git remote add gitlab https://gitlab.com/USER/REPO.git
   git push -u gitlab main
   ```
   Дальше после каждого коммита можно пушить в оба: `git push origin main && git push gitlab main`.

**Почему коммиты «Unverified» и как сделать Verified**

GitHub показывает «Unverified», если коммит не подписан. Чтобы коммиты были **Verified**:

1. **Подпись коммитов по SSH (рекомендуется)**  
   - Убедитесь, что у вас есть SSH-ключ и он добавлен в GitHub: Settings → SSH and GPG keys.  
   - Включите подписание коммитов этим ключом и укажите его в git:
   ```bash
   git config --global gpg.format ssh
   git config --global user.signingkey "ПУТЬ_К_ПУБЛИЧНОМУ_КЛЮЧУ"
   git config --global commit.gpgsign true
   ```
   Вместо пути к ключу подставьте путь к вашему **публичному** SSH-ключу (например `~/.ssh/id_ed25519.pub` или `C:\Users\USERNAME\.ssh\id_ed25519.pub`).  
   - В GitHub: Settings → SSH and GPG keys → New SSH key → **Signing Key** — вставьте тот же публичный ключ и отметьте «Use for commit signing».  
   - Новые коммиты будут подписаны. Старые коммиты останутся Unverified; при желании можно переписать историю с подписью (`git rebase` и т.п., осторожно при уже запушенной истории).

2. **Подпись коммитов по GPG**  
   - Установите GPG (например [Gpg4win](https://www.gpg4win.org/)), создайте ключ: `gpg --full-generate-key`.  
   - Узнайте ID ключа: `gpg --list-secret-keys --keyid-format long`.  
   - В git: `git config --global user.signingkey ID_КЛЮЧА`, `git config --global commit.gpgsign true`.  
   - Экспорт публичного ключа: `gpg --armor --export ID_КЛЮЧА`, скопируйте вывод.  
   - В GitHub: Settings → SSH and GPG keys → New GPG key — вставьте ключ.  
   - Новые коммиты станут Verified.

После настройки все **новые** коммиты будут отображаться как Verified. Уже существующие коммиты на GitHub не переведутся в Verified автоматически.

## Что делать дальше

1. **Проверить пайплайн из коробки**  
   Код правите в основной папке (`Твой лучший HR.SEO-накрутка`). Для запуска Docker скопируйте проект в папку с латиницей (например `C:\Projects\seo-agent`) или сделайте там `git clone` с GitHub, затем:
   ```powershell
   docker compose up -d --build
   docker compose run --rm orchestrator-api alembic -c alembic.ini upgrade head
   docker compose run --rm orchestrator-api python -c "from libs.common.seed_data import run_seed; run_seed()"
   ```
   Открыть http://localhost:8000/admin, нажать «Запустить ежедневную генерацию», проверить статью в списке и quality report.

2. **Подключить реальные API**  
   Вместо заглушек: выдать ключи SERP, LLM, Tilda (в .env или в настройках), реализовать клиенты в `libs/common/clients/` и в сервисах (serp-intel, content-gen, publisher-tilda).

3. **Автозапуск раз в день**  
   Настроить cron/systemd (на сервере) или RQ Scheduler / отдельный scheduler-сервис, который раз в сутки вызывает `POST /jobs/run_daily`.

4. **Мониторинг и прод**  
   Логи (JSON + ротация), метрики, алерты; вынести конфиг в env; при необходимости — Kubernetes/Helm или отдельные инстансы сервисов.

5. **Через 6 месяцев: Update Engine**  
   Реализовать пайплайн обновления статей (по расписанию или по триггеру), используя заложенные таблицы и `JobType.UPDATE_ARTICLE`.
