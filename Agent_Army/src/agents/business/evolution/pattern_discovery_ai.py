"""
Pattern Discovery AI - 发现新的投资模式
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path
from collections import defaultdict

from src.core.base_agent import BaseAgent, AgentCapability
from src.core.logger import LoggerMixin


class PatternDiscoveryAI(BaseAgent, LoggerMixin):
    """
    模式发现AI

    职责：
    1. 从成功案例中发现新的投资模式
    2. 从失败案例中识别风险模式
    3. 验证模式有效性
    4. 模式入库和检索
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.pattern_db_path = Path(config.get("pattern_db_path", "data/pattern_db.json"))
        self.pattern_db_path.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(
            name="Pattern Discovery AI",
            role="发现和验证投资模式",
            capabilities=[
                AgentCapability(
                    name="discover_patterns",
                    description="从经验库中发现模式",
                    input_type="experience_database",
                    output_type="pattern_list"
                ),
                AgentCapability(
                    name="verify_pattern",
                    description="验证模式有效性",
                    input_type="pattern",
                    output_type="verification_result"
                ),
                AgentCapability(
                    name="search_patterns",
                    description="搜索相关模式",
                    input_type="search_criteria",
                    output_type="matched_patterns"
                ),
            ]
        )

        self.pattern_db = self._load_pattern_db()
        self.discovery_history = []

        self.logger.info(f"Pattern Discovery AI initialized")
        self.logger.info(f"Pattern DB: {self.pattern_db_path}")
        self.logger.info(f"Total patterns: {len(self.pattern_db)}")

    async def discover_patterns(
        self,
        experience_cases: List[Dict[str, Any]],
        min_support: int = 3
    ) -> List[Dict[str, Any]]:
        """
        从经验库中发现模式

        Args:
            experience_cases: 经验案例列表
            min_support: 最小支持度（至少出现几次才算模式）

        Returns:
            发现的模式列表
        """
        self.logger.info(f"Discovering patterns from {len(experience_cases)} cases (min_support={min_support})")

        # 分离成功和失败案例
        success_cases = [c for c in experience_cases if c.get("case_type") == "success"]
        failure_cases = [c for c in experience_cases if c.get("case_type") == "failure"]

        self.logger.info(f"Success cases: {len(success_cases)}, Failure cases: {len(failure_cases)}")

        patterns = []

        # 从成功案例中发现盈利模式
        if len(success_cases) >= min_support:
            success_patterns = self._discover_success_patterns(success_cases, min_support)
            patterns.extend(success_patterns)

        # 从失败案例中发现风险模式
        if len(failure_cases) >= min_support:
            failure_patterns = self._discover_failure_patterns(failure_cases, min_support)
            patterns.extend(failure_patterns)

        # 记录发现历史
        self.discovery_history.append({
            "discovery_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_cases": len(experience_cases),
            "patterns_found": len(patterns),
            "success_patterns": sum(1 for p in patterns if p.get("pattern_type") == "success"),
            "failure_patterns": sum(1 for p in patterns if p.get("pattern_type") == "failure")
        })

        self.logger.info(f"Pattern discovery completed: {len(patterns)} patterns found")

        return patterns

    def _discover_success_patterns(
        self,
        success_cases: List[Dict[str, Any]],
        min_support: int
    ) -> List[Dict[str, Any]]:
        """从成功案例中发现盈利模式"""
        patterns = []

        # 模式1: 低PB高ROE模式
        low_pb_high_roe = [
            c for c in success_cases
            if c.get("dimensions", {}).get("fundamental", {}).get("pb", 999) < 1.0
            and c.get("dimensions", {}).get("fundamental", {}).get("roe", 0) > 10
        ]
        if len(low_pb_high_roe) >= min_support:
            avg_accuracy = sum(c.get("actual_result", {}).get("accuracy", 0) for c in low_pb_high_roe) / len(low_pb_high_roe)
            patterns.append({
                "pattern_id": f"success_low_pb_high_roe_{datetime.now().strftime('%Y%m%d')}",
                "pattern_name": "低PB高ROE盈利模式",
                "pattern_type": "success",
                "description": "PB<1.0 且 ROE>10% 的股票表现优异",
                "conditions": {
                    "pb_max": 1.0,
                    "roe_min": 10
                },
                "support": len(low_pb_high_roe),
                "confidence": avg_accuracy,
                "examples": [c["record_id"] for c in low_pb_high_roe[:3]],
                "discovered_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        # 模式2: 政策支持模式
        policy_supported = [
            c for c in success_cases
            if c.get("dimensions", {}).get("policy", {}).get("support", False) is True
        ]
        if len(policy_supported) >= min_support:
            avg_accuracy = sum(c.get("actual_result", {}).get("accuracy", 0) for c in policy_supported) / len(policy_supported)
            patterns.append({
                "pattern_id": f"success_policy_supported_{datetime.now().strftime('%Y%m%d')}",
                "pattern_name": "政策支持盈利模式",
                "pattern_type": "success",
                "description": "有政策支持的股票表现更好",
                "conditions": {
                    "policy_support": True
                },
                "support": len(policy_supported),
                "confidence": avg_accuracy,
                "examples": [c["record_id"] for c in policy_supported[:3]],
                "discovered_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        # 模式3: 技术面突破模式
        breakthrough = [
            c for c in success_cases
            if c.get("dimensions", {}).get("technical", {}).get("trend") == "up"
        ]
        if len(breakthrough) >= min_support:
            avg_accuracy = sum(c.get("actual_result", {}).get("accuracy", 0) for c in breakthrough) / len(breakthrough)
            patterns.append({
                "pattern_id": f"success_technical_breakthrough_{datetime.now().strftime('%Y%m%d')}",
                "pattern_name": "技术面突破盈利模式",
                "pattern_type": "success",
                "description": "趋势向上的股票更容易成功",
                "conditions": {
                    "trend": "up"
                },
                "support": len(breakthrough),
                "confidence": avg_accuracy,
                "examples": [c["record_id"] for c in breakthrough[:3]],
                "discovered_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        return patterns

    def _discover_failure_patterns(
        self,
        failure_cases: List[Dict[str, Any]],
        min_support: int
    ) -> List[Dict[str, Any]]:
        """从失败案例中发现风险模式"""
        patterns = []

        # 模式1: 高PB低ROE风险
        high_pb_low_roe = [
            c for c in failure_cases
            if c.get("dimensions", {}).get("fundamental", {}).get("pb", 0) > 2.0
            and c.get("dimensions", {}).get("fundamental", {}).get("roe", 999) < 8
        ]
        if len(high_pb_low_roe) >= min_support:
            avg_deviation = sum(c.get("actual_result", {}).get("deviation", 0) for c in high_pb_low_roe) / len(high_pb_low_roe)
            patterns.append({
                "pattern_id": f"failure_high_pb_low_roe_{datetime.now().strftime('%Y%m%d')}",
                "pattern_name": "高PB低ROE风险模式",
                "pattern_type": "failure",
                "description": "PB>2.0 且 ROE<8% 的股票风险较高",
                "conditions": {
                    "pb_min": 2.0,
                    "roe_max": 8
                },
                "support": len(high_pb_low_roe),
                "risk_level": avg_deviation,
                "examples": [c["record_id"] for c in high_pb_low_roe[:3]],
                "discovered_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        # 模式2: 资金流出风险
        capital_outflow = [
            c for c in failure_cases
            if c.get("dimensions", {}).get("capital", {}).get("flow") == "out"
        ]
        if len(capital_outflow) >= min_support:
            avg_deviation = sum(c.get("actual_result", {}).get("deviation", 0) for c in capital_outflow) / len(capital_outflow)
            patterns.append({
                "pattern_id": f"failure_capital_outflow_{datetime.now().strftime('%Y%m%d')}",
                "pattern_name": "资金流出风险模式",
                "pattern_type": "failure",
                "description": "资金流出的股票风险较高",
                "conditions": {
                    "capital_flow": "out"
                },
                "support": len(capital_outflow),
                "risk_level": avg_deviation,
                "examples": [c["record_id"] for c in capital_outflow[:3]],
                "discovered_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        return patterns

    async def verify_pattern(
        self,
        pattern: Dict[str, Any],
        new_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证模式有效性

        Args:
            pattern: 待验证的模式
            new_cases: 新的案例数据

        Returns:
            验证结果
        """
        self.logger.info(f"Verifying pattern: {pattern['pattern_id']}")

        pattern_id = pattern["pattern_id"]
        conditions = pattern.get("conditions", {})

        # 统计符合条件的案例
        matched_cases = []
        for case in new_cases:
            if self._match_conditions(case, conditions):
                matched_cases.append(case)

        if not matched_cases:
            return {
                "pattern_id": pattern_id,
                "verified": False,
                "reason": "No matching cases found",
                "matched_count": 0
            }

        # 计算验证指标
        if pattern.get("pattern_type") == "success":
            success_count = sum(1 for c in matched_cases if c.get("case_type") == "success")
            verification_rate = success_count / len(matched_cases)
        else:
            failure_count = sum(1 for c in matched_cases if c.get("case_type") == "failure")
            verification_rate = failure_count / len(matched_cases)

        # 判断是否通过验证（准确率>=60%）
        passed = verification_rate >= 0.6

        result = {
            "pattern_id": pattern_id,
            "verified": passed,
            "matched_count": len(matched_cases),
            "verification_rate": verification_rate,
            "original_confidence": pattern.get("confidence", 0),
            "verified_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if passed:
            self.logger.info(f"Pattern verified: {pattern_id} (rate={verification_rate:.1%})")
        else:
            self.logger.warning(f"Pattern verification failed: {pattern_id} (rate={verification_rate:.1%})")

        return result

    def _match_conditions(
        self,
        case: Dict[str, Any],
        conditions: Dict[str, Any]
    ) -> bool:
        """检查案例是否符合条件"""
        dimensions = case.get("dimensions", {})

        for key, value in conditions.items():
            if key == "pb_max":
                if dimensions.get("fundamental", {}).get("pb", 999) >= value:
                    return False
            elif key == "pb_min":
                if dimensions.get("fundamental", {}).get("pb", 0) <= value:
                    return False
            elif key == "roe_min":
                if dimensions.get("fundamental", {}).get("roe", 0) < value:
                    return False
            elif key == "roe_max":
                if dimensions.get("fundamental", {}).get("roe", 999) >= value:
                    return False
            elif key == "policy_support":
                if dimensions.get("policy", {}).get("support", False) != value:
                    return False
            elif key == "trend":
                if dimensions.get("technical", {}).get("trend") != value:
                    return False
            elif key == "capital_flow":
                if dimensions.get("capital", {}).get("flow") != value:
                    return False

        return True

    async def search_patterns(
        self,
        stock_code: Optional[str] = None,
        pattern_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索模式

        Args:
            stock_code: 股票代码筛选
            pattern_type: 模式类型筛选（success/failure）
            limit: 返回数量限制

        Returns:
            匹配的模式列表
        """
        self.logger.info(f"Searching patterns: stock_code={stock_code}, pattern_type={pattern_type}")

        results = []

        for pattern_id, pattern in self.pattern_db.items():
            # 类型筛选
            if pattern_type and pattern.get("pattern_type") != pattern_type:
                continue

            results.append(pattern)

            if len(results) >= limit:
                break

        self.logger.info(f"Found {len(results)} patterns")

        return results

    async def save_pattern(self, pattern: Dict[str, Any]) -> bool:
        """
        保存模式到数据库

        Args:
            pattern: 模式数据

        Returns:
            是否成功
        """
        pattern_id = pattern.get("pattern_id")
        if not pattern_id:
            self.logger.error("Pattern ID is required")
            return False

        self.pattern_db[pattern_id] = pattern
        self._save_pattern_db()

        self.logger.info(f"Pattern saved: {pattern_id}")

        return True

    def _load_pattern_db(self) -> Dict[str, Any]:
        """加载模式数据库"""
        if self.pattern_db_path.exists():
            try:
                with open(self.pattern_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load pattern DB: {e}")
                return {}
        else:
            return {}

    def _save_pattern_db(self):
        """保存模式数据库"""
        try:
            with open(self.pattern_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.pattern_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save pattern DB: {e}")

    async def execute(self, task: str, **kwargs) -> Any:
        """
        执行任务

        Args:
            task: 任务名称
            **kwargs: 任务参数

        Returns:
            任务结果
        """
        if task == "discover":
            return await self.discover_patterns(
                experience_cases=kwargs.get("experience_cases", []),
                min_support=kwargs.get("min_support", 3)
            )
        elif task == "verify":
            return await self.verify_pattern(
                pattern=kwargs.get("pattern", {}),
                new_cases=kwargs.get("new_cases", [])
            )
        elif task == "search":
            return await self.search_patterns(
                stock_code=kwargs.get("stock_code"),
                pattern_type=kwargs.get("pattern_type"),
                limit=kwargs.get("limit", 10)
            )
        elif task == "save":
            return await self.save_pattern(
                pattern=kwargs.get("pattern", {})
            )
        else:
            raise ValueError(f"Unknown task: {task}")

    async def get_statistics(self) -> Dict[str, Any]:
        """获取模式数据库统计"""
        total_patterns = len(self.pattern_db)
        success_patterns = sum(1 for p in self.pattern_db.values() if p.get("pattern_type") == "success")
        failure_patterns = sum(1 for p in self.pattern_db.values() if p.get("pattern_type") == "failure")

        return {
            "total_patterns": total_patterns,
            "success_patterns": success_patterns,
            "failure_patterns": failure_patterns,
            "discovery_count": len(self.discovery_history)
        }

    async def get_discovery_history(self) -> List[Dict[str, Any]]:
        """获取发现历史"""
        return self.discovery_history
