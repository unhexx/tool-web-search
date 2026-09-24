# tool-web-search

Local-first web_search. Offline JSON corpus by default. Optional `SEARXNG_URL` for a self-hosted instance (already used by agentic_loop_template operator stack).

Client-side tool for mixing with xAI server-side tools:

https://docs.x.ai/developers/tools/advanced-usage#mixing-server-side-and-client-side-tools

## Local first

Tasks that do not need a third-party network service run entirely in this process.
Bind address is `127.0.0.1` only.

## Dev loop

Две команды. Шаблон лежит рядом (`../agentic_loop_template`) и не копируется в git.
Живой Grok идёт в шлюз `127.0.0.1:8110`, тот спереди pxpipe `127.0.0.1:8100`.
Mock и тесты в модель не ходят.

```bash
./init
./loop --dry-run
./loop
./loop --live
```

`./loop` гоняет mock и в модель не ходит. `./loop --live` стартует только если шлюз и pxpipe отвечают.

Выдачу можно ужать до бюджета символов: аргумент `budget_chars` или `WEB_CONTEXT_BUDGET_CHARS`. URL не режутся, сжимается snippet и отваливается хвост выдачи. Это слой инструмента. pxpipe сжимает уже запрос к модели.

## Run

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q
TOOL_TOKEN=local TOOL_PORT=8094 .venv/bin/python -m tool_web_search.server
```

```bash
docker compose up -d --build
curl -sS http://127.0.0.1:8094/healthz
curl -sS http://127.0.0.1:8094/schema
curl -sS -H 'Authorization: Bearer local' -H 'Content-Type: application/json' \
  -d '{"arguments":{}}' http://127.0.0.1:8094/v1/invoke
```

## xAI client-side schema

`GET /schema` returns the function-calling descriptor. Register it next to any
server-side tools (`web_search`, `x_search`, `code_execution`, …) you still
want xAI to execute. When the model calls this function, execution pauses and
your loop must `POST /v1/invoke`.

## Security

- `no-new-privileges`, `cap_drop: ALL`, read-only root, tmpfs `/tmp`
- published on loopback only
- bearer `TOOL_TOKEN` (default `local` — change before any non-loopback bind)
- SearXNG `secret_key` не в git: его создаёт `deploy/searxng/init-settings.sh` в volume `searxng_data`

Copyright 2026 Evgeniy Chistyakov · https://exception.expert

## Документы для агентов

- [Дизайн](docs/DESIGN.md)
- [Цикл и сжатие контекста](docs/LOOP.md)
- [Очередь задач](docs/AGENT_TASKS.md)
- [AGENTS.md](AGENTS.md)

