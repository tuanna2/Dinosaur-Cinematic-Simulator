"""Revision 3: restore anatomical detail and correct environment shading in saved masters."""
import bpy, math, random, sys, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'blender'))
from bootstrap_assets import mesh, ell, tube, material, parts

def open_master(path):
    backup=path.with_name(path.stem+'_v2.blend')
    if not backup.exists(): shutil.copy2(path,backup)
    bpy.ops.wm.open_mainfile(filepath=str(path))

def export(path,out):
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    bpy.ops.export_scene.gltf(filepath=str(ROOT/out),export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_skins=True)

def dino(species):
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend';open_master(path)
    rig=bpy.data.objects['Rig'];skin=next(m for m in bpy.data.materials if m.name.startswith(species+'_pebbled_skin'))
    if species=='triceratops':
        parts.clear()
        # Closed, deformation-compatible frill rather than a zero-thickness sheet.
        ob=ell('Scalloped solid frill',(0,1.77,2.0),(1.12,.19,.97),skin,'head')
        for v in ob.data.vertices:
            a=math.atan2((v.co.z-2)/.97,v.co.x/1.12);r=1+.035*math.cos(a*16); v.co.x*=r;v.co.z=2+(v.co.z-2)*r
        for o in parts: o.parent=rig;mod=o.modifiers.new('Skin','ARMATURE');mod.object=rig
    # Small eyes set into skull rather than protruding marble-like eyeballs.
    for ob in [o for o in bpy.context.scene.objects if o.type=='MESH']:
        for p in ob.data.polygons:
            if 'iris' in ob.data.materials[p.material_index].name:
                pass
    export(path,f'web/public/assets/dinosaurs/{species}_master.glb')

def env():
    path=ROOT/'blender/environments/tropical_rainforest.blend';open_master(path);random.seed(899)
    ground=bpy.data.objects['Continuous wet terrain']
    for p in ground.data.polygons:
        if p.normal.z<0:p.flip()
    # Source leaf modules have their normals corrected to catch skylight consistently.
    for ob in bpy.context.scene.objects:
        if ob.type=='MESH' and any('Canopy' in m.name or 'Grassland' in m.name for m in ob.data.materials):
            for p in ob.data.polygons:
                if p.normal.z<0:p.flip()
    leaf=[bpy.data.materials['Canopy '+str(i)] for i in range(3)]
    for i,m in enumerate(leaf):
        m.diffuse_color=(*[(.045,.10,.023),(.075,.15,.037),(.10,.19,.045)][i],1)
        m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=m.diffuse_color
    buckets=[([],[]) for _ in range(3)]
    def leafblade(c,a,l,w,slot):
        vs,fs=buckets[slot];k=len(vs);dx=math.cos(a);dy=math.sin(a)
        for j in range(7):
            t=j/6;wide=math.sin(math.pi*t)**.8*w;z=c[2]+math.sin(t*math.pi)*.16*l-t*t*.18*l
            for side in [-1,0,1]: vs.append((c[0]+dx*l*t-dy*wide*side,c[1]+dy*l*t+dx*wide*side,z+(.07*l*math.sin(math.pi*t) if side==0 else 0)))
        for j in range(6):
            for side in range(2):fs.append((k+j*3+side,k+(j+1)*3+side,k+(j+1)*3+side+1,k+j*3+side+1))
    for ob in list(bpy.context.scene.objects):
        if not ob.name.startswith('Rainforest trunk'):continue
        coords=[v.co for v in ob.data.vertices]; x=sum(v.x for v in coords)/len(coords);y=-sum(v.y for v in coords)/len(coords);z=max(v.z for v in coords)
        for j in range(180):
            a=random.random()*math.tau;r=random.random()**.5*4
            leafblade((x+math.cos(a)*r,y+math.sin(a)*r,z-random.random()*3),random.random()*math.tau,random.uniform(.8,1.8),random.uniform(.15,.32),j%3)
    # Rich fern-shaped foliage replaces the angular understory leaves.
    for ob in list(bpy.context.scene.objects):
        if ob.name.startswith('Understory fern layer'):bpy.data.objects.remove(ob,do_unlink=True)
    for j in range(650):
        x=random.uniform(-280,80);y=random.choice([-1,1])*random.uniform(12,32)
        for k in range(9):
            a=k*math.tau/9;l=random.uniform(.5,1.5)
            for q in range(7):
                t=q/7;cx=x+math.cos(a)*l*t;cy=y+math.sin(a)*l*t;z=.15+math.sin(t*math.pi)*l*.4
                for s in [-1,1]:leafblade((cx,cy,z),a+s*.85,l*.33*(1-t)+.05,.06,k%3)
    for i,(v,f) in enumerate(buckets):
        o=mesh('Layered canopy and fern modules',v,f,leaf[i])
        for p in o.data.polygons:
            if p.normal.z<0:p.flip()
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    groups={}
    for o in list(bpy.context.scene.objects):
        if o.type=='MESH':groups.setdefault(tuple(m.name for m in o.data.materials),[]).append(o)
    for group in groups.values():
        bpy.ops.object.select_all(action='DESELECT')
        for ob in group:ob.select_set(True)
        bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join()
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'web/public/assets/environments/tropical_rainforest.glb'),export_format='GLB',export_animations=False)

for s in ['triceratops','environment']:env() if s=='environment' else dino(s)
