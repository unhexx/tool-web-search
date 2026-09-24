"""Local web_search: offline corpus first, optional self-hosted SearXNG.

Does not call xAI or commercial search APIs. SearXNG is optional and still
self-hosted; set TOOL_OFFLINE=1 to force the local corpus only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
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
            "images": {"type": "boolean", "default": False, "description": "Image hits: corpus field image, or SearXNG categories=images when online"},
            "budget_chars": {
                "type": "integer",
                "description": "Optional cap on the JSON size of results. Snippets shrink, then the lowest-ranked hits drop. URLs stay intact.",
            },
        },
        "required": ["query"],
    },
}


_TRACKING = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
}


def corpus_path() -> Path:
    raw = os.environ.get("WEB_CORPUS")
    if raw:
        return Path(raw)
    local = Path.cwd() / "corpus" / "index.json"
    if local.is_file():
        return local
    return Path("/app/corpus/index.json")


def canonical_url(url: str) -> str:
    if not url or url.startswith("file:"):
        return url
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        return url
    host = parts.hostname.lower() if parts.hostname else parts.netloc.lower()
    if parts.port and not ((parts.scheme == "http" and parts.port == 80) or (parts.scheme == "https" and parts.port == 443)):
        host = f"{host}:{parts.port}"
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _TRACKING
    ]
    query = urlencode(sorted(query_pairs))
    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return urlunsplit((parts.scheme.lower(), host, path, query, ""))


def _chars(rows: list[dict[str, Any]]) -> int:
    return len(json.dumps(rows, ensure_ascii=False, separators=(",", ":")))


def fit_results(results: list[dict[str, Any]], budget_chars: int | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [dict(row) for row in results]
    raw = _chars(rows)
    if budget_chars is None:
        return rows, {"compressed": False, "chars_in": raw, "chars_out": raw}
    if budget_chars < 1:
        raise ValueError("budget_chars must be positive")
    for _ in range(64):
        if _chars(rows) <= budget_chars:
            break
        idx = max(range(len(rows)), key=lambda i: len(str(rows[i].get("snippet") or "")))
        snippet = str(rows[idx].get("snippet") or "")
        if len(snippet) > 24:
            rows[idx]["snippet"] = snippet[: max(16, len(snippet) // 2)].rstrip() + "…"
            continue
        if len(rows) > 1:
            rows.pop()
            continue
        if rows and rows[0].get("snippet"):
            rows[0]["snippet"] = ""
            continue
        break
    out = _chars(rows)
    return rows, {
        "compressed": out < raw or len(rows) < len(results),
        "chars_in": raw,
        "chars_out": out,
        "budget_chars": budget_chars,
        "over_budget": out > budget_chars,
    }


def merge_hits(local: list[dict[str, Any]], remote: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for row in local + remote:
        key = canonical_url(str(row.get("url") or ""))
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        merged.append(row)
        if len(merged) >= limit:
            break
    return merged


def _budget(arguments: dict[str, Any]) -> int | None:
    if arguments.get("budget_chars") is not None:
        return int(arguments["budget_chars"])
    raw = os.environ.get("WEB_CONTEXT_BUDGET_CHARS", "").strip()
    if not raw:
        return None
    return int(raw)


def _corpus() -> list[dict[str, Any]]:
    path = corpus_path()
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _hit(row: dict[str, Any], score: int) -> dict[str, Any]:
    hit: dict[str, Any] = {
        "title": row.get("title") or "",
        "url": row.get("url") or "",
        "snippet": row.get("snippet") or "",
        "score": score,
        "source": "local_corpus",
    }
    if row.get("image"):
        hit["image"] = row["image"]
    return hit


def _local(query: str, limit: int, images: bool) -> list[dict[str, Any]]:
    tokens = [t.lower() for t in query.split() if t]
    hits = []
    for row in _corpus():
        if images and not row.get("image"):
            continue
        blob = " ".join(str(row.get(k, "")) for k in ("title", "url", "snippet", "body", "image")).lower()
        score = sum(1 for t in tokens if t in blob)
        if score:
            hits.append(_hit(row, score))
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
    local = _local(query, limit, images)
    remote: list[dict[str, str]] = []
    remote_error = None
    try:
        remote = _searx(query, limit, images)
    except Exception as exc:  # noqa: BLE001
        remote_error = str(exc)
    merged = merge_hits(local, remote, limit)
    fitted, context = fit_results(merged, _budget(arguments))
    return {
        "query": query,
        "results": fitted,
        "local_hits": len(local),
        "searxng_hits": len(remote),
        "searxng_error": remote_error,
        "offline": os.environ.get("TOOL_OFFLINE", "0") in {"1", "true", "yes"},
        "context": context,
    }


def main() -> None:
    serve(TOOL, SCHEMA, run)


if __name__ == "__main__":
    main()
