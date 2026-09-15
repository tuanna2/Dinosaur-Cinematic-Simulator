"""Move the edge tree obstructing the reviewed camera corridor, in the saved source."""
import bpy,bmesh,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'blender/environments/tropical_rainforest_quality_candidate.blend';bpy.ops.wm.open_mainfile(filepath=str(p))
# Measured shot_006 camera at (17.06, 8.0, 20.44) in Three.js; tree immediately in front.
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or not ob.name.startswith(('Canopy edge','Buttress','Layered edge foliage')):continue
 bm=bmesh.new();bm.from_mesh(ob.data);seen=set()
 for v in bm.verts:
  if v in seen:continue
  stack=[v];seen.add(v);comp=[]
  while stack:
   q=stack.pop();comp.append(q)
   for e in q.link_edges:
    n=e.other_vert(q)
    if n not in seen:seen.add(n);stack.append(n)
  c=sum((v.co for v in comp),Vector())/len(comp)
  if (c.x-16.07)**2+(c.y+20.06)**2<4.7**2:
   for v in comp:v.co.x+=7
 bm.to_mesh(ob.data);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(p));sys.path.insert(0,str(ROOT/'blender'));import export_quality_environment
