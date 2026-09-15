"""Weld repaired skin insertions and transfer weights without changing any bone or action."""
import bpy,sys,shutil
from pathlib import Path
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'));import export_glb
for species in ['velociraptor','trex','triceratops']:
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend';backup=path.with_name(path.stem+'_v8.blend')
    if not backup.exists():shutil.copy2(path,backup)
    bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];objs=[]
    for ob in bpy.context.scene.objects:
        if ob.type=='MESH' and ob.data.polygons and all('pebbled_skin' in ob.data.materials[i].name for i in {p.material_index for p in ob.data.polygons}):objs.append(ob)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objs:ob.select_set(True)
    bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='Unified_deforming_skin'
    kd=KDTree(len(ob.data.vertices));weights=[]
    for v in ob.data.vertices:kd.insert(v.co,v.index);weights.append([(g.group,g.weight) for g in v.groups])
    kd.balance()
    for m in list(ob.modifiers):ob.modifiers.remove(m)
    m=ob.modifiers.new('Weld anatomical insertions','REMESH');m.mode='VOXEL';m.voxel_size=.032 if species!='velociraptor' else .01;m.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=m.name)
    m=ob.modifiers.new('Smooth insertions','SMOOTH');m.factor=.8;m.iterations=4;bpy.ops.object.modifier_apply(modifier=m.name)
    m=ob.modifiers.new('Browser triangle budget','DECIMATE');m.ratio=.42;bpy.ops.object.modifier_apply(modifier=m.name)
    indices=list(range(len(ob.data.vertices)))
    for g in ob.vertex_groups:g.remove(indices)
    for v in ob.data.vertices:
        total={}
        for co,i,d in kd.find_n(v.co,4):
            for g,w in weights[i]:total[g]=total.get(g,0)+w/(d+.004)**2
        norm=sum(total.values())
        for g,w in total.items():ob.vertex_groups[g].add([v.index],w/norm,'REPLACE')
    uv=ob.data.uv_layers.new(name='SkinUV')
    for p in ob.data.polygons:
        p.use_smooth=True
        for li in p.loop_indices:
            v=ob.data.vertices[ob.data.loops[li].vertex_index].co;uv.data[li].uv=(-v.y*.29+v.x*.13,v.z*.36)
    ob.data.validate();m=ob.modifiers.new('Skin','ARMATURE');m.object=r;ob.parent=r
    bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.argv=['export_glb.py','--','--output',str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb')];export_glb.main()
