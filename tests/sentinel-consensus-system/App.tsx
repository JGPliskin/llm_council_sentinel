import React, { useState, useEffect } from 'react';
import { 
  Terminal, 
  Activity, 
  ShieldAlert, 
  Cpu, 
  Users, 
  MessageSquare, 
  ChevronRight, 
  Globe, 
  Lock,
  Zap,
  LayoutGrid,
  Menu
} from 'lucide-react';

// --- Types ---
interface LogEntry {
  id: string;
  title: string;
  active: boolean;
  status: 'complete' | 'analyzing' | 'error';
}

interface PeerReview {
  name: string;
  id: string;
  rank: number;
  status: string;
  content: string;
  avatarColor: string;
}

// --- Mock Data ---
const MOCK_LOGS: LogEntry[] = [
  { id: '#257707', title: '最后的测试关闭', active: true, status: 'analyzing' },
  { id: '#461735', title: '快要好了', active: false, status: 'complete' },
  { id: '#d00369', title: '杨幂脚臭传闻', active: false, status: 'error' },
  { id: '#3181f6', title: 'Angelababy比较', active: false, status: 'complete' },
  { id: '#9f17d2', title: '完成了吗', active: false, status: 'complete' },
  { id: '#d305f4', title: '思念她', active: false, status: 'complete' },
];

const PEERS: PeerReview[] = [
  {
    name: 'DONALD_TRUMP',
    id: 'SENTINEL_01',
    rank: 9,
    status: 'ACTIVE',
    content: '逻辑自洽，普遍化测试有哲学来源支撑，标注正当终止条件，资源约束下维护信任体系有效。执行：完成评估，除非安全危机。',
    avatarColor: 'bg-orange-500'
  },
  {
    name: 'IMMANUEL_KANT',
    id: 'SENTINEL_02',
    rank: 1,
    status: 'CAUTION',
    content: '哲学框架严谨，论证链条完整，从普遍化测试到人即目的测试，逻辑自洽。但过于理论化，缺乏对具体情境的适应性分析。',
    avatarColor: 'bg-blue-600'
  },
  {
    name: 'HIDEO_KOJIMA',
    id: 'SENTINEL_13',
    rank: 8,
    status: 'SYNCED',
    content: '康德伦理学框架严谨，普遍化检验与目的检验提供清晰决策路径，具有高度可执行性。',
    avatarColor: 'bg-purple-600'
  }
];

// --- Components ---

const Background = () => (
  <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden bg-[#02040a]">
    {/* Grid Floor Effect */}
    <div 
      className="absolute inset-0 opacity-20"
      style={{
        backgroundImage: `linear-gradient(#06b6d4 1px, transparent 1px), linear-gradient(90deg, #06b6d4 1px, transparent 1px)`,
        backgroundSize: '40px 40px',
        transform: 'perspective(500px) rotateX(20deg) scale(1.5)',
        transformOrigin: 'center 80%'
      }}
    />
    
    {/* Vignette */}
    <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,#000000_90%)]" />
    
    {/* Scanline Overlay */}
    <div className="absolute inset-0 z-10 opacity-[0.03] pointer-events-none" 
         style={{
           backgroundImage: 'linear-gradient(transparent 50%, #000 50%)',
           backgroundSize: '100% 4px'
         }} 
    />
    <div 
      className="absolute inset-0 z-10 bg-gradient-to-b from-transparent via-[rgba(6,182,212,0.05)] to-transparent pointer-events-none"
      style={{ animation: 'scanline 8s linear infinite' }}
    />
  </div>
);

interface NeonTextProps {
  children?: React.ReactNode;
  className?: string;
  color?: string;
}

const NeonText: React.FC<NeonTextProps> = ({ children, className = "", color = "text-cyan-400" }) => (
  <span className={`${className} ${color} drop-shadow-[0_0_5px_rgba(6,182,212,0.8)] font-orbitron`}>
    {children}
  </span>
);

interface TechPanelProps {
  children?: React.ReactNode;
  className?: string;
  active?: boolean;
}

const TechPanel: React.FC<TechPanelProps> = ({ children, className = "", active = false }) => {
  return (
    <div className={`relative ${className} transition-all duration-300 group`}>
      {/* Background with glass effect */}
      <div className={`absolute inset-0 clip-corner-both backdrop-blur-md transition-colors duration-300
        ${active ? 'bg-cyan-950/40 border-l-4 border-cyan-400' : 'bg-[#0a0f1e]/80 border-l-2 border-slate-700'}`} 
      />
      
      {/* Border Lines (Decorations) */}
      <div className={`absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 transition-colors duration-300 ${active ? 'border-cyan-400' : 'border-slate-600'}`} />
      <div className={`absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 transition-colors duration-300 ${active ? 'border-cyan-400' : 'border-slate-600'}`} />

      {/* Content */}
      <div className="relative z-10 p-4">
        {children}
      </div>
    </div>
  );
};

const ThinkingBlock = () => (
  <div className="relative mt-6 mb-8 mx-2">
    <div className="absolute -top-3 left-4 bg-[#050510] px-2 z-20">
      <NeonText className="text-xs tracking-widest text-emerald-400">LOGIC_PROCESS // KANT_PROTOCOL</NeonText>
    </div>
    <div className="border border-emerald-500/30 bg-emerald-950/10 p-6 rounded-sm backdrop-blur-sm clip-corner-top-right relative overflow-hidden">
        {/* Animated line inside */}
        <div className="absolute top-0 left-0 h-full w-[2px] bg-emerald-500/50" />
        
        <div className="space-y-4 font-rajdhani text-lg">
            <div className="flex items-start space-x-3">
                <div className="mt-1"><Terminal size={16} className="text-emerald-400" /></div>
                <div>
                    <h4 className="text-emerald-300 font-bold uppercase tracking-wider text-sm mb-1">辨别感性驱动</h4>
                    <p className="text-emerald-100/70 text-base leading-relaxed">
                        识别用户欲望——无论结果好坏，皆欲立即关闭测试。显示出冲动与对结果的漠视。
                    </p>
                </div>
            </div>
            
            <div className="flex items-start space-x-3 opacity-90">
                 <div className="mt-1"><LayoutGrid size={16} className="text-emerald-400" /></div>
                 <div>
                    <h4 className="text-emerald-300 font-bold uppercase tracking-wider text-sm mb-1">抽象行为准则</h4>
                    <p className="text-emerald-100/70 text-base leading-relaxed">
                        将“无论结果好坏，我都关闭测试”概念化为准则：在面对任何评估或决定时，我可以随意终止过程。
                    </p>
                </div>
            </div>

            <div className="flex items-start space-x-3 opacity-80">
                <div className="mt-1"><Lock size={16} className="text-emerald-400" /></div>
                <div>
                    <h4 className="text-emerald-300 font-bold uppercase tracking-wider text-sm mb-1">定言令式检验</h4>
                    <p className="text-emerald-100/70 text-base leading-relaxed">
                       1. 若所有人均随意终止评估，社会缺乏可信度。2. 此时把他人仅作工具，违背人即目的原则。
                    </p>
                </div>
            </div>
        </div>
    </div>
  </div>
);

export default function App() {
  const [currentTime, setCurrentTime] = useState<string>("");
  const [selectedLogId, setSelectedLogId] = useState<string>('#257707');

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      // Format like the game: HH:MM:SS
      setCurrentTime(now.toLocaleTimeString('en-US', { hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="relative w-full h-screen text-cyan-100 overflow-hidden font-rajdhani selection:bg-cyan-500 selection:text-black">
      <Background />

      {/* --- HUD Header --- */}
      <header className="absolute top-0 left-0 w-full h-16 z-50 flex items-center justify-between px-6 border-b border-cyan-500/20 bg-[#050a14]/90 backdrop-blur">
        <div className="flex items-center space-x-4">
            <div className="flex flex-col">
                <NeonText className="text-2xl font-bold tracking-[0.2em] italic">MISSION LOGS</NeonText>
                <div className="text-[10px] text-cyan-600 tracking-widest flex items-center space-x-2">
                    <span>DEFENSE AREA: 008%</span>
                    <span className="w-20 h-1 bg-cyan-900 overflow-hidden relative">
                         <div className="absolute top-0 left-0 h-full w-[8%] bg-cyan-400 animate-pulse" />
                    </span>
                </div>
            </div>
        </div>

        {/* Center Top Clock/Timer */}
        <div className="absolute left-1/2 transform -translate-x-1/2 top-0 bg-cyan-950/80 px-8 pt-2 pb-4 clip-corner-both border-b-2 border-cyan-500/50">
            <NeonText className="text-3xl font-mono tracking-widest text-white">{currentTime}</NeonText>
            <div className="text-center text-[10px] text-cyan-400 tracking-[0.3em] uppercase mt-1">System Time</div>
        </div>

        <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2 text-sm text-cyan-400/70">
                <Globe size={14} />
                <span className="tracking-widest">ONLINE</span>
            </div>
             <div className="flex items-center space-x-2 text-sm text-cyan-400/70">
                <Cpu size={14} />
                <span className="tracking-widest">SENTINEL GEN-2</span>
            </div>
            <button className="text-cyan-500 hover:text-white transition-colors"><Menu size={24} /></button>
        </div>
      </header>

      {/* --- Main Layout --- */}
      <main className="absolute inset-0 pt-20 pb-12 px-6 grid grid-cols-12 gap-6 z-20">
        
        {/* --- Left Column: Mission Select --- */}
        <aside className="col-span-3 flex flex-col space-y-4 no-scrollbar overflow-y-auto pr-2 pb-10">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-cyan-500 text-xs tracking-[0.2em] font-orbitron">ARCHIVE_DATA</h3>
                <Activity size={14} className="text-cyan-500 animate-pulse" />
            </div>

            <button className="group relative w-full h-12 bg-cyan-500/10 border border-cyan-400/50 flex items-center justify-center overflow-hidden hover:bg-cyan-500/20 transition-all clip-corner-top-right">
                 <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/diagmonds-light.png')] opacity-10" />
                 <span className="text-cyan-300 font-orbitron tracking-widest group-hover:scale-110 transition-transform flex items-center">
                    <Zap size={16} className="mr-2" /> INITIATE SESSION
                 </span>
            </button>
            
            <div className="space-y-3 mt-4">
                {MOCK_LOGS.map((log) => (
                    <TechPanel 
                        key={log.id} 
                        active={log.id === selectedLogId}
                        className="cursor-pointer hover:translate-x-2"
                    >
                        <div className="flex justify-between items-start" onClick={() => setSelectedLogId(log.id)}>
                            <div>
                                <div className={`text-[10px] font-mono mb-1 ${log.id === selectedLogId ? 'text-amber-400' : 'text-slate-500'}`}>ID {log.id}</div>
                                <div className={`font-bold tracking-wide text-lg ${log.id === selectedLogId ? 'text-white text-shadow-glow' : 'text-slate-400'}`}>
                                    {log.title}
                                </div>
                            </div>
                            {log.active && <div className="w-2 h-2 bg-amber-400 rounded-full animate-ping mt-2" />}
                        </div>
                    </TechPanel>
                ))}
            </div>
        </aside>

        {/* --- Center Column: Dialogue & Analysis --- */}
        <section className="col-span-6 flex flex-col relative h-full">
            
            {/* Header for Center */}
            <div className="flex items-center space-x-4 mb-6 border-b border-cyan-500/30 pb-4">
                <div className="w-16 h-16 bg-gradient-to-br from-amber-600 to-amber-900 border-2 border-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.5)] flex items-center justify-center text-4xl font-bold font-orbitron text-white">
                    ?
                </div>
                <div className="flex-1">
                     <div className="flex items-center space-x-2 text-xs text-amber-500/80 font-mono tracking-widest mb-1">
                        <ShieldAlert size={12} />
                        <span>ENTITY // COUNCILOR // CLASS A</span>
                     </div>
                     <NeonText className="text-5xl font-black text-white tracking-wide" color="text-white">
                        康德
                     </NeonText>
                     <div className="text-[10px] text-slate-500 tracking-[0.5em] mt-1 uppercase">ID: Immanuel</div>
                </div>
            </div>

            {/* Scrollable Content Area */}
            <div className="flex-1 overflow-y-auto no-scrollbar relative pr-2 pb-10">
                {/* Thinking Process Block */}
                <ThinkingBlock />

                {/* Proposal Section */}
                <div className="mt-8 mx-2 animate-[slideIn_0.5s_ease-out]">
                    <div className="flex items-center space-x-2 mb-4">
                        <div className="flex space-x-1">
                            <ChevronRight className="text-amber-500" />
                            <ChevronRight className="text-amber-500 opacity-50" />
                        </div>
                        <h3 className="text-amber-500 font-bold font-orbitron text-xl tracking-widest">PROPOSAL: 康德</h3>
                    </div>

                    <div className="pl-6 border-l-2 border-amber-500/20 space-y-6">
                        <p className="text-xl text-white font-medium leading-relaxed drop-shadow-md">
                            首先，把你的冲动与对结果的漠视放在一边。让我们看看这个问题中，<span className="text-cyan-300 border-b border-cyan-500/50">理性的声音</span>是什么。
                        </p>
                        
                        <div className="space-y-2">
                             <div className="text-slate-400 text-sm font-mono tracking-wide">1. 你的行为准则</div>
                             <div className="text-lg text-cyan-100/90 italic pl-4">
                                “不论最终测试的结果好坏，我都把它关掉。”
                             </div>
                        </div>

                         <div className="space-y-2">
                             <div className="text-slate-400 text-sm font-mono tracking-wide">2. 抽象化</div>
                             <div className="bg-amber-500/10 border border-amber-500/30 p-4 text-amber-100">
                                在任何评估或决定过程中，我可以随意终止程序，以免面对可能的不利结局。
                             </div>
                        </div>

                         <div className="space-y-2">
                             <div className="text-slate-400 text-sm font-mono tracking-wide">3. 定言令式检验</div>
                             <div className="flex items-center space-x-2">
                                <span className="w-4 h-4 rounded-full border border-cyan-400 flex items-center justify-center text-[10px]">1</span>
                                <span className="text-lg">普遍化测试</span>
                             </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Stage Indicator Footer */}
            <div className="absolute bottom-0 left-0 right-0 h-10 bg-[#050a14] border-t border-cyan-900 flex items-center justify-between px-4 text-xs font-mono">
                <div className="flex items-center space-x-4">
                    <div className="flex space-x-1">
                        <div className="w-6 h-4 border border-cyan-700 bg-cyan-900/50" />
                        <div className="w-6 h-4 border border-cyan-700 bg-cyan-900/50" />
                        <div className="w-6 h-4 border border-cyan-700" />
                    </div>
                    <span className="text-purple-400">STAGE [03 / 03] // CONSENSUS</span>
                </div>
                <div className="text-slate-600">CPU: 45% MEM: 12GB</div>
            </div>
        </section>

        {/* --- Right Column: Peer Reviews / Units --- */}
        <aside className="col-span-3 flex flex-col h-full pl-4 border-l border-cyan-900/30 relative">
             <div className="absolute top-0 right-0 text-[100px] font-bold text-white/5 font-orbitron -z-10 overflow-hidden pointer-events-none select-none">
                G-13
            </div>

             <div className="flex items-center justify-between mb-6">
                <NeonText className="text-sm tracking-[0.2em]">UNIT_STATUS</NeonText>
                <Users size={16} className="text-cyan-400" />
            </div>

            <div className="space-y-6 overflow-y-auto no-scrollbar pb-20">
                {PEERS.map((peer, idx) => (
                    <div key={peer.id} className="relative group">
                        {/* Connecting Line Style */}
                        <div className="absolute -left-4 top-4 w-4 h-[1px] bg-cyan-800" />
                        <div className="absolute -left-4 top-4 w-[1px] h-full bg-cyan-800/30" />

                        <div className="bg-[#080c18] border border-cyan-800 hover:border-cyan-400 transition-colors duration-300 p-1">
                            {/* Header */}
                            <div className="flex justify-between items-center bg-cyan-950/30 px-2 py-1 mb-2">
                                <div className="flex items-center space-x-2">
                                    <div className={`w-2 h-2 rounded-full ${peer.status === 'ACTIVE' ? 'bg-green-500 animate-pulse' : 'bg-slate-500'}`} />
                                    <span className="text-xs font-bold text-cyan-200">{peer.name}</span>
                                </div>
                                <span className="text-[10px] font-mono text-cyan-600">RANK #{peer.rank}</span>
                            </div>

                            {/* Content */}
                            <div className="p-2">
                                <p className="text-sm text-slate-300 leading-snug font-light">
                                    {peer.content}
                                </p>
                            </div>
                            
                            {/* Decorative footer for card */}
                            <div className="h-1 w-full bg-cyan-900/50 mt-2 flex justify-end">
                                <div className="w-1/3 h-full bg-cyan-600/50" />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </aside>
      </main>

      {/* --- Bottom Action Bar (Sentinel Selection Style) --- */}
      <footer className="absolute bottom-0 w-full h-16 bg-[#02040a] border-t border-cyan-500/30 z-50 flex items-center justify-center space-x-4 px-10">
         <div className="absolute left-6 bottom-4 flex items-center space-x-3 text-slate-500">
             <div className="p-2 border border-slate-700 rounded-full">
                <Users size={20} />
             </div>
             <div>
                 <div className="text-xs text-white font-bold">ADMIN_USER</div>
                 <div className="text-[10px] tracking-widest">ACCESS_GRANTED</div>
             </div>
         </div>

         {/* Selection Buttons */}
         {['康德', '小岛秀夫', '特朗普'].map((name, i) => (
             <button key={name} className={`
                relative h-10 min-w-[180px] px-6 skew-x-[-20deg] border-2 transition-all duration-200 group
                ${i === 1 ? 'border-cyan-400 bg-cyan-900/40' : 'border-slate-700 hover:border-amber-500 bg-[#0a1020]'}
             `}>
                 <div className="skew-x-[20deg] flex items-center justify-between w-full h-full">
                     <span className="text-[10px] text-slate-400 uppercase tracking-widest">Councilor</span>
                     <span className={`font-bold font-orbitron ${i === 1 ? 'text-cyan-100 text-shadow-glow' : 'text-slate-300 group-hover:text-amber-400'}`}>
                        {name}
                     </span>
                     <span className="text-[10px] font-mono opacity-50">#{i === 1 ? '2.0' : `1.${3+i*4}`}</span>
                 </div>
             </button>
         ))}
      </footer>
    </div>
  );
}