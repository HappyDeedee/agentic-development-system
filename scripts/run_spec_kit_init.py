#!/usr/bin/env python3
"""Controlled Spec Kit initializer.

Only `allowed` policy runs automatically. `gated` policy requires
`--confirm-policy gated`. Other policies refuse execution.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from audit_agentic_system import SPEC_KIT_INIT_COMMAND, SPEC_KIT_INIT_COMMAND_WITH_FORCE, analyze, normalize


SKIP_MANIFEST_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
}


def collect_manifest(root: Path) -> list[str]:
    if not root.exists():
        return []
    paths: list[str] = []
    for path in root.rglob("*"):
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in SKIP_MANIFEST_DIRS for part in rel_parts):
            continue
        paths.append(normalize(path, root) + ("/" if path.is_dir() else ""))
    return sorted(set(paths))


def changed_paths(before: list[str], after: list[str]) -> tuple[list[str], list[str]]:
    before_set = set(before)
    after_set = set(after)
    added = sorted(after_set - before_set)
    possible_modified = sorted(before_set & after_set)
    tracked = (
        ".specify/",
        ".agents/",
        "specs/",
        "AGENTS.md",
        "CLAUDE.md",
    )
    modified = [path for path in possible_modified if path.startswith(tracked) or path in tracked]
    return added, modified


def verify_spec_kit_init(root: Path) -> dict[str, object]:
    required = [
        ".specify",
        ".agents/skills/speckit-specify",
        ".specify/workflows/speckit/workflow.yml",
    ]
    missing = [rel for rel in required if not (root / rel).exists()]
    return {
        "ok": not missing,
        "required": required,
        "missing": missing,
    }


def write_manifest(root: Path, manifest: dict[str, object]) -> Path:
    manifest_dir = root / ".specify" / "agentic-development-system"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / "spec-kit-init-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return path


def refuse(message: str, audit: dict[str, object], code: int) -> int:
    print(message)
    print(json.dumps(
        {
            "project_layer": audit.get("project_layer"),
            "spec_kit_policy": audit.get("spec_kit_policy"),
            "spec_kit_policy_reasons": audit.get("spec_kit_policy_reasons"),
            "spec_kit_next_skill": audit.get("spec_kit_next_skill"),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--confirm-policy", default="", help="Required token for gated policy")
    parser.add_argument("--json", action="store_true", help="Print JSON manifest on success")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    audit = analyze(root)
    policy = str(audit["spec_kit_policy"])

    if policy == "already_present":
        return refuse("Refusing Spec Kit init: Spec Kit is already present.", audit, 3)
    if policy in {"forbidden", "unavailable"}:
        return refuse(f"Refusing Spec Kit init: policy is {policy}.", audit, 2)
    if policy == "gated" and args.confirm_policy != "gated":
        return refuse("Refusing Spec Kit init: gated policy requires --confirm-policy gated.", audit, 4)
    if policy not in {"allowed", "gated"}:
        return refuse(f"Refusing Spec Kit init: unsupported policy {policy}.", audit, 2)

    command = list(SPEC_KIT_INIT_COMMAND_WITH_FORCE if policy == "gated" else SPEC_KIT_INIT_COMMAND)
    before = collect_manifest(root)
    started_at = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    after = collect_manifest(root)
    added, modified = changed_paths(before, after)
    verification = verify_spec_kit_init(root)
    manifest: dict[str, object] = {
        "timestamp": started_at,
        "root": str(root),
        "policy": policy,
        "command": command,
        "returncode": completed.returncode,
        "stdout_excerpt": completed.stdout[-4000:],
        "stderr_excerpt": completed.stderr[-4000:],
        "paths_before_count": len(before),
        "paths_after_count": len(after),
        "added_paths": added,
        "modified_or_existing_tracked_paths": modified,
        "verification": verification,
    }

    manifest_path: Path | None = None
    if (root / ".specify").exists():
        manifest_path = write_manifest(root, manifest)
        manifest["manifest_path"] = str(manifest_path)

    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        print(f"Command: {' '.join(command)}")
        print(f"Exit code: {completed.returncode}")
        print(f"Verification ok: {verification['ok']}")
        if manifest_path:
            print(f"Manifest: {manifest_path}")
        if not verification["ok"]:
            print("Missing:")
            for item in verification["missing"]:  # type: ignore[union-attr]
                print(f"- {item}")
    if completed.returncode != 0:
        return completed.returncode
    return 0 if verification["ok"] else 5


if __name__ == "__main__":
    raise SystemExit(main())
