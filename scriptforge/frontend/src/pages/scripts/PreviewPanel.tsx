import { Users, ListOrdered, Settings2 } from 'lucide-react';
import type { DirectorRole, DirectorAct } from '../../services/scripts';

interface Props {
  step: number;
  directorMode: boolean;
  // Step 1
  toneName?: string;
  customTone?: string;
  sceneType?: string;
  directorModeValue?: boolean;
  topic?: string;
  // Step 2
  roles: DirectorRole[];
  // Step 3
  acts: DirectorAct[];
  // Step 4
  generated: boolean;
}

const SCENE_LABELS: Record<string, string> = {
  entertainment_comedy: '搞笑整蛊', entertainment_chat: '聊天陪伴', entertainment_game: '游戏互动', entertainment_gossip: '热点八卦',
  knowledge_science: '知识科普', knowledge_debate: '观点辩论', knowledge_career: '职业揭秘',
  emotion_love: '恋爱婚姻', emotion_family: '亲情家庭', emotion_friendship: '友情社交',
  talent_performance: '才艺表演', talent_encouragement: '暖心鼓励',
  // backward compat
  entertainment: '搞笑整蛊', talent: '才艺表演', emotional: '恋爱婚姻',
};

export default function PreviewPanel({ step, directorMode, toneName, customTone, sceneType, directorModeValue, topic, roles, acts, generated }: Props) {
  const visibleStep = directorMode ? step : (step >= 3 ? step - 1 : step);

  return (
    <div className="flex-1 p-6 space-y-6 overflow-y-auto animate-[fadeIn_300ms_ease-in-out]">
      {/* Step 1 preview */}
      {visibleStep === 0 && (
        <div className="max-w-md mx-auto">
          <h3 className="text-sm font-medium text-text-secondary flex items-center gap-2 mb-4"><Settings2 className="w-4 h-4" /> 剧本设定摘要</h3>
          <div className="space-y-3 p-4 bg-bg-card rounded-lg border border-border-default">
            <Row label="调性" value={customTone || toneName || '未选择'} />
            <Row label="场景" value={SCENE_LABELS[sceneType || ''] || '未选择'} />
            <Row label="模式" value={directorModeValue ? '编导模式' : '简单模式'} />
            <Row label="话题" value={topic || '未填写'} />
          </div>
          {!toneName && !customTone && <p className="text-xs text-text-muted text-center mt-4">在左侧完成设定后将在此显示摘要</p>}
        </div>
      )}

      {/* Step 2 preview */}
      {visibleStep === 1 && (
        <div className="max-w-lg mx-auto">
          <h3 className="text-sm font-medium text-text-secondary flex items-center gap-2 mb-4"><Users className="w-4 h-4" /> 角色阵容</h3>
          {roles.length === 0 ? (
            <p className="text-xs text-text-muted text-center py-8">还没有添加角色</p>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {roles.map((r, i) => {
                const borderColor = r.role_type === 'anchor' ? 'border-brand/40' : r.role_type === 'caller' ? 'border-green-500/40' : 'border-gray-400/40';
                const bgColor = r.role_type === 'anchor' ? 'bg-brand/5' : r.role_type === 'caller' ? 'bg-green-500/5' : 'bg-gray-500/5';
                const typeLabel = r.role_type === 'anchor' ? '主播' : r.role_type === 'caller' ? '连线人' : '群演';
                return (
                  <div key={i} className={`p-3 rounded-lg border ${borderColor} ${bgColor}`}>
                    <div className="flex items-center gap-2">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                        r.role_type === 'anchor' ? 'bg-brand/20 text-brand' : r.role_type === 'caller' ? 'bg-green-500/20 text-green-600' : 'bg-gray-500/20 text-gray-500'
                      }`}>{r.name[0]}</div>
                      <div>
                        <p className="text-sm font-medium text-text-primary">{r.name}</p>
                        <p className="text-[10px] text-text-muted">{typeLabel}{r.position ? ` · ${r.position}` : ''}</p>
                      </div>
                    </div>
                    {r.function && <p className="text-[10px] text-text-muted mt-1 truncate">{r.function}</p>}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Step 3 preview */}
      {visibleStep === 2 && directorMode && (
        <div className="max-w-md mx-auto">
          <h3 className="text-sm font-medium text-text-secondary flex items-center gap-2 mb-4"><ListOrdered className="w-4 h-4" /> 剧情时间线</h3>
          {acts.length === 0 ? (
            <p className="text-xs text-text-muted text-center py-8">还没有添加麦序</p>
          ) : (
            <div className="relative pl-6">
              {acts.map((a, i) => (
                <div key={i} className="relative pb-4 last:pb-0">
                  {i < acts.length - 1 && <div className="absolute left-[-16px] top-4 bottom-0 w-0.5 bg-border-default" />}
                  <div className="absolute left-[-20px] top-1 w-2.5 h-2.5 rounded-full bg-brand ring-2 ring-brand/20" />
                  <div className="p-3 bg-bg-card rounded-lg border border-border-default">
                    <p className="text-sm font-medium text-text-primary">{a.title}</p>
                    <p className="text-[10px] text-text-muted mt-0.5">{a.task.slice(0, 80)}{a.task.length > 80 ? '...' : ''}</p>
                    <div className="flex gap-1 mt-1.5">
                      {a.participants.map((p, j) => (
                        <span key={j} className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-brand/10 text-brand">{p}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step 4 preview */}
      {visibleStep === (directorMode ? 3 : 2) && (
        <div className="max-w-md mx-auto text-center">
          {!generated ? (
            <div className="py-12 space-y-3">
              <div className="text-4xl">🎬</div>
              <p className="text-sm text-text-secondary">点击左侧「生成脚本」按钮开始创作</p>
              <p className="text-xs text-text-muted">AI 将根据你的设定生成专业直播脚本</p>
            </div>
          ) : (
            <p className="text-sm text-text-secondary">脚本已生成，请查看下方展示区</p>
          )}
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-text-muted">{label}</span>
      <span className="text-sm text-text-primary font-medium">{value}</span>
    </div>
  );
}
