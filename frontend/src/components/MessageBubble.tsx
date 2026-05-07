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
 * Refinado para estética mono-space e glassmorphism premium.
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
      "flex gap-3 group animate-in fade-in slide-in-from-bottom-2 duration-500",
      !isAegis && "flex-row-reverse"
    )}>
      {/* Icon Indicator */}
      <div className={cn(
        "w-7 h-7 flex items-center justify-center shrink-0 border transition-all duration-500",
        isAegis 
          ? "border-cyan-500/30 bg-cyan-500/10 text-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.1)]" 
          : "border-white/10 bg-white/5 text-white/40"
      )}>
        {isAegis ? <Cpu className="w-3.5 h-3.5" /> : <User className="w-3.5 h-3.5" />}
      </div>

      {/* Message Content Container */}
      <div className={cn(
        "flex flex-col gap-1.5 max-w-[88%]",
        !isAegis && "items-end"
      )}>
        {/* Metadata Header */}
        <div className="flex items-center gap-3 px-1">
          <span className="text-[8px] font-mono tracking-[0.2em] text-white/30 uppercase">
            {isAegis ? (agentUsed || 'Aegis_Process') : 'Authorized_User'}
          </span>
          <div className="w-1 h-1 rounded-full bg-white/10" />
          <span className="text-[8px] font-mono text-white/20 uppercase">
            {timestamp}
          </span>
          {isAegis && latencyMs && (
            <span className="text-[8px] font-mono text-cyan-500/40">{latencyMs}ms</span>
          )}
        </div>

        {/* Text Block */}
        <div className={cn(
          "px-4 py-3 text-[11px] font-mono leading-relaxed tracking-wide transition-all duration-300",
          "glass border backdrop-blur-md",
          isAegis 
            ? "border-white/5 text-white/80 bg-white/[0.02] group-hover:bg-white/[0.04] group-hover:border-white/10" 
            : "border-cyan-500/10 text-cyan-100/90 bg-cyan-500/[0.03] group-hover:bg-cyan-500/[0.06] group-hover:border-cyan-500/20"
        )}>
          {content}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
