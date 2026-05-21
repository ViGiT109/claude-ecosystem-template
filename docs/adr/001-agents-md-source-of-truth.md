# ADR-001: AGENTS.md is the source-of-truth for AI agent rules

**Date:** 2026-05-21
**Status:** Accepted
**Deciders:** Template maintainers (v2.0.0 production-readiness audit)

---

## Context

Until v1.x, `CLAUDE.md` at the project root was the canonical place to document
rules for AI coding agents in this project. Claude Code reads it automatically,
which made it the obvious choice when the template was Claude-only.

Two pressures pushed us off that position:

1. **Cross-tool portability.** A small but real ecosystem now reads
   [AGENTS.md](https://github.com/openai/codex) instead: Codex CLI, Cursor,
   Windsurf, Aider, and others. Projects increasingly want one file every agent
   can pick up, not a per-tool zoo.
2. **Drift risk.** When the same rules live in multiple places (`CLAUDE.md`,
   `.cursor/rules`, `AGENTS.md`), they fall out of sync within weeks. The
   audit at the start of v2.0.0 found exactly this pattern in adjacent
   projects.

We needed a single canonical file plus a deterministic way to feed Claude Code
the content it expects under the `CLAUDE.md` name.

## Decision

We will treat **`AGENTS.md` as the source-of-truth** for AI agent rules in
this template, and auto-generate **`CLAUDE.md` from it** at commit time via a
pre-commit hook.

Concretely:

- `AGENTS.md` is hand-edited; `CLAUDE.md` is regenerated.
- `scripts/sync_agents_md.py` copies `AGENTS.md` → `CLAUDE.md` (verbatim, with
  a generated-by header).
- A pre-commit hook (`agents-md-sync`) runs `sync_agents_md.py --check` and
  fails the commit if the two files disagree, forcing the agent to regenerate.
- The script also exposes a `--write` mode used inside the hook to fix drift
  in one command.

## Consequences

### Positive

- One canonical document. Multiple agent tools read it natively, no drift.
- The pre-commit guardrail makes it impossible to ship a stale `CLAUDE.md`.
- Migrating to a new agent tool in the future is a no-op: the tool either
  reads `AGENTS.md` directly, or we add a one-line generator alongside the
  existing one for `CLAUDE.md`.

### Negative / Trade-offs

- New contributors who instinctively edit `CLAUDE.md` will hit a pre-commit
  failure. The hook message points them at `AGENTS.md`, but it adds one
  initial step to the learning curve.
- Two files in the tree look like they're hand-maintained; we mitigate this
  with a `<!-- Auto-generated; edit AGENTS.md -->` header at the top of
  `CLAUDE.md`.

### Neutral

- The content footprint is the same — we did not split rules into per-agent
  flavors. If we ever need to, the generator is the natural extension point.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Keep `CLAUDE.md` as canonical; copy to `AGENTS.md` | Locks us into the Claude-only tool name; flips the polarity once another agent becomes important |
| Symlink `CLAUDE.md` → `AGENTS.md` | Doesn't work on Windows for non-admin users; breaks under some Windows-on-NTFS git configs |
| Two independent files, no enforcement | We tried this in adjacent projects — drift within 4 weeks every time |
| Single file under a third name (e.g. `AGENT_RULES.md`) | Neither Claude Code nor the AGENTS.md ecosystem picks it up; we'd need generators for both, doubling maintenance |

## References

- Spec: [`docs/specs/2026-05-21-production-readiness.md`](../specs/2026-05-21-production-readiness.md) §Phase 1
- Generator: [`scripts/sync_agents_md.py`](../../scripts/sync_agents_md.py)
- AGENTS.md standard: https://github.com/openai/codex
- Pre-commit hook config: `.pre-commit-config.yaml` (`agents-md-sync` hook)
