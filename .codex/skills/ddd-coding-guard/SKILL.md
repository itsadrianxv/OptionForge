---
name: ddd-coding-guard
description: Use when implementing or changing OptionsForge-family strategy behavior, scaffold templates, or `src/strategy` code where bounded contexts, dependency direction, or domain language could drift away from the repository's DDD rules.
---

# DDD Coding Guard

## Overview

Use this skill before writing code that could change the OptionsForge family architecture. The job is to classify the touched bounded context, block hard DDD violations, and force a concrete preflight plus a final self-review.

Read these files first:
- `docs/architecture/ddd-constitution.md`
- `docs/architecture/context-map.md`
- `docs/architecture/refactor-catalog.md` when the proposed change smells like cleanup rather than straight implementation

## When To Block

Stop implementation and redesign if any of these are true:
- domain code imports infrastructure modules, framework types, or vendor payloads
- business rules are being added to gateway, persistence, web, bootstrap, or runtime-entry layers
- cross-context handoffs rely on mutable entities or raw vendor payloads instead of ports, DTOs, or value objects
- the proposed change introduces a new facade or coordinator layer that flattens boundaries

Do not "just implement it for now". Redlines are blockers.

## Workflow

1. Identify every touched path and map it to a bounded context.
2. Read the minimum relevant source files plus the constitution/context map.
3. Emit a `DDD Preflight Card` before implementation.
4. If a redline is hit, stop and replace the approach with the smallest compliant alternative.
5. If no redline is hit, implement while keeping grey-line debt visible.
6. Before completion, emit a `DDD Self-Review`.

## DDD Preflight Card

Use this structure:

```text
DDD Preflight Card
- Change: ...
- Bounded context: ...
- Target layer: ...
- Domain concepts: ...
- Allowed dependencies: ...
- Redline checks: pass/fail with reason
- Required tests: ...
```

## Grey-Line Warnings

Warn and improve when you see:
- bloated `StrategyEntry` or workflow objects
- stateful domain services that should use explicit policy/context objects
- anemic entities
- missing value objects
- ubiquitous-language drift between mother and child repos

Do not silently accept these. Either improve them in-scope or list them in the final self-review.

## DDD Self-Review

Use this structure before claiming completion:

```text
DDD Self-Review
- Context respected: yes/no
- Dependency direction respected: yes/no
- Business rules kept out of adapters/bootstrap/web: yes/no
- Explicit port/DTO/VO boundaries used: yes/no
- No new facade/coordinator flattening: yes/no
- Remaining grey-line debt: ...
```

## Common Mistakes

- treating `src/strategy/runtime/**` as a safe place for domain rules because it already has assembled dependencies
- moving domain parsing into infrastructure helpers and then calling the helpers back from domain code
- keeping new strategy policy in mutable service instance fields because it feels convenient
- reusing vendor payloads as domain contracts to avoid introducing value objects
