"""
分镜规则库 - 动作-运镜映射、禁止组合、推荐修正。

用于后处理校验，自动修正不合理的分镜参数。
"""

import logging

logger = logging.getLogger(__name__)

# 动作关键词 → 推荐运镜（按优先级排序，匹配第一个命中的）
ACTION_TO_CAMERA_MAP: dict[str, str] = {
    "破空": "推",
    "爆炸": "推",
    "冲出": "跟",
    "冲向": "跟",
    "冲入": "跟",
    "奔跑": "跟",
    "逃跑": "跟",
    "追赶": "跟",
    "走进": "推",
    "走近": "推",
    "靠近": "推",
    "靠近镜头": "推",
    "退后": "拉",
    "远离": "拉",
    "后退": "拉",
    "离开": "拉",
    "转身": "摇",
    "回头": "摇",
    "环顾": "摇",
    "扫视": "摇",
    "眺望": "摇",
    "出现": "固定",
    "消失": "拉",
    "浮现": "固定",
    "显现": "固定",
    "站起": "推",
    "坐下": "拉",
    "倒下": "拉",
    "摔倒": "拉",
    "抬头": "推",
    "低头": "拉",
    "握手": "推",
    "拥抱": "固定",
    "打斗": "移",
    "搏斗": "移",
    "闪避": "移",
    "飞起": "跟",
    "跳跃": "跟",
    "飞行": "跟",
    "下坠": "跟",
    "沉默": "固定",
    "凝视": "固定",
    "微笑": "固定",
    "哭泣": "推",
    "怒吼": "推",
    "大喊": "推",
    "低语": "推",
    "颤抖": "固定",
    "发光": "固定",
    "闪烁": "固定",
    "变暗": "固定",
}

# 禁止的 (shot_type, camera_move) 组合
FORBIDDEN_COMBINATIONS: set[tuple[str, str]] = {
    ("远景", "推"),     # 远景推镜头效果不明显
    ("远景", "拉"),     # 远景拉镜头冗余
    ("特写", "摇"),     # 特写摇镜头不合理
    ("特写", "移"),     # 特写移镜头不稳
    ("全景", "推"),     # 全景推镜头建议改为中景推
}

# 不合理组合的修正建议
SUGGESTION_MAP: dict[tuple[str, str], tuple[str, str]] = {
    ("远景", "推"): ("中景", "推"),
    ("远景", "拉"): ("全景", "拉"),
    ("特写", "摇"): ("近景", "摇"),
    ("特写", "移"): ("近景", "移"),
    ("全景", "推"): ("中景", "推"),
}


def suggest_camera_move(action_text: str) -> str | None:
    """
    根据动作文本推荐运镜方式。

    Args:
        action_text: 动作描述文本。

    Returns:
        推荐的运镜方式，或 None（无匹配）。
    """
    if not action_text:
        return None
    for keyword, camera in ACTION_TO_CAMERA_MAP.items():
        if keyword in action_text:
            return camera
    return None


def validate_storyboard(
    shot_type: str,
    camera_move: str,
    action: str,
) -> tuple[bool, str]:
    """
    校验分镜参数是否合理。

    Args:
        shot_type: 景别。
        camera_move: 运镜方式。
        action: 动作描述。

    Returns:
        (is_valid, suggestion) 元组。
        is_valid 为 True 表示参数合理；
        is_valid 为 False 时 suggestion 包含修正建议。
    """
    # 检查禁止组合
    combo = (shot_type, camera_move)
    if combo in FORBIDDEN_COMBATIONS:
        fix = SUGGESTION_MAP.get(combo)
        if fix:
            return False, f"景别「{shot_type}」与运镜「{camera_move}」冲突，建议改为：景别「{fix[0]}」运镜「{fix[1]}」"
        return False, f"景别「{shot_type}」与运镜「{camera_move}」组合不合理"

    # 检查动作与运镜是否匹配
    suggested = suggest_camera_move(action)
    if suggested and suggested != camera_move:
        return False, f"动作「{action[:20]}」更适合运镜「{suggested}」，当前为「{camera_move}」"

    return True, ""


def validate_and_fix_storyboard(item: dict) -> list[str]:
    """
    校验并自动修正单个分镜的不合理参数。

    Args:
        item: 分镜数据字典（会被就地修改）。

    Returns:
        警告消息列表（空表示无需修正）。
    """
    warnings: list[str] = []

    shot_type = item.get("shot_type", "中景")
    camera_move = item.get("camera_move", "固定")
    action = item.get("action", "")

    # 1. 检查禁止组合并自动修正
    combo = (shot_type, camera_move)
    if combo in SUGGESTION_MAP:
        fix_shot, fix_camera = SUGGESTION_MAP[combo]
        warnings.append(
            f"第{item.get('episode_no', '?')}集第{item.get('shot_no', '?')}镜: "
            f"景别「{shot_type}」+运镜「{camera_move}」→ 自动修正为 景别「{fix_shot}」+运镜「{fix_camera}」"
        )
        item["shot_type"] = fix_shot
        item["camera_move"] = fix_camera

    # 2. 检查动作与运镜匹配，仅记录警告不强制修改（保留创作灵活性）
    suggested = suggest_camera_move(action)
    if suggested and suggested != item.get("camera_move"):
        warnings.append(
            f"第{item.get('episode_no', '?')}集第{item.get('shot_no', '?')}镜: "
            f"动作建议使用运镜「{suggested}」，当前为「{item['camera_move']}」"
        )

    return warnings
