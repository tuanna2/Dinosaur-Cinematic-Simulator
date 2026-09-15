"""Register workshop exports via the repository's asset registration entry point."""
import argparse, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('--status',choices=['draft','approved'],default='draft'); a=p.parse_args()
for species,clips in [('velociraptor',['stalk','run','attack','react','flee']),('trex',['walk','roar','attack']),('triceratops',['graze','run','defend']),('environment',[])]:
    env=species=='environment'
    source='blender/environments/tropical_rainforest.blend' if env else f'blender/dinosaurs/{species}/{species}_master.blend'
    path='/assets/environments/tropical_rainforest.glb' if env else f'/assets/dinosaurs/{species}_master.glb'
    ids=[('env_tropical_rainforest','environment')] if env else [(f'dino_{species}_master','dinosaur')]+[(f'anim_{"raptor" if species=="velociraptor" else species}_{clip}','animation') for clip in clips]
    for id,kind in ids:
        subprocess.run([sys.executable,'pipeline/register_asset.py',id,'--type',kind,'--status',a.status,'--blender-source',source,'--export-path','web/public'+path,'--web-path',path,'--species','tyrannosaurus_rex' if species=='trex' else species,'--skeleton-id',species+'_v1' if not env else 'none','--notes','Reviewed for reusable bootstrap previews only; cinematic visual target remains unmet. See docs/VISUAL_BOOTSTRAP_REVIEW.md.','--replace'],cwd=ROOT,check=True)
