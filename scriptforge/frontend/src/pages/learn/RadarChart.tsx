import { useState } from 'react';

interface Props {
  data: Record<string, string | number>;
  compareData?: Record<string, string | number> | null;
  label?: string;
  compareLabel?: string;
  size?: number;
}

const LABELS: Record<string, string> = {
  aggressiveness: '犀利度',
  humor: '幽默感',
  empathy: '共情力',
  rhythm: '节奏感',
  metaphor_usage: '比喻能力',
  catchphrase_density: '口头禅频率',
};

const DESCRIPTIONS: Record<string, string> = {
  aggressiveness: '表达中的锐利程度和对抗性，高值表示更直接犀利',
  humor: '使用幽默元素和梗的频率，高值表示更善用幽默',
  empathy: '对他人情感的回应和共鸣能力，高值表示更善共情',
  rhythm: '对话节奏的把控和变化，高值表示节奏感更强',
  metaphor_usage: '使用比喻和修辞的丰富度，高值表示更善用修辞',
  catchphrase_density: '口头禅和标志性表达的使用频率',
};

const AXES = Object.keys(LABELS);
const BRAND_COLOR = '#6366F1';
const COMPARE_COLOR = '#F59E0B';

export default function RadarChart({
  data, compareData, label, compareLabel, size = 260,
}: Props) {
  const [tooltip, setTooltip] = useState<{
    idx: number; x: number; y: number; val: number;
    compareVal?: number;
  } | null>(null);

  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 44;
  const n = AXES.length;
  const angleStep = (2 * Math.PI) / n;

  const getPoint = (i: number, val: number) => {
    const angle = -Math.PI / 2 + i * angleStep;
    return { x: cx + val * Math.cos(angle), y: cy + val * Math.sin(angle) };
  };

  const rings = [0.25, 0.5, 0.75, 1];

  const values = AXES.map((key) => {
    // Backend uses 'rhythm_score' to avoid clashing with the text 'rhythm' field
    const dataKey = key === 'rhythm' ? 'rhythm_score' : key;
    const v = data[dataKey];
    const num = typeof v === 'number' ? v : parseFloat(String(v)) || 0;
    return Math.min(Math.max(num / 10, 0), 1);
  });

  const compareValues = compareData
    ? AXES.map((key) => {
        const dataKey = key === 'rhythm' ? 'rhythm_score' : key;
        const v = compareData[dataKey];
        const num = typeof v === 'number' ? v : parseFloat(String(v)) || 0;
        return Math.min(Math.max(num / 10, 0), 1);
      })
    : null;

  const dataPoints = AXES.map((_, i) => getPoint(i, values[i] * r));
  const dataPath = dataPoints.map((p) => `${p.x},${p.y}`).join(' ');

  const comparePoints = compareValues
    ? AXES.map((_, i) => getPoint(i, compareValues[i] * r))
    : null;
  const comparePath = comparePoints
    ? comparePoints.map((p) => `${p.x},${p.y}`).join(' ')
    : null;

  const handleHover = (idx: number, x: number, y: number, isPrimary: boolean) => {
    const val = isPrimary ? values[idx] : compareValues?.[idx] ?? 0;
    setTooltip({ idx, x, y, val: val * 10, compareVal: isPrimary ? undefined : values[idx] * 10 });
  };

  return (
    <div className="relative">
      {/* Legend */}
      {(compareData && compareLabel) && (
        <div className="flex items-center justify-center gap-4 mb-2">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 rounded-sm" style={{ background: BRAND_COLOR }} />
            <span className="text-xs text-text-secondary">{label || '当前人设'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 rounded-sm" style={{ background: COMPARE_COLOR }} />
            <span className="text-xs text-text-secondary">{compareLabel}</span>
          </div>
        </div>
      )}

      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="mx-auto"
        onMouseLeave={() => setTooltip(null)}
      >
        {/* Grid rings */}
        {rings.map((scale) => (
          <polygon
            key={scale}
            points={AXES.map((_, i) => {
              const p = getPoint(i, scale * r);
              return `${p.x},${p.y}`;
            }).join(' ')}
            fill="none"
            stroke="#2A2A2A"
            strokeWidth={1}
          />
        ))}

        {/* Axis lines */}
        {AXES.map((_, i) => {
          const p = getPoint(i, r);
          return (
            <line key={i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="#2A2A2A" strokeWidth={1} />
          );
        })}

        {/* Compare polygon (behind primary) */}
        {comparePath && (
          <polygon
            points={comparePath}
            fill="rgba(245, 158, 11, 0.15)"
            stroke={COMPARE_COLOR}
            strokeWidth={2}
            strokeDasharray="4 2"
          />
        )}

        {/* Primary data polygon */}
        <polygon
          points={dataPath}
          fill="rgba(99, 102, 241, 0.2)"
          stroke={BRAND_COLOR}
          strokeWidth={2}
        />

        {/* Compare dots */}
        {comparePoints?.map((p, i) => (
          <circle
            key={`c${i}`}
            cx={p.x}
            cy={p.y}
            r={4}
            fill={COMPARE_COLOR}
            className="cursor-pointer"
            onMouseEnter={() => handleHover(i, p.x, p.y, false)}
            onMouseLeave={() => setTooltip(null)}
          />
        ))}

        {/* Primary dots */}
        {dataPoints.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={4}
            fill={BRAND_COLOR}
            className="cursor-pointer"
            onMouseEnter={() => handleHover(i, p.x, p.y, true)}
            onMouseLeave={() => setTooltip(null)}
          />
        ))}

        {/* Labels */}
        {AXES.map((key, i) => {
          const p = getPoint(i, r + 24);
          return (
            <text
              key={key}
              x={p.x}
              y={p.y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="text-[10px] fill-[#888888]"
            >
              {LABELS[key]}
            </text>
          );
        })}
      </svg>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute z-50 bg-bg-card border border-border-default rounded-lg px-3 py-2 shadow-lg pointer-events-none"
          style={{
            left: tooltip.x,
            top: tooltip.y - 12,
            transform: 'translate(-50%, -100%)',
          }}
        >
          <p className="text-sm font-medium text-text-primary">
            {LABELS[AXES[tooltip.idx]]}
          </p>
          <p className="text-xs text-brand mt-0.5">
            {tooltip.val.toFixed(1)} / 10
          </p>
          {tooltip.compareVal !== undefined && (
            <p className="text-xs mt-0.5" style={{ color: COMPARE_COLOR }}>
              对比: {tooltip.compareVal.toFixed(1)} / 10
            </p>
          )}
          <p className="text-[10px] text-text-muted mt-1 max-w-[160px] leading-snug">
            {DESCRIPTIONS[AXES[tooltip.idx]]}
          </p>
        </div>
      )}
    </div>
  );
}
