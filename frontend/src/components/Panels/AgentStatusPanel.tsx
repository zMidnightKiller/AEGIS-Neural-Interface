import React, { useState, useEffect } from 'react';
import { Activity, Shield, Zap, CheckCircle2 } from 'lucide-react';

interface AgentStatus {
  name: string;
  description: string;
  status: string;
}

const AgentStatusPanel: React.FC = () => {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8080/agents/status')
      .then(res => res.json())
      .then(data => {
        setAgents(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch agents:', err);
        setLoading(false);
      });
  }, []);

  return (
    <section className="glass rounded-lg p-4 border-l-2 border-primary/50">
      <h2 className="text-[10px] uppercase tracking-[0.2em] text-white/40 mb-4 flex items-center gap-2">
        <Activity className="w-3 h-3 text-primary" /> Active Agents
      </h2>
      
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center gap-2 text-[10px] text-white/40 animate-pulse">
            <Zap className="w-3 h-3" /> INITIALIZING AGENTS...
          </div>
        ) : (
          agents.map((agent) => (
            <div key={agent.name} className="space-y-1 group">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  <Shield className="w-3 h-3 text-primary opacity-60" />
                  <span className="text-[10px] font-bold uppercase tracking-wider text-white/80 group-hover:text-primary transition-colors">
                    {agent.name}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                   <div className={`w-1.5 h-1.5 rounded-full ${agent.status === 'ready' ? 'bg-primary' : 'bg-accent'} pulse-glow`} />
                   <span className="text-[8px] text-white/40 uppercase font-mono">{agent.status}</span>
                </div>
              </div>
              <p className="text-[9px] text-white/50 leading-relaxed pl-5 italic">
                {agent.description}
              </p>
              <div className="h-[1px] w-full bg-white/5 mt-2" />
            </div>
          ))
        )}
      </div>

      <div className="mt-4 pt-2 border-t border-white/5">
        <div className="flex items-center gap-2 text-[9px] text-primary/60">
          <CheckCircle2 className="w-3 h-3" />
          <span className="uppercase tracking-tighter">All systems operational</span>
        </div>
      </div>
    </section>
  );
};

export default AgentStatusPanel;
