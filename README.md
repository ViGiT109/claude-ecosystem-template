# ${PROJECT_NAME}

${PROJECT_VISION}

---

## Quick Start

```powershell
git clone <repo-url> C:\${PROJECT_NAME}
cd C:\${PROJECT_NAME}
.\bootstrap.ps1          # personalize, install deps, first commit
```

See `ENVIRONMENT_SETUP.md` for the full setup guide.

## Project Structure

```
${PROJECT_NAME}/
├── .agents/             # AI rules and coding conventions
├── .claude/             # Claude Code commands, hooks, agents, skills
├── .memory/             # Project memory bank (activeContext, lessons, etc.)
├── docs/adr/            # Architecture Decision Records
├── docs/specs/          # Feature specifications
├── scripts/             # Operational scripts (health check, reasoning bank, etc.)
├── .ecosystem.toml      # Project stack declaration
├── CLAUDE.md            # AI assistant rules (auto-loaded by Claude Code)
├── ROADMAP.md           # Now / Next / Later
├── BUGS.md              # Bug registry
└── CHANGELOG.md         # Keep-a-Changelog
```

## AI Ecosystem

This project uses a **Claude Code AI ecosystem** with:

- **Progressive Disclosure** — context loaded in 3 tiers (ALWAYS / AUTO / ON-DEMAND)
- **Memory Bank** — 7 persistent markdown files in `.memory/`
- **ReasoningBank** — ChromaDB-backed semantic lesson retrieval
- **Deterministic Hooks** — `session_start`, `block_no_verify`, `stop_audit`
- **Self-Improvement Loop** — errors → lessons → rules → hooks

Start a session: `/new_session`
Audit a session: `/audit_ecosystem`

## Documentation

- `ENVIRONMENT_SETUP.md` — full setup guide
- `ROADMAP.md` — project roadmap
- `CHANGELOG.md` — change history
- `docs/adr/` — architectural decisions
- `docs/specs/` — feature specifications
