#!/usr/bin/env python3
"""Report deterministic AI-trope violations in prose."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]


RULES = (
    Rule("em dash", re.compile("—")),
    Rule("en dash used as dash", re.compile("–")),
    Rule("faux em dash", re.compile(r"(?<=\S)\s+-\s+(?=\S)")),
    Rule(
        "manufactured contrast",
        re.compile(
            r"\b(?:not just\b.{0,80}\bbut|more than\b|not merely\b|not about\b.{0,80}\b(?:it is|it's) about)\b",
            re.IGNORECASE,
        ),
    ),
    Rule(
        "abstract cliche",
        re.compile(
            r"\b(?:rich tapestry|ever-evolving landscape|vibrant ecosystem|dynamic world|rapidly changing space)\b",
            re.IGNORECASE,
        ),
    ),
    Rule(
        "false suspense",
        re.compile(
            r"(?:\bthe best part\?|\bhere is where it gets interesting\b|\bbut the real surprise was\b|\bthat is when everything changed\b)",
            re.IGNORECASE,
        ),
    ),
    Rule(
        "patronizing analogy",
        re.compile(
            r"\b(?:think of it as|swiss army knife for|imagine a world where)\b",
            re.IGNORECASE,
        ),
    ),
    Rule(
        "pompous connector",
        re.compile(
            r"\b(?:serves as|acts as|functions as|stands as)\b",
            re.IGNORECASE,
        ),
    ),
    Rule(
        "grand conclusion",
        re.compile(
            r"\b(?:ultimately|at the end of the day|this reminds us that|it is a testament to|in a world where)\b",
            re.IGNORECASE,
        ),
    ),
    Rule(
        "generic human-centered polish",
        re.compile(
            r"\b(?:deeply human|meaningful connection|thoughtful experience|experience (?:feels|is) (?:thoughtful|personal)|intentional design|empowering users|designed with you in mind|made easy|a simple,? friendly way|your \w+, your way|keep the day yours|make space for|still evolving)\b",
            re.IGNORECASE,
        ),
    ),
)


def mask_fixed_text(text: str) -> str:
    """Replace code and quoted spans with spaces while preserving positions."""
    chars = list(text)
    patterns = (
        re.compile(r"```.*?```", re.DOTALL),
        re.compile(r"`[^`\n]*`"),
        re.compile(r"(?<!\w)'(?:[^'\\]|\\.)*'(?!\w)"),
        re.compile(r'"(?:[^"\\]|\\.)*"'),
        re.compile(r"‘[^’\n]*’|“[^”\n]*”"),
    )
    for pattern in patterns:
        visible = "".join(chars)
        for match in pattern.finditer(visible):
            for index in range(match.start(), match.end()):
                if chars[index] != "\n":
                    chars[index] = " "
    return "".join(chars)


def mask_numeric_ranges(text: str) -> str:
    chars = list(text)
    for match in re.finditer(r"(?<=\d)–(?=\d)", text):
        chars[match.start()] = " "
    return "".join(chars)


def line_and_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    last_newline = text.rfind("\n", 0, offset)
    column = offset - last_newline
    return line, column


def lint(text: str) -> list[str]:
    masked = mask_numeric_ranges(mask_fixed_text(text))
    findings: list[str] = []
    for rule in RULES:
        for match in rule.pattern.finditer(masked):
            line, column = line_and_column(text, match.start())
            excerpt = text[match.start() : match.end()].replace("\n", " ")
            findings.append(f"{line}:{column}: {rule.name}: {excerpt}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()

    findings = lint(args.file.read_text())
    if findings:
        print("\n".join(findings))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
