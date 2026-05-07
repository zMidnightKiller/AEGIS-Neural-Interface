import * as THREE from 'three';
import { NeuralNode } from './bodies';

/**
 * Interface para um efeito temporário na cena.
 */
interface VisualEffect {
  update(delta: number): boolean; // retorna false quando o efeito deve ser removido
  dispose(): void;
}

/**
 * Efeito de explosão de partículas.
 */
class ParticleExplosion implements VisualEffect {
  private points: THREE.Points;
  private velocities: THREE.Vector3[];
  private life: number = 1.0;
  private scene: THREE.Scene;

  constructor(scene: THREE.Scene, position: THREE.Vector3, color: number, count: number = 50) {
    this.scene = scene;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    this.velocities = [];

    for (let i = 0; i < count; i++) {
      positions[i * 3] = position.x;
      positions[i * 3 + 1] = position.y;
      positions[i * 3 + 2] = position.z;
      
      this.velocities.push(new THREE.Vector3(
        (Math.random() - 0.5) * 50,
        (Math.random() - 0.5) * 50,
        (Math.random() - 0.5) * 50
      ));
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      color: color,
      size: 3,
      transparent: true,
      opacity: 1.0,
      blending: THREE.AdditiveBlending
    });

    this.points = new THREE.Points(geometry, material);
    this.scene.add(this.points);
  }

  update(delta: number): boolean {
    this.life -= delta;
    if (this.life <= 0) return false;

    const positions = this.points.geometry.attributes.position.array as Float32Array;
    for (let i = 0; i < this.velocities.length; i++) {
      positions[i * 3] += this.velocities[i].x * delta;
      positions[i * 3 + 1] += this.velocities[i].y * delta;
      positions[i * 3 + 2] += this.velocities[i].z * delta;
    }
    this.points.geometry.attributes.position.needsUpdate = true;
    (this.points.material as THREE.PointsMaterial).opacity = this.life;
    
    return true;
  }

  dispose() {
    this.scene.remove(this.points);
    this.points.geometry.dispose();
    (this.points.material as THREE.Material).dispose();
  }
}

/**
 * Efeito de pulso de dados que viaja entre dois pontos.
 */
class DataPulse implements VisualEffect {
  private mesh: THREE.Mesh;
  private scene: THREE.Scene;
  private start: THREE.Vector3;
  private end: THREE.Vector3;
  private progress: number = 0;
  private speed: number;

  constructor(scene: THREE.Scene, start: THREE.Vector3, end: THREE.Vector3, color: number, speed: number = 2.0) {
    this.scene = scene;
    this.start = start.clone();
    this.end = end.clone();
    this.speed = speed;

    const geometry = new THREE.SphereGeometry(1.2, 8, 8);
    const material = new THREE.MeshBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending
    });
    this.mesh = new THREE.Mesh(geometry, material);
    this.scene.add(this.mesh);
  }

  update(delta: number): boolean {
    this.progress += delta * this.speed;
    if (this.progress >= 1.0) return false;

    this.mesh.position.lerpVectors(this.start, this.end, this.progress);
    
    // Efeito de rastro/glow
    const scale = 1.0 + Math.sin(this.progress * Math.PI) * 1.5;
    this.mesh.scale.set(scale, scale, scale);
    (this.mesh.material as THREE.MeshBasicMaterial).opacity = 1.0 - this.progress;

    return true;
  }

  dispose() {
    this.scene.remove(this.mesh);
    this.mesh.geometry.dispose();
    (this.mesh.material as THREE.Material).dispose();
  }
}

/**
 * Efeito de linha de energia animada.
 */
class EnergyLine implements VisualEffect {
  private line: THREE.Line;
  private scene: THREE.Scene;
  private life: number = 0.8;
  private start: THREE.Vector3;
  private end: THREE.Vector3 = new THREE.Vector3(0, 0, 0);

  constructor(scene: THREE.Scene, start: THREE.Vector3, color: number) {
    this.scene = scene;
    this.start = start.clone();
    const geometry = new THREE.BufferGeometry().setFromPoints([this.start, this.end]);
    const material = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending
    });
    this.line = new THREE.Line(geometry, material);
    this.scene.add(this.line);
  }

  update(delta: number): boolean {
    this.life -= delta;
    if (this.life <= 0) return false;

    const progress = 1.0 - (this.life / 0.8);
    // Move o ponto inicial em direção ao centro
    const currentStart = new THREE.Vector3().lerpVectors(this.start, this.end, progress);
    this.line.geometry.setFromPoints([currentStart, this.end]);
    (this.line.material as THREE.LineBasicMaterial).opacity = this.life / 0.8;

    return true;
  }

  dispose() {
    this.scene.remove(this.line);
    this.line.geometry.dispose();
    (this.line.material as THREE.Material).dispose();
  }
}

/**
 * GalaxyEvents: Gerencia a integração de eventos WebSocket com a visualização galáctica.
 */
export class GalaxyEvents {
  private bodies: NeuralNode[];
  private scene: THREE.Scene;
  private setBlackHoleActivity: (active: boolean) => void;
  private setVoiceState: (active: boolean, pulse: number) => void;
  private setListening: (active: boolean) => void;
  private effects: VisualEffect[] = [];

  constructor(
    scene: THREE.Scene, 
    bodies: NeuralNode[], 
    setBlackHoleActivity: (active: boolean) => void,
    setVoiceState: (active: boolean, pulse: number) => void,
    setListening: (active: boolean) => void
  ) {
    this.scene = scene;
    this.bodies = bodies;
    this.setBlackHoleActivity = setBlackHoleActivity;
    this.setVoiceState = setVoiceState;
    this.setListening = setListening;
  }

  /**
   * Atualiza as animações de efeitos.
   */
  public update(delta: number) {
    for (let i = this.effects.length - 1; i >= 0; i--) {
      if (!this.effects[i].update(delta)) {
        this.effects[i].dispose();
        this.effects.splice(i, 1);
      }
    }
  }

  /**
   * Processa um evento recebido via WebSocket.
   */
  public handleEvent(event: any) {
    const { event_type, data } = event;
    const center = new THREE.Vector3(0, 0, 0);

    switch (event_type) {
      case 'thinking':
        this.setBlackHoleActivity(true);
        // Pequenos pulsos aleatórios de todos para o centro
        this.bodies.forEach(b => {
          if (Math.random() > 0.7) {
            this.effects.push(new DataPulse(this.scene, b.mesh.position, center, 0x4444aa, 1.5));
          }
        });
        break;

      case 'voice_speaking':
        this.setVoiceState(true, data.amplitude || 0);
        this.setListening(false);
        break;

      case 'voice_finished':
        this.setVoiceState(false, 0);
        this.setListening(false);
        break;

      case 'voice_listening':
        this.setListening(true);
        this.setVoiceState(false, 0);
        break;

      case 'agent_started':
        this.triggerAgentAnimation(data.agent, true);
        const agent = this.findBody(data.agent);
        if (agent) {
          this.effects.push(new DataPulse(this.scene, center, agent.mesh.position, 0x00ffff, 1.2));
        }
        break;

      case 'agent_finished':
        this.triggerAgentAnimation(data.agent, false);
        this.triggerAgentFinishedAnimation(data.agent, data.success !== false);
        this.setBlackHoleActivity(false);
        const finishingAgent = this.findBody(data.agent);
        if (finishingAgent) {
          this.effects.push(new DataPulse(this.scene, finishingAgent.mesh.position, center, 0x00ff00, 2.0));
        }
        break;

      case 'tool_called':
        this.triggerToolAnimation(data.tool);
        const tool = this.findBody(data.tool);
        if (tool) {
          // Pulso do centro para a ferramenta
          this.effects.push(new DataPulse(this.scene, center, tool.mesh.position, 0xffff00, 2.5));
        }
        break;

      case 'memory_retrieved':
        this.triggerMemoryAnimation();
        break;

      case 'error':
        this.triggerErrorAnimation(data.agent || data.tool);
        this.setBlackHoleActivity(false);
        break;

      default:
        console.debug('Evento não tratado:', event_type);
    }
  }

  private triggerAgentAnimation(agentName: string, active: boolean) {
    const body = this.findBody(agentName);
    if (body) {
      body.setHalo(active);
      if (active) body.activatePulse();
    }
  }

  private triggerAgentFinishedAnimation(agentName: string, success: boolean) {
    const body = this.findBody(agentName);
    if (body && success) {
      this.effects.push(new ParticleExplosion(this.scene, body.mesh.position, 0x00ff00));
    }
  }

  private triggerToolAnimation(toolName: string) {
    const body = this.findBody(toolName);
    if (body) {
      body.activatePulse();
      // Linha de energia do nó até o centro
      this.effects.push(new EnergyLine(this.scene, body.mesh.position, 0x00ffff));
    }
  }

  private triggerMemoryAnimation() {
    this.bodies.forEach(body => {
      if (body.config.type === 'memory') {
        body.activatePulse();
        // Data pulse da memória para o centro
        this.effects.push(new DataPulse(this.scene, body.mesh.position, new THREE.Vector3(0,0,0), 0x4444ff, 1.8));
      }
    });
  }

  private triggerErrorAnimation(name: string) {
    const body = this.findBody(name);
    if (body) {
      body.triggerError();
      this.effects.push(new ParticleExplosion(this.scene, body.mesh.position, 0xff0000, 30));
      this.effects.push(new DataPulse(this.scene, body.mesh.position, new THREE.Vector3(0,0,0), 0xff0000, 4.0));
    }
  }

  private findBody(name: string): NeuralNode | undefined {
    if (!name) return undefined;
    
    const searchName = name.toLowerCase().replace('_', ' ');
    return this.bodies.find(b => {
      const bodyName = b.config.name.toLowerCase();
      return bodyName.includes(searchName) || searchName.includes(bodyName.split(' ')[0]);
    });
  }
}
