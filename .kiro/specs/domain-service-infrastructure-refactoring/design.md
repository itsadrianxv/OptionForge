# 设计文档：领域服务基础设施职责分离

## 概述

本设计文档描述了将领域服务层中的基础设施职责提取到基础设施层的重构方案。当前代码审查发现，SmartOrderExecutor、AdvancedOrderScheduler、ConcentrationMonitor 和 TimeDecayMonitor 等领域服务包含了序列化、合约解析、日期计算等基础设施层职责，违反了分层架构原则。

### 重构目标

1. **职责分离**: 将技术实现细节从领域层移至基础设施层
2. **接口稳定**: 保持领域服务的公共接口不变，确保应用层代码无需修改
3. **可复用性**: 基础设施组件可在多个领域服务间复用
4. **可测试性**: 保持现有测试覆盖率，新增组件具有独立测试

### 架构原则

- **依赖倒置**: 领域层不依赖基础设施层的具体实现
- **单一职责**: 每个组件只负责一个明确的职责
- **开闭原则**: 对扩展开放，对修改封闭

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Application)                  │
│                                                          │
│  - 使用领域服务的公共接口                                 │
│  - 不感知基础设施层的变化                                 │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    领域层 (Domain)                       │
│                                                          │
│  领域服务 (纯业务逻辑):                                   │
│  - SmartOrderExecutor: 价格计算、超时管理、重试逻辑       │
│  - AdvancedOrderScheduler: 拆单逻辑、子单生命周期         │
│  - ConcentrationMonitor: 集中度计算、HHI 计算            │
│  - TimeDecayMonitor: Theta 计算、到期识别                │
│                                                          │
│  移除的职责:                                              │
│  ✗ 序列化/反序列化                                        │
│  ✗ 合约代码解析                                           │
│  ✗ 日期计算                                               │
│  ✗ YAML 配置加载                                          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 基础设施层 (Infrastructure)               │
│                                                          │
│  新增/扩展组件:                                           │
│  - SmartOrderExecutorSerializer                         │
│  - AdvancedOrderSchedulerSerializer                     │
│  - ContractHelper (扩展)                                │
│  - DateCalculator                                       │
│  - DomainServiceConfigLoader                            │
└─────────────────────────────────────────────────────────┘
```

### 重构策略

采用**适配器模式**和**工厂模式**实现职责分离：

1. **序列化器 (Serializer)**: 使用适配器模式，将领域对象转换为可持久化格式
2. **配置加载器 (Config Loader)**: 使用工厂模式，从配置创建领域服务实例
3. **工具类 (Helper/Calculator)**: 提供纯函数的技术能力

## 组件和接口

### 1. SmartOrderExecutorSerializer

**位置**: `src/strategy/infrastructure/persistence/smart_order_executor_serializer.py`

**职责**: 负责 SmartOrderExecutor 的序列化和反序列化

**接口设计**:

```python
from typing import Dict, Any, Optional
from src.strategy.domain.domain_service.execution.smart_order_executor import SmartOrderExecutor
from src.strategy.domain.value_object.trading.order_execution import OrderExecutionConfig

class SmartOrderExecutorSerializer:
    """SmartOrderExecutor 序列化器"""
    
    @staticmethod
    def to_dict(executor: SmartOrderExecutor) -> Dict[str, Any]:
        """
        将 SmartOrderExecutor 序列化为字典
        
        Args:
            executor: SmartOrderExecutor 实例
            
        Returns:
            JSON 兼容的字典
        """
        pass
    
    @staticmethod
    def from_dict(
        data: Dict[str, Any],
        config: Optional[OrderExecutionConfig] = None
    ) -> SmartOrderExecutor:
        """
        从字典反序列化 SmartOrderExecutor
        
        Args:
            data: 序列化的字典数据
            config: 可选的配置对象，如果为 None 则从 data 中读取
            
        Returns:
            SmartOrderExecutor 实例
        """
        pass
```

**实现要点**:

- 序列化配置对象的所有字段
- 序列化 `_orders` 字典中的所有 ManagedOrder
- 反序列化时正确恢复对象状态
- 处理缺失字段，使用默认值

### 2. AdvancedOrderSchedulerSerializer

**位置**: `src/strategy/infrastructure/persistence/advanced_order_scheduler_serializer.py`

**职责**: 负责 AdvancedOrderScheduler 的序列化和反序列化

**接口设计**:

```python
from typing import Dict, Any, Optional
from src.strategy.domain.domain_service.execution.advanced_order_scheduler import AdvancedOrderScheduler
from src.strategy.domain.value_object.trading.order_execution import AdvancedSchedulerConfig

class AdvancedOrderSchedulerSerializer:
    """AdvancedOrderScheduler 序列化器"""
    
    @staticmethod
    def to_dict(scheduler: AdvancedOrderScheduler) -> Dict[str, Any]:
        """
        将 AdvancedOrderScheduler 序列化为字典
        
        Args:
            scheduler: AdvancedOrderScheduler 实例
            
        Returns:
            JSON 兼容的字典
        """
        pass
    
    @staticmethod
    def from_dict(
        data: Dict[str, Any],
        config: Optional[AdvancedSchedulerConfig] = None
    ) -> AdvancedOrderScheduler:
        """
        从字典反序列化 AdvancedOrderScheduler
        
        Args:
            data: 序列化的字典数据
            config: 可选的配置对象，如果为 None 则从 data 中读取
            
        Returns:
            AdvancedOrderScheduler 实例
        """
        pass
```

**实现要点**:

- 序列化配置对象的所有字段
- 序列化 `_orders` 字典中的所有 AdvancedOrder
- 正确处理 AdvancedOrder 的复杂结构（子单、时间片等）
- 反序列化时恢复完整的订单状态

### 3. ContractHelper (扩展)

**位置**: `src/strategy/infrastructure/parsing/contract_helper.py`

**职责**: 扩展现有的 ContractHelper，增加到期日提取和行权价分组方法

**新增接口**:

```python
class ContractHelper:
    # ... 现有方法 ...
    
    @staticmethod
    def extract_expiry_from_symbol(vt_symbol: str) -> str:
        """
        从合约代码中提取到期日
        
        期权合约格式示例: "IO2401-C-4000.CFFEX", "m2509-C-2800.DCE"
        提取年月部分作为到期日标识
        
        Args:
            vt_symbol: 合约代码
            
        Returns:
            到期日字符串（如 "2401", "2509"），解析失败返回 "unknown"
            
        Examples:
            >>> ContractHelper.extract_expiry_from_symbol("IO2401-C-4000.CFFEX")
            "2401"
            >>> ContractHelper.extract_expiry_from_symbol("m2509-C-2800.DCE")
            "2509"
        """
        pass
    
    @staticmethod
    def group_by_strike_range(vt_symbol: str) -> str:
        """
        将行权价分组到区间
        
        期权合约格式示例: "IO2401-C-4000.CFFEX", "m2509-C-2800.DCE"
        根据行权价大小自动确定区间宽度：
        - 行权价 < 1000: 区间宽度 100
        - 1000 <= 行权价 < 5000: 区间宽度 500
        - 行权价 >= 5000: 区间宽度 1000
        
        Args:
            vt_symbol: 合约代码
            
        Returns:
            行权价区间字符串（如 "4000-4500", "2800-2900"），解析失败返回 "unknown"
            
        Examples:
            >>> ContractHelper.group_by_strike_range("IO2401-C-4000.CFFEX")
            "4000-4500"
            >>> ContractHelper.group_by_strike_range("m2509-C-2800.DCE")
            "2500-3000"
        """
        pass
```

**实现要点**:

- 使用正则表达式提取年月部分（YYMM 格式）
- 使用正则表达式提取行权价
- 根据行权价大小动态确定区间宽度
- 处理异常情况，返回 "unknown"
- 保持与现有方法的一致性

### 4. DateCalculator

**位置**: `src/strategy/infrastructure/utils/date_calculator.py`

**职责**: 提供日期计算工具方法

**接口设计**:

```python
from datetime import datetime
from typing import Optional

class DateCalculator:
    """日期计算工具类"""
    
    @staticmethod
    def calculate_days_to_expiry(
        expiry_date_str: str,
        current_date: datetime
    ) -> Optional[int]:
        """
        计算距离到期天数
        
        Args:
            expiry_date_str: 到期日字符串（YYMM 格式，如 "2401", "2509"）
            current_date: 当前日期
            
        Returns:
            距离到期天数，解析失败返回 None
            
        Examples:
            >>> from datetime import datetime
            >>> DateCalculator.calculate_days_to_expiry("2401", datetime(2023, 12, 1))
            45  # 假设到期日是 2024-01-15
        """
        pass
    
    @staticmethod
    def parse_expiry_date(expiry_date_str: str) -> Optional[datetime]:
        """
        解析到期日字符串为 datetime 对象
        
        Args:
            expiry_date_str: 到期日字符串（YYMM 格式）
            
        Returns:
            datetime 对象（假设到期日是该月的第三个星期五），解析失败返回 None
            
        Note:
            期权标准到期日是每月第三个星期五，简化实现使用该月 15 日作为近似
        """
        pass
```

**实现要点**:

- 解析 YYMM 格式的到期日字符串
- 假设到期日是该月的 15 日（简化实现）
- 计算当前日期到到期日的天数差
- 处理异常情况，返回 None

### 5. DomainServiceConfigLoader

**位置**: `src/main/config/domain_service_config_loader.py` (扩展现有文件)

**职责**: 从 YAML 配置创建领域服务实例

**新增接口**:

```python
from typing import Dict, Any
from src.strategy.domain.domain_service.execution.smart_order_executor import SmartOrderExecutor
from src.strategy.domain.domain_service.execution.advanced_order_scheduler import AdvancedOrderScheduler
from src.strategy.domain.value_object.trading.order_execution import (
    OrderExecutionConfig,
    AdvancedSchedulerConfig
)

class DomainServiceConfigLoader:
    # ... 现有方法 ...
    
    @staticmethod
    def create_smart_order_executor(config_dict: Dict[str, Any]) -> SmartOrderExecutor:
        """
        从 YAML 配置字典创建 SmartOrderExecutor 实例
        
        Args:
            config_dict: YAML 配置字典
            
        Returns:
            SmartOrderExecutor 实例
            
        Note:
            缺失的配置项使用 OrderExecutionConfig 的默认值
        """
        pass
    
    @staticmethod
    def create_advanced_order_scheduler(config_dict: Dict[str, Any]) -> AdvancedOrderScheduler:
        """
        从 YAML 配置字典创建 AdvancedOrderScheduler 实例
        
        Args:
            config_dict: YAML 配置字典
            
        Returns:
            AdvancedOrderScheduler 实例
            
        Note:
            缺失的配置项使用 AdvancedSchedulerConfig 的默认值
        """
        pass
```

**实现要点**:

- 从配置字典中提取配置参数
- 使用默认值处理缺失的配置项
- 创建配置对象
- 使用配置对象创建领域服务实例

## 数据模型

### 序列化数据格式

#### SmartOrderExecutor 序列化格式

```json
{
  "config": {
    "timeout_seconds": 30,
    "max_retries": 3,
    "slippage_ticks": 2,
    "price_tick": 0.2
  },
  "orders": {
    "order_id_1": {
      "vt_orderid": "order_id_1",
      "instruction": { /* OrderInstruction 字典 */ },
      "submit_time": "2024-01-15T10:30:00",
      "is_active": true,
      "retry_count": 0
    }
  }
}
```

#### AdvancedOrderScheduler 序列化格式

```json
{
  "config": {
    "default_batch_size": 10,
    "default_interval_seconds": 60,
    "default_num_slices": 5,
    "default_volume_randomize_ratio": 0.1,
    "default_price_offset_ticks": 2,
    "default_price_tick": 0.2
  },
  "orders": {
    "order_id_1": {
      "order_id": "order_id_1",
      "request": { /* AdvancedOrderRequest 字典 */ },
      "status": "EXECUTING",
      "child_orders": [ /* ChildOrder 列表 */ ],
      "filled_volume": 0,
      "slice_schedule": [ /* SliceEntry 列表 */ ]
    }
  }
}
```

### 配置数据格式

#### SmartOrderExecutor YAML 配置

```yaml
timeout_seconds: 30
max_retries: 3
slippage_ticks: 2
price_tick: 0.2
```

#### AdvancedOrderScheduler YAML 配置

```yaml
default_batch_size: 10
default_interval_seconds: 60
default_num_slices: 5
default_volume_randomize_ratio: 0.1
default_price_offset_ticks: 2
default_price_tick: 0.2
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*


### 属性 1: SmartOrderExecutor 序列化往返保持等价性

*对于任何*有效的 SmartOrderExecutor 实例，使用 SmartOrderExecutorSerializer 序列化后再反序列化，应该产生与原实例等价的对象（配置参数相同，订单状态相同）。

**验证需求**: 1.5

### 属性 2: AdvancedOrderScheduler 序列化往返保持等价性

*对于任何*有效的 AdvancedOrderScheduler 实例，使用 AdvancedOrderSchedulerSerializer 序列化后再反序列化，应该产生与原实例等价的对象（配置参数相同，订单状态相同，子单状态相同）。

**验证需求**: 2.5

### 属性 3: 合约代码到期日提取正确性

*对于任何*符合期权合约格式的 vt_symbol（包含 YYMM 格式的年月信息），ContractHelper.extract_expiry_from_symbol 应该正确提取出 YYMM 格式的到期日字符串。

**验证需求**: 3.2, 4.3

### 属性 4: 合约代码行权价分组正确性

*对于任何*符合期权合约格式的 vt_symbol（包含行权价信息），ContractHelper.group_by_strike_range 应该将行权价分组到正确的区间，且行权价应该落在返回的区间范围内。

**验证需求**: 3.3

### 属性 5: 合约解析幂等性

*对于任何*有效的合约代码，多次调用 ContractHelper 的解析方法（extract_expiry_from_symbol 或 group_by_strike_range）应该返回相同的结果。

**验证需求**: 3.6

### 属性 6: 日期计算正确性

*对于任何*有效的 YYMM 格式到期日字符串和当前日期，DateCalculator.calculate_days_to_expiry 计算的天数应该等于手动计算的天数差（假设到期日为该月 15 日）。

**验证需求**: 4.2, 4.5

### 属性 7: 配置加载正确性

*对于任何*有效的 YAML 配置字典（可能包含部分或全部配置项），DomainServiceConfigLoader 创建的领域服务实例应该：
1. 对于配置字典中存在的配置项，实例的配置参数应该与配置字典中的值相同
2. 对于配置字典中缺失的配置项，实例的配置参数应该使用默认值

**验证需求**: 6.2, 6.3, 6.4, 6.5

## 错误处理

### 序列化器错误处理

**SmartOrderExecutorSerializer**:
- 输入验证：检查 executor 参数是否为 None
- 数据完整性：确保所有必需字段都存在
- 类型错误：捕获并记录类型转换错误
- 返回值：序列化失败时抛出 SerializationError 异常

**AdvancedOrderSchedulerSerializer**:
- 输入验证：检查 scheduler 参数是否为 None
- 复杂对象处理：正确处理嵌套的 AdvancedOrder、ChildOrder 等对象
- 日期时间序列化：正确处理 datetime 对象的序列化和反序列化
- 返回值：序列化失败时抛出 SerializationError 异常

### 解析器错误处理

**ContractHelper**:
- 格式验证：检查合约代码格式是否符合预期
- 正则匹配失败：返回 "unknown" 而不是抛出异常
- 日志记录：记录警告信息以便调试
- 容错性：对于无法解析的合约代码，返回默认值而不是中断程序

### 日期计算错误处理

**DateCalculator**:
- 格式验证：检查到期日字符串是否为 YYMM 格式
- 日期有效性：验证年月是否有效（月份 1-12）
- 异常捕获：捕获 datetime 构造异常
- 返回值：计算失败时返回 None

### 配置加载错误处理

**DomainServiceConfigLoader**:
- 配置验证：检查配置字典是否为有效的字典类型
- 类型转换：处理配置值的类型转换错误
- 默认值回退：配置项缺失或无效时使用默认值
- 日志记录：记录配置加载过程中的警告和错误

## 测试策略

### 双重测试方法

本重构项目采用单元测试和属性测试相结合的策略：

**单元测试**:
- 验证具体的序列化/反序列化示例
- 测试边界条件和特殊情况
- 验证错误处理逻辑
- 测试与现有代码的集成

**属性测试**:
- 验证序列化往返属性（属性 1, 2）
- 验证解析逻辑的正确性和一致性（属性 3, 4, 5）
- 验证日期计算的准确性（属性 6）
- 验证配置加载的正确性（属性 7）
- 每个属性测试运行至少 100 次迭代

### 测试框架选择

- **单元测试框架**: pytest
- **属性测试框架**: Hypothesis
- **测试覆盖率工具**: pytest-cov

### 测试组织

```
tests/
├── strategy/
│   ├── infrastructure/
│   │   ├── persistence/
│   │   │   ├── test_smart_order_executor_serializer.py  # 单元测试
│   │   │   ├── test_smart_order_executor_serializer_properties.py  # 属性测试
│   │   │   ├── test_advanced_order_scheduler_serializer.py  # 单元测试
│   │   │   └── test_advanced_order_scheduler_serializer_properties.py  # 属性测试
│   │   ├── parsing/
│   │   │   ├── test_contract_helper_extension.py  # 单元测试
│   │   │   └── test_contract_helper_properties.py  # 属性测试
│   │   └── utils/
│   │       ├── test_date_calculator.py  # 单元测试
│   │       └── test_date_calculator_properties.py  # 属性测试
│   └── domain/
│       └── domain_service/
│           ├── test_execution_refactoring_integration.py  # 集成测试
│           └── test_risk_refactoring_integration.py  # 集成测试
└── main/
    └── config/
        ├── test_domain_service_config_loader.py  # 单元测试
        └── test_domain_service_config_loader_properties.py  # 属性测试
```

### 属性测试配置

每个属性测试必须：
1. 使用 `@given` 装饰器定义输入生成策略
2. 配置至少 100 次迭代：`@settings(max_examples=100)`
3. 使用注释标记对应的设计属性：
   ```python
   # Feature: domain-service-infrastructure-refactoring, Property 1: SmartOrderExecutor 序列化往返保持等价性
   ```

### 回归测试策略

为确保重构不破坏现有功能：

1. **保留现有测试**: 所有现有的单元测试、属性测试和集成测试必须继续通过
2. **行为等价性验证**: 通过集成测试验证重构前后的行为一致性
3. **性能基准**: 确保序列化/反序列化性能不低于原实现
4. **测试覆盖率**: 重构后的测试覆盖率不低于重构前

### 测试数据生成策略

**Hypothesis 策略定义**:

```python
from hypothesis import strategies as st
from datetime import datetime, timedelta

# SmartOrderExecutor 生成策略
@st.composite
def smart_order_executor_strategy(draw):
    config = OrderExecutionConfig(
        timeout_seconds=draw(st.integers(min_value=10, max_value=300)),
        max_retries=draw(st.integers(min_value=0, max_value=10)),
        slippage_ticks=draw(st.integers(min_value=0, max_value=10)),
        price_tick=draw(st.floats(min_value=0.01, max_value=1.0)),
    )
    return SmartOrderExecutor(config)

# 合约代码生成策略
@st.composite
def option_contract_symbol_strategy(draw):
    # 生成符合格式的期权合约代码
    product = draw(st.sampled_from(["IO", "MO", "HO", "m", "c"]))
    year = draw(st.integers(min_value=24, max_value=29))
    month = draw(st.integers(min_value=1, max_value=12))
    option_type = draw(st.sampled_from(["C", "P"]))
    strike = draw(st.integers(min_value=1000, max_value=10000))
    exchange = draw(st.sampled_from(["CFFEX", "DCE", "CZCE"]))
    return f"{product}{year:02d}{month:02d}-{option_type}-{strike}.{exchange}"

# YYMM 格式到期日生成策略
@st.composite
def expiry_date_str_strategy(draw):
    year = draw(st.integers(min_value=24, max_value=29))
    month = draw(st.integers(min_value=1, max_value=12))
    return f"{year:02d}{month:02d}"

# 配置字典生成策略（可能缺失某些字段）
@st.composite
def partial_config_dict_strategy(draw):
    config_dict = {}
    if draw(st.booleans()):
        config_dict["timeout_seconds"] = draw(st.integers(min_value=10, max_value=300))
    if draw(st.booleans()):
        config_dict["max_retries"] = draw(st.integers(min_value=0, max_value=10))
    if draw(st.booleans()):
        config_dict["slippage_ticks"] = draw(st.integers(min_value=0, max_value=10))
    if draw(st.booleans()):
        config_dict["price_tick"] = draw(st.floats(min_value=0.01, max_value=1.0))
    return config_dict
```

### 集成测试策略

**测试场景**:

1. **序列化集成测试**: 验证序列化器与持久化服务的集成
2. **配置加载集成测试**: 验证配置加载器与应用启动流程的集成
3. **领域服务集成测试**: 验证重构后的领域服务与应用层的集成
4. **端到端测试**: 验证完整的业务流程（从配置加载到订单执行）

**测试数据**:

- 使用真实的配置文件进行测试
- 使用真实的合约代码格式
- 模拟真实的业务场景

## 实施计划

### 阶段 1: 基础设施层组件开发

1. 创建 `SmartOrderExecutorSerializer`
2. 创建 `AdvancedOrderSchedulerSerializer`
3. 扩展 `ContractHelper`（添加 `extract_expiry_from_symbol` 和 `group_by_strike_range`）
4. 创建 `DateCalculator`
5. 扩展 `DomainServiceConfigLoader`

### 阶段 2: 单元测试和属性测试

1. 为每个新组件编写单元测试
2. 为每个正确性属性编写属性测试
3. 确保所有测试通过

### 阶段 3: 领域服务重构

1. 修改 `SmartOrderExecutor`：移除 `to_dict`、`from_dict`、`from_yaml_config` 方法
2. 修改 `AdvancedOrderScheduler`：移除 `to_dict`、`from_dict`、`from_yaml_config` 方法
3. 修改 `ConcentrationMonitor`：使用 `ContractHelper` 替代内部方法
4. 修改 `TimeDecayMonitor`：使用 `ContractHelper` 和 `DateCalculator` 替代内部方法

### 阶段 4: 集成测试和回归测试

1. 运行所有现有测试，确保通过
2. 编写集成测试验证重构后的行为
3. 检查测试覆盖率

### 阶段 5: 文档更新

1. 更新所有新增组件的文档字符串
2. 更新重构后的领域服务文档
3. 添加使用示例和迁移指南

## 迁移指南

### 应用层代码迁移

**重要**: 应用层代码无需修改，因为领域服务的公共接口保持不变。

### 序列化代码迁移

**重构前**:
```python
# 序列化
executor = SmartOrderExecutor(config)
data = executor.to_dict()

# 反序列化
executor = SmartOrderExecutor.from_dict(data)
```

**重构后**:
```python
from src.strategy.infrastructure.persistence.smart_order_executor_serializer import SmartOrderExecutorSerializer

# 序列化
executor = SmartOrderExecutor(config)
data = SmartOrderExecutorSerializer.to_dict(executor)

# 反序列化
executor = SmartOrderExecutorSerializer.from_dict(data)
```

### 配置加载代码迁移

**重构前**:
```python
# 从 YAML 配置创建实例
config_dict = yaml.safe_load(config_file)
executor = SmartOrderExecutor.from_yaml_config(config_dict)
```

**重构后**:
```python
from src.main.config.domain_service_config_loader import DomainServiceConfigLoader

# 从 YAML 配置创建实例
config_dict = yaml.safe_load(config_file)
executor = DomainServiceConfigLoader.create_smart_order_executor(config_dict)
```

### 合约解析代码迁移

**重构前**:
```python
# ConcentrationMonitor 内部
expiry = self._extract_expiry_from_symbol(vt_symbol)
strike_range = self._group_by_strike_range(vt_symbol)
```

**重构后**:
```python
from src.strategy.infrastructure.parsing.contract_helper import ContractHelper

# ConcentrationMonitor 内部
expiry = ContractHelper.extract_expiry_from_symbol(vt_symbol)
strike_range = ContractHelper.group_by_strike_range(vt_symbol)
```

### 日期计算代码迁移

**重构前**:
```python
# TimeDecayMonitor 内部
days = self._calculate_days_to_expiry(expiry_str, current_date)
```

**重构后**:
```python
from src.strategy.infrastructure.utils.date_calculator import DateCalculator

# TimeDecayMonitor 内部
days = DateCalculator.calculate_days_to_expiry(expiry_str, current_date)
```

## 风险和缓解措施

### 风险 1: 序列化格式不兼容

**描述**: 新的序列化器可能无法正确反序列化旧格式的数据

**缓解措施**:
- 在序列化器中添加版本检测逻辑
- 提供数据迁移工具
- 保留向后兼容性

### 风险 2: 性能下降

**描述**: 新的实现可能导致序列化/反序列化性能下降

**缓解措施**:
- 进行性能基准测试
- 优化关键路径
- 使用缓存减少重复计算

### 风险 3: 测试覆盖不足

**描述**: 重构可能引入未被测试覆盖的边界情况

**缓解措施**:
- 使用属性测试覆盖大量随机输入
- 增加边界条件的单元测试
- 进行代码审查

### 风险 4: 集成问题

**描述**: 新组件可能与现有系统集成时出现问题

**缓解措施**:
- 编写全面的集成测试
- 在测试环境中充分验证
- 采用渐进式部署策略

## 设计决策记录

### 决策 1: 使用静态方法而非实例方法

**背景**: 序列化器和工具类可以设计为实例方法或静态方法

**决策**: 使用静态方法

**理由**:
- 序列化器和工具类不需要维护状态
- 静态方法更简单，无需实例化
- 符合函数式编程风格，易于测试

### 决策 2: 扩展现有 ContractHelper 而非创建新类

**背景**: 可以创建新的 ContractParser 类或扩展现有的 ContractHelper

**决策**: 扩展现有的 ContractHelper

**理由**:
- ContractHelper 已经包含合约解析逻辑
- 避免创建功能重复的类
- 保持代码组织的一致性

### 决策 3: 日期计算使用简化实现

**背景**: 期权到期日是每月第三个星期五，计算复杂

**决策**: 使用该月 15 日作为近似

**理由**:
- 简化实现，降低复杂度
- 对于风险监控场景，几天的误差可接受
- 可以在未来需要时优化为精确计算

### 决策 4: 配置加载器放在 main/config 而非 infrastructure

**背景**: 配置加载器可以放在基础设施层或应用层

**决策**: 放在 main/config 目录

**理由**:
- 配置加载是应用启动的一部分
- 与现有的配置加载代码保持一致
- 便于应用层使用

### 决策 5: 保持领域服务接口不变

**背景**: 可以修改领域服务的公共接口以适应新设计

**决策**: 保持公共接口不变

**理由**:
- 最小化对应用层的影响
- 降低重构风险
- 符合开闭原则

## 参考资料

### 设计模式

- **适配器模式**: 用于序列化器，将领域对象适配为可持久化格式
- **工厂模式**: 用于配置加载器，从配置创建领域服务实例
- **策略模式**: 可用于未来扩展不同的序列化策略

### 架构原则

- **分层架构**: 清晰的层次划分，职责分离
- **依赖倒置原则**: 高层模块不依赖低层模块
- **单一职责原则**: 每个类只有一个变化的理由
- **开闭原则**: 对扩展开放，对修改封闭

### 相关文档

- [领域驱动设计 (DDD)](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [分层架构模式](https://www.oreilly.com/library/view/software-architecture-patterns/9781491971437/ch01.html)
- [属性测试最佳实践](https://hypothesis.readthedocs.io/en/latest/quickstart.html)
