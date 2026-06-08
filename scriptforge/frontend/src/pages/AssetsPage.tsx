import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ChevronLeft, ChevronRight, Trash2, Play, Pause,
  FolderOpen, FileVideo, FileAudio, FileText,
  X, Inbox, Save, Pencil, ArrowLeft, Users, User, RefreshCw, Mic, Loader2,
} from 'lucide-react';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import EmptyState from '../components/ui/EmptyState';
import { toast } from '../components/ui/Toast';
import ConfirmModal from '../components/ui/ConfirmModal';
import { listAssets, deleteAsset, getGroupStats, updateAsset, retranscribeAsset, buildVoiceProfile, batchRetranscribe, getBatchRetranscribeStatus, listVoiceProfiles } from '../services/assets';
import { getTaskRecord, listTaskRecords } from '../services/taskRecords';
import type { AssetItem, AssetGroupStats } from '../types';

// ─── Helpers ────────────────────────────────────────────────

const formatSize = (bytes: number): string => {
  if (!bytes) return '-';
  if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${bytes} B`;
};

const formatDuration = (s: number): string => {
  if (!s) return '-';
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return m > 0 ? `${m}:${String(sec).padStart(2, '0')}` : `0:${String(sec).padStart(2, '0')}`;
};

// ─── Skeleton Components ────────────────────────────────────

function SkeletonGroupCard() {
  return (
    <div className="bg-bg-card border border-border-default rounded-lg p-4 animate-pulse">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-bg-hover shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-3.5 w-24 rounded bg-bg-hover" />
          <div className="h-2.5 w-16 rounded bg-bg-hover" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <div className="h-10 rounded-md bg-bg-hover" />
        <div className="h-10 rounded-md bg-bg-hover" />
        <div className="h-10 rounded-md bg-bg-hover" />
      </div>
      <div className="mt-2 h-5 w-20 rounded bg-bg-hover" />
    </div>
  );
}

function SkeletonVideoRow() {
  return (
    <div className="bg-bg-card border border-border-default rounded-lg p-3 animate-pulse">
      <div className="flex items-center gap-3 mb-2">
        <div className="h-4 w-48 rounded bg-bg-hover" />
        <div className="h-3 w-20 rounded bg-bg-hover" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="h-8 rounded bg-bg-hover" />
        <div className="h-8 rounded bg-bg-hover" />
        <div className="h-8 rounded bg-bg-hover" />
      </div>
    </div>
  );
}

function SkeletonGroupGrid() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
      {Array.from({ length: 8 }).map((_, i) => <SkeletonGroupCard key={i} />)}
    </div>
  );
}

// ─── Infinite Scroll Hook ────────────────────────────────────

function useInfiniteAssets(anchor: string | undefined) {
  const [items, setItems] = useState<AssetItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const pageSize = 100;
  const sentinelRef = useRef<HTMLDivElement>(null);
  const pagesLoaded = useRef(0);

  // Reset when anchor changes
  useEffect(() => {
    setItems([]);
    setTotal(0);
    pagesLoaded.current = 0;
  }, [anchor]);

  // Load first page when anchor is set
  const { isLoading } = useQuery({
    queryKey: ['assets-infinite', anchor],
    queryFn: async () => {
      const res = await listAssets({ anchor_name: anchor!, page: 1, page_size: pageSize });
      setItems(res.items);
      setTotal(res.total);
      pagesLoaded.current = 1;
      return res;
    },
    enabled: !!anchor,
  });

  const hasMore = items.length < total;

  const loadMore = useCallback(async () => {
    if (!anchor || loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const nextPage = pagesLoaded.current + 1;
      const res = await listAssets({ anchor_name: anchor, page: nextPage, page_size: pageSize });
      setItems(prev => [...prev, ...res.items]);
      pagesLoaded.current = nextPage;
    } finally {
      setLoadingMore(false);
    }
  }, [anchor, loadingMore, hasMore]);

  // Intersection Observer for sentinel
  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      entries => { if (entries[0].isIntersecting) loadMore(); },
      { rootMargin: '200px' },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [loadMore]);

  return { items, total, isLoading, loadingMore, hasMore, sentinelRef };
};

// ─── Audio Player Hook ──────────────────────────────────────

function useAudioPlayer() {
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [audioEl, setAudioEl] = useState<HTMLAudioElement | null>(null);

  const toggle = useCallback((asset: AssetItem) => {
    if (playingId === asset.id && audioEl) {
      audioEl.pause();
      setPlayingId(null);
      setAudioEl(null);
      return;
    }
    if (audioEl) {
      audioEl.pause();
    }
    if (!asset.video_url && !asset.file_path) return;
    const src = asset.video_url || `/uploads/videos/${asset.file_path.split(/[\\/]/).pop()}`;
    const el = new Audio(src);
    el.onended = () => { setPlayingId(null); setAudioEl(null); };
    el.onerror = () => { toast('error', '音频播放失败'); setPlayingId(null); setAudioEl(null); };
    el.play();
    setPlayingId(asset.id);
    setAudioEl(el);
  }, [playingId, audioEl]);

  const stop = useCallback(() => {
    if (audioEl) { audioEl.pause(); }
    setPlayingId(null);
    setAudioEl(null);
  }, [audioEl]);

  return { playingId, toggle, stop };
}

// ─── Level 1: Group Cards ───────────────────────────────────

function GroupCard({
  group, onClick, hasProfile, onBuildProfile, onBatchRetranscribe, building, retranscribing, progress,
}: {
  group: AssetGroupStats;
  onClick: () => void;
  hasProfile: boolean;
  onBuildProfile: () => void;
  onBatchRetranscribe: () => void;
  building: boolean;
  retranscribing: boolean;
  progress: { current: number; total: number } | null;
}) {
  return (
    <div
      className="bg-bg-card border border-border-default rounded-lg p-4 cursor-pointer
        hover:-translate-y-0.5 hover:border-brand/50 transition-all duration-200 group"
    >
      <div onClick={onClick} className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-brand/15 flex items-center justify-center shrink-0">
          {group.persona_name ? (
            <User className="w-5 h-5 text-brand" />
          ) : (
            <Users className="w-5 h-5 text-brand" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-text-primary truncate">
            {group.persona_name || group.anchor_name}
          </h3>
          {group.persona_name && (
            <p className="text-xs text-text-muted truncate">主播：{group.anchor_name}</p>
          )}
        </div>
      </div>

      <div onClick={onClick} className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-blue-400/10 rounded-md py-1.5 px-2">
          <p className="text-base font-semibold text-blue-400">{group.video_count}</p>
          <p className="text-[10px] text-text-muted">视频</p>
        </div>
        <div className="bg-amber-400/10 rounded-md py-1.5 px-2">
          <p className="text-base font-semibold text-amber-400">{group.audio_count}</p>
          <p className="text-[10px] text-text-muted">音频</p>
        </div>
        <div className="bg-emerald-400/10 rounded-md py-1.5 px-2">
          <p className="text-base font-semibold text-emerald-400">{group.transcript_count}</p>
          <p className="text-[10px] text-text-muted">文本</p>
        </div>
      </div>

      {/* Voice profile / retranscribe actions */}
      <div className="mt-2 flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
        {hasProfile ? (
          <>
            <span className="text-[10px] text-success flex items-center gap-0.5">
              <Mic className="w-3 h-3" /> 声纹已建档
            </span>
            <button
              onClick={onBatchRetranscribe}
              disabled={retranscribing}
              className="ml-auto inline-flex items-center gap-1 px-2 py-1 rounded text-[11px]
                text-brand hover:bg-brand/10 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3 h-3 ${retranscribing ? 'animate-spin' : ''}`} />
              {retranscribing && progress ? `${progress.current}/${progress.total}` : '全部重新转写'}
            </button>
          </>
        ) : group.audio_count >= 8 ? (
          <button
            onClick={onBuildProfile}
            disabled={building}
            className="ml-auto inline-flex items-center gap-1 px-2 py-1 rounded text-[11px]
              text-amber-400 hover:bg-amber-400/10 transition-colors disabled:opacity-50"
          >
            <Mic className={`w-3 h-3 ${building ? 'animate-pulse' : ''}`} />
            {building ? '建档中...' : '声纹建档'}
          </button>
        ) : (
          <span className="text-[10px] text-text-muted">
            需 ≥8 条音频方可建档（当前 {group.audio_count}）
          </span>
        )}
      </div>

      <div onClick={onClick} className="mt-2 text-[11px] text-text-muted text-right">
        总计 {formatSize(group.total_size)}
      </div>
    </div>
  );
}

// ─── Level 2: Video Row (video → audio → text) ─────────────

function VideoRow({
  video, audio, transcript, playingId, onToggleAudio, onDelete, onUpdateText, onRetranscribe, retranscribingId, retranscribeProgress,
}: {
  video: AssetItem | undefined;
  audio: AssetItem | undefined;
  transcript: AssetItem | undefined;
  playingId: string | null;
  onToggleAudio: (asset: AssetItem) => void;
  onDelete: (id: string) => void;
  onUpdateText: (id: string, text: string) => void;
  onRetranscribe: (id: string) => void;
  retranscribingId: string | null;
  retranscribeProgress: { assetId: string; pct: number; eta: number | null; message: string } | null;
}) {
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState('');
  const [saving, setSaving] = useState(false);
  const title = video?.video_title || audio?.video_title || transcript?.video_title || '未命名视频';

  const startEdit = () => {
    setEditText(transcript?.transcription_text || '');
    setEditing(true);
  };

  const saveText = async () => {
    setSaving(true);
    try {
      await onUpdateText(transcript!.id, editText);
      setEditing(false);
      toast('success', '文字已保存');
    } catch {
      toast('error', '保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-bg-card border border-border-default rounded-lg p-3 hover:border-border-focus transition-colors">
      {/* Title + meta */}
      <div className="flex items-center gap-3 mb-2">
        <p className="text-sm font-medium text-text-primary truncate flex-1">{title}</p>
        <div className="flex items-center gap-1.5 shrink-0 text-[10px] text-text-muted">
          {video?.duration && <span className="font-mono">{formatDuration(video.duration)}</span>}
          {video && <span>{formatSize(video.file_size)}</span>}
        </div>
      </div>

      {/* Two-column: left (video+audio) | right (transcript) */}
      <div className="flex gap-3">
        {/* Left: Video + Audio stacked */}
        <div className="w-[200px] shrink-0 space-y-2">
          {/* Video */}
          <div>
            <div className="flex items-center gap-1 text-[10px] text-text-muted mb-1">
              <FileVideo className="w-3 h-3 text-blue-400" />
              <span>视频</span>
            </div>
            {video?.video_url ? (
              <video
                src={video.video_url}
                controls
                className="w-full h-[90px] rounded-md bg-black object-contain"
                preload="metadata"
              />
            ) : (
              <div className="w-full h-[90px] rounded-md bg-bg-hover flex items-center justify-center">
                <span className="text-xs text-text-muted">无视频</span>
              </div>
            )}
          </div>

          {/* Audio */}
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1 text-[10px] text-text-muted">
                <FileAudio className="w-3 h-3 text-amber-400" />
                <span>音频</span>
                {audio?.duration && <span className="font-mono">{formatDuration(audio.duration)}</span>}
              </div>
              {audio && (
                retranscribingId === audio.id && retranscribeProgress?.assetId === audio.id ? (
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-bg-hover rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-brand to-brand-hover rounded-full transition-all duration-500"
                          style={{ width: `${retranscribeProgress.pct}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-text-muted font-mono w-7 text-right">{retranscribeProgress.pct}%</span>
                    </div>
                    {retranscribeProgress.message && (
                      <p className="text-[10px] text-text-muted truncate">
                        {retranscribeProgress.eta != null && retranscribeProgress.eta > 0
                          ? `预计还需 ${Math.ceil(retranscribeProgress.eta)} 秒`
                          : retranscribeProgress.message}
                      </p>
                    )}
                  </div>
                ) : (
                  <button
                    onClick={() => onRetranscribe(audio.id)}
                    disabled={!!retranscribingId}
                    className="p-0.5 rounded text-text-muted hover:text-amber-400 hover:bg-amber-400/10 transition-colors disabled:opacity-50"
                    title="重新识别（人声分离 + ASR）"
                  >
                    <RefreshCw className="w-3 h-3" />
                  </button>
                )
              )}
            </div>
            {audio ? (
              <div className="w-full h-[36px] rounded-md bg-bg-hover flex items-center justify-center gap-3">
                <button
                  onClick={() => onToggleAudio(audio)}
                  className="w-7 h-7 rounded-full bg-amber-400/20 flex items-center justify-center
                    hover:bg-amber-400/40 transition-colors"
                >
                  {playingId === audio.id ? (
                    <Pause className="w-3.5 h-3.5 text-amber-400" />
                  ) : (
                    <Play className="w-3.5 h-3.5 text-amber-400 ml-0.5" />
                  )}
                </button>
                <div className="flex items-center gap-[1.5px]">
                  {[8, 14, 6, 16, 10, 12, 5, 15].map((h, i) => (
                    <div
                      key={i}
                      className={`w-[1.5px] rounded-full ${playingId === audio.id ? 'bg-amber-400' : 'bg-amber-400/30'}`}
                      style={{
                        height: `${h}px`,
                        animation: playingId === audio.id ? `waveBar 1.2s ease-in-out ${i * 0.1}s infinite alternate` : 'none',
                      }}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <div className="w-full h-[36px] rounded-md bg-bg-hover flex items-center justify-center">
                <span className="text-[10px] text-text-muted">无音频</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Transcript */}
        <div className="flex-1 min-w-0 flex flex-col">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-1 text-[10px] text-text-muted">
              <FileText className="w-3 h-3 text-emerald-400" />
              <span>文字</span>
              {transcript && (
                <span className="text-text-muted">
                  {transcript.transcription_text ? `${transcript.transcription_text.length} 字` : ''}
                </span>
              )}
            </div>
            {transcript && !editing && (
              <button
                onClick={startEdit}
                className="p-1 rounded text-text-muted hover:text-brand hover:bg-brand/10 transition-colors"
                title="编辑文字"
              >
                <Pencil className="w-3 h-3" />
              </button>
            )}
          </div>
          {transcript ? (
            editing ? (
              <div className="relative flex-1">
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="w-full h-full min-h-[120px] bg-bg-hover border border-border-default rounded-md p-2 text-xs
                    text-text-primary leading-relaxed resize-none outline-none focus:border-brand"
                />
                <div className="absolute bottom-2 right-2 flex gap-1">
                  <button
                    onClick={() => setEditing(false)}
                    className="p-1 rounded bg-bg-card border border-border-default text-text-muted hover:text-text-primary"
                  >
                    <X className="w-3 h-3" />
                  </button>
                  <button
                    onClick={saveText}
                    disabled={saving}
                    className="p-1 rounded bg-brand text-white hover:bg-brand/80 disabled:opacity-50"
                  >
                    {saving ? <Spinner size={12} className="text-white" /> : <Save className="w-3 h-3" />}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex-1 max-h-[200px] rounded-md bg-bg-hover p-2.5 overflow-y-auto text-xs text-text-secondary leading-relaxed whitespace-pre-wrap">
                {transcript.transcription_text || '暂无转写内容'}
              </div>
            )
          ) : (
            <div className="flex-1 min-h-[120px] rounded-md bg-bg-hover flex items-center justify-center">
              <span className="text-xs text-text-muted">无文字</span>
            </div>
          )}
        </div>
      </div>

      {/* Bottom actions */}
      <div className="flex items-center justify-end mt-2">
        <div className="flex gap-1">
          {video && (
            <button
              onClick={() => onDelete(video.id)}
              className="p-1 text-text-muted hover:text-error transition-colors"
              title="删除视频"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          )}
          {audio && (
            <button
              onClick={() => onDelete(audio.id)}
              className="p-1 text-text-muted hover:text-error transition-colors"
              title="删除音频"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          )}
          {transcript && (
            <button
              onClick={() => onDelete(transcript.id)}
              className="p-1 text-text-muted hover:text-error transition-colors"
              title="删除文字"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────

export default function AssetsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const qc = useQueryClient();
  const [selectedAnchor, setSelectedAnchor] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [retranscribingId, setRetranscribingId] = useState<string | null>(null);
  const [retranscribeProgress, setRetranscribeProgress] = useState<{
    assetId: string; pct: number; eta: number | null; message: string;
  } | null>(null);
  const retranscribePollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [buildingProfile, setBuildingProfile] = useState<string | null>(null);
  const [batchRetranscribing, setBatchRetranscribing] = useState<string | null>(null);
  const [batchProgress, setBatchProgress] = useState<{ anchor: string; current: number; total: number } | null>(null);
  const batchPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Auto-resume running tasks on mount / page refresh ──
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { items } = await listTaskRecords({ status: 'running', page_size: 10 });
        if (cancelled || items.length === 0) return;

        for (const tr of items) {
          if (tr.trigger === 'batch_retranscribe') {
            // Resume batch progress
            setBatchRetranscribing(tr.anchor_name);
            setBatchProgress({ anchor: tr.anchor_name, current: tr.transcribed_count || 0, total: tr.video_count });
            const tid = tr.task_id;
            batchPollRef.current = setInterval(async () => {
              try {
                const s = await getBatchRetranscribeStatus(tid);
                setBatchProgress({ anchor: tr.anchor_name, current: s.progress, total: s.total });
                if (s.result_summary?.message) {
                  toast('info', s.result_summary.message, { duration: 2500 });
                }
                if (s.status === 'completed' || s.status === 'failed') {
                  if (batchPollRef.current) clearInterval(batchPollRef.current);
                  setBatchRetranscribing(null);
                  setBatchProgress(null);
                  if (s.status === 'completed') toast('success', `批量重转写完成：${s.progress}/${s.total}`);
                  else toast('error', s.error_message || '批量重转写失败');
                  qc.invalidateQueries({ queryKey: ['assets-group-stats'] });
                  qc.invalidateQueries({ queryKey: ['assets-infinite'] });
                }
              } catch { /* ignore */ }
            }, 3000);
            break; // Only one batch at a time
          }

          if (tr.trigger === 'retranscribe') {
            // Resume single retranscribe progress
            const rs = tr.result_summary as Record<string, unknown> | null;
            setRetranscribingId('__resumed__');
            setRetranscribeProgress({
              assetId: '__resumed__',
              pct: (rs?.progress_pct as number) || 0,
              eta: (rs?.eta_seconds as number) ?? null,
              message: (rs?.message as string) || '恢复中...',
            });
            const tid = tr.task_id;
            retranscribePollRef.current = setInterval(async () => {
              try {
                const t = await getTaskRecord(tid);
                const tRs = t.result_summary as Record<string, unknown> | null;
                if (t.status === 'completed' || t.status === 'failed') {
                  if (retranscribePollRef.current) clearInterval(retranscribePollRef.current);
                  setRetranscribingId(null);
                  setRetranscribeProgress(null);
                  if (t.status === 'completed') toast('success', '重新识别完成');
                  else toast('error', t.error_message || '重新识别失败');
                  qc.invalidateQueries({ queryKey: ['assets-infinite'] });
                } else if (tRs) {
                  setRetranscribeProgress({
                    assetId: '__resumed__',
                    pct: (tRs.progress_pct as number) || 0,
                    eta: (tRs.eta_seconds as number) ?? null,
                    message: (tRs.message as string) || '',
                  });
                }
              } catch { /* ignore */ }
            }, 3000);
          }
        }
      } catch { /* ignore */ }
    })();
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Support URL-based task_id filter
  const urlTaskId = searchParams.get('task_id') || undefined;

  const audioPlayer = useAudioPlayer();

  // Level 1: group stats
  const { data: groups, isLoading: groupsLoading } = useQuery({
    queryKey: ['assets-group-stats'],
    queryFn: getGroupStats,
  });

  // Voice profiles lookup
  const { data: voiceProfilesData } = useQuery({
    queryKey: ['voice-profiles'],
    queryFn: listVoiceProfiles,
  });
  const profileSet = useMemo(() => {
    const set = new Set<string>();
    for (const p of voiceProfilesData?.profiles || []) set.add(p.anchor_name);
    return set;
  }, [voiceProfilesData]);

  // Level 2: infinite scroll assets for selected anchor
  const {
    items: assetItems,
    total,
    isLoading: assetsLoading,
    loadingMore,
    hasMore,
    sentinelRef,
  } = useInfiniteAssets(selectedAnchor);

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteAsset(id),
    onSuccess: () => {
      toast('success', '资产已删除');
      setDeleteId(null);
      qc.invalidateQueries({ queryKey: ['assets-infinite'] });
      qc.invalidateQueries({ queryKey: ['assets-group-stats'] });
    },
    onError: (err: any) => toast('error', err?.response?.data?.detail || '删除失败'),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, text }: { id: string; text: string }) => updateAsset(id, { transcription_text: text }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets-infinite'] });
    },
    onError: (err: any) => toast('error', err?.response?.data?.detail || '更新失败'),
  });

  // Group assets by video_title for the three-column view
  const videoRows = useMemo(() => {
    const grouped = new Map<string, { video?: AssetItem; audio?: AssetItem; transcript?: AssetItem }>();

    for (const a of assetItems) {
      const key = a.video_title || a.task_id;
      const existing = grouped.get(key) || {};
      if (a.asset_type === 'video') existing.video = a;
      else if (a.asset_type === 'audio') existing.audio = a;
      else if (a.asset_type === 'transcript') existing.transcript = a;
      grouped.set(key, existing);
    }

    return Array.from(grouped.entries()).map(([title, assets]) => ({
      title,
      ...assets,
    }));
  }, [assetItems]);

  const handleUpdateText = async (id: string, text: string) => {
    await updateMut.mutateAsync({ id, text });
  };

  const handleRetranscribe = async (id: string) => {
    setRetranscribingId(id);
    setRetranscribeProgress({ assetId: id, pct: 0, eta: null, message: '正在启动...' });
    try {
      const res = await retranscribeAsset(id);
      const taskId = res.task_id;

      retranscribePollRef.current = setInterval(async () => {
        try {
          const tr = await getTaskRecord(taskId);
          const rs = tr.result_summary as Record<string, unknown> | null;
          if (tr.status === 'completed') {
            if (retranscribePollRef.current) clearInterval(retranscribePollRef.current);
            setRetranscribingId(null);
            setRetranscribeProgress(null);
            toast('success', '重新识别完成，文字已更新');
            qc.invalidateQueries({ queryKey: ['assets-by-anchor'] });
          } else if (tr.status === 'failed') {
            if (retranscribePollRef.current) clearInterval(retranscribePollRef.current);
            setRetranscribingId(null);
            setRetranscribeProgress(null);
            toast('error', tr.error_message || '重新识别失败');
          } else if (rs) {
            setRetranscribeProgress({
              assetId: id,
              pct: (rs.progress_pct as number) || 0,
              eta: (rs.eta_seconds as number) ?? null,
              message: (rs.message as string) || '',
            });
          }
        } catch {
          // ignore poll errors
        }
      }, 3000);
    } catch (err: any) {
      setRetranscribingId(null);
      setRetranscribeProgress(null);
      toast('error', err?.response?.data?.detail || '重新识别失败');
    }
  };

  const handleBuildProfile = async (anchorName: string) => {
    setBuildingProfile(anchorName);
    try {
      const res = await buildVoiceProfile(anchorName);
      toast('success', `声纹建档完成：${res.audio_count} 条音频，维度 ${res.embedding_dim}`);
      qc.invalidateQueries({ queryKey: ['voice-profiles'] });
    } catch (err: any) {
      toast('error', err?.response?.data?.detail || '声纹建档失败');
    } finally {
      setBuildingProfile(null);
    }
  };

  const handleBatchRetranscribe = async (anchorName: string) => {
    setBatchRetranscribing(anchorName);
    setBatchProgress({ anchor: anchorName, current: 0, total: 0 });
    try {
      const res = await batchRetranscribe(anchorName);
      const total = res.total;
      setBatchProgress({ anchor: anchorName, current: 0, total });
      toast('info', `批量重转写已启动，共 ${total} 条音频`);

      // Poll progress every 3s
      const taskId = res.task_id;
      batchPollRef.current = setInterval(async () => {
        try {
          const s = await getBatchRetranscribeStatus(taskId);
          setBatchProgress({ anchor: anchorName, current: s.progress, total: s.total });
          if (s.result_summary?.message) {
            toast('info', s.result_summary.message, { duration: 2500 });
          }
          if (s.status === 'completed') {
            if (batchPollRef.current) clearInterval(batchPollRef.current);
            setBatchRetranscribing(null);
            setBatchProgress(null);
            toast('success', `批量重转写完成：${s.progress}/${s.total}`);
            qc.invalidateQueries({ queryKey: ['assets-group-stats'] });
            qc.invalidateQueries({ queryKey: ['assets-by-anchor'] });
          } else if (s.status === 'failed') {
            if (batchPollRef.current) clearInterval(batchPollRef.current);
            setBatchRetranscribing(null);
            setBatchProgress(null);
            toast('error', s.error_message || '批量重转写失败');
          }
        } catch {
          // ignore poll errors
        }
      }, 3000);
    } catch (err: any) {
      setBatchRetranscribing(null);
      setBatchProgress(null);
      toast('error', err?.response?.data?.detail || '启动批量重转写失败');
    }
  };

  // ─── Level 2 View (selected anchor) ───
  if (selectedAnchor) {
    const anchorGroups = groups?.filter(g => g.anchor_name === selectedAnchor);
    const currentGroup = anchorGroups?.[0];

    return (
      <div className="h-[calc(100vh-3.5rem-3rem)] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="shrink-0 border-b border-border-default px-6 py-3 flex items-center gap-3">
          <button
            onClick={() => { audioPlayer.stop(); setSelectedAnchor(null); }}
            className="p-1.5 rounded-md text-text-secondary hover:bg-bg-hover transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="min-w-0 flex-1">
            <h2 className="text-base font-semibold text-text-primary truncate">
              {currentGroup?.persona_name || selectedAnchor}
            </h2>
            {currentGroup?.persona_name && (
              <p className="text-xs text-text-muted">主播：{selectedAnchor}</p>
            )}
          </div>
          <div className="flex gap-2">
            <Badge variant="default" className="text-[10px]">
              <FileVideo className="w-3 h-3 mr-1 text-blue-400" />
              {currentGroup?.video_count || 0} 视频
            </Badge>
            <Badge variant="default" className="text-[10px]">
              <FileAudio className="w-3 h-3 mr-1 text-amber-400" />
              {currentGroup?.audio_count || 0} 音频
            </Badge>
            <Badge variant="default" className="text-[10px]">
              <FileText className="w-3 h-3 mr-1 text-emerald-400" />
              {currentGroup?.transcript_count || 0} 文本
            </Badge>
          </div>
        </div>

        {/* Batch retranscribe progress bar */}
        {batchRetranscribing === selectedAnchor && batchProgress && (
          <div className="shrink-0 border-t border-border-default px-6 py-2 flex items-center gap-3 bg-brand/5">
            <Loader2 className="w-4 h-4 text-brand animate-spin shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-text-primary font-medium">
                  批量转写中 {batchProgress.current}/{batchProgress.total}
                </span>
                <span className="text-text-muted">
                  {batchProgress.total > 0 ? Math.round((batchProgress.current / batchProgress.total) * 100) : 0}%
                </span>
              </div>
              <div className="h-1 bg-bg-hover rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand rounded-full transition-all duration-500"
                  style={{ width: `${batchProgress.total > 0 ? (batchProgress.current / batchProgress.total) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {assetsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 6 }).map((_, i) => <SkeletonVideoRow key={i} />)}
            </div>
          ) : videoRows.length === 0 ? (
            <EmptyState
              icon={Inbox}
              title="暂无素材"
              description="该主播下没有素材资产"
            />
          ) : (
            <>
              {videoRows.map((row) => (
                <VideoRow
                  key={row.title}
                  video={row.video}
                  audio={row.audio}
                  transcript={row.transcript}
                  playingId={audioPlayer.playingId}
                  onToggleAudio={audioPlayer.toggle}
                  onDelete={(id) => setDeleteId(id)}
                  onUpdateText={handleUpdateText}
                  onRetranscribe={handleRetranscribe}
                  retranscribingId={retranscribingId}
                  retranscribeProgress={retranscribeProgress}
                />
              ))}

              {/* Infinite scroll sentinel + status */}
              <div ref={sentinelRef} className="h-1" />
              <div className="flex items-center justify-center gap-2 py-3 text-xs text-text-muted">
                {loadingMore && (
                  <>
                    <Spinner size={14} className="text-brand" />
                    <span>加载更多...</span>
                  </>
                )}
                {!hasMore && videoRows.length > 0 && (
                  <span>共 {total} 条素材已全部加载</span>
                )}
              </div>
            </>
          )}
        </div>

        {/* Delete modal */}
        {deleteId && (
          <ConfirmModal
            open={!!deleteId}
            title="确认删除"
            message="确定要删除此资产吗？关联的文件也会被删除，此操作不可恢复。"
            loading={deleteMut.isPending}
            onConfirm={() => deleteMut.mutate(deleteId!)}
            onCancel={() => setDeleteId(null)}
          />
        )}
      </div>
    );
  }

  // ─── Level 1 View (group cards) ───
  return (
    <div className="h-[calc(100vh-3.5rem-3rem)] overflow-y-auto p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text-primary">素材资产</h2>
        <p className="text-xs text-text-muted">按人设/主播分组管理素材</p>
      </div>

      {groupsLoading ? (
        <SkeletonGroupGrid />
      ) : !groups || groups.length === 0 ? (
        <EmptyState
          icon={Inbox}
          title="暂无素材资产"
          description='请在"学习中心"提交抖音用户、视频链接或上传文件，处理完成后素材将自动归档到这里'
          actions={[
            { label: '前往学习中心', onClick: () => navigate('/learn'), variant: 'secondary' },
          ]}
        />
      ) : (
        <>
          {/* Summary stats */}
          <div className="grid grid-cols-4 gap-3">
            <div className="bg-bg-card border border-border-default rounded-lg p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-brand/15">
                <Users className="w-5 h-5 text-brand" />
              </div>
              <div>
                <p className="text-xl font-semibold text-text-primary">{groups.length}</p>
                <p className="text-xs text-text-muted">人设/主播</p>
              </div>
            </div>
            <div className="bg-bg-card border border-border-default rounded-lg p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-blue-400/15">
                <FileVideo className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xl font-semibold text-text-primary">
                  {groups.reduce((s, g) => s + g.video_count, 0)}
                </p>
                <p className="text-xs text-text-muted">视频</p>
              </div>
            </div>
            <div className="bg-bg-card border border-border-default rounded-lg p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-amber-400/15">
                <FileAudio className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xl font-semibold text-text-primary">
                  {groups.reduce((s, g) => s + g.audio_count, 0)}
                </p>
                <p className="text-xs text-text-muted">音频</p>
              </div>
            </div>
            <div className="bg-bg-card border border-border-default rounded-lg p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-emerald-400/15">
                <FileText className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-xl font-semibold text-text-primary">
                  {groups.reduce((s, g) => s + g.transcript_count, 0)}
                </p>
                <p className="text-xs text-text-muted">文本</p>
              </div>
            </div>
          </div>

          {/* Group cards grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
            {groups.map((g) => (
              <GroupCard
                key={g.anchor_name}
                group={g}
                hasProfile={profileSet.has(g.anchor_name)}
                onClick={() => setSelectedAnchor(g.anchor_name)}
                onBuildProfile={() => handleBuildProfile(g.anchor_name)}
                onBatchRetranscribe={() => handleBatchRetranscribe(g.anchor_name)}
                building={buildingProfile === g.anchor_name}
                retranscribing={batchRetranscribing === g.anchor_name}
                progress={batchRetranscribing === g.anchor_name ? batchProgress : null}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
