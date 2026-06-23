#!/usr/bin/env python3
"""Validate dry-run machine-readable governance outputs for a repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentic_governance import validate_governance_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--agentic-dir", required=True, help="Dry-run or future docs/.agentic directory")
    parser.add_argument("--original-agents", help="Optional file containing the expected original AGENTS.md text")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    agentic_dir = Path(args.agentic_dir).resolve()
    original_text = None
    if args.original_agents:
        original_text = Path(args.original_agents).read_text(encoding="utf-8", errors="replace")
    errors, warnings = validate_governance_bundle(repo_root, agentic_dir, original_text)
    result = {
        "schema_version": "agent-execution-readiness-validation/v1",
        "repo_root": str(repo_root),
        "agentic_dir": str(agentic_dir),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Valid: {result['valid']}")
        print("Errors:")
        for item in errors or ["none"]:
            print(f"- {item}")
        print("Warnings:")
        for item in warnings or ["none"]:
            print(f"- {item}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
