#!/usr/bin/env python3
"""Export machine-readable capability routing for a repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentic_governance import build_capability_routing, build_context


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--task-text", default="", help="Optional task text for route classification")
    parser.add_argument("--output", help="Write capability-routing.json to this file")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    audit, _contract = build_context(root, (args.task_text or "").strip())
    payload = json.dumps(build_capability_routing(root, audit), ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8", newline="\n")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
