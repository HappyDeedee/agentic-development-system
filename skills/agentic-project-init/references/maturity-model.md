# Maturity Model

Use this reference to decide whether the project needs controlled Spec Kit
initialization, a minimal governance shim, or mature-project upgrade behavior.

Default development model: **SDD-first hybrid**. Mature or partial projects
should be helped to adopt spec/requirements-first governance where useful.
Spec Kit owns the main SDD chain. TDD is reserved for concrete implementation
risks. Do not imply a mature project must convert to a new framework before
receiving useful guidance.

## Levels

| Level | Signal | Behavior |
| --- | --- | --- |
| 0: No contract | No `AGENTS.md` or equivalent, few docs | Use Spec Kit init when allowed; add only minimal governance shim |
| 1: Entry contract | `AGENTS.md`, `CLAUDE.md`, or similar exists | Extend missing workflow/state docs only |
| 2: Persistent context | State, tasks, decisions, validation docs exist | Avoid duplicates; patch canonical docs and run Todo Main-Baseline Diff Audit |
| 3: Standards and specs | Standards/specs/requirements/traceability exist | Use responsibility mapping first; do not duplicate Spec Kit artifacts |
| 4: Review and recovery | Cross-validation, test results, handoff records exist | Treat as mature; no blind scaffold; verify open TODOs still match current main before implementation |

## Scenario A: New Or Thin Project

Signals:

- no durable agent entry file;
- no `docs/` directory or only one or two generic docs;
- no current-state or task tracker;
- no decision or validation record;
- no Spec Kit artifacts, specs, or standards.

Action:

- run Spec Kit init when policy is `allowed`;
- require explicit gated confirmation for thin-safe non-empty roots;
- create only minimal governance shim files when needed;
- keep placeholders short and leave unknowns as pending;
- keep implementation readiness false until constitution, spec, plan, tasks,
  and validation evidence are clear.

## Scenario B: Existing Or Mature Project

Signals:

- `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, or equivalent exists;
- `docs/` contains several project documents;
- any current-state, task, change-request, traceability, test-plan,
  test-results, decision, architecture, deployment, or workflow docs exist;
- project docs already define update rules or implementation order.

Action:

- do not create parallel docs by default;
- map existing docs to responsibilities;
- audit open TODOs against current main or the selected worktree baseline
  before calling work implementation-ready;
- rewrite, demote, merge, archive, remove, or mark `Needs Baseline` for TODOs
  that are stale, duplicate, already covered, conflicting, or based on old
  screens, old architecture, old branches, old screenshots, or stale chat;
- identify gaps;
- patch existing canonical docs when the user asked for implementation;
- create new docs only for responsibilities with no existing owner.

## Ambiguity Rule

If the evidence is mixed, treat the project as Scenario B. It is safer to
avoid parallel docs than to scaffold over an existing system.
