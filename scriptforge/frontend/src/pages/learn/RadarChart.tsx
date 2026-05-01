interface Props {
  data: Record<string, string | number>;
  size?: number;
}

const LABELS: Record<string, string> = {
  aggressiveness: '攻击性',
  humor: '幽默感',
  empathy: '共情力',
  rhythm: '节奏感',
  metaphor_usage: '隐喻',
  catchphrase_density: '口癖密度',
};

const AXES = Object.keys(LABELS);

export default function RadarChart({ data, size = 260 }: Props) {
  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 40;
  const n = AXES.length;
  const angleStep = (2 * Math.PI) / n;

  const getPoint = (i: number, val: number) => {
    const angle = -Math.PI / 2 + i * angleStep;
    return {
      x: cx + val * Math.cos(angle),
      y: cy + val * Math.sin(angle),
    };
  };

  // Grid rings
  const rings = [0.25, 0.5, 0.75, 1];

  // Data polygon
  const values = AXES.map((key) => {
    const v = data[key];
    const num = typeof v === 'number' ? v : parseFloat(String(v)) || 0;
    return Math.min(Math.max(num / 10, 0), 1); // assume 0-10 scale
  });

  const dataPoints = AXES.map((_, i) => getPoint(i, values[i] * r));
  const dataPath = dataPoints.map((p) => `${p.x},${p.y}`).join(' ');

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="mx-auto">
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

      {/* Data polygon */}
      <polygon
        points={dataPath}
        fill="rgba(99, 102, 241, 0.2)"
        stroke="#6366F1"
        strokeWidth={2}
      />

      {/* Data dots */}
      {dataPoints.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={3} fill="#6366F1" />
      ))}

      {/* Labels */}
      {AXES.map((key, i) => {
        const p = getPoint(i, r + 22);
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
  );
}
