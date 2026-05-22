---
description: Print a 4-line traffic-light summary of ecosystem health (audit, lessons, hooks, version sync).
model: haiku
---

# Diagnostic status

Run `python scripts/diag_dashboard.py --summary` and surface the result.

```bash
python scripts/diag_dashboard.py --summary
```

If anything is 🟡 or 🔴 — say so in plain language and suggest the
next action:

- audit 🔴 → "запусти `ecosystem-auditor` сабагент"
- audit 🟡 → "аудит стареет, проверить когда удобно"
- lessons 🟡 → "запусти `/consolidate_lessons`"
- hooks 🟡/🔴 → "`python scripts/check_hook_health.py`"
- version 🔴 → "rare; check `python scripts/check_version_sync.py` для деталей"

For the full breakdown (audits trend, retrieval mix, trajectories) —
run `python scripts/diag_dashboard.py` without the flag.
