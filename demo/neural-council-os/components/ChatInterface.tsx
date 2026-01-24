import React, { useEffect, useRef } from 'react';
import { Character, Message } from '../types';
import ReactMarkdown from 'react-markdown';

interface ChatInterfaceProps {
  activeCharacters: Character[]; 
  messages: Message[];
  isTyping: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ activeCharacters, messages, isTyping }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping, activeCharacters]);

  return (
    <div className="flex-1 relative flex flex-col overflow-hidden">
        {/* --- HOLOGRAPHIC STAGE (BACKGROUND LAYER) --- */}
        <div className="absolute inset-0 z-0 flex items-end justify-center pointer-events-none overflow-hidden pb-10 gap-2 md:gap-4 lg:gap-12 px-4">
            {/* Background Grid */}
            <div className="absolute inset-0 bg-grid-pattern opacity-[0.03]"></div>
            
            {/* Render Active Characters as Tachie (Standing Art) */}
            {activeCharacters.map((char, index) => (
                <div 
                    key={char.id}
                    className={`
                        relative h-[70%] md:h-[85%] w-auto aspect-[3/5] transition-all duration-700 ease-in-out transform
                        flex flex-col justify-end
                    `}
                    style={{
                        animation: `hologramFadeIn 0.5s ease-out ${index * 0.1}s forwards`,
                        opacity: 0,
                    }}
                >
                    {/* --- THE BORDER FRAME (Top, Left, Right) --- */}
                    <div className={`
                        absolute inset-0 z-20 
                        border-t-2 border-l-2 border-r-2 
                        border-cyber-primary/40
                        bg-gradient-to-b from-cyber-primary/5 to-transparent
                        box-border pointer-events-none
                    `}>
                        {/* Corner Accents */}
                        <div className="absolute top-0 left-0 w-2 h-8 bg-cyber-primary/60"></div>
                        <div className="absolute top-0 right-0 w-2 h-8 bg-cyber-primary/60"></div>
                        <div className="absolute top-0 left-0 w-8 h-2 bg-cyber-primary/60"></div>
                        <div className="absolute top-0 right-0 w-8 h-2 bg-cyber-primary/60"></div>
                        
                        {/* Scanner Line Animation */}
                        <div className="absolute inset-0 w-full h-[2px] bg-cyber-primary/30 animate-scan-vertical"></div>
                    </div>

                    {/* Character Image */}
                    <img 
                        src={char.standingUrl} 
                        alt={char.name}
                        className="h-full w-full object-cover object-top mask-image-gradient relative z-10"
                        style={{
                            maskImage: 'linear-gradient(to bottom, black 70%, transparent 100%)',
                            WebkitMaskImage: 'linear-gradient(to bottom, black 70%, transparent 100%)',
                            filter: 'drop-shadow(0 0 10px rgba(0, 240, 255, 0.2)) grayscale(20%) sepia(10%) hue-rotate(180deg) saturate(150%)',
                            opacity: 0.8 // Slightly transparent for hologram feel
                        }}
                    />
                    
                    {/* Holographic Scanlines overlay on image */}
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 bg-[length:100%_2px,3px_100%] pointer-events-none mix-blend-hard-light opacity-30"></div>
                    
                    {/* Name Tag */}
                    <div className="absolute bottom-[10%] left-1/2 -translate-x-1/2 bg-black/80 border border-cyber-primary/30 backdrop-blur px-2 md:px-3 py-1 text-[8px] md:text-[10px] font-mono text-cyber-primary uppercase tracking-widest z-30 whitespace-nowrap">
                        {char.name}
                    </div>
                </div>
            ))}
        </div>

        {/* --- MESSAGES LAYER --- */}
        <div className="flex-1 z-10 overflow-y-auto p-4 lg:p-8 space-y-4 md:space-y-6 scrollbar-hide" ref={scrollRef}>
            {activeCharacters.length === 0 && messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 font-mono">
                    <div className="text-4xl mb-4 opacity-20">⚠</div>
                    <p>NO NEURAL LINK ESTABLISHED</p>
                    <p className="text-xs mt-2 text-cyber-primary animate-pulse">Select a unit from the deck to begin</p>
                </div>
            )}

            {messages.map((msg) => (
                <div 
                    key={msg.id} 
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                    <div 
                        className={`
                        max-w-[85%] md:max-w-[70%] lg:max-w-[60%] p-3 md:p-4 relative border backdrop-blur-xl shadow-lg
                        ${msg.role === 'user' 
                            ? 'bg-slate-900/90 border-slate-600 text-slate-100 clip-corners-right' 
                            : 'bg-black/80 border-cyber-primary/40 text-cyber-text clip-corners-left'}
                        `}
                    >
                        {/* Header */}
                        <div className="flex justify-between items-center mb-1 md:mb-2 pb-1 md:pb-2 border-b border-white/10 text-[8px] md:text-[10px] font-mono opacity-70 uppercase">
                            <span>{msg.role === 'user' ? 'ADMIN_USER' : 'COUNCIL_RESPONSE'}</span>
                            <span>{new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                        </div>

                        {/* Content */}
                        <div className="font-mono text-xs md:text-sm leading-relaxed prose prose-invert prose-p:my-1 prose-headings:text-cyber-secondary prose-strong:text-cyber-primary">
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>

                        {/* Decor */}
                        {msg.role === 'model' && (
                            <div className="absolute -left-1 top-0 bottom-0 w-1 bg-cyber-primary shadow-[0_0_10px_cyan]"></div>
                        )}
                    </div>
                </div>
            ))}

            {isTyping && (
                <div className="flex justify-start">
                    <div className="bg-black/80 backdrop-blur border border-cyber-primary/30 p-3 md:p-4 clip-corners-left flex items-center gap-2">
                        <span className="w-1.5 h-1.5 md:w-2 md:h-2 bg-cyber-primary animate-bounce"></span>
                        <span className="w-1.5 h-1.5 md:w-2 md:h-2 bg-cyber-primary animate-bounce delay-100"></span>
                        <span className="w-1.5 h-1.5 md:w-2 md:h-2 bg-cyber-primary animate-bounce delay-200"></span>
                        <span className="text-[10px] md:text-xs font-mono text-cyber-primary ml-2">DELIBERATING...</span>
                    </div>
                </div>
            )}
        </div>

        <style>{`
            @keyframes hologramFadeIn {
                from { opacity: 0; transform: translateY(20px) scale(0.95); filter: blur(10px); }
                to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0px); }
            }
            @keyframes scan-vertical {
                0% { top: 0%; opacity: 0; }
                10% { opacity: 1; }
                90% { opacity: 1; }
                100% { top: 100%; opacity: 0; }
            }
            .animate-scan-vertical {
                animation: scan-vertical 3s linear infinite;
                background: linear-gradient(to bottom, transparent, rgba(0, 240, 255, 0.5), transparent);
                height: 4px;
            }
        `}</style>
    </div>
  );
};

export default ChatInterface;