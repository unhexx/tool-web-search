import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deploy" / "searxng" / "init-settings.sh"
TEMPLATE = ROOT / "deploy" / "searxng" / "settings.yml"
PLACEHOLDER = "__SEARXNG_SECRET_KEY__"
KEY_RE = re.compile(r'^ {2}secret_key: "([0-9a-f]{64})"$', re.M)


def _run(template: Path, target: Path) -> None:
    env = os.environ.copy()
    env.update({
        "SEARXNG_SETTINGS_TEMPLATE": str(template),
        "SEARXNG_SETTINGS_TARGET": str(target),
        "SEARXNG_INIT_ONLY": "1",
    })
    subprocess.run(["sh", str(SCRIPT)], check=True, env=env)


def test_template_has_placeholder_not_a_committed_key():
    text = TEMPLATE.read_text(encoding="utf-8")
    assert PLACEHOLDER in text
    assert "tool-web-search-local-dev-not-ultrasecretkey" not in text
    assert "ultrasecretkey" not in text
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "settings.yml:/etc/searxng/settings.yml" not in compose
    assert "init-settings.sh" in compose
    assert "searxng_data:/etc/searxng" in compose


def test_init_writes_secret_once_and_keeps_it(tmp_path):
    target = tmp_path / "etc" / "settings.yml"
    _run(TEMPLATE, target)
    first = target.read_text(encoding="utf-8")
    assert PLACEHOLDER not in first
    key = KEY_RE.search(first).group(1)

    custom = tmp_path / "template.yml"
    custom.write_text(TEMPLATE.read_text(encoding="utf-8") + "\n# marker-keep\n", encoding="utf-8")
    _run(custom, target)
    second = target.read_text(encoding="utf-8")
    assert f'secret_key: "{key}"' in second
    assert "marker-keep" in second
    assert PLACEHOLDER not in second


def test_known_committed_key_is_replaced(tmp_path):
    target = tmp_path / "settings.yml"
    target.write_text(
        'server:\n  secret_key: "tool-web-search-local-dev-not-ultrasecretkey"\n',
        encoding="utf-8",
    )
    _run(TEMPLATE, target)
    text = target.read_text(encoding="utf-8")
    assert "tool-web-search-local-dev" not in text
    assert KEY_RE.search(text)
    assert "formats:" in text
