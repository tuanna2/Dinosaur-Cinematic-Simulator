import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import * as SkeletonUtils from "three/addons/utils/SkeletonUtils.js";
import type { AssetManifest } from "../types";

export class AssetRegistry {
  private readonly paths = new Map<string, string>();
  private readonly templates = new Map<string, THREE.Object3D>();
  private readonly loader = new GLTFLoader();

  constructor(manifest: AssetManifest) {
    for (const asset of manifest.assets) {
      if (asset.web_path) this.paths.set(asset.id, asset.web_path);
    }
  }

  async instantiate(assetId: string): Promise<THREE.Object3D | null> {
    const path = this.paths.get(assetId);
    if (!path) return null;

    let template = this.templates.get(assetId);
    if (!template) {
      const gltf = await this.loader.loadAsync(path);
      template = gltf.scene;
      this.templates.set(assetId, template);
    }

    return SkeletonUtils.clone(template);
  }
}
