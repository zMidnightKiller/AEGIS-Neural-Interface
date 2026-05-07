import React, { useRef, useEffect } from 'react';
import { Send, Mic, Activity, Database } from 'lucide-react';
import MessageBubble from './MessageBubble';
import ThinkingIndicator from './ThinkingIndicator';

interface Message {
  id: string;
  role: 'user' | 'aegis';
  content: string;
  timestamp: string;
  agentUsed?: string;
  latencyMs?: number;
}

interface InteractionCardProps {
  messages: Message[];
  inputValue: string;
  setInputValue: (val: string) => void;
  onSendMessage: () => void;
  isThinking: boolean;
  status: 'online' | 'offline' | 'busy';
  latency: number;
  mode: string;
  wsError: string | null;
}

export const InteractionCard: React.FC<InteractionCardProps> = ({
  messages,
  inputValue,
  setInputValue,
  onSendMessage,
  isThinking,
  status,
  latency,
  mode,
  wsError
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isThinking]);

  return (
    <div className="w-[440px] max-h-[600px] flex flex-col glass bg-black/10 backdrop-blur-2xl border border-white/10 shadow-2xl overflow-hidden transition-all pointer-events-auto group">
      {/* Dynamic Border Glow */}
      <div className="absolute inset-0 border border-cyan-500/0 group-hover:border-cyan-500/20 transition-all pointer-events-none" />
      
      {/* Top Header - Telemetry */}
      <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className={`w-2 h-2 rounded-full ${status === 'online' ? 'bg-cyan-400' : status === 'busy' ? 'bg-yellow-500' : 'bg-red-500'} relative z-10`} />
            {status === 'online' && <div className="absolute inset-0 w-2 h-2 rounded-full bg-cyan-400 animate-ping opacity-75" />}
          </div>
          <div className="flex flex-col">
            <span className="text-[9px] font-mono leading-none tracking-[0.2em] text-white/40 uppercase">System_Link</span>
            <span className="text-[11px] font-mono font-bold tracking-widest text-cyan-400 uppercase">{status}</span>
          </div>
        </div>
        
        <div className="flex gap-6">
          <div className="flex flex-col items-end">
            <span className="text-[8px] font-mono text-white/20 uppercase tracking-tighter">Latency</span>
            <span className="text-[10px] font-mono text-white/60">{latency}ms</span>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-[8px] font-mono text-white/20 uppercase tracking-tighter">Mode</span>
            <span className="text-[10px] font-mono text-cyan-500/80">{mode}</span>
          </div>
        </div>
      </div>

      {/* Messages Feed */}
      <div 
        ref={scrollRef}
        className="flex-1 p-5 overflow-y-auto space-y-5 min-h-[320px] max-h-[420px] custom-scrollbar"
      >
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-white/10 py-12">
            <Activity className="w-10 h-10 mb-4 opacity-20" />
            <p className="text-[10px] font-mono uppercase tracking-[0.3em] text-center max-w-[200px] leading-relaxed">
              Neural_Link_Established.<br/>Awaiting_Input_Sequence...
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} {...msg} />
          ))
        )}
        {isThinking && (
          <div className="pt-2">
            <ThinkingIndicator />
          </div>
        )}
      </div>

      {/* System Alerts */}
      {wsError && (
        <div className="mx-5 mb-4 p-2 bg-red-500/10 border border-red-500/20 rounded text-[9px] font-mono text-red-400 uppercase tracking-widest text-center animate-pulse">
          Critical_Error: {wsError}
        </div>
      )}

      {/* Control Input */}
      <div className="p-5 pt-0 bg-gradient-to-t from-black/20 to-transparent">
        <div className="relative group/input">
          <input 
            type="text" 
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onSendMessage()}
            disabled={status !== 'online'}
            placeholder="ENTER COMMAND..."
            className="w-full bg-white/[0.03] border border-white/10 rounded-lg py-4 px-5 pr-24 text-[11px] font-mono text-white placeholder:text-white/10 focus:outline-none focus:border-cyan-500/40 focus:bg-white/[0.05] transition-all"
          />
          
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
            <button className="p-2 text-white/20 hover:text-cyan-400 transition-colors">
              <Mic className="w-4 h-4" />
            </button>
            <div className="w-px h-4 bg-white/10 mx-1" />
            <button 
              onClick={onSendMessage}
              disabled={!inputValue.trim() || status !== 'online'}
              className="p-2.5 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-md hover:bg-cyan-500/20 hover:border-cyan-500/40 transition-all active:scale-95 disabled:opacity-10"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        {/* Sub-Actions Toolbar */}
        <div className="flex items-center justify-between mt-5 px-1">
          <div className="flex gap-5">
            <button className="flex items-center gap-2 text-[9px] font-mono text-white/30 hover:text-cyan-400 uppercase tracking-[0.2em] transition-colors">
              <Database className="w-3 h-3" /> Memory
            </button>
            <button className="flex items-center gap-2 text-[9px] font-mono text-white/30 hover:text-cyan-400 uppercase tracking-[0.2em] transition-colors">
              <Activity className="w-3 h-3" /> Status
            </button>
          </div>
          <button className="text-[8px] font-mono text-white/10 hover:text-white/30 uppercase tracking-widest">
            Log_v3.2.0
          </button>
        </div>
      </div>
    </div>
  );
};
