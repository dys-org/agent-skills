# Agent Skills

Five portable agent skills authored and maintained by dys-org. GitHub is the canonical source; this collection is not published to npm and does not require npm publication.

| Skill | Purpose | Invocation |
| --- | --- | --- |
| `code-simplifier` | Focused readability and complexity refactoring that preserves behavior. | May be invoked implicitly. |
| `multi-angle-code-review` | Read-only review across code, tests, comments, errors, types, and simplification. | Explicit only. |
| `plex-library-organizer` | Metadata-backed, approval-gated Plex library planning and organization. | Explicit only. |
| `prose` | Draft, revise, or audit prose while removing common AI writing tropes. | Explicit only. |
| `streamline` | Explicit four-angle cleanup of changed code: reuse, simplification, efficiency, and altitude. | Explicit only. |

`code-simplifier` works on a specific readability or complexity refactor. `streamline` reviews an entire changeset through four cleanup angles and applies the resulting quality improvements.

## Install with Skills CLI

The commands below use the current [`skills` CLI](https://github.com/vercel-labs/skills#readme).

```bash
# Discover the collection
npx skills add dys-org/agent-skills --list

# Install one or several skills into the current project
npx skills add dys-org/agent-skills --skill code-simplifier
npx skills add dys-org/agent-skills --skill code-simplifier --skill streamline
npx skills add dys-org/agent-skills --skill prose

# Choose agents, or install globally
npx skills add dys-org/agent-skills --skill prose -a claude-code -a codex
npx skills add dys-org/agent-skills --skill prose -g -a codex -y

# Update or remove an installed skill
npx skills update streamline
npx skills remove streamline
```

Pin an immutable release or commit by using a Git URL:

```bash
npx skills add https://github.com/dys-org/agent-skills.git#v0.2.0 --skill prose
npx skills add https://github.com/dys-org/agent-skills/archive/<commit-sha>.zip --skill streamline
```

## Plex organizer prerequisites

The organizer requires Python 3.10+, network access, and TMDB and/or TVDB credentials appropriate to the media being organized. Copy the sanitized `.env-example` near the media root or export the documented variables. Plans use root-relative paths only; absolute paths and any path resolving outside the selected media root are rejected.

## Releases

The collection uses manual collection-level SemVer recorded in [`CHANGELOG.md`](CHANGELOG.md). Release tags pin the complete five-skill collection.
