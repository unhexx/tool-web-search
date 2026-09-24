# Пять способов встроить цикл и сжатие контекста

Решение к 1.1.0. Сверка: [consumer-starter](https://github.com/unhexx/agentic_loop_template/blob/main/examples/consumer-starter/README.md), [Agent-Init.consumer.sh](https://github.com/unhexx/agentic_loop_template/blob/main/examples/consumer-starter/Agent-Init.consumer.sh), [AGENT_ROLES.md](https://github.com/unhexx/agentic_loop_template/blob/main/AGENT_ROLES.md), [docs/proxy.md](https://github.com/unhexx/agentic_loop_template/blob/main/docs/proxy.md), [pxpipe](https://github.com/teamchong/pxpipe), [спектр контекста](https://agentpatterns.ai/loop-engineering/loop-strategy-spectrum/).

В релиз вошли все пять, в узком виде. Сервис поиска остаётся stdlib, корпус первый, loopback, bearer.

## 1. Цикл рядом с сервисом, не внутри него

`./init` и `./loop` — обёртки. У `memory.supervisor` нет команд `init` и `loop`: есть `run`, `resume`, `status`, `stop`, `run-parallel`.

`./init` вызывает `Agent-Init.sh`: симлинк на `../agentic_loop_template`, `pip install -e`, `python -m memory state init`, адрес шлюза в `activate`. `./loop` вызывает `python -m memory.supervisor run`.

Дерево шаблона и сам pxpipe в git не копируем. Раздел Adaptation в README шаблона до сих пор говорит «скопируй шаблон», а quick start и consumer-starter — «симлинк». Берём симлинк, иначе копия отстаёт.

## 2. Дизайн — файлы на диске, не шестая роль

В контракте пять ролей: Orchestrator, Coder, Tester, Debugger, Reviewer. Отдельной роли Design нет.

Дизайн этого репозитория уже лежит в `docs/DESIGN.md`, `docs/LOOP.md`, `.agent/PLAN.md`, `.agent/TODO.md`. `./loop` не стартует без плана. Исследование копится в этих файлах, а каждый прогон `./loop` читает их заново и делает один ход.

## 3. Свежий ход, холодный старт

Накопление всего чата подходит для синтеза и портится на длинной дистанции. Сжатие внутри сессии годится на средний горизонт и может увести цель. Для правок кода надёжнее чистый ход и состояние на диске.

Поэтому `./loop` не подгружает архивы `.agent`. Cold-start шаблона тот же: снимок состояния, а не дамп на мегабайты. Проваленный ход оставляет на диске последний успешный handoff.

## 4. Сжимать выдачу текстом, не картинкой

pxpipe рисует крупные tool result, старую историю и статичную системную плиту. Свежие реплики и ответ модели остаются текстом. Точные строки (URL, токен, хеш) в картинку класть нельзя: промах читается как уверенная выдумка, а для Grok сжатие картинкой по умолчанию выключено.

Этот инструмент поэтому режет выдачу сам: `budget_chars` / `WEB_CONTEXT_BUDGET_CHARS` укорачивает snippet и сбрасывает хвост, URL не трогает. Картинками поиск не гоняем. Цифры чужих бенчмарков pxpipe на этот корпус не переносим.

## 5. Живой адаптер падает закрытым на тех же портах

Grok → шлюз `127.0.0.1:8110/v1` → pxpipe `127.0.0.1:8100`. Порт `47821` — это собственный quickstart pxpipe, не наша схема.

`proxy.mode=required`. `./loop` (mock) в модель не ходит. `./loop --live` не стартует, если `/health` шлюза не подтвердил pxpipe. `preferred` не включаем: при нём шлюз умеет уйти на публичный fallback. Gemini в юнит `:8100` не добавляем. `deploy/compose.env` шаблона не копируем.

Поиск наружу — только свой SearXNG на `127.0.0.1:8080`, один на машину. Коммерческий поиск, чтобы «накормить» цикл, не подключаем.

## Что не делаем в 1.1.0

- Вендорить `memory/` или pxpipe.
- Включать картиночное сжатие Grok по умолчанию.
- T-007: вынос `secret_key` SearXNG из git. Это отдельная операционная правка.

## Проверка

```bash
./init
./loop --dry-run
./loop
.venv/bin/pytest -q
```

Mock-цикл заканчивается `PR_READY` у ревьюера. `./loop --live` без шлюза завершается с кодом 2.
