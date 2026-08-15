"""剪映模板包格式检查器 — J 线验证点实测工具.

用法:
    python scripts/_inspect_jy_template.py <模板包根目录> [--deep]

检查项 (对应 docs/剪映草稿产线-设计方案.md §3.3 三验证点):
  1. 加密与否: draft_content.json 是否明文 JSON (剪映 6.0+ 保存过的草稿为 AES 加密)
  2. 素材完整性: 草稿引用的本地素材路径是否存在 / 引用了多少外部资源
  3. 可替换性: 视频/文本素材的命名规律, 特效/转场/贴纸资源 ID 清单

--deep: 额外解析每个明文草稿的轨道/素材明细 (慢)
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# Windows GBK 控制台打 emoji 会炸, 强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 剪映草稿关键键名 (draft_content.json 顶层)
TRACK_KEYS = ("tracks",)
MATERIAL_GROUPS = (
    "videos", "audios", "texts", "stickers", "effects",
    "transitions", "filters", "animations", "fonts", "canvases",
    "shapes", "placeholders",
)


def is_plaintext_json(path: Path) -> tuple[bool, str]:
    """返回 (是否明文, 说明)."""
    raw = path.read_bytes()
    if not raw.strip():
        return False, "空文件"
    stripped = raw.lstrip()
    if stripped[:1] in (b"{", b"["):
        try:
            json.loads(raw.decode("utf-8", errors="strict"))
            return True, "明文 JSON"
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return False, f"JSON 头但解析失败({exc.__class__.__name__})"
    return False, f"二进制/加密 (首字节 {stripped[:4].hex()})"


def inspect_draft(path: Path, deep: bool) -> dict:
    ok, note = is_plaintext_json(path)
    # 新版剪映 draft_content.json 加密, 但 template.json 常是完整明文镜像 (素材/轨道/特效全量)
    mirror = path.parent / "template.json"
    if not ok and mirror.exists():
        m_ok, m_note = is_plaintext_json(mirror)
        if m_ok:
            return _parse_draft(mirror, deep, source_note=f"content加密, template.json明文镜像")
    info = _parse_draft(path, deep) if ok else {
        "plaintext": False, "note": note, "materials": {},
        "missing_assets": 0, "asset_paths": [], "duration_us": None,
    }
    return info


def _parse_draft(path: Path, deep: bool, source_note: str = "明文 JSON") -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    info = {
        "path": path,
        "plaintext": True,
        "note": source_note,
        "materials": {},
        "missing_assets": 0,
        "asset_paths": [],
        "duration_us": data.get("duration"),
    }
    for group in MATERIAL_GROUPS + ("video_effects", "material_animations", "beats", "placeholders"):
        items = data.get("materials", {}).get(group) or []
        if not items:
            continue
        info["materials"][group] = len(items)
        if group in ("videos", "audios"):
            for item in items:
                p = item.get("path") or item.get("remote_url") or ""
                if p:
                    info["asset_paths"].append(p)
                    local = item.get("local_path") or p
                    if local and not Path(local).exists() and item.get("local_material", True):
                        info["missing_assets"] += 1
    if deep:
        tracks = data.get("tracks") or []
        seg_types = Counter(t.get("type", "?") for t in tracks)
        info["tracks"] = dict(seg_types)
    return info


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", help="模板包根目录 (解压后)")
    parser.add_argument("--deep", action="store_true", help="解析明文草稿明细")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"目录不存在: {root}")

    drafts = sorted(root.rglob("draft_content.json"))
    # 按顶层项目文件夹分组, 每组只取最浅层的 draft_content.json
    # (剪映会在 history_snapshot/ 等子目录存历史版本, 不应重复计数)
    by_top: dict[str, Path] = {}
    for d in drafts:
        try:
            top = d.relative_to(root).parts[0]
        except ValueError:
            continue
        prev = by_top.get(top)
        if prev is None or len(d.parts) < len(prev.parts):
            by_top[top] = d
    drafts = sorted(by_top.values())
    meta_files = sorted(root.rglob("draft_meta_info.json"))
    print(f"根目录: {root}")
    print(f"草稿数: {len(drafts)} (draft_content.json) | meta: {len(meta_files)}\n")

    if not drafts:
        print("!! 未找到任何 draft_content.json — 可能是: 手机版模板/工程文件格式/压缩包未解压")
        # 打印目录结构前两层辅助判断
        for p in sorted(root.rglob("*"))[:40]:
            if p.is_file():
                print("  样本文件:", p.relative_to(root))
        return

    n_plain = 0
    for d in drafts:
        info = inspect_draft(d, args.deep)
        mark = "✅" if info["plaintext"] else "❌"
        n_plain += info["plaintext"]
        rel = d.parent.relative_to(root)
        line = f"{mark} {rel or '.'}  [{info['note']}]"
        if info["duration_us"]:
            line += f"  时长≈{info['duration_us'] / 1_000_000:.0f}s"
        print(line)
        if info["plaintext"]:
            if info["materials"]:
                print(f"     素材: {info['materials']}")
            if info["asset_paths"]:
                sample = [Path(p).name for p in info["asset_paths"][:5]]
                print(f"     素材命名样本: {sample}")
            if info["missing_assets"]:
                print(f"     ⚠️ 缺失本地素材 {info['missing_assets']} 个 (引用路径不存在)")
            if args.deep and info.get("tracks"):
                print(f"     轨道: {info['tracks']}")

    print(f"\n== 汇总: {n_plain}/{len(drafts)} 明文可代码化 ==")
    if n_plain < len(drafts):
        print("加密草稿需走应对链: 旧版剪映打开重存 / 云空间降级取回 / 社区解密工具 (见设计方案 §2.3)")


if __name__ == "__main__":
    main()
