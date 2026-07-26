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
class DefaultsConfig:
    host_id: str
    voice_id: str
    backend: str
    base_url_fish: str
    base_url_f5: str
    base_url_indextts: str
    base_url_comfyui: str
    comfyui_timeout_sec: int
    roles_output_root: str


@dataclass(frozen=True)
class Config:
    app: AppConfig
    deepseek: DeepSeekConfig
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


def load_config(path: Path | str | None = None) -> Config:
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
    deepseek = DeepSeekConfig(
        api_key=_resolve_env(ds_raw.get("api_key", "")),
        base_url=ds_raw.get("base_url", "https://api.deepseek.com"),
        model_flash=ds_raw.get("model_flash", "deepseek-v4-flash"),
        model_pro=ds_raw.get("model_pro", "deepseek-v4-pro"),
        default_model=ds_raw.get("default_model", "flash"),
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
        comfyui_timeout_sec=int(defaults_raw.get("comfyui_timeout_sec", 600)),
        roles_output_root=defaults_raw.get(
            "roles_output_root", "E:/数字人计划/roles"
        ),
    )

    return Config(app=app, deepseek=deepseek, defaults=defaults, raw=raw)


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
