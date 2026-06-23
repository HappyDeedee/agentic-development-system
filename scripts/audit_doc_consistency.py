#!/usr/bin/env python3
"""Audit Markdown governance docs against machine-readable export rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from machine_readable_docs import build_docs_bundle, consistency_warnings, schema_errors, validation_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    outputs = build_docs_bundle(repo_root)
    validation = validation_result(repo_root, outputs)
    result = {
        "schema_version": "doc-consistency-audit/v1",
        "repo_root": str(repo_root),
        "valid": validation["valid"],
        "errors": schema_errors(outputs),
        "warnings": consistency_warnings(outputs),
        "needs_confirmation_count": validation["needs_confirmation_count"],
        "source_policy": outputs["docs-bundle.json"]["source_policy"],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Valid: {result['valid']}")
        print(f"Needs confirmation count: {result['needs_confirmation_count']}")
        print("Warnings:")
        for item in result["warnings"]:
            print(f"- {item}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
