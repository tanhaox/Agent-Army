"""director_prompt 包行为契约断言 (重构后逐字保持).

覆盖: 7 公共 API 导入 / mock 目录 5 节 / DB 失败空 pack / DB 失败 fallback mock /
词表包缺失 None / build_director_prompt 输出块 / strip_host_mode 无 host 残留。
"""
from __future__ import annotations

import sys
import traceback

# ── 1) 7 公共 API 导入 ──
from app.services.director_prompt import (  # noqa: E402
    build_director_prompt,
    build_real_material_catalog,
    build_vocabulary_pack,
    load_director_prompt,
    load_vocabulary_pack,
    mock_material_catalog,
    rebuild_vocabulary_pack,
)
from app.services.director_prompt._strip_host import strip_host_mode  # noqa: E402

PASS = []


def ok(name: str) -> None:
    PASS.append(name)
    print(f"  ✓ {name}")


class BoomSession:
    """DB 查询即抛异常, 模拟连接失败."""

    def query(self, *a, **k):
        raise RuntimeError("boom")


def main() -> int:
    # ── 2) mock 目录 5 节 ──
    cat = mock_material_catalog()
    assert set(cat) == {"港口", "工厂", "城市", "数据图表", "标题卡"}, set(cat)
    ok("mock_material_catalog 5 节")

    # ── 3) build_vocabulary_pack DB 失败 → 空 pack ──
    pack = build_vocabulary_pack(BoomSession())
    assert pack["type"] == "vocabulary_pack"
    assert pack["version"] == 1
    assert pack["dimensions"] == {} and pack["stats"] == {}
    ok("build_vocabulary_pack DB 失败 → 空 pack")

    # ── 4) build_real_material_catalog DB 失败 → mock fallback ──
    cat2 = build_real_material_catalog(BoomSession())
    assert set(cat2) >= {"港口", "工厂", "城市", "数据图表", "标题卡"}
    ok("build_real_material_catalog DB 失败 → mock")

    # ── 5) load_vocabulary_pack: 存在与否都返回合法类型 ──
    p = load_vocabulary_pack()
    assert p is None or isinstance(p, dict)
    ok("load_vocabulary_pack → None|dict")

    # ── 6) strip_host_mode: 对真实/兜底系统提示词都无 host 残留 ──
    base = load_director_prompt()
    stripped = strip_host_mode(base)
    # 兜底正则删光含 host 行; 输出不应含 host 工作流字样
    assert "host" not in stripped, stripped[:500]
    assert "老陈出镜" not in stripped
    ok("strip_host_mode 无 host 残留")

    # ── 7) build_director_prompt 全链路 (无出镜 + 全禁用 + 全启用) ──
    timings = [{"start_sec": 0.0, "end_sec": 5.0, "segment_id": "seg-001"}]

    # 7a) 只开 P/H → 无出镜裁剪 + 画幅 + 词表约束 + timing + 管线约束
    p_nohost = build_director_prompt(
        script_text="大家好，今天聊财经。",
        segment_timings=timings,
        video_format="portrait",
        script_title="测试标题",
        enabled_pipelines={"p", "h"},
    )
    assert "当前画幅是 **portrait**" in p_nohost
    assert "## 补充输入2说明：关键词词表包选词规则（硬性）" in p_nohost
    assert "## 补充输入3：每句口播的真实起止时间（秒）" in p_nohost
    assert "## 管线限制（硬性约束 — 必须遵守！）" in p_nohost
    assert "- C线 ComfyUI → 禁止工作流: host, mixed_host_broll" in p_nohost
    assert "开场/收尾用 hf_title 替代 host 出镜" in p_nohost
    assert "测试标题" in p_nohost and "大家好，今天聊财经。" in p_nohost
    ok("build_director_prompt 只开 P/H")

    # 7b) 全部启用 → 无管线约束块
    p_all = build_director_prompt(
        script_text="大家好。",
        segment_timings=timings,
        enabled_pipelines={"c", "p", "h"},
    )
    assert "## 管线限制" not in p_all
    ok("build_director_prompt 全启用 → 无管线约束")

    # 7c) 无出镜 + 全禁用 → host 替代方案走本地兜底
    p_none = build_director_prompt(
        script_text="大家好。",
        segment_timings=timings,
        enabled_pipelines=set(),
    )
    assert "开场/收尾用 broll_local 替代 (本地素材兜底)" in p_none
    assert "需要空镜时用 broll_local 替代" in p_none
    assert "数据可视化/标题卡用 broll_local 替代" in p_none
    ok("build_director_prompt 全禁用 → 本地兜底")

    print(f"\n== 行为契约断言: {len(PASS)}/8 通过 ==")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
