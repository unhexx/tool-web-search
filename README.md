# tool-web-search

Локальный клиентский `web_search`: сначала JSON-корпус, при необходимости — свой SearXNG. Коммерческий поиск и server-side search xAI этот процесс не вызывает.

Local-first client tool. Offline corpus by default, optional self-hosted SearXNG, loopback only.

[![Release](https://img.shields.io/github/v/release/unhexx/tool-web-search?display_name=tag&label=release)](https://github.com/unhexx/tool-web-search/releases/latest)
[![Tests](https://img.shields.io/github/actions/workflow/status/unhexx/tool-web-search/test.yml?branch=main&label=tests)](https://github.com/unhexx/tool-web-search/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-3110/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Bind](https://img.shields.io/badge/bind-127.0.0.1-blue)](docs/DEPLOY.md)
[![Stdlib](https://img.shields.io/badge/deps-stdlib-lightgrey)](pyproject.toml)

Смешивается с серверными инструментами xAI как клиентская функция: модель останавливается на вызове, ваш цикл делает `POST /v1/invoke`. Схема: [Mixing server-side and client-side tools](https://docs.x.ai/developers/tools/advanced-usage#mixing-server-side-and-client-side-tools).

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Что возвращает поиск](#что-возвращает-поиск)
- [Корпус](#корпус)
- [Свой SearXNG](#свой-searxng)
- [Цикл разработки](#цикл-разработки)
- [Безопасность](#безопасность)
- [Документация](#документация)

## Быстрый старт

Нужен Python 3.11+. Зависимостей у пакета нет, `pytest` ставится только для разработки.

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q
TOOL_TOKEN=local TOOL_PORT=8094 .venv/bin/python -m tool_web_search.server
```

В другом терминале:

```bash
curl -sS http://127.0.0.1:8094/healthz
curl -sS http://127.0.0.1:8094/schema
curl -sS -H 'Authorization: Bearer local' -H 'Content-Type: application/json' \
  -d '{"arguments":{"query":"agent tools","num_results":3}}' \
  http://127.0.0.1:8094/v1/invoke
```

Тот же сервис в контейнере слушает только loopback. По умолчанию `TOOL_OFFLINE=1`, наружу он не ходит.

```bash
docker compose up -d --build
curl -sS http://127.0.0.1:8094/healthz
```

Образ собирается локально (`tool-web-search:local`), в реестр не публикуется. Внутри контейнера порт задаёт compose: `8094`. Без `TOOL_PORT` процесс из исходников слушает `8090` на `127.0.0.1`.

Команды консоли после установки пакета: `tool-web-search` и `tool-web-search-loop`.

## Что возвращает поиск

`POST /v1/invoke` с телом `{"arguments":{...}}`. Обязателен `query`. `num_results` режется в диапазон 1…20, по умолчанию 5.

| Аргумент | Смысл |
| --- | --- |
| `query` | Строка запроса. Пустая строка — ошибка 400. |
| `num_results` | Сколько хитов оставить после склейки. |
| `images` | `true`: из корпуса только строки с полем `image`. В онлайне SearXNG получает `categories=images`. |
| `budget_chars` | Потолок размера JSON выдачи. Сначала ужимается самый длинный snippet, затем отваливается хвост. URL не режутся. |

Тот же потолок можно задать окружением `WEB_CONTEXT_BUDGET_CHARS`. Аргумент вызова сильнее переменной.

Успешный ответ: `{"ok": true, "tool": "web_search", "result": {...}}`. В `result` лежат `results`, счётчики `local_hits` и `searxng_hits`, `searxng_error`, флаг `offline` и объект `context` (`chars_in`, `chars_out`, `compressed`, `over_budget`).

Полная таблица маршрутов, коды ошибок и пример тела — в [docs/API.md](docs/API.md).

## Корпус

Файл по умолчанию — `./corpus/index.json`, если он есть. Иначе `/app/corpus/index.json`. Свой путь: `WEB_CORPUS`.

Строка — объект с полями `title`, `url`, `snippet`, `body`. Картинка — необязательное поле `image`. Совпадение считается по вхождению слов запроса в эти поля. Подробности и правила канонического URL — в [docs/CORPUS.md](docs/CORPUS.md).

## Свой SearXNG

Живой метапоиск выключен, пока `TOOL_OFFLINE` равен `1`, `true` или `yes`. Чтобы включить его, поставьте `TOOL_OFFLINE=0` и `SEARXNG_URL`.

Один SearXNG на машину. Если порт `127.0.0.1:8080` уже занят стеком `agentic_loop_template`, второй контейнер не поднимают: инструмент смотрит на уже работающий инстанс.

```bash
# свой профиль
TOOL_OFFLINE=0 SEARXNG_URL=http://searxng:8080 \
  docker compose --profile searxng up -d --build

# уже запущенный SearXNG на хосте
TOOL_OFFLINE=0 SEARXNG_URL=http://host.docker.internal:8080 \
  docker compose up -d --build
```

`secret_key` в git не хранится. При первом старте `deploy/searxng/init-settings.sh` пишет ключ в volume `searxng_data` и дальше его не меняет. Смена ключа — удаление volume. Переменные окружения собраны в [docs/CONFIGURATION.md](docs/CONFIGURATION.md), порядок запуска — в [docs/DEPLOY.md](docs/DEPLOY.md).

## Цикл разработки

Шаблон цикла лежит рядом (`../agentic_loop_template`) и в этот репозиторий не копируется. `./init` делает симлинк, venv и editable-установку. `./loop` гоняет mock и в модель не ходит. `./loop --live` стартует только если шлюз `127.0.0.1:8110` отвечает и подтверждает pxpipe на `127.0.0.1:8100`.

```bash
./init
./loop --dry-run
./loop
```

Роли супервизора: Orchestrator, Coder, Tester, Debugger, Reviewer. Дизайн — это файлы `docs/DESIGN.md` и `.agent/PLAN.md`, не шестая роль. Без плана `./loop` завершается с кодом 2.

Решения по сжатию контекста — в [docs/LOOP.md](docs/LOOP.md).

## Безопасность

- Сервис публикуется на `127.0.0.1`. В compose у контейнера `cap_drop: ALL`, `no-new-privileges`, read-only root и tmpfs `/tmp`.
- Вызов требует `Authorization: Bearer <TOOL_TOKEN>`. Значение по умолчанию — `local`. Его меняют до любого bind не на loopback.
- `GET /healthz` и `GET /schema` без токена. Тело `POST` больше 2 МБ отклоняется.
- Офлайн-режим не вызывает `urlopen`, даже если `SEARXNG_URL` задан.
- Поиск не ходит в xAI и в коммерческие API.

## Документация

| Документ | О чём |
| --- | --- |
| [docs/README.md](docs/README.md) | Оглавление |
| [docs/API.md](docs/API.md) | Маршруты, схема, ошибки, пример ответа |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Переменные окружения |
| [docs/CORPUS.md](docs/CORPUS.md) | Формат корпуса и дедуп URL |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Compose и один SearXNG на машину |
| [docs/DESIGN.md](docs/DESIGN.md) | Зачем два контура поиска |
| [docs/LOOP.md](docs/LOOP.md) | `./init`, `./loop`, pxpipe |
| [docs/AGENT_TASKS.md](docs/AGENT_TASKS.md) | Очередь задач |
| [CHANGELOG.md](CHANGELOG.md) | Что вошло в версии |
| [AGENTS.md](AGENTS.md) | Правила для локальных агентов |

Copyright 2026 Evgeniy Chistyakov · https://exception.expert
