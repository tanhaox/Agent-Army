import { useState } from 'react';
import { FileText, Star, Copy, Edit3, Download, RotateCcw, Check, X } from 'lucide-react';
import type { Dialogue } from '../../types';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import { toast } from '../../components/ui/Toast';
import type { ScriptResult } from '../../services/scripts';

const EMOTION_EMOJI: Record<string, string> = {
  '感动': '😢', '愤怒': '😡', '搞笑': '😂', '惊讶': '😲',
  '平静': '😌', '激动': '🔥', '温馨': '❤️', '紧张': '😰',
  '悲伤': '😞', '兴奋': '🎉', '尴尬': '😅', '愤怒': '😤',
};

interface Props {
  result: ScriptResult;
  onSave: (content: any) => void;
  onRegenerate: (speaker: string) => void;
}

export default function ScriptDisplay({ result, onSave, onRegenerate }: Props) {
  const [editMode, setEditMode] = useState(false);
  const [activeVersion, setActiveVersion] = useState(result.recommended_version ?? 0);
  const [editedDialogues, setEditedDialogues] = useState<Dialogue[]>(
    result.versions ? (result.versions[0]?.dialogues || []) : result.dialogues
  );
  const [hoveredHighlight, setHoveredHighlight] = useState<number | null>(null);
  const [showCompliance, setShowCompliance] = useState(false);

  const isMultiVersion = result.multi_version && result.versions && result.versions.length > 0;
  const currentVersion = isMultiVersion ? result.versions[activeVersion] : null;
  const activeDialogues = editMode ? editedDialogues : (currentVersion?.dialogues || result.dialogues);
  const activeHighlights = currentVersion?.highlights || result.highlights;
  const activeCompliance = currentVersion?.compliance || result.compliance;
  const activeTitle = currentVersion?.overall_style_note
    ? `${result.versions?.[activeVersion]?.version_name || ''}版`
    : result.title || '';
  const activeWordCount = currentVersion?.word_count || result.word_count;

  const handleCopy = () => {
    const text = activeDialogues
      .map((d) => `[${d.speaker}] ${d.text}`)
      .join('\n\n');
    navigator.clipboard.writeText(text).then(() => toast('success', '已复制到剪贴板'));
  };

  const handleExport = () => {
    const title = isMultiVersion ? `${result.versions?.[activeVersion]?.version_name || ''}版` : (result.title || '脚本');
    const lines = [`# ${title}\n`];
    activeDialogues.forEach((d) => {
      lines.push(`[${d.speaker}] (${d.emotion})`);
      lines.push(d.text);
      lines.push('');
    });
    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    toast('success', '已导出为 TXT 文件');
  };

  const handleSaveEdit = () => {
    onSave({ ...result, dialogues: editedDialogues });
    setEditMode(false);
  };

  const handleCancelEdit = () => {
    setEditedDialogues(activeDialogues);
    setEditMode(false);
  };

  const switchVersion = (idx: number) => {
    setActiveVersion(idx);
    setEditedDialogues(result.versions?.[idx]?.dialogues || []);
    setEditMode(false);
  };

  const updateDialogue = (idx: number, text: string) => {
    setEditedDialogues((prev) => prev.map((d, i) => (i === idx ? { ...d, text } : d)));
  };

  const highlightMap = new Map(activeHighlights.map((h) => [h.turn, h]));

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Version tabs */}
      {isMultiVersion && (
        <div className="px-6 py-2 border-b border-border-default flex gap-2">
          {result.versions!.map((v, i) => (
            <button
              key={v.version_id}
              onClick={() => switchVersion(i)}
              className={`px-4 py-1.5 text-sm rounded-md transition-colors ${
                i === activeVersion
                  ? 'bg-brand text-white'
                  : 'text-text-secondary hover:bg-bg-hover'
              }`}
            >
              {v.version_name}
              {i === result.recommended_version && <span className="ml-1">⭐</span>}
            </button>
          ))}
        </div>
      )}

      {/* Title */}
      <div className="px-6 py-4 border-b border-border-default">
        <h2 className="text-xl font-semibold text-text-primary">
          {isMultiVersion ? result.versions?.[activeVersion]?.version_name + '版' : result.title}
        </h2>
        {result.emotion_curve_actual.length > 0 && (
          <div className="flex gap-2 mt-2">
            {result.emotion_curve_actual.map((seg, i) => (
              <span key={i} className="text-xs text-text-muted">{seg}</span>
            ))}
          </div>
        )}
      </div>

      {/* Dialogues */}
      <div className="flex-1 overflow-auto px-6 py-4 space-y-3">
        {activeDialogues.map((d, idx) => {
          const isHost = d.speaker === '主播';
          const hl = highlightMap.get(d.turn);

          return (
            <div
              key={d.turn}
              className="relative"
              onMouseEnter={() => hl && setHoveredHighlight(d.turn)}
              onMouseLeave={() => setHoveredHighlight(null)}
            >
              {/* Highlight tooltip */}
              {hoveredHighlight === d.turn && hl && (
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-bg-hover border border-border-default rounded-md px-3 py-1.5 text-xs text-text-primary whitespace-nowrap z-10 shadow-lg">
                  ⭐ {hl.title}
                </div>
              )}

              <div className={`flex ${isHost ? 'justify-start' : 'justify-end'}`}>
                <div
                  className={`max-w-[75%] rounded-lg px-4 py-3 relative ${
                    isHost ? 'bg-[#1E1E2A]' : 'bg-bg-card'
                  } border border-border-default`}
                >
                  {/* Star */}
                  {d.is_highlight && (
                    <Star className="absolute top-2 right-2 w-4 h-4 text-warning fill-warning" />
                  )}

                  {/* Speaker + emotion */}
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-sm font-semibold text-text-primary">{d.speaker}</span>
                    <Badge variant="default" className="text-[10px]">
                      {EMOTION_EMOJI[d.emotion] || ''} {d.emotion}
                    </Badge>
                  </div>

                  {/* Text */}
                  {editMode ? (
                    <textarea
                      value={editedDialogues[idx].text}
                      onChange={(e) => updateDialogue(idx, e.target.value)}
                      rows={3}
                      className="w-full bg-bg-primary border border-brand rounded-md px-3 py-2 text-sm text-text-primary outline-none resize-none"
                    />
                  ) : (
                    <p className="text-base leading-[1.8] text-text-primary">{d.text}</p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom bar */}
      <div className="border-t border-border-default bg-bg-sidebar px-6 py-3 flex items-center justify-between">
        {/* Left: actions */}
        <div className="flex items-center gap-2">
          {editMode ? (
            <>
              <Button size="sm" onClick={handleSaveEdit}><Check className="w-3.5 h-3.5" /> 保存</Button>
              <Button size="sm" variant="ghost" onClick={handleCancelEdit}><X className="w-3.5 h-3.5" /> 取消</Button>
            </>
          ) : (
            <>
              <Button size="sm" variant="secondary" onClick={() => setEditMode(true)}>
                <Edit3 className="w-3.5 h-3.5" /> 编辑
              </Button>
              <Button size="sm" variant="ghost" onClick={() => onRegenerate('主播')}>
                <RotateCcw className="w-3.5 h-3.5" /> 重新生成
              </Button>
              <Button size="sm" variant="ghost" onClick={handleCopy}>
                <Copy className="w-3.5 h-3.5" /> 复制全部
              </Button>
              <Button size="sm" variant="ghost" onClick={handleExport}>
                <Download className="w-3.5 h-3.5" /> 导出
              </Button>
            </>
          )}
        </div>

        {/* Right: stats */}
        <div className="flex items-center gap-4 text-xs text-text-secondary">
          <span>{activeWordCount} 字</span>
          <span>{activeDialogues.length} 轮</span>
          <button
            onClick={() => setShowCompliance(!showCompliance)}
            className="flex items-center gap-1"
          >
            {activeCompliance.passed ? (
              <Badge variant="success">合规通过</Badge>
            ) : (
              <Badge variant="warning">{activeCompliance.hit_count} 个敏感词</Badge>
            )}
          </button>
        </div>
      </div>

      {/* Compliance detail */}
      {showCompliance && !activeCompliance.passed && (
        <div className="border-t border-border-default bg-bg-card px-6 py-3">
          <p className="text-xs text-text-muted mb-2">合规检测结果：</p>
          <div className="space-y-1">
            {activeCompliance.hits.map((hit: any, i: number) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <Badge variant={hit.severity === 'high' ? 'error' : 'warning'}>{hit.word}</Badge>
                <span className="text-text-muted">{hit.category}</span>
              </div>
            ))}
          </div>
          {activeCompliance.suggestion && (
            <p className="text-xs text-warning mt-2">{activeCompliance.suggestion}</p>
          )}
        </div>
      )}
    </div>
  );
}
