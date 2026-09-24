# HTTP API

Процесс — `python -m tool_web_search.server` или консольная команда `tool-web-search`. Хост по умолчанию `127.0.0.1`, порт по умолчанию `8090`. Compose и примеры в README задают `TOOL_PORT=8094`.

Ответы — JSON, `Content-Type: application/json; charset=utf-8`.

## Маршруты

| Метод | Путь | Токен | Назначение |
| --- | --- | --- | --- |
| GET | `/healthz`, `/health` | нет | `{"status":"ok","tool":"web_search","mode":"local"}` |
| GET | `/schema` | нет | Дескриптор function calling. |
| POST | `/v1/invoke`, `/invoke` | `Authorization: Bearer <TOOL_TOKEN>` | Выполнить поиск. |

Другой путь — `404` и `{"error":"not_found","path":"..."}`.

## Схема функции

`GET /schema` отдаёт объект, который регистрируют рядом с серверными инструментами xAI. Имя функции — `web_search`. Когда модель её вызывает, серверный цикл останавливается: выполнить поиск должен ваш код через `POST /v1/invoke`.

Параметры:

| Поле | Тип | Обязательно | Поведение |
| --- | --- | --- | --- |
| `query` | string | да | Непустая строка после `strip`. Иначе 400, `query is required`. |
| `num_results` | integer | нет | По умолчанию 5. Значение зажимается в 1…20. |
| `images` | boolean | нет | По умолчанию `false`. В корпусе остаются только строки с непустым `image`. Онлайн-запрос к SearXNG получает `categories=images`. |
| `budget_chars` | integer | нет | Потолок длины JSON массива `results`. Число меньше 1 — ошибка `budget_chars must be positive`. |

## Вызов

Тело — объект. Аргументы читаются из поля `arguments`. Если его нет, аргументами считается всё тело.

```bash
curl -sS -H 'Authorization: Bearer local' -H 'Content-Type: application/json' \
  -d '{"arguments":{"query":"agent tools","num_results":3,"budget_chars":800}}' \
  http://127.0.0.1:8094/v1/invoke
```

Успех, код 200:

```json
{
  "ok": true,
  "tool": "web_search",
  "result": {
    "query": "agent tools",
    "results": [
      {
        "title": "Agentic loop template",
        "url": "https://github.com/unhexx/agentic_loop_template",
        "snippet": "Self-improving agentic loop",
        "score": 1,
        "source": "local_corpus"
      }
    ],
    "local_hits": 1,
    "searxng_hits": 0,
    "searxng_error": null,
    "offline": true,
    "context": {
      "compressed": false,
      "chars_in": 180,
      "chars_out": 180
    }
  }
}
```

Поля хита из корпуса: `title`, `url`, `snippet`, `score` (сколько слов запроса нашлось), `source` = `local_corpus`. Поле `image` появляется только если оно было в строке корпуса. Хит SearXNG: `title`, `url`, `snippet`, `source` = `searxng` (без `score`).

Порядок склейки: сначала локальные хиты, затем SearXNG. Одинаковый канонический URL схлопывается, побеждает локальная строка. Лимит применяется уже к склейке.

`context` без бюджета: `compressed`, `chars_in`, `chars_out`. С бюджетом добавляются `budget_chars` и `over_budget`. Сжатие укорачивает самый длинный snippet (хвост заменяется на `…`), затем выбрасывает последние хиты. URL, title и image не обрезаются. Если один короткий хит всё ещё длиннее бюджета, `over_budget` становится `true`.

Ошибка SearXNG не роняет локальный корпус: `searxng_hits` будет 0, текст исключения ляжет в `searxng_error`. При `TOOL_OFFLINE=1` сетевой вызов не делается, даже если `SEARXNG_URL` задан.

## Ошибки вызова

| Код | Когда | Тело |
| --- | --- | --- |
| 401 | Нет заголовка, нет схемы `Bearer`, токен не совпал. | `{"ok":false,"error":"missing bearer token"}` или `invalid bearer token` |
| 400 | Пустой запрос, аргументы не объект, `budget_chars` < 1, тело больше 2 000 000 байт, битый JSON. | `{"ok":false,"error":"...","trace":"..."}` |
| 404 | Неизвестный путь. | `{"error":"not_found","path":"..."}` |

Пустой `TOOL_TOKEN` отключает проверку. Для loopback-разработки оставлен дефолт `local`. Перед bind не на `127.0.0.1` токен задают явно.

`trace` в ответе 400 обрезан до последних 1500 символов. Наружу этот порт не публикуют.
