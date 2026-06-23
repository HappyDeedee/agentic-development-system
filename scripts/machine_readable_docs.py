"""Deterministic Markdown-to-JSON helpers for project governance docs."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DOC_OUTPUTS = {
    "state": "state.json",
    "tasks": "tasks.json",
    "decisions": "decisions.json",
    "traceability": "traceability.json",
    "validation": "validation.json",
    "bundle": "docs-bundle.json",
}

SOURCE_GROUPS = {
    "state": ("GOAL.md", "CURRENT_STATE.md"),
    "tasks": ("TASKS.md", "CHANGE_REQUESTS.md"),
    "decisions": ("DECISIONS.md",),
    "traceability": ("TRACEABILITY.md",),
    "validation": ("TEST_PLAN.md", "TEST_RESULTS.md"),
}

SCHEMA_BY_OUTPUT = {
    "state.json": "project-state/v1",
    "tasks.json": "task-registry/v1",
    "decisions.json": "decision-registry/v1",
    "traceability.json": "traceability-matrix/v1",
    "validation.json": "validation-results/v1",
    "docs-bundle.json": "docs-bundle/v1",
}

CONFIRMATION_MARKERS = (
    "needs confirmation",
    "needs_confirmation",
    "待确认",
    "需要确认",
    "todo",
    "tbd",
    "unknown",
    "未确认",
)


def docs_root(repo_root: Path) -> Path:
    return repo_root / "docs"


def default_agentic_dir(repo_root: Path) -> Path:
    return docs_root(repo_root) / ".agentic"


def read_doc(repo_root: Path, rel_name: str) -> dict[str, Any]:
    path = docs_root(repo_root) / rel_name
    exists = path.is_file()
    text = path.read_text(encoding="utf-8", errors="replace") if exists else ""
    return {
        "path": f"docs/{rel_name}",
        "exists": exists,
        "bytes": len(text.encode("utf-8")),
        "line_count": len(text.splitlines()) if exists else 0,
        "text": text,
    }


def public_source_doc(doc: dict[str, Any]) -> dict[str, Any]:
    return {key: doc[key] for key in ("path", "exists", "bytes", "line_count")}


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip() or None
    return None


def headings(text: str, limit: int = 25) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            result.append({"level": len(match.group(1)), "title": match.group(2), "line": lineno})
        if len(result) >= limit:
            break
    return result


def checkbox_items(text: str, source_path: str, limit: int = 500) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    pattern = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$")
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = pattern.match(line)
        if not match:
            continue
        checked = match.group(1).lower() == "x"
        label = match.group(2).strip()
        items.append(
            {
                "id": stable_item_id(source_path, lineno, label),
                "label": label,
                "status": "done" if checked else "open",
                "source": source_path,
                "line": lineno,
                "needs_confirmation": contains_confirmation_marker(label),
            }
        )
        if len(items) >= limit:
            break
    return items


def table_rows(text: str, source_path: str, limit: int = 300) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pending_headers: list[str] | None = None
    for lineno, line in enumerate(text.splitlines(), start=1):
        cells = split_table_line(line)
        if not cells:
            pending_headers = None
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells):
            continue
        if pending_headers is None:
            pending_headers = cells
            continue
        row = {
            pending_headers[index]: cells[index] if index < len(cells) else ""
            for index in range(len(pending_headers))
        }
        rows.append({"source": source_path, "line": lineno, "columns": row})
        if len(rows) >= limit:
            break
    return rows


def split_table_line(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def contains_confirmation_marker(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in CONFIRMATION_MARKERS)


def stable_item_id(source_path: str, lineno: int, label: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", label).strip("-").lower()
    return f"{Path(source_path).stem.lower()}-{lineno}-{slug[:48] or 'item'}"


def collect_needs_confirmation(*items: Any) -> list[str]:
    notes: list[str] = []
    for item in items:
        append_confirmation_notes(notes, item)
    return dedupe_preserve_order(notes)


def append_confirmation_notes(notes: list[str], item: Any) -> None:
    if isinstance(item, dict):
        if item.get("needs_confirmation") and item.get("label"):
            notes.append(str(item["label"]))
        for value in item.values():
            append_confirmation_notes(notes, value)
    elif isinstance(item, list):
        for value in item:
            append_confirmation_notes(notes, value)
    elif isinstance(item, str) and contains_confirmation_marker(item):
        notes.append(item)


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def extract_state(repo_root: Path, docs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    goal_doc = docs["GOAL.md"]
    current_doc = docs["CURRENT_STATE.md"]
    goal_title = first_heading(goal_doc["text"]) if goal_doc["exists"] else None
    current_title = first_heading(current_doc["text"]) if current_doc["exists"] else None
    state = {
        "schema_version": "project-state/v1",
        "repo_root": str(repo_root),
        "source_documents": [public_source_doc(goal_doc), public_source_doc(current_doc)],
        "goal": {
            "title": goal_title,
            "headings": headings(goal_doc["text"]),
            "status": "needs_confirmation" if not goal_title else "extracted",
        },
        "current_state": {
            "title": current_title,
            "headings": headings(current_doc["text"]),
            "status": infer_status(current_doc["text"]),
        },
    }
    state["needs_confirmation"] = collect_needs_confirmation(state)
    if not goal_title:
        state["needs_confirmation"].append("GOAL.md missing top-level goal heading.")
    if state["current_state"]["status"] == "needs_confirmation":
        state["needs_confirmation"].append("CURRENT_STATE.md status needs confirmation.")
    state["needs_confirmation"] = dedupe_preserve_order(state["needs_confirmation"])
    return state


def extract_tasks(repo_root: Path, docs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    task_doc = docs["TASKS.md"]
    cr_doc = docs["CHANGE_REQUESTS.md"]
    tasks = checkbox_items(task_doc["text"], task_doc["path"])
    change_requests = table_rows(cr_doc["text"], cr_doc["path"], limit=200)
    result = {
        "schema_version": "task-registry/v1",
        "repo_root": str(repo_root),
        "source_documents": [public_source_doc(task_doc), public_source_doc(cr_doc)],
        "tasks": tasks,
        "change_requests": change_requests,
    }
    result["needs_confirmation"] = collect_needs_confirmation(result)
    return result


def extract_decisions(repo_root: Path, docs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    decision_doc = docs["DECISIONS.md"]
    decision_items = table_rows(decision_doc["text"], decision_doc["path"], limit=250)
    if not decision_items:
        decision_items = heading_items(decision_doc["text"], decision_doc["path"])
    result = {
        "schema_version": "decision-registry/v1",
        "repo_root": str(repo_root),
        "source_documents": [public_source_doc(decision_doc)],
        "decisions": decision_items,
    }
    result["needs_confirmation"] = collect_needs_confirmation(result)
    return result


def extract_traceability(repo_root: Path, docs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    trace_doc = docs["TRACEABILITY.md"]
    result = {
        "schema_version": "traceability-matrix/v1",
        "repo_root": str(repo_root),
        "source_documents": [public_source_doc(trace_doc)],
        "traceability_items": table_rows(trace_doc["text"], trace_doc["path"], limit=500),
    }
    result["needs_confirmation"] = collect_needs_confirmation(result)
    return result


def extract_validation(repo_root: Path, docs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    plan_doc = docs["TEST_PLAN.md"]
    results_doc = docs["TEST_RESULTS.md"]
    result = {
        "schema_version": "validation-results/v1",
        "repo_root": str(repo_root),
        "source_documents": [public_source_doc(plan_doc), public_source_doc(results_doc)],
        "validation_items": table_rows(results_doc["text"], results_doc["path"], limit=300),
        "test_plan_headings": headings(plan_doc["text"]),
    }
    result["needs_confirmation"] = collect_needs_confirmation(result)
    return result


def heading_items(text: str, source_path: str) -> list[dict[str, Any]]:
    return [
        {"source": source_path, "line": item["line"], "title": item["title"], "level": item["level"]}
        for item in headings(text, limit=200)
    ]


def infer_status(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in ("complete", "completed", "已完成", "完成")):
        return "contains_completed_signal"
    if any(marker in lowered for marker in ("blocked", "阻塞", "待确认", "needs confirmation")):
        return "contains_blocker_signal"
    return "needs_confirmation"


def load_source_docs(repo_root: Path) -> dict[str, dict[str, Any]]:
    names = sorted({name for group in SOURCE_GROUPS.values() for name in group})
    return {name: read_doc(repo_root, name) for name in names}


def build_docs_bundle(repo_root: Path) -> dict[str, dict[str, Any]]:
    docs = load_source_docs(repo_root)
    outputs = {
        "state.json": extract_state(repo_root, docs),
        "tasks.json": extract_tasks(repo_root, docs),
        "decisions.json": extract_decisions(repo_root, docs),
        "traceability.json": extract_traceability(repo_root, docs),
        "validation.json": extract_validation(repo_root, docs),
    }
    bundle = {
        "schema_version": "docs-bundle/v1",
        "repo_root": str(repo_root),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "outputs": {name: {"schema_version": payload["schema_version"]} for name, payload in outputs.items()},
        "source_policy": {
            "machine_readable_state": "primary",
            "markdown_role": "human_summary",
            "write_policy": "dry-run by default; --write required for docs/.agentic",
        },
        "needs_confirmation": collect_needs_confirmation(outputs),
    }
    outputs["docs-bundle.json"] = bundle
    return outputs


def write_docs_bundle(outputs: dict[str, dict[str, Any]], output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for filename, payload in outputs.items():
        path = output_dir / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        written.append(str(path))
    return written


def load_output_dir(target: Path) -> dict[str, dict[str, Any]]:
    return {
        filename: json.loads((target / filename).read_text(encoding="utf-8"))
        for filename in DOC_OUTPUTS.values()
        if (target / filename).is_file()
    }


def schema_errors(outputs: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for filename, schema_version in SCHEMA_BY_OUTPUT.items():
        payload = outputs.get(filename)
        if not isinstance(payload, dict):
            errors.append(f"{filename} is missing.")
            continue
        if payload.get("schema_version") != schema_version:
            errors.append(f"{filename} schema_version must be {schema_version}.")
        if filename != "docs-bundle.json" and not isinstance(payload.get("source_documents"), list):
            errors.append(f"{filename} source_documents must be a list.")
        if not isinstance(payload.get("needs_confirmation"), list):
            errors.append(f"{filename} needs_confirmation must be a list.")
    return errors


def consistency_warnings(outputs: dict[str, dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for filename, payload in outputs.items():
        for source in payload.get("source_documents", []):
            if isinstance(source, dict) and not source.get("exists"):
                warnings.append(f"{filename} source missing: {source.get('path')}")
    if not outputs.get("tasks.json", {}).get("tasks"):
        warnings.append("tasks.json has no checkbox tasks; source may use tables or prose only.")
    if not outputs.get("traceability.json", {}).get("traceability_items"):
        warnings.append("traceability.json has no table rows; traceability may need manual mapping.")
    return dedupe_preserve_order(warnings)


def validation_result(target: Path, outputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors = schema_errors(outputs)
    warnings = consistency_warnings(outputs)
    return {
        "schema_version": "machine-readable-docs-validation/v1",
        "target": str(target),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "output_count": len(outputs),
        "needs_confirmation_count": sum(len(payload.get("needs_confirmation", [])) for payload in outputs.values()),
    }
