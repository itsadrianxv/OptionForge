# OptionForge

面向 Coding Agent 的期权策略研发脚手架。

这个仓库现在以模板仓库和 agent 资产为中心，不再把安装式命令包装器作为默认入口。核心目标是保留可读的策略意图、清晰的 editable surface，以及稳定的验证闭环，让 agent 直接在现有代码基础上迭代策略实现。

## 核心资产

- `strategy_spec.toml`
  - 策略意图与 acceptance source of truth
- `focus/strategies/*/strategy.manifest.toml`
  - pack、surface、workflow 元数据
- `.focus/context.json`
  - 当前策略的机器可读上下文契约
- `.focus/SYSTEM_MAP.md`
- `.focus/ACTIVE_SURFACE.md`
- `.focus/TASK_BRIEF.md`
- `.focus/WORKFLOWS.md`
- `.focus/TASK_ROUTER.md`
- `.focus/TEST_MATRIX.md`
- `tests/TEST.md`
  - 当前策略的测试与验证摘要
- `artifacts/validation/latest.json`
  - 最近一次验证产物

## 开发方式

默认做法不是“先学一套 CLI”，而是：

1. 读取 `strategy_spec.toml` 和 `.focus/context.json`
2. 按 editable surface 修改代码
3. 在需要时刷新 focus 资产
4. 先跑 `focus.smoke`，必要时再跑 `focus.full`
5. 只有在任务确实需要执行证据时，才运行 runtime 或 backtest 工作流

## 运行与验证语义

`focus/strategies/main/strategy.manifest.toml` 中的 `[workflow]` 段定义了当前仓库的模块级入口：

- `runtime_module`
- `backtest_module`
- `monitor_script`

`[acceptance]` 段定义默认 verification profile、selectors、关键日志和关键产物。

## 目录概览

- `src/main`
  - 运行时装配、focus 资产、验证服务
- `src/backtesting`
  - 回测配置与执行
- `src/strategy`
  - 策略应用层、领域层、基础设施层、runtime provider
- `src/web`
  - 只读监控界面
- `focus`
  - pack 与策略 manifest 元数据
- `.focus`
  - 生成后的导航与上下文文件
- `tests`
  - 运行时、focus、验证与策略测试
- `deploy`
  - deploy-main 工作流与容器部署入口

## 文档

- `AGENTS.md`
  - 仓库操作与交付政策
- `AGENTS_FOCUS.md`
  - agent-first 阅读、编辑和验证约定
- `docs/slides/OptionForge-internal-share.html`
  - 当前内部分享材料

## 许可证

本项目采用 [GNU Affero General Public License v3.0](LICENSE)。
