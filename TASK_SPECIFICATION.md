# TASK_SPECIFICATION.md — tool-web-search

**Project:** tool-web-search
**Version Target:** 1.1.0
**Primary Goal:** Две команды поднимают рабочий цикл ролей, а живые вызовы модели идут через pxpipe.

## Business Objectives

- `./init` ставит соседний Agentix, venv и прокси в `activate` без копирования дерева шаблона.
- `./loop` проводит роли Design → Orchestrator → Coder → Tester → Debugger → Reviewer и завершается на mock без сети.
- `./loop --live` не стартует, если шлюз `:8110` или pxpipe `:8100` молчит.
- Поиск остаётся локальным: корпус и опциональный свой SearXNG, без коммерческих API.

## Scope

**In scope:** bootstrap цикла, команда `loop`, бюджет контекста на выдаче поиска, путь к корпусу по умолчанию для запуска без Docker, релиз 1.1.0.
**Out of scope:** вендоринг `memory/`, второй pxpipe для agy, публикация наружу за loopback, платный поиск.

## Success Criteria

- `./init` печатает `INIT_OK`, `python -c "import memory"` работает из `.venv`.
- `./loop --dry-run` показывает цепочку ролей и команду supervisor.
- `./loop` с mock-адаптером заканчивается статусом ревьюера DONE.
- `pytest` зелёный.
- Релиз 1.1.0 опубликован на GitHub с `main`.

Передачи между ролями — JSON по схеме шаблона `HANDOFF_SCHEMA.md`.
