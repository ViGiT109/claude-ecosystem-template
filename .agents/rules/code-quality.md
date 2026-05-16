# Code Quality Rules

> Universal code quality principles. Not specific to any framework or ML domain.

## Function size

- Functions should do one thing. If a function needs a multi-sentence description — split it.
- Target: ≤ 40 lines per function (excluding docstring and type hints).
- If you find yourself adding `# --- section ---` comments inside a function — that is a sign to extract.

## No dead code

- Delete unused imports, variables, parameters, and functions.
- Do not comment out code "for later" — use git history instead.
- Exception: `# noqa: F401` with justification for re-exported names.

## Validate at system boundaries only

- Validate user input, external API responses, and file reads at entry points.
- Trust internal functions to receive valid arguments — do not double-validate.
- Do not add defensive null-checks for conditions that cannot happen by construction.

## No speculative abstractions

- Do not create helper functions, base classes, or utility modules for hypothetical future reuse.
- Three similar implementations is fine. Abstract only when the fourth appears.
- A direct implementation is better than an elegant abstraction nobody asked for.

## Error handling

- Handle errors at the right level: where you have enough context to recover or report meaningfully.
- Do not swallow exceptions silently (`except: pass` is almost always wrong).
- Log the exception with context before re-raising or converting to a domain error.

## Comments

- Default: no comments. Well-named identifiers explain the what.
- Write a comment only when the **why** is non-obvious: a hidden constraint, a workaround,
  a subtle invariant, or behavior that would surprise a reader.
- Do not comment what the code does — rename the function instead.

## Naming

- Prefer explicit over short: `user_payment_method` over `upm`.
- Boolean names: use `is_`, `has_`, `can_` prefixes (`is_active`, `has_permission`).
- Functions: verb phrase (`calculate_total`, `send_notification`).
- Avoid abbreviations except universally understood ones (`id`, `url`, `http`, `db`).

## Testing

- Unit tests go in `tests/` and match the module they test (`tests/test_payments.py`).
- Test one behavior per test function.
- Use real data (or minimal fixtures) rather than mocks for critical paths.
- Smoke-test new features before closing the task.
