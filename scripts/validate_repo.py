#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
EXPECTED = {"code-simplifier", "multi-angle-code-review", "plex-library-organizer", "streamline"}
errors = []

actual = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
if actual != EXPECTED:
    errors.append(f"skill directories: expected {sorted(EXPECTED)}, got {sorted(actual)}")

names = []
for skill_dir in sorted((ROOT / "skills").iterdir()):
    skill_file = skill_dir / "SKILL.md"
    text = skill_file.read_text()
    match = re.match(r"---\n(.*?)\n---", text, re.S)
    if not match:
        errors.append(f"{skill_file}: missing YAML frontmatter")
        continue
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            fields[key] = value.strip()
    for required in ("name", "description", "license"):
        if not fields.get(required):
            errors.append(f"{skill_file}: missing {required}")
    if fields.get("name") != skill_dir.name:
        errors.append(f"{skill_file}: name does not match directory")
    if fields.get("license") != "MIT":
        errors.append(f"{skill_file}: license must be MIT")
    names.append(fields.get("name"))

    for reference in re.findall(r"`((?:scripts|references|assets)/[^`\s]+)`", text):
        if not (skill_dir / reference.rstrip(".,)")).exists():
            errors.append(f"{skill_file}: missing referenced file {reference}")

    eval_file = skill_dir / "evals/evals.json"
    try:
        data = json.loads(eval_file.read_text())
        evals = data["evals"]
        if data.get("skill_name") != skill_dir.name or len(evals) < 6:
            errors.append(f"{eval_file}: wrong skill name or fewer than six evals")
        for case in evals:
            if not {"id", "prompt", "expected_output", "files"} <= case.keys():
                errors.append(f"{eval_file}: malformed eval case")
    except (OSError, ValueError, KeyError) as exc:
        errors.append(f"{eval_file}: invalid JSON: {exc}")

if len(names) != len(set(names)):
    errors.append("skill names are not unique")

for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    if path.name == ".env-example":
        continue
    try:
        text = path.read_text()
    except UnicodeDecodeError:
        continue
    for pattern in (r"/Users/[A-Za-z0-9._-]+", r"/home/[A-Za-z0-9._-]+", r"BEGIN (?:RSA |OPENSSH )?PRIVATE KEY", r"(?im)^\s*(?:TMDB_TOKEN|TMDB_API_KEY|TVDB_API_KEY|TVDB_PIN)\s*=\s*\S+"):
        if re.search(pattern, text):
            errors.append(f"{path.relative_to(ROOT)}: possible personal path or secret")
            break

if errors:
    print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
    raise SystemExit(1)
print("Repository validation passed for: " + ", ".join(sorted(EXPECTED)))
