#!/usr/bin/env python3
"""Execute an approved Plex organizer plan.

This script is intentionally conservative:
- default mode is validation / dry-run summary only
- `--execute` is required to mutate the filesystem
- it supports the two lightweight plan shapes the skill currently emits:
  1. TV-style: `actions` + `delete_candidates`
  2. Movie-style: `resolved_items` + optional `probable_tv_items` / `delete_candidates`

The model should still decide *whether* a plan is correct. This script only
applies a reviewed plan deterministically.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


VIDEO_EXT = {'.mkv', '.mp4', '.avi', '.m4v', '.mov', '.wmv', '.mpg', '.mpeg', '.ts', '.m2ts', '.iso'}
SUB_EXT = {'.srt', '.ass', '.ssa', '.sub', '.idx', '.vtt', '.sup'}
ARCHIVE_EXT = {'.zip', '.rar', '.7z', '.tar', '.gz'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply an approved Plex organizer plan")
    parser.add_argument("plan_json", help="Path to .plex-organizer/plan.json")
    parser.add_argument("--root", help="Optional media root; defaults to parent of .plex-organizer")
    parser.add_argument("--execute", action="store_true", help="Actually move files and delete approved items")
    parser.add_argument("--keep-plan-dir", action="store_true", help="Do not remove the .plex-organizer dir after success")
    return parser.parse_args()


def same_path(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except FileNotFoundError:
        return str(a) == str(b)


def resolve_plan_path(root: Path, value: str, field: str) -> Path:
    relative = Path(value)
    if relative.is_absolute():
        raise ValueError(f"{field} must be root-relative: {value}")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{field} resolves outside media root: {value}") from exc
    return resolved


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def gather_operations(plan: dict[str, Any], root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ops: list[dict[str, Any]] = []
    deletes: list[dict[str, Any]] = []

    if "actions" in plan:
        for action in plan.get("actions", []):
            ops.append(
                {
                    "kind": "video",
                    "source": resolve_plan_path(root, action["source"], "source"),
                    "target": resolve_plan_path(root, action["target"], "target"),
                    "raw": action,
                }
            )
            for sub in action.get("subtitles", []):
                ops.append(
                    {
                        "kind": "subtitle",
                        "source": resolve_plan_path(root, sub["source"], "subtitle source"),
                        "target": resolve_plan_path(root, sub["target"], "subtitle target"),
                        "raw": sub,
                    }
                )
        for item in plan.get("delete_candidates", []):
            if isinstance(item, dict):
                deletes.append({"path": resolve_plan_path(root, item["path"], "delete candidate"), "reason": item.get("reason", "approved delete")})
            else:
                deletes.append({"path": resolve_plan_path(root, str(item), "delete candidate"), "reason": "approved delete"})
        return ops, deletes

    if "resolved_items" in plan:
        for item in plan.get("resolved_items", []):
            proposed = item.get("proposed", {})
            ops.append(
                {
                    "kind": "video",
                    "source": resolve_plan_path(root, item["video"], "source"),
                    "target": resolve_plan_path(root, proposed["video_target"], "target"),
                    "raw": item,
                }
            )
            for sub in proposed.get("subtitle_targets", []):
                ops.append(
                    {
                        "kind": "subtitle",
                        "source": resolve_plan_path(root, sub["source"], "subtitle source"),
                        "target": resolve_plan_path(root, sub["target"], "subtitle target"),
                        "raw": sub,
                    }
                )
        for item in plan.get("delete_candidates", []):
            if isinstance(item, dict):
                deletes.append({"path": resolve_plan_path(root, item["path"], "delete candidate"), "reason": item.get("reason", "approved delete")})
            else:
                deletes.append({"path": resolve_plan_path(root, str(item), "delete candidate"), "reason": "approved delete"})
        return ops, deletes

    raise SystemExit("Unsupported plan schema: expected `actions` or `resolved_items`")


def validate_operations(ops: list[dict[str, Any]]) -> dict[str, Any]:
    duplicate_targets: dict[str, list[str]] = defaultdict(list)
    missing_sources: list[str] = []
    conflicts: list[dict[str, str]] = []

    for op in ops:
        duplicate_targets[str(op["target"])].append(str(op["source"]))
        if not op["source"].exists():
            missing_sources.append(str(op["source"]))

    dupes = {target: sources for target, sources in duplicate_targets.items() if len(sources) > 1}

    for op in ops:
        target = op["target"]
        source = op["source"]
        if target.exists() and not same_path(source, target):
            conflicts.append({"kind": op["kind"], "source": str(source), "target": str(target)})

    return {
        "duplicate_targets": dupes,
        "missing_sources": missing_sources,
        "conflicts": conflicts,
    }


def move_file(source: Path, target: Path) -> bool:
    if same_path(source, target):
        return False
    ensure_parent(target)
    source.rename(target)
    return True


def remove_empty_dirs(root: Path, exclude: set[Path] | None = None) -> list[str]:
    exclude = exclude or set()
    removed: list[str] = []
    changed = True
    while changed:
        changed = False
        for dirpath, dirnames, filenames in os.walk(root, topdown=False):
            path = Path(dirpath)
            if path == root or path in exclude:
                continue
            try:
                next(path.iterdir())
            except StopIteration:
                path.rmdir()
                removed.append(str(path.relative_to(root)))
                changed = True
            except (FileNotFoundError, OSError):
                pass
    return removed


def count_tree(root: Path) -> dict[str, Any]:
    summary = {"videos": 0, "subtitles": 0, "archives": 0, "junk": 0, "top_level_videos": []}
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            path = Path(dirpath) / filename
            ext = path.suffix.lower()
            if ext in VIDEO_EXT:
                summary["videos"] += 1
                if path.parent == root:
                    summary["top_level_videos"].append(str(path.relative_to(root)))
            elif ext in SUB_EXT:
                summary["subtitles"] += 1
            elif ext in ARCHIVE_EXT:
                summary["archives"] += 1
            if filename == '.DS_Store' or filename.startswith('._') or filename.endswith('.parts'):
                summary["junk"] += 1
    summary["top_level_videos"].sort()
    return summary


def main() -> int:
    args = parse_args()
    supplied_plan = Path(args.plan_json)
    if supplied_plan.is_absolute():
        raise SystemExit("plan_json must be root-relative")
    root = Path(args.root).resolve() if args.root else Path.cwd().resolve()
    plan_path = resolve_plan_path(root, args.plan_json, "plan_json")
    if not plan_path.exists():
        raise SystemExit(f"Plan not found: {plan_path}")

    plan = json.loads(plan_path.read_text())
    ops, deletes = gather_operations(plan, root)
    validation = validate_operations(ops)

    summary: dict[str, Any] = {
        "plan_json": str(plan_path),
        "root": str(root),
        "operations": len(ops),
        "video_operations": sum(1 for op in ops if op["kind"] == "video"),
        "subtitle_operations": sum(1 for op in ops if op["kind"] == "subtitle"),
        "delete_candidates": len(deletes),
        "validation": validation,
        "execute": args.execute,
    }

    if validation["duplicate_targets"] or validation["missing_sources"] or validation["conflicts"]:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 2

    if not args.execute:
        summary["message"] = "Validation passed. Re-run with --execute to apply changes."
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    created_dirs: set[str] = set()
    moved_videos = 0
    moved_subtitles = 0

    for op in ops:
        if not op["target"].parent.exists():
            op["target"].parent.mkdir(parents=True, exist_ok=True)
            created_dirs.add(str(op["target"].parent))

    for op in [op for op in ops if op["kind"] == "video"]:
        if move_file(op["source"], op["target"]):
            moved_videos += 1

    for op in [op for op in ops if op["kind"] == "subtitle"]:
        if move_file(op["source"], op["target"]):
            moved_subtitles += 1

    deleted = 0
    for item in deletes:
        path = item["path"]
        if path.exists() and path.is_file():
            path.unlink()
            deleted += 1

    removed_dirs = remove_empty_dirs(root, exclude={plan_path.parent})

    expected_plan_dir = (root / ".plex-organizer").resolve()
    if not args.keep_plan_dir and plan_path.parent == expected_plan_dir and plan_path.parent.exists():
        shutil.rmtree(plan_path.parent)

    summary.update(
        {
            "moved_videos": moved_videos,
            "moved_subtitles": moved_subtitles,
            "deleted_files": deleted,
            "removed_empty_dirs": len(removed_dirs),
            "post_apply": count_tree(root),
        }
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
