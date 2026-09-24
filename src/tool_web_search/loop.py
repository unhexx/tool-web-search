"""Второй шаг запуска: роли цикла и супервизор шаблона.

Mock не ходит в модель. --live требует шлюз :8110 и pxpipe :8100.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROLES = ("Design", "Orchestrator", "Coder", "Tester", "Debugger", "Reviewer")
GATEWAY = "http://127.0.0.1:8110/health"


def repo_root() -> Path:
    return Path.cwd()


def plan_path(root: Path) -> Path:
    return root / ".agent" / "PLAN.md"


def supervisor_command(adapter: str, max_cycles: int, create_pr: bool) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "memory.supervisor",
        "run",
        "--adapter",
        adapter,
        "--max-cycles",
        str(max_cycles),
    ]
    if not create_pr:
        cmd.append("--no-pr")
    return cmd


def describe(adapter: str, max_cycles: int, create_pr: bool) -> dict:
    return {
        "roles": list(ROLES),
        "adapter": adapter,
        "proxy": "skip" if adapter == "mock" else "required",
        "pxpipe": "http://127.0.0.1:8100",
        "gateway": "http://127.0.0.1:8110",
        "design_gate": ".agent/PLAN.md",
        "command": supervisor_command(adapter, max_cycles, create_pr),
    }


def proxy_ready(url: str = GATEWAY, timeout: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return False
    if not isinstance(payload, dict) or not payload.get("ok"):
        return False
    if "pxpipe_ok" in payload:
        return bool(payload["pxpipe_ok"])
    pxpipe = payload.get("pxpipe")
    if isinstance(pxpipe, dict) and "ok" in pxpipe:
        return bool(pxpipe["ok"])
    return True


def memory_importable() -> bool:
    try:
        import memory.supervisor  # noqa: F401
    except ImportError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="loop")
    parser.add_argument("--live", action="store_true", help="Адаптер grok через шлюз и pxpipe")
    parser.add_argument("--adapter", default=None)
    parser.add_argument("--max-cycles", type=int, default=1)
    parser.add_argument("--pr", action="store_true", help="Разрешить супервизору открыть PR")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    adapter = args.adapter or ("grok" if args.live else os.environ.get("AGENTIX_LOOP_ADAPTER", "mock"))
    root = repo_root()
    if not plan_path(root).is_file():
        print("Нет .agent/PLAN.md — сначала дизайн и план, затем ./loop", file=sys.stderr)
        return 2
    if args.max_cycles < 1:
        print("max-cycles должен быть >= 1", file=sys.stderr)
        return 2

    summary = describe(adapter, args.max_cycles, args.pr)
    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if adapter != "mock" and not proxy_ready():
        print("Живой адаптер остановлен: шлюз :8110 или pxpipe :8100 не отвечает", file=sys.stderr)
        return 2
    if not memory_importable():
        print("Пакет memory не установлен. Сначала ./init", file=sys.stderr)
        return 2

    print(json.dumps({"roles": summary["roles"], "adapter": adapter, "proxy": summary["proxy"]}, ensure_ascii=False))
    completed = subprocess.run(summary["command"], cwd=root, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
