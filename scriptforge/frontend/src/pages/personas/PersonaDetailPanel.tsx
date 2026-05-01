import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, ChevronDown, ChevronRight } from 'lucide-react';
import { getPersona, getPersonaSlices } from '../../services/persona';
import Tabs from '../../components/ui/Tabs';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Spinner from '../../components/ui/Spinner';
import RadarChart from '../learn/RadarChart';

interface Props {
  personaId: string;
}

const DETAIL_TABS = [
  { key: 'overview', label: '特征总览' },
  { key: 'slices', label: '切片素材' },
  { key: 'history', label: '版本历史' },
];

export default function PersonaDetail({ personaId }: Props) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<string>('overview');

  const { data: persona, isLoading } = useQuery({
    queryKey: ['persona', personaId],
    queryFn: () => getPersona(personaId),
    enabled: !!personaId,
  });

  if (isLoading) return <div className="flex-1 flex items-center justify-center"><Spinner className="text-brand" /></div>;
  if (!persona) return <div className="flex-1 flex items-center justify-center text-text-muted">选择一个人设查看详情</div>;

  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold text-text-primary">{persona.name}</h2>
          <Badge variant="default">v{persona.version}</Badge>
        </div>
        <Button size="sm" onClick={() => navigate(`/scripts?persona_id=${personaId}`)}>
          应用到新脚本 <ArrowRight className="w-3.5 h-3.5" />
        </Button>
      </div>

      <Tabs tabs={DETAIL_TABS} active={activeTab} onChange={setActiveTab} />

      {activeTab === 'overview' && (
        <div className="space-y-4">
          {/* Style summary */}
          <div className="bg-bg-card border border-border-default rounded-lg p-4">
            <h4 className="text-sm font-medium text-text-secondary mb-2">风格综述</h4>
            <p className="text-sm text-text-primary leading-relaxed">{persona.global_style}</p>
          </div>

          {/* Radar + style */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-bg-card border border-border-default rounded-lg p-4">
              <h4 className="text-sm font-medium text-text-secondary mb-2">语言风格雷达</h4>
              <RadarChart data={persona.language_style || {}} />
            </div>
            <div className="space-y-4">
              {/* Catchphrases */}
              {persona.catchphrases?.length ? (
                <div className="bg-bg-card border border-border-default rounded-lg p-4">
                  <h4 className="text-sm font-medium text-text-secondary mb-2">口头禅</h4>
                  <div className="flex flex-wrap gap-2">
                    {persona.catchphrases.map((p, i) => <Badge key={i} variant="default">{p}</Badge>)}
                  </div>
                </div>
              ) : null}

              {/* Core values */}
              {persona.core_values?.length ? (
                <div className="bg-bg-card border border-border-default rounded-lg p-4">
                  <h4 className="text-sm font-medium text-text-secondary mb-2">核心价值观</h4>
                  <div className="flex flex-wrap gap-2">
                    {persona.core_values.map((v, i) => <Badge key={i} variant="success">{v}</Badge>)}
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          {/* Reaction patterns */}
          {persona.reaction_patterns && Object.keys(persona.reaction_patterns).length > 0 && (
            <div className="bg-bg-card border border-border-default rounded-lg p-4">
              <h4 className="text-sm font-medium text-text-secondary mb-3">反应模式</h4>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(persona.reaction_patterns).map(([key, val]) => (
                  <div key={key} className="bg-bg-primary rounded-md p-3">
                    <p className="text-xs text-brand font-medium mb-1">{key}</p>
                    <p className="text-sm text-text-primary">{String(val)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sentence templates */}
          {persona.sentence_templates?.length ? (
            <div className="bg-bg-card border border-border-default rounded-lg p-4">
              <h4 className="text-sm font-medium text-text-secondary mb-3">句式模板</h4>
              <ul className="space-y-2 font-mono text-sm">
                {persona.sentence_templates.map((tpl, i) => (
                  <li key={i} className="bg-bg-primary rounded-md px-3 py-2 text-text-primary">{tpl}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      )}

      {activeTab === 'slices' && (
        <SlicesTab personaId={personaId} totalCount={persona.slice_count} onNavigate={navigate} />
      )}

      {activeTab === 'history' && (
        <div className="space-y-2">
          {Array.from({ length: persona.version }, (_, i) => persona.version - i).map((v) => {
            const note = persona.version_notes?.find((n) => n.version === v);
            return (
              <div key={v} className="bg-bg-card border border-border-default rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-text-primary font-medium">版本 {v}</span>
                    {v === persona.version && <Badge variant="success">当前</Badge>}
                  </div>
                  <span className="text-xs text-text-muted">{persona.created_at?.split('T')[0] || '未知日期'}</span>
                </div>
                {note && (
                  <div className="mt-2 text-xs text-text-muted flex items-center gap-3">
                    <span>+{note.added_slices} 条切片</span>
                    <span>{note.summary}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function SlicesTab({ personaId, totalCount, onNavigate }: { personaId: string; totalCount: number; onNavigate: (path: string) => void }) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const { data: slicesData, isLoading } = useQuery({
    queryKey: ['persona-slices', personaId],
    queryFn: () => getPersonaSlices(personaId),
    enabled: !!personaId,
  });

  const slices = slicesData?.items || [];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-text-secondary">关联切片 {totalCount} 条</p>
        <Button size="sm" variant="ghost" onClick={() => onNavigate('/learn')}>上传新切片</Button>
      </div>
      {isLoading ? (
        <div className="flex justify-center py-8"><Spinner className="text-brand" /></div>
      ) : slices.length === 0 ? (
        <p className="text-sm text-text-muted py-8 text-center">暂无切片数据</p>
      ) : (
        <div className="space-y-2">
          {slices.map((s: any, i: number) => (
            <div key={s.id} className="bg-bg-card border border-border-default rounded-lg p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {s.emotion_tag && <Badge variant="default" className="text-[10px]">{s.emotion_tag}</Badge>}
                    {s.action_desc && <span className="text-xs text-text-muted">{s.action_desc}</span>}
                  </div>
                  <p className="text-sm text-text-primary">
                    {expandedIdx === i ? s.original_text : s.preview}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {s.source_url && <span className="text-[10px] text-text-muted truncate max-w-[80px]">{s.source_url}</span>}
                  <button
                    onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
                    className="text-text-muted hover:text-text-primary"
                  >
                    {expandedIdx === i ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
