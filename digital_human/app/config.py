"""Application configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "app.yaml"


@dataclass(frozen=True)
class AppConfig:
    name: str
    port: int
    host: str
    database_url: str
    data_dir: Path


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str
    base_url: str
    model_flash: str
    model_pro: str
    default_model: str


@dataclass(frozen=True)
class LocalLLMConfig:
    base_url: str
    model: str
    api_key: str
    timeout_sec: int
    max_retries: int
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class DefaultsConfig:
    host_id: str
    voice_id: str
    backend: str
    base_url_fish: str
    base_url_f5: str
    base_url_indextts: str
    base_url_comfyui: str
    comfyui_output_dir: str
    comfyui_input_dir: str
    comfyui_timeout_sec: int
    roles_output_root: str
    # HF (HyperFrames) 视觉渲染模块 — 独立管线,不接 ComfyUI
    hyperframes_bin: str
    hf_render_timeout_sec: int
    hf_visual_root: str
    hf_template_root: str
    # IndexTTS2 / 对齐 / 导演 2.0
    indextts_timeout_sec: int
    whisper_model_size: str
    whisper_device: str
    director_output_root: str
    composition_output_root: str
    # Pexels 素材 resolve 工具 (ID-003)
    pexels_api_key_env: str
    materials_dir: str
    pexels_daily_download_quota: int
    pexels_default_max_results: int
    pexels_min_duration_sec: int
    pexels_preferred_resolution: str
    max_host_slots: int
    job_auto_cleanup_days: int
    # 素材保留策略 (2026-08-07): completed job 的 slot 素材保留天数。
    # 0 = 关闭保留 (回退到旧行为, 出片即删 slots/)。
    slot_retention_days: int
    # 导演素材输入模式 (ID-034): "vocabulary" = 注入关键词词表包 (默认, ~3KB,
    # 解决全量 catalog ~26KB 拖慢 DeepSeek); "full" = 注入全量素材库清单 (旧行为)。
    director_catalog_mode: str


@dataclass(frozen=True)
class Config:
    app: AppConfig
    deepseek: DeepSeekConfig
    local_llm: LocalLLMConfig
    defaults: DefaultsConfig
    raw: dict[str, Any]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _resolve_env(value: Any) -> Any:
    """Replace strings like ${VAR} or ${VAR:default} with environment values."""
    if not isinstance(value, str):
        return value
    if value.startswith("${") and value.endswith("}"):
        inner = value[2:-1]
        if ":" in inner:
            key, default = inner.split(":", 1)
            return os.environ.get(key, default)
        return os.environ.get(inner, "")
    return value


def _load_dotenv(path: Path | None = None) -> None:
    """轻量 .env 加载器 (无第三方依赖).

    仅 setdefault, 不覆盖进程已有环境变量 — 启动脚本显式 set 的值优先.
    pexels_service 等直接读 os.environ 的模块依赖此处注入.
    """
    env_path = path or (PROJECT_ROOT / ".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, val)


def load_config(path: Path | str | None = None) -> Config:
    _load_dotenv()
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    raw = _load_yaml(config_path)

    app_raw = raw.get("app", {})
    data_dir_raw = app_raw.get("data_dir", str(PROJECT_ROOT / "data"))
    data_dir = Path(data_dir_raw)
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    app = AppConfig(
        name=app_raw.get("name", "digital-human-pipeline"),
        port=int(app_raw.get("port", 54321)),
        host=app_raw.get("host", "127.0.0.1"),
        database_url=app_raw.get(
            "database_url",
            f"sqlite:///{data_dir / 'pipeline.db'}",
        ),
        data_dir=data_dir,
    )

    ds_raw = raw.get("deepseek", {})
    api_key = _resolve_env(ds_raw.get("api_key", ""))
    if not api_key:
        # Allow missing key in development, but LLMService will raise on actual use.
        api_key = ""
    deepseek = DeepSeekConfig(
        api_key=api_key,
        base_url=ds_raw.get("base_url", "https://api.deepseek.com"),
        model_flash=ds_raw.get("model_flash", "deepseek-v4-flash"),
        model_pro=ds_raw.get("model_pro", "deepseek-v4-pro"),
        default_model=ds_raw.get("default_model", "flash"),
    )

    llm_raw = raw.get("local_llm", {})
    local_llm = LocalLLMConfig(
        base_url=llm_raw.get("base_url", "http://127.0.0.1:8080"),
        model=llm_raw.get("model", "qwythos-9b"),
        api_key=_resolve_env(llm_raw.get("api_key", "")),
        timeout_sec=int(llm_raw.get("timeout_sec", 120)),
        max_retries=int(llm_raw.get("max_retries", 2)),
        temperature=float(llm_raw.get("temperature", 0.3)),
        max_tokens=int(llm_raw.get("max_tokens", 1024)),
    )

    defaults_raw = raw.get("defaults", {})
    defaults = DefaultsConfig(
        host_id=defaults_raw.get("host_id", "laochen"),
        voice_id=defaults_raw.get("voice_id", "laochen_default"),
        backend=defaults_raw.get("backend", "fish"),
        base_url_fish=defaults_raw.get("base_url_fish", "http://127.0.0.1:7860"),
        base_url_f5=defaults_raw.get("base_url_f5", "http://127.0.0.1:7861"),
        base_url_indextts=defaults_raw.get("base_url_indextts", "http://127.0.0.1:7862"),
        base_url_comfyui=defaults_raw.get("base_url_comfyui", "http://127.0.0.1:8188"),
        comfyui_output_dir=defaults_raw.get(
            "comfyui_output_dir", "E:/AI/ComfyUI_windows_portable/ComfyUI/output"
        ),
        comfyui_input_dir=defaults_raw.get(
            "comfyui_input_dir", "E:/AI/ComfyUI_windows_portable/ComfyUI/input"
        ),
        comfyui_timeout_sec=int(defaults_raw.get("comfyui_timeout_sec", 600)),
        roles_output_root=defaults_raw.get(
            "roles_output_root", "E:/数字人计划/roles"
        ),
        # HF 视觉渲染模块
        hyperframes_bin=defaults_raw.get("hyperframes_bin", "npx"),
        hf_render_timeout_sec=int(defaults_raw.get("hf_render_timeout_sec", 300)),
        hf_visual_root=defaults_raw.get(
            "hf_visual_root", "E:/数字人计划/hf_visual"
        ),
        hf_template_root=defaults_raw.get(
            "hf_template_root", "E:/AI/digital_human/hf_prep"
        ),
        # Pexels 素材 resolve 工具 (ID-003)
        pexels_api_key_env=defaults_raw.get("pexels_api_key_env", "PEXELS_API_KEY"),
        materials_dir=defaults_raw.get("materials_dir", "E:/数字人计划/materials"),
        pexels_daily_download_quota=int(
            defaults_raw.get("pexels_daily_download_quota", 200)
        ),
        pexels_default_max_results=int(
            defaults_raw.get("pexels_default_max_results", 5)
        ),
        pexels_min_duration_sec=int(defaults_raw.get("pexels_min_duration_sec", 5)),
        pexels_preferred_resolution=defaults_raw.get(
            "pexels_preferred_resolution", "FHD"
        ),
        max_host_slots=int(defaults_raw.get("max_host_slots", 4)),
        job_auto_cleanup_days=int(defaults_raw.get("job_auto_cleanup_days", 7)),
        slot_retention_days=int(defaults_raw.get("slot_retention_days", 7)),
        director_catalog_mode=defaults_raw.get("director_catalog_mode", "vocabulary"),
        # IndexTTS2 / 对齐 / 导演 2.0
        indextts_timeout_sec=int(defaults_raw.get("indextts_timeout_sec", 300)),
        whisper_model_size=defaults_raw.get("whisper_model_size", "large-v3"),
        whisper_device=defaults_raw.get("whisper_device", "cuda"),
        director_output_root=defaults_raw.get(
            "director_output_root", "E:/数字人计划/director"
        ),
        composition_output_root=defaults_raw.get(
            "composition_output_root", "E:/数字人计划/composition"
        ),
    )

    return Config(app=app, deepseek=deepseek, local_llm=local_llm, defaults=defaults, raw=raw)


# ── Lazy global accessor (loaded by app.main.lifespan) ──────────────
_config: Config | None = None


def set_config(cfg: Config) -> None:
    """Set the module-level config (called from app.main lifespan)."""
    global _config
    _config = cfg


def get_config() -> Config:
    """Return the loaded config; raises RuntimeError if lifespan didn't run."""
    if _config is None:
        raise RuntimeError("Config not loaded (lifespan did not run)")
    return _config
