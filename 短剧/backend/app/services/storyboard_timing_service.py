"""
分镜时长分配与节奏分析服务。

提供自动时长分配、集适配性分析、爆款节奏建议。
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── 景别基础时长 ──────────────────────────────────────────
SHOT_TYPE_DURATION: dict[str, int] = {
    "特写": 3,
    "近景": 3,
    "中景": 5,
    "全景": 5,
    "远景": 7,
}

# ── 运镜时长修正 ──────────────────────────────────────────
CAMERA_MOVE_DURATION_BONUS: dict[str, int] = {
    "固定": 0,
    "推": 1,
    "拉": 1,
    "摇": 0,
    "移": 1,
    "跟": 2,
}

# ── 情绪强度权重（用于关键镜头检测和时长加成）──────────────
EMOTION_INTENSITY: dict[str, float] = {
    "紧张": 0.9,
    "恐惧": 0.9,
    "愤怒": 0.85,
    "惊喜": 0.8,
    "甜蜜": 0.5,
    "喜悦": 0.6,
    "悲伤": 0.7,
    "感动": 0.7,
    "期待": 0.65,
    "困惑": 0.4,
    "平静": 0.3,
}

# ── 悬念/高潮情绪（用于自动标记关键镜头）──────────────────
CLIMAX_EMOTIONS = {"紧张", "恐惧", "愤怒", "惊喜"}
SUSPENSE_EMOTIONS = {"期待", "紧张"}

# ── 默认每集目标时长范围 ──────────────────────────────────
DEFAULT_MIN_DURATION = 60
DEFAULT_MAX_DURATION = 90
DEFAULT_TARGET_DURATION = 75


def auto_assign_durations(
    storyboards: list[dict],
    total_episode_duration: int = DEFAULT_TARGET_DURATION,
) -> list[dict]:
    """
    根据景别、运镜、情绪自动分配每个分镜的预估时长。

    算法：
    1. 计算每个分镜的基础时长（景别 + 运镜修正）
    2. 关键镜头（情绪强度 >= 0.8）额外 +2 秒
    3. 等比缩放使总时长逼近目标

    Args:
        storyboards: 同一集的分镜列表（字典格式）。
        total_episode_duration: 该集目标总时长（秒）。

    Returns:
        更新了 duration_seconds 和 is_key_moment 的分镜列表。
    """
    if not storyboards:
        return storyboards

    # Step 1: 计算原始时长 + 标记关键镜头
    raw_durations = []
    for item in storyboards:
        shot = item.get("shot_type", "中景")
        camera = item.get("camera_move", "固定")
        emotion = item.get("emotion", "平静")

        base = SHOT_TYPE_DURATION.get(shot, 5)
        bonus = CAMERA_MOVE_DURATION_BONUS.get(camera, 0)

        is_key = EMOTION_INTENSITY.get(emotion, 0.3) >= 0.8
        if is_key:
            bonus += 2

        item["is_key_moment"] = is_key
        raw = base + bonus
        item["duration_seconds"] = raw
        raw_durations.append(raw)

    # Step 2: 等比缩放到目标时长
    total_raw = sum(raw_durations)
    if total_raw > 0 and total_raw != total_episode_duration:
        scale = total_episode_duration / total_raw
        for item in storyboards:
            item["duration_seconds"] = max(2, round(item["duration_seconds"] * scale))

    # Step 3: 修正总时长偏差（四舍五入导致）
    actual = sum(item["duration_seconds"] for item in storyboards)
    diff = total_episode_duration - actual
    if diff != 0:
        # 将差值分配给关键镜头（优先）或最后一个镜头
        targets = [i for i, s in enumerate(storyboards) if s.get("is_key_moment")]
        if not targets:
            targets = [len(storyboards) - 1]
        per_target = diff // len(targets)
        remainder = diff - per_target * len(targets)
        for idx in targets:
            storyboards[idx]["duration_seconds"] = max(
                2, storyboards[idx]["duration_seconds"] + per_target
            )
        if remainder:
            storyboards[targets[0]]["duration_seconds"] += remainder

    logger.info(
        "时长分配完成: %d 个分镜, 目标 %ds, 实际 %ds",
        len(storyboards), total_episode_duration,
        sum(s["duration_seconds"] for s in storyboards),
    )
    return storyboards


def analyze_episode_fitness(
    episode_storyboards: list[dict],
    target_min: int = DEFAULT_MIN_DURATION,
    target_max: int = DEFAULT_MAX_DURATION,
) -> dict:
    """
    集适配性分析：检查分镜数量、情绪曲线、时长、悬念。

    Args:
        episode_storyboards: 同一集的分镜列表。

    Returns:
        分析报告 dict，包含 score, issues, suggestions。
    """
    issues: list[str] = []
    suggestions: list[str] = []
    score = 100

    count = len(episode_storyboards)
    ep_no = episode_storyboards[0].get("episode_no", "?") if episode_storyboards else "?"

    # 1. 分镜数量检查（5-12合理范围）
    if count < 5:
        issues.append(f"第{ep_no}集分镜数量偏少({count}个)，建议至少5个以保证叙事节奏")
        score -= 15
    elif count > 12:
        issues.append(f"第{ep_no}集分镜数量过多({count}个)，建议控制在12个以内")
        score -= 10

    # 2. 情绪曲线检查
    emotions = [s.get("emotion", "平静") for s in episode_storyboards]
    intensities = [EMOTION_INTENSITY.get(e, 0.3) for e in emotions]
    max_intensity = max(intensities) if intensities else 0
    has_peak = max_intensity >= 0.8

    if not has_peak:
        issues.append(f"第{ep_no}集缺少情绪高潮点，全集情绪偏平淡")
        suggestions.append("增加一个紧张/惊喜/愤怒的近景反应镜头来制造高潮")
        score -= 20

    # 3. 结尾悬念检查
    if emotions:
        last_emotion = emotions[-1]
        if last_emotion not in SUSPENSE_EMOTIONS and last_emotion not in CLIMAX_EMOTIONS:
            issues.append(f"第{ep_no}集结尾情绪为'{last_emotion}'，缺乏悬念感")
            suggestions.append("结尾增加一个期待/紧张情绪镜头，制造悬念引导下一集")
            score -= 15

    # 4. 总时长检查
    total_duration = sum(s.get("duration_seconds", 5) for s in episode_storyboards)
    if total_duration < target_min:
        issues.append(f"第{ep_no}集总时长{total_duration}秒，低于目标下限{target_min}秒")
        suggestions.append("延长关键镜头时长或增加过渡镜头")
        score -= 15
    elif total_duration > target_max:
        issues.append(f"第{ep_no}集总时长{total_duration}秒，超出目标上限{target_max}秒")
        suggestions.append("缩短远景/固定镜头时长")
        score -= 10

    # 5. 关键镜头分布
    key_count = sum(1 for s in episode_storyboards if s.get("is_key_moment"))
    if key_count == 0:
        suggestions.append("建议标记至少1个关键镜头（高潮/反转），增加其时长")
        score -= 5

    score = max(0, score)

    return {
        "episode_no": ep_no,
        "shot_count": count,
        "total_duration": total_duration,
        "key_moment_count": key_count,
        "emotion_peak": max(intensities) if intensities else 0,
        "has_suspense_ending": emotions[-1] in SUSPENSE_EMOTIONS if emotions else False,
        "score": score,
        "issues": issues,
        "suggestions": suggestions,
    }


def suggest_rhythm_adjustments(
    episodes_storyboards: dict[int, list[dict]],
    total_episodes: int = 0,
) -> dict:
    """
    爆款节奏引擎：分析所有集的情绪分布，建议节奏调整。

    核心规则：
    - 3集短剧：高潮集中在第2-3集
    - 每集结尾悬念镜头时长适当延长
    - 避免全集中情绪平淡
    - 第1集开头需要强吸引力

    Args:
        episodes_storyboards: {集数: [分镜列表]} 的字典。
        total_episodes: 总集数（默认取字典长度）。

    Returns:
        节奏分析报告，含 overall_score, per_episode, global_suggestions。
    """
    if not total_episodes:
        total_episodes = max(episodes_storyboards.keys()) if episodes_storyboards else 0

    # 每集适配性分析
    per_episode: dict[int, dict] = {}
    for ep_no, sbs in sorted(episodes_storyboards.items()):
        per_episode[ep_no] = analyze_episode_fitness(sbs)

    global_suggestions: list[str] = []
    overall_score = sum(ep["score"] for ep in per_episode.values())
    if per_episode:
        overall_score = round(overall_score / len(per_episode))

    if total_episodes == 0:
        return {
            "overall_score": 0,
            "per_episode": {},
            "global_suggestions": ["暂无分镜数据"],
        }

    # 3集短剧节奏规则
    if total_episodes <= 3:
        # 第1集：需要强开场
        ep1 = per_episode.get(1, {})
        if ep1.get("emotion_peak", 0) < 0.7:
            global_suggestions.append(
                "第1集情绪峰值偏低，建议开头增加冲突/惊喜镜头以抓住观众"
            )

        # 第2-3集：应有高潮
        for ep_no in range(2, total_episodes + 1):
            ep = per_episode.get(ep_no, {})
            if ep.get("emotion_peak", 0) < 0.8:
                global_suggestions.append(
                    f"第{ep_no}集缺少情绪高潮，爆款节奏建议在第{ep_no}集加入反转或冲突"
                )

    else:
        # 多集短剧（5-10集）
        mid_point = total_episodes // 2
        mid_ep = per_episode.get(mid_point, {})
        if mid_ep.get("emotion_peak", 0) < 0.8:
            global_suggestions.append(
                f"中间第{mid_point}集缺少高潮，建议在此处安排重大转折"
            )

    # 全集情绪平淡检查
    all_peaks = [ep.get("emotion_peak", 0) for ep in per_episode.values()]
    if all_peaks and max(all_peaks) < 0.7:
        global_suggestions.append(
            "所有集的情绪峰值均偏低，整体节奏偏平淡，建议至少2-3集设置强烈冲突"
        )

    # 每集结尾悬念检查
    no_suspense_eps = [
        ep_no for ep_no, ep in per_episode.items()
        if not ep.get("has_suspense_ending") and ep_no < total_episodes
    ]
    if no_suspense_eps:
        eps_str = "、".join(f"第{e}集" for e in no_suspense_eps[:3])
        global_suggestions.append(
            f"{eps_str}结尾缺乏悬念，建议增加期待/紧张情绪镜头引导下集"
        )

    # 时长一致性
    durations = [ep.get("total_duration", 0) for ep in per_episode.values()]
    if len(durations) >= 2:
        avg_dur = sum(durations) / len(durations)
        inconsistent = [
            ep_no for ep_no, ep in per_episode.items()
            if abs(ep.get("total_duration", 0) - avg_dur) > 15
        ]
        if inconsistent:
            eps_str = "、".join(f"第{e}集" for e in inconsistent[:3])
            global_suggestions.append(
                f"{eps_str}时长与平均差异超过15秒，建议调整以保持系列一致性"
            )

    return {
        "overall_score": overall_score,
        "per_episode": per_episode,
        "global_suggestions": global_suggestions,
    }
