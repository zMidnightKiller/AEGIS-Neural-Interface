import React, { useEffect, useRef, useState } from 'react';
import { GalaxyEngine } from './engine';
import { HUD } from './hud';
import { NodePanel } from './NodePanel';
import type { NeuralNodeConfig } from './bodies';

interface GalaxyViewProps {
  onModeChange?: (mode: string) => void;
}

/**
 * GalaxyView: Componente React que renderiza o canvas Three.js da Rede Neural Cósmica.
 */
const GalaxyView: React.FC<GalaxyViewProps> = ({ onModeChange }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const engineRef = useRef<GalaxyEngine | null>(null);
  
  // States para UI
  const [hoveredNode, setHoveredNode] = useState<NeuralNodeConfig | null>(null);
  const [selectedNode, setSelectedNode] = useState<NeuralNodeConfig | null>(null);
  const [metrics, setMetrics] = useState({
    mode: 'Standard',
    activeNodes: 11,
    latency: 18,
    status: 'ONLINE' as const
  });

  useEffect(() => {
    if (containerRef.current) {
      engineRef.current = new GalaxyEngine(containerRef.current);
      
      // Configurar Callbacks da Engine
      engineRef.current.onNodeHover = (node) => setHoveredNode(node);
      engineRef.current.onNodeClick = (node) => setSelectedNode(node);
      engineRef.current.onBlackHoleClick = () => {
        setSelectedNode({
          name: 'AEGIS Neural Core (Gargantua)',
          type: 'core',
          complexity: 1.0,
          position: new (window as any).THREE.Vector3(0, 0, 0),
          radius: 35,
          color: 0xffaa44
        } as any);
      };

      engineRef.current.start();
    }

    const handleAegisEvent = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (engineRef.current) {
        engineRef.current.emit(customEvent.detail);
      }
    };

    window.addEventListener('aegis-event', handleAegisEvent);

    return () => {
      engineRef.current?.dispose();
      window.removeEventListener('aegis-event', handleAegisEvent);
    };
  }, []);

  return (
    <div className="relative w-full h-full overflow-hidden bg-black">
      {/* Canvas Container */}
      <div 
        ref={containerRef} 
        className="absolute inset-0 z-0 cursor-crosshair"
      />

      {/* HUD Overlay */}
      <HUD 
        mode={metrics.mode}
        activeNodes={metrics.activeNodes}
        latency={metrics.latency}
        status={metrics.status}
      />

      {/* Tooltip on Hover */}
      {hoveredNode && !selectedNode && (
        <div 
          className="absolute pointer-events-none bg-black/60 border border-cyan-500/30 backdrop-blur-sm p-2 px-3 rounded text-[10px] text-cyan-400 font-mono z-30 uppercase tracking-tighter shadow-[0_0_15px_rgba(34,211,238,0.2)]"
          style={{ 
            left: '50%', 
            top: '20%', 
            transform: 'translate(-50%, -50%)' 
          }}
        >
          {hoveredNode.name} | INTEGRIDADE: {Math.round(hoveredNode.complexity * 100)}%
        </div>
      )}

      {/* Side Panel for Selected Node */}
      <NodePanel 
        node={selectedNode} 
        onClose={() => setSelectedNode(null)} 
      />

      {/* Floating Mode Button */}
      <div className="absolute bottom-8 right-8 z-30">
        <button 
          className="bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 p-3 px-6 rounded-full text-cyan-400 font-mono text-xs tracking-widest transition-all hover:scale-105 active:scale-95 flex items-center space-x-3 group backdrop-blur-md"
          onClick={() => {
            const modes = ['STANDARD', 'SILENT', 'ANALYSIS'];
            const currentIndex = modes.indexOf(metrics.mode.toUpperCase());
            const nextMode = modes[(currentIndex + 1) % modes.length];
            setMetrics(prev => ({ ...prev, mode: nextMode }));
            if (engineRef.current) {
              engineRef.current.setMode(nextMode);
            }
            if (onModeChange) {
              onModeChange(nextMode);
            }
          }}
        >
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="group-hover:text-white transition-colors">/SISTEMA: {metrics.mode.toUpperCase()}</span>
        </button>
      </div>
    </div>
  );
};

export default GalaxyView;
