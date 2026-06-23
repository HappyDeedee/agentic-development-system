#!/usr/bin/env python3
"""Read-only Spec Kit integration planner.

This script reports whether Spec Kit initialization is allowed, gated,
forbidden, already present, or unavailable. It does not write files and does
not run `specify init`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_agentic_system import analyze


def build_plan(root: Path) -> dict[str, object]:
    audit = analyze(root)
    command_plan = audit["spec_kit_command_plan"]
    assert isinstance(command_plan, dict)
    policy_reasons = audit["spec_kit_policy_reasons"]
    assert isinstance(policy_reasons, list)
    blockers: list[str] = []
    if audit["spec_kit_policy"] in {"forbidden", "unavailable"}:
        blockers.extend(str(item) for item in policy_reasons)
    if audit["repo_boundary"] in {"nested_repos", "mixed_workspace"}:
        blockers.append("Select the target repository before initialization.")
    if audit["sensitive_signals"]:
        blockers.append("Confirm sensitive-data boundary before initialization.")
    return {
        "root": str(root),
        "project_layer": audit["project_layer"],
        "repo_boundary": audit["repo_boundary"],
        "sensitive_signals": audit["sensitive_signals"],
        "nested_repos": audit["nested_repos"],
        "spec_kit_cli": audit["spec_kit_cli"],
        "spec_kit_project_status": audit["spec_kit_project_status"],
        "policy": audit["spec_kit_policy"],
        "policy_reasons": policy_reasons,
        "recommended_command": command_plan.get("command", []),
        "expected_write_scope": command_plan.get("expected_write_scope", []),
        "requires_user_confirmation": command_plan.get("requires_user_confirmation", False),
        "confirm_policy_token": command_plan.get("required_token"),
        "force_allowed": audit["spec_kit_force_allowed"],
        "collision_risk": audit["spec_kit_collision_risk"],
        "next_skill": audit["spec_kit_next_skill"],
        "blockers": sorted(set(blockers)),
    }


def print_text(plan: dict[str, object]) -> None:
    print(f"Root: {plan['root']}")
    print(f"Project layer: {plan['project_layer']}")
    print(f"Spec Kit policy: {plan['policy']}")
    print(f"Collision risk: {plan['collision_risk']}")
    print(f"Next skill: {plan['next_skill']}")
    print("Policy reasons:")
    for item in plan["policy_reasons"]:  # type: ignore[union-attr]
        print(f"- {item}")
    print("Recommended command:")
    command = plan["recommended_command"]
    if command:
        print(" ".join(command))  # type: ignore[arg-type]
    else:
        print("- none")
    print("Expected write scope:")
    for item in plan["expected_write_scope"]:  # type: ignore[union-attr]
        print(f"- {item}")
    print("Blockers:")
    blockers = plan["blockers"]
    if blockers:
        for item in blockers:  # type: ignore[union-attr]
            print(f"- {item}")
    else:
        print("- none")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    plan = build_plan(root)
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print_text(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
