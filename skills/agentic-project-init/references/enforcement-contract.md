# Enforcement Contract

Use this reference when upgrading an existing/mature project and adding hard
guardrails. The goal is to keep documentation promises aligned with executable
checks.

## Core Rule

Do not write a hard rule in docs unless the project can verify it.

Hard-rule wording includes:

- must not;
- do not;
- forbidden;
- prohibited;
- unless accepted CR;
- fails if;
- cannot.

If the project cannot enforce the rule, downgrade the wording to a
recommendation or add a documented follow-up.

## Path Guardrails

When a project explicitly forbids parallel SDD artifacts, write a concrete
path set:

```yaml
forbidden_files:
  - docs/STATE.md
forbidden_dirs:
  - agent-os/specs
  - duplicate-specs
```

Use `forbidden_dirs` only when the whole directory tree is forbidden. If the
project only forbids a legacy or duplicate SDD subdirectory, use that exact
subdirectory:

```yaml
forbidden_dirs:
  - agent-os/specs
```

Do not say "do not introduce Agent OS as a tree" while only checking
`agent-os/specs`. Either:

- forbid and check `agent-os`; or
- say only `agent-os/specs` is forbidden.

## Responsibility Matrix

For each default skeleton responsibility, record:

| Field | Meaning |
| --- | --- |
| responsibility | e.g. current state, validation, specs |
| existing_owner | existing canonical file or "none" |
| default_path | default skeleton path |
| action | keep, patch owner, create missing owner, or forbid |
| enforcement | check script, CI, manual review, or none |

Hard `forbid` actions require executable enforcement.

## Consistency Check

Before finishing a mature-project upgrade, compare:

1. paths named as forbidden in `AGENTS.md` and workflow docs;
2. paths checked by the project's documentation check script;
3. paths reported in test/validation docs.

The sets must match. If they do not, fix the docs or the check before claiming
the upgrade is verified.

## Recommended Output

When reporting a mature-project upgrade, include:

- detected scenario;
- responsibility map;
- gap matrix;
- forbidden_files;
- forbidden_dirs;
- enforcement location;
- validation command and result.
