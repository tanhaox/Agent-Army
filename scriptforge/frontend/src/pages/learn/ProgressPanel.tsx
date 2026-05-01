import { useEffect, useRef } from 'react';
import {
  Download, FileText, Search, Brain, BarChart3,
  CheckCircle, AlertCircle, Loader2, User, Video,
  Filter, Trophy, ListChecks,
} from 'lucide-react';

export interface ProgressEvent {
  step: string;
  message: string;
  current?: number;
  total?: number;
  phase?: 'start' | 'done' | 'failed';
  title?: string;
  file_size?: number;
  download_seconds?: number;
  word_count?: number;
  asr_seconds?: number;
  video_duration?: number;
  page?: number;
  total_collected?: number;
  total_before_filter?: number;
  filtered_count?: number;
  selected_count?: number;
  top_videos?: { title: string; play_count: number; duration: number }[];
  play_strs?: string[];
  profile?: any;
  follower_count?: number;
  enhanced?: boolean;
  enhanced_data?: any;
  asr_sub_phase?: string;
  asr_progress_pct?: number;
  asr_char_count?: number;
  asr_elapsed?: number;
  asr_current_time?: number;
  asr_total_duration?: number;
  results?: any[];
  downloaded?: number;
  failed?: number;
  result?: any;
}

const STEP_META: Record<string, { icon: typeof Download; label: string }> = {
  fetching_profile: { icon: User, label: '获取博主信息' },
  fetching_video_list: { icon: Video, label: '搜索视频列表' },
  filtering_and_sorting: { icon: Filter, label: '筛选排序' },
  top_selected: { icon: Trophy, label: '选定视频' },
  downloading_videos: { icon: Download, label: '下载视频' },
  extracting_audio: { icon: FileText, label: '提取音频' },
  transcribing: { icon: ListChecks, label: '转写文字' },
  search_enhancing: { icon: Search, label: '搜索增强' },
  analyzing: { icon: Brain, label: 'AI 深度分析' },
  generating_report: { icon: BarChart3, label: '生成报告' },
};

const STEP_ORDER = [
  'fetching_profile',
  'fetching_video_list',
  'filtering_and_sorting',
  'top_selected',
  'downloading_videos',
  'extracting_audio',
  'transcribing',
  'search_enhancing',
  'analyzing',
  'generating_report',
];

function getOrderedSteps(hasSearch: boolean): string[] {
  const steps = STEP_ORDER.filter((s) => {
    if (s === 'search_enhancing') return hasSearch;
    return true;
  });
  return steps;
}

interface Props {
  events: ProgressEvent[];
}

export default function ProgressPanel({ events }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events.length]);

  if (!events.length) return null;

  const hasSearch = events.some((e) => e.step === 'search_enhancing' || e.step === 'search_done');
  const orderedSteps = getOrderedSteps(hasSearch);

  // Build step status map
  const stepStatus: Record<string, 'pending' | 'active' | 'done'> = {};
  for (const s of orderedSteps) stepStatus[s] = 'pending';

  const completedSteps = new Set<string>();

  for (const ev of events) {
    const step = ev.step;
    if (step === 'profile_done') { completedSteps.add('fetching_profile'); continue; }
    if (step === 'video_list_done') { completedSteps.add('fetching_video_list'); continue; }
    if (step === 'filtering_and_sorting') { completedSteps.add('fetching_video_list'); continue; }
    if (step === 'top_selected') { completedSteps.add('top_selected'); completedSteps.add('filtering_and_sorting'); continue; }
    if (step === 'search_done') { completedSteps.add('search_enhancing'); continue; }
    if (step === 'transcribe_done') {
      completedSteps.add('transcribing');
      completedSteps.add('extracting_audio');
      completedSteps.add('downloading_videos');
      continue;
    }
    if (step === 'done' || step === 'error') continue;

    if (STEP_META[step]) {
      if (!completedSteps.has(step)) {
        stepStatus[step] = 'active';
      }
      if (ev.phase === 'done') {
        completedSteps.add(step);
      }
    }
  }

  for (const s of completedSteps) {
    stepStatus[s] = 'done';
  }

  const lastEvent = events[events.length - 1];
  const isDone = lastEvent?.step === 'done';
  const isError = lastEvent?.step === 'error';

  // Progress percentage
  const doneCount = Object.values(stepStatus).filter((s) => s === 'done').length;
  const totalSteps = orderedSteps.length;
  const progress = isDone ? 100 : Math.round((doneCount / totalSteps) * 100);

  // Collect recent messages for display
  const recentMessages = events.slice(-20).filter((e) => e.message && e.step !== 'done' && e.step !== 'error');

  // Get group progress for download/extract/transcribe
  function getGroupProgress(stepKey: string): { current: number; total: number } | null {
    const relevant = events.filter((e) => e.step === stepKey && e.total && e.total > 0);
    if (!relevant.length) return null;
    const last = relevant[relevant.length - 1];
    return { current: last.current || 0, total: last.total };
  }

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs text-text-muted">
          <span>{isDone ? '处理完成' : isError ? '处理失败' : '正在处理...'}</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 bg-bg-hover rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isError ? 'bg-error' : isDone ? 'bg-success' : 'bg-gradient-to-r from-brand to-brand-hover'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Step list */}
      <div className="space-y-1">
        {orderedSteps.map((step) => {
          const status = stepStatus[step];
          const meta = STEP_META[step];
          if (!meta) return null;

          const Icon = meta.icon;
          const isActive = status === 'active';
          const isDone2 = status === 'done';

          const groupProgress = isActive ? getGroupProgress(step) : null;

          return (
            <div
              key={step}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive ? 'bg-brand/10 text-brand' : isDone2 ? 'text-text-secondary' : 'text-text-muted opacity-50'
              }`}
            >
              {isActive ? (
                <Loader2 className="w-4 h-4 animate-spin shrink-0" />
              ) : isDone2 ? (
                <CheckCircle className="w-4 h-4 text-success shrink-0" />
              ) : (
                <Icon className="w-4 h-4 shrink-0" />
              )}
              <span className={isActive ? 'font-medium' : ''}>{meta.label}</span>

              {/* Inline progress for grouped steps */}
              {groupProgress && (
                <span className="ml-auto text-xs tabular-nums">
                  {groupProgress.current}/{groupProgress.total}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Live log: recent messages with auto-scroll */}
      {recentMessages.length > 0 && !isDone && !isError && (
        <div
          ref={scrollRef}
          className="max-h-48 overflow-y-auto bg-bg-card border border-border-default rounded-md text-xs space-y-0.5"
        >
          {recentMessages.map((ev, i) => (
            <div key={i} className="flex items-start gap-2 px-3 py-1.5 border-b border-border-default last:border-b-0">
              {ev.phase === 'done' ? (
                <CheckCircle className="w-3 h-3 text-success shrink-0 mt-0.5" />
              ) : ev.phase === 'failed' ? (
                <AlertCircle className="w-3 h-3 text-error shrink-0 mt-0.5" />
              ) : (
                <span className="w-3 h-3 shrink-0 mt-0.5 rounded-full border border-brand/40 bg-brand/10" />
              )}
              <span className="text-text-secondary leading-relaxed">{ev.message}</span>
              {ev.phase === 'done' && ev.download_seconds != null && (
                <span className="ml-auto text-text-muted shrink-0">{ev.download_seconds}s</span>
              )}
              {ev.phase === 'done' && ev.asr_seconds != null && (
                <span className="ml-auto text-text-muted shrink-0">{ev.asr_seconds}s</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ASR sub-progress bar — shown during transcription */}
      {(() => {
        const asrEvents = events.filter((e) => e.step === 'transcribing' && e.asr_progress_pct != null);
        const lastAsr = asrEvents[asrEvents.length - 1];
        const asrLoading = events.some((e) => e.step === 'transcribing' && e.asr_sub_phase === 'loading');
        if (!lastAsr && !asrLoading) return null;
        const pct = lastAsr?.asr_progress_pct ?? 0;
        const charCount = lastAsr?.asr_char_count ?? 0;
        const elapsed = lastAsr?.asr_elapsed ?? 0;
        return (
          <div className="bg-bg-card border border-border-default rounded-md px-4 py-3 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-text-secondary">
                {asrLoading ? '正在加载语音识别模型...' : `正在转写语音 ${pct}%`}
              </span>
              {!asrLoading && charCount > 0 && (
                <span className="text-text-muted tabular-nums">
                  {charCount} 字 · {elapsed.toFixed(0)}s
                </span>
              )}
            </div>
            <div className="h-2.5 bg-bg-hover rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 bg-gradient-to-r from-brand to-brand-hover"
                style={{ width: asrLoading ? '0%' : `${pct}%` }}
              />
            </div>
            {asrLoading && (
              <div className="h-2.5 bg-bg-hover rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-brand/30 animate-pulse" style={{ width: '60%' }} />
              </div>
            )}
          </div>
        );
      })()}

      {/* Error message */}
      {isError && (
        <div className="flex items-start gap-2 p-3 bg-error/10 border border-error/20 rounded-md">
          <AlertCircle className="w-4 h-4 text-error shrink-0 mt-0.5" />
          <span className="text-sm text-error">{lastEvent.message}</span>
        </div>
      )}

      {/* Search enhancement badge */}
      {events.some((e) => e.step === 'search_done' && e.enhanced) && (
        <div className="flex items-center gap-2 px-3 py-2 bg-warning/10 border border-warning/20 rounded-md text-sm">
          <Search className="w-4 h-4 text-warning" />
          <span className="text-warning">已整合网络公开资料增强分析</span>
        </div>
      )}

      {/* Done summary */}
      {isDone && lastEvent.result && (
        <div className="flex items-center gap-2 px-3 py-2 bg-success/10 border border-success/20 rounded-md text-sm">
          <CheckCircle className="w-4 h-4 text-success" />
          <span className="text-success">
            处理完成 — {lastEvent.result.materials?.length || 0} 个素材已分析
          </span>
        </div>
      )}
    </div>
  );
}
