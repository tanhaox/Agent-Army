"""Voice router: CRUD + TTS test/trial endpoint."""
from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Voice
from ..services.gpu_service_manager import get_gpu_service_manager
from ..schemas import (
    VoiceCreate,
    VoiceOut,
    VoiceUpdate,
    VoiceTestRequest,
    VoiceCarnivalRequest,
    VoiceSetReferenceRequest,
)
from .jobs import _publish

router = APIRouter(prefix="/api/voices", tags=["voices"])


@router.get("", response_model=list[VoiceOut])
def list_voices(db: Session = Depends(get_db)):
    return db.query(Voice).order_by(Voice.name).all()


@router.get("/{voice_id}", response_model=VoiceOut)
def get_voice(voice_id: str, db: Session = Depends(get_db)):
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


@router.post("", response_model=VoiceOut, status_code=201)
def create_voice(body: VoiceCreate, db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    # Merge params into config_json
    params = data.pop("params", None)
    if params:
        config_json = data.get("config_json") or {}
        config_json["params"] = params
        data["config_json"] = config_json
    voice = Voice(**data)
    db.add(voice)
    db.commit()
    db.refresh(voice)
    return voice


@router.put("/{voice_id}", response_model=VoiceOut)
def update_voice(voice_id: str, body: VoiceUpdate, db: Session = Depends(get_db)):
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    data = body.model_dump(exclude_unset=True)
    # Merge params into config_json
    params = data.pop("params", None)
    if params:
        config_json = dict(voice.config_json) if voice.config_json else {}
        config_json["params"] = params
        data["config_json"] = config_json
    for k, v in data.items():
        setattr(voice, k, v)
    db.commit()
    db.refresh(voice)
    return voice


@router.delete("/{voice_id}", status_code=204)
def delete_voice(voice_id: str, db: Session = Depends(get_db)):
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    db.delete(voice)
    db.commit()


@router.post("/{voice_id}/test")
def test_voice(voice_id: str, body: VoiceTestRequest, db: Session = Depends(get_db)):
    """Synthesize a short test sentence with the selected voice.

    Returns the audio WAV file for the browser to play.
    """
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")

    base_url_fish = voice.base_url_fish or "http://127.0.0.1:7860"
    base_url_f5 = voice.base_url_f5 or "http://127.0.0.1:7861"
    base_url_indextts = voice.base_url_indextts or "http://127.0.0.1:7862"
    backend = voice.backend or "fish"
    ref_audio = Path(voice.reference_audio_path) if voice.reference_audio_path else None
    ref_text = voice.reference_text or ""
    master_audio = Path(voice.master_audio_path) if voice.master_audio_path else ref_audio
    master_text = voice.master_text or ref_text
    master_style = "calm"
    if body.params:
        ms = getattr(body.params, "master_style", None)
        if isinstance(ms, str) and ms in ("calm", "excited", "relaxed"):
            master_style = ms

    # Pre-flight: indextts backend needs an existing master audio file
    if backend == "indextts":
        if not master_audio or not master_audio.exists():
            raise HTTPException(
                status_code=400,
                detail="Backend=indextts 需要主音色音频 (master_audio_path)。请在编辑面板上传 master audio,或先填写 reference_audio_path 作为兜底。",
            )

    # Merge params: saved (config_json) as base, request body.params overrides.
    merged_params: dict[str, Any] = {}
    if voice.config_json and isinstance(voice.config_json, dict):
        saved = voice.config_json.get("params")
        if saved and isinstance(saved, dict):
            merged_params.update(saved)
    if body.params:
        merged_params.update(body.params.model_dump(exclude_unset=True))

    # Save to a temp file so we can stream it back.
    tmp = Path(tempfile.mktemp(suffix=".wav"))

    # Ensure tts_client is importable.
    _project_root = Path(__file__).resolve().parents[2]
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

    from scripts import tts_client

    try:
        with get_gpu_service_manager().session(backend):
            tts_client.synthesize(
                text=body.text,
                output_path=tmp,
                backend=backend,  # type: ignore[arg-type]
                voice_id=voice.name,
                reference_audio=master_audio if master_audio and master_audio.exists() else None,
                reference_text=master_text,
                base_url_fish=base_url_fish,
                base_url_f5=base_url_f5,
                base_url_indextts=base_url_indextts,
                master_audio=master_audio,
                master_text=master_text,
                master_style=master_style,
                params=merged_params or None,
            )
        return FileResponse(
            path=tmp,
            media_type="audio/wav",
            filename=f"test_{voice.name}.wav",
            headers={"Content-Disposition": "inline"},
        )
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail=f"TTS test failed: {exc}")


# In-memory store: job_id -> {"zip_bytes": bytes | None, "error": str | None}
_carnival_jobs: dict[str, dict[str, Any]] = {}


@router.post("/{voice_id}/carnival")
async def carnival_voice_start(voice_id: str, body: VoiceCarnivalRequest, db: Session = Depends(get_db)):
    """疯狂抽卡: 异步启动抽卡任务, 返回 job_id 用于 SSE 进度监听.

    POST 后立即返回 job_id.
    客户端再连 GET /api/jobs/{job_id}/events 拿 SSE 进度.
    生成完成后 GET /api/voices/carnival/{job_id}/download 下载 ZIP.
    """
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")

    base_url_fish = voice.base_url_fish or "http://127.0.0.1:7860"
    base_url_f5 = voice.base_url_f5 or "http://127.0.0.1:7861"
    base_url_indextts = voice.base_url_indextts or "http://127.0.0.1:7862"
    backend = voice.backend or "fish"
    ref_audio = Path(voice.reference_audio_path) if voice.reference_audio_path else None
    ref_text = voice.reference_text or ""
    master_audio = Path(voice.master_audio_path) if voice.master_audio_path else ref_audio
    master_text = voice.master_text or ref_text
    master_style = "calm"
    if body.params:
        ms = getattr(body.params, "master_style", None)
        if isinstance(ms, str) and ms in ("calm", "excited", "relaxed"):
            master_style = ms

    # Pre-flight: indextts backend needs an existing master audio file
    if backend == "indextts":
        if not master_audio or not master_audio.exists():
            raise HTTPException(
                status_code=400,
                detail="Backend=indextts 需要主音色音频 (master_audio_path)。请在编辑面板上传 master audio,或先填写 reference_audio_path 作为兜底。",
            )

    # Merge params: saved (config_json) as base, request body.params overrides.
    merged_params: dict[str, Any] = {}
    if voice.config_json and isinstance(voice.config_json, dict):
        saved = voice.config_json.get("params")
        if saved and isinstance(saved, dict):
            merged_params.update(saved)
    if body.params:
        merged_params.update(body.params.model_dump(exclude_unset=True))

    job_id = str(uuid.uuid4())[:8]
    _carnival_jobs[job_id] = {"zip_bytes": None, "error": None}

    def _run_carnival():
        """Background thread: generate all versions, publish SSE progress."""
        _project_root = Path(__file__).resolve().parents[2]
        if str(_project_root) not in sys.path:
            sys.path.insert(0, str(_project_root))

        from scripts import tts_client

        tmp_dir = Path(tempfile.mkdtemp(suffix="_carnival"))
        try:
            def _svc_notify(message: str) -> None:
                _publish(job_id, {"type": "carnival_service", "message": message})

            with get_gpu_service_manager().session(backend, status_callback=_svc_notify):
                for i in range(body.count):
                    version_params = dict(merged_params) if merged_params else {}
                    version_params["seed"] = i + 1

                    out_path = tmp_dir / f"version_{i+1:02d}.wav"
                    tts_client.synthesize(
                        text=body.text,
                        output_path=out_path,
                        backend=backend,
                        voice_id=voice.name,
                        reference_audio=master_audio if master_audio and master_audio.exists() else None,
                        reference_text=master_text,
                        base_url_fish=base_url_fish,
                        base_url_f5=base_url_f5,
                        base_url_indextts=base_url_indextts,
                        master_audio=master_audio,
                        master_text=master_text,
                        master_style=master_style,
                        params=version_params,
                    )

                    _publish(job_id, {
                        "type": "carnival_progress",
                        "current": i + 1,
                        "total": body.count,
                        "seed": i + 1,
                    })

            # Package all WAVs into a ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i in range(body.count):
                    wav_path = tmp_dir / f"version_{i+1:02d}.wav"
                    if wav_path.exists():
                        zf.write(wav_path, f"version_{i+1:02d}.wav")
            _carnival_jobs[job_id]["zip_bytes"] = zip_buffer.getvalue()

            _publish(job_id, {
                "type": "carnival_done",
                "job_id": job_id,
                "total": body.count,
            })
        except Exception as exc:
            _carnival_jobs[job_id]["error"] = str(exc)
            _publish(job_id, {
                "type": "carnival_error",
                "error": str(exc),
            })
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    threading.Thread(target=_run_carnival, daemon=True).start()

    return {"job_id": job_id, "total": body.count}


@router.get("/carnival/{job_id}/download")
def carnival_download(job_id: str):
    """下载抽卡完成的 ZIP 包."""
    job = _carnival_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["error"]:
        raise HTTPException(status_code=502, detail=f"Carnival failed: {job['error']}")
    if job["zip_bytes"] is None:
        raise HTTPException(status_code=425, detail="Carnival still in progress")
    return Response(
        content=job["zip_bytes"],
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=carnival_{job_id}.zip",
        },
    )


@router.post("/{voice_id}/test-and-anchor")
def test_and_anchor(voice_id: str, body: VoiceTestRequest, db: Session = Depends(get_db)):
    """合成试听音频并直接设为固定参考音锚点.

    生成音频保存到 references/{voice_id}/anchor.wav,
    同时更新 voice 的 reference_audio_path 和 reference_text.
    返回 WAV 文件供浏览器播放/试听.
    """
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")

    base_url_fish = voice.base_url_fish or "http://127.0.0.1:7860"
    base_url_f5 = voice.base_url_f5 or "http://127.0.0.1:7861"
    base_url_indextts = voice.base_url_indextts or "http://127.0.0.1:7862"
    backend = voice.backend or "fish"
    ref_audio = Path(voice.reference_audio_path) if voice.reference_audio_path else None
    ref_text = voice.reference_text or ""
    master_audio = Path(voice.master_audio_path) if voice.master_audio_path else ref_audio
    master_text = voice.master_text or ref_text

    # Pre-flight: indextts backend needs an existing master audio file
    if backend == "indextts":
        if not master_audio or not master_audio.exists():
            raise HTTPException(
                status_code=400,
                detail="Backend=indextts 需要主音色音频 (master_audio_path)。请在编辑面板上传 master audio,或先填写 reference_audio_path 作为兜底。",
            )

    merged_params: dict[str, Any] = {}
    if voice.config_json and isinstance(voice.config_json, dict):
        saved = voice.config_json.get("params")
        if saved and isinstance(saved, dict):
            merged_params.update(saved)
    if body.params:
        merged_params.update(body.params.model_dump(exclude_unset=True))

    _project_root = Path(__file__).resolve().parents[2]
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    from scripts import tts_client

    ref_dir = _project_root / "references" / voice_id
    ref_dir.mkdir(parents=True, exist_ok=True)
    output_path = ref_dir / "anchor.wav"

    try:
        with get_gpu_service_manager().session(backend):
            tts_client.synthesize(
                text=body.text,
                output_path=output_path,
                backend=backend,
                voice_id=voice.name,
                reference_audio=None,
                reference_text="",
                base_url_fish=base_url_fish,
                base_url_f5=base_url_f5,
                base_url_indextts=base_url_indextts,
                master_audio=master_audio,
                master_text=master_text,
                master_style="calm",
                params=merged_params or None,
            )
        voice.reference_audio_path = str(output_path)
        voice.reference_text = body.text
        db.commit()
        db.refresh(voice)

        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename=f"anchor_{voice.name}.wav",
            headers={"Content-Disposition": "inline"},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Anchor TTS failed: {exc}")


@router.post("/{voice_id}/set-reference")
def set_voice_reference(voice_id: str, body: VoiceSetReferenceRequest, db: Session = Depends(get_db)):
    """将用户选中的优质音频片段设为音色的固定参考音锚点.

    参考音 + 准确文本 = Fish Speech "声音锚点" (最可靠的音色稳定方式).
    后续所有 TTS 请求都使用同样的 reference_audio + reference_text.
    """
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")

    audio_path = Path(body.audio_path)
    if not audio_path.exists():
        raise HTTPException(status_code=400, detail=f"Audio file not found: {audio_path}")

    # Copy reference audio into a permanent location under digital_human/
    project_root = Path(__file__).resolve().parents[2]
    ref_dir = project_root / "references" / voice_id
    ref_dir.mkdir(parents=True, exist_ok=True)
    ref_path = ref_dir / "anchor.wav"
    shutil.copy2(str(audio_path), str(ref_path))

    # Update voice record
    voice.reference_audio_path = str(ref_path)
    voice.reference_text = body.audio_text
    db.commit()
    db.refresh(voice)

    return {"status": "ok", "detail": f"参考音锚点已设为: {ref_path}"}


@router.post("/{voice_id}/upload-master")
async def upload_master_audio(
    voice_id: str,
    audio: UploadFile = File(...),
    master_text: str = Form(""),
    db: Session = Depends(get_db),
):
    """上传/更新 IndexTTS2 主音色参考音频 (master tape).

    接收 multipart form-data (audio file + master_text),
    持久化到 references/{voice_id}/master_<ts><suffix>,
    同时更新 voice.master_audio_path (与可选的 master_text).
    """
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")

    project_root = Path(__file__).resolve().parents[2]
    ref_dir = project_root / "references" / voice_id
    ref_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(audio.filename or "master.wav").suffix or ".wav"
    dest = ref_dir / f"master_{int(time.time() * 1000)}{suffix}"
    blob = await audio.read()
    if not blob:
        raise HTTPException(status_code=400, detail="Empty file")
    dest.write_bytes(blob)

    voice.master_audio_path = str(dest)
    if master_text:
        voice.master_text = master_text
    db.commit()
    db.refresh(voice)

    return {
        "status": "ok",
        "master_audio_path": voice.master_audio_path,
        "master_text": voice.master_text,
        "size_bytes": len(blob),
    }
