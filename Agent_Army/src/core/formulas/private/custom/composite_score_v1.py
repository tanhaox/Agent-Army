"""
私有公式：综合评分 v1
人工设计的多维度评分公式
"""


class CompositeScoreV1:
    """
    私有公式：综合评分 v1

    创建信息：
        - 创建时间：2026-03-14
        - 创建者：人工设计
        - 版本：1.0

    赛马数据：
        - 使用次数：0次
        - 准确率：待测试
        - 状态：testing（测试中）

    说明：
        综合评分 = ROE得分(30%) + 增长得分(30%) + 估值得分(20%) + 风险得分(20%)
        这是我们对价值投资的多维度量化评估
    """

    FORMULA_META = {
        "name": "composite_score",
        "version": "v1",
        "full_name": "综合评分 v1",
        "created_at": "2026-03-14",
        "created_by": "human",
        "usage_count": 0,
        "accuracy": 0.0,
        "status": "testing",
        "description": "多维度综合评分",
        "weights": {
            "roe": 0.30,
            "growth": 0.30,
            "valuation": 0.20,
            "risk": 0.20
        },
        "thresholds": {
            "roe_excellent": 15.0,  # ROE优秀阈值
            "growth_healthy": 10.0,  # 增长健康阈值
            "debt_safe": 50.0  # 负债率安全阈值
        }
    }

    @staticmethod
    def calculate(data: dict, params: dict = None) -> float:
        """
        计算综合评分

        Args:
            data: {
                "roe": ROE百分比,
                "revenue_growth": 营收增长率百分比,
                "profit_growth": 净利润增长率百分比,
                "pe": PE倍数,
                "debt_ratio": 负债率百分比
            }
            params: 可选参数（覆盖默认参数）

        Returns:
            综合评分（0-100分）
        """
        if params is None:
            params = CompositeScoreV1.FORMULA_META
            weights = params["weights"]
            thresholds = params["thresholds"]
        else:
            weights = params.get("weights", CompositeScoreV1.FORMULA_META["weights"])
            thresholds = params.get("thresholds", CompositeScoreV1.FORMULA_META["thresholds"])

        # 1. ROE得分 (30%)
        roe = data.get("roe", 0)
        if roe >= thresholds["roe_excellent"]:
            roe_score = 100
        elif roe >= 10:
            roe_score = 70
        else:
            roe_score = 40

        # 2. 增长得分 (30%)
        revenue_growth = data.get("revenue_growth", 0)
        profit_growth = data.get("profit_growth", 0)
        avg_growth = (revenue_growth + profit_growth) / 2

        if avg_growth >= thresholds["growth_healthy"]:
            growth_score = 100
        elif avg_growth >= 5:
            growth_score = 70
        else:
            growth_score = 40

        # 3. 估值得分 (20%)
        pe = data.get("pe", 0)
        if pe <= 15:
            valuation_score = 100  # 低估值
        elif pe <= 25:
            valuation_score = 70  # 合理估值
        else:
            valuation_score = 40  # 高估值

        # 4. 风险得分 (20%)
        debt_ratio = data.get("debt_ratio", 0)
        if debt_ratio <= thresholds["debt_safe"]:
            risk_score = 100  # 低风险
        elif debt_ratio <= 70:
            risk_score = 70  # 中等风险
        else:
            risk_score = 40  # 高风险

        # 加权平均
        composite_score = (
            roe_score * weights["roe"] +
            growth_score * weights["growth"] +
            valuation_score * weights["valuation"] +
            risk_score * weights["risk"]
        )

        return round(composite_score, 2)

    @staticmethod
    def breakdown(data: dict) -> dict:
        """
        分解评分（用于结果解释）

        Args:
            data: 同 calculate 的输入

        Returns:
            各维度得分明细
        """
        params = CompositeScoreV1.FORMULA_META
        weights = params["weights"]
        thresholds = params["thresholds"]

        # 计算各维度得分
        roe = data.get("roe", 0)
        if roe >= thresholds["roe_excellent"]:
            roe_score = 100
            roe_reason = f"ROE {roe:.1f}% ≥ {thresholds['roe_excellent']:.1f}% (优秀)"
        elif roe >= 10:
            roe_score = 70
            roe_reason = f"ROE {roe:.1f}% 在10-15%之间 (良好)"
        else:
            roe_score = 40
            roe_reason = f"ROE {roe:.1f}% < 10% (较差)"

        revenue_growth = data.get("revenue_growth", 0)
        profit_growth = data.get("profit_growth", 0)
        avg_growth = (revenue_growth + profit_growth) / 2

        if avg_growth >= thresholds["growth_healthy"]:
            growth_score = 100
            growth_reason = f"平均增长 {avg_growth:.1f}% ≥ {thresholds['growth_healthy']:.1f}% (健康)"
        elif avg_growth >= 5:
            growth_score = 70
            growth_reason = f"平均增长 {avg_growth:.1f}% 在5-10%之间 (一般)"
        else:
            growth_score = 40
            growth_reason = f"平均增长 {avg_growth:.1f}% < 5% (缓慢)"

        pe = data.get("pe", 0)
        if pe <= 15:
            valuation_score = 100
            valuation_reason = f"PE {pe:.1f} ≤ 15 (低估值)"
        elif pe <= 25:
            valuation_score = 70
            valuation_reason = f"PE {pe:.1f} 在15-25之间 (合理)"
        else:
            valuation_score = 40
            valuation_reason = f"PE {pe:.1f} > 25 (高估值)"

        debt_ratio = data.get("debt_ratio", 0)
        if debt_ratio <= thresholds["debt_safe"]:
            risk_score = 100
            risk_reason = f"负债率 {debt_ratio:.1f}% ≤ {thresholds['debt_safe']:.1f}% (低风险)"
        elif debt_ratio <= 70:
            risk_score = 70
            risk_reason = f"负债率 {debt_ratio:.1f}% 在50-70%之间 (中等风险)"
        else:
            risk_score = 40
            risk_reason = f"负债率 {debt_ratio:.1f}% > 70% (高风险)"

        # 加权得分
        composite_score = CompositeScoreV1.calculate(data)

        return {
            "composite_score": composite_score,
            "breakdown": {
                "roe": {
                    "score": roe_score,
                    "weight": weights["roe"],
                    "weighted_score": roe_score * weights["roe"],
                    "reason": roe_reason
                },
                "growth": {
                    "score": growth_score,
                    "weight": weights["growth"],
                    "weighted_score": growth_score * weights["growth"],
                    "reason": growth_reason
                },
                "valuation": {
                    "score": valuation_score,
                    "weight": weights["valuation"],
                    "weighted_score": valuation_score * weights["valuation"],
                    "reason": valuation_reason
                },
                "risk": {
                    "score": risk_score,
                    "weight": weights["risk"],
                    "weighted_score": risk_score * weights["risk"],
                    "reason": risk_reason
                }
            }
        }
