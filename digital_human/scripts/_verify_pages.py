# -*- coding: utf-8 -*-
"""三页拆分浏览器验证: console/page 错误捕获 + 跳转链 + 素材包面板渲染."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

CHROME = r"C:\Users\tanhaox\AppData\Local\ms-playwright\chromium-1208\chrome-win64\chrome.exe"
B = "http://127.0.0.1:54321"

errors = []

def attach(page, tag):
    page.on("console", lambda m: errors.append(f"[{tag}] console.{m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"[{tag}] pageerror: {e}"))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=CHROME)
    ctx = browser.new_context()
    page = ctx.new_page()

    # ── 1. 新闻线索页 ──
    attach(page, "news")
    page.goto(f"{B}/web/index.html")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)  # DOMContentLoaded 调取最近文章+素材包
    title_ok = "新闻线索" in page.title()
    pkg_btn = page.locator("#btn-material-create").is_enabled()
    pkg_sel_options = page.locator("#package-select option").count()
    audit_visible = page.locator("#audit-report").is_visible()
    audit_chips = page.locator("#audit-layers .layer-chip").count()
    quota_hint = page.locator(".quota-hint").count()
    print(f"news: title_ok={title_ok} 聚合按钮可用={pkg_btn} 包下拉选项={pkg_sel_options} "
          f"审计报告可见={audit_visible} 层chip={audit_chips} 到期提示={quota_hint}")
    # 截图
    page.screenshot(path="outputs/_verify_news.png", full_page=True)
    # 跳转链: 点 去洗稿
    if page.locator("#btn-goto-writing").is_enabled():
        page.click("#btn-goto-writing")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)

    # ── 2. 文字加工中心 (应带 article_id/package_id 参数跳入) ──
    attach(page, "writing")
    url = page.url
    print("writing url:", url[:110])
    banner_visible = page.locator("#article-banner").is_visible()
    badge = page.locator("#material-context-info").inner_text().strip()
    rewrite_enabled = page.locator("#btn-rewrite").is_enabled()
    tpl_options = page.locator("#rewrite-template option").count()
    char_label = page.locator("#script-char-count").inner_text()
    print(f"writing: banner={banner_visible} badge='{badge}' 洗稿按钮={rewrite_enabled} 模板数={tpl_options} 字数='{char_label}'")
    page.screenshot(path="outputs/_verify_writing.png", full_page=True)
    # ── 3. 音频加工中心 ──
    scripts = page.evaluate("fetch('/api/scripts?limit=1').then(r=>r.json())")
    if scripts:
        page.goto(f"{B}/web/audio.html?script_id={scripts[0]['id']}")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
    attach(page, "audio")
    seg_rows = page.locator("#segments-list .segment").count()
    voice_options = page.locator("#voice-select option").count()
    audio_btn = page.locator("#btn-audio").is_enabled()
    nav3 = page.locator("nav a", has_text="音频加工").count()
    print(f"audio: 段落行={seg_rows} 音色选项={voice_options} 生成按钮={audio_btn} nav三链接={nav3}")
    page.screenshot(path="outputs/_verify_audio.png", full_page=True)

    browser.close()

print("\n=== Console/Page 错误 ===")
if errors:
    for e in errors:
        print(e)
    sys.exit(1)
print("0 错误 ✓")
