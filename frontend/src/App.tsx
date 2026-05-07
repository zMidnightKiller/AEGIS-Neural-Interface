import React, { useState, useEffect, useRef } from 'react';
import GalaxyView from './galaxy/GalaxyView';
import { InteractionCard } from './components/InteractionCard';

interface Message {
  id: string;
  role: 'user' | 'aegis';
  content: string;
  timestamp: string;
  agentUsed?: string;
  latencyMs?: number;
}

const SESSION_ID = Math.random().toString(36).substring(7);
const WS_URL = `ws://localhost:8080/ws/${SESSION_ID}`;

/**
 * Interface de Chat - Componente Principal AEGIS.
 * Layout imersivo com InteractionCard no canto inferior esquerdo.
 */
const App: React.FC = () => {
  const [status, setStatus] = useState<'online' | 'busy' | 'offline'>('offline');
  const [latency, setLatency] = useState(0);
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

  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans scanline relative overflow-hidden">
      {/* Background Neural Network */}
      <div className="fixed inset-0 z-0 w-full h-full">
        <GalaxyView onModeChange={(m: any) => setMode(m as any)} />
      </div>
      
      {/* Interface Layer */}
      <div className="relative z-10 flex flex-col h-screen pointer-events-none p-8">
        {/* Interaction Center (Bottom Left) */}
        <div className="mt-auto pointer-events-auto">
          <InteractionCard 
            messages={messages}
            inputValue={inputValue}
            setInputValue={setInputValue}
            onSendMessage={handleSendMessage}
            isThinking={isThinking}
            status={status}
            latency={latency}
            mode={mode}
            wsError={wsError}
          />
        </div>

        {/* System Labels Overlay (Top Right) */}
        <div className="absolute top-8 right-8 flex flex-col items-end space-y-1 opacity-40 pointer-events-none font-mono">
          <div className="text-[10px] tracking-[0.3em] uppercase">Neural_Interface_v3.2</div>
          <div className="text-[8px] tracking-[0.2em] text-cyan-500 uppercase">Aegis_Cognitive_Secure_Link</div>
        </div>
      </div>
    </div>
  );
};

export default App;
