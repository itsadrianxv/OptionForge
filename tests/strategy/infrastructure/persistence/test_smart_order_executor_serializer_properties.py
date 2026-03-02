"""
SmartOrderExecutorSerializer 属性测试

使用 Hypothesis 验证序列化器的通用正确性属性。
"""
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
import pytest

from src.strategy.infrastructure.persistence.smart_order_executor_serializer import SmartOrderExecutorSerializer
from src.strategy.domain.domain_service.execution.smart_order_executor import SmartOrderExecutor
from src.strategy.domain.value_object.trading.order_execution import OrderExecutionConfig, ManagedOrder
from src.strategy.domain.value_object.trading.order_instruction import OrderInstruction, Direction, Offset, OrderType


# Hypothesis 策略定义

@st.composite
def order_execution_config_strategy(draw):
    """生成 OrderExecutionConfig 实例"""
    return OrderExecutionConfig(
        timeout_seconds=draw(st.integers(min_value=10, max_value=300)),
        max_retries=draw(st.integers(min_value=0, max_value=10)),
        slippage_ticks=draw(st.integers(min_value=0, max_value=10)),
        price_tick=draw(st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False)),
    )


@st.composite
def order_instruction_strategy(draw):
    """生成 OrderInstruction 实例"""
    products = ["IO", "MO", "HO", "m", "c", "SR", "CF"]
    year = draw(st.integers(min_value=24, max_value=29))
    month = draw(st.integers(min_value=1, max_value=12))
    option_type = draw(st.sampled_from(["C", "P"]))
    strike = draw(st.integers(min_value=1000, max_value=10000))
    exchanges = ["CFFEX", "DCE", "CZCE", "SHFE"]
    
    vt_symbol = f"{draw(st.sampled_from(products))}{year:02d}{month:02d}-{option_type}-{strike}.{draw(st.sampled_from(exchanges))}"
    
    return OrderInstruction(
        vt_symbol=vt_symbol,
        direction=draw(st.sampled_from([Direction.LONG, Direction.SHORT])),
        offset=draw(st.sampled_from([Offset.OPEN, Offset.CLOSE])),
        volume=draw(st.integers(min_value=1, max_value=1000)),
        price=draw(st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False)),
        signal=draw(st.text(min_size=0, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126))),
        order_type=draw(st.sampled_from([OrderType.LIMIT, OrderType.MARKET])),
    )


@st.composite
def managed_order_strategy(draw):
    """生成 ManagedOrder 实例"""
    instruction = draw(order_instruction_strategy())
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    time_offset = draw(st.integers(min_value=0, max_value=365 * 24 * 3600))
    
    return ManagedOrder(
        vt_orderid=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=48, max_codepoint=122))),
        instruction=instruction,
        submit_time=base_time + timedelta(seconds=time_offset),
        retry_count=draw(st.integers(min_value=0, max_value=10)),
        is_active=draw(st.booleans()),
    )


@st.composite
def smart_order_executor_strategy(draw):
    """生成 SmartOrderExecutor 实例"""
    config = draw(order_execution_config_strategy())
    executor = SmartOrderExecutor(config)
    
    # 生成 0-5 个订单
    num_orders = draw(st.integers(min_value=0, max_value=5))
    for i in range(num_orders):
        order = draw(managed_order_strategy())
        executor._orders[order.vt_orderid] = order
    
    return executor


class TestSmartOrderExecutorSerializerProperties:
    """SmartOrderExecutorSerializer 属性测试"""
    
    # Feature: domain-service-infrastructure-refactoring, Property 1: SmartOrderExecutor 序列化往返保持等价性
    # **Validates: Requirements 1.5**
    @given(executor=smart_order_executor_strategy())
    @settings(max_examples=100, deadline=None)
    def test_roundtrip_preserves_config(self, executor):
        """
        属性 1: SmartOrderExecutor 序列化往返保持配置等价性
        
        对于任何有效的 SmartOrderExecutor 实例，序列化后再反序列化，
        配置参数应该与原实例相同。
        """
        # 序列化
        data = SmartOrderExecutorSerializer.to_dict(executor)
        
        # 反序列化
        restored = SmartOrderExecutorSerializer.from_dict(data)
        
        # 验证配置等价性
        assert restored.config.timeout_seconds == executor.config.timeout_seconds
        assert restored.config.max_retries == executor.config.max_retries
        assert restored.config.slippage_ticks == executor.config.slippage_ticks
        assert abs(restored.config.price_tick - executor.config.price_tick) < 1e-9
    
    # Feature: domain-service-infrastructure-refactoring, Property 1: SmartOrderExecutor 序列化往返保持等价性
    # **Validates: Requirements 1.5**
    @given(executor=smart_order_executor_strategy())
    @settings(max_examples=100, deadline=None)
    def test_roundtrip_preserves_order_count(self, executor):
        """
        属性 1: SmartOrderExecutor 序列化往返保持订单数量
        
        对于任何有效的 SmartOrderExecutor 实例，序列化后再反序列化，
        订单数量应该与原实例相同。
        """
        # 序列化
        data = SmartOrderExecutorSerializer.to_dict(executor)
        
        # 反序列化
        restored = SmartOrderExecutorSerializer.from_dict(data)
        
        # 验证订单数量
        assert len(restored._orders) == len(executor._orders)
    
    # Feature: domain-service-infrastructure-refactoring, Property 1: SmartOrderExecutor 序列化往返保持等价性
    # **Validates: Requirements 1.5**
    @given(executor=smart_order_executor_strategy())
    @settings(max_examples=100, deadline=None)
    def test_roundtrip_preserves_order_ids(self, executor):
        """
        属性 1: SmartOrderExecutor 序列化往返保持订单 ID
        
        对于任何有效的 SmartOrderExecutor 实例，序列化后再反序列化，
        所有订单 ID 应该保持不变。
        """
        # 序列化
        data = SmartOrderExecutorSerializer.to_dict(executor)
        
        # 反序列化
        restored = SmartOrderExecutorSerializer.from_dict(data)
        
        # 验证订单 ID
        assert set(restored._orders.keys()) == set(executor._orders.keys())
    
    # Feature: domain-service-infrastructure-refactoring, Property 1: SmartOrderExecutor 序列化往返保持等价性
    # **Validates: Requirements 1.5**
    @given(executor=smart_order_executor_strategy())
    @settings(max_examples=100, deadline=None)
    def test_roundtrip_preserves_order_details(self, executor):
        """
        属性 1: SmartOrderExecutor 序列化往返保持订单详情
        
        对于任何有效的 SmartOrderExecutor 实例，序列化后再反序列化，
        每个订单的详细信息应该与原实例相同。
        """
        # 序列化
        data = SmartOrderExecutorSerializer.to_dict(executor)
        
        # 反序列化
        restored = SmartOrderExecutorSerializer.from_dict(data)
        
        # 验证每个订单的详情
        for oid in executor._orders:
            orig_order = executor._orders[oid]
            rest_order = restored._orders[oid]
            
            # 验证订单基本信息
            assert rest_order.vt_orderid == orig_order.vt_orderid
            assert rest_order.retry_count == orig_order.retry_count
            assert rest_order.is_active == orig_order.is_active
            
            # 验证提交时间（精确到秒）
            assert rest_order.submit_time.replace(microsecond=0) == orig_order.submit_time.replace(microsecond=0)
            
            # 验证指令详情
            assert rest_order.instruction.vt_symbol == orig_order.instruction.vt_symbol
            assert rest_order.instruction.direction == orig_order.instruction.direction
            assert rest_order.instruction.offset == orig_order.instruction.offset
            assert rest_order.instruction.volume == orig_order.instruction.volume
            assert abs(rest_order.instruction.price - orig_order.instruction.price) < 1e-6
            assert rest_order.instruction.signal == orig_order.instruction.signal
            assert rest_order.instruction.order_type == orig_order.instruction.order_type
    
    # Feature: domain-service-infrastructure-refactoring, Property 1: SmartOrderExecutor 序列化往返保持等价性
    # **Validates: Requirements 1.5**
    @given(executor=smart_order_executor_strategy())
    @settings(max_examples=100, deadline=None)
    def test_double_roundtrip_stability(self, executor):
        """
        属性 1: SmartOrderExecutor 双重往返序列化稳定性
        
        对于任何有效的 SmartOrderExecutor 实例，进行两次往返序列化，
        结果应该与一次往返序列化相同（幂等性）。
        """
        # 第一次往返
        data1 = SmartOrderExecutorSerializer.to_dict(executor)
        restored1 = SmartOrderExecutorSerializer.from_dict(data1)
        
        # 第二次往返
        data2 = SmartOrderExecutorSerializer.to_dict(restored1)
        restored2 = SmartOrderExecutorSerializer.from_dict(data2)
        
        # 验证配置相同
        assert restored2.config.timeout_seconds == restored1.config.timeout_seconds
        assert restored2.config.max_retries == restored1.config.max_retries
        assert restored2.config.slippage_ticks == restored1.config.slippage_ticks
        assert abs(restored2.config.price_tick - restored1.config.price_tick) < 1e-9
        
        # 验证订单数量和 ID 相同
        assert len(restored2._orders) == len(restored1._orders)
        assert set(restored2._orders.keys()) == set(restored1._orders.keys())
    
    # Feature: domain-service-infrastructure-refactoring, Property 1: SmartOrderExecutor 序列化往返保持等价性
    # **Validates: Requirements 1.5**
    @given(
        config=order_execution_config_strategy(),
        partial_config=st.dictionaries(
            keys=st.sampled_from(["timeout_seconds", "max_retries", "slippage_ticks", "price_tick"]),
            values=st.one_of(
                st.integers(min_value=10, max_value=300),
                st.integers(min_value=0, max_value=10),
                st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False)
            ),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_partial_config_uses_defaults(self, config, partial_config):
        """
        属性 1: 部分配置使用默认值
        
        对于任何部分配置字典（可能缺失某些字段），反序列化后的实例
        应该对缺失字段使用默认值。
        """
        data = {
            "config": partial_config,
            "orders": {}
        }
        
        executor = SmartOrderExecutorSerializer.from_dict(data)
        defaults = OrderExecutionConfig()
        
        # 验证提供的字段使用配置值，缺失的字段使用默认值
        if "timeout_seconds" in partial_config:
            assert executor.config.timeout_seconds == partial_config["timeout_seconds"]
        else:
            assert executor.config.timeout_seconds == defaults.timeout_seconds
        
        if "max_retries" in partial_config:
            assert executor.config.max_retries == partial_config["max_retries"]
        else:
            assert executor.config.max_retries == defaults.max_retries
        
        if "slippage_ticks" in partial_config:
            assert executor.config.slippage_ticks == partial_config["slippage_ticks"]
        else:
            assert executor.config.slippage_ticks == defaults.slippage_ticks
        
        if "price_tick" in partial_config:
            assert abs(executor.config.price_tick - partial_config["price_tick"]) < 1e-9
        else:
            assert abs(executor.config.price_tick - defaults.price_tick) < 1e-9
    
    # Feature: domain-service-infrastructure-refactoring, Property 1: SmartOrderExecutor 序列化往返保持等价性
    # **Validates: Requirements 1.5**
    @given(executor=smart_order_executor_strategy())
    @settings(max_examples=100, deadline=None)
    def test_serialized_data_is_json_compatible(self, executor):
        """
        属性 1: 序列化数据是 JSON 兼容的
        
        对于任何有效的 SmartOrderExecutor 实例，序列化后的数据
        应该是 JSON 兼容的（可以被 json.dumps 处理）。
        """
        import json
        
        # 序列化
        data = SmartOrderExecutorSerializer.to_dict(executor)
        
        # 验证可以转换为 JSON 字符串
        json_str = json.dumps(data)
        
        # 验证可以从 JSON 字符串恢复
        restored_data = json.loads(json_str)
        
        # 验证恢复的数据可以反序列化
        restored_executor = SmartOrderExecutorSerializer.from_dict(restored_data)
        
        # 验证配置相同
        assert restored_executor.config.timeout_seconds == executor.config.timeout_seconds
        assert len(restored_executor._orders) == len(executor._orders)
