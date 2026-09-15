import * as THREE from "three";
import type { RuntimeEnvironment } from "../types";

export class EnvironmentController {
  private readonly rain: THREE.Points;
  private readonly rainPositions: Float32Array;
  private readonly initialRainPositions: Float32Array;
  private readonly sun = new THREE.DirectionalLight(0xffffff, 3.0);
  private readonly hemi = new THREE.HemisphereLight(0xffffff, 0x273124, 2.0);
  private rainSpeed = 16;

  constructor(private readonly scene: THREE.Scene, environment: RuntimeEnvironment) {
    this.scene.add(this.hemi, this.sun);
    this.sun.castShadow = true;
    this.sun.position.set(-12, 22, 8);

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(140, 140),
      new THREE.MeshStandardMaterial({ color: 0x40553a, roughness: 0.72, metalness: 0.03 }),
    );
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);

    this.addPlaceholderForest();
    const rain = this.createRain(2200);
    this.rain = rain.points;
    this.rainPositions = rain.positions;
    this.initialRainPositions = rain.positions.slice();
    this.scene.add(this.rain);

    this.applyTimeOfDay(environment.time_of_day);
    this.applyWeather(environment.weather);
  }

  update(dt: number): void {
    if (!this.rain.visible) return;
    for (let i = 1; i < this.rainPositions.length; i += 3) {
      this.rainPositions[i] -= this.rainSpeed * dt;
      if (this.rainPositions[i] < 0.2) this.rainPositions[i] += 28;
    }
    const position = this.rain.geometry.getAttribute("position") as THREE.BufferAttribute;
    position.needsUpdate = true;
  }

  reset(): void {
    this.rainPositions.set(this.initialRainPositions);
    const position = this.rain.geometry.getAttribute("position") as THREE.BufferAttribute;
    position.needsUpdate = true;
  }

  applyWeather(weather: string): void {
    const normalized = weather.toLowerCase();
    const heavy = normalized.includes("heavy") || normalized.includes("storm");
    const rainy = heavy || normalized.includes("rain");
    this.rain.visible = rainy;
    this.rainSpeed = heavy ? 22 : 14;

    const fogDensity = heavy ? 0.026 : rainy ? 0.020 : 0.012;
    this.scene.fog = new THREE.FogExp2(0x8fa095, fogDensity);
    const material = this.rain.material as THREE.PointsMaterial;
    material.opacity = heavy ? 0.58 : 0.38;
  }

  applyTimeOfDay(timeOfDay: string): void {
    const value = timeOfDay.toLowerCase();
    if (value.includes("late_afternoon") || value.includes("sunset")) {
      this.scene.background = new THREE.Color(0x9aada2);
      this.sun.color.set(0xffe0b0);
      this.sun.intensity = 3.2;
      this.hemi.color.set(0xbfd0c8);
      this.hemi.intensity = 1.8;
      return;
    }
    if (value.includes("night")) {
      this.scene.background = new THREE.Color(0x18242d);
      this.sun.color.set(0x9fb6d8);
      this.sun.intensity = 0.45;
      this.hemi.color.set(0x7186a0);
      this.hemi.intensity = 0.75;
      return;
    }
    this.scene.background = new THREE.Color(0xb8c6bc);
    this.sun.color.set(0xfff2d6);
    this.sun.intensity = 2.8;
    this.hemi.color.set(0xd2ded7);
    this.hemi.intensity = 2.1;
  }

  private addPlaceholderForest(): void {
    const treeMaterial = new THREE.MeshStandardMaterial({ color: 0x304b30, roughness: 1 });
    const trunkMaterial = new THREE.MeshStandardMaterial({ color: 0x4a3828, roughness: 1 });
    for (let i = 0; i < 96; i += 1) {
      const side = i % 2 === 0 ? -1 : 1;
      const x = side * (15 + (i % 9) * 2.25);
      const z = -42 + (i % 24) * 3.7;
      const height = 4.5 + (i % 5) * 0.65;

      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.32, height * 0.68, 7), trunkMaterial);
      trunk.position.set(x, height * 0.34, z);
      const crown = new THREE.Mesh(new THREE.ConeGeometry(1.1 + (i % 3) * 0.25, height, 8), treeMaterial);
      crown.position.set(x, height * 0.72, z);
      this.scene.add(trunk, crown);
    }
  }

  private createRain(count: number): { points: THREE.Points; positions: Float32Array } {
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      positions[i * 3] = ((i * 37) % 120) - 60;
      positions[i * 3 + 1] = 1 + ((i * 53) % 28);
      positions[i * 3 + 2] = ((i * 71) % 120) - 60;
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({ size: 0.055, transparent: true, opacity: 0.5, depthWrite: false });
    return { points: new THREE.Points(geometry, material), positions };
  }
}
