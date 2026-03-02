"""
SmartOrderExecutorSerializer 单元测试

测试序列化器的基本功能、边界条件和错误处理。
"""
import pytest
from datetime import datetime

from src.strategy.infrastructure.persistence.smart_order_executor_serializer import SmartOrderExecutorSerializer
from src.strategy.domain.domain_service.execution.smart_order_executor import SmartOrderExecutor
from src.strategy.domain.value_object.trading.order_execution import OrderExecutionConfig, ManagedOrder
from src.strategy.domain.value_object.trading.order_instruction import OrderInstruction, Direction, Offset, OrderType


class TestSmartOrderExecutorSerializer:
    """SmartOrderExecutorSerializer 单元测试"""
    
    def test_serialize_basic_executor(self):
        """测试基本序列化"""
        config = OrderExecutionConfig(
            timeout_seconds=30,
            max_retries=3,
            slippage_ticks=2,
            price_tick=0.2
        )
        executor = SmartOrderExecutor(config)
        
        data = SmartOrderExecutorSerializer.to_dict(executor)
        
        assert data["config"]["timeout_seconds"] == 30
        assert data["config"]["max_retries"] == 3
        assert data["config"]["slippage_ticks"] == 2
        assert data["config"]["price_tick"] == 0.2
        assert data["orders"] == {}
    
    def test_deserialize_basic_executor(self):
        """测试基本反序列化"""
        data = {
            "config": {
                "timeout_seconds": 30,
                "max_retries": 3,
                "slippage_ticks": 2,
                "price_tick": 0.2
            },
            "orders": {}
        }
        
        executor = SmartOrderExecutorSerializer.from_dict(data)
        
        assert executor.config.timeout_seconds == 30
        assert executor.config.max_retries == 3
        assert executor.config.slippage_ticks == 2
        assert executor.config.price_tick == 0.2
        assert len(executor._orders) == 0
    
    def test_serialize_executor_with_orders(self):
        """测试包含订单的序列化"""
        config = OrderExecutionConfig()
        executor = SmartOrderExecutor(config)
        
        # 注册订单
        instruction = OrderInstruction(
            vt_symbol="IO2401-C-4000.CFFEX",
            direction=Direction.LONG,
            offset=Offset.OPEN,
            volume=10,
            price=100.0,
            signal="test_signal",
            order_type=OrderType.LIMIT
        )
        executor.register_order("order_001", instruction)
        
        data = SmartOrderExecutorSerializer.to_dict(executor)
        
        assert "order_001" in data["orders"]
        order_data = data["orders"]["order_001"]
        assert order_data["vt_orderid"] == "order_001"
        assert order_data["instruction"]["vt_symbol"] == "IO2401-C-4000.CFFEX"
        assert order_data["instruction"]["volume"] == 10
        assert order_data["is_active"] is True
    
    def test_deserialize_executor_with_orders(self):
        """测试包含订单的反序列化"""
        data = {
            "config": {
                "timeout_seconds": 30,
                "max_retries": 3,
                "slippage_ticks": 2,
                "price_tick": 0.2
            },
            "orders": {
                "order_001": {
                    "vt_orderid": "order_001",
                    "instruction": {
                        "vt_symbol": "IO2401-C-4000.CFFEX",
                        "direction": "long",
                        "offset": "open",
                        "volume": 10,
                        "price": 100.0,
                        "signal": "test_signal",
                        "order_type": "limit"
                    },
                    "submit_time": "2024-01-15T10:30:00",
                    "retry_count": 0,
                    "is_active": True
                }
            }
        }
        
        executor = SmartOrderExecutorSerializer.from_dict(data)
        
        assert len(executor._orders) == 1
        assert "order_001" in executor._orders
        order = executor._orders["order_001"]
        assert order.vt_orderid == "order_001"
        assert order.instruction.vt_symbol == "IO2401-C-4000.CFFEX"
        assert order.instruction.volume == 10
        assert order.is_active is True
    
    def test_roundtrip_serialization(self):
        """测试往返序列化"""
        config = OrderExecutionConfig(
            timeout_seconds=60,
            max_retries=5,
            slippage_ticks=3,
            price_tick=0.5
        )
        executor = SmartOrderExecutor(config)
        
        # 注册多个订单
        for i in range(3):
            instruction = OrderInstruction(
                vt_symbol=f"IO2401-C-{4000 + i * 100}.CFFEX",
                direction=Direction.LONG if i % 2 == 0 else Direction.SHORT,
                offset=Offset.OPEN,
                volume=10 + i,
                price=100.0 + i * 10,
                signal=f"signal_{i}",
                order_type=OrderType.LIMIT
            )
            executor.register_order(f"order_{i:03d}", instruction)
        
        # 序列化
        data = SmartOrderExecutorSerializer.to_dict(executor)
        
        # 反序列化
        restored = SmartOrderExecutorSerializer.from_dict(data)
        
        # 验证配置
        assert restored.config.timeout_seconds == executor.config.timeout_seconds
        assert restored.config.max_retries == executor.config.max_retries
        assert restored.config.slippage_ticks == executor.config.slippage_ticks
        assert restored.config.price_tick == executor.config.price_tick
        
        # 验证订单
        assert len(restored._orders) == len(executor._orders)
        for oid in executor._orders:
            assert oid in restored._orders
            orig_order = executor._orders[oid]
            rest_order = restored._orders[oid]
            assert rest_order.vt_orderid == orig_order.vt_orderid
            assert rest_order.instruction.vt_symbol == orig_order.instruction.vt_symbol
            assert rest_order.instruction.volume == orig_order.instruction.volume
            assert rest_order.is_active == orig_order.is_active
    
    def test_deserialize_with_missing_config_fields(self):
        """测试缺失配置字段的默认值处理"""
        data = {
            "config": {
                "timeout_seconds": 45
                # 其他字段缺失
            },
            "orders": {}
        }
        
        executor = SmartOrderExecutorSerializer.from_dict(data)
        
        # 验证提供的字段
        assert executor.config.timeout_seconds == 45
        
        # 验证缺失字段使用默认值
        defaults = OrderExecutionConfig()
        assert executor.config.max_retries == defaults.max_retries
        assert executor.config.slippage_ticks == defaults.slippage_ticks
        assert executor.config.price_tick == defaults.price_tick
    
    def test_deserialize_with_empty_config(self):
        """测试空配置使用默认值"""
        data = {
            "config": {},
            "orders": {}
        }
        
        executor = SmartOrderExecutorSerializer.from_dict(data)
        
        # 所有字段应使用默认值
        defaults = OrderExecutionConfig()
        assert executor.config.timeout_seconds == defaults.timeout_seconds
        assert executor.config.max_retries == defaults.max_retries
        assert executor.config.slippage_ticks == defaults.slippage_ticks
        assert executor.config.price_tick == defaults.price_tick
    
    def test_deserialize_with_provided_config(self):
        """测试使用提供的配置对象"""
        config = OrderExecutionConfig(
            timeout_seconds=100,
            max_retries=10,
            slippage_ticks=5,
            price_tick=1.0
        )
        
        data = {
            "config": {
                "timeout_seconds": 30,  # 这个会被忽略
                "max_retries": 3
            },
            "orders": {}
        }
        
        executor = SmartOrderExecutorSerializer.from_dict(data, config=config)
        
        # 应使用提供的配置对象
        assert executor.config.timeout_seconds == 100
        assert executor.config.max_retries == 10
        assert executor.config.slippage_ticks == 5
        assert executor.config.price_tick == 1.0
    
    def test_serialize_none_executor_raises_error(self):
        """测试序列化 None 抛出错误"""
        with pytest.raises(ValueError, match="executor cannot be None"):
            SmartOrderExecutorSerializer.to_dict(None)
    
    def test_deserialize_none_data_raises_error(self):
        """测试反序列化 None 抛出错误"""
        with pytest.raises(ValueError, match="data cannot be None"):
            SmartOrderExecutorSerializer.from_dict(None)
    
    def test_deserialize_missing_orders_key(self):
        """测试缺失 orders 键"""
        data = {
            "config": {
                "timeout_seconds": 30
            }
            # orders 键缺失
        }
        
        executor = SmartOrderExecutorSerializer.from_dict(data)
        
        # 应该创建空的订单字典
        assert len(executor._orders) == 0
    
    def test_serialize_executor_with_inactive_orders(self):
        """测试包含非活跃订单的序列化"""
        config = OrderExecutionConfig()
        executor = SmartOrderExecutor(config)
        
        # 注册订单并标记为已成交
        instruction = OrderInstruction(
            vt_symbol="IO2401-C-4000.CFFEX",
            direction=Direction.LONG,
            offset=Offset.OPEN,
            volume=10,
            price=100.0,
            signal="test_signal",
            order_type=OrderType.LIMIT
        )
        executor.register_order("order_001", instruction)
        executor.mark_order_filled("order_001")
        
        data = SmartOrderExecutorSerializer.to_dict(executor)
        
        # 验证非活跃状态被正确序列化
        assert data["orders"]["order_001"]["is_active"] is False
        
        # 反序列化并验证
        restored = SmartOrderExecutorSerializer.from_dict(data)
        assert restored._orders["order_001"].is_active is False
