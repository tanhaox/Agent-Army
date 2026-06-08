import { useState } from 'react';
import { Plus, Pencil, X, ArrowUp, ArrowDown, ListOrdered } from 'lucide-react';
import type { DirectorAct, DirectorRole } from '../../services/scripts';

interface Props {
  acts: DirectorAct[];
  roles: DirectorRole[];
  onChange: (acts: DirectorAct[]) => void;
}

interface ActModalData {
  title: string;
  task: string;
  participants: string[];
}

export default function StepThreeForm({ acts, roles, onChange }: Props) {
  const [showModal, setShowModal] = useState(false);
  const [editIdx, setEditIdx] = useState(-1);
  const [modalData, setModalData] = useState<ActModalData>({ title: '', task: '', participants: [] });

  const inputCls = 'w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand';
  const labelCls = 'text-xs font-medium text-text-secondary';
  const badgeCls = 'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium';

  const saveAct = () => {
    if (!modalData.title.trim() || !modalData.task.trim()) return;
    const updated = [...acts];
    if (editIdx >= 0) {
      updated[editIdx] = { ...modalData, sort_order: editIdx };
    } else {
      updated.push({ ...modalData, sort_order: acts.length });
    }
    onChange(updated);
    setShowModal(false);
  };

  const deleteAct = (i: number) => onChange(acts.filter((_, j) => j !== i));

  const moveAct = (i: number, dir: -1 | 1) => {
    const t = i + dir;
    if (t < 0 || t >= acts.length) return;
    const updated = [...acts];
    [updated[i], updated[t]] = [updated[t], updated[i]];
    updated.forEach((a, j) => (a.sort_order = j));
    onChange(updated);
  };

  const openAdd = () => {
    setEditIdx(-1);
    const nextNum = acts.length + 1;
    const nums = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
    setModalData({ title: `第${nums[nextNum - 1] || nextNum}麦`, task: '', participants: [] });
    setShowModal(true);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className={`${labelCls} flex items-center gap-1`}><ListOrdered className="w-3.5 h-3.5" /> 麦序管理</label>
        <button onClick={openAdd} className="flex items-center gap-1 text-xs text-brand hover:text-brand-hover">
          <Plus className="w-3 h-3" /> 添加麦序
        </button>
      </div>

      {acts.length === 0 && (
        <p className="text-xs text-text-muted text-center py-4">还没有添加麦序，点击上方按钮开始编写剧情</p>
      )}

      {/* Timeline */}
      <div className="relative pl-4">
        {acts.map((a, i) => (
          <div key={i} className="relative pb-4 last:pb-0">
            {/* Vertical line */}
            {i < acts.length - 1 && <div className="absolute left-[3px] top-4 bottom-0 w-0.5 bg-border-default" />}
            {/* Dot */}
            <div className="absolute left-0 top-1.5 w-2 h-2 rounded-full bg-brand ring-2 ring-brand/20" />
            {/* Card */}
            <div className="ml-4 p-2.5 rounded-lg border border-border-default bg-bg-card hover:border-brand/30 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className="text-sm text-text-primary font-medium">{a.title}</span>
                  {a.participants.map((p, j) => (
                    <span key={j} className={`${badgeCls} bg-brand/10 text-brand`}>{p}</span>
                  ))}
                </div>
                <div className="flex items-center gap-0.5 shrink-0">
                  <button onClick={() => moveAct(i, -1)} disabled={i === 0} className="p-0.5 text-text-muted hover:text-text-primary disabled:opacity-30"><ArrowUp className="w-3 h-3" /></button>
                  <button onClick={() => moveAct(i, 1)} disabled={i === acts.length - 1} className="p-0.5 text-text-muted hover:text-text-primary disabled:opacity-30"><ArrowDown className="w-3 h-3" /></button>
                  <button onClick={() => { setEditIdx(i); setModalData({ title: a.title, task: a.task, participants: [...a.participants] }); setShowModal(true); }} className="p-0.5 text-text-muted hover:text-brand"><Pencil className="w-3 h-3" /></button>
                  <button onClick={() => deleteAct(i)} className="p-0.5 text-text-muted hover:text-error"><X className="w-3 h-3" /></button>
                </div>
              </div>
              <p className="text-[10px] text-text-muted mt-1">{a.task.slice(0, 80)}{a.task.length > 80 ? '...' : ''}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Act Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowModal(false)}>
          <div className="bg-bg-card rounded-xl shadow-2xl w-[400px] max-h-[80vh] overflow-y-auto p-5 space-y-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-base font-semibold text-text-primary">{editIdx >= 0 ? '编辑麦序' : '添加麦序'}</h3>
            <div className="space-y-1">
              <label className={labelCls}>麦序标题 *</label>
              <input value={modalData.title} onChange={(e) => setModalData({ ...modalData, title: e.target.value })} placeholder="如：第一麦" className={inputCls} />
            </div>
            <div className="space-y-1">
              <label className={labelCls}>出场角色</label>
              <div className="flex flex-wrap gap-1.5">
                {roles.map((r, ri) => {
                  const selected = modalData.participants.includes(r.name);
                  return (
                    <button key={ri} type="button" onClick={() => {
                      const ps = selected ? modalData.participants.filter((p) => p !== r.name) : [...modalData.participants, r.name];
                      setModalData({ ...modalData, participants: ps });
                    }} className={`${badgeCls} border transition-colors ${selected ? 'bg-brand/15 text-brand border-brand/30' : 'bg-bg-sidebar text-text-secondary border-border-default hover:border-brand'}`}>
                      {r.name}
                    </button>
                  );
                })}
                {roles.length === 0 && <p className="text-[10px] text-text-muted">请先在步骤二添加角色</p>}
              </div>
            </div>
            <div className="space-y-1">
              <label className={labelCls}>剧情任务/梗概 *</label>
              <textarea value={modalData.task} onChange={(e) => setModalData({ ...modalData, task: e.target.value })} placeholder="如：两人交流等待亲子鉴定结果..." rows={4} className={`${inputCls} resize-none`} />
            </div>
            <div className="flex gap-2 pt-2">
              <button onClick={() => setShowModal(false)} className="flex-1 py-2 rounded-md text-sm border border-border-default text-text-secondary hover:bg-bg-hover">取消</button>
              <button onClick={saveAct} disabled={!modalData.title.trim() || !modalData.task.trim()} className="flex-1 py-2 rounded-md text-sm bg-brand text-white hover:bg-brand-hover disabled:opacity-40">保存</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
