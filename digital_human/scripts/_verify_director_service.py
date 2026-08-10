"""director_service 重构行为契约验证 (8 项断言).

用法: cd F:/AI-Agent-Local/digital_human && PYTHONIOENCODING=utf-8 PYTHONPATH=F:/AI-Agent-Local/digital_human \
      .venv/Scripts/python.exe scripts/_verify_director_service.py
"""
import sys

from sqlalchemy.orm import Session

from app.services import director_service as ds


class NoneSession:
    """mock DB session — get 返回 None (not-found 路径)."""

    def get(self, model, pk):
        return None

    def commit(self):
        pass

    def refresh(self, obj):
        pass


class JobSession:
    """mock DB session — get 返回预设 job (有值路径)."""

    def __init__(self, job):
        self.job = job

    def get(self, model, pk):
        return self.job

    def commit(self):
        pass

    def refresh(self, obj):
        pass


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
    return all(hasattr(ds, n) for n in [
        "create_director_plan", "replace_failed_slot", "append_trace",
        "get_trace", "mark_job_reviewed", "complete_job_if_slots_done",
    ])


def create_sig():
    import inspect
    sig = inspect.signature(ds.create_director_plan)
    params = list(sig.parameters)
    return params == ["db", "script_id", "audio_file_id", "job_id",
                      "material_catalog", "language", "is_cancelled", "enabled_pipelines"] and \
        sig.parameters["material_catalog"].kind == inspect.Parameter.KEYWORD_ONLY


def replace_sig():
    import inspect
    sig = inspect.signature(ds.replace_failed_slot)
    return list(sig.parameters) == ["db", "slot", "fallback_chain", "enabled_pipelines"]


def mark_missing():
    try:
        ds.mark_job_reviewed(NoneSession(), "nope")
        return False
    except ValueError as e:
        return str(e) == "DirectorJob nope not found"


def mark_missing_lc():
    try:
        ds.complete_job_if_slots_done(NoneSession(), "nope")
        return False
    except ValueError as e:
        return str(e) == "DirectorJob nope not found"


def trace_shape():
    db = NoneSession()
    job = type("Job", (), {"plan_json": {"trace": []}})()
    ds.append_trace(db, job, "alignment", "done", "对齐完成 12.0s / 3 段")
    t = job.plan_json["trace"]
    return len(t) == 1 and t[0]["step"] == "alignment" and t[0]["status"] == "done" \
        and set(t[0]) == {"n", "ts", "step", "status", "detail"}


def get_trace_empty():
    job = type("Job", (), {"plan_json": None})()
    return ds.get_trace(NoneSession(), job) == []


def complete_all_done():
    job = type("Job", (), {
        "status": "planning",
        "slots": [type("S", (), {"status": "completed"})(),
                  type("S", (), {"status": "replaced"})()],
    })()
    db = JobSession(job)
    job2 = ds.complete_job_if_slots_done(db, job)
    return job2.status == "completed"


check("6 公共 API 存在", api_present)
check("create_director_plan 签名逐字", create_sig)
check("replace_failed_slot 签名逐字", replace_sig)
check("mark_job_reviewed 缺失→ValueError 消息逐字", mark_missing)
check("complete_job_if_slots_done 缺失→ValueError 逐字", mark_missing_lc)
check("append_trace 结构", trace_shape)
check("get_trace 空", get_trace_empty)
check("complete_job_if_slots_done 全完成→completed", complete_all_done)

failed = 0
for name, status in results:
    print(f"  {'✓' if status == 'PASS' else '✗'} {name}: {status}")
    if status != "PASS":
        failed += 1
print(f"\n通过 {len(results) - failed}/{len(results)}")
sys.exit(1 if failed else 0)
