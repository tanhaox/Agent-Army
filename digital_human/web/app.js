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
  toggle('btn-rewrite', false);
  setStatus('status-rewrite', '洗稿中，请稍候...');
  try {
    const { job_id } = await api('POST', `/articles/${currentArticle.id}/rewrite`, {});
    const source = new EventSource(`${API}/jobs/${job_id}/events`);
    source.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
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

async function fetchScript(scriptId) {
  currentScript = await api('GET', `/scripts/${scriptId}`);
  document.getElementById('script-text').value = currentScript.script_text;
  renderProjectDir(currentScript.project_dir);
  renderSegments(currentScript.segments);
  loadVoices();
}

async function loadVoices() {
  try {
    const voices = await api('GET', '/voices');
    const select = document.getElementById('voice-select');
    select.innerHTML = '';
    voices.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.textContent = `${v.name} (${v.backend})`;
      select.appendChild(opt);
    });
  } catch (e) {
    console.error('加载音色失败', e);
  }
}

function renderProjectDir(projectDir) {
  let el = document.getElementById('project-dir');
  if (!el) {
    el = document.createElement('div');
    el.id = 'project-dir';
    el.className = 'project-dir';
    const step = document.querySelector('.step:nth-of-type(2)');
    step.insertBefore(el, document.getElementById('script-text'));
  }
  if (projectDir) {
    el.innerHTML = `<strong>项目目录：</strong><a href="file:///${projectDir}" target="_blank">${projectDir}</a>`;
  } else {
    el.innerHTML = '';
  }
}

async function saveScript() {
  if (!currentScript) return;
  const text = document.getElementById('script-text').value.trim();
  try {
    currentScript = await api('PUT', `/scripts/${currentScript.id}`, { script_text: text });
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
  const ordered = [...selected, ...segments.filter(s => !s.selected_for_host)];
  ordered.forEach((seg, idx) => {
    const div = document.createElement('div');
    div.className = 'segment ' + (seg.selected_for_host ? 'selected' : 'unselected');
    div.dataset.id = seg.id;
    const orderLabel = seg.selected_for_host ? String(idx + 1) : '-';
    div.innerHTML = `
      <div class="order">${orderLabel}</div>
      <input type="checkbox" ${seg.selected_for_host ? 'checked' : ''} onchange="toggleSegment('${seg.id}', this.checked)">
      <div class="text">${escapeHtml(seg.text)}</div>
      <div class="meta">${seg.segment_type || ''}</div>
      <div class="controls">
        <button class="small" onclick="moveSegment('${seg.id}', -1)" ${!seg.selected_for_host || idx === 0 ? 'disabled' : ''}>↑</button>
        <button class="small" onclick="moveSegment('${seg.id}', 1)" ${!seg.selected_for_host || idx === selected.length - 1 ? 'disabled' : ''}>↓</button>
      </div>
    `;
    container.appendChild(div);
  });
  updateDirectorCount();
}

function updateDirectorCount() {
  const container = document.getElementById('segments-list');
  const checked = container.querySelectorAll('input[type="checkbox"]:checked').length;
  document.getElementById('director-count').textContent = `已选 ${checked} 句`;
}

async function toggleSegment(segmentId, selected) {
  const seg = currentScript.segments.find(s => s.id === segmentId);
  if (!seg) return;
  seg.selected_for_host = selected;
  if (selected) {
    const maxOrder = Math.max(...currentScript.segments.filter(s => s.selected_for_host).map(s => s.host_order), -1);
    seg.host_order = maxOrder + 1;
  }
  renderSegments(currentScript.segments);
  document.getElementById('btn-save-director').disabled = false;
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
  document.getElementById('btn-save-director').disabled = false;
}

async function saveDirectorSelections() {
  const segs = currentScript.segments;
  const selected = segs.filter(s => s.selected_for_host).sort((a, b) => a.host_order - b.host_order);
  selected.forEach((s, i) => { s.host_order = i; });
  try {
    for (const seg of segs) {
      await api('PUT', `/segments/${seg.id}`, {
        selected_for_host: seg.selected_for_host,
        host_order: seg.host_order,
      });
    }
    document.getElementById('btn-save-director').disabled = true;
    setStatus('status-rewrite', '导演选择已保存', false, true);
  } catch (e) {
    setStatus('status-rewrite', e.message, true);
  }
}

async function generateAudio() {
  if (!currentScript) return;
  toggle('btn-audio', false);
  setStatus('status-audio', '生成音频中...');
  try {
    const voiceId = document.getElementById('voice-select').value;
    const query = voiceId ? `?voice_id=${encodeURIComponent(voiceId)}&selected_only=true` : '?selected_only=true';
    const job = await api('POST', `/audio/scripts/${currentScript.id}/generate-audio${query}`);
    setStatus('status-audio', `任务已创建: ${job.id}`);
    const container = document.getElementById('audio-list');
    container.innerHTML = '';
    const source = new EventSource(`${API}/jobs/${job.id}/events`);
    source.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.type === 'tts_progress') {
        setStatus('status-audio', `进度 ${data.completed}/${data.total}`);
        if (data.audio_file) {
          appendAudioItem(data.audio_file);
        }
      } else if (data.type === 'tts_done') {
        source.close();
        setStatus('status-audio', '音频生成完成', false, true);
        loadAudioFiles(job.id);
        toggle('btn-audio', true);
      } else if (data.type === 'tts_error') {
        source.close();
        setStatus('status-audio', data.error, true);
        toggle('btn-audio', true);
      }
    };
    source.onerror = () => {
      source.close();
      setStatus('status-audio', 'SSE 连接错误', true);
      toggle('btn-audio', true);
    };
  } catch (e) {
    setStatus('status-audio', e.message, true);
    toggle('btn-audio', true);
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

async function loadAudioFiles(jobId) {
  const files = await api('GET', `/audio/jobs/${jobId}/files`);
  const container = document.getElementById('audio-list');
  container.innerHTML = '';
  files.forEach(f => appendAudioItem(f));
}

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
