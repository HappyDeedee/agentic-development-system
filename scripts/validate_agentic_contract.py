#!/usr/bin/env python3
"""Validate a generated agent loop contract or a project root."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentic_contract import build_contract, validate_contract
from audit_agentic_system import analyze


def load_or_build_contract(target: Path, task_text: str) -> dict[str, object]:
    if target.is_file():
        return json.loads(target.read_text(encoding="utf-8"))
    return build_contract(target, analyze(target, task_text), task_text)


def print_text(result: dict[str, object]) -> None:
    print(f"Valid: {result['valid']}")
    print(f"Contract schema: {result['contract_schema_version']}")
    print("Errors:")
    for item in result["errors"]:  # type: ignore[index]
        print(f"- {item}")
    if not result["errors"]:
        print("- none")
    print("Warnings:")
    for item in result["warnings"]:  # type: ignore[index]
        print(f"- {item}")
    if not result["warnings"]:
        print("- none")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", default=".", help="Project root or contract JSON file")
    parser.add_argument("--task-text", default="", help="Optional task text for route classification")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    contract = load_or_build_contract(target, (args.task_text or "").strip())
    errors, warnings = validate_contract(contract)
    result = {
        "schema_version": "agentic-contract-validation/v1",
        "contract_schema_version": contract.get("schema_version"),
        "target": str(target),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
