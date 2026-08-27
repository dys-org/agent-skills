---
name: plex-library-organizer
license: MIT
description: Organize messy movie and TV libraries for Plex using TMDB for movies and TVDB for series. Use whenever the user wants to rename or restructure media folders, fix Plex matching, clean subtitle files, normalize Specials or extras, remove release junk, or prepare ripped/downloaded media for Plex. Always build a dry-run plan first, surface low-confidence matches and collisions, and only apply changes after explicit user confirmation.
disable-model-invocation: true
---

# Plex Library Organizer

Organize movie and TV files into Plex-friendly names and folders.

This skill is for filesystem cleanup and metadata-backed renaming, not for downloading media.

## Credentials

Do not store API credentials inside the skill directory.

This skill expects metadata API credentials to be available either as exported environment variables or in a `.env` file near the media library being organized.

Supported variables:
- `TMDB_TOKEN`
- `TMDB_API_KEY`
- `TVDB_API_KEY`
- `TVDB_PIN` (optional if the user's TVDB key requires it)

Resolution order (bounded deliberately):
1. already-exported environment variables
2. `.env` in the current working directory
3. `.env` inside the target media folder
4. `.env` in the target folder's parent

Typical layouts:
- `/media/.env`
- `/media/movies/...`
- `/media/tv/...`

or

- `/media/movies/.env`
- `/media/tv/...`

If credentials cannot be found, stop and ask the user for the correct `.env` location or for exported environment variables.

Never write secrets into:
- `SKILL.md`
- bundled scripts
- logs
- generated plans

## Metadata sources

- **Movies:** use TMDB
  - Prefer `TMDB_TOKEN` as a Bearer token.
  - `TMDB_API_KEY` can exist as a fallback, but Bearer auth is preferred.
- **TV:** use TVDB
  - Authenticate with `POST /login` using `TVDB_API_KEY` and optional `TVDB_PIN`.
  - Use the returned Bearer token for subsequent API calls.
  - Use **official** episode ordering unless the user explicitly asks for DVD, absolute, or another TVDB season type.
  - Fetch **English series and episode translations** for final Plex names when TVDB defaults to another language.
  - Do not assume branding maps 1:1 to separate series. Verify whether TVDB official order folds sequel branding or continuation branding into a parent show.

If API behavior or endpoint details are unclear, verify current official TMDB/TVDB documentation through the documentation tools available in the current agent environment.

## Bundled scripts

Use bundled scripts when they reduce repetitive, deterministic work, but keep judgment in the model.

Current helpers:
- `scripts/tvdb_client.py`
  - use for TVDB login, series search, official-episode fetches, and English translation lookups
- `scripts/tmdb_client.py`
  - use for TMDB movie search, title+year lookups, and fetching canonical movie metadata by id
- `scripts/normalize_titles.py`
  - use for consistent title normalization and similarity checks during matching
- `scripts/apply_plan.py`
  - use to validate or execute an already-approved `plan.json`

Do **not** turn these helpers into a rigid pipeline.
- Keep ambiguous metadata choices, duplicate-vs-version decisions, cross-library move decisions, and user-facing summaries in the model.
- Prefer plain JSON plans and small helper scripts over a large abstraction layer.

## Core rules

1. **Always scan and plan before renaming.**
2. **Always show low-confidence matches, collisions, and unusual cases before applying.**
3. **Only apply after explicit user approval.**
4. **Do not delete media files without confirmation.**
5. **Junk files may be proposed for deletion, but still summarize them.**
6. **Prefer Finder-friendly names:** replace `:` with ` - ` unless the user explicitly wants official punctuation preserved.
7. **Remove release junk** from final names: resolution, source, codec, group tags, repack tags, YTS-style clutter, etc.
8. **Preserve accents and apostrophes by default** unless the user asks for ASCII-only normalization.
9. **If the user changes the filesystem after the dry run, rescan and rebuild the plan.** Do not apply from stale inventory.

## Scan first

Use `bash` with `find`, `rg`, and `python3` to inventory the target folder.

Identify:
- video files
- subtitle files
- archives like `.zip`
- junk files such as `.DS_Store`, `._*`, `.parts`
- whether the target is movies, TV, or mixed
- files already carrying SxxEyy codes
- title-only files that need episode-title matching
- nested release folders that should be flattened
- cross-show bundles that contain episodes from multiple series
- standalone movie files buried inside TV folders or TV-related files buried inside movie folders
- anthology or shorts collections where TVDB official seasons may be years or decade-like values
- single-file compilations that appear to contain an entire miniseries or whole season
- artifact-only leftover folders containing only artwork, `.nfo`, `.txt`, posters, or release notes

When the root is mixed, handle **movies and TV separately**.

Every path stored in a plan must be relative to the selected media root. Reject absolute paths and any source, target, or deletion candidate that resolves outside that root.

Save a dry-run plan inside the target root in this hidden folder:
- `.plex-organizer/plan.json`
- `.plex-organizer/summary.md`

Remove temporary planning artifacts automatically only when their resolved directory is exactly `<media-root>/.plex-organizer`.

## Report structure before apply

Before making changes, present:
- target path
- detected media type
- credential source used (do not print secret values)
- counts of videos, subtitles, extras, junk files
- proposed top-level folder names
- representative rename examples
- low-confidence matches
- collisions or duplicate target paths
- files that would go to `Specials` or `Other`
- files that would move to another show folder or to the movie library
- artifact-only leftover folders that would remain after moves
- files proposed for deletion

Then ask for approval.

## Movie workflow

### Matching

For each movie group:
- If a video is already inside a movie folder, treat the folder as the grouping unit.
- If a video is in the root, create a movie folder for it.
- Derive an initial title and year from the current folder/file name.
- Search TMDB with title + year first, then broader search if needed.
- Prefer the official TMDB title and release year.
- If multiple close matches exist, show them to the user rather than guessing silently.

### Final movie naming

Use:
- `Movie Title (Year)/Movie Title (Year).ext`

Examples:
- `Batman (1966)/Batman (1966).mkv`
- `Spider-Man - No Way Home (2021)/Spider-Man - No Way Home (2021).mp4`

### Movie subtitles

Rename sidecars to match the movie basename.

Preferred forms:
- `Movie Title (Year).srt`
- `Movie Title (Year).eng.srt`
- `Movie Title (Year).eng.sdh.srt`
- `Movie Title (Year).eng.forced.srt`

If subtitles are buried inside `Subs/` folders, move them beside the movie file and convert them to Plex-style sidecars when the language/flag can be inferred from the file name.

If subtitle archives such as `.zip` are present, propose deletion after confirming with the user.

## TV workflow

### Series matching

- Search TVDB for the series.
- Include year when the current folder suggests one.
- Use the official series title and year for the show folder.
- Prefer `Show Name (Year)` for Plex TV Series matching.
- Fetch the English series translation before final naming when TVDB's primary title is not English.
- Verify whether the material belongs to a differently branded continuation that TVDB official order folds into another series.

Examples:
- `Brooklyn Nine-Nine (2013)`
- `The Simpsons (1989)`

### Episode matching

Prefer this order:

1. **SxxEyy already present in filenames**
   - verify against TVDB official ordering
   - replace release-junk filenames with clean episode titles
   - do not assume the visible season numbers in source folders are authoritative if TVDB official ordering folds the material into a parent series or uses different season numbering

2. **Multi-episode files**
   - detect patterns like `S04E11-E12`
   - use Plex form `S04E11-E12`
   - if both episodes share the same base title, use the shared base title
   - otherwise join titles with ` + `

3. **Title-only files**
   - use season context from folder names when available
   - match against TVDB official episode titles using normalized title comparison
   - normalize punctuation, apostrophes, accents, Roman numerals vs digits, `Part I/II` vs `Part 1/2`, and prefixes like `Session #`, `Chapter`, or similar release-added text when comparing
   - fetch English episode translations before final naming if TVDB defaults to another language
   - use part numbers like `Part 1`, `Part 2`, or `(1)`, `(2)` to disambiguate
   - if confidence is low, stop and ask the user

4. **Absolute-numbered anime or anthology-style files**
   - when source files are numbered by absolute episode number, map them to TVDB official `seasonNumber` and `number` before final naming
   - for anthology/shorts libraries, use the official TVDB season number exactly as returned, even if it looks like a year or decade-like season such as `1940`, `1950`, or `1960`

5. **Single-file whole-series or whole-miniseries compilations**
   - do not pretend a compilation file is a normal single episode
   - either leave it untouched, or place it in `Other/` with a note that Plex will not index it as individual episodes unless it is split

### Final TV naming

Use:
- `Show Name (Year)/Season 01/Show Name - S01E01 - Episode Title.ext`

Use the **official TVDB season number in the folder and code**, even when that means unusual folders such as `Season 1940` or `Season 1950` for anthology shorts.

Use `Specials/` for TVDB season 0 by default.
`Season 00` is also acceptable to Plex, but default to `Specials` unless the user requests otherwise.

Examples:
- `Poker Face (2023)/Season 01/Poker Face - S01E01 - Dead Man's Hand.mkv`
- `Miss Marple (1984)/Specials/Miss Marple - S00E03 - A Caribbean Mystery.mkv`

### TV subtitles

Rename sidecars to match the episode basename.

Examples:
- `Show Name - S01E01 - Episode Title.eng.srt`
- `Show Name - S01E01 - Episode Title.eng.sdh.srt`
- `Show Name - S01E01 - Episode Title.eng.forced.srt`

## Known tricky TVDB patterns

Watch for these cases before assuming the obvious folder structure is correct:

- **Anthology shorts with year- or decade-like official seasons**
  - Example: `Tom and Jerry (1940)` uses official seasons like `1940`, `1950`, and `1960`.
  - Do not invent intermediate season folders such as `Season 1941` just because the short aired in 1941.
  - Use the exact official `seasonNumber` returned by TVDB.

- **Continuation branding folded into a parent series**
  - Example: `Justice League Unlimited` may be part of `Justice League (2001)` official ordering rather than a separate official TVDB series flow for rename purposes.
  - Verify with TVDB before final naming.

- **Cross-show bundles**
  - Example: a `Batman Beyond` bundle may contain the main show, a standalone movie, a short, and crossover episodes from `The Zeta Project`, `Static Shock`, or `Justice League`.
  - Split those files into their correct destinations instead of forcing everything under one show.

- **Anime / translated-title matching**
  - Example: `Cowboy Bebop`, `Dragon Ball Z`, and `One-Punch Man` may need English episode translations from TVDB rather than raw default-language episode names.
  - Normalize prefixes like `Session #`, chapter labels, punctuation, apostrophes, and `Part I/II` vs `Part 1/2` before comparing.

- **Single-file whole-series compilations**
  - Example: one `CLONE_WARS_2003.mkv` file containing the full miniseries.
  - Treat this as a compilation, not a normal episode. Leave it untouched or place it in `Other/` with a warning that Plex will not index it as separate episodes unless split.

## Extras and non-episode content

For TV extras, do **not** use a generic `Extras` folder.

Use Plex-recognized extra directories when possible:
- `Behind The Scenes`
- `Deleted Scenes`
- `Featurettes`
- `Interviews`
- `Scenes`
- `Shorts`
- `Trailers`
- `Other`

If the material is clearly bonus content but not classifiable, put it in:
- `Other/`

Examples:
- season special-features discs
- music videos
- featurettes
- stray `.nfo` files the user wants retained

If a TV bundle contains files that clearly belong to **other shows**, split them into the correct series folders instead of forcing them under the current show.

If a TV bundle contains a **standalone movie**, do not silently keep it under the TV show. Surface it in the dry run and, if the user approves cross-library cleanup, move it into the movie library using the movie workflow.

For movie libraries, do not invent extra folders unless the user asks. Report unrecognized non-movie files separately.

## Junk cleanup

After approval, remove or offer to remove:
- `.DS_Store`
- `._*`
- `.parts`
- empty release folders left behind after moves
- empty `Subs/` folders after subtitle flattening
- leftover subtitle archives if the user approves
- artifact-only leftover folders containing only artwork, posters, `.nfo`, `.txt`, or release notes, if the user wants them removed

## Safety checks before apply

Before executing the rename/move plan:
- ensure every target path is unique
- ensure target folders do not conflict with existing unrelated folders
- surface duplicate videos that may represent alternate versions
- distinguish likely accidental duplicates from intentional alternate versions and ask before deleting
- keep multi-version files distinct rather than overwriting them

If multiple versions of the same movie remain in one folder, name them distinctly, for example:
- `Movie Title (Year) - Version 1.mkv`
- `Movie Title (Year) - Version 2.mkv`

## Apply phase

When the user approves:
1. create target folders
2. move/rename media files
3. move/rename subtitle sidecars
4. move recognized extras
5. split crossover or cross-show files into their correct series folders
6. move approved standalone movies into the movie library when requested
7. remove junk files
8. remove empty directories
9. verify the final tree
10. summarize what changed

When a dry-run `plan.json` already captures the approved file moves, prefer `scripts/apply_plan.py` over ad hoc shell renames so apply-time behavior stays deterministic and easy to re-verify.

## Final summary

Report:
- number of movie/show folders renamed
- number of media files moved/renamed
- number of subtitle files normalized
- number of extras moved
- number of files moved to `Specials`, `Other`, or another show folder
- number of standalone movies moved across libraries, if any
- number of junk files removed
- any artifact-only folders or compilation files still requiring manual attention
- any leftovers still requiring manual attention

## Examples

### Example 1: Movies
User: "Rename and restructure the movies in this folder for Plex using TMDB and the token in my .env. Show me the plan first."

Expected behavior:
- find `.env`
- scan movie files and sidecars
- match titles against TMDB
- propose `Movie Title (Year)` folder/file names
- ask before applying

### Example 2: TV
User: "Clean up `../tv` for Plex using TVDB. Fix seasons, specials, subtitles, and extras, but don't apply until I approve."

Expected behavior:
- authenticate to TVDB
- identify each series
- use official episode ordering
- rename to `Show Name (Year)/Season XX/...`
- use `Specials/` for season 0
- use `Other/` for generic extras
- ask before applying

### Example 3: Mixed messy files
User: "This TV folder is a mess. Some files have SxxEyy, some only have titles, and there are .parts and .DS_Store files everywhere. Make it Plex-friendly."

Expected behavior:
- inventory first
- title-match only where necessary
- report low-confidence mappings
- separate episode files from extras
- propose junk cleanup
- wait for approval before changes

### Example 4: Anthology shorts with odd official seasons
User: "Organize my `Tom and Jerry` and `Donald Duck` folders for Plex using TVDB official order. Keep the official season structure even if it looks weird."

Expected behavior:
- identify anthology/shorts handling early
- verify TVDB official season numbers instead of inventing per-year seasons
- use exact official seasons such as `Season 1940`, `Season 1950`, or `Season 1960` when that is what TVDB uses
- title-match shorts by normalized episode title and year
- report any shorts that still need manual review before apply

### Example 5: Cross-show TV bundle with movie inside
User: "This `Batman Beyond` folder also has the movie and crossover episodes from other DC shows. Split everything into the right Plex locations, but show me the plan first."

Expected behavior:
- identify the main `Batman Beyond` episodes
- route the short to `Specials`
- surface the standalone movie and, if the user approves, move it into the movie library using movie naming rules
- split crossover episodes into the correct show folders such as `The Zeta Project`, `Static Shock`, or `Justice League`
- summarize all cross-show moves before apply

### Example 6: Single-file compilation
User: "I have one MKV that contains the entire `Star Wars: Clone Wars (2003)` miniseries. Put it somewhere sensible for Plex, but don't pretend it's a regular episode."

Expected behavior:
- recognize it as a whole-series compilation
- warn that Plex will not index it as individual episodes unless split
- leave it untouched or place it in `Other/` depending on the user's preference
- do not fabricate episode-level filenames for the compilation
