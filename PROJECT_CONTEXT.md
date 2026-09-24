# PROJECT_CONTEXT.md

> Source of Truth: `TASK_SPECIFICATION.md`

## Project Identification

| Parameter | Value |
|-----------|-------|
| **Project** | tool-web-search |
| **Goal** | Локальный web_search и цикл разработки в два шага: init, loop |
| **Tech Stack** | Python 3.11+, stdlib HTTP, Agentix (симлинк), pxpipe :8100, шлюз :8110 |
| **Current Branch** | main |

## Current Status

| Field | Value |
|-------|-------|
| **Cycle Number** | 3 |
| **Current Phase** | release |
| **Status** | DONE |
| **Confidence** | 0.9 |

## Key Decisions

- Шаблон не копируем: `./init` делает симлинк на `../agentic_loop_template` (или `AGENTIX_TEMPLATE`).
- Mock и CI не ходят в модель. Живой Grok только через шлюз в pxpipe.
- Сжатие выдачи поиска — обычный бюджет символов в процессе инструмента. pxpipe сжимает запрос к модели, а не JSON SearXNG.

## Permanent Rules

- Незакрытые пункты берутся из `.agent/PLAN.md` и `.agent/TODO.md`.
- Коммиты по-русски, от разработчика. В конце спринта merge в `main` и push.
- Секреты и `.env.agentic` не коммитить.
