import { useCallback } from 'react';
import { Upload, X } from 'lucide-react';

const ACCEPT = '.txt';

interface Props {
  files: File[];
  onFilesChange: (files: File[]) => void;
}

export default function TxtUploader({ files, onFilesChange }: Props) {
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const dropped = Array.from(e.dataTransfer.files).filter((f) =>
        f.name.toLowerCase().endsWith('.txt')
      );
      if (dropped.length) onFilesChange([...files, ...dropped]);
    },
    [files, onFilesChange]
  );

  const handleInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = Array.from(e.target.files || []).filter((f) =>
        f.name.toLowerCase().endsWith('.txt')
      );
      if (selected.length) onFilesChange([...files, ...selected]);
      e.target.value = '';
    },
    [files, onFilesChange]
  );

  const remove = (idx: number) => onFilesChange(files.filter((_, i) => i !== idx));

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <label
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="block border-2 border-dashed border-border-default rounded-lg p-8 text-center cursor-pointer hover:border-brand transition-colors duration-150 bg-bg-card"
      >
        <Upload className="w-8 h-8 mx-auto mb-3 text-text-muted" />
        <p className="text-sm text-text-secondary">
          拖拽 .txt 文件到此处，或 <span className="text-brand">点击选择</span>
        </p>
        <p className="text-xs text-text-muted mt-1">支持多文件选择</p>
        <input type="file" accept={ACCEPT} multiple className="hidden" onChange={handleInput} />
      </label>

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs text-text-muted">已选 {files.length} 个文件</p>
          {files.map((f, i) => (
            <div
              key={`${f.name}-${i}`}
              className="flex items-center justify-between bg-bg-primary rounded-md px-3 py-2 text-sm group"
            >
              <span className="text-text-primary truncate">{f.name}</span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-text-muted">
                  {(f.size / 1024).toFixed(1)} KB
                </span>
                <button
                  onClick={() => remove(i)}
                  className="text-text-muted hover:text-error transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
