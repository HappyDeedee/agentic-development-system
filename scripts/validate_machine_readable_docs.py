#!/usr/bin/env python3
"""Validate machine-readable docs output or build it from a repo root."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from machine_readable_docs import build_docs_bundle, default_agentic_dir, load_output_dir, validation_result


def load_or_build(target: Path) -> dict[str, dict[str, object]]:
    if target.is_dir() and (target / "docs-bundle.json").is_file():
        return load_output_dir(target)  # type: ignore[return-value]
    agentic_dir = default_agentic_dir(target)
    if agentic_dir.is_dir() and (agentic_dir / "docs-bundle.json").is_file():
        return load_output_dir(agentic_dir)  # type: ignore[return-value]
    return build_docs_bundle(target)  # type: ignore[return-value]


def print_text(result: dict[str, object]) -> None:
    print(f"Valid: {result['valid']}")
    print(f"Output count: {result['output_count']}")
    print(f"Needs confirmation count: {result['needs_confirmation_count']}")
    print("Errors:")
    errors = result["errors"]
    for item in errors:  # type: ignore[union-attr]
        print(f"- {item}")
    if not errors:
        print("- none")
    print("Warnings:")
    warnings = result["warnings"]
    for item in warnings:  # type: ignore[union-attr]
        print(f"- {item}")
    if not warnings:
        print("- none")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", default=".", help="Repo root or docs/.agentic output directory")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    outputs = load_or_build(target)
    result = validation_result(target, outputs)  # type: ignore[arg-type]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
