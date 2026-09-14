import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_repo import validate


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        (self.root / "skills").mkdir()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def add_skill(self, name="example", metadata_name=None, description="Example skill"):
        skill_dir = self.root / "skills" / name
        (skill_dir / "evals").mkdir(parents=True)
        metadata_name = name if metadata_name is None else metadata_name
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {metadata_name}\ndescription: {description}\n---\n"
        )
        (skill_dir / "evals" / "evals.json").write_text(json.dumps({
            "skill_name": name,
            "evals": [{
                "id": 1,
                "prompt": "Do the thing",
                "expected_output": "The thing is done",
                "files": [],
            }],
        }))
        return skill_dir

    def test_new_valid_skill_is_discovered_without_validator_changes(self):
        self.add_skill("first")
        self.add_skill("newly-added")
        self.assertEqual(validate(self.root), [])

    def test_missing_or_mismatched_metadata_fails(self):
        missing = self.add_skill("missing", description="")
        mismatched = self.add_skill("mismatched", metadata_name="different")
        errors = validate(self.root)
        self.assertTrue(any(str(missing / "SKILL.md") in error and "missing description" in error for error in errors))
        self.assertTrue(any(str(mismatched / "SKILL.md") in error and "name does not match" in error for error in errors))

    def test_broken_resource_reference_fails(self):
        skill_dir = self.add_skill()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(skill_file.read_text() + "Use `scripts/missing.py`.\n")
        self.assertTrue(any("missing referenced file scripts/missing.py" in error for error in validate(self.root)))

    def test_missing_empty_or_malformed_eval_fixtures_fail(self):
        missing = self.add_skill("missing")
        (missing / "evals/evals.json").unlink()

        empty = self.add_skill("empty")
        (empty / "evals/evals.json").write_text(json.dumps({"skill_name": "empty", "evals": []}))

        malformed = self.add_skill("malformed")
        (malformed / "evals/evals.json").write_text(json.dumps({
            "skill_name": "malformed",
            "evals": [{"id": 1}],
        }))

        errors = validate(self.root)
        self.assertTrue(any(str(missing / "evals/evals.json") in error for error in errors))
        self.assertTrue(any(str(empty / "evals/evals.json") in error and "nonempty list" in error for error in errors))
        self.assertTrue(any(str(malformed / "evals/evals.json") in error and "malformed eval case" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
