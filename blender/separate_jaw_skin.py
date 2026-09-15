"""Restore separately deforming mandible geometry from the original editable master."""
import bpy,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'));import export_glb
for species in ['velociraptor','trex','triceratops']:
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend';backup=path.with_name(path.stem+'_pre_jaw_separation.blend')
    if not backup.exists():shutil.copy2(path,backup)
    bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig']
    # The sloping neck bone has a different roll from the jaw: retain its original pitch.
    for a in bpy.data.actions:
        for layer in a.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        if curve.array_index==0 and curve.data_path=='pose.bones["neck"].rotation_euler':
                            for k in curve.keyframe_points:k.co.y*=-1;k.handle_left.y*=-1;k.handle_right.y*=-1
    if species!='triceratops':
        skin=next(m for m in bpy.data.materials if m.name.startswith(species+'_pebbled_skin'))
        for ob in bpy.context.scene.objects:
            if ob.type!='MESH' or not ob.data.polygons or not all('pebbled_skin' in ob.data.materials[i].name for i in {p.material_index for p in ob.data.polygons}):continue
            jaw=ob.vertex_groups.get('jaw');head=ob.vertex_groups.get('head')
            if not jaw or not head:continue
            for v in ob.data.vertices:
                w=next((g.weight for g in v.groups if g.group==jaw.index),0)
                if w:
                    hw=next((g.weight for g in v.groups if g.group==head.index),0)
                    jaw.remove([v.index]);head.add([v.index],w+hw,'REPLACE');v.co.z+=w*(.11 if species=='trex' else .035)
        with bpy.data.libraries.load(str(path.with_name(path.stem+'_v1.blend')),link=False) as (a,b):b.objects=['Skinned_Anatomy']
        ref=b.objects[0];ji=ref.vertex_groups['jaw'].index
        indices={v.index for v in ref.data.vertices if any(g.group==ji and g.weight>.99 for g in v.groups)}
        faces=[p for p in ref.data.polygons if all(i in indices for i in p.vertices) and 'pebbled_skin' in ref.data.materials[p.material_index].name]
        used=sorted({i for p in faces for i in p.vertices});lookup={old:new for new,old in enumerate(used)}
        me=bpy.data.meshes.new('Mandible');me.from_pydata([ref.data.vertices[i].co for i in used],[],[[lookup[i] for i in p.vertices] for p in faces]);me.materials.append(skin)
        ob=bpy.data.objects.new('Separate skinned mandible',me);bpy.context.collection.objects.link(ob);ob.parent=rig;ob.vertex_groups.new(name='jaw').add(list(range(len(used))),1,'REPLACE');mod=ob.modifiers.new('Skin','ARMATURE');mod.object=rig
        uv=me.uv_layers.new(name='SkinUV')
        for p in me.polygons:
            p.use_smooth=True
            for li in p.loop_indices:
                v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(-v.y*.29+v.x*.13,v.z*.36)
        bpy.data.objects.remove(ref,do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.argv=['export_glb.py','--','--output',str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb')];export_glb.main()
