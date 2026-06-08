import { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Clock, CheckCircle, AlertCircle, Loader2, ArrowRight, Sparkles, User, FolderOpen } from 'lucide-react';
import Button from '../../components/ui/Button';
import Spinner from '../../components/ui/Spinner';
import { getDouyinTaskStatus, type DouyinTaskStatus } from '../../services/douyin';
import { listTaskRecords } from '../../services/taskRecords';
import { getBatchRetranscribeStatus } from '../../services/assets';
import type { TaskRecord } from '../../types';

const STEP_LABELS: Record<string, string> = {
  fetching_profile: '获取博主信息',
  fetching_video_list: '搜索视频列表',
  filtering_and_sorting: '筛选排序',
  top_selected: '选定Top视频',
  downloading_videos: '下载视频',
  extracting_audio: '提取音频',
  building_voice_profile: '构建声纹档案',
  transcribing: '语音转写',
  search_enhancing: '搜索增强',
  analyzing: 'AI深度分析',
  generating_report: '生成报告',
  done: '完成',
};

interface TaskItem {
  id: string;
  url: string;
  count: number;
  submittedAt: number;
  status: DouyinTaskStatus | null;
}

interface Props {
  tasks: TaskItem[];
  onRemove: (id: string) => void;
  onViewResult: (taskId: string, result: any) => void;
}

export default function TaskListPanel({ tasks, onRemove, onViewResult }: Props) {
  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['task-records'],
    queryFn: () => listTaskRecords({ page: 1, page_size: 20 }),
    refetchOnWindowFocus: false,
    refetchInterval: 10000,
  });

  const historyItems: TaskRecord[] = historyData?.items || [];
  const activeTaskIds = new Set(tasks.map((t) => t.id));

  // Only show: running tasks (real-time) + recent completed (last 5)
  // Filter out failed tasks — they clutter the list and cause layout jumping
  const displayHistory = historyItems
    .filter((h) => !activeTaskIds.has(h.task_id))
    .filter((h) => h.status === 'running' || h.status === 'completed')
    .slice(0, 8);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-text-secondary">
        <Clock className="w-4 h-4" />
        任务历史
      </div>

      {/* Active (in-progress) tasks */}
      {tasks.map((task) => (
        <TaskRow
          key={task.id}
          task={task}
          onRemove={onRemove}
          onViewResult={onViewResult}
        />
      ))}

      {/* Completed/failed historical tasks from DB */}
      {historyLoading && (
        <div className="flex justify-center py-4"><Spinner className="text-brand" /></div>
      )}

      {displayHistory.map((record) => (
        <HistoryRow key={record.task_id} record={record} />
      ))}

      {tasks.length === 0 && displayHistory.length === 0 && !historyLoading && (
        <p className="text-xs text-text-muted">暂无任务记录</p>
      )}
    </div>
  );
}

/** Active task row — polls status every 3s */
function TaskRow({ task, onRemove, onViewResult }: {
  task: TaskItem;
  onRemove: (id: string) => void;
  onViewResult: (taskId: string, result: any) => void;
}) {
  const navigate = useNavigate();
  const [status, setStatus] = useState<DouyinTaskStatus | null>(task.status);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const mounted = useRef(true);

  const poll = useCallback(async () => {
    try {
      const s = await getDouyinTaskStatus(task.id);
      if (!mounted.current) return;
      setStatus(s);
      if (s.status === 'completed' || s.status === 'failed') {
        if (timer.current) clearInterval(timer.current);
      }
    } catch {
      // ignore poll errors
    }
  }, [task.id]);

  useEffect(() => {
    mounted.current = true;
    if (task.status?.status === 'completed' || task.status?.status === 'failed') {
      setStatus(task.status);
      return;
    }
    poll();
    timer.current = setInterval(poll, 3000);
    return () => {
      mounted.current = false;
      if (timer.current) clearInterval(timer.current);
    };
  }, [task.id]);

  const isDone = status?.status === 'completed';
  const isFailed = status?.status === 'failed';
  const isProcessing = status?.status === 'processing' || status?.status === 'queued';
  const isPartial = isDone && status?.partial_success === true;
  const stepLabel = status?.step ? (STEP_LABELS[status.step] || status.step) : '';

  return (
    <div className={`bg-bg-card border rounded-lg p-3 transition-colors ${
      isFailed ? 'border-error/30 bg-error/5' :
      isPartial ? 'border-warning/30 bg-warning/5' :
      isDone ? 'border-success/30' :
      'border-border-default'
    }`}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {isProcessing && <Loader2 className="w-3.5 h-3.5 text-brand animate-spin shrink-0" />}
            {isDone && !isPartial && <CheckCircle className="w-3.5 h-3.5 text-success shrink-0" />}
            {isPartial && <AlertCircle className="w-3.5 h-3.5 text-warning shrink-0" />}
            {isFailed && <AlertCircle className="w-3.5 h-3.5 text-error shrink-0" />}
            <span className="text-sm text-text-primary truncate">
              {status?.profile?.anchor_name || status?.result?.profile?.anchor_name || '博主'}
            </span>
            <span className="text-[10px] text-text-muted shrink-0">Top {task.count}</span>
          </div>
          <div className="mt-1 flex items-center gap-2">
            <span className={`text-xs ${
              isFailed ? 'text-error' : isPartial ? 'text-warning' : isDone ? 'text-success' : 'text-brand'
            }`}>
              {isFailed ? '失败' :
               isPartial ? `部分成功` :
               isDone ? '已完成' :
               stepLabel || '排队中...'}
            </span>
            {isProcessing && status?.message && (
              <span className="text-xs text-text-muted truncate">{status.message}</span>
            )}
            {isProcessing && status?.current && status?.total && (
              <span className="text-xs text-text-muted">{status.current}/{status.total}</span>
            )}
          </div>
          {isProcessing && status?.current && status?.total && (
            <div className="mt-2 h-1 bg-bg-hover rounded-full overflow-hidden">
              <div className="h-full bg-brand rounded-full transition-all duration-500"
                style={{ width: `${((status.current || 0) / (status.total || 1)) * 100}%` }} />
            </div>
          )}
          {isFailed && status?.error && (
            <p className="mt-2 text-xs text-error">{status.error}</p>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {isDone && status?.result_summary?.persona_id && (
            <Button variant="secondary" size="sm"
              onClick={() => navigate(`/personas?select=${status.result_summary?.persona_id}`)}>
              <Sparkles className="w-3 h-3" /> 查看人设
            </Button>
          )}
          {isDone && !status?.result_summary?.persona_id && (
            <Button variant="secondary" size="sm"
              onClick={() => onViewResult(task.id, status?.result)}>
              <ArrowRight className="w-3 h-3" /> 查看
            </Button>
          )}
          <button onClick={() => onRemove(task.id)}
            className="text-text-muted hover:text-error transition-colors text-lg leading-none px-1">
            &times;
          </button>
        </div>
      </div>
    </div>
  );
}

/** Historical task row — loaded from DB. Running tasks poll for progress. */
function HistoryRow({ record }: { record: TaskRecord }) {
  const navigate = useNavigate();
  const isCompleted = record.status === 'completed';
  const isFailed = record.status === 'failed';
  const isRunning = record.status === 'running';

  // Progress polling for running batch_retranscribe tasks
  const [progress, setProgress] = useState<{ current: number; total: number } | null>(null);
  useEffect(() => {
    if (!isRunning || record.trigger !== 'batch_retranscribe') return;
    const poll = async () => {
      try {
        const s = await getBatchRetranscribeStatus(record.task_id);
        if (s.status === 'completed' || s.status === 'failed') {
          setProgress(null);
          return;
        }
        setProgress({ current: s.progress, total: s.total });
      } catch { /* ignore */ }
    };
    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, [isRunning, record.task_id, record.trigger]);

  const progressPct = progress ? Math.round((progress.current / progress.total) * 100) : 0;

  return (
    <div className={`bg-bg-card border rounded-lg p-3 transition-colors ${
      isFailed ? 'border-error/30 bg-error/5' :
      isRunning ? 'border-brand/30 bg-brand/5' :
      'border-success/30'
    }`}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {isCompleted && <CheckCircle className="w-3.5 h-3.5 text-success shrink-0" />}
            {isFailed && <AlertCircle className="w-3.5 h-3.5 text-error shrink-0" />}
            {isRunning && <Loader2 className="w-3.5 h-3.5 text-brand animate-spin shrink-0" />}
            <span className="text-sm text-text-primary truncate">
              {record.anchor_name || '未知博主'}
            </span>
            <span className="text-[10px] text-text-muted shrink-0">
              {record.video_count} 视频
            </span>
          </div>
          <div className="mt-1 flex items-center gap-2">
            <span className={`text-xs ${isFailed ? 'text-error' : isRunning ? 'text-brand' : 'text-success'}`}>
              {isFailed ? '失败' : isRunning ? (progress ? `${progress.current}/${progress.total}` : '处理中...') : '已完成'}
            </span>
            {isCompleted && record.transcribed_count > 0 && (
              <span className="text-xs text-text-muted">
                {record.downloaded_count} 下载 / {record.transcribed_count} 转写
              </span>
            )}
            <span className="text-xs text-text-muted">
              {new Date(record.created_at).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          {/* Progress bar for running batch tasks */}
          {isRunning && progress && (
            <div className="mt-2">
              <div className="h-1.5 bg-bg-hover rounded-full overflow-hidden">
                <div className="h-full bg-brand rounded-full transition-all duration-500"
                  style={{ width: `${progressPct}%` }} />
              </div>
            </div>
          )}
          {isFailed && record.error_message && (
            <p className="mt-1 text-xs text-error truncate">{record.error_message}</p>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {isCompleted && record.persona_id && (
            <Button variant="secondary" size="sm"
              onClick={() => navigate(`/personas?select=${record.persona_id}`)}>
              <User className="w-3 h-3" /> 查看人设
            </Button>
          )}
          {isCompleted && record.task_id && (
            <Button variant="ghost" size="sm"
              onClick={() => navigate(`/assets?task_id=${record.task_id}`)}>
              <FolderOpen className="w-3 h-3" /> 素材
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

export { STEP_LABELS };
