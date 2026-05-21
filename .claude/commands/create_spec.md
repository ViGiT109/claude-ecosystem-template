---
description: Create a specification before implementing a complex task (Spec-Driven Development)
model: opus
---

# Create Specification

This workflow is mandatory for tasks requiring > 2 hours of work or changing architecture.

## When to use

- New module or significant refactoring
- Integration of a new service or API
- Any task touching > 3 files
- Any change that affects interfaces or data models

## Specification template

Create the file `docs/specs/YYYY-MM-DD-name.md`:

```markdown
# Specification: [Name]

## Problem Statement
What exactly needs to be solved? Why is the current state unsatisfactory?

## Scope
### In scope
- Specific changes
### Out of scope
- What will NOT change

## Proposed Solution
### Interface (API / CLI / UI)
How will the user interact?

### Architecture
Which modules are affected? Dependency diagram.

### Data Flow
Data source → how it's processed → destination.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Risks & Mitigations
| Risk | Probability | Mitigation |
|---|---|---|

## Estimated Effort
- Hours: X
- Files: Y
- Complexity: Low/Medium/High
```

## After creation

1. Show the spec to the user for review
2. Get approval
3. Create `task.md` from the Acceptance Criteria
4. Begin implementation

> **Triggers:** "create spec", "write specification", "implementation plan", "spec-driven", "design doc"
