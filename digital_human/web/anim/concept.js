// ── 立意人闸面板: 立意.md 只读展示 / 结构化编辑 / 保存与单场重掷 ──
import { $, esc, scenesReady } from './util.js';
import { api, fileUrl } from './api.js';
import { media } from './context.js';

let roAbort = null;   // 只读区请求中止器: 重渲染竞态时丢弃过期响应 (原实现无中止, 旧响应可能后到覆盖)
let editData = null;  // 编辑器结构化数据缓存 (保存/重掷后失效)

/** store 订阅者: 面板显隐 + 只读内容 + 场下拉 */
export function conceptView(state) {
  const st = state.st;
  const ready = scenesReady(st) && !st?.running_job;
  const panel = $('#concept-panel');
  panel.hidden = !ready;
  if (!ready) return;
  loadReadOnly();
  $('#concept-arc').innerHTML = (st.arcs || [])
    .map(a => `<option value="${esc(a.arc_id)}">${esc(a.arc_id)}</option>`).join('');
}

async function loadReadOnly() {
  roAbort?.abort();
  roAbort = new AbortController();
  const ro = $('#concept-ro');
  try {
    const r = await fetch(fileUrl('立意.md', media.ver), { signal: roAbort.signal });
    ro.textContent = r.ok
      ? (await r.text() || '(立意.md 为空 — 点✏️编辑直建)')
      : '(立意.md 读取失败 — 点✏️编辑)';
  } catch (e) {
    if (e.name !== 'AbortError') ro.textContent = '(立意.md 读取失败 — 点✏️编辑)';
  }
}

/** 编辑/只读切换 (懒加载结构化数据) */
export async function toggleConceptEdit() {
  const ed = $('#concept-edit'), ro = $('#concept-ro'), sb = $('#concept-save-btn');
  if (ed.hidden) {
    if (!editData) {
      editData = await api('/concept');
      ed.innerHTML = renderConceptEdit(editData);
    }
    ed.hidden = false; ro.hidden = true; sb.hidden = false;
  } else {
    ed.hidden = true; ro.hidden = false; sb.hidden = true;
  }
}

const MULTI = /mappings|carrier|motifs|banned/;   // 多行字段 (每行一条)

function field(label, id, val, ph) {
  const rows = MULTI.test(id) ? 3 : 1;
  const v = esc(Array.isArray(val) ? val.join('\n') : (val || ''));
  return `<label class="cf"><span>${label}</span>
    <textarea data-k="${id}" rows="${rows}" placeholder="${ph || (MULTI.test(id) ? '每行一条' : '')}">${v}</textarea></label>`;
}

/** 结构化编辑器: 每场一个 details, 字段名即后端 concept-save 契约 */
export function renderConceptEdit(d) {
  return (d.scenes || []).map(s => `
    <details class="cf-scene" data-arc="${esc(s.arc_id)}">
      <summary>${esc(s.arc_id)} · <span class="cf-sum">${esc((s.metaphor_core || s.narrative || '').slice(0, 44))}</span></summary>
      <div class="cf-body">
        ${field('这场讲什么', 'narrative', s.narrative)}
        ${field('核心映射 (A=B) — 改掉旧值会自动进禁用史', 'metaphor_core', s.metaphor_core)}
        ${field('分映射 (每行 x=y)', 'metaphor_mappings', s.metaphor_mappings)}
        ${field('口播承载句 (每行一句)', 'carrier_lines', s.carrier_lines)}
        ${field('画面母题 (每行一个可画画面)', 'visual_motifs', s.visual_motifs)}
        ${field('运动线', 'motion', s.motion)}
        ${field('人批注 (写给导演, 全链可见)', 'concept_notes', s.concept_notes)}
        <button class="sm gold" data-act="conceptSaveOne" data-arc="${esc(s.arc_id)}">💾 只保存 ${esc(s.arc_id)}</button>
      </div></details>`).join('')
    + `<div class="cf-ep"><span>本集策略 (整案)</span>
       <input data-ep="1" data-k="ep_summary" value="${esc(d.ep_summary || '')}"></div>`;
}

/** 从 DOM 收集一场编辑结果 (多行字段拆行为数组) */
export function collectScene(card) {
  const sc = { arc_id: card.dataset.arc };
  card.querySelectorAll('[data-k]').forEach(el => {
    sc[el.dataset.k] = MULTI.test(el.dataset.k)
      ? el.value.split('\n').map(x => x.trim()).filter(Boolean)
      : el.value.trim();
  });
  return sc;
}

/**
 * 保存立意。查询统一圈定在 #concept-edit 内 — 页面将来出现同名结构也不串数据。
 * @param {Element|null} scope 传 details 元素 = 单场保存; null = 整案保存
 */
export async function saveConcept(scope) {
  let body;
  if (scope) {
    body = { scenes: [collectScene(scope)], ep_summary: null };
  } else {
    const host = $('#concept-edit');
    const scenes = [...host.querySelectorAll('details[data-arc]')].map(collectScene);
    const epEl = host.querySelector('[data-ep]');
    body = { scenes, ep_summary: epEl ? epEl.value.trim() : null };
  }
  await api('/concept-save', body);
  invalidateConcept();
}

/** 编辑缓存失效 (下次进编辑重新拉取) */
export function invalidateConcept() { editData = null; }

/** 保存/重掷后回到只读态并刷新内容 (替代原 location.reload 全页刷新) */
export function resetConceptPanel() {
  invalidateConcept();
  $('#concept-edit').hidden = true;
  $('#concept-ro').hidden = false;
  $('#concept-save-btn').hidden = true;
}
