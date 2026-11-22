# Changelog

All notable collection-level changes are recorded here. This project uses Semantic Versioning.

## [0.6.0](https://github.com/dys-org/agent-skills/compare/v0.5.0...v0.6.0) (2026-11-22)


### Features

* allow model invocation for multi-angle-code-review ([#15](https://github.com/dys-org/agent-skills/issues/15)) ([c30350d](https://github.com/dys-org/agent-skills/commit/c30350da3c6aa08100e5b4b49f3d4ebf95cc3bd4))

## [0.5.0](https://github.com/dys-org/agent-skills/compare/v0.4.1...v0.5.0) (2026-11-21)


### Features

* remove parallel review modes from streamline and multi-angle-code-review ([#13](https://github.com/dys-org/agent-skills/issues/13)) ([b2e1b6a](https://github.com/dys-org/agent-skills/commit/b2e1b6abd73dbc5cbc99bea0edcb8beb178eaadd))

## [0.4.1](https://github.com/dys-org/agent-skills/compare/v0.4.0...v0.4.1) (2026-11-04)


### Bug Fixes

* consolidate automatic cleanup selection on streamline ([#11](https://github.com/dys-org/agent-skills/issues/11)) ([800a04e](https://github.com/dys-org/agent-skills/commit/800a04ef49691325c35f9f46448d18f40feebb23))

## [0.4.0](https://github.com/dys-org/agent-skills/compare/v0.3.0...v0.4.0) (2026-10-30)


### Features

* aggressively purge comments in streamline ([#8](https://github.com/dys-org/agent-skills/issues/8)) ([f389510](https://github.com/dys-org/agent-skills/commit/f389510fda265c7a678271dc4dad1985a081faa8))
* flag review comments more aggressively ([#10](https://github.com/dys-org/agent-skills/issues/10)) ([30357a1](https://github.com/dys-org/agent-skills/commit/30357a1d79bbb2e4e626e58638131d542f57ea25))

## [0.3.0](https://github.com/dys-org/agent-skills/compare/v0.2.2...v0.3.0) (2026-09-14)


### Features

* default reviews to single context ([#6](https://github.com/dys-org/agent-skills/issues/6)) ([019fdb9](https://github.com/dys-org/agent-skills/commit/019fdb9f6868b46a40d207e6dd6f6aa548658431))

## [Unreleased]

## [0.2.2] - 2026-09-13

- Strengthen `multi-angle-code-review` test guidance to prioritize observable regressions, identify redundant or brittle tests, and require evidence for recommendations.

## [0.2.1] - 2026-09-07

- Remove the prose skill's Python runtime dependency and deterministic linter. The skill now relies on its built-in final review.

## [0.2.0] - 2026-09-02

- Add the explicit-only `prose` skill for drafting, revision, and audits that avoid common AI writing tropes.
- Add a deterministic prose linter, unit tests, and eight behavioral evaluation fixtures.

## [0.1.1] - 2026-08-27

- Restore `streamline`'s detailed three-phase cleanup workflow, including four-perspective review, skip handling, and final comment hygiene.
- Simplify skill frontmatter to rely on the repository's root MIT license and require only `name` and `description`, while preserving explicit-only invocation metadata.

## [0.1.0] - 2026-08-27

- Publish `code-simplifier`, `multi-angle-code-review`, `plex-library-organizer`, and `streamline`.
- Add portable installation metadata, eval fixtures, validation, and organizer safety tests.

[Unreleased]: https://github.com/dys-org/agent-skills/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/dys-org/agent-skills/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/dys-org/agent-skills/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/dys-org/agent-skills/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/dys-org/agent-skills/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/dys-org/agent-skills/releases/tag/v0.1.0
