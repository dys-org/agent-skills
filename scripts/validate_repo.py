#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def validate(root: Path) -> list[str]:
    errors = []
    skills_dir = root / "skills"
    skill_dirs = sorted(path for path in skills_dir.iterdir() if path.is_dir())
    names = []

    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        try:
            text = skill_file.read_text()
        except OSError as exc:
            errors.append(f"{skill_file}: cannot read SKILL.md: {exc}")
            continue

        match = re.match(r"---\n(.*?)\n---", text, re.S)
        if not match:
            errors.append(f"{skill_file}: missing YAML frontmatter")
            continue

        fields = {}
        for line in match.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                key, value = line.split(":", 1)
                fields[key] = value.strip()
        for required in ("name", "description"):
            if not fields.get(required):
                errors.append(f"{skill_file}: missing {required}")
        if fields.get("name") != skill_dir.name:
            errors.append(f"{skill_file}: name does not match directory")
        names.append(fields.get("name"))

        for reference in re.findall(r"`((?:scripts|references|assets)/[^`\s]+)`", text):
            reference = reference.rstrip(".,)")
            if not (skill_dir / reference).exists():
                errors.append(f"{skill_file}: missing referenced file {reference}")

        eval_file = skill_dir / "evals/evals.json"
        try:
            data = json.loads(eval_file.read_text())
            evals = data["evals"]
            if data.get("skill_name") != skill_dir.name:
                errors.append(f"{eval_file}: skill name does not match directory")
            if not isinstance(evals, list) or not evals:
                errors.append(f"{eval_file}: evals must be a nonempty list")
                continue
            for case in evals:
                if not isinstance(case, dict) or not {
                    "id", "prompt", "expected_output", "files"
                } <= case.keys():
                    errors.append(f"{eval_file}: malformed eval case")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{eval_file}: invalid eval fixture: {exc}")

    if len(names) != len(set(names)):
        errors.append("skill names are not unique")
    return errors


def main() -> int:
    errors = validate(ROOT)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1

    skill_names = sorted(path.name for path in (ROOT / "skills").iterdir() if path.is_dir())
    print("Repository validation passed for: " + ", ".join(skill_names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
