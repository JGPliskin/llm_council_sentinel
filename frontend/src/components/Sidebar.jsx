import React from 'react';
import { LayoutGrid, Plus, Fingerprint, Trash2, CheckSquare, MessageSquare } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { format } from 'date-fns';

function Sidebar({
  conversations = [],
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onBulkDeleteConversations,
  isOpen = true
}) {
  const { t } = useTranslation();

  return (
    <div className={`hidden md:flex flex-col border-r border-zinc-800 bg-zinc-950 transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] overflow-hidden relative z-40 h-full ${isOpen ? 'w-64 opacity-100' : 'w-0 opacity-0'}`}>
      <div className="h-14 flex items-center px-4 border-b border-zinc-800 bg-zinc-900/20">
        <LayoutGrid className="w-5 h-5 text-zinc-500 mr-2" />
        <span className="text-xs font-bold text-zinc-300 tracking-widest uppercase">Mission Logs</span>
      </div>

      <div className="p-4">
        <button
          onClick={onNewConversation}
          className="w-full group relative flex items-center justify-center gap-2 py-3 px-4 bg-teal-900/10 border border-teal-500/50 hover:bg-teal-500/20 text-teal-400 text-xs font-bold uppercase tracking-wider transition-all"
          style={{ clipPath: 'polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)' }}
        >
          <Plus className="w-4 h-4" />
          <span>Initiate Session</span>
          <div className="absolute inset-0 bg-grid-pattern opacity-10 pointer-events-none group-hover:opacity-20"></div>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2 custom-scrollbar">
        <div className="text-[10px] text-zinc-600 font-mono mb-2 mt-2 uppercase">Recent Archives</div>
        {conversations.length === 0 && (
          <div className="text-xs text-zinc-600 font-mono p-2 text-center border border-dashed border-zinc-800 rounded">
            NO ARCHIVES FOUND
          </div>
        )}
        {conversations.map((item) => {
          const isSelected = item.id === currentConversationId;
          return (
            <div
              key={item.id}
              className={`group relative p-3 border-l-2 transition-all cursor-pointer ${isSelected ? 'bg-zinc-900/50 border-orange-500' : 'bg-zinc-900/30 border-zinc-800 hover:border-zinc-600 hover:bg-zinc-800/30'}`}
              onClick={() => onSelectConversation(item.id)}
            >
              <div className="flex justify-between items-start mb-1">
                <span className={`text-[10px] font-mono ${isSelected ? 'text-orange-400' : 'text-zinc-500 group-hover:text-zinc-400'}`}>
                  ID #{item.id.substring(0, 6)}
                </span>
                <button
                  onClick={(e) => { e.stopPropagation(); onDeleteConversation(item.id); }}
                  className="text-zinc-700 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                >
                  <Trash2 size={12} />
                </button>
              </div>
              <div className={`text-sm font-medium truncate font-sans ${isSelected ? 'text-zinc-200' : 'text-zinc-400 group-hover:text-zinc-300'}`}>
                {item.title || `Session ${item.created_at ? format(new Date(item.created_at), 'MM/dd HH:mm') : ''}`}
              </div>
            </div>
          );
        })}
      </div>

      <div className="p-4 border-t border-zinc-800 bg-zinc-900/40">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded bg-zinc-800 border border-zinc-700 flex items-center justify-center">
            <Fingerprint className="w-6 h-6 text-zinc-500" />
          </div>
          <div>
            <div className="text-xs font-bold text-zinc-300">ADMIN_USER</div>
            <div className="text-[10px] text-zinc-600 font-mono">ACCESS_GRANTED</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
