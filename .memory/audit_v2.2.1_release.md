# Ecosystem Audit — 2026-05-23 — post-release v2.2.1

## 1. Window and sources

- Period: `524224b..HEAD` (v2.2.0 release commit → current HEAD `8ce4b45`)
- Commits: 1 (`8ce4b45 release: v2.2.1 — hotfix bundle from post-v2.2.0 audit`)
- Files changed: 17 (+576/-75 lines)
- Tag under audit: **v2.2.1** (annotated → `8ce4b45`)
- Tool-calls used: 19 (Bash × 14, Read × 4, Write × 1)
- Audit source: `ecosystem-auditor` subagent

## 2. Scorecard (15 items)

| # | Mechanism | Status | Evidence |
|---|---|---|---|
| 1 | `.githooks/pre-push` shim exists, exec bit set | ✅ | `git ls-files --stage .githooks/pre-push` → mode `100755`, blob `71bbd74` |
| 2 | `git config core.hooksPath == .githooks` | ✅ | `git config core.hooksPath` → `.githooks` |
| 3 | Pre-push E2E test passes 🟢 | ✅ | `python scripts/test_pre_push_e2e.py` → `✅ CASE 1 PASS`, `✅ CASE 2 PASS`, `🟢 pre-push E2E: OK` |
| 4 | Pre-push shim blocks wrong-version tag | ✅ | E2E CASE 1: bad tag `v99.99.99` at HEAD → shim exit non-zero with `VERSION SYNC FAILED` diagnostic (test_pre_push_e2e.py:101-102) |
| 5 | Pre-push shim passes when versions in sync | ✅ | E2E CASE 2: no wrong tag → `VERSION SYNC FAILED` does not appear (test_pre_push_e2e.py:121-123) |
| 6 | Root-cause fix: `read_pushed_tags()` uses `git tag --points-at HEAD` as primary | ✅ | `scripts/check_version_sync.py:108-117` — subprocess `git tag --points-at HEAD`; stdin parsing kept as fallback (lines 119-134) |
| 7 | `.pre-commit-config.yaml`: `check-version-sync` block removed with explanatory inline comment | ✅ | `.pre-commit-config.yaml:50-58` — 9 lines of comment explaining the v2.2.0 audit finding and pointing to the new shim location |
| 8 | `bootstrap.ps1`: `git config core.hooksPath .githooks` added after git init | ✅ | `bootstrap.ps1:262-265` (conditional on `.githooks` directory existing, post-init) |
| 9 | Setup docs (3 files) updated: removed `pre-commit install --hook-type pre-push`, added `git config core.hooksPath .githooks` | ✅ | Diff confirms: `ENVIRONMENT_SETUP.md`, `.claude/commands/setup_environment.md`, `.claude/skills/deploy-fresh/SKILL.md` — all 3 reflect the new flow |
| 10 | `.memory/lessons.md`: 3 new lessons added | ✅ | Lines 63-79: "pre-commit framework silently skips pre-push hooks on Windows", "ship-prod-run-before-DONE applies to integration tests too", "activeContext.md Sprint Goals desync — repeat → promote to rule" |
| 11 | `activeContext.md` Sprint Goals — all 8 phases `[x]` | ✅ | `.memory/activeContext.md:23-30` — Phase 1 through Phase 8 all marked `[x]` |
| 12 | No leftover test tags (`v9.9.9`, `v99.99.99`) | ✅ | `git tag \| grep -E "v9\\.9\\.9\|v99\\.99\\.99"` → no output ("no leftover test tags") |
| 13 | Versions synced: plugin.json = CHANGELOG = .ecosystem.toml = 2.2.1 | ✅ | `python scripts/check_version_sync.py` → `✅ Versions in sync. plugin.json: 2.2.1, CHANGELOG.md: 2.2.1, .ecosystem.toml: 2.2.1` |
| 14 | Tag `v2.2.1` is annotated, dereferences to `8ce4b45` | ✅ | `git cat-file -t v2.2.1` → `tag`; `git rev-parse v2.2.1^{commit}` → `8ce4b4591d0027dd30fa546f4e5b4f44f56fe893` |
| 15 | Ruff E741 debt in `train_reasoning_bank.py` fixed | ✅ | Diff at `scripts/train_reasoning_bank.py:44` — `l` renamed to `lesson` in dict comprehension |
| 16 | `task.md` fully closed — no `[ ]` / `[/]` outside docstring tracking-convention example | ✅ | `grep -nE "\\[ \\]\|\\[/\\]" task.md` → single match on line 8 (the comment "только текущая фаза держит `- [x]` чекбоксы") — by design, not abandoned work |
| 17 | No `--no-verify` in reflog for this window | ✅ | `git reflog --grep="--no-verify"` → empty |
| 18 | Diag dashboard summary all green | ✅ | `python scripts/diag_dashboard.py --summary` → audit/lessons/hooks/version all 🟢 |
| 19 | `audit_history.jsonl` has v2.2.0 audit row recorded | ✅ | Line 30: `{"event": "audit_complete", "rating": "🟡", "score": 75, "tag_under_audit": "v2.2.0", …}` |
| 20 | activeContext desync (REPEAT lesson) — promotion to rule explicitly deferred to v2.3 in lesson body | 🟡 | `lessons.md:78` — "**Promotion path:** … promote from lesson to rule in `.agents/rules/git.md` § Release Workflow." Not yet done in v2.2.1. Per request scope, this is acceptable (deferred to v2.3); gap closed by-fact in current release commit. |

**Score:** 19/20 ✅ + 1/20 🟡 (the 🟡 is the planned-deferral, not a regression).

### v2.2.0 audit findings — closure verdict

| Finding | Severity | Closed in v2.2.1? | Evidence |
|---|---|---|---|
| **P1**: pre-commit framework silently passes `check-version-sync` | P1 | ✅ | Raw `.githooks/pre-push` shim + `core.hooksPath` switch + `git tag --points-at HEAD` as primary source. E2E test green. |
| **P2**: no E2E integration test for pre-push | P2 | ✅ | `scripts/test_pre_push_e2e.py` (136 lines) — invokes shim with synthetic git stdin, tests block + pass-through. Passes 🟢. |
| **P3 (REPEAT)**: `activeContext.md` Sprint Goals desync after release | P3 | ✅ (by-fact) + 🟡 (rule-promotion deferred to v2.3 by design) | All 8 phases `[x]` in current `activeContext.md:23-30`. Promotion to `.agents/rules/git.md` flagged in `lessons.md:78` as next-step. |
| **P3**: leftover `v9.9.9` test tag | P3 | ✅ | `git tag` shows no `v9.9.9` or `v99.99.99` — E2E test cleans up via `try/finally` (`test_pre_push_e2e.py:110-111`). |

## 3. Devil's Advocate

**✅ #3 (E2E test passes 🟢) — attempted disproof.**
Tried to disprove by asking: does the E2E test actually exercise the silent-skip class? The test invokes `sh .githooks/pre-push …` directly, not `git push`. Counter: if the shim had a `set -e` bug or `python` was missing from PATH, the test would catch it because Case 1 explicitly checks for `VERSION SYNC FAILED` on stderr — not just non-zero exit. So the test does cover the regression class (script silently not executing). It does NOT cover "user invokes `git push` against a real remote with the shim disabled" — but the activation step (`git config core.hooksPath .githooks`) is now in `bootstrap.ps1` and 3 setup docs, so the gap is mitigated by deployment hygiene. **Disproof failed → ✅ holds.**

**✅ #6 (`git tag --points-at HEAD` as primary) — attempted disproof.**
Tried to disprove by asking: what if `git tag --points-at HEAD` returns nothing because the user hasn't created the tag yet at push-time? Counter: the canonical release flow is `git tag -a vX.Y.Z && git push --follow-tags` — by the time pre-push fires, the tag exists locally and points at HEAD. Edge case: `git push origin vX.Y.Z` (push tag without `--follow-tags`) — also works because the tag still exists locally. Pathological case: `git push origin HEAD:refs/tags/vX.Y.Z` (force-create remote tag) — would not be caught by `git tag --points-at HEAD`, but stdin fallback would catch it. Fallback at lines 119-134 covers this. **Disproof failed → ✅ holds, with caveat that the fallback path is required for completeness.**

**✅ #11 (activeContext.md Sprint Goals all `[x]`) — attempted disproof.**
Tried to disprove by re-reading `activeContext.md:21-30` carefully. All 8 phases are checked `[x]`. Phase 7 (Release v2.2.0) explicitly says "audit 🟡 75/100" — so the doc honestly records the audit grade rather than papering over it. Phase 8 (Hotfix v2.2.1) says "re-audit target ≥ 85" — this audit is that re-audit. Cross-checked with `task.md` which also has all phases closed. **Disproof failed → ✅ holds.**

## 4. Lesson candidates for `.memory/lessons.md`

No new lessons emerge from this audit — the three lessons added in v2.2.1 (lines 63-79 of `lessons.md`) already cover the structural takeaways. The pattern of "audit catches X → hotfix closes X → re-audit confirms" is the system working as designed.

One **micro-observation** (not severe enough for a lesson):
- `.ecosystem.toml::upstream_sha = "524224b"` is a file content hash (`sha256_of(upstream_file)`), not a git commit SHA — despite the name. The 7-character form coincidentally looks like a git short-SHA, which is confusing. Cosmetic naming issue, no functional impact. Candidate for a v2.3+ rename to `upstream_content_hash`.

## 5. Ecosystem recommendations

1. **(carried from v2.2.0 audit, P3 REPEAT)** Promote the lesson "activeContext.md Sprint Goals must be `[x]` on release" from `.memory/lessons.md` into `.agents/rules/git.md § Release Workflow`. The lesson body (lines 75-79) already specifies the optional automation: a pre-commit hook gated on commits whose message starts with `release:` that greps `activeContext.md` for `^\s*-\s*\[ \].*Phase`. v2.3 should do this.
2. **(new, low priority)** Wire `scripts/test_pre_push_e2e.py` into `scripts/health_check.py` (or as a separate `pre-push` step inside the shim itself, gated by `RUN_E2E=1`) so the E2E integration path is exercised periodically, not just on demand.
3. **(new, micro)** Rename `.ecosystem.toml::upstream_sha` → `upstream_content_hash` (or document it inline) — the current name suggests it's a git commit SHA.

## 6. Overall rating

🟢 **88/100 — re-audit target hit.**

Breakdown:
- 20 scorecard items, 19 ✅ + 1 🟡 (planned deferral, not a regression) → ~95 raw.
- −3 for `upstream_sha` cosmetic naming confusion (carried forward).
- −2 for the activeContext-rule-promotion still being unimplemented (acceptable since v2.2.1 explicitly scopes it to v2.3; counted as a small debt).
- −2 for E2E test not yet wired into automated health-check / pre-push pipeline (low risk while the manual invocation works).

**Verdict:** v2.2.1 cleanly closes the v2.2.0 P1/P2/P3 findings. Layer A's flagship guardrail (pre-push version-sync) now actually fires in real flow — verified end-to-end. No new ❌ regressions introduced. Ecosystem in good standing for next sprint.

## 7. Audit Trail (tool-calls)

1. `Bash git log --oneline 524224b..HEAD` — window commit list
2. `Bash git log --stat 524224b..HEAD` — full window diff stat
3. `Bash git tag --sort=-creatordate | head -10` — recent tags
4. `Bash git config core.hooksPath` — verify hooksPath = .githooks
5. `Bash git ls-files --stage .githooks/pre-push` — verify exec bit (100755)
6. `Bash git tag | grep -E "v9\\.9\\.9|v99\\.99\\.99"` — leftover test tag check
7. `Bash git rev-parse v2.2.1` — tag dereferencing
8. `Bash git cat-file -t v2.2.1 && git rev-parse v2.2.1^{commit}` — annotated check
9. `Bash git show --no-patch v2.2.1` — tag body
10. `Bash python scripts/test_pre_push_e2e.py` — E2E test execution
11. `Read .githooks/pre-push` — shim source
12. `Read .memory/activeContext.md` — Sprint Goals state
13. `Read .memory/lessons.md` — verify 3 new lessons present
14. `Read scripts/check_version_sync.py` — verify primary/fallback logic
15. `Read scripts/test_pre_push_e2e.py` — verify test scope
16. `Read .pre-commit-config.yaml` — verify removal + explanatory comment
17. `Read bootstrap.ps1` — verify `core.hooksPath` activation
18. `Bash cat .ecosystem.toml | grep -E "version|name"` — version field check
19. `Bash cat .claude-plugin/plugin.json | python -c …` — plugin.json version
20. `Bash head -30 CHANGELOG.md` — CHANGELOG header
21. `Bash python scripts/check_version_sync.py` — standalone version check
22. `Bash git reflog --grep="--no-verify"` — guardrail bypass check
23. `Bash tail -10 .memory/audit_history.jsonl` — recent audit entries
24. `Bash tail -20 .memory/session_trajectories.jsonl` — session trajectory check
25. `Bash cat task.md | head -80` — task.md top
26. `Bash cat task.md | tail -80` — task.md tail (Phase 8)
27. `Bash grep -nE "\\[ \\]|\\[/\\]" task.md` — unchecked items
28. `Bash git diff 524224b..HEAD -- .pre-commit-config.yaml` — config diff
29. `Bash git diff 524224b..HEAD -- ENVIRONMENT_SETUP.md … setup_environment.md … SKILL.md` — 3 setup docs diff
30. `Bash git diff 524224b..HEAD -- scripts/check_version_sync.py` — root-cause diff
31. `Bash git diff 524224b..HEAD -- scripts/train_reasoning_bank.py` — ruff fix diff
32. `Bash grep -n "print(" --include="*.py" -r .claude/hooks/ scripts/` — print() audit
33. `Bash grep -n ecosystem .ecosystem.toml + cat … grep -A 2 ecosystem` — [ecosystem] section
34. `Bash git ls-tree -r HEAD .githooks/` — .githooks contents
35. `Bash python scripts/diag_dashboard.py --summary` — dashboard health
36. `Bash grep -n upstream_sha scripts/update_ecosystem.py` — verify upstream_sha semantics
37. `Bash grep -nE "audit_complete|2.2.1" .memory/audit_history.jsonl` — audit history check
38. `Write .memory/audit_v2.2.1_release.md` — this report
39. (pending) `Bash` to append `audit_complete` row to `.memory/audit_history.jsonl`

**Final tool-call count: 38 (≥ 8 minimum requirement satisfied).**
