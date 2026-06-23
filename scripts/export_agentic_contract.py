#!/usr/bin/env python3
"""Export the audit result as a machine-readable agent loop contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentic_contract import build_contract
from audit_agentic_system import analyze


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--task-text", default="", help="Optional task text for route classification")
    parser.add_argument("--output", help="Write JSON contract to this file")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    task_text = (args.task_text or "").strip()
    contract = build_contract(root, analyze(root, task_text), task_text)
    payload = json.dumps(contract, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8", newline="\n")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
