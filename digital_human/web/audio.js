// audio.js (2026-08-15) — 音频加工中心: 段落选择 / TTS / 一键成片 / 音色锁
// 从 app.js v6 迁入全部音频系函数; 依赖 app.js v7 共享层

// ── 段落渲染全家 (从 app.js v6 迁入) ──
function renderSegments(segments) {
  const container = document.getElementById('segments-list');
  if (!container) return;
  container.innerHTML = '';
  const selected = segments.filter(s => s.selected_for_host).sort((a, b) => a.host_order - b.host_order);
  const ordered = [...selected, ...segments.filter(s => !s.selected_for_host).sort((a, b) => a.line_index - b.line_index)];
  ordered.forEach((seg, idx) => {
    const div = document.createElement('div');
    div.className = 'segment ' + (seg.selected_for_host ? 'selected' : 'unselected');
    div.draggable = seg.selected_for_host;
    div.dataset.id = seg.id;
    if (seg.selected_for_host) {
      div.addEventListener('dragstart', handleDragStart);
      div.addEventListener('dragover', handleDragOver);
      div.addEventListener('drop', handleDrop);
      div.addEventListener('dragenter', handleDragEnter);
      div.addEventListener('dragleave', handleDragLeave);
      div.addEventListener('dragend', handleDragEnd);
    }
    const orderLabel = seg.selected_for_host ? String(idx + 1) : '-';
    const typeLabel = formatSegmentType(seg.segment_type);
    const durLabel = seg.estimated_duration ? `${seg.estimated_duration.toFixed(1)}s` : '';
    div.innerHTML = `
      <div class="drag-handle" ${seg.selected_for_host ? 'title="拖拽排序"' : ''}>${seg.selected_for_host ? '☰' : ''}</div>
      <div class="order">${orderLabel}</div>
      <input type="checkbox" ${seg.selected_for_host ? 'checked' : ''} onchange="toggleSegment('${seg.id}', this.checked)">
      <div class="text">${escapeHtml(seg.text)}</div>
      <div class="meta">
        <span class="type-badge">${typeLabel}</span>
        ${durLabel ? `<span class="duration">${durLabel}</span>` : ''}
      </div>
    `;
    container.appendChild(div);
  });
  updateDirectorCount();
}

function formatSegmentType(type) {
  const map = { opening: '开场', hook: '钩子', body: '正文', cta: '行动', ending: '结尾' };
  return map[type] || (type || '正文');
}

let dragSrcEl = null;

function handleDragStart(e) {
  dragSrcEl = this;
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', this.dataset.id);
  this.classList.add('dragging');
}

function handleDragOver(e) {
  if (e.preventDefault) e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
  return false;
}

function handleDragEnter(e) {
  this.classList.add('dragging');
}

function handleDragLeave(e) {
  this.classList.remove('dragging');
}

function handleDrop(e) {
  e.stopPropagation();
  e.preventDefault();
  if (!dragSrcEl || dragSrcEl === this) return false;
  const srcId = dragSrcEl.dataset.id;
  const dstId = this.dataset.id;
  reorderSegmentsByDrag(srcId, dstId);
  dragSrcEl.classList.remove('dragging');
  return false;
}

function handleDragEnd(e) {
  document.querySelectorAll('.segment').forEach(el => el.classList.remove('dragging'));
  dragSrcEl = null;
}

function reorderSegmentsByDrag(srcId, dstId) {
  const selected = currentScript.segments.filter(s => s.selected_for_host).sort((a, b) => a.host_order - b.host_order);
  const srcIdx = selected.findIndex(s => s.id === srcId);
  const dstIdx = selected.findIndex(s => s.id === dstId);
  if (srcIdx < 0 || dstIdx < 0) return;
  const [moved] = selected.splice(srcIdx, 1);
  selected.splice(dstIdx, 0, moved);
  selected.forEach((s, i) => { s.host_order = i; });
  renderSegments(currentScript.segments);
  setSaveDirectorEnabled(false);
}

function updateDirectorCount() {
  const container = document.getElementById('segments-list');
  if (!container) return;
  const checked = container.querySelectorAll('input[type="checkbox"]:checked').length;
  const totalDuration = Array.from(container.querySelectorAll('.segment.selected')).reduce((sum, el) => {
    const d = currentScript.segments.find(s => s.id === el.dataset.id);
    return sum + (d && d.estimated_duration ? d.estimated_duration : 0);
  }, 0);
  const count = document.getElementById('director-count');
  if (count) count.textContent = `已选 ${checked} 句 / 约 ${totalDuration.toFixed(1)}s`;
}

function selectAll(selected) {
  if (!currentScript) return;
  currentScript.segments.forEach((seg, i) => {
    seg.selected_for_host = selected;
    if (selected) seg.host_order = i;
    else seg.host_order = 0;
  });
  renderSegments(currentScript.segments);
  setSaveDirectorEnabled(false);
}

async function toggleSegment(segmentId, selected) {
  const seg = currentScript.segments.find(s => s.id === segmentId);
  if (!seg) return;
  seg.selected_for_host = selected;
  if (selected) {
    const maxOrder = Math.max(...currentScript.segments.filter(s => s.selected_for_host).map(s => s.host_order), -1);
    seg.host_order = maxOrder + 1;
  } else {
    seg.host_order = 0;
  }
  renderSegments(currentScript.segments);
  setSaveDirectorEnabled(false);
  // 2026-08-14: 立即同步 DB (之前只改本地, 取消勾选不存 → generate-audio 读 DB 仍生成)
  try {
    await api('PUT', `/scripts/segments/${segmentId}`, {
      selected_for_host: seg.selected_for_host,
      host_order: seg.host_order,
    });
  } catch (e) {
    setStatus('status-audio', '勾选保存失败: ' + e.message, true);
  }
}

async function moveSegment(segmentId, direction) {
  const selected = currentScript.segments.filter(s => s.selected_for_host).sort((a, b) => a.host_order - b.host_order);
  const idx = selected.findIndex(s => s.id === segmentId);
  if (idx < 0) return;
  const newIdx = idx + direction;
  if (newIdx < 0 || newIdx >= selected.length) return;
  [selected[idx], selected[newIdx]] = [selected[newIdx], selected[idx]];
  selected.forEach((s, i) => { s.host_order = i; });
  renderSegments(currentScript.segments);
  setSaveDirectorEnabled(false);
}

async function saveDirectorSelections() {
  const segs = currentScript.segments;
  const selected = segs.filter(s => s.selected_for_host).sort((a, b) => a.host_order - b.host_order);
  selected.forEach((s, i) => { s.host_order = i; });
  try {
    const segmentIds = selected.map(s => s.id);
    await api('POST', `/scripts/${currentScript.id}/segments/reorder`, segmentIds);
    for (const seg of segs) {
      await api('PUT', `/scripts/segments/${seg.id}`, {
        selected_for_host: seg.selected_for_host,
      });
    }
    setSaveDirectorEnabled(true);
    setStatus('status-audio', '导演选择已保存', false, true);
  } catch (e) {
    setStatus('status-audio', e.message, true);
  }
}

// ── persona 音色锁 (2026-08-15 拆页: 按脚本模板锁音色, fetchScript 调用) ──
async function applyPersonaLockByTemplate(template) {
  const lockDiv = document.getElementById('persona-lock');
  const voiceSelect = document.getElementById('voice-select');
  if (!lockDiv || !voiceSelect) return;
  try {
    const persona = await api('GET', `/personas/by-template/${encodeURIComponent(template)}`);
    if (persona && persona.voice_id) {
      voiceSelect.value = persona.voice_id;
      voiceSelect.disabled = true;
      const voiceName = persona.voice ? persona.voice.name : persona.voice_id;
      const roleName = persona.role ? persona.role.name : '未绑定';
      lockDiv.innerHTML = `🔒 人物「${persona.name}」已锁定 — 音色: ${voiceName} | 形象: ${roleName}`;
      lockDiv.style.display = 'block';
    } else {
      voiceSelect.disabled = false;
      lockDiv.style.display = 'none';
    }
  } catch (e) {
    voiceSelect.disabled = false;
    lockDiv.style.display = 'none';
  }
}

// ── TTS 生成 (从 app.js v6 迁入) ──
async function generateAudio() {
  if (!currentScript) return;
  toggle('btn-audio', false);
  toggle('btn-onestop', false);
  setStatus('status-audio', '生成音频中...');
  try {
    const voiceId = document.getElementById('voice-select').value;
    const query = voiceId ? `?voice_id=${encodeURIComponent(voiceId)}&selected_only=true` : '?selected_only=true';
    const job = await api('POST', `/audio/scripts/${currentScript.id}/generate-audio${query}`);
    setStatus('status-audio', `任务已创建: ${job.id}`);
    const container = document.getElementById('audio-list');
    container.innerHTML = '';
    connectAudioSSE(job.id);
  } catch (e) {
    setStatus('status-audio', e.message, true);
    toggle('btn-audio', true);
    toggle('btn-onestop', true);
  }
}

// ── 🚀 一键成片 (2026-08-09) ──
let _onestopAudioSSE = null;
async function oneStop() {
  if (!currentScript) return;
  const btn = document.getElementById('btn-onestop');
  btn.disabled = true;
  btn.textContent = '⏳ 一键成片中...';
  toggle('btn-audio', false);
  try {
    const voiceId = document.getElementById('voice-select').value;
    const query = voiceId ? `?voice_id=${encodeURIComponent(voiceId)}&selected_only=true` : '?selected_only=true';
    const job = await api('POST', `/audio/scripts/${currentScript.id}/generate-audio${query}`);
    setStatus('status-audio', `一键成片: 音频任务已提交 (${job.id})`);
    const container = document.getElementById('audio-list');
    container.innerHTML = '';
    if (_onestopAudioSSE) { _onestopAudioSSE.close(); _onestopAudioSSE = null; }
    _onestopAudioSSE = new EventSource(`${API}/jobs/${job.id}/events`);
    _onestopAudioSSE.onmessage = (ev) => {
      let data;
      try { data = JSON.parse(ev.data); } catch (_) { return; }
      if (data.type === 'tts_service') {
        setStatus('status-audio', data.message);
      } else if (data.type === 'tts_progress') {
        setStatus('status-audio', `一键成片: 音频进度 ${data.completed}/${data.total}`);
        if (data.audio_file) appendAudioItem(data.audio_file);
      } else if (data.type === 'tts_done') {
        if (_onestopAudioSSE) { _onestopAudioSSE.close(); _onestopAudioSSE = null; }
        const btnOnestop = document.getElementById('btn-onestop');
        if (btnOnestop) btnOnestop.textContent = '🚀 一键成片';
        setStatus('status-audio', '音频就绪 — 即将进入导演台自动跑完剩余步骤', false, true);
        if (data.combined_audio) prependCombinedAudio(data.combined_audio);
        loadAudioFiles(job.id);
        try { localStorage.setItem('dh_onestop', '1'); } catch (_) {}
        window.location.href = `/web/director.html?script_id=${encodeURIComponent(currentScript.id)}`
          + (data.combined_audio ? `&audio_id=${encodeURIComponent(data.combined_audio.id)}` : '')
          + '&auto=1';
      } else if (data.type === 'tts_error') {
        if (_onestopAudioSSE) { _onestopAudioSSE.close(); _onestopAudioSSE = null; }
        const btnOnestop = document.getElementById('btn-onestop');
        if (btnOnestop) { btnOnestop.disabled = false; btnOnestop.textContent = '🚀 一键成片'; }
        toggle('btn-audio', true);
        setStatus('status-audio', data.error, true);
        try { localStorage.removeItem('dh_onestop'); } catch (_) {}
      }
    };
    _onestopAudioSSE.onerror = () => {
      if (_onestopAudioSSE && _onestopAudioSSE.readyState === EventSource.CLOSED) {
        _onestopAudioSSE.close(); _onestopAudioSSE = null;
        const btnOnestop = document.getElementById('btn-onestop');
        if (btnOnestop) { btnOnestop.disabled = false; btnOnestop.textContent = '🚀 一键成片'; }
        toggle('btn-audio', true);
        setStatus('status-audio', 'SSE 连接错误', true);
      }
    };
  } catch (e) {
    const btnOnestop = document.getElementById('btn-onestop');
    if (btnOnestop) { btnOnestop.disabled = false; btnOnestop.textContent = '🚀 一键成片'; }
    toggle('btn-audio', true);
    setStatus('status-audio', e.message, true);
  }
}

// ── ID-019: 公共音频 SSE 处理 ──
let _audioSSE = null;
function connectAudioSSE(jobId) {
  if (_audioSSE) { _audioSSE.close(); _audioSSE = null; }
  _audioSSE = new EventSource(`${API}/jobs/${jobId}/events`);
  _audioSSE.onmessage = (ev) => {
    let data;
    try { data = JSON.parse(ev.data); } catch (_) { return; }  // P2-4: 坏数据不崩
    if (data.type === 'tts_service') {
      setStatus('status-audio', data.message);
    } else if (data.type === 'tts_progress') {
      setStatus('status-audio', `进度 ${data.completed}/${data.total}`);
      if (data.audio_file) {
        appendAudioItem(data.audio_file);
      }
    } else if (data.type === 'tts_done') {
      _audioSSE.close(); _audioSSE = null;
      setStatus('status-audio', '音频生成完成', false, true);
      if (data.combined_audio) {
        prependCombinedAudio(data.combined_audio);
      }
      loadAudioFiles(jobId);
      toggle('btn-audio', true);
      // 衔接下一步: 带脚本+合并音频跳到视觉导演页自动建任务
      showDirectorHandoff(currentScript.id, data.combined_audio ? data.combined_audio.id : '');
    } else if (data.type === 'tts_error') {
      _audioSSE.close(); _audioSSE = null;
      setStatus('status-audio', data.error, true);
      toggle('btn-audio', true);
    }
  };
  _audioSSE.onerror = () => {
    if (_audioSSE && _audioSSE.readyState === EventSource.CLOSED) {
      _audioSSE.close(); _audioSSE = null;
      setStatus('status-audio', 'SSE 连接错误', true);
      toggle('btn-audio', true);
    }
  };
}

// ── ID-019: 刷新/跳页返回后恢复音频任务状态 ──
async function restoreAudioJobs() {
  if (!currentScript) return;
  const container = document.getElementById('audio-list');
  if (!container) return;
  const jobs = await api('GET', `/audio/jobs?script_id=${encodeURIComponent(currentScript.id)}&limit=20`)
    .catch(() => []);
  if (!jobs || !jobs.length) return;

  const active = jobs.find(j => j.status === 'pending' || j.status === 'running');
  if (active) {
    setStatus('status-audio', `任务进行中 (${active.id.slice(0, 8)}…) 已恢复订阅`);
    connectAudioSSE(active.id);
    return;
  }

  // P0-1 方案 1: 最新 failed 任务提示可续传 — 已生成段保留在盘, 重试自动跳过
  const latestFailed = jobs.find(j => j.status === 'failed');
  if (latestFailed) {
    const done = latestFailed.completed_segments || 0;
    const total = latestFailed.total_segments || 0;
    if (done > 0 && done < total) {
      setStatus('status-audio', `上次生成失败于 ${done}/${total} 段 — 重新生成将从断点继续`, true);
    } else {
      setStatus('status-audio', '上次生成失败 — 重新生成将从头开始', true);
    }
  }

  const completed = jobs.filter(j => j.status === 'completed').slice(0, 3);
  container.innerHTML = '';
  for (const job of completed) {
    await loadAudioFiles(job.id);
  }
}

function appendAudioItem(f) {
  const container = document.getElementById('audio-list');
  const div = document.createElement('div');
  div.className = 'audio-item';
  const label = f.filename + (f.duration ? ` (${f.duration.toFixed(2)}s)` : '');
  div.innerHTML = `
    <div>${label}</div>
    <audio controls src="${API}/audio/files/${f.id}/download"></audio>
    <a href="${API}/audio/files/${f.id}/download" download>下载</a>
  `;
  container.appendChild(div);
}

function prependCombinedAudio(f) {
  const container = document.getElementById('audio-list');
  const prev = container.querySelector('.audio-item.combined');
  if (prev) prev.remove();
  const div = document.createElement('div');
  div.className = 'audio-item combined';
  div.style.borderLeft = '3px solid var(--accent)';
  div.style.background = 'rgba(59,130,246,0.06)';
  const label = '🎙️ 完整段落音频' + (f.duration ? ` (${f.duration.toFixed(2)}s)` : '');
  div.innerHTML = `
    <div style="min-width:160px;font-weight:600;color:var(--accent);">${label}</div>
    <audio controls src="${API}/audio/files/${f.id}/download"></audio>
    <a href="${API}/audio/files/${f.id}/download" download>下载</a>
  `;
  container.insertBefore(div, container.firstChild);
}

async function loadAudioFiles(jobId) {
  const files = await api('GET', `/audio/jobs/${jobId}/files`);
  const container = document.getElementById('audio-list');
  container.innerHTML = '';
  const combined = files.find(f => !f.segment_id);
  if (combined) {
    prependCombinedAudio(combined);
  }
  files.filter(f => f.segment_id).forEach(f => appendAudioItem(f));
}

// ── 音频加工 → 视觉导演衔接: 倒计时跳转, 携带 script/audio ID ──
let directorHandoffTimer = null;

function showDirectorHandoff(scriptId, audioId) {
  const container = document.getElementById('audio-list');
  if (!container) return;
  const prev = document.getElementById('director-handoff');
  if (prev) prev.remove();

  const url = `/web/director.html?script_id=${encodeURIComponent(scriptId)}`
    + (audioId ? `&audio_id=${encodeURIComponent(audioId)}` : '')
    + '&auto=1';

  const div = document.createElement('div');
  div.id = 'director-handoff';
  div.className = 'audio-item';
  div.style.borderLeft = '3px solid #8b5cf6';
  div.style.background = 'rgba(139,92,246,0.08)';
  div.style.marginTop = '0.75rem';
  div.innerHTML = `
    <div style="flex:1;font-weight:600;color:#a78bfa;">
      🎬 音频就绪 — <span id="handoff-count">8</span>s 后进入视觉导演自动创建任务
    </div>
    <button class="btn btn-primary btn-sm" type="button" id="handoff-go">立即进入</button>
    <button class="btn btn-secondary btn-sm" type="button" id="handoff-stay">留在本页</button>
  `;
  container.parentNode.insertBefore(div, container);

  const go = () => {
    if (directorHandoffTimer) { clearInterval(directorHandoffTimer); directorHandoffTimer = null; }
    window.location.href = url;
  };
  document.getElementById('handoff-go').onclick = go;
  document.getElementById('handoff-stay').onclick = () => {
    if (directorHandoffTimer) { clearInterval(directorHandoffTimer); directorHandoffTimer = null; }
    div.querySelector('div').innerHTML = '🎬 音频就绪 — 可随时进入视觉导演继续下一步';
    document.getElementById('handoff-stay').remove();
  };

  let remain = 8;
  directorHandoffTimer = setInterval(() => {
    remain -= 1;
    const el = document.getElementById('handoff-count');
    if (!el) { clearInterval(directorHandoffTimer); directorHandoffTimer = null; return; }
    el.textContent = remain;
    if (remain <= 0) go();
  }, 1000);
}

// ── 本页脚本下拉回调 (与文字加工页 selectExistingScript 区分命名) ──
async function selectScriptForAudio(select) {
  const scriptId = select.value;
  if (!scriptId) return;
  try {
    await fetchScript(scriptId);
    toggle('btn-audio', true);
    toggle('btn-onestop', true);
    setStatus('status-audio', '已调取脚本 — 选段落和音色后生成', false, true);
  } catch (e) {
    setStatus('status-audio', '调取脚本失败: ' + e.message, true);
  }
}

// ── 初始化: URL 参数 script_id (从文字加工中心/拆书讲书页跳入) ──
document.addEventListener('DOMContentLoaded', async () => {
  const scriptId = new URLSearchParams(location.search).get('script_id');
  if (scriptId) {
    try {
      await fetchScript(scriptId);
      toggle('btn-audio', true);
      toggle('btn-onestop', true);
      setStatus('status-audio', '脚本已加载 — 选段落和音色后生成', false, true);
      // 2026-08-20: 同步下拉选中, 与拆书讲书页进产线跳转联动
      try {
        await loadScriptList();
        const sel = document.getElementById('script-select');
        if (sel && [...sel.options].some(o => o.value === scriptId)) sel.value = scriptId;
      } catch (_) { /* 下拉不同步不阻塞 */ }
    } catch (e) {
      setStatus('status-audio', '加载脚本失败: ' + e.message, true);
    }
  }
  // PPT 书集上下文 (2026-08-21)
  _refreshPptBookCtx();
  // 恢复未完成 PPT 任务 (刷新后继续看进度, 不丢 job)
  // 优先 sessionStorage, 其次 URL 参数 ?ppt_job_id= (跨刷新/跨会话手工续看)
  try {
    const params = new URLSearchParams(location.search);
    const saved = sessionStorage.getItem('pptJobId') || params.get('ppt_job_id');
    if (saved) {
      _pptJobId = saved;
      const st = await (await fetch(API + `/ppt/${saved}/status`)).json();
      if (st && st.status === 'running') {
        _connectPPTSSE(saved);
        _pollPPT(saved);
      }
    }
  } catch (_) { /* 恢复失败不阻塞 */ }
});

// ── PPT 出片 (2026-08-20): 上传 → 解析 → 渲染 (有 PPT 走 PPT 产线, 无则现有) ──
// 2026-08-21: book_id/ep_index 绑定拆书系列 + 母本皮肤包
let _pptJobId = null;
let _pptES = null;

// 从 URL 取 book_id/ep_index (从拆书讲书页进产线带参)
function _pptBookCtx() {
  const p = new URLSearchParams(location.search);
  return { book_id: p.get('book_id') || '', ep_index: p.get('ep_index') || '' };
}

async function _refreshPptBookCtx() {
  const ctx = _pptBookCtx();
  const el = document.getElementById('ppt-bookctx');
  if (!el) return;
  if (!ctx.book_id) { el.textContent = ''; return; }
  let txt = `📖 书 ${ctx.book_id.slice(0, 8)}…` + (ctx.ep_index ? ` · 第${ctx.ep_index}集` : '');
  try {
    const r = await (await fetch(API + `/ppt/series-skin/${encodeURIComponent(ctx.book_id)}`)).json();
    if (r.has_master) txt += ` ｜ ✅ 已有母本(第${r.master_ep}集), 渲染自动对齐皮肤`;
  } catch (_) {}
  el.textContent = txt;
}

async function uploadPPT() {
  const file = document.getElementById('ppt-file').files[0];
  const status = document.getElementById('ppt-status');
  if (!file) { status.textContent = '请先选择 .pptx 文件'; return; }
  status.textContent = '上传解析中…';
  const ctx = _pptBookCtx();
  try {
    const fd = new FormData();
    fd.append('file', file);
    if (ctx.book_id) fd.append('book_id', ctx.book_id);
    if (ctx.ep_index) fd.append('ep_index', ctx.ep_index);
    // 2026-08-22: 前端选的音色传入 PPT 产线 (此前固定用书账号音色静姐)
    const voiceId = document.getElementById('voice-select').value;
    if (voiceId) fd.append('voice_id', voiceId);
    const resp = await fetch(API + '/ppt/upload', { method: 'POST', body: fd });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    const r = await resp.json();
    _pptJobId = r.job_id;
    try { sessionStorage.setItem('pptJobId', _pptJobId); } catch (_) {}
    const preview = (r.preview || []).map(p =>
      `P${p.index} [${p.notes_len}字] ${p.text_preview}`).join('\n');
    document.getElementById('ppt-preview').textContent = preview;
    document.getElementById('btn-ppt-render').disabled = false;
    // 母本按钮: 绑定了 book_id 且尚未有母本时显示
    const masterBtn = document.getElementById('btn-ppt-master');
    if (masterBtn) {
      if (ctx.book_id && ctx.ep_index && !r.has_master) {
        masterBtn.style.display = '';
        masterBtn.disabled = false;
      } else {
        masterBtn.style.display = 'none';
      }
    }
    let msg = `解析成功: ${r.slides} 页`;
    if (r.has_master) msg += ` · 已套用现成母本(第${r.master_ep}集)皮肤`;
    if (ctx.book_id && ctx.ep_index && !r.has_master) msg += ' · 可点「定为母本」';
    status.textContent = msg;
    document.getElementById('ppt-download').style.display = 'none';
  } catch (e) {
    status.textContent = '上传失败: ' + e.message;
  }
}

async function markMasterPPT() {
  if (!_pptJobId) return;
  const btn = document.getElementById('btn-ppt-master');
  const status = document.getElementById('ppt-status');
  btn.disabled = true; btn.textContent = '⏳ 抽取中…';
  try {
    const resp = await fetch(API + `/ppt/${_pptJobId}/mark-master`, { method: 'POST' });
    if (!resp.ok) { const e = await resp.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${resp.status}`); }
    const r = await resp.json();
    status.textContent = `✅ 已定为母本: 主色 ${r.color_tokens.join('/')} 字号档 ${r.fontsize_tokens.join('/')}`;
    btn.textContent = '✓ 已为母本';
    toast('母本皮肤包已生成', 'success');
    _refreshPptBookCtx();
  } catch (e) {
    status.textContent = '定为母本失败: ' + e.message;
    btn.disabled = false; btn.textContent = '📌 定为母本';
  }
}

async function renderPPT() {
  const status = document.getElementById('ppt-status');
  if (!_pptJobId) { status.textContent = '请先上传 PPT'; return; }
  const btn = document.getElementById('btn-ppt-render');
  btn.disabled = true; btn.textContent = '⏳ 成片中…';
  status.textContent = '开始 PPT 成片 (TTS → 渲染 → 拼片, 约 15-25 分钟)…';
  try {
    const resp = await fetch(API + `/ppt/${_pptJobId}/render`, { method: 'POST' });
    if (!resp.ok) { const e = await resp.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${resp.status}`); }
    _connectPPTSSE(_pptJobId);
    _pollPPT(_pptJobId);
  } catch (e) {
    status.textContent = '成片启动失败: ' + e.message;
    btn.disabled = false; btn.textContent = '🎬 PPT 一键成片';
  }
}

function _connectPPTSSE(jobId) {
  if (_pptES) _pptES.close();
  _pptES = new EventSource(API + `/ppt/${jobId}/events`);
  _pptES.onmessage = ev => {
    const d = JSON.parse(ev.data);
    if (d.type === 'ppt_done') { setStatus('ppt-status-ss', '成片完成 ✓', false, true); }
    if (d.type === 'ppt_error') { setStatus('ppt-status-ss', '成片失败: ' + (d.msg || ''), true); }
  };
  _pptES.onerror = () => _pptES.close();
}

async function _pollPPT(jobId) {
  const status = document.getElementById('ppt-status');
  const btn = document.getElementById('btn-ppt-render');
  try {
    const resp = await fetch(API + `/ppt/${jobId}/status`);
    const st = await resp.json();
    const ev = st.events || [];
    const bar = document.getElementById('ppt-progress');
    if (ev.length) status.textContent = ev[ev.length - 1].msg;
    // 进度条: 取最近带 progress 的事件 (TTS x/21 / 渲染 x/21)
    if (bar) {
      let prog = null;
      for (let i = ev.length - 1; i >= 0 && !prog; i--) if (ev[i].progress) prog = ev[i];
      if (prog && prog.progress && String(prog.progress).includes('/')) {
        const parts = String(prog.progress).split('/').map(Number);
        if (parts[1] > 0) { bar.value = parts[0] / parts[1]; bar.style.display = ''; }
      } else {
        bar.style.display = 'none';
      }
    }
    if (st.status === 'running') {
      setTimeout(() => _pollPPT(jobId), 3000);
    } else {
      if (bar) bar.style.display = 'none';
      if (st.status === 'failed' || st.error) {
        btn.disabled = false; btn.textContent = '🎬 PPT 一键成片';
        status.textContent = '失败: ' + (st.error || '');
      } else if (st.status === 'done') {
        btn.disabled = false; btn.textContent = '🎬 PPT 一键成片';
        const dl = document.getElementById('ppt-download');
        const jyBtn = document.getElementById('btn-ppt-jy');
        if (st.draft) {
          // jy2 元素级: 草稿已直接进剪映草稿箱, 隐藏下载/手动导出按钮
          status.textContent = '✅ 剪映草稿已生成: ' + st.draft.draft_name + ' — 打开剪映即可查看/导出';
          if (dl) dl.style.display = 'none';
          if (jyBtn) jyBtn.style.display = 'none';
          const draftEl = document.getElementById('ppt-draft-name');
          if (draftEl) draftEl.textContent = st.draft.draft_name;
        } else {
          dl.href = API + `/ppt/${jobId}/download`;
          dl.style.display = '';
          if (jyBtn) { jyBtn.style.display = ''; jyBtn.disabled = false; jyBtn.dataset.jobId = jobId; }
          status.textContent = '成片完成 ✓ 可下载或导出剪映草稿';
        }
      }
    }
  } catch (e) {
    status.textContent = '轮询失败: ' + e.message;
  }
}

// PPT 出片 → 剪映草稿 (J 线)
async function exportPPTJy() {
  const btn = document.getElementById('btn-ppt-jy');
  const jobId = btn && btn.dataset.jobId;
  const status = document.getElementById('ppt-status');
  if (!jobId) { status.textContent = '请先完成成片'; return; }
  btn.disabled = true; btn.textContent = '⏳ 导出中…';
  try {
    const resp = await fetch(API + `/ppt/${jobId}/export-jy-draft`, { method: 'POST' });
    if (!resp.ok) { const e = await resp.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${resp.status}`); }
    const r = await resp.json();
    status.textContent = `剪映草稿已导出 ✓ ${r.video_segments} 页画面 + ${r.text_segments} 条字幕 → ${r.draft_name}`;
    btn.disabled = false; btn.textContent = '🎬 导出剪映草稿';
    toast('剪映草稿已生成', 'success');
  } catch (e) {
    status.textContent = '导出失败: ' + e.message;
    btn.disabled = false; btn.textContent = '🎬 导出剪映草稿';
  }
}
