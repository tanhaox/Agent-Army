# 进行中-20260808-gpu_service_manager-诊断报告

**文件**: `app/services/gpu_service_manager.py`(495 行)
**日期**: 2026-08-08
**阶段**: ✅ 已完成（变更摘要见 `已完成-20260808-gpu_service_manager-架构重构.md`）

## 现状

单 GPU 串行调度器 — TTS(Fish/F5/IndexTTS2)+ ComfyUI 轮流跑,服务按需拉起 / 排队执行 / 空闲自动关停。职责:

1. **内置部署事实** — `_BUILTIN_SPECS`(57 行)4 服务配置(fish/f5/indextts/comfyui),可被 app.yaml `tts_services` 覆盖。
2. **模型定义** — `ServiceSpec`(dataclass)/ `_ServiceState`(dataclass)。
3. **服务生命周期** — `GPUServiceManager`(287 行): session 排队 → `_ensure_running` → 执行 → 释放;`_launch`/`_stop_service`/`_force_free_port`/`_kill_proc_tree` 启停;看门狗空闲自动关。
4. **HTTP/进程工具** — `_http_ok`(8)/ `_port_of`(4)/ `_pids_listening_on`(23)。
5. **模块级单例** — `_manager`/`_manager_lock`/`_build_specs`/`get_gpu_service_manager`(惰性,读 config app.yaml `tts_services`)。

**公共 API**: `get_gpu_service_manager`。类型 `GPUServiceManager`/`ServiceSpec` 供内部构造。**`_manager` 私有单例被 main.py 直接访问**(`gpu_service_manager._manager.shutdown()`),包化后必须由 `__init__.py` 命名空间持有。

## AST 测量 (物理行)

| 成员 | 行数 | 类型 |
|---|---|---|
| `GPUServiceManager` | **287** | OVER > 200 (需拆) |
| `GPUServiceManager._ensure_running` | **51** | OVER > 40 (需拆) |
| `GPUServiceManager.session` | 40 | OK (编排, 压线) |
| `GPUServiceManager._force_free_port` | 39 | OK (压线) |
| `GPUServiceManager._start_watchdog` | 20 | OK |
| `GPUServiceManager.__init__` | 18 | OK |
| `GPUServiceManager._kill_proc_tree` | 15 | OK |
| `ServiceSpec` | 12 | OK (纯数据) |
| `GPUServiceManager._stop_if_idle` | 10 | OK |
| `module._pids_listening_on` | 23 | OK |
| `module._build_specs` | 17 | OK |
| `module.get_gpu_service_manager` | 16 | OK |

**2 个超限**: 文件 495(>250)、类 287(>200)、`_ensure_running` 51(>40)。`session`(40)/`_force_free_port`(39)压线。

## 问题 (违反硬性约束)

1. **文件 495 行 > 250** — 需拆包。
2. **`GPUServiceManager` 类 287 行 > 200** — 需拆出生命周期为 mixin。
3. **`_ensure_running` 51 行 > 40** — 需拆出轮询阶段 `_await_ready`。

## 依赖与调用面

**依赖**(均不反向引用,无循环导入风险):
- `urllib`/`subprocess`/`threading`/`dataclasses` — 标准库
- `app.config.get_config` — 仅 `get_gpu_service_manager` 内 **lazy 导入**(防启动循环)

**外部引用面(7 处代码,0 处测试)**:
| 引用方 | 符号 | 说明 |
|---|---|---|
| `app/main.py:51-56` | `gpu_service_manager._manager` | **私有单例直接访问**,包化后 __init__ 命名空间必须持有 `_manager` |
| `app/routers/audio.py:16,151` | `get_gpu_service_manager` | 顶层导入 + 调用 |
| `app/routers/director_routes/retry.py:106-107` | `get_gpu_service_manager` | lazy 导入 + `.session("comfyui")` |
| `app/routers/tts_services.py:6,14,20` | `get_gpu_service_manager` | status/stop_all |
| `app/routers/voices.py:22,145,235,358` | `get_gpu_service_manager` | `.session(backend, ...)` |
| `app/services/slot_executor.py:18,152,218` | `get_gpu_service_manager` | 顶层导入 + 调用 |

无外部引用 `GPUServiceManager`/`ServiceSpec`/私有工具 — 但为公共 API 稳定性,`__init__` re-export 前两者。

## 行为契约 (逐字保持)

- **`session`**: `_NO_LOCAL_SERVICE={"elevenlabs"}` 或 backend 不在 specs → 直接 `yield` 放行;`auto_manage=False` → 直接放行;排队消息 `"GPU 排队中 (前面还有任务)…"`;finally 里 `idle_timeout_sec<=0` → `_stop_if_idle(force=True)` 否则 `_start_watchdog()`。
- **`_ensure_running`**: 健康 → 外部启动复用日志 `"[gpu_svc] %s 已由外部启动, 直接复用"`;僵死先杀;腾显存遍历其他服务 `f"正在关闭 {name} 以腾出显存…"`;强杀端口;启动消息 `f"正在启动 {name} 服务 (首次加载模型约 1-2 分钟)…"`;就绪消息 `f"{name} 服务就绪"` + 日志 `"[gpu_svc] %s ready at %s"`;失败 `RuntimeError(f"{name} 进程启动即退出 (exit={code}), 日志: logs/gpu_svc_{key}.log")`;超时 `TimeoutError(f"{name} 启动超时 ({timeout:.0f}s), 日志: logs/gpu_svc_{key}.log")`。
- **`_force_free_port` 端口保护**: 54321/7861/8188 永不强杀(返回);5 轮 `taskkill /PID <pid> /T /F`;日志 `"[gpu_svc] port %s still held by PID %s after kill, force taskkill"` / `"[gpu_svc] port %s STILL occupied after force kill"`。
- **`_launch`**: LOG_DIR `gpu_svc_{key}.log` append;env 合并 + `PYTHONIOENCODING=utf-8`;相对 exe 基于 spec.cwd 解析;Windows `CREATE_NEW_PROCESS_GROUP|CREATE_NO_WINDOW`。
- **`_build_specs`**: `{**builtin, **override}` 合并;`cwd=Path(...)`/`command=list(...)`/`env=dict(...)`。
- **`get_gpu_service_manager`**: 惰性单例;`idle_timeout_sec=float(svc_cfg.get(..., 300))`/`startup_timeout_sec`/`auto_manage=bool(svc_cfg.get(..., True))`。
- **看门狗**: 15s 轮询;全停且 `_waiting==0` 线程退出;`"gpu-svc-watchdog"` daemon。

## 拆分方案 (5 模块, 全部 ≤250 行, 3 类上限内)

| 新模块 | 职责 | 迁入内容 | 预估行数 |
|---|---|---|---|
| `__init__.py` | 模块级单例(`_manager`/`_manager_lock`/`get_gpu_service_manager`)+ re-export + `__all__` | 单例逻辑 + `GPUServiceManager`/`ServiceSpec` re-export | ~55 |
| `_specs.py` | 部署事实 + 模型 + 构建 | `_BUILTIN_SPECS` / `ServiceSpec` / `_NO_LOCAL_SERVICE` / `_build_specs` | ~110 |
| `_http.py` | HTTP/端口进程工具 | `_http_ok` / `_port_of` / `_pids_listening_on` | ~45 |
| `_lifecycle.py` | 服务启停 + 看门狗 mixin | `_ServiceLifecycleMixin`: `_ensure_running`(拆 `_await_ready`)/ `_launch` / `_stop_service` / `_force_free_port` / `_kill_proc_tree` / `_stop_if_idle` / `_start_watchdog` | ~190 |
| `_manager.py` | 主类(对外 API) | `GPUServiceManager(_ServiceLifecycleMixin)`: `__init__` / `session` / `status` / `stop_all` / `shutdown` / `_touch` | ~110 |

**类数**: `ServiceSpec`/`_ServiceState` 为纯数据类(dataclass,不计入),普通类 = `_ServiceLifecycleMixin` + `GPUServiceManager` = **2 ≤ 3** ✅。

**拆类方式**: 生命周期方法移入 `_ServiceLifecycleMixin`(行为零改动,仍 `self.xxx`),主类瘦身为对外 API + 状态持有。`_ensure_running` 51 行拆出 `_await_ready` 轮询段(两个函数各 ≤40)。`session`(40)/`_force_free_port`(39)压线,以 `--orch` 声明。

**关键点**: `_manager` 单例定义在 `__init__.py` 命名空间 — main.py `gpu_service_manager._manager` 才拿到同一个全局;`get_gpu_service_manager` 内 `global _manager` 同步更新。

## 下一步

拆分执行 → AST 硬约束 → 行为契约断言 → 原文件 send2trash → 变更摘要文档 → 更新本报告为 ✅ 已完成。
