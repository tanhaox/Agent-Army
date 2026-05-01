import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronRight, Sparkles } from 'lucide-react';
import { listRoomTones } from '../../services/roomTone';
import { listPersonas } from '../../services/persona';
import type { GenerateParams } from '../../services/scripts';

const EMOTION_CURVES = [
  { value: 'default', label: '自然起伏' },
  { value: 'rollercoaster', label: '过山车式' },
  { value: 'warm', label: '温水煮蛙' },
  { value: 'confrontation', label: '对抗式' },
  { value: 'mystery', label: '悬疑式' },
];

const SCENE_TYPES = [
  { value: 'entertainment', label: '泛娱乐连线', desc: '制造娱乐效果和可切片的高能时刻' },
  { value: 'talent', label: '才艺维护', desc: '维护付费用户情感关系，制造直播效果' },
  { value: 'emotional', label: '情感倾诉', desc: '倾听情感困惑，引发直播间观众共鸣' },
];

const AGE_RANGES = ['18-25', '25-35', '35-45', '45+'];

interface Props {
  onGenerate: (params: GenerateParams) => void;
  loading: boolean;
  preselectedPersonaId?: string;
  anchorFollowerCount?: number;
}

export default function ConfigPanel({ onGenerate, loading, preselectedPersonaId, anchorFollowerCount }: Props) {
  const [toneId, setToneId] = useState('');
  const [personaId, setPersonaId] = useState(preselectedPersonaId || '');
  const [guestName, setGuestName] = useState('');
  const [ageRange, setAgeRange] = useState('');
  const [occupation, setOccupation] = useState('');
  const [personality, setPersonality] = useState('');
  const [coreIssue, setCoreIssue] = useState('');
  const [emotionCurve, setEmotionCurve] = useState('default');
  const [strategyMix, setStrategyMix] = useState('conservative');
  const [hotTopic, setHotTopic] = useState('');
  const [multiVersion, setMultiVersion] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [sceneType, setSceneType] = useState('entertainment');
  const [enableCallerEnhancement, setEnableCallerEnhancement] = useState(true);

  const { data: tonesData } = useQuery({ queryKey: ['roomTones'], queryFn: listRoomTones });
  const { data: personasData } = useQuery({ queryKey: ['personas'], queryFn: () => listPersonas(0, 50) });

  const tones = tonesData?.items || [];
  const personas = personasData?.items || [];

  const selectedTone = tones.find((t) => t.id === toneId);
  const selectedPersona = personas.find((p) => p.id === personaId);

  const canGenerate = toneId && personaId && coreIssue.trim() && !loading;

  const handleGenerate = () => {
    onGenerate({
      tone_id: toneId,
      persona_id: personaId,
      guest_config: {
        name: guestName || undefined,
        age_range: ageRange || undefined,
        occupation: occupation || undefined,
        personality: personality || undefined,
        core_issue: coreIssue,
      },
      emotion_curve: emotionCurve,
      strategy_mix: strategyMix,
      hot_topic: hotTopic || undefined,
      multi_version: multiVersion || undefined,
      scene_type: sceneType,
      enable_caller_enhancement: enableCallerEnhancement && (anchorFollowerCount ?? 0) >= 1000000,
    });
  };

  return (
    <div className="w-[320px] shrink-0 border-r border-border-default bg-bg-sidebar overflow-y-auto p-4 space-y-5">
      {/* Tone */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-text-secondary">直播间调性</label>
        <select
          value={toneId}
          onChange={(e) => setToneId(e.target.value)}
          className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand transition-colors"
        >
          <option value="">选择调性...</option>
          {tones.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        {selectedTone && <p className="text-xs text-text-muted">{selectedTone.description}</p>}
      </div>

      {/* Persona */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-text-secondary">网红人设</label>
        <select
          value={personaId}
          onChange={(e) => setPersonaId(e.target.value)}
          className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand transition-colors"
        >
          <option value="">选择人设...</option>
          {personas.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        {selectedPersona && (
          <p className="text-xs text-text-muted truncate">{selectedPersona.global_style.slice(0, 80)}</p>
        )}
      </div>

      <div className="h-px bg-border-default" />

      {/* Guest */}
      <div className="space-y-3">
        <h3 className="text-xs font-medium text-text-secondary">连线人配置</h3>
        <input
          value={guestName}
          onChange={(e) => setGuestName(e.target.value)}
          placeholder="名称（可选）"
          className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
        />
        <div className="grid grid-cols-2 gap-2">
          <select
            value={ageRange}
            onChange={(e) => setAgeRange(e.target.value)}
            className="bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand"
          >
            <option value="">年龄段</option>
            {AGE_RANGES.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <input
            value={occupation}
            onChange={(e) => setOccupation(e.target.value)}
            placeholder="职业"
            className="bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
          />
        </div>
        <textarea
          value={personality}
          onChange={(e) => setPersonality(e.target.value)}
          placeholder="性格描述"
          rows={2}
          className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand resize-none"
        />
        <div className="space-y-1">
          <label className="text-xs text-text-secondary">
            核心问题/连线诉求 <span className="text-error">*</span>
          </label>
          <textarea
            value={coreIssue}
            onChange={(e) => setCoreIssue(e.target.value)}
            placeholder="必填：连线人的核心问题或诉求"
            rows={3}
            className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand resize-none"
          />
        </div>
      </div>

      {/* Advanced */}
      <div>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors w-full"
        >
          {showAdvanced ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          高级选项
        </button>
        {showAdvanced && (
          <div className="mt-3 space-y-3">
            {/* Scene Type */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-text-secondary">连线场景</label>
              <div className="grid grid-cols-3 gap-1">
                {SCENE_TYPES.map((s) => (
                  <button
                    key={s.value}
                    onClick={() => setSceneType(s.value)}
                    className={`px-1.5 py-1.5 rounded-md text-xs border transition-colors text-center ${
                      sceneType === s.value
                        ? 'bg-brand text-white border-brand'
                        : 'bg-bg-card text-text-secondary border-border-default hover:border-brand'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-text-muted">
                {SCENE_TYPES.find((s) => s.value === sceneType)?.desc}
              </p>
            </div>
            <select
              value={emotionCurve}
              onChange={(e) => setEmotionCurve(e.target.value)}
              className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand"
            >
              {EMOTION_CURVES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
            <select
              value={strategyMix}
              onChange={(e) => setStrategyMix(e.target.value)}
              className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary outline-none focus:border-brand"
            >
              <option value="conservative">保守模式</option>
              <option value="mixed">融合模式</option>
              <option value="experimental">实验模式</option>
            </select>
            <input
              value={hotTopic}
              onChange={(e) => setHotTopic(e.target.value)}
              placeholder="绑定热点话题（可选）"
              className="w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
            />
            {/* Caller Enhancement */}
            {(anchorFollowerCount ?? 0) >= 1000000 && (
              <div className="flex items-start gap-2 p-2 bg-brand/5 border border-brand/20 rounded-md">
                <input
                  type="checkbox"
                  id="callerEnhance"
                  checked={enableCallerEnhancement}
                  onChange={(e) => setEnableCallerEnhancement(e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded border-border-default text-brand focus:ring-brand"
                />
                <label htmlFor="callerEnhance" className="text-xs text-text-primary cursor-pointer leading-tight">
                  连线者节奏增强
                  <span className="block text-[10px] text-text-muted mt-0.5">注入大V叙事逻辑（去标签化），提升连线者话术质量</span>
                </label>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Multi-version toggle */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="multiVersion"
          checked={multiVersion}
          onChange={(e) => setMultiVersion(e.target.checked)}
          className="w-4 h-4 rounded border-border-default text-brand focus:ring-brand"
        />
        <label htmlFor="multiVersion" className="text-sm text-text-primary cursor-pointer">
          生成多版本
        </label>
      </div>
      {multiVersion && (
        <p className="text-xs text-text-muted -mt-3">生成 3 种不同风格版本（反转型/共鸣型/搞笑型），预计耗时 30-60 秒</p>
      )}

      {/* Generate */}
      <button
        disabled={!canGenerate}
        onClick={handleGenerate}
        className={`w-full h-12 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-all duration-150
          ${canGenerate
            ? 'bg-brand text-white hover:bg-brand-hover active:bg-brand-active cursor-pointer'
            : 'bg-bg-hover text-text-muted cursor-not-allowed'}`}
      >
        {loading ? (
          <>
            <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-20" />
              <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
            生成中...
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4" />
            生成脚本
          </>
        )}
      </button>
    </div>
  );
}
