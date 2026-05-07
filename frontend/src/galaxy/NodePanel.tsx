import React from 'react';
import type { CelestialBodyConfig } from './bodies';

interface NodePanelProps {
  node: CelestialBodyConfig | null;
  onClose: () => void;
}

/**
 * NodePanel: Painel lateral com detalhes e métricas de um componente específico.
 */
export const NodePanel: React.FC<NodePanelProps> = ({ node, onClose }) => {
  if (!node) return null;

  return (
    <div className="absolute right-0 top-0 h-full w-80 bg-black/80 border-l border-cyan-900/50 backdrop-blur-md z-20 p-6 text-cyan-100 flex flex-col transform transition-transform duration-300">
      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-cyan-400 uppercase">{node.name}</h2>
          <p className="text-[10px] opacity-50 tracking-widest">{node.type.toUpperCase()} COMPONENT</p>
        </div>
        <button 
          onClick={onClose}
          className="text-cyan-600 hover:text-cyan-400 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Metrics Section */}
      <div className="space-y-6 flex-grow">
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="opacity-60">COMPLEXIDADE</span>
            <span>{Math.round(node.complexity * 100)}%</span>
          </div>
          <div className="w-full h-1 bg-cyan-900 overflow-hidden">
            <div 
              className="h-full bg-cyan-400 shadow-[0_0_10px_#22d3ee]" 
              style={{ width: `${node.complexity * 100}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-cyan-900/30">
          <div className="space-y-1">
            <p className="text-[10px] opacity-50 uppercase">Requisições</p>
            <p className="text-lg font-semibold">1,240</p>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] opacity-50 uppercase">Sucesso</p>
            <p className="text-lg font-semibold text-green-400">99.2%</p>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] opacity-50 uppercase">Latência p50</p>
            <p className="text-lg font-semibold">12ms</p>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] opacity-50 uppercase">Latência p99</p>
            <p className="text-lg font-semibold">145ms</p>
          </div>
        </div>

        <div className="space-y-2 pt-4 border-t border-cyan-900/30">
          <p className="text-[10px] opacity-50 uppercase">Descrição</p>
          <p className="text-sm leading-relaxed opacity-80 italic">
            Componente ativo do sistema orquestrado pelo núcleo AEGIS. 
            Responsável pelo processamento de dados e execução de ferramentas em regime determinístico.
          </p>
        </div>
      </div>

      {/* Footer / Status */}
      <div className="mt-auto pt-6 border-t border-cyan-900/30 flex items-center space-x-2">
        <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
        <span className="text-[10px] tracking-widest opacity-60 uppercase font-bold">Orbital Sync: Estável</span>
      </div>
    </div>
  );
};
