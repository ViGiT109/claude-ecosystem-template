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
- [x] Add `check_bootstrap_done()` scanning `README.md`, `CLAUDE.md`, `.ecosystem.toml` for `${PROJECT_NAME}` placeholder
- [x] If found → print 🔴 BOOTSTRAP REQUIRED block + early return (skip normal context output)
- [x] Skip guard in template repo itself via `TEMPLATE_README.md` sentinel (bootstrap.ps1 removes it)
- [x] Smoke test: 3-scenario check (template/downstream/restored) — all pass
- [x] Commit: `feat(hooks): block session with 🔴 BOOTSTRAP REQUIRED on unprocessed placeholders`

### 1.4 — AGENTS.md source-of-truth + sync system
- [x] Create `AGENTS.md` from current `CLAUDE.md` (with universal terminology: «AI assistant» / «agent» instead of «Claude»)
- [x] Create `.agents/claude-overrides.md` (Claude-specific sections, starts as empty stub)
- [x] Write `scripts/sync_agents_md.py` (--write / --stdout / --check modes; supports overrides; emits AUTO-GENERATED header)
- [x] Regenerate `CLAUDE.md` via the script
- [x] Add `agents-md-sync` hook to `.pre-commit-config.yaml`
- [x] Smoke test: edit AGENTS.md without re-sync → pre-commit hook Failed; post-revert → Passed
- [x] Commit: `feat(agents): AGENTS.md as source-of-truth + sync script + pre-commit guard`

### Verification (PR #1 acceptance)
- [x] `git ls-files .claude/skills` returns lowercase paths
- [x] `python scripts/sync_agents_md.py --check` → exit 0 (no drift)
- [x] Simulated bootstrap guard: hook prints 🔴 block when `${PROJECT_NAME}` is present
- [x] No leftover `.claude/Skills/` (case-sensitive) path references outside `task.md` / spec
- [x] `pre-commit run --all-files` → `agents-md-sync` Passed; `task-guardrail` correctly flags own list; ruff Skipped (no Python source yet)

### Wrap-up
- [x] Update `.memory/activeContext.md` — Phase 1 done, Phase 2 next
- [-] `gh pr create` against main — **N/A**: no `origin` remote configured + `gh` CLI absent. Branch is local-only. User decides: (a) add GitHub remote + push + open PR, (b) merge branch into main locally, (c) keep branch for review without PR.
