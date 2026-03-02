"""
AdvancedOrderSchedulerSerializer 属性测试

使用 Hypothesis 验证序列化器的通用正确性属性。
"""
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
import pytest

from src.strategy.infrastructure.persistence.advanced_order_scheduler_serializer import AdvancedOrderSchedulerSerializer
from src.strategy.domain.domain_service.execution.advanced_order_scheduler import AdvancedOrderScheduler
from src.strategy.domain.value_object.trading.order_execution import AdvancedSchedulerConfig
from src.strategy.domain.value_object.trading.order_instruction import OrderInstruction, Direction, Offset, OrderType
from src.strategy.domain.value_object.trading.advanced_order import (
    AdvancedOrder, AdvancedOrderRequest, AdvancedOrderType, AdvancedOrderStatus,
    ChildOrder, SliceEntry
)


# Hypothesis 策略定义

@st.composite
def advanced_scheduler_config_strategy(draw):
    """生成 AdvancedSchedulerConfig 实例"""
    return AdvancedSchedulerConfig(
        default_batch_size=draw(st.integers(min_value=1, max_value=100)),
        default_interval_seconds=draw(st.integers(min_value=10, max_value=600)),
        default_num_slices=draw(st.integers(min_value=1, max_value=20)),
        default_volume_randomize_ratio=draw(st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False)),
        default_price_offset_ticks=draw(st.integers(min_value=0, max_value=10)),
        default_price_tick=draw(st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False)),
    )


@st.composite
def order_instruction_strategy(draw):
    """生成 OrderInstruction 实例"""
    products = ["IO", "MO", "HO", "m", "c"]
    year = draw(st.integers(min_value=24, max_value=29))
    month = draw(st.integers(min_value=1, max_value=12))
    option_type = draw(st.sampled_from(["C", "P"]))
    strike = draw(st.integers(min_value=1000, max_value=10000))
    exchanges = ["CFFEX", "DCE", "CZCE"]
    
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
def child_order_strategy(draw, parent_id):
    """生成 ChildOrder 实例"""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    time_offset = draw(st.integers(min_value=0, max_value=365 * 24 * 3600))
    
    return ChildOrder(
        child_id=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=48, max_codepoint=122))),
        parent_id=parent_id,
        volume=draw(st.integers(min_value=1, max_value=100)),
        scheduled_time=base_time + timedelta(seconds=time_offset) if draw(st.booleans()) else None,
        is_submitted=draw(st.booleans()),
        is_filled=draw(st.booleans()),
        price_offset=draw(st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False)),
    )


@st.composite
def slice_entry_strategy(draw):
    """生成 SliceEntry 实例"""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    time_offset = draw(st.integers(min_value=0, max_value=365 * 24 * 3600))
    
    return SliceEntry(
        scheduled_time=base_time + timedelta(seconds=time_offset),
        volume=draw(st.integers(min_value=1, max_value=100)),
    )


@st.composite
def advanced_order_request_strategy(draw):
    """生成 AdvancedOrderRequest 实例"""
    instruction = draw(order_instruction_strategy())
    
    return AdvancedOrderRequest(
        order_type=draw(st.sampled_from(list(AdvancedOrderType))),
        instruction=instruction,
        batch_size=draw(st.integers(min_value=0, max_value=100)),
        time_window_seconds=draw(st.integers(min_value=0, max_value=3600)),
        num_slices=draw(st.integers(min_value=0, max_value=20)),
        volume_profile=draw(st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False), min_size=0, max_size=10)),
        interval_seconds=draw(st.integers(min_value=0, max_value=600)),
        per_order_volume=draw(st.integers(min_value=0, max_value=100)),
        volume_randomize_ratio=draw(st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False)),
        price_offset_ticks=draw(st.integers(min_value=0, max_value=10)),
        price_tick=draw(st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False)),
    )


@st.composite
def advanced_order_strategy(draw):
    """生成 AdvancedOrder 实例"""
    order_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=48, max_codepoint=122)))
    request = draw(advanced_order_request_strategy())
    
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    time_offset = draw(st.integers(min_value=0, max_value=365 * 24 * 3600))
    
    # 生成 0-3 个子单
    num_children = draw(st.integers(min_value=0, max_value=3))
    child_orders = [draw(child_order_strategy(order_id)) for _ in range(num_children)]
    
    # 生成 0-3 个时间片
    num_slices = draw(st.integers(min_value=0, max_value=3))
    slice_schedule = [draw(slice_entry_strategy()) for _ in range(num_slices)]
    
    return AdvancedOrder(
        order_id=order_id,
        request=request,
        status=draw(st.sampled_from(list(AdvancedOrderStatus))),
        filled_volume=draw(st.integers(min_value=0, max_value=1000)),
        child_orders=child_orders,
        created_time=base_time + timedelta(seconds=time_offset),
        slice_schedule=slice_schedule,
    )


@st.composite
def advanced_order_scheduler_strategy(draw):
    """生成 AdvancedOrderScheduler 实例"""
    config = draw(advanced_scheduler_config_strategy())
    scheduler = AdvancedOrderScheduler(config)
    
    # 生成 0-3 个订单
    num_orders = draw(st.integers(min_value=0, max_value=3))
    for i in range(num_orders):
        order = draw(advanced_order_strategy())
        scheduler._orders[order.order_id] = order
    
    return scheduler


class TestAdvancedOrderSchedulerSerializerProperties:
    """AdvancedOrderSchedulerSerializer 属性测试"""
    
    # Feature: domain-service-infrastructure-refactoring, Property 2: AdvancedOrderScheduler 序列化往返保持等价性
    # **Validates: Requirements 2.5**
    @given(scheduler=advanced_order_scheduler_strategy())
    @settings(max_examples=100, deadline=None)
    def test_roundtrip_preserves_config(self, scheduler):
        """
        属性 2: AdvancedOrderScheduler 序列化往返保持配置等价性
        
        对于任何有效的 AdvancedOrderScheduler 实例，序列化后再反序列化，
        配置参数应该与原实例相同。
        """
        # 序列化
        data = AdvancedOrderSchedulerSerializer.to_dict(scheduler)
        
        # 反序列化
        restored = AdvancedOrderSchedulerSerializer.from_dict(data)
        
        # 验证配置等价性
        assert restored.config.default_batch_size == scheduler.config.default_batch_size
        assert restored.config.default_interval_seconds == scheduler.config.default_interval_seconds
        assert restored.config.default_num_slices == scheduler.config.default_num_slices
        assert abs(restored.config.default_volume_randomize_ratio - scheduler.config.default_volume_randomize_ratio) < 1e-9
        assert restored.config.default_price_offset_ticks == scheduler.config.default_price_offset_ticks
        assert abs(restored.config.default_price_tick - scheduler.config.default_price_tick) < 1e-9
    
    # Feature: domain-service-infrastructure-refactoring, Property 2: AdvancedOrderScheduler 序列化往返保持等价性
    # **Validates: Requirements 2.5**
    @given(scheduler=advanced_order_scheduler_strategy())
    @settings(max_examples=100, deadline=None)
    def test_roundtrip_preserves_order_count(self, scheduler):
        """
        属性 2: AdvancedOrderScheduler 序列化往返保持订单数量
        
        对于任何有效的 AdvancedOrderScheduler 实例，序列化后再反序列化，
        订单数量应该与原实例相同。
        """
        # 序列化
        data = AdvancedOrderSchedulerSerializer.to_dict(scheduler)
        
        # 反序列化
        restored = AdvancedOrderSchedulerSerializer.from_dict(data)
        
        # 验证订单数量
        assert len(restored._orders) == len(scheduler._orders)
    
    # Feature: domain-service-infrastructure-refactoring, Property 2: AdvancedOrderScheduler 序列化往返保持等价性
    # **Validates: Requirements 2.5**
    @given(scheduler=advanced_order_scheduler_strategy())
    @settings(max_examples=100, deadline=None)
    def test_roundtrip_preserves_order_ids(self, scheduler):
        """
        属性 2: AdvancedOrderScheduler 序列化往返保持订单 ID
        
        对于任何有效的 AdvancedOrderScheduler 实例，序列化后再反序列化，
        所有订单 ID 应该保持不变。
        """
        # 序列化
        data = AdvancedOrderSchedulerSerializer.to_dict(scheduler)
        
        # 反序列化
        restored = AdvancedOrderSchedulerSerializer.from_dict(data)
        
        # 验证订单 ID
        assert set(restored._orders.keys()) == set(scheduler._orders.keys())
    
    # Feature: domain-service-infrastructure-refactoring, Property 2: AdvancedOrderScheduler 序列化往返保持等价性
    # **Validates: Requirements 2.5**
    @given(scheduler=advanced_order_scheduler_strategy())
    @settings(max_examples=100, deadline=None)
    def test_roundtrip_preserves_order_details(self, scheduler):
        """
        属性 2: AdvancedOrderScheduler 序列化往返保持订单详情
        
        对于任何有效的 AdvancedOrderScheduler 实例，序列化后再反序列化，
        每个订单的详细信息应该与原实例相同。
        """
        # 序列化
        data = AdvancedOrderSchedulerSerializer.to_dict(scheduler)
        
        # 反序列化
        restored = AdvancedOrderSchedulerSerializer.from_dict(data)
        
        # 验证每个订单的详情
        for oid in scheduler._orders:
            orig_order = scheduler._orders[oid]
            rest_order = restored._orders[oid]
            
            # 验证订单基本信息
            assert rest_order.order_id == orig_order.order_id
            assert rest_order.status == orig_order.status
            assert rest_order.filled_volume == orig_order.filled_volume
            
            # 验证创建时间（精确到秒）
            assert rest_order.created_time.replace(microsecond=0) == orig_order.created_time.replace(microsecond=0)
            
            # 验证请求详情
            assert rest_order.request.order_type == orig_order.request.order_type
            assert rest_order.request.instruction.vt_symbol == orig_order.request.instruction.vt_symbol
            assert rest_order.request.batch_size == orig_order.request.batch_size
            assert rest_order.request.time_window_seconds == orig_order.request.time_window_seconds
    
    # Feature: domain-service-infrastructure-refactoring, Property 2: AdvancedOrderScheduler 序列化往返保持等价性
    # **Validates: Requirements 2.5**
    @given(scheduler=advanced_order_scheduler_strategy())
    @settings(max_examples=100, deadline=None)
    def test_roundtrip_preserves_child_orders(self, scheduler):
        """
        属性 2: AdvancedOrderScheduler 序列化往返保持子单信息
        
        对于任何有效的 AdvancedOrderScheduler 实例，序列化后再反序列化，
        每个订单的子单信息应该与原实例相同。
        """
        # 序列化
        data = AdvancedOrderSchedulerSerializer.to_dict(scheduler)
        
        # 反序列化
        restored = AdvancedOrderSchedulerSerializer.from_dict(data)
        
        # 验证每个订单的子单
        for oid in scheduler._orders:
            orig_order = scheduler._orders[oid]
            rest_order = restored._orders[oid]
            
            # 验证子单数量
            assert len(rest_order.child_orders) == len(orig_order.child_orders)
            
            # 验证每个子单的详情
            for i, orig_child in enumerate(orig_order.child_orders):
                rest_child = rest_order.child_orders[i]
                assert rest_child.child_id == orig_child.child_id
                assert rest_child.parent_id == orig_child.parent_id
                assert rest_child.volume == orig_child.volume
                assert rest_child.is_submitted == orig_child.is_submitted
                assert rest_child.is_filled == orig_child.is_filled
                assert abs(rest_child.price_offset - orig_child.price_offset) < 1e-6
    
    # Feature: domain-service-infrastructure-refactoring, Property 2: AdvancedOrderScheduler 序列化往返保持等价性
    # **Validates: Requirements 2.5**
    @given(scheduler=advanced_order_scheduler_strategy())
    @settings(max_examples=100, deadline=None)
    def test_roundtrip_preserves_slice_schedule(self, scheduler):
        """
        属性 2: AdvancedOrderScheduler 序列化往返保持时间片调度
        
        对于任何有效的 AdvancedOrderScheduler 实例，序列化后再反序列化，
        每个订单的时间片调度应该与原实例相同。
        """
        # 序列化
        data = AdvancedOrderSchedulerSerializer.to_dict(scheduler)
        
        # 反序列化
        restored = AdvancedOrderSchedulerSerializer.from_dict(data)
        
        # 验证每个订单的时间片调度
        for oid in scheduler._orders:
            orig_order = scheduler._orders[oid]
            rest_order = restored._orders[oid]
            
            # 验证时间片数量
            assert len(rest_order.slice_schedule) == len(orig_order.slice_schedule)
            
            # 验证每个时间片的详情
            for i, orig_slice in enumerate(orig_order.slice_schedule):
                rest_slice = rest_order.slice_schedule[i]
                assert rest_slice.volume == orig_slice.volume
                # 验证时间（精确到秒）
                assert rest_slice.scheduled_time.replace(microsecond=0) == orig_slice.scheduled_time.replace(microsecond=0)
    
    # Feature: domain-service-infrastructure-refactoring, Property 2: AdvancedOrderScheduler 序列化往返保持等价性
    # **Validates: Requirements 2.5**
    @given(scheduler=advanced_order_scheduler_strategy())
    @settings(max_examples=100, deadline=None)
    def test_double_roundtrip_stability(self, scheduler):
        """
        属性 2: AdvancedOrderScheduler 双重往返序列化稳定性
        
        对于任何有效的 AdvancedOrderScheduler 实例，进行两次往返序列化，
        结果应该与一次往返序列化相同（幂等性）。
        """
        # 第一次往返
        data1 = AdvancedOrderSchedulerSerializer.to_dict(scheduler)
        restored1 = AdvancedOrderSchedulerSerializer.from_dict(data1)
        
        # 第二次往返
        data2 = AdvancedOrderSchedulerSerializer.to_dict(restored1)
        restored2 = AdvancedOrderSchedulerSerializer.from_dict(data2)
        
        # 验证配置相同
        assert restored2.config.default_batch_size == restored1.config.default_batch_size
        assert restored2.config.default_interval_seconds == restored1.config.default_interval_seconds
        
        # 验证订单数量和 ID 相同
        assert len(restored2._orders) == len(restored1._orders)
        assert set(restored2._orders.keys()) == set(restored1._orders.keys())
    
    # Feature: domain-service-infrastructure-refactoring, Property 2: AdvancedOrderScheduler 序列化往返保持等价性
    # **Validates: Requirements 2.5**
    @given(scheduler=advanced_order_scheduler_strategy())
    @settings(max_examples=100, deadline=None)
    def test_serialized_data_is_json_compatible(self, scheduler):
        """
        属性 2: 序列化数据是 JSON 兼容的
        
        对于任何有效的 AdvancedOrderScheduler 实例，序列化后的数据
        应该是 JSON 兼容的（可以被 json.dumps 处理）。
        """
        import json
        
        # 序列化
        data = AdvancedOrderSchedulerSerializer.to_dict(scheduler)
        
        # 验证可以转换为 JSON 字符串
        json_str = json.dumps(data)
        
        # 验证可以从 JSON 字符串恢复
        restored_data = json.loads(json_str)
        
        # 验证恢复的数据可以反序列化
        restored_scheduler = AdvancedOrderSchedulerSerializer.from_dict(restored_data)
        
        # 验证配置相同
        assert restored_scheduler.config.default_batch_size == scheduler.config.default_batch_size
        assert len(restored_scheduler._orders) == len(scheduler._orders)
