#!/usr/bin/env python3
"""Export machine-readable agent policy for a repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentic_governance import build_agent_policy, build_context


def write_or_print(payload: dict[str, object], output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output:
        path = Path(output).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8", newline="\n")
    else:
        print(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--task-text", default="", help="Optional task text for route classification")
    parser.add_argument("--output", help="Write agent-policy.json to this file")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    audit, contract = build_context(root, (args.task_text or "").strip())
    write_or_print(build_agent_policy(root, audit, contract), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
