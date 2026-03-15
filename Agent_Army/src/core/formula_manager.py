"""
公式管理器 - 赛马机制
管理私有公式的选择、淘汰、优化
"""

import importlib
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.logger import get_logger


class FormulaManager:
    """
    公式管理器 - 负责赛马机制

    职责：
    1. 加载标准公式（只读）
    2. 加载私有公式（可管理）
    3. 赛马机制选择最优公式
    4. 记录公式使用情况
    5. 自动淘汰低效公式
    6. 允许管理层创建新公式
    """

    def __init__(self):
        self.logger = get_logger("formula_manager")

        # 标准公式（只读）
        self.standard_formulas = self._load_standard_formulas()

        # 私有公式（可管理）
        self.private_formulas = self._load_private_formulas()

        # AI生成的公式目录
        self.ai_formula_dir = Path(__file__).parent / "private" / "ai_generated"
        self.ai_formula_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"公式库初始化完成", extra={
            "standard_count": len(self.standard_formulas),
            "private_count": len(self.private_formulas)
        })

    def _load_standard_formulas(self) -> Dict[str, Any]:
        """加载标准公式（业界公认，不可修改）"""
        formulas = {}

        try:
            from src.core.formulas.standard import (
                StandardFinancialFormulas,
                StandardValuationFormulas
            )

            # 财务公式
            for method_name in dir(StandardFinancialFormulas):
                if not method_name.startswith("_"):
                    formulas[f"standard.{method_name}"] = getattr(StandardFinancialFormulas, method_name)

            # 估值公式
            for method_name in dir(StandardValuationFormulas):
                if not method_name.startswith("_"):
                    formulas[f"standard.{method_name}"] = getattr(StandardValuationFormulas, method_name)

            self.logger.info(f"加载标准公式: {len(formulas)}个")

        except Exception as e:
            self.logger.error(f"加载标准公式失败: {str(e)}")

        return formulas

    def _load_private_formulas(self) -> Dict[str, List[Any]]:
        """加载私有公式（可调整，赛马机制）"""
        formulas = {}

        try:
            from src.core.formulas.private import SafetyMarginV1, CompositeScoreV1

            # 按公式名称分组（可能有多个版本）
            for formula_class in [SafetyMarginV1, CompositeScoreV1]:
                name = formula_class.FORMULA_META["name"]

                if name not in formulas:
                    formulas[name] = []

                formulas[name].append(formula_class)

            self.logger.info(f"加载私有公式: {len(formulas)}组")

        except Exception as e:
            self.logger.error(f"加载私有公式失败: {str(e)}")

        return formulas

    def get_formula(
        self,
        formula_name: str,
        use_best: bool = True,
        version: Optional[str] = None
    ) -> Any:
        """
        获取公式

        Args:
            formula_name: 公式名称（如 "roe" 或 "safety_margin"）
            use_best: 是否使用最优版本（赛马机制）
            version: 指定版本（如 "v1"），优先级高于 use_best

        Returns:
            公式类或方法

        Raises:
            ValueError: 公式不存在
        """
        # 1. 优先查找标准公式
        standard_key = f"standard.{formula_name}"
        if standard_key in self.standard_formulas:
            return self.standard_formulas[standard_key]

        # 2. 查找私有公式
        if formula_name in self.private_formulas:
            candidates = self.private_formulas[formula_name]

            # 2.1 指定版本
            if version:
                for formula in candidates:
                    if formula.FORMULA_META["version"] == version:
                        return formula
                raise ValueError(f"公式 {formula_name} 版本 {version} 不存在")

            # 2.2 使用最优版本（赛马机制）
            if use_best:
                # 过滤掉已淘汰的公式
                active_candidates = [
                    f for f in candidates
                    if f.FORMULA_META["status"] != "deprecated"
                ]

                if not active_candidates:
                    raise ValueError(f"公式 {formula_name} 已全部淘汰")

                # 选择准确率最高的
                best = max(
                    active_candidates,
                    key=lambda f: f.FORMULA_META["accuracy"]
                )
                return best

            # 2.3 随机选择（用于测试新公式）
            return random.choice(candidates)

        raise ValueError(f"公式 {formula_name} 不存在")

    def calculate(
        self,
        formula_name: str,
        data: Dict,
        params: Optional[Dict] = None,
        use_best: bool = True
    ) -> Any:
        """
        使用公式计算（便捷方法）

        Args:
            formula_name: 公式名称
            data: 输入数据
            params: 公式参数（私有公式专用）
            use_best: 是否使用最优版本

        Returns:
            计算结果
        """
        formula = self.get_formula(formula_name, use_best)

        # 私有公式有 calculate 静态方法
        if hasattr(formula, "calculate"):
            return formula.calculate(data, params)

        # 标准公式是静态方法
        if callable(formula):
            return formula(data)

        raise ValueError(f"公式 {formula_name} 格式错误")

    def record_usage(self, formula_name: str, formula_version: str, success: bool):
        """
        记录公式使用结果（用于赛马）

        Args:
            formula_name: 公式名称
            formula_version: 公式版本
            success: 是否成功（预测准确）
        """
        if formula_name not in self.private_formulas:
            return

        # 找到对应版本
        for formula in self.private_formulas[formula_name]:
            if formula.FORMULA_META["version"] == formula_version:
                meta = formula.FORMULA_META

                # 更新使用次数
                meta["usage_count"] += 1

                # 更新准确率（滑动窗口，最近100次）
                old_accuracy = meta["accuracy"]
                weight = min(0.1, 1.0 / meta["usage_count"])  # 逐渐降低权重
                new_accuracy = old_accuracy * (1 - weight) + (1.0 if success else 0.0) * weight
                meta["accuracy"] = new_accuracy

                self.logger.info(
                    f"公式使用记录: {formula_name} {formula_version}",
                    extra={
                        "usage_count": meta["usage_count"],
                        "old_accuracy": f"{old_accuracy:.2%}",
                        "new_accuracy": f"{new_accuracy:.2%}",
                        "success": success
                    }
                )

                # 自动淘汰机制
                if meta["usage_count"] >= 50 and meta["accuracy"] < 0.6:
                    meta["status"] = "deprecated"
                    self.logger.warning(
                        f"公式已淘汰: {formula_name} {formula_version} "
                        f"(准确率 {new_accuracy:.2%} < 60%)"
                    )

                break

    def create_ai_formula(
        self,
        formula_type: str,
        purpose: Dict[str, str],
        creation_basis: Dict[str, Any],
        usage_conditions: Dict[str, Any],
        formula_code: str,
        created_by: str = "CorpsCoordinator AI"
    ) -> str:
        """
        创建AI生成的公式（管理层调用）

        ⭐ 三大核心要求：
        1. 公式用途（purpose）
        2. 创建依据（creation_basis）
        3. 使用条件（usage_conditions）

        Args:
            formula_type: 公式类型（如 composite_score, safety_margin）
            purpose: {
                "description": "此公式是干什么的",
                "target": "目标场景",
                "output": "输出什么",
                "usage_scenario": "使用场景"
            }
            creation_basis: {
                "data_sources": ["基于哪些数据"],
                "methodology": "怎么算出来的",
                "reference": "参考了什么",
                "validation": "验证方法",
                "ai_reasoning": "AI的推理过程"
            }
            usage_conditions: {
                "prerequisites": ["前置条件"],
                "limitations": ["限制条件"],
                "parameters": {"param_name": {"value": "", "range": "", "description": ""}}
            }
            formula_code: 公式代码（Python代码字符串）
            created_by: 创建者（如 "CorpsCoordinator AI"）

        Returns:
            新公式文件名（标准化命名）

        Raises:
            ValueError: 参数不完整
        """
        # ========== 1. 验证三大核心要求 ==========
        required_purpose_fields = ["description", "target", "output", "usage_scenario"]
        for field in required_purpose_fields:
            if field not in purpose:
                raise ValueError(f"缺少用途信息: {field}")

        required_basis_fields = ["data_sources", "methodology", "ai_reasoning"]
        for field in required_basis_fields:
            if field not in creation_basis:
                raise ValueError(f"缺少创建依据: {field}")

        required_condition_fields = ["prerequisites", "limitations"]
        for field in required_condition_fields:
            if field not in usage_conditions:
                raise ValueError(f"缺少使用条件: {field}")

        # ========== 2. 确定版本号 ==========
        version = self._get_next_version(formula_type)

        # ========== 3. 标准化文件命名 ==========
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        purpose_keyword = self._extract_purpose_keyword(purpose["target"])

        filename = f"{formula_type}_{purpose_keyword}_{version}_{timestamp}.py"
        filepath = self.ai_formula_dir / filename

        # ========== 4. 生成完整代码（带元数据）==========
        full_code = self._generate_formula_code(
            formula_type=formula_type,
            version=version,
            purpose=purpose,
            creation_basis=creation_basis,
            usage_conditions=usage_conditions,
            formula_code=formula_code,
            created_by=created_by
        )

        # ========== 5. 保存文件 ==========
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_code)

        self.logger.info(
            f"AI创建新公式: {filename}",
            extra={
                "formula_type": formula_type,
                "version": version,
                "purpose": purpose["description"],
                "created_by": created_by
            }
        )

        # TODO: 动态加载新公式到内存

        return filename

    def add_ai_review(
        self,
        formula_name: str,
        formula_version: str,
        reviewer: str,
        rating: float,
        comment: str,
        usage_context: str,
        suggestions: List[str] = None
    ):
        """
        添加AI评价（众AI评价机制）

        Args:
            formula_name: 公式名称
            formula_version: 公式版本
            reviewer: 评价者（如 "FundamentalAnalyzer AI"）
            rating: 评分（1-5星）
            comment: 评价内容
            usage_context: 使用场景
            suggestions: 改进建议

        Raises:
            ValueError: 公式不存在或评分无效
        """
        if rating < 1 or rating > 5:
            raise ValueError("评分必须在1-5之间")

        if formula_name not in self.private_formulas:
            raise ValueError(f"公式 {formula_name} 不存在")

        # 找到对应版本
        for formula in self.private_formulas[formula_name]:
            if formula.FORMULA_META["version"] == formula_version:
                meta = formula.FORMULA_META

                # 初始化 ai_reviews（如果不存在）
                if "ai_reviews" not in meta:
                    meta["ai_reviews"] = []

                # 添加评价
                review = {
                    "reviewer": reviewer,
                    "reviewed_at": datetime.now().isoformat(),
                    "rating": rating,
                    "comment": comment,
                    "usage_context": usage_context,
                    "suggestions": suggestions or []
                }
                meta["ai_reviews"].append(review)

                # 更新统计数据
                self._update_review_statistics(meta)

                self.logger.info(
                    f"AI评价已记录: {formula_name} {formula_version}",
                    extra={
                        "reviewer": reviewer,
                        "rating": rating,
                        "avg_rating": f"{meta['statistics']['avg_rating']:.2f}",
                        "total_reviews": meta['statistics']['total_reviews']
                    }
                )

                break

    def get_ai_reviews(self, formula_name: str, formula_version: str = None) -> List[Dict]:
        """
        获取公式的AI评价

        Args:
            formula_name: 公式名称
            formula_version: 公式版本（可选，不提供则返回所有版本）

        Returns:
            评价列表
        """
        if formula_name not in self.private_formulas:
            return []

        reviews = []

        for formula in self.private_formulas[formula_name]:
            if formula_version and formula.FORMULA_META["version"] != formula_version:
                continue

            if "ai_reviews" in formula.FORMULA_META:
                reviews.extend(formula.FORMULA_META["ai_reviews"])

        # 按评分排序（高分在前）
        reviews.sort(key=lambda r: r["rating"], reverse=True)

        return reviews

    def get_best_formula_by_reviews(self, formula_name: str) -> Any:
        """
        基于众AI评价选择最优公式

        综合考虑：
        - 平均评分
        - 准确率
        - 使用次数

        Args:
            formula_name: 公式名称

        Returns:
            最优公式
        """
        if formula_name not in self.private_formulas:
            raise ValueError(f"公式 {formula_name} 不存在")

        candidates = self.private_formulas[formula_name]

        # 过滤已淘汰的
        active = [f for f in candidates if f.FORMULA_META["status"] != "deprecated"]

        if not active:
            raise ValueError(f"公式 {formula_name} 已全部淘汰")

        # 综合评分 = 平均评分 * 0.4 + 准确率 * 5 * 0.4 + 使用次数归一化 * 0.2
        def calculate_composite_score(formula):
            meta = formula.FORMULA_META

            # 平均评分（1-5星）
            avg_rating = meta.get("statistics", {}).get("avg_rating", 0)

            # 准确率（0-1）
            accuracy = meta.get("accuracy", 0)

            # 使用次数归一化
            max_usage = max(f.FORMULA_META.get("usage_count", 0) for f in active)
            usage_normalized = meta.get("usage_count", 0) / max(max_usage, 1)

            # 综合评分
            composite = avg_rating * 0.4 + accuracy * 5 * 0.4 + usage_normalized * 5 * 0.2

            return composite

        best = max(active, key=calculate_composite_score)

        return best

    # ========== 辅助方法 ==========

    def _get_next_version(self, formula_type: str) -> str:
        """获取下一个版本号"""
        if formula_type not in self.private_formulas:
            return "v1"

        versions = []
        for formula in self.private_formulas[formula_type]:
            version_str = formula.FORMULA_META["version"]
            if version_str.startswith("v"):
                try:
                    version_num = int(version_str[1:])
                    versions.append(version_num)
                except ValueError:
                    pass

        if not versions:
            return "v1"

        return f"v{max(versions) + 1}"

    def _extract_purpose_keyword(self, target: str) -> str:
        """从目标场景提取关键词（用于文件命名）"""
        # 简单提取英文关键词
        keywords = {
            "价值投资": "value_investing",
            "成长股": "growth_stock",
            "价值": "value",
            "成长": "growth",
            "风险评估": "risk_assessment",
            "风险": "risk",
            "安全边际": "safety_margin",
            "格雷厄姆": "graham",
            "巴菲特": "buffett",
        }

        for cn, en in keywords.items():
            if cn in target:
                return en

        # 默认返回 generic
        return "general"

    def _generate_formula_code(
        self,
        formula_type: str,
        version: str,
        purpose: Dict[str, str],
        creation_basis: Dict[str, Any],
        usage_conditions: Dict[str, Any],
        formula_code: str,
        created_by: str
    ) -> str:
        """生成完整的公式代码（带元数据）"""

        template = f'''"""
AI生成的公式：{formula_type} {version}

========== 1. 公式用途 ==========
此公式是干什么的：{purpose["description"]}
目标场景：{purpose["target"]}
输出内容：{purpose["output"]}
使用场景：{purpose["usage_scenario"]}

========== 2. 创建依据 ==========
基于哪些数据：{", ".join(creation_basis["data_sources"])}
计算方法：{creation_basis["methodology"]}
参考来源：{creation_basis.get("reference", "无")}
验证方法：{creation_basis.get("validation", "无")}

AI的推理过程：
{creation_basis["ai_reasoning"]}

========== 3. 使用条件 ==========
前置条件：{", ".join(usage_conditions["prerequisites"])}
限制条件：{", ".join(usage_conditions["limitations"])}

参数说明：
'''

        # 添加参数说明
        if "parameters" in usage_conditions:
            for param_name, param_info in usage_conditions["parameters"].items():
                template += f"  - {param_name}: {param_info.get('description', '')} "
                template += f"(默认: {param_info.get('value', '')}, "
                template += f"范围: {param_info.get('range', '')})\\n"

        template += f'''

========== 元数据 ==========
创建时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
创建者：{created_by}
版本：{version}
状态：testing（测试中）

========== 众AI评价 ==========
（暂无评价）
"""

from typing import Dict, Any


class AIFormula_{formula_type}_{version.replace(".", "_")}:
    """
    AI生成的公式类
    """

    FORMULA_META = {{
        "name": "{formula_type}",
        "version": "{version}",
        "full_name": "{formula_type} {version}",
        "created_at": "{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}",
        "created_by": "{created_by}",

        # 三大核心要求
        "purpose": {repr(purpose)},
        "creation_basis": {repr(creation_basis)},
        "usage_conditions": {repr(usage_conditions)},

        # 赛马数据
        "usage_count": 0,
        "accuracy": 0.0,
        "status": "testing",

        # 众AI评价
        "ai_reviews": [],

        # 统计数据
        "statistics": {{
            "avg_rating": 0.0,
            "total_reviews": 0,
            "success_rate": 0.0,
            "avg_deviation": 0.0
        }}
    }}

    @staticmethod
    def calculate(data: Dict, params: Dict = None) -> Any:
        """
        计算公式

        Args:
            data: 输入数据
            params: 可选参数

        Returns:
            计算结果
        """
        if params is None:
            params = {{}}

        # ========== 公式代码 ==========
{self._indent_code(formula_code, 8)}
        # ========== 公式代码结束 ==========

    @staticmethod
    def explain(data: Dict, result: Any) -> str:
        """
        解释计算结果

        Args:
            data: 输入数据
            result: 计算结果

        Returns:
            解释文本
        """
        # AI可以在子类中实现更详细的解释
        return f"计算结果: {{result}}"

def _update_review_statistics(self, meta: Dict):
        """更新评价统计"""
        reviews = meta.get("ai_reviews", [])

        if not reviews:
            return

        # 计算平均评分
        total_rating = sum(r["rating"] for r in reviews)
        avg_rating = total_rating / len(reviews)

        # 更新统计
        if "statistics" not in meta:
            meta["statistics"] = {{}}

        meta["statistics"]["avg_rating"] = avg_rating
        meta["statistics"]["total_reviews"] = len(reviews)
'''

        return template

    def _indent_code(self, code: str, spaces: int) -> str:
        """缩进代码"""
        indent = " " * spaces
        lines = code.split("\n")
        return "\n".join(indent + line for line in lines)

    def _update_review_statistics(self, meta: Dict):
        """更新评价统计"""
        reviews = meta.get("ai_reviews", [])

        if not reviews:
            return

        # 计算平均评分
        total_rating = sum(r["rating"] for r in reviews)
        avg_rating = total_rating / len(reviews)

        # 更新统计
        if "statistics" not in meta:
            meta["statistics"] = {}

        meta["statistics"]["avg_rating"] = avg_rating
        meta["statistics"]["total_reviews"] = len(reviews)

    def update_private_param(
        self,
        formula_name: str,
        param_name: str,
        param_value: Any
    ):
        """
        更新私有公式参数（管理层调用）

        Args:
            formula_name: 公式名称
            param_name: 参数名
            param_value: 参数值
        """
        if formula_name not in self.private_formulas:
            raise ValueError(f"公式 {formula_name} 不存在")

        # 更新所有版本的参数
        for formula in self.private_formulas[formula_name]:
            if "parameters" in formula.FORMULA_META:
                old_value = formula.FORMULA_META["parameters"].get(param_name)
                formula.FORMULA_META["parameters"][param_name] = param_value

                self.logger.info(
                    f"公式参数已更新: {formula_name} "
                    f"{param_name} {old_value} → {param_value}"
                )

    def get_formula_info(self, formula_name: str) -> Dict:
        """获取公式信息（用于展示）"""
        info = {
            "name": formula_name,
            "standard": None,
            "private": []
        }

        # 标准公式
        standard_key = f"standard.{formula_name}"
        if standard_key in self.standard_formulas:
            info["standard"] = {
                "exists": True,
                "type": "业界公认",
                "editable": False
            }

        # 私有公式
        if formula_name in self.private_formulas:
            for formula in self.private_formulas[formula_name]:
                meta = formula.FORMULA_META
                info["private"].append({
                    "version": meta["version"],
                    "created_by": meta["created_by"],
                    "usage_count": meta["usage_count"],
                    "accuracy": f"{meta['accuracy']:.2%}",
                    "status": meta["status"]
                })

        return info

    def list_formulas(self) -> Dict[str, List[str]]:
        """列出所有公式"""
        return {
            "standard": [
                name.replace("standard.", "")
                for name in self.standard_formulas.keys()
            ],
            "private": list(self.private_formulas.keys())
        }
