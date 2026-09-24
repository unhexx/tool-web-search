# Настройки

Все настройки — переменные окружения. Файл конфигурации сервис не читает. Пример для compose: [compose.env.example](../compose.env.example). Его копируют в `compose.env` (в git этот файл не входит) и подключают сами, compose автоматически его не подхватывает.

## Сервис

| Переменная | По умолчанию | Смысл |
| --- | --- | --- |
| `TOOL_HOST` | `127.0.0.1` | Адрес `ThreadingHTTPServer`. В compose стоит `0.0.0.0` внутри сети контейнера, наружу проброшен только `127.0.0.1:8094`. |
| `TOOL_PORT` | `8090` | Порт. Compose и README используют `8094`, чтобы не пересечься с другими локальными tool на `8090`. |
| `TOOL_TOKEN` | `local` | Bearer для `POST /v1/invoke`. Пустая строка выключает проверку. |
| `TOOL_OFFLINE` | в коде `0`, в compose `1` | `1`, `true`, `yes` — не вызывать SearXNG. Любое другое значение при заданном `SEARXNG_URL` разрешает сеть. |
| `WEB_CORPUS` | `./corpus/index.json`, если файл есть, иначе `/app/corpus/index.json` | Путь к массиву документов. |
| `SEARXNG_URL` | пусто | База своего инстанса без хвоста `/search`, например `http://127.0.0.1:8080`. Пустое значение — только корпус. |
| `WEB_CONTEXT_BUDGET_CHARS` | пусто | Потолок символов JSON выдачи, если в вызове нет `budget_chars`. Пусто — не сжимать. |

Приоритет бюджета: аргумент `budget_chars` в теле вызова, затем `WEB_CONTEXT_BUDGET_CHARS`.

Таймаут HTTP к SearXNG — 20 секунд. Категория картинок добавляется только при `images=true`.

## Образ и compose

| Параметр | Значение |
| --- | --- |
| Образ tool | Собирается из [Dockerfile](../Dockerfile): `python:3.12-slim-bookworm`, пользователь `tool` uid 10001, `EXPOSE 8094`. |
| Имя образа | `tool-web-search:local`. В Docker Hub не пушится. |
| Лимиты tool | `mem_limit` 256m, `pids_limit` 128, read-only root, tmpfs `/tmp` 64m, `cap_drop: ALL`. |
| Healthcheck tool | `GET http://127.0.0.1:8094/healthz` изнутри контейнера. SearXNG этот check не ждёт. |
| Профиль `searxng` | Образ `docker.io/searxng/searxng:latest`, порт публикации `127.0.0.1:8080:8080`. В `up` без профиля не входит. |
| Volume | `searxng_data` → `/etc/searxng`. Туда попадает живой `settings.yml` с ключом. |
| Шаблон настроек | `deploy/searxng/settings.yml` монтируется только для чтения в `/usr/local/share/tool-web-search/settings.yml`. |
| Limiter | `deploy/searxng/limiter.toml` монтируется в `/etc/searxng/limiter.toml`. |

`SEARXNG_BASE_URL` внутри профиля — `http://127.0.0.1:8080/`. Это адрес, который SearXNG пишет в свои ссылки, не адрес, по которому tool ходит в SearXNG. Для tool из соседнего контейнера нужен `SEARXNG_URL=http://searxng:8080`. Для tool на хосте — `http://127.0.0.1:8080`. Для уже поднятого инстанса шаблона из контейнера tool — `http://host.docker.internal:8080`.

## Ключ SearXNG

Скрипт `deploy/searxng/init-settings.sh` — entrypoint профиля. Он подставляет `secret_key` вместо плейсхолдера `__SEARXNG_SECRET_KEY__`.

| Переменная | По умолчанию | Смысл |
| --- | --- | --- |
| `SEARXNG_SETTINGS_TEMPLATE` | `/usr/local/share/tool-web-search/settings.yml` | Откуда читать шаблон. |
| `SEARXNG_SETTINGS_TARGET` | `/etc/searxng/settings.yml` | Куда писать живой файл. |
| `SEARXNG_SECRET_PLACEHOLDER` | `__SEARXNG_SECRET_KEY__` | Строка, которую надо заменить. |
| `SEARXNG_NEXT_ENTRYPOINT` | `/usr/local/searxng/entrypoint.sh` | Штатный entrypoint образа после подготовки файла. |
| `SEARXNG_INIT_ONLY` | `0` | `1` — записать settings и выйти. Так скрипт проверяют тесты. |

Уже записанный ключ из 64 hex-символов сохраняется, остальные поля шаблона накатываются заново. Ключ другой формы (в том числе старая строка из истории git) при следующем старте заменяется новым. Чтобы сменить устойчивый ключ, volume удаляют.

Генерация: `secrets.token_hex(32)` из Python образа SearXNG, иначе системный `python3`, иначе 32 байта из `/dev/urandom`.

## Цикл

Эти переменные нужны `./init` и `./loop`, не поисковому HTTP.

| Переменная | Смысл |
| --- | --- |
| `AGENTIX_TEMPLATE` | Каталог шаблона, если он лежит не в `../agentic_loop_template`. |
| `AGENTIX_LOOP_ADAPTER` | Адаптер `./loop`, если не передан `--live` и не `--adapter`. По умолчанию `mock`. |
| `GROK_CLI_CHAT_PROXY_BASE_URL` | Пишет `./init` в `activate`: `http://127.0.0.1:8110/v1`. |
| `AGENTIX_PXPIPE_URL` | Пишет `./init` в `activate`: `http://127.0.0.1:8100`. |

`./loop --live` проверяет `http://127.0.0.1:8110/health`: в ответе должны быть `ok` и `pxpipe_ok` (или `pxpipe.ok`). Иначе код выхода 2, публичный fallback не используется.
