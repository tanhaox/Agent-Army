import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { FileText } from 'lucide-react';
import ConfigPanel from './scripts/ConfigPanel';
import ScriptDisplay from './scripts/ScriptDisplay';
import Spinner from '../components/ui/Spinner';
import { toast } from '../components/ui/Toast';
import { generateScript, updateScript, regeneratePart } from '../services/scripts';
import type { GenerateParams, ScriptResult } from '../services/scripts';

export default function ScriptsPage() {
  const [searchParams] = useSearchParams();
  const preselectedPersonaId = searchParams.get('persona_id') || undefined;
  const [result, setResult] = useState<ScriptResult | null>(null);

  const generateMut = useMutation({
    mutationFn: (params: GenerateParams) =>
      generateScript({
        ...params,
        multi_version: params.multi_version || undefined,
      }),
    onSuccess: (data) => {
      setResult(data);
      if (data.multi_version && data.versions) {
        toast('success', `已生成 ${data.versions.length} 个版本脚本`);
      } else {
        toast('success', `脚本生成完成：${data.dialogues.length} 轮对话`);
      }
    },
    onError: (err: any) => {
      toast('error', err?.response?.data?.detail || '脚本生成失败');
    },
  });

  const handleSave = async (content: any) => {
    if (!result) return;
    try {
      await updateScript(result.script_id, content);
      toast('success', '脚本已保存');
    } catch {
      toast('error', '保存失败');
    }
  };

  const handleRegenerate = async (speaker: string) => {
    if (!result) return;
    try {
      const res = await regeneratePart(result.script_id, speaker);
      toast('success', `已重新生成 ${res.regenerated_count} 条${speaker}台词`);
      // Refresh the script
      generateMut.reset();
    } catch (err: any) {
      toast('error', err?.response?.data?.detail || '重新生成失败');
    }
  };

  return (
    <div className="flex h-[calc(100vh-3.5rem-3rem)]">
      {/* Config panel */}
      <ConfigPanel onGenerate={(params) => generateMut.mutate(params)} loading={generateMut.isPending} preselectedPersonaId={preselectedPersonaId} />

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0">
        {generateMut.isPending ? (
          /* Loading state */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-4">
              <Spinner size={40} className="text-brand mx-auto" />
              <p className="text-text-secondary text-sm">AI 正在精心创作中...</p>
              <p className="text-text-muted text-xs">预计需要 15-60 秒</p>
            </div>
          </div>
        ) : result ? (
          /* Script display */
          <ScriptDisplay result={result} onSave={handleSave} onRegenerate={handleRegenerate} />
        ) : (
          /* Empty state */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-4 max-w-md">
              <FileText className="w-16 h-16 text-text-muted mx-auto" />
              <h2 className="text-xl font-semibold text-text-primary">还没有生成脚本</h2>
              <p className="text-sm text-text-secondary leading-relaxed">
                在左侧配置直播间调性、网红人设和连线人信息，然后点击"生成脚本"按钮
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
