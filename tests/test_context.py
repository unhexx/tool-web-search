import json

import pytest

from tool_web_search.server import canonical_url, fit_results, merge_hits, run


def test_canonical_url_strips_tracking_and_slash():
    left = canonical_url("HTTPS://Example.COM/docs/?utm_source=x&b=1&utm_medium=mail")
    right = canonical_url("https://example.com/docs?b=1")
    assert left == right == "https://example.com/docs?b=1"


def test_merge_drops_duplicate_canonical_url():
    local = [{"title": "L", "url": "https://example.com/docs?utm_source=a", "snippet": "local"}]
    remote = [{"title": "R", "url": "https://example.com/docs/", "snippet": "remote"}]
    merged = merge_hits(local, remote, 5)
    assert len(merged) == 1
    assert merged[0]["title"] == "L"


def test_fit_results_shrinks_under_budget():
    rows = [
        {"title": "a", "url": "https://a.example/1", "snippet": "alpha " * 40},
        {"title": "b", "url": "https://b.example/2", "snippet": "beta " * 40},
    ]
    fitted, meta = fit_results(rows, 180)
    assert meta["compressed"] is True
    assert meta["chars_out"] <= 180
    assert fitted[0]["url"] == "https://a.example/1"
    assert "…" in fitted[0]["snippet"] or len(fitted) == 1


def test_offline_corpus_does_not_open_network(tmp_path, monkeypatch):
    idx = tmp_path / "index.json"
    idx.write_text(json.dumps([
        {"title": "FTS", "url": "file://note", "snippet": "local search corpus", "body": "agent tools"}
    ]), encoding="utf-8")
    monkeypatch.setenv("WEB_CORPUS", str(idx))
    monkeypatch.setenv("TOOL_OFFLINE", "1")
    monkeypatch.setenv("SEARXNG_URL", "http://127.0.0.1:9")

    def boom(*_a, **_k):
        raise AssertionError("urlopen")

    monkeypatch.setattr("tool_web_search.server.urlopen", boom)
    out = run({"query": "local search"})
    assert out["local_hits"] == 1
    assert out["searxng_hits"] == 0
    assert out["results"][0]["source"] == "local_corpus"


def test_images_stay_on_corpus_when_offline(tmp_path, monkeypatch):
    idx = tmp_path / "index.json"
    idx.write_text(json.dumps([
        {"title": "note", "url": "file://note", "snippet": "text", "body": "diagram"},
        {"title": "diagram", "url": "file://pic", "snippet": "diagram", "image": "file://pic.png"},
    ]), encoding="utf-8")
    monkeypatch.setenv("WEB_CORPUS", str(idx))
    monkeypatch.setenv("TOOL_OFFLINE", "1")
    monkeypatch.delenv("SEARXNG_URL", raising=False)
    out = run({"query": "diagram", "images": True})
    assert out["local_hits"] == 1
    assert out["results"][0]["image"] == "file://pic.png"
    assert out["searxng_hits"] == 0


def test_default_corpus_from_cwd(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "index.json").write_text(json.dumps([
        {"title": "cwd", "url": "file://cwd", "snippet": "nearby corpus", "body": ""}
    ]), encoding="utf-8")
    monkeypatch.delenv("WEB_CORPUS", raising=False)
    monkeypatch.setenv("TOOL_OFFLINE", "1")
    monkeypatch.chdir(tmp_path)
    out = run({"query": "nearby", "budget_chars": 500})
    assert out["local_hits"] == 1
    assert out["context"]["budget_chars"] == 500
    assert out["context"]["over_budget"] is False


def test_budget_must_be_positive(tmp_path, monkeypatch):
    idx = tmp_path / "index.json"
    idx.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("WEB_CORPUS", str(idx))
    monkeypatch.setenv("TOOL_OFFLINE", "1")
    with pytest.raises(ValueError):
        run({"query": "x", "budget_chars": 0})
