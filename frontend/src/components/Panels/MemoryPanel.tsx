import React, { useState, useEffect } from 'react';
import { Database, Tag, Link2 } from 'lucide-react';

interface Preference {
  relation: string;
  entity: string;
}

const MemoryPanel: React.FC = () => {
  const [profile, setProfile] = useState<Preference[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/memory/profile')
      .then(res => res.json())
      .then(data => {
        setProfile(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch profile:', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Semantic Profile Section */}
      <section className="glass rounded-lg p-4 border-l-2 border-secondary/50">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-white/40 mb-4 flex items-center gap-2">
          <Database className="w-3 h-3 text-secondary" /> Semantic Graph (UserProfile)
        </h2>
        
        <div className="space-y-3">
          {loading ? (
             <div className="text-[10px] text-white/40 font-mono">SCANNING NEURAL NETWORK...</div>
          ) : profile.length > 0 ? (
            profile.map((pref, i) => (
              <div key={i} className="flex items-center gap-2 group">
                <Tag className="w-3 h-3 text-secondary opacity-40 group-hover:opacity-100 transition-opacity" />
                <div className="flex flex-col">
                  <span className="text-[9px] text-white/40 uppercase font-mono">{pref.relation}</span>
                  <span className="text-xs text-white/90 group-hover:text-secondary transition-colors">{pref.entity}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="text-[10px] text-white/30 italic">Nenhum fato semântico extraído até o momento.</div>
          )}
        </div>
      </section>

      {/* Memory Status Visualizer */}
      <section className="glass rounded-lg p-4 border-l-2 border-white/20 flex-1">
        <div className="flex items-center justify-between mb-4">
            <h2 className="text-[10px] uppercase tracking-[0.2em] text-white/40 flex items-center gap-2">
                <Link2 className="w-3 h-3" /> Connectivity
            </h2>
        </div>
        
        <div className="flex flex-col items-center justify-center h-40 opacity-20 relative">
            <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-32 h-32 border border-white/20 rounded-full animate-ping" />
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-20 h-20 border border-white/40 rounded-full animate-pulse" />
            </div>
            <Database className="w-8 h-8 text-white" />
            <p className="text-[8px] mt-4 font-mono uppercase tracking-widest text-center">
                Neo4j Persistent Graph<br/>Chroma Vector Store
            </p>
        </div>
      </section>
    </div>
  );
};

export default MemoryPanel;
