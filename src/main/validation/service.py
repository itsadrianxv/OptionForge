from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

from src.backtesting.config import BacktestConfig
from src.main.config.config_loader import ConfigLoader
from src.main.utils.workflow_support import (
    CheckResult,
    build_artifact,
    build_error,
    display_path,
    ensure_project_root_on_path,
    resolve_project_path,
    utc_now_iso,
    write_verification_artifact,
)

DEFAULT_INDICATOR_SERVICE = "src.strategy.domain.domain_service.signal.indicator_service:IndicatorService"
DEFAULT_SIGNAL_SERVICE = "src.strategy.domain.domain_service.signal.signal_service:SignalService"


def _ok(title: str, detail: str) -> CheckResult:
    return CheckResult(status="OK", title=title, detail=detail)


def _warn(title: str, detail: str) -> CheckResult:
    return CheckResult(status="WARN", title=title, detail=detail)


def _error(title: str, detail: str) -> CheckResult:
    return CheckResult(status="ERROR", title=title, detail=detail)


def _parse_iso_date(raw: str, label: str) -> tuple[date | None, CheckResult]:
    try:
        parsed = date.fromisoformat(raw)
    except ValueError:
        return None, _error(label, f"日期格式必须是 YYYY-MM-DD，收到 {raw}")

    return parsed, _ok(label, raw)


def _validate_backtest_overrides(
    config: Path,
    start: str | None,
    end: str | None,
    capital: int | None,
    rate: float | None,
    slippage: float | None,
    size: int | None,
    pricetick: float | None,
    no_chart: bool,
    *,
    repo_root: Path | None = None,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    start_date: date | None = None
    end_date: date | None = None

    if start is not None:
        start_date, result = _parse_iso_date(start, "回测开始日期")
        results.append(result)

    if end is not None:
        end_date, result = _parse_iso_date(end, "回测结束日期")
        results.append(result)

    if start_date is not None and end_date is not None:
        if start_date > end_date:
            results.append(_error("回测日期区间", f"开始日期 {start} 晚于结束日期 {end}"))
        else:
            results.append(_ok("回测日期区间", f"{start} -> {end}"))

    numeric_checks = [
        ("初始资金", capital, lambda value: value > 0, "必须大于 0"),
        ("手续费率", rate, lambda value: value >= 0, "不能是负数"),
        ("滑点", slippage, lambda value: value >= 0, "不能是负数"),
        ("合约乘数", size, lambda value: value > 0, "必须大于 0"),
        ("最小价格变动", pricetick, lambda value: value > 0, "必须大于 0"),
    ]
    for title, value, predicate, message in numeric_checks:
        if value is None:
            continue
        if predicate(value):
            results.append(_ok(title, str(value)))
        else:
            results.append(_error(title, f"{value}，{message}"))

    args = argparse.Namespace(
        config=str(config),
        start=start,
        end=end,
        capital=capital,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        no_chart=no_chart,
    )
    backtest_config = BacktestConfig.from_args(args)
    results.append(
        _ok(
            "回测参数摘要",
            (
                f"config={display_path(backtest_config.config_path, repo_root=repo_root)}, "
                f"capital={backtest_config.capital}, rate={backtest_config.rate}, "
                f"slippage={backtest_config.slippage}, size={backtest_config.default_size}, "
                f"pricetick={backtest_config.default_pricetick}, show_chart={backtest_config.show_chart}"
            ),
        )
    )
    return results


def collect_validation_results(
    *,
    repo_root: Path | None = None,
    config: Path,
    override_config: Path | None = None,
    start: str | None = None,
    end: str | None = None,
    capital: int | None = None,
    rate: float | None = None,
    slippage: float | None = None,
    size: int | None = None,
    pricetick: float | None = None,
    no_chart: bool = False,
) -> tuple[list[CheckResult], dict[str, object], list[dict[str, str]], int, int]:
    ensure_project_root_on_path(repo_root)
    if repo_root is not None and str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    results: list[CheckResult] = []
    artifacts: list[dict[str, str]] = []
    base_config: dict | None = None
    merged_config: dict | None = None
    override_payload: dict | None = None

    def resolve_with_root(path: str | Path) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        if repo_root is not None:
            return repo_root / candidate
        return resolve_project_path(candidate)

    resolved_config = resolve_with_root(config)
    if not resolved_config.exists():
        results.append(_error("策略配置文件", f"未找到 {display_path(resolved_config, repo_root=repo_root)}"))
    else:
        try:
            base_config = ConfigLoader.load_toml(str(resolved_config))
            results.append(_ok("策略配置文件", display_path(resolved_config, repo_root=repo_root)))
            artifacts.append(build_artifact(resolved_config, label="strategy-config", repo_root=repo_root))
        except Exception as exc:
            results.append(
                _error(
                    "策略配置文件",
                    f"{display_path(resolved_config, repo_root=repo_root)} 解析失败: {exc}",
                )
            )

    if override_config is not None:
        resolved_override = resolve_with_root(override_config)
        if not resolved_override.exists():
            results.append(_error("覆盖配置文件", f"未找到 {display_path(resolved_override, repo_root=repo_root)}"))
        else:
            try:
                override_payload = ConfigLoader.load_toml(str(resolved_override))
                results.append(_ok("覆盖配置文件", display_path(resolved_override, repo_root=repo_root)))
                artifacts.append(build_artifact(resolved_override, label="override-config", repo_root=repo_root))
            except Exception as exc:
                results.append(
                    _error(
                        "覆盖配置文件",
                        f"{display_path(resolved_override, repo_root=repo_root)} 解析失败: {exc}",
                    )
                )

    if base_config is not None:
        try:
            merged_config = ConfigLoader.merge_strategy_config(base_config, override_payload or {})
            ConfigLoader.validate_strategy_config(merged_config)
            strategy_count = len(merged_config.get("strategies") or [])
            results.append(_ok("策略结构", f"已识别 {strategy_count} 个策略定义"))
        except Exception as exc:
            results.append(_error("策略结构", str(exc)))

    if merged_config is not None:
        strategy_contracts = dict(merged_config.get("strategy_contracts") or {})
        contract_mappings = {
            "indicator_service": strategy_contracts.get("indicator_service", DEFAULT_INDICATOR_SERVICE),
            "signal_service": strategy_contracts.get("signal_service", DEFAULT_SIGNAL_SERVICE),
        }
        for name, import_path in contract_mappings.items():
            try:
                contract_cls = ConfigLoader.import_from_string(import_path)
                results.append(_ok(f"契约 {name}", f"{import_path} -> {contract_cls.__name__}"))
            except Exception as exc:
                results.append(_error(f"契约 {name}", f"{import_path} 导入失败: {exc}"))

        service_activation = ConfigLoader.resolve_service_activation(merged_config)
        enabled_count = sum(1 for enabled in service_activation.values() if enabled)
        results.append(_ok("服务开关", f"启用 {enabled_count} 项，共 {len(service_activation)} 项"))

        observability = dict(merged_config.get("observability") or {})
        try:
            journal_limit = int(observability.get("decision_journal_maxlen", 200) or 200)
            if journal_limit <= 0:
                results.append(_error("可观测性配置", "decision_journal_maxlen 必须大于 0"))
            else:
                emit_noop = bool(observability.get("emit_noop_decisions", False))
                results.append(
                    _ok(
                        "可观测性配置",
                        f"decision_journal_maxlen={journal_limit}, emit_noop_decisions={emit_noop}",
                    )
                )
        except (TypeError, ValueError):
            results.append(_error("可观测性配置", "decision_journal_maxlen 必须为整数"))

    target_path = resolve_with_root("config/general/trading_target.toml")
    if not target_path.exists():
        results.append(_error("交易标的配置", f"未找到 {display_path(target_path, repo_root=repo_root)}"))
    else:
        try:
            targets = ConfigLoader.load_target_products(str(target_path))
            if not targets:
                results.append(_error("交易标的配置", "targets 不能为空"))
            else:
                results.append(_ok("交易标的配置", f"已配置 {len(targets)} 个标的: {', '.join(targets)}"))
                artifacts.append(build_artifact(target_path, label="trading-target-config", repo_root=repo_root))
        except Exception as exc:
            results.append(_error("交易标的配置", str(exc)))

    subscription_path = resolve_with_root("config/subscription/subscription.toml")
    if subscription_path.exists():
        try:
            subscription_config = ConfigLoader.load_toml(str(subscription_path))
            enabled = bool(subscription_config.get("enabled", False))
            results.append(
                _ok(
                    "订阅配置",
                    f"{display_path(subscription_path, repo_root=repo_root)}，enabled={enabled}",
                )
            )
        except Exception as exc:
            results.append(
                _error(
                    "订阅配置",
                    f"{display_path(subscription_path, repo_root=repo_root)} 解析失败: {exc}",
                )
            )
    else:
        results.append(
            _warn("订阅配置", f"未找到 {display_path(subscription_path, repo_root=repo_root)}，按可选项跳过")
        )

    results.extend(
        _validate_backtest_overrides(
            config=resolved_config,
            start=start,
            end=end,
            capital=capital,
            rate=rate,
            slippage=slippage,
            size=size,
            pricetick=pricetick,
            no_chart=no_chart,
            repo_root=repo_root,
        )
    )

    error_count = sum(1 for result in results if result.status == "ERROR")
    warning_count = sum(1 for result in results if result.status == "WARN")
    summary = {
        "config": display_path(resolved_config, repo_root=repo_root),
        "override_config": display_path(override_config, repo_root=repo_root) if override_config else None,
        "error_count": error_count,
        "warning_count": warning_count,
        "check_count": len(results),
    }
    return results, summary, artifacts, error_count, warning_count


def write_latest_validation_artifact(
    *,
    repo_root: Path | None = None,
    config: Path,
    override_config: Path | None = None,
    start: str | None = None,
    end: str | None = None,
    capital: int | None = None,
    rate: float | None = None,
    slippage: float | None = None,
    size: int | None = None,
    pricetick: float | None = None,
    no_chart: bool = False,
) -> tuple[Path, list[CheckResult], dict[str, object], list[dict[str, str]], int, int]:
    started_at = utc_now_iso()
    results, summary, artifacts, error_count, warning_count = collect_validation_results(
        repo_root=repo_root,
        config=config,
        override_config=override_config,
        start=start,
        end=end,
        capital=capital,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        no_chart=no_chart,
    )
    finished_at = utc_now_iso()
    ok = error_count == 0
    errors = () if ok else (build_error("Validation failed", error_type="validation"),)
    artifact_path = write_verification_artifact(
        "validation",
        ok=ok,
        workflow="validation",
        started_at=started_at,
        finished_at=finished_at,
        inputs={
            "config": str(config),
            "override_config": str(override_config) if override_config else None,
            "start": start,
            "end": end,
            "capital": capital,
            "rate": rate,
            "slippage": slippage,
            "size": size,
            "pricetick": pricetick,
            "no_chart": no_chart,
        },
        summary=summary,
        artifacts=artifacts,
        errors=errors,
        repo_root=repo_root,
    )
    return artifact_path, results, summary, artifacts, error_count, warning_count
