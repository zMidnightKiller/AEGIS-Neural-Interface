import React from 'react';
import { Cpu, User } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utilitário para merge de classes Tailwind.
 */
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface MessageBubbleProps {
  role: 'user' | 'aegis';
  content: string;
  timestamp: string;
  agentUsed?: string;
  latencyMs?: number;
}

/**
 * Componente MessageBubble para exibir mensagens no chat.
 * Suporta papeis 'user' e 'aegis' com estilos distintos.
 */
const MessageBubble: React.FC<MessageBubbleProps> = ({ 
  role, 
  content, 
  timestamp, 
  agentUsed,
  latencyMs 
}) => {
  const isAegis = role === 'aegis';

  return (
    <div className={cn(
      "flex gap-4 group animate-in fade-in slide-in-from-bottom-2 duration-300",
      !isAegis && "flex-row-reverse"
    )}>
      {/* Avatar */}
      <div className={cn(
        "w-8 h-8 rounded border flex items-center justify-center shrink-0 transition-all shadow-hud",
        isAegis 
          ? "border-primary/30 bg-primary/10 text-primary" 
          : "border-white/10 bg-white/5 text-white/60"
      )}>
        {isAegis ? <Cpu className="w-4 h-4" /> : <User className="w-4 h-4" />}
      </div>

      {/* Content */}
      <div className={cn(
        "space-y-2 max-w-[85%]",
        !isAegis && "items-end flex flex-col"
      )}>
        <div className="flex items-center gap-3">
          <p className="text-[10px] text-white/40 font-mono tracking-tighter uppercase">
            {isAegis ? (agentUsed || 'AEGIS') : 'USER'} — {timestamp}
          </p>
          {isAegis && latencyMs && (
            <span className="text-[9px] text-primary/40 font-mono">{latencyMs}ms</span>
          )}
        </div>

        <div className={cn(
          "p-4 rounded-xl text-sm leading-relaxed text-white/90 glass border transition-all",
          isAegis 
            ? "rounded-tl-none border-white/10 group-hover:border-primary/20" 
            : "rounded-tr-none border-white/10 bg-white/5 group-hover:border-white/20"
        )}>
          {content}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
