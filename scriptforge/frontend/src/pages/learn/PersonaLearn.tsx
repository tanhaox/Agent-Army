import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Sparkles, ArrowRight } from 'lucide-react';
import TxtUploader from './TxtUploader';
import RadarChart from './RadarChart';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Card from '../../components/ui/Card';
import Spinner from '../../components/ui/Spinner';
import { toast } from '../../components/ui/Toast';
import { analyzePersona, getPersona, listPersonas, appendSlices } from '../../services/persona';
import type { PersonaDetail } from '../../types';

const EMOTION_OPTIONS = [
  '搞笑', '感动', '愤怒', '震惊', '煽情', '反转打脸', '其他',
];

export default function PersonaLearn() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const [emotion, setEmotion] = useState('');
  const [actionDesc, setActionDesc] = useState('');
  const [personaId, setPersonaId] = useState<string | null>(null);
  const [report, setReport] = useState<PersonaDetail | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);

  const [selectedAppendId, setSelectedAppendId] = useState('');
  const [appendResult, setAppendResult] = useState<{ version: number; summary: string } | null>(null);

  const { data: personasData } = useQuery({
    queryKey: ['personas'],
    queryFn: () => listPersonas(0, 50),
  });
  const availablePersonas = personasData?.items || [];

  const analyzeMut = useMutation({
    mutationFn: async () => {
      // Read all txt files as text
      const texts = await Promise.all(
        files.map((f) => f.text())
      );
      return analyzePersona({
        slices: texts.map((text, i) => ({
          text,
          source_url: files[i]?.name || undefined,
        })),
        force_new: false,
      });
    },
    onSuccess: async (result) => {
      toast('success', `人设分析完成，已${result.action === 'created' ? '创建' : '更新'}`);
      setPersonaId(result.persona_id);

      // Fetch full persona detail
      setLoadingReport(true);
      try {
        const detail = await getPersona(result.persona_id);
        setReport(detail);
      } catch {
        toast('error', '获取人设详情失败');
      } finally {
        setLoadingReport(false);
      }

      setFiles([]);
    },
    onError: (err: any) => {
      toast('error', err?.response?.data?.detail || '分析失败，请检查后端服务');
    },
  });

  const canAnalyze = files.length > 0 && !analyzeMut.isPending;

  const appendMut = useMutation({
    mutationFn: async () => {
      if (!selectedAppendId || files.length === 0) throw new Error('请选择人设并上传文件');
      const texts = await Promise.all(files.map((f) => f.text()));
      return appendSlices(selectedAppendId, texts, {
        emotion_tag: emotion || undefined,
        action_desc: actionDesc || undefined,
      });
    },
    onSuccess: (result) => {
      toast('success', `已追加到人设，版本更新至 v${result.version}`);
      setAppendResult({ version: result.version, summary: result.changes_summary?.summary || '特征已更新' });
      setFiles([]);
    },
    onError: (err: any) => {
      toast('error', err?.response?.data?.detail || '追加失败');
    },
  });

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Upload */}
      <TxtUploader files={files} onFilesChange={setFiles} />

      {/* Metadata */}
      <Card>
        <h3 className="text-sm font-medium text-text-primary mb-3">高级选项</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-text-secondary">切片情绪主调</label>
            <select
              value={emotion}
              onChange={(e) => setEmotion(e.target.value)}
              className="bg-bg-primary border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand transition-colors"
            >
              <option value="">未选择</option>
              {EMOTION_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-text-secondary">关键动作描述</label>
            <input
              value={actionDesc}
              onChange={(e) => setActionDesc(e.target.value)}
              placeholder="可选，如：拍桌子、突然站起"
              className="bg-bg-primary border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand transition-colors"
            />
          </div>
        </div>
      </Card>

      {/* Action */}
      <Button
        size="lg"
        disabled={!canAnalyze}
        loading={analyzeMut.isPending}
        onClick={() => analyzeMut.mutate()}
        className="w-full"
      >
        {analyzeMut.isPending ? '分析中...' : '开始分析'}
      </Button>

      {/* Loading report */}
      {loadingReport && (
        <div className="flex items-center justify-center py-12 gap-3 text-text-secondary">
          <Spinner size={20} className="text-brand" />
          <span className="text-sm">加载人设报告...</span>
        </div>
      )}

      {/* Report */}
      {report && !loadingReport && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-text-primary">
            <Sparkles className="w-5 h-5 text-brand" />
            <h2 className="text-lg font-semibold">人设分析报告</h2>
          </div>

          {/* Persona ID */}
          <p className="text-xs text-text-muted">Persona ID: {personaId}</p>

          {/* Radar + Style */}
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <h4 className="text-sm font-medium text-text-secondary mb-2">风格雷达</h4>
              <RadarChart data={report.language_style || {}} />
            </Card>
            <Card>
              <h4 className="text-sm font-medium text-text-secondary mb-2">风格评述</h4>
              <p className="text-sm text-text-primary leading-relaxed">
                {report.global_style}
              </p>
              {report.version > 1 && (
                <p className="text-xs text-text-muted mt-3">版本 v{report.version}</p>
              )}
            </Card>
          </div>

          {/* Catchphrases */}
          {report.catchphrases && report.catchphrases.length > 0 && (
            <Card>
              <h4 className="text-sm font-medium text-text-secondary mb-3">口头禅</h4>
              <div className="flex flex-wrap gap-2">
                {report.catchphrases.map((phrase, i) => (
                  <Badge key={i} variant="default">{phrase}</Badge>
                ))}
              </div>
            </Card>
          )}

          {/* Reaction patterns */}
          {report.reaction_patterns && Object.keys(report.reaction_patterns).length > 0 && (
            <Card>
              <h4 className="text-sm font-medium text-text-secondary mb-3">反应模式</h4>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(report.reaction_patterns).map(([key, val]) => (
                  <div key={key} className="bg-bg-primary rounded-md p-3">
                    <p className="text-xs text-brand font-medium mb-1">{key}</p>
                    <p className="text-sm text-text-primary">{String(val)}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Sentence templates */}
          {report.sentence_templates && report.sentence_templates.length > 0 && (
            <Card>
              <h4 className="text-sm font-medium text-text-secondary mb-3">句式模板</h4>
              <ul className="space-y-2 font-mono text-sm">
                {report.sentence_templates.map((tpl, i) => (
                  <li key={i} className="bg-bg-primary rounded-md px-3 py-2 text-text-primary">
                    {tpl}
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {/* Core values */}
          {report.core_values && report.core_values.length > 0 && (
            <Card>
              <h4 className="text-sm font-medium text-text-secondary mb-3">核心价值观</h4>
              <div className="flex flex-wrap gap-2">
                {report.core_values.map((v, i) => (
                  <Badge key={i} variant="success">{v}</Badge>
                ))}
              </div>
            </Card>
          )}

          {/* Append to existing persona */}
          <Card>
            <h4 className="text-sm font-medium text-text-secondary mb-3">追加到已有人设</h4>
            <div className="flex gap-2">
              <select
                value={selectedAppendId}
                onChange={(e) => { setSelectedAppendId(e.target.value); setAppendResult(null); }}
                className="flex-1 bg-bg-primary border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand"
              >
                <option value="">选择目标人设...</option>
                {availablePersonas.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} (v{p.version})</option>
                ))}
              </select>
              <Button
                size="md"
                disabled={!selectedAppendId || files.length === 0}
                loading={appendMut.isPending}
                onClick={() => appendMut.mutate()}
              >
                追加
              </Button>
            </div>
            {appendResult && (
              <div className="mt-3 bg-bg-primary rounded-md p-3 text-sm space-y-1">
                <p className="text-text-primary">已更新至 <Badge variant="success">v{appendResult.version}</Badge></p>
                <p className="text-text-muted">{appendResult.summary}</p>
              </div>
            )}
          </Card>

          {/* Navigate to persona detail */}
          {personaId && (
            <Button variant="secondary" onClick={() => navigate(`/personas?select=${personaId}`)} className="w-full">
              查看人设详情 <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
