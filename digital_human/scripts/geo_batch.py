# -*- coding: utf-8 -*-
"""地缘素材双套装弹 (2026-08-28 用户单):
① 8 国宣传片 (美/日/菲/伊朗/俄/乌/韩/欧盟), 20-40 切片, 干净无字幕
② 领导人讲话 (集会/议会/竞选/G7/国情咨文), 每类 5-6 切片, 只要"在讲"画面
下载+切片阶段 (VPN on) → 打标 (VPN off, llama) → 只入无字幕片段。
"""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]

# (实体标签, 搜索词, 条数, 最大时长秒) — 都市向 (2026-08-28 用户令: 不选风景, 要都市类)
COUNTRY_PROMOS = [
    ("美国",   "ytsearch2:New York City Manhattan 4K aerial", 2, 600),
    ("日本",   "ytsearch2:Tokyo city 4K aerial night", 2, 600),
    ("菲律宾", "ytsearch2:Manila Philippines city 4K", 2, 600),
    ("伊朗",   "ytsearch2:Tehran Iran city 4K", 2, 600),
    ("俄罗斯", "ytsearch2:Moscow city 4K aerial", 2, 600),
    ("乌克兰", "ytsearch2:Kyiv Ukraine city 4K", 2, 600),
    ("韩国",   "ytsearch2:Seoul city 4K aerial", 2, 600),
    ("欧盟",   "ytsearch2:Brussels EU quarter city 4K", 2, 600),
]

LEADER_SPEECHES = [
    ("特朗普",   "ytsearch2:Trump rally speech", 2, 3600),
    ("特朗普",   "ytsearch1:Trump address nation speech", 1, 3600),
    ("高市早苗", "ytsearch2:Takaichi Sanae speech", 2, 3600),
    ("普京",     "ytsearch2:Putin speech", 2, 3600),
    ("泽连斯基", "ytsearch2:Zelensky speech", 2, 3600),
    ("马科斯",   "ytsearch2:Marcos president speech Philippines", 2, 3600),
    ("李在明",   "ytsearch2:Lee Jae-myung speech", 2, 3600),
    ("佩泽希齐扬", "ytsearch2:Iran president Pezeshkian speech", 2, 3600),
    ("冯德莱恩", "ytsearch2:von der Leyen speech", 2, 3600),
    ("G7峰会",   "ytsearch2:G7 summit leaders gathering", 2, 3600),
]

# 0828 首轮未命中/零干净 → 补弹清单 (下次 VPN 连上时跑)
RETRY_ROUND = [
    ("美国",   "ytsearch3:New York City 4K timelapse", 3, 600),
    ("韩国",   "ytsearch3:Seoul Korea 4K timelapse", 3, 600),
    ("普京",   "ytsearch3:Putin speech highlights", 3, 3600),
    ("高市早苗", "ytsearch3:Takaichi press conference", 3, 3600),
    ("李在明", "ytsearch3:Lee Jae-myung inauguration speech", 3, 3600),
    ("马科斯", "ytsearch3:Marcos SONA speech", 3, 3600),
    ("G7峰会", "ytsearch3:G7 summit press conference", 3, 3600),
]


def run_retry() -> None:
    """补弹: 首轮未命中的实体换口径重搜 (需 VPN)."""
    for row in RETRY_ROUND:
        run(*row)


def run(entity: str, url: str, max_n: int, max_dur: int) -> None:
    print(f"\n━━━ {entity} | {url} ━━━", flush=True)
    subprocess.run(
        [sys.executable, str(ROOT / "sandbox/yt_ingest.py"), "batch",
         "--company", entity, "--url", url,
         "--max", str(max_n), "--max-duration", str(max_dur)],
        cwd=str(ROOT), timeout=1800)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "retry":
        run_retry()
        return
    for row in COUNTRY_PROMOS + LEADER_SPEECHES:
        run(*row)
    print("\n全部下载+切片完成 → 等用户断 VPN 后跑 tag --all + clean-only 入库", flush=True)


if __name__ == "__main__":
    main()
