import * as THREE from "three";
import { AssetRegistry } from "./AssetRegistry";
import { CameraDirector } from "./CameraDirector";
import { createDinosaurPlaceholder } from "./PlaceholderFactory";
import type { ActionEvent, ExecutionPlan, RuntimeEvent } from "../types";

interface MotionState {
  mode: "idle" | "toward" | "away";
  targetIds: string[];
  speed: number;
}

export class CinematicRuntime {
  readonly scene = new THREE.Scene();
  readonly camera = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 1000);
  readonly renderer: THREE.WebGLRenderer;

  private readonly actors = new Map<string, THREE.Object3D>();
  private readonly motion = new Map<string, MotionState>();
  private readonly cameraDirector = new CameraDirector(this.camera);
  private readonly initialPositions = new Map<string, THREE.Vector3>();
  private playing = false;
  private elapsed = 0;
  private lastFrame = performance.now();
  private eventIndex = 0;
  private raf = 0;

  constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly plan: ExecutionPlan,
    private readonly assets: AssetRegistry,
    private readonly onTime?: (seconds: number) => void,
  ) {
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.buildEnvironment();
    window.addEventListener("resize", this.resize);
  }

  async initialize(): Promise<void> {
    for (const [index, instance] of this.plan.instances.entries()) {
      const loaded = await this.assets.instantiate(instance.asset_id).catch(() => null);
      const actor = loaded ?? createDinosaurPlaceholder(instance.species);
      actor.name = instance.instance_id;
      actor.userData.groupId = instance.group_id;
      actor.userData.assetId = instance.asset_id;
      actor.userData.species = instance.species;

      const position = this.spawnPosition(instance.group_id, index);
      actor.position.copy(position);
      this.initialPositions.set(instance.instance_id, position.clone());
      this.actors.set(instance.instance_id, actor);
      this.motion.set(instance.instance_id, { mode: "idle", targetIds: [], speed: 0 });
      this.scene.add(actor);
    }

    const first = this.plan.instances[0];
    this.cameraDirector.apply("aerial_establishing", first ? this.actors.get(first.instance_id) ?? null : null, 35);
    this.resize();
    this.loop();
  }

  play(): void {
    this.playing = true;
    this.lastFrame = performance.now();
  }

  pause(): void {
    this.playing = false;
  }

  restart(): void {
    this.playing = false;
    this.elapsed = 0;
    this.eventIndex = 0;
    for (const [id, actor] of this.actors) {
      const initial = this.initialPositions.get(id);
      if (initial) actor.position.copy(initial);
      actor.rotation.set(0, 0, 0);
      this.motion.set(id, { mode: "idle", targetIds: [], speed: 0 });
    }
    this.onTime?.(0);
    this.play();
  }

  dispose(): void {
    cancelAnimationFrame(this.raf);
    window.removeEventListener("resize", this.resize);
    this.renderer.dispose();
  }

  private buildEnvironment(): void {
    this.scene.background = new THREE.Color(0x9aada2);
    this.scene.fog = new THREE.FogExp2(0x8fa095, 0.018);

    const hemi = new THREE.HemisphereLight(0xcad9d1, 0x273124, 2.0);
    this.scene.add(hemi);

    const sun = new THREE.DirectionalLight(0xfff1cf, 3.0);
    sun.position.set(-12, 22, 8);
    sun.castShadow = true;
    this.scene.add(sun);

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(120, 120),
      new THREE.MeshStandardMaterial({ color: 0x40553a, roughness: 0.92 }),
    );
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);

    const treeMaterial = new THREE.MeshStandardMaterial({ color: 0x304b30, roughness: 1 });
    for (let i = 0; i < 80; i += 1) {
      const tree = new THREE.Mesh(new THREE.ConeGeometry(1.2, 5 + (i % 4), 7), treeMaterial);
      const side = i % 2 === 0 ? -1 : 1;
      tree.position.set(side * (16 + (i % 9) * 2.2), 2.5, -35 + (i % 20) * 3.7);
      this.scene.add(tree);
    }
  }

  private spawnPosition(groupId: string, index: number): THREE.Vector3 {
    if (groupId === "raptor_pack") {
      const local = index % 8;
      return new THREE.Vector3(-10 + (local % 4) * 1.8, 0, 3 + Math.floor(local / 4) * 2.4);
    }
    if (groupId === "triceratops_01") return new THREE.Vector3(1, 0, -3);
    if (groupId === "trex_01") return new THREE.Vector3(20, 0, 12);
    return new THREE.Vector3(index * 2, 0, 0);
  }

  private loop = (): void => {
    const now = performance.now();
    const dt = Math.min((now - this.lastFrame) / 1000, 0.05);
    this.lastFrame = now;

    if (this.playing) {
      this.elapsed = Math.min(this.elapsed + dt, this.plan.duration_seconds);
      this.processEvents();
      this.updateActors(dt);
      this.onTime?.(this.elapsed);
      if (this.elapsed >= this.plan.duration_seconds) this.playing = false;
    }

    this.renderer.render(this.scene, this.camera);
    this.raf = requestAnimationFrame(this.loop);
  };

  private processEvents(): void {
    while (this.eventIndex < this.plan.events.length) {
      const event: RuntimeEvent = this.plan.events[this.eventIndex];
      if (event.time > this.elapsed) break;
      if (event.type === "camera") {
        const target = this.resolveActor(event.camera.target);
        this.cameraDirector.apply(event.camera.preset, target, event.camera.lens_mm ?? 50);
      } else {
        this.applyAction(event);
      }
      this.eventIndex += 1;
    }
  }

  private applyAction(event: ActionEvent): void {
    const ids = event.resolved_instances;
    const targets = event.resolved_target_instances;
    let mode: MotionState["mode"] = "idle";
    let speed = 0;

    if (["stalk", "chase", "attack", "enter"].includes(event.action)) {
      mode = "toward";
      speed = event.action === "stalk" ? 0.8 : event.action === "attack" ? 2.1 : 1.6;
    } else if (["flee_to_grassland", "scatter", "retreat"].includes(event.action)) {
      mode = "away";
      speed = event.action === "scatter" ? 2.4 : 1.8;
    }

    for (const id of ids) {
      this.motion.set(id, { mode, targetIds: targets, speed });
      const actor = this.actors.get(id);
      if (actor) actor.userData.animationId = event.animation ?? null;
    }
  }

  private updateActors(dt: number): void {
    for (const [id, state] of this.motion) {
      if (state.mode === "idle") continue;
      const actor = this.actors.get(id);
      if (!actor) continue;
      const target = state.targetIds.length ? this.actors.get(state.targetIds[0]) : null;
      const direction = new THREE.Vector3();
      if (target) direction.subVectors(target.position, actor.position);
      else direction.set(state.mode === "away" ? -1 : 1, 0, -0.3);
      direction.y = 0;
      if (direction.lengthSq() < 0.001) continue;
      direction.normalize();
      if (state.mode === "away") direction.multiplyScalar(-1);
      actor.position.addScaledVector(direction, state.speed * dt);
      actor.rotation.y = Math.atan2(direction.x, direction.z);
    }
  }

  private resolveActor(groupOrInstance?: string): THREE.Object3D | null {
    if (!groupOrInstance) return null;
    const direct = this.actors.get(groupOrInstance);
    if (direct) return direct;
    const instanceId = this.plan.actor_groups[groupOrInstance]?.[0];
    return instanceId ? this.actors.get(instanceId) ?? null : null;
  }

  private resize = (): void => {
    const width = this.canvas.clientWidth || window.innerWidth;
    const height = this.canvas.clientHeight || window.innerHeight;
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / Math.max(height, 1);
    this.camera.updateProjectionMatrix();
  };
}
