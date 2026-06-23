# Document Skeleton

Use these files as the default **governance shim** skeleton. Create missing
files only when no existing equivalent owns the same responsibility.

For existing projects, prefer a responsibility map over filename matching.
Never create a parallel file just because the shim uses a different name.

Spec Kit owns constitution, requirements, plan, tasks, and implementation
artifacts. Do not use this skeleton to create a competing SDD tree.

If documenting hard prohibitions for a mature project, also read
`enforcement-contract.md`. The docs and the executable check must agree on the
exact forbidden paths.

Read `baseline-gate.md` before creating tasks, goals, phase plans, or
cross-validation prompts. Plan-like docs must name their current baseline and
the existing behavior they protect.

## Responsibility Equivalents

| Responsibility | Shim default | Common existing equivalents |
| --- | --- | --- |
| Agent entry contract | `AGENTS.md` | `CLAUDE.md`, `.cursor/rules`, `.github/copilot-instructions.md` |
| Workflow and routing | `docs/AGENTIC_WORKFLOW.md` | `docs/AGENT_WORKFLOW.md`, `docs/CONTRIBUTING.md`, `docs/DEVELOPMENT.md` |
| Current state | `docs/STATE.md` | `docs/CURRENT_STATE.md`, `docs/STATUS.md`, `docs/current-status.md` |
| Decisions | `docs/DECISIONS.md` | `docs/adr/`, `docs/ADR.md`, architecture decision docs |
| Validation | `docs/VALIDATION.md` | `docs/TEST_PLAN.md`, `docs/TEST_RESULTS.md`, CI docs |
| Test results | `docs/TEST_RESULTS.md` | dated validation logs, CI evidence |
| Requirements | Spec Kit | `.specify/memory/constitution.md`, `specs/*/spec.md`, existing PRD/CR docs |
| Plan | Spec Kit | `specs/*/plan.md`, existing technical plans |
| Tasks | Spec Kit or existing tracker | `specs/*/tasks.md`, existing issue tracker, existing `docs/TASKS.md` |
| Standards | project-specific | coding standards, architecture docs, existing `agent-os/standards/` |
| Legacy specs | map only | existing `agent-os/specs/`, existing `specs/` |

## `AGENTS.md`

Purpose: first-read contract for agents.

Required sections:

- Required Reading
- Start Rule
- Spec Kit Policy
- Capability Routing
- Documentation Rule
- Validation Rule
- Sensitive Data Rule
- Existing Work Rule
- Todo Baseline Review Rule when the project has a task tracker, roadmap, CR
  list, phase plan, or any other open TODO system

For mature projects with open TODOs, prefer adding the following concise local
rule to the existing agent-entry file instead of creating new governance docs:

```markdown
## Todo Baseline Review Rule

Before reviewing, generating, reordering, approving, or implementing open
TODOs, compare them against the current main/current worktree baseline.

For each active or next TODO, classify it as current, future, deferred,
Needs Confirmation, operator-gated, historical, duplicate/overlap,
stale/remove, or Needs Baseline.

Do not implement stale, duplicate, old-baseline, or Needs Baseline TODOs.
If a TODO is outdated, propose documentation changes first. Unmerged worktrees
are not mainline facts; rerun the baseline review after merge.
```

## `docs/AGENTIC_WORKFLOW.md`

Purpose: durable operating guide for agentic work.

Required sections:

- Source Of Truth
- Start Of Work
- Spec Kit Policy
- Skill Routing
- Legacy Artifact Mapping
- Decision Records
- Validation And Handoff

## `docs/STATE.md`

Purpose: current state, blockers, and next allowed action.

Do not create this file if an existing `docs/CURRENT_STATE.md` or equivalent
already owns current-state responsibility.

Required sections:

- Current State
- Next Allowed Action
- Blockers
- Recent Verification

## Existing Task Trackers

Do not create `docs/TASKS.md` as a Spec Kit substitute. If a project already
has `docs/TASKS.md`, issues, roadmap, or milestone docs, treat them as the
baseline review target.

When updating tasks, compare against the current baseline and explicitly
rewrite, complete, merge, remove, archive, or demote stale, superseded,
duplicate, historical, conflicting, or old-baseline items.

## `docs/DECISIONS.md`

Purpose: lightweight decision log and index to ADRs.

Create `docs/adr/` when decisions become durable enough to deserve full ADRs.

If the project already has ADRs, add an index or routing note only when needed.

## `docs/VALIDATION.md`

Purpose: define what proof is required before work can be called complete.

## `docs/TEST_RESULTS.md`

Purpose: append dated validation evidence after meaningful changes.

## Legacy `agent-os/`

Do not create `agent-os/product`, `agent-os/specs`, or `agent-os/standards` by
default. If these directories already exist:

- map `agent-os/standards` to implementation context;
- map `agent-os/specs` to historical or per-change context;
- check for conflicts with Spec Kit artifacts;
- preserve existing content unless the user asks for migration;
- do not duplicate requirements, plan, or task ownership.
