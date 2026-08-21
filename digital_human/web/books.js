// books 三页共享 (2026-08-20) — 书库 / 内容库 / 讲书
// books router 无 /api 前缀, 此处 api 胶水不带前缀 (与后端路径直连).
const BOOKS = { cur: null };
let _busy = false;
// 支持 # 前缀 (getElementById): $('#id') 与 $('id') 均可
const $ = id => document.getElementById(String(id).replace(/^#/, ''));

function esc(s) { return (s == null ? '' : String(s)).replace(/[<>&]/g, c => ({ '<':'&lt;', '>':'&gt;', '&':'&amp;' }[c])); }

async function api(path, opts) {
  const resp = await fetch(path, opts);
  if (!resp.ok) {
    let detail = '';
    try { detail = (await resp.json()).detail || ''; } catch (_) {}
    throw new Error(detail || `HTTP ${resp.status}`);
  }
  return resp.json().catch(() => ({}));
}

function toast(msg, type = 'info') {
  const el = $('#toast');
  if (!el) return;
  el.textContent = msg;
  el.style.background = type === 'error' ? '#7f1d1d' : (type === 'success' ? '#14532d' : '#1e40af');
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 4200);
}

// ── 共享渲染: 流程条 + 下一步入口 + 书名 shell ──
const JOB_STATUS = { created:'待补全', input_review:'待确认输入', roadmap_review:'待确认总纲', writing:'逐集写作中', done:'全部完成', failed:'失败' };

function flowBarHTML(prog) {
  const steps = (prog && prog.steps) || ['输入补全','评论层+素材','多集总纲','逐集确认','进产线'];
  const done = (prog && prog.done) || [false,false,false,false,false];
  const current = (prog && prog.current) || 1;
  const nDone = done.filter(Boolean).length;
  const bar = `<div class="flow-bar">
    ${steps.map((s, i) => {
      const cls = done[i] ? 'done' : (i + 1 === current ? 'active' : 'todo');
      return `<div class="flow-step ${cls}"><span class="flow-num">${i+1}</span>${s}</div>`;
    }).join('<div class="flow-arrow">→</div>')}
  </div>
  <div class="kv" style="margin:0.4rem 0"><span class="k">进度</span>${nDone}/${steps.length} 步完成 · 当前: <b>${steps[current-1]}</b></div>`;
  return bar;
}

function nextActionHTML(na) {
  if (!na) return '';
  return `<div class="next-action">
    <span class="next-label">▶ 下一步</span>
    <button class="sm" style="background:#16a34a" onclick="doNext('${na.button}', this)">${esc(na.label)}</button>
    <span class="hint">${esc(na.hint || '')}</span>
  </div>`;
}

function renderBookShell() {
  const b = BOOKS.cur;
  if (!$('book-shell')) return;
  $('book-shell').innerHTML = `
    <h1><a href="/web/books.html" style="color:#64748b;text-decoration:none">←</a> 《${esc(b.book_title)}》 <span class="badge">${JOB_STATUS[b.status] || b.status}</span></h1>
    ${flowBarHTML(b.progress)}
    ${nextActionHTML(b.progress && b.progress.next_action)}`;
}

// 加载书 → 渲染 shell + 调页面级 renderPage
async function loadBook(id) {
  BOOKS.cur = await api('/books/' + id);
  renderBookShell();
  if (typeof renderPage === 'function') renderPage(BOOKS.cur);
}

// 通用动作: 门禁已由各页控制, 此处 busy 锁 + POST + 刷新 + toast
async function run(path, btn) {
  if (_busy) { toast('有操作进行中，请等待', 'info'); return; }
  _busy = true;
  if (btn) { btn.disabled = true; btn.textContent = '⏳ 处理中…'; }
  try {
    await api(`/books/${BOOKS.cur.id}/${path}`, { method: 'POST' });
    await loadBook(BOOKS.cur.id);
    toast('完成', 'success');
  } catch (e) {
    toast('失败: ' + e.message, 'error');
  } finally {
    _busy = false;
    if (btn) btn.textContent = btn.dataset.origLabel || btn.textContent;
  }
}

// P0 下一步入口: 后端 progress.next_action 驱动; 'produce' 批量进产线后跳 audio
async function doNext(button, btn) {
  if (button === 'produce') {
    let lastSid = null;
    for (const e of BOOKS.cur.episodes || []) {
      if (e.status === 'confirmed' && !e.script_id) {
        toast(`第${e.ep}集进产线…`, 'info');
        const r = await api(`/books/${BOOKS.cur.id}/episodes/${e.ep}/produce`, {
          method: 'POST', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ persona_id: currentPersonaId() }),
        });
        lastSid = r.script_id;
      }
    }
    await loadBook(BOOKS.cur.id);
    if (lastSid) { toast('已全部进产线，跳转音频页…', 'success'); setTimeout(() => location.href = '/web/audio.html?script_id=' + lastSid, 1000); }
    else toast('没有待进产线的已确认集', 'info');
    return;
  }
  await run(button, btn);
}

// 讲书页覆盖: 当前选中人设 id (books_story.js 定义)
function currentPersonaId() {
  const sel = $('#produce-persona');
  return sel ? (sel.value || null) : null;
}

// ── 书库页专属 (books.html) ──
let BOOKS_LIST = [], _logCount = 0, _logTimer = null;
const KIND_BADGE = { essence: ['精华', ''], full: ['全书', 'need'], distilled: ['蒸馏', 'draft'] };
const EP_BADGE = { pending:'待生成', generating:'生成中', draft:'待确认', confirmed:'已确认' };

async function loadBooks() {
  BOOKS_LIST = (await api('/books')).books;
  const JOB = { created:'待补全', input_review:'待确认输入', roadmap_review:'待确认总纲', writing:'逐集写作中', done:'全部完成', failed:'失败' };
  $('#book-list').innerHTML = BOOKS_LIST.map(b => {
    const eps = b.episodes || [];
    const nConf = eps.filter(e => e.status === 'confirmed').length;
    const prog = b.progress || { done: [false,false,false,false,false], current: 1 };
    const nDone = prog.done.filter(Boolean).length;
    const dots = prog.done.map(d => `<span class="dot ${d ? 'on' : ''}"></span>`).join('');
    return `
    <div class="book-card" onclick="location.href='/web/books_content.html?book_id=${b.id}'">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem">
        <h3 style="margin:0 0 0.4rem">《${esc(b.book_title)}》 <span class="badge">${JOB[b.status] || b.status}</span></h3>
        <button class="sm secondary" onclick="event.stopPropagation();deleteBook('${b.id}','${esc(b.book_title)}')" style="flex-shrink:0" title="删除本书">删除</button>
      </div>
      <div class="kv"><span class="k">作者</span>${esc(b.author || '-')}</div>
      <div class="kv"><span class="k">进度</span>${nDone}/5 步 <span class="mini-dots">${dots}</span> ${eps.length ? `· 逐集已确认 ${nConf}/${eps.length}` : '· 未生成总纲'}</div>
      <div class="eps">${eps.map(e => `<span class="ep-dot ${e.status}" title="${EP_BADGE[e.status] || e.status}">E${e.ep}</span>`).join('') || '<span class="hint">未生成总纲</span>'}</div>
    </div>`;
  }).join('') || '<div class="hint">暂无项目</div>';
}

// 单本蒸馏: 事件委托 (data-distill 书名 → 反查 path), 避免反斜杠进 HTML 属性
let _libSrcs = [];
document.addEventListener('click', e => {
  const btn = e.target.closest('[data-distill]');
  if (btn) distillSingleByTitle(btn.dataset.distill);
});
async function loadLib() {
  const r = await api('/book-sources');
  const srcs = r.sources || [];
  _libSrcs = srcs;
  // 按书名去 .蒸馏 后缀分组: {书名: [source,...]}
  const base = fn => fn.replace(/\.蒸馏/, '').replace(/\.(txt|md|epub)$/i, '');
  const groups = {};
  srcs.forEach(s => { (groups[base(s.filename)] = groups[base(s.filename)] || []).push(s); });
  // 可蒸馏判定: 复用后端逻辑 (full 形态且无 .蒸馏)
  const isDistillable = s => s.kind === 'full' && !srcs.some(x =>
    x.filename !== s.filename && x.kind === 'distilled' && base(x.filename) === base(s.filename));

  // 组排序: 组内最新 mtime 降序 (新书/新蒸馏置顶); 记录组级信息
  const FOLD_MS = 30 * 24 * 3600 * 1000;  // 30 天折叠阈值
  const rows = Object.entries(groups).map(([name, list]) => {
    const maxMtime = Math.max(...list.map(s => s.mtime || 0));
    const hasFull = list.some(s => s.kind === 'full');
    const distillable = list.some(isDistillable);
    // 有可蒸馏任务 → 不折叠 (新任务需可见); 否则超 30 天折叠
    const stale = !distillable && (Date.now() / 1000 - maxMtime) > FOLD_MS / 1000;
    return { name, list, maxMtime, hasFull, distillable, stale };
  }).sort((a, b) => b.maxMtime - a.maxMtime);

  const nDistillable = rows.filter(x => x.distillable).length;
  $('#lib-panel').innerHTML = `<h2>书库 (${rows.length} 本<span class="hint"> · ${nDistillable} 待蒸馏</span>)</h2>` +
    rows.map(g => {
      const badges = g.list.map(s => {
        const [label, cls] = KIND_BADGE[s.kind] || ['?', ''];
        return `<span class="badge ${cls}">${label}</span>`;
      }).join('');
      const sizeTxt = g.list.map(s => `${(s.size/1024).toFixed(0)}KB`).join(' / ');
      const previewBtn = g.list.find(s => s.kind !== 'full')
        ? `<button class="sm secondary" onclick="previewSrc('${esc(g.list[0].filename)}')">预览</button>` : '';
      const distillBtn = g.distillable
        ? `<button class="sm" style="background:#7c3aed" data-distill="${esc(g.name)}">🔬 蒸馏</button>` : '';
      const ts = g.maxMtime ? new Date(g.maxMtime * 1000).toLocaleDateString('zh-CN') : '';
      if (g.stale) {
        // 折叠: 单行, 点开展开
        return `<div class="lib-group stale">
          <div class="lib-group-head" onclick="this.parentElement.classList.toggle('open')">
            <span class="fold-arrow">▶</span> <b>《${esc(g.name)}》</b> ${badges}
            <span class="hint">${sizeTxt} · ${ts}</span>
          </div>
          <div class="lib-group-body">${previewBtn}</div>
        </div>`;
      }
      return `<div class="lib-group">
        <div class="lib-group-head">
          <b>《${esc(g.name)}》</b> ${badges}
          <span class="hint">${sizeTxt} · ${ts}</span>
          <span style="flex:1"></span>${distillBtn}${previewBtn}
        </div>
      </div>`;
    }).join('') || '<div class="hint">书库为空</div>';
  return srcs;
}

async function distillSingleByTitle(name) {
  // 从缓存源列表反查可蒸馏的 path (full 形态且无 .蒸馏)
  const base = fn => fn.replace(/\.蒸馏/, '').replace(/\.(txt|md|epub)$/i, '');
  const cand = _libSrcs.find(s => s.kind === 'full' && base(s.filename) === base(name) + '');
  if (!cand) { toast('未找到该书源', 'error'); return; }
  const path = cand.path;
  const pname = name.replace(/ \([^)]*\)$/, '');  // 去 (zhihailib.com) 后缀显示
  if (!confirm(`🔬 对《${pname}》启动本地蒸馏？\n\n将拉起本地 Gemma (占 17G 显存)，对该书全文蒸馏出精华稿。\n结束后自动释放显存。`)) return;
  try {
    await api('/distill/start-single?path=' + encodeURIComponent(path), { method: 'POST' });
    toast(`《${pname}》蒸馏已启动`, 'info');
    _distillStart = Date.now();
    _logCount = 0;
    connectDistillSSE();
    pollDistill();
  } catch (e) {
    toast('蒸馏启动失败: ' + e.message, 'error');
  }
}

async function previewSrc(fn) {
  const r = await api('/book-sources/preview?filename=' + encodeURIComponent(fn));
  $('#pv-title').textContent = '预览: ' + r.filename;
  $('#pv-body').textContent = r.preview;
  $('#preview-modal').classList.add('active');
}

function renderLog(events) {
  if (!events.length) return;
  $('#distill-log').style.display = '';
  $('#distill-log-body').innerHTML = events.map(e =>
    `<span class="hint">${e.ts}</span> <span style="${e.level === 'ok' ? 'color:#86efac' : e.level === 'error' ? 'color:#fca5a5' : 'color:#94a3b8'}">${esc(e.msg)}</span>`).join('\n');
  $('#distill-log-body').scrollTop = 99999;
  _logCount = events.length;
}

// 蒸馏进度显示 (2026-08-20): 点击启动时记录开始时间, pollDistill 算百分比+耗时
let _distillStart = null;
let _wasRunning = false;  // 完成检测: running→false 时 toast 提示

async function pollDistill() {
  const st = await api('/distill/status');
  renderLog(st.events || []);
  // 确认按钮: 运行中隐藏, 完成后显示 (2026-08-20)
  const doneBtn = $('#distill-done-btn');
  if (doneBtn) doneBtn.style.display = st.running ? 'none' : (st.events && st.events.length ? '' : 'none');
  const liveBadge = $('#distill-live');
  if (liveBadge) liveBadge.style.display = st.running ? '' : 'none';
  let label = '';
  if (st.running) {
    const prog = st.progress || {};
    const book = esc(prog.book || '');
    const ch = String(prog.chapter || '');   // 形如 "41/58"
    const m = ch.match(/(\d+)\s*\/\s*(\d+)/);
    let pct = '';
    if (m) {
      const cur = parseInt(m[1], 10), tot = parseInt(m[2], 10);
      if (tot > 0) pct = ` (${Math.round(cur / tot * 100)}%)`;
    }
    // 耗时: 本页启动记录 → 刷新后从首条事件时间推断
    let dur = '';
    const stTs = _distillStart || (st.events && st.events[0] ? evTs(st.events[0].ts) : null);
    if (stTs) {
      const sec = Math.floor((Date.now() - stTs) / 1000);
      if (sec > 0 && sec < 24 * 3600) {
        const h = Math.floor(sec / 3600), mm = Math.floor((sec % 3600) / 60), ss = sec % 60;
        dur = ` · 已耗时 ${h ? h + 'h ' : ''}${mm}min ${ss}s`;
      }
    }
    label = `蒸馏中: ${book} ${esc(ch)}${pct}${dur}`;
  } else {
    label = st.events.length ? '批次结束 (显存已释放)' : '';
    // 完成检测 (2026-08-20): running 从 true → false 时, 弹出完成提示
    if (_wasRunning) {
      const doneOk = (st.done || []).filter(x => !/FAILED/.test(x)).length;
      const failed = (st.done || []).filter(x => /FAILED/.test(x)).length;
      toast(st.error ? `蒸馏失败: ${st.error}` : `蒸馏完成 ✓ 成功 ${doneOk}${failed ? ` / 失败 ${failed}` : ''}`, st.error ? 'error' : 'success');
      // 完成后自动刷新书库, 显示新蒸馏产物
      loadLib(); loadBooks();
    }
    if (!st.running) _distillStart = null;  // 完成后清计时
  }
  _wasRunning = st.running;
  $('#distill-state').textContent = label;
  $('#btn-distill').disabled = st.running;
  if (st.running || (st.events && st.events.length)) { if (!_logTimer) _logTimer = setTimeout(pollDistill, 2000); }
  else { _logTimer = null; }
  return st;
}

// 完成后确认: 隐藏蒸馏日志面板 + 清状态 + 清后端事件缓冲 (恢复正常页面)
function dismissDistill() {
  const logPanel = $('#distill-log');
  if (logPanel) logPanel.style.display = 'none';
  const state = $('#distill-state');
  if (state) state.textContent = '';
  const doneBtn = $('#distill-done-btn');
  if (doneBtn) doneBtn.style.display = 'none';
  const liveBadge = $('#distill-live');
  if (liveBadge) liveBadge.style.display = 'none';
  _logCount = 0;
  _wasRunning = false;
  if (_logTimer) { clearTimeout(_logTimer); _logTimer = null; }
  // 清后端事件缓冲, 刷新后不再显示旧日志
  api('/distill/clear', { method: 'POST' }).catch(() => {});
  loadLib(); loadBooks();
}

// HH:MM:SS 事件时间戳 → epoch ms (当日); 跨午夜不准但够用
function evTs(ts) {
  const m = String(ts || '').match(/(\d{1,2}):(\d{2}):(\d{2})/);
  if (!m) return null;
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate(),
    parseInt(m[1], 10), parseInt(m[2], 10), parseInt(m[3], 10)).getTime();
}

function connectDistillSSE() {
  const es = new EventSource('/distill/events');
  es.onmessage = ev => {
    const d = JSON.parse(ev.data);
    if (d.type === 'distill_done') { toast('蒸馏完成 ✓', 'success'); es.close(); pollDistill(); }
    if (d.type === 'distill_error') { toast('蒸馏失败: ' + (d.msg || ''), 'error'); es.close(); pollDistill(); }
  };
  es.onerror = () => es.close();
}

async function startDistill() {
  const st = await api('/distill/status');
  const pend = (await api('/distill/pending')).pending;
  if (!confirm(`启动批量蒸馏 ${pend.length} 本? 占用 4090 显存, 批次结束全杀 llama-server 腾卡。`)) return;
  await api('/distill/start', { method: 'POST' });
  _distillStart = Date.now();
  _logCount = 0;
  connectDistillSSE();
  pollDistill();
}

async function loadAll() { await loadLib(); await loadBooks(); await pollDistill(); }

async function openCreate() {
  const srcs = (await api('/book-sources')).sources;
  // 只列已蒸馏的书 (kind=distilled), value 存蒸馏文件路径, 显示书名 (去 .蒸馏 后缀)
  const distilled = srcs.filter(s => s.kind === 'distilled');
  const sel = $('#c-title');
  if (!distilled.length) {
    sel.innerHTML = '<option value="">— 暂无已蒸馏的书，请先蒸馏 —</option>';
  } else {
    sel.innerHTML = '<option value="">— 选择已蒸馏的书 —</option>' +
      distilled.map(s => `<option value="${esc(s.path)}">${esc(s.book_title.replace(/\.蒸馏$/, ''))}</option>`).join('');
  }
  $('#create-modal').classList.add('active');
}

function closeModal(id) { $(id).classList.remove('active'); }

async function createBook() {
  const sel = $('#c-title');
  const srcPath = sel.value;
  if (!srcPath) return alert('请选择已蒸馏的书');
  // 书名: 从蒸馏文件路径取文件名去 .蒸馏.txt
  const fn = srcPath.split(/[\\/]/).pop() || '';
  const bookTitle = fn.replace(/\.蒸馏(\.txt)?$/, '') || '未命名';
  const body = {
    book_title: bookTitle.replace(/[《》]/g, ''),
    author: $('#c-author').value || null,
    cart_url: $('#c-cart').value || null,
    selling_point: $('#c-sell').value || null,
    source_path: srcPath,  // 蒸馏精华文件 = L0 来源, 核心字段提取锚定
    source_url: $('#c-url').value || null,
  };
  const r = await api('/books', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  closeModal('create-modal');
  toast(`已创建《${bookTitle}》, 基于蒸馏精华`, 'success');
  location.href = '/web/books_content.html?book_id=' + r.id;
}

// 删除拆书项目: 二次确认 (破坏性, 级联删 6 集 + 产线产物)
async function deleteBook(id, title) {
  if (!confirm(`⚠️ 确定删除《${title}》？\n\n将删除全书 6 集稿、总纲、评论层/素材；若已进产线，关联的 Script/音频也会一并删除。\n\n此操作不可恢复！`)) return;
  try {
    const r = await api('/books/' + id, { method: 'DELETE' });
    toast(`已删除《${r.book_title || title}》`, 'success');
    loadBooks();
  } catch (e) {
    toast('删除失败: ' + e.message, 'error');
  }
}
