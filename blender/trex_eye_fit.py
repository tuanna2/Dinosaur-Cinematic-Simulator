"""Seat eye components against the measured skull surface, in rest space."""
import bpy,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'blender/dinosaurs/trex/trex_quality_candidate.blend';bpy.ops.wm.open_mainfile(filepath=str(p))
ob=bpy.data.objects['Trex_Atlas_Skin'];me=ob.data
skin={i for i,m in enumerate(me.materials) if m and m.name=='Trex_Refined_PBR'}
bvh=BVHTree.FromPolygons([v.co for v in me.vertices],[list(f.vertices) for f in me.polygons if f.material_index in skin])
for sign in [-1,1]:
 loc,n,idx,dist=bvh.ray_cast(Vector((sign*2,-2.32,3.55)),Vector((-sign,0,0)))
 print('SKULL EYE SURFACE',sign,loc,flush=True)
 if loc is None:raise RuntimeError('No skull intersection')
 for label,cx in [('Fitted amber eye',.732),('Fitted pupil',.784),('Orbital skin',.765)]:
  ids={i for i,m in enumerate(me.materials) if m and m.name==label}
  vv={v for f in me.polygons if f.material_index in ids for v in f.vertices}
  for index in vv:
   v=me.vertices[index]
   if v.co.x*sign<=0:continue
   offset=-.015 if label=='Fitted amber eye' else .013 if label=='Fitted pupil' else -.007
   v.co.x=loc.x+sign*offset+(v.co.x-sign*cx)*.52
   v.co.y=-2.32+(v.co.y+2.32)*.76;v.co.z=3.55+(v.co.z-3.55)*.76
bpy.ops.wm.save_as_mainfile(filepath=str(p));sys.path.insert(0,str(ROOT/'blender'));import export_glb
sys.argv=['export_glb.py','--','--output',str(ROOT/'web/public/assets/dinosaurs/trex_master.glb')];export_glb.main()
