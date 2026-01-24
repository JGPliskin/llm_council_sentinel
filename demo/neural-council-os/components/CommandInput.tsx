import React, { useState } from 'react';

interface CommandInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
}

const SHORTCUTS = [
  { label: 'PHILOSOPHY SHIELD', cmd: 'Explain your philosophical defense' },
  { label: 'CODE REVIEW', cmd: 'Review this code block' },
  { label: 'GLOBAL STRATEGY', cmd: 'Analyze global impact' }
];

const CommandInput: React.FC<CommandInputProps> = ({ onSend, disabled }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input);
      setInput('');
    }
  };

  const handleShortcut = (cmd: string) => {
    if (!disabled) {
      onSend(cmd);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto mb-6 px-4">
      {/* Decorative prompt line */}
      <div className="flex items-center gap-2 mb-2 text-[10px] font-mono text-slate-500 uppercase">
        <span className="text-cyber-primary">_COMMAND_LINE</span> // ACTIVE
      </div>

      <div className="relative">
        {/* Input Box */}
        <form onSubmit={handleSubmit} className="relative group">
            <div className="absolute inset-0 bg-cyber-primary/5 blur-sm rounded opacity-0 group-focus-within:opacity-100 transition-opacity"></div>
            <div className="relative flex items-center bg-black/60 border border-slate-700 group-focus-within:border-cyber-primary transition-colors p-4 clip-corners">
                <span className="text-cyber-primary font-mono mr-3 text-lg">{'>'}</span>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={disabled}
                    placeholder="Enter directive to deploy council..."
                    className="flex-1 bg-transparent border-none outline-none text-cyber-text font-mono placeholder-slate-600"
                    autoFocus
                />
                <button 
                    type="submit" 
                    disabled={disabled || !input.trim()}
                    className="ml-4 px-4 py-1 bg-cyber-primary/10 border border-cyber-primary/50 text-cyber-primary font-mono text-xs uppercase hover:bg-cyber-primary hover:text-black transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    ENGAGE
                </button>
            </div>
            {/* Corner visual */}
            <div className="absolute -bottom-1 -right-1 w-2 h-2 bg-cyber-primary opacity-50"></div>
        </form>
      </div>

      {/* Shortcuts */}
      <div className="flex flex-wrap gap-2 mt-3">
        {SHORTCUTS.map((sc, idx) => (
            <button
                key={idx}
                onClick={() => handleShortcut(sc.cmd)}
                disabled={disabled}
                className="flex items-center gap-2 px-3 py-1.5 border border-slate-700 rounded-sm bg-slate-900/50 hover:border-cyber-secondary hover:text-cyber-secondary text-xs font-mono text-slate-400 transition-all uppercase"
            >
                <span className="w-1.5 h-1.5 bg-slate-600 rounded-full group-hover:bg-cyber-secondary"></span>
                {sc.label}
            </button>
        ))}
      </div>
    </div>
  );
};

export default CommandInput;