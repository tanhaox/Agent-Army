import { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';

interface ScanProgress {
  phase: string; current: number; total: number; pct: number; extra?: string;
}

export default function ScanPage() {
  const [data, setData] = useState<any[]>([]);
  const [scanning, setScanning] = useState(false);
  const [stats, setStats] = useState({ signals: 0, l3: 0, l2: 0 });
  const [klineInfo, setKlineInfo] = useState('');
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const [currentPhase, setCurrentPhase] = useState<'download' | 'scan' | null>(null);
  const [skipDownload, setSkipDownload] = useState(false);
  const [phaseMessages, setPhaseMessages] = useState<string[]>([]);
  const [marketFilter, setMarketFilter] = useState<string>('全部');
  const abortRef = useRef<AbortController | null>(null);
  const navigate = useNavigate();

  const load = useCallback(async () => {
    try {
      const r = await api.get('/scan/results', { params: { limit: 500 } });
      const d = r.data.data || [];
      setData(d);
      setStats({ signals: d.length, l3: d.filter((x: any) => x.level === 'L3').length, l2: d.filter((x: any) => x.level === 'L2').length });
    } catch {}
    try {
      const r = await api.get('/scan/dates');
      if (r.data.dates?.length > 0) {
        const latest = r.data.dates[0];
        const days = Math.floor((Date.now() - new Date(latest).getTime()) / 86400000);
        setKlineInfo(days >= 2 ? `数据滞后 ${days} 天 (最新: ${latest})，请点击"全市场扫描"更新` : `最新数据: ${latest}`);
      }
    } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  const startScan = async () => {
    setScanning(true); setProgress(null); setCurrentPhase(null); setPhaseMessages([]);
    abortRef.current = new AbortController();
    try {
      const response = await fetch(`/api/scan/trigger?skip_download=${skipDownload}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}', signal: abortRef.current.signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const reader = response.body?.getReader();
      if (!reader) return;
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n'); buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: ScanProgress = JSON.parse(line.slice(6));
              setProgress(event);
              setCurrentPhase(event.phase as 'download' | 'scan' | null);
              if (event.extra) {
                  setPhaseMessages(prev => { const u = [...prev]; if (u[u.length-1] !== event.extra) u.push(event.extra!); if (u.length > 20) u.shift(); return u; });
              }
              if (event.phase === 'done') {
                setScanning(false); setCurrentPhase(null); await load();
                window.dispatchEvent(new CustomEvent('scan:completed'));
              } else if (event.phase === 'error') {
                setScanning(false);
              }
            } catch {}
          }
        }
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') { setScanning(false); }
    }
  };

  const phaseLabel = (p: string) => {
    const m: Record<string,string> = { toplist:'龙虎榜准备', download:'K线下载', scan:'TG扫描中', ambush_scan:'潜伏猎手', pattern_scan:'形态识别', deep_score:'多维度评分', nm_defense:'🛡️分钟线防伪', toplist_sync:'龙虎榜同步', accuracy_feedback:'准确率验证' };
    return m[p] || p;
  };

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: 24, background: '#0b0e14', minHeight: '100vh', color: '#c9d1d9', fontFamily: 'system-ui' }}>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>第二步：TG信号扫描</h1>
      <p style={{ color: '#6e7a8a', marginBottom: 16, fontSize: 13 }}>全市场TG指标扫描 → 生成股票池 → 进入下一步评分精选</p>

      {/* 扫描控制 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <button onClick={startScan} disabled={scanning}
          style={{ padding: '10px 28px', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600,
            cursor: scanning ? 'not-allowed' : 'pointer', background: scanning ? '#374151' : '#ef4444', color: '#fff' }}>
          {scanning ? '扫描中...' : '🚀 全市场扫描'}
        </button>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#6e7a8a', cursor: 'pointer' }}>
          <input type="checkbox" checked={skipDownload} onChange={e => setSkipDownload(e.target.checked)} style={{ accentColor: '#3b82f6', width: 14, height: 14 }} />
          跳过K线下载
        </label>
        {klineInfo && <span style={{ fontSize: 12, color: klineInfo.includes('滞后') ? '#f59e0b' : '#6e7a8a' }}>{klineInfo}</span>}
        <span style={{ flex: 1 }} />
        <button onClick={() => navigate('/analysis')}
          style={{ padding: '10px 28px', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600,
            cursor: 'pointer', background: '#3b82f6', color: '#fff' }}>
          下一步 → 评分精选
        </button>
        <button onClick={() => navigate('/result')}
          style={{ padding: '10px 28px', border: '1px solid #10b981', borderRadius: 8, fontSize: 14, fontWeight: 600,
            cursor: 'pointer', background: 'rgba(16,185,129,0.1)', color: '#10b981' }}>
          查看推荐结果 →
        </button>
      </div>

      {/* 板块过滤 */}
      <div style={{ display:'flex', gap:8, marginBottom:16 }}>
        {['全部','主板','中小板','创业板'].map(m => (
          <button key={m} onClick={() => setMarketFilter(m)}
            style={{ padding:'4px 16px', borderRadius:16, fontSize:12, fontWeight:500, border:'1px solid',
              background: marketFilter===m ? (m==='创业板'?'rgba(6,182,212,0.12)':m==='中小板'?'rgba(245,158,11,0.1)':'rgba(239,68,68,0.1)') : 'transparent',
              color: marketFilter===m ? (m==='创业板'?'#06b6d4':m==='中小板'?'#f59e0b':'#ef4444') : '#6e7a8a',
              borderColor: marketFilter===m ? (m==='创业板'?'rgba(6,182,212,0.3)':m==='中小板'?'rgba(245,158,11,0.25)':'rgba(239,68,68,0.25)') : '#1e2535',
              cursor:'pointer' }}>{m}</button>
        ))}
      </div>

      {/* 阶段指示器 */}
      {currentPhase && (
        <div style={{ display:'flex', gap:10, marginBottom:16, flexWrap:'wrap' }}>
          {['toplist','download','scan','ambush_scan','pattern_scan','deep_score','nm_defense','toplist_sync','accuracy_feedback'].map(p => (
            <div key={p} style={{ padding:'6px 14px', borderRadius:20, fontSize:11, fontWeight:500,
              background: currentPhase===p?'rgba(59,130,246,0.12)':'rgba(255,255,255,0.02)',
              color: currentPhase===p?'#3b82f6':'#4b5563',
              border: currentPhase===p?'1px solid rgba(59,130,246,0.3)':'1px solid #1e2535' }}>
              {phaseLabel(p)}
            </div>
          ))}
        </div>
      )}

      {/* 扫描进度 */}
      {scanning && progress && (
        <div style={{ marginBottom: 20, padding: 14, background: '#161b27', borderRadius: 10, border: '1px solid #1e2535' }}>
          <div style={{ display:'flex',justifyContent:'space-between',marginBottom:8,fontSize:13 }}>
            <span style={{color:'#3b82f6'}}>{progress.phase==='download'?'下载K线':progress.phase==='scan'?'TG扫描计算':`${phaseLabel(progress.phase)} ${progress.current}/${progress.total}`}</span>
            <span style={{color:'#6e7a8a'}}>{progress.pct}%</span>
          </div>
          <div style={{height:6,background:'#1e2535',borderRadius:3,marginBottom:8}}>
            <div style={{height:'100%',width:`${progress.pct}%`,background:'linear-gradient(90deg,#3b82f6,#ef4444)',borderRadius:3,transition:'width .3s'}}/>
          </div>
          {phaseMessages.length > 0 && (
            <div style={{maxHeight:120,overflowY:'auto',fontSize:11,color:'#6e7a8a'}}>
              {phaseMessages.slice(-8).map((m,i) => <div key={i} style={{padding:'2px 0'}}>{m}</div>)}
            </div>
          )}
        </div>
      )}

      {/* 结果表格 */}
      {data.length > 0 && (
        <div style={{ background: '#161b27', borderRadius: 10, border: '1px solid #1e2535', overflow: 'hidden' }}>
          <div style={{ padding: '10px 16px', borderBottom: '1px solid #1e2535', display:'flex', justifyContent:'space-between', fontSize: 12 }}>
            <span style={{ color: '#c9d1d9' }}>信号: <b style={{color:'#ef4444'}}>{stats.signals}</b> | L3: <b style={{color:'#f59e0b'}}>{stats.l3}</b> | L2: <b style={{color:'#60a5fa'}}>{stats.l2}</b></span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr style={{ background: '#1a2030' }}>
              {['代码','名称','市场','信号','TG评分','TG动量','距低点%','J值','量比','买入强度','收盘价'].map(h => (
                <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11, color: '#6e7a8a', fontWeight: 500 }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {data.filter((r:any) => marketFilter==='全部' || r.market===marketFilter || (!r.market && marketFilter==='主板')).map((r: any, i: number) => (
                <tr key={i} style={{ borderTop: '1px solid #1e2535' }}>
                  <td style={{ padding: '9px 14px' }}><code style={{ color: '#06b6d4' }}>{r.symbol}</code></td>
                  <td style={{ padding: '9px 14px', fontWeight: 600 }}>
                    {r.name}
                    {r.resonance_type === 'weekly_resonance' && (
                      <span style={{marginLeft:6,padding:'1px 5px',borderRadius:3,fontSize:9,fontWeight:700,background:'rgba(245,158,11,0.2)',color:'#fbbf24'}}>⭐周线共振</span>
                    )}
                    {r.resonance_type === 'weekly_driven' && (
                      <span style={{marginLeft:6,padding:'1px 5px',borderRadius:3,fontSize:9,fontWeight:600,background:'rgba(59,130,246,0.12)',color:'#60a5fa'}}>📅周线驱动</span>
                    )}
                  </td>
                  <td style={{ padding: '9px 14px' }}>
                    <span style={{ fontSize: 11, color: r.market === '创业板' ? '#06b6d4' : '#ef4444' }}>{r.market || '主板'}</span>
                  </td>
                  <td style={{ padding: '9px 14px' }}>
                    <span style={{ padding:'2px 6px',borderRadius:4,fontSize:11,fontWeight:600,
                      background: r.level==='L3'?'rgba(251,191,36,.15)':r.level==='L2'?'rgba(96,165,250,.15)':'rgba(156,163,175,.12)',
                      color: r.level==='L3'?'#f59e0b':r.level==='L2'?'#60a5fa':'#9ca3af' }}>{r.level||'-'}</span>
                  </td>
                  <td style={{ padding: '9px 14px', fontWeight: 600 }}>{r.composite_score?.toFixed(1)}</td>
                  <td style={{ padding: '9px 14px' }}>{r.tg_momentum?.toFixed(2)}</td>
                  <td style={{ padding: '9px 14px' }}>{r.dist_low?.toFixed(1)}%</td>
                  <td style={{ padding: '9px 14px' }}>{r.j_value?.toFixed(2)}</td>
                  <td style={{ padding: '9px 14px' }}>{r.vol_ratio?.toFixed(2)}</td>
                  <td style={{ padding: '9px 14px' }}>{r.buy_strength?.toFixed(2)}</td>
                  <td style={{ padding: '9px 14px' }}>{r.close_price?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!scanning && data.length === 0 && (
        <div style={{ textAlign: 'center', padding: 60, color: '#4b5563' }}>
          <div style={{ fontSize: 40, marginBottom: 8 }}>📡</div>
          <div style={{ fontSize: 14 }}>点击「全市场扫描」开始TG信号扫描</div>
        </div>
      )}

    </div>
  );
}
