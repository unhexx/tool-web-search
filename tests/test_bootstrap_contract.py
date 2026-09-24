from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_init_is_two_shots():
    init = (ROOT / "init").read_text(encoding="utf-8")
    agent = (ROOT / "Agent-Init.sh").read_text(encoding="utf-8")
    assert "Agent-Init.sh" in init
    assert "pip install -e" in init
    assert "ln -s" in agent
    assert "memory.proxy install-venv" in agent
    assert "AGENTIX_TEMPLATE" in agent
    assert "/agentic_loop_template" in (ROOT / ".gitignore").read_text(encoding="utf-8")


def test_proxy_required_in_config():
    text = (ROOT / ".agent" / "project_config.json").read_text(encoding="utf-8")
    assert '"mode": "required"' in text
    assert "127.0.0.1:8100" in text
    assert "127.0.0.1:8110" in text
