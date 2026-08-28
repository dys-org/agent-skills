---
name: code-simplifier
description: Simplify specific code for readability and maintainability while preserving behavior. Use when the user explicitly asks to reduce complexity, nesting, duplication, or indirection; clarify control flow; or improve naming and structure. This is a focused refactor, not a comprehensive diff or PR cleanup pass.
---

# Code Simplifier

## Purpose

Improve code readability, consistency, and maintainability without changing what the code does.

Treat simplification as a preservation task: the code should become easier to understand, test, debug, and extend, while all existing behavior remains intact.

## Scope

Prefer recently modified code unless the user explicitly asks for a wider pass.

Use available project context to identify the intended scope:

- VCS diffs, staged changes, or recent edits
- Files named by the user
- Failing lint/type/test output
- Project instruction files such as `AGENTS.md`, `CLAUDE.md`, `WARP.md`, `.cursorrules`, `GEMINI.md`, or repo-specific docs

Do not perform broad rewrites just because nearby code could be improved. Keep changes focused and reviewable.

## Core principles

### Preserve functionality

Change how the code is expressed, not what it does.

Before editing, identify the observable behavior that must remain stable:

- Inputs and outputs
- Public APIs and exported types
- Side effects
- Error behavior
- Ordering, persistence, and network behavior
- UI behavior and accessibility semantics

If preserving behavior is uncertain, stop and gather evidence with tests, type checks, or targeted inspection before rewriting.

### Follow project standards

Infer local conventions from the codebase instead of imposing generic style preferences.

Look for:

- Existing project instruction files
- Nearby working implementations
- Existing lint, formatting, and type conventions
- Established naming, module, component, and error-handling patterns

When local standards conflict with personal preference, use the project standard.

### Prefer clarity over cleverness

Optimize for future maintainers.

Good simplification often means:

- Reducing unnecessary nesting
- Removing redundant abstractions
- Naming intermediate values when it explains intent
- Consolidating duplicated logic
- Deleting comments that merely narrate obvious code
- Keeping comments that explain non-obvious constraints, tradeoffs, or domain rules

Avoid changes that only reduce line count. Dense one-liners, clever chaining, and over-generalized helpers can make code worse even when they look shorter.

### Preserve useful abstractions

Do not collapse abstractions just because they are small.

Keep abstractions when they:

- Express a domain concept
- Isolate side effects
- Improve testability
- Match established architectural boundaries
- Are reused or expected extension points

Remove or inline abstractions when they:

- Only rename a single obvious operation
- Hide important control flow
- Create indirection without semantic value
- Are unused or speculative

## Workflow

1. Identify the target code.
2. Read enough surrounding code to understand conventions and behavior.
3. Note the behavior that must be preserved.
4. Make the smallest coherent simplification.
5. Verify with existing tests, type checks, lint, or focused manual reasoning.
6. Summarize only meaningful changes and any verification performed.

For multi-file changes, simplify in small passes. Avoid mixing simplification with unrelated feature work.

## Safe refactoring patterns

Use these when they fit the codebase:

- Extract a named helper for repeated logic or a complex condition.
- Inline a helper when the helper adds no meaning and has one obvious call site.
- Replace boolean flag soup with named predicates.
- Convert repeated conditional branches into a small lookup only when the lookup stays readable.
- Split large functions by responsibility, not arbitrary length.
- Move validation or normalization closer to boundaries.
- Replace comments that explain "what" with names that reveal intent.
- Keep error handling explicit and consistent with the rest of the project.

## Anti-patterns to avoid

Avoid:

- Changing behavior while claiming it is only a refactor
- Broad formatting churn unrelated to simplification
- Rewriting stable code outside the requested scope
- Introducing new dependencies for cosmetic improvements
- Replacing readable code with dense functional chains
- Hiding important branching behind over-generic utilities
- Removing tests or weakening assertions to make a refactor pass
- Ignoring project instruction files or local conventions

## Verification guidance

Prefer running the narrowest reliable verification available:

- Unit tests for touched code
- Type checks for typed languages
- Lint/format checks if the repo has them
- Focused integration or UI checks when behavior crosses boundaries

If verification is not possible, say what was checked manually and what remains unverified.

## Response style

When finished, keep the summary brief:

- What kind of simplification was made
- What behavior was preserved
- What verification was run, or why it was not run

Do not list every mechanical edit.
