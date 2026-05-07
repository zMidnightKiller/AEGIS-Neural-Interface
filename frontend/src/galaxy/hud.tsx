import React from 'react';

interface HUDProps {
  mode: string;
  activeNodes: number;
  latency: number;
  status: 'ONLINE' | 'OFFLINE' | 'BUSY';
}

/**
 * HUD: Overlay com métricas globais do sistema.
 */
export const HUD: React.FC<HUDProps> = ({ mode, activeNodes, latency, status }) => {
  return (
    <div className="absolute inset-0 pointer-events-none z-10 p-6 font-mono text-cyan-400 select-none">
      {/* Top Left: System Metrics */}
      <div className="absolute top-6 left-6 space-y-1">
        <div className="flex items-center space-x-2">
          <span className="text-xs opacity-50">MODO:</span>
          <span className="text-sm font-bold tracking-widest">{mode.toUpperCase()}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs opacity-50">NÓS ATIVOS:</span>
          <span className="text-sm">{activeNodes}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs opacity-50">LATÊNCIA MÉDIA:</span>
          <span className="text-sm">{latency}ms</span>
        </div>
        <div className="mt-2 w-32 h-px bg-cyan-900 overflow-hidden relative">
          <div className="absolute inset-0 bg-cyan-400 opacity-30 animate-pulse" />
        </div>
      </div>

      {/* Top Right: Status & Gravity */}
      <div className="absolute top-6 right-6 text-right space-y-1">
        <div className="flex items-center justify-end space-x-2">
          <span className="text-sm font-bold tracking-tighter">GRAVIDADE ∞</span>
          <div className={`w-2 h-2 rounded-full ${status === 'ONLINE' ? 'bg-cyan-400 animate-pulse' : 'bg-red-500'}`} />
        </div>
        <div className="text-xs opacity-50 uppercase">Órbitas: Estáveis</div>
        <div className="text-xs opacity-50 uppercase">Status: {status}</div>
      </div>

      {/* Scanline Effect Overlay (CSS Only) */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_2px,3px_100%]" />
    </div>
  );
};
