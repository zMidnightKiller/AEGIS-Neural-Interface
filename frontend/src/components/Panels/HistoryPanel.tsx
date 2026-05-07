import React, { useState, useEffect } from 'react';
import { History, Clock, FileText, ChevronRight } from 'lucide-react';

interface Episode {
  id: string;
  content: string;
  metadata: any;
}

const HistoryPanel: React.FC = () => {
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8080/memory/episodes?n=5')
      .then(res => res.json())
      .then(data => {
        setEpisodes(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch history:', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="flex flex-col h-full space-y-4">
      <section className="glass rounded-lg p-4 border-l-2 border-accent/50 flex-1 overflow-hidden flex flex-col">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-white/40 mb-4 flex items-center gap-2">
          <History className="w-3 h-3 text-accent" /> Episodic Log (History)
        </h2>
        
        <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 space-y-3">
          {loading ? (
            <div className="text-[10px] text-white/40 font-mono animate-pulse">RETRIEVING EPISODES...</div>
          ) : episodes.length > 0 ? (
            episodes.map((ep) => (
              <div key={ep.id} className="p-2 rounded bg-white/5 border border-white/5 hover:bg-white/10 transition-colors cursor-help group relative">
                <div className="flex items-center justify-between mb-1">
                   <div className="flex items-center gap-1.5 text-accent opacity-60">
                      <Clock className="w-2.5 h-2.5" />
                      <span className="text-[8px] font-mono uppercase">
                        {ep.metadata?.timestamp ? new Date(ep.metadata.timestamp * 1000).toLocaleTimeString() : 'RECENT'}
                      </span>
                   </div>
                   <ChevronRight className="w-2.5 h-2.5 text-white/20 group-hover:text-accent transition-colors" />
                </div>
                <p className="text-[10px] text-white/70 line-clamp-2 leading-relaxed">
                  {ep.content}
                </p>
                
                {/* Tooltip on hover (simplified) */}
                <div className="absolute left-full ml-2 top-0 w-48 p-2 glass border border-accent/30 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 text-[9px] text-white/80 leading-snug shadow-2xl hidden lg:block">
                  <div className="flex items-center gap-1 mb-1 text-accent">
                    <FileText className="w-3 h-3" />
                    <span className="font-bold">FULL RECORD</span>
                  </div>
                  {ep.content.substring(0, 150)}...
                </div>
              </div>
            ))
          ) : (
            <div className="text-[10px] text-white/30 italic">Nenhum histórico disponível nesta unidade.</div>
          )}
        </div>
      </section>

      <section className="glass rounded-lg p-3 bg-accent/5 border border-accent/10">
        <div className="flex justify-between items-center text-[8px] font-mono text-accent/80 uppercase tracking-widest">
            <span>Storage: 42%</span>
            <span>Index: OK</span>
        </div>
        <div className="h-1 bg-white/5 rounded-full mt-2 overflow-hidden">
            <div className="h-full bg-accent w-[42%] opacity-50" />
        </div>
      </section>
    </div>
  );
};

export default HistoryPanel;
