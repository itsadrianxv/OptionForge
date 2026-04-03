# OptionsForge DDD Constitution

## Purpose

This constitution defines the default DDD guardrails for the OptionsForge family:
- the mother repository (`OptionsForge`)
- generated child repositories built from this scaffold
- sibling strategy repositories that keep the same `src/strategy` layering model

The target posture is strict DDD migration. New work must move the codebase closer to the target shape, not merely preserve the current pragmatic compromise.

## Default Target Shape

The preferred shape is:
- domain logic in `src/strategy/domain/**`
- application orchestration in `src/strategy/application/**`
- adapters and integrations in `src/strategy/infrastructure/**`
- composition and provider assembly in `src/strategy/runtime/**`
- process/bootstrap concerns in `src/main/**`
- outer interfaces in `src/web/**`, `src/interface/**`, `src/backtesting/**`, and similar peripheral modules

## Ubiquitous Language

Use business language from the strategy domain first:
- underlying
- option chain
- target instrument
- position aggregate
- execution state
- risk threshold
- close decision
- selection preference
- portfolio risk

Do not replace domain terms with vague technical placeholders such as `manager`, `helper`, `payload`, `coordinator`, or `processor` unless the object truly is only technical infrastructure.

## Layer Rules

### Domain
- May define aggregates, entities, value objects, domain services, domain events, and domain ports.
- Must not import infrastructure helpers, gateway adapters, web handlers, persistence implementations, framework-specific runtime types, or vendor payloads.
- Must not depend on `vnpy`, `akshare`, database drivers, HTTP clients, or transport-layer schemas.

### Application
- May orchestrate use cases, workflows, and state transitions across domain ports.
- May depend on domain abstractions and infrastructure implementations supplied at composition boundaries.
- Must not hide business rules inside glue code when those rules belong in aggregates, policies, or domain services.

### Infrastructure
- May translate between external systems and domain ports.
- May normalize vendor payloads, persist snapshots, and publish notifications.
- Must not become the home of trading rules, close-decision policy, selection ranking, or portfolio invariants.

### Runtime / Bootstrap / Interface Layers
- May compose dependencies, start processes, expose dashboards, and wire events.
- Must not become fallback locations for business rules that "already have the data".

## Redlines: Block Immediately

The following are hard violations. Stop implementation and redesign before writing code.

1. Domain imports infrastructure, framework, or vendor modules.
2. Business rules are added to gateway, persistence, web, bootstrap, or runtime-entry layers.
3. Cross-context handoffs use mutable entities or raw vendor payloads instead of explicit ports, DTOs, or value objects.
4. New facade/coordinator layers flatten existing boundaries instead of clarifying them.

## Grey Lines: Warn And Improve

These issues do not always require blocking, but they require an explicit improvement path.

- bloated `StrategyEntry` or workflow objects
- stateful domain services that should express policy through context or value objects
- anemic entities that carry data without enforcing invariants
- missing value objects for recurring trading concepts
- ubiquitous-language drift between mother and child repositories

## Mandatory Questions Before Coding

For any task touching `src/strategy/**`, answer these before implementation:
- Which bounded context owns this change?
- Which aggregate, policy, or invariant is affected?
- Which objects are true domain concepts, and which are only adapter payloads?
- Does the proposed dependency direction remain legal?
- Which test best proves the rule stays in the correct layer?

## Required Review Artifacts

### DDD Preflight Card
- change summary
- bounded context
- target layer
- domain concepts involved
- allowed dependencies
- redline checks
- required tests

### DDD Self-Review
- context respected
- dependency direction respected
- business rules kept out of adapters/bootstrap/web
- explicit port/DTO/VO boundaries used
- no new facade/coordinator flattening
- remaining grey-line debt

### Refactor Outputs
When a task is refactor-led, add:
- hotspot diagnosis
- refactor slice plan
- DDD debt delta
