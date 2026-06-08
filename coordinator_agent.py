#!/usr/bin/env python3
"""
CoordinatorAgent - 投资决策协调器

职责：
1. 接收各分析层的输出（技术面、基本面、资金面、新闻面）
2. 应用权重（当前为静态，后续可动态调整）
3. 执行否决规则（财务造假、监管立案、周线破位等）
4. 输出最终评分、推荐动作、仓位建议、理由

版本：v0.2 (集成 ML 预测)
"""

from typing import Dict, Any, Optional

class CoordinatorAgent:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化协调器
        :param weights: 各维度权重，默认与 config/weights.json 同步
        """
        self.weights = weights or {
            "technical": 0.35,
            "fundamental": 0.25,
            "capital": 0.18,
            "news": 0.05,
            "game": 0.05,
            "rs": 0.04,
            "ml": 0.03,
            "macro": 0.05
        }

    def coordinate(self,
                  technical_result: Dict[str, Any],
                  fundamental_result: Dict[str, Any],
                  capital_result: Dict[str, Any],
                  news_result: Dict[str, Any],
                  kline_result: Optional[Dict[str, Any]] = None,
                  rs_result: Optional[Dict[str, Any]] = None,
                  ml_result: Optional[Dict[str, Any]] = None,
                  macro_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        协调各层分析，生成最终投资建议
        :param technical_result: 技术分析结果，应包含 'total_score' (0-10) 和 'recommendation'
        :param fundamental_result: 基本面分析结果，应包含 'total_score' (0-10) 和 'recommendation'
        :param capital_result: 资金面分析结果，应包含 'total_score' (0-10) 和 'recommendation'
        :param news_result: 新闻面分析结果，应包含 'total_score' (0-10) 和 'recommendation'
        :param kline_result: K线博弈分析结果（可选）
        :param rs_result: 相对强度分析结果（可选）
        :param ml_result: ML预测结果（可选），应包含 'direction' ('up'/'down'), 'confidence', 'accuracy'
        :param macro_result: 宏观景气度结果（可选），应包含 'total_score' (0-10) 和 'comment'
        :return: 综合结果字典
        """
        # 1. 执行否决检查（优先级最高）
        veto = self._check_veto(technical_result, fundamental_result, capital_result, news_result)
        if veto["triggered"]:
            return {
                "total_score": 0,
                "recommendation": veto["action"],
                "position_advice": "清仓",
                "reasoning": veto["reason"],
                "details": {"veto": veto},
                "source": "CoordinatorAgent (VETO)"
            }

        # 2. 提取各层评分（若无评分字段则用推荐映射）
        tech_score = self._extract_score(technical_result, "technical")
        fund_score = self._extract_score(fundamental_result, "fundamental")
        cap_score = self._extract_score(capital_result, "capital")
        news_score = self._extract_score(news_result, "news")
        kline_score = self._extract_score(kline_result, "kline_game") if kline_result else None
        rs_score = self._extract_score(rs_result, "rs") if rs_result else None
        ml_score = self._extract_ml_score(ml_result) if ml_result else None

        # 3. 加权计算综合得分
        total_score = (
            tech_score * self.weights.get("technical", 0) +
            fund_score * self.weights.get("fundamental", 0) +
            cap_score * self.weights.get("capital", 0) +
            news_score * self.weights.get("news", 0)
        )

        # 如果有K线博弈分析，加入权重
        if kline_score is not None and "kline_game" in self.weights:
            total_score += kline_score * self.weights["kline_game"]

        if rs_score is not None and "rs" in self.weights:
            total_score += rs_score * self.weights["rs"]

        # ML预测作为调整项（不是独立权重，而是基于置信度的微调）
        if ml_score is not None and "ml" in self.weights:
            total_score += ml_score * self.weights["ml"]

        # 宏观景气度评分
        macro_score = self._extract_score(macro_result, "macro") if macro_result else None
        if macro_score is not None and "macro" in self.weights:
            total_score += macro_score * self.weights["macro"]

        # 4. 根据总分给出推荐和仓位建议
        recommendation, position_advice = self._map_score_to_advice(total_score)

        # 5. 生成简要理由
        reasoning = self._build_reasoning(tech_score, fund_score, cap_score, news_score,
                                          technical_result, fundamental_result,
                                          kline_result, rs_result, ml_result, macro_result)

        return {
            "total_score": round(total_score, 1),
            "recommendation": recommendation,
            "position_advice": position_advice,
            "reasoning": reasoning,
            "details": {
                "scores": {
                    "technical": tech_score,
                    "fundamental": fund_score,
                    "capital": cap_score,
                    "news": news_score,
                    "kline_game": kline_score,
                    "rs": rs_score,
                    "ml": ml_score,
                    "macro": macro_score
                },
                "weights": self.weights
            },
            "source": "CoordinatorAgent"
        }

    # ---------- 辅助方法 ----------
    def _extract_ml_score(self, ml_result: Dict[str, Any]) -> Optional[float]:
        """将 ML 预测结果转换为 0-10 评分

        ML预测方向和置信度映射为评分：
        - 上涨 + 高置信度 → 高分
        - 下跌 + 高置信度 → 低分
        - 低置信度 → 接近中性5.0

        Returns:
            0-10 评分，或 None（如果不可用）
        """
        if not ml_result:
            return None

        direction = ml_result.get('direction', 'unknown')
        confidence = float(ml_result.get('confidence', 0))
        accuracy = float(ml_result.get('accuracy', 0))

        if direction == 'unknown' or confidence < 0.1:
            return None

        # 基于置信度的调整幅度（0.5~2.5分）
        # 置信度 * 准确率衰减因子，避免过度依赖低准确率模型
        adj = confidence * max(0.3, accuracy) * 5.0

        if direction == 'up':
            return 5.0 + adj
        elif direction == 'down':
            return 5.0 - adj
        return None

    def _extract_score(self, result: Dict[str, Any], layer: str) -> float:
        """从各层结果中提取评分（0-10），若没有则根据推荐映射一个默认分"""
        if "total_score" in result:
            return min(max(result["total_score"], 0), 10)

        # 若没有评分，根据 recommendation 字段估算（用于兼容旧版）
        rec = result.get("recommendation", "").lower()
        if "强烈推荐" in rec or "买入" in rec:
            return 8.0
        elif "推荐" in rec or "增持" in rec:
            return 6.0
        elif "持有" in rec or "中性" in rec:
            return 5.0
        elif "减持" in rec or "谨慎" in rec:
            return 3.0
        elif "卖出" in rec or "回避" in rec:
            return 1.0
        else:
            # 默认中性
            return 5.0

    def _map_score_to_advice(self, score: float) -> tuple:
        """根据综合得分映射推荐和仓位"""
        if score >= 8.0:
            return "强烈推荐买入", "80%-100%"
        elif score >= 6.5:
            return "推荐买入", "60%-80%"
        elif score >= 5.0:
            return "持有/观望", "30%-60%"
        elif score >= 3.5:
            return "减持/谨慎", "10%-30%"
        else:
            return "卖出/回避", "0%-10%"

    def _build_reasoning(self, tech, fund, cap, news,
                       tech_result, fund_result, kline_result=None, rs_result=None,
                       ml_result=None, macro_result=None) -> str:
        """生成简短理由（可扩展）"""
        parts = []
        if tech >= 7:
            parts.append("技术面表现强劲")
        elif tech <= 3:
            parts.append("技术面承压")
        if fund >= 7:
            parts.append("基本面优秀")
        elif fund <= 3:
            parts.append("基本面疲软")
        if cap >= 7:
            parts.append("资金面流入积极")
        elif cap <= 3:
            parts.append("资金面流出")
        if news >= 7:
            parts.append("新闻面偏多")
        elif news <= 3:
            parts.append("新闻面偏空")

        # K线博弈分析（新增）
        if kline_result:
            kline_details = kline_result.get('details', {})
            kline_trend = kline_details.get('短期预测', '')
            kline_advantage = kline_details.get('博弈优势方', '')
            if kline_trend == '看涨':
                parts.append(f"K线博弈看涨（{kline_advantage}）")
            elif kline_trend == '看跌':
                parts.append(f"K线博弈看跌（{kline_advantage}）")
            elif kline_trend in ['偏涨', '偏跌']:
                parts.append(f"K线博弈{kline_trend}（{kline_advantage}）")

        # 相对强度分析（新增）
        if rs_result:
            rs_details = rs_result.get('details', {})
            rs_grade = rs_details.get('strength_grade', '')
            rs_rec = rs_result.get('recommendation', '')
            if rs_grade == 'strong':
                parts.append(f"相对强度强势（{rs_rec}）")
            elif rs_grade == 'weak':
                parts.append(f"相对强度弱势（{rs_rec}）")

        # ML预测信号
        if ml_result and ml_result.get('direction', 'unknown') != 'unknown':
            direction = ml_result['direction']
            confidence = ml_result.get('confidence', 0)
            accuracy = ml_result.get('accuracy', 0)
            if direction == 'up':
                parts.append(f"ML预测上涨（置信度{confidence:.0%}，历史准确率{accuracy:.0%}）")
            elif direction == 'down':
                parts.append(f"ML预测下跌（置信度{confidence:.0%}，历史准确率{accuracy:.0%}）")

        # 宏观景气度
        if macro_result:
            macro_score = macro_result.get('total_score', 0)
            macro_comment = macro_result.get('comment', '')
            if macro_score >= 7:
                parts.append(f"宏观偏暖（{macro_comment}）")
            elif macro_score <= 3:
                parts.append(f"宏观偏冷（{macro_comment}）")

        if not parts:
            parts.append("各维度信号不显著，建议观望")

        # 补充技术/基本面具体说明（可选）
        tech_trend = tech_result.get("trend", "")
        if tech_trend:
            parts.append(f"技术趋势: {tech_trend}")
        fund_rec = fund_result.get("recommendation", "")
        if fund_rec:
            parts.append(f"基本面建议: {fund_rec}")

        return "；".join(parts)

    def _check_veto(self, tech, fund, cap, news) -> Dict[str, Any]:
        """
        否决权检查（初期实现几个硬规则）
        返回 {"triggered": bool, "action": str, "reason": str}
        """
        # 示例规则1：若基本面分析中有财务造假嫌疑
        if fund.get("fraud_suspected", False):
            return {
                "triggered": True,
                "action": "强制卖出",
                "reason": "基本面检测到财务造假嫌疑，立即清仓"
            }

        # 示例规则2：若新闻面分析中有监管立案调查
        if news.get("regulatory_investigation", False):
            return {
                "triggered": True,
                "action": "强制清仓",
                "reason": "监管立案调查，强制清仓回避"
            }

        # 示例规则3：若技术面周线级别破位（需要技术分析结果中提供）
        if tech.get("weekly_breakdown", False):
            return {
                "triggered": True,
                "action": "减仓至观察仓",
                "reason": "周线级别破位，建议减仓至观察仓位（≤10%）"
            }

        # 可继续添加其他规则...

        return {"triggered": False, "action": None, "reason": None}


# ---------- 使用示例 ----------
if __name__ == "__main__":
    # 模拟各层分析结果（实际应从各 Agent 获取）
    tech_result = {
        "total_score": 7.2,
        "trend": "上升趋势",
        "recommendation": "推荐买入",
        "weekly_breakdown": False
    }
    fund_result = {
        "total_score": 6.5,
        "recommendation": "推荐买入",
        "fraud_suspected": False
    }
    capital_result = {
        "total_score": 5.0,
        "recommendation": "中性"
    }
    news_result = {
        "total_score": 8.0,
        "recommendation": "利好",
        "regulatory_investigation": False
    }

    agent = CoordinatorAgent()
    decision = agent.coordinate(tech_result, fund_result, capital_result, news_result)
    print("=== 最终决策 ===")
    for k, v in decision.items():
        print(f"{k}: {v}")
