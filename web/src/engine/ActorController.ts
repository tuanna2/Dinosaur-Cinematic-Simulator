import * as THREE from "three";
import type { AssetRegistry } from "./AssetRegistry";

export type DinosaurState =
  | "idle"
  | "graze"
  | "stalk"
  | "walk"
  | "chase"
  | "flee"
  | "attack"
  | "defend"
  | "react"
  | "roar";

const ONE_SHOT_STATES = new Set<DinosaurState>(["attack", "defend", "react", "roar"]);

export class ActorController {
  readonly mixer: THREE.AnimationMixer;
  state: DinosaurState = "idle";

  private activeAction: THREE.AnimationAction | null = null;
  private activeAnimationId: string | null = null;

  constructor(
    readonly root: THREE.Object3D,
    private readonly embeddedAnimations: THREE.AnimationClip[],
    private readonly assets: AssetRegistry,
  ) {
    this.mixer = new THREE.AnimationMixer(root);
  }

  setState(state: DinosaurState, animationId?: string | null): void {
    this.state = state;
    this.root.userData.behaviorState = state;
    if (!animationId || animationId === this.activeAnimationId) return;

    const clip =
      this.assets.getAnimationClip(animationId) ??
      this.assets.findEmbeddedClip(this.embeddedAnimations, animationId);
    if (!clip) {
      this.root.userData.animationId = animationId;
      this.root.userData.animationMissing = true;
      return;
    }

    const next = this.mixer.clipAction(clip);
    next.enabled = true;
    next.clampWhenFinished = ONE_SHOT_STATES.has(state);
    next.setLoop(ONE_SHOT_STATES.has(state) ? THREE.LoopOnce : THREE.LoopRepeat, Infinity);
    next.reset().fadeIn(0.22).play();
    this.activeAction?.fadeOut(0.22);
    this.activeAction = next;
    this.activeAnimationId = animationId;
    this.root.userData.animationId = animationId;
    this.root.userData.animationMissing = false;
  }

  update(dt: number): void {
    this.mixer.update(dt);
  }

  reset(): void {
    this.mixer.stopAllAction();
    this.activeAction = null;
    this.activeAnimationId = null;
    this.state = "idle";
    this.root.userData.behaviorState = "idle";
  }
}
