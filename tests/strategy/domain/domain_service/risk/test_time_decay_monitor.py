"""
TimeDecayMonitor 单元测试

测试时间衰减监控服务的组合 Theta 计算、临近到期持仓识别和到期日分组统计功能。
"""
import pytest
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


class TestTimeDecayMonitorConfig:
    """测试时间衰减监控配置"""
    
    def test_valid_config(self):
        """测试有效配置"""
        config = TimeDecayConfig(
            expiry_warning_days=7,
            critical_expiry_days=3,
        )
        monitor = TimeDecayMonitor(config)
        assert monitor is not None
        assert monitor._config.expiry_warning_days == 7
        assert monitor._config.critical_expiry_days == 3
    
    def test_default_config(self):
        """测试默认配置"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        assert monitor._config.expiry_warning_days == 7
        assert monitor._config.critical_expiry_days == 3


class TestPortfolioThetaCalculation:
    """测试组合 Theta 计算"""
    
    def test_calculate_portfolio_theta_single_position(self):
        """测试单个持仓的 Theta 计算"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        # 创建单个持仓
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            )
        ]
        
        # Greeks 数据：Theta = -0.05
        greeks_map = {
            "IO2401-C-4000.CFFEX": GreeksResult(
                delta=0.3,
                gamma=0.01,
                theta=-0.05,
                vega=50.0,
            )
        }
        
        metrics = monitor.calculate_portfolio_theta(positions, greeks_map)
        
        # 组合 Theta = -0.05 * 10 * 10000 = -5000
        assert abs(metrics.total_theta - (-5000.0)) < 1e-6
        # 每日衰减金额 = |-5000| = 5000
        assert abs(metrics.daily_decay_amount - 5000.0) < 1e-6
        assert metrics.position_count == 1
    
    def test_calculate_portfolio_theta_multiple_positions(self):
        """测试多个持仓的 Theta 聚合"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        # 创建多个持仓
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            ),
            Position(
                vt_symbol="HO2401-C-3000.CFFEX",
                underlying_vt_symbol="IH2401.CFFEX",
                signal="open_signal",
                volume=5,
                direction="short",
                open_price=0.6,
            ),
            Position(
                vt_symbol="MO2401-C-5000.CFFEX",
                underlying_vt_symbol="IM2401.CFFEX",
                signal="open_signal",
                volume=8,
                direction="short",
                open_price=0.4,
            ),
        ]
        
        # Greeks 数据
        greeks_map = {
            "IO2401-C-4000.CFFEX": GreeksResult(theta=-0.05),
            "HO2401-C-3000.CFFEX": GreeksResult(theta=-0.03),
            "MO2401-C-5000.CFFEX": GreeksResult(theta=-0.04),
        }
        
        metrics = monitor.calculate_portfolio_theta(positions, greeks_map)
        
        # 组合 Theta = (-0.05*10 + -0.03*5 + -0.04*8) * 10000
        #            = (-0.5 - 0.15 - 0.32) * 10000 = -9700
        expected_theta = (-0.05 * 10 + -0.03 * 5 + -0.04 * 8) * 10000
        assert abs(metrics.total_theta - expected_theta) < 1e-6
        assert abs(metrics.daily_decay_amount - abs(expected_theta)) < 1e-6
        assert metrics.position_count == 3
    
    def test_calculate_portfolio_theta_positive_theta(self):
        """测试正 Theta（买方持仓）"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        # 创建买方持仓（正 Theta）
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="long",
                open_price=0.5,
            )
        ]
        
        # 买方持仓通常有负 Theta（时间价值衰减对买方不利）
        greeks_map = {
            "IO2401-C-4000.CFFEX": GreeksResult(theta=-0.05)
        }
        
        metrics = monitor.calculate_portfolio_theta(positions, greeks_map)
        
        # 组合 Theta = -0.05 * 10 * 10000 = -5000
        assert abs(metrics.total_theta - (-5000.0)) < 1e-6
        # 每日衰减金额取绝对值
        assert abs(metrics.daily_decay_amount - 5000.0) < 1e-6
    
    def test_calculate_portfolio_theta_missing_greeks(self):
        """测试缺失 Greeks 数据"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            ),
            Position(
                vt_symbol="HO2401-C-3000.CFFEX",
                underlying_vt_symbol="IH2401.CFFEX",
                signal="open_signal",
                volume=5,
                direction="short",
                open_price=0.6,
            ),
        ]
        
        # 只提供一个合约的 Greeks
        greeks_map = {
            "IO2401-C-4000.CFFEX": GreeksResult(theta=-0.05)
        }
        
        metrics = monitor.calculate_portfolio_theta(positions, greeks_map)
        
        # 只计算有 Greeks 数据的持仓
        assert abs(metrics.total_theta - (-5000.0)) < 1e-6
        assert metrics.position_count == 1
    
    def test_calculate_portfolio_theta_inactive_positions(self):
        """测试非活跃持仓被排除"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            ),
            Position(
                vt_symbol="HO2401-C-3000.CFFEX",
                underlying_vt_symbol="IH2401.CFFEX",
                signal="open_signal",
                volume=0,  # 无持仓
                direction="short",
                open_price=0.6,
                is_closed=True,
            ),
        ]
        
        greeks_map = {
            "IO2401-C-4000.CFFEX": GreeksResult(theta=-0.05),
            "HO2401-C-3000.CFFEX": GreeksResult(theta=-0.03),
        }
        
        metrics = monitor.calculate_portfolio_theta(positions, greeks_map)
        
        # 只计算活跃持仓
        assert abs(metrics.total_theta - (-5000.0)) < 1e-6
        assert metrics.position_count == 1


class TestExpiringPositionIdentification:
    """测试临近到期持仓识别"""
    
    def test_identify_expiring_positions_warning_level(self):
        """测试识别警告级别的临近到期持仓"""
        config = TimeDecayConfig(
            expiry_warning_days=7,
            critical_expiry_days=3,
        )
        monitor = TimeDecayMonitor(config)
        
        # 当前日期：2024-01-08
        current_date = datetime(2024, 1, 8)
        
        # 创建持仓：到期日 2024-01（距离 7 天）
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            )
        ]
        
        expiring = monitor.identify_expiring_positions(positions, current_date)
        
        # 应该识别为警告级别
        assert len(expiring) == 1
        assert expiring[0].vt_symbol == "IO2401-C-4000.CFFEX"
        assert expiring[0].expiry_date == "2401"
        assert expiring[0].days_to_expiry == 7
        assert expiring[0].volume == 10
        assert expiring[0].urgency == "warning"
    
    def test_identify_expiring_positions_critical_level(self):
        """测试识别紧急级别的临近到期持仓"""
        config = TimeDecayConfig(
            expiry_warning_days=7,
            critical_expiry_days=3,
        )
        monitor = TimeDecayMonitor(config)
        
        # 当前日期：2024-01-12
        current_date = datetime(2024, 1, 12)
        
        # 创建持仓：到期日 2024-01（距离 3 天）
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            )
        ]
        
        expiring = monitor.identify_expiring_positions(positions, current_date)
        
        # 应该识别为紧急级别
        assert len(expiring) == 1
        assert expiring[0].urgency == "critical"
        assert expiring[0].days_to_expiry == 3
    
    def test_identify_expiring_positions_multiple_urgency_levels(self):
        """测试识别多个不同紧急程度的持仓"""
        config = TimeDecayConfig(
            expiry_warning_days=7,
            critical_expiry_days=3,
        )
        monitor = TimeDecayMonitor(config)
        
        # 当前日期：2024-01-10
        current_date = datetime(2024, 1, 10)
        
        # 创建多个持仓：不同到期日
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",  # 距离 5 天，warning
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            ),
            Position(
                vt_symbol="IO2402-C-4000.CFFEX",  # 距离 36 天，不提醒
                underlying_vt_symbol="IF2402.CFFEX",
                signal="open_signal",
                volume=5,
                direction="short",
                open_price=0.6,
            ),
            Position(
                vt_symbol="HO2401-C-3000.CFFEX",  # 距离 5 天，warning
                underlying_vt_symbol="IH2401.CFFEX",
                signal="open_signal",
                volume=8,
                direction="short",
                open_price=0.4,
            ),
        ]
        
        expiring = monitor.identify_expiring_positions(positions, current_date)
        
        # 应该识别 2 个警告级别的持仓
        assert len(expiring) == 2
        warning_positions = [p for p in expiring if p.urgency == "warning"]
        assert len(warning_positions) == 2
    
    def test_identify_expiring_positions_no_expiring(self):
        """测试无临近到期持仓"""
        config = TimeDecayConfig(
            expiry_warning_days=7,
            critical_expiry_days=3,
        )
        monitor = TimeDecayMonitor(config)
        
        # 当前日期：2024-01-01
        current_date = datetime(2024, 1, 1)
        
        # 创建持仓：到期日 2024-02（距离 45 天）
        positions = [
            Position(
                vt_symbol="IO2402-C-4000.CFFEX",
                underlying_vt_symbol="IF2402.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            )
        ]
        
        expiring = monitor.identify_expiring_positions(positions, current_date)
        
        # 不应该有临近到期持仓
        assert len(expiring) == 0
    
    def test_identify_expiring_positions_inactive_excluded(self):
        """测试非活跃持仓被排除"""
        config = TimeDecayConfig(
            expiry_warning_days=7,
            critical_expiry_days=3,
        )
        monitor = TimeDecayMonitor(config)
        
        current_date = datetime(2024, 1, 8)
        
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            ),
            Position(
                vt_symbol="HO2401-C-3000.CFFEX",
                underlying_vt_symbol="IH2401.CFFEX",
                signal="open_signal",
                volume=0,  # 无持仓
                direction="short",
                open_price=0.6,
                is_closed=True,
            ),
        ]
        
        expiring = monitor.identify_expiring_positions(positions, current_date)
        
        # 只识别活跃持仓
        assert len(expiring) == 1
        assert expiring[0].vt_symbol == "IO2401-C-4000.CFFEX"
    
    def test_identify_expiring_positions_already_expired(self):
        """测试已到期持仓"""
        config = TimeDecayConfig(
            expiry_warning_days=7,
            critical_expiry_days=3,
        )
        monitor = TimeDecayMonitor(config)
        
        # 当前日期：2024-01-20（已过 2401 到期日）
        current_date = datetime(2024, 1, 20)
        
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            )
        ]
        
        expiring = monitor.identify_expiring_positions(positions, current_date)
        
        # 已到期持仓，days_to_expiry 为负数，应该识别为 critical
        assert len(expiring) == 1
        assert expiring[0].days_to_expiry < 0
        assert expiring[0].urgency == "critical"


class TestExpiryDistribution:
    """测试到期日分组统计"""
    
    def test_calculate_expiry_distribution_single_expiry(self):
        """测试单一到期日的分组"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        # 创建同一到期日的持仓
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            ),
            Position(
                vt_symbol="IO2401-C-4100.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=5,
                direction="short",
                open_price=0.6,
            ),
        ]
        
        distribution = monitor.calculate_expiry_distribution(positions)
        
        # 应该只有一个分组
        assert len(distribution) == 1
        assert "2401" in distribution
        
        group = distribution["2401"]
        assert group.expiry_date == "2401"
        assert group.position_count == 2
        assert group.total_volume == 15
        assert len(group.positions) == 2
        assert "IO2401-C-4000.CFFEX" in group.positions
        assert "IO2401-C-4100.CFFEX" in group.positions
    
    def test_calculate_expiry_distribution_multiple_expiries(self):
        """测试多个到期日的分组"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        # 创建不同到期日的持仓
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            ),
            Position(
                vt_symbol="IO2402-C-4000.CFFEX",
                underlying_vt_symbol="IF2402.CFFEX",
                signal="open_signal",
                volume=5,
                direction="short",
                open_price=0.6,
            ),
            Position(
                vt_symbol="HO2401-C-3000.CFFEX",
                underlying_vt_symbol="IH2401.CFFEX",
                signal="open_signal",
                volume=8,
                direction="short",
                open_price=0.4,
            ),
        ]
        
        distribution = monitor.calculate_expiry_distribution(positions)
        
        # 应该有两个分组
        assert len(distribution) == 2
        assert "2401" in distribution
        assert "2402" in distribution
        
        # 验证 2401 分组
        group_2401 = distribution["2401"]
        assert group_2401.position_count == 2
        assert group_2401.total_volume == 18
        
        # 验证 2402 分组
        group_2402 = distribution["2402"]
        assert group_2402.position_count == 1
        assert group_2402.total_volume == 5
    
    def test_calculate_expiry_distribution_inactive_excluded(self):
        """测试非活跃持仓被排除"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            ),
            Position(
                vt_symbol="HO2401-C-3000.CFFEX",
                underlying_vt_symbol="IH2401.CFFEX",
                signal="open_signal",
                volume=0,  # 无持仓
                direction="short",
                open_price=0.6,
                is_closed=True,
            ),
        ]
        
        distribution = monitor.calculate_expiry_distribution(positions)
        
        # 只统计活跃持仓
        assert len(distribution) == 1
        group = distribution["2401"]
        assert group.position_count == 1
        assert group.total_volume == 10
    
    def test_calculate_expiry_distribution_unknown_expiry(self):
        """测试无法提取到期日的合约"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            ),
            Position(
                vt_symbol="INVALID.CFFEX",  # 无法提取到期日
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=5,
                direction="short",
                open_price=0.6,
            ),
        ]
        
        distribution = monitor.calculate_expiry_distribution(positions)
        
        # 应该有两个分组：2401 和 unknown
        assert len(distribution) == 2
        assert "2401" in distribution
        assert "unknown" in distribution
        
        # 验证 unknown 分组
        unknown_group = distribution["unknown"]
        assert unknown_group.position_count == 1
        assert unknown_group.total_volume == 5


class TestBoundaryConditions:
    """测试边界情况"""
    
    def test_empty_positions_list(self):
        """测试空持仓列表"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        positions = []
        greeks_map = {}
        
        # 测试 Theta 计算
        metrics = monitor.calculate_portfolio_theta(positions, greeks_map)
        assert metrics.total_theta == 0.0
        assert metrics.daily_decay_amount == 0.0
        assert metrics.position_count == 0
        
        # 测试到期识别
        current_date = datetime.now()
        expiring = monitor.identify_expiring_positions(positions, current_date)
        assert len(expiring) == 0
        
        # 测试到期分组
        distribution = monitor.calculate_expiry_distribution(positions)
        assert len(distribution) == 0
    
    def test_all_positions_same_expiry(self):
        """测试所有持仓同一到期日"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        # 创建多个同一到期日的持仓
        positions = [
            Position(
                vt_symbol=f"IO2401-C-{4000 + i * 100}.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            )
            for i in range(5)
        ]
        
        distribution = monitor.calculate_expiry_distribution(positions)
        
        # 应该只有一个分组
        assert len(distribution) == 1
        assert "2401" in distribution
        
        group = distribution["2401"]
        assert group.position_count == 5
        assert group.total_volume == 50
    
    def test_zero_theta_positions(self):
        """测试 Theta 为零的持仓"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            )
        ]
        
        greeks_map = {
            "IO2401-C-4000.CFFEX": GreeksResult(theta=0.0)
        }
        
        metrics = monitor.calculate_portfolio_theta(positions, greeks_map)
        
        assert metrics.total_theta == 0.0
        assert metrics.daily_decay_amount == 0.0
        assert metrics.position_count == 1
    
    def test_mixed_positive_negative_theta(self):
        """测试正负 Theta 混合"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        # 创建卖方和买方持仓
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",  # 卖方，负 Theta
                open_price=0.5,
            ),
            Position(
                vt_symbol="HO2401-C-3000.CFFEX",
                underlying_vt_symbol="IH2401.CFFEX",
                signal="open_signal",
                volume=5,
                direction="long",  # 买方，负 Theta
                open_price=0.6,
            ),
        ]
        
        greeks_map = {
            "IO2401-C-4000.CFFEX": GreeksResult(theta=-0.05),
            "HO2401-C-3000.CFFEX": GreeksResult(theta=-0.03),
        }
        
        metrics = monitor.calculate_portfolio_theta(positions, greeks_map)
        
        # 组合 Theta = (-0.05*10 + -0.03*5) * 10000 = -6500
        expected_theta = (-0.05 * 10 + -0.03 * 5) * 10000
        assert abs(metrics.total_theta - expected_theta) < 1e-6
        assert abs(metrics.daily_decay_amount - abs(expected_theta)) < 1e-6
    
    def test_very_large_theta(self):
        """测试极大的 Theta 值"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=100,
                direction="short",
                open_price=0.5,
            )
        ]
        
        greeks_map = {
            "IO2401-C-4000.CFFEX": GreeksResult(theta=-1.0)  # 极大的 Theta
        }
        
        metrics = monitor.calculate_portfolio_theta(positions, greeks_map)
        
        # 组合 Theta = -1.0 * 100 * 10000 = -1,000,000
        assert abs(metrics.total_theta - (-1000000.0)) < 1e-6
        assert abs(metrics.daily_decay_amount - 1000000.0) < 1e-6
    
    def test_expiry_date_extraction_various_formats(self):
        """测试各种合约代码格式的到期日提取"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        # 测试不同格式的合约代码
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",  # 标准格式
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            ),
            Position(
                vt_symbol="m2509-C-2800.DCE",  # 商品期权格式
                underlying_vt_symbol="m2509.DCE",
                signal="open_signal",
                volume=5,
                direction="short",
                open_price=0.6,
            ),
            Position(
                vt_symbol="HO2312-P-3000.CFFEX",  # 看跌期权
                underlying_vt_symbol="IH2312.CFFEX",
                signal="open_signal",
                volume=8,
                direction="short",
                open_price=0.4,
            ),
        ]
        
        distribution = monitor.calculate_expiry_distribution(positions)
        
        # 应该有三个分组
        assert len(distribution) == 3
        assert "2401" in distribution
        assert "2509" in distribution
        assert "2312" in distribution
    
    def test_custom_expiry_warning_days(self):
        """测试自定义到期提醒天数"""
        config = TimeDecayConfig(
            expiry_warning_days=14,  # 14 天提醒
            critical_expiry_days=5,   # 5 天紧急
        )
        monitor = TimeDecayMonitor(config)
        
        # 当前日期：2024-01-01
        current_date = datetime(2024, 1, 1)
        
        # 创建持仓：到期日 2024-01-10（距离 9 天）
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=10,
                direction="short",
                open_price=0.5,
            )
        ]
        
        expiring = monitor.identify_expiring_positions(positions, current_date)
        
        # 距离 9 天，应该触发警告（< 14 天）
        assert len(expiring) == 1
        assert expiring[0].urgency == "warning"
    
    def test_position_with_zero_volume(self):
        """测试零持仓量的持仓"""
        config = TimeDecayConfig()
        monitor = TimeDecayMonitor(config)
        
        positions = [
            Position(
                vt_symbol="IO2401-C-4000.CFFEX",
                underlying_vt_symbol="IF2401.CFFEX",
                signal="open_signal",
                volume=0,  # 零持仓
                direction="short",
                open_price=0.5,
            )
        ]
        
        greeks_map = {
            "IO2401-C-4000.CFFEX": GreeksResult(theta=-0.05)
        }
        
        # Theta 计算应该排除零持仓
        metrics = monitor.calculate_portfolio_theta(positions, greeks_map)
        assert metrics.total_theta == 0.0
        assert metrics.position_count == 0
        
        # 到期识别应该排除零持仓
        current_date = datetime(2024, 1, 8)
        expiring = monitor.identify_expiring_positions(positions, current_date)
        assert len(expiring) == 0
        
        # 到期分组应该排除零持仓
        distribution = monitor.calculate_expiry_distribution(positions)
        assert len(distribution) == 0
