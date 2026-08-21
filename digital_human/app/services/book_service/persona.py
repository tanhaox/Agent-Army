# -*- coding: utf-8 -*-
"""拆书账号人设种子 (2026-08-20) — 静读书 host+persona 幂等建账.

形象/音色不建记录: 运行时经既有 personas/roles/voices 面板绑定 (用户决策)。
品牌: 静读书 / 印章 读书 / 标语 一期拆透一本好书。
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models import Host, Persona

logger = logging.getLogger(__name__)

__all__ = ["ensure_book_account", "BOOK_PERSONA_KEY"]

BOOK_PERSONA_KEY = "jingshu"

# 静姐人设: 温柔知性、闺蜜式共情, 面向 25-40+ 女性成长读者
PERSONA_NAME = "静读书"
PERSONA_TARGET_READER = ("抖音、小红书：25岁迷茫年轻女生 → 40+ 困境宝妈、职场女性；"
                         "痛点是中年内耗、婚姻委屈、角色捆绑、自我丢失；"
                         "讲成长是'历经生活，依然精致从容'，共情大于讲课")


def ensure_book_account(db: Session) -> Host:
    """幂等: 书账号 host+persona 存在即返回, 缺失则建."""
    host = db.query(Host).filter(Host.persona_key == BOOK_PERSONA_KEY).first()
    if host:
        return host
    host = Host(
        name=PERSONA_NAME,
        persona_key=BOOK_PERSONA_KEY,
        brand_name=PERSONA_NAME,
        stamp_name="读书",
        brand_tag="一期拆透一本好书",
    )
    db.add(host)
    db.flush()
    db.add(Persona(
        name=PERSONA_NAME,
        prompt_template="jingshu-book",
        host_id=host.id,
        brand_name=PERSONA_NAME,
        stamp_name="读书",
        brand_tag="一期拆透一本好书",
        # 目标读者画像 (账号人设级): 书级缺省继承, 录入书时不再强制人工补.
        target_reader=PERSONA_TARGET_READER,
    ))
    db.commit()
    logger.info("[book] 书账号人设已建: %s (%s)", PERSONA_NAME, host.id[:8])
    return host
