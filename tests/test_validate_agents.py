from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_agents", ROOT / "scripts" / "validate_agents.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
validate_repository = MODULE.validate_repository

class ValidateAgentsTests(unittest.TestCase):
    def make_fixture(self, destination: Path) -> None:
        for name in [
            "plugin.json",
            "skill-routing.json",
            "README.md",
            "AGENTS.md",
        ]:
            shutil.copy2(ROOT / name, destination / name)
        for directory in ["agents", "rules"]:
            shutil.copytree(ROOT / directory, destination / directory)

    def test_repository_is_valid(self) -> None:
        self.assertEqual([], validate_repository(ROOT))

    def test_read_only_agent_cannot_gain_run_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            path = root / "agents" / "reviewer.md"
            text = path.read_text(encoding="utf-8").replace(
                "  - grep_search\n", "  - grep_search\n  - run_command\n", 1
            )
            path.write_text(text, encoding="utf-8")
            errors = validate_repository(root)
            self.assertTrue(
                any("read-only role exposes mutating tools" in error for error in errors)
            )

    def test_high_risk_agent_must_use_pro(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            path = root / "agents" / "oracle.md"
            text = path.read_text(encoding="utf-8").replace(
                "model: pro", "model: inherit", 1
            )
            path.write_text(text, encoding="utf-8")
            self.assertIn(
                f"{path}: high-risk role must use model: pro",
                validate_repository(root),
            )

    def test_verifier_cannot_directly_edit_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            path = root / "agents" / "verifier.md"
            text = path.read_text(encoding="utf-8").replace(
                "  - run_command\n", "  - write_to_file\n  - run_command\n", 1
            )
            path.write_text(text, encoding="utf-8")
            self.assertTrue(
                any("verifier must not expose direct edit tools" in error for error in validate_repository(root))
            )

    def test_manifest_route_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            path = root / "skill-routing.json"
            text = path.read_text(encoding="utf-8").replace(
                '"code-review.spec": "reviewer"',
                '"code-review.spec": "fixer"',
                1,
            )
            path.write_text(text, encoding="utf-8")
            self.assertIn(
                "skill-routing.json: workflow lane routing drifted",
                validate_repository(root),
            )

    def test_orchestration_requires_lane_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            path = root / "rules" / "orchestration.md"
            text = path.read_text(encoding="utf-8").replace(
                "same lane + dependent follow-up",
                "dependent follow-up",
                1,
            )
            path.write_text(text, encoding="utf-8")
            self.assertTrue(
                any("same lane + dependent follow-up" in error for error in validate_repository(root))
            )

    def test_orchestration_requires_writer_worktree_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            path = root / "rules" / "orchestration.md"
            text = path.read_text(encoding="utf-8").replace(
                "Workspace: branch",
                "Workspace: inherit",
                1,
            )
            path.write_text(text, encoding="utf-8")
            self.assertTrue(
                any("Workspace: branch" in error for error in validate_repository(root))
            )

    def test_plugin_manifest_rejects_unknown_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            path = root / "plugin.json"
            text = path.read_text(encoding="utf-8").replace(
                '\n}', ',\n  "version": "1.0.0"\n}', 1
            )
            path.write_text(text, encoding="utf-8")
            self.assertTrue(
                any("unsupported keys" in error for error in validate_repository(root))
            )

if __name__ == "__main__":
    unittest.main()
