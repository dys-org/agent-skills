---
name: multi-angle-code-review
description: Run a comprehensive code review across multiple quality angles. Use when the user asks to review a PR, branch, diff, or recent changes; wants targeted feedback on tests, comments, error handling, types, simplification, or overall code quality; or explicitly requests a parallel, subagent, or orchestrated review. Prefer this skill for multi-aspect code review before opening a PR or after review feedback lands.
disable-model-invocation: true
---

# Multi-Angle Code Review

## Goal
Review the current changeset across the applicable quality angles and return a concise, actionable summary tied to the changed code.

## Execution mode

By default, assign each applicable review angle to an independent reviewer and run them in parallel. If `low` appears immediately after the skill name, review all applicable angles yourself in one integrated pass; treat any remaining text as the review target or angle selection. If parallel delegation is unavailable, use the `low` behavior.

## Core principles

- Focus on changed files first; only expand scope when the diff requires broader context.
- Prefer concrete issues with file and line references over vague stylistic commentary.
- Do not invent problems. If something is uncertain, say so and explain what would confirm it.
- Read repository guidance before judging conventions. Check files such as `AGENTS.md`, `CLAUDE.md`, `README`, `CONTRIBUTING`, or other local instructions if present.
- Treat review as triage: critical issues first, then important issues, then suggestions.
- Keep review work read-only. Apply fixes only when the user separately asks for them.

## Review angles

Available angles are `comments`, `tests`, `errors`, `types`, `code`, and `simplify`. Infer which to cover from the user's request; use `all` or no selection to cover every applicable angle.

## Workflow

### 1. Determine review scope

Use any PR, branch, commit, diff, or file target supplied by the user. If GitHub CLI is available and useful, inspect the targeted or active PR for context.

Otherwise, gather both committed branch changes and working-tree changes:

- Use `git diff @{upstream}...HEAD`, falling back to `git diff main...HEAD` or `git diff HEAD~1` when there is no upstream.
- Use `git diff HEAD` for staged and unstaged tracked changes.
- Use `git status --short` to find untracked files and read those files directly.

### 2. Select applicable angles

- Always run **code**
- Run **tests** if test files changed or behavior changed
- Run **comments** if comments or docs changed
- Run **errors** if control flow, network, storage, async, or exception handling changed
- Run **types** if types, interfaces, schemas, or validation changed
- Run **simplify** if implementation code changed or the user explicitly asks for cleanup

### 3. Execute the review angles

Apply each angle's guidance to the relevant diff and nearby code. Read tests or documentation only as needed, and record material findings with severity and evidence.

For parallel review, give each reviewer the review scope, changed files, repository constraints, the read-only requirement, and its angle-specific guidance. Do not repeat delegated angles in the primary context.

If the user explicitly requested delegation but it is unavailable, mention that the integrated review was used instead.

### 4. Severity rules

Use these buckets consistently:

- **Critical** — must fix before merge; likely correctness, data loss, security, crash, or severe regression risk
- **Important** — should fix; meaningful maintainability, missing coverage, unsafe assumptions, or likely edge-case bugs
- **Suggestions** — optional improvements; simplifications, naming, readability, or follow-up cleanup
- **Strengths** — things the change does well that are worth preserving

Avoid inflating severity for minor style preferences.

### 5. Output format

Use this structure, omitting sections that have no useful content:

## Code Review Summary

### Critical Issues (X found)
- [review-angle] Issue description [`path/to/file:line`]

### Important Issues (X found)
- [review-angle] Issue description [`path/to/file:line`]

### Suggestions (X found)
- [review-angle] Suggestion [`path/to/file:line`]

### Strengths
- What the change does well

### Recommended Action
- Concrete next step derived from the findings

If there are no actionable findings, say so once instead of returning empty sections. Keep recommended actions specific to the findings and omit them when no action is needed.

## Angle-specific guidance

### comments

- Flag comments that restate obvious code
- Flag comments that appear inaccurate, stale, or overly detailed
- Prefer fewer, higher-value comments over exhaustive narration
- Check whether docs reflect the changed behavior
- Suggest a rewrite or removal for each comment issue

### tests

- Look for missing behavioral coverage, not just line coverage
- Check happy path, edge cases, failure paths, and regression risk
- Prefer precise tests over snapshot noise
- Notice when tests exist but do not actually verify the changed contract
- Explain what regression each proposed test would catch

### errors

- Flag empty catch blocks, broad exception handling, ignored return values, or dropped error context
- Check logging quality and whether failures can be diagnosed
- Check retry and cleanup paths where relevant
- Look for partial failure modes that leave state inconsistent

### types

- Prefer types that make invalid states harder to represent
- Flag ambiguous unions, leaky primitives, or unchecked casting
- Check whether validation and runtime behavior match the type surface
- Look for missing invariants at module boundaries

### code

- Check correctness first, then maintainability
- Compare the change against project conventions and local patterns
- Read nearby code before suggesting refactors
- Call out risky assumptions, dead code, duplicated logic, or weak abstractions when they matter

### simplify

- Suggest the smallest safe simplification
- Preserve behavior; do not propose cleanup that obscures intent
- Prefer removing unnecessary indirection, branches, and duplicated code
- Keep recommendations grounded in the actual diff, not hypothetical rewrites

## Consolidating delegated reviews

The primary context owns the final judgment:

1. Deduplicate overlapping findings by location, underlying issue, and remedy.
2. Verify file and line references against the current workspace when practical.
3. Drop vague, speculative, low-confidence, or purely stylistic findings.
4. Preserve useful evidence when multiple angles identify the same issue.
5. Order the remaining findings by severity and user impact.
6. Produce one coherent report rather than disconnected reviewer outputs.
