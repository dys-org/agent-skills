# Agent contribution rules

- Use Conventional Commit format for commit messages and pull request titles, such as `feat: add a skill`, `fix: repair validation`, or `chore: update tooling`. Mark breaking changes with `!` or a `BREAKING CHANGE:` footer.
- Do not manually edit `CHANGELOG.md` or `version.txt`. Release Please owns these files after the `v0.2.2` repair.
- Do not create or move release tags, or publish GitHub releases. Merge the Release Please PR after its required checks pass to perform a release.
