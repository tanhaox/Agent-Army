// 内容库页 (2026-08-20) — 输入补全 + 评论层 + 素材
// 依赖 books.js 共享 (api/esc/run/loadBook/toast). 渲染入口: renderPage(cur).

function renderPage(b) {
  const inp = b.input_json || {};
  const field = k => (inp[k] || {}).value || '';
  const tier = k => (inp[k] || {}).tier || '-';
  const needs = inp.needs_supplement || [];
  const prog = b.progress || { done: [false,false,false,false,false], current: 1 };
  const s1_ok = prog.done[0];         // 输入补全完成
  const has_roadmap = (b.episodes || []).length > 0;  // 总纲已生成 → 可进讲书
  const linkStory = document.getElementById('link-story');
  if (linkStory) linkStory.style.display = has_roadmap ? '' : 'none';

  $('#page-content').innerHTML = `
    <div class="panel">
      <h2>步骤1 · 输入补全 <span class="badge">tier: ${esc(tier('全书核心主张'))}</span></h2>
      <div class="kv"><span class="k">类型</span>${esc(field('书籍类型') || '-')}</div>
      <div class="kv"><span class="k">核心主张</span>${esc(field('全书核心主张') || '-')}</div>
      <div class="kv"><span class="k">概念</span>${esc((field('关键概念清单') || []).join(' / '))}</div>
      <div class="kv"><span class="k">金句</span>${esc((field('核心金句') || []).slice(0,2).join(' / '))}</div>
      <div class="kv"><span class="k">目标读者</span>${esc(field('目标读者画像') || '-')} ${(inp['目标读者画像']||{}).tier === 'persona' ? '<span class="badge">来自人设</span>' : ''}</div>
      ${needs.length ? `<div class="kv red"><span class="k">待补</span>${needs.join('、')}（点【补全输入】或人工补）</div>` : ''}
      <div class="toolbar" style="margin-top:0.8rem">
        <button class="sm" onclick="run('assess', this)">预评估 (Gate 0)</button>
        <button class="sm" style="${s1_ok ? '' : 'background:#16a34a'}" onclick="run('complete', this)">补全</button>
        <button class="sm warn" onclick="run('confirm-input', this)" ${s1_ok ? '' : 'disabled title="需先完成【补全】"'}>确认1 → 评论层+素材</button>
      </div>
      ${(() => { const r = (b.input_json || {}).risk_assessment; if (!r) return '';
        const icon = { green: '🟢', yellow: '🟡', red: '🔴' }[r.tier] || '❓';
        return `<div class="kv" style="margin-top:0.5rem">${icon} <b>${r.tier}</b>${r.abandon ? ' <span class="red">建议放弃</span>' : ''}
          ｜雷区: ${esc((r.risk_points || []).join(' / ')) || '-'}
          ｜安全操作: ${esc((r.min_safe_ops || []).slice(0, 3).join(' / ')) || '-'}</div>`; })()}
    </div>

    <div class="panel">
      <h2>步骤2 · 评论层 + 素材</h2>
      <div class="kv"><span class="k">评论层</span>${(inp.comment_layer || []).length} 条读者反应</div>
      <div class="kv"><span class="k">素材</span>${(inp.materials || []).length} 条</div>
      <div class="hint" style="margin-top:0.5rem">点【确认1】生成读者反应清单 + 素材包，供逐集创作戳痛点/制造共鸣。</div>
      ${(inp.comment_layer || []).length ? `
        <details style="margin-top:0.7rem"><summary style="cursor:pointer;font-size:0.85rem;color:#93c5fd">查看评论层内容</summary>
        <div style="margin-top:0.5rem">${(inp.comment_layer || []).map(c =>
          `<div class="kv" style="font-size:0.82rem">[${esc(c.type || '')}] ${esc(c.comment || '')}</div>`).join('')}</div></details>` : ''}
    </div>`;
}

function goStory(e) {
  e.preventDefault();
  if (BOOKS.cur) location.href = '/web/books_story.html?book_id=' + BOOKS.cur.id;
}

document.addEventListener('DOMContentLoaded', async () => {
  const id = new URLSearchParams(location.search).get('book_id');
  if (id) await loadBook(id);
  else $('#page-content').innerHTML = '<div class="hint">未指定书，从 <a href="/web/books.html">书库</a> 选择</div>';
});
