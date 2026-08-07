/* library.js — 视频库管理页(多维标签/编号/批量操作版) */
const API = '/api/library';
let currentTab = 'assets';
let editingId = null;
let _searchTimer = null;
let _dimensionOptions = {};
let _currentAssets = [];
let _selectedIds = new Set();
let _taggingJobId = null;
let _taggingSource = null;
let _taggingPollTimer = null;
const TAGGING_API = '/api/library/tagging';

const DIM_LABELS = {
  orientation: { portrait: '竖屏', landscape: '横屏' },
  source_type: { footage: '实拍', creative: '创意' },
  location: { domestic: '国内', foreign: '国外' },
  people: { people: '有人', none: '无人' },
  preference: { like: '喜欢', neutral: '中性', dislike: '厌恶' },
};

// ── Toast ──
function toast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => el.classList.remove('show'), 3500);
}

// ── Tab Switch ──
function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  document.getElementById('grid-assets').classList.toggle('hidden', tab !== 'assets');
  document.getElementById('grid-outputs').classList.toggle('hidden', tab !== 'outputs');
  document.getElementById('asset-filters').classList.toggle('hidden', tab !== 'assets');
  document.getElementById('batch-bar').classList.toggle('hidden', tab !== 'assets');
  loadCurrentTab();
}

function loadCurrentTab() {
  if (currentTab === 'assets') loadAssets();
  else loadOutputs();
}

// ── Search Debounce ──
function debounceSearch() {
  clearTimeout(_searchTimer);
  _searchTimer = setTimeout(() => loadCurrentTab(), 400);
}

function _multiSelectValues(id) {
  const opts = Array.from(document.getElementById(id).selectedOptions);
  return opts.map(o => o.value).filter(v => v);
}

// ── Load Assets ──
async function loadAssets() {
  const params = new URLSearchParams();
  const q = document.getElementById('search-input').value.trim();
  const orient = document.getElementById('filter-orientation').value;
  const sourceType = document.getElementById('filter-source_type').value;
  const location = document.getElementById('filter-location').value;
  const people = document.getElementById('filter-people').value;
  const preference = document.getElementById('filter-preference').value;
  const scenes = _multiSelectValues('filter-scenes').join(',');
  const shotTypes = _multiSelectValues('filter-shot_types').join(',');

  if (q) params.set('q', q);
  if (orient) params.set('orientation', orient);
  if (sourceType) params.set('source_type', sourceType);
  if (location) params.set('location', location);
  if (people) params.set('people', people);
  if (preference) params.set('preference', preference);
  if (scenes) params.set('scenes', scenes);
  if (shotTypes) params.set('shot_types', shotTypes);
  params.set('limit', '100');

  try {
    const r = await fetch(`${API}/assets?${params}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    _currentAssets = data.items || [];
    document.getElementById('result-count').textContent = `共 ${data.total} 条`;
    renderAssets(_currentAssets);
  } catch (e) { toast('加载失败: ' + e.message, 'error'); }
}

function renderAssets(items) {
  const grid = document.getElementById('grid-assets');
  const empty = document.getElementById('empty-state');
  if (!items.length) { grid.innerHTML = ''; empty.classList.remove('hidden'); return; }
  empty.classList.add('hidden');
  grid.innerHTML = items.map(a => {
    const orientLabel = DIM_LABELS.orientation[a.orientation] || a.orientation;
    const prefClass = a.preference === 'like' ? 'pref-like' : a.preference === 'dislike' ? 'pref-dislike' : '';
    const sourceLabel = DIM_LABELS.source_type[a.source_type] || a.source_type;
    const locationLabel = DIM_LABELS.location[a.location] || a.location;
    const peopleLabel = DIM_LABELS.people[a.people] || a.people;
    const desc = a.description_zh || a.description_en || a.raw_query || '—';
    const sceneTags = (a.scenes || []).map(t => `<span class="scene">${escHtml(t)}</span>`).join('');
    const shotTags = (a.shot_types || []).map(t => `<span class="shot">${escHtml(t)}</span>`).join('');
    const oldTags = (a.tags || []).slice(0, 4).map(t => `<span>${escHtml(t)}</span>`).join('');
    const selected = _selectedIds.has(a.id) ? 'checked' : '';
    return `
      <div class="video-card ${prefClass}" data-id="${a.id}">
        <label class="card-check"><input type="checkbox" ${selected} onchange="toggleSelect('${a.id}')"></label>
        <div class="thumb">
          <video src="${API}/assets/${a.id}/file" controls playsinline preload="metadata"></video>
          <div class="play-overlay"><div class="play-icon">▶</div></div>
          <span class="asset-no">${escHtml(a.asset_no)}</span>
          <span class="duration">${a.duration_sec?.toFixed(1) || '?'}s</span>
          <span class="orient-badge">${orientLabel}</span>
        </div>
        <div class="info">
          <div class="desc">${escHtml(desc)}</div>
          <div class="badges">
            <span class="badge source-${a.source_type}">${sourceLabel}</span>
            <span class="badge loc-${a.location}">${locationLabel}</span>
            <span class="badge people-${a.people}">${peopleLabel}</span>
            ${a.ai_tagged_at ? `<span class="badge ai-badge" title="AI 已打标: ${escHtml(a.ai_tag_model || '—')}">🤖 AI</span>` : ''}
          </div>
          <div class="meta">
            <span>${a.width}×${a.height}</span>
            ${a.photographer ? `<span>📷 ${escHtml(a.photographer)}</span>` : ''}
            <span>使用${a.used_count}次</span>
          </div>
          ${sceneTags || shotTags ? `<div class="tags dim-tags">${sceneTags}${shotTags}</div>` : ''}
          ${oldTags ? `<div class="tags">${oldTags}</div>` : ''}
        </div>
        <div class="actions">
          <button class="${a.preference === 'like' ? 'liked' : ''}" onclick="setPreference('${a.id}', 'like')">😍</button>
          <button class="${a.preference === 'neutral' ? 'active' : ''}" onclick="setPreference('${a.id}', 'neutral')">😐</button>
          <button class="${a.preference === 'dislike' ? 'disliked' : ''}" onclick="setPreference('${a.id}', 'dislike')">🚫</button>
          <button onclick="openEdit('${a.id}')">✏ 编辑</button>
          <button class="del" onclick="deleteAsset('${a.id}')">🗑</button>
        </div>
      </div>`;
  }).join('');
  updateBatchUI();
}

// ── Load Outputs ──
async function loadOutputs() {
  const params = new URLSearchParams();
  const q = document.getElementById('search-input').value.trim();
  const orient = document.getElementById('filter-orientation').value;
  if (q) params.set('q', q);
  if (orient) params.set('orientation', orient);
  params.set('limit', '100');

  try {
    const r = await fetch(`${API}/outputs?${params}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    document.getElementById('result-count').textContent = `共 ${data.total} 条`;
    renderOutputs(data.items);
  } catch (e) { toast('加载失败: ' + e.message, 'error'); }
}

function renderOutputs(items) {
  const grid = document.getElementById('grid-outputs');
  const empty = document.getElementById('empty-state');
  if (!items.length) { grid.innerHTML = ''; empty.classList.remove('hidden'); return; }
  empty.classList.add('hidden');
  grid.innerHTML = items.map(o => {
    const orientLabel = {portrait:'竖屏',landscape:'横屏',square:'方形'}[o.orientation] || o.orientation;
    return `
      <div class="video-card">
        <div class="thumb">
          <video src="${API}/outputs/${o.id}/file" controls playsinline preload="metadata"></video>
          <div class="play-overlay"><div class="play-icon">▶</div></div>
          <span class="duration">${o.duration_sec?.toFixed(1) || '?'}s</span>
          <span class="orient-badge">${orientLabel}</span>
        </div>
        <div class="info">
          <div class="desc">${escHtml(o.title)}</div>
          <div class="meta">
            <span>${formatDate(o.created_at)}</span>
            ${o.video_format ? `<span>${o.video_format}</span>` : ''}
          </div>
        </div>
        <div class="actions">
          <button class="del" onclick="deleteOutput('${o.id}')">🗑 删除</button>
        </div>
      </div>`;
  }).join('');
}

// ── Video play mutual exclusive + overlay ──
document.addEventListener('play', (e) => {
  const v = e.target;
  if (!v || v.tagName !== 'VIDEO') return;
  document.querySelectorAll('.video-card video').forEach(o => {
    if (o !== v && !o.paused) o.pause();
  });
  v.closest('.video-card')?.classList.add('playing');
}, true);
document.addEventListener('pause', (e) => {
  if (e.target && e.target.tagName === 'VIDEO') {
    e.target.closest('.video-card')?.classList.remove('playing');
  }
}, true);

// ── Actions ──
async function setPreference(id, pref) {
  try {
    const r = await fetch(`${API}/assets/${id}/preference`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preference: pref }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    loadAssets();
  } catch (e) { toast('操作失败', 'error'); }
}

async function deleteAsset(id) {
  if (!confirm('确认删除此素材？文件也会移入回收站。')) return;
  try {
    const r = await fetch(`${API}/assets/${id}?remove_file=true`, { method: 'DELETE' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast('已删除', 'success');
    loadAssets();
  } catch (e) { toast('删除失败', 'error'); }
}

async function deleteOutput(id) {
  if (!confirm('确认删除此成品？文件也会移入回收站。')) return;
  try {
    const r = await fetch(`${API}/outputs/${id}?remove_file=true`, { method: 'DELETE' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast('已删除', 'success');
    loadOutputs();
  } catch (e) { toast('删除失败', 'error'); }
}

// ── Batch Selection ──
function toggleSelect(id) {
  if (_selectedIds.has(id)) _selectedIds.delete(id);
  else _selectedIds.add(id);
  updateBatchUI();
}

function toggleSelectAll() {
  const checked = document.getElementById('select-all').checked;
  if (checked) _currentAssets.forEach(a => _selectedIds.add(a.id));
  else _currentAssets.forEach(a => _selectedIds.delete(a.id));
  renderAssets(_currentAssets);
}

function updateBatchUI() {
  document.getElementById('batch-count').textContent = `已选 ${_selectedIds.size}`;
  const allSelected = _currentAssets.length > 0 && _currentAssets.every(a => _selectedIds.has(a.id));
  document.getElementById('select-all').checked = allSelected;
}

async function batchUpdate(body, successMsg) {
  const ids = Array.from(_selectedIds);
  if (!ids.length) { toast('请先勾选素材', 'info'); return false; }
  try {
    await Promise.all(ids.map(id =>
      fetch(`${API}/assets/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }).then(r => { if (!r.ok) throw new Error(id); })
    ));
    toast(successMsg, 'success');
    _selectedIds.clear();
    loadAssets();
    return true;
  } catch (e) { toast('批量操作失败', 'error'); return false; }
}

async function batchSetPreference(pref) {
  await batchUpdate({ preference: pref }, `已批量设为${DIM_LABELS.preference[pref] || pref}`);
}

async function batchSetPeople(val) {
  await batchUpdate({ people: val }, `已批量设为${DIM_LABELS.people[val] || val}`);
}

async function batchAddScene() {
  const opts = (_dimensionOptions.scenes || []).map(s => `<option value="${escHtml(s)}">${escHtml(s)}</option>`).join('');
  openBatchModal('批量添加场景', `<select id="batch-value" size="8">${opts}</select>`, async () => {
    const v = document.getElementById('batch-value').value;
    if (!v) return;
    const ids = Array.from(_selectedIds);
    const updates = await Promise.all(ids.map(id => fetch(`${API}/assets/${id}`).then(r => r.json())));
    await Promise.all(updates.map(a => {
      const scenes = Array.from(new Set([...(a.scenes || []), v]));
      return fetch(`${API}/assets/${a.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenes }),
      });
    }));
    toast('已批量添加场景', 'success');
    closeBatchModal();
    _selectedIds.clear();
    loadAssets();
  });
}

async function batchAddShotType() {
  const opts = (_dimensionOptions.shot_types || []).map(s => `<option value="${escHtml(s)}">${escHtml(s)}</option>`).join('');
  openBatchModal('批量添加镜头', `<select id="batch-value" size="8">${opts}</select>`, async () => {
    const v = document.getElementById('batch-value').value;
    if (!v) return;
    const ids = Array.from(_selectedIds);
    const updates = await Promise.all(ids.map(id => fetch(`${API}/assets/${id}`).then(r => r.json())));
    await Promise.all(updates.map(a => {
      const shot_types = Array.from(new Set([...(a.shot_types || []), v]));
      return fetch(`${API}/assets/${a.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shot_types }),
      });
    }));
    toast('已批量添加镜头', 'success');
    closeBatchModal();
    _selectedIds.clear();
    loadAssets();
  });
}

async function batchDelete() {
  const ids = Array.from(_selectedIds);
  if (!ids.length) { toast('请先勾选素材', 'info'); return; }
  if (!confirm(`确认删除选中的 ${ids.length} 个素材？文件会移入回收站。`)) return;
  try {
    await Promise.all(ids.map(id => fetch(`${API}/assets/${id}?remove_file=true`, { method: 'DELETE' })));
    toast('已批量删除', 'success');
    _selectedIds.clear();
    loadAssets();
  } catch (e) { toast('批量删除失败', 'error'); }
}

// ── Scan Import ──
async function scanImport() {
  if (!confirm('扫描 materials 目录，导入未入库的视频文件？')) return;
  const btn = document.getElementById('scan-import-btn');
  btn.disabled = true;
  btn.textContent = '⏳ 扫描中...';
  try {
    const r = await fetch(`${API}/scan`, { method: 'POST' });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: r.statusText }));
      throw new Error(err.detail || `HTTP ${r.status}`);
    }
    const data = await r.json();
    toast(`扫描完成: 发现 ${data.scanned} 个视频, 导入 ${data.imported} 个, 跳过 ${data.skipped} 个`, 'success');
    loadAssets();
    loadTaggingCount();
  } catch (e) {
    toast('扫描失败: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '📥 扫描导入';
  }
}

// ── Edit Modal ──
function openEdit(id) {
  editingId = id;
  fetch(`${API}/assets/${id}`).then(r => {
    if (!r.ok) { toast('加载素材失败', 'error'); return null; }
    return r.json();
  }).then(a => {
    if (!a) return;
    document.getElementById('edit-desc-zh').value = a.description_zh || '';
    document.getElementById('edit-source_type').value = a.source_type || 'footage';
    document.getElementById('edit-location').value = a.location || 'foreign';
    document.getElementById('edit-people').value = a.people || 'none';
    document.getElementById('edit-scenes').value = (a.scenes || []).join(', ');
    document.getElementById('edit-shot_types').value = (a.shot_types || []).join(', ');
    document.getElementById('edit-tags').value = (a.tags || []).join(', ');
    document.getElementById('edit-modal').classList.remove('hidden');
  }).catch(() => toast('加载素材失败', 'error'));
}
function closeModal() { document.getElementById('edit-modal').classList.add('hidden'); editingId = null; }

async function saveEdit() {
  if (!editingId) return;
  const body = {
    description_zh: document.getElementById('edit-desc-zh').value || null,
    source_type: document.getElementById('edit-source_type').value,
    location: document.getElementById('edit-location').value,
    people: document.getElementById('edit-people').value,
    scenes: document.getElementById('edit-scenes').value.split(',').map(t => t.trim()).filter(Boolean),
    shot_types: document.getElementById('edit-shot_types').value.split(',').map(t => t.trim()).filter(Boolean),
    tags: document.getElementById('edit-tags').value.split(',').map(t => t.trim()).filter(Boolean),
  };
  try {
    const r = await fetch(`${API}/assets/${editingId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    toast('已保存', 'success');
    closeModal();
    loadAssets();
  } catch (e) { toast('保存失败', 'error'); }
}

// ── Batch Modal ──
function openBatchModal(title, html, onOk) {
  document.getElementById('batch-modal-title').textContent = title;
  document.getElementById('batch-modal-body').innerHTML = html;
  document.getElementById('batch-modal-ok').onclick = onOk;
  document.getElementById('batch-modal').classList.remove('hidden');
}
function closeBatchModal() { document.getElementById('batch-modal').classList.add('hidden'); }

// ── Dimensions / Categories ──
async function loadDimensions() {
  try {
    const r = await fetch(`${API}/dimensions`);
    if (!r.ok) return;
    _dimensionOptions = await r.json();
    fillSelect('filter-scenes', _dimensionOptions.scenes);
    fillSelect('filter-shot_types', _dimensionOptions.shot_types);
  } catch (_) {}
}

function fillSelect(id, items) {
  const sel = document.getElementById(id);
  sel.innerHTML = `<option value="">${id.includes('scenes') ? '场景' : '镜头'}</option>`;
  (items || []).forEach(c => {
    const o = document.createElement('option');
    o.value = c; o.textContent = c;
    sel.appendChild(o);
  });
}

// ── Utils ──
function escHtml(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function formatDate(ts) { if (!ts) return ''; try { return new Date(ts).toLocaleDateString('zh-CN'); } catch { return ts; } }

// ── AI Tagging ──
function setTaggingButtonStop() {
  const btn = document.getElementById('tagging-start-btn');
  btn.textContent = '⏹ 停止打标';
  btn.onclick = cancelTagging;
  btn.disabled = false;
  btn.title = '停止当前 AI 打标任务';
}

function resetTaggingButton() {
  const btn = document.getElementById('tagging-start-btn');
  btn.textContent = '🤖 AI 打标';
  btn.onclick = startTagging;
  btn.disabled = false;
  btn.title = '使用本地 AI 模型分析视频画面，自动生成多维标签';
}

async function startTagging() {
  const ids = Array.from(_selectedIds);
  const count = ids.length ? ids.length : '全部';
  const msg = ids.length
    ? `对选中的 ${ids.length} 个素材进行 AI 打标？`
    : `对所有未打标素材进行 AI 打标？(约需数分钟)`;

  if (!confirm(msg)) return;

  // 显示进度条
  const prog = document.getElementById('tagging-progress');
  prog.classList.remove('hidden');
  document.getElementById('tagging-status-text').textContent = '正在连接 AI 服务...';
  document.getElementById('tagging-progress-count').textContent = '—';
  document.getElementById('progress-fill').style.width = '0%';
  document.getElementById('tagging-current').textContent = '';
  document.getElementById('tagging-start-btn').disabled = true;

  try {
    const body = ids.length ? { asset_ids: ids } : {};
    const r = await fetch(`${TAGGING_API}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: r.statusText }));
      throw new Error(err.detail || `HTTP ${r.status}`);
    }
    const data = await r.json();
    _taggingJobId = data.job_id;
    renderTaggingProgress(data);
    setTaggingButtonStop();
    // 启动 SSE 监听
    connectTaggingSSE(data.job_id);
  } catch (e) {
    toast('AI 打标启动失败: ' + e.message, 'error');
    hideTaggingProgress();
    resetTaggingButton();
  }
}

function connectTaggingSSE(jobId) {
  if (_taggingSource) { _taggingSource.close(); }
  _taggingSource = new EventSource(`${TAGGING_API}/status/${jobId}/stream`);

  _taggingSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.type === 'heartbeat') return;
      renderTaggingProgress(data);
      if (data.type === 'complete') {
        toast(`AI 打标完成: ${data.done} 成功${data.failed ? `, ${data.failed} 失败` : ''}`, data.failed ? 'error' : 'success');
        finishTagging();
      } else if (data.type === 'failed') {
        toast('AI 打标任务失败: ' + (data.error || '未知错误'), 'error');
        finishTagging();
      } else if (data.type === 'cancelled') {
        toast('AI 打标已取消', 'info');
        finishTagging();
      }
    } catch (_) { /* ignore parse errors */ }
  };

  _taggingSource.onerror = () => {
    // SSE 断连，回退到轮询
    if (_taggingSource) { _taggingSource.close(); _taggingSource = null; }
    pollTaggingStatus(jobId);
  };
}

async function pollTaggingStatus(jobId) {
  try {
    const r = await fetch(`${TAGGING_API}/status/${jobId}`);
    if (!r.ok) { finishTagging(); return; }
    const data = await r.json();
    renderTaggingProgress(data);
    if (['completed', 'failed', 'cancelled'].includes(data.status)) {
      if (data.status === 'completed') {
        toast(`AI 打标完成: ${data.done} 成功${data.failed ? `, ${data.failed} 失败` : ''}`, data.failed ? 'error' : 'success');
      }
      finishTagging();
      return;
    }
    // 继续轮询
    _taggingSource = null; // clear SSE ref
    _taggingPollTimer = setTimeout(() => pollTaggingStatus(jobId), 2000);
  } catch (e) {
    finishTagging();
  }
}

function renderTaggingProgress(data) {
  document.getElementById('tagging-progress').classList.remove('hidden');

  // publish 事件用 "type", get_job_status 用 "status" — 归一化
  const state = data.status || data.type || '';
  const total = data.total || 0;
  const done = (data.done || 0) + (data.failed || 0);
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  document.getElementById('tagging-progress-count').textContent = `${done}/${total}`;
  document.getElementById('progress-fill').style.width = `${pct}%`;

  const statusText = document.getElementById('tagging-status-text');
  const currentEl = document.getElementById('tagging-current');

  if (state === 'completed' || state === 'complete') {
    statusText.textContent = `✅ 打标完成 — ${data.done || 0} 成功, ${data.failed || 0} 失败`;
    currentEl.textContent = '';
  } else if (state === 'failed') {
    statusText.textContent = `❌ 打标失败: ${data.error || ''}`;
    currentEl.textContent = '';
  } else if (state === 'cancelled') {
    statusText.textContent = '⏹ 已取消';
    currentEl.textContent = '';
  } else {
    statusText.textContent = '🤖 AI 打标进行中...';
    currentEl.textContent = data.current_asset_no ? `当前: ${data.current_asset_no}` : '';
  }
}

function hideTaggingProgress() {
  document.getElementById('tagging-progress').classList.add('hidden');
  resetTaggingButton();
}

function finishTagging() {
  _taggingJobId = null;
  if (_taggingSource) { _taggingSource.close(); _taggingSource = null; }
  if (_taggingPollTimer) { clearTimeout(_taggingPollTimer); _taggingPollTimer = null; }
  resetTaggingButton();
  loadTaggingCount();
  loadAssets();
  // 3 秒后自动隐藏进度条
  setTimeout(() => {
    if (!_taggingJobId) hideTaggingProgress();
  }, 5000);
}

async function cancelTagging() {
  if (!_taggingJobId) return;
  if (!confirm('确认取消 AI 打标任务？')) return;
  try {
    await fetch(`${TAGGING_API}/cancel/${_taggingJobId}`, { method: 'POST' });
  } catch (_) {}
  finishTagging();
  hideTaggingProgress();
}

async function loadTaggingCount() {
  try {
    const r = await fetch(`${TAGGING_API}/count`);
    if (!r.ok) return;
    const data = await r.json();
    document.getElementById('tagging-count').textContent =
      `AI: ${data.ai_tagged}/${data.total}`;
    document.getElementById('tagging-count').title =
      `AI 已打标 ${data.ai_tagged} / 共 ${data.total} 个素材`;
  } catch (_) {}
}

// ── Init ──
loadDimensions();
loadTaggingCount();
loadAssets();
