# API Reference — Claude Code Hooks

> Frozen reference: Claude Code hooks and settings API as of May 2026.
> Update only when Claude Code releases breaking changes to the hooks API.
> Source: https://docs.anthropic.com/en/claude-code/hooks

## Hooks API

### Event types

| Event | When it fires | Typical use |
|---|---|---|
| `SessionStart` | At the beginning of every conversation | Inject context, load memory |
| `PreToolUse` | Before any tool call | Block forbidden patterns, validate |
| `PostToolUse` | After any tool call | Log, notify |
| `Stop` | When Claude finishes a turn | Audit, persist state |
| `PreCompact` | Before context compaction | Archive important context |

### Hook command format (`.claude/settings.json`)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/_run.py .claude/hooks/session_start.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/_run.py .claude/hooks/block_no_verify.py",
            "timeout": 5
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/_run.py .claude/hooks/stop_audit.py",
            "timeout": 15,
            "async": true
          }
        ]
      }
    ]
  }
}
```

### Hook exit codes

| Exit code | Meaning |
|---|---|
| `0` | Allow (pass-through) |
| `2` | **Block** the action (PreToolUse only — tool call is cancelled) |
| Other non-zero | Error (logged, action still proceeds) |

### Hook stdin payload (PreToolUse)

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "git commit --no-verify ..."
  }
}
```

### Matcher syntax

- `"matcher": "Bash"` — matches by tool name
- `"matcher": "Bash(git commit:*)"` — matches tool + argument pattern (glob)
- No matcher → fires for all tool calls

## Slash commands

Location: `.claude/commands/*.md`
Invocation: `/<filename-without-extension>` in Claude Code

Frontmatter:
```yaml
---
description: One-line description shown in the command picker
---
```

## Subagents

Location: `.claude/agents/*.md`
Invocation: Automatic (by description match) or user-requested

Frontmatter:
```yaml
---
name: agent-name
description: When to use this agent (used for routing)
tools: Read, Grep, Glob, Bash   # optional subset
model: inherit                   # or claude-sonnet-4-6 etc.
memory: project                  # optional
---
```

## Skills

Location: `.claude/skills/<name>/SKILL.md`
Invocation: Via Skill tool when description matches user intent

Frontmatter:
```yaml
---
name: skill-name
description: When to activate (triggers listed here)
tools: optional tool subset
---
```

## Settings schema

Full schema: https://json.schemastore.org/claude-code-settings.json

Key fields:
- `autocompleteHistoryLimit` — history entries for autocomplete
- `permissions.allow` — pre-approved tool patterns (no confirmation prompt)
- `permissions.deny` — always-blocked patterns
- `hooks` — lifecycle hooks
- `env` — environment variable overrides
