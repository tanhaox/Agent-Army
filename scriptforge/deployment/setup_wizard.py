# -*- coding: utf-8 -*-
"""
ScriptForge 安装向导 v1.0
5 步向导：环境预检 -> 配置检查 -> 加载镜像 -> 构建启动 -> 完成
"""

import subprocess
import threading
import logging
import os
import sys
import shutil
import webbrowser
import re
import json
import tarfile
import time
import tkinter as tk
import tkinter.filedialog
from tkinter import font as tkfont

logger = logging.getLogger("setup_wizard")

# ── 常量 ──────────────────────────────────────────────────

VERSION = "v1.0"
WIN_W, WIN_H = 660, 580

C_BG      = "#0A0A0A"
C_CARD    = "#1A1A1A"
C_HOVER   = "#242424"
C_BORDER  = "#2A2A2A"
C_TEXT    = "#ECECEC"
C_SEC     = "#888888"
C_MUTED   = "#555555"
C_BRAND   = "#6366F1"
C_BRAND_HV= "#818CF8"
C_SUCCESS = "#10B981"
C_ERROR   = "#EF4444"
C_WARN    = "#F59E0B"

FONT = "微软雅黑"
FONT_MONO = "Consolas"

STEPS = ["环境预检", "安装配置", "加载镜像", "构建启动", "完成"]

# 项目根目录：exe 所在目录的上一级，或脚本所在目录的上一级
def _project_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_ROOT = _project_root()


# ── 主向导 ────────────────────────────────────────────────

class SetupWizard:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"ScriptForge 安装向导 {VERSION}")
        self.root.geometry(f"{WIN_W}x{WIN_H}")
        self.root.resizable(False, False)
        self.root.configure(bg=C_BG)
        self._center()

        self.current_step = 0
        self.check_results = {}
        self.log_lines = []
        self._lock = threading.Lock()
        self._src_root = PROJECT_ROOT      # original location (where tar lives)
        self.install_path = r"C:\ScriptForge"  # default install path, user can change

        self._build_ui()
        self.root.after(300, lambda: self._go_step(0))

    # ── helpers ──

    def _center(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - WIN_W) // 2
        y = (self.root.winfo_screenheight() - WIN_H) // 2
        self.root.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")

    def _f(self, size=10, bold=False):
        return (FONT, size, "bold" if bold else "normal")

    # ── build skeleton ──

    def _build_ui(self):
        # header
        hdr = tk.Frame(self.root, bg=C_BG)
        hdr.pack(fill="x", padx=30, pady=(18, 0))
        self.hdr_title = tk.Label(hdr, text="ScriptForge 安装向导",
                                  font=self._f(16, True), fg=C_TEXT, bg=C_BG)
        self.hdr_title.pack(anchor="w")
        self.hdr_sub = tk.Label(hdr, text="", font=self._f(9), fg=C_SEC, bg=C_BG)
        self.hdr_sub.pack(anchor="w", pady=(2, 0))

        # step indicator
        self.step_frame = tk.Frame(self.root, bg=C_BG)
        self.step_frame.pack(fill="x", padx=30, pady=(12, 0))
        self.step_widgets = []
        for i, name in enumerate(STEPS):
            f = tk.Frame(self.step_frame, bg=C_BG)
            f.pack(side="left")
            circ = tk.Label(f, text=str(i+1), font=self._f(10, True),
                            fg=C_MUTED, bg=C_HOVER, width=2, height=1)
            circ.pack(side="left")
            lbl = tk.Label(f, text=name, font=self._f(9), fg=C_MUTED, bg=C_BG)
            lbl.pack(side="left", padx=(4, 0))
            # connector line (except last)
            if i < len(STEPS) - 1:
                line = tk.Label(self.step_frame, text=" ── ", font=self._f(9),
                                fg=C_BORDER, bg=C_BG)
                line.pack(side="left", padx=2)
            else:
                line = None
            self.step_widgets.append({"circ": circ, "lbl": lbl, "line": line})

        # separator
        tk.Frame(self.root, bg=C_BORDER, height=1).pack(fill="x", padx=30, pady=(10, 0))

        # content area
        self.content = tk.Frame(self.root, bg=C_BG)
        self.content.pack(fill="both", expand=True, padx=30, pady=10)

        # bottom buttons
        bot = tk.Frame(self.root, bg=C_BG)
        bot.pack(fill="x", padx=30, pady=(0, 16))

        self.btn_back = tk.Button(bot, text="上一步", font=self._f(10),
                                  bg=C_HOVER, fg=C_SEC, relief="flat",
                                  padx=14, pady=5, cursor="hand2",
                                  command=self._go_back, state="disabled")
        self.btn_back.pack(side="left")

        self.btn_next = tk.Button(bot, text="下一步", font=self._f(10),
                                  bg=C_BRAND, fg="white", relief="flat",
                                  padx=14, pady=5, cursor="hand2",
                                  command=self._go_next, state="disabled")
        self.btn_next.pack(side="right")

        self.btn_cancel = tk.Button(bot, text="取消", font=self._f(10),
                                    bg=C_HOVER, fg=C_SEC, relief="flat",
                                    padx=14, pady=5, cursor="hand2",
                                    command=self.root.quit)
        self.btn_cancel.pack(side="right", padx=(0, 8))

    # ── step indicator update ──

    def _update_step_indicator(self, step):
        for i, w in enumerate(self.step_widgets):
            if i < step:
                w["circ"].configure(text="✓", fg=C_SUCCESS, bg="#0D2818")
                w["lbl"].configure(fg=C_SUCCESS)
            elif i == step:
                w["circ"].configure(text=str(i+1), fg="white", bg=C_BRAND)
                w["lbl"].configure(fg=C_TEXT)
            else:
                w["circ"].configure(text=str(i+1), fg=C_MUTED, bg=C_HOVER)
                w["lbl"].configure(fg=C_MUTED)

    # ── clear content ──

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ── navigation ──

    def _go_step(self, step):
        self.current_step = step
        self._update_step_indicator(step)
        self._clear_content()
        self.hdr_sub.configure(text=f"步骤 {step+1}/5：{STEPS[step]}")
        self.btn_back.configure(state="normal" if step > 0 else "disabled")
        self.btn_next.configure(state="disabled")

        [self._render_step0, self._render_step1, self._render_step2,
         self._render_step3, self._render_step4][step]()

    def _go_next(self):
        if self.current_step < 4:
            self._go_step(self.current_step + 1)

    def _go_back(self):
        if self.current_step > 0:
            self._go_step(self.current_step - 1)

    # ── log helper ──

    def _create_log(self, parent):
        lf = tk.Frame(parent, bg="#111111", bd=1, relief="solid")
        lf.pack(fill="both", expand=True, pady=(8, 0))
        log = tk.Text(lf, bg="#111111", fg=C_SEC, font=(FONT_MONO, 9),
                      wrap="word", state="disabled", height=10, bd=0,
                      insertbackground=C_TEXT, selectbackground=C_BRAND)
        sb = tk.Scrollbar(lf, command=log.yview)
        log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        log.pack(fill="both", expand=True, padx=4, pady=4)
        return log

    def _append_log(self, log_widget, text, color=None):
        def _do():
            log_widget.configure(state="normal")
            if color:
                tag = f"c_{color.replace('#','')}"
                log_widget.tag_configure(tag, foreground=color)
                log_widget.insert("end", text + "\n", tag)
            else:
                log_widget.insert("end", text + "\n")
            log_widget.see("end")
            log_widget.configure(state="disabled")
        self.root.after(0, _do)

    # ── progress bar helper ──

    def _create_progress(self, parent, total_steps=4):
        """Create a dark-themed progress bar. Returns (frame, update_fn)."""
        bar_h = 22
        pf = tk.Frame(parent, bg=C_BG)
        pf.pack(fill="x", pady=(6, 0))

        self._pb_canvas = tk.Canvas(pf, height=bar_h, bg="#111111",
                                    highlightthickness=1, highlightbackground=C_BORDER)
        self._pb_canvas.pack(fill="x")
        self._pb_total = total_steps
        self._pb_done = 0
        self._pb_bar_h = bar_h

        self._pb_label = tk.Label(pf, text=f"0/{total_steps} 个镜像", font=self._f(9),
                                  fg=C_MUTED, bg=C_BG)
        self._pb_label.pack(anchor="w", pady=(3, 0))

        # draw empty bar
        self._draw_progress()

        return pf

    def _draw_progress(self):
        c = self._pb_canvas
        c.delete("all")
        w = c.winfo_width() or 500
        h = self._pb_bar_h
        if self._pb_total <= 0:
            return
        ratio = self._pb_done / self._pb_total
        fill_w = int(w * ratio)

        # background
        c.create_rectangle(0, 0, w, h, fill="#111111", outline="")
        # filled portion
        if fill_w > 0:
            color = C_SUCCESS if self._pb_done >= self._pb_total else C_BRAND
            c.create_rectangle(0, 0, fill_w, h, fill=color, outline="")
        # percentage text
        pct = f"{int(ratio * 100)}%"
        c.create_text(w // 2, h // 2, text=pct, fill=C_TEXT, font=(FONT_MONO, 9, "bold"))

    def _tick_progress(self, loaded_name=""):
        self._pb_done += 1
        # Don't overwrite canvas while marquee is animating
        if not getattr(self, '_marquee_running', False):
            self._draw_progress()
        if loaded_name:
            self._pb_label.configure(
                text=f"已加载 {self._pb_done}/{self._pb_total}  -  {loaded_name}",
                fg=C_SUCCESS if self._pb_done >= self._pb_total else C_TEXT)
        else:
            self._pb_label.configure(text=f"{self._pb_done}/{self._pb_total}")

    # ── marquee animation ──

    def _start_marquee(self):
        """Start a marquee-style animation on the progress bar canvas."""
        self._marquee_running = True
        self._marquee_pos = 0
        self._marquee_dir = 1
        self._animate_marquee()

    def _animate_marquee(self):
        if not getattr(self, '_marquee_running', False):
            return
        c = self._pb_canvas
        c.delete("all")
        w = c.winfo_width() or 500
        h = self._pb_bar_h

        # background
        c.create_rectangle(0, 0, w, h, fill="#111111", outline="")
        # moving block
        block_w = 100
        x = self._marquee_pos
        c.create_rectangle(x, 2, x + block_w, h - 2, fill=C_BRAND, outline="")
        # text
        c.create_text(w // 2, h // 2, text="加载中...",
                      fill=C_TEXT, font=(FONT_MONO, 9, "bold"))
        # move
        self._marquee_pos += 4 * self._marquee_dir
        if self._marquee_pos + block_w >= w:
            self._marquee_dir = -1
        elif self._marquee_pos <= 0:
            self._marquee_dir = 1
        self.root.after(30, self._animate_marquee)

    def _stop_marquee(self):
        self._marquee_running = False

    # ── tar image count ──

    def _count_images_in_tar(self, tar_path):
        """Count images in a docker save tar via manifest.json."""
        try:
            with tarfile.open(tar_path, 'r') as tf:
                member = tf.getmember('manifest.json')
                f = tf.extractfile(member)
                manifest = json.load(f)
                return len(manifest)
        except Exception:
            return 4  # fallback

    # ── run command helper ──

    def _run_cmd(self, cmd, log_widget, on_done, cwd=None, on_line=None):
        """Run a command in a thread, stream output to log_widget.

        Uses binary mode + manual decode to avoid UnicodeDecodeError killing
        the reader thread (which would cause a pipe-buffer deadlock).
        """
        def reader_thread(proc):
            buf = b""
            while True:
                try:
                    chunk = proc.stdout.read(512)
                except Exception:
                    break
                if not chunk:
                    break
                buf += chunk
                # decode with error replacement
                text = buf.decode("utf-8", errors="replace")
                # split on \n or \r
                while "\n" in text or "\r" in text:
                    nl = text.find("\n")
                    cr = text.find("\r")
                    if nl < 0: nl = len(text) + 1
                    if cr < 0: cr = len(text) + 1
                    pos = min(nl, cr)
                    line = text[:pos].strip()
                    text = text[pos + 1:]
                    if line:
                        self._append_log(log_widget, line)
                        if on_line:
                            try:
                                on_line(line)
                            except Exception:
                                pass
                # keep unprocessed bytes (incomplete multi-byte seq)
                buf = text.encode("utf-8", errors="replace")
            # flush remaining
            if buf:
                remaining = buf.decode("utf-8", errors="replace").strip()
                if remaining:
                    self._append_log(log_widget, remaining)

        def worker():
            rc = -1
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=False, cwd=cwd or self.install_path,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                rt = threading.Thread(target=reader_thread, args=(proc,), daemon=True)
                rt.start()
                proc.wait()
                rt.join(timeout=5)
                rc = proc.returncode
            except Exception as e:
                self._append_log(log_widget, f"command error: {e}", C_ERROR)
            self.root.after(0, lambda: on_done(rc))
        threading.Thread(target=worker, daemon=True).start()

    def _heartbeat(self, log, label):
        """Periodically log elapsed time to show the process is alive."""
        self._heartbeat_stop = False
        self._heartbeat_start = time.time()
        def tick():
            if getattr(self, '_heartbeat_stop', True):
                return
            elapsed = int(time.time() - self._heartbeat_start)
            m, s = divmod(elapsed, 60)
            self._append_log(log, f"  {label}（已用时 {m}:{s:02d}）", C_MUTED)
            self.root.after(5000, tick)
        self.root.after(5000, tick)

    # ════════════════════════════════════════════════════════
    #  STEP 0 : 环境预检
    # ════════════════════════════════════════════════════════

    def _render_step0(self):
        self.check_results = {}
        f = self.content

        tk.Label(f, text="正在检测系统环境...", font=self._f(11),
                 fg=C_TEXT, bg=C_BG).pack(anchor="w", pady=(4, 8))

        checks = [
            ("docker", "Docker Desktop", ["docker", "--version"]),
            ("nvidia", "NVIDIA 显卡驱动", ["nvidia-smi"]),
            ("toolkit", "NVIDIA Container Toolkit",
             ["docker", "run", "--rm", "--gpus", "all",
              "nvidia/cuda:12.4.0-runtime-ubuntu22.04", "nvidia-smi"]),
        ]

        self.s0_cards = {}
        for cid, name, cmd in checks:
            card = tk.Frame(f, bg=C_CARD, highlightbackground=C_BORDER,
                            highlightthickness=1, padx=14, pady=10)
            card.pack(fill="x", pady=3)

            icon = tk.Label(card, text="◎", font=self._f(14), fg=C_BRAND,
                            bg=C_CARD, width=2)
            icon.pack(side="left")

            info = tk.Frame(card, bg=C_CARD)
            info.pack(side="left", fill="x", expand=True, padx=(8, 0))

            nm = tk.Label(info, text=name, font=self._f(10, True),
                          fg=C_TEXT, bg=C_CARD)
            nm.pack(anchor="w")

            st = tk.Label(info, text="正在检测...", font=self._f(9),
                          fg=C_BRAND, bg=C_CARD)
            st.pack(anchor="w")

            self.s0_cards[cid] = {"frame": card, "icon": icon, "name": nm, "status": st,
                                  "cmd": cmd, "optional": cid != "docker"}

        self.root.after(200, self._run_env_checks)

    def _run_env_checks(self):
        def worker():
            for cid, card_info in self.s0_cards.items():
                self.root.after(0, lambda c=cid: self._update_env_card(c, "checking"))
                try:
                    r = subprocess.run(
                        card_info["cmd"], capture_output=True, text=True, timeout=120,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    )
                    passed = r.returncode == 0
                    detail = ""
                    if cid == "docker" and passed:
                        detail = (r.stdout or "").strip()[:40]
                    elif cid == "nvidia" and passed:
                        for ln in (r.stdout or "").split("\n"):
                            if "NVIDIA-SMI" in ln:
                                detail = ln.strip()[:40]; break
                    self.check_results[cid] = passed
                    self.root.after(0, lambda c=cid, p=passed, d=detail:
                                    self._update_env_card(c, "pass" if p else "fail", d))
                except FileNotFoundError:
                    self.check_results[cid] = False
                    self.root.after(0, lambda c=cid: self._update_env_card(c, "fail", "未安装"))
                except subprocess.TimeoutExpired:
                    self.check_results[cid] = False
                    self.root.after(0, lambda c=cid: self._update_env_card(c, "fail", "检测超时"))
                except Exception as e:
                    self.check_results[cid] = False
                    self.root.after(0, lambda c=cid: self._update_env_card(c, "fail", str(e)[:40]))

            self.root.after(0, self._env_check_done)
        threading.Thread(target=worker, daemon=True).start()

    def _update_env_card(self, cid, state, detail=""):
        c = self.s0_cards[cid]
        if state == "checking":
            c["frame"].configure(bg="#0A0A2D", highlightbackground=C_BRAND)
            c["icon"].configure(text="◎", fg=C_BRAND, bg="#0A0A2D")
            c["name"].configure(bg="#0A0A2D")
            c["status"].configure(text="正在检测...", fg=C_BRAND, bg="#0A0A2D")
        elif state == "pass":
            c["frame"].configure(bg="#0D2818", highlightbackground=C_SUCCESS)
            c["icon"].configure(text="✓", fg=C_SUCCESS, bg="#0D2818")
            c["name"].configure(bg="#0D2818")
            c["status"].configure(text="已就绪" + (f"  {detail}" if detail else ""),
                                  fg=C_SUCCESS, bg="#0D2818")
        elif state == "fail":
            optional = c["optional"]
            if optional:
                c["frame"].configure(bg="#2D2A0A", highlightbackground=C_WARN)
                c["icon"].configure(text="!", fg=C_WARN, bg="#2D2A0A")
                c["name"].configure(bg="#2D2A0A")
                c["status"].configure(text=detail or "未安装（可选）",
                                      fg=C_WARN, bg="#2D2A0A")
            else:
                c["frame"].configure(bg="#2D0A0A", highlightbackground=C_ERROR)
                c["icon"].configure(text="✗", fg=C_ERROR, bg="#2D0A0A")
                c["name"].configure(bg="#2D0A0A")
                c["status"].configure(text=detail or "未安装（必需）",
                                      fg=C_ERROR, bg="#2D0A0A")

    def _env_check_done(self):
        docker_ok = self.check_results.get("docker", False)
        if docker_ok:
            self.btn_next.configure(state="normal")
            self.hdr_sub.configure(text="步骤 1/5: 环境预检 - 通过! 点击下一步继续")
        else:
            self.hdr_sub.configure(text="步骤 1/5: 环境预检 - Docker 未就绪, 请先安装 Docker Desktop")

    # ════════════════════════════════════════════════════════
    #  STEP 1 : 配置检查
    # ════════════════════════════════════════════════════════

    def _render_step1(self):
        f = self.content
        env_path = os.path.join(self.install_path, "backend", ".env")
        example_path = os.path.join(self.install_path, "deployment", ".env.example")

        # ── 安装路径选择 ──
        tk.Label(f, text="安装位置", font=self._f(11),
                 fg=C_TEXT, bg=C_BG).pack(anchor="w", pady=(4, 4))

        path_frame = tk.Frame(f, bg=C_BG)
        path_frame.pack(fill="x", pady=(0, 4))

        self.s1_path_entry = tk.Entry(path_frame, font=(FONT_MONO, 10),
                                      bg="#111111", fg=C_TEXT,
                                      insertbackground=C_TEXT,
                                      relief="solid", bd=1)
        self.s1_path_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.s1_path_entry.insert(0, self.install_path)

        tk.Button(path_frame, text="浏览", font=self._f(9),
                  bg=C_BRAND, fg="white", relief="flat",
                  padx=10, pady=2, cursor="hand2",
                  command=self._browse_install_path).pack(side="left", padx=(6, 0))

        self.s1_disk_label = tk.Label(f, text="", font=self._f(9), fg=C_SEC, bg=C_BG)
        self.s1_disk_label.pack(anchor="w", pady=(0, 8))
        self._update_disk_space()

        # ── 分隔线 ──
        tk.Frame(f, bg=C_BORDER, height=1).pack(fill="x", pady=(0, 8))

        # ── API Key ──
        tk.Label(f, text="DeepSeek API Key 配置", font=self._f(11),
                 fg=C_TEXT, bg=C_BG).pack(anchor="w", pady=(0, 4))

        self.s1_status = tk.Label(f, text="", font=self._f(10), bg=C_BG)
        self.s1_status.pack(anchor="w")

        self.s1_input_frame = tk.Frame(f, bg=C_BG)
        self.s1_input_frame.pack(fill="x", pady=(8, 0))

        tk.Label(self.s1_input_frame, text="DeepSeek API Key：",
                 font=self._f(10), fg=C_SEC, bg=C_BG).pack(anchor="w")

        inp_f = tk.Frame(self.s1_input_frame, bg=C_BG)
        inp_f.pack(fill="x", pady=(4, 0))

        self.s1_key_entry = tk.Entry(inp_f, font=(FONT_MONO, 11), bg="#111111",
                                     fg=C_TEXT, insertbackground=C_TEXT,
                                     relief="solid", bd=1, show="*")
        self.s1_key_entry.pack(fill="x", ipady=4)

        tk.Label(self.s1_input_frame, text="格式：sk-xxxxxxxxxxxxxxxx",
                 font=self._f(9), fg=C_MUTED, bg=C_BG).pack(anchor="w", pady=(4, 0))

        # check existing .env
        existing_key = ""
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as fh:
                    for line in fh:
                        if line.strip().startswith("DEEPSEEK_API_KEY="):
                            existing_key = line.strip().split("=", 1)[1].strip().strip("'\"")
                            break
            except Exception:
                pass

        if existing_key and existing_key not in ("", "sk-your-key-here", "change-me"):
            self.s1_status.configure(text="已检测到 API Key 配置", fg=C_SUCCESS)
            self.s1_key_entry.insert(0, existing_key)
            self.btn_next.configure(state="normal")
        else:
            self.s1_status.configure(text="请输入 DeepSeek API Key", fg=C_WARN)
            self.s1_key_entry.insert(0, "")
            self.s1_key_entry.focus_set()

        self.s1_key_entry.bind("<KeyRelease>", self._validate_key)

    def _validate_key(self, event=None):
        key = self.s1_key_entry.get().strip()
        if key.startswith("sk-") and len(key) > 10:
            self.s1_status.configure(text="API Key 格式正确", fg=C_SUCCESS)
            self.btn_next.configure(state="normal")
        elif key:
            self.s1_status.configure(text="API Key 格式不正确，应以 sk- 开头", fg=C_WARN)
            self.btn_next.configure(state="disabled")
        else:
            self.s1_status.configure(text="请输入 API Key", fg=C_MUTED)
            self.btn_next.configure(state="disabled")

    def _save_env(self):
        try:
            key = self.s1_key_entry.get().strip()
        except Exception:
            key = ""
        if not key:
            return
        env_path = os.path.join(self.install_path, "backend", ".env")
        example_path = os.path.join(self.install_path, "deployment", ".env.example")
        # fallback to source if install_path hasn't been populated yet
        if not os.path.exists(example_path):
            example_path = os.path.join(self._src_root, "deployment", ".env.example")

        if os.path.exists(env_path):
            # update existing
            with open(env_path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
            with open(env_path, "w", encoding="utf-8") as fh:
                for line in lines:
                    if line.strip().startswith("DEEPSEEK_API_KEY="):
                        fh.write(f"DEEPSEEK_API_KEY={key}\n")
                    else:
                        fh.write(line)
        elif os.path.exists(example_path):
            os.makedirs(os.path.dirname(env_path), exist_ok=True)
            shutil.copy2(example_path, env_path)
            with open(env_path, "r", encoding="utf-8") as fh:
                content = fh.read()
            content = content.replace("sk-your-key-here", key)
            with open(env_path, "w", encoding="utf-8") as fh:
                fh.write(content)

    # ── install path helpers ──

    def _browse_install_path(self):
        chosen = tkinter.filedialog.askdirectory(
            title="选择 ScriptForge 安装目录",
            initialdir=self.install_path,
        )
        if chosen and chosen != self.install_path:
            self.install_path = chosen
            self.s1_path_entry.delete(0, "end")
            self.s1_path_entry.insert(0, self.install_path)
            self._update_disk_space()

    def _update_disk_space(self):
        try:
            drive = os.path.splitdrive(self.install_path)[0] or "C:"
            usage = shutil.disk_usage(drive)
            free_gb = usage.free / (1024 ** 3)
            self.s1_disk_label.configure(
                text=f"{drive} 可用空间: {free_gb:.0f} GB（建议 ≥ 10 GB）",
                fg=C_SUCCESS if free_gb >= 10 else C_WARN)
        except Exception:
            self.s1_disk_label.configure(text="无法检测磁盘空间", fg=C_MUTED)

    def _copy_project_if_needed(self, on_done=None):
        """Copy project files to install_path if it differs from source.
        Runs in a background thread to avoid freezing the UI."""
        src = self._src_root
        dst = self.install_path
        if os.path.normpath(src) == os.path.normpath(dst):
            if on_done:
                self.root.after(0, on_done)
            return
        marker = os.path.join(dst, "docker-compose.yml")
        if os.path.exists(marker):
            if on_done:
                self.root.after(0, on_done)
            return

        def _copy_tree(sub):
            """Copy a subdirectory tree, skipping caches and build artifacts."""
            s = os.path.join(src, sub)
            d = os.path.join(dst, sub)
            if not os.path.isdir(s):
                return
            _skip = {".git", "__pycache__", "node_modules", ".next",
                     "venv", ".venv", ".idea", ".vscode", ".pytest_cache",
                     "models", "uploads", "logs", "backups", "voice_profiles",
                     "tests"}
            _skip_ext = (".pyc", ".egg-info")
            for dirpath, dirnames, filenames in os.walk(s):
                dirnames[:] = [dn for dn in dirnames
                               if dn.lower() not in _skip]
                rel = os.path.relpath(dirpath, s)
                td = os.path.join(d, rel) if rel != "." else d
                os.makedirs(td, exist_ok=True)
                for fn in filenames:
                    if fn.lower().endswith(_skip_ext):
                        continue
                    try:
                        shutil.copy2(os.path.join(dirpath, fn), os.path.join(td, fn))
                    except Exception:
                        pass

        def _copy_file(sub):
            """Copy a single file from src/sub to dst/sub."""
            s = os.path.join(src, sub)
            d = os.path.join(dst, sub)
            if os.path.isfile(s):
                os.makedirs(os.path.dirname(d), exist_ok=True)
                try:
                    shutil.copy2(s, d)
                except Exception:
                    pass

        def _worker():
            try:
                # Only copy files actually needed for docker build & runtime.
                os.makedirs(dst, exist_ok=True)
                _copy_file("docker-compose.yml")
                _copy_tree("deployment")
                _copy_tree("backend/app")
                _copy_tree("backend/alembic")
                _copy_tree("backend/offline_packages")
                _copy_file("backend/Dockerfile")
                _copy_file("backend/requirements.txt")
                _copy_file("backend/.dockerignore")
                # frontend: only need the built dist
                _copy_tree("frontend/dist")
            except Exception as e:
                logger.warning("Project copy failed: %s", e)
            if on_done:
                self.root.after(0, on_done)

        threading.Thread(target=_worker, daemon=True).start()

    # ════════════════════════════════════════════════════════
    #  STEP 2 : 加载镜像
    # ════════════════════════════════════════════════════════

    def _render_step2(self):
        f = self.content
        tar_path = os.path.join(self._src_root, "deployment", "docker-images", "base-images.tar")

        tk.Label(f, text="加载 Docker 基础镜像", font=self._f(11),
                 fg=C_TEXT, bg=C_BG).pack(anchor="w", pady=(4, 4))

        self.s2_log = self._create_log(f)

        if os.path.exists(tar_path):
            sz_mb = os.path.getsize(tar_path) // (1024 * 1024)
            img_count = self._count_images_in_tar(tar_path)

            self._append_log(self.s2_log, f"发现离线镜像包: base-images.tar ({sz_mb} MB)")
            self._append_log(self.s2_log, f"包含 {img_count} 个镜像，请耐心等待加载...")

            # progress bar
            self._create_progress(f, total_steps=img_count)
            self.root.update_idletasks()
            self._draw_progress()

            # start marquee animation
            self._start_marquee()

            # start heartbeat with elapsed time
            self._heartbeat(self.s2_log, "正在解压并加载镜像")

            def on_docker_load_line(line):
                if "Loaded image:" in line or "loaded image:" in line.lower():
                    name = line.split(":", 1)[-1].strip() if ":" in line else ""
                    self.root.after(0, lambda: self._tick_progress(name))

            self._run_cmd(
                ["docker", "load", "-i", tar_path],
                self.s2_log,
                self._on_images_loaded,
                cwd=self.install_path,
                on_line=on_docker_load_line,
            )
        else:
            self._append_log(self.s2_log, "未找到离线镜像包，构建时将从网络拉取", C_WARN)
            self._append_log(self.s2_log, "请确保网络连接正常")
            self.btn_next.configure(state="normal")

    def _on_images_loaded(self, rc):
        self._heartbeat_stop = True
        self._stop_marquee()
        if rc == 0:
            # ensure bar shows 100%
            self._pb_done = self._pb_total
            self._draw_progress()
            self._pb_label.configure(text=f"{self._pb_done}/{self._pb_total} 个镜像  -  全部加载完成",
                                     fg=C_SUCCESS)
            elapsed = int(time.time() - getattr(self, '_heartbeat_start', time.time()))
            m, s = divmod(elapsed, 60)
            self._append_log(self.s2_log, f"基础镜像加载完成（用时 {m}:{s:02d}）", C_SUCCESS)
            self.btn_next.configure(state="normal")
        else:
            self._append_log(self.s2_log, "镜像加载失败（将尝试在线拉取）", C_WARN)
            self.btn_next.configure(state="normal")

    # ════════════════════════════════════════════════════════
    #  STEP 3 : 构建启动
    # ════════════════════════════════════════════════════════

    def _render_step3(self):
        f = self.content

        tk.Label(f, text="构建并启动 ScriptForge 服务", font=self._f(11),
                 fg=C_TEXT, bg=C_BG).pack(anchor="w", pady=(4, 4))

        self._create_progress(f, total_steps=2)
        self.root.update_idletasks()

        self.s3_log = self._create_log(f)

        # Build status animation: writes directly into progress bar
        self._s3_building = True
        self._s3_status = "准备构建..."
        self._s3_pulse = 0
        self._s3_tick()

        self._heartbeat(self.s3_log, "正在构建")
        self._append_log(self.s3_log, "执行: docker compose build")

        def on_build_line(line):
            if "transferring context:" in line:
                parts = line.split("transferring context:")
                if len(parts) > 1:
                    info = parts[1].strip().split()[0]
                    self._s3_status = f"传输构建上下文 {info}"
            elif "exporting to image" in line:
                self._s3_status = "导出镜像..."
            elif re.match(r'^#\d+\s+\[', line):
                m = re.match(r'^#\d+\s+\[(\S+)', line)
                if m:
                    self._s3_status = f"构建服务: {m.group(1)}"

        self._run_cmd(
            ["docker", "compose", "build"],
            self.s3_log,
            self._on_build_done,
            cwd=self.install_path,
            on_line=on_build_line,
        )

    def _s3_tick(self):
        """Periodically redraw the progress bar with build status + pulse."""
        if not getattr(self, '_s3_building', False):
            return
        self._s3_pulse += 1
        dots = "." * ((self._s3_pulse % 4) + 1)

        c = self._pb_canvas
        c.delete("all")
        w = c.winfo_width() or 500
        h = self._pb_bar_h
        c.create_rectangle(0, 0, w, h, fill="#111111", outline="")
        c.create_text(w // 2, h // 2,
                      text=f"{self._s3_status}{dots}",
                      fill=C_BRAND, font=(FONT_MONO, 9, "bold"))

        self._pb_label.configure(text=self._s3_status, fg=C_TEXT)

        self.root.after(500, self._s3_tick)

    def _on_build_done(self, rc):
        self._heartbeat_stop = True
        self._s3_building = False
        if rc != 0:
            self._append_log(self.s3_log, "构建失败！", C_ERROR)
            self._pb_label.configure(text="构建失败", fg=C_ERROR)
            self._draw_progress()
            retry = tk.Button(self.content, text="重试构建", font=self._f(10),
                              bg=C_BRAND, fg="white", relief="flat",
                              padx=14, pady=4, cursor="hand2",
                              command=self._retry_build)
            retry.pack(pady=(8, 0))
            return

        self._tick_progress("构建完成")
        elapsed = int(time.time() - getattr(self, '_heartbeat_start', time.time()))
        m, s = divmod(elapsed, 60)
        self._append_log(self.s3_log, f"构建完成（用时 {m}:{s:02d}）", C_SUCCESS)
        self._append_log(self.s3_log, "执行: docker compose up -d")

        # restart animation for startup phase
        self._s3_building = True
        self._s3_status = "启动服务中"
        self._s3_pulse = 0
        self._s3_tick()
        self._heartbeat(self.s3_log, "正在启动")

        self._run_cmd(
            ["docker", "compose", "up", "-d"],
            self.s3_log,
            self._on_start_done,
            cwd=self.install_path,
        )

    def _on_start_done(self, rc):
        self._heartbeat_stop = True
        self._s3_building = False
        if rc != 0:
            self._append_log(self.s3_log, "启动失败！", C_ERROR)
            self._pb_label.configure(text="启动失败", fg=C_ERROR)
            self._draw_progress()
            retry = tk.Button(self.content, text="重试启动", font=self._f(10),
                              bg=C_BRAND, fg="white", relief="flat",
                              padx=14, pady=4, cursor="hand2",
                              command=self._retry_start)
            retry.pack(pady=(8, 0))
            return

        self._tick_progress("启动完成")
        self._append_log(self.s3_log, "所有服务已启动", C_SUCCESS)
        self.btn_next.configure(state="normal")

    def _retry_build(self):
        for w in self.content.winfo_children():
            if isinstance(w, tk.Button):
                w.destroy()
        self._s3_building = True
        self._s3_status = "准备构建..."
        self._s3_pulse = 0
        self._s3_tick()
        self._heartbeat(self.s3_log, "正在重新构建")
        self._append_log(self.s3_log, "重新构建...")
        self._run_cmd(["docker", "compose", "build"], self.s3_log,
                       self._on_build_done, cwd=self.install_path)

    def _retry_start(self):
        for w in self.content.winfo_children():
            if isinstance(w, tk.Button):
                w.destroy()
        self._s3_building = True
        self._s3_status = "启动服务中"
        self._s3_pulse = 0
        self._s3_tick()
        self._heartbeat(self.s3_log, "正在重新启动")
        self._append_log(self.s3_log, "重新启动...")
        self._run_cmd(["docker", "compose", "up", "-d"], self.s3_log,
                       self._on_start_done, cwd=self.install_path)

    # ════════════════════════════════════════════════════════
    #  STEP 4 : 完成
    # ════════════════════════════════════════════════════════

    def _render_step4(self):
        f = self.content

        tk.Label(f, text="🎉 ScriptForge 安装完成！", font=self._f(16, True),
                 fg=C_SUCCESS, bg=C_BG).pack(pady=(16, 4))

        tk.Label(f, text="系统已启动，等待约 30 秒后即可访问", font=self._f(10),
                 fg=C_SEC, bg=C_BG).pack()

        # access info card
        card = tk.Frame(f, bg=C_CARD, highlightbackground=C_SUCCESS,
                        highlightthickness=1, padx=20, pady=16)
        card.pack(fill="x", pady=(16, 8))

        ports = [
            ("前端页面", "http://localhost:3001"),
            ("后端 API", "http://localhost:8080"),
            ("API 文档", "http://localhost:8080/docs"),
        ]
        for label, url in ports:
            row = tk.Frame(card, bg=C_CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label + "：", font=self._f(10), fg=C_SEC,
                     bg=C_CARD, width=10, anchor="e").pack(side="left")
            link = tk.Label(row, text=url, font=(FONT_MONO, 10), fg=C_BRAND_HV,
                            bg=C_CARD, cursor="hand2")
            link.pack(side="left", padx=(4, 0))
            link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

        # buttons
        bf = tk.Frame(f, bg=C_BG)
        bf.pack(pady=(16, 0))

        tk.Button(bf, text="打开 ScriptForge", font=self._f(11, True),
                  bg=C_BRAND, fg="white", relief="flat",
                  padx=20, pady=8, cursor="hand2",
                  command=lambda: webbrowser.open("http://localhost:3001")).pack(side="left", padx=4)

        tk.Button(bf, text="退出", font=self._f(11),
                  bg=C_HOVER, fg=C_SEC, relief="flat",
                  padx=20, pady=8, cursor="hand2",
                  command=self.root.quit).pack(side="left", padx=4)

        # hide nav buttons
        self.btn_back.configure(state="disabled")
        self.btn_next.configure(state="disabled")
        self.btn_cancel.configure(text="退出")

    # ── override _go_next to save env between steps ──

    def _go_next(self):
        if self.current_step == 1:
            # read install path from entry (before widget destroyed)
            try:
                self.install_path = self.s1_path_entry.get().strip()
            except Exception:
                pass
            # validate API key
            try:
                key = self.s1_key_entry.get().strip()
            except Exception:
                key = ""
            if not key.startswith("sk-") or len(key) <= 10:
                return

            need_copy = (os.path.normpath(self._src_root) != os.path.normpath(self.install_path)
                         and not os.path.exists(os.path.join(self.install_path, "docker-compose.yml")))

            if need_copy:
                # show copying status, disable buttons
                self.s1_status.configure(text="正在复制项目文件到新路径，请稍候...", fg=C_BRAND)
                self.btn_next.configure(state="disabled", text="复制中...")
                self.btn_back.configure(state="disabled")
                self.root.update_idletasks()
                # ensure target dir exists before saving env
                os.makedirs(self.install_path, exist_ok=True)

            # save env (works on original src if no copy, or new path after makedirs)
            self._save_env()

            if need_copy:
                def _after_copy():
                    self._save_env()  # re-save to the now-copied location
                    self.btn_next.configure(text="下一步")
                    if self.current_step < 4:
                        self._go_step(self.current_step + 1)
                self._copy_project_if_needed(on_done=_after_copy)
            else:
                if self.current_step < 4:
                    self._go_step(self.current_step + 1)
        elif self.current_step < 4:
            self._go_step(self.current_step + 1)


# ── entry ──

def main():
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    import tkinter.messagebox
    tk.messagebox = tkinter.messagebox
    SetupWizard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
