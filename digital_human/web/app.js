const API = '/api';
let currentArticle = null;
let currentScript = null;

function setStatus(id, text, isError = false, isSuccess = false) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = 'status' + (isError ? ' error' : '') + (isSuccess ? ' success' : '');
}

function toggle(id, enabled) {
  const el = document.getElementById(id);
  if (el) el.disabled = !enabled;
}

// P1-1 修复: 安全设置「保存导演选择」按钮可用态。
// index.html 无 #btn-save-director 元素, 原代码 5 处直接访问
// getElementById(...).disabled 每次调用都抛 TypeError, 挡住
// 段落勾选/音色下拉/音频任务恢复。统一走这里, 元素缺失时静默跳过。
function setSaveDirectorEnabled(enabled) {
  const el = document.getElementById('btn-save-director');
  if (el) el.disabled = !enabled;
}

async function api(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const resp = await fetch(API + path, opts);
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    throw new Error(data.detail || `HTTP ${resp.status}`);
  }
  return resp.json().catch(() => ({}));
}

async function fetchUrl() {
  const urlInput = document.getElementById('article-url');
  const url = urlInput.value.trim();
  if (!url) {
    setStatus('status-create', '请先输入 URL', true);
    return;
  }
  const btn = document.getElementById('btn-fetch-url');
  btn.disabled = true;
  setStatus('status-create', '正在抓取...');
  try {
    const result = await api('POST', '/articles/fetch-url', { url });
    if (!result.ok) {
      setStatus('status-create', result.error || '抓取失败', true);
      return;
    }
    if (result.title) document.getElementById('article-title').value = result.title;
    if (result.raw_text) document.getElementById('article-text').value = result.raw_text;
    setStatus('status-create', '已自动填入标题和正文', false, true);
  } catch (e) {
    setStatus('status-create', e.message, true);
  } finally {
    btn.disabled = false;
  }
}

async function createArticle() {
  const title = document.getElementById('article-title').value.trim();
  const sourceUrl = document.getElementById('article-url').value.trim();
  const rawText = document.getElementById('article-text').value.trim();
  if (!rawText) {
    setStatus('status-create', '请输入原文内容', true);
    return;
  }
  try {
    currentArticle = await api('POST', '/articles', { title, source_url: sourceUrl, raw_text: rawText });
    setStatus('status-create', `稿件已创建: ${currentArticle.id}`, false, true);
    toggle('btn-rewrite', true);
  } catch (e) {
    setStatus('status-create', e.message, true);
  }
}

async function loadLatest() {
  try {
    const list = await api('GET', '/articles?limit=1');
    if (!list.length) {
      setStatus('status-rewrite', '暂无稿件', true);
      return;
    }
    currentArticle = list[0];
    setStatus('status-rewrite', `已加载稿件: ${currentArticle.id}`, false, true);
    toggle('btn-rewrite', true);
  } catch (e) {
    setStatus('status-rewrite', e.message, true);
  }
}

async function rewriteArticle() {
  if (!currentArticle) return;
  const model = document.getElementById('rewrite-model').value;
  const template = document.getElementById('rewrite-template').value || 'laochen_default';
  const videoFormat = document.getElementById('rewrite-format').value || 'portrait';
  const hostSelect = document.getElementById('rewrite-host');
  const personaId = (hostSelect && hostSelect.value) || null;
  toggle('btn-rewrite', false);
  setStatus('status-rewrite', '洗稿中，请稍候...');
  try {
    const perspective = document.getElementById('perspective-1')?.value?.trim() || null;
    const { job_id } = await api('POST', `/articles/${currentArticle.id}/rewrite`, { model, prompt_template: template, video_format: videoFormat, perspective, persona_id: personaId });
    const source = new EventSource(`${API}/jobs/${job_id}/events`);
    source.onmessage = (ev) => {
      let data;
      try { data = JSON.parse(ev.data); } catch (_) { return; }  // P2-4: 坏数据不崩
      if (data.type === 'rewrite_chunk') {
        const ta = document.getElementById('script-text');
        ta.value += data.chunk;
        ta.scrollTop = ta.scrollHeight;
      } else if (data.type === 'rewrite_done') {
        source.close();
        setStatus('status-rewrite', '洗稿完成', false, true);
        document.getElementById('script-text').value = '';
        fetchScript(data.script_id);
        toggle('btn-save-script', true);
        toggle('btn-audio', true);
        toggle('btn-save-director', false);
        // 显示修正观点区域
        const p2section = document.getElementById('perspective-2-section');
        if (p2section) p2section.style.display = 'block';
      } else if (data.type === 'rewrite_error') {
        source.close();
        setStatus('status-rewrite', data.error, true);
      }
    };
    source.onerror = () => {
      source.close();
      setStatus('status-rewrite', 'SSE 连接错误', true);
    };
  } catch (e) {
    setStatus('status-rewrite', e.message, true);
    toggle('btn-rewrite', true);
  }
}

async function correctScript() {
  if (!currentScript) return;
  const perspective = document.getElementById('perspective-2')?.value?.trim();
  if (!perspective) {
    setStatus('status-correct', '请输入修正观点', true);
    return;
  }
  const model = document.getElementById('rewrite-model').value;
  toggle('btn-correct', false);
  setStatus('status-correct', '修正中，请稍候...');
  try {
    const { job_id } = await api('POST', `/scripts/${currentScript.id}/correct`, { perspective, model });
    const source = new EventSource(`${API}/jobs/${job_id}/events`);
    source.onmessage = (ev) => {
      let data;
      try { data = JSON.parse(ev.data); } catch (_) { return; }
      if (data.type === 'correct_chunk') {
        const ta = document.getElementById('script-text');
        ta.value += data.chunk;
        ta.scrollTop = ta.scrollHeight;
      } else if (data.type === 'correct_done') {
        source.close();
        setStatus('status-correct', '修正完成', false, true);
        document.getElementById('script-text').value = '';
        fetchScript(data.script_id);
        toggle('btn-correct', true);
        toggle('btn-save-script', true);
        toggle('btn-audio', true);
      } else if (data.type === 'correct_error') {
        source.close();
        setStatus('status-correct', data.error, true);
        toggle('btn-correct', true);
      }
    };
    source.onerror = () => {
      source.close();
      setStatus('status-correct', 'SSE 连接错误', true);
      toggle('btn-correct', true);
    };
  } catch (e) {
    setStatus('status-correct', e.message, true);
    toggle('btn-correct', true);
  }
}

// ── 启用的管线 (2026-08-07 从 director.html 迁到流水线页) ──
// 生成音频前定死 C/P/H 开关，存 localStorage，导演台 createJob/execute/retry 复用。
// key: 'dh_pipeline_flags'; value: {c,p,h: boolean} (缺省全开, 兼容旧行为)

function getPipelineFlags() {
  try {
    const raw = localStorage.getItem('dh_pipeline_flags');
    if (raw) return JSON.parse(raw);
  } catch (e) { /* 损坏则回退默认 */ }
  // 默认 C 线关 (2026-08-07): 数字人出镜默认不启用, 只跑 P/H 线
  return { c: false, p: true, h: true };
}

function savePipelineFlags() {
  localStorage.setItem('dh_pipeline_flags', JSON.stringify(getPipelineFlags()));
}

/** director.js 复用: 返回当前启用的管线数组 ['c','p','h'] 的子集 */
function getEnabledPipelines() {
  const flags = getPipelineFlags();
  const enabled = [];
  if (flags.c) enabled.push('c');
  if (flags.p) enabled.push('p');
  if (flags.h) enabled.push('h');
  return enabled;
}

/** 流水线页开关 onchange: 写回 localStorage */
function onPipelineToggle() {
  const f = getPipelineFlags();
  f.c = document.getElementById('toggle-c')?.checked ?? f.c;
  f.p = document.getElementById('toggle-p')?.checked ?? f.p;
  f.h = document.getElementById('toggle-h')?.checked ?? f.h;
  savePipelineFlags();
  const n = (f.c ? 1 : 0) + (f.p ? 1 : 0) + (f.h ? 1 : 0);
  const hint = document.getElementById('pipeline-hint');
  if (hint) {
    hint.textContent = n === 3 ? '⚠ 三条管线全开: 将启用数字人出镜 (C线), LLM 可能规划 host slot。若只要 P/H 请关闭 C线'
      : n === 0 ? '⚠ 全部关闭，将只跑兜底(本地素材/黑场)' : '';
  }
}

async function fetchScript(scriptId) {
  currentScript = await api('GET', `/scripts/${scriptId}`);
  // 优先显示爆品改造最终稿 (boosted_text), 无则显示洗稿原稿
  document.getElementById('script-text').value = currentScript.boosted_text || currentScript.script_text;
  renderProjectDir(currentScript.project_dir);
  renderSegments(currentScript.segments);
  loadVoices();
  // ID-019: 刷新/跳页返回后恢复音频任务状态（活跃任务重连 SSE + 最近已完成历史）
  restoreAudioJobs();
}

async function loadVoices() {
  const select = document.getElementById('voice-select');
  const previous = select.value;
  try {
    const voices = await api('GET', '/voices');
    select.innerHTML = '';
    const defaultOpt = document.createElement('option');
    defaultOpt.value = '';
    defaultOpt.textContent = voices.length ? '默认音色（跟随主持人）' : '默认音色（暂无已保存音色）';
    select.appendChild(defaultOpt);
    voices.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.textContent = `${v.name} (${v.backend})`;
      select.appendChild(opt);
    });
    // Preserve user's selection across reloads (e.g. fetchScript re-triggers).
    if (previous && [...select.options].some(o => o.value === previous)) {
      select.value = previous;
    }
  } catch (e) {
    console.error('加载音色失败', e);
    select.innerHTML = '<option value="">默认音色（音色列表加载失败）</option>';
  }
}

async function loadHosts() {
  const select = document.getElementById('rewrite-host');
  if (!select) return; // 非流水线页无此元素
  try {
    // 人物即账号 (2026-08-08): 下拉读 /personas, 选项值 = persona.id,
    // 洗稿 POST 带 persona_id, 后端从 persona→host 闭环取账号/品牌/开结尾。
    const personas = await api('GET', '/personas');
    select.innerHTML = '';
    if (!personas.length) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = '无人物（请先到「人物」页创建）';
      select.appendChild(opt);
      return;
    }
    // 默认选中绑定 laochen host 的人物（与后端 config 默认 host 一致），其次选第一条
    let defaultSelected = false;
    personas.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.brand_name ? `${p.name} · ${p.brand_name}` : `${p.name} · ${p.prompt_template}`;
      select.appendChild(opt);
      // 展示标记: 绑定 host 的优先 (带品牌即代表绑定了账号)
      if (!defaultSelected && p.brand_name) {
        opt.selected = true;
        defaultSelected = true;
      }
    });
    if (!defaultSelected && personas.length) select.selectedIndex = 0;
  } catch (e) {
    console.error('加载数字人失败', e);
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = '人物加载失败';
    select.appendChild(opt);
  }
}

async function loadPromptTemplates() {
  try {
    const templates = await api('GET', '/articles/prompt-templates');
    const select = document.getElementById('rewrite-template');
    select.innerHTML = '';
    if (!templates.length) {
      const opt = document.createElement('option');
      opt.value = 'laochen_default';
      opt.textContent = 'laochen_default';
      select.appendChild(opt);
      return;
    }
    templates.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.name;
      select.appendChild(opt);
    });
  } catch (e) {
    console.error('加载提示词模板失败', e);
    const select = document.getElementById('rewrite-template');
    select.innerHTML = '<option value="laochen_default">laochen_default</option>';
  }
}

function renderProjectDir(projectDir) {
  let el = document.getElementById('project-dir');
  if (!el) {
    el = document.createElement('div');
    el.id = 'project-dir';
    el.className = 'project-dir';
    // P1-2 修复: index.html 只有 .step-dot, 旧选择器 .step:nth-of-type(2)
    // 返回 null → insertBefore 崩溃挡住整个脚本加载。改为以
    // script-text 及其父卡片(#step-2-card)为锚点, 找不到时跳过渲染。
    const scriptText = document.getElementById('script-text');
    const anchor = scriptText ? scriptText.parentElement : document.querySelector('#step-2-card, .card');
    if (!anchor) {
      console.error('renderProjectDir: 未找到插入锚点, 跳过项目目录渲染');
      return;
    }
    anchor.insertBefore(el, scriptText);
  }
  if (projectDir) {
    el.innerHTML = `<strong>项目目录：</strong><span style="color:#94a3b8;word-break:break-all;">${projectDir}</span> <span style="font-size:0.75rem;color:#64748b;">(服务器本地路径，请直接在服务器查看)</span>`;
  } else {
    el.innerHTML = '';
  }
}

async function saveScript() {
  if (!currentScript) return;
  const text = document.getElementById('script-text').value.trim();
  try {
    // 编辑的是最终稿 (有 boosted_text) → 更新 boosted_text; 否则更新 script_text
    const payload = currentScript.boosted_text
      ? { boosted_text: text }
      : { script_text: text };
    currentScript = await api('PUT', `/scripts/${currentScript.id}`, payload);
    setStatus('status-rewrite', '脚本已保存并重新分段', false, true);
    renderSegments(currentScript.segments);
    toggle('btn-audio', true);
  } catch (e) {
    setStatus('status-rewrite', e.message, true);
  }
}

function renderSegments(segments) {
  const container = document.getElementById('segments-list');
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
  const checked = container.querySelectorAll('input[type="checkbox"]:checked').length;
  const totalDuration = Array.from(container.querySelectorAll('.segment.selected')).reduce((sum, el) => {
    const d = currentScript.segments.find(s => s.id === el.dataset.id);
    return sum + (d && d.estimated_duration ? d.estimated_duration : 0);
  }, 0);
  document.getElementById('director-count').textContent = `已选 ${checked} 句 / 约 ${totalDuration.toFixed(1)}s`;
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
      await api('PUT', `/segments/${seg.id}`, {
        selected_for_host: seg.selected_for_host,
      });
    }
    setSaveDirectorEnabled(true);
    setStatus('status-rewrite', '导演选择已保存', false, true);
  } catch (e) {
    setStatus('status-rewrite', e.message, true);
  }
}

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
    // 统一走公共 SSE 处理 (tts_service / tts_progress / tts_done / tts_error)
    connectAudioSSE(job.id);
  } catch (e) {
    setStatus('status-audio', e.message, true);
    toggle('btn-audio', true);
    toggle('btn-onestop', true);
  }
}

// ── 🚀 一键成片 (2026-08-09) ──
// 等价于依次点击「生成音频 → 创建并规划 → 执行 Slots → 合成视频」。
// 音频生成由本页完成; 之后三阶段(规划/执行/合成)在导演台 director.html 执行。
// 通过 localStorage 'dh_onestop' 标记自动模式, 导演台按 SSE 事件自动串联:
//   tts_done → 跳导演台(auto=1) → plan_done → executeJob → exec_done → composeJob → compose_done(结束)
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
        // 写入自动成片标记 + 跳转导演台 (auto=1 触发自动创建规划)
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
// 统一处理 tts_service / tts_progress / tts_done / tts_error 四类事件,
// generateAudio 与 restoreAudioJobs 共用, 避免重复实现。
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
    // 只在连接真正关闭时清理 (CLOSED=2), 不要在重连中 (CONNECTING=0) 误杀
    if (_audioSSE && _audioSSE.readyState === EventSource.CLOSED) {
      _audioSSE.close(); _audioSSE = null;
      setStatus('status-audio', 'SSE 连接错误', true);
      toggle('btn-audio', true);
    }
  };
}

// ── ID-019: 刷新/跳页返回后恢复音频任务状态 ──
// GET /api/audio/jobs?script_id= 列出该脚本全部任务:
//   - pending/running 活跃任务 → 重连 SSE 继续观察进度
//   - failed 任务 → 提示可续传 (P0-1 方案 1: 失败不删盘, 重试从断点继续)
//   - 最近 3 个 completed 任务 → 加载其历史音频文件
async function restoreAudioJobs() {
  if (!currentScript) return;
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
  const container = document.getElementById('audio-list');
  if (container) container.innerHTML = '';
  for (const job of completed) {
    await loadAudioFiles(job.id);
    // 多个已完成任务需防止 prependCombinedAudio 覆盖, 直接依次渲染即可
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
  // Remove previous combined audio if exists
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
  // Show combined audio (segment_id=null) first
  const combined = files.find(f => !f.segment_id);
  if (combined) {
    prependCombinedAudio(combined);
  }
  // Show per-segment files below
  files.filter(f => f.segment_id).forEach(f => appendAudioItem(f));
}

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── 流水线 → 视觉导演衔接: 音频完成后倒计时跳转, 携带 script/audio ID ──
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
  // 挂在 audio-list 外面, 避免被 loadAudioFiles 的 innerHTML='' 清掉
  container.parentNode.insertBefore(div, container);

  const go = () => {
    if (directorHandoffTimer) { clearInterval(directorHandoffTimer); directorHandoffTimer = null; }
    window.location.href = url;
  };
  document.getElementById('handoff-go').onclick = go;
  document.getElementById('handoff-stay').onclick = () => {
    if (directorHandoffTimer) { clearInterval(directorHandoffTimer); directorHandoffTimer = null; }
    // 保留入口, 去掉倒计时
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

// ---------------------------------------------------------------------------
// 人物关联锁定: 选定提示词模板后, 自动锁定音色和形象
// ---------------------------------------------------------------------------
let _personaLocked = false;

async function checkPersonaLock() {
  const template = document.getElementById('rewrite-template').value;
  const lockDiv = document.getElementById('persona-lock');
  const voiceSelect = document.getElementById('voice-select');
  if (!template || !lockDiv) return;

  try {
    const persona = await api('GET', `/personas/by-template/${encodeURIComponent(template)}`);
    if (persona && persona.voice_id) {
      // 锁定音色
      _personaLocked = true;
      voiceSelect.value = persona.voice_id;
      voiceSelect.disabled = true;
      const voiceName = persona.voice ? persona.voice.name : persona.voice_id;
      const roleName = persona.role ? persona.role.name : '未绑定';
      lockDiv.innerHTML = `🔒 人物「${persona.name}」已锁定 — 音色: ${voiceName} | 形象: ${roleName}`;
      lockDiv.style.display = 'block';
    } else {
      _personaLocked = false;
      voiceSelect.disabled = false;
      lockDiv.style.display = 'none';
    }
  } catch (e) {
    // 查询失败不影响流程
    _personaLocked = false;
    voiceSelect.disabled = false;
    lockDiv.style.display = 'none';
  }
}

// 绑定模板下拉框 change 事件
document.addEventListener('DOMContentLoaded', () => {
  // 恢复流水线页管线开关状态 (2026-08-07 从 director 迁入, 持久化到 localStorage)
  try {
    const flags = getPipelineFlags();
    const tc = document.getElementById('toggle-c');
    const tp = document.getElementById('toggle-p');
    const th = document.getElementById('toggle-h');
    if (tc) tc.checked = flags.c;
    if (tp) tp.checked = flags.p;
    if (th) th.checked = flags.h;
  } catch (e) { /* 无开关 DOM (非流水线页) 时忽略 */ }
  const tplSelect = document.getElementById('rewrite-template');
  if (tplSelect) tplSelect.addEventListener('change', checkPersonaLock);
  // 观点1 字数统计
  const p1 = document.getElementById('perspective-1');
  if (p1) p1.addEventListener('input', () => {
    const cnt = document.getElementById('perspective-1-count');
    if (cnt) cnt.textContent = p1.value.length;
  });
  // 观点2 字数统计
  const p2 = document.getElementById('perspective-2');
  if (p2) p2.addEventListener('input', () => {
    const cnt = document.getElementById('perspective-2-count');
    if (cnt) cnt.textContent = p2.value.length;
  });
});
