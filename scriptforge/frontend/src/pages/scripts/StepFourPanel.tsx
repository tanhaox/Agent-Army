import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

const EMOTION_CURVES = [
  { value: 'default', label: '自然起伏' },
  { value: 'rollercoaster', label: '过山车式' },
  { value: 'warm', label: '温水煮蛙' },
  { value: 'confrontation', label: '对抗式' },
  { value: 'mystery', label: '悬疑式' },
];

interface Props {
  emotionCurve: string;
  setEmotionCurve: (v: string) => void;
  requiredLines: string;
  setRequiredLines: (v: string) => void;
  multiVersion: boolean;
  setMultiVersion: (v: boolean) => void;
  enableCallerEnhancement: boolean;
  setEnableCallerEnhancement: (v: boolean) => void;
  anchorFollowerCount?: number;
  loading: boolean;
  canGenerate: boolean;
  onGenerate: () => void;
}

export default function StepFourPanel({
  emotionCurve, setEmotionCurve,
  requiredLines, setRequiredLines,
  multiVersion, setMultiVersion,
  enableCallerEnhancement, setEnableCallerEnhancement,
  anchorFollowerCount,
  loading, canGenerate, onGenerate,
}: Props) {
  const [showAdvanced, setShowAdvanced] = useState(true);

  const inputCls = 'w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand';
  const selectCls = inputCls;
  const labelCls = 'text-xs font-medium text-text-secondary';

  return (
    <div className="space-y-5">
      {/* Advanced options */}
      <div>
        <button onClick={() => setShowAdvanced(!showAdvanced)} className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors w-full">
          {showAdvanced ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          高级选项
        </button>
        {showAdvanced && (
          <div className="mt-3 space-y-3">
            <div className="space-y-1">
              <label className={labelCls}>情绪曲线</label>
              <select value={emotionCurve} onChange={(e) => setEmotionCurve(e.target.value)} className={selectCls}>
                {EMOTION_CURVES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div className="space-y-1">
              <label className={labelCls}>指定爆点/梗句（可选）</label>
              <textarea value={requiredLines} onChange={(e) => setRequiredLines(e.target.value)} placeholder={"每行一个爆点，如：\n主播用做饭比喻人生\n连线者突然哭了然后反转"} rows={3} className={`${inputCls} resize-none`} />
              <p className="text-[10px] text-text-muted">每行一个爆点，系统将尽力让这些句子出现在脚本中</p>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="multiVersion" checked={multiVersion} onChange={(e) => setMultiVersion(e.target.checked)} className="w-4 h-4 rounded border-border-default text-brand focus:ring-brand" />
              <label htmlFor="multiVersion" className="text-sm text-text-primary cursor-pointer">生成多版本</label>
            </div>
            {multiVersion && <p className="text-xs text-text-muted -mt-2">生成 3 种不同风格版本（反转型/共鸣型/搞笑型），预计耗时 30-60 秒</p>}
            {(anchorFollowerCount ?? 0) >= 1000000 && (
              <div className="flex items-start gap-2 p-2 bg-brand/5 border border-brand/20 rounded-md">
                <input type="checkbox" id="callerEnhance" checked={enableCallerEnhancement} onChange={(e) => setEnableCallerEnhancement(e.target.checked)} className="w-4 h-4 mt-0.5 rounded border-border-default text-brand focus:ring-brand" />
                <label htmlFor="callerEnhance" className="text-xs text-text-primary cursor-pointer leading-tight">
                  连线者节奏增强
                  <span className="block text-[10px] text-text-muted mt-0.5">注入大V叙事逻辑（去标签化），提升连线者话术质量</span>
                </label>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Generate button */}
      <button
        disabled={!canGenerate}
        onClick={onGenerate}
        className={`w-full h-12 rounded-lg text-base font-medium flex items-center justify-center gap-2 transition-all duration-150 ${
          canGenerate
            ? 'bg-brand text-white hover:bg-brand-hover hover:shadow-lg hover:shadow-brand/25 cursor-pointer'
            : 'bg-bg-hover text-text-muted cursor-not-allowed'
        }`}
      >
        {loading ? (
          <><svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-20" /><path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" /></svg>正在生成中...</>
        ) : '🚀 生成脚本'}
      </button>
    </div>
  );
}
