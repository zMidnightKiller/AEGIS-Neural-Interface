"use client";

import React, { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 300, height: 300 });

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const response = await fetch('http://localhost:8000/memory/graph');
        const data = await response.json();
        // Adicionar complexidade aleatória se não vier do backend para efeito visual de "Espaço"
        const enhancedNodes = data.nodes.map((n: any) => ({
          ...n,
          val: n.val || Math.floor(Math.random() * 60) + 5, // Nível de complexidade
          type: n.val > 50 ? 'galaxy' : n.val > 30 ? 'star' : n.val > 15 ? 'planet' : 'asteroid'
        }));
        setGraphData({ nodes: enhancedNodes, links: data.links });
      } catch (error) {
        console.error("Erro ao carregar o grafo:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
    const interval = setInterval(fetchGraph, 10000);

    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight
      });
    }

    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="text-cyan-500/50 text-[10px] animate-pulse">Iniciando Telescópio Neural...</div>;

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden bg-[radial-gradient(ellipse_at_center,_#0a1929_0%,_#050505_100%)]">
      {/* Starfield Background */}
      <div className="absolute inset-0 opacity-30 pointer-events-none" 
           style={{ backgroundImage: 'radial-gradient(white 1px, transparent 1px)', backgroundSize: '100px 100px' }} />
      
      <ForceGraph2D
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        backgroundColor="rgba(0,0,0,0)"
        nodeLabel={(node: any) => `${node.id} (${node.type.toUpperCase()})`}
        nodeColor={(node: any) => {
          if (node.type === 'galaxy') return '#d000ff';
          if (node.type === 'star') return '#ffea00';
          if (node.type === 'planet') return '#00e5ff';
          return '#415a77';
        }}
        linkColor={() => 'rgba(255, 255, 255, 0.1)'}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.002}
        nodeCanvasObject={(node: any, ctx, globalScale) => {
          if (!node.x || !node.y || isNaN(node.x) || isNaN(node.y)) return;
          
          const size = Math.sqrt(Math.max(1, node.val || 1)) * 1.5;
          const label = node.id;
          const fontSize = 10 / globalScale;
          
          // Desenhar o objeto celestial
          ctx.beginPath();
          ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
          
          let gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, size);
          
          if (node.type === 'galaxy') {
            gradient.addColorStop(0, '#d000ff');
            gradient.addColorStop(1, 'rgba(208, 0, 255, 0)');
            ctx.shadowColor = '#d000ff';
            ctx.shadowBlur = 15;
          } else if (node.type === 'star') {
            gradient.addColorStop(0, '#ffea00');
            gradient.addColorStop(0.8, '#ff9100');
            gradient.addColorStop(1, 'transparent');
            ctx.shadowColor = '#ffea00';
            ctx.shadowBlur = 20;
          } else if (node.type === 'planet') {
            gradient.addColorStop(0, '#00e5ff');
            gradient.addColorStop(1, '#004d40');
            ctx.shadowColor = '#00e5ff';
            ctx.shadowBlur = 5;
          } else {
            gradient.addColorStop(0, '#415a77');
            gradient.addColorStop(1, '#0d1b2a');
          }
          
          ctx.fillStyle = gradient;
          ctx.fill();
          
          // Anéis para planetas
          if (node.type === 'planet') {
            ctx.beginPath();
            ctx.ellipse(node.x, node.y, size * 1.8, size * 0.5, Math.PI / 4, 0, 2 * Math.PI);
            ctx.strokeStyle = 'rgba(0, 229, 255, 0.2)';
            ctx.stroke();
          }

          // Rastro de galáxia
          if (node.type === 'galaxy') {
            ctx.beginPath();
            ctx.arc(node.x, node.y, size * 2.5, 0, 2 * Math.PI);
            ctx.strokeStyle = 'rgba(208, 0, 255, 0.1)';
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.setLineDash([]);
          }

          // Texto
          ctx.font = `${fontSize}px 'Inter', sans-serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
          ctx.fillText(label, node.x, node.y + size + 10);
          
          // Reset shadow
          ctx.shadowBlur = 0;
        }}
      />
    </div>
  );
}
