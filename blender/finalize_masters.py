"""Restore last intact skin revision, then add joint bridges without deleting body geometry.
Keeps all existing bones/actions and retains the failed surface experiment for inspection.
"""
import bpy,bmesh,sys,shutil,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'));from bootstrap_assets import tube
import export_glb
for species in ['velociraptor','trex','triceratops']:
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend';experiment=path.with_name(path.stem+'_surface_experiment.blend')
    if not experiment.exists():shutil.copy2(path,experiment)
    bpy.ops.wm.open_mainfile(filepath=str(path.with_name(path.stem+'_v4.blend')))
    r=bpy.data.objects['Rig'];rex=species=='trex';tri=species=='triceratops';h=2.65 if rex else 1.85 if tri else .74;width=.8 if rex else 1.05 if tri else .23;length=1.9 if rex else 2 if tri else .62
    skin=next(m for m in bpy.data.materials if m.name.startswith(species+'_pebbled_skin'))
    for side,sign in [('L',-1),('R',1)]:
        x=sign*width*.82
        pts=[(x,0,h),(x,.06,h*.84),(x,.28,h*.65),(x,.45,h*.48),(x,.30,h*.35),(x,.06,h*.22),(x,-.1,h*.14),(x,.03,.13 if rex or tri else .055)]
        radii=[width*.42,width*.43,width*.30,width*.24,width*.20,width*.14,width*.115,width*.12]
        ob=tube('Joint bridge '+side,pts,radii,skin,None,20);ob.parent=r
        groups={n:ob.vertex_groups.new(name=n) for n in ['thigh_'+side,'shin_'+side,'foot_'+side]}
        ringweights=[{'thigh_'+side:1},{'thigh_'+side:1},{'thigh_'+side:1},{'thigh_'+side:.5,'shin_'+side:.5},{'shin_'+side:1},{'shin_'+side:1},{'shin_'+side:.3,'foot_'+side:.7},{'foot_'+side:1}]
        for v in ob.data.vertices:
            for name,w in ringweights[v.index//20].items():groups[name].add([v.index],w,'REPLACE')
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(ob.data);bm.free();mod=ob.modifiers.new('Skin','ARMATURE');mod.object=r
    # An enveloping continuous tail covers segment seams, preserving the original skin underneath.
    old=[]
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        tails={g.index for g in ob.vertex_groups if g.name.startswith('tail')}
        for v in ob.data.vertices:
            if sum(g.weight for g in v.groups if g.group in tails)>.5:old.append(v.co.copy())
    start=length*.65;end=max(v.y for v in old)+.02;points=[];rads=[];N=60
    for i in range(N):
        t=i/(N-1);y=start+(end-start)*t;z=h-.1-(y-length)*.12/(length*.75)
        points.append((0,-y,z));near=[math.hypot(v.x,v.z-z) for v in old if abs(v.y-y)<(end-start)/N*1.2]
        rads.append(max(near,default=width*.4*(1-t))+.015)
    for i in range(N-2,-1,-1):rads[i]=max(rads[i],rads[i+1])
    rads[-1]=.005
    ob=tube('Continuous tail envelope',points,rads,skin,None,24);ob.parent=r
    names=['pelvis','tail_01','tail_02','tail_03'];groups={n:ob.vertex_groups.new(name=n) for n in names};anchors=[start,length,length*1.75,length*2.5]
    for v in ob.data.vertices:
        y=v.co.y;i=0
        while i<2 and y>anchors[i+1]:i+=1
        t=max(0,min(1,(y-anchors[i])/(anchors[i+1]-anchors[i])))
        groups[names[i]].add([v.index],1-t,'REPLACE');groups[names[i+1]].add([v.index],t,'REPLACE')
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(ob.data);bm.free();mod=ob.modifiers.new('Skin','ARMATURE');mod.object=r
    import numpy as np
    for img in bpy.data.images:
        if 'scales' in img.name:
            a=np.array(img.pixels[:],dtype=np.float32).reshape(-1,4);a[:,:3]=a[:,:3]**.78;img.pixels.foreach_set(a.ravel());img.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.argv=['export_glb.py','--','--output',str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb')];export_glb.main()
