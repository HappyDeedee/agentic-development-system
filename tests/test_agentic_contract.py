import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"


def run_script(script_name, *args):
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), *args],
        cwd=str(PLUGIN_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"{script_name} failed with {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed.stdout


class AgenticContractTests(unittest.TestCase):
    def test_audit_emits_legacy_and_contract_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = run_script("audit_agentic_system.py", temp_dir, "--json")
            audit = json.loads(output)

        self.assertIn("project_layer", audit)
        self.assertIn("implementation_readiness", audit)
        self.assertIn("agent_loop_contract_readiness", audit)
        self.assertIn("machine_readable_governance_status", audit)
        self.assertIn("recommended_contract_files", audit)
        self.assertEqual(
            audit["agent_loop_contract_readiness"]["loop"],
            ["observe", "plan", "act", "verify", "update_state", "decide_next_loop"],
        )

    def test_export_and_validate_contract_for_temp_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            export_output = run_script("export_agentic_contract.py", temp_dir)
            contract = json.loads(export_output)
            validate_output = run_script("validate_agentic_contract.py", temp_dir, "--json")
            validation = json.loads(validate_output)

        self.assertEqual(contract["schema_version"], "agentic-loop-contract/v1")
        self.assertEqual(contract["loop"]["contract_order"][0], "observe")
        self.assertTrue(validation["valid"], validation)
        self.assertEqual(validation["schema_version"], "agentic-contract-validation/v1")

    def test_schema_files_are_json(self):
        schema_dir = PLUGIN_ROOT / "schemas"
        for name in [
            "goal.schema.json",
            "loop.contract.schema.json",
            "state.schema.json",
            "traceability.schema.json",
            "project.state.schema.json",
            "task.registry.schema.json",
            "decision.registry.schema.json",
            "traceability.matrix.schema.json",
            "validation.results.schema.json",
            "docs.bundle.schema.json",
            "agent.policy.schema.json",
            "capability.routing.schema.json",
            "agent.entry.schema.json",
            "execution.readiness.schema.json",
        ]:
            with self.subTest(name=name):
                parsed = json.loads((schema_dir / name).read_text(encoding="utf-8"))
                self.assertIn("$schema", parsed)
                self.assertEqual(parsed.get("type"), "object")

    def test_machine_readable_docs_dry_run_does_not_write_repo_docs(self):
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as output_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            (docs / "GOAL.md").write_text("# Test Goal\n", encoding="utf-8")
            (docs / "CURRENT_STATE.md").write_text("# State\nUnknown\n", encoding="utf-8")
            (docs / "TASKS.md").write_text("- [ ] Needs confirmation task\n", encoding="utf-8")
            (docs / "CHANGE_REQUESTS.md").write_text(
                "| ID | Status |\n| --- | --- |\n| CR-1 | Needs Confirmation |\n",
                encoding="utf-8",
            )
            (docs / "DECISIONS.md").write_text("# Decisions\n", encoding="utf-8")
            (docs / "TRACEABILITY.md").write_text("| Req | Task |\n| --- | --- |\n| R1 | T1 |\n", encoding="utf-8")
            (docs / "TEST_PLAN.md").write_text("# Test Plan\n", encoding="utf-8")
            (docs / "TEST_RESULTS.md").write_text(
                "| Date | Result |\n| --- | --- |\n| today | TBD |\n",
                encoding="utf-8",
            )

            output = run_script(
                "export_machine_readable_docs.py",
                str(repo),
                "--output",
                output_dir,
                "--dry-run",
                "--json",
            )
            summary = json.loads(output)
            state = json.loads((Path(output_dir) / "state.json").read_text(encoding="utf-8"))
            validation = json.loads(run_script("validate_machine_readable_docs.py", output_dir, "--json"))

        self.assertEqual(summary["mode"], "dry-run")
        self.assertFalse((repo / "docs" / ".agentic").exists())
        self.assertTrue(validation["valid"], validation)
        self.assertGreater(len(state["needs_confirmation"]), 0)

    def test_machine_readable_docs_audit_reports_missing_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "docs").mkdir()
            output = run_script("audit_doc_consistency.py", str(repo), "--json")
            audit = json.loads(output)

        self.assertTrue(audit["valid"], audit)
        self.assertGreater(audit["needs_confirmation_count"], 0)
        self.assertTrue(any("source missing" in item for item in audit["warnings"]))

    def test_agent_governance_exports_and_validates_without_applying_patch(self):
        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as output_dir:
            repo = Path(temp_dir)
            docs = repo / "docs"
            docs.mkdir()
            original_agents = "# Agent Guide\n\nRead docs before implementation.\n"
            (repo / "AGENTS.md").write_text(original_agents, encoding="utf-8")
            (docs / "GOAL.md").write_text("# Test Goal\n", encoding="utf-8")
            (docs / "CURRENT_STATE.md").write_text("# State\nNeeds Confirmation\n", encoding="utf-8")
            (docs / "TASKS.md").write_text("- [ ] Needs confirmation task\n", encoding="utf-8")
            (docs / "CHANGE_REQUESTS.md").write_text(
                "| ID | Status |\n| --- | --- |\n| CR-1 | Needs Confirmation |\n",
                encoding="utf-8",
            )
            (docs / "DECISIONS.md").write_text("# Decisions\n", encoding="utf-8")
            (docs / "TRACEABILITY.md").write_text("| Req | Task |\n| --- | --- |\n| R1 | T1 |\n", encoding="utf-8")
            (docs / "TEST_PLAN.md").write_text("# Test Plan\n", encoding="utf-8")
            (docs / "TEST_RESULTS.md").write_text(
                "| Date | Result |\n| --- | --- |\n| today | TBD |\n",
                encoding="utf-8",
            )

            output_path = Path(output_dir)
            run_script("export_agentic_contract.py", str(repo), "--output", str(output_path / "loop-contract.json"))
            run_script("export_agent_policy.py", str(repo), "--output", str(output_path / "agent-policy.json"))
            run_script(
                "export_capability_routing.py",
                str(repo),
                "--output",
                str(output_path / "capability-routing.json"),
            )
            run_script(
                "export_execution_readiness.py",
                str(repo),
                "--agentic-dir",
                str(output_path),
                "--output",
                str(output_path / "execution-readiness.json"),
            )
            run_script(
                "export_agent_entry_patch.py",
                str(repo),
                "--output",
                str(output_path / "proposed-agents-md.patch"),
            )
            validation = json.loads(
                run_script(
                    "validate_agent_execution_readiness.py",
                    str(repo),
                    "--agentic-dir",
                    str(output_path),
                    "--json",
                )
            )

            policy = json.loads((output_path / "agent-policy.json").read_text(encoding="utf-8"))
            routing = json.loads((output_path / "capability-routing.json").read_text(encoding="utf-8"))
            readiness = json.loads((output_path / "execution-readiness.json").read_text(encoding="utf-8"))
            patch = (output_path / "proposed-agents-md.patch").read_text(encoding="utf-8")
            agents_text_after = (repo / "AGENTS.md").read_text(encoding="utf-8")
            docs_agentic_exists = (repo / "docs" / ".agentic").exists()

        self.assertTrue(validation["valid"], validation)
        self.assertEqual(policy["schema_version"], "agent-policy/v1")
        self.assertIn("docs/.agentic/agent-policy.json", policy["required_read_order"])
        self.assertEqual(policy["loop_order"], ["observe", "plan", "act", "verify", "update_state", "decide_next_loop"])
        route_names = {item["capability"] for item in routing["routes"]}
        expected_routes = {
            "spec-kit",
            "superpowers",
            "plan-cross-validation",
            "architecture-decision-records",
            "validation",
        }
        self.assertTrue(expected_routes.issubset(route_names))
        self.assertFalse(readiness["implementation_readiness"])
        self.assertIn("Agentic Machine-Readable Governance Rule", patch)
        self.assertEqual(agents_text_after, original_agents)
        self.assertFalse(docs_agentic_exists)


if __name__ == "__main__":
    unittest.main()
