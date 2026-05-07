import React from 'react';
import { Cpu } from 'lucide-react';

/**
 * Indicador visual de processamento (thinking state) do AEGIS.
 * Exibe uma animacao de pulso e pontos saltitantes.
 */
const ThinkingIndicator: React.FC = () => {
  return (
    <div className="flex gap-4 animate-pulse">
      <div className="w-8 h-8 rounded border border-primary/30 bg-primary/10 flex items-center justify-center shrink-0 shadow-hud">
        <Cpu className="w-4 h-4 text-primary pulse-glow" />
      </div>
      <div className="space-y-2">
        <p className="text-[10px] text-white/40 font-mono tracking-tighter uppercase">AEGIS — PROCESSANDO...</p>
        <div className="flex items-center gap-1.5 p-3 glass border border-primary/20 rounded-xl rounded-tl-none">
          <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]" />
          <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]" />
          <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" />
        </div>
      </div>
    </div>
  );
};

export default ThinkingIndicator;
