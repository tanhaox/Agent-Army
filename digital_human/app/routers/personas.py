"""Persona API — 数字人物关联 (提示词模板 + 音色 + 形象)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Persona, Role, Voice
from ..schemas import PersonaCreate, PersonaOut, PersonaUpdate

router = APIRouter(prefix="/api/personas", tags=["personas"])


@router.get("", response_model=list[PersonaOut])
def list_personas(db: Session = Depends(get_db)):
    """列出所有人物关联."""
    return db.query(Persona).order_by(Persona.created_at).all()


@router.post("", response_model=PersonaOut, status_code=201)
def create_persona(body: PersonaCreate, db: Session = Depends(get_db)):
    """创建人物关联 (prompt_template 唯一)."""
    existing = (
        db.query(Persona)
        .filter(Persona.prompt_template == body.prompt_template)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"提示词模板 '{body.prompt_template}' 已绑定人物 '{existing.name}'",
        )
    if body.voice_id and not db.get(Voice, body.voice_id):
        raise HTTPException(status_code=404, detail=f"Voice {body.voice_id} not found")
    if body.role_id and not db.get(Role, body.role_id):
        raise HTTPException(status_code=404, detail=f"Role {body.role_id} not found")

    persona = Persona(
        name=body.name,
        prompt_template=body.prompt_template,
        voice_id=body.voice_id,
        role_id=body.role_id,
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


@router.put("/{persona_id}", response_model=PersonaOut)
def update_persona(persona_id: str, body: PersonaUpdate, db: Session = Depends(get_db)):
    """更新人物关联."""
    persona = db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    if body.prompt_template is not None and body.prompt_template != persona.prompt_template:
        dup = (
            db.query(Persona)
            .filter(Persona.prompt_template == body.prompt_template, Persona.id != persona_id)
            .first()
        )
        if dup:
            raise HTTPException(
                status_code=409,
                detail=f"提示词模板 '{body.prompt_template}' 已绑定人物 '{dup.name}'",
            )
        persona.prompt_template = body.prompt_template

    if body.name is not None:
        persona.name = body.name
    if body.voice_id is not None:
        if body.voice_id and not db.get(Voice, body.voice_id):
            raise HTTPException(status_code=404, detail=f"Voice {body.voice_id} not found")
        persona.voice_id = body.voice_id or None
    if body.role_id is not None:
        if body.role_id and not db.get(Role, body.role_id):
            raise HTTPException(status_code=404, detail=f"Role {body.role_id} not found")
        persona.role_id = body.role_id or None

    db.commit()
    db.refresh(persona)
    return persona


@router.delete("/{persona_id}", status_code=204)
def delete_persona(persona_id: str, db: Session = Depends(get_db)):
    """删除人物关联."""
    persona = db.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    db.delete(persona)
    db.commit()


@router.get("/by-template/{template_name}", response_model=PersonaOut | None)
def get_persona_by_template(template_name: str, db: Session = Depends(get_db)):
    """根据提示词模板名查询关联的人物 (流水线联动用)."""
    persona = (
        db.query(Persona)
        .filter(Persona.prompt_template == template_name)
        .first()
    )
    return persona
