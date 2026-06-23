"""Machine-readable contract helpers for the agentic development audit."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOOP_ORDER = ["observe", "plan", "act", "verify", "update_state", "decide_next_loop"]
SCHEMA_FILES = [
    "schemas/goal.schema.json",
    "schemas/loop.contract.schema.json",
    "schemas/state.schema.json",
    "schemas/traceability.schema.json",
]
DOC_SCHEMA_FILES = [
    "schemas/project.state.schema.json",
    "schemas/task.registry.schema.json",
    "schemas/decision.registry.schema.json",
    "schemas/traceability.matrix.schema.json",
    "schemas/validation.results.schema.json",
    "schemas/docs.bundle.schema.json",
    "schemas/agent.policy.schema.json",
    "schemas/capability.routing.schema.json",
    "schemas/agent.entry.schema.json",
    "schemas/execution.readiness.schema.json",
]
CONTRACT_SCRIPTS = [
    "scripts/export_agentic_contract.py",
    "scripts/validate_agentic_contract.py",
]
DOC_SCRIPTS = [
    "scripts/export_machine_readable_docs.py",
    "scripts/validate_machine_readable_docs.py",
    "scripts/audit_doc_consistency.py",
    "scripts/export_agent_policy.py",
    "scripts/export_capability_routing.py",
    "scripts/export_execution_readiness.py",
    "scripts/export_agent_entry_patch.py",
    "scripts/validate_agent_execution_readiness.py",
]


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def recommended_contract_files() -> list[str]:
    return [*SCHEMA_FILES, *DOC_SCHEMA_FILES, *CONTRACT_SCRIPTS, *DOC_SCRIPTS]


def machine_readable_governance_status() -> dict[str, Any]:
    root = plugin_root()
    missing = [rel for rel in recommended_contract_files() if not (root / rel).is_file()]
    return {
        "schema_version": "machine-readable-governance/v1",
        "status": "ready" if not missing else "incomplete",
        "schema_files": SCHEMA_FILES,
        "doc_schema_files": DOC_SCHEMA_FILES,
        "export_command": "python <plugin-root>/scripts/export_agentic_contract.py <repo-root>",
        "validate_command": "python <plugin-root>/scripts/validate_agentic_contract.py <repo-root> --json",
        "docs_export_command": (
            "python <plugin-root>/scripts/export_machine_readable_docs.py "
            "<repo-root> --output <dir> --dry-run"
        ),
        "docs_validate_command": "python <plugin-root>/scripts/validate_machine_readable_docs.py <dir> --json",
        "docs_consistency_command": "python <plugin-root>/scripts/audit_doc_consistency.py <repo-root> --json",
        "agent_policy_command": (
            "python <plugin-root>/scripts/export_agent_policy.py "
            "<repo-root> --output <dir>/agent-policy.json"
        ),
        "capability_routing_command": (
            "python <plugin-root>/scripts/export_capability_routing.py "
            "<repo-root> --output <dir>/capability-routing.json"
        ),
        "execution_readiness_command": (
            "python <plugin-root>/scripts/export_execution_readiness.py "
            "<repo-root> --output <dir>/execution-readiness.json"
        ),
        "agent_entry_patch_command": (
            "python <plugin-root>/scripts/export_agent_entry_patch.py "
            "<repo-root> --output <dir>/proposed-agents-md.patch"
        ),
        "execution_readiness_validate_command": (
            "python <plugin-root>/scripts/validate_agent_execution_readiness.py "
            "<repo-root> --agentic-dir <dir> --json"
        ),
        "missing_files": missing,
    }


def build_loop_readiness(audit: dict[str, Any]) -> dict[str, Any]:
    blocking_decisions = list(audit.get("blocking_decisions") or [])
    ready = bool(audit.get("implementation_readiness")) and not blocking_decisions
    if ready:
        next_decision = "implementation_ready"
    elif blocking_decisions:
        next_decision = "stop_for_decision"
    else:
        next_decision = "continue_governance_loop"
    return {
        "schema_version": "agentic-loop-readiness/v1",
        "loop": LOOP_ORDER,
        "status": "ready" if ready else "blocked",
        "next_decision": next_decision,
        "observe_sources": [
            "project files",
            "agent entry docs",
            "docs and task trackers",
            "Spec Kit artifacts",
            "test and CI signals",
        ],
        "plan_inputs": [
            "project_layer",
            "spec_kit_policy",
            "todo_baseline_readiness",
            "capability_fit_status",
            "blocking_decisions",
        ],
        "verify_gates": [
            "implementation_readiness",
            "todo_main_baseline_diff_required",
            "spec_kit_collision_risk",
            "sensitive_signals",
        ],
        "blocking_decisions": blocking_decisions,
    }


def contract_goal_section(audit: dict[str, Any], task_text: str) -> dict[str, Any]:
    return {
        "description": task_text or "Audit repository readiness before implementation.",
        "success_criteria": [
            "Project layer is classified from current files.",
            "Blocking decisions are explicit.",
            "Spec Kit policy is reported before initialization.",
            "Validation evidence path is named before implementation.",
        ],
        "validation_commands": [
            "python <plugin-root>/scripts/audit_agentic_system.py <repo-root> --json",
            "python <plugin-root>/scripts/validate_agentic_contract.py <repo-root> --json",
        ],
        "non_goals": [
            "Do not write product code during initialization.",
            "Do not scaffold parallel docs in mature projects.",
        ],
        "decision_gates": list(audit.get("blocking_decisions") or []),
    }


def contract_state_section(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_layer": audit.get("project_layer"),
        "project_kind": audit.get("project_kind"),
        "repo_boundary": audit.get("repo_boundary"),
        "implementation_readiness": audit.get("implementation_readiness"),
        "todo_baseline_readiness": audit.get("todo_baseline_readiness"),
        "spec_kit_policy": audit.get("spec_kit_policy"),
        "capability_fit_status": audit.get("capability_fit_status"),
        "blocking_decisions": list(audit.get("blocking_decisions") or []),
    }


def contract_loop_section(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "contract_order": LOOP_ORDER,
        "observe": {
            "required_fields": [
                "role_hits",
                "manifest_files",
                "test_signals",
                "sensitive_signals",
                "nested_repos",
            ]
        },
        "plan": {
            "required_fields": [
                "project_layer",
                "workflow_level",
                "spec_kit_policy",
                "capability_slot_recommendations",
            ]
        },
        "act": {
            "allowed_when": "spec_kit_policy is allowed or gated, or user requested canonical-doc patches",
            "write_boundary": audit.get("layer_policy", {}),
        },
        "verify": {
            "required_fields": [
                "test_signals",
                "ci_signals",
                "todo_baseline_required_columns",
                "todo_diff_review_required_actions",
            ]
        },
        "update_state": {
            "required_docs": [
                "state/current status",
                "tasks",
                "decisions",
                "validation evidence",
                "traceability when requirements change",
            ]
        },
        "decide_next_loop": {
            "next_decision": build_loop_readiness(audit)["next_decision"],
            "blocking_decisions": list(audit.get("blocking_decisions") or []),
        },
    }


def contract_traceability_section(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "role_hits": audit.get("role_hits", {}),
        "missing_roles": list(audit.get("missing_roles") or []),
        "validation_evidence": list(audit.get("test_signals") or []),
        "baseline_evidence": list(audit.get("task_tracker_files") or []),
        "capability_slot_recommendations": list(audit.get("capability_slot_recommendations") or []),
    }


def contract_audit_section(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "project_layer": audit.get("project_layer"),
        "spec_kit_policy": audit.get("spec_kit_policy"),
        "spec_kit_next_skill": audit.get("spec_kit_next_skill"),
        "todo_main_baseline_diff_required": audit.get("todo_main_baseline_diff_required"),
        "machine_readable_governance_status": machine_readable_governance_status(),
        "recommended_contract_files": recommended_contract_files(),
    }


def build_contract(root: Path, audit: dict[str, Any], task_text: str = "") -> dict[str, Any]:
    return {
        "schema_version": "agentic-loop-contract/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "task_text": task_text,
        "goal": contract_goal_section(audit, task_text),
        "state": contract_state_section(audit),
        "loop": contract_loop_section(audit),
        "traceability": contract_traceability_section(audit),
        "audit": contract_audit_section(audit),
    }


def validate_contract(contract: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if contract.get("schema_version") != "agentic-loop-contract/v1":
        errors.append("schema_version must be agentic-loop-contract/v1.")
    for section in ["goal", "state", "loop", "traceability", "audit"]:
        if not isinstance(contract.get(section), dict):
            errors.append(f"{section} must be an object.")
    loop = contract.get("loop")
    if isinstance(loop, dict):
        if loop.get("contract_order") != LOOP_ORDER:
            errors.append("loop.contract_order does not match the required loop order.")
        for phase in LOOP_ORDER:
            if not isinstance(loop.get(phase), dict):
                errors.append(f"loop.{phase} must be an object.")
    state = contract.get("state")
    if isinstance(state, dict) and state.get("implementation_readiness") is not True:
        warnings.append("implementation_readiness is false; this can be valid when blockers remain.")
    return errors, warnings
