# Task: v2.0.0 Release

**Branch:** `main` (post-fast-forward from `feat/v2.0.0-phase-6b-design-bundle`)
**Spec:** [docs/specs/2026-05-21-production-readiness.md](docs/specs/2026-05-21-production-readiness.md)
**Goal:** Cut the v2.0.0 release locally.

## Steps

- [x] Fast-forward merge `feat/v2.0.0-phase-6b-design-bundle` → `main` (linear stack of 12 commits, stack tip `ea82587`)
- [x] Write `CHANGELOG.md` v2.0.0 entry — Keep-a-Changelog format, breaking changes called out (AGENTS.md source-of-truth, Skills→skills rename, generic skills removed, Opus-default policy)
- [x] Update `.memory/activeContext.md` — released state, next-steps refreshed
- [x] Update `task.md` — release wrap-up
- [x] Commit `release: v2.0.0 — production-readiness upgrade` (NO `--no-verify`)
- [x] Tag `v2.0.0` on the release commit (annotated)

## Pending (post-commit, awaiting user direction)

- [-] Push `main` + tag to `origin` — user confirms
- [-] Draft GitHub release notes via `gh release create v2.0.0`
- [-] Sanity `/audit_ecosystem` on released state (target ≥90/100)

## Acceptance

- `main` carries all 12 v2.0.0 commits + the release commit
- `CHANGELOG.md` has a complete `## [2.0.0]` section
- `git tag` lists `v2.0.0`
- pre-commit clean
