"""gpu_service_manager 新旧逐字 diff — 相同输入下比较输出字节级一致.

用法: cd F:/AI-Agent-Local/digital_human && PYTHONIOENCODING=utf-8 PYTHONPATH=F:/AI-Agent-Local/digital_human \
      .venv/Scripts/python.exe scripts/_diff_gpu_service_manager.py
"""
import importlib.util
import inspect
import pathlib
import sys
from unittest.mock import patch

sys.path.insert(0, ".")

OLD = pathlib.Path("app/services/gpu_service_manager.py")


def load_old(name):
    spec = importlib.util.spec_from_file_location(name, OLD)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


old = load_old("old_gpu_service_manager")
import app.services.gpu_service_manager as new  # noqa: E402

checks = []


def eq(name, old_val, new_val):
    same = old_val == new_val
    checks.append((name, same, old_val, new_val))


# 1. 公共 API 覆盖 — 新包 __all__ 覆盖旧模块对外函数/类
OLD_PUBLIC = {"get_gpu_service_manager", "GPUServiceManager", "ServiceSpec"}
eq("public API names", True, set(new.__all__) >= OLD_PUBLIC)

# 2. 签名逐字
old_cls = old.GPUServiceManager
new_cls = new.GPUServiceManager
for name in ("__init__", "session", "status", "stop_all", "shutdown",
             "_ensure_running", "_launch", "_stop_service", "_stop_if_idle"):
    eq(f"GPUServiceManager.{name} sig",
       inspect.signature(getattr(old_cls, name)),
       inspect.signature(getattr(new_cls, name)))
eq("get_gpu_service_manager sig",
   inspect.signature(old.get_gpu_service_manager),
   inspect.signature(new.get_gpu_service_manager))

# 3. ServiceSpec dataclass 字段 + health_url 逐字
old_spec = old.ServiceSpec("k", "n", "http://127.0.0.1:1", "/health", pathlib.Path("."), [], {})
new_spec = new.ServiceSpec("k", "n", "http://127.0.0.1:1", "/health", pathlib.Path("."), [], {})
eq("ServiceSpec fields", [f for f in old.ServiceSpec.__dataclass_fields__],
   [f for f in new.ServiceSpec.__dataclass_fields__])
eq("ServiceSpec.health_url", old_spec.health_url, new_spec.health_url)

# 4. 内置部署事实逐字 (SpecSpec 表)
def run_builds(fn, raw):
    specs, svc_cfg = fn(raw)
    out = {}
    for k, s in specs.items():
        out[k] = (s.display_name, s.base_url, s.health_path, str(s.cwd),
                  s.command, s.env)
    return svc_cfg, out


RAW = {"tts_services": {}}
eq("build_specs 内置表", run_builds(old._build_specs, dict(RAW)), run_builds(new._specs.build_specs, dict(RAW)))

# 5. build_specs override 合并
RAW2 = {"tts_services": {"fish": {"base_url": "http://127.0.0.1:9999", "env": {"X": "1"}}}}
eq("build_specs override", run_builds(old._build_specs, dict(RAW2)), run_builds(new._specs.build_specs, dict(RAW2)))

# 6. _NO_LOCAL_SERVICE / NO_LOCAL_SERVICE 逐字
eq("NO_LOCAL_SERVICE", old._NO_LOCAL_SERVICE, new._specs.NO_LOCAL_SERVICE)

# 7. session 放行路径 — 非本地/不在 specs/auto_manage=False
def run_session_pt(fn, specs, auto, backend):
    mgr = fn(specs=specs, idle_timeout_sec=300, auto_manage=auto)
    entered = []
    with mgr.session(backend):
        entered.append(True)
    return entered


eq("session 放行 elevenlabs", run_session_pt(old.GPUServiceManager, {}, True, "elevenlabs"),
   run_session_pt(new_cls, {}, True, "elevenlabs"))
eq("session 放行 不在specs", run_session_pt(old.GPUServiceManager, {}, True, "nope"),
   run_session_pt(new_cls, {}, True, "nope"))
eq("session 放行 auto_manage=False", run_session_pt(old.GPUServiceManager, {}, False, "fish"),
   run_session_pt(new_cls, {}, False, "fish"))

# 8. _force_free_port 端口保护 (mock 工具, 不真杀)
def force_result(fn_cls):
    spec = type("S", (), {"base_url": "http://127.0.0.1:54321"})()
    out = []
    with patch("app.services.gpu_service_manager._http.pids_listening_on", return_value=[123]) as pl, \
         patch("app.services.gpu_service_manager._http.port_of", return_value=54321):
        fn_cls._force_free_port(spec)
        out.append(pl.call_count)
    return out


eq("_force_free_port 保护端口不杀", force_result(old.GPUServiceManager), force_result(new_cls))

# 9. status 结构 (mock http_ok False, 不真探测)
# 注意: 不能用 `import pkg._manager as nm` — __init__.py 的全局单例 `_manager=None`
# 遮蔽了同名子模块 (import a.b as c 绑定的是 a.b 属性查找结果). 用 importlib 取真模块.
import importlib
new_manager_mod = importlib.import_module("app.services.gpu_service_manager._manager")


def run_status(mgr, module, attr):
    orig = getattr(module, attr)
    setattr(module, attr, lambda *a, **k: False)
    try:
        return mgr.status()
    finally:
        setattr(module, attr, orig)


eq("status 结构",
   run_status(old.GPUServiceManager({}), old, "_http_ok"),
   run_status(new_cls({}), new_manager_mod, "http_ok"))

# 10. _kill_proc_tree 已完成进程 → no-op
proc = type("P", (), {"poll": lambda self: 0})()
eq("kill 已退出进程 no-op",
   old.GPUServiceManager._kill_proc_tree(proc, old.ServiceSpec("k", "n", "u", "/", pathlib.Path("."), [], {})),
   new_cls._kill_proc_tree(proc, new.ServiceSpec("k", "n", "u", "/", pathlib.Path("."), [], {})))

fails = [c for c in checks if not c[1]]
for name, same, o, n in checks:
    print(f"  {'✓' if same else '✗'} {name}")
    if not same:
        print(f"      old: {o!r}\n      new: {n!r}")
print(f"\n通过 {len(checks) - len(fails)}/{len(checks)}")
sys.exit(1 if fails else 0)
