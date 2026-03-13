# 贡献指南

感谢你关注这个项目。

本仓库是一个面向期权策略研发的 Python 脚手架，重点在于让策略编排、领域服务、基础设施、回测与监控能力可以持续演进。因此提交改动时，请尽量保持：

- 改动边界清晰，一次 PR 只解决一类问题
- 先补最小必要实现，再逐步扩展能力
- 配置、测试、部署改动同步更新说明

## 本地开发

建议使用 `Python 3.12`。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 运行与测试

本地运行：

```powershell
python src/main/main.py --mode standalone --config config/strategy_config.toml --paper
```

运行测试：

```powershell
pytest -c config/pytest.ini
```

Docker Compose 冒烟检查：

```powershell
docker compose --env-file deploy/.env.example -f deploy/docker-compose.yml config
docker build -f deploy/Dockerfile -t optionforge:local .
```

## 提交规范

请尽量遵循 Conventional Commits，并使用中文提交信息。

示例：

```text
fix: 修复策略快照读取异常
feat: 增加回测参数扫描入口
docs: 更新部署与测试说明
```

## Pull Request 要求

提交 PR 时请尽量说明：

- 这次改动解决了什么问题
- 改动影响了哪些模块
- 如何验证这次改动
- 是否涉及配置、接口或部署变更

仓库已提供 PR 模板，请按模板补充必要信息。
