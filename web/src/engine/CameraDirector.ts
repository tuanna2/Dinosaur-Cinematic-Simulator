import * as THREE from "three";

interface CameraPreset {
  offset: THREE.Vector3;
  focusHeight: number;
  damping: number;
}

const PRESETS: Record<string, CameraPreset> = {
  aerial_establishing: { offset: new THREE.Vector3(18, 22, 24), focusHeight: 1.0, damping: 2.0 },
  static_hide: { offset: new THREE.Vector3(-8, 2.2, 9), focusHeight: 1.2, damping: 5.0 },
  medium_tracking: { offset: new THREE.Vector3(8, 4.5, 10), focusHeight: 1.5, damping: 4.0 },
  low_threat_reveal: { offset: new THREE.Vector3(7, 1.8, 9), focusHeight: 1.8, damping: 3.0 },
  wide_observational: { offset: new THREE.Vector3(16, 7, 18), focusHeight: 1.0, damping: 2.8 },
  long_lens_observation: { offset: new THREE.Vector3(26, 5, 28), focusHeight: 1.4, damping: 2.4 },
};

export class CameraDirector {
  private target: THREE.Object3D | null = null;
  private preset: CameraPreset = PRESETS.aerial_establishing;
  private targetFocalLength = 50;
  private readonly focus = new THREE.Vector3();
  private readonly desiredPosition = new THREE.Vector3();

  constructor(private readonly camera: THREE.PerspectiveCamera) {}

  apply(presetName: string, target: THREE.Object3D | null, lensMm = 50, immediate = false): void {
    this.target = target;
    this.preset = PRESETS[presetName] ?? { offset: new THREE.Vector3(10, 5, 12), focusHeight: 1.2, damping: 3.5 };
    this.targetFocalLength = lensMm;
    if (immediate) {
      this.computeFocus();
      this.camera.position.copy(this.focus).add(this.preset.offset);
      this.camera.setFocalLength(this.targetFocalLength);
      this.camera.lookAt(this.focus);
      this.camera.updateProjectionMatrix();
    }
  }

  update(dt: number): void {
    this.computeFocus();
    this.desiredPosition.copy(this.focus).add(this.preset.offset);
    const alpha = 1 - Math.exp(-this.preset.damping * dt);
    this.camera.position.lerp(this.desiredPosition, alpha);

    const currentFocal = this.camera.getFocalLength();
    const nextFocal = THREE.MathUtils.lerp(currentFocal, this.targetFocalLength, alpha);
    this.camera.setFocalLength(nextFocal);
    this.camera.lookAt(this.focus);
    this.camera.updateProjectionMatrix();
  }

  private computeFocus(): void {
    this.focus.set(0, 0, 0);
    this.target?.getWorldPosition(this.focus);
    this.focus.y += this.preset.focusHeight;
  }
}
