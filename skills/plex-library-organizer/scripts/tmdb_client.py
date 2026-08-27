#!/usr/bin/env python3
"""Small TMDB helper for the plex-library-organizer skill.

Purposefully narrow:
- load TMDB credentials from env / nearby .env
- search movies by title, with optional year
- fetch one movie record by TMDB id

This is the movie-side counterpart to tvdb_client.py: a small deterministic
helper the model can use after it decides what to inspect.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


KNOWN_ENV_KEYS = ["TMDB_TOKEN", "TMDB_API_KEY", "TVDB_API_KEY", "TVDB_PIN"]


def load_env_for_target(target_root: Path | None = None) -> tuple[dict[str, str], dict[str, Any] | None]:
    env = dict(os.environ)
    if any(env.get(key) for key in KNOWN_ENV_KEYS):
        return env, {
            "type": "env",
            "path": str(Path.cwd()),
            "keys": [key for key in KNOWN_ENV_KEYS if env.get(key)],
        }

    candidates: list[Path] = []
    seen: set[Path] = set()
    roots = [Path.cwd()]
    if target_root:
        roots.extend([target_root, target_root.parent])

    for root in roots:
        p = root / ".env"
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            candidates.append(rp)

    for env_path in candidates:
        if not env_path.exists():
            continue
        found_keys: list[str] = []
        for line in env_path.read_text(errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            key, value = s.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            env.setdefault(key, value)
            if key in KNOWN_ENV_KEYS:
                found_keys.append(key)
        if found_keys:
            return env, {
                "type": "dotenv",
                "path": str(env_path),
                "keys": found_keys,
            }

    return env, None


class TMDBClient:
    def __init__(self, token: str | None = None, api_key: str | None = None):
        self.token = token
        self.api_key = api_key
        if not self.token and not self.api_key:
            raise ValueError("TMDB_TOKEN or TMDB_API_KEY is required")
        self._cache: dict[str, Any] = {}

    def _headers(self) -> dict[str, str]:
        headers = {"accept": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        return headers

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        params = params or {}
        if not self.token and self.api_key and "api_key" not in params:
            params["api_key"] = self.api_key
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = "https://api.themoviedb.org/3" + path + ("?" + query if query else "")
        if url in self._cache:
            return self._cache[url]
        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.load(response)
        self._cache[url] = payload
        return payload

    def search_movie(self, query: str, year: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"query": query, "include_adult": "false"}
        if year:
            params["year"] = year
        data = self.get("/search/movie", params)
        return list(data.get("results", []))[:limit]

    def movie(self, movie_id: int) -> dict[str, Any]:
        return self.get(f"/movie/{movie_id}")


def build_client(target_root: Path | None = None) -> TMDBClient:
    env, source = load_env_for_target(target_root)
    token = env.get("TMDB_TOKEN")
    api_key = env.get("TMDB_API_KEY")
    if not token and not api_key:
        raise SystemExit("TMDB_TOKEN or TMDB_API_KEY not found in env or nearby .env")
    return TMDBClient(token=token, api_key=api_key)


def cmd_search(args: argparse.Namespace) -> int:
    client = build_client(Path(args.target_root).resolve() if args.target_root else None)
    results = client.search_movie(args.query, year=args.year, limit=args.limit)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


def cmd_movie(args: argparse.Namespace) -> int:
    client = build_client(Path(args.target_root).resolve() if args.target_root else None)
    print(json.dumps(client.movie(args.movie_id), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Small TMDB helper for Plex library organization")
    parser.add_argument("--target-root", help="Optional media root used for nearby .env lookup")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Search TMDB movies")
    p_search.add_argument("query")
    p_search.add_argument("--year")
    p_search.add_argument("--limit", type=int, default=5)
    p_search.set_defaults(func=cmd_search)

    p_movie = sub.add_parser("movie", help="Fetch one movie by TMDB id")
    p_movie.add_argument("movie_id", type=int)
    p_movie.set_defaults(func=cmd_movie)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
