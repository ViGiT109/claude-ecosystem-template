---
description: Run the Agentic TDD cycle (Test-Driven Development) for new features or bug fixes
---

# Agentic TDD Workflow

Strict Red-Green-Refactor sequence for developing new features or fixing bugs.
Use this whenever the change touches logic that can be expressed as a test.

## Phase 1: 🔴 RED (Write a failing test)

> **Forbidden:** writing or modifying functional code at this stage. Focus ONLY on the test.

1. Create or update the relevant test file in `tests/` (e.g. `tests/test_new_feature.py`).
2. Describe the desired behavior of the function, class, or module as a test.
3. Add any mocks or fixtures the component needs for isolation.
4. Run the test:
```bash
pytest tests/test_new_feature.py -v
```
5. Confirm the test **FAILS**. If it passes immediately — either it tests the wrong thing, or the functionality already exists.

---

## Phase 2: 🟢 GREEN (Minimum working code)

1. Implement the minimal functional code required to make the test pass.
2. Write **only** what is needed — no speculative design, no future-proofing.
3. Re-run the test repeatedly until it passes:
```bash
pytest tests/test_new_feature.py -v
```

---

## Phase 3: 🔵 REFACTOR (Improve the code)

1. With the test green, clean up the code to meet project standards (read `.agents/context/coding-conventions.md` if needed).
2. Eliminate duplication. Add type hints. Ensure logger is used instead of print().
3. Run the full health check to confirm nothing regressed:
```powershell
python scripts/health_check.py
```

> **If `health_check.py` or any other tests fail after refactoring — step back and fix them.**
> The task is complete only when BOTH the new tests AND the health check pass.
