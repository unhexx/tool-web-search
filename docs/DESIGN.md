# Дизайн: tool-web-search

## Назначение

Клиентский `web_search` / заготовка `search_images` без xAI server-side search.

Два контура:

1. **Локальный корпус** `corpus/index.json` — всегда, без сети.
2. **SearXNG** — self-hosted метапоиск, профиль compose `searxng`. Это не Google API и не xAI.

## Что такое SearXNG в этом репозитории

SearXNG — самохостный метапоисковик. Он принимает запрос, ходит в настроенные публичные движки и отдаёт агрегированный JSON. Нужен только когда агенту нужны *живые* веб-результаты. По умолчанию профиль выключен (`TOOL_OFFLINE=1`), чтобы цикл разработки не зависел от внешних поисковиков.

SearXNG в этом репо:

- образ `searxng/searxng`
- порт `127.0.0.1:8080`
- JSON включён (`formats: [html, json]`)
- `public_instance: false`, limiter выключен, settings/limiter смонтированы `:ro`
- ключ локальный, не для публичного инстанса

Можно не поднимать свой SearXNG, а указать уже существующий инстанс шаблона `agentic_loop_template` (`SEARXNG_URL=http://127.0.0.1:8080`).

## Архитектура

```
invoke(query)
  -> _local(corpus)                 # всегда
  -> _searx(SEARXNG_URL)            # если URL задан и TOOL_OFFLINE=0
  -> merge по url
```

## План развёртывания

| Режим | Команда | Сеть |
|-------|---------|------|
| Только корпус (CI, агентный цикл) | `docker compose up -d --build` | нет |
| Корпус + SearXNG | `TOOL_OFFLINE=0 docker compose --profile searxng up -d --build` и `SEARXNG_URL=http://searxng:8080` | SearXNG → внешние движки |
| Корпус + SearXNG шаблона | `SEARXNG_URL=http://host.docker.internal:8080 TOOL_OFFLINE=0 docker compose up -d` | как у шаблона |

Не публиковать `:8080` и `:8094` на `0.0.0.0`.

## Когда SearXNG не нужен

Любой поиск по своим файлам, README, заранее собранному индексу — только корпус. Не поднимать SearXNG «на всякий случай».

