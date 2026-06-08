"""
短视频爆款分镜审核标准 - 多维度量化评估。

评估维度：情绪曲线、注意力钩子、结尾悬念、镜头多样性、
关键镜头分布、总时长与数量、视觉节奏匹配。
"""

import logging
import math
from collections import Counter

logger = logging.getLogger(__name__)

# ── 情绪强度映射（0-10）───────────────────────────────────
EMOTION_INTENSITY: dict[str, int] = {
    "紧张": 9, "恐惧": 9, "愤怒": 8, "惊喜": 8,
    "期待": 7, "感动": 6, "悲伤": 5, "喜悦": 5,
    "甜蜜": 4, "困惑": 3, "平静": 2,
}

# ── 快速动作关键词（应配短镜头 ≤4s）───────────────────────
FAST_ACTION_KEYWORDS = ("奔跑", "追赶", "冲出", "打斗", "搏斗", "闪避", "飞起", "跳跃", "拔剑", "出手", "转身")
# ── 慢速动作关键词（应配长镜头 ≥6s）───────────────────────
SLOW_ACTION_KEYWORDS = ("凝视", "回忆", "沉默", "沉思", "等待", "缓步", "叹息", "泪流")

# ── 默认目标范围 ──────────────────────────────────────────
TARGET_MIN_DURATION = 60
TARGET_MAX_DURATION = 90
TARGET_MIN_SHOTS = 5
TARGET_MAX_SHOTS = 8


def calculate_emotion_intensity(emotion: str) -> int:
    """情绪到强度映射（0-10）。"""
    return EMOTION_INTENSITY.get(emotion, 3)


def _evaluate_emotion_curve(items: list[dict]) -> tuple[int, list[str]]:
    """情绪曲线起伏评估。"""
    if len(items) < 2:
        return 60, ["分镜数不足，无法评估情绪曲线"]

    intensities = [calculate_emotion_intensity(it.get("emotion", "平静")) for it in items]
    avg = sum(intensities) / len(intensities)
    max_val = max(intensities)

    issues = []
    score = 100

    if max_val < avg * 1.5:
        issues.append("情绪曲线缺乏明显波峰，建议增加一个高强度情绪镜头（紧张/愤怒/惊喜）")
        score -= 30
    if max(intensities) - min(intensities) < 3:
        issues.append("情绪起伏幅度过小，建议增加情绪对比（如平静→紧张的突转）")
        score -= 20

    return max(0, score), issues


def _evaluate_hook_density(items: list[dict]) -> tuple[int, list[str]]:
    """注意力钩子密度评估。"""
    if not items:
        return 0, ["无分镜数据"]

    total_duration = sum(it.get("duration_seconds", 5) for it in items)
    hook_points = 0

    for it in items:
        if it.get("is_key_moment"):
            hook_points += 1
        if it.get("vfx") and it["vfx"] != "无":
            hook_points += 1
        intensity = calculate_emotion_intensity(it.get("emotion", "平静"))
        if intensity >= 8:
            hook_points += 1

    # 期望每15秒至少1个钩子
    expected_hooks = max(1, total_duration / 15)
    ratio = hook_points / expected_hooks if expected_hooks > 0 else 0

    issues = []
    if ratio < 0.5:
        issues.append(f"注意力钩子不足（当前{hook_points}个，建议{int(expected_hooks)}个以上），增加特效或强烈情绪镜头")
    elif ratio < 0.8:
        issues.append("钩子密度偏低，可考虑在关键转折处增加特效或反应镜头")

    score = min(100, int(ratio * 100))
    return max(0, score), issues


def _evaluate_ending_suspense(items: list[dict], is_last_episode: bool = False) -> tuple[int, list[str]]:
    """结尾悬念强度评估。"""
    if not items:
        return 0, ["无分镜数据"]

    last = items[-1]
    last_emotion = last.get("emotion", "平静")
    last_action = last.get("action", "")
    issues = []
    score = 100

    if is_last_episode:
        return score, []

    emotion_strength = calculate_emotion_intensity(last_emotion)
    suspense_keywords = ("悬念", "秘密", "真相", "突然", "意外", "发现", "转身", "凝视")

    has_suspense_emotion = emotion_strength >= 7
    has_suspense_action = any(kw in last_action for kw in suspense_keywords)

    if not has_suspense_emotion and not has_suspense_action:
        issues.append(f"结尾缺乏悬念（情绪='{last_emotion}'），建议改为期待/紧张情绪或添加暗示性动作")
        score -= 40
    elif not has_suspense_emotion:
        issues.append("结尾情绪偏弱，建议提升为期待或紧张情绪增强悬念感")
        score -= 15

    return max(0, score), issues


def _evaluate_shot_diversity(items: list[dict]) -> tuple[int, list[str]]:
    """镜头多样性评估。"""
    if not items:
        return 0, ["无分镜数据"]

    shot_types = set(it.get("shot_type", "中景") for it in items)
    camera_moves = set(it.get("camera_move", "固定") for it in items)
    durations = [it.get("duration_seconds", 5) for it in items]

    issues = []
    score = 100

    if len(shot_types) < 3:
        issues.append(f"景别种类偏少（{len(shot_types)}种），建议使用≥3种景别增加视觉变化")
        score -= 20

    if len(camera_moves) < 2:
        issues.append(f"运镜种类偏少（{len(camera_moves)}种），建议混合使用推/拉/摇/跟增加动感")
        score -= 20

    if len(durations) >= 3:
        std_dev = math.sqrt(sum((d - sum(durations) / len(durations)) ** 2 for d in durations) / len(durations))
        if std_dev < 1.5:
            issues.append("镜头时长过于均匀，建议关键镜头适当延长以制造节奏变化")
            score -= 15

    return max(0, score), issues


def _evaluate_key_moment_placement(items: list[dict]) -> tuple[int, list[str]]:
    """关键镜头分布评估。"""
    if not items:
        return 0, ["无分镜数据"]

    key_positions = [i / len(items) for i, it in enumerate(items) if it.get("is_key_moment")]
    issues = []
    score = 100

    if not key_positions:
        issues.append("未标记任何关键镜头，建议在高潮/反转处标记关键镜头")
        return 40, issues

    has_peak = any(0.5 <= p <= 0.85 for p in key_positions)
    if not has_peak:
        issues.append("关键镜头不在高潮区间（50%-85%进度），建议将关键镜头调整到每集中后段")
        score -= 25

    return max(0, score), issues


def _evaluate_duration_and_count(items: list[dict]) -> tuple[int, list[str]]:
    """总时长与分镜数量评估。"""
    if not items:
        return 0, ["无分镜数据"]

    total = sum(it.get("duration_seconds", 5) for it in items)
    count = len(items)
    issues = []
    score = 100

    if total < TARGET_MIN_DURATION:
        issues.append(f"总时长{total}秒低于{TARGET_MIN_DURATION}秒下限")
        score -= 20
    elif total > TARGET_MAX_DURATION:
        issues.append(f"总时长{total}秒超出{TARGET_MAX_DURATION}秒上限")
        score -= 15

    if count < TARGET_MIN_SHOTS:
        issues.append(f"分镜数量{count}个偏少（建议{TARGET_MIN_SHOTS}-{TARGET_MAX_SHOTS}个）")
        score -= 15
    elif count > TARGET_MAX_SHOTS + 4:
        issues.append(f"分镜数量{count}个偏多，建议精简")
        score -= 10

    return max(0, score), issues


def _evaluate_visual_rhythm(items: list[dict]) -> tuple[int, list[str]]:
    """视觉节奏匹配评估。"""
    if not items:
        return 0, ["无分镜数据"]

    mismatches = 0
    issues = []

    for it in items:
        action = it.get("action", "")
        duration = it.get("duration_seconds", 5)
        is_fast = any(kw in action for kw in FAST_ACTION_KEYWORDS)
        is_slow = any(kw in action for kw in SLOW_ACTION_KEYWORDS)

        if is_fast and duration > 5:
            mismatches += 1
        elif is_slow and duration < 5:
            mismatches += 1

    if mismatches > 0:
        issues.append(f"{mismatches}个镜头的动作节奏与时长不匹配（快速动作应用短镜头，慢动作用长镜头）")

    score = max(0, 100 - mismatches * 15)
    return score, issues


# ── 维度权重 ──────────────────────────────────────────────
DIMENSION_WEIGHTS = {
    "emotion_curve": 0.20,
    "hook_density": 0.15,
    "ending_suspense": 0.15,
    "shot_diversity": 0.15,
    "key_moment_placement": 0.10,
    "duration_and_count": 0.15,
    "visual_rhythm": 0.10,
}


def evaluate_episode(items: list[dict], is_last_episode: bool = False) -> dict:
    """
    评估单集分镜质量。

    Returns:
        {
            "score": 78,
            "dimensions": {"emotion_curve": 90, ...},
            "issues": [...],
            "suggestions": [...]
        }
    """
    evaluators = {
        "emotion_curve": lambda: _evaluate_emotion_curve(items),
        "hook_density": lambda: _evaluate_hook_density(items),
        "ending_suspense": lambda: _evaluate_ending_suspense(items, is_last_episode),
        "shot_diversity": lambda: _evaluate_shot_diversity(items),
        "key_moment_placement": lambda: _evaluate_key_moment_placement(items),
        "duration_and_count": lambda: _evaluate_duration_and_count(items),
        "visual_rhythm": lambda: _evaluate_visual_rhythm(items),
    }

    dimensions: dict[str, int] = {}
    all_issues: list[str] = []

    for dim_name, evaluator in evaluators.items():
        dim_score, dim_issues = evaluator()
        dimensions[dim_name] = dim_score
        all_issues.extend(dim_issues)

    weighted_score = sum(
        dimensions[k] * w for k, w in DIMENSION_WEIGHTS.items()
    )
    overall = round(weighted_score)

    suggestions = _generate_suggestions(dimensions, all_issues)

    return {
        "episode": items[0].get("episode_no", "?") if items else "?",
        "shot_count": len(items),
        "total_duration": sum(it.get("duration_seconds", 5) for it in items),
        "score": overall,
        "dimensions": dimensions,
        "issues": all_issues,
        "suggestions": suggestions,
    }


def _generate_suggestions(dimensions: dict[str, int], issues: list[str]) -> list[str]:
    """根据弱项生成可执行建议。"""
    suggestions = []

    if dimensions.get("emotion_curve", 100) < 70:
        suggestions.append("在每集中后段插入一个近景/特写的高强度情绪镜头（紧张/愤怒/惊喜）")
    if dimensions.get("hook_density", 100) < 60:
        suggestions.append("增加特效镜头或关键转折的反应镜头，保持每15秒至少一个注意力钩子")
    if dimensions.get("ending_suspense", 100) < 70:
        suggestions.append("将每集最后一镜的情绪改为期待/紧张，动作加入暗示性描述")
    if dimensions.get("shot_diversity", 100) < 70:
        suggestions.append("混合使用远景/中景/特写和推/摇/跟运镜，避免视觉单调")
    if dimensions.get("key_moment_placement", 100) < 70:
        suggestions.append("在每集60%-80%进度处安排关键镜头（反转/高潮）")
    if dimensions.get("visual_rhythm", 100) < 70:
        suggestions.append("快速动作镜头压缩到3-4秒，慢动作镜头延长到6-8秒")

    if not suggestions and not issues:
        suggestions.append("该集节奏良好，无需调整")

    return suggestions


def evaluate_project(
    storyboards_by_episode: dict[int, list[dict]],
) -> dict:
    """
    评估整个项目分镜质量。

    Args:
        storyboards_by_episode: {集数: [分镜列表]}

    Returns:
        完整审核报告。
    """
    total_episodes = max(storyboards_by_episode.keys()) if storyboards_by_episode else 0
    episodes_report: list[dict] = []

    for ep_no, items in sorted(storyboards_by_episode.items()):
        report = evaluate_episode(items, is_last_episode=(ep_no == total_episodes))
        episodes_report.append(report)

    overall_score = 0
    if episodes_report:
        overall_score = round(sum(ep["score"] for ep in episodes_report) / len(episodes_report))

    global_suggestions: list[str] = []
    weak_eps = [ep for ep in episodes_report if ep["score"] < 70]
    if weak_eps:
        ep_nums = ", ".join(f"第{ep['episode']}集" for ep in weak_eps)
        global_suggestions.append(f"{ep_nums}评分偏低（<70），建议优先优化")

    emotion_low = [ep for ep in episodes_report if ep["dimensions"].get("emotion_curve", 100) < 60]
    if emotion_low:
        ep_nums = ", ".join(f"第{ep['episode']}集" for ep in emotion_low)
        global_suggestions.append(f"{ep_nums}情绪曲线偏平淡，建议增加情绪反转")

    return {
        "overall_score": overall_score,
        "episodes": episodes_report,
        "global_suggestions": global_suggestions,
    }
