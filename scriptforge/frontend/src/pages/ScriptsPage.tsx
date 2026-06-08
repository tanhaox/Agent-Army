import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from '../components/ui/Toast';
import Spinner from '../components/ui/Spinner';
import { generateScript, updateScript, regeneratePart } from '../services/scripts';
import type { GenerateParams, ScriptResult, DirectorRole, DirectorAct } from '../services/scripts';
import { listPersonas } from '../services/persona';
import { listRoomTones } from '../services/roomTone';

import StepIndicator from './scripts/StepIndicator';
import StepOneForm from './scripts/StepOneForm';
import StepTwoForm from './scripts/StepTwoForm';
import StepThreeForm from './scripts/StepThreeForm';
import StepFourPanel from './scripts/StepFourPanel';
import PreviewPanel from './scripts/PreviewPanel';
import ScriptDisplay from './scripts/ScriptDisplay';
import DegradedBanner from '../components/ui/DegradedBanner';
import { saveDirectorDraft, loadDirectorDraft, clearDirectorDraft } from '../lib/autoSave';

export interface StepOneData {
  toneId: string;
  customTone: string;
  sceneType: string;
  directorMode: boolean;
  topic: string;
}

export default function ScriptsPage() {
  const [searchParams] = useSearchParams();
  const preselectedPersonaId = searchParams.get('persona_id') || undefined;

  // Step navigation
  const [step, setStep] = useState(0);
  const [maxReached, setMaxReached] = useState(0);

  // Step 1: Setup
  const [stepOne, setStepOne] = useState<StepOneData>({
    toneId: '',
    customTone: '',
    sceneType: 'entertainment_comedy',
    directorMode: false,
    topic: '',
  });

  // Step 2: Cast
  const [roles, setRoles] = useState<DirectorRole[]>([]);

  // Step 3: Outline
  const [acts, setActs] = useState<DirectorAct[]>([]);

  // Step 4: Generate
  const [emotionCurve, setEmotionCurve] = useState('default');
  const [requiredLines, setRequiredLines] = useState('');
  const [multiVersion, setMultiVersion] = useState(false);
  const [enableCallerEnhancement, setEnableCallerEnhancement] = useState(true);
  const [result, setResult] = useState<ScriptResult | null>(null);

  // Resolve tone name for preview
  const { data: tonesData } = useQuery({ queryKey: ['roomTones'], queryFn: listRoomTones });
  const { data: personasData } = useQuery({ queryKey: ['personas'], queryFn: () => listPersonas(0, 50) });
  const toneName = tonesData?.items?.find((t) => t.id === stepOne.toneId)?.name;

  // Derive anchor follower count from selected persona
  const primaryAnchor = roles.find((r) => r.role_type === 'anchor');
  const anchorPersona = personasData?.items?.find((p) => p.id === primaryAnchor?.persona_id);
  const anchorFollowerCount = anchorPersona?.source_follower_count ?? 0;

  // Auto-add primary anchor from preselected persona
  useEffect(() => {
    if (preselectedPersonaId && roles.length === 0) {
      const persona = personasData?.items?.find((p) => p.id === preselectedPersonaId);
      if (persona) {
        setRoles([{ role_type: 'anchor', name: persona.name, position: '主唛', function: '主持控场', persona_id: persona.id, sort_order: 0 }]);
      }
    }
  }, [preselectedPersonaId, personasData]);

  // Restore director draft on mount
  useEffect(() => {
    const draft = loadDirectorDraft();
    if (!draft) return;
    setStepOne(prev => ({
      ...prev,
      directorMode: true,
      toneId: draft.stepOne.toneId || prev.toneId,
      customTone: draft.stepOne.customTone || '',
      sceneType: draft.stepOne.sceneType || prev.sceneType,
      topic: draft.stepOne.topic || '',
    }));
    if (draft.roles.length > 0) setRoles(draft.roles);
    if (draft.acts.length > 0) setActs(draft.acts);
    toast('info', '已恢复上次未完成的编导草稿');
  }, []);

  // Auto-save director draft (debounced)
  const saveTimerRef = useRef<ReturnType<typeof setTimeout>>();
  useEffect(() => {
    if (!stepOne.directorMode) return;
    if (roles.length === 0 && acts.length === 0) return;
    clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      saveDirectorDraft({
        timestamp: Date.now(),
        roles,
        acts,
        stepOne: { toneId: stepOne.toneId, customTone: stepOne.customTone, sceneType: stepOne.sceneType, topic: stepOne.topic },
      });
    }, 500);
    return () => clearTimeout(saveTimerRef.current);
  }, [stepOne.directorMode, roles, acts, stepOne.toneId, stepOne.customTone, stepOne.sceneType, stepOne.topic]);

  const goTo = (s: number) => {
    if (s <= maxReached) setStep(s);
  };
  const goNext = () => {
    const next = step + 1;
    // In simple mode, skip step 2 (outline)
    const realNext = (!stepOne.directorMode && next === 2) ? 3 : next;
    setStep(realNext);
    if (realNext > maxReached) setMaxReached(realNext);
  };
  const goBack = () => { if (step > 0) setStep(step - 1); };

  // Can proceed checks
  const stepOneValid = (stepOne.toneId === '__custom__' ? stepOne.customTone.trim() : stepOne.toneId) && (!stepOne.directorMode || true) && (stepOne.directorMode || stepOne.topic.trim());
  const stepTwoValid = roles.some((r) => r.role_type === 'anchor' && r.persona_id);
  const stepThreeValid = !stepOne.directorMode || acts.length > 0;

  const canGenerate = stepOneValid && stepTwoValid && (stepOne.directorMode ? stepThreeValid : true);

  // Generate mutation
  const generateMut = useMutation({
    mutationFn: (params: GenerateParams) => generateScript(params),
    onSuccess: (data) => {
      setResult(data);
      clearDirectorDraft();
      if (data.multi_version && data.versions) {
        toast('success', `已生成 ${data.versions.length} 个版本脚本`);
      } else {
        const count = data.dialogues?.length ?? 0;
        toast('success', count > 0 ? `脚本生成完成：${count} 轮对话` : '脚本生成完成');
      }
    },
    onError: (err: any) => toast('error', err?.response?.data?.detail || '脚本生成失败'),
  });

  const handleGenerate = () => {
    const primaryAnchor = roles.find((r) => r.role_type === 'anchor');
    const guestRoles = roles.filter((r) => r.role_type !== 'anchor');

    // Build guest_config: single object for 1 guest, array for multiple
    const guestConfigs = guestRoles.map((g) => ({
      name: g.name || undefined,
      core_issue: g.storyline || undefined,
      personality: g.function || undefined,
      occupation: undefined,
      perspective: g.perspective || undefined,
    }));
    const guestConfig = guestConfigs.length === 0
      ? { core_issue: stepOne.topic || '直播连线' }
      : guestConfigs.length === 1
        ? guestConfigs[0]
        : guestConfigs;

    generateMut.mutate({
      tone_id: stepOne.toneId === '__custom__' ? '' : stepOne.toneId,
      persona_id: primaryAnchor?.persona_id || '',
      guest_config: guestConfig as any,
      emotion_curve: emotionCurve,
      scene_type: stepOne.sceneType,
      multi_version: multiVersion || undefined,
      enable_caller_enhancement: enableCallerEnhancement && anchorFollowerCount >= 1000000,
      topic: stepOne.topic.trim() || undefined,
      required_lines: requiredLines.trim() ? requiredLines.trim().split('\n').filter((l) => l.trim()) : undefined,
      custom_tone: stepOne.customTone.trim() || undefined,
      director_roles: stepOne.directorMode ? roles : undefined,
      director_acts: stepOne.directorMode ? acts : undefined,
    });
  };

  const handleSave = async (content: any) => {
    if (!result) return;
    try { await updateScript(result.script_id, content); toast('success', '脚本已保存'); }
    catch { toast('error', '保存失败'); }
  };

  const handleRegenerate = async (speaker: string) => {
    if (!result) return;
    try {
      const res = await regeneratePart(result.script_id, speaker);
      toast('success', `已重新生成 ${res.regenerated_count} 条${speaker}台词`);
      generateMut.reset();
    } catch (err: any) { toast('error', err?.response?.data?.detail || '重新生成失败'); }
  };

  const isGenerating = generateMut.isPending;
  const hasResult = !!result;

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem-3rem)]">
      {/* Step indicator */}
      <StepIndicator current={step} maxStep={maxReached} directorMode={stepOne.directorMode} onChange={goTo} />

      {/* Main content area */}
      {!hasResult ? (
        <div className="flex flex-1 min-h-0">
          {/* Left panel */}
          <div className="w-[400px] shrink-0 border-r border-border-default bg-bg-sidebar overflow-y-auto p-5 space-y-4">
            {/* Step forms */}
            {step === 0 && <StepOneForm data={stepOne} onChange={setStepOne} />}
            {step === 1 && <StepTwoForm roles={roles} onChange={setRoles} anchorFollowerCount={anchorFollowerCount} />}
            {step === 2 && stepOne.directorMode && <StepThreeForm acts={acts} roles={roles} onChange={setActs} />}
            {step === 3 && (
              <StepFourPanel
                emotionCurve={emotionCurve} setEmotionCurve={setEmotionCurve}
                requiredLines={requiredLines} setRequiredLines={setRequiredLines}
                multiVersion={multiVersion} setMultiVersion={setMultiVersion}
                enableCallerEnhancement={enableCallerEnhancement} setEnableCallerEnhancement={setEnableCallerEnhancement}
                anchorFollowerCount={anchorFollowerCount}
                loading={isGenerating} canGenerate={canGenerate}
                onGenerate={handleGenerate}
              />
            )}

            {/* Navigation buttons */}
            <div className="flex items-center justify-between pt-4 border-t border-border-default">
              {step > 0 ? (
                <button onClick={goBack} className="flex items-center gap-1 px-4 py-2 text-sm text-text-secondary hover:text-text-primary border border-border-default rounded-md hover:bg-bg-hover transition-colors">
                  <ChevronLeft className="w-4 h-4" /> 上一步
                </button>
              ) : <div />}
              {step < 3 && (
                <button
                  disabled={step === 0 ? !stepOneValid : step === 1 ? !stepTwoValid : !stepThreeValid}
                  onClick={goNext}
                  className="flex items-center gap-1 px-4 py-2 text-sm text-white bg-brand hover:bg-brand-hover rounded-md disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  下一步 <ChevronRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Right preview */}
          <PreviewPanel
            step={step}
            directorMode={stepOne.directorMode}
            toneName={toneName}
            customTone={stepOne.customTone}
            sceneType={stepOne.sceneType}
            directorModeValue={stepOne.directorMode}
            topic={stepOne.topic}
            roles={roles}
            acts={acts}
            generated={false}
          />
        </div>
      ) : isGenerating ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-4">
            <Spinner size={40} className="text-brand mx-auto" />
            <p className="text-text-secondary text-sm">AI 正在精心创作中...</p>
            <p className="text-text-muted text-xs">预计需要 15-60 秒</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-auto">
          {result.degraded && <div className="px-6 pt-4"><DegradedBanner /></div>}
          <ScriptDisplay result={result} onSave={handleSave} onRegenerate={handleRegenerate} />
        </div>
      )}
    </div>
  );
}
