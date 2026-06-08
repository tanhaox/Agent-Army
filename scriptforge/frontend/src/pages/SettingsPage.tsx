import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { X, Search, ChevronLeft, ChevronRight, Trash2, Eye, Cookie, CheckCircle, AlertCircle, Zap, Inbox, Power, HardDrive } from 'lucide-react';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import EmptyState from '../components/ui/EmptyState';
import { toast } from '../components/ui/Toast';
import ConfirmModal from '../components/ui/ConfirmModal';
import {
  listStrategies,
  getStrategy,
  deleteStrategy,
} from '../services/strategies';
import type { StrategyListItem, StrategyDetail } from '../services/strategies';
import {
  listSensitiveWords,
  addSensitiveWord,
  batchImportWords,
  deleteSensitiveWord,
} from '../services/sensitiveWords';
import type { SensitiveWordItem } from '../services/sensitiveWords';
import {
  getDouyinCookieStatus,
  updateDouyinCookie,
  getUserSettings,
  updateUserSettings,
} from '../services/settings';
import type { UserSettings } from '../services/settings';

const NAV_ITEMS = [
  { key: 'general', label: '通用设置' },
  { key: 'strategies', label: '策略库管理' },
  { key: 'sensitive', label: '敏感词管理' },
  { key: 'douyin_cookie', label: '抖音 Cookie' },
  { key: 'api', label: 'API 配置' },
  { key: 'account', label: '账号信息' },
];

const EMOTION_OPTIONS = [
  { value: 'default', label: '自然起伏' },
  { value: 'rollercoaster', label: '过山车式' },
  { value: 'warm', label: '温水煮蛙' },
  { value: 'confrontation', label: '对抗式' },
  { value: 'mystery', label: '悬疑式' },
];

// ─── General Tab ─────────────────────────────────────────────
function GeneralTab() {
  const qc = useQueryClient();

  const { data: settings, isLoading } = useQuery({
    queryKey: ['user-settings'],
    queryFn: getUserSettings,
  });

  const saveMut = useMutation({
    mutationFn: (vars: { emotion_curve?: string; strategy_mix?: string }) =>
      updateUserSettings(vars),
    onSuccess: () => {
      toast('success', '通用设置已保存');
      qc.invalidateQueries({ queryKey: ['user-settings'] });
    },
    onError: () => toast('error', '保存失败'),
  });

  const [emotionCurve, setEmotionCurve] = useState('default');
  const [strategyMix, setStrategyMix] = useState('conservative');
  const [restartCountdown, setRestartCountdown] = useState<number | null>(null);
  const [restartConfirm, setRestartConfirm] = useState(false);
  const [cleanupConfirm, setCleanupConfirm] = useState(false);
  const [diskInfo, setDiskInfo] = useState<{ uploads_gb: number; disk_total_gb: number; disk_free_gb: number } | null>(null);

  const fetchDiskInfo = useCallback(async () => {
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      if (data.checks?.disk?.status === 'ok') {
        setDiskInfo(data.checks.disk);
      }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchDiskInfo(); }, [fetchDiskInfo]);

  const handleRestart = async () => {
    setRestartConfirm(false);
    try {
      await fetch('/api/admin/restart', { method: 'POST' });
    } catch {
      // Expected: backend process exits, connection drops
    }
    let remaining = 10;
    setRestartCountdown(remaining);
    const timer = setInterval(() => {
      remaining -= 1;
      setRestartCountdown(remaining);
      if (remaining <= 0) {
        clearInterval(timer);
        window.location.reload();
      }
    }, 1000);
  };

  useEffect(() => {
    if (settings) {
      setEmotionCurve(settings.emotion_curve || 'default');
      setStrategyMix(settings.strategy_mix || 'conservative');
    }
  }, [settings]);

  // One-time migration from localStorage
  useEffect(() => {
    const local = localStorage.getItem('sf_settings');
    if (local && settings) {
      try {
        const parsed = JSON.parse(local);
        if (parsed.emotionCurve || parsed.strategyMix) {
          saveMut.mutate({
            emotion_curve: parsed.emotionCurve || settings.emotion_curve,
            strategy_mix: parsed.strategyMix || settings.strategy_mix,
          });
          localStorage.removeItem('sf_settings');
        }
      } catch { /* ignore */ }
    }
  }, [settings]);

  if (isLoading) return <Spinner size={24} className="text-brand" />;

  return (
    <div className="space-y-6 max-w-lg">
      <div className="space-y-1.5">
        <label className="text-sm text-text-secondary">默认情绪曲线</label>
        <select
          value={emotionCurve}
          onChange={(e) => setEmotionCurve(e.target.value)}
          className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand"
        >
          {EMOTION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
      <div className="space-y-1.5">
        <label className="text-sm text-text-secondary">默认策略模式</label>
        <select
          value={strategyMix}
          onChange={(e) => setStrategyMix(e.target.value)}
          className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand"
        >
          <option value="conservative">保守模式</option>
          <option value="mixed">融合模式</option>
          <option value="experimental">实验模式</option>
        </select>
      </div>
      <Button
        loading={saveMut.isPending}
        onClick={() => saveMut.mutate({ emotion_curve: emotionCurve, strategy_mix: strategyMix })}
      >
        保存设置
      </Button>

      {/* Backend restart */}
      <div className="mt-8 pt-6 border-t border-border-default">
        <h3 className="text-sm font-medium text-text-primary mb-2">服务管理</h3>
        <p className="text-xs text-text-muted mb-3">重启后端服务将中断所有进行中的任务，请谨慎操作。</p>
        <Button
          variant="danger"
          onClick={() => setRestartConfirm(true)}
          disabled={restartCountdown !== null}
        >
          <Power className="w-4 h-4 mr-1.5" />
          {restartCountdown !== null ? `正在重启 (${restartCountdown}s)` : '重启后端服务'}
        </Button>
      </div>

      {/* Legacy persona cleanup */}
      <div className="mt-6 pt-6 border-t border-border-default">
        <h3 className="text-sm font-medium text-text-primary mb-2">数据管理</h3>

        {/* Disk usage info */}
        {diskInfo && (
          <div className="mb-4 p-3 bg-bg-card border border-border-default rounded-lg space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-text-muted">uploads/ 目录</span>
              <span className="text-text-primary font-medium">{diskInfo.uploads_gb} GB</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-text-muted">磁盘剩余</span>
              <span className={`font-medium ${diskInfo.disk_free_gb < 10 ? 'text-error' : diskInfo.disk_free_gb < 50 ? 'text-warning' : 'text-success'}`}>
                {diskInfo.disk_free_gb} GB / {diskInfo.disk_total_gb} GB
              </span>
            </div>
            <div className="h-1.5 bg-bg-hover rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${diskInfo.disk_free_gb < 10 ? 'bg-error' : diskInfo.disk_free_gb < 50 ? 'bg-warning' : 'bg-success'}`}
                style={{ width: `${Math.min(100, ((diskInfo.disk_total_gb - diskInfo.disk_free_gb) / diskInfo.disk_total_gb) * 100)}%` }}
              />
            </div>
          </div>
        )}

        <p className="text-xs text-text-muted mb-3">删除没有精细特征分析的旧版人设数据，以便重新克隆获取 18 维度分析。</p>
        <Button
          variant="danger"
          onClick={() => setCleanupConfirm(true)}
        >
          <Trash2 className="w-4 h-4 mr-1.5" />
          清空旧版人设
        </Button>
        <div className="mt-4 pt-4 border-t border-border-default">
          <p className="text-xs text-text-muted mb-3">扫描并删除 uploads 目录中不被任何素材记录引用的孤立文件，释放磁盘空间。</p>
          <Button
            variant="secondary"
            onClick={async () => {
              try {
                const res = await fetch('/api/assets/cleanup-orphan-files', { method: 'POST' });
                const data = await res.json();
                const freedMB = (data.freed_bytes / 1024 / 1024).toFixed(1);
                toast('success', `已清理 ${data.deleted_count} 个孤立文件，释放 ${freedMB} MB`);
                fetchDiskInfo();
              } catch {
                toast('error', '清理失败');
              }
            }}
          >
            <HardDrive className="w-4 h-4 mr-1.5" />
            清理孤立文件
          </Button>
        </div>
      </div>

      {/* Restart Confirm */}
      <ConfirmModal
        open={restartConfirm}
        title="确认重启后端服务"
        message="重启将中断所有进行中的任务，确定继续？"
        confirmText="确认重启"
        confirmVariant="warning"
        onConfirm={handleRestart}
        onCancel={() => setRestartConfirm(false)}
      />

      {/* Cleanup Legacy Confirm */}
      <ConfirmModal
        open={cleanupConfirm}
        title="确认清空旧版人设"
        message="将删除所有不含精细特征分析的旧版人设数据，此操作不可恢复。"
        confirmText="确认删除"
        onConfirm={async () => {
          setCleanupConfirm(false);
          try {
            const res = await fetch('/api/personas/cleanup-legacy', { method: 'POST' });
            const data = await res.json();
            toast('success', `已删除 ${data.deleted_count} 个旧版人设`);
          } catch {
            toast('error', '清理失败');
          }
        }}
        onCancel={() => setCleanupConfirm(false)}
      />
    </div>
  );
}

// ─── Strategies Tab ──────────────────────────────────────────
function StrategiesTab() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [patternFilter, setPatternFilter] = useState('');
  const [searchText, setSearchText] = useState('');
  const [detailId, setDetailId] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const pageSize = 15;

  const { data, isLoading } = useQuery({
    queryKey: ['strategies-list', page, patternFilter],
    queryFn: () => listStrategies(page, pageSize, undefined, patternFilter || undefined),
  });

  const { data: detail } = useQuery({
    queryKey: ['strategy-detail', detailId],
    queryFn: () => getStrategy(detailId!),
    enabled: !!detailId,
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteStrategy(id),
    onSuccess: () => {
      toast('success', '策略已删除');
      setDeleteId(null);
      qc.invalidateQueries({ queryKey: ['strategies-list'] });
    },
    onError: (err: any) => toast('error', err?.response?.data?.detail || '删除失败'),
  });

  const items = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  const filtered = searchText
    ? items.filter(
        (s) =>
          s.title.toLowerCase().includes(searchText.toLowerCase()) ||
          s.extracted_pattern.toLowerCase().includes(searchText.toLowerCase()) ||
          (s.tags || []).some((t) => t.toLowerCase().includes(searchText.toLowerCase())),
      )
    : items;

  // Compute stats from current page data
  const typeCount: Record<string, number> = {};
  let scoreSum = 0;
  for (const s of items) {
    const pt = s.pattern_type || 'unknown';
    typeCount[pt] = (typeCount[pt] || 0) + 1;
    scoreSum += s.quality_score;
  }
  const avgScore = items.length > 0 ? (scoreSum / items.length).toFixed(1) : '-';

  return (
    <div className="space-y-5">
      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-bg-card border border-border-default rounded-lg p-3 text-center">
          <p className="text-xl font-semibold text-text-primary">{total}</p>
          <p className="text-xs text-text-muted">策略总数</p>
        </div>
        <div className="bg-bg-card border border-border-default rounded-lg p-3 text-center">
          <p className="text-xl font-semibold text-text-primary">{Object.keys(typeCount).length}</p>
          <p className="text-xs text-text-muted">策略类型</p>
        </div>
        <div className="bg-bg-card border border-border-default rounded-lg p-3 text-center">
          <p className="text-xl font-semibold text-brand">{avgScore}</p>
          <p className="text-xs text-text-muted">平均质量分</p>
        </div>
        <div className="bg-bg-card border border-border-default rounded-lg p-3 text-center">
          <div className="flex flex-wrap gap-1 justify-center">
            {Object.entries(typeCount).slice(0, 3).map(([t, c]) => (
              <Badge key={t} variant="default" className="text-[10px]">{t}: {c}</Badge>
            ))}
          </div>
          <p className="text-xs text-text-muted mt-1">类型分布</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 items-end">
        <div className="flex-1 space-y-1">
          <label className="text-xs text-text-secondary">搜索</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="搜索标题、内容或标签..."
              className="w-full bg-bg-card border border-border-default rounded-md pl-9 pr-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
            />
          </div>
        </div>
        <div className="space-y-1">
          <label className="text-xs text-text-secondary">策略类型</label>
          <select
            value={patternFilter}
            onChange={(e) => { setPatternFilter(e.target.value); setPage(1); }}
            className="bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none"
          >
            <option value="">全部类型</option>
            <option value="hook">Hook</option>
            <option value="transition">Transition</option>
            <option value="climax">Climax</option>
            <option value="closure">Closure</option>
            <option value="reversal">Reversal</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Spinner size={24} className="text-brand" />
          <span className="ml-3 text-sm text-text-secondary">加载策略库...</span>
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Zap}
          title={total === 0 ? '暂无策略数据' : '没有匹配的策略'}
          description={total === 0 ? '请先在"学习中心"上传素材并提取策略，策略将自动收录到策略库' : '尝试调整筛选条件或搜索关键词'}
        />
      ) : (
        <div className="border border-border-default rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-bg-card text-text-secondary text-xs">
                <th className="text-left px-3 py-2">标题</th>
                <th className="text-left px-3 py-2">类型</th>
                <th className="text-left px-3 py-2">分类</th>
                <th className="text-left px-3 py-2">质量分</th>
                <th className="text-left px-3 py-2">标签</th>
                <th className="text-left px-3 py-2">使用次数</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => (
                <tr key={s.id} className="border-t border-border-default hover:bg-bg-hover transition-colors">
                  <td className="px-3 py-2.5 text-text-primary max-w-[280px] truncate">{s.title}</td>
                  <td className="px-3 py-2.5">
                    <Badge variant="default">{s.pattern_type || '-'}</Badge>
                  </td>
                  <td className="px-3 py-2.5 text-text-muted">{s.category}</td>
                  <td className="px-3 py-2.5">
                    <span className={`font-medium ${s.quality_score >= 7 ? 'text-success' : s.quality_score >= 4 ? 'text-warning' : 'text-error'}`}>
                      {s.quality_score.toFixed(1)}
                    </span>
                  </td>
                  <td className="px-3 py-2.5">
                    <div className="flex gap-1 flex-wrap">
                      {(s.tags || []).slice(0, 2).map((t, i) => (
                        <Badge key={i} variant="success" className="text-[10px]">{t}</Badge>
                      ))}
                      {(s.tags || []).length > 2 && (
                        <span className="text-[10px] text-text-muted">+{s.tags!.length - 2}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-2.5 text-text-muted">{s.usage_count}</td>
                  <td className="px-3 py-2.5">
                    <div className="flex gap-1">
                      <button
                        onClick={() => setDetailId(s.id)}
                        className="p-1 text-text-muted hover:text-brand transition-colors"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setDeleteId(s.id)}
                        className="p-1 text-text-muted hover:text-error transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-text-muted">
            第 {page} / {totalPages} 页，共 {total} 条
          </span>
          <div className="flex gap-1">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="p-1.5 rounded-md text-text-secondary hover:bg-bg-hover disabled:opacity-30 disabled:pointer-events-none"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="p-1.5 rounded-md text-text-secondary hover:bg-bg-hover disabled:opacity-30 disabled:pointer-events-none"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {detailId && detail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setDetailId(null)}>
          <div className="bg-bg-card border border-border-default rounded-lg w-[640px] max-h-[80vh] overflow-auto p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-text-primary">{detail.title}</h3>
              <button onClick={() => setDetailId(null)} className="text-text-muted hover:text-text-primary">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-3 gap-3 text-sm">
              <div><span className="text-text-muted">类型：</span><Badge variant="default">{detail.pattern_type || '-'}</Badge></div>
              <div><span className="text-text-muted">分类：</span><span className="text-text-primary">{detail.category}</span></div>
              <div><span className="text-text-muted">质量分：</span><span className="font-medium text-brand">{detail.quality_score}</span></div>
            </div>

            <div>
              <p className="text-xs font-medium text-text-secondary mb-1">策略描述</p>
              <p className="text-sm text-text-primary leading-relaxed bg-bg-hover rounded-md p-3">{detail.extracted_pattern}</p>
            </div>

            {detail.emotional_curve && (
              <div>
                <p className="text-xs font-medium text-text-secondary mb-1">情绪曲线</p>
                <p className="text-sm text-text-primary bg-bg-hover rounded-md p-3">{JSON.stringify(detail.emotional_curve)}</p>
              </div>
            )}

            {detail.sentence_templates?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-text-secondary mb-1">句式模板</p>
                <div className="space-y-1">
                  {detail.sentence_templates.map((t, i) => (
                    <p key={i} className="text-sm text-text-primary bg-bg-hover rounded-md px-3 py-1.5">{t}</p>
                  ))}
                </div>
              </div>
            )}

            {detail.tags?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-text-secondary mb-1">标签</p>
                <div className="flex flex-wrap gap-1.5">
                  {detail.tags.map((t, i) => <Badge key={i} variant="success">{t}</Badge>)}
                </div>
              </div>
            )}

            {detail.source_text && (
              <div>
                <p className="text-xs font-medium text-text-secondary mb-1">来源文本</p>
                <p className="text-xs text-text-muted bg-bg-hover rounded-md p-3 max-h-32 overflow-auto">{detail.source_text}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      <ConfirmModal
        open={!!deleteId}
        title="确认删除"
        message="确定要删除此策略吗？此操作不可恢复。"
        loading={deleteMut.isPending}
        onConfirm={() => deleteMut.mutate(deleteId!)}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}

// ─── Sensitive Words Tab (API-backed) ────────────────────────
function SensitiveTab() {
  const qc = useQueryClient();
  const [newWord, setNewWord] = useState('');
  const [category, setCategory] = useState('广告');
  const [severity, setSeverity] = useState('medium');
  const [page, setPage] = useState(1);
  const [deleteWordId, setDeleteWordId] = useState<string | null>(null);
  const pageSize = 50;

  const { data, isLoading } = useQuery({
    queryKey: ['sensitive-words', page],
    queryFn: () => listSensitiveWords(page, pageSize),
  });

  const addMut = useMutation({
    mutationFn: () => addSensitiveWord(newWord.trim(), category, severity),
    onSuccess: () => {
      toast('success', '已添加');
      setNewWord('');
      qc.invalidateQueries({ queryKey: ['sensitive-words'] });
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || '添加失败';
      toast('error', detail);
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteSensitiveWord(id),
    onSuccess: () => {
      toast('success', '已删除');
      qc.invalidateQueries({ queryKey: ['sensitive-words'] });
    },
    onError: (err: any) => toast('error', err?.response?.data?.detail || '删除失败'),
  });

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (ev) => {
      const lines = (ev.target?.result as string).split('\n').map((l) => l.trim()).filter(Boolean);
      try {
        const result = await batchImportWords(lines.map((l) => ({ word: l, category: '其他', severity: 'medium' })));
        toast('success', `导入 ${result.added} 个词，跳过 ${result.skipped} 个重复`);
        qc.invalidateQueries({ queryKey: ['sensitive-words'] });
      } catch (err: any) {
        toast('error', '导入失败');
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  const words = data?.items || [];
  const total = data?.total || 0;
  const high = words.filter((w) => w.severity === 'high').length;
  const medium = words.filter((w) => w.severity === 'medium').length;
  const low = words.filter((w) => w.severity === 'low').length;

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: '总数', value: total, color: 'text-text-primary' },
          { label: '高危', value: high, color: 'text-error' },
          { label: '中危', value: medium, color: 'text-warning' },
          { label: '低危', value: low, color: 'text-success' },
        ].map((s) => (
          <div key={s.label} className="bg-bg-card border border-border-default rounded-lg p-3 text-center">
            <p className={`text-xl font-semibold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-text-muted">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Add form */}
      <div className="flex gap-2 items-end">
        <div className="flex-1 space-y-1">
          <label className="text-xs text-text-secondary">新词条</label>
          <input value={newWord} onChange={(e) => setNewWord(e.target.value)} placeholder="输入敏感词"
            className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
            onKeyDown={(e) => e.key === 'Enter' && newWord.trim() && addMut.mutate()} />
        </div>
        <select value={category} onChange={(e) => setCategory(e.target.value)}
          className="bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none">
          {['政治', '色情', '暴力', '广告', '其他'].map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}
          className="bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none">
          <option value="high">高危</option>
          <option value="medium">中危</option>
          <option value="low">低危</option>
        </select>
        <Button size="sm" disabled={!newWord.trim()} loading={addMut.isPending} onClick={() => addMut.mutate()}>添加</Button>
      </div>

      {/* Batch import */}
      <label className="inline-block cursor-pointer">
        <input type="file" accept=".txt" className="hidden" onChange={handleImport} />
        <Button variant="secondary" size="sm" onClick={() => {}}>批量导入 TXT</Button>
      </label>

      {/* Word list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Spinner size={24} className="text-brand" />
          <span className="ml-3 text-sm text-text-secondary">加载敏感词库...</span>
        </div>
      ) : words.length > 0 ? (
        <div className="border border-border-default rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-bg-card text-text-secondary text-xs">
                <th className="text-left px-3 py-2">词条</th>
                <th className="text-left px-3 py-2">分类</th>
                <th className="text-left px-3 py-2">严重程度</th>
                <th className="text-left px-3 py-2">添加时间</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {words.map((w) => (
                <tr key={w.id} className="border-t border-border-default">
                  <td className="px-3 py-2 text-text-primary">{w.word}</td>
                  <td className="px-3 py-2 text-text-muted">{w.category}</td>
                  <td className="px-3 py-2">
                    <Badge variant={w.severity === 'high' ? 'error' : w.severity === 'medium' ? 'warning' : 'success'}>
                      {w.severity === 'high' ? '高危' : w.severity === 'medium' ? '中危' : '低危'}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 text-text-muted">
                    {w.created_at ? new Date(w.created_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-3 py-2">
                    <button
                      onClick={() => setDeleteWordId(w.id)}
                      className="text-text-muted hover:text-error text-xs transition-colors"
                    >删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 text-sm text-text-muted">暂无敏感词</div>
      )}

      {/* Delete Word Confirm */}
      <ConfirmModal
        open={!!deleteWordId}
        title="确认删除"
        message="确定要删除此敏感词吗？"
        loading={deleteMut.isPending}
        onConfirm={() => { deleteMut.mutate(deleteWordId!); setDeleteWordId(null); }}
        onCancel={() => setDeleteWordId(null)}
      />
    </div>
  );
}

// ─── API Config Tab ──────────────────────────────────────────
function ApiTab() {
  const qc = useQueryClient();
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('https://api.deepseek.com/v1');
  const [testing, setTesting] = useState(false);
  const [showKey, setShowKey] = useState(false);

  const { data: settings, isLoading } = useQuery({
    queryKey: ['user-settings'],
    queryFn: getUserSettings,
  });

  const saveMut = useMutation({
    mutationFn: (vars: { api_base_url?: string; api_key?: string }) => updateUserSettings(vars),
    onSuccess: () => {
      toast('success', 'API 配置已保存');
      qc.invalidateQueries({ queryKey: ['user-settings'] });
      setApiKey('');
    },
    onError: () => toast('error', '保存失败'),
  });

  useEffect(() => {
    if (settings) {
      setBaseUrl(settings.api_base_url || 'https://api.deepseek.com/v1');
    }
    // One-time migration from localStorage to backend
    const saved = localStorage.getItem('sf_api_config');
    if (saved && settings) {
      try {
        const s = JSON.parse(saved);
        if (s.apiKey && !settings.api_key_configured) {
          saveMut.mutate({ api_key: s.apiKey });
        }
        if (s.baseUrl && !settings.api_base_url) {
          setBaseUrl(s.baseUrl);
        }
        localStorage.removeItem('sf_api_config');
      } catch { /* ignore */ }
    }
  }, [settings]);

  const save = () => {
    const payload: { api_base_url: string; api_key?: string } = { api_base_url: baseUrl };
    if (apiKey.trim()) {
      payload.api_key = apiKey.trim();
    }
    saveMut.mutate(payload);
  };

  const testConnection = async () => {
    setTesting(true);
    try {
      const r = await fetch('/api/health');
      if (r.ok) toast('success', '后端服务连接正常');
      else toast('error', '后端响应异常');
    } catch {
      toast('error', '无法连接后端服务');
    } finally {
      setTesting(false);
    }
  };

  if (isLoading) return <Spinner size={24} className="text-brand" />;

  return (
    <div className="space-y-6 max-w-lg">
      <div className="space-y-1.5">
        <label className="text-sm text-text-secondary">DeepSeek API Key</label>
        <div className="relative">
          <input
            type={showKey ? 'text' : 'password'}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={settings?.api_key_masked || 'sk-...'}
            className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 pr-10 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
          />
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary text-xs"
          >
            {showKey ? '隐藏' : '显示'}
          </button>
        </div>
        {settings?.api_key_configured && !apiKey && (
          <p className="text-xs text-text-muted">当前：{settings.api_key_masked}</p>
        )}
        {!settings?.api_key_configured && !apiKey && (
          <p className="text-xs text-warning">未配置 API Key，请设置以启用 AI 功能</p>
        )}
      </div>
      <div className="space-y-1.5">
        <label className="text-sm text-text-secondary">API Base URL</label>
        <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
          className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand" />
      </div>
      <div className="flex gap-3">
        <Button loading={saveMut.isPending} onClick={save}>保存</Button>
        <Button variant="secondary" loading={testing} onClick={testConnection}>连接测试</Button>
      </div>
    </div>
  );
}

// ─── Douyin Cookie Tab ─────────────────────────────────────────
function DouyinCookieTab() {
  const [cookieText, setCookieText] = useState('');
  const [saveResult, setSaveResult] = useState<{ ok: boolean; msg: string } | null>(null);

  const { data: status, isLoading } = useQuery({
    queryKey: ['douyin-cookie-status'],
    queryFn: getDouyinCookieStatus,
  });

  const saveMut = useMutation({
    mutationFn: async (text: string) => {
      let parsed: unknown;
      try {
        parsed = JSON.parse(text);
      } catch {
        throw new Error('JSON 格式不正确，请检查粘贴内容');
      }

      let cookies: { name: string; value: string; domain?: string; path?: string }[];

      if (Array.isArray(parsed)) {
        // EditThisCookie export format: [{ name, value, domain, path }, ...]
        cookies = parsed.map((c: any) => ({
          name: c.name || '',
          value: c.value ?? '',
          domain: c.domain || '.douyin.com',
          path: c.path || '/',
        }));
      } else if (typeof parsed === 'object' && parsed !== null) {
        // Simple key-value format: { "name": "value", ... }
        cookies = Object.entries(parsed as Record<string, string>).map(([name, value]) => ({
          name,
          value,
          domain: '.douyin.com',
          path: '/',
        }));
      } else {
        throw new Error('不支持的 JSON 格式');
      }

      const valid = cookies.filter((c) => c.name && c.value);
      if (!valid.length) {
        throw new Error('未找到有效的 Cookie 条目');
      }
      return updateDouyinCookie(valid);
    },
    onSuccess: (res) => {
      toast('success', `Cookie 已更新，共包含 ${res.cookie_count} 个`);
      setSaveResult({ ok: true, msg: `Cookie 已更新，共包含 ${res.cookie_count} 个` });
      setCookieText('');
    },
    onError: (err: any) => {
      const msg = err?.message || err?.response?.data?.detail || '保存失败';
      toast('error', msg);
      setSaveResult({ ok: false, msg });
    },
  });

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Guide card */}
      <div className="bg-bg-card border border-border-default rounded-lg p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Cookie className="w-4 h-4 text-brand" />
          <h3 className="text-sm font-semibold text-text-primary">如何获取抖音 Cookie</h3>
        </div>
        <ol className="space-y-2 text-sm text-text-secondary list-decimal list-inside leading-relaxed">
          <li>
            在电脑上打开 Chrome / Edge 浏览器，访问{' '}
            <code className="px-1.5 py-0.5 bg-bg-hover rounded text-xs text-brand">www.douyin.com</code>{' '}
            并手动扫码登录
          </li>
          <li>
            安装浏览器扩展{' '}
            <code className="px-1.5 py-0.5 bg-bg-hover rounded text-xs text-brand">EditThisCookie</code>
            （可从 Chrome 应用商店搜索安装）
          </li>
          <li>登录成功后，点击 EditThisCookie 扩展图标，选择「导出」→ 复制 JSON 内容</li>
          <li>将复制的 JSON 粘贴到下方文本框中，点击「保存 Cookie」</li>
        </ol>
      </div>

      {/* Current status */}
      {isLoading ? (
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <Spinner size={16} className="text-brand" />
          <span>检查 Cookie 状态...</span>
        </div>
      ) : status?.status === 'configured' ? (
        <div className="flex items-center gap-2 text-sm text-success">
          <CheckCircle className="w-4 h-4 shrink-0" />
          <span>当前已配置，共 {status.cookie_count} 个 Cookie</span>
        </div>
      ) : (
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>尚未配置 Cookie</span>
        </div>
      )}

      {/* Textarea */}
      <div className="space-y-1.5">
        <label className="text-sm text-text-secondary">粘贴 Cookie JSON</label>
        <textarea
          value={cookieText}
          onChange={(e) => { setCookieText(e.target.value); setSaveResult(null); }}
          rows={10}
          placeholder={'[\n  { "name": "sessionid", "value": "xxx", "domain": ".douyin.com" },\n  { "name": "sid_tt", "value": "xxx", "domain": ".douyin.com" }\n]'}
          className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted/50 outline-none focus:border-brand font-mono resize-y"
        />
      </div>

      {/* Save button + result */}
      <div className="flex items-center gap-4">
        <Button
          disabled={!cookieText.trim()}
          loading={saveMut.isPending}
          onClick={() => saveMut.mutate(cookieText)}
        >
          保存 Cookie
        </Button>
        {saveResult && (
          <span className={`text-sm ${saveResult.ok ? 'text-success' : 'text-error'}`}>
            {saveResult.msg}
          </span>
        )}
      </div>
    </div>
  );
}

// ─── Account Tab ─────────────────────────────────────────────
function AccountTab() {
  const { data: settings, isLoading } = useQuery({
    queryKey: ['user-settings'],
    queryFn: getUserSettings,
  });

  if (isLoading) return <Spinner size={24} className="text-brand" />;

  const planType = settings?.plan_type || '免费版';
  const quotaUsed = settings?.quota_used ?? 0;
  const quotaTotal = settings?.quota_total ?? 5;
  const pct = quotaTotal > 0 ? (quotaUsed / quotaTotal) * 100 : 0;

  return (
    <div className="space-y-6 max-w-lg">
      <div className="bg-bg-card border border-border-default rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-secondary">用户名</span>
          <span className="text-sm text-text-primary">{settings?.username || '-'}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-secondary">邮箱</span>
          <span className="text-sm text-text-primary">{settings?.email || '-'}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-secondary">当前套餐</span>
          <Badge variant="default">{planType}</Badge>
        </div>
      </div>

      <div className="bg-bg-card border border-border-default rounded-lg p-5 space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-text-secondary">额度使用</span>
          <span className="text-text-primary">{quotaUsed} / {quotaTotal}</span>
        </div>
        <div className="h-2 bg-bg-hover rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-brand to-brand-hover rounded-full transition-all" style={{ width: `${pct}%` }} />
        </div>
        <p className="text-xs text-text-muted">额度每月1日重置</p>
      </div>

      <Button variant="secondary" onClick={() => toast('warning', '升级套餐功能即将推出')}>升级套餐</Button>
    </div>
  );
}

// ─── Tab Registry ────────────────────────────────────────────
const TAB_COMPONENTS: Record<string, () => React.ReactNode> = {
  general: GeneralTab,
  strategies: StrategiesTab,
  sensitive: SensitiveTab,
  douyin_cookie: DouyinCookieTab,
  api: ApiTab,
  account: AccountTab,
};

export default function SettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromUrl = searchParams.get('tab');
  const [active, setActive] = useState(tabFromUrl && TAB_COMPONENTS[tabFromUrl] ? tabFromUrl : 'general');
  const TabComponent = TAB_COMPONENTS[active];

  useEffect(() => {
    if (tabFromUrl && TAB_COMPONENTS[tabFromUrl]) {
      setActive(tabFromUrl);
    }
  }, [tabFromUrl]);

  const handleTabChange = (key: string) => {
    setActive(key);
    setSearchParams({ tab: key }, { replace: true });
  };

  return (
    <div className="flex h-[calc(100vh-3.5rem-3rem)]">
      {/* Left nav */}
      <div className="w-[220px] shrink-0 border-r border-border-default bg-bg-sidebar p-4">
        <h3 className="text-sm font-semibold text-text-primary mb-4">系统设置</h3>
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              onClick={() => handleTabChange(item.key)}
              className={`w-full text-left px-3 py-2.5 rounded-md text-sm transition-all duration-150
                ${active === item.key
                  ? 'bg-bg-hover text-text-primary border-l-2 border-brand -ml-0.5 pl-[10px]'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'}`}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Right content */}
      <div className="flex-1 overflow-auto p-6">
        <h2 className="text-lg font-semibold text-text-primary mb-6">
          {NAV_ITEMS.find((n) => n.key === active)?.label}
        </h2>
        <TabComponent />
      </div>
    </div>
  );
}
