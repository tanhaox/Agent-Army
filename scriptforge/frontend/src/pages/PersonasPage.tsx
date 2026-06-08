import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Users } from 'lucide-react';
import PersonaList from './personas/PersonaList';
import PersonaDetailPanel from './personas/PersonaDetailPanel';
import CreatorPage from './CreatorPage';
import EmptyState from '../components/ui/EmptyState';

type PageTab = 'personas' | 'creator';

const PAGE_TABS: { key: PageTab; label: string }[] = [
  { key: 'personas', label: '现有人设' },
  { key: 'creator', label: 'AI 生成' },
];

export default function PersonasPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [selectedId, setSelectedId] = useState<string | null>(() => searchParams.get('select'));
  const [pageTab, setPageTab] = useState<PageTab>('personas');

  useEffect(() => {
    const idFromUrl = searchParams.get('select');
    if (idFromUrl) setSelectedId(idFromUrl);
  }, [searchParams]);

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem-3rem)]">
      {/* Page-level tabs */}
      <div className="flex gap-1 border-b border-border-default px-6">
        {PAGE_TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setPageTab(key)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors duration-150 relative cursor-pointer
              ${pageTab === key ? 'text-brand' : 'text-text-secondary hover:text-text-primary'}`}
          >
            {label}
            {pageTab === key && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-brand rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {pageTab === 'personas' ? (
        <div className="flex flex-1 min-h-0">
          <PersonaList selected={selectedId} onSelect={setSelectedId} />
          <div className="flex-1 min-w-0 overflow-y-auto">
            {selectedId ? (
              <PersonaDetailPanel personaId={selectedId} />
            ) : (
              <div className="flex-1 flex items-center justify-center h-full">
                <EmptyState
                icon={Users}
                title="选择或创建人设"
                description="选择左侧人设查看详情，或前往学习中心上传素材分析新的人设"
                actions={[
                  { label: '前往学习中心', onClick: () => navigate('/learn'), variant: 'secondary' },
                ]}
              />
              </div>
            )}
          </div>
        </div>
      ) : (
        <CreatorPage />
      )}
    </div>
  );
}
