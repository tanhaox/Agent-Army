# -*- coding: utf-8 -*-
"""素材包 router (2026-08-15): 多源聚合 / 七层覆盖审计 / 智谱定向补搜.

后台 job 照抄 scripts._run_boost_background daemon-thread 模式:
抓取(可选) → 补搜(可选) → 审计 → 落库 + SSE (material_* 事件).
"""
from __future__ import annotations

import logging
import threading
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import db_session, get_db
from ..models import Article, MaterialItem, MaterialPackage
from ..schemas.materials import (
    MaterialItemAddRequest,
    MaterialItemOut,
    MaterialPackageBriefOut,
    MaterialPackageOut,
    PackageCreateRequest,
    SupplementSearchRequest,
)
from ..services import material_service
from ..services.url_fetcher import fetch_url
from .jobs import _publish

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/materials", tags=["materials"])


def _brief(pkg: MaterialPackage) -> MaterialPackageBriefOut:
    return MaterialPackageBriefOut(
        id=pkg.id,
        article_id=pkg.article_id,
        title=pkg.title,
        status=pkg.status,
        search_rounds=pkg.search_rounds,
        error_message=pkg.error_message,
        created_at=pkg.created_at,
        updated_at=pkg.updated_at,
        item_count=len(pkg.items),
    )


def _detail(pkg: MaterialPackage, article: Article | None = None) -> MaterialPackageOut:
    # 解构层 research 资料清单并入补搜候选池 (2026-08-16: 此前只躺在评论层面板)
    research_hints = []
    if article is not None and article.deconstruct_json:
        research_hints = [str(r) for r in (article.deconstruct_json.get("research") or []) if r]
    return MaterialPackageOut(
        id=pkg.id,
        article_id=pkg.article_id,
        title=pkg.title,
        status=pkg.status,
        audit_json=pkg.audit_json,
        search_rounds=pkg.search_rounds,
        error_message=pkg.error_message,
        created_at=pkg.created_at,
        updated_at=pkg.updated_at,
        items=[MaterialItemOut.model_validate(it) for it in pkg.items],
        gap_queries=material_service.collect_gap_queries(pkg.audit_json, research_hints),
    )


def _run_package_job(
    package_id: str,
    job_id: str,
    *,
    urls: list[str] | None = None,
    supplement_queries: list[str] | None = None,
) -> None:
    """素材包后台线程: 抓取(可选) → 补搜(可选) → 审计 → 落库 + SSE."""
    with db_session() as db2:
        try:
            pkg = db2.query(MaterialPackage).filter(MaterialPackage.id == package_id).first()
            if not pkg:
                _publish(job_id, {"type": "material_error", "package_id": package_id, "error": "素材包不存在"})
                return
            article = db2.query(Article).filter(Article.id == pkg.article_id).first()
            if not article:
                _publish(job_id, {"type": "material_error", "package_id": package_id, "error": "主稿不存在"})
                return
            pkg.status = "collecting"
            pkg.error_message = None
            db2.commit()

            # 1) 批量抓取 (建包时)
            if urls:
                results = material_service.batch_fetch_urls(urls)
                for i, res in enumerate(results, start=1):
                    db2.add(MaterialItem(
                        package_id=pkg.id,
                        source_type="url",
                        title=res["title"] or None,
                        source_url=res["url"],
                        raw_text=res["raw_text"],
                        fetch_ok=res["ok"],
                        char_count=len(res["raw_text"]),
                    ))
                    if i % 2 == 0 or i == len(results):
                        _publish(job_id, {
                            "type": "material_fetch_progress",
                            "package_id": pkg.id, "done": i, "total": len(results),
                        })
                db2.commit()
                db2.refresh(pkg)

            # 2) 智谱定向补搜 (缺口搜索词)
            if supplement_queries:
                _publish(job_id, {
                    "type": "material_search_start",
                    "package_id": pkg.id, "queries": supplement_queries,
                })
                material_service.search_and_ingest(db2, pkg, supplement_queries)
                pkg.search_rounds += 1
                db2.commit()
                db2.refresh(pkg)

            # 3) 七层覆盖审计 (传上一轮结果: applicable 锁定, 防 LLM 判定翻转)
            _publish(job_id, {"type": "material_audit_start", "package_id": pkg.id})
            ok_items = [it for it in pkg.items if it.fetch_ok and it.raw_text]
            audit = material_service.audit_package(
                article.raw_text, ok_items, prev_audit=pkg.audit_json,
                track=getattr(article, "track", "tech") or "tech",
            )
            if audit is None:
                pkg.status = "failed"
                pkg.error_message = "审计 LLM 输出解析失败，请重试（重新审计）"
                db2.commit()
                _publish(job_id, {"type": "material_error", "package_id": pkg.id, "error": pkg.error_message})
                return
            pkg.audit_json = audit
            # 审计 item_tags 回填到条目 layer_tags;
            # item_numbers 映射 (2026-08-25): 精确按 item_id 查编号 — 修复旧版按
            # ok_items 位置反推在 fetch_ok 翻转时错位; 旧包无映射退化位置反推。
            _num_map = audit.get("item_numbers") or {}
            for i, item in enumerate(ok_items, start=1):
                n = _num_map.get(str(item.id), i)
                item.layer_tags = (audit.get("item_tags") or {}).get(str(n)) or None
            covered = sum(1 for l in audit["layers"].values() if l["covered"])
            pkg.status = "audited"
            db2.commit()
            _publish(job_id, {
                "type": "material_done",
                "package_id": pkg.id, "covered": covered, "total": 7,
            })
        except Exception as exc:
            logger.exception("[material] background job failed for %s: %s", package_id, exc)
            try:
                pkg = db2.query(MaterialPackage).filter(MaterialPackage.id == package_id).first()
                if pkg:
                    pkg.status = "failed"
                    pkg.error_message = str(exc)
                    db2.commit()
            except Exception:
                pass
            try:
                _publish(job_id, {"type": "material_error", "package_id": package_id, "error": str(exc)})
            except Exception:
                pass


def _spawn(package_id: str, *, urls: list[str] | None = None,
           supplement_queries: list[str] | None = None) -> str:
    """生成 job_id 并起 daemon 线程, 返回 job_id."""
    job_id = uuid.uuid4().hex[:12]
    threading.Thread(
        target=_run_package_job,
        kwargs={
            "package_id": package_id,
            "job_id": job_id,
            "urls": urls,
            "supplement_queries": supplement_queries,
        },
        daemon=True,
    ).start()
    return job_id


@router.post("/packages")
def create_package(payload: PackageCreateRequest, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == payload.article_id).first()
    if not article:
        raise HTTPException(404, "Article not found")
    pkg = MaterialPackage(article_id=article.id, title=payload.title or article.title)
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    job_id = _spawn(pkg.id, urls=payload.urls)
    return {"id": pkg.id, "job_id": job_id, "status": pkg.status}


@router.get("/packages")
def list_packages(article_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(MaterialPackage)
    if article_id:
        q = q.filter(MaterialPackage.article_id == article_id)
    pkgs = q.order_by(MaterialPackage.created_at.desc()).all()
    return [_brief(p) for p in pkgs]


@router.get("/packages/{package_id}")
def get_package(package_id: str, db: Session = Depends(get_db)):
    pkg = db.query(MaterialPackage).filter(MaterialPackage.id == package_id).first()
    if not pkg:
        raise HTTPException(404, "Material package not found")
    article = db.query(Article).filter(Article.id == pkg.article_id).first()
    return _detail(pkg, article)


@router.post("/packages/{package_id}/items", response_model=MaterialItemOut)
def add_item(package_id: str, payload: MaterialItemAddRequest, db: Session = Depends(get_db)):
    pkg = db.query(MaterialPackage).filter(MaterialPackage.id == package_id).first()
    if not pkg:
        raise HTTPException(404, "Material package not found")
    if payload.url:
        res = fetch_url(payload.url)
        item = MaterialItem(
            package_id=pkg.id,
            source_type="url",
            title=res.get("title") or payload.title,
            source_url=payload.url,
            raw_text=res.get("raw_text") or "",
            fetch_ok=bool(res.get("ok")),
            char_count=len(res.get("raw_text") or ""),
        )
    elif payload.text:
        item = MaterialItem(
            package_id=pkg.id,
            source_type="manual",
            title=payload.title,
            raw_text=payload.text,
            fetch_ok=True,
            char_count=len(payload.text),
        )
    else:
        raise HTTPException(422, "url 或 text 至少提供一项")
    pkg.status = "collecting"
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/packages/{package_id}/items/{item_id}")
def delete_item(package_id: str, item_id: str, db: Session = Depends(get_db)):
    item = (
        db.query(MaterialItem)
        .filter(MaterialItem.id == item_id, MaterialItem.package_id == package_id)
        .first()
    )
    if not item:
        raise HTTPException(404, "Material item not found")
    pkg = db.query(MaterialPackage).filter(MaterialPackage.id == package_id).first()
    if pkg:
        pkg.status = "collecting"
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.post("/packages/{package_id}/audit")
def run_audit(package_id: str, db: Session = Depends(get_db)):
    pkg = db.query(MaterialPackage).filter(MaterialPackage.id == package_id).first()
    if not pkg:
        raise HTTPException(404, "Material package not found")
    job_id = _spawn(pkg.id)
    return {"job_id": job_id}


@router.post("/packages/{package_id}/supplement-search")
def supplement_search(package_id: str, payload: SupplementSearchRequest, db: Session = Depends(get_db)):
    pkg = db.query(MaterialPackage).filter(MaterialPackage.id == package_id).first()
    if not pkg:
        raise HTTPException(404, "Material package not found")
    queries = [q.strip()[:70] for q in (payload.queries or []) if q.strip()]
    if not queries:
        queries = material_service.collect_gap_queries(pkg.audit_json)
    if not queries:
        raise HTTPException(400, "无可补搜的查询词（先跑审计或勾选搜索词）")
    job_id = _spawn(pkg.id, supplement_queries=queries)
    return {"job_id": job_id, "queries": queries}


@router.delete("/packages/{package_id}")
def delete_package(package_id: str, db: Session = Depends(get_db)):
    pkg = db.query(MaterialPackage).filter(MaterialPackage.id == package_id).first()
    if not pkg:
        raise HTTPException(404, "Material package not found")
    db.delete(pkg)
    db.commit()
    return {"ok": True}
