import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { Lock, CheckCircle, Video } from 'lucide-react';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Modal from '../../components/ui/Modal';
import { toast } from '../../components/ui/Toast';
import type { MaterialItem } from '../LearnPage';

const EMOTION_OPTIONS = [
  { value: '', label: '未选择' },
  { value: '搞笑', label: '搞笑' },
  { value: '感动', label: '感动' },
  { value: '愤怒', label: '愤怒' },
  { value: '震惊', label: '震惊' },
  { value: '反转', label: '反转' },
  { value: '共鸣', label: '共鸣' },
  { value: '其他', label: '其他' },
];

interface LineData {
  timestamp: string;
  seconds: number;
  text: string;
  role: string;
  emotion: string;
  materialId: string;
}

interface Props {
  materials: MaterialItem[];
  onLock: (verifiedText: string) => void;
  locked: boolean;
  anchorProfile?: import('../../types').AnchorProfile | null;
}

const ROLE_COLORS: Record<string, string> = {
  '主播': 'text-brand font-semibold',
  '连麦人A': 'text-yellow-400 font-semibold',
  '连麦人B': 'text-green-400 font-semibold',
  '连麦人C': 'text-purple-400 font-semibold',
};

export default function VerificationPanel({ materials, onLock, locked, anchorProfile }: Props) {
  const [roles, setRoles] = useState<string[]>(['主播', '连麦人A']);
  const [activeRole, setActiveRole] = useState('主播');
  const [videoModal, setVideoModal] = useState<{ open: boolean; seconds: number; name: string; src?: string }>({ open: false, seconds: 0, name: '' });

  // Parse all materials into lines with timestamps
  const lines = useMemo<LineData[]>(() => {
    const result: LineData[] = [];
    for (const m of materials) {
      const text = m.editedText || m.rawText;
      if (!text) continue;

      // If we have segments, use them for precise timestamps
      if (m.segments && m.segments.length > 0) {
        for (const seg of m.segments) {
          if (!seg.text.trim()) continue;
          const mins = Math.floor(seg.start / 60);
          const secs = Math.floor(seg.start % 60);
          result.push({
            timestamp: `[${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}]`,
            seconds: seg.start,
            text: seg.text.trim(),
            role: '',
            emotion: '',
            materialId: m.id,
          });
        }
      } else {
        // No segments — split by lines, assign sequential timestamps
        const textLines = text.split('\n').filter((l) => l.trim());
        textLines.forEach((line, i) => {
          const mins = Math.floor(i * 10 / 60);
          const secs = (i * 10) % 60;
          result.push({
            timestamp: `[${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}]`,
            seconds: i * 10,
            text: line.trim(),
            role: '',
            emotion: '',
            materialId: m.id,
          });
        });
      }
    }
    return result;
  }, [materials]);

  const [lineData, setLineData] = useState<LineData[]>(lines);

  // Sync when materials change, preserving existing role/emotion annotations
  useEffect(() => {
    if (locked) return;
    setLineData((prev) => {
      if (prev.length === lines.length) {
        return lines.map((l, i) => ({ ...l, role: prev[i]?.role || '', emotion: prev[i]?.emotion || '' }));
      }
      return lines;
    });
  }, [materials, locked, lines]);

  // ---- Role annotation ----
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleAnnotate = useCallback(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    if (start === end) {
      toast('warning', '请先在文本中选中要标注的句子');
      return;
    }

    const fullText = ta.value;
    // Find which line(s) are selected
    const beforeLines = fullText.substring(0, start).split('\n');
    const startLineIdx = beforeLines.length - 1;

    setLineData((prev) => {
      const next = [...prev];
      if (next[startLineIdx]) {
        next[startLineIdx] = { ...next[startLineIdx], role: activeRole };
      }
      return next;
    });
    toast('success', `已标注为「${activeRole}」`);
  }, [activeRole]);

  const addRole = () => {
    const nextLabel = `连麦人${String.fromCharCode(65 + roles.length - 1)}`;
    if (roles.length >= 6) {
      toast('warning', '最多支持 6 个角色');
      return;
    }
    setRoles((prev) => [...prev, nextLabel]);
    toast('success', `已添加 ${nextLabel}`);
  };

  // ---- Emotion per line ----
  const setEmotion = (idx: number, emotion: string) => {
    setLineData((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], emotion };
      return next;
    });
  };

  // ---- Timestamp click → video ----
  const handleTimestampClick = (line: LineData) => {
    const mat = materials.find((m) => m.id === line.materialId);
    if (!mat) return;
    const src = mat.audioPath || mat.sourceUrl;
    setVideoModal({ open: true, seconds: line.seconds, name: mat.name, src });
  };

  // ---- Build merged text for display ----
  const mergedText = lineData.map((l) => {
    const rolePrefix = l.role ? `${l.role}: ` : '';
    return `${l.timestamp} ${rolePrefix}${l.text}`;
  }).join('\n');

  // ---- Lock ----
  const handleLock = () => {
    if (!lineData.some((l) => l.role)) {
      toast('warning', '请至少标注一行角色');
      return;
    }
    const finalText = mergedText;
    onLock(finalText);
    toast('success', '素材已锁定');
  };

  // ---- Merged text for editing (synced with lineData) ----
  const [editText, setEditText] = useState('');
  const handleEditMerge = (text: string) => {
    setEditText(text);
  };

  return (
    <div className="space-y-4">
      {/* Anchor banner */}
      {anchorProfile && (
        <div className="p-3 bg-bg-card border border-border-default rounded-lg flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-brand/20 flex items-center justify-center text-brand font-bold text-xs shrink-0 overflow-hidden">
            {anchorProfile.avatar_url ? (
              <img src={anchorProfile.avatar_url} alt="" className="w-full h-full object-cover" />
            ) : (
              anchorProfile.anchor_name.slice(0, 1)
            )}
          </div>
          <div className="flex-1 min-w-0">
            <span className="text-sm font-semibold text-text-primary">{anchorProfile.anchor_name}</span>
            <span className="text-xs text-text-muted ml-2">
              {anchorProfile.follower_count >= 10000
                ? `${(anchorProfile.follower_count / 10000).toFixed(1)}万`
                : anchorProfile.follower_count} 粉丝
            </span>
            {anchorProfile.bio && (
              <p className="text-xs text-text-muted mt-0.5 truncate">{anchorProfile.bio}</p>
            )}
          </div>
        </div>
      )}

      {/* Merged text preview */}
      <div>
        <label className="text-sm font-medium text-text-secondary block mb-2">合并全文预览</label>
        <textarea
          ref={textareaRef}
          value={locked ? mergedText : (editText || mergedText)}
          onChange={(e) => { if (!locked) handleEditMerge(e.target.value); }}
          disabled={locked}
          rows={12}
          className="w-full bg-bg-card border border-border-default rounded-lg px-4 py-3 text-sm text-text-primary font-mono leading-relaxed outline-none focus:border-brand resize-y disabled:opacity-60 disabled:cursor-not-allowed"
        />
      </div>

      {/* Role annotation toolbar */}
      {!locked && (
        <div className="bg-bg-card border border-border-default rounded-lg p-4 space-y-3">
          <h4 className="text-sm font-medium text-text-secondary">角色标注工具</h4>
          <p className="text-xs text-text-muted">在上方文本中选中一句话，然后点击下方按钮标注角色</p>
          <div className="flex flex-wrap gap-2">
            {roles.map((role) => (
              <button
                key={role}
                onClick={() => setActiveRole(role)}
                className={`px-3 py-1.5 rounded-md text-sm border transition-colors ${
                  activeRole === role
                    ? 'bg-brand text-white border-brand'
                    : 'bg-bg-primary text-text-secondary border-border-default hover:border-brand'
                }`}
              >
                🎭 {role}
              </button>
            ))}
            <button
              onClick={addRole}
              className="px-3 py-1.5 rounded-md text-sm border border-dashed border-border-default text-text-muted hover:border-brand hover:text-brand transition-colors"
            >
              + 添加角色
            </button>
          </div>
          <Button size="sm" onClick={handleAnnotate} disabled={locked}>
            标注选中行为「{activeRole}」
          </Button>
        </div>
      )}

      {/* Per-line view with timestamps, roles, emotions */}
      {lineData.length > 0 && (
        <div className="space-y-1">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-text-secondary">逐行校验</h4>
            <span className="text-xs text-text-muted">{lineData.length} 行</span>
          </div>
          <div className="bg-bg-card border border-border-default rounded-lg divide-y divide-border-default max-h-[400px] overflow-y-auto">
            {lineData.map((line, i) => (
              <div key={i} className="flex items-center gap-2 px-3 py-2 hover:bg-bg-hover transition-colors">
                {/* Timestamp — clickable */}
                <button
                  onClick={() => handleTimestampClick(line)}
                  className="text-xs text-brand hover:underline shrink-0 font-mono"
                >
                  {line.timestamp}
                </button>

                {/* Role label */}
                {line.role ? (
                  <span className={`text-xs shrink-0 ${ROLE_COLORS[line.role] || 'text-text-muted'}`}>
                    {line.role}:
                  </span>
                ) : (
                  <span className="w-2 shrink-0" />
                )}

                {/* Text */}
                <span className="text-sm text-text-primary flex-1 min-w-0 truncate">
                  {line.text}
                </span>

                {/* Emotion selector */}
                <select
                  value={line.emotion}
                  onChange={(e) => setEmotion(i, e.target.value)}
                  disabled={locked}
                  className="bg-bg-primary border border-border-default rounded px-1.5 py-0.5 text-[10px] text-text-secondary outline-none shrink-0 disabled:opacity-60"
                >
                  {EMOTION_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lock button */}
      {!locked ? (
        <Button size="lg" onClick={handleLock} className="w-full" disabled={lineData.length === 0}>
          <CheckCircle className="w-4 h-4" />
          校验完毕，锁定素材
        </Button>
      ) : (
        <div className="flex items-center justify-center gap-2 py-3 text-sm text-text-muted">
          <Lock className="w-4 h-4" />
          素材已锁定，可在下方开始处理
        </div>
      )}

      {/* Video player modal */}
      <Modal
        open={videoModal.open}
        onClose={() => setVideoModal((v) => ({ ...v, open: false }))}
        title={videoModal.name}
        className="max-w-3xl"
      >
        {videoModal.src ? (
          <video
            key={`${videoModal.src}-${videoModal.seconds}`}
            controls
            autoPlay
            className="w-full rounded-lg"
            src={videoModal.src.startsWith('http') ? videoModal.src : `/api/files/${videoModal.src}`}
            onLoadedMetadata={(e) => {
              (e.target as HTMLVideoElement).currentTime = videoModal.seconds;
            }}
          >
            您的浏览器不支持视频播放
          </video>
        ) : (
          <p className="text-sm text-text-muted py-8 text-center">暂无可播放的视频源</p>
        )}
      </Modal>
    </div>
  );
}
