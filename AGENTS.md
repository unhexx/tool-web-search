# AGENTS.md — tool-web-search

## Project Goal

Локальный `web_search`: офлайн-корпус и опциональный свой SearXNG. Цикл разработки — соседний Agentix, живые вызовы модели идут через шлюз `:8110` в pxpipe `:8100`.

## Current Status

Каркас продукта 1.0.0 на `main`. Цикл ставится двумя командами: `./init`, затем `./loop`.

## Recommended Stack (do not deviate without an ADR)

- Language / runtime: Python 3.11+
- Package manager: pip, venv в `.venv`
- Tests: `.venv/bin/pytest -q`
- Lint / types: нет отдельного линтера; pytest — ворота

## Exact Commands

```bash
./init
./loop
.venv/bin/pytest -q
TOOL_TOKEN=local TOOL_PORT=8094 .venv/bin/python -m tool_web_search.server
```

`./loop` по умолчанию гоняет mock-адаптер (оркестратор → кодер → тестер → ревьюер, отладчик если тесты красные). Живой Grok через pxpipe: `./loop --live`.

## Definition of Done (any feature)

- [ ] Схема `/schema` и реализация — один источник, без второй копии контракта
- [ ] Тест на изменение; весь `pytest` зелёный
- [ ] README обновлён, если изменились команды или форма ответа
- [ ] В git нет секретов, токенов и сырых персональных данных
- [ ] Один логический коммит на задачу, по-русски, обычным голосом разработчика

## Boundaries — NEVER

- Коммитить `.env`, `.env.agentic`, токены и приватные ключи
- Копировать дерево `agentic_loop_template/` в этот репозиторий
- Ходить в коммерческие поисковые API или в xAI web_search из этого процесса
- Слушать не на loopback в локальном запуске
- Пускать живой адаптер мимо pxpipe (`AGENTIX_PROXY=0` только осознанно)

## Preferred Development Loop

1. `./init` один раз на машине (симлинк на `../agentic_loop_template`, editable install, proxy в `activate`)
2. Прочитать `TASK_SPECIFICATION.md` и `.agent/PLAN.md`
3. Узкий срез, тест, `pytest`
4. `./loop` проверяет цепочку ролей; `./loop --live` — только когда шлюз и pxpipe отвечают
5. В конце спринта — merge в `main` и push

Промпты ролей лежат в шаблоне: `agentic_loop_template/prompts/short_orchestrator_prompt.md`.
