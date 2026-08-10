"""新旧 director_prompt 逐字行为 diff.

加载磁盘上的原文件 app/services/director_prompt.py 为 old 模块,
新包 app/services/director_prompt/ 为 new 模块, 对比公共函数在相同
输入下的输出是否逐字节一致。测试用 DB 异常, 故两边都不碰真实 DB。
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import traceback

ROOT = pathlib.Path("F:/AI-Agent-Local/digital_human")
sys.path.insert(0, str(ROOT))

# ── 加载旧模块 (从原文件路径, 避免同名包优先) ──
old_path = ROOT / "app/services/director_prompt.py"
spec = importlib.util.spec_from_file_location("old_director_prompt", old_path)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)

# ── 加载新包 ──
from app.services.director_prompt import (  # noqa: E402
    build_director_prompt as new_build,
    build_real_material_catalog as new_cat,
    build_vocabulary_pack as new_pack,
    load_director_prompt as new_load,
    mock_material_catalog as new_mock,
)
from app.services.director_prompt._strip_host import strip_host_mode as new_strip  # noqa: E402

old_build = old.build_director_prompt
old_cat = old.build_real_material_catalog
old_pack = old.build_vocabulary_pack
old_load = old.load_director_prompt
old_mock = old.mock_material_catalog
old_strip = old._strip_host_mode

FAIL = []


def diff(name: str, a: str, b: str) -> None:
    if a == b:
        print(f"  ✓ {name} 逐字节一致")
    else:
        FAIL.append(name)
        print(f"  ✗ {name} 不一致! 长度 old={len(a)} new={len(b)}")
        for i, (ca, cb) in enumerate(zip(a, b)):
            if ca != cb:
                print(f"    首处差异 @{i}: old={ca!r} new={cb!r}")
                print(f"    old 上下文: {a[max(0,i-40):i+40]!r}")
                print(f"    new 上下文: {b[max(0,i-40):i+40]!r}")
                break


class BoomSession:
    def query(self, *a, **k):
        raise RuntimeError("boom")


def main() -> int:
    # 1) load_director_prompt
    diff("load_director_prompt", old_load(), new_load())

    # 2) mock_material_catalog
    diff("mock_material_catalog", old_mock(), new_mock())

    # 3) build_vocabulary_pack DB 失败
    diff("build_vocabulary_pack(boom)", old_pack(BoomSession()), new_pack(BoomSession()))

    # 4) build_real_material_catalog DB 失败
    diff("build_real_material_catalog(boom)", old_cat(BoomSession()), new_cat(BoomSession()))

    # 5) _strip_host_mode 直接对比
    base = old_load()
    diff("_strip_host_mode(base)", old_strip(base), new_strip(base))

    # 6) build_director_prompt 多场景对比
    timings = [
        {"start_sec": 0.0, "end_sec": 4.2, "segment_id": "seg-001"},
        {"start_sec": 4.2, "end_sec": 8.0, "segment_id": "seg-002"},
    ]
    cases = [
        ("全启用 c/p/h", {"c", "p", "h"}),
        ("无出镜 p/h", {"p", "h"}),
        ("全禁用", set()),
        ("None 默认", None),
        ("只开 c", {"c"}),
    ]
    for label, pipes in cases:
        kwargs = dict(
            script_text="大家好，今天我们来聊进出口数据。",
            segment_timings=timings,
            material_catalog=None,
            video_format="portrait",
            script_title="测试标题",
            enabled_pipelines=pipes,
        )
        diff(f"build_director_prompt [{label}]", old_build(**kwargs), new_build(**kwargs))

    print(f"\n== 逐字 diff: {len(FAIL) and f'{len(FAIL)} 处不一致' or '全部一致'} ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
