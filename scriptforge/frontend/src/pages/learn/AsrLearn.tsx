import { useState, useCallback, useEffect, useRef } from 'react';
import { Upload, X, ChevronDown, ChevronRight, Link, Zap, CheckSquare, Square, Users } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Spinner from '../../components/ui/Spinner';
import { toast } from '../../components/ui/Toast';
import { batchTranscribe, getTaskStatus } from '../../services/asr';
import { importFromUrl, getImportTaskStatus } from '../../services/importer';
import { importDouyinUser } from '../../services/douyin';
import { batchExtractStrategies } from '../../services/strategies';
import type { ExtractResult } from '../../services/strategies';
import type { DouyinVideoResult } from '../../services/douyin';

const VIDEO_EXTS = ['.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav', '.flac'];
const ACCEPT_STR = VIDEO_EXTS.join(',');
const MAX_SIZE = 500 * 1024 * 1024;

type FileStatus = 'waiting' | 'transcribing' | 'done' | 'error';
type Category = 'auto' | 'monologue' | 'one_on_one' | 'one_on_many';

interface FileItem {
  file?: File;
  sourceUrl?: string;
  audioPath?: string;
  status: FileStatus;
  text?: string;
  category: Category;
  expanded: boolean;
  selected: boolean;
  extractedStrategies?: ExtractResult;
}

const CATEGORY_LABELS: Record<Category, string> = {
  auto: '自动检测',
  monologue: '单人口播',
  one_on_one: '1v1连线',
  one_on_many: '1vN连线',
};

const CATEGORY_BADGE: Record<Category, 'default' | 'success' | 'warning' | 'error'> = {
  auto: 'default',
  monologue: 'success',
  one_on_one: 'warning',
  one_on_many: 'error',
};

export default function AsrLearn() {
  const [fileItems, setFileItems] = useState<FileItem[]>([]);
  const [polling, setPolling] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [importUrl, setImportUrl] = useState('');
  const [importPolling, setImportPolling] = useState(false);
  const importTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [douyinUserUrl, setDouyinUserUrl] = useState('');
  const [douyinUserCount, setDouyinUserCount] = useState(5);
  const [showDouyinUserPanel, setShowDouyinUserPanel] = useState(false);

  const handleInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const added = Array.from(e.target.files || []).map((f) => ({
      file: f,
      status: 'waiting' as FileStatus,
      category: 'auto' as Category,
      expanded: false,
      selected: false,
    }));
    setFileItems((prev) => [...prev, ...added]);
    e.target.value = '';
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const added = Array.from(e.dataTransfer.files)
        .filter((f) => f.size <= MAX_SIZE)
        .map((f) => ({
          file: f,
          status: 'waiting' as FileStatus,
          category: 'auto' as Category,
          expanded: false,
          selected: false,
        }));
      if (added.length) setFileItems((prev) => [...prev, ...added]);
    },
    []
  );

  const removeItem = (idx: number) => setFileItems((prev) => prev.filter((_, i) => i !== idx));

  const toggleExpand = (idx: number) =>
    setFileItems((prev) =>
      prev.map((item, i) => (i === idx ? { ...item, expanded: !item.expanded } : item))
    );

  const setCategory = (idx: number, cat: Category) =>
    setFileItems((prev) =>
      prev.map((item, i) => (i === idx ? { ...item, category: cat } : item))
    );

  const batchMut = useMutation({
    mutationFn: async () => {
      const waitingFiles = fileItems.filter((f) => f.status === 'waiting' && f.file);
      if (!waitingFiles.length) throw new Error('没有待转写的文件');
      return batchTranscribe(waitingFiles.map((f) => f.file!));
    },
    onSuccess: (result) => {
      toast('success', `已提交 ${result.file_count} 个文件进行转写`);
      setPolling(true);
      setProgress({ current: 0, total: result.file_count });
      setFileItems((prev) =>
        prev.map((item) =>
          item.status === 'waiting' ? { ...item, status: 'transcribing' as FileStatus } : item
        )
      );
      pollTask(result.task_id);
    },
    onError: (err: any) => {
      toast('error', err?.response?.data?.detail || err.message || '转写提交失败');
    },
  });

  const pollTask = (taskId: string) => {
    timerRef.current = setInterval(async () => {
      try {
        const status = await getTaskStatus(taskId);
        if (status.status === 'SUCCESS') {
          clearInterval(timerRef.current!);
          setPolling(false);
          const results = status.result || [];
          let resultIdx = 0;
          setFileItems((prev) =>
            prev.map((item) => {
              if (item.status !== 'transcribing') return item;
              const r = results[resultIdx++];
              if (r && !r.error) {
                return { ...item, status: 'done' as FileStatus, text: r.text };
              }
              return { ...item, status: 'error' as FileStatus };
            })
          );
          setProgress({ current: results.length, total: results.length });
          toast('success', '转写完成');
        } else if (status.status === 'FAILURE') {
          clearInterval(timerRef.current!);
          setPolling(false);
          toast('error', '转写任务失败');
          setFileItems((prev) =>
            prev.map((item) =>
              item.status === 'transcribing' ? { ...item, status: 'error' as FileStatus } : item
            )
          );
        } else if (status.status === 'PROCESSING') {
          const meta = (status as any).meta;
          if (meta?.current && meta?.total) {
            setProgress({ current: meta.current, total: meta.total });
          }
        }
      } catch {
        clearInterval(timerRef.current!);
        setPolling(false);
        toast('error', '轮询任务状态失败');
      }
    }, 2000);
  };

  const importMut = useMutation({
    mutationFn: async () => {
      const url = importUrl.trim();
      if (!url) throw new Error('请输入视频链接');
      return importFromUrl(url);
    },
    onSuccess: (result) => {
      const url = importUrl.trim();
      setImportUrl('');

      // Sync mode: Celery unavailable, result returned directly
      if (result.status === 'SUCCESS' && result.result) {
        const text = result.result.transcription?.text || '';
        const warning = result.result.warning;
        const newItem: FileItem = {
          sourceUrl: url,
          status: text ? 'done' : 'error',
          text: text || undefined,
          audioPath: result.result.audio_path,
          category: 'auto',
          expanded: false,
          selected: false,
        };
        setFileItems((prev) => [...prev, newItem]);
        if (warning) {
          toast('warning', warning);
        } else if (text) {
          toast('success', '链接导入转写完成');
        } else {
          toast('error', '导入完成但未获取到转写结果');
        }
        return;
      }

      // Async mode: Celery task submitted, start polling
      toast('success', '导入任务已提交');
      setImportPolling(true);
      const newItem: FileItem = {
        sourceUrl: url,
        status: 'transcribing',
        category: 'auto',
        expanded: false,
        selected: false,
      };
      setFileItems((prev) => [...prev, newItem]);
      pollImportTask(result.task_id, fileItems.length);
    },
    onError: (err: any) => {
      toast('error', err?.response?.data?.detail || err.message || '导入失败');
    },
  });

  const pollImportTask = (taskId: string, itemIndex: number) => {
    importTimerRef.current = setInterval(async () => {
      try {
        const status = await getImportTaskStatus(taskId);
        if (status.status === 'success') {
          clearInterval(importTimerRef.current!);
          setImportPolling(false);
          const text = status.result?.transcription?.text || '';
          setFileItems((prev) =>
            prev.map((item, i) =>
              i === itemIndex
                ? { ...item, status: 'done' as FileStatus, text, audioPath: status.result?.audio_path }
                : item
            )
          );
          toast('success', '链接导入转写完成');
        } else if (status.status === 'failed') {
          clearInterval(importTimerRef.current!);
          setImportPolling(false);
          toast('error', status.error || '导入转写失败');
          setFileItems((prev) =>
            prev.map((item, i) =>
              i === itemIndex ? { ...item, status: 'error' as FileStatus } : item
            )
          );
        }
      } catch {
        clearInterval(importTimerRef.current!);
        setImportPolling(false);
        toast('error', '轮询导入状态失败');
      }
    }, 3000);
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (importTimerRef.current) clearInterval(importTimerRef.current);
    };
  }, []);

  const douyinUserMut = useMutation({
    mutationFn: async () => {
      const url = douyinUserUrl.trim();
      if (!url) throw new Error('请输入抖音用户主页链接');
      return importDouyinUser(url, douyinUserCount);
    },
    onSuccess: (result) => {
      setDouyinUserUrl('');
      const newItems: FileItem[] = result.downloaded.map((v: DouyinVideoResult) => ({
        sourceUrl: v.source_url,
        audioPath: v.audio_path,
        status: 'waiting' as FileStatus,
        category: 'auto' as Category,
        expanded: false,
        selected: false,
      }));
      if (newItems.length) {
        setFileItems((prev) => [...prev, ...newItems]);
        toast('success', `已下载 ${newItems.length} 个视频`);
      }
      if (result.failed.length > 0) {
        toast('warning', `${result.failed.length} 个视频下载失败`);
      }
    },
    onError: (err: any) => {
      toast('error', err?.response?.data?.detail || err.message || '抖音用户视频导入失败');
    },
  });

  const toggleSelect = (idx: number) =>
    setFileItems((prev) =>
      prev.map((item, i) => (i === idx ? { ...item, selected: !item.selected } : item))
    );

  const selectAllDone = () =>
    setFileItems((prev) => {
      const doneItems = prev.filter((f) => f.status === 'done' && f.text);
      const allSelected = doneItems.length > 0 && doneItems.every((f) => f.selected);
      return prev.map((item) =>
        item.status === 'done' && item.text ? { ...item, selected: !allSelected } : item
      );
    });

  const selectedDoneItems = fileItems.filter((f) => f.status === 'done' && f.text && f.selected);

  const extractMut = useMutation({
    mutationFn: async () => {
      if (!selectedDoneItems.length) throw new Error('请先选择已完成的转写结果');
      return batchExtractStrategies(
        selectedDoneItems.map((item) => ({
          text: item.text!,
          category: item.category === 'auto' ? 'monologue' : item.category,
        }))
      );
    },
    onSuccess: (result) => {
      toast('success', `已提取 ${result.total_extracted} 条策略`);
      let resultIdx = 0;
      setFileItems((prev) =>
        prev.map((item) => {
          if (item.status === 'done' && item.text && item.selected) {
            const r = result.results[resultIdx++];
            return { ...item, extractedStrategies: r || undefined, selected: false };
          }
          return item;
        })
      );
    },
    onError: (err: any) => {
      toast('error', err?.response?.data?.detail || err.message || '策略提取失败');
    },
  });

  const canTranscribe = fileItems.some((f) => f.status === 'waiting') && !polling && !batchMut.isPending && !importPolling && !douyinUserMut.isPending;

  const statusBadge = (s: FileStatus) => {
    switch (s) {
      case 'waiting': return <Badge variant="default">等待中</Badge>;
      case 'transcribing': return <Badge variant="warning">转写中</Badge>;
      case 'done': return <Badge variant="success">已完成</Badge>;
      case 'error': return <Badge variant="error">失败</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* URL Import */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="url"
            value={importUrl}
            onChange={(e) => setImportUrl(e.target.value)}
            placeholder="粘贴抖音/YouTube/B站视频链接..."
            className="w-full pl-9 pr-3 py-2.5 bg-bg-card border border-border-default rounded-lg text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand transition-colors"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !importMut.isPending && importUrl.trim()) {
                importMut.mutate();
              }
            }}
          />
        </div>
        <Button
          size="lg"
          disabled={!importUrl.trim() || importMut.isPending || importPolling}
          loading={importMut.isPending || importPolling}
          onClick={() => importMut.mutate()}
        >
          {importPolling ? '导入中...' : '导入'}
        </Button>
      </div>

      {/* Douyin User Import */}
      <div className="space-y-2">
        <button
          onClick={() => setShowDouyinUserPanel(!showDouyinUserPanel)}
          className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
        >
          <Users className="w-4 h-4" />
          {showDouyinUserPanel ? '收起' : '批量导入抖音用户视频'}
          <ChevronRight className={`w-3 h-3 transition-transform ${showDouyinUserPanel ? 'rotate-90' : ''}`} />
        </button>
        {showDouyinUserPanel && (
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                type="url"
                value={douyinUserUrl}
                onChange={(e) => setDouyinUserUrl(e.target.value)}
                placeholder="粘贴抖音用户主页链接，如 https://www.douyin.com/user/MS4wLjAB..."
                className="w-full pl-9 pr-3 py-2.5 bg-bg-card border border-border-default rounded-lg text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand transition-colors"
              />
            </div>
            <select
              value={douyinUserCount}
              onChange={(e) => setDouyinUserCount(Number(e.target.value))}
              className="bg-bg-card border border-border-default rounded-lg px-3 py-2 text-sm text-text-primary outline-none"
            >
              {[3, 5, 10, 15, 20].map((n) => (
                <option key={n} value={n}>Top {n}</option>
              ))}
            </select>
            <Button
              size="lg"
              disabled={!douyinUserUrl.trim() || douyinUserMut.isPending}
              loading={douyinUserMut.isPending}
              onClick={() => douyinUserMut.mutate()}
            >
              批量下载
            </Button>
          </div>
        )}
      </div>

      {/* Upload zone */}
      <label
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="block border-2 border-dashed border-border-default rounded-lg p-8 text-center cursor-pointer hover:border-brand transition-colors duration-150 bg-bg-card"
      >
        <Upload className="w-8 h-8 mx-auto mb-3 text-text-muted" />
        <p className="text-sm text-text-secondary">
          拖拽音视频文件到此处，或 <span className="text-brand">点击选择</span>
        </p>
        <p className="text-xs text-text-muted mt-1">
          支持 {VIDEO_EXTS.join('/')}，单文件上限 500MB
        </p>
        <input
          type="file"
          accept={ACCEPT_STR}
          multiple
          className="hidden"
          onChange={handleInput}
        />
      </label>

      {/* Progress bar */}
      {polling && progress.total > 0 && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-text-muted">
            <span>转写进度</span>
            <span>{progress.current}/{progress.total}</span>
          </div>
          <div className="h-1.5 bg-bg-hover rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand to-brand-hover rounded-full transition-all duration-300"
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* File list */}
      {fileItems.length > 0 && (
        <div className="space-y-2">
          {/* Select all bar */}
          {fileItems.some((f) => f.status === 'done' && f.text) && (
            <div className="flex items-center gap-2 px-1">
              <button onClick={selectAllDone} className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary">
                {fileItems.filter((f) => f.status === 'done' && f.text).every((f) => f.selected)
                  ? <CheckSquare className="w-3.5 h-3.5 text-brand" />
                  : <Square className="w-3.5 h-3.5" />}
                全选已完成
              </button>
            </div>
          )}
          {fileItems.map((item, i) => (
            <div key={i} className="bg-bg-card border border-border-default rounded-lg overflow-hidden">
              {/* Header row */}
              <div className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-3 min-w-0">
                  {item.status === 'transcribing' ? (
                    <Spinner size={14} className="text-brand shrink-0" />
                  ) : item.text ? (
                    <button onClick={() => toggleExpand(i)} className="text-text-muted hover:text-text-primary shrink-0">
                      {item.expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </button>
                  ) : (
                    <span className="w-4" />
                  )}
                  {item.sourceUrl ? (
                    <>
                      <span className="text-sm text-text-primary truncate">
                        {item.sourceUrl.length > 50 ? item.sourceUrl.slice(0, 50) + '...' : item.sourceUrl}
                      </span>
                      <Badge variant="default" className="text-[10px]">链接导入</Badge>
                    </>
                  ) : (
                    <>
                      <span className="text-sm text-text-primary truncate">{item.file!.name}</span>
                      <span className="text-xs text-text-muted shrink-0">
                        {(item.file!.size / 1024 / 1024).toFixed(1)} MB
                      </span>
                    </>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {/* Select checkbox for done items */}
                  {item.status === 'done' && item.text && (
                    <button onClick={() => toggleSelect(i)} className="text-text-muted hover:text-brand">
                      {item.selected
                        ? <CheckSquare className="w-3.5 h-3.5 text-brand" />
                        : <Square className="w-3.5 h-3.5" />}
                    </button>
                  )}
                  {/* Category selector */}
                  <select
                    value={item.category}
                    onChange={(e) => setCategory(i, e.target.value as Category)}
                    className="bg-bg-primary border border-border-default rounded-sm px-2 py-1 text-xs text-text-secondary outline-none"
                  >
                    {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                  <Badge variant={CATEGORY_BADGE[item.category]} className="text-[10px]">
                    {CATEGORY_LABELS[item.category]}
                  </Badge>
                  {statusBadge(item.status)}
                  <button onClick={() => removeItem(i)} className="text-text-muted hover:text-error transition-colors ml-1">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              {/* Expanded text */}
              {item.expanded && item.text && (
                <div className="px-4 pb-3 border-t border-border-default">
                  <p className="text-sm text-text-primary leading-relaxed mt-3 font-mono whitespace-pre-wrap">
                    {item.text}
                  </p>
                </div>
              )}
              {/* Extracted strategies */}
              {item.extractedStrategies && item.extractedStrategies.strategies.length > 0 && (
                <div className="px-4 pb-3 border-t border-border-default">
                  <p className="text-xs text-text-muted mt-3 mb-2">提取到的策略：</p>
                  <div className="space-y-2">
                    {item.extractedStrategies.strategies.map((s, si) => (
                      <div key={si} className="bg-bg-primary border border-border-default rounded-md px-3 py-2">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="default" className="text-[10px]">{s.pattern_type}</Badge>
                          <span className="text-xs text-text-muted">评分: {s.quality_score}</span>
                        </div>
                        <p className="text-sm text-text-primary">{s.description}</p>
                        {s.tags.length > 0 && (
                          <div className="flex gap-1 mt-1">
                            {s.tags.map((t, ti) => (
                              <span key={ti} className="text-[10px] text-text-muted bg-bg-hover px-1.5 py-0.5 rounded">{t}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <Button size="lg" disabled={!canTranscribe} loading={batchMut.isPending || polling} onClick={() => batchMut.mutate()}>
          {polling ? '转写中...' : '开始转写'}
        </Button>
        <Button
          size="lg"
          variant="secondary"
          disabled={selectedDoneItems.length === 0}
          loading={extractMut.isPending}
          onClick={() => extractMut.mutate()}
        >
          <Zap className="w-4 h-4" />
          {selectedDoneItems.length > 0 ? `提取策略 (${selectedDoneItems.length})` : '提取策略'}
        </Button>
      </div>
    </div>
  );
}
