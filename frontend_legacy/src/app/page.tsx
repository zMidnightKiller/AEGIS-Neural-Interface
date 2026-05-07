"use client";

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Cpu, 
  Database, 
  Settings, 
  Terminal, 
  Activity, 
  Mic, 
  Layers,
  ChevronRight,
  User,
  Bot
} from 'lucide-react';
import dynamic from 'next/dynamic';
const KnowledgeGraph = dynamic(() => import('./components/KnowledgeGraph'), { ssr: false });

export default function HelenChat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Sistemas ativos. Conexão com a rede neural RichNeeGas estabelecida. Estou monitorando os mercados para você, senhor. Como podemos evoluir nossa estratégia hoje?' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [radarActive, setRadarActive] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    // Simulação de chamada para a API FastAPI (localhost:8000/chat)
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      });
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      // Mock se a API não estiver rodando
      setTimeout(() => {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: `Simulação de processamento. Recebi: "${input}". A API local não foi detectada, mas os sistemas de interface estão operacionais.` 
        }]);
        setIsTyping(false);
      }, 1500);
      return;
    }
    setIsTyping(false);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await sendVoiceData(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Erro ao acessar microfone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendVoiceData = async (blob: Blob) => {
    setIsTyping(true);
    const formData = new FormData();
    formData.append('file', blob, 'recording.wav');

    try {
      const response = await fetch('http://localhost:8000/voice/chat', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      
      setMessages(prev => [...prev, 
        { role: 'user', content: data.text || 'Transcrição de áudio...' },
        { role: 'assistant', content: data.text ? data.text : 'Processando voz...' }
      ]);

      if (data.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${data.audio_base64}`);
        audio.play();
      }
    } catch (error) {
      console.error('Erro no processamento de voz:', error);
    }
    setIsTyping(false);
  };

  return (
    <main className="flex h-screen w-full bg-[#050505] overflow-hidden text-[#e0e1dd] p-4 gap-4 relative">
      <div className="noise" />
      <div className="hud-grid absolute inset-0 pointer-events-none" />
      
      {/* Partículas flutuantes de fundo - OTIMIZADO PARA HARDWARE */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ y: '110vh', x: `${Math.random() * 100}vw`, opacity: 0 }}
            animate={{ 
              y: '-10vh', 
              opacity: [0, 0.3, 0],
              scale: [1, 1.2, 1]
            }}
            transition={{ 
              duration: 10 + Math.random() * 20, 
              repeat: Infinity,
              delay: Math.random() * 20
            }}
            className="absolute w-1 h-1 bg-cyan-400 rounded-full blur-[1px]"
          />
        ))}
      </div>
      
      {/* Sidebar Esquerda - Status & Memória */}
      <motion.aside 
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="w-80 flex flex-col gap-4"
      >
        <div className="glass p-4 rounded-lg flex-1 flex flex-col gap-6">
          <div className="flex items-center gap-2 border-b border-cyan-500/30 pb-2">
            <Cpu className="text-cyan-400 w-5 h-5 animate-pulse" />
            <h2 className="font-bold tracking-widest text-cyan-400 glow-text uppercase text-sm">Status do Sistema</h2>
          </div>
          
          <div className="space-y-4">
            <StatusItem icon={<Activity className="w-4 h-4" />} label="Core Engine" value="Operacional" color="text-emerald-400" />
            <StatusItem icon={<Database className="w-4 h-4" />} label="RichNeeGas Link" value="Sincronizado" color="text-cyan-400" />
            <StatusItem icon={<Layers className="w-4 h-4" />} label="Modo" value="ESTRATÉGICO" />
            <StatusItem icon={<Activity className="w-4 h-4" />} label="Análise Volatilidade" value="Baixa" color="text-cyan-400" />
          </div>

          <div className="mt-auto">
            <div className="text-[10px] text-cyan-500/50 mb-2 font-mono uppercase tracking-widest">Protocolos de Inteligência</div>
            <div className="flex flex-wrap gap-2">
              <AgentBadge name="Sentimento" active />
              <AgentBadge name="Risco" active />
              <AgentBadge name="Trade" />
              <AgentBadge name="Memória" active />
            </div>
          </div>
        </div>

        <div className="glass p-4 rounded-lg h-2/5 flex flex-col relative overflow-hidden">
          <div className="flex items-center gap-2 mb-4 z-10">
            <Cpu className="text-cyan-400 w-4 h-4 animate-pulse" />
            <h3 className="text-xs font-mono uppercase text-cyan-500/70 tracking-tighter">Knowledge Neural Network</h3>
          </div>
          
          <div className="flex-1 relative">
            <KnowledgeGraph />
          </div>

          <div className="mt-2 flex justify-between text-[7px] font-mono text-cyan-500/30 uppercase tracking-tighter z-10">
            <span>Nodes: Active</span>
            <span>Sync: Real-time</span>
          </div>
        </div>

        <div className="glass p-4 rounded-lg h-1/4"></div>
      </motion.aside>

      {/* Área Central - Chat */}
      <section className="flex-1 flex flex-col glass rounded-lg overflow-hidden border border-cyan-500/20">
        {/* Header */}
        <header className="p-4 border-b border-cyan-500/20 flex justify-between items-center bg-cyan-900/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full border border-cyan-400 flex items-center justify-center bg-cyan-400/10 shadow-[0_0_10px_rgba(0,229,255,0.3)]">
              <span className="text-cyan-400 font-bold text-lg">H</span>
            </div>
            <div>
              <h1 className="font-bold tracking-tight text-white glow-text">HELEN</h1>
              <p className="text-[10px] text-cyan-400/60 uppercase tracking-widest font-mono">General Intelligence System</p>
            </div>
          </div>
          <div className="flex gap-4">
            <button className="p-2 hover:bg-cyan-400/10 rounded-full transition-colors"><Settings className="w-5 h-5 text-cyan-400/50" /></button>
          </div>
        </header>

        {/* Messages Container */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide"
        >
          {messages.map((msg, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-indigo-500/20 border border-indigo-500/30' : 'bg-cyan-500/20 border border-cyan-500/30'}`}>
                  {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4 text-cyan-400" />}
                </div>
                <div className={`p-4 rounded-2xl text-sm leading-relaxed ${msg.role === 'user' ? 'bg-surface/60 rounded-tr-none' : 'bg-surface/30 rounded-tl-none border border-cyan-500/10'}`}>
                  {msg.content}
                </div>
              </div>
            </motion.div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-surface/30 p-4 rounded-2xl rounded-tl-none animate-pulse flex gap-1">
                <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full" />
                <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full" />
                <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full" />
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <footer className="p-6 bg-cyan-900/5 border-t border-cyan-500/10">
          <div className="relative flex items-center gap-3">
            <button 
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              className={`p-3 glass rounded-xl transition-all ${isRecording ? 'bg-red-500/20 text-red-500 border-red-500/50' : 'text-cyan-500/50 hover:text-cyan-400 hover:bg-cyan-400/10'}`}
            >
              <Mic className={`w-5 h-5 ${isRecording ? 'animate-pulse' : ''}`} />
            </button>
            <div className="flex-1 relative">
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Enviar comando para HELEN..."
                className="w-full bg-surface/50 border border-cyan-500/20 rounded-xl px-5 py-3 outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 transition-all text-sm"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-2">
                <kbd className="hidden sm:inline-block px-1.5 py-0.5 rounded border border-cyan-500/30 text-[10px] text-cyan-500/50 font-mono">ENTER</kbd>
              </div>
            </div>
            <button 
              onClick={handleSend}
              className="p-3 bg-cyan-500 hover:bg-cyan-400 text-black rounded-xl transition-all shadow-[0_0_15px_rgba(0,229,255,0.4)]"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <div className="mt-4 flex justify-center gap-6 text-[10px] font-mono text-cyan-500/40 uppercase tracking-[0.2em]">
            <span>Neural Link: Active</span>
            <span>Identity: Established</span>
            <span>Protocol: Secure</span>
          </div>
        </footer>
      </section>

    </main>
  );
}

function StatusItem({ icon, label, value, color = "text-cyan-400" }: any) {
  return (
    <div className="flex justify-between items-center group">
      <div className="flex items-center gap-2 text-xs text-cyan-100/50 font-mono uppercase">
        {icon}
        <span>{label}</span>
      </div>
      <div className={`text-xs font-bold uppercase tracking-wider ${color} flex items-center gap-1`}>
        {value}
        <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </div>
  );
}

function AgentBadge({ name, active = false }: any) {
  return (
    <div className={`px-3 py-1 rounded-md text-[9px] font-mono uppercase border transition-all duration-300 ${
      active 
        ? 'border-cyan-400/50 text-cyan-400 bg-cyan-400/10 shadow-[0_0_10px_rgba(0,229,255,0.15)]' 
        : 'border-white/5 text-white/20'
    }`}>
      {name}
    </div>
  );
}
