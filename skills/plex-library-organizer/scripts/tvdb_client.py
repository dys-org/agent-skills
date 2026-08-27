#!/usr/bin/env python3
"""Small TVDB helper for the plex-library-organizer skill.

Keep this intentionally narrow:
- authenticate with TVDB v4
- search series
- fetch all official-order episodes for a series
- fetch English translations for series / episodes

This script is useful when the model already decided *what* to inspect and just
needs deterministic API access without re-implementing pagination each time.
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


class TVDBClient:
    def __init__(self, api_key: str, pin: str | None = None):
        self.api_key = api_key
        self.pin = pin
        self.token = self._login()
        self._cache: dict[str, Any] = {}

    def _login(self) -> str:
        body = {"apikey": self.api_key}
        if self.pin:
            body["pin"] = self.pin
        req = urllib.request.Request(
            "https://api4.thetvdb.com/v4/login",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.load(response)
        return payload["data"]["token"]

    def get(self, url: str) -> Any:
        if url in self._cache:
            return self._cache[url]
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            payload = json.load(response)
        self._cache[url] = payload
        return payload

    def search_series(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        url = "https://api4.thetvdb.com/v4/search?" + urllib.parse.urlencode(
            {"query": query, "type": "series"}
        )
        data = self.get(url)
        return list(data.get("data", []))[:limit]

    def series_translation(self, series_id: int, language: str = "eng") -> dict[str, Any]:
        url = f"https://api4.thetvdb.com/v4/series/{series_id}/translations/{language}"
        return self.get(url).get("data", {})

    def episode_translation(self, episode_id: int, language: str = "eng") -> dict[str, Any]:
        url = f"https://api4.thetvdb.com/v4/episodes/{episode_id}/translations/{language}"
        return self.get(url).get("data", {})

    def series_episodes_official(self, series_id: int) -> list[dict[str, Any]]:
        page = 0
        episodes: list[dict[str, Any]] = []
        while True:
            url = f"https://api4.thetvdb.com/v4/series/{series_id}/episodes/default?page={page}"
            payload = self.get(url)
            episodes.extend(payload.get("data", {}).get("episodes", []))
            if payload.get("links", {}).get("next") is None:
                break
            page += 1
        return episodes


def build_client(target_root: Path | None = None) -> TVDBClient:
    env, source = load_env_for_target(target_root)
    if not env.get("TVDB_API_KEY"):
        raise SystemExit("TVDB_API_KEY not found in env or nearby .env")
    return TVDBClient(env["TVDB_API_KEY"], env.get("TVDB_PIN"))


def cmd_search(args: argparse.Namespace) -> int:
    client = build_client(Path(args.target_root).resolve() if args.target_root else None)
    results = client.search_series(args.query, limit=args.limit)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


def cmd_series(args: argparse.Namespace) -> int:
    client = build_client(Path(args.target_root).resolve() if args.target_root else None)
    output: dict[str, Any] = {
        "series_id": args.series_id,
        "series_translation": client.series_translation(args.series_id),
    }
    if args.episodes:
        output["episodes"] = client.series_episodes_official(args.series_id)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def cmd_episode_translation(args: argparse.Namespace) -> int:
    client = build_client(Path(args.target_root).resolve() if args.target_root else None)
    print(json.dumps(client.episode_translation(args.episode_id), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Small TVDB helper for Plex library organization")
    parser.add_argument("--target-root", help="Optional media root used for nearby .env lookup")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Search TVDB series")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=5)
    p_search.set_defaults(func=cmd_search)

    p_series = sub.add_parser("series", help="Fetch series translation and optionally official episodes")
    p_series.add_argument("series_id", type=int)
    p_series.add_argument("--episodes", action="store_true")
    p_series.set_defaults(func=cmd_series)

    p_episode = sub.add_parser("episode-translation", help="Fetch one episode translation")
    p_episode.add_argument("episode_id", type=int)
    p_episode.set_defaults(func=cmd_episode_translation)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
