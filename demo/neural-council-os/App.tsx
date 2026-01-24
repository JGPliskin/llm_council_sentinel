import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import UnitDeck from './components/UnitDeck';
import CommandInput from './components/CommandInput';
import ChatInterface from './components/ChatInterface';
import UnitInfoPanel from './components/UnitInfoPanel';
import { CHARACTERS } from './constants';
import { Message } from './types';
import { sendMessageToGemini } from './services/geminiService';

const App: React.FC = () => {
  // State now tracks an ARRAY of selected IDs
  const [selectedCharIds, setSelectedCharIds] = useState<string[]>([CHARACTERS[0].id]);
  const [hoveredCharId, setHoveredCharId] = useState<string | null>(null);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  // Derived state: Get actual character objects
  const activeCharacters = CHARACTERS.filter(c => selectedCharIds.includes(c.id));

  // Determine which character description to show
  // Priority: Hovered -> Most Recently Selected (last in list) -> First Selected -> Null
  const displayedCharId = hoveredCharId || (selectedCharIds.length > 0 ? selectedCharIds[selectedCharIds.length - 1] : null);
  const displayedCharacter = CHARACTERS.find(c => c.id === displayedCharId) || null;


  const handleSendMessage = async (text: string) => {
    if (activeCharacters.length === 0) return;

    // Optimistic Update
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: Date.now()
    };

    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setIsTyping(true);

    // Call Gemini with the LIST of active characters
    const responseText = await sendMessageToGemini(
      newHistory, 
      text, 
      activeCharacters
    );

    const modelMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: 'model',
      content: responseText,
      timestamp: Date.now()
    };

    setMessages([...newHistory, modelMsg]);
    setIsTyping(false);
  };

  const handleToggleCharacter = (id: string) => {
      setSelectedCharIds(prev => {
          if (prev.includes(id)) {
              return prev.filter(cId => cId !== id);
          } else {
              return [...prev, id];
          }
      });
  };

  return (
    <div className="flex h-[100dvh] w-screen overflow-hidden bg-cyber-black text-white selection:bg-cyber-primary selection:text-black font-sans">
      {/* Background Overlay for Scanlines */}
      <div className="scanline pointer-events-none z-50 fixed inset-0"></div>
      
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative bg-[url('https://images.unsplash.com/photo-1535868463750-c78d9543614f?q=80&w=2676&auto=format&fit=crop')] bg-cover bg-center">
        <div className="absolute inset-0 bg-cyber-dark/95 backdrop-blur-sm"></div>

        {/* Top Header Bar */}
        <div className="relative z-10 h-10 md:h-12 border-b border-cyber-panel flex items-center justify-between px-4 md:px-6 bg-cyber-dark/80 backdrop-blur shrink-0">
            <div className="text-[8px] md:text-[10px] font-mono text-slate-500 uppercase tracking-[0.2em]">
                System Status // {activeCharacters.length > 0 ? `${activeCharacters.length} UNITS` : 'STANDBY'}
            </div>
            <div className="flex items-center gap-2 md:gap-4">
                 <div className="text-[8px] md:text-[10px] font-mono text-cyber-primary flex items-center gap-1">
                     <span className={`w-1 md:w-1.5 h-1 md:h-1.5 rounded-full ${activeCharacters.length > 0 ? 'bg-cyber-primary animate-pulse' : 'bg-red-500'}`}></span>
                     <span className="hidden md:inline">NEURAL_BRIDGE_ACTIVE</span>
                     <span className="md:hidden">ONLINE</span>
                 </div>
                 <div className="w-6 h-6 md:w-8 md:h-8 rounded-full border border-slate-700 bg-slate-800 overflow-hidden">
                    <img src="https://images.unsplash.com/photo-1511367461989-f85a21fda167?q=80&w=200&auto=format&fit=crop" className="opacity-50 grayscale" alt="Overseer" />
                 </div>
            </div>
        </div>

        {/* Chat / Hero Area (Holographic Stage) */}
        <ChatInterface 
            activeCharacters={activeCharacters} 
            messages={messages} 
            isTyping={isTyping}
        />

        {/* Info Panel (The Red Box Area) */}
        <div className="relative z-10 shrink-0">
            <UnitInfoPanel character={displayedCharacter} />
        </div>

        {/* Input Area */}
        <CommandInput 
            onSend={handleSendMessage} 
            disabled={isTyping || activeCharacters.length === 0} 
        />

        {/* Bottom Unit Deck */}
        <UnitDeck 
            characters={CHARACTERS} 
            selectedIds={selectedCharIds} 
            onToggle={handleToggleCharacter}
            onHover={setHoveredCharId}
        />
      </div>
    </div>
  );
};

export default App;