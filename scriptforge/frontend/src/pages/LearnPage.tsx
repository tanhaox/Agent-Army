import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import {
  BookOpen, Link, Users, Upload, ChevronDown, ChevronRight,
  Zap, Sparkles, ArrowRight, Lock, CheckCircle,
} from 'lucide-react';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import { toast } from '../components/ui/Toast';
import TxtUploader from './learn/TxtUploader';
import RadarChart from './learn/RadarChart';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import MaterialEditor from './learn/MaterialEditor';
import VerificationPanel from './learn/VerificationPanel';
import ProgressPanel from './learn/ProgressPanel';
import type { ProgressEvent } from './learn/ProgressPanel';
import { batchTranscribe, getTaskStatus } from '../services/asr';
import { importFromUrl, getImportTaskStatus } from '../services/importer';
import { importDouyinUser, getUserProfile } from '../services/douyin';
import { analyzePersona, getPersona } from '../services/persona';
import { batchExtractStrategies } from '../services/strategies';
import type { PersonaDetail } from '../types';
import type { AnchorProfile } from '../types';
import type { ExtractResult } from '../services/strategies';

const VIDEO_EXTS = ['.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav', '.flac'];
const ACCEPT_VIDEO = VIDEO_EXTS.join(',');
const MAX_FILE_SIZE = 500 * 1024 * 1024;

export interface MaterialItem {
  id: string;
  type: 'video' | 'audio' | 'txt';
  name: string;
  rawText: string;
  editedText: string;
  sourceUrl?: string;
  audioPath?: string;
  segments?: { start: number; end: number; text: string }[];
  duration?: number;
  status: 'pending' | 'processing' | 'done' | 'error';
  selected: boolean;
}

let _idCounter = 0;
const nextId = () => `mat_${++_idCounter}_${Date.now()}`;

function formatCount(n: number): string {
  if (n >= 100000000) return `${(n / 100000000).toFixed(1)}亿`;
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`;
  return String(n);
}

export default function LearnPage() {
  const navigate = useNavigate();

  // ---- Core state ----
  const [materials, setMaterials] = useState<MaterialItem[]>([]);
  const [isVerified, setIsVerified] = useState(false);
  const [verifiedText, setVerifiedText] = useState('');

  // ---- Zone 4 results ----
  const [personaId, setPersonaId] = useState<string | null>(null);
  const [personaDetail, setPersonaDetail] = useState<PersonaDetail | null>(null);
  const [strategyResult, setStrategyResult] = useState<ExtractResult | null>(null);

  // ---- SSE streaming progress ----
  const [progressEvents, setProgressEvents] = useState<ProgressEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  // ---- Anchor Profile ----
  const [anchorProfile, setAnchorProfile] = useState<AnchorProfile | null>(null);

  const profileMut = useMutation({
    mutationFn: (url: string) => getUserProfile(url),
    onSuccess: (profile) => setAnchorProfile(profile),
    onError: () => { /* silent — don't block main flow */ },
  });

  // ---- Zone 1: Method A — Douyin User ----
  const [dyUserUrl, setDyUserUrl] = useState('');
  const [dyUserCount, setDyUserCount] = useState(5);

  const handleDyUrlBlur = useCallback(() => {
    const url = dyUserUrl.trim();
    if (url && /douyin\.com\/user\//.test(url) && !anchorProfile && !profileMut.isPending) {
      profileMut.mutate(url);
    }
  }, [dyUserUrl, anchorProfile, profileMut]);

  const dyUserMut = useMutation({
    mutationFn: () => importDouyinUser(dyUserUrl.trim(), dyUserCount),
    onSuccess: (res) => {
      const items: MaterialItem[] = res.downloaded.map((v) => ({
        id: nextId(),
        type: 'video' as const,
        name: v.desc || v.aweme_id,
        rawText: '',
        editedText: '',
        sourceUrl: v.source_url,
        audioPath: v.audio_path,
        duration: v.duration,
        status: 'pending' as const,
        selected: true,
      }));
      setMaterials((prev) => [...prev, ...items]);
      setDyUserUrl('');
      toast('success', `已拉取 ${res.downloaded.length} 个视频`);
      if (res.failed.length) toast('warning', `${res.failed.length} 个失败`);
    },
    onError: (err: any) => toast('error', err?.response?.data?.detail || '抖音拉取失败'),
  });

  // ---- Zone 1: Method B — Single URL ----
  const [singleUrl, setSingleUrl] = useState('');
  const [singlePolling, setSinglePolling] = useState(false);
  const singleTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const singleUrlMut = useMutation({
    mutationFn: () => importFromUrl(singleUrl.trim()),
    onSuccess: (res) => {
      setSingleUrl('');
      if (res.status === 'SUCCESS' && res.result) {
        const text = res.result.transcription?.text || '';
        const segs = res.result.transcription?.segments || [];
        const item: MaterialItem = {
          id: nextId(),
          type: 'video',
          name: res.result.source_url?.slice(0, 60) || '视频导入',
          rawText: text,
          editedText: text,
          sourceUrl: res.result.source_url,
          audioPath: res.result.audio_path,
          segments: segs,
          duration: res.result.transcription?.duration,
          status: 'done',
          selected: true,
        };
        setMaterials((prev) => [...prev, item]);
        if (res.result.warning) toast('warning', res.result.warning);
        else toast('success', '视频导入转写完成');
        return;
      }
      // Async mode — poll
      setSinglePolling(true);
      const tmpItem: MaterialItem = {
        id: nextId(),
        type: 'video',
        name: singleUrl.trim().slice(0, 60),
        rawText: '',
        editedText: '',
        sourceUrl: singleUrl.trim(),
        status: 'processing',
        selected: true,
      };
      const idx = materials.length;
      setMaterials((prev) => [...prev, tmpItem]);
      const taskId = res.task_id;
      singleTimer.current = setInterval(async () => {
        try {
          const s = await getImportTaskStatus(taskId);
          if (s.status === 'success') {
            clearInterval(singleTimer.current!);
            setSinglePolling(false);
            const t = s.result?.transcription?.text || '';
            setMaterials((prev) =>
              prev.map((m, i) => i === idx ? { ...m, rawText: t, editedText: t, status: 'done' as const, segments: s.result?.transcription?.segments, duration: s.result?.transcription?.duration } : m)
            );
            toast('success', '视频导入转写完成');
          } else if (s.status === 'failed') {
            clearInterval(singleTimer.current!);
            setSinglePolling(false);
            setMaterials((prev) => prev.map((m, i) => i === idx ? { ...m, status: 'error' as const } : m));
            toast('error', s.error || '导入失败');
          }
        } catch {
          clearInterval(singleTimer.current!);
          setSinglePolling(false);
        }
      }, 3000);
    },
    onError: (err: any) => toast('error', err?.response?.data?.detail || '导入失败'),
  });

  // ---- Zone 1: Method C — Video/Audio upload ----
  const [videoPolling, setVideoPolling] = useState(false);
  const [videoProgress, setVideoProgress] = useState({ current: 0, total: 0 });
  const videoTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const handleVideoInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const items: MaterialItem[] = files.map((f) => ({
      id: nextId(),
      type: (f.name.match(/\.(mp4|avi|mov|mkv)$/i) ? 'video' : 'audio') as MaterialItem['type'],
      name: f.name,
      rawText: '',
      editedText: '',
      status: 'pending' as const,
      selected: true,
    }));
    setMaterials((prev) => [...prev, ...items]);
    e.target.value = '';
  }, []);

  const batchMut = useMutation({
    mutationFn: async () => {
      const pending = materials.filter((m) => m.status === 'pending' && m.type !== 'txt');
      if (!pending.length) throw new Error('没有待转写的文件');
      // We need the actual File objects — for simplicity, trigger batch via upload
      return { task_id: 'manual', file_count: pending.length, pending };
    },
    onSuccess: () => {
      toast('warning', '请使用文件上传方式直接拖拽视频/音频文件');
    },
  });

  const handleVideoDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files).filter(
      (f) => f.size <= MAX_FILE_SIZE && VIDEO_EXTS.some((ext) => f.name.toLowerCase().endsWith(ext))
    );
    if (!files.length) return;
    // Start transcription immediately
    const items: MaterialItem[] = files.map((f) => ({
      id: nextId(),
      type: (f.name.match(/\.(mp4|avi|mov|mkv)$/i) ? 'video' : 'audio') as MaterialItem['type'],
      name: f.name,
      rawText: '',
      editedText: '',
      status: 'processing' as const,
      selected: true,
    }));
    const startIdx = materials.length;
    setMaterials((prev) => [...prev, ...items]);
    setVideoPolling(true);
    setVideoProgress({ current: 0, total: files.length });

    batchTranscribe(files)
      .then((res) => {
        const taskId = res.task_id;
        videoTimer.current = setInterval(async () => {
          try {
            const s = await getTaskStatus(taskId);
            if (s.status === 'SUCCESS') {
              clearInterval(videoTimer.current!);
              setVideoPolling(false);
              const results = s.result || [];
              let ri = 0;
              setMaterials((prev) =>
                prev.map((m, i) => {
                  if (i < startIdx || m.status !== 'processing') return m;
                  const r = results[ri++];
                  if (r && !r.error) return { ...m, rawText: r.text, editedText: r.text, status: 'done' as const, segments: r.segments, duration: r.duration };
                  return { ...m, status: 'error' as const };
                })
              );
              setVideoProgress({ current: results.length, total: results.length });
              toast('success', '转写完成');
            } else if (s.status === 'FAILURE') {
              clearInterval(videoTimer.current!);
              setVideoPolling(false);
              toast('error', '转写任务失败');
              setMaterials((prev) => prev.map((m) => m.status === 'processing' ? { ...m, status: 'error' as const } : m));
            } else if (s.status === 'PROCESSING') {
              const meta = (s as any).meta;
              if (meta?.current && meta?.total) setVideoProgress({ current: meta.current, total: meta.total });
            }
          } catch {
            clearInterval(videoTimer.current!);
            setVideoPolling(false);
          }
        }, 2000);
      })
      .catch((err) => {
        setVideoPolling(false);
        toast('error', '转写提交失败');
        setMaterials((prev) => prev.map((m) => m.status === 'processing' ? { ...m, status: 'error' as const } : m));
      });
  }, [materials.length]);

  // ---- Zone 1: Method D — TXT upload ----
  const [txtFiles, setTxtFiles] = useState<File[]>([]);

  const handleTxtConfirm = useCallback(async () => {
    if (!txtFiles.length) return;
    const texts = await Promise.all(txtFiles.map((f) => f.text()));
    const items: MaterialItem[] = txtFiles.map((f, i) => ({
      id: nextId(),
      type: 'txt' as const,
      name: f.name,
      rawText: texts[i],
      editedText: texts[i],
      status: 'done' as const,
      selected: true,
    }));
    setMaterials((prev) => [...prev, ...items]);
    setTxtFiles([]);
    toast('success', `已导入 ${items.length} 个文本文件`);
  }, [txtFiles]);

  // ---- Cleanup timers ----
  useEffect(() => {
    return () => {
      if (singleTimer.current) clearInterval(singleTimer.current);
      if (videoTimer.current) clearInterval(videoTimer.current);
    };
  }, []);

  // ---- Material updates ----
  const updateMaterial = useCallback((id: string, updates: Partial<MaterialItem>) => {
    setMaterials((prev) => prev.map((m) => (m.id === id ? { ...m, ...updates } : m)));
  }, []);

  const removeMaterial = useCallback((id: string) => {
    setMaterials((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const toggleSelect = useCallback((id: string) => {
    setMaterials((prev) => prev.map((m) => (m.id === id ? { ...m, selected: !m.selected } : m)));
  }, []);

  const selectedMaterials = materials.filter((m) => m.selected && m.status === 'done' && m.editedText);

  // ---- Zone 4: Process ----
  const processMut = useMutation({
    mutationFn: async () => {
      const slices = selectedMaterials.map((m) => ({ text: m.editedText, source_url: m.sourceUrl }));
      const text = verifiedText || selectedMaterials.map((m) => m.editedText).join('\n\n');
      const [personaRes, strategyRes] = await Promise.all([
        analyzePersona({ slices, force_new: true }),
        batchExtractStrategies([{ text, category: 'monologue' }]),
      ]);
      return { personaRes, strategyRes };
    },
    onSuccess: async ({ personaRes, strategyRes }) => {
      setPersonaId(personaRes.persona_id);
      setStrategyResult(strategyRes.results[0] || null);
      try {
        const detail = await getPersona(personaRes.persona_id);
        setPersonaDetail(detail);
      } catch {
        toast('error', '获取人设详情失败');
      }
      toast('success', '处理完成');
    },
    onError: (err: any) => toast('error', err?.response?.data?.detail || '处理失败'),
  });

  // ---- Derived ----
  const hasMaterials = materials.length > 0;
  const doneMaterials = materials.filter((m) => m.status === 'done');

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <BookOpen className="w-6 h-6 text-brand" />
        <h1 className="text-2xl font-semibold">学习中心</h1>
      </div>

      {/* ===== Zone 1: Material Import ===== */}
      <section>
        <h2 className="text-lg font-semibold text-text-primary mb-4">素材导入</h2>

        <div className="space-y-4">
          {/* Method A: Douyin User */}
          <div className="bg-bg-card border border-border-default rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3 text-sm font-medium text-text-secondary">
              <Users className="w-4 h-4" />
              方式 A：粘贴抖音主页链接
            </div>
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type="url"
                  value={dyUserUrl}
                  onChange={(e) => { setDyUserUrl(e.target.value); if (anchorProfile) setAnchorProfile(null); }}
                  onBlur={handleDyUrlBlur}
                  placeholder="粘贴抖音主播主页链接，如 https://www.douyin.com/user/MS4w..."
                  className="w-full pl-9 pr-3 py-2.5 bg-bg-primary border border-border-default rounded-lg text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
                />
              </div>
              <select value={dyUserCount} onChange={(e) => setDyUserCount(Number(e.target.value))} className="bg-bg-primary border border-border-default rounded-lg px-3 py-2 text-sm text-text-primary outline-none">
                {[3, 5, 10, 15, 20].map((n) => <option key={n} value={n}>Top {n}</option>)}
              </select>
              <Button disabled={!dyUserUrl.trim() || dyUserMut.isPending} loading={dyUserMut.isPending} onClick={() => dyUserMut.mutate()}>
                开始拉取
              </Button>
              <Button
                variant="secondary"
                disabled={!dyUserUrl.trim() || isStreaming}
                loading={isStreaming}
                onClick={() => {
                  const url = dyUserUrl.trim();
                  if (!url || isStreaming) return;
                  setIsStreaming(true);
                  setProgressEvents([]);
                  setPersonaId(null);
                  setPersonaDetail(null);
                  setStrategyResult(null);

                  fetch('/api/import/douyin-user/stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, count: dyUserCount }),
                  })
                    .then(async (response) => {
                      if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                      }
                      const reader = response.body?.getReader();
                      if (!reader) return;
                      const decoder = new TextDecoder();
                      let buffer = '';

                      while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\n');
                        buffer = lines.pop() || '';

                        for (const line of lines) {
                          if (line.startsWith('data: ')) {
                            try {
                              const data = JSON.parse(line.slice(6));
                              setProgressEvents((prev) => [...prev, data]);

                              // Early profile display
                              if (data.step === 'profile_done' && data.profile) {
                                setAnchorProfile(data.profile);
                              }

                              if (data.step === 'done' && data.result) {
                                const r = data.result;
                                if (r.profile) setAnchorProfile(r.profile);
                                if (r.analysis) {
                                  setPersonaId(r.analysis.persona_id || 'stream');
                                }
                                if (r.narrative) {
                                  // narrative data will be in persona detail
                                }
                                if (r.strategies?.results?.[0]) {
                                  setStrategyResult(r.strategies.results[0]);
                                }
                                if (r.analysis) {
                                  setPersonaDetail({
                                    id: r.analysis.persona_id || 'stream',
                                    name: r.analysis.name || '',
                                    global_style: r.analysis.global_style || '',
                                    catchphrases: r.analysis.catchphrases || null,
                                    reaction_patterns: r.analysis.reaction_patterns || null,
                                    sentence_templates: r.analysis.sentence_templates || null,
                                    core_values: r.analysis.core_values || null,
                                    language_style: r.analysis.language_style || null,
                                    tone_adaptation: r.analysis.tone_adaptation || null,
                                    narrative_style: r.narrative || null,
                                    version: 1,
                                    is_active: true,
                                    created_at: new Date().toISOString(),
                                    slice_count: r.materials?.length || 0,
                                    version_notes: null,
                                  });
                                }
                                toast('success', '处理完成');
                              }
                              if (data.step === 'error') {
                                toast('error', data.message);
                              }
                            } catch { /* ignore parse errors */ }
                          }
                        }
                      }
                    })
                    .catch((err) => {
                      toast('error', `流式处理失败: ${err.message}`);
                    })
                    .finally(() => {
                      setIsStreaming(false);
                    });
                }}
              >
                <Sparkles className="w-4 h-4" />
                {isStreaming ? '处理中...' : '一键处理'}
              </Button>
            </div>

            {/* Anchor Profile Card */}
            {(profileMut.isPending || anchorProfile) && (
              <div className="mt-3 p-3 bg-bg-primary border border-border-default rounded-lg flex items-center gap-3">
                {profileMut.isPending ? (
                  <div className="flex items-center gap-2 text-sm text-text-muted">
                    <Spinner size={16} className="text-brand" />
                    正在获取博主信息...
                  </div>
                ) : anchorProfile && (
                  <>
                    <div className="w-10 h-10 rounded-full bg-brand/20 flex items-center justify-center text-brand font-bold text-sm shrink-0 overflow-hidden">
                      {anchorProfile.avatar_url ? (
                        <img src={anchorProfile.avatar_url} alt="" className="w-full h-full object-cover" />
                      ) : (
                        anchorProfile.anchor_name.slice(0, 1)
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-text-primary truncate">{anchorProfile.anchor_name}</span>
                        <span className="text-[10px] text-text-muted">@{anchorProfile.anchor_id}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-0.5">
                        <span className="text-xs text-text-secondary">{formatCount(anchorProfile.follower_count)} 粉丝</span>
                        <span className="text-xs text-text-secondary">{formatCount(anchorProfile.like_count)} 获赞</span>
                      </div>
                      {anchorProfile.bio && (
                        <p className="text-xs text-text-muted mt-1 line-clamp-2">{anchorProfile.bio}</p>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Method B: Single URL */}
          <div className="bg-bg-card border border-border-default rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3 text-sm font-medium text-text-secondary">
              <Link className="w-4 h-4" />
              方式 B：粘贴单个视频链接
            </div>
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type="url"
                  value={singleUrl}
                  onChange={(e) => setSingleUrl(e.target.value)}
                  placeholder="粘贴抖音/B站/YouTube视频链接..."
                  className="w-full pl-9 pr-3 py-2.5 bg-bg-primary border border-border-default rounded-lg text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
                  onKeyDown={(e) => { if (e.key === 'Enter' && !singleUrlMut.isPending && singleUrl.trim()) singleUrlMut.mutate(); }}
                />
              </div>
              <Button disabled={!singleUrl.trim() || singleUrlMut.isPending || singlePolling} loading={singleUrlMut.isPending || singlePolling} onClick={() => singleUrlMut.mutate()}>
                {singlePolling ? '导入中...' : '开始导入'}
              </Button>
            </div>
          </div>

          {/* Method C: Video/Audio upload */}
          <div className="bg-bg-card border border-border-default rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3 text-sm font-medium text-text-secondary">
              <Upload className="w-4 h-4" />
              方式 C：拖拽视频/音频文件
            </div>
            <label
              onDrop={handleVideoDrop}
              onDragOver={(e) => e.preventDefault()}
              className="block border-2 border-dashed border-border-default rounded-lg p-6 text-center cursor-pointer hover:border-brand transition-colors bg-bg-primary"
            >
              <Upload className="w-6 h-6 mx-auto mb-2 text-text-muted" />
              <p className="text-sm text-text-secondary">拖拽文件到此处，或 <span className="text-brand">点击选择</span></p>
              <p className="text-xs text-text-muted mt-1">支持 {VIDEO_EXTS.join('/')}，上限 500MB</p>
              <input type="file" accept={ACCEPT_VIDEO} multiple className="hidden" onChange={handleVideoInput} />
            </label>
            {videoPolling && videoProgress.total > 0 && (
              <div className="mt-3 space-y-1">
                <div className="flex justify-between text-xs text-text-muted">
                  <span>转写进度</span>
                  <span>{videoProgress.current}/{videoProgress.total}</span>
                </div>
                <div className="h-1.5 bg-bg-hover rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-brand to-brand-hover rounded-full transition-all" style={{ width: `${(videoProgress.current / videoProgress.total) * 100}%` }} />
                </div>
              </div>
            )}
          </div>

          {/* Method D: TXT upload */}
          <div className="bg-bg-card border border-border-default rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3 text-sm font-medium text-text-secondary">
              <BookOpen className="w-4 h-4" />
              方式 D：上传 TXT 文本文件
            </div>
            <TxtUploader files={txtFiles} onFilesChange={setTxtFiles} />
            {txtFiles.length > 0 && (
              <Button className="mt-3 w-full" onClick={handleTxtConfirm}>
                确认导入 {txtFiles.length} 个文件
              </Button>
            )}
          </div>
        </div>

        {/* Material list */}
        {hasMaterials && (
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-text-secondary">已导入素材 ({materials.length})</h3>
            </div>
            {materials.map((m) => (
              <div key={m.id} className="bg-bg-card border border-border-default rounded-lg px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <input type="checkbox" checked={m.selected} onChange={() => toggleSelect(m.id)} className="w-4 h-4 accent-brand" />
                  <span className="text-sm text-text-primary truncate">{m.name}</span>
                  {m.sourceUrl && <Badge variant="default" className="text-[10px]">链接</Badge>}
                  {m.type === 'txt' && <Badge variant="success" className="text-[10px]">TXT</Badge>}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {m.status === 'processing' && <Spinner size={14} className="text-brand" />}
                  {m.status === 'done' && <Badge variant="success">已完成</Badge>}
                  {m.status === 'pending' && <Badge variant="default">待转写</Badge>}
                  {m.status === 'error' && <Badge variant="error">失败</Badge>}
                  <button onClick={() => removeMaterial(m.id)} className="text-text-muted hover:text-error transition-colors">
                    &times;
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ===== Zone 2: Material Editor ===== */}
      {doneMaterials.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-text-primary mb-4">素材编辑与精调</h2>
          <MaterialEditor
            materials={doneMaterials}
            onUpdate={updateMaterial}
            locked={isVerified}
            anchorName={anchorProfile?.anchor_name}
          />
        </section>
      )}

      {/* ===== Zone 3: Verification ===== */}
      {selectedMaterials.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
            人工校验与角色标注
            {isVerified && <Badge variant="success"><Lock className="w-3 h-3 mr-1" />已锁定</Badge>}
          </h2>
          <VerificationPanel
            materials={selectedMaterials}
            onLock={(text) => { setVerifiedText(text); setIsVerified(true); }}
            locked={isVerified}
            anchorProfile={anchorProfile}
          />
        </section>
      )}

      {/* ===== Zone 4: Processing & Results ===== */}
      <section>
        <h2 className="text-lg font-semibold text-text-primary mb-4">处理与结果</h2>

        {anchorProfile && (
          <div className="mb-4 p-3 bg-brand/5 border border-brand/20 rounded-lg flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-brand/20 flex items-center justify-center text-brand font-bold text-xs shrink-0 overflow-hidden">
              {anchorProfile.avatar_url ? (
                <img src={anchorProfile.avatar_url} alt="" className="w-full h-full object-cover" />
              ) : (
                anchorProfile.anchor_name.slice(0, 1)
              )}
            </div>
            <div>
              <span className="text-sm font-medium text-text-primary">正在分析博主：</span>
              <span className="text-sm font-semibold text-brand">{anchorProfile.anchor_name}</span>
              <span className="text-xs text-text-muted ml-2">{formatCount(anchorProfile.follower_count)} 粉丝</span>
            </div>
          </div>
        )}

        {/* SSE streaming progress — always visible when streaming from "一键处理" */}
        {(isStreaming || progressEvents.length > 0) && !personaDetail && (
          <ProgressPanel events={progressEvents} />
        )}

        {/* SSE Results — always visible when done via "一键处理" */}
        {(personaDetail || strategyResult) && isStreaming === false && progressEvents.length > 0 && !processMut.isPending && (
          <div className="mt-6 grid grid-cols-2 gap-6">
            {/* Left: Persona Report */}
            {personaDetail && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-text-primary">
                  <Sparkles className="w-5 h-5 text-brand" />
                  <h3 className="text-base font-semibold">人设分析报告</h3>
                  <Badge variant="default" className="text-[10px]">基于已编辑文本</Badge>
                </div>

                <Card>
                  <RadarChart data={personaDetail.language_style || {}} size={220} />
                </Card>

                {personaDetail.global_style && (
                  <Card>
                    <h4 className="text-sm font-medium text-text-secondary mb-2">风格评述</h4>
                    <p className="text-sm text-text-primary leading-relaxed">{personaDetail.global_style}</p>
                  </Card>
                )}

                {personaDetail.catchphrases?.length > 0 && (
                  <Card>
                    <h4 className="text-sm font-medium text-text-secondary mb-2">口头禅</h4>
                    <div className="flex flex-wrap gap-2">
                      {personaDetail.catchphrases.map((p, i) => <Badge key={i}>{p}</Badge>)}
                    </div>
                  </Card>
                )}

                {personaDetail.reaction_patterns && Object.keys(personaDetail.reaction_patterns).length > 0 && (
                  <Card>
                    <h4 className="text-sm font-medium text-text-secondary mb-2">反应模式</h4>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(personaDetail.reaction_patterns).map(([k, v]) => (
                        <div key={k} className="bg-bg-primary rounded-md p-2">
                          <p className="text-xs text-brand font-medium">{k}</p>
                          <p className="text-sm text-text-primary">{String(v)}</p>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                {personaDetail.sentence_templates?.length > 0 && (
                  <Card>
                    <h4 className="text-sm font-medium text-text-secondary mb-2">句式模板</h4>
                    <ul className="space-y-1 font-mono text-sm">
                      {personaDetail.sentence_templates.map((t, i) => <li key={i} className="bg-bg-primary rounded-md px-3 py-2">{t}</li>)}
                    </ul>
                  </Card>
                )}

                <div className="flex gap-2">
                  {personaId && (
                    <Button variant="secondary" onClick={() => navigate(`/personas?select=${personaId}`)}>
                      查看人设详情 <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  )}
                  {personaId && (
                    <Button variant="secondary" onClick={() => navigate(`/scripts?persona_id=${personaId}`)}>
                      用此人设生成脚本 <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  )}
                </div>
              </div>
            )}

            {/* Right: Strategy Cards */}
            {strategyResult && strategyResult.strategies.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-text-primary">
                  <Zap className="w-5 h-5 text-brand" />
                  <h3 className="text-base font-semibold">编剧策略</h3>
                  <Badge variant="default" className="text-[10px]">基于已编辑文本</Badge>
                </div>
                {strategyResult.strategies.map((s, i) => (
                  <Card key={i}>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="default">{s.pattern_type}</Badge>
                      <span className="text-xs text-text-muted">评分: {s.quality_score}</span>
                    </div>
                    <p className="text-sm text-text-primary mb-2">{s.description}</p>
                    {s.sentence_templates?.length > 0 && (
                      <div className="space-y-1 mb-2">
                        {s.sentence_templates.map((t, ti) => (
                          <p key={ti} className="text-xs font-mono bg-bg-primary rounded px-2 py-1">{t}</p>
                        ))}
                      </div>
                    )}
                    {s.tags?.length > 0 && (
                      <div className="flex gap-1">
                        {s.tags.map((t, ti) => <Badge key={ti} variant="success" className="text-[10px]">{t}</Badge>)}
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {!isVerified ? (
          <p className="text-sm text-text-muted">请先在上方完成校验并锁定素材。</p>
        ) : (
          <>
            {!isStreaming && !progressEvents.length ? (
              <Button
                size="lg"
                loading={processMut.isPending}
                onClick={() => processMut.mutate()}
                className="w-full"
              >
                <Sparkles className="w-4 h-4" />
                {processMut.isPending ? '处理中...' : '开始处理'}
              </Button>
            ) : null}

            {/* Manual processing results (non-SSE) */}
            {(personaDetail || strategyResult) && progressEvents.length === 0 && !processMut.isPending && (
              <div className="mt-6 grid grid-cols-2 gap-6">
                {/* Left: Persona Report */}
                {personaDetail && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-text-primary">
                      <Sparkles className="w-5 h-5 text-brand" />
                      <h3 className="text-base font-semibold">人设分析报告</h3>
                      <Badge variant="default" className="text-[10px]">基于已编辑文本</Badge>
                    </div>

                    <Card>
                      <RadarChart data={personaDetail.language_style || {}} size={220} />
                    </Card>

                    {personaDetail.global_style && (
                      <Card>
                        <h4 className="text-sm font-medium text-text-secondary mb-2">风格评述</h4>
                        <p className="text-sm text-text-primary leading-relaxed">{personaDetail.global_style}</p>
                      </Card>
                    )}

                    {personaDetail.catchphrases?.length > 0 && (
                      <Card>
                        <h4 className="text-sm font-medium text-text-secondary mb-2">口头禅</h4>
                        <div className="flex flex-wrap gap-2">
                          {personaDetail.catchphrases.map((p, i) => <Badge key={i}>{p}</Badge>)}
                        </div>
                      </Card>
                    )}

                    {personaDetail.reaction_patterns && Object.keys(personaDetail.reaction_patterns).length > 0 && (
                      <Card>
                        <h4 className="text-sm font-medium text-text-secondary mb-2">反应模式</h4>
                        <div className="grid grid-cols-2 gap-2">
                          {Object.entries(personaDetail.reaction_patterns).map(([k, v]) => (
                            <div key={k} className="bg-bg-primary rounded-md p-2">
                              <p className="text-xs text-brand font-medium">{k}</p>
                              <p className="text-sm text-text-primary">{String(v)}</p>
                            </div>
                          ))}
                        </div>
                      </Card>
                    )}

                    {personaDetail.sentence_templates?.length > 0 && (
                      <Card>
                        <h4 className="text-sm font-medium text-text-secondary mb-2">句式模板</h4>
                        <ul className="space-y-1 font-mono text-sm">
                          {personaDetail.sentence_templates.map((t, i) => <li key={i} className="bg-bg-primary rounded-md px-3 py-2">{t}</li>)}
                        </ul>
                      </Card>
                    )}

                    <div className="flex gap-2">
                      {personaId && (
                        <Button variant="secondary" onClick={() => navigate(`/personas?select=${personaId}`)}>
                          查看人设详情 <ArrowRight className="w-3.5 h-3.5" />
                        </Button>
                      )}
                      {personaId && (
                        <Button variant="secondary" onClick={() => navigate(`/scripts?persona_id=${personaId}`)}>
                          用此人设生成脚本 <ArrowRight className="w-3.5 h-3.5" />
                        </Button>
                      )}
                    </div>
                  </div>
                )}

                {/* Right: Strategy Cards */}
                {strategyResult && strategyResult.strategies.length > 0 && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-text-primary">
                      <Zap className="w-5 h-5 text-brand" />
                      <h3 className="text-base font-semibold">编剧策略</h3>
                      <Badge variant="default" className="text-[10px]">基于已编辑文本</Badge>
                    </div>
                    {strategyResult.strategies.map((s, i) => (
                      <Card key={i}>
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="default">{s.pattern_type}</Badge>
                          <span className="text-xs text-text-muted">评分: {s.quality_score}</span>
                        </div>
                        <p className="text-sm text-text-primary mb-2">{s.description}</p>
                        {s.sentence_templates?.length > 0 && (
                          <div className="space-y-1 mb-2">
                            {s.sentence_templates.map((t, ti) => (
                              <p key={ti} className="text-xs font-mono bg-bg-primary rounded px-2 py-1">{t}</p>
                            ))}
                          </div>
                        )}
                        {s.tags?.length > 0 && (
                          <div className="flex gap-1">
                            {s.tags.map((t, ti) => <Badge key={ti} variant="success" className="text-[10px]">{t}</Badge>)}
                          </div>
                        )}
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
