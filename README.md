# Agentic Development System

Codex plugin for agentic development governance, Spec Kit-safe project entry,
and machine-readable project documentation.

It helps existing repositories move from prompt-only work to a repeatable agent
loop:

```text
Observe -> Plan -> Act -> Verify -> Update State -> Decide Next Loop
```

## What It Provides

- Repository readiness audit before implementation.
- Mature-project protection and baseline-aware TODO review.
- Spec Kit policy detection with safe `forbidden` / `selective_integration`
  behavior for existing governed projects.
- Machine-readable documentation export from existing Markdown docs.
- Agent governance outputs:
  - `agent-policy.json`
  - `capability-routing.json`
  - `loop-contract.json`
  - `execution-readiness.json`
  - `proposed-agents-md.patch`
- Dry-run-first validation so the plugin can inspect and propose changes
  without modifying the target repository.

## Plugin Layout

```text
.codex-plugin/plugin.json
skills/
scripts/
schemas/
assets/
tests/
.plugin-eval/benchmark.json
```

## Local Installation

Create or update a Codex marketplace file that points at this plugin.

Example marketplace root:

```text
E:\myproject\.agents\plugins\marketplace.json
```

Example entry:

```json
{
  "name": "myproject-local",
  "interface": {
    "displayName": "MyProject Local"
  },
  "plugins": [
    {
      "name": "agentic-development-system",
      "source": {
        "source": "local",
        "path": "./plugin/agentic-development-system"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

Register and install:

```powershell
codex plugin marketplace add E:\myproject
codex plugin add agentic-development-system@myproject-local
codex plugin list --marketplace myproject-local
```

Open a new Codex thread after reinstalling so updated skill metadata is loaded.

## Common Commands

Audit a repository:

```powershell
python scripts\audit_agentic_system.py E:\path\to\repo --json
```

Export machine-readable docs in dry-run mode:

```powershell
python scripts\export_machine_readable_docs.py E:\path\to\repo --output $env:TEMP\agentic-docs --dry-run --json
```

Validate generated docs:

```powershell
python scripts\validate_machine_readable_docs.py $env:TEMP\agentic-docs --json
```

Export agent governance files:

```powershell
python scripts\export_agentic_contract.py E:\path\to\repo --output $env:TEMP\agentic-docs\loop-contract.json
python scripts\export_agent_policy.py E:\path\to\repo --output $env:TEMP\agentic-docs\agent-policy.json
python scripts\export_capability_routing.py E:\path\to\repo --output $env:TEMP\agentic-docs\capability-routing.json
python scripts\export_execution_readiness.py E:\path\to\repo --output $env:TEMP\agentic-docs\execution-readiness.json
python scripts\export_agent_entry_patch.py E:\path\to\repo --output $env:TEMP\agentic-docs\proposed-agents-md.patch
```

Validate execution readiness:

```powershell
python scripts\validate_agent_execution_readiness.py E:\path\to\repo --agentic-dir $env:TEMP\agentic-docs --json
```

## Safety Model

The default workflow is read-only or dry-run.

- Do not write `docs/.agentic/` unless the user explicitly authorizes `--write`.
- Do not apply `proposed-agents-md.patch` automatically.
- Do not run Spec Kit init in mature governed projects.
- Preserve `needs_confirmation` instead of inferring ambiguous work is complete.
- Treat secrets, local profiles, cookies, runtime data, and private evidence as
  out of scope for bootstrap reads.

## Development

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Compile scripts:

```powershell
$scripts = Get-ChildItem .\scripts -Filter *.py -File
python -m py_compile @($scripts | ForEach-Object { $_.FullName })
```

Evaluate the plugin:

```powershell
plugin-eval analyze . --format markdown
plugin-eval benchmark . --config .\.plugin-eval\benchmark.json --format markdown
```

When changing plugin behavior, update `.codex-plugin/plugin.json` with a new
Codex cachebuster version and reinstall:

```powershell
codex plugin add agentic-development-system@myproject-local
```

## Current Status

The plugin has been validated with `plugin-eval` at grade A with no failing or
error checks in the latest local evaluation.
