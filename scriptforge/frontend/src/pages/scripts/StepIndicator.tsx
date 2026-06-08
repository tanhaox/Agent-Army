import { Check } from 'lucide-react';

const STEPS = [
  { key: 'setup', label: '剧本设定', desc: '选择直播间氛围和剧本类型' },
  { key: 'cast', label: '角色选角', desc: '确定参与剧本的所有角色' },
  { key: 'outline', label: '剧情大纲', desc: '为编导模式编写每麦剧情任务' },
  { key: 'generate', label: '生成与精调', desc: '一键生成并精细化调整' },
];

interface Props {
  current: number;
  maxStep: number;
  directorMode: boolean;
  onChange: (step: number) => void;
}

export default function StepIndicator({ current, maxStep, directorMode, onChange }: Props) {
  const visibleSteps = directorMode ? STEPS : STEPS.filter((_, i) => i !== 2);
  const adjustedCurrent = directorMode ? current : (current >= 3 ? current - 1 : current);

  return (
    <div className="px-6 pt-4 pb-2">
      {/* Step nodes */}
      <div className="flex items-center justify-center gap-0">
        {visibleSteps.map((step, i) => {
          const isCompleted = i < adjustedCurrent;
          const isCurrent = i === adjustedCurrent;
          const isFuture = i > adjustedCurrent;
          const canClick = i <= maxStep && i !== adjustedCurrent;

          return (
            <div key={step.key} className="flex items-center">
              {/* Connector line */}
              {i > 0 && (
                <div className={`w-12 h-0.5 transition-colors duration-300 ${
                  i <= adjustedCurrent ? 'bg-brand' : 'bg-border-default'
                }`} />
              )}

              {/* Node */}
              <button
                disabled={!canClick}
                onClick={() => {
                  const realStep = directorMode ? i : (i >= 2 ? i + 1 : i);
                  onChange(realStep);
                }}
                className={`flex flex-col items-center gap-1.5 transition-all duration-200 ${
                  canClick ? 'cursor-pointer hover:scale-105' : 'cursor-default'
                }`}
              >
                <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300 ${
                  isCompleted ? 'bg-brand text-white' :
                  isCurrent ? 'bg-brand text-white ring-4 ring-brand/20' :
                  'border-2 border-border-default text-text-muted'
                }`}>
                  {isCompleted ? <Check className="w-4 h-4" /> : i + 1}
                </div>
                <span className={`text-xs whitespace-nowrap ${
                  isFuture ? 'text-text-muted' : 'text-text-primary font-medium'
                }`}>
                  {step.label}
                </span>
              </button>
            </div>
          );
        })}
      </div>

      {/* Description */}
      <p className="text-center text-sm text-text-secondary mt-2">
        {visibleSteps[adjustedCurrent]?.desc}
      </p>

      {/* Progress bar */}
      <div className="mt-2 h-1 bg-bg-hover rounded-full overflow-hidden">
        <div
          className="h-full bg-brand rounded-full transition-all duration-500"
          style={{ width: `${((adjustedCurrent + 1) / visibleSteps.length) * 100}%` }}
        />
      </div>
    </div>
  );
}
