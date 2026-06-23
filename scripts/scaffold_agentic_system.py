#!/usr/bin/env python3
"""Create a minimal Spec Kit-aware governance shim.

The scaffold creates missing files only and never overwrites existing content.
It is intended for empty or thin ungoverned projects only. It does not create
parallel Spec Kit, Agent OS product, or Agent OS specs trees.
"""

from __future__ import annotations

import argparse
from pathlib import Path


GOVERNANCE_SIGNALS = (
    "AGENTS.md",
    "CLAUDE.md",
    ".github/copilot-instructions.md",
    "docs/AGENTIC_WORKFLOW.md",
    "docs/AGENT_WORKFLOW.md",
    "docs/CURRENT_STATE.md",
    "docs/STATE.md",
    "docs/TASKS.md",
    "docs/CHANGE_REQUESTS.md",
    "docs/DECISIONS.md",
    "docs/TRACEABILITY.md",
    "docs/TEST_PLAN.md",
    "docs/TEST_RESULTS.md",
    ".specify",
    "specs",
)

THIN_SAFE_FILES = {".gitignore", "README.md", "readme.md"}


FILES = {
    "AGENTS.md": """# Agent Guide

This file is the entry contract for AI coding agents working in this project.
Treat durable project documents and Spec Kit artifacts as the source of truth.
Do not rely on chat history alone.

## Development Model

Default to SDD-first hybrid development.

Spec Kit owns the main SDD chain:

1. `$speckit-constitution`
2. `$speckit-specify`
3. `$speckit-plan`
4. `$speckit-tasks`
5. `$speckit-implement`

Use TDD during high-risk, behavior-changing, regression-prone, or concrete
implementation stages. Do not treat this project as pure TDD, pure BDD, or
DDD unless the project later chooses that model explicitly.

## Required Reading

Before implementation, read:

1. `.specify/memory/constitution.md` when Spec Kit is present
2. Relevant `specs/*/spec.md`, `plan.md`, and `tasks.md`
3. `docs/AGENTIC_WORKFLOW.md`
4. `docs/STATE.md`
5. `docs/DECISIONS.md`
6. `docs/VALIDATION.md`

## Start Rule

Before changing code or project files:

1. Identify the requested outcome.
2. Identify the selected repository or workspace boundary.
3. Check whether Spec Kit is present or should be initialized.
4. If Spec Kit is absent, run the read-only planner before initialization:
   `python <plugin-root>/scripts/plan_spec_kit_integration.py <repo-root>`.
5. Stop if the planner reports `forbidden`, `unavailable`, multi-repo,
   nested-repo, or sensitive-data blockers.
6. Do not call the project implementation-ready until requirement, plan,
   tasks, and validation evidence are clear.

## Project Layer Routing

- `empty_directory`: Spec Kit init plus minimal governance shim; writes allowed
  when initialization was requested; capability: Spec Kit gated runner.
- `contentful_ungoverned_workspace`: inventory and model boundary first; write
  only after inventory; ask user; capability: governance-review.
- `initialized_unscoped_workspace`: fill missing goal, boundary, and validation
  fields in existing owners; patch existing owners only; ask user; capability:
  baseline-validation.
- `single_repo_code_project`: audit docs/code/test signals, then propose
  selective integration; write after scope is clear; usually ask user;
  capability: code-understanding plus Spec Kit.
- `multi_repo_workspace`: stop and ask the user to select the active repo; no
  writes; capability: baseline-validation.
- `nested_upstream_repo`: treat nested repo as separate upstream boundary; no
  writes; capability: baseline-validation.
- `document_or_evidence_workspace`: protect private inputs and record evidence
  boundaries; metadata/governance writes only; ask user; capability:
  governance-review.
- `partially_governed_project`: patch canonical docs only, no parallel
  skeleton; write after confirmation; capability: gap patch proposal.
- `mature_governed_project`: responsibility map and selective integration
  only; canonical-doc patches only; ask user for writes; capability:
  selective integration.

## Capability Routing

- Use `$speckit-constitution` for project principles and non-negotiable
  boundaries.
- Use `$speckit-specify` for requirements, user stories, and acceptance.
- Use `$speckit-plan` for technical approach and validation strategy.
- Use `$speckit-tasks` for task breakdown.
- Use `$speckit-implement` after the project is implementation-ready.
- Use `$architecture-decision-records` for durable architecture, stack, data,
  deployment, or security decisions.
- Use Superpowers for implementation planning, TDD, verification, review, and
  finishing.
- Use `$plan-cross-validation` for risky or high-impact plans before
  implementation.
- Prefer ast-grep for safe local structural code checks when installed and
  scan scope is clear.

## Todo Baseline Review Rule

Before reviewing, generating, reordering, approving, or implementing open
TODOs, compare them against the current main/current worktree baseline.

For each active or next TODO, classify it as current, future, deferred,
Needs Confirmation, operator-gated, historical, duplicate/overlap,
stale/remove, or Needs Baseline.

Do not implement stale, duplicate, old-baseline, or Needs Baseline TODOs.
If a TODO is outdated, propose documentation changes first. Unmerged worktrees
are not mainline facts; rerun the baseline review after merge.

## Sensitive Data Rule

Never commit secrets, credentials, tokens, cookies, private keys, production
data, local databases, or environment-specific runtime files.
Treat customer records, legal materials, screenshots, cookies, account
profiles, and exported private documents as sensitive unless the user
explicitly selects them.

## Existing Work Rule

The worktree may contain user changes. Do not revert or overwrite work you did
not make.
""",
    "docs/AGENTIC_WORKFLOW.md": """# Agentic Workflow

## Source Of Truth

Spec Kit artifacts own the main SDD chain when present:

`constitution -> spec -> plan -> tasks -> implement`.

This project-level shim owns entry routing, mature-project protection,
baseline rollback prevention, sensitive-data boundaries, multi-repo gates, and
capability routing. It does not replace Spec Kit.

## Start Of Work

Before implementation, identify the requested outcome, governing artifacts,
current state, next allowed action, validation requirements, and blockers.

For non-empty targets, treat existing files as the baseline. Confirm the
working boundary before editing: root repository, nested repository, workspace
docs, private evidence workflow, or a new project area.

## Spec Kit Policy

- `allowed`: empty directory, CLI ready, no boundary or sensitive blockers.
- `gated`: thin-safe directory only, requires explicit confirmation token.
- `already_present`: use the next `$speckit-*` skill instead of init.
- `forbidden`: partial, mature, multi-repo, nested, or sensitive workspace.
- `unavailable`: CLI missing, check failed, or required init flags missing.

Use `scripts/plan_spec_kit_integration.py` for read-only planning and
`scripts/run_spec_kit_init.py` only when the policy permits it.

## Skill Routing

- `$speckit-constitution`: principles, governance constraints, project
  non-goals, and protected boundaries.
- `$speckit-specify`: requirements, user stories, acceptance criteria.
- `$speckit-plan`: technical plan, data/API/test strategy, risks.
- `$speckit-tasks`: task breakdown.
- `$speckit-implement`: implementation once gates are clear.
- `$architecture-decision-records`: durable technology, data, deployment,
  security, permission, API, or maintenance decisions.
- Superpowers: implementation planning, TDD, verification, review, and
  finishing discipline.
- `$plan-cross-validation`: independent read-only critique for high-impact or
  risky plans before implementation.
- ast-grep: safe structural code search when installed and target scope is
  selected.

## Legacy Artifact Mapping

If `agent-os/`, `docs/TASKS.md`, or legacy specs already exist, map them to
Spec Kit responsibilities instead of duplicating them. Existing Agent OS
standards may remain implementation context; they are not the SDD source of
truth when Spec Kit is active.

## Validation And Handoff

Record dated validation evidence in `docs/TEST_RESULTS.md`. Work is complete
only when implementation, checks, and docs agree.
""",
    "docs/STATE.md": """# State

## Current State

Minimal Spec Kit-aware governance shim was created. Spec Kit initialization,
product mission, first implementation goal, repository boundary, and
validation path may still be pending.

Implementation readiness: false.

## Next Allowed Action

Run the read-only Spec Kit integration planner. If policy is `allowed`, run the
controlled Spec Kit initializer. If policy is `gated`, get explicit
confirmation before using the runner.

## Blockers

- Spec Kit project status may be pending.
- Product mission and first deliverable may be pending.
- Repository or workspace boundary may be pending.
- Validation path may be pending.

## Recent Verification

Governance shim files were created. Run the agentic audit after edits and
record the result in `docs/TEST_RESULTS.md`.
""",
    "docs/DECISIONS.md": """# Decisions

Record durable decisions here. Use `docs/adr/` for full ADRs when a decision
affects architecture, stack, data, deployment, security, API contracts, or
long-term maintenance.
""",
    "docs/VALIDATION.md": """# Validation

A task is complete only when implementation, checks, and documentation state
agree.

## Required Proof By Scope

- Agentic docs: run the agentic audit, confirm required files exist, and update
  `docs/TEST_RESULTS.md`.
- Spec Kit init: run the controlled runner and inspect the generated manifest.
- Code repository work: run relevant tests and checks from that repository
  root.
- Local evidence or document analysis: record source files reviewed, outputs
  produced, and extraction limitations without exposing private content.
- External integrations: verify credentials, callback URLs, network access,
  and dry-run behavior before claiming readiness.

## Completion Rule

Do not claim work is complete when only planning has changed. The validation
evidence must match the requested outcome.
""",
    "docs/TEST_RESULTS.md": """# Test Results

Record dated validation results here.
""",
    "docs/adr/.gitkeep": "",
}


def existing_top_level_entries(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {
        path.name
        for path in root.iterdir()
        if path.name not in {".DS_Store", "Thumbs.db"}
    }


def collect_nested_repositories(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [
        git_dir.parent
        for git_dir in root.rglob(".git")
        if git_dir.is_dir() and git_dir.parent != root
    ]


def collect_scaffold_blockers(root: Path) -> tuple[list[str], list[Path], set[str]]:
    existing_top_level = existing_top_level_entries(root)
    governance_hits = [rel for rel in GOVERNANCE_SIGNALS if (root / rel).exists()]
    nested_repos = collect_nested_repositories(root)
    unsafe_content = existing_top_level - THIN_SAFE_FILES - {".git"}
    return governance_hits, nested_repos, unsafe_content


def print_scaffold_refusal(
    governance_hits: list[str],
    nested_repos: list[Path],
    unsafe_content: set[str],
) -> None:
    print("Refusing scaffold: target is not empty/thin.")
    if governance_hits:
        print("Governance or Spec Kit signals:")
        for item in governance_hits:
            print(f"  {item}")
    if nested_repos:
        print("Nested repositories:")
        for item in nested_repos:
            print(f"  {item}")
    if unsafe_content:
        print("Existing content:")
        for item in sorted(unsafe_content):
            print(f"  {item}")
    print("Run audit_agentic_system.py first and use selective integration.")


def write_scaffold_files(root: Path) -> tuple[list[str], list[str]]:
    created: list[str] = []
    skipped: list[str] = []
    for rel_path, content in FILES.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            skipped.append(rel_path)
            continue
        path.write_text(content, encoding="utf-8", newline="\n")
        created.append(rel_path)
    return created, skipped


def print_scaffold_result(created: list[str], skipped: list[str]) -> None:
    print("Created:")
    for item in created:
        print(f"  {item}")
    print("Skipped existing:")
    for item in skipped:
        print(f"  {item}")
    print("Implementation readiness: false")
    print("Next: run plan_spec_kit_integration.py and follow the Spec Kit policy.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    governance_hits, nested_repos, unsafe_content = collect_scaffold_blockers(root)
    if governance_hits or nested_repos or unsafe_content:
        print_scaffold_refusal(governance_hits, nested_repos, unsafe_content)
        return 2

    created, skipped = write_scaffold_files(root)
    print_scaffold_result(created, skipped)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
