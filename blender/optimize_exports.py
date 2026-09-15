"""Validate saved masters; export a bounded browser mesh budget without destructively reducing source foliage."""
import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for species in ['velociraptor','trex','triceratops']:
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
    for ob in bpy.context.scene.objects:
        if ob.type=='MESH':ob.data.validate(verbose=True);ob.data.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    sys.argv=['export_glb.py','--','--output',str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb')]
    sys.path.insert(0,str(ROOT/'blender'));import export_glb;export_glb.main()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/environments/tropical_rainforest.blend'))
for ob in list(bpy.context.scene.objects):
    if ob.type!='MESH':continue
    ob.data.validate();ob.data.update()
    if ob.name.startswith('Layered canopy'):
        bpy.context.view_layer.objects.active=ob
        dec=ob.modifiers.new('Browser leaf budget','DECIMATE');dec.ratio=.13;bpy.ops.object.modifier_apply(modifier=dec.name)
    elif ob.name.startswith('River stone') or ob.name.startswith('Rain pool'):
        bpy.context.view_layer.objects.active=ob
        dec=ob.modifiers.new('Browser clutter budget','DECIMATE');dec.ratio=.3;bpy.ops.object.modifier_apply(modifier=dec.name)
groups={}
for ob in list(bpy.context.scene.objects):
    if ob.type=='MESH':groups.setdefault(tuple(m.name for m in ob.data.materials),[]).append(ob)
for objects in groups.values():
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join()
sys.argv=['export_glb.py','--','--output',str(ROOT/'web/public/assets/environments/tropical_rainforest.glb')];export_glb.main()
