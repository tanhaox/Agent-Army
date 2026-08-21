"""Database session management."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

logger = logging.getLogger(__name__)

_engine = None
_session_maker = None


def _apply_manual_migrations(engine) -> None:
    """幂等迁移: 给已有表补列.

    Base.metadata.create_all 只建新表, 不会给已有表加列.
    旧库缺列时执行 ALTER TABLE ADD COLUMN (SQLite 支持, 非破坏性).
    """
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        # director_jobs.pipelines
        if "director_jobs" in tables:
            cols = {c["name"] for c in inspector.get_columns("director_jobs")}
            if "pipelines" not in cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE director_jobs ADD COLUMN pipelines VARCHAR(32)"))
                logger.info("[db] migrated: director_jobs.pipelines column added")

        # hosts 品牌/账号列 (2026-08-08): 账号信息挂到 Host, 洗稿选 host 后随流水线上屏
        if "hosts" in tables:
            cols = {c["name"] for c in inspector.get_columns("hosts")}
            host_cols = {
                "brand_name": "VARCHAR(128)",
                "stamp_name": "VARCHAR(16)",
                "brand_tag": "VARCHAR(64)",
            }
            for col_name, col_type in host_cols.items():
                if col_name not in cols:
                    with engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE hosts ADD COLUMN {col_name} {col_type}"))
                    logger.info("[db] migrated: hosts.%s column added", col_name)

        # book_projects.source_url (2026-08-19): 知海书页链接爬元数据当 L1.
        if "book_projects" in tables:
            cols = {c["name"] for c in inspector.get_columns("book_projects")}
            if "source_url" not in cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE book_projects ADD COLUMN source_url VARCHAR(2048)"))
                logger.info("[db] migrated: book_projects.source_url column added")

        # book_episodes 产线桥接列 (2026-08-19).
        if "book_episodes" in tables:
            cols = {c["name"] for c in inspector.get_columns("book_episodes")}
            for col_name, col_type in (("script_id", "VARCHAR(36)"), ("director_job_id", "VARCHAR(36)")):
                if col_name not in cols:
                    with engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE book_episodes ADD COLUMN {col_name} {col_type}"))
                    logger.info("[db] migrated: book_episodes.%s column added", col_name)

        # audio_jobs.tts_cache_key (2026-08-21): TTS缓存 — 稿没变复用已有音频, 免重跑合成.
        if "audio_jobs" in tables:
            cols = {c["name"] for c in inspector.get_columns("audio_jobs")}
            if "tts_cache_key" not in cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE audio_jobs ADD COLUMN tts_cache_key VARCHAR(64)"))
                logger.info("[db] migrated: audio_jobs.tts_cache_key column added")

        # personas 整合账号字段 (2026-08-08): 人物即账号.
        # Persona 吸收品牌/开结尾/显式 host_id 绑定, 洗稿页选人物即选账号.
        if "personas" in tables:
            cols = {c["name"] for c in inspector.get_columns("personas")}
            persona_cols = {
                "brand_name": "VARCHAR(128)",
                "stamp_name": "VARCHAR(16)",
                "brand_tag": "VARCHAR(64)",
                "fixed_opening": "TEXT",
                "fixed_ending": "TEXT",
                "host_id": "VARCHAR(36)",
                "target_reader": "TEXT",
            }
            for col_name, col_type in persona_cols.items():
                if col_name not in cols:
                    with engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE personas ADD COLUMN {col_name} {col_type}"))
                    logger.info("[db] migrated: personas.%s column added", col_name)

            # 数据修复: 生产库 laotan persona 与 laochen host 实为同一数字人,
            # 但旧逻辑 (prompt_template.like(host.persona_key + "%")) 匹配不上,
            # 导致账号/人物绑定断裂 (audio 回退 / 品牌注入均落空).
            # 策略: 仅当 hosts 表恰好 1 个 host 时, 给所有未绑定 persona 补绑 + 品牌补全;
            # 多 host 库不自动猜绑, 留待人物页手动编辑 (非破坏性).
            if _session_maker is not None:
                try:
                    from .models import Host, Persona

                    db = _session_maker()
                    try:
                        hosts = db.query(Host).all()
                        if len(hosts) == 1:
                            host = hosts[0]
                            fixed = 0
                            for persona in db.query(Persona).filter(Persona.host_id.is_(None)).all():
                                persona.host_id = host.id
                                if not persona.brand_name:
                                    persona.brand_name = host.brand_name
                                if not persona.stamp_name:
                                    persona.stamp_name = host.stamp_name
                                if not persona.brand_tag:
                                    persona.brand_tag = host.brand_tag
                                if not persona.fixed_opening:
                                    persona.fixed_opening = host.fixed_opening
                                if not persona.fixed_ending:
                                    persona.fixed_ending = host.fixed_ending
                                fixed += 1
                            if fixed:
                                db.commit()
                                logger.info("[db] personas bound: %d persona(s) → host %s", fixed, host.persona_key)
                    finally:
                        db.close()
                except Exception as exc:
                    logger.warning("[db] personas host bind skipped: %s", exc)

            # 数据修复 (2026-08-20): 目标读者画像移入人设级 — 给已有书账号 persona
            # 补默认读者画像; 清理书 input_json.needs_supplement 里的目标读者画像条目
            # (改由 complete_input 从 persona 继承, 不再要求录入时人工补).
            if _session_maker is not None:
                try:
                    from .models import Host, Persona, BookProject

                    db = _session_maker()
                    try:
                        _DEFAULT_READER = ("对个人成长、商业规律、心理学感兴趣的普通职场人；"
                                           "刷抖音中长视频")
                        fixed_p = 0
                        for persona in db.query(Persona).all():
                            if not persona.target_reader:
                                persona.target_reader = _DEFAULT_READER
                                fixed_p += 1
                        fixed_b = 0
                        # 已存在书: 清 needs_supplement 里的读者画像条目 + 回填继承值
                        book_persona = (
                            db.query(Persona)
                            .filter(Persona.prompt_template == "jingshu-book")
                            .first()
                        )
                        inherited = (book_persona.target_reader if book_persona else None) or _DEFAULT_READER
                        for book in db.query(BookProject).all():
                            inp = dict(book.input_json or {})
                            changed = False
                            needs = inp.get("needs_supplement") or []
                            if "目标读者画像" in needs:
                                needs = [x for x in needs if x != "目标读者画像"]
                                inp["needs_supplement"] = needs
                                changed = True
                            if not (inp.get("目标读者画像") or {}).get("value"):
                                inp["目标读者画像"] = {"value": inherited, "tier": "persona", "inherited": True}
                                changed = True
                            if changed:
                                book.input_json = inp
                                fixed_b += 1
                        if fixed_p or fixed_b:
                            db.commit()
                            logger.info("[db] target_reader backfill: persona=%d book_clean+inherit=%d",
                                        fixed_p, fixed_b)
                    finally:
                        db.close()
                except Exception as exc:
                    logger.warning("[db] target_reader backfill skipped: %s", exc)

        # articles 评论层 (2026-08-15): 解构产物持久化, 新闻线索页展示
        if "articles" in tables:
            cols = {c["name"] for c in inspector.get_columns("articles")}
            if "deconstruct_json" not in cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE articles ADD COLUMN deconstruct_json TEXT"))
                logger.info("[db] migrated: articles.deconstruct_json column added")
            # 赛道 (2026-08-16): tech/geo, 建稿勾选驱动评论层+七层审计分支
            if "track" not in cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE articles ADD COLUMN track VARCHAR(16) DEFAULT 'tech'"))
                logger.info("[db] migrated: articles.track column added")

        # video_assets 内容质量分 (2026-08-16 烂素材治理③): VLM 质量打分产物,
        # matcher 硬底线+排序依据 — 治"分辨率没问题但内容平庸"的主病
        if "video_assets" in tables:
            cols = {c["name"] for c in inspector.get_columns("video_assets")}
            va_cols = {"quality_score": "FLOAT", "quality_reason": "TEXT"}
            for col_name, col_type in va_cols.items():
                if col_name not in cols:
                    with engine.begin() as conn:
                        conn.execute(
                            text(f"ALTER TABLE video_assets ADD COLUMN {col_name} {col_type}")
                        )
                    logger.info("[db] migrated: video_assets.%s column added", col_name)

        # scripts 爆品改造列 (2026-08-10): 洗稿后自动跑 P1开场→P2预埋→P3节奏.
        # boosted_text = 改造后全文 (保留 script_text 洗稿原稿); boost_titles = 标题候选 JSON.
        if "scripts" in tables:
            cols = {c["name"] for c in inspector.get_columns("scripts")}
            script_cols = {
                "boosted_text": "TEXT",
                "boost_titles": "TEXT",
                "deconstruct_json": "TEXT",
                "emotion_annotations": "TEXT",
                # 素材聚合 (2026-08-15): 洗稿挂的素材包回溯
                "material_package_id": "VARCHAR(36)",
            }
            for col_name, col_type in script_cols.items():
                if col_name not in cols:
                    with engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE scripts ADD COLUMN {col_name} {col_type}"))
                    logger.info("[db] migrated: scripts.%s column added", col_name)
    except Exception as exc:
        logger.warning("[db] manual migrations skipped: %s", exc)


def init_db(database_url: str) -> None:
    global _engine, _session_maker
    _engine = create_engine(database_url, connect_args={"check_same_thread": False})
    _session_maker = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    Base.metadata.create_all(bind=_engine)
    _apply_manual_migrations(_engine)


def get_engine():
    return _engine


def get_session_maker():
    return _session_maker


@contextmanager
def db_session() -> Iterator[Session]:
    """统一 Session 生命周期: 创建 → yield → finally 自动 close.

    调用点直接 `with db_session() as db:`。未初始化(init_db 未跑)时
    raise RuntimeError, 与 get_db 语义一致; 需要静默跳过时调用点自行
    用 `if get_session_maker() is None:` 守卫。
    """
    if _session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    db = _session_maker()
    try:
        yield db
    finally:
        db.close()


def get_db():
    if _session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    db = _session_maker()
    try:
        yield db
    finally:
        db.close()
