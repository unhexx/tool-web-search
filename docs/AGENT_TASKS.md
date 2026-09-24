# Задачи локальным агентам: tool-web-search

- [ ] T-001 Профиль `searxng`: healthcheck tool ждёт `/healthz` SearXNG только если профиль включён (не ломать default up).
- [ ] T-002 Пример `compose.env.example` с `TOOL_OFFLINE`, `SEARXNG_URL`, `TOOL_TOKEN`.
- [ ] T-003 Дедуп результатов по каноническому URL (срезать tracking query).
- [ ] T-004 Режим `images=true` без SearXNG: искать в корпусе поле `image` / локальный каталог, не ходить наружу.
- [ ] T-005 Контрактный тест: offline корпус не вызывает urlopen (mock/guard).
- [ ] T-006 Документировать пересечение с `python -m memory.stack search` шаблона — один инстанс SearXNG на машину.
- [ ] T-007 Ротация `secret_key` SearXNG вынести из git в volume при первом старте (скрипт init).

## Закрыто

- [x] T-000 Локальный корпус + отказ от сети при TOOL_OFFLINE=1.

