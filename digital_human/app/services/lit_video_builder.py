"""LTX 2.3 音频→视频 workflow builder — 54321 Web 系统 SSOT 版.

为什么 Python 构造而非 JSON dump:
  - 用户禁忌: 不要把临时实验 payload 当作最终 SSOT
  - 节点 ID 手写易错, 函数化构造避免 fragile
  - 帧数公式 round(duration*fps)+1 + 对齐 8n+1 在 build 时校验

约定:
  - 返回 ComfyUI API dict-format workflow: {node_id (str): {class_type, inputs}}
  - inputs 中引用其他节点的输出用 ["<node_id>", output_index] 的列表
  - 所有节点 ID 用 int 转 str 的字符串 key
"""
from __future__ import annotations

import random
from typing import Any


def build_ltx23_video_workflow(
    *,
    audio_filename: str,
    storyboard: list[dict[str, Any]],
    duration_sec: float,
    fps: int,
    width: int,
    height: int,
    seed: int | None = None,
    ckpt_name: str = "ltx-2.3-22b-distilled-q8_0.gguf",
    audio_vae_name: str = "ltx-2.3-audio-vae.safetensors",
    dual_clip_name1: str = "t5xxl_fp8mixed.safetensors",
    dual_clip_name2: str = "t5xxl_fp8mixed.safetensors",
    dual_clip_type: str = "ltxv",
    filename_prefix: str = "dhv_",
    steps: int = 20,
    cfg: float = 1.5,
    sampler_name: str = "euler",
    scheduler: str = "simple",
    positive_prompt: str | None = None,
    negative_prompt: str | None = None,
) -> dict[str, dict[str, Any]]:
    """返回 dict-format workflow {node_id: {class_type, inputs}}."""
    frame_count = _frame_count(duration_sec, fps)
    if seed is None:
        seed = random.randint(0, 2_147_483_647)

    nodes: dict[str, dict[str, Any]] = {}

    # ── 1. checkpoint + dual CLIP + audio VAE ──
    nodes["100"] = {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": ckpt_name},
    }
    nodes["110"] = {
        "class_type": "DualCLIPLoader",
        "inputs": {
            "clip_name1": dual_clip_name1,
            "clip_name2": dual_clip_name2,
            "type": dual_clip_type,
            "device": "default",
        },
    }
    nodes["120"] = {
        "class_type": "VAELoader",
        "inputs": {"vae_name": audio_vae_name},
    }

    # ── 2. audio trim to duration ──
    nodes["200"] = {
        "class_type": "LoadAudio",
        "inputs": {"audio": audio_filename},
    }
    nodes["210"] = {
        "class_type": "TrimAudioDuration",
        "inputs": {
            "audio": ["200", 0],
            "trim_to": "seconds",
            "duration": duration_sec,
        },
    }

    # ── 3. latent (空视频潜变量 + 音频潜变量) ──
    nodes["300"] = {
        "class_type": "EmptyLTXVLatentVideo",
        "inputs": {
            "width": width,
            "height": height,
            "length": frame_count,
            "batch_size": 1,
        },
    }
    nodes["310"] = {
        "class_type": "LTXVAudioVAEEncode",
        "inputs": {
            "audio": ["210", 0],
            "vae": ["120", 0],
        },
    }

    # ── 4. image guide chain (多分镜图 → LTXVAddGuide) ──
    prev_latent: list[str | int] = ["300", 0]
    for i, sb in enumerate(storyboard):
        load_id = f"{400 + i * 2}"
        guide_id = f"{400 + i * 2 + 1}"
        nodes[load_id] = {
            "class_type": "LoadImage",
            "inputs": {"image": sb["filename"]},
        }
        frame_idx = sb.get(
            "frame_idx",
            i * max(1, frame_count // max(1, len(storyboard))),
        )
        strength = sb.get("strength", 0.85)
        nodes[guide_id] = {
            "class_type": "LTXVAddGuide",
            "inputs": {
                "latent": prev_latent,
                "image": [load_id, 0],
                "frame_idx": int(frame_idx),
                "strength": float(strength),
            },
        }
        prev_latent = [guide_id, 0]

    # ── 5. concat video+audio latent ──
    nodes["500"] = {
        "class_type": "LTXVConcatAVLatent",
        "inputs": {
            "video_latent": prev_latent,
            "audio_latent": ["310", 0],
        },
    }

    # ── 6. sampler ──
    pos = positive_prompt or (
        "talking head, cinematic, smooth motion, consistent character, "
        "looking at camera, high quality, sharp focus"
    )
    neg = negative_prompt or (
        "blurry, distorted, jittery, mouth artifacts, extra fingers, "
        "low quality, deformed face, asymmetric eyes"
    )
    nodes["600"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": pos, "clip": ["110", 0]},
    }
    nodes["610"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": neg, "clip": ["110", 0]},
    }
    nodes["620"] = {
        "class_type": "SamplerCustom",
        "inputs": {
            "model": ["100", 0],
            "positive": ["600", 0],
            "negative": ["610", 0],
            "latent": ["500", 0],
            "seed": int(seed),
            "steps": int(steps),
            "cfg": float(cfg),
            "sampler_name": sampler_name,
            "scheduler": scheduler,
        },
    }

    # ── 7. separate + decode audio ──
    nodes["700"] = {
        "class_type": "LTXVSeparateAVLatent",
        "inputs": {"latent": ["620", 0]},
    }
    nodes["710"] = {
        "class_type": "LTXVAudioVAEDecode",
        "inputs": {"samples": ["700", 1], "vae": ["120", 0]},
    }

    # ── 8. VHS_VideoCombine → mp4 ──
    nodes["800"] = {
        "class_type": "VHS_VideoCombine",
        "inputs": {
            "frames": ["700", 0],
            "audio": ["710", 0],
            "frame_rate": int(fps),
            "format": "video/h264-mp4",
            "save_output": True,
            "filename_prefix": filename_prefix,
        },
    }

    return nodes


def _frame_count(duration_sec: float, fps: int) -> int:
    """round(duration * fps) + 1, 对齐 8n+1.

    例: 10s @ 24fps → round(240)+1 = 241 = 8*30+1 ✓
        9.96s @ 24fps → round(239.04)+1 = 240, 对齐 → 241 (8*30+1)
    """
    n = round(duration_sec * fps) + 1
    while (n - 1) % 8 != 0:
        n += 1
    if n < 9:
        n = 9
    return n