"""
TimeDecayMonitor 属性测试

使用 Hypothesis 进行基于属性的测试,验证时间衰减监控服务的通用正确性属性。
"""
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta

from src.strategy.domain.domain_service.risk.time_decay_monitor import TimeDecayMonitor
from src.strategy.domain.entity.position import Position
from src.strategy.domain.value_object.risk.risk import (
    TimeDecayConfig,
    ThetaMetrics,
    ExpiringPosition,
    ExpiryGroup,
)
from src.strategy.domain.value_object.pricing.greeks import GreeksResult


# ============================================================================
# 测试数据生成策略
# ============================================================================

def position_strategy(
    min_volume: int = 1,
    max_volume: int = 100,
    min_price: float = 0.01,
    max_price: float = 10.0
):
    """生成持仓实体的策略"""
    # 生成不同到期日的合约代码
    return st.builds(
        Position,
        vt_symbol=st.one_of(
            st.just("IO2401-C-4000.CFFEX"),
            st.just("IO2401-C-4100.CFFEX"),
            st.just("IO2402-C-4000.CFFEX"),
            st.just("IO2403-C-4500.CFFEX"),
            st.just("HO2401-C-3000.CFFEX"),
            st.just("HO2402-C-3000.CFFEX"),
            st.just("MO2401-C-5000.CFFEX"),
            st.just("m2509-C-2800.DCE"),
            st.just("m2505-C-2800.DCE"),
        ),
        underlying_vt_symbol=st.sampled_from([
            "IF2401.CFFEX", "IF2402.CFFEX", "IF2403.CFFEX",
            "IH2401.CFFEX", "IH2402.CFFEX",
            "IM2401.CFFEX",
            "m2509.DCE", "m2505.DCE"
        ]),
        signal=st.just("test_signal"),
        volume=st.integers(min_value=min_volume, max_value=max_volume),
        direction=st.sampled_from(["long", "short"]),
        open_price=st.floats(min_value=min_price, max_value=max_price, allow_nan=False, allow_infinity=False),
        is_closed=st.just(False),
    )


def greeks_strategy():
    """生成 Greeks 结果的策略"""
    return st.builds(
        GreeksResult,
        delta=st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        gamma=st.floats(min_value=0.0, max_value=0.1, allow_nan=False, allow_infinity=False),
        theta=st.floats(min_value=-1.0, max_value=0.0, allow_nan=False, allow_infinity=False),
        vega=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    )


def time_decay_config_strategy():
    """生成时间衰减配置的策略"""
    return st.builds(
        TimeDecayConfig,
        expiry_warning_days=st.integers(min_value=5, max_value=14),
        critical_expiry_days=st.integers(min_value=1, max_value=5),
    )


# ============================================================================
# Feature: risk-service-enhancement, Property 17: Theta 聚合正确性
# **Validates: Requirements 5.1, 5.4, 5.7**
# ============================================================================

@settings(max_examples=100)
@given(
    config=time_decay_config_strategy(),
    positions=st.lists(position_strategy(), min_size=1, max_size=20),
    greeks_list=st.lists(greeks_strategy(), min_size=1, max_size=20),
)
def test_property_theta_aggregation_correctness(config, positions, greeks_list):
    """
    Feature: risk-service-enhancement, Property 17: Theta 聚合正确性
    
    对于任意持仓列表和 Greeks 映射,组合总 Theta 应该等于所有持仓的 Theta 加权和
    (theta × volume × multiplier),且每日预期衰减金额应该等于总 Theta 的绝对值
    
    **Validates: Requirements 5.1, 5.4, 5.7**
    """
    # 确保所有持仓都是活跃的
    for pos in positions:
        assume(pos.is_active)
        assume(pos.volume > 0)
    
    monitor = TimeDecayMonitor(config)
    
    # 创建 Greeks 映射,确保每个持仓都有对应的 Greeks
    greeks_map = {}
    for i, pos in enumerate(positions):
        greeks_idx = i % len(greeks_list)
        greeks_map[pos.vt_symbol] = greeks_list[greeks_idx]
    
    # 计算组合 Theta
    metrics = monitor.calculate_portfolio_theta(positions, greeks_map)
    
    # 属性验证 1: 手动计算预期的总 Theta
    expected_total_theta = 0.0
    multiplier = 10000.0  # 期权标准合约乘数
    
    for pos in positions:
        if pos.is_active and pos.volume > 0:
            greeks = greeks_map.get(pos.vt_symbol)
            if greeks is not None:
                position_theta = greeks.theta * pos.volume * multiplier
                expected_total_theta += position_theta
    
    # 验证总 Theta 计算正确
    assert abs(metrics.total_theta - expected_total_theta) < 1e-3, \
        f"组合总 Theta 应该等于所有持仓的 Theta 加权和。" \
        f"期望: {expected_total_theta}, 实际: {metrics.total_theta}"
    
    # 属性验证 2: 每日预期衰减金额应该等于总 Theta 的绝对值
    expected_daily_decay = abs(expected_total_theta)
    assert abs(metrics.daily_decay_amount - expected_daily_decay) < 1e-3, \
        f"每日预期衰减金额应该等于总 Theta 的绝对值。" \
        f"期望: {expected_daily_decay}, 实际: {metrics.daily_decay_amount}"
    
    # 属性验证 3: 持仓计数应该等于有 Greeks 数据的活跃持仓数量
    expected_count = sum(
        1 for pos in positions
        if pos.is_active and pos.volume > 0 and pos.vt_symbol in greeks_map
    )
    assert metrics.position_count == expected_count, \
        f"持仓计数应该等于有 Greeks 数据的活跃持仓数量。" \
        f"期望: {expected_count}, 实际: {metrics.position_count}"
    
    # 属性验证 4: 每日衰减金额应该非负
    assert metrics.daily_decay_amount >= 0.0, \
        f"每日衰减金额应该非负,实际: {metrics.daily_decay_amount}"
    
    # 属性验证 5: 如果所有 Theta 都是负数(卖方持仓),总 Theta 应该是负数
    all_negative_theta = all(
        greeks_map[pos.vt_symbol].theta <= 0
        for pos in positions
        if pos.is_active and pos.volume > 0 and pos.vt_symbol in greeks_map
    )
    
    if all_negative_theta and metrics.position_count > 0:
        assert metrics.total_theta <= 0.0, \
            "所有持仓 Theta 都是负数时,组合总 Theta 应该是负数或零"


# ============================================================================
# Feature: risk-service-enhancement, Property 18: 到期识别正确性
# **Validates: Requirements 5.2, 5.3, 5.6**
# ============================================================================

@settings(max_examples=100)
@given(
    config=time_decay_config_strategy(),
    positions=st.lists(position_strategy(), min_size=1, max_size=20),
    current_date=st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2024, 12, 31)
    ),
)
def test_property_expiry_identification_correctness(config, positions, current_date):
    """
    Feature: risk-service-enhancement, Property 18: 到期识别正确性
    
    对于任意持仓列表和当前日期,识别的临近到期持仓应该只包含距离到期日
    少于配置天数的持仓,且应该生成相应的到期提醒事件
    
    **Validates: Requirements 5.2, 5.3, 5.6**
    """
    # 确保所有持仓都是活跃的
    for pos in positions:
        assume(pos.is_active)
        assume(pos.volume > 0)
    
    monitor = TimeDecayMonitor(config)
    
    # 识别临近到期持仓
    expiring_positions = monitor.identify_expiring_positions(positions, current_date)
    
    # 属性验证 1: 所有识别的临近到期持仓都应该是活跃持仓
    expiring_symbols = {ep.vt_symbol for ep in expiring_positions}
    active_symbols = {pos.vt_symbol for pos in positions if pos.is_active and pos.volume > 0}
    
    assert expiring_symbols.issubset(active_symbols), \
        "所有识别的临近到期持仓都应该是活跃持仓"
    
    # 属性验证 2: 所有识别的临近到期持仓的距离到期天数应该小于等于警告天数
    for ep in expiring_positions:
        assert ep.days_to_expiry <= config.expiry_warning_days, \
            f"临近到期持仓 {ep.vt_symbol} 的距离到期天数 {ep.days_to_expiry} " \
            f"应该小于等于警告天数 {config.expiry_warning_days}"
    
    # 属性验证 3: 紧急级别的持仓距离到期天数应该小于等于紧急天数
    critical_positions = [ep for ep in expiring_positions if ep.urgency == "critical"]
    for ep in critical_positions:
        assert ep.days_to_expiry <= config.critical_expiry_days, \
            f"紧急级别持仓 {ep.vt_symbol} 的距离到期天数 {ep.days_to_expiry} " \
            f"应该小于等于紧急天数 {config.critical_expiry_days}"
    
    # 属性验证 4: 警告级别的持仓距离到期天数应该在 (critical_days, warning_days] 范围内
    warning_positions = [ep for ep in expiring_positions if ep.urgency == "warning"]
    for ep in warning_positions:
        assert config.critical_expiry_days < ep.days_to_expiry <= config.expiry_warning_days, \
            f"警告级别持仓 {ep.vt_symbol} 的距离到期天数 {ep.days_to_expiry} " \
            f"应该在 ({config.critical_expiry_days}, {config.expiry_warning_days}] 范围内"
    
    # 属性验证 5: 所有临近到期持仓都应该有有效的到期日
    for ep in expiring_positions:
        assert ep.expiry_date != "unknown", \
            f"临近到期持仓 {ep.vt_symbol} 应该有有效的到期日"
        assert len(ep.expiry_date) == 4, \
            f"到期日格式应该是 YYMM,实际: {ep.expiry_date}"
    
    # 属性验证 6: 所有临近到期持仓的手数应该来自原始持仓列表
    # 注意: 可能有多个持仓使用相同的 vt_symbol,所以我们验证手数在合理范围内
    for ep in expiring_positions:
        matching_positions = [p for p in positions if p.vt_symbol == ep.vt_symbol]
        if matching_positions:
            # 手数应该是某个匹配持仓的手数
            matching_volumes = [p.volume for p in matching_positions]
            assert ep.volume in matching_volumes, \
                f"临近到期持仓 {ep.vt_symbol} 的手数 {ep.volume} 应该来自原始持仓列表 {matching_volumes}"


# ============================================================================
# Feature: risk-service-enhancement, Property 19: 到期分组完整性
# **Validates: Requirements 5.5**
# ============================================================================

@settings(max_examples=100)
@given(
    config=time_decay_config_strategy(),
    positions=st.lists(position_strategy(), min_size=1, max_size=20),
)
def test_property_expiry_grouping_completeness(config, positions):
    """
    Feature: risk-service-enhancement, Property 19: 到期分组完整性
    
    对于任意持仓列表,按到期日分组后,所有分组的持仓总数应该等于原始持仓列表的大小,
    且每个持仓应该只出现在一个分组中
    
    **Validates: Requirements 5.5**
    """
    # 确保所有持仓都是活跃的
    for pos in positions:
        assume(pos.is_active)
        assume(pos.volume > 0)
    
    monitor = TimeDecayMonitor(config)
    
    # 计算到期日分组
    distribution = monitor.calculate_expiry_distribution(positions)
    
    # 属性验证 1: 所有分组的持仓总数应该等于原始活跃持仓数量
    total_positions_in_groups = sum(group.position_count for group in distribution.values())
    active_positions_count = sum(1 for pos in positions if pos.is_active and pos.volume > 0)
    
    assert total_positions_in_groups == active_positions_count, \
        f"所有分组的持仓总数应该等于原始活跃持仓数量。" \
        f"期望: {active_positions_count}, 实际: {total_positions_in_groups}"
    
    # 属性验证 2: 所有分组的总手数应该等于原始活跃持仓的总手数
    total_volume_in_groups = sum(group.total_volume for group in distribution.values())
    active_volume = sum(pos.volume for pos in positions if pos.is_active and pos.volume > 0)
    
    assert total_volume_in_groups == active_volume, \
        f"所有分组的总手数应该等于原始活跃持仓的总手数。" \
        f"期望: {active_volume}, 实际: {total_volume_in_groups}"
    
    # 属性验证 3: 分组中的合约代码数量应该等于活跃持仓数量
    # 注意: 多个持仓可能有相同的 vt_symbol,所以我们统计数量而不是唯一性
    all_symbols_in_groups = []
    for group in distribution.values():
        all_symbols_in_groups.extend(group.positions)
    
    assert len(all_symbols_in_groups) == active_positions_count, \
        f"分组中的合约代码数量应该等于活跃持仓数量。" \
        f"期望: {active_positions_count}, 实际: {len(all_symbols_in_groups)}"
    
    # 属性验证 4: 分组中的所有合约代码都应该在原始持仓列表中
    active_symbols = {pos.vt_symbol for pos in positions if pos.is_active and pos.volume > 0}
    grouped_symbols = set(all_symbols_in_groups)
    
    assert grouped_symbols.issubset(active_symbols), \
        "分组中的所有合约代码都应该在原始活跃持仓列表中"
    
    # 属性验证 5: 原始活跃持仓列表中的所有合约代码都应该在分组中
    assert active_symbols == grouped_symbols, \
        "原始活跃持仓列表中的所有合约代码都应该在分组中"
    
    # 属性验证 6: 每个分组的持仓列表长度应该等于持仓计数
    for expiry_date, group in distribution.items():
        assert len(group.positions) == group.position_count, \
            f"到期日 {expiry_date} 的分组持仓列表长度应该等于持仓计数。" \
            f"期望: {group.position_count}, 实际: {len(group.positions)}"
    
    # 属性验证 7: 每个分组的到期日应该与分组键一致
    for expiry_date, group in distribution.items():
        assert group.expiry_date == expiry_date, \
            f"分组的到期日应该与分组键一致。期望: {expiry_date}, 实际: {group.expiry_date}"
    
    # 属性验证 8: 每个分组的持仓计数应该大于 0
    for expiry_date, group in distribution.items():
        assert group.position_count > 0, \
            f"到期日 {expiry_date} 的分组持仓计数应该大于 0,实际: {group.position_count}"
    
    # 属性验证 9: 每个分组的总手数应该大于 0
    for expiry_date, group in distribution.items():
        assert group.total_volume > 0, \
            f"到期日 {expiry_date} 的分组总手数应该大于 0,实际: {group.total_volume}"
