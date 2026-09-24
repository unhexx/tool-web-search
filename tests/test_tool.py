import json
from tool_web_search.server import run


def test_offline_corpus(tmp_path, monkeypatch):
    idx = tmp_path / "index.json"
    idx.write_text(json.dumps([
        {"title": "FTS", "url": "file://note", "snippet": "local search corpus", "body": "agent tools"}
    ]), encoding="utf-8")
    monkeypatch.setenv("WEB_CORPUS", str(idx))
    monkeypatch.setenv("TOOL_OFFLINE", "1")
    monkeypatch.delenv("SEARXNG_URL", raising=False)
    out = run({"query": "local search"})
    assert out["local_hits"] == 1
    assert out["results"][0]["source"] == "local_corpus"
