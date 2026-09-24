import json

from tool_web_search.loop import describe, main, proxy_ready


def test_dry_run_lists_every_role(capsys):
    assert main(["--dry-run"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["roles"] == [
        "Orchestrator",
        "Coder",
        "Tester",
        "Debugger",
        "Reviewer",
    ]
    assert payload["adapter"] == "mock"
    assert payload["proxy"] == "skip"
    assert "--no-pr" in payload["command"]


def test_live_dry_run_requires_proxy_in_the_plan(capsys):
    assert main(["--dry-run", "--live"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["adapter"] == "grok"
    assert payload["proxy"] == "required"
    assert "8100" in payload["pxpipe"]


def test_describe_matches_command():
    plan = describe("mock", 1, False)
    assert plan["command"][-1] == "--no-pr"


def test_missing_plan_stops(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["--dry-run"]) == 2
    assert "PLAN.md" in capsys.readouterr().err


def test_proxy_ready_false_on_closed_port(monkeypatch):
    monkeypatch.setattr("tool_web_search.loop.GATEWAY", "http://127.0.0.1:9/health")
    assert proxy_ready("http://127.0.0.1:9/health", timeout=0.3) is False
