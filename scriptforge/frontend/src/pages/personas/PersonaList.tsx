import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Users } from 'lucide-react';
import { listPersonas } from '../../services/persona';
import type { PersonaListItem } from '../../types';
import Spinner from '../../components/ui/Spinner';

interface Props {
  selected: string | null;
  onSelect: (id: string) => void;
}

export default function PersonaList({ selected, onSelect }: Props) {
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['personas'],
    queryFn: () => listPersonas(0, 50),
  });

  const items: PersonaListItem[] = (data?.items || []).filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="w-[280px] shrink-0 border-r border-border-default bg-bg-sidebar flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border-default">
        <h3 className="text-sm font-semibold text-text-primary mb-3">人设列表</h3>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索人设..."
            className="w-full bg-bg-card border border-border-default rounded-md pl-8 pr-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-brand"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex justify-center py-8"><Spinner className="text-brand" /></div>
        ) : items.length === 0 ? (
          <div className="px-4 py-8 text-center">
            <Users className="w-8 h-8 text-text-muted mx-auto mb-2" />
            <p className="text-xs text-text-muted">
              {search ? '未找到匹配的人设' : '还没有人设，去学习中心上传切片并分析'}
            </p>
          </div>
        ) : (
          items.map((p) => (
            <button
              key={p.id}
              onClick={() => onSelect(p.id)}
              className={`w-full text-left px-4 py-3 border-b border-border-default transition-colors duration-150
                ${selected === p.id
                  ? 'bg-bg-hover border-l-2 border-l-brand'
                  : 'hover:bg-bg-hover'}`}
            >
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-bg-card flex items-center justify-center text-xs text-text-muted font-medium shrink-0">
                  {p.name[0]}
                </div>
                <div className="min-w-0">
                  <p className="text-sm text-text-primary truncate">{p.name}</p>
                  <p className="text-xs text-text-muted">v{p.version}</p>
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
