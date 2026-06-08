import { useQuery } from '@tanstack/react-query';
import { listRoomTones } from '../../services/roomTone';
import type { StepOneData } from './ScriptsPage';

const SCENE_GROUPS = [
  {
    group: '娱乐互动',
    items: [
      { value: 'entertainment_comedy', label: '搞笑整蛊', icon: '😂' },
      { value: 'entertainment_chat', label: '聊天陪伴', icon: '☕' },
      { value: 'entertainment_game', label: '游戏互动', icon: '🎮' },
      { value: 'entertainment_gossip', label: '热点八卦', icon: '🍉' },
    ],
  },
  {
    group: '知识观点',
    items: [
      { value: 'knowledge_science', label: '知识科普', icon: '📚' },
      { value: 'knowledge_debate', label: '观点辩论', icon: '⚖️' },
      { value: 'knowledge_career', label: '职业揭秘', icon: '🔍' },
    ],
  },
  {
    group: '情感关系',
    items: [
      { value: 'emotion_love', label: '恋爱婚姻', icon: '💔' },
      { value: 'emotion_family', label: '亲情家庭', icon: '🏠' },
      { value: 'emotion_friendship', label: '友情社交', icon: '🤝' },
    ],
  },
  {
    group: '才艺展示',
    items: [
      { value: 'talent_performance', label: '才艺表演', icon: '🎤' },
      { value: 'talent_encouragement', label: '暖心鼓励', icon: '💪' },
    ],
  },
];

const SCENE_FLAT = SCENE_GROUPS.flatMap((g) => g.items);

interface Props {
  data: StepOneData;
  onChange: (d: StepOneData) => void;
}

export default function StepOneForm({ data, onChange }: Props) {
  const { data: tonesData } = useQuery({ queryKey: ['roomTones'], queryFn: listRoomTones });
  const tones = tonesData?.items || [];
  const selectedTone = tones.find((t) => t.id === data.toneId);

  const set = <K extends keyof StepOneData>(k: K, v: StepOneData[K]) => onChange({ ...data, [k]: v });

  const inputCls = 'w-full bg-bg-card border border-border-default rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand';
  const labelCls = 'text-xs font-medium text-text-secondary';

  return (
    <div className="space-y-5">
      {/* Tone */}
      <div className="space-y-2">
        <label className={labelCls}>直播间调性</label>
        <select value={data.toneId} onChange={(e) => { const v = e.target.value; onChange({ ...data, toneId: v, customTone: v === '__custom__' ? data.customTone : '' }); }} className={inputCls}>
          <option value="">选择调性...</option>
          {tones.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          <option value="__custom__">✏️ 自定义调性...</option>
        </select>
        {data.toneId === '__custom__' && (
          <textarea value={data.customTone} onChange={(e) => set('customTone', e.target.value)} placeholder="描述你想要的直播间氛围，如：家庭伦理剧情向，悬疑反转风格" rows={2} className={`${inputCls} resize-none text-xs`} />
        )}
        {selectedTone && <p className="text-xs text-text-muted">{selectedTone.description}</p>}
      </div>

      {/* Scene type */}
      <div className="space-y-2">
        <label className={labelCls}>连线场景</label>
        <div className="space-y-2.5">
          {SCENE_GROUPS.map((g) => (
            <div key={g.group}>
              <p className="text-[10px] text-text-muted mb-1.5">{g.group}</p>
              <div className="flex flex-wrap gap-1.5">
                {g.items.map((s) => (
                  <button
                    key={s.value}
                    onClick={() => set('sceneType', s.value)}
                    className={`px-2.5 py-1.5 rounded-md border text-xs transition-all duration-150 whitespace-nowrap ${
                      data.sceneType === s.value
                        ? 'border-brand bg-brand/10 text-brand'
                        : 'border-border-default bg-bg-card text-text-secondary hover:border-brand/40'
                    }`}
                  >
                    <span className="mr-1">{s.icon}</span>{s.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Script mode */}
      <div className="space-y-2">
        <label className={labelCls}>剧本类型</label>
        <div className="grid grid-cols-2 gap-2">
          <button onClick={() => set('directorMode', false)}
            className={`p-3 rounded-lg border text-left transition-all duration-150 ${
              !data.directorMode ? 'border-brand bg-brand/5' : 'border-border-default bg-bg-card hover:border-brand/40'
            }`}>
            <span className="text-lg">🎤</span>
            <p className={`text-sm font-medium mt-1 ${!data.directorMode ? 'text-text-primary' : 'text-text-secondary'}`}>简单模式</p>
            <p className="text-[10px] text-text-muted mt-0.5">一个话题，一段连线，自由发挥</p>
          </button>
          <button onClick={() => set('directorMode', true)}
            className={`p-3 rounded-lg border text-left transition-all duration-150 ${
              data.directorMode ? 'border-brand bg-brand/5' : 'border-border-default bg-bg-card hover:border-brand/40'
            }`}>
            <span className="text-lg">🎬</span>
            <p className={`text-sm font-medium mt-1 ${data.directorMode ? 'text-text-primary' : 'text-text-secondary'}`}>编导模式</p>
            <p className="text-[10px] text-text-muted mt-0.5">多角色、多麦序、结构化剧情</p>
          </button>
        </div>
        {data.directorMode && (
          <p className="text-[10px] text-brand">编导模式将解锁「角色选角」和「剧情大纲」步骤</p>
        )}
      </div>

      {/* Topic (required in simple mode) */}
      <div className="space-y-1">
        <label className={labelCls}>
          连线话题 {!data.directorMode && <span className="text-error">*</span>}
        </label>
        <input value={data.topic} onChange={(e) => set('topic', e.target.value)} placeholder="如：结婚彩礼该不该给、35岁程序员转行" className={inputCls} />
      </div>
    </div>
  );
}
