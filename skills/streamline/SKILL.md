---
name: streamline
license: MIT
description: Clean up changed code for clarity, reuse, and efficiency while preserving observable behavior. Use only when explicitly invoked for a quality-focused cleanup pass, not for correctness review.
disable-model-invocation: true
compatibility: Requires repository access and git; uses independent parallel review when available and otherwise runs inline.
---

# Streamline

Clean up the changed code without changing observable behavior. This is a quality cleanup pass, not a correctness or bug review: do not fix behavior merely because it seems wrong.

## Route the review

Review all four perspectives in the current context when the invocation includes `low` as a standalone mode immediately after the skill name OR when independent parallel delegation is unavailable. Otherwise, assign one independent reviewer to each perspective in parallel. Use the same workflow in either case. Treat any remaining text as the review target.

If the invocation names an explicit target, review it. Otherwise use `git diff @{upstream}...HEAD`, falling back to `git diff main...HEAD` and then `git diff HEAD~1`. Include `git diff HEAD` when the working tree has changes or the range diff is empty.

## Review and clean up

Inspect the target and its surrounding code, then review exactly these four perspectives:

1. **Reuse** — existing helpers, utilities, or abstractions that should be reused instead of duplicated.
2. **Simplification** — redundant state, duplication, nesting, dead code, or single-use temporary aliases that add no meaning and can be removed or made clearer.
3. **Efficiency** — repeated expensive work or avoidable retention that can be reduced without changing behavior.
4. **Abstraction depth** — special cases placed at the wrong level; prefer the general underlying mechanism when it preserves behavior and keeps the change in scope.

Normalize and deduplicate findings across perspectives. Apply only fixes whose behavior is preserved. Skip and document findings that risk intended behavior, require broad changes outside the target, or are false positives. Do not add generic refactoring advice, correctness fixes, or unrelated edits.

## Finalize

Reread the final diff. Inspect every added or changed comment. Keep comments only when they explain a non-obvious invariant, gotcha, external constraint, or why a simpler-looking alternative is wrong; PREFER ONE LINE. Remove comments that restate code, narrate control flow or the change, or duplicate readable signatures or types. In tests, prefer expressive test names unless setup intent is non-obvious. Preserve directives and annotations consumed by tooling.

End with a terse summary of fixes and skips (or that the target was already clean), and truthfully state whether parallel or inline mode ran.
