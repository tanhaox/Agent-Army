"""
视觉设定预设库 - 内置爆款短剧风格包。

每种预设包含完整的视觉参数，确保所有角色风格一致。
"""

from typing import Any


class VisualPreset:
    """视觉预设。"""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        settings: dict[str, str],
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.settings = settings


# ==================== 内置预设风格包 ====================

PRESETS: list[VisualPreset] = [
    VisualPreset(
        id="modern_romance",
        name="都市甜宠",
        description="明亮温馨的现代都市风格，适合甜宠/霸总/青春题材",
        settings={
            "art_style": "动漫风格，柔和渲染",
            "era": "modern",
            "environment": "豪华公寓，现代办公室，樱花公园，咖啡厅",
            "lighting": "暖色柔光，黄金时段，自然阳光",
            "color_palette": "粉色，暖白，柔金色",
            "camera_angle": "中景，微俯拍",
            "render_quality": "精细，4K，电影级",
            "global_note": "柔和浪漫氛围，所有角色保持统一的暖色调光影",
        },
    ),
    VisualPreset(
        id="cyberpunk",
        name="赛博朋克",
        description="霓虹闪烁的未来都市，适合科幻/赛博/暗黑题材",
        settings={
            "art_style": "半写实，赛博朋克美学",
            "era": "near_future",
            "environment": "霓虹灯小巷，雨夜街道，全息广告牌，地下俱乐部",
            "lighting": "霓虹辉光，蓝紫色轮廓光，体积雾",
            "color_palette": "霓虹蓝，品红，青色，深紫",
            "camera_angle": "低角度，戏剧性透视",
            "render_quality": "虚幻引擎5，8K，光线追踪，电影级",
            "global_note": "高对比霓虹光影，雨水与反射，统一赛博朋克氛围",
        },
    ),
    VisualPreset(
        id="xianxia_fantasy",
        name="古风仙侠",
        description="水墨风格，仙气缭绕，淡雅色调，适合修真/仙侠/古言题材",
        settings={
            "art_style": "中国水墨画风，空灵飘逸",
            "era": "ancient",
            "environment": "浮空仙岛，竹林，瀑布，天宫",
            "lighting": "柔和月光，灵气光芒，金色光尘",
            "color_palette": "翡翠绿，淡金，墨黑，云白",
            "camera_angle": "远景，优雅构图",
            "render_quality": "精细水墨渲染，4K，电影级，传统国画质感",
            "global_note": "所有角色统一古风仙侠美学，飘逸长袍，灵气光环",
        },
    ),
    VisualPreset(
        id="dark_fantasy",
        name="暗黑玄幻",
        description="深沉暗黑的奇幻风格，适合暗黑/复仇/权谋题材",
        settings={
            "art_style": "暗黑奇幻，精细插画",
            "era": "fantasy",
            "environment": "哥特城堡，暗黑森林，地下王座，血月天空",
            "lighting": "明暗对比布光，火光，不祥辉光",
            "color_palette": "深红，漆黑，暗紫，银色",
            "camera_angle": "戏剧性低角度，倾斜构图",
            "render_quality": "超精细，4K，电影级，压抑氛围",
            "global_note": "暗黑戏剧性基调，所有角色统一哥特奇幻设定",
        },
    ),
    VisualPreset(
        id="wasteland",
        name="末世废土",
        description="荒凉破败的末日风格，适合末世/丧尸/求生题材",
        settings={
            "art_style": "粗粝写实，末世风格",
            "era": "post_apocalyptic",
            "environment": "废墟城市，废弃工厂，沙漠荒原，地下避难所",
            "lighting": "烈日强光，尘雾弥漫，闪烁日光灯",
            "color_palette": "低饱和橙，锈褐，灰烬灰，暗绿",
            "camera_angle": "远景建立镜头，纪实风格",
            "render_quality": "照片级写实，4K，胶片颗粒感，电影级",
            "global_note": "破旧沧桑质感，所有角色展现生存磨损，统一废土氛围",
        },
    ),
    VisualPreset(
        id="campus_youth",
        name="校园青春",
        description="清新明亮的校园风格，适合校园/青春/恋爱题材",
        settings={
            "art_style": "动漫风格，线条干净，明亮色彩",
            "era": "modern",
            "environment": "校园，教室，天台，图书馆，运动场",
            "lighting": "明亮自然光，镜头光晕，柔和阴影",
            "color_palette": "天蓝，草绿，校服白，樱花粉",
            "camera_angle": "平视，柔和构图",
            "render_quality": "干净动漫风，4K，鲜艳色彩",
            "global_note": "明亮青春氛围，所有角色统一校园场景风格",
        },
    ),
    VisualPreset(
        id="steampunk",
        name="蒸汽朋克",
        description="齿轮与蒸汽的机械美学，适合蒸汽朋克/机械/冒险题材",
        settings={
            "art_style": "蒸汽朋克插画，精细机械风",
            "era": "victorian_futurism",
            "environment": "钟表工坊，飞艇甲板，黄铜塔楼，齿轮城市",
            "lighting": "暖色钨丝灯，蒸汽逆光，琥珀色辉光",
            "color_palette": "黄铜金，铜色，红木棕，青蓝点缀",
            "camera_angle": "对称构图，机械框架",
            "render_quality": "精密细节，4K，电影级，金属质感",
            "global_note": "维多利亚机械美学，所有角色穿着蒸汽朋克时代服饰",
        },
    ),
    VisualPreset(
        id="noir_detective",
        name="黑色悬疑",
        description="经典黑白影调的侦探风格，适合悬疑/推理/犯罪题材",
        settings={
            "art_style": "黑色电影风格，高对比",
            "era": "mid_century",
            "environment": "雨夜街道，昏暗办公室，烟雾缭绕的酒吧，阴暗小巷",
            "lighting": "百叶窗阴影，台灯单光源，烟雾弥漫",
            "color_palette": "黑色，白色，银色，暗暖色调",
            "camera_angle": "倾斜角度，特写，戏剧性阴影",
            "render_quality": "胶片颗粒感，4K，黑色电影摄影",
            "global_note": "高对比黑白美学，所有角色统一阴影与悬疑氛围",
        },
    ),
]

# 按 id 索引
_PRESET_MAP: dict[str, VisualPreset] = {p.id: p for p in PRESETS}


def list_presets() -> list[dict[str, Any]]:
    """获取所有预设列表（含 settings）。"""
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "settings": p.settings,
        }
        for p in PRESETS
    ]


def get_preset(preset_id: str) -> dict[str, Any] | None:
    """根据 ID 获取预设。"""
    p = _PRESET_MAP.get(preset_id)
    if p is None:
        return None
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "settings": p.settings,
    }


def get_default_settings() -> dict[str, str]:
    """获取默认视觉设定（都市甜宠风格）。"""
    return {
        "art_style": "动漫风格，精细渲染",
        "era": "modern",
        "environment": "现代都市",
        "lighting": "电影级布光",
        "color_palette": "鲜艳色彩",
        "camera_angle": "中景",
        "render_quality": "精细，4K",
        "global_note": "",
    }


def build_consistency_block(settings: dict[str, str]) -> str:
    """
    根据视觉设定构建一致性的 prompt 后缀。
    所有角色的 image_prompt 都追加此后缀，确保风格统一。
    """
    parts = [
        settings.get("environment", ""),
        settings.get("lighting", ""),
        settings.get("camera_angle", ""),
        settings.get("art_style", ""),
        settings.get("color_palette", ""),
        settings.get("render_quality", "精细，4K"),
    ]
    if settings.get("global_note"):
        parts.append(settings["global_note"])

    return "，".join(p for p in parts if p)
