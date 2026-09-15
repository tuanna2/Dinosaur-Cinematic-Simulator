"""Close exposed insertion boundaries left by replacing limb and tail surfaces."""
import bpy,bmesh,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'));import export_glb
for species in ['velociraptor','trex','triceratops']:
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend';backup=path.with_name(path.stem+'_v7.blend')
    if not backup.exists():shutil.copy2(path,backup)
    bpy.ops.wm.open_mainfile(filepath=str(path))
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(ob.data);edges=[e for e in bm.edges if e.is_boundary]
        if edges:
            result=bmesh.ops.holes_fill(bm,edges=edges,sides=0);bmesh.ops.triangulate(bm,faces=result.get('faces',[]))
            print(species,ob.name,'closed boundary edges',len(edges))
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(ob.data);bm.free();ob.data.validate()
    bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.argv=['export_glb.py','--','--output',str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb')];export_glb.main()
