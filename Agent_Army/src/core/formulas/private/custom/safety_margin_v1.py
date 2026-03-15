"""
私有公式：安全边际 v1
人工设计的公式，可通过赛马机制淘汰
"""


class SafetyMarginV1:
    """
    私有公式：安全边际 v1

    创建信息：
        - 创建时间：2026-03-14
        - 创建者：人工设计
        - 版本：1.0

    赛马数据：
        - 使用次数：0次
        - 准确率：待测试
        - 状态：testing（测试中）

    说明：
        安全边际 = (内在价值 - 当前价格) / 内在价值
        这是我们对格雷厄姆安全边际的理解和应用
    """

    FORMULA_META = {
        "name": "safety_margin",
        "version": "v1",
        "full_name": "安全边际 v1",
        "created_at": "2026-03-14",
        "created_by": "human",
        "usage_count": 0,
        "accuracy": 0.0,  # 待测试
        "status": "testing",  # testing, active, deprecated
        "description": "基于内在价值的安全边际计算",
        "parameters": {
            "min_threshold": 30.0,  # 最低安全边际要求30%
        }
    }

    @staticmethod
    def calculate(data: dict, params: dict = None) -> float:
        """
        计算安全边际

        Args:
            data: {
                "intrinsic_value": 内在价值（元）,
                "current_price": 当前价格（元）
            }
            params: 可选参数（覆盖默认参数）

        Returns:
            安全边际百分比（如 28.5 表示 28.5%）
        """
        if params is None:
            params = SafetyMarginV1.FORMULA_META["parameters"]

        intrinsic_value = data.get("intrinsic_value", 0)
        current_price = data.get("current_price", 0)

        if intrinsic_value == 0:
            return 0.0

        safety_margin = (intrinsic_value - current_price) / intrinsic_value * 100

        return round(safety_margin, 2)

    @staticmethod
    def evaluate(safety_margin: float) -> str:
        """
        评估安全边际是否达标

        Args:
            safety_margin: 安全边际百分比

        Returns:
            评估结果
        """
        min_threshold = SafetyMarginV1.FORMULA_META["parameters"]["min_threshold"]

        if safety_margin >= min_threshold:
            return f"✅ 安全边际充足（{safety_margin:.1f}% >= {min_threshold:.1f}%）"
        else:
            return f"⚠️ 安全边际不足（{safety_margin:.1f}% < {min_threshold:.1f}%）"
