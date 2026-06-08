import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Bot, ArrowRight, Clock, Layers, BookOpen, MoreVertical, Trash2, Plus, X, Sparkles, Loader2 } from 'lucide-react';
import { listPersonas, deletePersona, patchPersona, getAnchorsWithoutPersona, generatePersonaFromAssets } from '../services/persona';
import type { PersonaListItem, NarrativeModel } from '../types';
import Badge from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import EmptyState from '../components/ui/EmptyState';
import { toast } from '../components/ui/Toast';
import ConfirmModal from '../components/ui/ConfirmModal';

// ─── Helpers ────────────────────────────────────────────────

function scoreBadge(nm: NarrativeModel | null | undefined) {
  const score = nm?.completeness_score ?? 0;
  if (score >= 80) return <Badge variant="success">克隆优秀</Badge>;
  if (score >= 50) return <Badge variant="warning">可用</Badge>;
  return <Badge variant="danger">素材不足</Badge>;
}

function sourceLabel(p: PersonaListItem) {
  if (p.source_anchor_name) {
    return <Badge variant="success">克隆自 @{p.source_anchor_name}</Badge>;
  }
  return <Badge variant="default">手动创建</Badge>;
}

function formatTime(iso: string | null) {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}

// ─── Card Menu (three dots) ─────────────────────────────────

function CardMenu({ onDelete }: { onDelete: () => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={(e) => { e.stopPropagation(); setOpen(!open); }}
        className="p-1.5 rounded-md text-text-muted hover:text-text-primary hover:bg-bg-hover transition-colors"
      >
        <MoreVertical className="w-4 h-4" />
      </button>
      {open && (
        <div
          className="absolute right-0 top-full mt-1 bg-bg-card border border-border-default rounded-lg shadow-lg z-50 py-1 min-w-[120px]"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => { setOpen(false); onDelete(); }}
            className="w-full px-3 py-2 text-sm text-error hover:bg-bg-hover text-left transition-colors flex items-center gap-2"
          >
            <Trash2 className="w-3.5 h-3.5" />
            删除
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Tag Editor ─────────────────────────────────────────────

function TagEditor({
  tags, personaId, onUpdate, onRemoveTagRequest,
}: {
  tags: string[];
  personaId: string;
  onUpdate: (newTags: string[]) => void;
  onRemoveTagRequest?: (tag: string) => void;
}) {
  const [adding, setAdding] = useState(false);
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (adding && inputRef.current) inputRef.current.focus();
  }, [adding]);

  const addTag = () => {
    const val = input.trim();
    if (!val) { setAdding(false); setInput(''); return; }
    if (tags.includes(val)) { toast('error', '标签已存在'); return; }
    const newTags = [...tags, val];
    onUpdate(newTags);
    setInput('');
    setAdding(false);
  };

  const removeTag = (tag: string) => {
    if (onRemoveTagRequest) { onRemoveTagRequest(tag); return; }
    onUpdate(tags.filter(t => t !== tag));
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5 mt-2">
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
          onClick={(e) => e.stopPropagation()}
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

// ─── Main Page ──────────────────────────────────────────────

export default function AiAnchorsPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [search, setSearch] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<PersonaListItem | null>(null);
  const [removeTagTarget, setRemoveTagTarget] = useState<{ id: string; tag: string } | null>(null);
  const [generating, setGenerating] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['personas'],
    queryFn: () => listPersonas(0, 50),
  });

  const { data: pendingAnchors } = useQuery({
    queryKey: ['anchors-without-persona'],
    queryFn: getAnchorsWithoutPersona,
  });

  const generateMut = useMutation({
    mutationFn: (anchorName: string) => generatePersonaFromAssets(anchorName),
    onMutate: (anchorName) => setGenerating(anchorName),
    onSuccess: (result) => {
      setGenerating(null);
      toast('success', `人设创建成功！完整度 ${result.completeness_score}%`);
      qc.invalidateQueries({ queryKey: ['personas'] });
      qc.invalidateQueries({ queryKey: ['anchors-without-persona'] });
    },
    onError: (err: any) => {
      setGenerating(null);
      toast('error', err?.response?.data?.detail || '创建人设失败');
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => deletePersona(id),
    onSuccess: () => {
      toast('success', '已删除');
      setDeleteTarget(null);
      qc.invalidateQueries({ queryKey: ['personas'] });
    },
    onError: (err: any) => toast('error', err?.response?.data?.detail || '删除失败'),
  });

  const patchMut = useMutation({
    mutationFn: ({ id, tags }: { id: string; tags: string[] }) => patchPersona(id, { tags }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['personas'] }),
    onError: () => toast('error', '标签更新失败'),
  });

  const items: PersonaListItem[] = (data?.items || []).filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.source_anchor_name || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="h-[calc(100vh-3.5rem-3rem)] flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border-default">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-brand/10 flex items-center justify-center">
              <Bot className="w-5 h-5 text-brand" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-text-primary">AI仿生主播</h1>
              <p className="text-xs text-text-muted">克隆真实主播的直播风格，生成仿生人设模型</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-text-muted">
            共 {items.length} 个模型
          </div>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索主播名称或人设名称..."
            className="w-full bg-bg-card border border-border-default rounded-lg pl-10 pr-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand transition-colors"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="flex justify-center py-20"><Spinner className="text-brand" /></div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Bot}
            title={search ? '未找到匹配的主播模型' : '还没有仿生主播模型'}
            description={search ? '尝试其他关键词搜索' : '前往学习中心克隆第一个主播，AI 将自动生成仿生人设模型'}
            actions={search ? undefined : [
              { label: '前往学习中心', onClick: () => navigate('/learn'), variant: 'primary' },
            ]}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((p) => {
              const nm = p.narrative_model;
              const unitCount = nm?.narrative_units?.length ?? 0;
              const score = nm?.completeness_score ?? 0;
              const tags = p.tags || [];

              return (
                <div
                  key={p.id}
                  onClick={() => navigate(`/personas?select=${p.id}`)}
                  className="bg-bg-card border border-border-default rounded-xl p-5 text-left hover:border-brand/40 hover:shadow-md transition-all duration-200 group cursor-pointer relative"
                >
                  {/* Top: Avatar + Name + Menu */}
                  <div className="flex items-start gap-3 mb-3">
                    <div className="w-12 h-12 rounded-full bg-brand/10 flex items-center justify-center text-lg font-semibold text-brand shrink-0">
                      {p.source_anchor_name ? p.source_anchor_name[0] : p.name[0]}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-text-primary truncate">
                        @{p.source_anchor_name || p.name}
                      </p>
                      <p className="text-xs text-text-muted truncate mt-0.5">{p.name}</p>
                    </div>
                    <div onClick={(e) => e.stopPropagation()}>
                      <CardMenu onDelete={() => setDeleteTarget(p)} />
                    </div>
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-1.5">
                    {sourceLabel(p)}
                    {scoreBadge(nm)}
                  </div>

                  {/* Custom Tags */}
                  <TagEditor
                    tags={tags}
                    personaId={p.id}
                    onUpdate={(newTags) => patchMut.mutate({ id: p.id, tags: newTags })}
                    onRemoveTagRequest={(tag) => setRemoveTagTarget({ id: p.id, tag })}
                  />

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-xs text-text-muted mt-3">
                    {nm && (
                      <>
                        <span className="flex items-center gap-1">
                          <Layers className="w-3 h-3" />
                          {nm.catchphrase_count} 口头禅
                        </span>
                        <span className="flex items-center gap-1">
                          <BookOpen className="w-3 h-3" />
                          {unitCount} 叙事单元
                        </span>
                      </>
                    )}
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTime(p.created_at)}
                    </span>
                  </div>

                  {/* Completeness bar */}
                  {nm && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-text-muted">克隆完整度</span>
                        <span className={`font-medium ${score >= 80 ? 'text-success' : score >= 50 ? 'text-warning' : 'text-error'}`}>
                          {score}%
                        </span>
                      </div>
                      <div className="h-1.5 bg-bg-hover rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            score >= 80 ? 'bg-success' : score >= 50 ? 'bg-warning' : 'bg-error'
                          }`}
                          style={{ width: `${score}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Pending anchors: have transcripts but no persona */}
            {pendingAnchors?.filter(a =>
              a.anchor_name.toLowerCase().includes(search.toLowerCase())
            ).map((a) => (
              <div
                key={a.anchor_name}
                className="bg-bg-card border border-dashed border-border-default rounded-xl p-5 text-left hover:border-brand/30 transition-all duration-200 relative"
              >
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-12 h-12 rounded-full bg-bg-hover flex items-center justify-center text-lg font-semibold text-text-muted shrink-0">
                    {a.anchor_name[0]}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-text-primary truncate">
                      @{a.anchor_name}
                    </p>
                    <p className="text-xs text-text-muted mt-0.5">
                      {a.transcript_count} 条转写文字，待生成人设
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="warning">待建卡</Badge>
                  {a.transcript_count >= 5 && <Badge variant="success">素材充足</Badge>}
                </div>

                <div className="flex items-center gap-4 text-xs text-text-muted mt-3">
                  <span className="flex items-center gap-1">
                    <BookOpen className="w-3 h-3" />
                    {a.transcript_count} 条文字
                  </span>
                </div>

                <button
                  onClick={() => generateMut.mutate(a.anchor_name)}
                  disabled={generating === a.anchor_name || generateMut.isPending}
                  className={`mt-3 w-full flex items-center justify-center gap-1.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                    a.transcript_count >= 3
                      ? 'bg-brand/10 text-brand hover:bg-brand/20'
                      : 'bg-bg-hover text-text-muted cursor-not-allowed'
                  } disabled:opacity-50`}
                >
                  {generating === a.anchor_name ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      AI 分析中...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      创建人设档案
                    </>
                  )}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Persona Confirm */}
      <ConfirmModal
        open={!!deleteTarget}
        title="确认删除"
        message={`确定要删除「${deleteTarget?.name || ''}」吗？此操作不可撤销。`}
        loading={deleteMut.isPending}
        onConfirm={() => { if (deleteTarget) deleteMut.mutate(deleteTarget.id); }}
        onCancel={() => setDeleteTarget(null)}
      />

      {/* Remove Tag Confirm */}
      <ConfirmModal
        open={!!removeTagTarget}
        title="确认删除标签"
        message={`确定要删除标签「${removeTagTarget?.tag || ''}」吗？`}
        confirmText="确认删除"
        loading={patchMut.isPending}
        onConfirm={() => {
          if (removeTagTarget) {
            const p = data?.items?.find((x) => x.id === removeTagTarget.id);
            if (p) patchMut.mutate({ id: removeTagTarget.id, tags: (p.tags || []).filter((t) => t !== removeTagTarget.tag) });
          }
          setRemoveTagTarget(null);
        }}
        onCancel={() => setRemoveTagTarget(null)}
      />
    </div>
  );
}
