import * as THREE from 'three';
import { NeuralNode } from './bodies';
import type { NeuralNodeConfig } from './bodies';

/**
 * createScene: Define o conteúdo visual da interface de rede neural cósmica.
 */
export function createScene() {
  const scene = new THREE.Scene();
  const bodies: NeuralNode[] = [];
  const connections: THREE.LineSegments[] = [];

  // 1. Estrelas Procedurais (Fundo)
  const starGeometry = new THREE.BufferGeometry();
  const starPositions = [];
  const starColors = [];

  for (let i = 0; i < 4000; i++) {
    starPositions.push(
      (Math.random() - 0.5) * 3000,
      (Math.random() - 0.5) * 3000,
      (Math.random() - 0.5) * 3000
    );
    const brightness = 0.4 + Math.random() * 0.6;
    starColors.push(brightness, brightness, brightness);
  }

  starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));
  starGeometry.setAttribute('color', new THREE.Float32BufferAttribute(starColors, 3));

  const starMaterial = new THREE.PointsMaterial({
    size: 1.5,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
  });

  const stars = new THREE.Points(starGeometry, starMaterial);
  scene.add(stars);

  // 2. Buraco Negro Central (Estilo Gargantua)
  const gargantua = new THREE.Group();
  gargantua.name = 'BlackHole';
  
  // Event Horizon
  const coreGeometry = new THREE.SphereGeometry(35, 32, 32);
  const coreMaterial = new THREE.MeshBasicMaterial({ color: 0x000000 });
  const core = new THREE.Mesh(coreGeometry, coreMaterial);
  gargantua.add(core);

  // Accretion Disk (Horizontal)
  const diskGeo = new THREE.RingGeometry(40, 100, 64);
  const diskMat = new THREE.MeshBasicMaterial({
    color: 0xffaa44,
    transparent: true,
    opacity: 0.6,
    side: THREE.DoubleSide
  });
  const accretionDisk = new THREE.Mesh(diskGeo, diskMat);
  accretionDisk.rotation.x = Math.PI / 2;
  gargantua.add(accretionDisk);

  // Gravitational Lensing Ring (Vertical/Warped)
  const lensGeo = new THREE.TorusGeometry(60, 2, 16, 100);
  const lensMat = new THREE.MeshBasicMaterial({
    color: 0xffcc88,
    transparent: true,
    opacity: 0.3
  });
  const lensRing = new THREE.Mesh(lensGeo, lensMat);
  // Simula a distorção visual de Interstellar
  lensRing.rotation.y = Math.PI / 4;
  gargantua.add(lensRing);

  // Glow central
  const glowGeo = new THREE.SphereGeometry(38, 32, 32);
  const glowMat = new THREE.MeshBasicMaterial({
    color: 0xff8800,
    transparent: true,
    opacity: 0.15,
  });
  const glow = new THREE.Mesh(glowGeo, glowMat);
  gargantua.add(glow);

  scene.add(gargantua);

  // 3. Definição dos Nós da Rede Neural
  const nodeConfigs: NeuralNodeConfig[] = [
    // Core Cluster
    { name: 'Working Memory', radius: 4, position: new THREE.Vector3(80, 40, 20), color: 0x00ffff, complexity: 0.8, type: 'memory' },
    { name: 'Episodic Memory', radius: 5, position: new THREE.Vector3(-70, 60, -30), color: 0xaaaaff, complexity: 0.9, type: 'memory' },
    { name: 'Semantic Memory', radius: 6, position: new THREE.Vector3(50, -80, -40), color: 0xffaaff, complexity: 0.95, type: 'memory' },

    // Agents Cluster
    { name: 'Research Agent', radius: 7, position: new THREE.Vector3(140, 20, -60), color: 0x44ff44, complexity: 0.7, type: 'agent' },
    { name: 'Task Agent', radius: 7, position: new THREE.Vector3(-120, -30, 80), color: 0x4444ff, complexity: 0.6, type: 'agent' },
    { name: 'Code Agent', radius: 8, position: new THREE.Vector3(100, 100, 100), color: 0xff4444, complexity: 0.85, type: 'agent' },
    { name: 'Memory Agent', radius: 6, position: new THREE.Vector3(-100, 90, -100), color: 0xffff44, complexity: 0.8, type: 'agent' },

    // Tools Cluster
    { name: 'Web Search', radius: 3, position: new THREE.Vector3(200, -50, 20), color: 0x00ccff, complexity: 0.4, type: 'tool' },
    { name: 'File System', radius: 3, position: new THREE.Vector3(-180, 40, 120), color: 0x00ccff, complexity: 0.3, type: 'tool' },
    { name: 'Run Code', radius: 3, position: new THREE.Vector3(50, -150, 150), color: 0x00ccff, complexity: 0.5, type: 'tool' },
    { name: 'Browser Control', radius: 4, position: new THREE.Vector3(-60, -120, -200), color: 0xaaaaff, complexity: 0.6, type: 'tool' },
  ];

  nodeConfigs.forEach(config => {
    const node = new NeuralNode(config);
    scene.add(node.mesh);
    bodies.push(node);
  });

  // 4. Criação das Conexões (Sinapses)
  const lineMaterial = new THREE.LineBasicMaterial({
    color: 0x4444aa,
    transparent: true,
    opacity: 0.2
  });

  const updateConnections = () => {
    // Remove conexões antigas
    connections.forEach(c => scene.remove(c));
    connections.length = 0;

    const points = [];
    // Conectar nós próximos (Simulando rede neural)
    for (let i = 0; i < bodies.length; i++) {
      for (let j = i + 1; j < bodies.length; j++) {
        const dist = bodies[i].mesh.position.distanceTo(bodies[j].mesh.position);
        if (dist < 180) { // Limite de conexão
          points.push(bodies[i].mesh.position.clone());
          points.push(bodies[j].mesh.position.clone());
        }
      }
      // Todos conectam ao centro (Gargantua) com menor opacidade
      points.push(bodies[i].mesh.position.clone());
      points.push(new THREE.Vector3(0, 0, 0));
    }

    const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
    const lineSegments = new THREE.LineSegments(lineGeometry, lineMaterial);
    scene.add(lineSegments);
    connections.push(lineSegments);
  };

  // 5. NebulosaProcedural
  const nebulaGroup = new THREE.Group();
  const nebulaMaterial = new THREE.MeshBasicMaterial({
    color: 0x4400ff,
    transparent: true,
    opacity: 0.03,
  });

  for (let i = 0; i < 6; i++) {
    const blobGeo = new THREE.SphereGeometry(200, 16, 16);
    const blob = new THREE.Mesh(blobGeo, nebulaMaterial);
    blob.position.set((Math.random() - 0.5) * 800, (Math.random() - 0.5) * 600, (Math.random() - 0.5) * 800);
    blob.scale.set(1.5, 0.7, 2);
    nebulaGroup.add(blob);
  }
  scene.add(nebulaGroup);

  // Update Function
  let lastTime = 0;
  let accretionSpeed = 0.015;
  let operatingMode: string = 'STANDARD';
  let isListening: boolean = false;

  const update = (time: number, voicePulse: number = 0, voiceActive: boolean = false) => {
    const delta = time - lastTime;
    lastTime = time;

    // Shimmer das estrelas
    starMaterial.opacity = 0.6 + Math.sin(time * 1.5) * 0.2;
    
    // Rotação Gargantua
    const currentSpeed = (voiceActive || isListening) ? accretionSpeed * 4 : accretionSpeed;
    accretionDisk.rotation.z += currentSpeed;
    lensRing.rotation.z -= currentSpeed * 0.5;
    lensRing.rotation.x = Math.sin(time * 0.2) * 0.2;
    
    // Pulso central sincronizado
    let targetPulse = 1.0;
    if (voiceActive) {
      targetPulse = 1.0 + voicePulse * 0.4;
      diskMat.color.setHex(0xffffff); // Brilha branco ao falar
    } else if (isListening) {
      targetPulse = 1.0 + Math.abs(Math.sin(time * 6)) * 0.08;
      diskMat.color.setHex(0x00ffff);
    } else {
      targetPulse = 1.0 + Math.sin(time * 1.2) * 0.05;
      diskMat.color.setHex(0xffaa44);
    }
    
    accretionDisk.scale.set(targetPulse, targetPulse, 1);
    glow.scale.set(targetPulse, targetPulse, targetPulse);
    
    // Movimento da nebulosa
    nebulaGroup.rotation.y += 0.0005;

    // Atualizar Corpos Neurais
    bodies.forEach(node => node.update(time, delta));
    
    // Atualizar Conexões
    updateConnections();

    // Aplicação de Modos Visuais
    if (operatingMode === 'SILENT') {
      diskMat.opacity = 0.1;
      lineMaterial.opacity = 0.05;
    } else if (operatingMode === 'ANALYSIS') {
      diskMat.opacity = 0.8;
      lineMaterial.opacity = 0.4;
      lineMaterial.color.setHex(0x00ffff);
    } else {
      diskMat.opacity = 0.6;
      lineMaterial.opacity = 0.2;
      lineMaterial.color.setHex(0x4444aa);
    }
  };

  const setBlackHoleActivity = (active: boolean) => {
    accretionSpeed = active ? 0.06 : 0.015;
  };

  const setOperatingMode = (mode: string) => {
    operatingMode = mode.toUpperCase();
  };

  const setIsListening = (active: boolean) => {
    isListening = active;
  };

  return { scene, update, bodies, setBlackHoleActivity, setOperatingMode, setIsListening };
}
