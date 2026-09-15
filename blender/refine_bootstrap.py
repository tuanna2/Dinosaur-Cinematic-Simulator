"""Revision 2: edit existing masters; retain versioned sources and skeleton identity."""
import bpy, sys, math, shutil, random
from pathlib import Path
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'blender'))
from bootstrap_assets import mesh, tube, material

def preserve(path):
    backup=path.with_name(path.stem+'_v1.blend')
    if not backup.exists(): shutil.copy2(path,backup)

def dinosaur(species):
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend'; preserve(path); bpy.ops.wm.open_mainfile(filepath=str(path))
    ob=bpy.data.objects['Skinned_Anatomy']; rig=bpy.data.objects['Rig']; tri=species=='triceratops'; rex=species=='trex'
    # Sculpt proportional refinement on the existing source mesh.
    names={g.index:g.name for g in ob.vertex_groups}; width=.8 if rex else 1.05 if tri else .23; h=2.65 if rex else 1.85 if tri else .74
    for v in ob.data.vertices:
        name=names[v.groups[0].group] if v.groups else ''
        if name.startswith('thigh'):
            x=(-1 if name.endswith('L') else 1)*width*.82
            v.co.x=x+(v.co.x-x)*.8
            v.co.y*=.82
            v.co.z=h*.72+(v.co.z-h*.72)*.79
        # Continuous conical tail envelope replaces the stepped overlapping cylinders.
        if name.startswith('tail'):
            y=v.co.y; length=1.9 if rex else 2 if tri else .62
            if y>length*.8:
                radius=width*.67*max(.012,1-(y-length*.8)/(length*2.65))
                center=h-.1-(y-length)*.12/(length*.75)
                old=math.hypot(v.co.x,v.co.z-center)
                if old>radius:
                    ratio=radius/old; v.co.x*=ratio; v.co.z=center+(v.co.z-center)*ratio
    # Subtler texture contrast; retain packed original artwork.
    import numpy as np
    for img in bpy.data.images:
        if 'scales' not in img.name: continue
        data=np.array(img.pixels[:],dtype=np.float32).reshape(-1,4)
        avg=data[:,:3].mean(axis=0)
        data[:,:3]=avg+(data[:,:3]-avg)*.32
        data[:,:3]*=1.25
        img.pixels.foreach_set(data.ravel()); img.pack()
    # Separate the skin for continuous remeshing; preserve eyes, keratin, oral cavity.
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in ob.data.polygons: p.select='pebbled_skin' in ob.data.materials[p.material_index].name
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    skin=next(o for o in bpy.context.selected_objects if o!=ob)
    # Keep a nearest-surface transfer map for stable original skin weights.
    kd=KDTree(len(skin.data.vertices)); old=[]
    for i,v in enumerate(skin.data.vertices): kd.insert(v.co,i); old.append([(g.group,g.weight) for g in v.groups])
    kd.balance(); bpy.context.view_layer.objects.active=skin
    for mod in list(skin.modifiers): skin.modifiers.remove(mod)
    rem=skin.modifiers.new('Continuous skin surface','REMESH'); rem.mode='VOXEL'; rem.voxel_size=.045 if rex or tri else .014; rem.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=rem.name)
    sm=skin.modifiers.new('Anatomical surface relaxation','SMOOTH'); sm.factor=1.15; sm.iterations=5; bpy.ops.object.modifier_apply(modifier=sm.name)
    dec=skin.modifiers.new('Browser topology budget','DECIMATE'); dec.ratio=.48; bpy.ops.object.modifier_apply(modifier=dec.name)
    for v in skin.data.vertices:
        weights={}
        for co,idx,d in kd.find_n(v.co,4):
            for group,w in old[idx]: weights[group]=weights.get(group,0)+w/(d+.005)**2
        total=sum(weights.values())
        for g,w in weights.items(): skin.vertex_groups[g].add([v.index],w/total,'REPLACE')
    uv=skin.data.uv_layers.new(name='SkinUV')
    for p in skin.data.polygons:
        p.use_smooth=True
        for li in p.loop_indices:
            v=skin.data.vertices[skin.data.loops[li].vertex_index].co
            uv.data[li].uv=(-v.y*.29+v.x*.13,v.z*.36)
    mod=skin.modifiers.new('Skin','ARMATURE'); mod.object=rig
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    bpy.ops.export_scene.gltf(filepath=str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb'),export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_skins=True)

def environment():
    path=ROOT/'blender/environments/tropical_rainforest.blend'; preserve(path); bpy.ops.wm.open_mainfile(filepath=str(path))
    random.seed(3881)
    # Ground material includes original spatial mottling to break up the flat plane.
    import numpy as np
    n=512; y,x=np.mgrid[:n,:n]; arr=np.ones((n,n,4),dtype=np.float32)
    noise=np.random.default_rng(8).random((n,n)); mott=.75+.17*np.sin(x*.041)*np.sin(y*.064)+.1*noise
    for i,c in enumerate([.115,.14,.065]): arr[:,:,i]=c*mott
    img=bpy.data.images.new('Forest floor mottling',width=n,height=n); img.pixels.foreach_set(arr.ravel()); img.pack()
    m=bpy.data.materials['Rain-dark loam']; tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=img; m.node_tree.links.new(tex.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    # Add layered understory modules along clearing edges, including the reveal location.
    leaves=[bpy.data.materials['Canopy '+str(i)] for i in range(3)]; bark=bpy.data.materials['Wet buttress bark']
    buckets=[([],[]) for _ in range(3)]
    for i in range(850):
        x=random.uniform(-290,80); y=random.choice([-1,1])*random.uniform(13,40)
        z=random.uniform(.05,1.8)
        for j in range(12):
            a=j*math.tau/12; length=random.uniform(.6,1.8); w=length*.16; dx=math.cos(a); dy=math.sin(a); vs,fs=buckets[j%3]; k=len(vs)
            vs.extend([(x,y,z),(x+dx*length*.45-dy*w,y+dy*length*.45+dx*w,z+.3),(x+dx*length*.5,y+dy*length*.5,z+.42),(x+dx*length*.45+dy*w,y+dy*length*.45-dx*w,z+.3),(x+dx*length,y+dy*length,z+.18)])
            fs.extend([tuple(k+q for q in f) for f in [(0,1,2),(0,2,3),(1,4,2),(2,4,3)]])
    for i,(v,f) in enumerate(buckets): mesh('Understory fern layer',v,f,leaves[i])
    # Keep editable modules in the master; batch export copy only to reduce draw calls.
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    groups={}
    for ob in list(bpy.context.scene.objects):
        if ob.type=='MESH': groups.setdefault(tuple(m.name for m in ob.data.materials),[]).append(ob)
    for group in groups.values():
        bpy.ops.object.select_all(action='DESELECT')
        for ob in group: ob.select_set(True)
        bpy.context.view_layer.objects.active=group[0]; bpy.ops.object.join()
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'web/public/assets/environments/tropical_rainforest.glb'),export_format='GLB',export_animations=False)

for s in sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['velociraptor','trex','triceratops','environment']:
    environment() if s=='environment' else dinosaur(s)
