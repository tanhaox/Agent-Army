// 讲书页 (2026-08-20) — 多集总纲(内联编辑) + 逐集稿 + 发布挂车 + 进产线(人设下拉)
// 依赖 books.js 共享. 渲染入口: renderPage(cur). 人设下拉复用 writing.js loadHosts 模式.

let EDIT_EP = null;

function renderPage(b) {
  const inp = b.input_json || {};
  const eps = b.episodes || [];
  const prog = b.progress || { done: [false,false,false,false,false], current: 1 };
  const s1_ok = prog.done[0], s3_ok = prog.done[1];
  const roadmap_ok = eps.length > 0;
  const any_pending = eps.some(e => e.status === 'pending' || e.status === 'generating');
  const any_draft = eps.some(e => e.status === 'draft');
  const EP_BADGE = { pending:'待生成', generating:'生成中', draft:'待确认', confirmed:'已确认' };

  // 总纲表格 (内联编辑): 列 = 集/主题/对应书中内容/核心任务/承上/启下/概念
  const roadmapTable = eps.length ? `
    <table id="roadmap-table"><tr>
      <th>集</th><th>主题</th><th>对应书中内容</th><th>核心任务</th><th>承上</th><th>启下</th><th>概念</th>
    </tr>${eps.map(e => {
      const r = e.roadmap || {};
      return `<tr>
        <td>${e.ep}</td>
        <td class="td-edit" contenteditable="true" data-ep="${e.ep}" data-field="主题">${esc(r.主题 || '')}</td>
        <td class="td-edit" contenteditable="true" data-ep="${e.ep}" data-field="对应书中内容">${esc(r.对应书中内容 || '')}</td>
        <td class="td-edit" contenteditable="true" data-ep="${e.ep}" data-field="核心任务">${esc(r.核心任务 || '')}</td>
        <td class="td-edit" contenteditable="true" data-ep="${e.ep}" data-field="承上">${esc(r.承上 || '')}</td>
        <td class="td-edit" contenteditable="true" data-ep="${e.ep}" data-field="启下">${esc(r.启下 || '')}</td>
        <td class="td-edit" contenteditable="true" data-ep="${e.ep}" data-field="概念">${esc((r.概念 || []).join('、'))}</td>
      </tr>`; }).join('')}
    </table>` : '<div class="hint">未生成</div>';

  // 逐集操作行
  const epRows = eps.map(e => {
    const btns = [];
    btns.push(`<button class="sm" onclick="run('episodes/${e.ep}/generate', this)" ${e.status==='confirmed' ? 'disabled title="已确认"' : ''}>生成 (pro)</button>`);
    btns.push(`<button class="sm secondary" onclick="openEdit(${e.ep})" ${e.script_text ? '' : 'disabled title="先生成稿"'}>修稿</button>`);
    btns.push(`<button class="sm warn" onclick="run('episodes/${e.ep}/confirm', this)" ${e.status==='draft' ? '' : 'disabled title="稿子需先生成并人工过稿"'}>确认3</button>`);
    btns.push(`<button class="sm secondary" onclick="rerunEp(${e.ep})" ${e.status==='pending' ? 'disabled' : ''}>级联重跑≥${e.ep}</button>`);
    if (e.status === 'confirmed' && !e.script_id)
      btns.push(`<button class="sm" style="background:#14532d" onclick="produceEp(${e.ep})">进产线 →</button>`);
    if (e.script_id) {
      btns.push(`<button class="sm" style="background:#14532d" onclick="ttsEp('${e.script_id}')">TTS</button>`);
      btns.push(`<button class="sm" style="background:#14532d" onclick="directEp('${e.script_id}')">导演任务</button>`);
      btns.push(`<a href="/web/audio.html?script_id=${e.script_id}&book_id=${encodeURIComponent(BOOKS.cur.id)}&ep_index=${e.ep}" target="_blank" style="background:#334155;color:#e2e8f0;padding:0.3rem 0.65rem;font-size:0.82rem;border-radius:4px;text-decoration:none">音频页 ↗</a>`);
      btns.push(`<a href="/web/director.html" target="_blank" style="background:#334155;color:#e2e8f0;padding:0.3rem 0.65rem;font-size:0.82rem;border-radius:4px;text-decoration:none">导演台 ↗</a>`);
      // 重跑进产线 (2026-08-20): 删旧 Script 重建, 换新产线/发现错误时用
      btns.push(`<button class="sm warn" onclick="rerunProduce(${e.ep})" title="删旧产线产物, 重新进产线">重跑进产线</button>`);
    }
    return `<div style="border-top:1px solid #334155; padding:0.7rem 0">
      <div class="kv"><b>第${e.ep}集 ${esc(e.title || '')}</b> <span class="badge ${e.status==='confirmed'?'':'need'}">${EP_BADGE[e.status] || e.status}</span></div>
      ${e.script_text ? `<pre class="script">${esc(e.script_text.slice(0, 1200))}${e.script_text.length > 1200 ? '\n…' : ''}</pre>` : ''}
      <div class="toolbar" style="margin-top:0.5rem;margin-bottom:0">${btns.join('')}</div>
    </div>`;
  }).join('');

  $('#page-content').innerHTML = `
    <div class="panel">
      <h2>步骤3 · 多集总纲 <span class="badge">${roadmap_ok ? eps.length + ' 集' : ''}</span> <span class="hint">单元格可直接编辑，加入你的个人视角</span></h2>
      ${roadmapTable}
      <div class="toolbar" style="margin-top:0.8rem">
        <button class="sm" style="${roadmap_ok ? '' : 'background:#16a34a'}" onclick="run('roadmap', this)" ${s3_ok || roadmap_ok ? '' : 'disabled title="需先完成【确认1】"'}>生成总纲 (pro, ~1-3min)</button>
        ${roadmap_ok ? `<button class="sm" style="background:#16a34a" onclick="saveRoadmap()">💾 保存修改</button>` : ''}
        <button class="sm warn" onclick="run('confirm-roadmap', this)" ${roadmap_ok ? '' : 'disabled title="需先生成总纲"'}>确认2 → 进入逐集</button>
      </div>
    </div>

    <div class="panel">
      <h2>步骤4 · 逐集稿 <span class="hint">${eps.filter(e=>e.status==='confirmed').length}/${eps.length} 集已确认</span></h2>
      ${eps.length ? `<div class="toolbar" style="margin-bottom:0.8rem">
        <div class="form-row">
          <div style="flex:0 0 220px;">
            <label>数字人（人物）</label>
            <select id="produce-persona" style="width:100%;padding:0.4rem 0.6rem;font-size:0.82rem;"><option value="">加载中…</option></select>
          </div>
          <span class="persona-lock" id="produce-persona-lock"></span>
        </div>
        <button class="sm" style="background:#16a34a" onclick="generateRemaining(this)" ${any_pending ? '' : 'disabled title="没有待生成的集"'}>⏭ 一键生成剩余集</button>
        <button class="sm warn" onclick="confirmRemaining(this)" ${any_draft ? '' : 'disabled title="没有待确认的集"'}>✔ 一键确认剩余</button>
      </div>` : ''}
      ${eps.length ? epRows : '<div class="hint">先生成总纲</div>'}
    </div>

    <div class="panel">
      <h2>发布 · 挂车清单</h2>
      <div class="toolbar" style="margin-bottom:0"><button class="sm secondary" onclick="showChecklist()">查看挂车清单</button></div>
      <pre class="script" id="checklist" style="display:none"></pre>
    </div>`;

  if (eps.length) loadProducePersonas(inp.persona_id);
}

// ── 人设下拉 (复用 writing.js loadHosts + checkPersonaLock 模式, 2026-08-20) ──
async function loadProducePersonas(savedId) {
  const select = document.getElementById('produce-persona');
  if (!select) return;
  try {
    // personas 端点在 /api 前缀下 (其余 books 端点无前缀), 直接 fetch 完整路径
    const resp = await fetch('/api/personas');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const personas = await resp.json();
    select.innerHTML = '';
    if (!personas.length) {
      select.innerHTML = '<option value="">无人物（先去「人物」页创建）</option>';
      return;
    }
    let defaultSelected = false;
    // 预选: 本书记住的 persona_id → 静读书 (brand=静读书) → 首个有品牌
    const bookPersona = savedId;
    let jingshuBook = null;
    personas.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.brand_name ? `${p.name} · ${p.brand_name}` : `${p.name} · ${p.prompt_template}`;
      if (p.id === bookPersona) { opt.selected = true; defaultSelected = true; }
      if (p.brand_name === '静读书') jingshuBook = opt;
      select.appendChild(opt);
    });
    if (!defaultSelected && jingshuBook) { jingshuBook.selected = true; defaultSelected = true; }
    if (!defaultSelected && personas.length) select.selectedIndex = 0;
    // 选人设 → 显示锁定信息 (音色/形象), 复用 checkPersonaLock 展示逻辑
    select.addEventListener('change', showProducePersonaLock);
    showProducePersonaLock();
  } catch (e) {
    console.error('加载人物失败', e);
    select.innerHTML = '<option value="">人物加载失败</option>';
  }
}

// 展示所选人设的锁定信息 (音色/形象), 与 writing.checkPersonaLock 同款
let _producePersonasCache = [];
async function showProducePersonaLock() {
  const lock = document.getElementById('produce-persona-lock');
  const select = document.getElementById('produce-persona');
  if (!lock || !select) return;
  try {
    if (!_producePersonasCache.length) {
      const resp = await fetch('/api/personas');
      if (resp.ok) _producePersonasCache = await resp.json();
    }
    const p = _producePersonasCache.find(x => x.id === select.value);
    if (!p) { lock.style.display = 'none'; lock.textContent = ''; return; }
    const voiceName = p.voice ? p.voice.name : (p.voice_id ? '已绑定' : '未绑定');
    const roleName = p.role ? p.role.name : '未绑定';
    lock.textContent = `🔒 人物「${p.name}」— 音色: ${voiceName}（音频加工页锁定）| 形象: ${roleName}`;
    lock.style.display = '';
  } catch (e) {
    lock.style.display = 'none'; lock.textContent = '';
  }
}

// ── 总纲内联编辑: 保存 → PUT /books/{id}/roadmap ──
async function saveRoadmap() {
  if (_busy) { toast('有操作进行中，请等待', 'info'); return; }
  const rows = [];
  const hadScript = (BOOKS.cur.episodes || []).some(e => e.script_text);
  document.querySelectorAll('#roadmap-table tr[data-row]').length;  // no-op guard
  const trs = document.querySelectorAll('#roadmap-table tr');
  for (let i = 1; i < trs.length; i++) {  // skip header
    const cells = trs[i].querySelectorAll('td');
    const ep = parseInt(cells[0].textContent.trim(), 10);
    const get = field => {
      const cell = trs[i].querySelector(`td[data-field="${field}"]`);
      return cell ? cell.textContent.trim() : '';
    };
    const concepts = get('概念').split(/[、;；\n]+/).map(s => s.trim()).filter(Boolean);
    rows.push({
      ep, 主题: get('主题'), 对应书中内容: get('对应书中内容'), 核心任务: get('核心任务'),
      承上: get('承上'), 启下: get('启下'), 概念: concepts,
    });
  }
  if (!rows.length) { toast('没有可保存的总纲', 'info'); return; }
  _busy = true;
  try {
    await api(`/books/${BOOKS.cur.id}/roadmap`, {
      method: 'PUT', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ episodes: rows }),
    });
    await loadBook(BOOKS.cur.id);
    toast('总纲已保存', 'success');
    if (hadScript) toast('已改总纲，建议对受影响集级联重跑', 'info');
  } catch (e) {
    toast('保存失败: ' + e.message, 'error');
  } finally { _busy = false; }
}

// ── 批量 ──
async function generateRemaining(btn) {
  const pending = (BOOKS.cur.episodes || []).filter(e => e.status !== 'confirmed');
  if (!pending.length) { toast('没有待生成的集', 'info'); return; }
  if (!confirm(`将依次生成剩余 ${pending.length} 集（每集约2-5分钟，请保持页面打开）`)) return;
  _busy = true;
  if (btn) { btn.disabled = true; btn.textContent = `⏳ 0/${pending.length}`; }
  let done = 0;
  try {
    for (const e of pending) {
      toast(`生成第 ${e.ep} 集… (${done+1}/${pending.length})`, 'info');
      await api(`/books/${BOOKS.cur.id}/episodes/${e.ep}/generate`, { method: 'POST' });
      done++;
      await loadBook(BOOKS.cur.id);
      const nb = document.querySelector('[onclick^="generateRemaining"]');
      if (nb) { nb.textContent = `⏳ ${done}/${pending.length}`; nb.disabled = true; }
    }
    toast(`全部生成完成 (${done} 集)，请逐集确认`, 'success');
  } catch (e) {
    toast(`第${done+1}集生成失败: ${e.message}`, 'error');
  } finally {
    _busy = false;
    await loadBook(BOOKS.cur.id);
  }
}

async function confirmRemaining(btn) {
  const drafts = (BOOKS.cur.episodes || []).filter(e => e.status === 'draft');
  if (!drafts.length) { toast('没有待确认的集', 'info'); return; }
  if (!confirm(`确认所有 ${drafts.length} 集草稿？确认后进入定稿，后续修改需重跑。`)) return;
  _busy = true;
  if (btn) btn.disabled = true;
  try {
    for (const e of drafts) await api(`/books/${BOOKS.cur.id}/episodes/${e.ep}/confirm`, { method: 'POST' });
    await loadBook(BOOKS.cur.id);
    toast(`已确认 ${drafts.length} 集`, 'success');
  } catch (e) { toast('确认失败: ' + e.message, 'error'); }
  finally { _busy = false; }
}

// ── 破坏性操作防护 ──
async function rerunEp(n) {
  const affected = (BOOKS.cur.episodes || []).filter(e => e.ep >= n).length;
  if (!confirm(`⚠️ 级联重跑第 ${n} 集起：将清空第 ${n}~${n+affected-1} 集（共${affected}集）的稿件并重新生成，不可恢复！\n\n确认继续？`)) return;
  await run(`episodes/${n}/rerun`);
}

// ── 修稿 modal ──
function openEdit(n) {
  EDIT_EP = n;
  const e = BOOKS.cur.episodes.find(x => x.ep === n);
  $('#e-script').value = e.script_text || '';
  $('#e-ep-title').value = e.title || '';
  $('#e-duration').value = e.target_duration_sec || 600;
  $('#e-title').textContent = `第${n}集 修稿`;
  $('#edit-modal').classList.add('active');
}

async function saveEdit() {
  const body = { script_text: $('#e-script').value };
  const t = $('#e-ep-title').value.trim(); if (t) body.title = t;
  const d = parseFloat($('#e-duration').value); if (d && d >= 60) body.target_duration_sec = d;
  await api(`/books/${BOOKS.cur.id}/episodes/${EDIT_EP}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  closeModal('edit-modal');
  await loadBook(BOOKS.cur.id);
  toast('已保存', 'success');
}

// ── 挂车清单 ──
async function showChecklist() {
  const r = await api(`/books/${BOOKS.cur.id}/cart-checklist`);
  $('#checklist').style.display = ''; $('#checklist').textContent = r.checklist;
}

// ── 进产线 + TTS + 导演 (audio 连通) ──
async function produceEp(n) {
  const e = BOOKS.cur.episodes.find(x => x.ep === n);
  if (!confirm(`第${n}集 确认进产线? 生成 Script+解析段`)) return;
  const r = await api(`/books/${BOOKS.cur.id}/episodes/${n}/produce`, {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ persona_id: currentPersonaId() }),
  });
  await loadBook(BOOKS.cur.id);
  toast(`进产线成功: script_id=${r.script_id}`, 'success');
  // 进产线自动跳音频页 (audio 连通, 带 book/ep 供 PPT 系列皮肤对齐)
  setTimeout(() => location.href = `/web/audio.html?script_id=${r.script_id}&book_id=${encodeURIComponent(BOOKS.cur.id)}&ep_index=${n}`, 1200);
}

// 重跑进产线 (2026-08-20): 删旧 Script/segments 重建 → 跳 audio 页 (可换 PPT 产线)
async function rerunProduce(n) {
  const e = BOOKS.cur.episodes.find(x => x.ep === n);
  if (!confirm(`⚠️ 重跑第 ${n} 集进产线？\n\n将删除该集已有的 Script/解析段 (旧 TTS/导演任务保留在磁盘)，重新生成新的进产线产物，然后跳转音频页。\n\n用于发现错误重做，或切换新产线 (如 PPT 出片)。`)) return;
  try {
    const r = await api(`/books/${BOOKS.cur.id}/episodes/${n}/produce`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ persona_id: currentPersonaId(), force: true }),
    });
    await loadBook(BOOKS.cur.id);
    toast(`重跑成功: 新 script_id=${r.script_id}`, 'success');
    // 跳 audio 页 — 可选 PPT 出片或走现有产线 (带 book/ep 供皮肤对齐)
    setTimeout(() => location.href = `/web/audio.html?script_id=${r.script_id}&book_id=${encodeURIComponent(BOOKS.cur.id)}&ep_index=${n}`, 1200);
  } catch (err) {
    toast('重跑失败: ' + err.message, 'error');
  }
}

// 修复 TTS bug: 路径 /audio/scripts/{sid}/generate-audio + 字段 r.id
async function ttsEp(sid) {
  const r = await api(`/audio/scripts/${sid}/generate-audio?selected_only=true`, { method: 'POST' });
  toast(`TTS 已派发: job=${r.id}，请到 音频页 查看`, 'success');
}

function directEp(sid) {
  window.open(`/web/director.html?script_id=${sid}`, '_blank');
}

function goContent(e) {
  e.preventDefault();
  if (BOOKS.cur) location.href = '/web/books_content.html?book_id=' + BOOKS.cur.id;
}

document.addEventListener('DOMContentLoaded', async () => {
  const id = new URLSearchParams(location.search).get('book_id');
  if (id) await loadBook(id);
  else $('#page-content').innerHTML = '<div class="hint">未指定书，从 <a href="/web/books.html">书库</a> 选择</div>';
});
