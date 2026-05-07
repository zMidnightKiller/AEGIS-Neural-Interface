import React, { useRef, useEffect } from 'react';
import { Send, Mic, Activity, Terminal, Database, Search } from 'lucide-react';
import MessageBubble from './MessageBubble';
import ThinkingIndicator from './ThinkingIndicator';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface InteractionCardProps {
  messages: Message[];
  inputValue: string;
  setInputValue: (val: string) => void;
  onSendMessage: () => void;
  isThinking: boolean;
  status: 'online' | 'offline' | 'connecting';
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
    <div className="w-[420px] max-h-[600px] flex flex-col glass border-cyan-500/30 bg-black/40 backdrop-blur-xl rounded-none border-l-2 border-t-2 shadow-[0_0_50px_rgba(0,0,0,0.5)] overflow-hidden transition-all pointer-events-auto">
      {/* Top Telemetry Bar */}
      <div className="p-3 border-b border-white/10 flex items-center justify-between bg-cyan-500/5">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${status === 'online' ? 'bg-cyan-400 animate-pulse' : 'bg-red-500'}`} />
          <span className="text-[10px] font-mono tracking-[0.2em] text-cyan-400/80 uppercase">
            LINK_{status.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center gap-4 text-[9px] font-mono text-white/40 uppercase">
          <span>LATENCY: {latency}MS</span>
          <span className="text-cyan-400/60">MODE: {mode}</span>
        </div>
      </div>

      {/* Messages Area */}
      <div 
        ref={scrollRef}
        className="flex-1 p-4 overflow-y-auto space-y-4 min-h-[300px] max-h-[400px] custom-scrollbar bg-gradient-to-b from-transparent to-cyan-500/5"
      >
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-white/20 space-y-2 opacity-50">
            <Terminal className="w-8 h-8 mb-2" />
            <p className="text-[10px] font-mono uppercase tracking-widest text-center">
              Aguardando diretiva...<br/>Inicie comunicação neural
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} {...msg} />
          ))
        )}
        {isThinking && <ThinkingIndicator />}
      </div>

      {/* Error Alert */}
      {wsError && (
        <div className="px-4 py-1 bg-red-500/20 border-y border-red-500/30 text-red-400 text-[9px] uppercase tracking-tighter text-center animate-pulse">
          SISTEMA_CRITICAL: {wsError}
        </div>
      )}

      {/* Input Section */}
      <div className="p-4 bg-black/60 border-t border-cyan-500/20">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <input 
              type="text" 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && onSendMessage()}
              disabled={status !== 'online'}
              placeholder="Digite um comando..."
              className="w-full bg-cyan-500/5 border border-cyan-500/20 rounded-none py-3 px-4 text-xs font-mono text-cyan-100 placeholder:text-cyan-500/30 focus:outline-none focus:border-cyan-400/50 transition-all focus:bg-cyan-500/10"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
              <button className="p-1.5 text-cyan-500/50 hover:text-cyan-400 transition-colors">
                <Mic className="w-4 h-4" />
              </button>
            </div>
          </div>
          <button 
            onClick={onSendMessage}
            disabled={!inputValue.trim() || status !== 'online'}
            className="p-3 bg-cyan-500/20 border border-cyan-500/40 text-cyan-400 hover:bg-cyan-500/30 hover:border-cyan-400 transition-all active:scale-95 disabled:opacity-30 disabled:pointer-events-none shadow-[0_0_15px_rgba(34,211,238,0.1)]"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        
        {/* Quick Tools */}
        <div className="flex items-center gap-4 mt-4 px-1">
          <button className="flex items-center gap-2 text-[9px] font-mono text-cyan-500/60 hover:text-cyan-400 uppercase tracking-widest transition-colors">
            <Database className="w-3 h-3" /> Memória
          </button>
          <button className="flex items-center gap-2 text-[9px] font-mono text-cyan-500/60 hover:text-cyan-400 uppercase tracking-widest transition-colors">
            <Activity className="w-3 h-3" /> Status
          </button>
          <button className="flex items-center gap-2 text-[9px] font-mono text-cyan-500/60 hover:text-cyan-400 uppercase tracking-widest transition-colors">
            <Search className="w-3 h-3" /> Log
          </button>
        </div>
      </div>
    </div>
  );
};
