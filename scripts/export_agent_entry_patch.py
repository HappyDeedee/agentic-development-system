#!/usr/bin/env python3
"""Export a proposed AGENTS.md patch without applying it."""

from __future__ import annotations

import argparse
from pathlib import Path

from agentic_governance import build_agent_entry_patch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".", help="Repository root")
    parser.add_argument("--output", help="Write proposed patch to this file")
    args = parser.parse_args()

    patch = build_agent_entry_patch(Path(args.repo_root).resolve())
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(patch, encoding="utf-8", newline="\n")
    else:
        print(patch, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
