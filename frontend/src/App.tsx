import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Cpu, Database, Activity, Search, Send, User } from 'lucide-react';
import MessageBubble from './components/MessageBubble';
import ThinkingIndicator from './components/ThinkingIndicator';
import AgentStatusPanel from './components/Panels/AgentStatusPanel';
import HistoryPanel from './components/Panels/HistoryPanel';
import GalaxyView from './galaxy/GalaxyView';

interface Message {
  id: string;
  role: 'user' | 'aegis';
  content: string;
  timestamp: string;
  agentUsed?: string;
  latencyMs?: number;
}

const SESSION_ID = Math.random().toString(36).substring(7);
const WS_URL = `ws://localhost:8000/ws/${SESSION_ID}`;

/**
 * Interface de Chat - Componente Principal AEGIS.
 */
const App: React.FC = () => {
  const [status, setStatus] = useState<'online' | 'busy' | 'offline'>('offline');
  const [latency, setLatency] = useState(0);
  const [activeTab, setActiveTab] = useState<'console' | 'memory' | 'research'>('console');
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  const [mode, setMode] = useState<'STANDARD' | 'SILENT' | 'ANALYSIS' | 'BRIEFING' | 'VERBOSE'>('STANDARD');
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'aegis',
      content: 'Sistemas inicializados. Sou o AEGIS. Interface HUD configurada e pronta para operações.',
      timestamp: new Date().toLocaleTimeString(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [wsError, setWsError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      socketRef.current?.close();
    };
  }, []);

  const connectWebSocket = () => {
    try {
      const socket = new WebSocket(WS_URL);
      socketRef.current = socket;

      socket.onopen = () => {
        setStatus('online');
        setWsError(null);
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'status' && data.status === 'thinking') {
          setIsThinking(true);
          window.dispatchEvent(new CustomEvent('aegis-event', { detail: { event_type: 'thinking', data: {} } }));
        } else if (data.type === 'event') {
          window.dispatchEvent(new CustomEvent('aegis-event', { detail: data }));
        } else if (data.type === 'message') {
          setIsThinking(false);
          const newMessage: Message = {
            id: Date.now().toString(),
            role: 'aegis',
            content: data.text,
            timestamp: new Date(data.timestamp * 1000).toLocaleTimeString(),
            agentUsed: data.agent_used,
            latencyMs: data.latency_ms,
          };
          setMessages(prev => [...prev, newMessage]);
          setLatency(data.latency_ms || 0);
        } else if (data.type === 'error') {
          setIsThinking(false);
          setWsError(data.message);
        }
      };

      socket.onclose = () => {
        setStatus('offline');
        setTimeout(connectWebSocket, 3000);
      };

      socket.onerror = () => {
        setStatus('offline');
        setWsError("Falha na conexão com o Core Engine.");
      };
    } catch (err) {
      console.error('Connection failed:', err);
      setWsError("Erro ao tentar conectar ao servidor.");
    }
  };


  const handleSendMessage = (text?: string) => {
    const messageText = text || inputValue;
    if (!messageText.trim() || status !== 'online') return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages(prev => [...prev, userMessage]);
    socketRef.current?.send(JSON.stringify({ 
      text: messageText, 
      mode: mode 
    }));
    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white flex flex-col font-sans scanline relative overflow-hidden">
      <GalaxyView onModeChange={(m: any) => setMode(m)} />
      
      <div className="absolute inset-0 flex flex-col pointer-events-none z-10">
        <header className="h-14 border-b border-white/5 glass flex items-center justify-between px-6 pointer-events-auto">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-primary/20 rounded flex items-center justify-center border border-primary/30">
              <Cpu className={`w-5 h-5 text-primary ${status === 'online' ? 'pulse-glow' : 'opacity-40'}`} />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-widest uppercase">AEGIS <span className="text-primary">CORE</span></h1>
            </div>
          </div>

          <div className="flex items-center gap-6 text-[10px] font-mono uppercase tracking-widest hidden md:flex">
            <div>STATUS: <span className={status === 'online' ? 'text-primary' : 'text-red-500'}>{status}</span></div>
            <div>LATENCY: <span className="text-primary">{latency}ms</span></div>
            <div>MODE: <span className="text-accent">{mode}</span></div>
          </div>

          <div className="flex items-center gap-4">
            <button 
              onClick={() => setShowRightSidebar(!showRightSidebar)}
              className={`p-2 rounded-full transition-colors ${showRightSidebar ? 'text-primary bg-primary/10' : 'text-white/60 hover:text-white'}`}
            >
              <Activity className="w-4 h-4" />
            </button>
            <div className="w-8 h-8 rounded-full border border-white/10 flex items-center justify-center bg-white/5">
              <User className="w-4 h-4 text-white/60" />
            </div>
          </div>
        </header>

        <main className="flex-1 flex overflow-hidden p-4 gap-4 pointer-events-none">
          <aside className="w-64 flex flex-col gap-4 hidden lg:flex pointer-events-auto">
            <AgentStatusPanel />
            <nav className="glass rounded-lg flex-1 p-2">
               <div className="space-y-1">
                  {[
                    { id: 'console', icon: <Terminal className="w-4 h-4" />, label: 'Console' },
                    { id: 'memory', icon: <Database className="w-4 h-4" />, label: 'Memory' },
                    { id: 'research', icon: <Search className="w-4 h-4" />, label: 'Research' },
                  ].map((item) => (
                    <button 
                      key={item.id} 
                      onClick={() => setActiveTab(item.id as any)}
                      className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs transition-all ${activeTab === item.id ? 'bg-primary/10 text-primary border border-primary/20' : 'text-white/60 hover:text-white'}`}
                    >
                      {item.icon}
                      <span className="tracking-wide uppercase">{item.label}</span>
                    </button>
                  ))}
               </div>
            </nav>
          </aside>

          <section className="flex-1 flex flex-col glass rounded-lg border-t border-white/10 overflow-hidden relative pointer-events-auto bg-black/20 backdrop-blur-[2px]">
            {activeTab === 'console' ? (
              <>
                <div className="flex-1 p-6 overflow-y-auto space-y-6 custom-scrollbar">
                  {messages.map((msg) => (
                    <MessageBubble key={msg.id} {...msg} />
                  ))}
                  {isThinking && <ThinkingIndicator />}
                  <div ref={messagesEndRef} />
                </div>

                {/* Error Banner */}
                {wsError && (
                  <div className="absolute top-4 left-1/2 -translate-x-1/2 glass px-4 py-2 rounded-full border border-red-500/50 text-red-500 text-[10px] uppercase tracking-widest animate-bounce z-50">
                     ERROR: {wsError}
                  </div>
                )}

                <div className="p-4 border-t border-white/5 bg-black/60">
                  <div className="relative">
                    <input 
                      type="text" 
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyDown={handleKeyPress}
                      disabled={status !== 'online'}
                      placeholder="Comando..."
                      className="w-full bg-white/5 border border-white/10 rounded-lg py-3 px-4 pr-12 text-sm focus:outline-none focus:border-primary/50"
                    />
                    <button 
                      onClick={() => handleSendMessage()}
                      disabled={!inputValue.trim() || status !== 'online'}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-primary"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-white/40 font-mono text-sm uppercase tracking-widest">
                Simulated Module
              </div>
            )}
          </section>

          {showRightSidebar && (
            <aside className="w-80 flex flex-col gap-4 hidden xl:flex pointer-events-auto">
               <HistoryPanel />
            </aside>
          )}
        </main>

        <footer className="h-6 bg-primary/10 border-t border-primary/20 px-4 flex items-center justify-between text-[9px] font-mono tracking-[0.2em] text-primary/80 pointer-events-auto">
          <span>ENCRYPTED_STREAM: ACTIVE</span>
          <span>© 2026 AEGIS COGNITIVE SYSTEMS</span>
        </footer>
      </div>
    </div>
  );
};

export default App;
