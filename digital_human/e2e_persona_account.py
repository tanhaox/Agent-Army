"""E2E 验证: 人物即账号方案 (2026-08-08).

验证点:
  1. 迁移幂等: init_db 连跑两次, 不重复 ALTER / 不报错
  2. seed 无硬编码品牌: 默认 host name=数字人频道, 品牌字段全 None
  3. persona→host 闭环:
     - GET /api/personas 返回品牌字段
     - PUT /api/personas/{id} 更新品牌 + 绑定 host
     - 洗稿 POST rewrite 带 persona_id → script.host_id 正确解析
     - 洗稿后 segments 的 opening/ending 类型来自 persona.fixed_opening/ending
  4. _merge_brand 注入 persona 品牌, 无「老陈」残留
"""
import logging
import sys
import tempfile
import uuid
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
sys.stdout.reconfigure(encoding="utf-8")

import yaml

TMP = Path(tempfile.mkdtemp(prefix="dh_e2e_"))
CFG = TMP / "config.yaml"
DB = TMP / "e2e.db"

cfg_doc = {
    "app": {"database_url": f"sqlite:///{DB.as_posix()}", "data_dir": str(TMP / "data")},
    "deepseek": {
        "api_key": "sk-mock",
        "base_url": "http://127.0.0.1:9",
        "model_flash": "flash-mock",
        "model_pro": "pro-mock",
        "default_model": "flash",
    },
    "local_llm": {"base_url": "http://127.0.0.1:9", "model": "mock"},
    "defaults": {"host_id": "laochen"},
}
CFG.write_text(yaml.safe_dump(cfg_doc, allow_unicode=True), encoding="utf-8")

# 关键: lifespan 用模块顶部的 `from .config import load_config`, 直接重绑使其读到临时 config
from app.config import load_config, set_config
import app.config as config_mod

config_mod.load_config = lambda *a, **k: load_config(CFG)

import app.main as main_mod

main_mod.load_config = config_mod.load_config
from app.database import init_db, get_session_maker, db_session
from app.main import _seed_defaults
from app.models import Host, Persona, Script, Segment

cfg = load_config(CFG)
set_config(cfg)

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}  {detail}")


# ── 1. 迁移幂等 ──
print("[1] 迁移幂等 (init_db x2)")
init_db(cfg.app.database_url)
init_db(cfg.app.database_url)
check("init_db 两次无异常", True)
import sqlalchemy as sa

eng = sa.create_engine(cfg.app.database_url)
insp = sa.inspect(eng)
persona_cols = {c["name"] for c in insp.get_columns("personas")}
host_cols = {c["name"] for c in insp.get_columns("hosts")}
for c in ("brand_name", "stamp_name", "brand_tag", "fixed_opening", "fixed_ending", "host_id"):
    check(f"personas.{c} 存在", c in persona_cols)
for c in ("brand_name", "stamp_name", "brand_tag"):
    check(f"hosts.{c} 存在", c in host_cols)

# ── 2. seed 去硬编码 ──
print("[2] seed 去硬编码")
_seed_defaults()
with db_session() as db:
    host = db.query(Host).filter(Host.persona_key == "laochen").first()
    check("默认 host 存在", host is not None)
    check("默认 host.name 中性 (无老陈)", host is not None and "老陈" not in (host.name or ""), str(host.name if host else None))
    check("默认 host 品牌字段全空", host is not None and host.brand_name is None and host.stamp_name is None and host.brand_tag is None)
    host_id = host.id

# ── 3. app 启动 + persona CRUD ──
print("[3] persona CRUD (品牌 + host 绑定)")
from app.main import create_app

app = create_app()
from fastapi.testclient import TestClient

with TestClient(app) as client:
    r = client.get("/api/personas")
    check("GET /api/personas 200", r.status_code == 200, str(r.status_code))
    r = client.get("/api/hosts")
    check("GET /api/hosts 200", r.status_code == 200, str(r.status_code))

    pname = f"谭老师_{uuid.uuid4().hex[:6]}"
    r = client.post("/api/personas", json={
        "name": pname, "prompt_template": "laotan", "voice_id": None, "role_id": None,
    })
    check("POST /api/personas 201", r.status_code == 201, f"{r.status_code} {r.text[:200]}")
    p = r.json()
    persona_id = p["id"]

    opening = "大家好，欢迎来到谭聊财经频道。"
    ending = "关注我，每天读懂财经数据。"
    r = client.put(f"/api/personas/{persona_id}", json={
        "name": pname, "prompt_template": "laotan",
        "brand_name": "谭聊财经", "stamp_name": "谭聊", "brand_tag": "数据锐评",
        "fixed_opening": opening, "fixed_ending": ending,
        "host_id": host_id,
    })
    check("PUT /api/personas 200", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
    p2 = r.json()
    for k, v in {"brand_name": "谭聊财经", "stamp_name": "谭聊", "brand_tag": "数据锐评"}.items():
        check(f"PUT 后 persona.{k}", p2.get(k) == v, str(p2.get(k)))
    check("PUT 后 persona.host_id", p2.get("host_id") == host_id)
    check("PUT 后 persona.fixed_opening", p2.get("fixed_opening") == opening)

    # ── 4. 洗稿: persona_id → host → 开结尾落段 ──
    print("[4] 洗稿链路")
    import app.routers.articles as arts_mod

    orig_rewrite = arts_mod.LLMService.rewrite_article

    def fake_rewrite(self, raw_text, prompt_template=None, model=None, stream=True,
                     chunk_callback=None, perspective=None):
        txt = (opening + "\n最近公布的二季度数据好于预期，主要源于消费回暖和出口韧性。\n"
               "工业增加值同比增长百分之五点八，服务业保持稳定。\n" + ending)
        if chunk_callback:
            chunk_callback(txt)
        return txt

    arts_mod.LLMService.rewrite_article = fake_rewrite

    r = client.post("/api/articles", json={"title": "E2E 洗稿测试", "raw_text": "原文"})
    check("POST /api/articles 200", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
    article_id = r.json()["id"]

    r = client.post(f"/api/articles/{article_id}/rewrite", json={
        "persona_id": persona_id, "prompt_template": "laotan", "video_format": "portrait",
    })
    check("POST rewrite 200", r.status_code == 200, f"{r.status_code} {r.text[:200]}")

    # BackgroundTasks 在 TestClient 请求返回后执行 (with 块内), 轮询 script 表
    import time
    script_id = None
    for _ in range(100):
        with db_session() as db:
            s = db.query(Script).filter(Script.article_id == article_id).first()
            if s:
                script_id = s.id
                break
        time.sleep(0.1)
    check("洗稿后 script 创建", script_id is not None)
    if script_id:
        with db_session() as db:
            s = db.query(Script).filter(Script.id == script_id).first()
            check("script.host_id == host", s.host_id == host_id, str(s.host_id))
            segs = db.query(Segment).filter(Segment.script_id == script_id).order_by(Segment.host_order).all()
            types = [seg.segment_type for seg in segs]
            texts = [seg.text for seg in segs]
            check("首段 opening", bool(types) and types[0] == "opening", str(types))
            check("末段 ending", bool(types) and types[-1] == "ending", str(types))
            check("opening 文本含谭聊", bool(texts) and opening in texts[0], str(texts[0] if texts else None))
            check("ending 文本含谭聊", bool(texts) and ending in texts[-1], str(texts[-1] if texts else None))
            joined = " ".join(texts)
            check("洗稿文本无老陈", "老陈" not in joined)

    arts_mod.LLMService.rewrite_article = orig_rewrite

    # ── 5. _merge_brand 闭环 ──
    print("[5] _merge_brand 品牌注入")
    from app.services.slot_workflows.hf import _merge_brand

    if script_id:
        with db_session() as db:
            s = db.query(Script).filter(Script.id == script_id).first()
            slot = type("S", (), {})()
            slot.director_job = type("J", (), {"script": s})()
            data = {}
            _merge_brand(data, slot, db)
            check("brand_name 注入谭聊财经", data.get("brand_name") == "谭聊财经", str(data.get("brand_name")))
            check("stamp_name 注入谭聊", data.get("stamp_name") == "谭聊", str(data.get("stamp_name")))
            check("brand_tag 注入数据锐评", data.get("brand_tag") == "数据锐评", str(data.get("brand_tag")))
            import json
            joined = json.dumps(data, ensure_ascii=False)
            check("注入无老陈", "老陈" not in joined)

print(f"\n结果: PASS={PASS} FAIL={FAIL}  库={DB}")
if FAIL:
    print("E2E 存在失败项")
    sys.exit(1)
print("E2E 全部通过")
