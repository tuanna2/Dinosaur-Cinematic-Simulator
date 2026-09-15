import * as THREE from "three";
import { ActorController } from "./ActorController";
import { AssetRegistry } from "./AssetRegistry";
import { BehaviorSystem, intentForAction, type MotionIntent } from "./BehaviorSystem";
import { CameraDirector } from "./CameraDirector";
import { EnvironmentController } from "./EnvironmentController";
import { createDinosaurPlaceholder } from "./PlaceholderFactory";
import type { ActionEvent, ExecutionPlan, RuntimeEvent } from "../types";

export interface RuntimeSnapshot {
  scenario_id: string;
  time: number;
  playing: boolean;
  actors: Array<{
    id: string;
    group_id: string;
    state: string;
    animation_id: string | null;
    position: [number, number, number];
  }>;
}

export class CinematicRuntime {
  readonly scene = new THREE.Scene();
  readonly camera = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 1000);
  readonly renderer: THREE.WebGLRenderer;

  private readonly actors = new Map<string, THREE.Object3D>();
  private readonly controllers = new Map<string, ActorController>();
  private readonly motion = new Map<string, MotionIntent>();
  private readonly cameraDirector = new CameraDirector(this.camera);
  private readonly behavior = new BehaviorSystem();
  private readonly environment: EnvironmentController;
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
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.environment = new EnvironmentController(this.scene, plan.environment);
    window.addEventListener("resize", this.resize);
  }

  get durationSeconds(): number {
    return this.plan.duration_seconds;
  }

  get currentTime(): number {
    return this.elapsed;
  }

  async initialize(): Promise<void> {
    await this.assets.preload(this.plan.required_assets);

    const environmentAsset = await this.assets.instantiate(this.plan.environment.asset_id).catch(() => null);
    if (environmentAsset) {
      environmentAsset.root.name = this.plan.environment.asset_id;
      environmentAsset.root.userData.runtimeEnvironment = true;
      this.enableShadows(environmentAsset.root);
      this.scene.add(environmentAsset.root);
      this.environment.setPlaceholderWorldVisible(false);
    }

    for (const [index, instance] of this.plan.instances.entries()) {
      const loaded = await this.assets.instantiate(instance.asset_id).catch(() => null);
      const actor = loaded?.root ?? createDinosaurPlaceholder(instance.species);
      const embeddedAnimations = loaded?.animations ?? [];
      actor.name = instance.instance_id;
      actor.userData.groupId = instance.group_id;
      actor.userData.assetId = instance.asset_id;
      actor.userData.species = instance.species;
      actor.userData.animationId = null;
      this.enableShadows(actor);
      // A fixed 1.5m pack slot intersects larger loaded animals. Derive a
      // conservative horizontal body clearance from the actual master bounds.
      const size = new THREE.Box3().setFromObject(actor).getSize(new THREE.Vector3());
      actor.userData.bodyClearance = Math.max(0.25, Math.min(size.x, size.z) * 0.5, Math.max(size.x, size.z) * 0.3);

      const position = this.spawnPosition(instance.group_id, index);
      actor.position.copy(position);
      this.initialPositions.set(instance.instance_id, position.clone());
      this.actors.set(instance.instance_id, actor);
      this.controllers.set(instance.instance_id, new ActorController(actor, embeddedAnimations, this.assets));
      this.motion.set(instance.instance_id, intentForAction("idle", []));
      this.scene.add(actor);
    }

    const first = this.plan.instances[0];
    this.cameraDirector.apply(
      "aerial_establishing",
      first ? this.actors.get(first.instance_id) ?? null : null,
      35,
      true,
    );
    this.processEvents();
    this.resize();
    this.render();
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
    this.resetSimulation();
    this.play();
  }

  seek(seconds: number): void {
    const target = THREE.MathUtils.clamp(seconds, 0, this.plan.duration_seconds);
    this.pause();
    this.resetSimulation(false);
    const step = 1 / Math.max(this.plan.render.fps, 1);
    while (this.elapsed + step < target) this.simulate(step, false);
    if (target > this.elapsed) this.simulate(target - this.elapsed, false);
    this.onTime?.(this.elapsed);
    this.render();
  }

  stepFrame(frames = 1): void {
    this.pause();
    const frameCount = Math.max(1, Math.floor(frames));
    const step = 1 / Math.max(this.plan.render.fps, 1);
    for (let i = 0; i < frameCount && this.elapsed < this.plan.duration_seconds; i += 1) {
      this.simulate(Math.min(step, this.plan.duration_seconds - this.elapsed), false);
    }
    this.onTime?.(this.elapsed);
    this.render();
  }

  renderFrameAt(seconds: number): void {
    this.seek(seconds);
    this.render();
  }

  captureDataUrl(type = "image/png", quality?: number): string {
    this.render();
    return this.canvas.toDataURL(type, quality);
  }

  snapshot(): RuntimeSnapshot {
    return {
      scenario_id: this.plan.scenario_id,
      time: this.elapsed,
      playing: this.playing,
      actors: [...this.actors.entries()].map(([id, actor]) => ({
        id,
        group_id: String(actor.userData.groupId ?? ""),
        state: String(actor.userData.behaviorState ?? "idle"),
        animation_id: typeof actor.userData.animationId === "string" ? actor.userData.animationId : null,
        position: [actor.position.x, actor.position.y, actor.position.z],
      })),
    };
  }

  dispose(): void {
    cancelAnimationFrame(this.raf);
    window.removeEventListener("resize", this.resize);
    this.renderer.dispose();
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
      this.simulate(dt, true);
      if (this.elapsed >= this.plan.duration_seconds) this.playing = false;
    }

    this.render();
    this.raf = requestAnimationFrame(this.loop);
  };

  private simulate(dt: number, notify: boolean): void {
    if (dt <= 0) return;
    this.elapsed = Math.min(this.elapsed + dt, this.plan.duration_seconds);
    this.processEvents();
    this.updateActors(dt);
    for (const controller of this.controllers.values()) controller.update(dt);
    this.environment.update(dt);
    this.cameraDirector.update(dt);
    if (notify) this.onTime?.(this.elapsed);
  }

  private processEvents(): void {
    while (this.eventIndex < this.plan.events.length) {
      const event: RuntimeEvent = this.plan.events[this.eventIndex];
      if (event.time > this.elapsed) break;
      if (event.type === "camera") {
        const target = this.resolveActor(event.camera.target);
        const frameZero = event.time === 0 && this.elapsed === 0;
        this.cameraDirector.apply(event.camera.preset, target, event.camera.lens_mm ?? 50, frameZero);
      } else {
        this.applyAction(event);
      }
      this.eventIndex += 1;
    }
  }

  private applyAction(event: ActionEvent): void {
    const intent = intentForAction(event.action, event.resolved_target_instances);
    for (const id of event.resolved_instances) {
      this.motion.set(id, { ...intent, targetIds: [...intent.targetIds] });
      const controller = this.controllers.get(id);
      controller?.setState(intent.state, event.animation);
      const actor = this.actors.get(id);
      if (actor) actor.userData.action = event.action;
    }
  }

  private updateActors(dt: number): void {
    for (const [id, intent] of this.motion) {
      const actor = this.actors.get(id);
      if (!actor || intent.speed <= 0) continue;

      const target = intent.targetIds.length ? this.actors.get(intent.targetIds[0]) ?? null : null;
      const targetPosition = target?.position ?? null;
      const clearance = target ? Number(actor.userData.bodyClearance) + Number(target.userData.bodyClearance) : 0;
      const groupId = String(actor.userData.groupId ?? "");
      const neighbors = this.groupNeighborPositions(groupId, id);
      const direction = this.behavior.desiredDirection(
        id,
        groupId,
        intent,
        actor.position,
        targetPosition,
        neighbors,
        clearance,
      );
      if (direction.lengthSq() < 0.0001) continue;

      let speed = intent.speed;
      if (targetPosition) {
        const distance = actor.position.distanceTo(targetPosition);
        if (intent.state === "attack" || intent.state === "chase") {
          const stopDistance = Math.max(clearance, intent.state === "attack" ? 2.0 : 1.5);
          if (distance < stopDistance && distance > 0.0001) {
            // Resolve an existing overlap gradually, including on state changes.
            direction.subVectors(actor.position, targetPosition).normalize();
            speed = Math.min(speed, (stopDistance - distance) / dt);
          } else {
            speed = Math.min(speed, Math.max(0, distance - stopDistance) / dt);
          }
        }
      }

      actor.position.addScaledVector(direction, speed * dt);
      if (speed > 0) {
        const yaw = Math.atan2(direction.x, direction.z);
        const targetRotation = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
        actor.quaternion.slerp(targetRotation, 1 - Math.exp(-7 * dt));
      }
    }
  }

  private groupNeighborPositions(groupId: string, actorId: string): THREE.Vector3[] {
    const ids = this.plan.actor_groups[groupId] ?? [];
    const positions: THREE.Vector3[] = [];
    for (const id of ids) {
      if (id === actorId) continue;
      const actor = this.actors.get(id);
      if (actor) positions.push(actor.position);
    }
    return positions;
  }

  private resolveActor(groupOrInstance?: string): THREE.Object3D | null {
    if (!groupOrInstance) return null;
    const direct = this.actors.get(groupOrInstance);
    if (direct) return direct;
    const instanceId = this.plan.actor_groups[groupOrInstance]?.[0];
    return instanceId ? this.actors.get(instanceId) ?? null : null;
  }

  private resetSimulation(notify = true): void {
    this.playing = false;
    this.elapsed = 0;
    this.eventIndex = 0;
    this.environment.reset();
    for (const [id, actor] of this.actors) {
      const initial = this.initialPositions.get(id);
      if (initial) actor.position.copy(initial);
      actor.rotation.set(0, 0, 0);
      actor.userData.animationId = null;
      actor.userData.action = "idle";
      this.controllers.get(id)?.reset();
      this.motion.set(id, intentForAction("idle", []));
    }
    const first = this.plan.instances[0];
    this.cameraDirector.apply(
      "aerial_establishing",
      first ? this.actors.get(first.instance_id) ?? null : null,
      35,
      true,
    );
    this.processEvents();
    if (notify) this.onTime?.(0);
  }

  private enableShadows(root: THREE.Object3D): void {
    root.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        object.castShadow = true;
        object.receiveShadow = true;
      }
    });
  }

  private render(): void {
    this.renderer.render(this.scene, this.camera);
  }

  private resize = (): void => {
    const width = this.canvas.clientWidth || window.innerWidth;
    const height = this.canvas.clientHeight || window.innerHeight;
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / Math.max(height, 1);
    this.camera.updateProjectionMatrix();
  };
}
