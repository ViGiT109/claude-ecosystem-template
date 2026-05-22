# Template Guide — claude-ecosystem-template

> **This file is for the template repo itself.**
> It is removed by `bootstrap.ps1` when you start a new project.

## What this template is

A clean, reusable starting point for any software project that uses Claude Code (or any
[AGENTS.md](https://github.com/openai/codex)-compatible agent: Codex, Cursor, Windsurf, Aider) as its AI assistant.
It bundles a mature AI governance ecosystem ported from a production project (v6 after 18 months).

### What you get

- **Progressive Disclosure** — context loaded in 3 tiers (ALWAYS/AUTO/ON-DEMAND)
- **Memory Bank** — persistent markdown files in `.memory/` (activeContext, lessons, progress, brief, patterns, tech, API reference)
- **ReasoningBank** — ChromaDB-backed semantic retrieval of past lessons
- **Deterministic Hooks** — `session_start`, `block_no_verify`, `stop_audit`, `planning_hint`, `statusline` (Python, no Bash dependency)
- **Self-Improvement Loop** — error → lesson → rule → guardrail
- **Slash Commands** — `/new_session`, `/audit_ecosystem`, `/extract_lesson`, `/create_spec`, `/agentic_tdd`, `/commit_and_release`, `/setup_environment`, `/model_check`, `/handoff`
- **Subagents** — `ecosystem-auditor`, `code-reviewer`, `researcher` (each runs in isolated context with its own model)
- **Skills** — `clean-workspace`, `deploy-fresh`
- **Modular Rules** — common, git, code-quality, model-policy + coding-conventions, changelog-rules
- **CI Workflows** — stack-auto-detecting lint + test, ecosystem audit freshness check
- **Bootstrap script** — one-run personalization

> **Want the rationale, not just the feature list?** See [`docs/template-design.md`](docs/template-design.md) — explains
> *why* the ecosystem is shaped this way and what was learned over 18 months of iteration.

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
│   ├── ecosystem-auditor.md
│   ├── code-reviewer.md
│   └── researcher.md
├── hooks/           # Lifecycle hooks (Python)
│   ├── _run.py            # Hook launcher — finds Python without requiring Bash
│   ├── session_start.py
│   ├── block_no_verify.py
│   ├── planning_hint.py
│   ├── statusline.py
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
├── api_reference_hooks.md
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
├── setup_mcp.ps1           # MCP server install
└── clean_workspace.ps1     # 3-level workspace cleanup
```

---

## Keeping the template up to date

The AI infrastructure (hooks, commands, agents) evolves independently of project state.
Since v2.1 there is a built-in sync tool — `scripts/update_ecosystem.py`:

```bash
# Dry-run (default): show what would change, write nothing
python scripts/update_ecosystem.py --from <path-or-git-url>

# Apply the plan
python scripts/update_ecosystem.py --from <path-or-git-url> --apply

# Skip a subtree
python scripts/update_ecosystem.py --from <upstream> --apply --exclude '.claude/skills/*'

# Overwrite hand-edited files (SHA-protected by default)
python scripts/update_ecosystem.py --from <upstream> --apply --force
```

The script syncs `.claude/`, `.agents/`, `scripts/` and `AGENTS.md`. It **never** touches
`.memory/`, `.env*`, `task.md`, `.git/`. Hand-edits are detected via a SHA snapshot
stored under `[ecosystem.file_shas]` in `.ecosystem.toml` — modified files are listed as
`blocked` and require `--force` to overwrite. After an `--apply`, the script refreshes the
snapshot and records the upstream commit in `.ecosystem.toml::ecosystem.upstream_sha`.

Manual diffing remains an option if you want full control — the script's dry-run mode
prints a per-file plan first.

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

## Design rationale

The architecture story (why three memory tiers, why hooks-in-Python, why AGENTS.md is canonical,
why default to Opus) lives in [`docs/template-design.md`](docs/template-design.md). That doc survives
`bootstrap.ps1` and stays in downstream projects, so the rationale isn't lost when the template
repo is cloned away.
