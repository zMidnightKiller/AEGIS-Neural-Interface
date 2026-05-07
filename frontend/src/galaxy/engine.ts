import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { createScene } from './scene';
import { GalaxyEvents } from './events';

/**
 * GalaxyEngine: Gerencia o ciclo de vida do Three.js para a Interface Galáctica.
 */
export class GalaxyEngine {
  private container: HTMLElement;
  private renderer: THREE.WebGLRenderer;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private controls: OrbitControls;
  private animationId: number | null = null;
  private clock: THREE.Clock;
  private eventsHandler: GalaxyEvents | null = null;
  private raycaster: THREE.Raycaster;
  private mouse: THREE.Vector2;
  private bodies: any[] = [];
  
  // Callbacks para UI React
  public onNodeHover: (node: any | null) => void = () => {};
  public onNodeClick: (node: any | null) => void = () => {};
  public onBlackHoleClick: () => void = () => {};

  constructor(container: HTMLElement) {
    this.container = container;
    this.clock = new THREE.Clock();
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    // Setup Renderer
    this.renderer = new THREE.WebGLRenderer({ 
      antialias: true, 
      alpha: true 
    });
    console.log(`GalaxyEngine: Initializing with dimensions ${container.clientWidth}x${container.clientHeight}`);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.setClearColor(0x050505, 1); // Fundo quase preto, mas não zero
    this.container.appendChild(this.renderer.domElement);

    // Setup Camera
    this.camera = new THREE.PerspectiveCamera(
      60, 
      container.clientWidth / container.clientHeight, 
      1, 
      2000
    );
    this.camera.position.set(0, 300, 500);

    // Setup Controls
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.rotateSpeed = 0.5;
    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 0.2;

    // Create Scene
    const { 
      scene, 
      update, 
      bodies, 
      setBlackHoleActivity, 
      setOperatingMode, 
      setIsListening 
    } = createScene();
    this.scene = scene;
    this.updateScene = update;
    this.setOperatingMode = setOperatingMode;
    this.setIsListening = setIsListening;
    this.bodies = bodies;
    
    // Initialize Events Handler
    this.eventsHandler = new GalaxyEvents(
      this.scene, 
      bodies, 
      setBlackHoleActivity,
      (active, pulse) => {
        this.voiceActive = active;
        this.voicePulse = pulse || 0;
      },
      (active) => {
        if (this.setIsListening) this.setIsListening(active);
      }
    );

    // Listeners para Raycasting
    this.container.addEventListener('pointermove', this.onPointerMove.bind(this));
    this.container.addEventListener('pointerdown', this.onPointerDown.bind(this));
    window.addEventListener('resize', this.onWindowResize.bind(this));
  }

  private updateScene: (time: number, pulse?: number, active?: boolean) => void;
  private setOperatingMode: (mode: string) => void;
  private setIsListening: (active: boolean) => void;
  private voicePulse: number = 0;
  private voiceActive: boolean = false;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;

  /**
   * Configura a análise de áudio para sincronização visual.
   */
  public setupAudioAnalysis(stream: MediaStream | HTMLAudioElement) {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 256;
    
    let source;
    if (stream instanceof MediaStream) {
      source = this.audioContext.createMediaStreamSource(stream);
    } else {
      source = this.audioContext.createMediaElementSource(stream);
      source.connect(this.audioContext.destination);
    }
    
    source.connect(this.analyser);
    
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const analyze = () => {
      if (this.analyser && this.voiceActive) {
        this.analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        this.voicePulse = sum / (bufferLength * 255); // Normaliza 0-1
      } else if (!this.voiceActive) {
        this.voicePulse = 0;
      }
      requestAnimationFrame(analyze);
    };
    analyze();
  }

  private onPointerMove(event: PointerEvent) {
    const rect = this.container.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.checkIntersections(false);
  }

  private onPointerDown(_event: PointerEvent) {
    this.checkIntersections(true);
  }

  private checkIntersections(isClick: boolean) {
    this.raycaster.setFromCamera(this.mouse, this.camera);
    
    // Coletar todas as meshes de corpos para interseção
    const targetMeshes = [...this.bodies.map(b => b.mesh), this.scene.getObjectByName('BlackHole')!];
    const intersects = this.raycaster.intersectObjects(targetMeshes, true);

    if (intersects.length > 0) {
      const hitObject = intersects[0].object;
      
      // Verificar se é o Buraco Negro
      let isBlackHole = false;
      let current: any = hitObject;
      while (current) {
        if (current.name === 'BlackHole') {
          isBlackHole = true;
          break;
        }
        current = current.parent;
      }

      if (isBlackHole) {
        if (isClick) {
          this.onBlackHoleClick();
          this.controls.autoRotate = false;
        } else {
          document.body.style.cursor = 'pointer';
        }
        return;
      }

      // Encontrar qual CelestialBody foi atingido
      let bodyFound = null;
      for (const body of this.bodies) {
        let currentBody: any = hitObject;
        while (currentBody) {
          if (currentBody === body.mesh) {
            bodyFound = body;
            break;
          }
          currentBody = currentBody.parent;
        }
        if (bodyFound) break;
      }

      if (bodyFound) {
        if (isClick) {
          this.onNodeClick(bodyFound.config);
          this.controls.autoRotate = false; // Para rotação ao selecionar
        } else {
          this.onNodeHover(bodyFound.config);
          document.body.style.cursor = 'pointer';
        }
        return;
      }
    }

    if (!isClick) {
      this.onNodeHover(null);
      document.body.style.cursor = 'default';
    }
  }

  private onWindowResize() {
    this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
  }

  public start() {
    console.log("GalaxyEngine: Animation cycle started");
    const animate = () => {
      this.animationId = requestAnimationFrame(animate);
      const now = this.clock.getElapsedTime();
      const delta = this.clock.getDelta(); 
      
      this.updateScene(now, this.voicePulse, this.voiceActive);
      if (this.eventsHandler) {
        this.eventsHandler.update(delta);
      }
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    };
    animate();
  }

  public setMode(mode: string) {
    if (this.setOperatingMode) {
      this.setOperatingMode(mode);
    }
  }

  public stop() {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
    }
  }

  /**
   * Encaminha um evento para o processador de animações.
   */
  public emit(event: any) {
    if (this.eventsHandler) {
      this.eventsHandler.handleEvent(event);
    }
  }

  public dispose() {
    this.stop();
    window.removeEventListener('resize', this.onWindowResize.bind(this));
    this.renderer.dispose();
    if (this.container.contains(this.renderer.domElement)) {
      this.container.removeChild(this.renderer.domElement);
    }
  }
}
