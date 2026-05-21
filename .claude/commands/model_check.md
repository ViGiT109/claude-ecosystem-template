---
description: Recommend a model (Opus 4.7 / Sonnet 4.6 / Haiku 4.5) for the current task based on context window usage and task character
model: inherit
---

# Model Check

Source of truth: `.agents/rules/model-policy.md`. Read it before deciding.

## Steps

### 1. Read last user prompt and recent tool activity

Scan the last 3-5 turns: what is the user asking for, which tools were used,
how many files were read/written, how large were the results.

### 2. Estimate context window usage

Count approximate tokens consumed (tool results + conversation):
- Small (<50K): context is clean
- Medium (50-140K): watch for Sonnet/Haiku pressure
- Large (>140K): Sonnet/Haiku will compact; Opus still comfortable
- Critical (>700K): even Opus approaches limit — consider `/handoff`

Express as a percentage of the active model's window
(Opus 4.7: 1M, Sonnet 4.6: 200K, Haiku 4.5: 200K).

### 3. Decide the right model per `model-policy.md`

Apply in priority order:

1. **Always-Opus allowlist** — planning, spec writing, audits, security, hard debug,
   cross-cutting refactors (>3 files), irreversible actions → **Opus 4.7**
2. **>150K context override** — expected work will exceed 150K tokens → **Opus 4.7**
   regardless of task character
3. **Sonnet safe-path whitelist** — approved spec, ≤3 files, ≤200 lines, no new
   architectural decisions, verifiable by tests/types/lint → **Sonnet 4.6**
4. Otherwise → **Opus 4.7** (default)

### 4. Emit the recommendation block

```
💡 MODEL RECOMMENDATION
   Suggested: <Opus 4.7 | Sonnet 4.6 | Haiku 4.5>
   Reason: <one-liner referencing model-policy.md>
   Context: <pct>% of <window>
   Switch via: /model <opus|sonnet|haiku>
```

### 5. If ctx >70% — also emit the handoff block

```
🔄 SESSION HANDOFF RECOMMENDED
   Context: <pct>% of <window> — switching models won't reclaim space
   Suggested action: /handoff → new session → /new_session
```
