# 需求文档：领域服务基础设施职责分离

## 引言

本需求文档定义了将领域服务层中的基础设施职责提取到基础设施层的重构需求。通过代码审查发现，部分领域服务包含了序列化、合约解析等基础设施层职责，违反了分层架构原则。本次重构旨在保持领域层的纯净性，将技术实现细节下沉到基础设施层。

## 术语表

- **领域服务 (Domain_Service)**: 位于领域层的服务，封装不属于实体或值对象的业务逻辑
- **基础设施层 (Infrastructure_Layer)**: 提供技术能力的层次，包括持久化、序列化、外部系统集成等
- **序列化器 (Serializer)**: 负责将对象转换为可持久化格式（如 JSON、YAML）的组件
- **合约解析器 (Contract_Parser)**: 负责解析合约代码、提取合约信息的工具服务
- **SmartOrderExecutor**: 智能订单执行器领域服务
- **AdvancedOrderScheduler**: 高级订单调度器领域服务
- **ConcentrationMonitor**: 集中度监控领域服务
- **TimeDecayMonitor**: 时间衰减监控领域服务

## 需求

### 需求 1: 提取订单执行器序列化职责

**用户故事:** 作为系统架构师，我希望将 SmartOrderExecutor 的序列化逻辑提取到基础设施层，以便领域服务保持纯净的业务逻辑。

#### 验收标准

1. THE Infrastructure_Layer SHALL 提供 SmartOrderExecutorSerializer 类
2. WHEN 需要序列化 SmartOrderExecutor 状态时，THE SmartOrderExecutorSerializer SHALL 将其转换为字典格式
3. WHEN 需要反序列化时，THE SmartOrderExecutorSerializer SHALL 从字典恢复 SmartOrderExecutor 实例
4. THE SmartOrderExecutor SHALL 移除 to_dict、from_dict、from_yaml_config 方法
5. FOR ALL 有效的 SmartOrderExecutor 实例，序列化后反序列化 SHALL 产生等价的对象（往返属性）

### 需求 2: 提取订单调度器序列化职责

**用户故事:** 作为系统架构师，我希望将 AdvancedOrderScheduler 的序列化逻辑提取到基础设施层，以便统一管理序列化策略。

#### 验收标准

1. THE Infrastructure_Layer SHALL 提供 AdvancedOrderSchedulerSerializer 类
2. WHEN 需要序列化 AdvancedOrderScheduler 状态时，THE AdvancedOrderSchedulerSerializer SHALL 将其转换为字典格式
3. WHEN 需要反序列化时，THE AdvancedOrderSchedulerSerializer SHALL 从字典恢复 AdvancedOrderScheduler 实例
4. THE AdvancedOrderScheduler SHALL 移除 to_dict、from_dict、from_yaml_config 方法
5. FOR ALL 有效的 AdvancedOrderScheduler 实例，序列化后反序列化 SHALL 产生等价的对象（往返属性）

### 需求 3: 提取合约代码解析职责

**用户故事:** 作为系统架构师，我希望将合约代码解析逻辑集中到基础设施层，以便复用解析逻辑并便于维护。

#### 验收标准

1. THE Infrastructure_Layer SHALL 扩展现有的 ContractHelper 类，增加到期日提取和行权价分组方法
2. WHEN 提供合约代码时，THE ContractHelper SHALL 提取到期日信息（如 "2401", "2509"）
3. WHEN 提供合约代码时，THE ContractHelper SHALL 将行权价分组到合理区间（如 "4000-4100"）
4. THE ConcentrationMonitor SHALL 使用 ContractHelper 替代内部的 _extract_expiry_from_symbol 和 _group_by_strike_range 方法
5. THE TimeDecayMonitor SHALL 使用 ContractHelper 替代内部的 _extract_expiry_from_symbol 方法
6. FOR ALL 有效的合约代码，解析逻辑 SHALL 返回一致的结果

### 需求 4: 提取日期计算职责

**用户故事:** 作为系统架构师，我希望将日期计算逻辑提取到基础设施层工具类，以便在多个服务间复用。

#### 验收标准

1. THE Infrastructure_Layer SHALL 提供 DateCalculator 工具类
2. WHEN 提供到期日字符串和当前日期时，THE DateCalculator SHALL 计算距离到期的天数
3. THE DateCalculator SHALL 支持 YYMM 格式的到期日字符串（如 "2401", "2509"）
4. THE TimeDecayMonitor SHALL 使用 DateCalculator 替代内部的 _calculate_days_to_expiry 方法
5. FOR ALL 有效的日期输入，计算结果 SHALL 准确无误

### 需求 5: 保持领域服务接口稳定

**用户故事:** 作为应用层开发者，我希望领域服务的公共接口保持不变，以便重构不影响现有调用代码。

#### 验收标准

1. THE SmartOrderExecutor SHALL 保持所有公共业务方法的签名不变
2. THE AdvancedOrderScheduler SHALL 保持所有公共业务方法的签名不变
3. THE ConcentrationMonitor SHALL 保持所有公共业务方法的签名不变
4. THE TimeDecayMonitor SHALL 保持所有公共业务方法的签名不变
5. WHEN 应用层调用领域服务时，THE 领域服务 SHALL 返回与重构前相同的结果

### 需求 6: 配置加载适配

**用户故事:** 作为系统运维人员，我希望从 YAML 配置文件加载领域服务配置的功能继续可用，以便保持现有的配置管理方式。

#### 验收标准

1. THE Infrastructure_Layer SHALL 提供配置加载器，支持从 YAML 字典创建领域服务实例
2. WHEN 提供 YAML 配置字典时，THE 配置加载器 SHALL 创建正确配置的 SmartOrderExecutor 实例
3. WHEN 提供 YAML 配置字典时，THE 配置加载器 SHALL 创建正确配置的 AdvancedOrderScheduler 实例
4. THE 配置加载器 SHALL 对缺失的配置项使用默认值
5. FOR ALL 有效的 YAML 配置，加载后的实例 SHALL 具有正确的配置参数

### 需求 7: 测试覆盖保持

**用户故事:** 作为质量保证工程师，我希望重构后的代码保持原有的测试覆盖率，以便确保功能正确性。

#### 验收标准

1. THE 重构后的代码 SHALL 通过所有现有的单元测试
2. THE 重构后的代码 SHALL 通过所有现有的属性测试
3. THE 重构后的代码 SHALL 通过所有现有的集成测试
4. WHEN 运行测试套件时，THE 测试覆盖率 SHALL 不低于重构前的水平
5. THE 新增的基础设施层组件 SHALL 具有相应的单元测试

### 需求 8: 文档更新

**用户故事:** 作为开发团队成员，我希望重构后的代码有清晰的文档说明，以便理解新的架构设计。

#### 验收标准

1. THE 新增的序列化器类 SHALL 包含清晰的类文档字符串
2. THE 扩展的 ContractHelper 类 SHALL 包含新增方法的文档说明
3. THE DateCalculator 类 SHALL 包含使用示例和参数说明
4. THE 重构后的领域服务 SHALL 更新文档字符串，说明职责变化
5. THE 代码注释 SHALL 解释关键的设计决策
