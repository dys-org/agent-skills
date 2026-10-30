---
name: streamline
description: Clean up changed code for clarity, reuse, and efficiency while preserving observable behavior. Use only when explicitly invoked for a quality-focused cleanup pass, not to find bugs.
disable-model-invocation: true
---

# Streamline

Improve the changed code without altering its observable behavior. This is a quality-cleanup pass, not a correctness review. Do not fix behavior merely because it appears wrong.

## Route the review

By default, review all four perspectives in the current context. If `high` appears immediately after the skill name, assign one independent reviewer to each perspective and run them concurrently; treat any remaining text as the review target. If parallel delegation is unavailable, use the default single-context behavior. Use the same workflow in either mode.

If the invocation names a PR, branch, file, or other explicit target, review that target. Otherwise, use `git diff @{upstream}...HEAD`, falling back to `git diff main...HEAD` and then `git diff HEAD~1`. Include `git diff HEAD` when the working tree has changes or the range diff is empty. The resulting changes are the review scope.

### Phase 1 — Review

Examine the scoped changes from each perspective below. Record every actionable finding with its `file`, `line`, a one-sentence `summary`, the concrete cost it introduces, and the proposed correction.

#### Reuse

Look in adjacent files and shared or utility modules for existing code that already provides a capability introduced by the change. Identify the specific helper or abstraction to reuse instead of maintaining another implementation.

#### Simplification

Find complexity that does not contribute behavior: information stored more than once or derivable from other state, copied blocks with minor differences, avoidable nesting, unreachable leftovers, and single-use aliases that merely rename an expression. Describe the smallest clearer equivalent.

#### Efficiency

Find work the change performs more often or earlier than necessary, including repeated computation, repeated file or network access, independent operations performed serially, and eager work added to initialization or frequently used paths.

For callbacks, closures, or other long-lived values, check whether they retain a larger surrounding environment than they need. When that retention is material, prefer an object that owns only the required data. State what computation, I/O, waiting, or retained state the correction removes.

#### Abstraction depth

Check whether the change belongs at the layer where it was implemented. When a caller-specific exception compensates for behavior owned by shared infrastructure, prefer the smallest general correction at the owning layer, provided it preserves intended behavior and remains within scope.

Do not introduce correctness fixes, unrelated edits, or generic refactoring advice.

### Phase 2 — Apply the fixes

Wait until all four perspectives are complete. Merge findings that describe the same underlying mechanism, then apply each unique correction directly.

Apply only changes that preserve intended behavior. Skip a finding when its correction would alter intent, require broad work outside the review scope, or prove to be a false positive. Record every skip briefly.

### Phase 3 — Purge comments

Target zero comments in the original diff or attached to changed code. Leave all others alone; cleanup does not expand scope.

Make comments unnecessary through clearer code. Otherwise, keep only those preventing a specific wrong change by explaining an external constraint, inexpressible invariant, or broken obvious alternative. One line max.

Always delete:

- comments that restate or narrate the code
- docstrings that repeat the signature
- banners
- change history
- commented-out code
- `TODO`/`NOTE`/`FIXME` without a ticket
- any comment in tests

Keep tooling directives. When unsure, delete.

### Phase 4 — Summarize

Summarize fixes and skips, or say the code was already clean. Give the number of deleted comments and list each survivor as `file:line — reason`. State whether you used parallel reviewers or a single context.
