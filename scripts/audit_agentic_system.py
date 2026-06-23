#!/usr/bin/env python3
"""Read-only audit for agentic development readiness.

The audit maps existing files to agentic responsibilities and builds a small
project facts model. It helps an agent decide whether to scaffold, augment, or
stop for boundary clarification before implementation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentic_contract import (
    build_loop_readiness,
    machine_readable_governance_status,
    recommended_contract_files,
)


DEVELOPMENT_MODEL_RECOMMENDATION = "SDD-first hybrid"

SPEC_KIT_REQUIRED_INIT_FLAGS = (
    "--integration",
    "--integration-options",
    "--script",
    "--here",
    "--force",
)

SPEC_KIT_INIT_COMMAND = (
    "specify",
    "init",
    "--here",
    "--integration",
    "codex",
    "--integration-options=--skills",
    "--script",
    "ps",
)

SPEC_KIT_INIT_COMMAND_WITH_FORCE = (*SPEC_KIT_INIT_COMMAND, "--force")

SPEC_KIT_INTEGRATION_COMMAND = (
    "specify",
    "integration",
    "install",
    "codex",
    "--integration-options=--skills",
    "--script",
    "ps",
)

SPEC_KIT_SKILLS = (
    "speckit-constitution",
    "speckit-specify",
    "speckit-plan",
    "speckit-tasks",
    "speckit-implement",
    "speckit-converge",
    "speckit-clarify",
    "speckit-analyze",
    "speckit-checklist",
)

THIN_SAFE_FILES = {".gitignore", "README.md", "readme.md"}

DEFAULT_SKELETON_FILES = (
    "AGENTS.md",
    "docs/AGENTIC_WORKFLOW.md",
    "docs/STATE.md",
    "docs/DECISIONS.md",
    "docs/VALIDATION.md",
    "docs/TEST_RESULTS.md",
)

DEFAULT_SKELETON_DIRS = (
    "docs/adr",
)

MANIFEST_FILES = (
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "composer.json",
    "Gemfile",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
)

TEST_SIGNAL_PATHS = (
    "tests",
    "test",
    "spec",
    "pytest.ini",
    "tox.ini",
    "vitest.config.ts",
    "jest.config.js",
    "playwright.config.ts",
)

CI_SIGNAL_PATHS = (
    ".github/workflows",
    ".gitlab-ci.yml",
    "azure-pipelines.yml",
    "Jenkinsfile",
)

TODO_BASELINE_REQUIRED_COLUMNS = (
    "todo_label",
    "cr_phase_or_requirement_owner",
    "current_baseline_source",
    "current_classification",
    "baseline_evidence",
    "baseline_diff_result",
    "required_action",
    "protected_existing_behavior",
    "validation_or_acceptance_entry",
    "implementation_readiness",
)

TODO_DIFF_REVIEW_REQUIRED_ACTIONS = (
    "keep-as-current",
    "rewrite-for-current-baseline",
    "mark-completed",
    "merge-duplicate",
    "defer/future",
    "operator-gate",
    "archive/historical",
    "remove-stale",
    "Needs Baseline",
)

WORKFLOW_LEVELS = (
    "readonly",
    "light_change",
    "standard_change",
    "high_risk_change",
    "doc_governance",
    "parallel_candidate",
)

CAPABILITY_SLOTS = (
    "governance-review",
    "baseline-validation",
    "code-understanding",
    "uiux-design",
    "debugging",
    "implementation",
    "verification",
    "parallel-work",
    "release-handoff",
)

LOCAL_SKILL_ROOTS = (
    Path.home() / ".codex" / "skills",
    Path.home() / ".agents" / "skills",
)

LOCAL_PLUGIN_CACHE_ROOTS = (
    Path.home() / ".codex" / "plugins" / "cache",
    Path.home() / ".agents" / "plugins" / "cache",
)

CAPABILITY_ROUTING_RULES = {
    "spec-kit": (
        "spec-kit",
        "spec kit",
        "$spec-kit",
        "$speckit-constitution",
        "$speckit-specify",
        "$speckit-plan",
        "$speckit-tasks",
        "$speckit-implement",
        ".specify",
    ),
    "superpowers": ("superpowers", "tdd", "verification", "finishing"),
    "plan-cross-validation": ("plan-cross-validation", "$plan-cross-validation", "cross-validation"),
    "architecture-decision-records": ("architecture-decision-records", "adr", "decision record"),
    "code-understanding": ("aider", "repo-map", "repo map", "ast-grep", "code-understanding"),
}

CAPABILITY_LOCAL_CHECKS = {
    "spec-kit": {
        "skills": ("spec-kit",),
        "plugins": (),
        "commands": ("specify",),
    },
    "superpowers": {
        "skills": (),
        "plugins": ("superpowers",),
        "commands": (),
    },
    "plan-cross-validation": {
        "skills": ("plan-cross-validation",),
        "plugins": (),
        "commands": (),
    },
    "architecture-decision-records": {
        "skills": ("architecture-decision-records",),
        "plugins": (),
        "commands": (),
    },
    "aider": {
        "skills": (),
        "plugins": (),
        "commands": ("aider",),
    },
    "ast-grep": {
        "skills": (),
        "plugins": (),
        "commands": ("ast-grep", "sg"),
    },
}

TODO_BASELINE_REVIEW_RULE_TITLE = "Todo Baseline Review Rule"

TODO_BASELINE_REVIEW_RULE_SNIPPET = """## Todo Baseline Review Rule

Before reviewing, generating, reordering, approving, or implementing open TODOs,
compare them against the current main/current worktree baseline.

For each active or next TODO, classify it as current, future, deferred,
Needs Confirmation, operator-gated, historical, duplicate/overlap,
stale/remove, or Needs Baseline.

Do not implement stale, duplicate, old-baseline, or Needs Baseline TODOs.
If a TODO is outdated, propose documentation changes first. Unmerged worktrees
are not mainline facts; rerun the baseline review after merge.
"""

TODO_BASELINE_RULE_PATTERNS = (
    "todo baseline review rule",
    "todo main-baseline diff",
    "todo main baseline diff",
    "todo baseline coverage audit",
)

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".scala",
    ".dart",
    ".lua",
    ".ex",
    ".exs",
    ".sh",
    ".ps1",
}

SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".next",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

SENSITIVE_NAME_PARTS = (
    ".env",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "token",
    "cookie",
    "cookies",
    "private",
    "customer",
    "client",
    "legal",
    "evidence",
    "export",
    "profile",
    "profiles",
    "backup",
)

SENSITIVE_CJK_PARTS = (
    "法律",
    "案例",
    "客户",
    "证据",
    "隐私",
    "账号",
    "资料",
)

SENSITIVE_SUFFIXES = (
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".crt",
    ".cookie",
    ".cookies",
    ".sqlite",
    ".db",
)


@dataclass(frozen=True)
class Role:
    name: str
    description: str
    candidates: tuple[str, ...]


ROLES = (
    Role(
        "agent_entry",
        "Agent entry contract",
        (
            "AGENTS.md",
            "CLAUDE.md",
            ".github/copilot-instructions.md",
            ".cursor/rules",
        ),
    ),
    Role(
        "workflow",
        "Agentic workflow and routing",
        (
            "docs/AGENTIC_WORKFLOW.md",
            "docs/AGENT_WORKFLOW.md",
            "docs/CONTRIBUTING.md",
            "docs/DEVELOPMENT.md",
        ),
    ),
    Role(
        "state",
        "Current state and next action",
        (
            "docs/STATE.md",
            "docs/CURRENT_STATE.md",
            "docs/STATUS.md",
            "docs/current-status.md",
        ),
    ),
    Role(
        "tasks",
        "Task tracking",
        (
            "docs/TASKS.md",
            "docs/ROADMAP.md",
            "docs/roadmap.md",
        ),
    ),
    Role(
        "requirements",
        "Requirement or change intake",
        (
            "docs/GOAL.md",
            "docs/PRODUCT_REQUIREMENTS.md",
            "docs/CHANGE_REQUESTS.md",
            "specs",
            ".specify",
        ),
    ),
    Role(
        "decisions",
        "Durable decisions and ADRs",
        (
            "docs/DECISIONS.md",
            "docs/ADR.md",
            "docs/adr",
            "adr",
        ),
    ),
    Role(
        "validation",
        "Validation plan and evidence",
        (
            "docs/VALIDATION.md",
            "docs/TEST_PLAN.md",
            "docs/TEST_RESULTS.md",
            ".github/workflows",
        ),
    ),
    Role(
        "traceability",
        "Traceability matrix",
        (
            "docs/TRACEABILITY.md",
            "docs/traceability.md",
        ),
    ),
    Role(
        "standards",
        "Project standards",
        (
            "agent-os/standards",
            "docs/CODING_STANDARDS.md",
            "docs/ARCHITECTURE.md",
            "docs/FRONTEND_ARCHITECTURE.md",
        ),
    ),
    Role(
        "specs",
        "Per-change specs",
        (
            "agent-os/specs",
            "specs",
            ".specify/specs",
        ),
    ),
)


def normalize(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def path_exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def is_meaningful(path: Path) -> bool:
    return path.name not in {".DS_Store", "Thumbs.db"}


def collect_docs(root: Path) -> list[str]:
    docs = root / "docs"
    if not docs.exists():
        return []
    return sorted(
        normalize(path, root)
        for path in docs.rglob("*")
        if path.is_file()
    )


def iter_project_paths(root: Path) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    dirs: list[Path] = []
    if not root.exists():
        return files, dirs

    for path in root.rglob("*"):
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if not rel_parts:
            continue
        if any(part in SKIP_DIR_NAMES for part in rel_parts[:-1]):
            continue
        if path.is_dir():
            dirs.append(path)
            if path.name in SKIP_DIR_NAMES:
                continue
        elif path.is_file():
            files.append(path)
    return files, dirs


def collect_nested_repos(root: Path) -> list[str]:
    nested: list[str] = []
    for git_dir in root.rglob(".git"):
        if not git_dir.is_dir():
            continue
        repo_root = git_dir.parent
        if repo_root == root:
            continue
        nested.append(normalize(repo_root, root))
    return sorted(set(nested))


def collect_matching_existing(root: Path, candidates: tuple[str, ...]) -> list[str]:
    return [rel for rel in candidates if path_exists(root, rel)]


def collect_sensitive_signals(root: Path, files: list[Path], dirs: list[Path]) -> list[str]:
    signals: list[str] = []
    for path in [*files, *dirs]:
        rel = normalize(path, root)
        rel_lower = rel.lower()
        name_lower = path.name.lower()
        suffix_lower = path.suffix.lower()
        if rel_lower.endswith(".env.example"):
            continue
        if suffix_lower in SENSITIVE_SUFFIXES:
            signals.append(rel)
            continue
        if any(part in rel_lower or part in name_lower for part in SENSITIVE_NAME_PARTS):
            signals.append(rel)
            continue
        if any(part in rel or part in path.name for part in SENSITIVE_CJK_PARTS):
            signals.append(rel)
    return sorted(set(signals))[:50]


def count_code_files(files: list[Path]) -> int:
    return sum(1 for path in files if path.suffix.lower() in CODE_EXTENSIONS)


def estimate_open_todos(root: Path, task_files: list[str]) -> int:
    """Conservatively count unchecked Markdown task markers in task trackers."""
    marker = re.compile(r"^\s*[-*]\s+\[\s\]\s+")
    count = 0
    for rel in task_files:
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        count += sum(1 for line in text.splitlines() if marker.match(line))
    return count


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def run_command(args: tuple[str, ...] | list[str], timeout: int = 20) -> dict[str, object]:
    try:
        completed = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": f"Command timed out after {timeout}s.",
        }
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def output_excerpt(value: object, limit: int = 800) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def parse_specify_version(output: str) -> str | None:
    match = re.search(r"CLI Version\s+([0-9][^\s]*)", output)
    if match:
        return match.group(1)
    match = re.search(r"\b([0-9]+\.[0-9]+\.[0-9]+)\b", output)
    return match.group(1) if match else None


def command_output(result: dict[str, object]) -> str:
    return "\n".join(
        part for part in (str(result.get("stdout", "")), str(result.get("stderr", ""))) if part
    )


def empty_spec_kit_cli_result(command_path: str | None) -> dict[str, object]:
    return {
        "command": "specify",
        "path": command_path,
        "available": bool(command_path),
        "version": None,
        "version_status": "missing",
        "check_status": "not_run",
        "check_returncode": None,
        "init_help_status": "not_run",
        "required_init_flags": list(SPEC_KIT_REQUIRED_INIT_FLAGS),
        "supported_init_flags": [],
        "missing_init_flags": list(SPEC_KIT_REQUIRED_INIT_FLAGS),
        "ready": False,
        "evidence": [],
    }


def update_spec_kit_version_status(result: dict[str, object], evidence: list[str]) -> dict[str, object]:
    version_result = run_command(("specify", "version"), timeout=20)
    version = parse_specify_version(command_output(version_result))
    result["version"] = version
    result["version_status"] = "ok" if version_result["ok"] else "failed"
    if version:
        evidence.append(f"`specify version` reported CLI Version {version}.")
    else:
        evidence.append("`specify version` did not expose a parseable CLI version.")
    return version_result


def update_spec_kit_check_status(result: dict[str, object], evidence: list[str]) -> dict[str, object]:
    check_result = run_command(("specify", "check"), timeout=30)
    result["check_status"] = "passed" if check_result["ok"] else "failed"
    result["check_returncode"] = check_result["returncode"]
    if check_result["ok"]:
        evidence.append("`specify check` passed.")
    else:
        check_excerpt = output_excerpt(check_result.get("stderr") or check_result.get("stdout"))
        evidence.append(f"`specify check` failed: {check_excerpt}")
    return check_result


def update_spec_kit_help_status(result: dict[str, object], evidence: list[str]) -> list[str]:
    help_result = run_command(("specify", "init", "--help"), timeout=20)
    help_output = command_output(help_result)
    supported = [flag for flag in SPEC_KIT_REQUIRED_INIT_FLAGS if flag in help_output]
    missing = [flag for flag in SPEC_KIT_REQUIRED_INIT_FLAGS if flag not in supported]
    result["init_help_status"] = "ok" if help_result["ok"] else "failed"
    result["supported_init_flags"] = supported
    result["missing_init_flags"] = missing
    if not missing:
        evidence.append("`specify init --help` includes required init flags.")
    else:
        evidence.append(f"`specify init --help` is missing required flags: {', '.join(missing)}.")
    return missing


def detect_spec_kit_cli() -> dict[str, object]:
    command_path = shutil.which("specify")
    result = empty_spec_kit_cli_result(command_path)
    evidence: list[str] = []
    if not command_path:
        evidence.append("`specify` was not found on PATH.")
        result["evidence"] = evidence
        return result

    version_result = update_spec_kit_version_status(result, evidence)
    check_result = update_spec_kit_check_status(result, evidence)
    missing = update_spec_kit_help_status(result, evidence)
    result["ready"] = bool(command_path and version_result["ok"] and check_result["ok"] and not missing)
    result["evidence"] = evidence
    return result


def collect_speckit_project_skills(root: Path) -> list[str]:
    skills_root = root / ".agents" / "skills"
    if not skills_root.exists():
        return []
    matches: list[str] = []
    for skill_dir in skills_root.glob("speckit-*"):
        if skill_dir.is_dir():
            matches.append(normalize(skill_dir, root))
    return sorted(matches)


def collect_spec_kit_artifacts(root: Path) -> dict[str, list[str]]:
    artifact_map = {
        "spec": "spec.md",
        "plan": "plan.md",
        "tasks": "tasks.md",
    }
    artifacts: dict[str, list[str]] = {key: [] for key in artifact_map}
    specs_root = root / "specs"
    if not specs_root.exists():
        return artifacts
    for spec_dir in specs_root.iterdir():
        if not spec_dir.is_dir():
            continue
        for key, filename in artifact_map.items():
            path = spec_dir / filename
            if path.is_file():
                artifacts[key].append(normalize(path, root))
    return {key: sorted(values) for key, values in artifacts.items()}


def choose_spec_kit_next_skill(status: dict[str, object]) -> str:
    if not status.get("specify_dir"):
        return "$speckit-constitution"
    artifacts = status.get("artifacts", {})
    if not status.get("constitution"):
        return "$speckit-constitution"
    if isinstance(artifacts, dict):
        if not artifacts.get("spec"):
            return "$speckit-specify"
        if not artifacts.get("plan"):
            return "$speckit-plan"
        if not artifacts.get("tasks"):
            return "$speckit-tasks"
    return "$speckit-implement"


def detect_spec_kit_project_status(root: Path) -> dict[str, object]:
    artifacts = collect_spec_kit_artifacts(root)
    status: dict[str, object] = {
        "specify_dir": (root / ".specify").exists(),
        "constitution": (root / ".specify" / "memory" / "constitution.md").is_file(),
        "integration_json": (root / ".specify" / "integration.json").is_file(),
        "workflow": (root / ".specify" / "workflows" / "speckit" / "workflow.yml").is_file(),
        "codex_skills": collect_speckit_project_skills(root),
        "artifacts": artifacts,
        "has_spec_artifacts": any(artifacts.values()),
    }
    status["already_present"] = bool(
        status["specify_dir"]
        or status["constitution"]
        or status["integration_json"]
        or status["workflow"]
        or status["codex_skills"]
        or status["has_spec_artifacts"]
    )
    status["next_skill"] = choose_spec_kit_next_skill(status)
    return status


def is_thin_safe_workspace(root: Path, top_level: list[Path]) -> bool:
    names = {path.name for path in top_level if is_meaningful(path)}
    return bool(names) and names.issubset(THIN_SAFE_FILES | {".git"})


def expected_spec_kit_write_scope(policy: str) -> list[str]:
    if policy in {"allowed", "gated"}:
        return [
            ".specify/",
            ".agents/skills/speckit-*",
            "specs/",
        ]
    if policy == "already_present":
        return [
            ".agents/skills/speckit-*",
            ".specify/integration.json",
            ".specify/workflows/speckit/workflow.yml",
        ]
    return []


def build_spec_kit_command_plan(policy: str) -> dict[str, object]:
    if policy == "allowed":
        return {
            "mode": "init",
            "command": list(SPEC_KIT_INIT_COMMAND),
            "requires_user_confirmation": False,
            "expected_write_scope": expected_spec_kit_write_scope(policy),
        }
    if policy == "gated":
        return {
            "mode": "init",
            "command": list(SPEC_KIT_INIT_COMMAND_WITH_FORCE),
            "requires_user_confirmation": True,
            "required_token": "gated",
            "expected_write_scope": expected_spec_kit_write_scope(policy),
        }
    if policy == "already_present":
        return {
            "mode": "integration_install",
            "command": list(SPEC_KIT_INTEGRATION_COMMAND),
            "requires_user_confirmation": True,
            "expected_write_scope": expected_spec_kit_write_scope(policy),
        }
    return {
        "mode": "mapping_only",
        "command": [],
        "requires_user_confirmation": False,
        "expected_write_scope": [],
    }


def classify_spec_kit_policy(
    root: Path,
    top_level: list[Path],
    project_layer: str,
    repo_boundary: str,
    nested_repos: list[str],
    sensitive_signals: list[str],
    spec_kit_cli: dict[str, object],
    spec_kit_project_status: dict[str, object],
) -> dict[str, object]:
    reasons: list[str] = []
    collision_risk = "none"
    force_allowed = False

    if not spec_kit_cli.get("ready"):
        if not spec_kit_cli.get("available"):
            reasons.append("Spec Kit CLI `specify` is not available on PATH.")
        elif spec_kit_cli.get("check_status") != "passed":
            reasons.append("`specify check` did not pass.")
        elif spec_kit_cli.get("missing_init_flags"):
            reasons.append("`specify init --help` is missing required flags.")
        else:
            reasons.append("Spec Kit CLI is installed but not verified as ready.")
        policy = "unavailable"
    elif spec_kit_project_status.get("already_present"):
        policy = "already_present"
        reasons.append(
            "Spec Kit artifacts already exist; use the next `$speckit-*` skill "
            "or install/update integration instead of running init."
        )
    elif repo_boundary in {"nested_repos", "mixed_workspace"} or nested_repos:
        policy = "forbidden"
        collision_risk = "high"
        reasons.append(
            "Nested or multi-repo boundary detected; user must select the target "
            "repository before Spec Kit init."
        )
    elif sensitive_signals:
        policy = "forbidden"
        collision_risk = "high"
        reasons.append(
            "Sensitive path signals detected; confirm data boundary and exclusions "
            "before any initializer writes project metadata."
        )
    elif project_layer == "empty_directory":
        policy = "allowed"
        reasons.append("Target is empty and Spec Kit CLI is ready; automatic initialization is allowed.")
    elif is_thin_safe_workspace(root, top_level):
        policy = "gated"
        collision_risk = "medium"
        force_allowed = False
        reasons.append(
            "Target contains only thin-safe files; Spec Kit init may run only with "
            "explicit gated confirmation."
        )
    elif project_layer in {"partially_governed_project", "mature_governed_project"}:
        policy = "forbidden"
        collision_risk = "high"
        reasons.append(
            "Existing governance owns project responsibilities; provide selective "
            "mapping instead of creating `.specify/`."
        )
    elif project_layer in {"multi_repo_workspace", "nested_upstream_repo", "document_or_evidence_workspace"}:
        policy = "forbidden"
        collision_risk = "high"
        reasons.append("Project layer requires boundary or evidence governance before Spec Kit init.")
    else:
        policy = "forbidden"
        collision_risk = "medium"
        reasons.append(
            "Non-empty project is not thin-safe; output mapping recommendations "
            "and ask before adopting Spec Kit."
        )

    if policy == "forbidden" and project_layer in {"partially_governed_project", "mature_governed_project"}:
        maturity_reason = (
            "Existing governance owns project responsibilities; use selective integration mapping only."
        )
        if maturity_reason not in reasons:
            reasons.append(maturity_reason)

    command_plan = build_spec_kit_command_plan(policy)
    if policy == "allowed":
        collision_risk = "none"
    return {
        "policy": policy,
        "reasons": reasons,
        "command_plan": command_plan,
        "force_allowed": force_allowed,
        "collision_risk": collision_risk,
        "next_skill": spec_kit_project_status.get("next_skill", "$speckit-constitution"),
    }


def first_existing_skill_dir(skill_name: str) -> Path | None:
    for root in LOCAL_SKILL_ROOTS:
        if not root.exists():
            continue
        direct = root / skill_name
        candidates = [direct] if direct.exists() else []
        candidates.extend(root.rglob(skill_name))
        for candidate in candidates:
            try:
                if candidate.is_dir():
                    return candidate
            except OSError:
                if candidate.name == skill_name:
                    return candidate
    return None


def skill_readability_status(skill_name: str) -> tuple[str, str]:
    skill_dir = first_existing_skill_dir(skill_name)
    if not skill_dir:
        return "missing", "No local skill directory found."
    skill_file = skill_dir / "SKILL.md"
    try:
        text = skill_file.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return "installed_but_unverified", f"Skill exists but SKILL.md could not be read: {exc}"
    if not text.strip():
        return "installed_but_unverified", "Skill exists but SKILL.md is empty."
    return "available", f"Readable at {skill_file}"


def find_agent_entry_files(root: Path, role_hits: dict[str, list[str]]) -> list[str]:
    entry_files: list[str] = []
    for rel in role_hits.get("agent_entry", []):
        path = root / rel
        if path.is_file():
            entry_files.append(rel)
    return entry_files


def has_todo_baseline_review_rule(root: Path, entry_files: list[str]) -> bool:
    for rel in entry_files:
        text = read_text(root / rel).lower()
        if any(pattern in text for pattern in TODO_BASELINE_RULE_PATTERNS):
            return True
    return False


def todo_baseline_rule_status(
    root: Path,
    role_hits: dict[str, list[str]],
    task_files: list[str],
    open_todo_count: int,
) -> tuple[bool, list[str], bool, str, str]:
    entry_files = find_agent_entry_files(root, role_hits)
    rule_present = has_todo_baseline_review_rule(root, entry_files)
    rule_required = bool(task_files and open_todo_count > 0)
    status = "not_required"
    if rule_required and rule_present:
        status = "present"
    elif rule_required and entry_files:
        status = "missing_from_agent_entry"
    elif rule_required and not entry_files:
        status = "missing_agent_entry"
    suggestion = ""
    if rule_required and not rule_present:
        target = entry_files[0] if entry_files else "AGENTS.md"
        suggestion = (
            f"Add a `{TODO_BASELINE_REVIEW_RULE_TITLE}` section to `{target}` "
            "so future agents must compare open TODOs against the current "
            "main/current worktree baseline before implementation."
        )
    return rule_required, entry_files, rule_present, status, suggestion


def classify_todo_baseline_readiness(task_files: list[str], open_todo_count: int) -> str:
    if not task_files:
        return "no_task_tracker"
    if open_todo_count == 0:
        return "no_open_todos_detected"
    return "manual_audit_required"


def todo_baseline_source_hint(root: Path) -> str:
    if (root / ".git").exists():
        return (
            "Use the current Git branch/worktree as the baseline; if the intended "
            "baseline is main, confirm the current checkout or compare against "
            "main before judging TODOs."
        )
    return "No root .git directory detected; confirm the selected workspace baseline before judging TODOs."


def todo_staleness_risk_notes(task_files: list[str], open_todo_count: int) -> list[str]:
    if not task_files:
        return ["No task tracker detected, so TODO/main-baseline diff cannot be performed by this audit."]
    if open_todo_count == 0:
        return ["No unchecked Markdown TODOs detected in the task tracker files."]
    return [
        "Open TODOs require a manual Todo Main-Baseline Diff Audit before implementation.",
        "Compare each open TODO with the current main or selected worktree baseline.",
        (
            "Rewrite, complete, merge, defer, operator-gate, archive, remove, "
            "or mark Needs Baseline for stale or misaligned TODOs."
        ),
        (
            "Do not treat unmerged worktree or prototype changes as mainline "
            "facts; record a rerun-after-merge note instead."
        ),
    ]


def classify_project_kind(
    code_file_count: int,
    manifest_files: list[str],
    docs_count: int,
    sensitive_signals: list[str],
) -> str:
    if code_file_count > 0 or manifest_files:
        if sensitive_signals and docs_count > 0:
            return "mixed"
        return "code"
    if sensitive_signals:
        return "evidence"
    if docs_count > 0:
        return "docs"
    return "unknown"


def classify_repo_boundary(root: Path, nested_repos: list[str]) -> str:
    root_is_repo = (root / ".git").exists()
    if root_is_repo and nested_repos:
        return "mixed_workspace"
    if root_is_repo:
        return "git_repo"
    if nested_repos:
        return "nested_repos"
    return "non_git_workspace"


def classify_scenario(
    content_state: str,
    scenario: str,
    repo_boundary: str,
    project_kind: str,
    nested_repos: list[str],
    sensitive_signals: list[str],
    manifest_files: list[str],
    role_hits: dict[str, list[str]],
) -> str:
    if content_state == "empty":
        return "empty_directory"
    if scenario == "existing_or_mature":
        if nested_repos or repo_boundary in {"nested_repos", "mixed_workspace"}:
            return "multi_repo_workspace"
        if not manifest_files and (not role_hits["requirements"] or not role_hits["traceability"]):
            return "initialized_unscoped_workspace"
        return "mature_governed_project"
    if scenario == "thin_or_partial":
        return "partially_governed_project"
    if repo_boundary in {"nested_repos", "mixed_workspace"}:
        return "multi_repo_workspace"
    if nested_repos:
        return "nested_upstream_repo"
    if project_kind == "evidence" or sensitive_signals:
        return "document_or_evidence_workspace"
    if manifest_files or project_kind == "code":
        return "single_repo_code_project"
    return "contentful_ungoverned_workspace"


def adoption_recommendation(project_layer: str) -> str:
    recommendations = {
        "empty_directory": "Minimal Scaffold",
        "contentful_ungoverned_workspace": "Inventory First",
        "initialized_unscoped_workspace": "Scope And Validation First",
        "single_repo_code_project": "Selective Integration",
        "multi_repo_workspace": "Boundary Confirmation",
        "nested_upstream_repo": "Boundary Confirmation",
        "document_or_evidence_workspace": "Lightweight SDD Evidence Governance",
        "partially_governed_project": "Gap Patch Proposal",
        "mature_governed_project": "Selective Integration",
    }
    return recommendations.get(project_layer, "Inventory First")


def classify_layer_write_policy(project_layer: str) -> dict[str, object]:
    policies: dict[str, dict[str, object]] = {
        "empty_directory": {
            "default_action": "Use Spec Kit init, then keep a minimal governance shim.",
            "write_allowed": True,
            "must_ask_user": False,
            "recommended_capability": "Spec Kit gated runner",
        },
        "contentful_ungoverned_workspace": {
            "default_action": "Inventory files and model the workspace boundary before writing.",
            "write_allowed": True,
            "must_ask_user": True,
            "recommended_capability": "governance-review",
        },
        "initialized_unscoped_workspace": {
            "default_action": "Fill missing goal, boundary, and validation fields in existing owners.",
            "write_allowed": True,
            "must_ask_user": True,
            "recommended_capability": "baseline-validation",
        },
        "single_repo_code_project": {
            "default_action": "Audit docs, code, tests, and propose selective SDD integration.",
            "write_allowed": True,
            "must_ask_user": True,
            "recommended_capability": "code-understanding plus SDD spec",
        },
        "multi_repo_workspace": {
            "default_action": "Stop and ask the user to choose the active repository.",
            "write_allowed": False,
            "must_ask_user": True,
            "recommended_capability": "baseline-validation",
        },
        "nested_upstream_repo": {
            "default_action": "Treat the nested repository as a separate upstream boundary.",
            "write_allowed": False,
            "must_ask_user": True,
            "recommended_capability": "baseline-validation",
        },
        "document_or_evidence_workspace": {
            "default_action": "Protect private inputs and record evidence boundaries.",
            "write_allowed": True,
            "must_ask_user": True,
            "recommended_capability": "governance-review",
        },
        "partially_governed_project": {
            "default_action": "Patch gaps in canonical docs only; do not create a parallel skeleton.",
            "write_allowed": True,
            "must_ask_user": True,
            "recommended_capability": "gap patch proposal",
        },
        "mature_governed_project": {
            "default_action": "Build a responsibility map and propose selective integration only.",
            "write_allowed": True,
            "must_ask_user": True,
            "recommended_capability": "selective integration",
        },
    }
    return policies.get(
        project_layer,
        {
            "default_action": "Inventory first and ask before writing.",
            "write_allowed": False,
            "must_ask_user": True,
            "recommended_capability": "governance-review",
        },
    )


def classify_structure_readiness(scenario: str, score: int) -> str:
    if scenario == "existing_or_mature":
        return "governed"
    if scenario == "thin_or_partial" or score > 0:
        return "partial"
    return "none"


def classify_content_readiness(
    role_hits: dict[str, list[str]],
    content_state: str,
    sensitive_signals: list[str],
    repo_boundary: str,
) -> str:
    if content_state == "empty":
        return "low"
    has_requirements = bool(role_hits["requirements"])
    has_tasks = bool(role_hits["tasks"])
    has_validation = bool(role_hits["validation"])
    has_state = bool(role_hits["state"])
    if has_requirements and has_tasks and has_validation and has_state and not sensitive_signals:
        return "high"
    if has_tasks or has_state or has_validation:
        if repo_boundary in {"nested_repos", "mixed_workspace"} or sensitive_signals:
            return "medium"
        return "medium"
    return "low"


def build_blocking_decisions(
    content_state: str,
    role_hits: dict[str, list[str]],
    repo_boundary: str,
    nested_repos: list[str],
    sensitive_signals: list[str],
) -> list[str]:
    blockers: list[str] = []
    if content_state == "empty":
        blockers.append("Define the first implementation goal and validation path.")
    if repo_boundary == "non_git_workspace":
        blockers.append("Decide whether the target root should become a Git repository.")
    if repo_boundary in {"nested_repos", "mixed_workspace"} or nested_repos:
        blockers.append("Select the active repository or workspace boundary before code work.")
    if sensitive_signals:
        blockers.append("Confirm private-data handling and scan exclusions before reading content.")
    if not role_hits["requirements"]:
        blockers.append("Define requirement or change-intake ownership before implementation.")
    if not role_hits["validation"]:
        blockers.append("Define validation evidence before claiming work complete.")
    return blockers


def recommend_aider(
    project_kind: str,
    repo_boundary: str,
    code_file_count: int,
    manifest_files: list[str],
    sensitive_signals: list[str],
    nested_repos: list[str],
) -> tuple[bool, str, list[str], list[str]]:
    exclusions = sorted(
        set(
            [
                ".git/",
                "node_modules/",
                ".venv/",
                "venv/",
                "dist/",
                "build/",
                "__pycache__/",
                ".env",
                ".env.*",
                "*.pem",
                "*.key",
                "*.cookie",
                "*.cookies",
            ]
            + [f"{repo}/" for repo in nested_repos]
            + sensitive_signals[:20]
        )
    )

    if repo_boundary in {"nested_repos", "mixed_workspace"}:
        return False, "Workspace boundary must be confirmed before repo-map scanning.", [], exclusions
    if sensitive_signals:
        return False, "Sensitive-path signals require explicit scan-scope confirmation first.", [], exclusions
    if project_kind not in {"code", "mixed"}:
        return False, "Target is not primarily a code repository.", [], exclusions
    if code_file_count >= 30 or len(manifest_files) >= 2:
        scan_scope = ["."]
        return True, "Codebase is large or structured enough to benefit from a repo map.", scan_scope, exclusions
    return False, "Project appears small enough for direct inspection.", [], exclusions


def collect_local_skill_names() -> list[str]:
    names: set[str] = set()
    for root in LOCAL_SKILL_ROOTS:
        if not root.exists():
            continue
        for skill_file in root.rglob("SKILL.md"):
            try:
                rel = skill_file.parent.relative_to(root).as_posix()
            except ValueError:
                continue
            if rel:
                names.add(rel.replace("/", ":"))
    return sorted(names)


def collect_local_plugin_names() -> list[str]:
    names: set[str] = set()
    for root in LOCAL_PLUGIN_CACHE_ROOTS:
        if not root.exists():
            continue
        for plugin_json in root.rglob("plugin.json"):
            try:
                data = json.loads(read_text(plugin_json))
            except json.JSONDecodeError:
                continue
            name = data.get("name")
            if isinstance(name, str) and name.strip():
                names.add(name.strip())
    return sorted(names)


def collect_route_text(root: Path, role_hits: dict[str, list[str]]) -> str:
    candidates: list[str] = []
    for role_name in ("agent_entry", "workflow"):
        candidates.extend(role_hits.get(role_name, []))
    texts: list[str] = []
    for rel in sorted(set(candidates)):
        path = root / rel
        if path.is_file():
            texts.append(read_text(path).lower())
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix.lower() in {".md", ".txt", ".mdx"}:
                    texts.append(read_text(child).lower())
    return "\n".join(texts)


def detect_capability_routing_status(root: Path, role_hits: dict[str, list[str]]) -> tuple[str, list[str]]:
    route_text = collect_route_text(root, role_hits)
    if not route_text.strip():
        return "missing", list(CAPABILITY_ROUTING_RULES)
    missing = [
        capability
        for capability, tokens in CAPABILITY_ROUTING_RULES.items()
        if not any(token in route_text for token in tokens)
    ]
    if not missing:
        return "complete", []
    if len(missing) == len(CAPABILITY_ROUTING_RULES):
        return "missing", missing
    return "partial", missing


def detect_capability_availability(
    local_skill_names: list[str],
    local_plugin_names: list[str],
) -> dict[str, dict[str, object]]:
    skill_catalog = " ".join(local_skill_names).lower()
    plugin_catalog = " ".join(local_plugin_names).lower()
    availability: dict[str, dict[str, object]] = {}
    for capability, checks in CAPABILITY_LOCAL_CHECKS.items():
        evidence: list[str] = []
        status = "missing"
        for skill_name in checks["skills"]:
            skill_status, detail = skill_readability_status(skill_name)
            if skill_status == "available":
                status = "available"
                evidence.append(detail)
            elif skill_status == "installed_but_unverified" and status != "available":
                status = "installed_but_unverified"
                evidence.append(detail)
            elif skill_name in skill_catalog and status == "missing":
                status = "installed_but_unverified"
                evidence.append(f"Matched local skill catalog entry for {skill_name}.")
        for plugin_name in checks["plugins"]:
            if plugin_name in plugin_catalog:
                status = "available"
                evidence.append(f"Matched local plugin {plugin_name}.")
        for command_name in checks["commands"]:
            command_path = shutil.which(command_name)
            if command_path:
                status = "available"
                evidence.append(f"Command `{command_name}` found at {command_path}.")
        availability[capability] = {
            "status": status,
            "evidence": evidence or ["No local skill, plugin, or command match found."],
        }
    return availability


def missing_or_unverified_capabilities(
    capability_routing_status: str,
    missing_routing_capabilities: list[str],
    capability_availability: dict[str, dict[str, object]],
) -> list[str]:
    missing: list[str] = []
    for capability in missing_routing_capabilities:
        missing.append(f"routing:{capability}")
    for capability, details in capability_availability.items():
        if details["status"] != "available":
            missing.append(f"local:{capability}:{details['status']}")
    if capability_routing_status == "missing" and not missing_routing_capabilities:
        missing.append("routing:all")
    return missing


def capability_fit_status(
    capability_routing_status: str,
    missing_or_unverified: list[str],
) -> str:
    if not missing_or_unverified and capability_routing_status == "complete":
        return "complete"
    if capability_routing_status == "missing":
        return "missing_routing"
    if any(item.endswith(":missing") for item in missing_or_unverified):
        return "partial"
    if missing_or_unverified:
        return "unverified"
    return "partial"


def detect_local_matches(
    names: list[str],
    keywords: tuple[str, ...],
) -> list[str]:
    lowered_names = [(name, name.lower()) for name in names]
    matches = [name for name, lowered in lowered_names if any(keyword in lowered for keyword in keywords)]
    return matches[:10]


def classify_workflow_level(
    scenario: str,
    content_readiness: str,
    repo_boundary: str,
    sensitive_signals: list[str],
    open_todo_count: int,
) -> str:
    if scenario == "existing_or_mature" and open_todo_count > 0:
        return "doc_governance"
    if repo_boundary in {"nested_repos", "mixed_workspace"} or sensitive_signals:
        return "high_risk_change"
    if content_readiness == "high" and scenario == "existing_or_mature":
        return "standard_change"
    if content_readiness == "medium" or open_todo_count > 0:
        return "light_change"
    return "readonly"


def recommend_capability_slots(
    project_kind: str,
    scenario: str,
    repo_boundary: str,
    content_readiness: str,
    open_todo_count: int,
    sensitive_signals: list[str],
    test_signals: list[str],
    manifest_files: list[str],
    task_text: str,
    local_skill_names: list[str],
    local_plugin_names: list[str],
) -> list[dict[str, object]]:
    slots: list[dict[str, object]] = []
    combined_catalog = sorted(set(local_skill_names + local_plugin_names))
    uiux_matches = detect_local_matches(
        combined_catalog,
        ("uiux", "ui-ux", "frontend", "design", "shadcn", "visual"),
    )
    governance_matches = detect_local_matches(
        combined_catalog,
        ("plan-cross-validation", "agentic-project-init", "governance", "baseline"),
    )
    debugging_matches = detect_local_matches(
        combined_catalog,
        ("systematic-debugging", "debug", "troubleshoot"),
    )
    verification_matches = detect_local_matches(
        combined_catalog,
        ("verification", "validation", "test", "check"),
    )
    code_understanding_matches = detect_local_matches(
        combined_catalog,
        ("aider", "repo-map", "code-understanding"),
    )
    parallel_matches = detect_local_matches(
        combined_catalog,
        ("parallel", "subagent", "worktree"),
    )
    release_matches = detect_local_matches(
        combined_catalog,
        ("handoff", "finishing", "commit", "push"),
    )
    implementation_matches = detect_local_matches(
        combined_catalog,
        ("implementation", "executing", "tdd"),
    )

    def add(
        slot: str,
        reason: str,
        confidence: str = "medium",
        available_matches: list[str] | None = None,
    ) -> None:
        if slot not in CAPABILITY_SLOTS:
            return
        if any(existing["slot"] == slot for existing in slots):
            return
        item: dict[str, object] = {
            "slot": slot,
            "reason": reason,
            "confidence": confidence,
        }
        if available_matches:
            item["available_local_matches"] = available_matches
        slots.append(item)

    task_text_lower = task_text.lower()
    uiux_task_signal = any(token in task_text_lower for token in ("ui", "ux", "frontend", "layout", "visual", "design"))
    debugging_task_signal = any(token in task_text_lower for token in ("debug", "bug", "failure", "error", "broken"))
    parallel_task_signal = any(token in task_text_lower for token in ("parallel", "split", "subagent", "worktree"))
    implementation_task_signal = any(
        token in task_text_lower
        for token in ("implement", "build", "ship", "feature", "code")
    )
    verification_task_signal = any(token in task_text_lower for token in ("verify", "test", "audit", "check", "proof"))
    governance_task_signal = any(
        token in task_text_lower
        for token in (
            "todo",
            "baseline",
            "plan",
            "roadmap",
            "phase",
            "goal",
            "doc",
            "documentation",
            "cr",
        )
    )

    if open_todo_count > 0 or scenario == "existing_or_mature" or governance_task_signal:
        add(
            "baseline-validation",
            "Open TODOs or mature governance call for baseline diff review.",
            "high",
            governance_matches,
        )
        add(
            "governance-review",
            "Task/phase/CR hygiene needs doc governance before implementation.",
            "high",
            governance_matches,
        )
    if project_kind in {"code", "mixed"} and len(manifest_files) >= 2:
        add(
            "code-understanding",
            "Structured code repository may benefit from repo-map style reading.",
            "medium",
            code_understanding_matches,
        )
    if repo_boundary in {"nested_repos", "mixed_workspace"} or sensitive_signals:
        add(
            "baseline-validation",
            "Boundary or sensitive-path signals need careful baseline scoping.",
            "high",
            governance_matches,
        )
    if uiux_task_signal:
        add(
            "uiux-design",
            "UI-sensitive work benefits from explicit visual/layout review.",
            "medium",
            uiux_matches,
        )
    if debugging_task_signal or scenario == "existing_or_mature" and "debug" in task_text_lower:
        add(
            "debugging",
            "Unexpected behavior or regressions need focused debugging.",
            "medium",
            debugging_matches,
        )
    if content_readiness in {"medium", "high"} and open_todo_count == 0:
        add(
            "implementation",
            "Current baseline looks stable enough for direct implementation.",
            "medium",
            implementation_matches,
        )
    if test_signals or verification_task_signal:
        add(
            "verification",
            "Existing tests or validation hooks should be used to prove the change.",
            "medium",
            verification_matches,
        )
    if repo_boundary in {"nested_repos", "mixed_workspace"} or parallel_task_signal:
        add(
            "parallel-work",
            "Multiple boundaries suggest careful split ownership if work is parallelized.",
            "medium",
            parallel_matches,
        )
    if project_kind != "code":
        add(
            "release-handoff",
            "Documentation/evidence changes may still need a clean handoff summary.",
            "medium",
            release_matches,
        )

    return slots


def detect_agent_entry_rule_gaps(
    todo_baseline_review_rule_required: bool,
    todo_baseline_review_rule_present: bool,
    todo_baseline_review_rule_status: str,
) -> list[str]:
    gaps: list[str] = []
    if todo_baseline_review_rule_required and not todo_baseline_review_rule_present:
        gaps.append("Target agent-entry contract is missing a Todo Baseline Review Rule.")
    if todo_baseline_review_rule_status == "missing_agent_entry":
        gaps.append("No agent-entry contract was found to carry the baseline review rule.")
    return gaps


INIT_MODE_RECOMMENDATIONS = {
    "mature_governed_project": (
        "Use selective integration mode: do not scaffold or create parallel docs; "
        "map responsibilities, run a Todo Main-Baseline Diff Audit, patch "
        "canonical docs for stale or misaligned TODOs, and create only "
        "truly missing owners. When adding "
        "hard guardrails, define exact "
        "forbidden_files and forbidden_dirs and make project checks enforce "
        "the same path set."
    ),
    "partially_governed_project": (
        "Use selective integration mode: do not scaffold or create parallel docs; "
        "map responsibilities, run a Todo Main-Baseline Diff Audit, patch "
        "canonical docs for stale or misaligned TODOs, and create only "
        "truly missing owners. When adding "
        "hard guardrails, define exact "
        "forbidden_files and forbidden_dirs and make project checks enforce "
        "the same path set."
    ),
    "initialized_unscoped_workspace": (
        "Use scope-and-validation mode: the scaffold exists, but do not "
        "start implementation until goal, selected boundary, requirement "
        "owner, and validation evidence are defined."
    ),
    "multi_repo_workspace": (
        "Use boundary-confirmation mode: do not scaffold or run automatic "
        "repo-map scans until the user selects the active repository."
    ),
    "nested_upstream_repo": (
        "Use boundary-confirmation mode: do not scaffold or run automatic "
        "repo-map scans until the user selects the active repository."
    ),
    "document_or_evidence_workspace": (
        "Use evidence-governance mode: protect sensitive inputs, avoid "
        "automatic code-understanding scans, and record only supported facts."
    ),
}

EMPTY_WORKSPACE_RECOMMENDATION = (
    "Use greenfield scaffold mode: create the minimal SDD-first hybrid "
    "agentic skeleton and keep implementation_readiness false until "
    "goal, boundary, and validation are defined."
)

CONTENTFUL_WORKSPACE_RECOMMENDATION = (
    "Use contentful-workspace mode: inventory existing files, preserve "
    "boundaries, protect sensitive paths, then scaffold only supported facts."
)

BASELINE_GATE_TRIGGERS = (
    "create_or_update_cr",
    "generate_or_reorder_todos",
    "write_goal_or_phase_plan",
    "generate_cross_validation_brief",
    "start_implementation",
    "code_review_or_acceptance",
    "close_out_docs",
)

BASELINE_GATE_REQUIRED_FIELDS = (
    "baseline_source",
    "baseline_evidence_read",
    "existing_behavior_to_preserve",
    "out_of_scope_or_must_not_redesign",
    "old_baseline_conflict_rule",
)

TODO_BASELINE_CLASSIFICATIONS = (
    "active/current",
    "future-valid",
    "deferred",
    "Needs Confirmation",
    "operator-gated",
    "historical/archive-only",
    "stale/remove",
    "duplicate/overlap",
    "Needs Baseline",
)

TODO_MAIN_BASELINE_DIFF_PURPOSE = (
    "Compare open TODOs against current main or the selected worktree "
    "baseline and repair stale, duplicate, conflicting, already-covered, "
    "or under-evidenced items before implementation."
)


def recommended_init_mode(project_layer: str, content_state: str) -> str:
    if content_state == "empty":
        return EMPTY_WORKSPACE_RECOMMENDATION
    return INIT_MODE_RECOMMENDATIONS.get(project_layer, CONTENTFUL_WORKSPACE_RECOMMENDATION)


def workflow_recommendations(workflow_level: str) -> list[dict[str, object]]:
    reason = (
        "Mature project with open TODOs should start in doc governance."
        if workflow_level == "doc_governance"
        else "Current facts suggest a lighter or direct workflow."
    )
    return [
        {
            "workflow_level": workflow_level,
            "reason": reason,
            "details": [
                "current baseline checked",
                "open TODOs compared to baseline",
                "smallest matching workflow level selected",
            ],
        }
    ]


def implementation_readiness_summary(
    todo_baseline_audit_required: bool,
    todo_baseline_review_rule_required: bool,
    todo_baseline_review_rule_present: bool,
) -> str:
    if not todo_baseline_audit_required:
        return "No open TODO main-baseline diff blocker detected by the structural scan."
    rule_note = (
        " The project agent-entry file also needs a Todo Baseline Review Rule."
        if todo_baseline_review_rule_required and not todo_baseline_review_rule_present
        else ""
    )
    return "Open TODOs require a manual Todo Main-Baseline Diff Audit before implementation." + rule_note


def collect_audit_inputs(root: Path) -> dict[str, object]:
    role_hits: dict[str, list[str]] = {}
    for role in ROLES:
        role_hits[role.name] = collect_matching_existing(root, role.candidates)

    top_level = [path for path in root.iterdir() if is_meaningful(path)] if root.exists() else []
    content_state = "empty" if not top_level else "contentful"
    files, dirs = iter_project_paths(root)
    docs = collect_docs(root)
    docs_count = len(docs)
    nested_repos = collect_nested_repos(root)
    manifest_files = collect_matching_existing(root, MANIFEST_FILES)
    test_signals = collect_matching_existing(root, TEST_SIGNAL_PATHS)
    ci_signals = collect_matching_existing(root, CI_SIGNAL_PATHS)
    sensitive_signals = collect_sensitive_signals(root, files, dirs)
    code_file_count = count_code_files(files)

    covered = [name for name, hits in role_hits.items() if hits]
    score = len(covered)
    task_tracker_files = role_hits["tasks"]
    open_todo_count = estimate_open_todos(root, task_tracker_files)
    todo_baseline_readiness = classify_todo_baseline_readiness(task_tracker_files, open_todo_count)
    todo_baseline_audit_required = todo_baseline_readiness == "manual_audit_required"
    (
        todo_baseline_review_rule_required,
        agent_entry_files,
        todo_baseline_review_rule_present,
        todo_baseline_review_rule_status,
        todo_baseline_review_rule_suggestion,
    ) = todo_baseline_rule_status(root, role_hits, task_tracker_files, open_todo_count)

    return {
        "role_hits": role_hits,
        "top_level": top_level,
        "content_state": content_state,
        "docs_count": docs_count,
        "nested_repos": nested_repos,
        "manifest_files": manifest_files,
        "test_signals": test_signals,
        "ci_signals": ci_signals,
        "sensitive_signals": sensitive_signals,
        "code_file_count": code_file_count,
        "covered": covered,
        "score": score,
        "task_tracker_files": task_tracker_files,
        "open_todo_count": open_todo_count,
        "todo_baseline_readiness": todo_baseline_readiness,
        "todo_baseline_audit_required": todo_baseline_audit_required,
        "todo_baseline_review_rule_required": todo_baseline_review_rule_required,
        "agent_entry_files": agent_entry_files,
        "todo_baseline_review_rule_present": todo_baseline_review_rule_present,
        "todo_baseline_review_rule_status": todo_baseline_review_rule_status,
        "todo_baseline_review_rule_suggestion": todo_baseline_review_rule_suggestion,
    }


def classify_governance_scenario(score: int, has_entry: bool, docs_count: int) -> str:
    if score >= 6 or (has_entry and docs_count >= 5):
        scenario = "existing_or_mature"
    elif score >= 2 or docs_count > 0 or has_entry:
        scenario = "thin_or_partial"
    else:
        scenario = "new_or_empty"
    return scenario


def build_project_context(root: Path, facts: dict[str, object]) -> dict[str, object]:
    role_hits = facts["role_hits"]
    assert isinstance(role_hits, dict)
    docs_count = int(facts["docs_count"])
    nested_repos = facts["nested_repos"]
    manifest_files = facts["manifest_files"]
    sensitive_signals = facts["sensitive_signals"]
    top_level = facts["top_level"]
    assert isinstance(nested_repos, list)
    assert isinstance(manifest_files, list)
    assert isinstance(sensitive_signals, list)
    assert isinstance(top_level, list)

    scenario = classify_governance_scenario(
        int(facts["score"]),
        bool(role_hits["agent_entry"]),
        docs_count,
    )
    repo_boundary = classify_repo_boundary(root, nested_repos)
    project_kind = classify_project_kind(
        int(facts["code_file_count"]),
        manifest_files,
        docs_count,
        sensitive_signals,
    )
    project_scenario = classify_scenario(
        str(facts["content_state"]),
        scenario,
        repo_boundary,
        project_kind,
        nested_repos,
        sensitive_signals,
        manifest_files,
        role_hits,
    )
    project_layer = project_scenario
    layer_policy = classify_layer_write_policy(project_layer)
    spec_kit_cli = detect_spec_kit_cli()
    spec_kit_project_status = detect_spec_kit_project_status(root)
    spec_kit_policy_result = classify_spec_kit_policy(
        root,
        top_level,
        project_layer,
        repo_boundary,
        nested_repos,
        sensitive_signals,
        spec_kit_cli,
        spec_kit_project_status,
    )
    return {
        "scenario": scenario,
        "repo_boundary": repo_boundary,
        "project_kind": project_kind,
        "project_scenario": project_scenario,
        "project_layer": project_layer,
        "layer_policy": layer_policy,
        "spec_kit_cli": spec_kit_cli,
        "spec_kit_project_status": spec_kit_project_status,
        "spec_kit_policy_result": spec_kit_policy_result,
    }


def build_workflow_context(
    root: Path,
    task_text: str,
    facts: dict[str, object],
    context: dict[str, object],
) -> dict[str, object]:
    role_hits = facts["role_hits"]
    assert isinstance(role_hits, dict)
    scenario = str(context["scenario"])
    repo_boundary = str(context["repo_boundary"])
    project_kind = str(context["project_kind"])
    content_state = str(facts["content_state"])
    sensitive_signals = facts["sensitive_signals"]
    nested_repos = facts["nested_repos"]
    manifest_files = facts["manifest_files"]
    test_signals = facts["test_signals"]
    score = int(facts["score"])
    assert isinstance(sensitive_signals, list)
    assert isinstance(nested_repos, list)
    assert isinstance(manifest_files, list)
    assert isinstance(test_signals, list)

    structure_readiness = classify_structure_readiness(scenario, score)
    content_readiness = classify_content_readiness(role_hits, content_state, sensitive_signals, repo_boundary)
    workflow_level = classify_workflow_level(
        scenario,
        content_readiness,
        repo_boundary,
        sensitive_signals,
        int(facts["open_todo_count"]),
    )
    blocking_decisions = build_blocking_decisions(
        content_state,
        role_hits,
        repo_boundary,
        nested_repos,
        sensitive_signals,
    )
    implementation_readiness = (
        scenario == "existing_or_mature"
        and content_readiness == "high"
        and not blocking_decisions
        and not facts["todo_baseline_audit_required"]
        and repo_boundary not in {"nested_repos", "mixed_workspace"}
        and not sensitive_signals
    )
    aider_recommended, aider_reason, aider_scan_scope, aider_exclusions = recommend_aider(
        project_kind,
        repo_boundary,
        int(facts["code_file_count"]),
        manifest_files,
        sensitive_signals,
        nested_repos,
    )
    local_skill_names = collect_local_skill_names()
    local_plugin_names = collect_local_plugin_names()
    capability_routing_status, missing_routing_capabilities = detect_capability_routing_status(root, role_hits)
    capability_availability = detect_capability_availability(local_skill_names, local_plugin_names)
    missing_or_unverified = missing_or_unverified_capabilities(
        capability_routing_status,
        missing_routing_capabilities,
        capability_availability,
    )
    fit_status = capability_fit_status(capability_routing_status, missing_or_unverified)
    capability_slot_recommendations = recommend_capability_slots(
        project_kind,
        scenario,
        repo_boundary,
        content_readiness,
        int(facts["open_todo_count"]),
        sensitive_signals,
        test_signals,
        manifest_files,
        task_text,
        local_skill_names,
        local_plugin_names,
    )
    agent_entry_rule_gaps = detect_agent_entry_rule_gaps(
        bool(facts["todo_baseline_review_rule_required"]),
        bool(facts["todo_baseline_review_rule_present"]),
        str(facts["todo_baseline_review_rule_status"]),
    )
    contract_seed = {
        "implementation_readiness": implementation_readiness,
        "blocking_decisions": blocking_decisions,
    }
    agent_loop_contract_readiness = build_loop_readiness(contract_seed)
    return {
        "structure_readiness": structure_readiness,
        "content_readiness": content_readiness,
        "workflow_level": workflow_level,
        "blocking_decisions": blocking_decisions,
        "implementation_readiness": implementation_readiness,
        "aider_recommended": aider_recommended,
        "aider_reason": aider_reason,
        "aider_scan_scope": aider_scan_scope,
        "aider_exclusions": aider_exclusions,
        "local_skill_names": local_skill_names,
        "local_plugin_names": local_plugin_names,
        "capability_routing_status": capability_routing_status,
        "missing_routing_capabilities": missing_routing_capabilities,
        "capability_availability": capability_availability,
        "fit_status": fit_status,
        "missing_or_unverified": missing_or_unverified,
        "capability_slot_recommendations": capability_slot_recommendations,
        "agent_entry_rule_gaps": agent_entry_rule_gaps,
        "agent_loop_contract_readiness": agent_loop_contract_readiness,
    }


def result_project_section(root: Path, facts: dict[str, object], context: dict[str, object]) -> dict[str, object]:
    role_hits = facts["role_hits"]
    assert isinstance(role_hits, dict)
    spec_kit_policy_result = context["spec_kit_policy_result"]
    assert isinstance(spec_kit_policy_result, dict)
    project_layer = str(context["project_layer"])
    return {
        "root": str(root),
        "scenario": context["scenario"],
        "project_scenario": context["project_scenario"],
        "project_layer": context["project_layer"],
        "development_model_recommendation": DEVELOPMENT_MODEL_RECOMMENDATION,
        "adoption_recommendation": adoption_recommendation(project_layer),
        "layer_policy": context["layer_policy"],
        "spec_kit_cli": context["spec_kit_cli"],
        "spec_kit_project_status": context["spec_kit_project_status"],
        "spec_kit_policy": spec_kit_policy_result["policy"],
        "spec_kit_policy_reasons": spec_kit_policy_result["reasons"],
        "spec_kit_command_plan": spec_kit_policy_result["command_plan"],
        "spec_kit_force_allowed": spec_kit_policy_result["force_allowed"],
        "spec_kit_collision_risk": spec_kit_policy_result["collision_risk"],
        "spec_kit_next_skill": spec_kit_policy_result["next_skill"],
        "content_state": facts["content_state"],
        "repo_boundary": context["repo_boundary"],
        "project_kind": context["project_kind"],
        "score": facts["score"],
        "docs_count": facts["docs_count"],
        "code_file_count": facts["code_file_count"],
        "covered_roles": facts["covered"],
        "missing_roles": [role.name for role in ROLES if not role_hits[role.name]],
        "role_hits": role_hits,
        "nested_repos": facts["nested_repos"],
        "manifest_files": facts["manifest_files"],
        "test_signals": facts["test_signals"],
        "ci_signals": facts["ci_signals"],
        "sensitive_signals": facts["sensitive_signals"],
    }


def result_todo_section(root: Path, facts: dict[str, object], workflow: dict[str, object]) -> dict[str, object]:
    return {
        "structure_readiness": workflow["structure_readiness"],
        "content_readiness": workflow["content_readiness"],
        "workflow_level": workflow["workflow_level"],
        "todo_baseline_readiness": facts["todo_baseline_readiness"],
        "todo_baseline_audit_required": facts["todo_baseline_audit_required"],
        "todo_main_baseline_diff_required": facts["todo_baseline_audit_required"],
        "agent_entry_files": facts["agent_entry_files"],
        "todo_baseline_review_rule_required": facts["todo_baseline_review_rule_required"],
        "todo_baseline_review_rule_present": facts["todo_baseline_review_rule_present"],
        "todo_baseline_review_rule_status": facts["todo_baseline_review_rule_status"],
        "todo_baseline_review_rule_suggestion": facts["todo_baseline_review_rule_suggestion"],
        "todo_baseline_review_rule_recommended_snippet": TODO_BASELINE_REVIEW_RULE_SNIPPET,
        "todo_baseline_source_hint": todo_baseline_source_hint(root),
        "todo_baseline_required_columns": list(TODO_BASELINE_REQUIRED_COLUMNS),
        "todo_diff_review_required_actions": list(TODO_DIFF_REVIEW_REQUIRED_ACTIONS),
        "todo_staleness_risk_notes": todo_staleness_risk_notes(
            facts["task_tracker_files"],  # type: ignore[arg-type]
            int(facts["open_todo_count"]),
        ),
        "workflow_recommendations": workflow_recommendations(str(workflow["workflow_level"])),
    }


def result_capability_section(workflow: dict[str, object]) -> dict[str, object]:
    return {
        "capability_routing_status": workflow["capability_routing_status"],
        "missing_capability_routing": workflow["missing_routing_capabilities"],
        "capability_availability": workflow["capability_availability"],
        "capability_fit_status": workflow["fit_status"],
        "missing_or_unverified_capabilities": workflow["missing_or_unverified"],
        "capability_slot_recommendations": workflow["capability_slot_recommendations"],
        "local_skill_names": workflow["local_skill_names"],
        "local_plugin_names": workflow["local_plugin_names"],
        "agent_entry_rule_gaps": workflow["agent_entry_rule_gaps"],
        "agent_loop_contract_readiness": workflow["agent_loop_contract_readiness"],
        "machine_readable_governance_status": machine_readable_governance_status(),
        "recommended_contract_files": recommended_contract_files(),
    }


def result_readiness_section(facts: dict[str, object], workflow: dict[str, object]) -> dict[str, object]:
    return {
        "task_tracker_files": facts["task_tracker_files"],
        "open_todo_count_estimate": facts["open_todo_count"],
        "implementation_readiness_notes": implementation_readiness_summary(
            bool(facts["todo_baseline_audit_required"]),
            bool(facts["todo_baseline_review_rule_required"]),
            bool(facts["todo_baseline_review_rule_present"]),
        ),
        "implementation_readiness": workflow["implementation_readiness"],
        "blocking_decisions": workflow["blocking_decisions"],
        "aider_recommended": workflow["aider_recommended"],
        "aider_reason": workflow["aider_reason"],
        "aider_scan_scope": workflow["aider_scan_scope"],
        "aider_exclusions": workflow["aider_exclusions"],
    }


def result_static_contract_section(facts: dict[str, object], recommendation: str) -> dict[str, object]:
    return {
        "recommended_init_mode": recommendation,
        "default_skeleton_files": list(DEFAULT_SKELETON_FILES),
        "default_skeleton_dirs": list(DEFAULT_SKELETON_DIRS),
        "baseline_gate_triggers": list(BASELINE_GATE_TRIGGERS),
        "baseline_gate_required_fields": list(BASELINE_GATE_REQUIRED_FIELDS),
        "todo_baseline_classifications": list(TODO_BASELINE_CLASSIFICATIONS),
        "todo_main_baseline_diff_audit": {
            "compatibility_alias": "Todo Baseline Coverage Audit",
            "purpose": TODO_MAIN_BASELINE_DIFF_PURPOSE,
            "required_actions": list(TODO_DIFF_REVIEW_REQUIRED_ACTIONS),
            "agent_entry_rule": TODO_BASELINE_REVIEW_RULE_TITLE,
            "agent_entry_rule_required": facts["todo_baseline_review_rule_required"],
            "agent_entry_rule_present": facts["todo_baseline_review_rule_present"],
        },
        "recommendation": recommendation,
    }


def build_audit_result(
    root: Path,
    facts: dict[str, object],
    context: dict[str, object],
    workflow: dict[str, object],
) -> dict[str, object]:
    recommendation = recommended_init_mode(str(context["project_layer"]), str(facts["content_state"]))
    result: dict[str, object] = {}
    sections = (
        result_project_section(root, facts, context),
        result_todo_section(root, facts, workflow),
        result_capability_section(workflow),
        result_readiness_section(facts, workflow),
        result_static_contract_section(facts, recommendation),
    )
    for section in sections:
        result.update(section)
    return result


def analyze(root: Path, task_text: str = "") -> dict[str, object]:
    facts = collect_audit_inputs(root)
    context = build_project_context(root, facts)
    workflow = build_workflow_context(root, task_text, facts, context)
    return build_audit_result(root, facts, context, workflow)


def print_list(title: str, values: list[str]) -> None:
    print(f"{title}:")
    if values:
        for item in values:
            print(f"- {item}")
    else:
        print("- none")
    print()


def print_summary_section(result: dict[str, object]) -> None:
    keys = (
        ("Root", "root"),
        ("Scenario", "scenario"),
        ("Project scenario", "project_scenario"),
        ("Project layer", "project_layer"),
        ("Development model recommendation", "development_model_recommendation"),
        ("Adoption recommendation", "adoption_recommendation"),
        ("Capability fit status", "capability_fit_status"),
        ("Spec Kit policy", "spec_kit_policy"),
        ("Spec Kit next skill", "spec_kit_next_skill"),
        ("Spec Kit collision risk", "spec_kit_collision_risk"),
        ("Content state", "content_state"),
        ("Repo boundary", "repo_boundary"),
        ("Project kind", "project_kind"),
        ("Score", "score"),
        ("Docs count", "docs_count"),
        ("Code file count", "code_file_count"),
        ("Structure readiness", "structure_readiness"),
        ("Content readiness", "content_readiness"),
        ("Workflow level", "workflow_level"),
        ("TODO baseline readiness", "todo_baseline_readiness"),
        ("TODO baseline audit required", "todo_baseline_audit_required"),
        ("TODO main-baseline diff required", "todo_main_baseline_diff_required"),
    )
    for label, key in keys:
        print(f"{label}: {result[key]}")
    entry_files = result["agent_entry_files"]
    print(f"Agent entry files: {', '.join(entry_files) if entry_files else 'none'}")
    print(f"Todo Baseline Review Rule required: {result['todo_baseline_review_rule_required']}")
    print(f"Todo Baseline Review Rule present: {result['todo_baseline_review_rule_present']}")
    print(f"Todo Baseline Review Rule status: {result['todo_baseline_review_rule_status']}")
    if result["todo_baseline_review_rule_suggestion"]:
        print(f"Todo Baseline Review Rule suggestion: {result['todo_baseline_review_rule_suggestion']}")
    print(f"TODO baseline source hint: {result['todo_baseline_source_hint']}")
    print(f"Open TODO count estimate: {result['open_todo_count_estimate']}")
    print(f"Implementation readiness: {result['implementation_readiness']}")
    print(f"Implementation readiness notes: {result['implementation_readiness_notes']}")
    contract_readiness = result["agent_loop_contract_readiness"]
    assert isinstance(contract_readiness, dict)
    print(f"Agent loop contract status: {contract_readiness.get('status')}")
    print(f"Agent loop next decision: {contract_readiness.get('next_decision')}")
    governance_status = result["machine_readable_governance_status"]
    assert isinstance(governance_status, dict)
    print(f"Machine-readable governance status: {governance_status.get('status')}")
    print()


def print_spec_kit_section(result: dict[str, object]) -> None:
    print("Layer policy:")
    layer_policy = result["layer_policy"]
    assert isinstance(layer_policy, dict)
    for key, value in layer_policy.items():
        print(f"- {key}: {value}")
    print()
    print("Spec Kit CLI:")
    spec_kit_cli = result["spec_kit_cli"]
    assert isinstance(spec_kit_cli, dict)
    for key in ("path", "available", "version", "check_status", "ready"):
        print(f"- {key}: {spec_kit_cli.get(key)}")
    print_list("Spec Kit policy reasons", result["spec_kit_policy_reasons"])  # type: ignore[arg-type]
    print("Spec Kit command plan:")
    print(json.dumps(result["spec_kit_command_plan"], ensure_ascii=False, indent=2))
    print()


def print_responsibility_section(result: dict[str, object]) -> None:
    print("Responsibility map:")
    role_hits = result["role_hits"]
    assert isinstance(role_hits, dict)
    for role in ROLES:
        hits = role_hits.get(role.name, [])
        status = "covered" if hits else "missing"
        print(f"- {role.name}: {status}")
        if hits:
            for hit in hits:
                print(f"  - {hit}")
    print()


def print_inventory_section(result: dict[str, object]) -> None:
    print_list("Manifest files", result["manifest_files"])  # type: ignore[arg-type]
    print_list("Test signals", result["test_signals"])  # type: ignore[arg-type]
    print_list("CI signals", result["ci_signals"])  # type: ignore[arg-type]
    print_list("Task tracker files", result["task_tracker_files"])  # type: ignore[arg-type]
    print_list("Nested repositories", result["nested_repos"])  # type: ignore[arg-type]
    print_list("Sensitive path signals", result["sensitive_signals"])  # type: ignore[arg-type]
    print(f"Aider recommended: {result['aider_recommended']}")
    print(f"Aider reason: {result['aider_reason']}")
    print_list("Aider scan scope", result["aider_scan_scope"])  # type: ignore[arg-type]
    print_list("Aider exclusions", result["aider_exclusions"])  # type: ignore[arg-type]
    print_list("Blocking decisions", result["blocking_decisions"])  # type: ignore[arg-type]
    print_list("Agent entry rule gaps", result["agent_entry_rule_gaps"])  # type: ignore[arg-type]
    print(f"Capability routing status: {result['capability_routing_status']}")
    print_list("Missing capability routing", result["missing_capability_routing"])  # type: ignore[arg-type]
    print_list(
        "Missing or unverified capabilities",
        result["missing_or_unverified_capabilities"],  # type: ignore[arg-type]
    )
    print_list("Local skill names", result["local_skill_names"])  # type: ignore[arg-type]
    print_list("Local plugin names", result["local_plugin_names"])  # type: ignore[arg-type]


def print_baseline_gate_section(result: dict[str, object]) -> None:
    print("Default skeleton paths:")
    for item in result["default_skeleton_files"]:
        print(f"- file: {item}")
    for item in result["default_skeleton_dirs"]:
        print(f"- dir: {item}")
    print()
    print("Current Baseline Gate triggers:")
    for item in result["baseline_gate_triggers"]:
        print(f"- {item}")
    print()
    print("Current Baseline Gate required fields:")
    for item in result["baseline_gate_required_fields"]:
        print(f"- {item}")
    print()
    print("Todo Main-Baseline Diff Audit required columns:")
    for item in result["todo_baseline_required_columns"]:
        print(f"- {item}")
    print()
    print("Todo Main-Baseline Diff Audit required actions:")
    for item in result["todo_diff_review_required_actions"]:
        print(f"- {item}")
    print()
    if result["todo_baseline_review_rule_required"]:
        print("Recommended AGENTS.md Todo Baseline Review Rule snippet:")
        print(result["todo_baseline_review_rule_recommended_snippet"])
        print()
    print("Todo staleness risk notes:")
    for item in result["todo_staleness_risk_notes"]:
        print(f"- {item}")
    print()
    print("Todo Main-Baseline Diff Audit classifications:")
    for item in result["todo_baseline_classifications"]:
        print(f"- {item}")
    print()


def print_recommendation_section(result: dict[str, object]) -> None:
    print_list(
        "Workflow recommendations",
        [
            json.dumps(item, ensure_ascii=False)
            for item in result["workflow_recommendations"]  # type: ignore[index]
        ],
    )
    print_list(
        "Capability slot recommendations",
        [
            json.dumps(item, ensure_ascii=False)
            for item in result["capability_slot_recommendations"]  # type: ignore[index]
        ],
    )
    print(f"Recommendation: {result['recommendation']}")


def print_text(result: dict[str, object]) -> None:
    print_summary_section(result)
    print_spec_kit_section(result)
    print_responsibility_section(result)
    print_inventory_section(result)
    print_baseline_gate_section(result)
    print_recommendation_section(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="Project root")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    parser.add_argument("--task-text", default="", help="Optional task text for route classification")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    task_text = (args.task_text or "").strip()
    result = analyze(root, task_text)
    if task_text:
        lowered = task_text.lower()
        if any(
            token in lowered
            for token in ["todo", "baseline", "plan", "roadmap", "phase", "goal", "doc", "documentation"]
        ):
            result["task_route_classification"] = "doc_governance"
        elif any(token in lowered for token in ["ui", "ux", "frontend", "layout", "visual", "design"]):
            result["task_route_classification"] = "uiux-design"
        elif any(token in lowered for token in ["debug", "bug", "failure", "error", "broken"]):
            result["task_route_classification"] = "debugging"
        elif any(token in lowered for token in ["parallel", "split", "subagent", "worktree"]):
            result["task_route_classification"] = "parallel_candidate"
        elif any(token in lowered for token in ["implement", "build", "ship", "feature", "code"]):
            result["task_route_classification"] = "implementation"
        else:
            result["task_route_classification"] = "readonly"
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
