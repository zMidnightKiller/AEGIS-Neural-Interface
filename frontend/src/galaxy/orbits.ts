import * as THREE from 'three';

/**
 * Cria uma linha circular para representar uma órbita.
 */
export function createOrbitLine(radius: number, color: number = 0x444444): THREE.Line {
  const curve = new THREE.EllipseCurve(
    0, 0,            // ax, ay
    radius, radius,  // xRadius, yRadius
    0, 2 * Math.PI,  // aStartAngle, aEndAngle
    false,           // aClockwise
    0                // aRotation
  );

  const points = curve.getPoints(128);
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  
  const material = new THREE.LineDashedMaterial({
    color: color,
    linewidth: 1,
    scale: 1,
    dashSize: 3,
    gapSize: 2,
    transparent: true,
    opacity: 0.3
  });

  const orbit = new THREE.Line(geometry, material);
  orbit.rotation.x = Math.PI / 2; // Deita a órbita no plano XZ
  orbit.computeLineDistances(); // Necessário para LineDashedMaterial
  
  return orbit;
}

/**
 * Cria múltiplas órbitas para os anéis definidos.
 */
export function createGalaxyOrbits(scene: THREE.Scene) {
  const orbitRadii = [90, 155, 210, 260];
  const orbits: THREE.Line[] = [];

  orbitRadii.forEach(radius => {
    const orbit = createOrbitLine(radius);
    scene.add(orbit);
    orbits.push(orbit);
  });

  return orbits;
}
