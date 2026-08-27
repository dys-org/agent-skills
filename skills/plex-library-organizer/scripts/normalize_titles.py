#!/usr/bin/env python3
"""Normalization helpers for fuzzy episode / movie title comparison.

Keep this small and inspectable. The model should still decide whether a fuzzy
match is acceptable; this script only provides consistent comparison helpers.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
import unicodedata


RELEASE_NOISE_RE = re.compile(
    r"(?i)\b(2160p|1080p|720p|480p|blu[- ]?ray|brrip|bdrip|webrip|web[- ]?dl|dvdrip|x264|x265|hevc|h264|xvid|aac|dts|repack|remastered|proper|extended|uncut|10bit|8bit|yify|yts|galaxyrg|etrg|tgx)\b"
)
SESSION_PREFIX_RE = re.compile(r"^(session\s*#?\d+\s*:?|chapter\s*[ivxlcdm0-9]+\s*:?)\s*", re.I)
PART_PARENS_RE = re.compile(r"\((\d+)\)")


def normalize_title(text: str) -> str:
    s = unicodedata.normalize("NFKD", text).lower()
    s = s.replace("&", " and ")
    s = s.replace("_", " ")
    s = s.replace("’", "'").replace("`", "'")
    s = PART_PARENS_RE.sub(r" part \1 ", s)
    s = s.replace("'", "")
    s = RELEASE_NOISE_RE.sub(" ", s)
    s = s.replace("part iv", "part 4")
    s = s.replace("part iii", "part 3")
    s = s.replace("part ii", "part 2")
    s = s.replace("part i", "part 1")
    s = SESSION_PREFIX_RE.sub("", s)
    s = re.sub(r"\b(the|a|an)\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def similarity(a: str, b: str) -> float:
    na = normalize_title(a)
    nb = normalize_title(b)
    if not na or not nb:
        return 0.0
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    jaccard = len(ta & tb) / len(ta | tb) if ta and tb else 0.0
    return max(ratio, jaccard)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize and compare media titles")
    sub = parser.add_subparsers(dest="command", required=True)

    p_norm = sub.add_parser("normalize", help="Normalize one title")
    p_norm.add_argument("text")

    p_sim = sub.add_parser("similarity", help="Compare two titles")
    p_sim.add_argument("a")
    p_sim.add_argument("b")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "normalize":
        print(normalize_title(args.text))
        return 0

    if args.command == "similarity":
        print(f"{similarity(args.a, args.b):.4f}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
