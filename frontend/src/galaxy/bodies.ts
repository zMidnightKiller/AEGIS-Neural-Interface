import * as THREE from 'three';

/**
 * NeuralNodeConfig: Define as propriedades de um nó na rede neural cósmica.
 */
export type NeuralNodeConfig = {
  name: string;
  radius: number;
  position: THREE.Vector3;
  color: number;
  complexity: number;
  type: 'core' | 'memory' | 'agent' | 'tool';
};

export class NeuralNode {
  public mesh: THREE.Group;
  private bodyMesh: THREE.Mesh;
  public config: NeuralNodeConfig;
  private basePosition: THREE.Vector3;
  private driftOffset: THREE.Vector3;
  private halo: THREE.Mesh | null = null;

  // Animation States
  private pulseValue: number = 0;
  private haloValue: number = 0;
  private errorFlash: number = 0;
  private originalColor: number;

  constructor(config: NeuralNodeConfig) {
    this.config = config;
    this.originalColor = config.color;
    this.mesh = new THREE.Group();
    this.basePosition = config.position.clone();
    this.driftOffset = new THREE.Vector3(
      Math.random() * 10,
      Math.random() * 10,
      Math.random() * 10
    );
    
    this.mesh.position.copy(this.basePosition);

    this.bodyMesh = this.createBodyMesh();
    this.mesh.add(this.bodyMesh);
    
    // Adicionar Label
    const label = this.createLabel(config.name);
    label.position.y = config.radius + 8;
    this.mesh.add(label);

    // Adicionar Halo
    this.halo = this.createHalo();
    this.mesh.add(this.halo);
  }

  private createHalo(): THREE.Mesh {
    const geometry = new THREE.SphereGeometry(this.config.radius * 1.8, 32, 32);
    const material = new THREE.MeshBasicMaterial({
      color: this.config.color,
      transparent: true,
      opacity: 0,
      side: THREE.BackSide
    });
    return new THREE.Mesh(geometry, material);
  }

  public activatePulse() {
    this.pulseValue = 1.0;
  }

  public setHalo(active: boolean) {
    this.haloValue = active ? 1.0 : 0.0;
  }

  public triggerError() {
    this.errorFlash = 3.0;
  }

  private createBodyMesh(): THREE.Mesh {
    const size = this.config.radius * (0.9 + this.config.complexity * 0.3);
    const geometry = new THREE.SphereGeometry(size, 24, 24);
    
    // Material brilhante como uma estrela
    const material = new THREE.MeshStandardMaterial({ 
      color: this.config.color,
      emissive: this.config.color,
      emissiveIntensity: 0.5,
      roughness: 0.3,
      metalness: 0.8
    });

    return new THREE.Mesh(geometry, material);
  }

  private createLabel(text: string): THREE.Sprite {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    if (context) {
      canvas.width = 256;
      canvas.height = 64;
      context.font = 'Bold 24px Inter, Arial';
      context.fillStyle = 'rgba(255, 255, 255, 0.7)';
      context.textAlign = 'center';
      context.fillText(text, 128, 40);
    }
    
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(30, 8, 1);
    return sprite;
  }

  public update(time: number, delta: number) {
    // Movimento de deriva sutil (Drift)
    const driftX = Math.sin(time * 0.5 + this.driftOffset.x) * 5;
    const driftY = Math.cos(time * 0.4 + this.driftOffset.y) * 5;
    const driftZ = Math.sin(time * 0.6 + this.driftOffset.z) * 5;
    
    this.mesh.position.set(
      this.basePosition.x + driftX,
      this.basePosition.y + driftY,
      this.basePosition.z + driftZ
    );
    
    // Rotação própria sutil
    this.bodyMesh.rotation.y += delta * 0.3;

    // --- Processar Animações ---
    
    // 1. Pulso
    if (this.pulseValue > 0) {
      const scale = 1.0 + Math.sin(this.pulseValue * Math.PI) * 0.5;
      this.bodyMesh.scale.set(scale, scale, scale);
      this.pulseValue -= delta * 1.5; 
    } else {
      this.bodyMesh.scale.set(1, 1, 1);
    }

    // 2. Halo
    if (this.halo) {
      const targetOpacity = this.haloValue > 0 ? 0.2 + Math.sin(time * 4) * 0.1 : 0;
      const mat = this.halo.material as THREE.MeshBasicMaterial;
      mat.opacity = THREE.MathUtils.lerp(mat.opacity, targetOpacity, 0.1);
    }

    // 3. Erro (Flash Vermelho)
    if (this.errorFlash > 0) {
      const isRed = Math.floor(time * 10) % 2 === 0;
      const mat = this.bodyMesh.material as THREE.MeshStandardMaterial;
      if (isRed) {
        mat.emissive.setHex(0xff0000);
      } else {
        mat.emissive.setHex(this.originalColor);
      }
      this.errorFlash -= delta;
    } else {
      const mat = this.bodyMesh.material as THREE.MeshStandardMaterial;
      if (mat.emissive.getHex() === 0xff0000) {
        mat.emissive.setHex(this.originalColor);
      }
    }
  }
}
