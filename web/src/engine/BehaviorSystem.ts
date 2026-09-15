import * as THREE from "three";
import type { DinosaurState } from "./ActorController";

export interface MotionIntent {
  state: DinosaurState;
  targetIds: string[];
  speed: number;
  action: string;
}

export function intentForAction(action: string, targetIds: string[]): MotionIntent {
  if (action === "stalk") return { state: "stalk", targetIds, speed: 0.8, action };
  if (["chase", "run"].includes(action)) return { state: "chase", targetIds, speed: 2.3, action };
  if (["attack", "enter"].includes(action)) return { state: action === "attack" ? "attack" : "walk", targetIds, speed: action === "attack" ? 2.0 : 1.25, action };
  if (["flee", "flee_to_grassland", "scatter", "retreat"].includes(action)) {
    return { state: "flee", targetIds, speed: action === "scatter" ? 2.6 : 2.0, action };
  }
  if (action === "graze") return { state: "graze", targetIds, speed: 0, action };
  if (action === "defend") return { state: "defend", targetIds, speed: 0, action };
  if (action === "react") return { state: "react", targetIds, speed: 0, action };
  if (["roar", "victory_roar"].includes(action)) return { state: "roar", targetIds, speed: 0, action };
  return { state: "idle", targetIds, speed: 0, action };
}

export class BehaviorSystem {
  desiredDirection(
    actorId: string,
    groupId: string,
    intent: MotionIntent,
    actorPosition: THREE.Vector3,
    targetPosition: THREE.Vector3 | null,
    neighbors: readonly THREE.Vector3[],
    minimumTargetDistance = 0,
  ): THREE.Vector3 {
    const direction = new THREE.Vector3();

    if (targetPosition) {
      const destination = targetPosition.clone();
      if (groupId === "raptor_pack" && intent.state !== "flee") {
        destination.add(this.packSlot(actorId, intent.action, minimumTargetDistance));
      }
      direction.subVectors(destination, actorPosition);
    } else {
      direction.set(intent.state === "flee" ? -1 : 1, 0, -0.25);
    }

    direction.y = 0;
    if (intent.state === "flee" && targetPosition) direction.multiplyScalar(-1);
    if (direction.lengthSq() > 0.0001) direction.normalize();

    if (groupId === "raptor_pack") {
      direction.add(this.separation(actorPosition, neighbors).multiplyScalar(0.75));
    }

    direction.y = 0;
    return direction.lengthSq() > 0.0001 ? direction.normalize() : direction;
  }

  private packSlot(actorId: string, action: string, minimumDistance: number): THREE.Vector3 {
    const index = this.stableIndex(actorId, 8);
    const angle = (index / 8) * Math.PI * 2;
    const radius = Math.max(minimumDistance, action === "stalk" ? 5.0 : action === "attack" ? 1.5 : 2.8);
    return new THREE.Vector3(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
  }

  private separation(position: THREE.Vector3, neighbors: readonly THREE.Vector3[]): THREE.Vector3 {
    const force = new THREE.Vector3();
    for (const other of neighbors) {
      const delta = new THREE.Vector3().subVectors(position, other);
      const distanceSq = delta.lengthSq();
      if (distanceSq < 0.0001 || distanceSq > 6.25) continue;
      force.add(delta.normalize().multiplyScalar(1 / Math.max(distanceSq, 0.25)));
    }
    return force;
  }

  private stableIndex(value: string, modulo: number): number {
    let hash = 0;
    for (let i = 0; i < value.length; i += 1) hash = (hash * 31 + value.charCodeAt(i)) >>> 0;
    return hash % modulo;
  }
}
