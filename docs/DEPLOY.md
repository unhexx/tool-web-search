# Развёртывание tool-web-search и SearXNG

## Когда поднимать SearXNG

Только если нужен живой веб-поиск. Для корпуса и CI — нет.

```bash
# локальный корпус
docker compose up -d --build

# корпус + SearXNG этого репозитория
export TOOL_OFFLINE=0
export SEARXNG_URL=http://searxng:8080
docker compose --profile searxng up -d --build
curl -sS 'http://127.0.0.1:8080/search?q=test&format=json' | head
curl -sS -H 'Authorization: Bearer local' -H 'Content-Type: application/json' \
  -d '{"arguments":{"query":"agent tools","num_results":3}}' \
  http://127.0.0.1:8094/v1/invoke
```

Если SearXNG уже запущен из `agentic_loop_template` (`127.0.0.1:8080`), второй инстанс не поднимать: задать `SEARXNG_URL=http://host.docker.internal:8080` и работать без профиля `searxng`.

`deploy/searxng/settings.yml` — шаблон без секрета. При старте контейнера `init-settings.sh` подставляет `secret_key` в volume `searxng_data`. Уже записанный ключ (64 hex-символа) сохраняется, остальные поля шаблона накладываются заново. Чтобы сменить ключ, удалите volume. Старый ключ из git больше не используется.

Тот же порт занимает `python -m memory.stack search` в шаблоне. Это один процесс SearXNG на машину, не второй движок. Клиент инструмента и клиент стека ходят в один JSON `/search`. Пример переменных — `compose.env.example`.
