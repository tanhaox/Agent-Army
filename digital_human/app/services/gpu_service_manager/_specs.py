"""GPU 服务部署事实 + 模型定义 + 配置构建.

内置默认 (可被 config/app.yaml `tts_services.<key>` 覆盖):
  fish     E:/AI/tts/fish-speech       tools/api_server.py  :7860  /v1/health
  f5       E:/AI/tts/F5-TTS            f5-tts_infer-gradio  :7861  /
  indextts E:/AI/tts/index-tts2.5     api_server.py        :7862  /health
  comfyui  E:/AI/ComfyUI_windows_portable main.py           :8188  /system_stats
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = ["ServiceSpec", "build_specs", "NO_LOCAL_SERVICE"]


# ── 内置部署事实 ──────────────────────────────────────────────
_BUILTIN_SPECS: dict[str, dict[str, Any]] = {
    "fish": {
        "display_name": "Fish Speech",
        "base_url": "http://127.0.0.1:7860",
        "health_path": "/v1/health",
        "cwd": "E:/AI/tts/fish-speech",
        "command": [
            ".venv/Scripts/python.exe", "tools/api_server.py",
            "--listen", "127.0.0.1:7860",
            "--llama-checkpoint-path", "E:/AI/tts/models/s2-pro",
            "--decoder-checkpoint-path", "E:/AI/tts/models/s2-pro/codec.pth",
            "--decoder-config-name", "modded_dac_vq",
            "--device", "cuda",
        ],
        "env": {},
    },
    "f5": {
        "display_name": "F5-TTS",
        "base_url": "http://127.0.0.1:7861",
        "health_path": "/",
        "cwd": "E:/AI/tts/F5-TTS",
        "command": [
            ".venv/Scripts/f5-tts_infer-gradio.exe",
            "--host", "127.0.0.1", "--port", "7861",
        ],
        "env": {},
    },
    "indextts": {
        # 2026-08-25 回退产线至 IndexTTS2: 2.5 语速/韵律/情绪联动仍需联调, 不可投产。
        # 2.5 安装保留在 E:/AI/tts/index-tts2.5 (实验位), 联调完成后改回:
        #   cwd=E:/AI/tts/index-tts2.5 + HF_HOME 同目录 + display_name IndexTTS2.5
        # 端口与接口两版一致。
        "display_name": "IndexTTS2",
        "base_url": "http://127.0.0.1:7862",
        "health_path": "/health",
        "cwd": "E:/AI/tts/index-tts-windows",
        "command": [
            ".venv/Scripts/python.exe", "api_server.py",
            "--port", "7862", "--host", "127.0.0.1",
        ],
        # 与 api_server 内部一致: 清 PYTHONPATH + HF 镜像
        "env": {
            "PYTHONPATH": "",
            "HF_ENDPOINT": "https://hf-mirror.com",
            "HF_HOME": "E:/AI/tts/index-tts-windows/.huggingface",
        },
    },
    "comfyui": {
        "display_name": "ComfyUI",
        "base_url": "http://127.0.0.1:8188",
        "health_path": "/system_stats",
        "cwd": "E:/AI/ComfyUI_windows_portable",
        "command": [
            "python_embeded/python.exe", "-s", "ComfyUI/main.py",
            "--windows-standalone-build", "--listen", "127.0.0.1",
        ],
        # 与 run_nvidia_gpu.bat 一致: CUDA_VISIBLE_DEVICES=0 锚定 4090
        # (本机 CUDA 视角 CUDA0=4090 / CUDA1=4060, 不设会落 4060 8GB OOM)
        "env": {"CUDA_VISIBLE_DEVICES": "0"},
    },
}

# elevenlabs 等云端后端不占本地 GPU, session 直接放行
NO_LOCAL_SERVICE = {"elevenlabs"}


@dataclass
class ServiceSpec:
    key: str
    display_name: str
    base_url: str
    health_path: str
    cwd: Path
    command: list[str]
    env: dict[str, str]

    @property
    def health_url(self) -> str:
        return self.base_url.rstrip("/") + self.health_path


def build_specs(raw_cfg: dict[str, Any]) -> tuple[dict[str, ServiceSpec], dict[str, Any]]:
    """内置默认 + app.yaml `tts_services` 覆盖 → ServiceSpec 表."""
    svc_cfg = raw_cfg.get("tts_services") or {}
    specs: dict[str, ServiceSpec] = {}
    for key, builtin in _BUILTIN_SPECS.items():
        override = svc_cfg.get(key) or {}
        merged = {**builtin, **override}
        specs[key] = ServiceSpec(
            key=key,
            display_name=merged["display_name"],
            base_url=merged["base_url"],
            health_path=merged["health_path"],
            cwd=Path(merged["cwd"]),
            command=list(merged["command"]),
            env=dict(merged.get("env") or {}),
        )
    return specs, svc_cfg
