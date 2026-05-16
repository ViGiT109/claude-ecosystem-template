# Template Guide — claude-ecosystem-template

> **This file is for the template repo itself.**
> It is removed by `bootstrap.ps1` when you start a new project.

## What this template is

A clean, reusable starting point for any software project that uses Claude Code as its AI assistant.
It bundles a mature AI governance ecosystem ported from a production project (v6 after 18 months).

### What you get

- **Progressive Disclosure** — context loaded in 3 tiers (ALWAYS/AUTO/ON-DEMAND)
- **Memory Bank** — 7 persistent markdown files (activeContext, lessons, progress, brief, patterns, tech, CC state)
- **ReasoningBank** — ChromaDB-backed semantic retrieval of past lessons
- **Deterministic Hooks** — session_start, block_no_verify, stop_audit (Python, no Bash dependency)
- **Self-Improvement Loop** — error → lesson → rule → guardrail
- **7 Slash Commands** — new_session, audit_ecosystem, extract_lesson, create_spec, agentic_tdd, commit_and_release, setup_environment
- **Subagent** — ecosystem-auditor (cross-session behavioral audit in isolated context)
- **2 Skills** — clean-workspace, deploy-fresh
- **Modular Rules** — common, git, code-quality + coding-conventions, changelog-rules
- **CI Workflows** — stack-auto-detecting lint + test, ecosystem audit freshness check
- **Bootstrap script** — one-run personalization

---

## How to start a new project from this template

### Option A: Copy (simplest)

```powershell
# Copy template to new project folder
Copy-Item -Recurse C:\claude-ecosystem-template C:\my-new-project

# Enter and bootstrap
cd C:\my-new-project
.\bootstrap.ps1
```

### Option B: GitHub template (if pushed to GitHub)

1. Click "Use this template" on the GitHub repo.
2. Clone the new repo.
3. Run `.\bootstrap.ps1`.

---

## What `bootstrap.ps1` does

1. Prompts for: project name, vision (1 sentence), language (Python/Node/Other), entry point, git scopes.
2. Writes answers to `.ecosystem.toml`.
3. Substitutes `${PROJECT_NAME}`, `${PROJECT_VISION}`, `${STAKEHOLDERS}`, `${PROJECT_SCOPES}` across template files.
4. Removes `TEMPLATE_README.md` and `bootstrap.ps1` itself (job done).
5. Copies `.env.example` → `.env`.
6. Optional: scaffolds `pyproject.toml` (Python) or `package.json` (Node).
7. Runs `git init` if `.git` is absent; creates first commit.
8. Optionally runs `.\scripts\setup_mcp.ps1`.

Bootstrap is idempotent: re-running detects already-substituted markers and asks before overwriting.

---

## Directory layout explained

```
.claude/
├── commands/        # Slash commands (/.md → /command-name in Claude Code)
├── agents/          # Subagents (routed by description match)
├── hooks/           # Lifecycle hooks (Python)
│   ├── _run.py      # Hook launcher — finds Python without requiring Bash
│   ├── session_start.py
│   ├── block_no_verify.py
│   └── stop_audit.py
├── skills/          # Skill packs (SKILL.md frontmatter)
│   ├── clean-workspace/
│   └── deploy-fresh/
└── settings.json    # Hook wiring + baseline permissions

.agents/
├── rules/           # Modular AI rules (loaded on demand)
│   ├── common.md
│   ├── git.md
│   └── code-quality.md
└── context/         # Reference documents (loaded on demand)
    ├── coding-conventions.md
    └── changelog-rules.md

.memory/             # Project memory bank (in git, shared with all contributors)
├── activeContext.md
├── lessons.md
├── progress.md
├── projectbrief.md
├── systemPatterns.md
├── techContext.md
├── claude_code_state.md
├── audit_history.jsonl
├── retrieval_logs.jsonl
├── session_trajectories.jsonl
├── chroma_db/       # ChromaDB vector store (gitignored, populates on first use)
└── models/          # Embedding model cache (gitignored, lazy bootstrap)

scripts/
├── finalize_session.py     # Session closure ritual
├── reasoning_bank.py       # ChromaDB ingestion + retrieval CLI
├── prune_memory.py         # Deduplicate lessons via cosine similarity
├── health_check.py         # Project health (reads .ecosystem.toml)
├── check_task_guardrail.py # Pre-commit: blocks on unchecked tasks
├── monitor_context.py      # Token budget estimation
├── setup_mcp.ps1           # MCP server install
└── clean_workspace.ps1     # 3-level workspace cleanup
```

---

## Keeping the template up to date

The AI infrastructure (hooks, commands, agents) evolves independently of project state.
To update a project's infrastructure from a newer template version:

1. Compare the `C:\claude-ecosystem-template\.claude\` directory with your project's `.claude\`.
2. Copy updated files manually (or via a diff tool).
3. Test hooks fire correctly (`/new_session`, commit attempt).

A future improvement: publish the `.claude/` layer as an installable Claude Code plugin
so projects can `npx update-ecosystem` instead.

---

## Customizing for your project

After `bootstrap.ps1` runs:

1. **Fill `.memory/projectbrief.md`** — vision, users, core features.
2. **Fill `.memory/techContext.md`** — stack, dependencies, MCP servers.
3. **Update `.agents/rules/git.md`** — set project-specific commit scopes.
4. **Update `.pre-commit-config.yaml`** — remove hooks that don't apply (e.g. ruff for Node projects).
5. **Add your first ADR** (`docs/adr/001-...`) if you've made an architectural choice.
6. **Run `/new_session`** — the ecosystem should load cleanly.

---

## Maturity history

This template is derived from Bingo7 v6 (Python ML/trading project, ~85/100 ecosystem maturity
after 7 major iterations over 18 months). Domain-specific code was stripped; generic patterns
and improvements were applied immediately.
