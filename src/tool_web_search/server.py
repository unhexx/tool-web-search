"""Local web_search: offline corpus first, optional self-hosted SearXNG.

Does not call xAI or commercial search APIs. SearXNG is optional and still
self-hosted; set TOOL_OFFLINE=1 to force the local corpus only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from tool_http import serve

TOOL = "web_search"
SCHEMA = {
    "type": "function",
    "name": "web_search",
    "description": "Search a local document corpus. If SEARXNG_URL is set and TOOL_OFFLINE is not set, also query a self-hosted SearXNG instance. Never calls xAI web_search.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "num_results": {"type": "integer", "default": 5},
            "images": {"type": "boolean", "default": False, "description": "Image search via SearXNG categories=images"},
        },
        "required": ["query"],
    },
}


def _corpus() -> list[dict[str, str]]:
    path = Path(os.environ.get("WEB_CORPUS", "/app/corpus/index.json"))
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _local(query: str, limit: int) -> list[dict[str, str]]:
    tokens = [t.lower() for t in query.split() if t]
    hits = []
    for row in _corpus():
        blob = " ".join(str(row.get(k, "")) for k in ("title", "url", "snippet", "body")).lower()
        score = sum(1 for t in tokens if t in blob)
        if score:
            hits.append({**{k: row.get(k, "") for k in ("title", "url", "snippet")}, "score": score, "source": "local_corpus"})
    hits.sort(key=lambda r: r["score"], reverse=True)
    return hits[:limit]


def _searx(query: str, limit: int, images: bool) -> list[dict[str, str]]:
    base = os.environ.get("SEARXNG_URL", "").rstrip("/")
    if not base:
        return []
    if os.environ.get("TOOL_OFFLINE", "0") in {"1", "true", "yes"}:
        return []
    params = {"q": query, "format": "json", "pageno": 1}
    if images:
        params["categories"] = "images"
    url = f"{base}/search?{urlencode(params)}"
    with urlopen(url, timeout=20) as resp:  # noqa: S310
        payload = json.loads(resp.read().decode("utf-8"))
    results = []
    for item in (payload.get("results") or [])[:limit]:
        results.append({
            "title": item.get("title") or "",
            "url": item.get("url") or item.get("img_src") or "",
            "snippet": item.get("content") or "",
            "source": "searxng",
        })
    return results


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    query = arguments.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query is required")
    limit = int(arguments.get("num_results") or 5)
    limit = max(1, min(limit, 20))
    images = bool(arguments.get("images"))
    local = _local(query, limit)
    remote: list[dict[str, str]] = []
    remote_error = None
    try:
        remote = _searx(query, limit, images)
    except Exception as exc:  # noqa: BLE001
        remote_error = str(exc)
    merged = local + [r for r in remote if r.get("url") not in {x.get("url") for x in local}]
    return {
        "query": query,
        "results": merged[:limit],
        "local_hits": len(local),
        "searxng_hits": len(remote),
        "searxng_error": remote_error,
        "offline": os.environ.get("TOOL_OFFLINE", "0") in {"1", "true", "yes"},
    }


def main() -> None:
    serve(TOOL, SCHEMA, run)


if __name__ == "__main__":
    main()
