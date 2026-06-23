#!/usr/bin/env python3
"""Export project governance Markdown into machine-readable JSON files."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from machine_readable_docs import build_docs_bundle, default_agentic_dir, write_docs_bundle


def resolve_output_dir(repo_root: Path, output: str | None, write: bool) -> Path:
    if write:
        return default_agentic_dir(repo_root)
    if output:
        return Path(output).resolve()
    return Path(tempfile.gettempdir()) / "agentic-machine-readable-docs"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--output", help="Output directory for generated JSON files")
    parser.add_argument("--dry-run", action="store_true", help="Generate files outside docs/.agentic")
    parser.add_argument("--write", action="store_true", help="Write to docs/.agentic under the repository")
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    write = bool(args.write)
    output_dir = resolve_output_dir(repo_root, args.output, write)
    outputs = build_docs_bundle(repo_root)
    written = write_docs_bundle(outputs, output_dir)
    result = {
        "schema_version": "machine-readable-docs-export/v1",
        "repo_root": str(repo_root),
        "mode": "write" if write else "dry-run",
        "output_dir": str(output_dir),
        "written": written,
        "output_count": len(written),
        "repo_docs_modified": write,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Mode: {result['mode']}")
        print(f"Output dir: {output_dir}")
        print("Written:")
        for path in written:
            print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
