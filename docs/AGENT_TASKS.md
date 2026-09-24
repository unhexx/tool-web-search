# Задачи локальным агентам: tool-web-search

- [ ] T-007 Ротация `secret_key` SearXNG вынести из git в volume при первом старте (скрипт init).

## Закрыто

- [x] T-000 Локальный корпус + отказ от сети при TOOL_OFFLINE=1.
- [x] T-001 Healthcheck сервиса tool бьёт только свой `/healthz`. SearXNG в профиле `searxng` и default `up` его не ждёт.
- [x] T-002 `compose.env.example`: `TOOL_OFFLINE`, `SEARXNG_URL`, `TOOL_TOKEN`, бюджет символов.
- [x] T-003 Дедуп по каноническому URL: схема и хост в нижнем регистре, без tracking-параметров и хвостового слэша.
- [x] T-004 `images=true` в офлайне берёт поле `image` корпуса и не открывает сеть.
- [x] T-005 Тест: при `TOOL_OFFLINE=1` и заданном `SEARXNG_URL` `urlopen` не вызывается.
- [x] T-006 Один SearXNG на машину — см. `docs/DEPLOY.md`.

