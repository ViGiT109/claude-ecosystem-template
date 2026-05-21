# Model Policy

> Single source of truth for **which model to use for which task** in this ecosystem.
> Loaded on demand by slash-commands, subagents, and hooks that emit a `💡 MODEL` block.
> Companion files: [common.md](common.md), [git.md](git.md), [code-quality.md](code-quality.md).

## TL;DR

| Situation | Model | How it gets selected |
|---|---|---|
| New session start | **Opus 4.7** | Default per user preference (reliability first) |
| Slash-command / subagent | **frontmatter `model:`** | Declared explicitly — no inference at runtime |
| Mechanical impl on approved spec | **Sonnet 4.6** | Frontmatter or silent subagent delegation |
| Task expected to exceed 150K context | **Opus 4.7** | Context window — Sonnet/Haiku will compact and lose state |
| Session at >70% of model's context window | (handoff) | Emit `🔄 SESSION` block — recommend `/handoff` + new session |

**Iconography:** `💡 MODEL` = model recommendation. `🧭 PLAN` = enter Plan Mode. `🔄 SESSION` = handoff recommended.

## Philosophy

This ecosystem **inverts** the common 2026 pattern (Sonnet-default, escalate to Opus).
Default is **Opus 4.7**; Sonnet 4.6 is an explicit opt-in on the safe-path whitelist below.

**Why:** the work here is mostly architecture, audits, lessons-extraction, and security-sensitive infra
edits. The cost of a model under-thinking these tasks is higher than the cost of an Opus token. When a
task is genuinely mechanical and bounded, we hand it to Sonnet — usually as a silent subagent
delegation from an Opus main thread, not by switching the main session.

Model selection is **declarative**, not inferred:

1. Slash-command / subagent frontmatter (`model: opus | sonnet | inherit`) wins.
2. If absent, the explicit `Agent(model=...)` call when delegating wins.
3. Otherwise the session's current model is inherited.

There is no "Claude picks on the fly" path — every model choice lives in source.

## Always Opus 4.7 (allowlist)

Use Opus whenever the work matches any of:

- **Planning / spec writing.** Plan Mode, `/create_spec`, ADR drafting, multi-phase decomposition.
- **Audits.** `/audit_ecosystem`, security review, code review of non-trivial diffs.
- **Refactor across >3 files** or any change with cross-cutting blast radius.
- **Hard debug.** Unreproducible bug, race condition, "works in staging not prod", flake hunting.
- **Security / migrations / finance.** Auth, secrets handling, DB migrations, payment flows,
  any irreversible action.

These categories also imply **Plan Mode** as a likely next step — see [§Planning hint](#planning-hint).

## Sonnet 4.6 safe-path (whitelist)

Sonnet is appropriate **only** when all of these hold:

- The task is implementation of an **already-approved spec** that has been through ≥1 review.
- Edits are bounded (≤3 files, ≤200 lines net).
- No new architectural decisions are required mid-task.
- Outcome is verifiable by tests, types, or lint — not by judgement.

Concrete safe-path tasks:

- Trivial edits: typos, formatting, variable renames.
- Documentation written **over existing code** (no new design).
- Tests written against an approved contract.
- Dead-code cleanup with grep confirming no references.
- Mechanical commit pipelines (lint → test → commit → push) — see `/commit_and_release`.

If unsure whether a task is "safe-path" — it isn't. Default back to Opus.

## Context Window Awareness

| Model | Context window | Practical session budget (70%) |
|---|---|---|
| Opus 4.7 | **1M** tokens | ~700K — fits multi-phase work in one session |
| Sonnet 4.6 | 200K tokens | ~140K — long sessions compact aggressively |
| Haiku 4.5 | 200K tokens | ~140K |

**Decision rule (overrides everything else):** if the planned work is expected to exceed
**150K context** (long audits, multi-file refactors, deep research with many tool results) →
use **Opus 4.7** regardless of task character. Sonnet/Haiku will compact mid-session and silently
lose precision on the early reasoning.

**Session handoff trigger:** when the current session reaches **>70%** of the active model's window,
emit a `🔄 SESSION` block recommending `/handoff` + a new session. Switching models mid-session
**does not** reclaim context — only a new session does.

## Model Switch Checkpoint — minimally-blocking

Do **not** stop the user with a `💡 MODEL` block by default. Block only when **both** hold:

1. The **current** model is unfit for the immediately upcoming task (e.g. Sonnet about to make an
   architectural decision).
2. Delegating to a subagent with the right model is **not** an option (the work must continue
   interactively in the main thread).

If a subagent can handle it — delegate silently and continue. If the current model can finish the
task without quality loss — say nothing. Only when the user must hit `/model` themselves do we
emit the blocking `💡 MODEL` block.

**Default start:** every new session begins on **Opus 4.7**. Sonnet is opt-in via explicit
`/model claude-sonnet-4-6` from the user. Don't downgrade the main thread automatically.

## Hybrid execution via subagents — silent delegation

Subagent invocations (`Agent(...)`) accept `model: "opus" | "sonnet" | "haiku"`. Use this aggressively
and **silently** — the user sees only the final result, not the delegation.

Rules:

- Always pass an explicit `model:` to `Agent` when the task can benefit from a different model than
  the main thread. Never default to `inherit` if you have an opinion.
- Do not announce delegations. Don't print "delegating to Sonnet…" — it's an internal optimization.
- Do not block the main thread waiting for confirmation. Run, await, integrate the result.

Recommended patterns:

| Main thread | Delegation | Why |
|---|---|---|
| Opus 4.7 (architect / auditor) | Sonnet → mechanical edits per approved plan | Cheap, fast, bounded |
| Opus 4.7 | Sonnet → web research / link crawl (`researcher` subagent in Phase 6) | I/O-bound, summarization |
| Opus 4.7 | Sonnet → file discovery / grep sweep (`Explore`) | Pure search, no judgement |
| Opus 4.7 | Opus subagent in worktree → heavy refactor | Isolate context, parallelize |

## Block formats

These are the **exact** templates the agent emits. They are detected by humans and possibly by future
hooks — keep them stable.

```
💡 MODEL RECOMMENDATION
   Suggested: <Opus 4.7 | Sonnet 4.6 | Haiku 4.5>
   Reason: <one-liner referencing this policy>
   Context: <pct>% of <window>
   Switch via: /model <opus|sonnet|haiku>
```

```
🧭 PLAN PHASE RECOMMENDED
   Trigger: «<matched keyword or heuristic>»
   Suggested action: Enter Plan Mode (Shift+Tab)
```

```
🔄 SESSION HANDOFF RECOMMENDED
   Context: <pct>% of <window> — switching models won't reclaim space
   Suggested action: /handoff → new session → /new_session
```

These blocks are **non-blocking** by default. Only the `💡 MODEL` block blocks the response when
the Model Switch Checkpoint conditions above are met.

## Cross-reference — where this policy is applied

| Surface | How the rule lands |
|---|---|
| Slash-commands | Frontmatter `model:` in `.claude/commands/*.md` (declared per command) |
| Subagents | Frontmatter `model:` in `.claude/agents/*.md` |
| `/model_check` | Reads this file; emits the `💡 MODEL` block on demand |
| `/handoff` | Emits the `🔄 SESSION` block; updates `.memory/activeContext.md` |
| `planning_hint.py` hook | Emits the `🧭 PLAN + 💡 MODEL` combined block on UserPromptSubmit triggers (see AGENTS.md §Planning-phase signaling) |
| `session_start.py` hook | Emits the `🔄 SESSION` block when transcript size exceeds 70% of the active model's window (see AGENTS.md §Session handoff signaling) |

## Env killswitches

| Variable | Effect |
|---|---|
| `CLAUDE_DISABLE_PLANNING_HINT=1` | Silences the `planning_hint.py` hook — `🧭 PLAN` blocks not auto-emitted by the hook (agent-side rule in AGENTS.md still applies) |

The `💡 MODEL` and `🔄 SESSION` blocks have no killswitch — they are emitted only when the rules
above are actually met, so silencing them would hide a real signal.
