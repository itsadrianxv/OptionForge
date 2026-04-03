# OptionsForge Refactor Catalog

Use this catalog when a repository hotspot violates the DDD constitution.

| Smell | Class | First move | Done when |
| --- | --- | --- | --- |
| Domain imports infrastructure helper or adapter | Redline | Extract a domain port, pure value object helper, or translator at the infrastructure edge | Domain no longer imports infrastructure code |
| Domain imports vendor/framework types (`vnpy`, broker payloads, DB models) | Redline | Introduce normalized domain facts or an anti-corruption adapter | Vendor types stop crossing into domain modules |
| Business rules live in gateway, persistence, web, bootstrap, or runtime entry | Redline | Move decision logic into aggregate, policy, domain service, or application workflow | Outer layer only transports and orchestrates |
| New facade/coordinator flattens boundaries | Redline | Delete the layer and make the real dependency path explicit | Boundary becomes easier to see, not harder |
| `StrategyEntry` / workflow object keeps growing | Grey line | Carve out one use-case slice or runtime-state holder at a time | Entry object mostly delegates instead of owning logic |
| Domain service stores mutable runtime state | Grey line | Replace instance state with context objects, policy value objects, or config records | Service behavior depends on inputs, not hidden instance fields |
| Entity is anemic | Grey line | Move one invariant or lifecycle rule into the entity/aggregate | Entity behavior protects its own consistency |
| Repeated primitive bundles (`dict`, loose strings, float tuples) cross layers | Grey line | Introduce value objects or DTOs around the concept | Boundaries become explicit and typed by meaning |
| Child repo drifts from mother-repo language | Grey line | Align names to the shared ubiquitous language and document exceptions | Equivalent concepts use the same names across the family |

## Slice Planning Rule

Never propose a big-bang rewrite for an existing hotspot. Produce the smallest safe slice that:
1. removes one redline or contains one grey-line cluster
2. preserves current behavior with focused regression tests
3. leaves the next slice easier, not harder

## Required Refactor Outputs

### Hotspot diagnosis
- current smell
- why it violates the constitution
- redline or grey-line classification
- target shape

### Refactor slice plan
- first slice
- safety test for that slice
- next deferred slice
- risks if deferred

### DDD debt delta
- debt removed now
- debt intentionally left behind
- reason for deferral
