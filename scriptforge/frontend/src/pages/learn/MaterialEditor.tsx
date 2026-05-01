import { useState } from 'react';
import { ChevronDown, ChevronRight, Video } from 'lucide-react';
import Modal from '../../components/ui/Modal';
import Badge from '../../components/ui/Badge';
import type { MaterialItem } from '../LearnPage';

interface Props {
  materials: MaterialItem[];
  onUpdate: (id: string, updates: Partial<MaterialItem>) => void;
  locked: boolean;
  anchorName?: string;
}

export default function MaterialEditor({ materials, onUpdate, locked, anchorName }: Props) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [videoModal, setVideoModal] = useState<{ open: boolean; src?: string; name?: string }>({ open: false });

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleTextEdit = (id: string, text: string) => {
    onUpdate(id, { editedText: text });
  };

  const openVideo = (m: MaterialItem) => {
    // Use audioPath or sourceUrl — construct a playable source
    const src = m.audioPath || m.sourceUrl;
    setVideoModal({ open: true, src, name: m.name });
  };

  if (!materials.length) return null;

  return (
    <>
      <div className="space-y-2">
        {materials.map((m) => {
          const expanded = expandedIds.has(m.id);
          const isVideo = m.type === 'video' || !!m.sourceUrl;

          return (
            <div key={m.id} className="bg-bg-card border border-border-default rounded-lg overflow-hidden">
              {/* Card header */}
              <div className="flex items-center justify-between px-4 py-3">
                <button
                  onClick={() => toggleExpand(m.id)}
                  className="flex items-center gap-2 text-sm text-text-primary hover:text-brand transition-colors min-w-0"
                >
                  {expanded ? <ChevronDown className="w-4 h-4 shrink-0" /> : <ChevronRight className="w-4 h-4 shrink-0" />}
                  <span className="truncate">{m.name}</span>
                  {anchorName && <Badge variant="default" className="text-[10px] shrink-0">来自: {anchorName}</Badge>}
                </button>
                <div className="flex items-center gap-2 shrink-0">
                  {isVideo && (
                    <button
                      onClick={() => openVideo(m)}
                      className="flex items-center gap-1 text-xs text-text-muted hover:text-brand transition-colors px-2 py-1 rounded hover:bg-bg-hover"
                    >
                      <Video className="w-3.5 h-3.5" />
                      查看原视频
                    </button>
                  )}
                  {m.duration != null && (
                    <span className="text-xs text-text-muted">{Math.round(m.duration)}s</span>
                  )}
                </div>
              </div>

              {/* Card body — editable textarea */}
              {expanded && (
                <div className="px-4 pb-3 border-t border-border-default">
                  <textarea
                    value={m.editedText}
                    onChange={(e) => handleTextEdit(m.id, e.target.value)}
                    disabled={locked}
                    rows={8}
                    className="w-full mt-3 bg-bg-primary border border-border-default rounded-md px-3 py-2 text-sm text-text-primary font-mono leading-relaxed outline-none focus:border-brand resize-y disabled:opacity-60 disabled:cursor-not-allowed"
                    placeholder="转写文本将在此显示..."
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Video preview modal */}
      <Modal
        open={videoModal.open}
        onClose={() => setVideoModal({ open: false })}
        title={videoModal.name || '视频预览'}
        className="max-w-3xl"
      >
        {videoModal.src ? (
          <video
            controls
            className="w-full rounded-lg"
            src={videoModal.src.startsWith('http') ? videoModal.src : `/api/files/${videoModal.src}`}
          >
            您的浏览器不支持视频播放
          </video>
        ) : (
          <p className="text-sm text-text-muted py-8 text-center">暂无可播放的视频源</p>
        )}
      </Modal>
    </>
  );
}
