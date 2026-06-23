---
name: machine-readable-docs-upgrade
description: Use when converting or auditing repository governance Markdown into machine-readable JSON, especially docs/.agentic exports, schema validation, Markdown-vs-JSON consistency checks, or dry-run migration planning.
---

# Machine Readable Docs Upgrade

Use this skill to turn project governance docs into schema-backed JSON without
rewriting the original Markdown by default.

## Start

Run a dry-run export first:

```bash
python <plugin-root>/scripts/export_machine_readable_docs.py <repo-root> --output <output-dir> --dry-run --json
```

Validate the generated output:

```bash
python <plugin-root>/scripts/validate_machine_readable_docs.py <output-dir> --json
```

Audit Markdown consistency directly from the repo:

```bash
python <plugin-root>/scripts/audit_doc_consistency.py <repo-root> --json
```

For agent-entry governance dry-runs, export the policy, routing, readiness,
loop contract, and proposed entry patch to the same temporary directory:

```bash
python <plugin-root>/scripts/export_agentic_contract.py <repo-root> --output <output-dir>/loop-contract.json
python <plugin-root>/scripts/export_agent_policy.py <repo-root> --output <output-dir>/agent-policy.json
python <plugin-root>/scripts/export_capability_routing.py <repo-root> --output <output-dir>/capability-routing.json
python <plugin-root>/scripts/export_execution_readiness.py <repo-root> --agentic-dir <output-dir> --output <output-dir>/execution-readiness.json
python <plugin-root>/scripts/export_agent_entry_patch.py <repo-root> --output <output-dir>/proposed-agents-md.patch
python <plugin-root>/scripts/validate_agent_execution_readiness.py <repo-root> --agentic-dir <output-dir> --json
```

## Output Contract

Default files:

- `state.json`
- `tasks.json`
- `decisions.json`
- `traceability.json`
- `validation.json`
- `docs-bundle.json`
- `agent-policy.json`
- `capability-routing.json`
- `loop-contract.json`
- `execution-readiness.json`
- `proposed-agents-md.patch`

When writing into a repository, the destination is `docs/.agentic/`. Require
explicit `--write`; otherwise use a temporary or user-selected output
directory.

## Boundaries

- Do not overwrite Markdown.
- Do not apply the proposed `AGENTS.md` patch unless the user explicitly
  authorizes a write/apply step.
- Do not infer completion or verification from ambiguous prose.
- Put uncertain facts in `needs_confirmation`.
- Treat JSON as the machine primary state and Markdown as the human summary.
- Do not implement product features while upgrading docs.

## Done Criteria

The upgrade pass is done when doc export succeeds, governance export succeeds,
validation is valid, consistency warnings are reported, proposed entry changes
are reviewable, and the user has a clear choice between keeping the dry-run
output or explicitly writing `docs/.agentic/` and applying the entry patch.
