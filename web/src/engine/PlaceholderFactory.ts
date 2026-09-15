import * as THREE from "three";

const SPECIES_SCALE: Record<string, [number, number, number]> = {
  velociraptor: [1.2, 0.9, 2.6],
  triceratops: [2.2, 1.6, 4.2],
  tyrannosaurus_rex: [2.4, 2.8, 6.0],
};

export function createDinosaurPlaceholder(species: string): THREE.Group {
  const group = new THREE.Group();
  const [sx, sy, sz] = SPECIES_SCALE[species] ?? [1.5, 1.2, 3.0];
  const material = new THREE.MeshStandardMaterial({ color: 0x78866b, roughness: 0.82 });

  const body = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz * 0.55), material);
  body.position.y = sy * 0.75;
  group.add(body);

  const head = new THREE.Mesh(new THREE.BoxGeometry(sx * 0.7, sy * 0.65, sz * 0.28), material);
  head.position.set(0, sy, -sz * 0.38);
  group.add(head);

  const tail = new THREE.Mesh(new THREE.ConeGeometry(sx * 0.32, sz * 0.7, 8), material);
  tail.rotation.x = Math.PI / 2;
  tail.position.set(0, sy * 0.65, sz * 0.52);
  group.add(tail);

  for (const x of [-sx * 0.27, sx * 0.27]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(sx * 0.18, sy * 0.8, sx * 0.2), material);
    leg.position.set(x, sy * 0.25, 0);
    group.add(leg);
  }

  group.userData.isPlaceholder = true;
  group.userData.species = species;
  return group;
}
