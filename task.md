# Task: v2.0.0 Phase 1 — Critical Fixes (PR #1)

**Branch:** `feat/v2.0.0-phase-1-critical-fixes`
**Spec:** [docs/specs/2026-05-21-production-readiness.md](docs/specs/2026-05-21-production-readiness.md) §Phase 1
**Goal:** unblock cross-platform cloning (macOS/Linux) + introduce AGENTS.md source-of-truth + bootstrap guard.

## Legend
- `[ ]` — not started (blocks commit)
- `[/]` — in progress (blocks commit)
- `[x]` — completed
- `[-]` — skipped / not applicable

## Steps

### 1.1 — Rename `.claude/Skills/` → `.claude/skills/`
- [x] Two-step git mv via temp dir (Windows case-insensitive workaround)
- [-] Update case-sensitive path references — N/A (no `.claude/Skills/` paths in code; prose mentions use lowercase inline path)
- [x] Verify `git ls-files .claude/skills` returns lowercase paths
- [x] Commit: `refactor(skills): rename Skills/ → skills/ for case-sensitive FS`

### 1.2 — Delete generic skills (deep-research, triz, problem-solving)
- [x] `git rm -r .claude/skills/{deep-research,triz,problem-solving}`
- [x] Verify no remaining references (Grep) — only in task.md and spec, intentional
- [x] Commit: `chore(skills): remove generic skills (deferred to Anthropic marketplace)`

### 1.3 — Bootstrap guard in `session_start.py`
- [ ] Add `check_bootstrap_done()` scanning `README.md`, `CLAUDE.md`, `.ecosystem.toml` for `${PROJECT_NAME}` placeholder
- [ ] If found → print 🔴 BOOTSTRAP REQUIRED block + early return (skip normal context output)
- [ ] Smoke test: temporarily reintroduce a placeholder → hook fires
- [ ] Commit: `feat(hooks): block session with 🔴 BOOTSTRAP REQUIRED on unprocessed placeholders`

### 1.4 — AGENTS.md source-of-truth + sync system
- [ ] Create `AGENTS.md` from current `CLAUDE.md` (with universal terminology: «AI assistant» / «agent» instead of «Claude»)
- [ ] Create `.agents/claude-overrides.md` (Claude-specific sections, may start empty)
- [ ] Write `scripts/sync_agents_md.py` (reads AGENTS.md + overrides → writes CLAUDE.md with `<!-- AUTO-GENERATED -->` header)
- [ ] Regenerate `CLAUDE.md` via the script
- [ ] Add `agents-md-sync` hook to `.pre-commit-config.yaml`
- [ ] Smoke test: edit AGENTS.md without re-sync → pre-commit blocks
- [ ] Commit: `feat(agents): AGENTS.md as source-of-truth + sync script + pre-commit guard`

### Verification (PR #1 acceptance)
- [ ] `git ls-files .claude/skills` returns lowercase paths
- [ ] `python scripts/sync_agents_md.py --stdout | diff - CLAUDE.md` → empty
- [ ] Simulated bootstrap guard: hook prints 🔴 block when `${PROJECT_NAME}` is present
- [ ] No leftover Skills (case-sensitive) references outside intentional contexts

### Wrap-up
- [ ] Update `.memory/activeContext.md` — Phase 1 done, Phase 2 next
- [ ] `gh pr create` against main
