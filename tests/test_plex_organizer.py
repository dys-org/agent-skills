import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "skills/plex-library-organizer/scripts"
APPLY = SCRIPTS / "apply_plan.py"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OrganizerTests(unittest.TestCase):
    def run_plan(self, root, plan, *args, plan_rel=".plex-organizer/plan.json"):
        path = root / plan_rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan))
        return subprocess.run(
            [sys.executable, str(APPLY), plan_rel, "--root", str(root), *args],
            text=True, capture_output=True, check=False,
        )

    def basic_plan(self):
        return {"actions": [{"source": "incoming/movie.mkv", "target": "Movie (2026)/Movie (2026).mkv"}], "delete_candidates": []}

    def test_dry_run_and_approved_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / "incoming/movie.mkv"
            source.parent.mkdir(); source.write_text("media")
            dry = self.run_plan(root, self.basic_plan())
            self.assertEqual(dry.returncode, 0); self.assertTrue(source.exists())
            applied = self.run_plan(root, self.basic_plan(), "--execute")
            self.assertEqual(applied.returncode, 0)
            self.assertTrue((root / "Movie (2026)/Movie (2026).mkv").exists())
            self.assertFalse((root / ".plex-organizer").exists())

    def test_collisions_and_missing_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "a").mkdir(); (root / "a/one.mkv").write_text("1")
            plan = {"actions": [{"source": "a/one.mkv", "target": "same.mkv"}, {"source": "a/missing.mkv", "target": "same.mkv"}]}
            result = self.run_plan(root, plan)
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["validation"]["duplicate_targets"])
            self.assertTrue(payload["validation"]["missing_sources"])

    def test_rejects_traversal_absolute_and_outside_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "source.mkv").write_text("x")
            outside = root.parent / "outside-do-not-delete.txt"; outside.write_text("safe")
            for field, value in (("target", "../escape.mkv"), ("target", str(outside)), ("delete", "../outside-do-not-delete.txt")):
                plan = {"actions": [{"source": "source.mkv", "target": "ok.mkv"}], "delete_candidates": []}
                if field == "target": plan["actions"][0]["target"] = value
                else: plan["delete_candidates"] = [value]
                result = self.run_plan(root, plan, "--execute")
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(outside.exists())
            outside.unlink()

    def test_plan_path_is_relative_and_cleanup_is_confined(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "source.mkv").write_text("x")
            absolute = subprocess.run([sys.executable, str(APPLY), str(root / "plan.json"), "--root", str(root)], text=True, capture_output=True)
            self.assertNotEqual(absolute.returncode, 0)
            result = self.run_plan(root, {"actions": [{"source": "source.mkv", "target": "done.mkv"}]}, "--execute", plan_rel="plans/plan.json")
            self.assertEqual(result.returncode, 0)
            self.assertTrue((root / "plans").exists())

    def test_bounded_credentials_and_secret_free_metadata(self):
        for name in ("tmdb_client", "tvdb_client"):
            module = load(name)
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp); target = base / "media/library"; target.mkdir(parents=True)
                (base / ".env").write_text("TMDB_TOKEN=grandparent-secret\nTVDB_API_KEY=grandparent-secret\n")
                clean_env = {key: value for key, value in os.environ.items() if key not in module.KNOWN_ENV_KEYS}
                with patch.dict(os.environ, clean_env, clear=True), patch("pathlib.Path.cwd", return_value=target):
                    env, source = module.load_env_for_target(target)
                self.assertIsNone(source)
                self.assertNotIn("grandparent-secret", json.dumps({"source": source}))


if __name__ == "__main__":
    unittest.main()
