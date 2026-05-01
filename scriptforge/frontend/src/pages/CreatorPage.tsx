import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Wand2, Users, Shuffle, Download, Save, Sparkles, ArrowRight } from 'lucide-react';
import { createPersona, createGuests, fusePersonas, savePersona } from '../services/creator';
import { listPersonas } from '../services/persona';
import type { CreatorPersonaResult, GuestCard } from '../services/creator';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import { toast } from '../components/ui/Toast';

type Tab = 'persona' | 'guests' | 'fusion';

const TABS: { key: Tab; label: string; icon: typeof Wand2 }[] = [
  { key: 'persona', label: '生成网红', icon: Wand2 },
  { key: 'guests', label: '批量连线人', icon: Users },
  { key: 'fusion', label: '风格融合', icon: Shuffle },
];

const RADAR_DIMS = [
  { key: 'aggressiveness', label: '攻击性' },
  { key: 'humor', label: '幽默' },
  { key: 'empathy', label: '共情' },
  { key: 'rhythm', label: '节奏' },
  { key: 'metaphor_usage', label: '比喻' },
  { key: 'catchphrase_density', label: '口头禅密度' },
];

function PersonaDisplay({ persona }: { persona: CreatorPersonaResult }) {
  const ls = persona.language_style || {};
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h3 className="text-lg font-semibold text-text-primary">{persona.persona_name}</h3>
        {persona.style_summary && <span className="text-xs text-text-muted">{persona.style_summary}</span>}
      </div>

      {persona.global_style && (
        <p className="text-sm text-text-secondary leading-relaxed">{persona.global_style}</p>
      )}

      {/* Radar bars */}
      <div className="space-y-2">
        {RADAR_DIMS.map((dim) => {
          const val = (ls[dim.key] as number) || 0;
          return (
            <div key={dim.key} className="flex items-center gap-3">
              <span className="text-xs text-text-muted w-20 shrink-0">{dim.label}</span>
              <div className="flex-1 h-2 bg-bg-hover rounded-full overflow-hidden">
                <div className="h-full bg-brand rounded-full transition-all" style={{ width: `${val * 10}%` }} />
              </div>
              <span className="text-xs text-text-secondary w-6 text-right">{val}</span>
            </div>
          );
        })}
      </div>

      {/* Catchphrases */}
      {persona.catchphrases?.length > 0 && (
        <div>
          <p className="text-xs font-medium text-text-secondary mb-1.5">口头禅</p>
          <div className="flex flex-wrap gap-1.5">
            {persona.catchphrases.map((c, i) => (
              <Badge key={i} variant="default">{c}</Badge>
            ))}
          </div>
        </div>
      )}

      {/* Reaction patterns */}
      {persona.reaction_patterns && Object.keys(persona.reaction_patterns).length > 0 && (
        <div>
          <p className="text-xs font-medium text-text-secondary mb-1.5">反应模式</p>
          <div className="space-y-1">
            {Object.entries(persona.reaction_patterns).map(([k, v]) => (
              <div key={k} className="flex items-start gap-2 text-sm">
                <Badge variant="warning">{k}</Badge>
                <span className="text-text-secondary">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sentence templates */}
      {persona.sentence_templates?.length > 0 && (
        <div>
          <p className="text-xs font-medium text-text-secondary mb-1.5">常用句式</p>
          <div className="space-y-1">
            {persona.sentence_templates.map((t, i) => (
              <p key={i} className="text-sm text-text-primary bg-bg-card border border-border-default rounded-md px-3 py-1.5">{t}</p>
            ))}
          </div>
        </div>
      )}

      {/* Core values */}
      {persona.core_values?.length > 0 && (
        <div>
          <p className="text-xs font-medium text-text-secondary mb-1.5">核心价值观</p>
          <div className="flex flex-wrap gap-1.5">
            {persona.core_values.map((v, i) => (
              <Badge key={i} variant="success">{v}</Badge>
            ))}
          </div>
        </div>
      )}

      {/* Recommended scenarios */}
      {persona.recommended_scenarios?.length > 0 && (
        <div>
          <p className="text-xs font-medium text-text-secondary mb-1.5">推荐调性</p>
          <div className="flex flex-wrap gap-1.5">
            {persona.recommended_scenarios.map((s, i) => (
              <Badge key={i} variant="default">{s}</Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function CreatorPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>('persona');
  const [savedPersonaId, setSavedPersonaId] = useState<string | null>(null);

  // --- Tab 1: Persona ---
  const [requirements, setRequirements] = useState('');
  const [generatedPersona, setGeneratedPersona] = useState<CreatorPersonaResult | null>(null);

  const personaMut = useMutation({
    mutationFn: (req: string) => createPersona(req),
    onSuccess: (data) => { setGeneratedPersona(data.persona); toast('success', '人设生成完成'); },
    onError: (err: any) => { toast('error', err?.response?.data?.detail || '生成失败'); },
  });

  const savePersonaMut = useMutation({
    mutationFn: (data: CreatorPersonaResult) => savePersona(data),
    onSuccess: (res) => { setSavedPersonaId(res.persona_id); toast('success', '人设已保存'); },
    onError: (err: any) => { toast('error', err?.response?.data?.detail || '保存失败'); },
  });

  // --- Tab 2: Guests ---
  const [guestTopic, setGuestTopic] = useState('');
  const [guestCount, setGuestCount] = useState(20);
  const [generatedGuests, setGeneratedGuests] = useState<GuestCard[]>([]);

  const guestMut = useMutation({
    mutationFn: () => createGuests(guestTopic, guestCount),
    onSuccess: (data) => { setGeneratedGuests(data.guests); toast('success', `已生成 ${data.count} 个连线人`); },
    onError: (err: any) => { toast('error', err?.response?.data?.detail || '生成失败'); },
  });

  // --- Tab 3: Fusion ---
  const [fusionIdA, setFusionIdA] = useState('');
  const [fusionIdB, setFusionIdB] = useState('');
  const [fusionRatio, setFusionRatio] = useState(0.5);
  const [fusedPersona, setFusedPersona] = useState<CreatorPersonaResult | null>(null);

  const { data: personasData } = useQuery({
    queryKey: ['personas-for-fusion'],
    queryFn: () => listPersonas(0, 50),
  });
  const personaOptions = personasData?.items || [];

  const fusionMut = useMutation({
    mutationFn: () => fusePersonas(fusionIdA, fusionIdB, fusionRatio),
    onSuccess: (data) => { setFusedPersona(data.persona); toast('success', '风格融合完成'); },
    onError: (err: any) => { toast('error', err?.response?.data?.detail || '融合失败'); },
  });

  const handleExportGuests = () => {
    const text = generatedGuests.map((g) =>
      `[${g.name}] ${g.age_range} | ${g.occupation}\n性格: ${g.personality}\n问题: ${g.core_issue}\n风格: ${g.speaking_style}\n标签: ${g.tags.join('、')}\n预期反应: ${g.expected_reaction}`
    ).join('\n\n---\n\n');
    navigator.clipboard.writeText(text).then(() => toast('success', '已复制到剪贴板'));
  };

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Tab bar */}
      <div className="px-6 py-3 border-b border-border-default flex gap-1">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === key ? 'bg-brand text-white' : 'text-text-secondary hover:bg-bg-hover'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {/* === Tab 1: Generate Persona === */}
        {activeTab === 'persona' && (
          <div className="max-w-3xl mx-auto space-y-6">
            <div>
              <label className="text-sm font-medium text-text-secondary block mb-2">风格要求</label>
              <textarea
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder="例如：一个温暖但有锋芒的情感主播，善于用做饭比喻人生，口头禅'家人们谁懂啊'"
                rows={4}
                className="w-full bg-bg-card border border-border-default rounded-lg px-4 py-3 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand resize-none"
              />
            </div>
            <Button
              size="lg"
              disabled={!requirements.trim()}
              loading={personaMut.isPending}
              onClick={() => personaMut.mutate(requirements)}
            >
              <Sparkles className="w-4 h-4" />
              生成人设
            </Button>

            {personaMut.isPending && (
              <div className="flex items-center justify-center py-12">
                <Spinner size={32} className="text-brand" />
                <span className="ml-3 text-sm text-text-secondary">AI 正在设计中...</span>
              </div>
            )}

            {generatedPersona && !personaMut.isPending && (
              <div className="space-y-4">
                <div className="bg-bg-card border border-border-default rounded-lg p-5">
                  <PersonaDisplay persona={generatedPersona} />
                </div>
                <div className="flex gap-3">
                  <Button onClick={() => savePersonaMut.mutate(generatedPersona)} loading={savePersonaMut.isPending}>
                    <Save className="w-4 h-4" />
                    保存人设
                  </Button>
                  {savedPersonaId && (
                    <Button variant="secondary" onClick={() => navigate(`/scripts?persona_id=${savedPersonaId}`)}>
                      立即生成脚本 <ArrowRight className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* === Tab 2: Batch Guests === */}
        {activeTab === 'guests' && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex gap-3">
              <input
                value={guestTopic}
                onChange={(e) => setGuestTopic(e.target.value)}
                placeholder="输入主题，如：职场吐槽、情感困惑、家庭矛盾"
                className="flex-1 bg-bg-card border border-border-default rounded-lg px-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
              />
              <select
                value={guestCount}
                onChange={(e) => setGuestCount(Number(e.target.value))}
                className="bg-bg-card border border-border-default rounded-lg px-3 py-2.5 text-sm text-text-primary outline-none"
              >
                {[5, 10, 15, 20, 30, 50].map((n) => (
                  <option key={n} value={n}>{n} 个</option>
                ))}
              </select>
              <Button disabled={!guestTopic.trim()} loading={guestMut.isPending} onClick={() => guestMut.mutate()}>
                <Users className="w-4 h-4" />
                生成连线人
              </Button>
            </div>

            {guestMut.isPending && (
              <div className="flex items-center justify-center py-12">
                <Spinner size={32} className="text-brand" />
                <span className="ml-3 text-sm text-text-secondary">AI 正在生成中...</span>
              </div>
            )}

            {generatedGuests.length > 0 && !guestMut.isPending && (
              <>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-text-muted">已生成 {generatedGuests.length} 个连线人</span>
                  <Button size="sm" variant="ghost" onClick={handleExportGuests}>
                    <Download className="w-3.5 h-3.5" /> 导出全部
                  </Button>
                </div>
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                  {generatedGuests.map((g, i) => (
                    <div key={i} className="bg-bg-card border border-border-default rounded-lg p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-text-primary">{g.name}</span>
                        <Badge variant="default" className="text-[10px]">{g.age_range}</Badge>
                      </div>
                      <p className="text-xs text-text-muted">{g.occupation} | {g.personality}</p>
                      <p className="text-sm text-text-primary">{g.core_issue}</p>
                      <div className="flex flex-wrap gap-1">
                        {g.tags.map((t, ti) => (
                          <Badge key={ti} variant="success" className="text-[10px]">{t}</Badge>
                        ))}
                      </div>
                      <p className="text-[10px] text-text-muted">预期反应: {g.expected_reaction}</p>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* === Tab 3: Fusion === */}
        {activeTab === 'fusion' && (
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-text-secondary block mb-1.5">人设 A</label>
                <select
                  value={fusionIdA}
                  onChange={(e) => setFusionIdA(e.target.value)}
                  className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand"
                >
                  <option value="">选择人设...</option>
                  {personaOptions.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-text-secondary block mb-1.5">人设 B</label>
                <select
                  value={fusionIdB}
                  onChange={(e) => setFusionIdB(e.target.value)}
                  className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand"
                >
                  <option value="">选择人设...</option>
                  {personaOptions.filter((p) => p.id !== fusionIdA).map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-text-secondary block mb-1.5">
                融合比例 — A: {Math.round(fusionRatio * 100)}% / B: {Math.round((1 - fusionRatio) * 100)}%
              </label>
              <input
                type="range"
                min={0.1}
                max={0.9}
                step={0.1}
                value={fusionRatio}
                onChange={(e) => setFusionRatio(Number(e.target.value))}
                className="w-full accent-brand"
              />
            </div>

            <Button
              disabled={!fusionIdA || !fusionIdB}
              loading={fusionMut.isPending}
              onClick={() => fusionMut.mutate()}
            >
              <Shuffle className="w-4 h-4" />
              融合生成
            </Button>

            {fusionMut.isPending && (
              <div className="flex items-center justify-center py-12">
                <Spinner size={32} className="text-brand" />
                <span className="ml-3 text-sm text-text-secondary">AI 正在融合中...</span>
              </div>
            )}

            {fusedPersona && !fusionMut.isPending && (
              <div className="space-y-4">
                <div className="bg-bg-card border border-border-default rounded-lg p-5">
                  <PersonaDisplay persona={fusedPersona} />
                </div>
                <div className="flex gap-3">
                  <Button onClick={() => savePersonaMut.mutate(fusedPersona)} loading={savePersonaMut.isPending}>
                    <Save className="w-4 h-4" />
                    保存人设
                  </Button>
                  {savedPersonaId && (
                    <Button variant="secondary" onClick={() => navigate(`/scripts?persona_id=${savedPersonaId}`)}>
                      立即生成脚本 <ArrowRight className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
