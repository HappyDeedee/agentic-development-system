# Current Baseline Gate

Use this reference whenever an agent creates or reviews anything that decides
future work. The goal is to prevent old plans, old screenshots, or stale chat
history from rolling back the current project.

## Trigger Points

Run the Current Baseline Gate before:

- creating or updating CRs;
- generating, pruning, or reordering TODOs;
- writing a goal, phase plan, roadmap, or implementation batch;
- generating a `$plan-cross-validation` review brief;
- starting implementation from an existing plan;
- code review, acceptance, or regression review;
- close-out documentation updates.

## Required Baseline Block

Every plan-like artifact should include a short block:

```markdown
## Current Baseline

- Baseline source: current worktree / branch / main / named commit.
- Baseline evidence read:
  - file or page inspected
  - current behavior observed
  - current docs checked
- Existing behavior to preserve:
  - behavior 1
  - behavior 2
- Out of scope / must not redesign:
  - area 1
  - area 2
- Old-baseline conflict rule:
  - If older plans, screenshots, phase docs, or chat conflict with current code
    and accepted current docs, the current baseline wins.
```

Keep the block concrete. Do not write "current baseline checked" without
listing evidence.

## What Counts As Evidence

Prefer evidence from the current repo or worktree:

- `git status`, branch/worktree identity, and recent diff when relevant;
- source files or UI files that own the behavior;
- current docs such as state, tasks, CRs, traceability, test plan, decisions,
  and specialist docs;
- local rendered UI, screenshots, browser checks, tests, or scripts when the
  plan touches UI/runtime behavior;
- current schema or migration state when the plan touches data.

Chat history and old screenshots are context, not baseline evidence.

## Anti-Rollback Review Questions

Before accepting a plan, answer:

1. Is the plan based on current code and current docs?
2. Which existing behavior must survive unchanged?
3. Does the plan import assumptions from an older phase, screenshot, branch, or
   chat thread?
4. Does it reopen completed work instead of creating a follow-up CR?
5. Does it preserve current layout, state, data, and workflow boundaries?
6. Does the validation prove "no rollback", not only "new work exists"?

## Routing

- Use `$speckit-constitution` for project principles or boundaries and
  `$speckit-specify` after the baseline is understood when the requirement
  itself needs specification.
- Use `$plan-cross-validation` to challenge current-baseline freshness for
  high-impact or risky plans.
- Use `$architecture-decision-records` when a baseline conflict requires a
  durable architecture or process decision.
- Use Superpowers after the baseline gate when implementation begins.

Run this gate before moving from one Spec Kit stage to the next whenever the
stage creates future work, changes scope, or approves implementation.

## Output For TODO And Goal Work

When generating TODOs or a goal, include:

- current baseline statement;
- TODO main-baseline diff result when open TODOs are reviewed or changed;
- protected existing behaviors;
- stale or superseded tasks removed or deferred;
- implementation boundary;
- validation that catches rollback.

## Todo Main-Baseline Diff Audit

`Todo Baseline Coverage Audit` is the older compatibility name for this same
gate. Do not interpret it as a form-filling exercise. Run this audit whenever
reviewing, creating, pruning, reordering, or approving a TODO list, roadmap,
phase plan, goal packet, or implementation batch. The audit is required for
mature projects that already have a task tracker.

The core task is to read the semantic diff between open TODOs and the current
main or selected worktree baseline, then repair the TODO system if it no longer
matches reality. Documentation is updated so the corrected baseline is durable,
not to preserve stale TODOs with extra fields.

For mature projects, the durable enforcement point is the target project's own
agent-entry contract, usually `AGENTS.md`. During any mature-project audit,
check whether `AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, or an equivalent entry
file includes a local Todo Baseline Review Rule. If the rule is missing, report
or apply the smallest patch to that file before treating open TODOs as
implementation-ready. The plugin rule alone is not enough because future agents
enter through the project contract.

Recommended local rule:

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

Review every open TODO, not only the theme the user mentioned. For each item,
record or be able to report:

- TODO label, CR/phase/requirement owner, and task location;
- current classification: `active/current`, `future-valid`, `deferred`,
  `Needs Confirmation`, `operator-gated`, `historical/archive-only`,
  `stale/remove`, `duplicate/overlap`, or `Needs Baseline`;
- required action: `keep-as-current`, `rewrite-for-current-baseline`,
  `mark-completed`, `merge-duplicate`, `defer/future`, `operator-gate`,
  `archive/historical`, `remove-stale`, or `Needs Baseline`;
- current project baseline evidence from code, docs, schema, UI, tests,
  runtime evidence, branch/worktree state, or accepted decisions;
- existing behavior that must not regress;
- validation or acceptance entry;
- implementation readiness: ready, blocked, future-only, or not ready.

For each open TODO, answer these review questions before implementation:

1. Does current main or the selected baseline already complete this TODO?
2. Is the TODO based on an old screen, old architecture, old phase plan, old
   branch, old screenshot, or stale chat context?
3. Does the TODO conflict with current behavior, layout, routing, data model,
   permissions, deployment shape, tests, or accepted decisions?
4. Is the TODO a duplicate or overlap of another CR, phase, or follow-up?
5. Does the TODO still have enough current evidence to stay active or next?

Classify an item as `Needs Baseline` when it is open but lacks enough current
project evidence to decide whether it is active, stale, deferred, or ready.
Do not let `Needs Baseline` items enter implementation. First add baseline
evidence, reclassify the item, or move it to a blocked/future/archive section.

If an item is stale, duplicate, already covered, or based on an old baseline,
repair the canonical TODO docs by rewriting it for the current baseline,
marking it complete, merging it into the owning item, deferring it, archiving
it, or removing it. Do not simply add baseline fields to keep an invalid TODO
alive.

Active and next TODOs must have baseline evidence, an owner, and a validation
entry. Backlog, future, deferred, and archive items may have lighter evidence,
but they must be clearly marked as not implementation-ready.

Unmerged worktrees, branches, prototypes, screenshots, or external plans are
not mainline facts. They may be recorded as pending evidence, but if a TODO
depends on them, record a follow-up to rerun the Todo Main-Baseline Diff Audit
after merge instead of treating the unmerged state as current main.

When the project has many TODOs, it is acceptable to report a compact table or
grouped findings, but the review must still cover every open item. Do not
sample only the most visible tasks.

## Output For Cross-Validation

When creating a cross-validation prompt, require the reviewer to compare the
plan against current repo evidence, read the open TODOs and current project
baseline, identify the semantic diff between TODOs and current main or the
selected baseline, and classify stale items as:

- active/current;
- future-valid;
- deferred;
- needs confirmation;
- operator-gated;
- historical/archive-only;
- duplicate/overlap;
- Needs Baseline;
- stale/remove.

Also require a proposed action for each stale or misaligned item:
`rewrite-for-current-baseline`, `mark-completed`, `merge-duplicate`,
`defer/future`, `operator-gate`, `archive/historical`, or `remove-stale`.

The cross-validation request should not merely ask "are docs complete?" It
should explicitly ask whether each active/next TODO still matches the current
code, UI, schema, routes, tests, deployment shape, and accepted decisions, and
what documentation change is needed when it does not.

## Close-Out Rule

After work completes, update the current-state, task, traceability, and test
evidence docs so the new baseline is durable for the next agent.
