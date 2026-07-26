"""Hosts router: list hosts for voice management."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Host
from ..schemas import HostOut

router = APIRouter(prefix="/api/hosts", tags=["hosts"])


@router.get("", response_model=list[HostOut])
def list_hosts(db: Session = Depends(get_db)):
    return db.query(Host).order_by(Host.name).all()
