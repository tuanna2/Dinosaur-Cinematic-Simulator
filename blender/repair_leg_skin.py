"""Continuous joint-spanning leg surfaces on existing bones; correct albedo readability."""
import bpy,bmesh,sys,shutil,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'))
from bootstrap_assets import tube
import export_glb
for species in ['velociraptor','trex','triceratops']:
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend';backup=path.with_name(path.stem+'_v6.blend')
    if not backup.exists():shutil.copy2(path,backup)
    bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];rex=species=='trex';tri=species=='triceratops';h=2.65 if rex else 1.85 if tri else .74;width=.8 if rex else 1.05 if tri else .23
    for ob in [o for o in bpy.context.scene.objects if o.type=='MESH']:
        bad={g.index for g in ob.vertex_groups if g.name.startswith(('thigh','shin'))};bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table()
        remove=[bm.verts[v.index] for v in ob.data.vertices if sum(g.weight for g in v.groups if g.group in bad)>.5]
        bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(ob.data);bm.free()
        sockets=set()
        for p in ob.data.polygons:
            if 'Mouth and nostril' in ob.data.materials[p.material_index].name:sockets.update(p.vertices)
        ex=.58 if rex else .56 if tri else .168;ey=2.4345 if rex else 2.13 if tri else .646;ez=3.307 if rex else 1.65 if tri else 1.04215;rad=.09 if rex else .08 if tri else .032
        for idx in sockets:
            v=ob.data.vertices[idx];c=Vector((math.copysign(ex,v.co.x),-ey,ez))
            if (v.co-c).length<rad*2.1:v.co=c+(v.co-c)*.6
    skin=next(m for m in bpy.data.materials if m.name.startswith(species+'_pebbled_skin'))
    for side,sign in [('L',-1),('R',1)]:
        x=sign*width*.82
        pts=[(x,0,h+.03),(x,.06,h*.84),(x,.28,h*.65),(x,.45,h*.48),(x,.30,h*.35),(x,.06,h*.22),(x,-.1,h*.14),(x,.03,.13 if rex or tri else .055)]
        radii=[width*.50,width*.54,width*.39,width*.26,width*.22,width*.16,width*.12,width*.14]
        ob=tube('Continuous hindlimb '+side,pts,radii,skin,None,24);ob.parent=rig
        groups={n:ob.vertex_groups.new(name=n) for n in ['pelvis','thigh_'+side,'shin_'+side,'foot_'+side]}
        ringweights=[{'pelvis':.25,'thigh_'+side:.75},{'thigh_'+side:1},{'thigh_'+side:1},{'thigh_'+side:.5,'shin_'+side:.5},{'shin_'+side:1},{'shin_'+side:1},{'shin_'+side:.3,'foot_'+side:.7},{'foot_'+side:1}]
        for v in ob.data.vertices:
            for name,w in ringweights[v.index//24].items():groups[name].add([v.index],w,'REPLACE')
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(ob.data);bm.free()
        mod=ob.modifiers.new('Skin','ARMATURE');mod.object=rig
    import numpy as np
    for img in bpy.data.images:
        if 'scales' in img.name:
            a=np.array(img.pixels[:],dtype=np.float32).reshape(-1,4);a[:,:3]=a[:,:3]**.72;img.pixels.foreach_set(a.ravel());img.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.argv=['export_glb.py','--','--output',str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb')];export_glb.main()
