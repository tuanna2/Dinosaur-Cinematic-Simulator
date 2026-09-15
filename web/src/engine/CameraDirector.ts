import * as THREE from "three";

export class CameraDirector {
  constructor(private readonly camera: THREE.PerspectiveCamera) {}

  apply(preset: string, target: THREE.Object3D | null, lensMm = 50): void {
    this.camera.setFocalLength(lensMm);
    const focus = new THREE.Vector3();
    target?.getWorldPosition(focus);

    const offsets: Record<string, THREE.Vector3> = {
      aerial_establishing: new THREE.Vector3(18, 22, 24),
      static_hide: new THREE.Vector3(-8, 2.2, 9),
      medium_tracking: new THREE.Vector3(8, 4.5, 10),
      low_threat_reveal: new THREE.Vector3(7, 1.8, 9),
      wide_observational: new THREE.Vector3(16, 7, 18),
      long_lens_observation: new THREE.Vector3(26, 5, 28),
    };

    const offset = offsets[preset] ?? new THREE.Vector3(10, 5, 12);
    this.camera.position.copy(focus).add(offset);
    this.camera.lookAt(focus.x, focus.y + 1, focus.z);
    this.camera.updateProjectionMatrix();
  }
}
