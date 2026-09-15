"""Repair new tail orientation and insertion seam; reduce protruding eyes."""
import bpy,bmesh,sys,shutil,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'));import export_glb
for species in ['velociraptor','trex','triceratops']:
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend';backup=path.with_name(path.stem+'_v5.blend')
    if not backup.exists():shutil.copy2(path,backup)
    bpy.ops.wm.open_mainfile(filepath=str(path));rex=species=='trex';tri=species=='triceratops'
    tail=bpy.data.objects['Continuous tail skin'];ys=[v.co.y for v in tail.data.vertices];start=min(ys);end=max(ys);h=2.65 if rex else 1.85 if tri else .74
    for v in tail.data.vertices:
        t=(v.co.y-start)/(end-start);center=h-.1-t*(.65 if rex or tri else .2);scale=1+.4*(1-t)**2
        v.co.x*=scale;v.co.z=center+(v.co.z-center)*scale
    bm=bmesh.new();bm.from_mesh(tail.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(tail.data);bm.free()
    for ob in [o for o in bpy.context.scene.objects if o.type=='MESH' and o!=tail]:
        chosen=set()
        for p in ob.data.polygons:
            if any(n in ob.data.materials[p.material_index].name for n in ['Amber iris','Obsidian pupil']):chosen.update(p.vertices)
        for i in chosen:
            v=ob.data.vertices[i];side=-1 if v.co.x<0 else 1
            ex=.6142 if rex else .5904 if tri else .18016;ey=2.4345 if rex else 2.13 if tri else .646;ez=3.307 if rex else 1.65 if tri else 1.04215
            center=Vector((side*ex,-ey,ez));v.co=center+(v.co-center)*.6
    bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.argv=['export_glb.py','--','--output',str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb')];export_glb.main()
