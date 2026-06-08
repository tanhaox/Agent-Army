"""
爆款短剧创意原则知识库 - 基于短视频心理机制，而非量化指标。

核心原则：
1. 3秒钩子：开场即抓人，不给用户划走的机会
2. 15秒反转：打破预期，制造认知冲突
3. 身份反差（爽点）：角色隐藏身份/实力暴露，制造极致满足感
4. 情绪落差：从压抑到释放，构建情感张力弧线
5. 信息悬念：已知信息≠角色已知，制造"上帝视角"紧张感
"""

import logging

logger = logging.getLogger(__name__)

# ── 爆款创意原则定义 ──────────────────────────────────────

PRINCIPLES = {
    "three_second_hook": {
        "name": "3秒钩子",
        "weight": 0.25,
        "description": "开场即抓人，不给用户划走的机会",
        "mechanism": "利用好奇心缺口+视觉冲击，在第一帧就建立不可抗拒的观看冲动",
        "examples": [
            "镜头1：一个耳光声先入，画面是一个女人面无表情的侧脸——谁打的？为什么？",
            "镜头1：电话响起，她接起来脸色骤变：'他……还活着？'",
            "镜头1：双手戴着手铐的特写，背景是法官宣判的声音",
            "镜头1：一个女人把婚戒扔进马桶，按下冲水键的特写",
        ],
        "shot_requirements": {
            "shot_type": "特写",
            "camera_move": "推",
            "emotion": "紧张|期待|惊喜",
            "duration_max": 4,
        },
        "check_rules": [
            "第一镜必须是特写或近景",
            "第一镜情绪强度>=7（紧张/恐惧/愤怒/惊喜/期待）",
            "第一镜必须有信息缺口（观众想知道但不知道的事）",
            "第一镜时长<=4秒",
        ],
    },
    "fifteen_second_reversal": {
        "name": "15秒反转",
        "weight": 0.20,
        "description": "每15-20秒制造一次认知颠覆，打破观众预期",
        "mechanism": "利用预测误差——当预测被打破时，多巴胺分泌激增，产生'爽感'",
        "examples": [
            "以为是道歉，结果是挑衅：'对不起，让你以为我会忍你一辈子'",
            "以为是认输，结果是宣战：'我确实什么都没有了，所以现在我什么都不怕'",
            "以为是重逢，原来是复仇：他微笑着走近，手里却攥着一份起诉书",
            "以为是悲剧，结果是转机：她哭是因为终于拿到了证据",
        ],
        "shot_requirements": {
            "position_range": (0.2, 0.4),  # 20%-40%位置
            "emotion_shift": True,  # 前后情绪必须有反差
            "dialogue_pattern": "先铺垫一种预期，对话打破它",
        },
        "check_rules": [
            "每集至少有一处情绪骤转（前后情绪差>=5级）",
            "反转镜头的对话或动作必须打破前一个镜头建立的预期",
            "反转不依赖巧合，而是角色主动行为",
        ],
    },
    "identity_contrast": {
        "name": "身份反差（爽点）",
        "weight": 0.25,
        "description": "隐藏身份/实力暴露，制造极致满足感",
        "mechanism": "利用社交等级重估——当被低估的人展现真实实力时，观众获得代偿性满足",
        "examples": [
            "所有人嘲笑她穷，镜头切到她手机上的银行余额：九位数",
            "他被骂'你算什么东西'，下一秒对方手机响了，老板说：'那是新任总裁'",
            "她被婆婆赶出家门，走出大门时一辆劳斯莱斯停下：'小姐，董事长让您回去'",
            "他穿着破旧工服被人鄙视，镜头慢推到胸口工牌——总工程师",
        ],
        "shot_requirements": {
            "shot_type": "近景→特写（揭露瞬间）",
            "camera_move": "推或拉",
            "emotion_before": "悲伤|愤怒|困惑",
            "emotion_after": "惊喜|期待",
            "vfx_optional": "光效（揭露瞬间加光芒）",
        },
        "check_rules": [
            "每集至少有一个'被低估→实力暴露'的情节节点",
            "揭露镜头必须是近景或特写，聚焦关键道具/表情",
            "身份暴露前必须有至少一个镜头铺垫被轻视/被误解",
        ],
    },
    "emotional_drop": {
        "name": "情绪落差",
        "weight": 0.15,
        "description": "从压抑到释放，构建情感张力弧线",
        "mechanism": "先建立情绪债务（压抑/委屈），再一次性释放，产生放大N倍的爽感",
        "examples": [
            "连续3个镜头展现屈辱（忍），最后一个镜头爆发（不忍了）",
            "温馨回忆画面→突然切回冰冷现实→泪水落下",
            "她一直在笑，但手在颤抖——镜头特写到发抖的手指",
            "所有人都在庆祝，只有他知道明天公司就要破产",
        ],
        "shot_requirements": {
            "structure": "压抑镜头(2-3个) → 爆发镜头(1个)",
            "压抑_shot_type": "中景或近景",
            "爆发_shot_type": "特写",
            "压抑_emotion": "悲伤|困惑|平静",
            "爆发_emotion": "愤怒|惊喜|紧张",
        },
        "check_rules": [
            "每集后半段（60%之后）至少有一个情绪爆发点",
            "爆发前必须有2-3个压抑/隐忍镜头铺垫",
            "爆发镜头景别必须是特写，情绪强度>=8",
        ],
    },
    "information_suspense": {
        "name": "信息悬念",
        "weight": 0.15,
        "description": "已知信息≠角色已知，制造'上帝视角'紧张感",
        "mechanism": "观众知道角色不知道的事，产生'不要开门！'式的强制性关注",
        "examples": [
            "观众看到反派藏在门后，女主角正笑着走向那扇门",
            "他知道她在撒谎（因为看到了证据），但假装相信，镜头给到他握紧的拳头",
            "观众知道主角被跟踪了，主角还在悠闲地走着——突然的脚步声",
            "她收到一条信息：'别回头'——镜头慢推到她身后的人影",
        ],
        "shot_requirements": {
            "structure": "信息交代镜头 → 角色无知行动镜头 → 悬念揭示",
            "information_shot": "远景或全景（交代全局信息）",
            "action_shot": "近景（角色不知情，观众替ta紧张）",
            "end_shot": "结尾必须暗示信息即将揭露",
        },
        "check_rules": [
            "每集结尾必须有一个未解决的悬念（信息差）",
            "结尾情绪必须是期待或紧张",
            "结尾动作必须暗示'即将发生某事'",
        ],
    },
}


def get_principle(principle_id: str) -> dict | None:
    """获取指定原则的详情。"""
    return PRINCIPLES.get(principle_id)


def get_all_principles() -> dict:
    """获取所有原则。"""
    return PRINCIPLES


def get_weighted_principles() -> list[tuple[str, float, dict]]:
    """返回按权重排序的原则列表 [(id, weight, principle)]。"""
    return sorted(
        [(k, v["weight"], v) for k, v in PRINCIPLES.items()],
        key=lambda x: x[1],
        reverse=True,
    )


def build_principles_prompt() -> str:
    """构建给LLM的爆款原则系统提示词。"""
    lines = [
        "你是爆款短剧分镜重构大师。你将基于以下5大爆款心理机制重新设计分镜：\n",
    ]

    for pid, p in PRINCIPLES.items():
        lines.append(f"### {p['name']}（权重{int(p['weight']*100)}%）")
        lines.append(f"机制：{p['mechanism']}")
        lines.append(f"要求：{p['description']}")
        lines.append("示例：")
        for ex in p["examples"][:2]:
            lines.append(f"  - {ex}")
        lines.append("")

    lines.append("### 输出格式")
    lines.append("对每一集，输出5-7个镜头的JSON数组。")

    return "\n".join(lines)
