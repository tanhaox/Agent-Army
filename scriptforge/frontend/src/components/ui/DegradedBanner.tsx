import { AlertTriangle } from 'lucide-react';

interface Props {
  message?: string;
}

export default function DegradedBanner({ message }: Props) {
  return (
    <div className="flex items-center gap-2 px-4 py-2.5 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-sm text-yellow-400">
      <AlertTriangle className="w-4 h-4 shrink-0" />
      <span>{message || 'AI 服务暂时不可用，当前结果为降级生成，质量可能受限。请稍后重试。'}</span>
    </div>
  );
}
