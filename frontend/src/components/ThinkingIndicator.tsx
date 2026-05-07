import React from 'react';
import { Cpu } from 'lucide-react';

/**
 * Indicador visual de processamento (thinking state) do AEGIS.
 * Refinado para o novo sistema monospaçado e glassmorphism.
 */
const ThinkingIndicator: React.FC = () => {
  return (
    <div className="flex gap-3 animate-in fade-in duration-700">
      <div className="w-7 h-7 flex items-center justify-center border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.15)] animate-pulse">
        <Cpu className="w-3.5 h-3.5" />
      </div>
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2 px-1">
          <span className="text-[8px] font-mono tracking-[0.3em] text-cyan-400/60 uppercase animate-pulse">
            Neural_Processing_Active
          </span>
        </div>
        <div className="flex items-center gap-2 px-4 py-3 glass border border-white/5 bg-white/[0.02]">
          <div className="w-1 h-1 bg-cyan-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
          <div className="w-1 h-1 bg-cyan-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
          <div className="w-1 h-1 bg-cyan-400 rounded-full animate-bounce" />
        </div>
      </div>
    </div>
  );
};

export default ThinkingIndicator;
