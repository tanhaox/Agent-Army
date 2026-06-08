import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, Pencil, X, ExternalLink } from 'lucide-react';
import { listPersonas } from '../../services/persona';
import type { DirectorRole } from '../../services/scripts';

interface Props {
  roles: DirectorRole[];
  onChange: (roles: DirectorRole[]) => void;
  anchorFollowerCount?: number;
}

const PERSPECTIVE_OPTIONS = [
  { value: 'first_person_experience', label: '我亲身经历的事' },
  { value: 'first_person_participant', label: '我参与的事' },
  { value: 'third_person', label: '客观讲述' },
];

interface RoleModalData {
  name: string;
  role_type: 'caller' | 'extra';
  function: string;
  storyline: string;
  perspective: string;
}

const EMPTY_GUEST: RoleModalData = { name: '', role_type: 'caller', function: '', storyline: '', perspective: '' };

export default function StepTwoForm({ roles, onChange, anchorFollowerCount }: Props) {
  const [showModal, setShowModal] = useState(false);
  const [editIdx, setEditIdx] = useState(-1);
  const [modalData, setModalData] = useState<RoleModalData>({ ...EMPTY_GUEST });
  const [show2ndMic, setShow2ndMic] = useState(false);

  const { data: personasData } = useQuery({ queryKey: ['personas'], queryFn: () => listPersonas(0, 50) });
  const personas = personasData?.items || [];

  const anchors = roles.filter((r) => r.role_type === 'anchor');
  const guests = roles.filter((r) => r.role_type !== 'anchor');
  const primaryAnchor = anchors[0];
  const secondaryAnchor = anchors[1];

  const inputCls = 'w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand';
  const labelCls = 'text-xs font-medium text-text-secondary';

  const updateAnchor = (index: number, field: string, value: string) => {
    const updated = [...roles];
    if (index < anchors.length) {
      const realIdx = roles.indexOf(anchors[index]);
      updated[realIdx] = { ...updated[realIdx], [field]: value };
    }
    onChange(updated);
  };

  const setAnchorPersona = (index: number, personaId: string) => {
    const updated = [...roles];
    if (index === 0 && anchors.length === 0) {
      updated.unshift({ role_type: 'anchor', name: '', position: '主唛', function: '主持控场', persona_id: personaId, sort_order: 0 });
    } else if (index < anchors.length) {
      const realIdx = roles.indexOf(anchors[index]);
      const persona = personas.find((p) => p.id === personaId);
      updated[realIdx] = { ...updated[realIdx], persona_id: personaId, name: persona?.name || updated[realIdx].name };
    }
    onChange(updated);
  };

  const saveGuest = () => {
    if (!modalData.name.trim()) return;
    const updated = [...roles];
    const role: DirectorRole = {
      role_type: modalData.role_type,
      name: modalData.name,
      function: modalData.function || undefined,
      storyline: modalData.storyline || undefined,
      perspective: modalData.perspective || undefined,
      sort_order: 0,
    };
    if (editIdx >= 0) {
      const realIdx = roles.indexOf(guests[editIdx]);
      updated[realIdx] = role;
    } else {
      role.sort_order = roles.length;
      updated.push(role);
    }
    onChange(updated);
    setShowModal(false);
  };

  const deleteGuest = (gi: number) => {
    if (gi < 0 || gi >= guests.length) return;
    const realIdx = roles.indexOf(guests[gi]);
    if (realIdx >= 0) onChange(roles.filter((_, i) => i !== realIdx));
  };

  return (
    <div className="space-y-5">
      {/* Primary Anchor */}
      <div className="space-y-2">
        <label className={labelCls}>主唛（AI仿生主播）</label>
        <select value={primaryAnchor?.persona_id || ''} onChange={(e) => setAnchorPersona(0, e.target.value)} className={inputCls}>
          <option value="">选择主播人设...</option>
          {personas.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        {primaryAnchor?.persona_id && (
          <div className="flex items-center gap-2 p-2 rounded-md border border-brand/30 bg-brand/5">
            <div className="w-8 h-8 rounded-full bg-brand/20 flex items-center justify-center text-brand text-xs font-bold">
              {(primaryAnchor.name || '?')[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-text-primary font-medium truncate">{primaryAnchor.name}</p>
              <p className="text-[10px] text-text-muted truncate">{primaryAnchor.position} · {primaryAnchor.function}</p>
            </div>
          </div>
        )}
        <a href="/personas?tab=ai-generate" target="_blank" className="inline-flex items-center gap-1 text-xs text-brand hover:underline">
          <ExternalLink className="w-3 h-3" /> 新建人设
        </a>
      </div>

      {/* Secondary mic */}
      <div className="space-y-2">
        {!show2ndMic && !secondaryAnchor ? (
          <button onClick={() => {
            setShow2ndMic(true);
            const updated = [...roles];
            updated.push({ role_type: 'anchor', name: '', position: '2唛', function: '', persona_id: '', sort_order: roles.length });
            onChange(updated);
          }} className="text-xs text-brand hover:underline">+ 添加2唛</button>
        ) : (
          <>
            <label className={labelCls}>2唛（可选）</label>
            <select value={secondaryAnchor?.persona_id || ''} onChange={(e) => setAnchorPersona(1, e.target.value)} className={inputCls}>
              <option value="">选择2唛人设...</option>
              {personas.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </>
        )}
      </div>

      <div className="h-px bg-border-default" />

      {/* Guests */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className={labelCls}>连线人 / 群演</label>
          <button onClick={() => { setEditIdx(-1); setModalData({ ...EMPTY_GUEST }); setShowModal(true); }}
            className="flex items-center gap-1 text-xs text-brand hover:text-brand-hover">
            <Plus className="w-3 h-3" /> 添加角色
          </button>
        </div>
        {guests.length === 0 && (
          <p className="text-xs text-text-muted text-center py-4">还没有添加角色，点击上方按钮添加</p>
        )}
        {guests.map((g, gi) => (
          <div key={gi} className="flex items-center gap-2 p-2 rounded-md border border-border-default hover:border-brand/30 transition-colors">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
              g.role_type === 'caller' ? 'bg-green-500/15 text-green-600' : 'bg-gray-500/15 text-gray-500'
            }`}>
              {g.name[0]}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-sm text-text-primary font-medium">{g.name}</span>
                <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  g.role_type === 'caller' ? 'bg-green-500/15 text-green-600' : 'bg-gray-500/15 text-gray-500'
                }`}>
                  {g.role_type === 'caller' ? '连线人' : '群演'}
                </span>
              </div>
              {g.function && <p className="text-[10px] text-text-muted truncate">{g.function}</p>}
            </div>
            <button onClick={() => {
              setEditIdx(gi);
              setModalData({ name: g.name, role_type: g.role_type as 'caller' | 'extra', function: g.function || '', storyline: g.storyline || '', perspective: g.perspective || '' });
              setShowModal(true);
            }} className="p-1 text-text-muted hover:text-brand"><Pencil className="w-3 h-3" /></button>
            <button onClick={() => deleteGuest(gi)} className="p-1 text-text-muted hover:text-error"><X className="w-3 h-3" /></button>
          </div>
        ))}
      </div>

      {/* Guest Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowModal(false)}>
          <div className="bg-bg-card rounded-xl shadow-2xl w-[400px] max-h-[80vh] overflow-y-auto p-5 space-y-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-base font-semibold text-text-primary">{editIdx >= 0 ? '编辑角色' : '添加角色'}</h3>
            <div className="space-y-1">
              <label className={labelCls}>角色名 *</label>
              <input value={modalData.name} onChange={(e) => setModalData({ ...modalData, name: e.target.value })} placeholder="如：周华强" className={inputCls} />
            </div>
            <div className="space-y-1">
              <label className={labelCls}>角色类型</label>
              <select value={modalData.role_type} onChange={(e) => setModalData({ ...modalData, role_type: e.target.value as 'caller' | 'extra' })} className={inputCls}>
                <option value="caller">连线人</option>
                <option value="extra">群演</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className={labelCls}>身份描述</label>
              <input value={modalData.function} onChange={(e) => setModalData({ ...modalData, function: e.target.value })} placeholder="如：公安队长，周华强好友" className={inputCls} />
            </div>
            <div className="space-y-1">
              <label className={labelCls}>核心问题/故事线</label>
              <textarea value={modalData.storyline} onChange={(e) => setModalData({ ...modalData, storyline: e.target.value })} placeholder="角色的故事背景和动机..." rows={3} className={`${inputCls} resize-none`} />
            </div>
            <div className="space-y-1">
              <label className={labelCls}>叙事视角</label>
              <div className="space-y-1">
                {PERSPECTIVE_OPTIONS.map((p) => (
                  <label key={p.value} className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-bg-hover cursor-pointer">
                    <input type="radio" name="perspective" checked={modalData.perspective === p.value} onChange={() => setModalData({ ...modalData, perspective: p.value })} className="w-3.5 h-3.5 text-brand" />
                    <span className="text-sm text-text-primary">{p.label}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <button onClick={() => setShowModal(false)} className="flex-1 py-2 rounded-md text-sm border border-border-default text-text-secondary hover:bg-bg-hover">取消</button>
              <button onClick={saveGuest} disabled={!modalData.name.trim()} className="flex-1 py-2 rounded-md text-sm bg-brand text-white hover:bg-brand-hover disabled:opacity-40">保存</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
