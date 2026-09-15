import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import * as SkeletonUtils from "three/addons/utils/SkeletonUtils.js";
import type { GLTF } from "three/addons/loaders/GLTFLoader.js";
import type { AssetManifest } from "../types";

export interface RuntimeAssetInstance {
  root: THREE.Object3D;
  animations: THREE.AnimationClip[];
}

interface LoadedAsset {
  scene: THREE.Object3D;
  animations: THREE.AnimationClip[];
}

export class AssetRegistry {
  private readonly paths = new Map<string, string>();
  private readonly cache = new Map<string, Promise<LoadedAsset>>();
  private readonly loaded = new Map<string, LoadedAsset>();
  private readonly loader = new GLTFLoader();

  constructor(manifest: AssetManifest) {
    for (const asset of manifest.assets) {
      if (asset.web_path) this.paths.set(asset.id, asset.web_path);
    }
  }

  has(assetId: string): boolean {
    return this.paths.has(assetId);
  }

  async preload(assetIds: Iterable<string>): Promise<void> {
    await Promise.all(
      [...new Set(assetIds)]
        .filter((assetId) => this.paths.has(assetId))
        .map((assetId) => this.load(assetId).then(() => undefined).catch(() => undefined)),
    );
  }

  async instantiate(assetId: string): Promise<RuntimeAssetInstance | null> {
    if (!this.paths.has(assetId)) return null;
    const loaded = await this.load(assetId);
    return {
      root: SkeletonUtils.clone(loaded.scene),
      animations: loaded.animations,
    };
  }

  getAnimationClip(assetId: string): THREE.AnimationClip | null {
    const loaded = this.loaded.get(assetId);
    if (!loaded || loaded.animations.length === 0) return null;
    return this.pickClip(assetId, loaded.animations);
  }

  findEmbeddedClip(animations: THREE.AnimationClip[], animationId: string): THREE.AnimationClip | null {
    if (animations.length === 0) return null;
    return this.pickClip(animationId, animations);
  }

  private load(assetId: string): Promise<LoadedAsset> {
    const cached = this.cache.get(assetId);
    if (cached) return cached;

    const path = this.paths.get(assetId);
    if (!path) return Promise.reject(new Error(`No web_path registered for ${assetId}`));

    const promise = this.loader.loadAsync(path).then((gltf: GLTF) => {
      const value: LoadedAsset = { scene: gltf.scene, animations: gltf.animations };
      this.loaded.set(assetId, value);
      return value;
    });
    this.cache.set(assetId, promise);
    return promise;
  }

  private pickClip(assetId: string, clips: THREE.AnimationClip[]): THREE.AnimationClip {
    const normalizedId = this.normalize(assetId.replace(/^anim_/, ""));
    const exact = clips.find((clip) => this.normalize(clip.name) === normalizedId);
    if (exact) return exact;

    const actionName = normalizedId.split("_").at(-1) ?? normalizedId;
    const action = clips.find((clip) => this.normalize(clip.name).endsWith(actionName));
    return action ?? clips[0];
  }

  private normalize(value: string): string {
    return value.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  }
}
