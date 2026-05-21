# Task: v2.0.0 Phase 6b — Design Bundle (PR #6b)

**Branch:** `feat/v2.0.0-phase-6b-design-bundle` (off Phase 6a)
**Spec:** [docs/specs/2026-05-21-production-readiness.md](docs/specs/2026-05-21-production-readiness.md) §Phase 6
**Goal:** Design-heavy second half of the original Phase 6 — new subagents, statusline hook, ADR worked example, design-rationale doc.

## Legend
- `[ ]` — not started (blocks commit)
- `[/]` — in progress (blocks commit)
- `[x]` — completed
- `[-]` — skipped / not applicable

## Steps

### 6.2 — Subagents (Opus design)
- [x] **6.2a** `.claude/agents/code-reviewer.md` — `model: opus`, `tools: Read, Grep, Glob, Bash`. Use for thorough, independent reviews of staged/diff'd changes. System prompt: security focus, correctness, style, no commits. Mirror frontmatter shape of `ecosystem-auditor.md`.
- [x] **6.2b** `.claude/agents/researcher.md` — `model: sonnet`, `tools: Read, Grep, Glob, WebFetch, WebSearch`. Use for open-ended investigation that should not burn main-thread context. System prompt: scope discipline, citation hygiene, "report don't act".

### 6.3 — Statusline hook
- [x] **6.3a** `.claude/hooks/statusline.py` — reads JSON from stdin (Claude Code statusLine API), outputs single-line `🤖 <model> | 🌿 <branch> | 📊 <ctx%>`. Graceful fallbacks (no git → no branch segment).
- [x] **6.3b** Register in `.claude/settings.json` under top-level `statusLine` field, routed through `_run.py`.

### 6.6 — ADR + spec examples
- [x] **6.6a** `docs/adr/001-agents-md-source-of-truth.md` — real worked example documenting why `AGENTS.md` is the source-of-truth (PR #1 decision). Uses `_template.md` structure.
- [x] **6.6b** Update `docs/adr/README.md` index — add ADR-001 row, replace template placeholder.
- [x] **6.6c** Update `docs/specs/README.md` index — add the production-readiness spec row.

### 6.7 — Design doc
- [x] **6.7a** Create `docs/template-design.md` — captures the "why" (Progressive Disclosure, Self-Improvement Loop, hooks-in-Python rationale, 3-level memory model, maturity history). Survives bootstrap so downstream projects retain the rationale.
- [x] **6.7b** Slim `TEMPLATE_README.md` to quickstart + directory layout; cross-reference `docs/template-design.md` for rationale. (Don't delete — bootstrap.ps1 removes it on first run anyway.)

### wrap
- [x] Manifest + AGENTS.md sync sanity (`regenerate_plugin_manifest.py --check`, `sync_agents_md.py --check`)
- [x] Update `.memory/activeContext.md` — Phase 6b complete; remaining Phase 6 work done; ready for CHANGELOG/tag
- [x] Commit `feat(design): v2.0.0 Phase 6b — subagents + statusline + design doc` (NO `--no-verify`)

## Acceptance
- 2 new subagent files exist with correct frontmatter (matches `ecosystem-auditor.md` schema)
- `statusline.py` runs to completion when fed empty stdin (no crash) and produces a sensible single-line output
- `settings.json` registers `statusLine` and validates against the schema (still loads)
- ADR-001 fills all template sections; both index README.md files updated
- `docs/template-design.md` exists; `TEMPLATE_README.md` references it
- pre-commit clean (manifest sync expects to detect new hook + 2 new agents)
