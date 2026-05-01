import { useState } from 'react';
import { Link } from 'react-router-dom';
import PersonaList from './personas/PersonaList';
import PersonaDetailPanel from './personas/PersonaDetailPanel';

export default function PersonasPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <div className="flex h-[calc(100vh-3.5rem-3rem)]">
      <PersonaList selected={selectedId} onSelect={setSelectedId} />

      <div className="flex-1 flex items-center justify-center">
        {selectedId ? (
          <PersonaDetailPanel personaId={selectedId} />
        ) : (
          <div className="text-center space-y-3 max-w-sm">
            <p className="text-text-secondary text-sm">
              选择左侧人设查看详情，或前往{' '}
              <Link to="/learn" className="text-brand hover:text-brand-hover transition-colors">
                学习中心
              </Link>{' '}
              创建新的人设
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
