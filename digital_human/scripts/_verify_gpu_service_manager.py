"""gpu_service_manager 重构行为契约验证.

用法: cd F:/AI-Agent-Local/digital_human && PYTHONIOENCODING=utf-8 PYTHONPATH=F:/AI-Agent-Local/digital_human \
      .venv/Scripts/python.exe scripts/_verify_gpu_service_manager.py
"""
import os
import sys
from unittest.mock import patch

from app.services import gpu_service_manager as m

results = []


def check(name, fn):
    try:
        out = fn()
        ok = bool(out) if not isinstance(out, bool) else out
    except Exception as e:
        ok = False
        results.append((name, f"EXC {type(e).__name__}: {e}"))
        return
    results.append((name, "PASS" if ok else "FAIL"))


def api_present():
    return all(hasattr(m, n) for n in [
        "GPUServiceManager", "ServiceSpec", "get_gpu_service_manager",
        "_manager", "_manager_lock",
    ])


def session_pass_through():
    """非本地服务 / backend 不在 specs / auto_manage=False → 直接放行."""
    mgr = m.GPUServiceManager(specs={}, idle_timeout_sec=300, auto_manage=False)
    entered = False
    with mgr.session("elevenlabs"):
        entered = True
    return entered


def session_local_manage():
    """本地 backend + auto_manage → 排队→ensure→touch→释放 + watchdog 启动."""
    spec = m.ServiceSpec(
        key="fish", display_name="Fish", base_url="http://127.0.0.1:7860",
        health_path="/v1/health", cwd=sys.path[0], command=["python", "-c", "pass"], env={},
    )
    mgr = m.GPUServiceManager(specs={"fish": spec}, idle_timeout_sec=300, auto_manage=True)
    calls = []
    with patch("app.services.gpu_service_manager._manager.http_ok", return_value=True) as ok, \
         patch("app.services.gpu_service_manager._lifecycle.http_ok", return_value=True) as ok2, \
         patch.object(mgr, "_touch", side_effect=lambda k: calls.append("touch")):
        with mgr.session("fish", lambda msg: calls.append(f"n:{msg}")):
            calls.append("body")
            assert mgr._gpu_lock.locked()
    return "body" in calls and "touch" in calls


def build_specs_merge():
    """内置默认 + override 合并 + 类型转换."""
    raw = {"tts_services": {
        "fish": {"base_url": "http://127.0.0.1:9999", "env": {"EXTRA": "1"}},
    }}
    specs, svc_cfg = m._specs.build_specs(raw)
    fish = specs["fish"]
    return (
        fish.base_url == "http://127.0.0.1:9999"
        and fish.health_path == "/v1/health"  # 内置保留
        and os.path.normcase(os.fspath(fish.cwd)) == os.path.normcase("E:/AI/tts/fish-speech")  # 内置 cwd 保留
        and fish.env == {"EXTRA": "1"}  # override 整个替换 env
        and "comfyui" in specs and len(specs) == 4
    )


def http_ok_status():
    from app.services.gpu_service_manager import _http
    return callable(_http.http_ok) and _http.http_ok("http://127.0.0.1:1/nonexistent", timeout=0.1) is False


def no_local_service():
    return m._specs.NO_LOCAL_SERVICE == {"elevenlabs"}


def get_singleton():
    """惰性单例: 同对象 + 全局 _manager 被赋值 (mock app.config.get_config)."""
    m._manager = None
    cfg = type("Cfg", (), {"raw": {"tts_services": {}}})()

    def fake_get_config():
        return cfg

    with patch("app.config.get_config", fake_get_config):
        a = m.get_gpu_service_manager()
        b = m.get_gpu_service_manager()
    return a is b and m._manager is a


check("公共 API + 私有单例命名空间存在", api_present)
check("session 放行 (非本地/不在 specs/auto_manage=False)", session_pass_through)
check("session 本地托管 → 排队+ensure+touch+释放", session_local_manage)
check("build_specs 内置+覆盖合并", build_specs_merge)
check("http_ok 不可达 → False", http_ok_status)
check("NO_LOCAL_SERVICE 逐字", no_local_service)
check("get_gpu_service_manager 惰性单例", get_singleton)

failed = 0
for name, status in results:
    print(f"  {'✓' if status == 'PASS' else '✗'} {name}: {status}")
    if status != "PASS":
        failed += 1
print(f"\n通过 {len(results) - failed}/{len(results)}")
sys.exit(1 if failed else 0)
