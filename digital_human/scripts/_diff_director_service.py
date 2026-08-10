"""director_service 新旧逐字 diff — 相同输入下比较输出字节级一致.

用法: cd F:/AI-Agent-Local/digital_human && PYTHONIOENCODING=utf-8 PYTHONPATH=F:/AI-Agent-Local/digital_human \
      .venv/Scripts/python.exe scripts/_diff_director_service.py
"""
import importlib.util
import pathlib
import sys

sys.path.insert(0, ".")

OLD = pathlib.Path("app/services/director_service.py")


def load_old(name):
    spec = importlib.util.spec_from_file_location(name, OLD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


old = load_old("old_director_service")
import app.services.director_service as new  # noqa: E402

checks = []


def eq(name, old_val, new_val):
    same = old_val == new_val
    checks.append((name, same, old_val, new_val))


# 1. 公共 API 集合 — 新包 __all__ 必须覆盖旧模块的外部公共函数
#    (旧模块把导入名也暴露为模块属性, 新包用 __all__ 干净导出, 属改进非回归)
OLD_PUBLIC = {"create_director_plan", "replace_failed_slot", "mark_job_reviewed",
              "complete_job_if_slots_done", "append_trace", "get_trace"}
eq("public API names", True, set(new.__all__) >= OLD_PUBLIC)

# 2. create_director_plan 签名
import inspect
eq("create sig", inspect.signature(old.create_director_plan), inspect.signature(new.create_director_plan))
eq("replace sig", inspect.signature(old.replace_failed_slot), inspect.signature(new.replace_failed_slot))
eq("mark sig", inspect.signature(old.mark_job_reviewed), inspect.signature(new.mark_job_reviewed))
eq("complete sig", inspect.signature(old.complete_job_if_slots_done), inspect.signature(new.complete_job_if_slots_done))
eq("append_trace sig", inspect.signature(old.append_trace), inspect.signature(new.append_trace))
eq("get_trace sig", inspect.signature(old.get_trace), inspect.signature(new.get_trace))

# 3. 异常消息逐字 (DB 失败路径)
class BoomSession:
    def __init__(self):
        self.added = []

    def get(self, model, pk):
        raise RuntimeError("boom")

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def add(self, obj):
        self.added.append(obj)


for fn_name in ("mark_job_reviewed", "complete_job_if_slots_done"):
    old_fn, new_fn = getattr(old, fn_name), getattr(new, fn_name)
    errs = []
    for fn in (old_fn, new_fn):
        try:
            fn(BoomSession(), "nope")
            errs.append(None)
        except Exception as e:
            errs.append(f"{type(e).__name__}: {e}")
    eq(f"{fn_name} not-found error", errs[0], errs[1])

# 4. append_trace 结构逐字
def run_trace(fn):
    job = type("Job", (), {"plan_json": {"trace": []}})()
    db = type("DB", (), {"commit": lambda self: None})()
    fn(db, job, "plan", "done", "规划完成, 5 slots 进入 reviewing")
    t = job.plan_json["trace"]
    return (len(t), t[0]["step"], t[0]["status"], t[0]["detail"],
            sorted(t[0].keys()), len(t[0]["ts"]) == 20)


eq("append_trace 输出", run_trace(old.append_trace), run_trace(new.append_trace))

# 5. get_trace 空
eq("get_trace empty", old.get_trace(BoomSession(), type("Job", (), {"plan_json": None})()),
   new.get_trace(BoomSession(), type("Job", (), {"plan_json": None})()))

# 6. complete_job_if_slots_done 全完成
def run_complete(fn):
    job = type("Job", (), {"status": "planning", "slots": [
        type("S", (), {"status": "completed"}), type("S", (), {"status": "replaced"})]})()
    db = type("DB", (), {"get": lambda self, m, pk: job,
                         "commit": lambda self: None, "refresh": lambda self, o: None})()
    fn(db, "j1")
    return job.status, getattr(job, "completed_at", None) is not None


eq("complete all done", run_complete(old.complete_job_if_slots_done),
   run_complete(new.complete_job_if_slots_done))

# 7. replace_failed_slot 无管线链逐字
def run_replace(fn):
    slot = type("S", (), {"workflow": "host", "status": "queued", "error_code": None,
                          "error_message": None, "director_job_id": "j1", "slot_index": 2,
                          "start_sec": 1.0, "end_sec": 2.0, "duration_sec": 1.0,
                          "text_context": "t", "segment_id": "s1", "visual_type": "host",
                          "params_json": {"k": "v"}, "id": "sl1"})()
    out = fn(BoomSession(), slot)
    return (out is slot, slot.status, slot.error_code, slot.error_message)


eq("replace_failed_slot no pipeline", run_replace(old.replace_failed_slot),
   run_replace(new.replace_failed_slot))

# 8. enabled_pipelines 动态链逐字
def run_replace_pl(fn):
    slot = type("S", (), {"workflow": "broll_pexels", "status": "queued", "error_code": None,
                          "error_message": None, "director_job_id": "j1", "slot_index": 2,
                          "start_sec": 1.0, "end_sec": 2.0, "duration_sec": 1.0,
                          "text_context": "t", "segment_id": "s1", "visual_type": "broll_pexels",
                          "params_json": {"k": "v"}, "id": "sl1"})()
    out = fn(BoomSession(), slot, enabled_pipelines={"c", "p"})
    return (out is slot, slot.status, out.workflow if out is not slot else None)


eq("replace_failed_slot pipelines", run_replace_pl(old.replace_failed_slot),
   run_replace_pl(new.replace_failed_slot))

fails = [c for c in checks if not c[1]]
for name, same, o, n in checks:
    print(f"  {'✓' if same else '✗'} {name}")
    if not same:
        print(f"      old: {o!r}\n      new: {n!r}")
print(f"\n通过 {len(checks) - len(fails)}/{len(checks)}")
sys.exit(1 if fails else 0)
