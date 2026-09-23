// ── 装配入口: 建 store → 挂视图 → 接动作 → 全局错误边界 → 首次加载 ──
// 模块全部用 ES Module, 不向 window 挂任何东西 (原页面 ~40 个全局函数/变量)。
import { $ } from './util.js';
import { api } from './api.js';
import { media } from './context.js';
import { createStore } from './store.js';
import { initDialog, toast, createDisposer } from './ui.js';
import { createJobRunner } from './job.js';
import { topbarView } from './topbar.js';
import { boardView } from './board.js';
import { conceptView } from './concept.js';
import { wireActions } from './actions.js';
import { initCart } from './cart.js';

// 0923 用户令: confirm 遮全屏 → 右下角迷你条 (在模块加载时覆写, 保证先于所有按钮动作)
window.confirm = function(msg) {
  const el = document.createElement('div');
  el.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:99999;background:#1a1714;border:1px solid #d2a85e;border-radius:8px;padding:10px 14px;max-width:340px;color:#ece5d8;font-size:.8rem;box-shadow:0 4px 20px rgba(0,0,0,.6)';
  const first = String(msg || '').split('\n')[0].slice(0, 42);
  el.innerHTML = '<div style="color:#e6c078;font-weight:600;margin-bottom:4px">' + first + '</div>'
    + '<div style="display:flex;gap:8px"><span style="color:#6f665a;font-size:.68rem;align-self:center">已执行</span></div>';
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
  return true;  // 同步 API 只能立即放行; 取消靠任务面板 ⛔ 按钮
};

// h3Retry 入 store: 按钮态/请求体都读 store, 不再回读 DOM (单向数据流)
const store = createStore({ st: null, h3Retry: false });

/** 任务终点: 刷媒体版本 (防旧图, 见 context.media) → 重拉状态 */
const runner = createJobRunner({
  fetchJob: async id => {
    const r = await fetch('/api/anim/job/' + id);
    if (!r.ok) throw new Error('job ' + r.status);
    return r.json();
  },
  cancelJob: id =>
    fetch('/api/anim/job/' + id + '/cancel', { method: 'POST' }).then(r => r.json()),
  onFinished: () => { media.bump(); refresh(); },
});

/** 刷新整页状态 (唯一的状态入口) */
export async function refresh() {
  try {
    const st = await api('/status');
    store.set({ st });
    if (st.running_job) runner.attach(st.running_job);   // 刷新时任务仍在跑 → 重挂面板
  } catch (e) {
    $('#sub').textContent = '加载失败: ' + e.message;
  }
}

// 单向数据流: refresh → store.set → 三个视图各自投影 (订阅者异常互不拖累)
store.subscribe(state => {
  topbarView(state);
  boardView(state);
  conceptView(state);
});

initDialog();
wireActions({ store, runner, refresh });
// 购物篮装配在后: 其订阅须晚于 boardView (板重渲染后回画勾选态)
initCart({ store });

// 页面级资源回收站: 输入监听 + 页面隐藏时的通道拆除
const pageDeps = createDisposer();
pageDeps.on($('#h3-retry'), 'change', e => store.set({ h3Retry: e.target.checked }));
pageDeps.on(window, 'pagehide', () => { pageDeps.dispose(); runner.detach(); }, { once: true });
pageDeps.on(window, 'pageshow', () => refresh());   // bfcache 返回: 重挂任务通道

// 全局错误边界: 未捕获异常给用户可见反馈, 不白屏不静默
window.addEventListener('error', e => toast('脚本错误: ' + e.message, true));
window.addEventListener('unhandledrejection', e =>
  toast('请求异常: ' + (e.reason?.message || e.reason), true));

refresh();
