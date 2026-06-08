"""
素材引用解析器 — 从提示词中提取多类型引用并解析为图片。

支持引用语法：
  @角色名          → 引用角色基准图
  @场景:场景名      → 引用场景背景图
  @道具:道具名      → 引用道具图
  @素材:素材名      → 引用已生成素材图

多图引用时，将参考图水平拼接后传入图生图 API。
"""

import logging
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.project_service import list_project_characters

logger = logging.getLogger(__name__)

# ── 引用正则 ──────────────────────────────────────────────
# 优先匹配带前缀的长格式，再匹配裸 @角色名
_SCENES_PATTERN = re.compile(r"@场景:([\w\u4e00-\u9fff]{1,30})")
_PROPS_PATTERN = re.compile(r"@道具:([\w\u4e00-\u9fff]{1,30})")
_MATERIAL_PATTERN = re.compile(r"@素材:([\w\u4e00-\u9fff]{1,30})")
_CHAR_PATTERN = re.compile(r"@([\u4e00-\u9fffa-zA-Z]{2,20})")
_ALL_REF_PATTERN = re.compile(r"@(?:场景|道具|素材):[\w\u4e00-\u9fff]+|@[\u4e00-\u9fffa-zA-Z]{2,20}")


class ResolvedRef:
    """解析后的引用项。"""
    __slots__ = ("ref_type", "name", "image_url", "image_bytes", "mark")

    def __init__(self, ref_type: str, name: str, image_url: str, mark: str):
        self.ref_type = ref_type
        self.name = name
        self.image_url = image_url
        self.image_bytes: bytes | None = None
        self.mark = mark


def parse_references(prompt: str) -> tuple[str, list[dict[str, str]]]:
    """
    解析提示词中的所有引用标记。

    Returns:
        (clean_prompt, refs) — 清理后的提示词和引用对象列表。
        每个引用对象: {"type": ..., "name": ..., "mark": ...}
    """
    refs: list[dict[str, str]] = []
    seen_marks: set[str] = set()

    # 1) @场景:名称
    for m in _SCENES_PATTERN.finditer(prompt):
        name = m.group(1)
        mark = m.group(0)
        if mark not in seen_marks:
            seen_marks.add(mark)
            refs.append({"type": "scene", "name": name, "mark": mark})

    # 2) @道具:名称
    for m in _PROPS_PATTERN.finditer(prompt):
        name = m.group(1)
        mark = m.group(0)
        if mark not in seen_marks:
            seen_marks.add(mark)
            refs.append({"type": "prop", "name": name, "mark": mark})

    # 3) @素材:名称
    for m in _MATERIAL_PATTERN.finditer(prompt):
        name = m.group(1)
        mark = m.group(0)
        if mark not in seen_marks:
            seen_marks.add(mark)
            refs.append({"type": "material", "name": name, "mark": mark})

    # 4) @角色名（排除已被前三种匹配的）
    for m in _CHAR_PATTERN.finditer(prompt):
        name = m.group(1)
        # 排除 "场景"、"道具"、"素材" 等前缀词
        if name in ("场景", "道具", "素材"):
            continue
        mark = m.group(0)
        if mark not in seen_marks:
            seen_marks.add(mark)
            refs.append({"type": "character", "name": name, "mark": mark})

    # 清理提示词：只移除 @ 符号，保留角色/素材名称
    # @场景:名称 → 场景:名称, @道具:名称 → 道具:名称, @素材:名称 → 素材:名称, @角色 → 角色
    clean = re.sub(r"@(场景|道具|素材):", r"\1:", prompt)
    clean = re.sub(r"@([\u4e00-\u9fffa-zA-Z]{2,20})", r"\1", clean)
    clean = clean.strip()
    # 压缩多余空格
    clean = re.sub(r"\s{2,}", " ", clean)

    return clean, refs


async def resolve_references(
    db: AsyncSession,
    project_id: str,
    refs: list[dict[str, str]],
) -> list[ResolvedRef]:
    """
    将引用列表解析为带图片的 ResolvedRef 列表。

    对每种引用类型采用不同的查找策略：
    - character → list_project_characters
    - scene/prop/material → 遍历项目 pregen_materials
    """
    if not refs:
        return []

    resolved: list[ResolvedRef] = []

    # 按类型分组
    char_refs = [r for r in refs if r["type"] == "character"]
    other_refs = [r for r in refs if r["type"] != "character"]

    # ── 解析角色引用 ──
    if char_refs:
        char_names = [r["name"] for r in char_refs]
        char_map = await _build_character_map(db, project_id, char_names)
        for r in char_refs:
            url = char_map.get(r["name"])
            if not url:
                logger.warning("未找到角色: %s", r["name"])
                continue
            rr = ResolvedRef("character", r["name"], url, r["mark"])
            rr.image_bytes = _load_image(url)
            if rr.image_bytes:
                resolved.append(rr)
                logger.info("角色引用已解析: %s -> %s", r["name"], url)

    # ── 解析场景/道具/素材引用 ──
    if other_refs:
        material_map = await _build_material_map(db, project_id)
        for r in other_refs:
            url = material_map.get((r["type"], r["name"]))
            if not url:
                # 尝试模糊匹配
                url = _fuzzy_match_material(material_map, r["type"], r["name"])
            if not url:
                logger.warning("未找到%s: %s", r["type"], r["name"])
                continue
            rr = ResolvedRef(r["type"], r["name"], url, r["mark"])
            rr.image_bytes = _load_image(url)
            if rr.image_bytes:
                resolved.append(rr)
                logger.info("%s引用已解析: %s -> %s", r["type"], r["name"], url)

    return resolved


def build_reference_description(resolved: list[ResolvedRef]) -> str:
    """
    为已解析的引用列表生成参考图布局说明，附加到提示词中。

    当多张参考图拼接为一张传入 img2img 时，模型需要知道拼接布局
    才能正确区分不同角色/素材。
    """
    if not resolved or len(resolved) <= 1:
        return ""

    parts: list[str] = []
    for i, ref in enumerate(resolved):
        position = "左侧" if i == 0 else ("右侧" if i == len(resolved) - 1 and len(resolved) == 2 else f"第{i+1}张")
        label = ref.name
        if ref.ref_type == "character":
            label = f"角色「{ref.name}」"
        elif ref.ref_type == "scene":
            label = f"场景「{ref.name}」"
        elif ref.ref_type == "prop":
            label = f"道具「{ref.name}」"
        parts.append(f"{position}为{label}")

    desc = "。参考图由多张图片水平拼接：" + "，".join(parts)
    return desc


def stitch_images(image_list: list[bytes], target_height: int = 1024) -> bytes | None:
    """
    将多张参考图水平拼接为一张。

    统一缩放至相同高度，保持宽高比，然后水平拼接。
    最多取前 3 张。

    Returns:
        拼接后的 JPEG 字节，失败返回 None。
    """
    if not image_list:
        return None
    if len(image_list) == 1:
        return image_list[0]

    try:
        from PIL import Image
        import io
    except ImportError:
        logger.warning("Pillow 未安装，无法拼接图片，仅使用第一张")
        return image_list[0]

    images: list[Image.Image] = []
    for img_bytes in image_list[:3]:
        try:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            images.append(img)
        except Exception as e:
            logger.warning("打开参考图失败: %s", e)
            continue

    if not images:
        return None
    if len(images) == 1:
        return image_list[0]

    # 统一高度
    resized: list[Image.Image] = []
    total_width = 0
    for img in images:
        ratio = target_height / img.height
        new_w = int(img.width * ratio)
        resized.append(img.resize((new_w, target_height), Image.LANCZOS))
        total_width += new_w

    # 水平拼接
    canvas = Image.new("RGB", (total_width, target_height), (0, 0, 0))
    x_offset = 0
    for img in resized:
        canvas.paste(img, (x_offset, 0))
        x_offset += img.width

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=90)
    logger.info("参考图拼接完成: %d张 -> %dx%d", len(resized), total_width, target_height)
    return buf.getvalue()


# ── 内部辅助 ──────────────────────────────────────────────

async def _build_character_map(
    db: AsyncSession,
    project_id: str,
    names: list[str],
) -> dict[str, str]:
    """构建 角色名 -> base_image_url 映射。"""
    char_list = await list_project_characters(db, project_id)
    name_map: dict[str, str] = {}
    for c in char_list:
        cname = c.get("character_name", "") or c.get("role_name", "")
        traits = c.get("traits", {})
        if isinstance(traits, dict):
            cname = traits.get("name", cname) or cname
        ref_images = c.get("reference_images", [])
        url = ""
        if isinstance(ref_images, list):
            # 取第一张实际存在的参考图
            for ref in ref_images:
                candidate = ref.get("url", "") if isinstance(ref, dict) else ref
                if candidate and _image_exists(candidate):
                    url = candidate
                    break
            # 回退：如果都不存在，取第一个非空 URL
            if not url:
                for ref in ref_images:
                    candidate = ref.get("url", "") if isinstance(ref, dict) else ref
                    if candidate:
                        url = candidate
                        break
        if cname and url:
            name_map[cname] = url
    return name_map


async def _build_material_map(db: AsyncSession, project_id: str) -> dict[tuple[str, str], str]:
    """
    构建 (type, name) -> url 映射，来源为项目内所有 pregen_materials。
    type 映射: background→scene, props→prop, vfx_ref→material, 其他→material
    """
    from app.services import storyboard_service

    result: dict[tuple[str, str], str] = {}
    storyboards = await storyboard_service.list_storyboards(db, project_id=project_id)

    for sb in storyboards:
        pm = sb.pregen_materials
        if not pm or not isinstance(pm, dict):
            continue

        # background → scene
        bg = pm.get("background")
        if isinstance(bg, str):
            # 用 episode/shot 上下文构建名称
            label = f"第{sb.episode_no}集背景"
            result[("scene", label)] = bg

        # vfx_ref → material
        vfx = pm.get("vfx_ref")
        if isinstance(vfx, str):
            label = f"第{sb.episode_no}集特效"
            result[("material", label)] = vfx

        # props → prop
        props = pm.get("props")
        if isinstance(props, dict):
            for prop_name, url in props.items():
                if isinstance(url, str):
                    result[("prop", prop_name)] = url

        # 其他键 → material
        for key, val in pm.items():
            if key in ("background", "vfx_ref", "props"):
                continue
            if isinstance(val, str):
                result[("material", key)] = val

    return result


def _fuzzy_match_material(
    material_map: dict[tuple[str, str], str],
    ref_type: str,
    ref_name: str,
) -> str | None:
    """模糊匹配素材名（包含关系）。"""
    for (t, n), url in material_map.items():
        if t == ref_type and (ref_name in n or n in ref_name):
            return url
    return None


def _image_exists(url: str) -> bool:
    """检查本地图片文件是否存在。"""
    if url.startswith("/static/"):
        local_path = Path(url.lstrip("/"))
        if local_path.exists():
            return True
        alt_path = Path("static") / url.replace("/static/", "")
        if alt_path.exists():
            return True
        for candidate in _alt_extensions(local_path):
            if candidate.exists():
                return True
        for candidate in _alt_extensions(alt_path):
            if candidate.exists():
                return True
        return False
    return bool(url)


def _load_image(url: str) -> bytes | None:
    """从本地路径或远程 URL 加载图片。自动尝试 .jpg/.png 互转。"""
    if url.startswith("/static/"):
        local_path = Path(url.lstrip("/"))
        if local_path.exists():
            return local_path.read_bytes()
        # Docker 容器内路径
        alt_path = Path("static") / url.replace("/static/", "")
        if alt_path.exists():
            return alt_path.read_bytes()
        # 尝试扩展名互转 .jpg ↔ .png
        for candidate in _alt_extensions(local_path):
            if candidate.exists():
                return candidate.read_bytes()
        for candidate in _alt_extensions(alt_path):
            if candidate.exists():
                return candidate.read_bytes()
        logger.warning("本地图片不存在: %s", url)
        return None

    import httpx
    try:
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.warning("下载远程图片失败: %s: %s", url, e)
        return None


def _alt_extensions(path: Path) -> list[Path]:
    """生成 .jpg ↔ .png 互转的候选路径。"""
    ext_map = {".jpg": ".png", ".jpeg": ".png", ".png": ".jpg"}
    ext = path.suffix.lower()
    alt = ext_map.get(ext)
    if alt:
        return [path.with_suffix(alt)]
    return []
