---
description: Deep behavioural audit of the AI ecosystem for a session. Run at user request (end of session or in a dedicated dialog).
---

# Ecosystem Audit

> **Core:** This is NOT a file-existence check. This is a **behavioural review** —
> did the ecosystem actually work correctly, did all mechanisms fire,
> were any rules violated, should any lessons be recorded?

---

## Launch modes

### Mode 1: Self-Audit (at the end of the current session)
- Standard mode. All phases A-E operate on the "current session".
- Minimal context: all actions are already in the agent's working memory.
- ⚠️ Limitation: context budget may be exhausted; self-reporting bias.

### Mode 2: Cross-Session Audit (in a NEW dialog — RECOMMENDED)
- Run in a NEW dialog to review 1-5 past sessions.
- Phase A adapts:
  - A1: `git log --since="2 days ago"` instead of "last 1-2 hours"
  - A5: read local `task.md` (if it exists) + `git log -p task.md` to see checklist evolution
- ✅ Advantages: fresh context budget, batch review, less bias.

### Mode 3: Infrastructure-only (script)
```powershell
python scripts/health_check.py
```
Quick structure check. Does NOT replace the behavioural audit.

---

> **CRITICAL RULE FOR THE AGENT:** This audit MUST NOT be done "by feel" or as a
> superficial table generated in 30 seconds. Every step requires **gathering evidence**
> via tools (git, file reads, Grep). Every verdict must cite **a concrete reference**
> to what actually happened (or didn't happen) in this session. If you cannot prove
> a verdict — mark it ❓ (unknown), not ✅.

> **HARD CONSTRAINTS:**
> 1. The audit **MUST** include at least **8 tool-calls** for evidence gathering. Fewer = audit rejected.
> 2. **MANDATORY**: use `sequential-thinking` (minimum 5 steps) in Phase C for deep analysis.
> 3. After filling the Phase B tables — **run "Devil's Advocate"** (Phase B.5): pick 3 ✅ verdicts and try to disprove them.
> 4. Record an **Audit Trail** — list ALL tool-calls used for evidence in the report.

---

## Phase A: Gather Evidence

**Before any conclusions — collect facts. Every point is mandatory.**

### A0. Infrastructure pre-check (optional)
```powershell
python scripts/health_check.py
```
→ If the script exists — save the output, use as evidence in Phase B.
→ If missing — skip; replace with behavioural checks.

### A1. Read git log
```
Run `git log --oneline -10` (Self-Audit) or `git log --since="2 days ago" --oneline` (Cross-Session).
```
→ Record: number of commits, Conventional Commits compliance, was there a push.

### A2. Read git diff (what changed this session)
```
Run `git diff HEAD~5..HEAD` or `git diff --stat origin/master...HEAD`.
```
→ Record: which files changed, which modules were touched.

### A3. Read current activeContext.md
```
Read .memory/activeContext.md — is the content up to date?
Does it reflect what was actually done this session?
```

### A4. Read lessons.md
```
Read .memory/lessons.md — were new entries added this session?
Were there errors/rollbacks that SHOULD have been recorded but weren't?
```

### A5. Check task.md (if it existed)
```
If a task.md was created this session — read it.
Also run `git log -p task.md` to see checklist evolution.
Were all items closed? Were they closed as work progressed, or all at the end?
```

### A6. Verify lessons.md updates
```
Read .memory/lessons.md — were new lessons added this session?
Compare `git log --oneline .memory/lessons.md` — if no commits but errors occurred, that's a violation.
```

---

## Phase B: Evaluate session protocol

**For each item give a verdict: ✅ (met), ❌ (violated), ⚠️ (partial), ❓ (unable to verify). Always provide EVIDENCE.**

### B1. Session start
| Check | Verdict | Evidence |
|---|---|---|
| Were `.memory/lessons.md` read at start? | | |
| Was `.memory/activeContext.md` read at start? | | |
| Was git log / git status checked? | | |
| Was a context summary provided to the user? | | |

### B2. Task planning
| Check | Verdict | Evidence |
|---|---|---|
| For tasks > 1 step: was task.md / implementation plan created? | | |
| For tasks > 2 hours / > 3 files: was a spec created? | | |
| Was the plan shown to the user before starting work? | | |

### B3. Task execution
| Check | Verdict | Evidence |
|---|---|---|
| Was the logger used instead of print() in backend modules? | | |
| Were type hints present in new/modified functions? | | |
| Were large files read with tail/head (not in full)? | | |
| Were tasks marked in task.md **as they were completed** (not all at the end)? | | |
| Was code quality maintained (no dead code, small functions, boundary validation)? | | |
| Was API signature verified before calling internal functions? | | |

### B4. Session close
| Check | Verdict | Evidence |
|---|---|---|
| Was activeContext.md updated with current state? | | |
| Were errors/rollbacks recorded in lessons.md (if any)? | | |
| Commit — Conventional Commits format? | | |
| Was `python scripts/finalize_session.py` called (or equivalent)? | | |
| Was there a git push? | | |

---

## Phase B.5: Devil's Advocate (mandatory)

**After filling Phase B tables — MUST do:**

1. Pick **3 any ✅** from tables B1-B4
2. For each — try to find evidence AGAINST ("what if this isn't true?")
3. If you couldn't disprove — explain why you're confident
4. If you found counter-evidence — revise verdict to ⚠️ or ❌

Goal: prevent self-reporting bias.

---

## Phase C: Identify new lessons

**Most important phase. MUST use `sequential-thinking` (minimum 5 steps).**

For each sequential-thinking step:
1. List ALL errors/rollbacks/inefficiencies from the session
2. For each — is it documented in lessons.md?
3. Cross-reference with existing anti-patterns — is this a repeating pattern?
4. Formulate concrete lessons / rule changes
5. Summarise — what specifically needs to be recorded/updated

### C1. Anti-patterns
Were any anti-patterns from lessons.md violated?
If yes — this indicates the Self-Improvement Loop isn't working and needs strengthening.

### C2. New patterns
Were there any errors/rollbacks/inefficiencies this session NOT documented in lessons.md?
If yes — **immediately** apply `/extract_lesson` and record them.

### C3. Rules
Do any rules in `.agents/rules/` need updating or adding?
If the same error has repeated 3+ times (check `.memory/lessons.md` or `audit_history.jsonl`) → promote to a rule.

---

## Phase C.5: Internet Scouting (optional, on request)

**When to run:** If the user asks for a retrospective, evolution, or GAP analysis.

1. Use `WebSearch` (2-3 queries) for fresh best practices:
   - `"Gold Standard AI-assisted project management 2026"`
   - `"Claude Code ecosystem best practices"`
   - `"Agent OS codebase governance rules"`
2. Find 2-3 new concepts not in the current `CLAUDE.md`
3. Cross-reference with current rules → GAP analysis
4. Propose concrete ecosystem updates

---

## Phase D: Final report

**Generate a structured report artifact:**

```markdown
# 🔬 Session Audit Report — [date]

## Overall rating: [🟢/🟡/🔴]

## Phase summary
| Phase | Result | Critical violations |
|---|---|---|
| Session start | X/4 ✅ | ... |
| Planning | X/3 ✅ | ... |
| Execution | X/6 ✅ | ... |
| Close | X/5 ✅ | ... |

## Issues found
1. ...
2. ...

## Fixes applied
1. Added lesson to lessons.md: "..."
2. ...

## Ecosystem improvement recommendations
1. ...
```

---

## Phase E: Apply fixes

If Phase C found new lessons or violations:
1. **Record** the lesson via `/extract_lesson` (right now)
2. **Propose** changes to rules/commands if a systemic issue was found

> **PROHIBITION:** Do not close the audit with "everything is generally fine". If every Phase B item has ✅ —
> show concrete evidence for each. A superficial audit is a failed audit.
>
> **PRE-SUBMISSION CHECKLIST:**
> - [ ] ≥ 8 tool-calls with evidence gathered
> - [ ] sequential-thinking in Phase C (≥ 5 steps)
> - [ ] Devil's Advocate in Phase B.5 (3 verdicts challenged)
> - [ ] Audit Trail listed in report
> - [ ] Each ❌ has a concrete reference
> - [ ] New lessons recorded in lessons.md (if any)

---

> **Triggers:** "audit ecosystem", "review my last session", "how did the ecosystem perform",
> "ecosystem audit", "session review", "behavioural audit"
