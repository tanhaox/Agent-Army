import { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { CircleDot, ChevronRight, Search, X, Loader2, WifiOff } from 'lucide-react';
import { listPersonas } from '../../services/persona';
import { listAssets } from '../../services/assets';
import { listScripts } from '../../services/scripts';
import { listTaskRecords } from '../../services/taskRecords';
import { useConnectionStatus } from '../../hooks/useConnectionStatus';

const ROUTE_META: Record<string, { label: string; parent?: string }> = {
  '/': { label: '剧情车间' },
  '/learn': { label: '学习中心' },
  '/personas': { label: '人设工坊' },
  '/scripts': { label: '剧情车间' },
  '/creator': { label: '角色工坊', parent: '/personas' },
  '/assets': { label: '素材资产' },
  '/settings': { label: '系统设置' },
};

interface SearchResult {
  personas: { id: string; name: string; version: number }[];
  assets: { id: string; anchor_name: string; video_title: string }[];
  scripts: { id: string; title: string; created_at: string | null }[];
}

export default function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const meta = ROUTE_META[location.pathname];
  const label = meta?.label || '页面不存在';
  const parentMeta = meta?.parent ? ROUTE_META[meta.parent] : null;

  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const { isOnline } = useConnectionStatus();
  const containerRef = useRef<HTMLDivElement>(null);

  // Debounced keyword for API calls
  const [debouncedQuery, setDebouncedQuery] = useState('');
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(t);
  }, [query]);

  // Search queries - only fire when debounced query exists
  const { data: personasData } = useQuery({
    queryKey: ['search-personas', debouncedQuery],
    queryFn: () => listPersonas(0, 5),
    enabled: !!debouncedQuery,
  });

  const { data: assetsData } = useQuery({
    queryKey: ['search-assets', debouncedQuery],
    queryFn: () => listAssets({ keyword: debouncedQuery, page_size: 5 }),
    enabled: !!debouncedQuery,
  });

  const { data: scriptsData } = useQuery({
    queryKey: ['search-scripts', debouncedQuery],
    queryFn: () => listScripts(0, 5, debouncedQuery),
    enabled: !!debouncedQuery,
  });

  // Build flat result list
  const results: SearchResult = {
    personas: (personasData?.items || []).map((p) => ({ id: p.id, name: p.name, version: p.version })),
    assets: (assetsData?.items || []).map((a) => ({ id: a.id, anchor_name: a.anchor_name, video_title: a.video_title })),
    scripts: (scriptsData?.items || []).map((s) => ({ id: s.id, title: s.title, created_at: s.created_at })),
  };

  const flatItems = [
    ...results.personas.map((p) => ({ type: 'persona' as const, ...p })),
    ...results.assets.map((a) => ({ type: 'asset' as const, ...a })),
    ...results.scripts.map((s) => ({ type: 'script' as const, ...s })),
  ];

  const total = flatItems.length;

  // Click outside to close
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Navigate to result
  const goTo = useCallback((item: typeof flatItems[number]) => {
    setOpen(false);
    setQuery('');
    if (item.type === 'persona') navigate(`/personas?select=${item.id}`);
    else if (item.type === 'asset') navigate(`/assets`);
    else if (item.type === 'script') navigate(`/scripts`);
  }, [navigate]);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') { setOpen(false); return; }
    if (!open || total === 0) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIdx((i) => Math.min(i + 1, total - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIdx((i) => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && activeIdx >= 0 && activeIdx < total) { e.preventDefault(); goTo(flatItems[activeIdx]); }
  };

  const hasResults = results.personas.length > 0 || results.assets.length > 0 || results.scripts.length > 0;

  // Running tasks polling
  const { data: runningData } = useQuery({
    queryKey: ['running-tasks'],
    queryFn: () => listTaskRecords({ status: 'running', page_size: 10 }),
    refetchInterval: 3000,
  });
  const runningTasks = runningData?.items || [];
  const hasRunning = runningTasks.length > 0;

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-border-default bg-bg-primary shrink-0">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 text-sm">
        <Link to="/" className="text-text-muted hover:text-text-secondary transition-colors">ScriptForge</Link>
        {parentMeta && (
          <>
            <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
            <Link to={meta!.parent!} className="text-text-muted hover:text-text-secondary transition-colors">{parentMeta.label}</Link>
          </>
        )}
        <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
        <span className="text-text-primary font-medium">{label}</span>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4">
        <div ref={containerRef} className="relative">
          <div className="flex items-center bg-bg-card border border-border-default rounded-md px-3 py-1.5 w-[280px]">
            <Search className="w-3.5 h-3.5 text-text-muted shrink-0" />
            <input
              value={query}
              onChange={(e) => { setQuery(e.target.value); setOpen(true); setActiveIdx(-1); }}
              onFocus={() => query && setOpen(true)}
              onKeyDown={handleKeyDown}
              placeholder="搜索博主、人设、脚本..."
              className="flex-1 bg-transparent ml-2 text-sm text-text-primary placeholder:text-text-muted outline-none"
            />
            {query && (
              <button onClick={() => { setQuery(''); setOpen(false); }} className="text-text-muted hover:text-text-primary">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Dropdown */}
          {open && debouncedQuery && (
            <div className="absolute top-full right-0 mt-1 w-[320px] bg-bg-card border border-border-default rounded-lg shadow-xl z-50 max-h-[400px] overflow-auto">
              {!hasResults ? (
                <p className="text-sm text-text-muted py-4 text-center">未找到相关内容</p>
              ) : (
                <div>
                  {results.personas.length > 0 && (
                    <>
                      <p className="text-xs text-text-muted px-3 pt-2 pb-1 font-medium">人设（{results.personas.length}）</p>
                      {results.personas.map((p, i) => {
                        const idx = i;
                        return (
                          <button key={p.id} onClick={() => goTo(flatItems[idx])}
                            className={`w-full text-left px-3 py-2 text-sm hover:bg-bg-hover transition-colors flex items-center justify-between ${activeIdx === idx ? 'bg-bg-hover' : ''}`}>
                            <span className="text-text-primary">{p.name}</span>
                            <span className="text-xs text-text-muted">v{p.version}</span>
                          </button>
                        );
                      })}
                    </>
                  )}
                  {results.personas.length > 0 && (results.assets.length > 0 || results.scripts.length > 0) && (
                    <div className="border-t border-border-default my-1" />
                  )}
                  {results.assets.length > 0 && (
                    <>
                      <p className="text-xs text-text-muted px-3 pt-2 pb-1 font-medium">素材（{results.assets.length}）</p>
                      {results.assets.map((a, i) => {
                        const idx = results.personas.length + i;
                        return (
                          <button key={a.id} onClick={() => goTo(flatItems[idx])}
                            className={`w-full text-left px-3 py-2 text-sm hover:bg-bg-hover transition-colors ${activeIdx === idx ? 'bg-bg-hover' : ''}`}>
                            <span className="text-text-primary">{a.anchor_name || a.video_title || '未命名素材'}</span>
                            {a.video_title && a.anchor_name && <span className="text-xs text-text-muted ml-2">{a.video_title}</span>}
                          </button>
                        );
                      })}
                    </>
                  )}
                  {results.assets.length > 0 && results.scripts.length > 0 && (
                    <div className="border-t border-border-default my-1" />
                  )}
                  {results.scripts.length > 0 && (
                    <>
                      <p className="text-xs text-text-muted px-3 pt-2 pb-1 font-medium">脚本（{results.scripts.length}）</p>
                      {results.scripts.map((s, i) => {
                        const idx = results.personas.length + results.assets.length + i;
                        return (
                          <button key={s.id} onClick={() => goTo(flatItems[idx])}
                            className={`w-full text-left px-3 py-2 text-sm hover:bg-bg-hover transition-colors flex items-center justify-between ${activeIdx === idx ? 'bg-bg-hover' : ''}`}>
                            <span className="text-text-primary">{s.title}</span>
                            <span className="text-xs text-text-muted">{s.created_at?.split('T')[0] || ''}</span>
                          </button>
                        );
                      })}
                    </>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Status */}
        <div className="relative group">
          {!isOnline ? (
            <div className="flex items-center gap-2 text-xs text-error cursor-default" title="请检查后端服务">
              <WifiOff className="w-3 h-3" />
              <span>连接断开</span>
            </div>
          ) : hasRunning ? (
            <div className={`flex items-center gap-2 text-xs cursor-default text-amber-400`}>
              <Loader2 className="w-3 h-3 animate-spin" />
              <span>{runningTasks.length} 个任务执行中</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-xs cursor-default text-success">
              <CircleDot className="w-3 h-3 fill-success" />
              <span>系统在线</span>
            </div>
          )}

          {/* Hover panel */}
          {hasRunning && (
            <div className="absolute top-full right-0 mt-2 w-[340px] bg-bg-card border border-border-default rounded-lg shadow-xl z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
              <div className="px-3 py-2 border-b border-border-default">
                <p className="text-xs font-medium text-text-primary">后台任务</p>
              </div>
              <div className="max-h-[280px] overflow-y-auto p-2 space-y-2">
                {runningTasks.map((t) => {
                  const isRetranscribe = t.trigger === 'retranscribe' || t.trigger === 'batch_retranscribe';
                  const summary = t.result_summary;
                  const progressPct = summary?.progress_pct ?? (
                    t.video_count > 0 ? Math.round(((t.downloaded_count + t.transcribed_count) / (t.video_count * 2)) * 100) : 0
                  );
                  const statusMsg = summary?.message || (
                    t.transcribed_count > 0
                      ? `转写 ${t.transcribed_count}/${t.video_count}`
                      : t.downloaded_count > 0
                        ? `下载 ${t.downloaded_count}/${t.video_count}`
                        : '准备中...'
                  );
                  return (
                    <button
                      key={t.id}
                      onClick={() => navigate(isRetranscribe ? '/assets' : '/learn')}
                      className="w-full text-left bg-bg-hover rounded-md p-2.5 hover:bg-bg-hover/80 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-medium text-text-primary truncate">
                          {isRetranscribe ? `重新识别 · ${t.anchor_name}` : t.anchor_name}
                        </span>
                        <Loader2 className="w-3 h-3 text-amber-400 animate-spin shrink-0" />
                      </div>
                      {isRetranscribe ? (
                        <div className="flex items-center gap-1.5 text-[10px] text-text-muted">
                          <span>人声分离 + ASR 转写中...</span>
                        </div>
                      ) : (
                        <>
                          <div className="text-[10px] text-text-muted mb-1.5 truncate">
                            {statusMsg}
                          </div>
                          <div className="h-1 bg-bg-primary rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-400 rounded-full transition-all duration-500" style={{ width: `${progressPct}%` }} />
                          </div>
                          {t.video_count > 0 && (
                            <div className="flex items-center justify-between mt-1 text-[10px] text-text-muted">
                              <span>{t.downloaded_count} 下载</span>
                              <span>{t.transcribed_count}/{t.video_count} 转写</span>
                            </div>
                          )}
                        </>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
