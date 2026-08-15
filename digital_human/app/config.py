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
class QwenConfig:
    api_key: str
    base_url: str
    model_flash: str
    model_pro: str
    default_model: str = "flash"


@dataclass(frozen=True)
class SiliconFlowConfig:
    api_key: str
    base_url: str
    model_flash: str
    model_pro: str


@dataclass(frozen=True)
class ZhipuConfig:
    """智谱联网搜索 (2026-08-15): 素材聚合补搜专用, 独立 /web_search 端点."""

    api_key: str
    base_url: str  # https://open.bigmodel.cn/api/paas/v4
    search_engine: str  # search_std / search_pro / search_pro_sogou / search_pro_quark
    content_size: str  # medium(摘要) / high(详细)
    count: int
    recency: str  # oneDay/oneWeek/oneMonth/oneYear/noLimit
    timeout_sec: int
    free_quota_expires: str  # 免费额度到期日 YYYY-MM-DD, 到期提示用


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
    # 本地素材成片复用上限 (2026-08-15): 同一素材最多进入 N 个成片 (used_count
    # 硬过滤, 防一批"万能素材"每个视频都被选中)。0 = 关闭限制。
    local_asset_max_uses: int
    # J 线剪映草稿目录 (2026-08-15): 导出的草稿直接落剪映草稿文件夹,
    # 打开剪映即可在列表顶部看到 (注册+时间戳由剪映自身扫描完成)。
    jianying_drafts_dir: str


@dataclass(frozen=True)
class Config:
    app: AppConfig
    deepseek: DeepSeekConfig
    siliconflow: SiliconFlowConfig
    qwen: QwenConfig
    local_llm: LocalLLMConfig
    zhipu: ZhipuConfig
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

    qw_raw = raw.get("qwen", {})
    qwen = QwenConfig(
        api_key=_resolve_env(qw_raw.get("api_key", "")),
        base_url=qw_raw.get("base_url", "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"),
        model_flash=qw_raw.get("model_flash", "qwen3.6-flash"),
        model_pro=qw_raw.get("model_pro", "qwen3.8-max"),
        default_model=qw_raw.get("default_model", "flash"),
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
        local_asset_max_uses=int(defaults_raw.get("local_asset_max_uses", 2)),
        # J 线: 默认落在当前用户的新版剪映草稿目录
        jianying_drafts_dir=defaults_raw.get(
            "jianying_drafts_dir",
            os.path.join(
                os.environ.get("LOCALAPPDATA", ""),
                "JianyingPro", "User Data", "Projects", "com.lveditor.draft",
            ),
        ),
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

    # 硅基流动 (可选, 缺失时用空值替代)
    sf_raw = raw.get("siliconflow", {})
    siliconflow = SiliconFlowConfig(
        api_key=sf_raw.get("api_key", ""),
        base_url=sf_raw.get("base_url", "https://api.siliconflow.cn/v1"),
        model_flash=sf_raw.get("model_flash", "deepseek-ai/DeepSeek-V4-Flash"),
        model_pro=sf_raw.get("model_pro", "deepseek-ai/DeepSeek-V4-Pro"),
    )

    # 智谱联网搜索 (2026-08-15): 素材聚合补搜, 独立 web_search 端点
    zp_raw = raw.get("zhipu", {})
    zhipu = ZhipuConfig(
        api_key=_resolve_env(zp_raw.get("api_key", "")),
        base_url=zp_raw.get("base_url", "https://open.bigmodel.cn/api/paas/v4"),
        search_engine=zp_raw.get("search_engine", "search_pro"),
        content_size=zp_raw.get("content_size", "high"),
        count=int(zp_raw.get("count", 5)),
        recency=zp_raw.get("recency", "noLimit"),
        timeout_sec=int(zp_raw.get("timeout_sec", 30)),
        free_quota_expires=zp_raw.get("free_quota_expires", "2026-09-12"),
    )
    return Config(app=app, deepseek=deepseek, siliconflow=siliconflow, qwen=qwen, local_llm=local_llm, zhipu=zhipu, defaults=defaults, raw=raw)


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
