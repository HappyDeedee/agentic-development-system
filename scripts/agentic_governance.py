"""Machine-readable agent governance helpers."""

from __future__ import annotations

import difflib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentic_contract import LOOP_ORDER, build_contract
from audit_agentic_system import analyze


GOVERNANCE_FILES = {
    "agent_policy": "agent-policy.json",
    "capability_routing": "capability-routing.json",
    "loop_contract": "loop-contract.json",
    "execution_readiness": "execution-readiness.json",
    "agent_entry_patch": "proposed-agents-md.patch",
}

REQUIRED_CAPABILITIES = (
    "spec-kit",
    "superpowers",
    "plan-cross-validation",
    "architecture-decision-records",
    "validation",
)

AGENT_ENTRY_RULE_TITLE = "Agentic Machine-Readable Governance Rule"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_context(root: Path, task_text: str = "") -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = root.resolve()
    audit = analyze(resolved, task_text)
    contract = build_contract(resolved, audit, task_text)
    return audit, contract


def build_agent_policy(root: Path, audit: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "agent-policy/v1",
        "generated_at": utc_now(),
        "repo_root": str(root.resolve()),
        "machine_readable_entrypoint": "docs/.agentic/agent-policy.json",
        "required_read_order": [
            "docs/.agentic/agent-policy.json",
            "docs/.agentic/capability-routing.json",
            "docs/.agentic/loop-contract.json",
            "docs/.agentic/execution-readiness.json",
            "docs/.agentic/docs-bundle.json",
            "AGENTS.md",
            "docs/GOAL.md",
            "docs/CURRENT_STATE.md",
            "docs/TASKS.md",
            "docs/DECISIONS.md",
            "docs/CHANGE_REQUESTS.md",
            "docs/TRACEABILITY.md",
            "docs/TEST_PLAN.md",
        ],
        "loop_order": list(LOOP_ORDER),
        "execution_boundaries": {
            "implementation_allowed": bool(audit.get("implementation_readiness")),
            "must_stop_when_blocked": True,
            "preserve_needs_confirmation": True,
            "forbid_spec_kit_init_when_policy": ["forbidden"],
            "forbid_unapproved_docs_agentic_write": True,
            "forbid_unapproved_agent_entry_patch": True,
        },
        "current_state": {
            "project_layer": audit.get("project_layer"),
            "implementation_readiness": audit.get("implementation_readiness"),
            "blocking_decisions": list(audit.get("blocking_decisions") or []),
            "spec_kit_policy": audit.get("spec_kit_policy"),
            "capability_fit_status": audit.get("capability_fit_status"),
            "todo_baseline_readiness": audit.get("todo_baseline_readiness"),
        },
        "validation_commands": [
            (
                "python <plugin-root>/scripts/validate_agent_execution_readiness.py "
                "<repo-root> --agentic-dir docs/.agentic --json"
            ),
            "python <plugin-root>/scripts/audit_agentic_system.py <repo-root> --json",
            "python <plugin-root>/scripts/validate_machine_readable_docs.py docs/.agentic --json",
        ],
        "source_contract_schema": contract.get("schema_version"),
    }


def route_policy_for_capability(name: str, audit: dict[str, Any]) -> dict[str, Any]:
    if name == "spec-kit":
        policy = audit.get("spec_kit_policy")
        return {
            "capability": name,
            "status": "available" if audit.get("spec_kit_cli", {}).get("available") else "unavailable",
            "route": "selective_integration" if policy == "forbidden" else audit.get("spec_kit_next_skill"),
            "policy": policy,
            "allowed_actions": ["responsibility_mapping", "route_to_next_skill"],
            "forbidden_actions": ["specify init", "run_spec_kit_init.py"],
            "requires_user_confirmation": policy in {"gated", "allowed"},
            "evidence": list(audit.get("spec_kit_policy_reasons") or []),
        }
    if name == "superpowers":
        return {
            "capability": name,
            "status": "available",
            "route": "implementation_discipline",
            "allowed_actions": ["test-driven-development", "systematic-debugging", "verification-before-completion"],
            "activation_gate": "implementation_readiness must be true and blocking_decisions must be empty",
            "forbidden_actions": ["override source-of-truth docs", "skip validation evidence"],
        }
    if name == "plan-cross-validation":
        return {
            "capability": name,
            "status": "available",
            "route": "independent_read_only_review",
            "triggers": [
                "high-risk plan",
                "roadmap or phase restructuring",
                "TODO baseline gaps",
                "permissions/security/deployment/data migration",
                "unclear acceptance criteria",
            ],
            "forbidden_actions": ["mutate project during review"],
        }
    if name == "architecture-decision-records":
        return {
            "capability": name,
            "status": "available",
            "route": "durable_decision_record",
            "triggers": [
                "architecture shape changes",
                "framework or persistence choices",
                "deployment/security/API contract decisions",
                "irreversible simplification or migration",
            ],
        }
    return {
        "capability": name,
        "status": "available",
        "route": "project_validation",
        "triggers": ["before completion", "after docs or code changes", "before state update"],
        "required_evidence": ["tests or docs checks", "audit output", "traceability update when requirements change"],
    }


def build_capability_routing(root: Path, audit: dict[str, Any]) -> dict[str, Any]:
    routes = [route_policy_for_capability(name, audit) for name in REQUIRED_CAPABILITIES]
    return {
        "schema_version": "capability-routing/v1",
        "generated_at": utc_now(),
        "repo_root": str(root.resolve()),
        "routing_status": audit.get("capability_routing_status"),
        "capability_fit_status": audit.get("capability_fit_status"),
        "required_capabilities": list(REQUIRED_CAPABILITIES),
        "routes": routes,
        "missing_or_unverified_capabilities": list(audit.get("missing_or_unverified_capabilities") or []),
        "slot_recommendations": list(audit.get("capability_slot_recommendations") or []),
    }


def build_execution_readiness(root: Path, audit: dict[str, Any], agentic_dir: str = "docs/.agentic") -> dict[str, Any]:
    blocking_decisions = list(audit.get("blocking_decisions") or [])
    implementation_ready = bool(audit.get("implementation_readiness")) and not blocking_decisions
    return {
        "schema_version": "execution-readiness/v1",
        "generated_at": utc_now(),
        "repo_root": str(root.resolve()),
        "agentic_dir": agentic_dir,
        "implementation_readiness": implementation_ready,
        "raw_implementation_readiness": audit.get("implementation_readiness"),
        "next_decision": "implementation_ready" if implementation_ready else "stop_or_continue_governance",
        "blocking_decisions": blocking_decisions,
        "spec_kit_policy": audit.get("spec_kit_policy"),
        "spec_kit_mode": "selective_integration" if audit.get("spec_kit_policy") == "forbidden" else "routed",
        "todo_baseline_readiness": audit.get("todo_baseline_readiness"),
        "todo_main_baseline_diff_required": audit.get("todo_main_baseline_diff_required"),
        "capability_fit_status": audit.get("capability_fit_status"),
        "agent_loop_contract_readiness": audit.get("agent_loop_contract_readiness"),
        "machine_readable_governance_status": audit.get("machine_readable_governance_status"),
        "required_files": list(GOVERNANCE_FILES.values())[:-1],
    }


def agent_entry_rule() -> str:
    return (
        f"\n## {AGENT_ENTRY_RULE_TITLE}\n\n"
        "Before implementation or documentation-governance work, read the machine-readable\n"
        "governance files under `docs/.agentic/` in this order: `agent-policy.json`,\n"
        "`capability-routing.json`, `loop-contract.json`, `execution-readiness.json`,\n"
        "and `docs-bundle.json`. Follow the loop contract exactly:\n"
        "Observe -> Plan -> Act -> Verify -> Update State -> Decide Next Loop.\n\n"
        "If `execution-readiness.json` reports `implementation_readiness=false`, do not\n"
        "start implementation. Use `capability-routing.json` to route to Spec Kit\n"
        "selective integration, plan-cross-validation, ADR capture, validation, or a\n"
        "user decision. Preserve `needs_confirmation` fields instead of inferring that\n"
        "ambiguous work is complete or verified.\n"
    )


def build_agent_entry_patch(root: Path) -> str:
    agents_path = root.resolve() / "AGENTS.md"
    original = agents_path.read_text(encoding="utf-8", errors="replace") if agents_path.is_file() else ""
    if AGENT_ENTRY_RULE_TITLE.lower() in original.lower():
        updated = original
    else:
        updated = original.rstrip() + "\n" + agent_entry_rule()
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile="AGENTS.md",
            tofile="AGENTS.md",
        )
    )


def build_all_governance(root: Path, task_text: str = "", agentic_dir: str = "docs/.agentic") -> dict[str, Any]:
    audit, contract = build_context(root, task_text)
    return {
        "agent-policy.json": build_agent_policy(root, audit, contract),
        "capability-routing.json": build_capability_routing(root, audit),
        "loop-contract.json": contract,
        "execution-readiness.json": build_execution_readiness(root, audit, agentic_dir),
    }


def validate_governance_bundle(
    repo_root: Path,
    agentic_dir: Path,
    original_agents_text: str | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    required_json = [
        "agent-policy.json",
        "capability-routing.json",
        "loop-contract.json",
        "execution-readiness.json",
    ]
    payloads: dict[str, dict[str, Any]] = {}
    for filename in required_json:
        path = agentic_dir / filename
        if not path.is_file():
            errors.append(f"{filename} is missing from {agentic_dir}.")
            continue
        try:
            payloads[filename] = __import__("json").loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive path
            errors.append(f"{filename} is not valid JSON: {exc}")

    expected_versions = {
        "agent-policy.json": "agent-policy/v1",
        "capability-routing.json": "capability-routing/v1",
        "loop-contract.json": "agentic-loop-contract/v1",
        "execution-readiness.json": "execution-readiness/v1",
    }
    for filename, expected in expected_versions.items():
        payload = payloads.get(filename)
        if payload and payload.get("schema_version") != expected:
            errors.append(f"{filename} schema_version must be {expected}.")

    routing = payloads.get("capability-routing.json", {})
    route_names = {
        item.get("capability")
        for item in routing.get("routes", [])
        if isinstance(item, dict)
    }
    for capability in REQUIRED_CAPABILITIES:
        if capability not in route_names:
            errors.append(f"capability-routing.json does not cover {capability}.")

    readiness = payloads.get("execution-readiness.json", {})
    if readiness.get("spec_kit_policy") == "forbidden" and readiness.get("spec_kit_mode") != "selective_integration":
        errors.append("execution-readiness.json must map forbidden Spec Kit policy to selective_integration.")

    policy = payloads.get("agent-policy.json", {})
    if policy.get("loop_order") != LOOP_ORDER:
        errors.append("agent-policy.json loop_order is invalid.")
    if "docs/.agentic/agent-policy.json" not in policy.get("required_read_order", []):
        errors.append("agent-policy.json must require the docs/.agentic entrypoint.")

    repo_agentic_dir = repo_root / "docs" / ".agentic"
    if repo_agentic_dir.exists():
        errors.append(f"Repository docs/.agentic exists unexpectedly: {repo_agentic_dir}")

    if original_agents_text is not None:
        current = (repo_root / "AGENTS.md").read_text(encoding="utf-8", errors="replace")
        if current != original_agents_text:
            errors.append("AGENTS.md changed during dry-run validation.")

    if not (agentic_dir / "proposed-agents-md.patch").is_file():
        warnings.append("proposed-agents-md.patch is missing from the dry-run artifact directory.")
    return errors, warnings
