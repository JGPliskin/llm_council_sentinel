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
    <div
      className={`flex flex-col border-r transition-all duration-500 overflow-hidden absolute md:relative h-full z-40 ${isOpen ? 'w-64 opacity-100 translate-x-0' : 'w-0 opacity-0 -translate-x-full md:translate-x-0'}`}
      style={{
        transitionTimingFunction: 'cubic-bezier(0.16, 1, 0.3, 1)',
        backgroundColor: 'var(--hud-bg-soft)',
        borderColor: 'var(--hud-cyan-soft)'
      }}
    >
      <div className="h-14 flex items-center px-4 border-b" style={{ borderColor: 'var(--hud-cyan-soft)', backgroundColor: 'rgba(6, 182, 212, 0.05)' }}>
        <LayoutGrid className="w-5 h-5 mr-2" style={{ color: 'var(--hud-cyan)' }} />
        <span className="hud-label" style={{ color: 'var(--hud-cyan)' }}>Mission Logs</span>
      </div>

      <div className="p-4">
        <button
          onClick={onNewConversation}
          className="w-full group relative flex items-center justify-center gap-2 py-3 px-4 text-xs font-bold uppercase tracking-wider transition-all clip-corner-both hud-border hover:hud-border-active"
          style={{ backgroundColor: 'rgba(6, 182, 212, 0.1)', color: 'var(--hud-cyan)' }}
        >
          <Plus className="w-4 h-4" />
          <span className="font-hud">Initiate Session</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2 custom-scrollbar">
        <div className="text-[10px] font-mono mb-2 mt-2 uppercase" style={{ color: 'var(--hud-muted)' }}>Recent Archives</div>
        {conversations.length === 0 && (
          <div className="text-xs font-mono p-2 text-center border border-dashed rounded" style={{ color: 'var(--hud-muted)', borderColor: 'var(--hud-cyan-soft)' }}>
            NO ARCHIVES FOUND
          </div>
        )}
        {conversations.map((item) => {
          const isSelected = item.id === currentConversationId;
          return (
            <div
              key={item.id}
              className={`group relative p-3 border-l-2 transition-all cursor-pointer tech-card ${isSelected ? 'hud-border-active' : ''}`}
              style={{
                borderLeftColor: isSelected ? 'var(--hud-amber)' : 'var(--hud-cyan-soft)'
              }}
              onClick={() => onSelectConversation(item.id)}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="text-[10px] font-mono" style={{ color: isSelected ? 'var(--hud-amber)' : 'var(--hud-muted)' }}>
                  ID #{item.id.substring(0, 6)}
                </span>
                <button
                  onClick={(e) => { e.stopPropagation(); onDeleteConversation(item.id); }}
                  className="text-zinc-700 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                >
                  <Trash2 size={12} />
                </button>
              </div>
              <div className="text-sm font-medium truncate font-sans" style={{ color: isSelected ? 'var(--hud-text)' : 'var(--hud-muted)' }}>
                {item.title || `Session ${item.created_at ? format(new Date(item.created_at), 'MM/dd HH:mm') : ''}`}
              </div>
            </div>
          );
        })}
      </div>

      <div className="p-4 border-t" style={{ borderColor: 'var(--hud-cyan-soft)', backgroundColor: 'rgba(6, 182, 212, 0.03)' }}>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded flex items-center justify-center" style={{ backgroundColor: 'var(--hud-bg)', border: '1px solid var(--hud-cyan-soft)' }}>
            <Fingerprint className="w-6 h-6" style={{ color: 'var(--hud-cyan)' }} />
          </div>
          <div>
            <div className="text-xs font-bold hud-label" style={{ color: 'var(--hud-text)' }}>ADMIN_USER</div>
            <div className="text-[10px] font-mono" style={{ color: 'var(--hud-muted)' }}>ACCESS_GRANTED</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Sidebar;
