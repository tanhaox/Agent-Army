"""
爆款元素库 - 系统内置的短剧创作知识库。

提供情绪钩子、反转模式、人设原型、节奏模板等静态数据，
供叙事树生成服务参考。
"""

from typing import Any


# ========== 情绪钩子库 ==========
EMOTION_HOOKS: list[dict[str, str]] = [
    {"name": "悬念开场", "example": "婚礼现场，新郎突然喊了另一个女人的名字"},
    {"name": "暴力冲突", "example": "一巴掌打过去，全场安静了"},
    {"name": "身份反转", "example": "外卖员摘下头盔，竟是千亿集团继承人"},
    {"name": "情感撕裂", "example": "看着手机里的诊断书，她决定隐瞒病情"},
    {"name": "极致羞辱", "example": "婆婆当众把嫁妆扔出大门"},
    {"name": "意外重逢", "example": "五年后的商业谈判桌上，对面坐着前夫"},
    {"name": "生死抉择", "example": "火灾现场，只能救一个：母亲还是孩子"},
    {"name": "秘密曝光", "example": "整理遗物时发现父亲留下的惊天秘密"},
    {"name": "权力碾压", "example": "董事长视察，总经理跪下喊了一声爸"},
    {"name": "甜蜜陷阱", "example": "他送的项链里藏着微型摄像头"},
]


# ========== 反转模式库 ==========
PLOT_TWISTS: list[dict[str, str]] = [
    {"name": "身份互换", "description": "主角和对手的真实身份与表面完全相反", "scenario": "都市、豪门"},
    {"name": "时间循环", "description": "重复经历同一天，每次发现新线索", "scenario": "悬疑、奇幻"},
    {"name": "真假替换", "description": "关键人物被冒充，真假难辨", "scenario": "豪门、宫斗"},
    {"name": "善意背叛", "description": "最亲近的人出于善意做出毁灭性决定", "scenario": "家庭、情感"},
    {"name": "受害者反转", "description": "受害者其实是幕后操纵者", "scenario": "悬疑、复仇"},
    {"name": "双重间谍", "description": "双方都以为对方是自己的棋子", "scenario": "商战、谍战"},
    {"name": "记忆欺骗", "description": "主角的核心记忆被篡改或虚构", "scenario": "心理、科幻"},
    {"name": "世代复仇", "description": "当前冲突是上一代恩怨的延续", "scenario": "豪门、家族"},
    {"name": "牺牲假象", "description": "看似牺牲实际是为更大计划的铺垫", "scenario": "情感、英雄"},
    {"name": "爱情交易", "description": "真爱原来是精心设计的商业布局", "scenario": "都市、豪门"},
    {"name": "生死互换", "description": "以为死去的人其实活着，反之亦然", "scenario": "悬疑、情感"},
    {"name": "道德困境", "description": "正确选择导致最坏结果", "scenario": "现实主义"},
    {"name": "预言自证", "description": "为避免预言做出的行为恰好实现预言", "scenario": "奇幻、悬疑"},
    {"name": "信任崩塌", "description": "证据指向无辜者，真正罪人逍遥法外", "scenario": "律政、悬疑"},
    {"name": "价值颠覆", "description": "最终发现追求的目标本身毫无意义", "scenario": "成长、哲理"},
    {"name": "敌友转换", "description": "敌人变成最强盟友，盟友变成最大敌人", "scenario": "商战、武侠"},
    {"name": "隐藏血统", "description": "普通人的身世牵动整个格局", "scenario": "豪门、奇幻"},
    {"name": "善有恶报", "description": "善良行为意外导致灾难性后果", "scenario": "现实主义"},
    {"name": "平行人生", "description": "同一个人的不同选择导致截然不同的人生", "scenario": "都市、奇幻"},
    {"name": "末路救赎", "description": "反派的最后一刻展现出人性光辉", "scenario": "情感、英雄"},
]


# ========== 人设原型库 ==========
CHARACTER_ARCHETYPES: list[dict[str, str]] = [
    {"name": "隐藏大佬", "trait": "表面平凡，实际权势滔天，关键时刻展露实力碾压对手"},
    {"name": "倔强小白", "trait": "出身平凡但性格坚韧，不服输，靠努力逆袭"},
    {"name": "双面甜心", "trait": "外表甜美无害，内心精明算计，目标明确"},
    {"name": "冷面守护", "trait": "表面冷漠疏离，实际默默守护在意的人"},
    {"name": "疯批美人", "trait": "行事出人意料，不按常理出牌，美丽且危险"},
    {"name": "复仇天使", "trait": "曾遭受巨大伤害，归来后精心策划复仇"},
    {"name": "纯真催化剂", "trait": "本人无城府，但存在本身改变周围所有人"},
    {"name": "伪善精英", "trait": "社会地位高，形象完美，但内心扭曲或藏着秘密"},
    {"name": "悲情英雄", "trait": "能力出众但命运多舛，总在牺牲与坚持间挣扎"},
    {"name": "搅局者", "trait": "不站任何阵营，凭直觉行事，打破所有规则"},
]


# ========== 节奏模板库 ==========
RHYTHM_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "快节奏3集",
        "episodes": 3,
        "pattern": [
            {"episode": 1, "core_conflict": "开篇钩子 + 核心矛盾爆发", "intensity": 9},
            {"episode": 2, "core_conflict": "反转升级 + 情感撕裂", "intensity": 10},
            {"episode": 3, "core_conflict": "终极对决 + 意外结局", "intensity": 8},
        ],
    },
    {
        "name": "经典5集",
        "episodes": 5,
        "pattern": [
            {"episode": 1, "core_conflict": "悬念开场 + 建立对立", "intensity": 7},
            {"episode": 2, "core_conflict": "冲突升级 + 初次交锋", "intensity": 8},
            {"episode": 3, "core_conflict": "大反转 + 陷入低谷", "intensity": 9},
            {"episode": 4, "core_conflict": "反击布局 + 情感高潮", "intensity": 10},
            {"episode": 5, "core_conflict": "终局对决 + 真相大白", "intensity": 8},
        ],
    },
    {
        "name": "长线10集",
        "episodes": 10,
        "pattern": [
            {"episode": 1, "core_conflict": "引人入胜的开场", "intensity": 7},
            {"episode": 2, "core_conflict": "建立人物关系网", "intensity": 6},
            {"episode": 3, "core_conflict": "第一次大冲突", "intensity": 8},
            {"episode": 4, "core_conflict": "暗线浮现 + 小反转", "intensity": 7},
            {"episode": 5, "core_conflict": "中段高潮 + 大反转", "intensity": 9},
            {"episode": 6, "core_conflict": "低谷与反思", "intensity": 6},
            {"episode": 7, "core_conflict": "新对手出现 + 升级", "intensity": 8},
            {"episode": 8, "core_conflict": "连环反转 + 信任崩塌", "intensity": 9},
            {"episode": 9, "core_conflict": "反击 + 情感爆发", "intensity": 10},
            {"episode": 10, "core_conflict": "终极对决 + 圆满收尾", "intensity": 8},
        ],
    },
    {
        "name": "甜蜜3集",
        "episodes": 3,
        "pattern": [
            {"episode": 1, "core_conflict": "欢喜冤家初遇 + 误会", "intensity": 5},
            {"episode": 2, "core_conflict": "共同经历 + 暧昧升级", "intensity": 7},
            {"episode": 3, "core_conflict": "表白 + 甜蜜大结局", "intensity": 6},
        ],
    },
    {
        "name": "虐心5集",
        "episodes": 5,
        "pattern": [
            {"episode": 1, "core_conflict": "命中注定的相遇", "intensity": 6},
            {"episode": 2, "core_conflict": "甜蜜期 + 隐藏危机", "intensity": 7},
            {"episode": 3, "core_conflict": "误会爆发 + 被迫分离", "intensity": 9},
            {"episode": 4, "core_conflict": "互相折磨 + 真相浮现", "intensity": 10},
            {"episode": 5, "core_conflict": "和解 + 追悔莫及", "intensity": 8},
        ],
    },
]


# ========== 辅助方法 ==========

def get_hook_names() -> list[str]:
    """获取所有情绪钩子名称。"""
    return [h["name"] for h in EMOTION_HOOKS]


def get_twist_names() -> list[str]:
    """获取所有反转模式名称。"""
    return [t["name"] for t in PLOT_TWISTS]


def get_archetype_names() -> list[str]:
    """获取所有人设原型名称。"""
    return [a["name"] for a in CHARACTER_ARCHETYPES]


def build_library_context() -> str:
    """
    构建供 AI 提示词参考的爆款知识库摘要。

    Returns:
        格式化的知识库文本，可直接嵌入系统提示词。
    """
    lines = ["【爆款元素参考】"]

    lines.append("\n可选开场钩子：" + "、".join(get_hook_names()))
    lines.append("可选反转模式：" + "、".join(get_twist_names()[:10]))
    lines.append("可选人设原型：" + "、".join(get_archetype_names()))

    lines.append("\n可选标签（每个节点至少选1个，兄弟节点用不同标签）：")
    lines.append("严重、普通、脑洞、反转、狗血、甜蜜、虐心、高概念、爽文、悬疑")

    lines.append("\n评分分布要求（同一父节点的子节点之间必须有区分度）：")
    lines.append("- 8-10分：强冲突、高反转、出人意料、爽感强（必须有至少1个）")
    lines.append("- 5-7分：有吸引力但套路化")
    lines.append("- 1-4分：平淡可预测（必须有至少1个，用于对比）")
    lines.append("- 禁止所有子节点评分相同或集中在5-7分！")

    return "\n".join(lines)
