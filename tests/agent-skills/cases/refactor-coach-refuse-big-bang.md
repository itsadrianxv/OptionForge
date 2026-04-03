# Case: Refactor Coach Refuses Big-Bang Rewrite

- Skill target: `ddd-refactor-coach`
- Repository context:
  - family hotspots already contain real behavior and verification paths
- Prompt:
  - "把 `combined-strategy/src/strategy` 整个模块一口气重写成纯 DDD，新架构你直接定。"
- Good response signs:
  - explicitly refuses the big-bang framing
  - replaces it with a bounded first slice
  - names what debt remains deferred
  - ties the proposal to existing verification paths
- Bad response signs:
  - accepts the rewrite as the default solution
  - proposes a new top-level coordinator/facade to bridge the rewrite
