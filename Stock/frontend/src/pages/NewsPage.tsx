import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import MetricCard from '../components/MetricCard';

const snapshotHint = (key: string, val: number | null | undefined): string => {
  if (val == null) return '';
  const v = Number(val);
  switch (key) {
    case 'm2_yoy': return v > 10 ? '偏宽松' : v > 7 ? '适度' : '偏紧';
    case 'shibor_on': return v < 1.3 ? '充裕' : v < 2.0 ? '正常' : '偏紧';
    case 'shibor_3m': return v < 1.6 ? '充裕' : v < 2.5 ? '正常' : '偏紧';
    case 'cpi_yoy': return v < 0 ? '通缩风险' : v < 2 ? '温和' : v < 4 ? '正常' : '通胀压力';
    case 'ppi_yoy': return v < 0 ? '通缩' : v < 3 ? '温和上行' : v < 5 ? '扩张' : '过热';
    case 'pmi': return v > 50.5 ? '扩张' : v > 50 ? '临界' : v > 49 ? '收缩' : '衰退';
    case 'margin': return v > 16000 ? '亢奋' : v > 14000 ? '偏热' : v > 12000 ? '正常' : '谨慎';
    default: return '';
  }
};

const REFERENCE_RANGES = [
  { label: 'M2 增速', body: '>10%=宽松利好, 7-10%=适度, <7%=收紧。当前反映央行货币政策松紧' },
  { label: 'M1-M2 剪刀差', body: '正值扩大=资金活化流入实体, 利好股市。负值=存款定期化, 避险情绪' },
  { label: 'SHIBOR 隔夜/3M', body: '隔夜<1.3%=流动性充裕, 3M<1.6%=资金成本低。走高=银行惜贷' },
  { label: 'LPR', body: '贷款市场报价利率。1Y=短期融资成本, 5Y=房贷基准。下行=降息利好' },
  { label: '10年国债', body: '无风险利率锚。<2.5%=低利率环境利好成长股, >3.5%=压制估值' },
  { label: 'CPI', body: '居民消费价格。1-3%温和=良性, <0%通缩=经济疲软, >4%=通胀收紧货币' },
  { label: 'PPI', body: '工业品出厂价格。>0%企业利润改善利好周期股, <0%=需求不足' },
  { label: 'CPI-PPI 剪刀差', body: '正值扩大=下游利润空间增大(利好消费), 负值=上游挤压下游' },
  { label: 'PMI', body: '采购经理指数。>50.5=经济扩张利好, 50±0.5=临界, <49=收缩风险' },
  { label: 'GDP 增速', body: '季频。>5.5%=强劲, 4.5-5.5%=平稳, <4%=下行压力' },
  { label: '融资余额', body: '>1.6万亿=杠杆亢奋(注意风险), 1.2-1.6万亿=正常, <1.2万亿=情绪谨慎' },
  { label: '融券余额', body: '做空力量参考。大幅上升=看空情绪浓厚, 下降=市场信心恢复' },
  { label: '北向持股', body: '外资通过沪深港通持有的A股总量。持续增加=外资看好, 持续减少=流出' },
  { label: '原油', body: 'INE上海原油。>600美元/桶=成本推动型通胀, <400=需求疲弱信号' },
  { label: '沪铜', body: '铜价上涨=工业需求旺盛(经济扩张), 下跌=需求萎缩。\"铜博士\"领先指标' },
  { label: '螺纹钢', body: '建筑钢材主力。价格上涨=基建地产活跃, 下跌=固定资产投资放缓' },
  { label: '沪金', body: '>500元/克=避险情绪浓, <400=风险偏好回升。金价与风险偏好负相关' },
];

export default function NewsPage() {
  const navigate = useNavigate();
  const [newsLoading, setNewsLoading] = useState(false);
  const [newsResult, setNewsResult] = useState<any>(null);
  const [newsError, setNewsError] = useState('');
  const [newsStep, setNewsStep] = useState('');
  const [newsPct, setNewsPct] = useState(0);
  const [todayEvents, setTodayEvents] = useState<{stock_events:any[],sector_events:any[],main_stock_events?:any[],sme_stock_events?:any[],chinext_stock_events?:any[]}|null>(null);
  const [lastAnalysis, setLastAnalysis] = useState<{hours_ago:number,stale:boolean}|null>(null);
  const [marginSentiment, setMarginSentiment] = useState<any>(null);
  const [freshness, setFreshness] = useState<any>(null);
  const [sectorHeat, setSectorHeat] = useState<any>(null);
  const [toplistData, setToplistData] = useState<any>(null);
  const [toplistMarket, setToplistMarket] = useState<string>('全部');
  const [macroSnapshot, setMacroSnapshot] = useState<any>(null);
  const [macroBrief, setMacroBrief] = useState<any>(null);

  const loadMacro = async () => {
    try { const r = await api.get('/macro/snapshot'); setMacroSnapshot(r.data.data); } catch {}
    try { const r = await api.get('/macro/brief'); setMacroBrief(r.data); } catch {}
  };

  const loadAll = async () => {
    try {
      const r = await api.get('/scan/news/events-today');
      if (r.data.data?.stock_events?.length > 0 || r.data.data?.sector_events?.length > 0) {
        setTodayEvents(r.data.data);
      }
      if (r.data.last_analysis) setLastAnalysis(r.data.last_analysis);
    } catch {}
    try { const r = await api.get('/scan/margin-sentiment'); setMarginSentiment(r.data.data); } catch {}
    try { const r = await api.get('/scan/data-freshness'); setFreshness(r.data.data); } catch {}
    try { const r = await api.get('/scan/sector-heat', { params: { days: 5 } }); if (r.data.data?.local) setSectorHeat(r.data.data.local); } catch {}
    try { const r = await api.get('/scan/toplist-analysis'); if (r.data.data) setToplistData(r.data.data); } catch {}
  };

  useEffect(() => { loadAll(); }, []);
  useEffect(() => { loadMacro(); }, []);

  const crawlNews = async () => {
    setNewsLoading(true); setNewsError(''); setNewsResult(null);
    setNewsStep(todayEvents ? '已有分析结果，检查新内容...' : '正在连接...');
    setNewsPct(0);
    try {
      const resp = await fetch('/api/scan/crawl-news?force=true', { method: 'POST' });
      const reader = resp.body?.getReader();
      if (!reader) { setNewsError('无法读取响应流'); setNewsLoading(false); return; }
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
              const evt = JSON.parse(line.slice(6));
              if (evt.error) { setNewsError(evt.msg); setNewsLoading(false); return; }
              if (evt.done) {
                setNewsResult(evt.data); setNewsPct(100); setNewsStep('完成');
                const ns = evt.data?.analysis?.stored;
                if (ns && (ns.stock_events > 0 || ns.sector_events > 0)) {
                  api.get('/scan/news/events-today').then(r => setTodayEvents(r.data.data)).catch(()=>{});
                }
                loadAll();
              } else if (evt.progress) {
                const base = evt.phase === 'stage2_analyze' ? 50 : 30;
                const rng = evt.phase === 'stage2_analyze' ? 25 : 20;
                setNewsPct(base + Math.round((evt.current / Math.max(evt.total, 1)) * rng));
                setNewsStep(evt.msg);
              } else {
                setNewsStep(evt.msg); if (evt.pct) setNewsPct(evt.pct);
              }
            } catch {}
          }
        }
      }
    } catch (e: any) { setNewsError(e.message || '网络错误'); }
    setNewsLoading(false);
  };

  const dirColor = (d: string) => d === 'bullish' ? '#ef4444' : d === 'bearish' ? '#10b981' : '#6e7a8a';
  const dirEmoji = (d: string) => d === 'bullish' ? '📈' : d === 'bearish' ? '📉' : '➖';

  const aEvents = todayEvents?.stock_events || [];
  const smeEvents = todayEvents?.sme_stock_events || aEvents.filter((e:any) => e.ts_code?.startsWith('002') || e.ts_code?.startsWith('003'));
  const mainEvents = todayEvents?.main_stock_events || aEvents.filter((e:any) => !e.ts_code?.startsWith('300') && !e.ts_code?.startsWith('301') && !e.ts_code?.startsWith('688') && !e.ts_code?.startsWith('002') && !e.ts_code?.startsWith('003'));
  const chinextEvents = todayEvents?.chinext_stock_events || aEvents.filter((e:any) => e.ts_code?.startsWith('300') || e.ts_code?.startsWith('301') || e.ts_code?.startsWith('688'));
  const [eventMarket, setEventMarket] = useState<string>('全部');
  const sectorEvents = (todayEvents?.sector_events || []).filter((e:any) => !(e.sector||'').startsWith('宏观-'));
  const macroEvents = (todayEvents?.sector_events || []).filter((e:any) => (e.sector||'').startsWith('宏观-'));

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: 24, background: '#0b0e14', minHeight: '100vh', color: '#c9d1d9', fontFamily: 'system-ui' }}>
      {macroSnapshot && (
        <div style={{ marginBottom: 28 }}>
          {/* ── 顶部结论 Banner ── */}
          <div style={{
            background: 'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(139,92,246,0.06) 100%)',
            border: '1px solid rgba(16,185,129,0.15)', borderRadius: 12, padding: '16px 20px',
            marginBottom: 20,
          }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: '#cbd5e1', marginBottom: 4 }}>
              {macroBrief?.macro_summary || '宏观数据加载中...'}
            </div>
            <div style={{ fontSize: 11, color: '#4b5563' }}>
              Tushare 结构化实时数据 · 零 LLM 成本 · 自动同步
            </div>
          </div>

          {/* ── 分组数据卡片 ── */}
          {[
            { title: '货币与利率', color: '#3b82f6', items: [
              { label: 'M2 增速', value: macroSnapshot?.m2_yoy?.value, unit: '%', hint: snapshotHint('m2_yoy', macroSnapshot?.m2_yoy?.value) },
              { label: 'M1-M2 剪刀差', value: macroSnapshot?.m1_yoy?.value != null ? (macroSnapshot?.m1_yoy?.value - macroSnapshot?.m2_yoy?.value).toFixed(1) : null, unit: '%', hint: '正=资金活化' },
              { label: 'SHIBOR 隔夜', value: macroSnapshot?.shibor_on?.value, unit: '%', hint: snapshotHint('shibor_on', macroSnapshot?.shibor_on?.value) },
              { label: 'SHIBOR 3个月', value: macroSnapshot?.shibor_3m?.value, unit: '%', hint: snapshotHint('shibor_3m', macroSnapshot?.shibor_3m?.value) },
              { label: 'LPR 1年期', value: macroSnapshot?.lpr_1y?.value, unit: '%', hint: '贷款基准利率' },
              { label: '10年国债', value: macroSnapshot?.bond_10y_yield?.value, unit: '%', hint: '无风险利率锚' },
            ]},
            { title: '通胀与景气', color: '#f59e0b', items: [
              { label: 'CPI 同比', value: macroSnapshot?.cpi_yoy?.value, unit: '%', hint: snapshotHint('cpi_yoy', macroSnapshot?.cpi_yoy?.value) },
              { label: 'PPI 同比', value: macroSnapshot?.ppi_yoy?.value, unit: '%', hint: snapshotHint('ppi_yoy', macroSnapshot?.ppi_yoy?.value) },
              { label: 'PMI 制造业', value: macroSnapshot?.pmi?.value, unit: '', hint: snapshotHint('pmi', macroSnapshot?.pmi?.value) },
              { label: 'GDP 增速', value: macroSnapshot?.gdp_yoy?.value, unit: '%', hint: '季频, >5.5%扩张' },
              { label: 'CPI-PPI 剪刀差', value: macroSnapshot?.cpi_yoy?.value != null ? (macroSnapshot?.cpi_yoy?.value - (macroSnapshot?.ppi_yoy?.value||0)).toFixed(1) : null, unit: '%', hint: '正=下游利润空间' },
            ]},
            { title: '资金情绪', color: '#10b981', items: [
              { label: '融资余额', value: ((macroSnapshot?.margin_balance?.value||0)/1e8).toFixed(0), unit: '亿', hint: snapshotHint('margin', (macroSnapshot?.margin_balance?.value||0)/1e8) },
              { label: '融券余额', value: ((macroSnapshot?.short_balance?.value||0)/1e8).toFixed(0), unit: '亿', hint: '做空力量参考' },
              { label: '北向持股', value: ((macroSnapshot?.north_hold_vol?.value||0)/1e8).toFixed(1), unit: '亿股', hint: '外资持仓总量' },
            ]},
            { title: '商品期货', color: '#8b5cf6', items: [
              { label: '原油 (INE)', value: macroSnapshot?.['commodity:crude_oil']?.value, unit: '元/桶', hint: '全球通胀之锚' },
              { label: '沪铜', value: macroSnapshot?.['commodity:copper']?.value, unit: '元/吨', hint: '经济晴雨表' },
              { label: '螺纹钢', value: macroSnapshot?.['commodity:rebar']?.value, unit: '元/吨', hint: '基建地产风向标' },
              { label: '沪金', value: macroSnapshot?.['commodity:gold']?.value, unit: '元/克', hint: '避险情绪指标' },
            ]},
          ].map((group, gi) => (
            <div key={gi} style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: group.color, marginBottom: 8, letterSpacing: 0.5 }}>
                {group.title}
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {group.items.map((item, ii) => {
                  const v = item.value;
                  const display = v != null ? (typeof v === 'number' ? (Math.abs(v) > 1000 ? v.toFixed(0) : v.toFixed(2)) : v) : '—';
                  return (
                    <div key={ii} style={{
                      flex: '1 1 130px', minWidth: 110,
                      background: '#161b27', border: '1px solid #1e2535', borderRadius: 10,
                      padding: '12px 14px', textAlign: 'center',
                    }}>
                      <div style={{ fontSize: 22, fontWeight: 800, color: '#e2e8f0', lineHeight: 1.1 }}>
                        {display}<span style={{ fontSize: 12, fontWeight: 400, color: '#6e7a8a', marginLeft: 2 }}>{item.unit}</span>
                      </div>
                      <div style={{ fontSize: 11, color: '#6e7a8a', marginTop: 2 }}>{item.label}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {/* ── 宏观评分 + 早报板块 ── */}
          {macroBrief?.sections && macroBrief.sections.length > 0 && (
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 4 }}>
              {macroBrief.sections.map((s: any, i: number) => (
                <div key={i} style={{ flex: '1 1 220px', padding: '12px 14px', background: '#161b27', border: '1px solid #1e2535', borderRadius: 10 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: '#a78bfa', marginBottom: 6 }}>{s.title}</div>
                  {s.items.map((item: string, j: number) => (
                    <div key={j} style={{ fontSize: 11, color: '#6e7a8a', lineHeight: 1.5 }}>· {item}</div>
                  ))}
                </div>
              ))}
            </div>
          )}

          {/* ── 底部名词解释 ── */}
          <details style={{ marginTop: 16, cursor: 'pointer' }}>
            <summary style={{ fontSize: 11, color: '#4b5563' }}>📖 指标参考范围</summary>
            <div style={{ marginTop: 8, padding: '12px 16px', background: '#0d1117', borderRadius: 8, fontSize: 11, color: '#6e7a8a', lineHeight: 1.7, display: 'flex', flexWrap: 'wrap', gap: '4px 24px' }}>
              {REFERENCE_RANGES.map((r, i) => (
                <span key={i}>
                  <span style={{ color: '#cbd5e1', fontWeight: 600 }}>{r.label}</span>
                  ：{r.body}
                </span>
              ))}
            </div>
          </details>
        </div>
      )}
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>第一步：新闻采集</h1>
      <p style={{ color: '#6e7a8a', marginBottom: 16, fontSize: 13 }}>近7天新闻事件 · 新鲜度自然衰减 · 新扫描不覆盖历史</p>

      <div style={{ display:'flex', gap:12, marginBottom: 12, flexWrap:'wrap' }}>
        {freshness?.stale && (
          <div style={{ flex:1, minWidth:250, padding: '10px 16px', borderRadius: 8, background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)' }}>
            <span style={{ fontSize: 16 }}>⚠️</span>
            <span style={{ fontSize: 13, color: '#f59e0b', marginLeft: 8 }}>{freshness.message || `数据滞后 ${freshness.lag_trading_days} 天`}</span>
          </div>
        )}
        {marginSentiment && (
          <MetricCard label="融资情绪" value={(marginSentiment.trend_pct>0?'+':'')+marginSentiment.trend_pct+'%'}
            trend={`${marginSentiment.sentiment==='bullish'?'偏多':marginSentiment.sentiment==='bearish'?'偏空':'中性'} ${marginSentiment.detail}`}
            trendUp={marginSentiment.sentiment==='bullish'}
            color={marginSentiment.sentiment==='bullish'?'#ef4444':marginSentiment.sentiment==='bearish'?'#10b981':'#6e7a8a'}/>
        )}
      </div>

      {sectorHeat && (
        <div style={{ display:'flex', gap:12, marginBottom: 16 }}>
          <div style={{ flex:1, background:'#161b27', border:'1px solid #1e2535', borderRadius:10, padding:12 }}>
            <div style={{ fontSize:12, color:'#ef4444', marginBottom:6, fontWeight:600 }}>热门板块 (近5日龙虎榜)</div>
            {(sectorHeat.hot_sectors || []).slice(0,10).map((s:any,i:number) => (
              <div key={i} style={{ display:'flex', justifyContent:'space-between', padding:'3px 0', fontSize:12 }}>
                <span style={{ color:'#c9d1d9' }}>{s.name}</span>
                <span style={{ color: s.avg_pct>0?'#ef4444':'#10b981' }}>{s.avg_pct>0?'+':''}{s.avg_pct}% ({s.count}次)</span>
              </div>
            ))}
          </div>
          <div style={{ flex:1, background:'#161b27', border:'1px solid #1e2535', borderRadius:10, padding:12 }}>
            <div style={{ fontSize:12, color:'#10b981', marginBottom:6, fontWeight:600 }}>风险板块</div>
            {(sectorHeat.risk_sectors || []).slice(0,5).map((s:any,i:number) => (
              <div key={i} style={{ display:'flex', justifyContent:'space-between', padding:'3px 0', fontSize:12 }}>
                <span style={{ color:'#c9d1d9' }}>{s.name}</span>
                <span style={{ color: s.avg_pct<0?'#10b981':'#ef4444' }}>{s.avg_pct}% ({s.count}次)</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <button onClick={crawlNews} disabled={newsLoading}
          style={{ padding: '10px 28px', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600,
            cursor: newsLoading ? 'not-allowed' : 'pointer', background: newsLoading ? '#374151' : '#06b6d4', color: '#fff' }}>
          {newsLoading ? '⏳ 分析中...' : '📰 新闻速报'}
        </button>
        {lastAnalysis && (
          <span style={{ fontSize: 13, color: lastAnalysis.stale ? '#f59e0b' : '#6e7a8a' }}>
            {lastAnalysis.stale ? '⚠ ' : ''}上次: {lastAnalysis.hours_ago <= 1 ? '1h内' : lastAnalysis.hours_ago < 24 ? `${lastAnalysis.hours_ago.toFixed(0)}h前` : `${(lastAnalysis.hours_ago/24).toFixed(1)}天前`}
            {lastAnalysis.stale && ' (建议更新)'}
          </span>
        )}
        {newsError && <span style={{ fontSize: 13, color: '#ef4444' }}>❌ {newsError}</span>}
        <span style={{ flex: 1 }} />
        <button onClick={() => navigate('/scan')}
          style={{ padding: '10px 28px', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600,
            cursor: 'pointer', background: '#3b82f6', color: '#fff' }}>
          下一步 → TG扫描
        </button>
      </div>

      {newsLoading && (
        <div style={{ marginBottom: 16, padding: 12, background: '#161b27', borderRadius: 8, border: '1px solid #1e2535' }}>
          <div style={{ display:'flex',justifyContent:'space-between',marginBottom:6,fontSize:13 }}>
            <span style={{color:'#06b6d4'}}>{newsStep}</span>
            <span style={{color:'#6e7a8a'}}>{newsPct}%</span>
          </div>
          <div style={{height:4,background:'#1e2535',borderRadius:2}}>
            <div style={{height:'100%',width:`${newsPct}%`,background:'linear-gradient(90deg,#06b6d4,#10b981)',borderRadius:2,transition:'width .3s'}}/>
          </div>
        </div>
      )}

      {(aEvents.length > 0 || sectorEvents.length > 0 || macroEvents.length > 0) && (
        <div style={{ display:'flex', gap:12, flexWrap:'wrap' }}>
          {macroEvents.length > 0 && (
            <div style={{ flex:1, minWidth:280, padding: 14, background: '#161b27', borderRadius: 10, border: '1px solid rgba(6,182,212,0.2)' }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#06b6d4', marginBottom: 10 }}>🌍 宏观环境 ({macroEvents.length})</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {macroEvents.map((e: any, i: number) => (
                  <div key={i} style={{ fontSize: 13, padding: '6px 10px', background: 'rgba(30,37,53,0.5)', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontWeight: 600, color: '#06b6d4' }}>{(e.sector||'').replace('宏观-','')}</span>
                    <span style={{ color: dirColor(e.direction) }}>{dirEmoji(e.direction)}</span>
                    <span style={{ color: '#8b949e', flex: 1 }}>{e.prediction}</span>
                    <span style={{ color: '#6e7a8a' }}>影响: {e.impact?.toFixed(1)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {aEvents.length > 0 && (
            <div style={{ flex:1, minWidth:300, padding: 14, background: '#161b27', borderRadius: 10, border: '1px solid #1e2535' }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#c9d1d9', marginBottom: 4, display:'flex',alignItems:'center',gap:8 }}>
                ⚡ 个股事件 ({eventMarket==='全部' ? aEvents.length : eventMarket==='主板' ? mainEvents.length : eventMarket==='中小板' ? smeEvents.length : chinextEvents.length})
                {['全部','主板','中小板','创业板'].map(m => (
                  <button key={m} onClick={() => setEventMarket(m)}
                    style={{ padding:'1px 8px', borderRadius:10, fontSize:10, fontWeight:500, border:'1px solid',
                      background: eventMarket===m ? 'rgba(6,182,212,0.1)' : 'transparent',
                      color: eventMarket===m ? '#06b6d4' : '#6e7a8a',
                      borderColor: eventMarket===m ? 'rgba(6,182,212,0.2)' : '#1e2535',
                      cursor:'pointer' }}>{m}</button>
                ))}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {(eventMarket==='主板' ? mainEvents : eventMarket==='中小板' ? smeEvents : eventMarket==='创业板' ? chinextEvents : aEvents).map((e: any, i: number) => (
                  <div key={i} style={{ fontSize: 13, padding: '6px 10px', background: 'rgba(30,37,53,0.5)', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontWeight: 600, color: '#06b6d4' }}>{e.ts_code}</span>
                    <span style={{ color: dirColor(e.direction) }}>{dirEmoji(e.direction)}</span>
                    <span style={{ color: '#8b949e', flex: 1 }}>{e.title}</span>
                    {e.days_ago > 0 && (
                      <span style={{ fontSize: 10, color: '#4b5563', whiteSpace: 'nowrap' }}>{e.days_ago < 1 ? '今天' : `${e.days_ago.toFixed(0)}天前`}</span>
                    )}
                    <span style={{ fontSize: 10, padding: '1px 4px', borderRadius: 3,
                      background: e.freshness >= 0.8 ? 'rgba(16,185,129,0.15)' : e.freshness >= 0.4 ? 'rgba(245,158,11,0.12)' : 'rgba(239,68,68,0.12)',
                      color: e.freshness >= 0.8 ? '#10b981' : e.freshness >= 0.4 ? '#f59e0b' : '#ef4444' }}>
                      {e.freshness >= 0.8 ? '●' : e.freshness >= 0.4 ? '◐' : '○'}
                    </span>
                    <span style={{ color: '#6e7a8a', fontSize: 11 }}>{e.display_score?.toFixed(1)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {sectorEvents.length > 0 && (
            <div style={{ flex:1, minWidth:300, padding: 14, background: '#161b27', borderRadius: 10, border: '1px solid #1e2535' }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#c9d1d9', marginBottom: 10 }}>📊 板块影响 ({sectorEvents.length})</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {sectorEvents.map((e: any, i: number) => (
                  <div key={i} style={{ fontSize: 13, padding: '6px 10px', background: 'rgba(30,37,53,0.5)', borderRadius: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontWeight: 600, color: '#a78bfa' }}>{e.sector}</span>
                    <span style={{ color: dirColor(e.direction) }}>{dirEmoji(e.direction)}</span>
                    <span style={{ color: '#8b949e', flex: 1 }}>{e.prediction}</span>
                    <span style={{ color: '#6e7a8a' }}>影响: {e.impact?.toFixed(1)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── 龙虎榜分析 ── */}
      {toplistData && toplistData.total > 0 && (
        <div style={{ marginTop: 20 }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#c9d1d9', marginBottom: 12, display:'flex',alignItems:'center',gap:8 }}>
            🐉 龙虎榜分析
            <span style={{ fontSize: 12, fontWeight: 400, color: '#6e7a8a' }}>
              {toplistData.date} | {toplistData.total} 只上榜
            </span>
            {['全部','主板','中小板','创业板'].map(m => (
              <button key={m} onClick={() => setToplistMarket(m)}
                style={{ padding:'2px 10px', borderRadius:12, fontSize:11, fontWeight:500, border:'1px solid',
                  background: toplistMarket===m ? 'rgba(245,158,11,0.12)' : 'transparent',
                  color: toplistMarket===m ? '#f59e0b' : '#6e7a8a',
                  borderColor: toplistMarket===m ? 'rgba(245,158,11,0.25)' : '#1e2535',
                  cursor:'pointer' }}>{m}</button>
            ))}
          </div>

          {/* 板块共振 */}
          {toplistData.sectors?.length > 0 && (
            <div style={{ display:'flex', gap:10, flexWrap:'wrap', marginBottom: 16 }}>
              {toplistData.sectors.slice(0, 6).map((sec: any, i: number) => (
                <div key={i} style={{ flex: '1 1 180px', minWidth: 160, padding: 12, borderRadius: 10,
                  background: sec.resonance === 'strong' ? 'rgba(239,68,68,0.08)' : 'rgba(59,130,246,0.04)',
                  border: sec.resonance === 'strong' ? '1px solid rgba(239,68,68,0.25)' : '1px solid rgba(59,130,246,0.12)' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: '#c9d1d9' }}>{sec.sector}</span>
                    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, fontWeight: 600,
                      background: sec.resonance === 'strong' ? 'rgba(239,68,68,0.15)' : 'rgba(59,130,246,0.12)',
                      color: sec.resonance === 'strong' ? '#ef4444' : '#3b82f6' }}>
                      {sec.resonance === 'strong' ? '强共振' : '一般'}
                    </span>
                  </div>
                  <div style={{ display:'flex', gap: 10, fontSize: 11, color: '#8b949e' }}>
                    <span>📊 {sec.count}只</span>
                    <span>🏛 {sec.institutions}机构</span>
                    {sec.notable > 0 && <span>🔥 {sec.notable}游资</span>}
                    {sec.good_force > 0 && <span style={{color:'#10b981'}}>✓{sec.good_force}合力优</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 个股信号 TOP 10 */}
          <div style={{ display:'flex', gap: 10, flexWrap:'wrap', marginBottom: 16 }}>
            {toplistData.stocks?.filter((s:any) => toplistMarket==='全部' || s.market===toplistMarket).slice(0, 10).map((st: any, i: number) => {
              const color = st.force_label === '合力优' ? '#10b981' : st.force_label === '集中' ? '#f59e0b' : '#ef4444';
              const netColor = st.net_buy_wan > 0 ? '#ef4444' : '#10b981';
              return (
                <div key={i} style={{ flex: '0 0 auto', minWidth: 200, padding: '8px 12px', borderRadius: 8,
                  background: '#161b27', border: '1px solid #1e2535' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: '#06b6d4' }}>{st.ts_code}</span>
                    <span style={{ fontSize: 11, padding: '2px 6px', borderRadius: 4, fontWeight: 600,
                      background: st.force_label === '合力优' ? 'rgba(16,185,129,0.12)' : st.force_label === '集中' ? 'rgba(245,158,11,0.12)' : 'rgba(239,68,68,0.12)',
                      color }}>{st.force_label}</span>
                  </div>
                  <div style={{ display:'flex', gap: 10, fontSize: 11, color: '#8b949e', marginTop: 4 }}>
                    <span style={{ color: netColor, fontWeight: 600 }}>{st.net_buy_wan > 0 ? '+' : ''}{st.net_buy_wan}万</span>
                    <span>买一{(st.top1_ratio*100).toFixed(0)}%</span>
                    {st.institutions > 0 && <span>🏛{st.institutions}</span>}
                    {st.notable > 0 && <span>🔥{st.notable}</span>}
                    {st.retail > 0 && <span style={{color:'#f59e0b'}}>👤{st.retail}</span>}
                    {st.is_three_day && <span style={{color:'#f59e0b'}}>⚠3日</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!todayEvents && !newsLoading && (
        <div style={{ textAlign: 'center', padding: 40, color: '#4b5563' }}>
          <div style={{ fontSize: 40, marginBottom: 8 }}>📰</div>
          <div style={{ fontSize: 14 }}>点击「新闻速报」采集并分析最新财经资讯</div>
        </div>
      )}
    </div>
  );
}
