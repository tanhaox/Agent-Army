"""Script and segment router (director endpoints included)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Script, Segment
from ..schemas import ScriptOut, ScriptUpdate, SegmentOut, SegmentUpdate

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.get("/{script_id}", response_model=ScriptOut)
def get_script(script_id: str, db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.put("/{script_id}", response_model=ScriptOut)
def update_script(script_id: str, payload: ScriptUpdate, db: Session = Depends(get_db)):
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    if payload.script_text is not None:
        script.script_text = payload.script_text
        # Re-parse segments preserving director selections.
        from ..services.script_parser import parse_script

        existing = {seg.line_index: seg for seg in script.segments}
        parsed = parse_script(script.script_text)
        new_segments = []
        for p in parsed:
            old = existing.get(p["line_index"])
            if old:
                old.text = p["text"]
                old.control_chars = p["control_chars"]
                old.segment_type = p["segment_type"]
            else:
                new_segments.append(Segment(script_id=script.id, **p))
        # Remove segments whose line_index no longer exists.
        new_line_indices = {p["line_index"] for p in parsed}
        for seg in script.segments:
            if seg.line_index not in new_line_indices:
                db.delete(seg)
        db.add_all(new_segments)

    if payload.status is not None:
        script.status = payload.status

    db.commit()
    db.refresh(script)
    return script


@router.put("/segments/{segment_id}", response_model=SegmentOut)
def update_segment(segment_id: str, payload: SegmentUpdate, db: Session = Depends(get_db)):
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    if payload.text is not None:
        segment.text = payload.text
    if payload.selected_for_host is not None:
        segment.selected_for_host = payload.selected_for_host
    if payload.host_order is not None:
        segment.host_order = payload.host_order
    if payload.segment_type is not None:
        segment.segment_type = payload.segment_type
    db.commit()
    db.refresh(segment)
    return segment


@router.post("/{script_id}/segments/reorder")
def reorder_segments(script_id: str, segment_ids: list[str], db: Session = Depends(get_db)):
    """Batch update host_order by ordered list of segment ids."""
    segments = db.query(Segment).filter(Segment.script_id == script_id).all()
    seg_map = {s.id: s for s in segments}
    if len(segment_ids) != len(seg_map):
        raise HTTPException(status_code=400, detail="Segment ids mismatch")
    for order, seg_id in enumerate(segment_ids):
        seg_map[seg_id].host_order = order
    db.commit()
    return {"updated": len(segment_ids)}


@router.get("/{script_id}/director-segments", response_model=list[SegmentOut])
def get_director_segments(script_id: str, db: Session = Depends(get_db)):
    """Return segments selected for host, ordered by host_order."""
    segments = (
        db.query(Segment)
        .filter(Segment.script_id == script_id, Segment.selected_for_host == True)
        .order_by(Segment.host_order)
        .all()
    )
    return segments
