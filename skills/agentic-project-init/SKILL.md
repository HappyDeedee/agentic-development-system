---
name: agentic-project-init
description: Use when entering or initializing a repository before implementation, especially to audit project layer, Spec Kit readiness, mature-project protection, baseline rollback risk, multi-repo or sensitive boundaries, and capability routing.
---

# Agentic Project Init

Use this skill before repository initialization or implementation. It is a
Spec Kit-aware governance shim: audit the project layer, protect mature
projects, prevent old-baseline rollback, and route to the next capability.

Default model: **SDD-first hybrid**. Spec Kit owns
`$speckit-constitution -> $speckit-specify -> $speckit-plan -> $speckit-tasks -> $speckit-implement`.
Use TDD as an implementation discipline for risky or behavioral changes, not
as the default project identity.

## Start

1. Run the read-only audit:

```bash
python <plugin-root>/scripts/audit_agentic_system.py <repo-root> --json
```

2. Report the decision fields that affect the next loop:
   `project_layer`, `implementation_readiness`, `blocking_decisions`,
   `spec_kit_policy`, `spec_kit_next_skill`, `todo_baseline_readiness`,
   `capability_fit_status`, `agent_loop_contract_readiness`, and
   `machine_readable_governance_status`.
3. If the user asked only for analysis, stop after blockers, routing, and the
   next allowed action.
4. If the user asked for a machine-readable handoff, export and validate:

```bash
python <plugin-root>/scripts/export_agentic_contract.py <repo-root> --output agentic-contract.json
python <plugin-root>/scripts/validate_agentic_contract.py agentic-contract.json --json
```

## Reference Routing

Load only the reference needed for the current decision:

| Need | Read |
| --- | --- |
| Non-empty target or layer ambiguity | `references/project-scenarios.md` |
| Capability or Spec Kit stage routing | `references/routing-rules.md` |
| TODOs, goals, phase plans, CRs, reviews | `references/baseline-gate.md` |
| Mature-project hard prohibitions | `references/enforcement-contract.md` |
| Writing governance docs | `references/document-skeleton.md` |
| Code-understanding scope or exclusions | `references/code-understanding.md` |
| Maturity-level ambiguity | `references/maturity-model.md` |

## Spec Kit Policy

Use the gated runner strategy.

| Policy | Action |
| --- | --- |
| `allowed` | Run init only when initialization was requested |
| `gated` | Require explicit `--confirm-policy gated` |
| `already_present` | Do not init; route to `spec_kit_next_skill` |
| `forbidden` | Report mapping, blockers, and selective integration only |
| `unavailable` | Report CLI/install/check blocker |

Read-only plan:

```bash
python <plugin-root>/scripts/plan_spec_kit_integration.py <repo-root> --json
```

Controlled init:

```bash
python <plugin-root>/scripts/run_spec_kit_init.py <repo-root>
```

Gated thin-safe init:

```bash
python <plugin-root>/scripts/run_spec_kit_init.py <repo-root> --confirm-policy gated
```

## Hard Boundaries

- Do not write product code during initialization.
- Do not scaffold `.specify/`, `specs/`, `docs/TASKS.md`, or
  `agent-os/specs` in partial or mature projects.
- Do not overwrite existing docs or create parallel SDD trees.
- Do not treat scaffold files as implementation readiness.
- Do not read private evidence, secrets, cookies, account profiles, legal
  records, customer exports, or local databases for content during bootstrap.
- Do not cross nested Git repository boundaries unless the user selects that
  nested repo as the active target.
- Treat `.agents/` as potentially sensitive; suggest `.gitignore` guidance
  but do not silently edit it in mature projects.

## Decision Loop

Follow this loop and keep each transition evidence-backed:

1. Observe: audit files, docs, boundaries, tests, Spec Kit state, TODOs, and
   sensitive signals.
2. Plan: classify the project layer and choose the smallest allowed route.
3. Act: only run the controlled script or patch canonical docs when policy and
   user intent permit it.
4. Verify: run audit/plan/contract validation and the project-specific checks.
5. Update state: record changed tasks, current state, decisions, validation,
   and traceability when requirements changed.
6. Decide next loop: continue, stop for a decision, or route to the next
   `$speckit-*`, ADR, validation, or implementation capability.

## Done Criteria

The bootstrap or upgrade is done only when the audit policy was followed, the
next allowed action is explicit, existing docs were preserved, validation
evidence has a home, and the exported contract validates when a
machine-readable handoff was requested.
