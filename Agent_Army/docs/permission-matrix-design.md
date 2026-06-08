# Agent Army 权限矩阵设计

> **版本**: v2.0（8部门制）
> **日期**: 2026-03-20
> **方案**: Plan B - 自己实现，不依赖OpenClaw

---

## 一、权限矩阵概述

### 1.1 核心概念

权限矩阵定义**谁可以调用谁**，确保系统安全性和职责分离。

```
核心原则：
1. 总司令可以调用任何部门
2. 部门之间不能互相调用（防止混乱）
3. 业务Agent不能调用管理层Agent
4. 跨部门调用必须经过总司令
```

### 1.2 架构层级

```
层级0: 投资者（用户）
   ↓ 只能调用
层级1: 总司令
   ↓ 可以调用
层级2: 8个部门
   ↓ 内部调用
层级3: 业务Agent（24个）
```

---

## 二、完整权限矩阵

### 2.1 权限矩阵表

| 调用者 | 总司令 | 研究部 | 分析部 | 预测部 | 策略部 | 验证部 | 监控部 | 优化部 | 配置部 |
|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| **投资者** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **总司令** | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **研究部** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **分析部** | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **预测部** | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **策略部** | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **验证部** | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **监控部** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **优化部** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **配置部** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

**说明**：
- ✅ = 允许调用
- ❌ = 禁止调用
- `-` = 不适用

### 2.2 权限规则详解

#### 规则1：投资者只能调用总司令

```python
# ✅ 允许
investor → commander

# ❌ 禁止
investor → research_department
investor → analysis_department
# ... 等等
```

#### 规则2：总司令可以调用任何部门

```python
# ✅ 全部允许
commander → research_department
commander → analysis_department
commander → prediction_department
commander → strategy_department
commander → validation_department
commander → monitoring_department
commander → optimization_department
commander → configuration_department
```

#### 规则3：部门之间不能互相调用

```python
# ❌ 禁止
research_department → analysis_department
analysis_department → prediction_department
prediction_department → strategy_department
# ... 等等

# 部门内部调用除外
research_department.agent1 → research_department.agent2  # ✅ 允许
```

#### 规则4：部门可以回调总司令

```python
# ✅ 允许（用于汇报结果）
research_department → commander
analysis_department → commander
prediction_department → commander
# ... 等等
```

---

## 三、权限检查实现

### 3.1 权限矩阵数据结构

```python
PERMISSION_MATRIX = {
    'investor': {
        'can_call': ['commander'],
        'description': '投资者只能调用总司令'
    },

    'commander': {
        'can_call': [
            'research_department',
            'analysis_department',
            'prediction_department',
            'strategy_department',
            'validation_department',
            'monitoring_department',
            'optimization_department',
            'configuration_department'
        ],
        'description': '总司令可以调用任何部门'
    },

    'research_department': {
        'can_call': ['commander', 'research_department'],
        'description': '研究部可以回调总司令和内部调用'
    },

    'analysis_department': {
        'can_call': ['commander', 'analysis_department'],
        'description': '分析部可以回调总司令和内部调用'
    },

    'prediction_department': {
        'can_call': ['commander', 'prediction_department'],
        'description': '预测部可以回调总司令和内部调用'
    },

    'strategy_department': {
        'can_call': ['commander', 'strategy_department'],
        'description': '策略部可以回调总司令和内部调用'
    },

    'validation_department': {
        'can_call': ['commander', 'validation_department'],
        'description': '验证部可以回调总司令和内部调用'
    },

    'monitoring_department': {
        'can_call': ['commander', 'monitoring_department'],
        'description': '监控部可以回调总司令和内部调用'
    },

    'optimization_department': {
        'can_call': ['commander', 'optimization_department'],
        'description': '优化部可以回调总司令和内部调用'
    },

    'configuration_department': {
        'can_call': ['commander', 'configuration_department'],
        'description': '配置部可以回调总司令和内部调用'
    }
}
```

### 3.2 权限检查器

```python
class PermissionChecker:
    """权限检查器"""

    def __init__(self):
        self.matrix = PERMISSION_MATRIX

    def can_call(self, caller: str, callee: str) -> bool:
        """
        检查caller是否可以调用callee

        Args:
            caller: 调用者（如 'commander', 'research_department'）
            callee: 被调用者

        Returns:
            True 如果允许调用，False 如果禁止
        """
        # 获取caller的权限列表
        caller_permissions = self.matrix.get(caller)
        if not caller_permissions:
            return False

        # 检查callee是否在允许列表中
        allowed_calls = caller_permissions['can_call']
        return callee in allowed_calls

    def check_call(self, caller: str, callee: str) -> bool:
        """
        检查调用权限，如果不允许则抛出异常

        Args:
            caller: 调用者
            callee: 被调用者

        Returns:
            True 如果允许

        Raises:
            PermissionError: 如果不允许调用
        """
        if not self.can_call(caller, callee):
            raise PermissionError(
                f"权限拒绝: {caller} 不能调用 {callee}"
            )

        return True

    def get_permissions(self, caller: str) -> list:
        """
        获取caller的权限列表

        Args:
            caller: 调用者

        Returns:
            允许调用的对象列表
        """
        caller_permissions = self.matrix.get(caller)
        if not caller_permissions:
            return []

        return caller_permissions['can_call']
```

### 3.3 使用示例

```python
# 创建权限检查器
checker = PermissionChecker()

# 检查权限
if checker.can_call('commander', 'research_department'):
    print("✅ 总司令可以调用研究部")
else:
    print("❌ 总司令不能调用研究部")

# 检查权限（带异常）
try:
    checker.check_call('research_department', 'analysis_department')
    print("✅ 研究部可以调用分析部")
except PermissionError as e:
    print(f"❌ {e}")

# 获取权限列表
permissions = checker.get_permissions('commander')
print(f"总司令可以调用: {', '.join(permissions)}")
```

---

## 四、Agent级别权限

### 4.1 部门内部Agent权限

每个部门内部的Agent也可以调用同部门的其他Agent。

```python
# 研究部内部权限
RESEARCH_DEPARTMENT_INTERNAL = {
    '产业链研究AI': {
        'can_call': ['宏观政策研究AI']
    },
    '宏观政策研究AI': {
        'can_call': ['产业链研究AI']
    }
}

# 分析部内部权限
ANALYSIS_DEPARTMENT_INTERNAL = {
    '基本面分析AI': {
        'can_call': ['估值分析AI', '历史分析AI']
    },
    '估值分析AI': {
        'can_call': ['基本面分析AI', '历史分析AI']
    },
    '历史分析AI': {
        'can_call': ['基本面分析AI', '估值分析AI']
    }
}
```

### 4.2 完整权限检查

```python
def check_full_permission(
    caller: str,
    callee: str,
    checker: PermissionChecker
) -> bool:
    """
    完整的权限检查（包括部门内部）

    Args:
        caller: 调用者（可以是部门或具体Agent）
        callee: 被调用者
        checker: 权限检查器

    Returns:
        True 如果允许调用
    """
    # 1. 先检查部门级别权限
    caller_dept = extract_department(caller)
    callee_dept = extract_department(callee)

    if caller_dept != callee_dept:
        # 跨部门调用，检查矩阵权限
        return checker.can_call(caller_dept, callee_dept)
    else:
        # 同部门调用，检查内部权限
        return check_internal_permission(caller, callee)
```

---

## 五、特殊权限

### 5.1 紧急停止权限

```python
# 总司令有紧急停止权限
EMERGENCY_STOP_PERMISSION = {
    'commander': ['*'],  # 可以停止任何任务
    'description': '总司令可以紧急停止任何正在运行的任务'
}
```

### 5.2 质量审核权限

```python
# 只有总司令可以质量审核
QUALITY_REVIEW_PERMISSION = {
    'allowed': ['commander'],
    'description': '只有总司令可以审核分析质量'
}
```

### 5.3 报告生成权限

```python
# 只有总司令可以生成最终报告
REPORT_GENERATION_PERMISSION = {
    'allowed': ['commander'],
    'description': '只有总司令可以汇总并生成最终报告'
}
```

---

## 六、权限验证流程

### 6.1 调用流程

```
┌─────────────┐
│ 调用者发起   │
│ 调用请求     │
└──────┬──────┘
       ↓
┌─────────────┐
│ 权限检查器   │
│ 检查矩阵     │
└──────┬──────┘
       ↓
    ┌──┴──┐
    ↓     ↓
  允许   禁止
    ↓     ↓
 执行   抛出
 调用   异常
```

### 6.2 权限检查装饰器

```python
def require_permission(callee: str):
    """
    权限检查装饰器

    使用示例：
    @require_permission('research_department')
    async def call_research_department(self):
        # 只有有权限的调用者才能执行
        pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # 获取调用者
            caller = self.name

            # 检查权限
            checker = PermissionChecker()
            if not checker.can_call(caller, callee):
                raise PermissionError(
                    f"权限拒绝: {caller} 不能调用 {callee}"
                )

            # 执行函数
            return await func(self, *args, **kwargs)

        return wrapper
    return decorator
```

---

## 七、权限配置管理

### 7.1 配置文件格式

```json
{
  "version": "2.0",
  "permission_matrix": {
    "investor": {
      "can_call": ["commander"],
      "description": "投资者只能调用总司令"
    },
    "commander": {
      "can_call": [
        "research_department",
        "analysis_department",
        "prediction_department",
        "strategy_department",
        "validation_department",
        "monitoring_department",
        "optimization_department",
        "configuration_department"
      ],
      "description": "总司令可以调用任何部门"
    }
  }
}
```

### 7.2 动态加载权限

```python
class PermissionManager:
    """权限管理器"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.matrix = PERMISSION_MATRIX

        if config_path:
            self.load_from_file(config_path)

    def load_from_file(self, path: str):
        """从配置文件加载权限"""
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            self.matrix = config['permission_matrix']

    def save_to_file(self, path: str):
        """保存权限到配置文件"""
        config = {
            'version': '2.0',
            'permission_matrix': self.matrix
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
```

---

## 八、安全最佳实践

### 8.1 权限最小化原则

```
只给予必要的最小权限

示例：
- 监控部不需要调用预测部
- 优化部不需要调用策略部
- 验证部不需要调用研究部
```

### 8.2 审计日志

```python
class PermissionAuditLogger:
    """权限审计日志"""

    def __init__(self):
        self.logger = logging.getLogger('permission_audit')

    def log_call(self, caller: str, callee: str, allowed: bool):
        """记录调用日志"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'caller': caller,
            'callee': callee,
            'allowed': allowed,
            'ip': get_client_ip()
        }

        self.logger.info(json.dumps(log_data))
```

### 8.3 权限变更通知

```python
def notify_permission_change(
    old_matrix: dict,
    new_matrix: dict
):
    """权限变更通知"""
    changes = diff_permission_matrix(old_matrix, new_matrix)

    if changes:
        send_notification(
            title="权限矩阵已更新",
            message=f"变更内容: {changes}",
            level="warning"
        )
```

---

## 九、测试用例

### 9.1 权限检查测试

```python
import pytest

def test_commander_can_call_any_department():
    """测试总司令可以调用任何部门"""
    checker = PermissionChecker()

    departments = [
        'research_department',
        'analysis_department',
        'prediction_department',
        'strategy_department',
        'validation_department',
        'monitoring_department',
        'optimization_department',
        'configuration_department'
    ]

    for dept in departments:
        assert checker.can_call('commander', dept)

def test_department_cannot_call_other_department():
    """测试部门不能互相调用"""
    checker = PermissionChecker()

    assert not checker.can_call('research_department', 'analysis_department')
    assert not checker.can_call('analysis_department', 'prediction_department')
    assert not checker.can_call('prediction_department', 'strategy_department')

def test_investor_can_only_call_commander():
    """测试投资者只能调用总司令"""
    checker = PermissionChecker()

    assert checker.can_call('investor', 'commander')
    assert not checker.can_call('investor', 'research_department')
```

---

**创建时间**: 2026-03-20
**设计师**: Claude
**版本**: v2.0（8部门制）
**状态**: 已完成
