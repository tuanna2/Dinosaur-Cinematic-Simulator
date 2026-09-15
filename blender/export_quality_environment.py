"""Export the saved environment candidate without reauthoring its contents."""
import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"blender"))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/"blender/environments/tropical_rainforest_quality_candidate.blend"))
for ob in list(bpy.context.scene.objects):
 if ob.type!='MESH':continue
 bpy.context.view_layer.objects.active=ob
 ratio=.13 if ob.name.startswith('Layered canopy') else .5 if ob.name.startswith('Layered edge foliage') else .3 if ob.name.startswith(('River stone','Rain pool')) else 1
 if ratio<1:
  dec=ob.modifiers.new('Export budget','DECIMATE');dec.ratio=ratio;bpy.ops.object.modifier_apply(modifier=dec.name)
groups={}
for ob in list(bpy.context.scene.objects):
 if ob.type=='MESH':groups.setdefault(tuple(m.name for m in ob.data.materials),[]).append(ob)
for obs in groups.values():
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:ob.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join()
import export_glb;sys.argv=['export_glb.py','--','--output',str(ROOT/'web/public/assets/environments/tropical_rainforest.glb')];export_glb.main()
