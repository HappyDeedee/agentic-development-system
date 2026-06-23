# Project Scenarios

Use this reference before initializing any non-empty target. The goal is to
model the current project facts before creating or updating the agentic
operating system.

## Core Rule

Empty directories may use the controlled Spec Kit initializer directly when
Spec Kit CLI is ready. Any non-empty target must be audited first. Existing
files are the baseline.

The default development model is **SDD-first hybrid**. Spec Kit owns the main
SDD chain: `$speckit-constitution -> $speckit-specify -> $speckit-plan ->
$speckit-tasks -> $speckit-implement`. TDD is a high-risk implementation
discipline, not the default project identity.

## Project Layer Matrix

Each layer defines only the default action, whether writes are allowed, whether
the user must be asked first, and the recommended capability.

| Layer | Default action | Write allowed | Must ask user | Recommended capability |
| --- | --- | --- | --- | --- |
| `empty_directory` | Use Spec Kit init, then minimal governance shim | Yes | No, when initialization was requested | Spec Kit gated runner |
| `contentful_ungoverned_workspace` | Inventory and model boundary first | Only after inventory | Yes | governance-review |
| `initialized_unscoped_workspace` | Fill missing goal, boundary, validation fields | Patch existing owners only | Yes | baseline-validation |
| `single_repo_code_project` | Audit docs/code/test signals, then propose selective integration | Yes, after scope is clear | Usually yes | code-understanding plus Spec Kit |
| `multi_repo_workspace` | Stop at boundary model and ask user to select target repo | No | Yes | baseline-validation |
| `nested_upstream_repo` | Treat nested repo as separate upstream boundary | No | Yes | baseline-validation |
| `document_or_evidence_workspace` | Protect private inputs and record evidence boundaries | Only metadata/governance | Yes | governance-review |
| `partially_governed_project` | Patch gaps in canonical docs, no parallel skeleton | Yes, after user confirms | Yes | gap patch proposal |
| `mature_governed_project` | Responsibility map and selective integration only | Only canonical-doc patches | Yes for writes | selective integration |

## Scenario Classes

| Scenario | Signals | Initialization mode |
| --- | --- | --- |
| `empty_directory` | No meaningful files or directories | Spec Kit init allowed when CLI is ready |
| `contentful_ungoverned_workspace` | Files or folders exist, but no agentic docs | Inventory first; only thin-safe roots may use gated Spec Kit init |
| `initialized_unscoped_workspace` | Agentic scaffold exists, but goal, requirements, boundary, or validation are still pending | Treat structure as present but implementation blocked |
| `single_repo_code_project` | Root has `.git` and code manifests | Build repo map of docs/code/test signals, then augment |
| `multi_repo_workspace` | Root has multiple nested `.git` directories | Treat root as workspace unless user selects one repo |
| `nested_upstream_repo` | Subdirectory is a cloned upstream project | Do not rewrite upstream governance without explicit scope |
| `document_or_evidence_workspace` | PDFs, docs, screenshots, customer/legal data | Protect sensitive inputs; avoid code assumptions |
| `partially_governed_project` | README/docs/tests exist, but agentic roles are incomplete | Patch gaps without duplicate skeletons |
| `mature_governed_project` | Agent entry, state, tasks, decisions, validation, traceability exist | Responsibility map and minimal patch only |

When multiple scenarios match, choose the most conservative one.

`multi_repo_workspace`, `nested_upstream_repo`, and any workspace with sensitive
signals must default `implementation_readiness` to `false`. They require user
confirmation of the target repository, scan scope, or private-data handling
before implementation or automatic code-understanding scans.

## Boundary Model

Classify the target before writing files:

- `git_repo`: target root is a Git repository.
- `non_git_workspace`: target root is not a Git repository.
- `nested_repos`: one or more child directories are Git repositories.
- `mixed_workspace`: root contains code, docs, private inputs, or nested repos
  with unclear ownership.

Do not cross nested repository boundaries during bootstrap unless the user
explicitly selects that nested repo as the target.

## Readiness Model

Report these readiness dimensions separately:

| Field | Meaning |
| --- | --- |
| `structure_readiness` | Whether agentic entry/state/task/decision/validation files exist |
| `content_readiness` | Whether product goal, boundary, first task, and validation are real |
| `todo_baseline_readiness` | Whether open active/next TODOs have been diffed against current main or the selected baseline and are not stale, duplicate, conflicting, already covered, or only future/deferred |
| `implementation_readiness` | Whether implementation may start without more decisions |

Example:

```text
structure_readiness: scaffolded
content_readiness: low
todo_baseline_readiness: required
implementation_readiness: false
```

Do not call a project mature just because scaffold or Spec Kit files exist. A
workspace with pending mission, pending Git boundary, or no validation path is
not implementation-ready.

Do not recommend scaffold mode or Spec Kit init for `partially_governed_project`
or `mature_governed_project`. Those layers get gap analysis, selective
integration, mapping recommendations, or canonical-doc patch proposals only.

A mature governed project with many open TODOs is also not implementation-ready
for a specific item until that item has passed the Todo Main-Baseline Diff
Audit: owner, current repo evidence, validation entry, clear readiness
classification, and a decision to keep, rewrite, complete, merge, defer,
operator-gate, archive, remove, or mark `Needs Baseline`.

## Blocking Decisions

Stop and report blocking decisions when:

- the root is not a Git repository and nested repositories exist;
- private evidence, secrets, cookies, legal records, or customer data are
  present;
- a nested upstream project could be dependency, fork, reference, or target;
- product mission and first deliverable are unknown;
- open TODOs are being treated as implementation-ready without a TODO versus
  current-main baseline diff;
- stale, duplicate, already-covered, conflicting, or old-baseline TODOs would
  enter implementation instead of being corrected in the canonical task docs;
- existing docs conflict with the requested initialization target;
- implementation is requested before validation can be named.

These are successful initialization findings, not tool failures.
