---
name: ddd-refactor-coach
description: Use when diagnosing DDD drift in existing OptionsForge-family code, planning boundary repairs, or turning a large architectural hotspot into a sequence of small refactor slices.
---

# DDD Refactor Coach

## Overview

Use this skill when the problem is not "write the next feature" but "this part of the codebase has drifted away from the intended DDD structure". The job is to diagnose the hotspot, classify the violation, and produce the smallest safe migration slices.

Read these files first:
- `docs/architecture/ddd-constitution.md`
- `docs/architecture/context-map.md`
- `docs/architecture/refactor-catalog.md`

## Workflow

1. Identify the hotspot paths and the current owner context.
2. Classify each smell as redline or grey line.
3. Explain why the current code violates the constitution.
4. Define the target shape without proposing a big-bang rewrite.
5. Produce a `hotspot diagnosis`.
6. Produce a `refactor slice plan`.
7. End with a `DDD debt delta`.

## Hotspot Diagnosis

Use this structure:

```text
Hotspot Diagnosis
- Hotspot: ...
- Current context: ...
- Violation class: redline/grey line
- Why it violates the constitution: ...
- Target shape: ...
```

## Refactor Slice Plan

Always prefer the smallest safe slice. Use this structure:

```text
Refactor Slice Plan
- Slice 1: ...
- Safety test: ...
- Slice 2: ...
- Safety test: ...
- Deferred debt: ...
```

If the user asks for a whole-module rewrite, refuse the big-bang version and replace it with slices.

## DDD Debt Delta

End with:

```text
DDD Debt Delta
- Debt removed now: ...
- Debt intentionally retained: ...
- Why retained: ...
- Best next slice: ...
```

## Red Flags

Stop and narrow the plan if you are about to:
- rewrite an entire context in one pass
- rename terms without mapping them to the existing ubiquitous language
- move logic across layers without a regression test for the moved behavior
- introduce a temporary facade/coordinator to "stabilize" the refactor

## Common Mistakes

- proposing the final architecture without showing the first safe slice
- treating every hotspot as a domain problem when some belong in application orchestration
- ignoring existing runtime behavior and verification paths while moving boundaries
- claiming a hotspot is fixed without stating what debt remains
