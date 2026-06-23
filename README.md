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

## External Capability Routes

This plugin is a governance and routing layer. It does not bundle every large
agentic workflow it can route to. `capability-routing.json` marks each route
with `bundled`, `source`, `dependency_status`, `install_hint`, and `fallback`.

Bundled or built-in:

- `validation`: project-local validation plus this plugin's audit/export/check
  scripts.

External routes to install or provide separately when needed:

- `spec-kit`: install Spec Kit CLI/skills separately and verify `specify` is on
  `PATH` before running Spec Kit stages.
- `superpowers`: install the Superpowers plugin separately, for example
  `codex plugin add superpowers@openai-api-curated` when that marketplace is
  available.
- `plan-cross-validation`: install the `plan-cross-validation` skill if you
  want independent plan/TODO/roadmap review as a first-class route.
- `architecture-decision-records`: install an ADR skill, or use the target
  repository's existing decision-record process.

If an external route is missing, the plugin should not pretend it ran. It
should report the missing dependency, use the route's fallback, or ask the user
to install the capability before continuing.

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

`.plugin-eval/benchmark.json` is kept in the repository as a public evaluation
fixture for plugin maintainers. It is not required at runtime and should not
contain private workspace paths.

## Local Installation

Create or update a Codex marketplace file that points at this plugin.

Example marketplace root:

```text
C:\path\to\your-marketplace\.agents\plugins\marketplace.json
```

Example entry:

```json
{
  "name": "local-agentic-plugins",
  "interface": {
    "displayName": "Local Agentic Plugins"
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
codex plugin marketplace add C:\path\to\your-marketplace
codex plugin add agentic-development-system@local-agentic-plugins
codex plugin list --marketplace local-agentic-plugins
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
codex plugin add agentic-development-system@local-agentic-plugins
```

## Current Status

The plugin has been validated with `plugin-eval` at grade A with no failing or
error checks in the latest local evaluation.
