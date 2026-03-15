"""
AI生成公式的元数据模板
"""

# AI创建公式时必须提供的元数据
AI_FORMULA_METADATA_TEMPLATE = {
    # ========== 基本信息 ==========
    "name": "公式名称（英文，如 composite_score）",
    "version": "版本号（如 v1, v2）",
    "full_name": "完整名称（如 综合评分公式 v1）",
    "created_at": "创建时间（2026-03-14 10:30:00）",
    "created_by": "创建者（如 CorpsCoordinator AI）",

    # ========== 三大核心要求 ==========

    # 1. 公式用途
    "purpose": {
        "description": "此公式是干什么的（一句话说明）",
        "target": "目标场景（如：筛选价值投资标的）",
        "output": "输出什么（如：0-100的综合评分）",
        "usage_scenario": "使用场景（如：基本面分析阶段）"
    },

    # 2. 创建依据
    "creation_basis": {
        "data_sources": ["基于哪些数据创建（如：历史财报数据）"],
        "methodology": "怎么算出来的（如：多因子加权平均）",
        "reference": "参考了什么（如：巴菲特价值投资理念）",
        "validation": "验证方法（如：回测过去3年数据）",
        "ai_reasoning": "AI的推理过程（详细说明为什么这样设计）"
    },

    # 3. 使用条件
    "usage_conditions": {
        "prerequisites": ["前置条件（如：必须有完整财报数据）"],
        "limitations": ["限制条件（如：不适用于金融行业）"],
        "parameters": {
            "param_name": {
                "value": "默认值",
                "range": "取值范围",
                "description": "参数说明"
            }
        }
    },

    # ========== 赛马数据 ==========
    "usage_count": 0,
    "accuracy": 0.0,
    "status": "testing",  # testing, active, deprecated

    # ========== 众AI评价 ==========
    "ai_reviews": [
        {
            "reviewer": "评价者（如 FundamentalAnalyzer AI）",
            "reviewed_at": "评价时间",
            "rating": 4.5,  # 1-5星评分
            "comment": "评价内容",
            "usage_context": "使用场景",
            "suggestions": ["改进建议"]
        }
    ],

    # ========== 统计数据 ==========
    "statistics": {
        "avg_rating": 0.0,  # 平均评分
        "total_reviews": 0,  # 总评价数
        "success_rate": 0.0,  # 成功率
        "avg_deviation": 0.0  # 平均偏差
    }
}

# ========== 文件命名标准 ==========

"""
AI生成公式的文件命名标准：

格式：{formula_type}_{purpose}_{version}_{timestamp}.py

示例：
  - composite_score_value_investing_v1_20260314_103000.py
  - safety_margin_graham_v2_20260315_143000.py
  - risk_assessment_fintech_v1_20260316_090000.py

规则：
  1. formula_type: 公式类型（composite_score, safety_margin, risk_assessment）
  2. purpose: 用途关键词（value_investing, graham, fintech）
  3. version: 版本号（v1, v2, v3）
  4. timestamp: 时间戳（YYYYMMDD_HHMMSS）

好处：
  - 文件名可以很长，但不会乱
  - 一眼看出公式类型和用途
  - 版本号清晰
  - 时间戳避免冲突
"""
