# CHANGELOG Maintenance Rules

> **This file contains rules for maintaining CHANGELOG.md.**
> Git conventions (commits, tags, branches) → see `.agents/rules/git.md`

## CHANGELOG.md — Change journal

### Format

```markdown
## [Unreleased]

### Added
- Brief description of what was added

### Fixed
- Brief description of the fix
```

### Categories

- **Added** — new features, modules, files
- **Changed** — changes to existing functionality
- **Fixed** — bug fixes
- **Removed** — deleted features or files
- **Deprecated** — features planned for removal
- **Security** — security-related changes

### Versioning (Semantic Versioning)

- **MAJOR** (x.0.0) — incompatible API changes or full architectural overhaul
- **MINOR** (0.x.0) — new functionality, backwards-compatible
- **PATCH** (0.0.x) — bug fixes only

### On release (creating a git tag)

1. Move all entries from `[Unreleased]` into a new section `[X.Y.Z] — YYYY-MM-DD`.
2. Leave `[Unreleased]` empty (section header only).
3. Commit: `docs(changelog): release vX.Y.Z`.
4. Tag: `git tag -a vX.Y.Z -m "vX.Y.Z: <summary>"`.

## SESSION_LOG format (optional)

If the project maintains a `SESSION_LOG.md` (not required by the ecosystem):

```markdown
## YYYY-MM-DD — Brief headline

**Task:** Structured description of user request (moderately condensed)
**Result:**
- What was done (no code — text descriptions only)
- Key decisions
- What was deferred or not completed
```

### Rules

- User's prompt: condensed and structured (NOT verbatim)
- No code blocks — text descriptions only
- One entry per session
- New entries added at the top (newest first)
