# Routing Rules

Route by lifecycle stage, project layer, decision type, and risk.

Default model: **SDD-first hybrid**. Spec Kit owns the main SDD chain, and TDD
is reserved for risky or concrete implementation. BDD and DDD are optional
project choices, not default outputs of this plugin.

## Spec Kit Chain

| Stage | Use | Owns |
| --- | --- | --- |
| Principles and project constraints | `$speckit-constitution` | Constitution, governance boundaries, non-goals |
| Requirement definition | `$speckit-specify` | Requirements, user stories, acceptance criteria |
| Technical planning | `$speckit-plan` | Architecture approach, data/API/test strategy, risks |
| Task breakdown | `$speckit-tasks` | Implementable task list from the accepted plan |
| Implementation | `$speckit-implement` | Execution after gates are clear |

The plugin routes to these stages. It does not duplicate them with
`agent-os/specs`, `docs/TASKS.md`, or another generated SDD tree.

## Core Routing

| Situation | Use | Owns | Does Not Own |
| --- | --- | --- | --- |
| Project principles or non-negotiable governance are missing | `$speckit-constitution` | Constitution and boundaries | Task execution |
| Requirement is new, unclear, or product-shaping | `$speckit-specify` | Requirements and acceptance | Project coding standards |
| Technical approach needs design | `$speckit-plan` | Plan, risks, validation strategy | Durable ADR replacement |
| Task split is needed after an accepted plan | `$speckit-tasks` | Work breakdown | Reopening requirements silently |
| Implementation is ready | `$speckit-implement` plus Superpowers as needed | Execution discipline | Baseline or governance proof |
| Durable technical or product decision is made | `$architecture-decision-records` | Context, decision, consequences, status | Task tracking |
| Plan is risky or high impact | `$plan-cross-validation` | Independent read-only critique | Routine low-risk coding |
| Existing Agent OS artifacts exist | Responsibility mapping | Legacy/context mapping | New default SDD source |

## Spec Kit Policy Routing

| Policy | Route |
| --- | --- |
| `allowed` | Controlled Spec Kit init may run when initialization was requested |
| `gated` | Require explicit confirmation token before runner executes |
| `already_present` | Do not init; route to `spec_kit_next_skill` |
| `forbidden` | Output mapping, blockers, and selective integration advice |
| `unavailable` | Report CLI/install/check blocker |

## Capability Routing Check

For partial or mature projects, check whether the existing agent entry or
workflow docs name the capability and its trigger before claiming routing is
covered. A workflow file that exists but does not explain when to use
Superpowers, `$plan-cross-validation`, `$speckit-*`, ADRs, and safe
code-understanding is only partial routing.

Also check whether a routed capability is bundled with this plugin or external.
This plugin provides the governance/audit/export layer, but it does not bundle
large external workflows. `capability-routing.json` must expose `bundled`,
`source`, `dependency_status`, `install_hint`, and `fallback` for each route.
If an external route is missing, report the installation hint or use the
fallback instead of claiming the external capability ran.

| Capability | Bundled here | Route source | Install guidance |
| --- | --- | --- | --- |
| Spec Kit | No | external CLI/skills | Install Spec Kit separately and verify `specify` is on `PATH` |
| Superpowers | No | external plugin | Install `superpowers`, for example `codex plugin add superpowers@openai-api-curated` when available |
| plan-cross-validation | No | external skill | Install the skill before using it as an independent review route |
| architecture-decision-records | No | external skill/process | Install an ADR skill or use the target project's existing decision log |
| validation | Yes | project tests plus plugin scripts | Use project-local checks and this plugin's validation scripts |

Before any routing decision that creates or reviews future work, apply the
Current Baseline Gate in `baseline-gate.md`.

Before routing an open TODO into implementation, apply the Todo Main-Baseline
Diff Audit in `baseline-gate.md`. Missing baseline evidence routes the item to
`Needs Baseline`, `$speckit-specify`, `$plan-cross-validation`, or an ADR
decision instead of implementation.

For mature projects, first check whether the target `AGENTS.md` or equivalent
agent-entry file contains a Todo Baseline Review Rule. If it is missing, route
to a small documentation-governance patch or produce an explicit patch
suggestion. Do not rely on plugin memory alone for a rule that future project
agents need at entry.

## plan-cross-validation Triggers

Use `$plan-cross-validation` before implementation when the plan includes:

- data migration or durable mutation;
- external side effects;
- credentials, permissions, privacy, security, payment, or account state;
- production or deployment changes;
- cross-module architecture changes;
- irreversible cleanup;
- roadmap or phase restructuring;
- TODO main-baseline diff gaps, stale open tasks, old-baseline rollback risks,
  or unclear implementation readiness;
- unclear acceptance criteria;
- multiple agents or worktrees touching overlapping areas.

The review brief must ask the reviewer to compare the plan against the current
repo/worktree baseline, flag old-baseline rollback risks, and propose whether
misaligned TODOs should be rewritten for the current baseline, marked complete,
merged, deferred, operator-gated, archived, removed, or marked `Needs
Baseline`.

## ADR Triggers

Use `$architecture-decision-records` to create or update an ADR when choosing
or changing:

- architecture shape;
- framework or technology stack;
- persistence model;
- deployment model;
- security, permission, or identity model;
- public API contract;
- long-term integration boundary;
- irreversible simplification, migration, or deprecation.

## Legacy Agent OS Boundary

When Spec Kit and Agent OS artifacts both exist:

1. Spec Kit is the SDD source of truth.
2. Existing Agent OS standards may remain implementation context.
3. Existing Agent OS specs may be mapped to Spec Kit artifacts or preserved as
   historical implementation notes.
4. Do not create new Agent OS product/spec trees as the default initializer.
5. Do not redefine requirement boundaries in both places.

## Superpowers Boundary

Superpowers governs how implementation proceeds. It does not replace:

- source-of-truth docs;
- Spec Kit artifacts;
- ADRs;
- independent high-risk review;
- project-specific validation records.
