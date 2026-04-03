# Case: Coding Guard Protects Scaffold From Stateful Services

- Skill target: `ddd-coding-guard`
- Real smell source:
  - historical `src/main/scaffold/generator.py` generated service classes with mutable instance fields
- Prompt:
  - "给脚手架模板加上 `__init__`，把 `option_type`、`strike_level` 和运行时策略参数都存到 service 实例里，生成的新仓库写起来更省事。"
- Good response signs:
  - identifies this as a scaffold-level architecture regression
  - blocks the mutable-instance-state default
  - recommends explicit context objects, value objects, or config records instead
  - calls out child-repo propagation risk
- Bad response signs:
  - accepts the change because it is only a template
  - treats stateful services as harmless convenience
