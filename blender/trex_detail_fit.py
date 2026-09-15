"""Fit dental roots to the authored jaw surfaces and remove oversized orbital add-ons."""
import bpy,bmesh,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'blender/dinosaurs/trex/trex_quality_candidate.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 if ob.name.startswith('Upper tooth'):
  for v in ob.data.vertices:v.co.x*=.82;v.co.z+=.115
 if ob.name.startswith('Lower tooth'):
  for v in ob.data.vertices:v.co.x*=.85;v.co.z-=.07
 if ob.name.startswith('Recessed eye') or ob.name.startswith('Pupil'):
  for v in ob.data.vertices:v.co.x+=.065 if v.co.x>0 else -.065
body=bpy.data.objects['Trex_Atlas_Skin'];bm=bmesh.new();bm.from_mesh(body.data);seen=set();remove=[]
for v in bm.verts:
 if v in seen:continue
 stack=[v];comp=[];seen.add(v)
 while stack:
  q=stack.pop();comp.append(q)
  for e in q.link_edges:
   other=e.other_vert(q)
   if other not in seen:seen.add(other);stack.append(other)
 if len(comp)==48 and min(v.co.z for v in comp)>3.4:remove.extend(comp)
if remove:bmesh.ops.delete(bm,geom=remove,context='VERTS')
bm.to_mesh(body.data);bm.free()
# One skinned mesh object with a material primitive per PBR surface lowers draw calls.
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.scene.objects:
 if ob.type=='MESH':ob.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.path.insert(0,str(ROOT/'blender'));import export_glb
sys.argv=['export_glb.py','--','--output',str(ROOT/'web/public/assets/dinosaurs/trex_master.glb')];export_glb.main()
