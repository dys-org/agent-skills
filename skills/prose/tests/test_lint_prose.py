import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "lint_prose.py"
SPEC = importlib.util.spec_from_file_location("lint_prose", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class LintProseTests(unittest.TestCase):
    def test_reports_banned_patterns(self):
        text = (
            "The best part? It serves as a bridge—an intentional design "
            "for a vibrant ecosystem."
        )
        findings = MODULE.lint(text)
        names = "\n".join(findings)
        self.assertIn("em dash", names)
        self.assertIn("false suspense", names)
        self.assertIn("pompous connector", names)
        self.assertIn("abstract cliche", names)
        self.assertIn("generic human-centered polish", names)

    def test_allows_fixed_text_ranges_and_compounds(self):
        text = (
            "The note says, 'Do not merge—schema v3 is still rolling out.' "
            "The rule covers versions 2.4–2.7 and each user-facing warning."
        )
        self.assertEqual([], MODULE.lint(text))

    def test_reports_sentence_dashes(self):
        self.assertTrue(MODULE.lint("One thought – another thought."))
        self.assertTrue(MODULE.lint("One thought–another thought."))
        self.assertTrue(MODULE.lint("One thought - another thought."))

    def test_apostrophes_do_not_mask_prose(self):
        findings = MODULE.lint("It's not just quick, but dependable. That's the claim.")
        self.assertTrue(any("manufactured contrast" in item for item in findings))

    def test_reports_close_generic_substitutes(self):
        text = (
            "Your schedule, your way. The experience feels thoughtful and personal. "
            "Keep the day yours while the product is still evolving."
        )
        findings = MODULE.lint(text)
        self.assertEqual(4, len(findings))
        self.assertTrue(all("generic human-centered polish" in item for item in findings))

    def test_ignores_code(self):
        text = "Use `left—right` exactly.\n```text\nnot just X, but Y\n```"
        self.assertEqual([], MODULE.lint(text))


if __name__ == "__main__":
    unittest.main()
