"""
公式工具 - 封装FormulaManager
"""

from typing import Dict, Any, Optional
from src.core.logger import get_logger
from src.core.formula_manager import FormulaManager


class FormulaTool:
    """
    公式工具

    职责：
    - 封装FormulaManager
    - 提供统一接口给AI Agent使用
    - AI Agent不关心公式如何计算
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("formula_tool")
        self.config = config or {}

        # 初始化FormulaManager
        self.manager = FormulaManager()

        self.logger.info("公式工具初始化完成")

    def calculate(
        self,
        formula_name: str,
        data: Dict[str, Any],
        params: Optional[Dict] = None,
        use_best: bool = True
    ) -> Any:
        """
        使用公式计算

        Args:
            formula_name: 公式名称（如 "roe", "composite_score"）
            data: 输入数据
            params: 公式参数（私有公式专用）
            use_best: 是否使用最优版本（赛马机制）

        Returns:
            计算结果
        """
        self.logger.info(f"计算公式: {formula_name}")

        result = self.manager.calculate(
            formula_name=formula_name,
            data=data,
            params=params,
            use_best=use_best
        )

        self.logger.info(f"计算完成: {formula_name} = {result}")

        return result

    def get_formula_info(self, formula_name: str) -> Dict:
        """
        获取公式信息

        Args:
            formula_name: 公式名称

        Returns:
            公式信息
        """
        return self.manager.get_formula_info(formula_name)

    def list_formulas(self) -> Dict:
        """
        列出所有公式

        Returns:
            {"standard": [...], "private": [...]}
        """
        return self.manager.list_formulas()

    def record_usage(
        self,
        formula_name: str,
        formula_version: str,
        success: bool
    ):
        """
        记录公式使用结果（用于赛马）

        Args:
            formula_name: 公式名称
            formula_version: 公式版本
            success: 是否成功（预测准确）
        """
        self.manager.record_usage(formula_name, formula_version, success)

    def add_ai_review(
        self,
        formula_name: str,
        formula_version: str,
        reviewer: str,
        rating: float,
        comment: str,
        usage_context: str = "",
        suggestions = None
    ):
        """
        添加AI评价

        Args:
            formula_name: 公式名称
            formula_version: 公式版本
            reviewer: 评价者
            rating: 评分（1-5）
            comment: 评价内容
            usage_context: 使用场景
            suggestions: 改进建议
        """
        self.manager.add_ai_review(
            formula_name=formula_name,
            formula_version=formula_version,
            reviewer=reviewer,
            rating=rating,
            comment=comment,
            usage_context=usage_context,
            suggestions=suggestions
        )


# ========== 便捷函数 ==========

def calculate(formula_name: str, data: Dict, params: Dict = None) -> Any:
    """
    使用公式计算（便捷函数）

    Args:
        formula_name: 公式名称
        data: 输入数据
        params: 公式参数

    Returns:
        计算结果
    """
    tool = FormulaTool()
    return tool.calculate(formula_name, data, params)
