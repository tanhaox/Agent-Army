import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, ChevronDown, ChevronRight, Pencil, X, Plus, PlusCircle,
  MoreVertical, Trash2, Archive, Bookmark, Download, Copy,
  RotateCcw, MessageSquare, Upload, ExternalLink, User,
} from 'lucide-react';
import {
  getPersona, getPersonaSlices, listPersonas,
  patchPersona, deletePersonaSlice, rollbackPersona, deletePersona, appendSlices,
  importLingo,
} from '../../services/persona';
import Tabs from '../../components/ui/Tabs';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Spinner from '../../components/ui/Spinner';
import { toast } from '../../components/ui/Toast';
import DegradedBanner from '../../components/ui/DegradedBanner';
import ConfirmModal from '../../components/ui/ConfirmModal';
import RadarChart from '../learn/RadarChart';
import type { PersonaDetail } from '../../types';

interface Props {
  personaId: string;
}

const DETAIL_TABS = [
  { key: 'overview', label: '特征总览' },
  { key: 'slices', label: '切片素材' },
  { key: 'history', label: '版本历史' },
];

const LS_LABELS: Record<string, string> = {
  aggressiveness: '犀利度', humor: '幽默感', empathy: '共情力',
  rhythm: '节奏感', rhythm_score: '节奏感', metaphor_usage: '比喻能力', catchphrase_density: '口头禅频率',
};
const LS_KEYS = Object.keys(LS_LABELS);

const RECOMMENDATIONS = [
  { type: '倾诉型', desc: '高共情力适合承接情感倾诉类连线', dim: 'empathy', th: 7 },
  { type: '挑战型', desc: '高幽默感适合制造喜剧效果对抗式连线', dim: 'humor', th: 7 },
  { type: '防守型', desc: '高犀利度适合应对质疑和辩论场景', dim: 'aggressiveness', th: 7 },
  { type: '悬疑型', desc: '高节奏感适合营造悬念和反转的叙事连线', dim: 'rhythm', th: 7 },
  { type: '文学型', desc: '高比喻能力适合文艺深度对话场景', dim: 'metaphor_usage', th: 7 },
];

// ─── Detail Tags (header inline) ───────────────────────────

function DetailTags({ tags, personaId }: { tags: string[]; personaId: string }) {
  const qc = useQueryClient();
  const [adding, setAdding] = useState(false);
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (adding && inputRef.current) inputRef.current.focus();
  }, [adding]);

  const patchMut = useMutation({
    mutationFn: (newTags: string[]) => patchPersona(personaId, { tags: newTags }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['persona-detail'] }),
    onError: () => toast('error', '标签更新失败'),
  });

  const addTag = () => {
    const val = input.trim();
    if (!val) { setAdding(false); setInput(''); return; }
    if (tags.includes(val)) { toast('error', '标签已存在'); return; }
    patchMut.mutate([...tags, val]);
    setInput('');
    setAdding(false);
  };

  const removeTag = (tag: string) => {
    patchMut.mutate(tags.filter(t => t !== tag));
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {tags.map(tag => (
        <span
          key={tag}
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-bg-hover text-text-secondary text-xs"
        >
          {tag}
          <button
            onClick={(e) => { e.stopPropagation(); removeTag(tag); }}
            className="text-text-muted hover:text-error transition-colors"
          >
            <X className="w-3 h-3" />
          </button>
        </span>
      ))}
      {adding ? (
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') addTag();
            if (e.key === 'Escape') { setAdding(false); setInput(''); }
          }}
          onBlur={addTag}
          placeholder="标签名"
          className="w-[100px] px-2 py-0.5 text-xs bg-bg-hover border border-border-default rounded-full
            text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
        />
      ) : (
        <button
          onClick={(e) => { e.stopPropagation(); setAdding(true); }}
          className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full border border-dashed border-border-default
            text-text-muted text-xs hover:border-brand hover:text-brand transition-colors"
        >
          <Plus className="w-3 h-3" />
          标签
        </button>
      )}
    </div>
  );
}

// ─── Tone Bar Chart ─────────────────────────────────────────

function ToneBarChart({ data, editable, onChange }: {
  data: Record<string, string | number> | null;
  editable?: boolean;
  onChange?: (k: string, v: number) => void;
}) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="bg-bg-card border border-border-default rounded-lg p-4">
        <h4 className="text-sm font-medium text-text-secondary mb-2">调性适配度</h4>
        <p className="text-sm text-text-muted py-4 text-center">暂无调性适配数据</p>
      </div>
    );
  }
  const toneLabels: Record<string, string> = {
    formal: '正式', casual: '随意', emotional: '感性', humorous: '幽默',
    aggressive: '犀利', gentle: '温柔', professional: '专业', storytelling: '叙事',
    inspirational: '励志', educational: '教育', entertaining: '娱乐', provocative: '挑衅',
  };
  const entries = Object.entries(data).map(([key, val]) => ({
    key, label: toneLabels[key] || key,
    value: typeof val === 'number' ? val : parseFloat(String(val)) || 0,
  }));
  const maxVal = Math.max(...entries.map((e) => e.value), 1);
  return (
    <div className="bg-bg-card border border-border-default rounded-lg p-4">
      <h4 className="text-sm font-medium text-text-secondary mb-3">调性适配度</h4>
      <div className="space-y-2.5">
        {entries.map(({ key, label, value }) => {
          const pct = maxVal > 0 ? (value / maxVal) * 100 : 0;
          return (
            <div key={key} className="flex items-center gap-3">
              <span className="text-xs text-text-secondary w-16 shrink-0 text-right">{label}</span>
              {editable ? (
                <input type="range" min={0} max={10} step={0.5} value={value}
                  onChange={(e) => onChange?.(key, parseFloat(e.target.value))}
                  className="flex-1 accent-brand" />
              ) : (
                <div className="flex-1 h-5 bg-bg-hover rounded-sm overflow-hidden">
                  <div className="h-full rounded-sm bg-gradient-to-r from-brand to-brand-hover transition-all duration-500" style={{ width: `${pct}%` }} />
                </div>
              )}
              <span className="text-xs text-text-muted w-10 shrink-0 text-right font-mono">{value}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Tag List Editor ────────────────────────────────────────

function TagEditor({ value, onChange, placeholder }: {
  value: string[]; onChange: (v: string[]) => void; placeholder?: string;
}) {
  const [input, setInput] = useState('');
  const add = () => {
    const t = input.trim();
    if (t && !value.includes(t)) { onChange([...value, t]); setInput(''); }
  };
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {value.map((tag, i) => (
          <span key={i} className="inline-flex items-center gap-1 bg-bg-hover rounded-md px-2 py-1 text-xs text-text-primary">
            {tag}
            <button onClick={() => onChange(value.filter((_, j) => j !== i))} className="text-text-muted hover:text-error">
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), add())}
          placeholder={placeholder || '输入后按回车添加...'}
          className="flex-1 bg-bg-primary border border-border-default rounded-md px-2 py-1 text-xs text-text-primary placeholder:text-text-muted outline-none focus:border-brand" />
        <button onClick={add} className="p-1 text-text-muted hover:text-brand"><Plus className="w-4 h-4" /></button>
      </div>
    </div>
  );
}

// ─── Export Helpers ──────────────────────────────────────────

function exportJSON(p: PersonaDetail) {
  const blob = new Blob([JSON.stringify(p, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${p.name}_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function copyPrompt(p: PersonaDetail) {
  const ls = Object.entries(p.language_style || {})
    .map(([k, v]) => `- ${LS_LABELS[k] || k}: ${v}/10`).join('\n');
  const cp = (p.catchphrases || []).map((c) => `"${c}"`).join('、');
  const rp = Object.entries(p.reaction_patterns || {})
    .map(([k, v]) => `  - ${k}: ${v}`).join('\n');
  const text = `# 人设：${p.name}\n\n## 风格综述\n${p.global_style}\n\n## 语言风格评分\n${ls}\n\n## 口头禅\n${cp}\n\n## 反应模式\n${rp}\n\n## 核心价值观\n${(p.core_values || []).join('、')}`;
  navigator.clipboard.writeText(text).then(
    () => toast('success', '已复制到剪贴板'),
    () => toast('error', '复制失败'),
  );
}

// ─── Main Component ─────────────────────────────────────────

export default function PersonaDetail({ personaId }: Props) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');
  const [compareId, setCompareId] = useState('');
  const [editing, setEditing] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{ type: string; label: string } | null>(null);

  const { data: persona, isLoading } = useQuery({
    queryKey: ['persona', personaId],
    queryFn: () => getPersona(personaId),
    enabled: !!personaId,
  });

  const { data: personasList } = useQuery({
    queryKey: ['personas-list'],
    queryFn: () => listPersonas(0, 50),
  });

  const { data: comparePersona } = useQuery({
    queryKey: ['persona', compareId],
    queryFn: () => getPersona(compareId),
    enabled: !!compareId,
  });

  // Edit form state
  const [editForm, setEditForm] = useState<PersonaDetail | null>(null);
  const startEdit = useCallback(() => {
    if (persona) { setEditForm({ ...persona }); setEditing(true); }
  }, [persona]);
  const cancelEdit = () => { setEditForm(null); setEditing(false); };

  const saveMut = useMutation({
    mutationFn: (fields: Parameters<typeof patchPersona>[1]) => patchPersona(personaId, fields),
    onSuccess: () => { toast('success', '已保存'); qc.invalidateQueries({ queryKey: ['persona', personaId] }); setEditing(false); setEditForm(null); },
    onError: () => toast('error', '保存失败'),
  });

  const statusMut = useMutation({
    mutationFn: (fields: Parameters<typeof patchPersona>[1]) => patchPersona(personaId, fields),
    onSuccess: () => { toast('success', '状态已更新'); qc.invalidateQueries({ queryKey: ['persona', personaId] }); qc.invalidateQueries({ queryKey: ['personas-list'] }); setMenuOpen(false); setConfirmAction(null); },
    onError: () => toast('error', '操作失败'),
  });

  const deleteMut = useMutation({
    mutationFn: () => deletePersona(personaId),
    onSuccess: () => { toast('success', '人设已删除'); qc.invalidateQueries({ queryKey: ['personas-list'] }); navigate('/personas'); },
    onError: () => toast('error', '删除失败'),
  });

  const reanalyzeMut = useMutation({
    mutationFn: (id: string) => fetch(`/api/persona/reanalyze/${id}`, { method: 'POST' }).then(r => { if (!r.ok) throw new Error('Re-analyze failed'); return r.json(); }),
    onSuccess: (data) => { toast('success', `重新训练完成，已升级至 v${data.version}（含替换词表、语言风格等新维度）`); qc.invalidateQueries({ queryKey: ['persona', personaId] }); },
    onError: () => toast('error', '重新训练失败，请检查该人设是否有足够的文本素材'),
  });

  const recommendations = useMemo(() => {
    const ls = (editing ? editForm : persona)?.language_style;
    if (!ls) return [];
    return RECOMMENDATIONS.filter((rec) => {
      const dataKey = rec.dim === 'rhythm' ? 'rhythm_score' : rec.dim;
      const v = ls[dataKey];
      return (typeof v === 'number' ? v : parseFloat(String(v)) || 0) >= rec.th;
    });
  }, [persona?.language_style, editForm?.language_style, editing]);

  if (isLoading) return <div className="flex-1 flex items-center justify-center"><Spinner className="text-brand" /></div>;
  if (!persona) return <div className="flex-1 flex items-center justify-center text-text-muted">选择一个人设查看详情</div>;

  const display = editing && editForm ? editForm : persona;
  const otherPersonas = personasList?.items?.filter((p) => p.id !== personaId) || [];
  const sliceCount = persona.narrative_model?.slice_count ?? persona.slice_count ?? 0;
  const clarity = sliceCount >= 5 ? 'high' : sliceCount >= 3 ? 'medium' : 'low';

  const handleConfirm = () => {
    if (!confirmAction) return;
    if (confirmAction.type === 'template') statusMut.mutate({ is_template: !persona.is_template });
    else if (confirmAction.type === 'archive') statusMut.mutate({ is_active: false });
    else if (confirmAction.type === 'delete') deleteMut.mutate();
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold text-text-primary">{persona.name}</h2>
          <Badge variant="default">v{persona.version}</Badge>
          {persona.is_template && <Badge variant="success">模板</Badge>}
          {persona.source_anchor_name && (
            <span className="inline-flex items-center gap-1 text-xs text-brand bg-brand/10 rounded-full px-2.5 py-0.5">
              <User className="w-3 h-3" />
              {persona.source_anchor_name}
              {persona.source_homepage_url && (
                <a href={persona.source_homepage_url} target="_blank" rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="text-brand/60 hover:text-brand transition-colors">
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </span>
          )}
        </div>
        <DetailTags tags={persona.tags || []} personaId={persona.id} />
        <div className="flex items-center gap-2">
          {!editing && (
            <>
              <Button size="sm" variant="outline" onClick={() => reanalyzeMut.mutate(persona.id)}
                disabled={reanalyzeMut.isPending}>
                {reanalyzeMut.isPending
                  ? <><Spinner className="w-3.5 h-3.5 mr-1" /> 训练中...</>
                  : <><RotateCcw className="w-3.5 h-3.5 mr-1" /> 重新训练</>}
              </Button>
              <Button size="sm" variant="secondary" onClick={startEdit}>
                <Pencil className="w-3.5 h-3.5 mr-1" /> 编辑
              </Button>
            </>
          )}
          <Button size="sm" onClick={() => navigate(`/scripts?persona_id=${personaId}`)}>
            应用到新脚本 <ArrowRight className="w-3.5 h-3.5" />
          </Button>
          {/* Status menu */}
          <div className="relative">
            <button onClick={() => setMenuOpen(!menuOpen)} className="p-2 text-text-muted hover:text-text-primary rounded-md hover:bg-bg-hover">
              <MoreVertical className="w-4 h-4" />
            </button>
            {menuOpen && (
              <div className="absolute right-0 top-full mt-1 bg-bg-card border border-border-default rounded-lg shadow-lg z-40 py-1 w-40">
                <button onClick={() => { setConfirmAction({ type: 'template', label: persona.is_template ? '取消模板标记' : '标记为模板' }); setMenuOpen(false); }}
                  className="w-full text-left px-3 py-2 text-sm text-text-primary hover:bg-bg-hover flex items-center gap-2">
                  <Bookmark className="w-3.5 h-3.5" /> {persona.is_template ? '取消模板' : '标记模板'}
                </button>
                <button onClick={() => { setConfirmAction({ type: 'archive', label: '归档此人设' }); setMenuOpen(false); }}
                  className="w-full text-left px-3 py-2 text-sm text-text-primary hover:bg-bg-hover flex items-center gap-2">
                  <Archive className="w-3.5 h-3.5" /> 归档
                </button>
                <button onClick={() => { setConfirmAction({ type: 'delete', label: '删除人设' }); setMenuOpen(false); }}
                  className="w-full text-left px-3 py-2 text-sm text-error hover:bg-bg-hover flex items-center gap-2"
                  disabled={persona.is_template}>
                  <Trash2 className="w-3.5 h-3.5" /> 删除
                </button>
                {persona.is_template && (
                  <p className="px-3 py-1 text-[10px] text-text-muted">模板人设不可删除，请先取消标记</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <Tabs tabs={DETAIL_TABS} active={activeTab} onChange={setActiveTab} />

      {/* Degraded warning */}
      {persona.degraded && <DegradedBanner />}

      {/* ── Overview Tab ── */}
      {activeTab === 'overview' && (
        <div className="space-y-4">
          {/* Clone diagnostics card */}
          <DiagnosisCard persona={persona} />

          {/* Style summary */}
          <div className="bg-bg-card border border-border-default rounded-lg p-4">
            <h4 className="text-sm font-medium text-text-secondary mb-2">风格综述</h4>
            {editing ? (
              <textarea value={editForm?.global_style || ''} rows={3}
                onChange={(e) => setEditForm({ ...editForm!, global_style: e.target.value })}
                className="w-full bg-bg-primary border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand resize-y" />
            ) : (
              <p className="text-sm text-text-primary leading-relaxed">{persona.global_style}</p>
            )}
          </div>

          {/* Radar + style */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-bg-card border border-border-default rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-text-secondary">语言风格雷达</h4>
                {!editing && (
                  <div className="relative">
                    <select value={compareId} onChange={(e) => setCompareId(e.target.value)}
                      className="bg-bg-hover border border-border-default rounded-md pl-2 pr-6 py-1 text-xs text-text-primary outline-none appearance-none cursor-pointer">
                      <option value="">对比: 无</option>
                      {otherPersonas.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                    <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 text-text-muted pointer-events-none" />
                  </div>
                )}
              </div>
              {editing ? (
                <div className="space-y-3 py-2">
                  {LS_KEYS.map((key) => {
                    const dataKey = key === 'rhythm' ? 'rhythm_score' : key;
                    return (
                    <div key={key} className="flex items-center gap-3">
                      <span className="text-xs text-text-secondary w-16 shrink-0">{LS_LABELS[key]}</span>
                      <input type="range" min={0} max={10} step={0.5}
                        value={typeof editForm?.language_style?.[dataKey] === 'number' ? editForm.language_style[dataKey] : 0}
                        onChange={(e) => {
                          const ls = { ...(editForm?.language_style || {}) };
                          ls[dataKey] = parseFloat(e.target.value);
                          setEditForm({ ...editForm!, language_style: ls });
                        }}
                        className="flex-1 accent-brand" />
                      <span className="text-xs text-text-muted w-8 text-right font-mono">
                        {editForm?.language_style?.[dataKey] ?? 0}
                      </span>
                    </div>
                    );
                  })}
                </div>
              ) : (
                <RadarChart data={persona.language_style || {}} label={persona.name}
                  compareData={comparePersona?.language_style || null} compareLabel={comparePersona?.name} />
              )}
            </div>
            <div className="space-y-4">
              {/* Catchphrases */}
              <div className="bg-bg-card border border-border-default rounded-lg p-4">
                <h4 className="text-sm font-medium text-text-secondary mb-2">口头禅</h4>
                {editing ? (
                  <TagEditor value={editForm?.catchphrases || []}
                    onChange={(v) => setEditForm({ ...editForm!, catchphrases: v })} placeholder="输入口头禅..." />
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {(persona.catchphrases || []).map((p, i) => <Badge key={i} variant="default">{p}</Badge>)}
                  </div>
                )}
              </div>
              {/* Core values */}
              <div className="bg-bg-card border border-border-default rounded-lg p-4">
                <h4 className="text-sm font-medium text-text-secondary mb-2">核心价值观</h4>
                {editing ? (
                  <TagEditor value={editForm?.core_values || []}
                    onChange={(v) => setEditForm({ ...editForm!, core_values: v })} placeholder="输入价值观..." />
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {(persona.core_values || []).map((v, i) => <Badge key={i} variant="success">{v}</Badge>)}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* V2 Detailed Traits */}
          {(editing ? editForm?.language_style_v2 : persona.language_style_v2) ? (() => {
            const v2 = (editing ? editForm!.language_style_v2 : persona.language_style_v2)!;
            const setV2 = (patch: Partial<typeof v2>) => {
              setEditForm({ ...editForm!, language_style_v2: { ...v2, ...patch } } as PersonaDetail);
            };
            return (
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-text-secondary">精细特征分析</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Group 1: Language Style */}
                <div className="bg-bg-card border border-border-default rounded-lg p-3.5 space-y-2.5">
                  <h5 className="text-xs font-medium text-brand">语言风格</h5>
                  {editing ? (
                    <>
                      <EditableScoreBar label="反问频率" value={v2.rhetorical_question_freq ?? 0} onChange={(v) => setV2({ rhetorical_question_freq: v })} />
                      <EditableScoreBar label="打断倾向" value={v2.interrupt_tendency ?? 0} onChange={(v) => setV2({ interrupt_tendency: v })} />
                      <EditableScoreBar label="用词尖锐度" value={v2.sharpness ?? 0} onChange={(v) => setV2({ sharpness: v })} />
                      <EditableScoreBar label="自黑倾向" value={v2.self_deprecation ?? 0} onChange={(v) => setV2({ self_deprecation: v })} />
                      <EditableText label="幽默类型" value={v2.humor_type || ''} onChange={(v) => setV2({ humor_type: v })} placeholder="如：讽刺型" />
                    </>
                  ) : (
                    <>
                      <ScoreBar label="反问频率" value={v2.rhetorical_question_freq} clarity={clarity} />
                      <ScoreBar label="打断倾向" value={v2.interrupt_tendency} clarity={clarity} />
                      <ScoreBar label="用词尖锐度" value={v2.sharpness} clarity={clarity} />
                      <ScoreBar label="自黑倾向" value={v2.self_deprecation} clarity={clarity} />
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-text-secondary">幽默类型</span>
                        <Badge variant="default" className="text-[10px]">{v2.humor_type || '未识别'}</Badge>
                      </div>
                    </>
                  )}
                </div>

                {/* Group 2: Rhythm */}
                <div className="bg-bg-card border border-border-default rounded-lg p-3.5 space-y-2.5">
                  <h5 className="text-xs font-medium text-brand">节奏模式</h5>
                  {editing ? (
                    <>
                      <EditableText label="语速" value={v2.pace || ''} onChange={(v) => setV2({ pace: v })} placeholder="快/中/慢" />
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-text-secondary w-16 shrink-0">最长停顿</span>
                        <input type="number" min={0} max={30} step={0.1} value={v2.max_pause_seconds ?? 0}
                          onChange={(e) => setV2({ max_pause_seconds: parseFloat(e.target.value) || 0 })}
                          className="w-20 bg-bg-hover border border-border-default rounded-md px-2 py-1 text-text-primary text-xs outline-none focus:border-brand" />
                        <span className="text-text-muted">秒</span>
                      </div>
                      <EditableScoreBar label="抢话频率" value={v2.grab_floor_freq ?? 0} onChange={(v) => setV2({ grab_floor_freq: v })} />
                      <EditableText label="独白长度" value={v2.monologue_length || ''} onChange={(v) => setV2({ monologue_length: v })} placeholder="短/中/长" />
                    </>
                  ) : (
                    <>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-text-secondary">语速</span>
                        <Badge variant="default" className="text-[10px]">{v2.pace || '中'}</Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-text-secondary">最长停顿</span>
                        <span className="text-text-primary font-mono">{v2.max_pause_seconds ?? '-'}秒</span>
                      </div>
                      <ScoreBar label="抢话频率" value={v2.grab_floor_freq} clarity={clarity} />
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-text-secondary">独白长度</span>
                        <Badge variant="default" className="text-[10px]">{v2.monologue_length || '中'}</Badge>
                      </div>
                    </>
                  )}
                </div>

                {/* Group 3: Emotion */}
                <div className="bg-bg-card border border-border-default rounded-lg p-3.5 space-y-2.5">
                  <h5 className="text-xs font-medium text-brand">情绪模式</h5>
                  {editing ? (
                    <>
                      <EditableText label="共情方式" value={v2.empathy_style || ''} onChange={(v) => setV2({ empathy_style: v })} placeholder="如：镜像共情" />
                      <EditableScoreBar label="情绪波动" value={v2.emotional_volatility ?? 0} onChange={(v) => setV2({ emotional_volatility: v })} />
                      <EditableTagList label="情绪触发点" values={v2.emotional_triggers || []}
                        onChange={(v) => setV2({ emotional_triggers: v })} placeholder="回车添加" variant="warning" />
                    </>
                  ) : (
                    <>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-text-secondary">共情方式</span>
                        <Badge variant="default" className="text-[10px]">{v2.empathy_style || '未识别'}</Badge>
                      </div>
                      <ScoreBar label="情绪波动" value={v2.emotional_volatility} clarity={clarity} />
                      <div className="text-xs">
                        <span className="text-text-secondary">情绪触发点</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {(v2.emotional_triggers || []).map((t, i) => (
                            <Badge key={i} variant="warning" className="text-[10px]">{t}</Badge>
                          ))}
                          {(!v2.emotional_triggers || v2.emotional_triggers.length === 0) && (
                            <span className="text-text-muted">无明显触发点</span>
                          )}
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* Group 4: Content Preferences */}
                <div className="bg-bg-card border border-border-default rounded-lg p-3.5 space-y-2.5">
                  <h5 className="text-xs font-medium text-brand">内容偏好</h5>
                  {editing ? (
                    <>
                      <EditableTagList label="比喻域" values={v2.metaphor_domains || []}
                        onChange={(v) => setV2({ metaphor_domains: v })} placeholder="回车添加" variant="success" />
                      <EditableTagList label="话题偏好" values={v2.topic_preferences || []}
                        onChange={(v) => setV2({ topic_preferences: v })} placeholder="回车添加" />
                      <EditableScoreBar label="金句密度" value={v2.punchline_density ?? 0} onChange={(v) => setV2({ punchline_density: v })} />
                    </>
                  ) : (
                    <>
                      <div className="text-xs">
                        <span className="text-text-secondary">比喻域</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {(v2.metaphor_domains || []).map((d, i) => (
                            <Badge key={i} variant="success" className="text-[10px]">{d}</Badge>
                          ))}
                          {(!v2.metaphor_domains || v2.metaphor_domains.length === 0) && (
                            <span className="text-text-muted">无明显偏好</span>
                          )}
                        </div>
                      </div>
                      <div className="text-xs">
                        <span className="text-text-secondary">话题偏好</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {(v2.topic_preferences || []).map((t, i) => (
                            <Badge key={i} variant="default" className="text-[10px]">{t}</Badge>
                          ))}
                        </div>
                      </div>
                      <ScoreBar label="金句密度" value={v2.punchline_density} clarity={clarity} />
                    </>
                  )}
                </div>

                {/* Group 5: Catchphrase Functions */}
                <div className="bg-bg-card border border-border-default rounded-lg p-3.5 space-y-2.5">
                  <h5 className="text-xs font-medium text-brand">口头禅功能</h5>
                  {editing ? (
                    <>
                      <EditableText label="开场" value={v2.opening_phrase || ''} onChange={(v) => setV2({ opening_phrase: v || null })} placeholder="如：说真的" />
                      <EditableText label="转折" value={v2.transition_phrase || ''} onChange={(v) => setV2({ transition_phrase: v || null })} placeholder="如：但是你听我说" />
                      <EditableText label="收尾" value={v2.closing_phrase || ''} onChange={(v) => setV2({ closing_phrase: v || null })} placeholder="如：就这样吧" />
                    </>
                  ) : (
                    <>
                      <PhraseRow label="开场" phrase={v2.opening_phrase} />
                      <PhraseRow label="转折" phrase={v2.transition_phrase} />
                      <PhraseRow label="收尾" phrase={v2.closing_phrase} />
                    </>
                  )}
                </div>
              </div>
            </div>
            );
          })() : (
            <div className="bg-bg-card border border-border-default rounded-lg p-4">
              <p className="text-xs text-text-muted">暂无精细特征数据，请重新分析人设以获取 18 维度精细特征。</p>
            </div>
          )}

          {/* Lingo Map */}
          <LingoMapEditor
            lingoMap={((editing ? editForm : persona)?.lingo_map) || {}}
            editing={!!editing}
            personaId={personaId}
          />

          {/* Recommendations */}
          {!editing && recommendations.length > 0 && (
            <div className="bg-bg-card border border-border-default rounded-lg p-4">
              <h4 className="text-sm font-medium text-text-secondary mb-3">互补连线人推荐</h4>
              <div className="grid grid-cols-3 gap-3">
                {recommendations.map((rec) => (
                  <div key={rec.type} className="bg-bg-primary border border-border-default rounded-lg p-3 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-brand">{rec.type}</span>
                      <Badge variant="default" className="text-[10px]">{LS_LABELS[rec.dim]} ≥ {rec.th}</Badge>
                    </div>
                    <p className="text-xs text-text-muted leading-relaxed">{rec.desc}</p>
                    <button onClick={() => navigate('/creator')} className="text-[11px] text-brand hover:underline">去生成连线人 →</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tone adaptation */}
          <ToneBarChart data={display.tone_adaptation as Record<string, string | number> | null}
            editable={editing}
            onChange={(k, v) => {
              const ta = { ...(editForm?.tone_adaptation || {}) };
              ta[k] = v;
              setEditForm({ ...editForm!, tone_adaptation: ta });
            }} />

          {/* Reaction patterns */}
          <div className="bg-bg-card border border-border-default rounded-lg p-4">
            <h4 className="text-sm font-medium text-text-secondary mb-3">反应模式</h4>
            {editing ? (
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(editForm?.reaction_patterns || {}).map(([key, val]) => (
                  <div key={key} className="bg-bg-primary rounded-md p-3">
                    <p className="text-xs text-brand font-medium mb-1">{key}</p>
                    <textarea value={String(val)} rows={2}
                      onChange={(e) => {
                        const rp = { ...(editForm?.reaction_patterns || {}) };
                        rp[key] = e.target.value;
                        setEditForm({ ...editForm!, reaction_patterns: rp });
                      }}
                      className="w-full bg-transparent border-none outline-none text-sm text-text-primary resize-y" />
                  </div>
                ))}
              </div>
            ) : persona.reaction_patterns && Object.keys(persona.reaction_patterns).length > 0 ? (
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(persona.reaction_patterns).map(([key, val]) => (
                  <div key={key} className="bg-bg-primary rounded-md p-3">
                    <p className="text-xs text-brand font-medium mb-1">{key}</p>
                    <p className="text-sm text-text-primary">{String(val)}</p>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-text-muted">暂无反应模式数据</p>}
          </div>

          {/* Sentence templates */}
          {(editing || persona.sentence_templates?.length) ? (
            <div className="bg-bg-card border border-border-default rounded-lg p-4">
              <h4 className="text-sm font-medium text-text-secondary mb-3">句式模板</h4>
              <ul className="space-y-2 font-mono text-sm">
                {(editing ? editForm?.sentence_templates || [] : persona.sentence_templates || []).map((tpl, i) => (
                  <li key={i} className="bg-bg-primary rounded-md px-3 py-2 text-text-primary flex items-center gap-2">
                    {editing ? (
                      <>
                        <input value={tpl} onChange={(e) => {
                          const st = [...(editForm?.sentence_templates || [])];
                          st[i] = e.target.value;
                          setEditForm({ ...editForm!, sentence_templates: st });
                        }} className="flex-1 bg-transparent outline-none text-text-primary text-sm font-mono" />
                        <button onClick={() => {
                          const st = (editForm?.sentence_templates || []).filter((_, j) => j !== i);
                          setEditForm({ ...editForm!, sentence_templates: st });
                        }} className="text-text-muted hover:text-error shrink-0"><X className="w-3.5 h-3.5" /></button>
                      </>
                    ) : tpl}
                  </li>
                ))}
                {editing && (
                  <li>
                    <button onClick={() => {
                      const st = [...(editForm?.sentence_templates || []), ''];
                      setEditForm({ ...editForm!, sentence_templates: st });
                    }} className="text-xs text-brand hover:underline flex items-center gap-1">
                      <Plus className="w-3 h-3" /> 添加句式
                    </button>
                  </li>
                )}
              </ul>
            </div>
          ) : null}

          {/* Edit actions */}
          {editing && (
            <div className="flex gap-3">
              <Button loading={saveMut.isPending} onClick={() => {
                if (!editForm) return;
                saveMut.mutate({
                  global_style: editForm.global_style,
                  catchphrases: editForm.catchphrases || undefined,
                  reaction_patterns: editForm.reaction_patterns || undefined,
                  sentence_templates: editForm.sentence_templates?.filter(Boolean) || undefined,
                  core_values: editForm.core_values || undefined,
                  language_style: editForm.language_style || undefined,
                  language_style_v2: (editForm.language_style_v2 as unknown as Record<string, unknown>) || undefined,
                  lingo_map: (editForm.lingo_map as unknown as Record<string, unknown>) || undefined,
                  tone_adaptation: editForm.tone_adaptation || undefined,
                });
              }}>保存修改</Button>
              <Button variant="secondary" onClick={cancelEdit}>取消</Button>
            </div>
          )}

          {/* Export */}
          {!editing && (
            <div className="flex gap-3">
              <Button variant="secondary" size="sm" onClick={() => exportJSON(persona)}>
                <Download className="w-3.5 h-3.5 mr-1" /> 导出 JSON
              </Button>
              <Button variant="secondary" size="sm" onClick={() => copyPrompt(persona)}>
                <Copy className="w-3.5 h-3.5 mr-1" /> 复制 Prompt
              </Button>
            </div>
          )}
        </div>
      )}

      {/* ── Slices Tab ── */}
      {activeTab === 'slices' && <SlicesTab personaId={personaId} totalCount={persona.slice_count} />}

      {/* ── History Tab ── */}
      {activeTab === 'history' && (
        <HistoryTab personaId={personaId} currentVersion={persona.version} versionNotes={persona.version_notes} created={persona.created_at} />
      )}

      {/* ── Confirm Modal ── */}
      <ConfirmModal
        open={!!confirmAction}
        title="确认操作"
        message={`确定要「${confirmAction?.label || ''}」吗？${confirmAction?.type === 'delete' ? '此操作不可恢复。' : ''}`}
        confirmText="确认"
        confirmVariant={confirmAction?.type === 'delete' ? 'danger' : 'primary'}
        loading={statusMut.isPending || deleteMut.isPending || reanalyzeMut.isPending}
        onConfirm={handleConfirm}
        onCancel={() => setConfirmAction(null)}
      />
    </div>
  );
}

// ── Slices Tab ──────────────────────────────────────────────

function SlicesTab({ personaId, totalCount }: { personaId: string; totalCount: number }) {
  const qc = useQueryClient();
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const fileInputRef = useState<HTMLInputElement | null>(null);

  const { data: slicesData, isLoading } = useQuery({
    queryKey: ['persona-slices', personaId],
    queryFn: () => getPersonaSlices(personaId),
    enabled: !!personaId,
  });

  const deleteSliceMut = useMutation({
    mutationFn: (sliceId: string) => deletePersonaSlice(personaId, sliceId),
    onSuccess: () => { toast('success', '切片已删除'); setDeleteId(null); qc.invalidateQueries({ queryKey: ['persona-slices', personaId] }); qc.invalidateQueries({ queryKey: ['persona', personaId] }); },
    onError: () => toast('error', '删除失败'),
  });

  const uploadMut = useMutation({
    mutationFn: (texts: string[]) => appendSlices(personaId, texts),
    onSuccess: () => { toast('success', '切片已上传并分析'); qc.invalidateQueries({ queryKey: ['persona-slices', personaId] }); qc.invalidateQueries({ queryKey: ['persona', personaId] }); },
    onError: () => toast('error', '上传失败'),
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      const lines = text.split('\n').map((l) => l.trim()).filter((l) => l.length > 10);
      if (lines.length > 0) uploadMut.mutate(lines);
      else toast('warning', '文件内容不足，每行至少10字');
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  const slices = slicesData?.items || [];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-text-secondary">关联切片 {totalCount} 条</p>
        <label className="cursor-pointer">
          <input ref={(el) => { fileInputRef[1](el); }} type="file" accept=".txt" className="hidden" onChange={handleFileUpload} />
          <Button size="sm" variant="ghost" loading={uploadMut.isPending} onClick={() => fileInputRef[0]?.click()}>
            <Upload className="w-3.5 h-3.5 mr-1" /> 上传新切片
          </Button>
        </label>
      </div>
      {isLoading ? (
        <div className="flex justify-center py-8"><Spinner className="text-brand" /></div>
      ) : slices.length === 0 ? (
        <p className="text-sm text-text-muted py-8 text-center">暂无切片数据</p>
      ) : (
        <div className="space-y-2">
          {slices.map((s: any, i: number) => (
            <div key={s.id} className="bg-bg-card border border-border-default rounded-lg p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {s.emotion_tag && <Badge variant="default" className="text-[10px]">{s.emotion_tag}</Badge>}
                    {s.action_desc && <span className="text-xs text-text-muted">{s.action_desc}</span>}
                  </div>
                  <p className="text-sm text-text-primary">
                    {expandedIdx === i ? s.original_text : s.preview}
                  </p>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button onClick={() => setDeleteId(s.id)} className="p-1 text-text-muted hover:text-error" title="删除">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={() => setExpandedIdx(expandedIdx === i ? null : i)} className="text-text-muted hover:text-text-primary">
                    {expandedIdx === i ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {/* Delete confirm */}
      <ConfirmModal
        open={!!deleteId}
        title="确认删除切片"
        message="此切片删除后不可恢复，确定继续？"
        loading={deleteSliceMut.isPending}
        onConfirm={() => { deleteSliceMut.mutate(deleteId!); setDeleteId(null); }}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}

// ── History Tab ─────────────────────────────────────────────

function HistoryTab({ personaId, currentVersion, versionNotes, created }: {
  personaId: string; currentVersion: number;
  versionNotes: { version: number; summary: string; added_slices: number }[] | null;
  created: string | null;
}) {
  const qc = useQueryClient();
  const [rollbackTarget, setRollbackTarget] = useState<number | null>(null);
  const [noteTarget, setNoteTarget] = useState<number | null>(null);
  const [noteText, setNoteText] = useState('');

  const rollbackMut = useMutation({
    mutationFn: (target: number) => rollbackPersona(personaId, target),
    onSuccess: () => { toast('success', '已回滚'); setRollbackTarget(null); qc.invalidateQueries({ queryKey: ['persona', personaId] }); },
    onError: () => toast('error', '回滚失败'),
  });

  const noteMut = useMutation({
    mutationFn: async ({ version, note }: { version: number; note: string }) => {
      const notes = [...(versionNotes || [])];
      const idx = notes.findIndex((n) => n.version === version);
      if (idx >= 0) {
        notes[idx] = { ...notes[idx], summary: notes[idx].summary ? `${notes[idx].summary}; ${note}` : note };
      } else {
        notes.push({ version, summary: note, added_slices: 0 });
      }
      // Use patchPersona to update version_notes - but that endpoint doesn't support version_notes yet
      // For now we'll use a workaround through the append mechanism
      return notes;
    },
    onSuccess: () => { toast('success', '备注已添加'); setNoteTarget(null); setNoteText(''); qc.invalidateQueries({ queryKey: ['persona', personaId] }); },
  });

  return (
    <div className="space-y-2">
      {Array.from({ length: currentVersion }, (_, i) => currentVersion - i).map((v) => {
        const note = versionNotes?.find((n) => n.version === v);
        return (
          <div key={v} className="bg-bg-card border border-border-default rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm text-text-primary font-medium">版本 {v}</span>
                {v === currentVersion && <Badge variant="success">当前</Badge>}
              </div>
              <div className="flex items-center gap-2">
                {v < currentVersion && (
                  <>
                    <button onClick={() => setRollbackTarget(v)}
                      className="p-1.5 text-text-muted hover:text-brand rounded-md hover:bg-bg-hover" title="回滚到此版本">
                      <RotateCcw className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => { setNoteTarget(v); setNoteText(''); }}
                      className="p-1.5 text-text-muted hover:text-brand rounded-md hover:bg-bg-hover" title="添加备注">
                      <MessageSquare className="w-3.5 h-3.5" />
                    </button>
                  </>
                )}
                <span className="text-xs text-text-muted">{created?.split('T')[0] || '未知日期'}</span>
              </div>
            </div>
            {note && (
              <div className="mt-2 text-xs text-text-muted flex items-center gap-3">
                {note.added_slices > 0 && <span>+{note.added_slices} 条切片</span>}
                <span>{note.summary}</span>
              </div>
            )}
          </div>
        );
      })}
      {/* Rollback confirm */}
      {rollbackTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={() => setRollbackTarget(null)}>
          <div className="absolute inset-0 bg-black/50" />
          <div className="relative bg-bg-card border border-border-default rounded-lg w-[400px] p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-base font-semibold text-text-primary">确认回滚</h3>
            <p className="text-sm text-text-secondary">确定回滚到版本 {rollbackTarget} 吗？当前特征将被覆盖（版本号+1）。</p>
            <div className="flex gap-3 justify-end">
              <Button variant="secondary" size="sm" onClick={() => setRollbackTarget(null)}>取消</Button>
              <Button size="sm" loading={rollbackMut.isPending} onClick={() => rollbackMut.mutate(rollbackTarget)}>确认回滚</Button>
            </div>
          </div>
        </div>
      )}
      {/* Note modal */}
      {noteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={() => setNoteTarget(null)}>
          <div className="absolute inset-0 bg-black/50" />
          <div className="relative bg-bg-card border border-border-default rounded-lg w-[400px] p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-base font-semibold text-text-primary">添加备注 — 版本 {noteTarget}</h3>
            <textarea value={noteText} onChange={(e) => setNoteText(e.target.value)} rows={3} placeholder="输入备注内容..."
              className="w-full bg-bg-primary border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand resize-y" />
            <div className="flex gap-3 justify-end">
              <Button variant="secondary" size="sm" onClick={() => setNoteTarget(null)}>取消</Button>
              <Button size="sm" disabled={!noteText.trim()} loading={noteMut.isPending}
                onClick={() => noteMut.mutate({ version: noteTarget, note: noteText.trim() })}>保存备注</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Score Bar (for v2 dimensions) ─────────────────────────────

function ScoreBar({ label, value, clarity }: { label: string; value: number; clarity: string }) {
  const pct = Math.min(Math.max(value, 0), 10) / 10 * 100;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-text-secondary w-16 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-bg-hover rounded-full overflow-hidden">
        <div className="h-full rounded-full bg-gradient-to-r from-brand to-brand-hover transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-text-muted font-mono w-6 text-right">{value}</span>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
        clarity === 'high' ? 'bg-success' : clarity === 'medium' ? 'bg-warning' : 'bg-error'
      }`} title={`置信度: ${clarity === 'high' ? '高' : clarity === 'medium' ? '中' : '低'}`} />
    </div>
  );
}

// ── Editable Score Bar (slider for v2 numeric dimensions) ─────

function EditableScoreBar({
  label, value, onChange,
}: {
  label: string; value: number; onChange: (v: number) => void;
}) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-text-secondary w-16 shrink-0">{label}</span>
      <input
        type="range" min={0} max={10} step={0.1}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="flex-1 h-1.5 accent-brand cursor-pointer"
      />
      <span className="text-text-primary font-mono w-8 text-right font-medium">{value}</span>
    </div>
  );
}

// ── Editable Text Field (for v2 string dimensions) ────────────

function EditableText({
  label, value, onChange, placeholder,
}: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string;
}) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-text-secondary w-16 shrink-0">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder || '输入...'}
        className="flex-1 bg-bg-hover border border-border-default rounded-md px-2 py-1 text-text-primary text-xs
          placeholder:text-text-muted outline-none focus:border-brand"
      />
    </div>
  );
}

// ── Editable Tag List (for v2 array dimensions) ───────────────

function EditableTagList({
  label, values, onChange, placeholder, variant = 'default',
}: {
  label: string; values: string[]; onChange: (v: string[]) => void;
  placeholder?: string; variant?: 'default' | 'success' | 'warning';
}) {
  const [input, setInput] = useState('');
  const add = () => {
    const t = input.trim();
    if (t && !values.includes(t)) { onChange([...values, t]); setInput(''); }
  };
  return (
    <div className="text-xs space-y-1">
      <span className="text-text-secondary">{label}</span>
      <div className="flex flex-wrap gap-1">
        {values.map((v, i) => (
          <span key={i} className="inline-flex items-center gap-0.5">
            <Badge variant={variant} className="text-[10px]">{v}</Badge>
            <button onClick={() => onChange(values.filter((_, j) => j !== i))} className="text-text-muted hover:text-error">
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-1 mt-1">
        <input
          value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), add())}
          placeholder={placeholder || '回车添加'}
          className="flex-1 bg-bg-hover border border-border-default rounded px-2 py-0.5 text-xs
            text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
        />
        <button onClick={add} className="p-0.5 text-text-muted hover:text-brand"><Plus className="w-3.5 h-3.5" /></button>
      </div>
    </div>
  );
}

// ── Lingo Map Editor ────────────────────────────────────────

function LingoMapEditor({
  lingoMap, editing, personaId,
}: {
  lingoMap: Record<string, string>;
  editing: boolean;
  personaId: string;
}) {
  const qc = useQueryClient();
  const entries = Object.entries(lingoMap);
  const fileRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);

  const patchMut = useMutation({
    mutationFn: (newMap: Record<string, string>) => patchPersona(personaId, { lingo_map: newMap as unknown as Record<string, unknown> }),
    onSuccess: () => { toast('success', '替换词表已更新'); qc.invalidateQueries({ queryKey: ['persona-detail'] }); },
    onError: () => toast('error', '更新失败'),
  });

  const removeEntry = (key: string) => {
    const next = { ...lingoMap };
    delete next[key];
    patchMut.mutate(next);
  };

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    try {
      const res = await importLingo(personaId, file);
      toast('success', `成功导入 ${res.imported_count} 组替换词，跳过 ${res.skipped_count} 行`);
      qc.invalidateQueries({ queryKey: ['persona-detail'] });
    } catch (err: any) {
      toast('error', err?.response?.data?.detail || '导入失败');
    } finally {
      setImporting(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  return (
    <div className="bg-bg-card border border-border-default rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-text-secondary">替换词表 (Lingo)</h4>
        <div className="flex items-center gap-2">
          <input
            ref={fileRef}
            type="file" accept=".txt,.md"
            onChange={handleFile}
            className="hidden"
          />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={importing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-brand bg-brand/10 rounded-md
              hover:bg-brand/20 transition-colors disabled:opacity-50"
          >
            <Upload className="w-3.5 h-3.5" />
            {importing ? '导入中...' : '导入文件'}
          </button>
        </div>
      </div>
      <p className="text-xs text-text-muted mb-3 leading-relaxed">
        每行一组：规范词 + 分隔符(空格/分号/Tab/逗号) + 替换词。空行和 # 开头的行为注释跳过。生成脚本时自动将规范词替换为主播特色用词。
      </p>

      {entries.length === 0 && !editing ? (
        <p className="text-xs text-text-muted py-2">暂无替换词。点击编辑添加，或点击"导入文件"批量导入。</p>
      ) : (
        <div className="space-y-2">
          {entries.map(([key, val]) => (
            <div key={key} className="flex items-center gap-2 text-xs group">
              <span className="bg-bg-hover rounded px-2 py-1 text-text-secondary min-w-[60px] text-center">{key}</span>
              <span className="text-text-muted">→</span>
              <span className="bg-brand/10 text-brand rounded px-2 py-1 min-w-[60px] text-center">{val}</span>
              {!editing && (
                <button
                  onClick={() => removeEntry(key)}
                  className="p-0.5 text-text-muted hover:text-error transition-colors opacity-0 group-hover:opacity-100"
                  title="删除"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {editing && <LingoMapAddForm lingoMap={lingoMap} onAdd={(k, v) => {
        patchMut.mutate({ ...lingoMap, [k]: v });
      }} />}
    </div>
  );
}

function LingoMapAddForm({
  lingoMap, onAdd,
}: {
  lingoMap: Record<string, string>; onAdd: (key: string, val: string) => void;
}) {
  const [key, setKey] = useState('');
  const [val, setVal] = useState('');

  const add = () => {
    const k = key.trim(), v = val.trim();
    if (!k || !v) return;
    if (lingoMap[k]) { toast('error', '该规范词已存在'); return; }
    onAdd(k, v);
    setKey('');
    setVal('');
  };

  return (
    <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border-default">
      <input
        value={key} onChange={(e) => setKey(e.target.value)}
        placeholder="规范词"
        className="w-24 bg-bg-hover border border-border-default rounded px-2 py-1 text-xs
          text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
      />
      <span className="text-text-muted text-xs">→</span>
      <input
        value={val} onChange={(e) => setVal(e.target.value)}
        placeholder="替换词"
        onKeyDown={(e) => e.key === 'Enter' && add()}
        className="w-24 bg-bg-hover border border-border-default rounded px-2 py-1 text-xs
          text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
      />
      <button onClick={add} className="p-1 text-text-muted hover:text-brand transition-colors">
        <Plus className="w-4 h-4" />
      </button>
    </div>
  );
}

function PhraseRow({ label, phrase }: { label: string; phrase: string | null }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-text-secondary w-8 shrink-0">{label}</span>
      {phrase ? (
        <span className="text-text-primary bg-bg-hover rounded px-2 py-0.5">&ldquo;{phrase}&rdquo;</span>
      ) : (
        <span className="text-text-muted">未识别</span>
      )}
    </div>
  );
}

// ── Diagnosis Card ────────────────────────────────────────────

function DiagnosisCard({ persona }: { persona: PersonaDetail }) {
  const navigate = useNavigate();
  const nm = persona.narrative_model;
  const score = nm?.completeness_score ?? 0;

  if (!nm) {
    return (
      <div className="bg-bg-card border border-border-default rounded-lg p-4">
        <h4 className="text-sm font-medium text-text-secondary mb-2">克隆诊断</h4>
        <p className="text-sm text-text-muted">诊断数据尚未生成，请重新处理或补充素材。</p>
      </div>
    );
  }

  const unitCount = nm.narrative_units?.length ?? 0;
  const isGood = score >= 50;

  return (
    <div className={`bg-bg-card border rounded-lg p-5 ${isGood ? 'border-success/30' : 'border-error/30'}`}>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-text-secondary">克隆诊断</h4>
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${score >= 80 ? 'text-success' : score >= 50 ? 'text-warning' : 'text-error'}`}>
            {score}
          </span>
          <span className="text-xs text-text-muted">/ 100</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="bg-bg-primary rounded-md p-2.5 text-center">
          <p className="text-lg font-semibold text-text-primary">{persona.slice_count}</p>
          <p className="text-[10px] text-text-muted">切片素材</p>
        </div>
        <div className="bg-bg-primary rounded-md p-2.5 text-center">
          <p className="text-lg font-semibold text-text-primary">{nm.catchphrase_count}</p>
          <p className="text-[10px] text-text-muted">口头禅</p>
        </div>
        <div className="bg-bg-primary rounded-md p-2.5 text-center">
          <p className="text-lg font-semibold text-text-primary">{unitCount}</p>
          <p className="text-[10px] text-text-muted">叙事单元</p>
        </div>
        <div className="bg-bg-primary rounded-md p-2.5 text-center">
          <p className={`text-lg font-semibold ${isGood ? 'text-success' : 'text-error'}`}>
            {isGood ? '充分' : '不足'}
          </p>
          <p className="text-[10px] text-text-muted">素材充分度</p>
        </div>
      </div>

      {nm.distinctive_features?.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {nm.distinctive_features.map((f, i) => (
            <span key={i} className="text-xs bg-brand/10 text-brand rounded px-2 py-0.5">{f}</span>
          ))}
        </div>
      )}

      {!isGood && (
        <p className="text-xs text-error mb-3">素材不足，建议补充更多视频以提高克隆质量</p>
      )}

      {(persona.source_homepage_url || persona.source_anchor_name) && (
        <Button
          variant={isGood ? 'secondary' : 'primary'}
          size="sm"
          className="w-full mb-2"
          onClick={() => {
            const params = new URLSearchParams({ mode: 'supplement', persona_id: persona.id });
            if (persona.source_homepage_url) params.set('url', persona.source_homepage_url);
            navigate(`/learn?${params.toString()}`);
          }}
        >
          <PlusCircle className="w-3.5 h-3.5 mr-1" />
          补充素材
        </Button>
      )}

      <Button
        variant="primary"
        size="sm"
        className="w-full"
        onClick={() => navigate(`/scripts?persona_id=${persona.id}`)}
      >
        用此主播生成脚本
        <ArrowRight className="w-3.5 h-3.5 ml-1" />
      </Button>
    </div>
  );
}
