"""One-time routed structural revision of the registered T-Rex source.
Preserve the rig/actions and mouth parts; fuse the existing exterior skin volumes,
shape the thigh/neck masses, and transfer original UVs and weights spatially.
"""
import bpy,bmesh,json,sys,shutil,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
asset=next(a for a in json.loads((ROOT/'config/asset_catalog.json').read_text())['assets'] if a['id']=='dino_trex_master')
p=ROOT/asset['blender_source'];backup=p.with_name(p.stem+'_before_structural.blend')
if not backup.exists():shutil.copy2(p,backup)
bpy.ops.wm.open_mainfile(filepath=str(p))
if bpy.context.scene.get('trex_structural_revision'):raise RuntimeError('Already revised; use preserved source intentionally for a new experiment')
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
body=bpy.data.objects['Trex_Atlas_Skin'];skinidx={i for i,m in enumerate(body.data.materials) if m and m.name=='Trex_Refined_PBR'}
# Partition by existing bone assignment, keeping the articulated mandible separate.
source=body.copy();source.data=body.data.copy();bpy.context.collection.objects.link(source);source.name='Structural_transfer_source'
jaw=body.vertex_groups.get('jaw').index
keep=[]
for f in source.data.polygons:
 isjaw=all(any(g.group==jaw and g.weight>.95 for g in source.data.vertices[i].groups) for i in f.vertices)
 if f.material_index in skinidx and not isjaw:keep.append(f.index)
bm=bmesh.new();bm.from_mesh(source.data);bm.faces.ensure_lookup_table();sel=set(keep)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index not in sel],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(source.data);bm.free()
# Shape existing vertices with broad, continuous fields rather than add new blobs.
for v in source.data.vertices:
 x,y,z=v.co;groups={source.vertex_groups[g.group].name:g.weight for g in v.groups}
 thigh=sum(groups.get(k,0) for k in ['thigh_L','thigh_R'])
 taper=.30*math.exp(-((z-1.60)/.46)**2)*thigh
 if abs(x)>.25:
  cx=math.copysign(.656,x);v.co.x=cx+(x-cx)*(1-taper);v.co.y=-.45+(y+.45)*(1-taper)
 neck=math.exp(-((y+1.5)/.56)**2-((z-2.85)/.62)**2)
 v.co.x*=1+.23*neck
# Remove only those exterior faces from the original object. Accessories and jaw remain.
bm=bmesh.new();bm.from_mesh(body.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index in sel],context='FACES');bm.to_mesh(body.data);bm.free()
# Repair duplicate sphere poles/boundaries before constructing a continuous exterior.
work=source.copy();work.data=source.data.copy();bpy.context.collection.objects.link(work);work.name='Trex_Continuous_Skin'
for mod in list(work.modifiers):work.modifiers.remove(mod)
bm=bmesh.new();bm.from_mesh(work.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00005);bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(work.data);bm.free()
bpy.ops.object.select_all(action='DESELECT');work.select_set(True);bpy.context.view_layer.objects.active=work
work.data.remesh_voxel_size=.027;work.data.use_remesh_preserve_volume=True;work.data.use_remesh_preserve_attributes=False
bpy.ops.object.voxel_remesh();print('REMESH',len(work.data.vertices),tuple(work.dimensions),flush=True)
if len(work.data.vertices)<10000 or work.dimensions.y<9 or work.dimensions.z<3.5:raise RuntimeError('Exterior volume lost; source has NOT been saved')
# Smooth only anatomical junctions strongly; protect feet, jaw line and facial silhouette.
g=work.vertex_groups.new(name='Structural_blend')
for v in work.data.vertices:
 x,y,z=v.co
 tail=math.exp(-((y-1.75)/.58)**2)
 hip=math.exp(-((abs(x)-.69)/.35)**2-((z-2.25)/.65)**2-((y-.02)/.7)**2)
 neck=math.exp(-((y+1.70)/.35)**2-((z-2.95)/.55)**2)
 w=max(tail,hip,neck)
 if z>.9 and w>.02:g.add([v.index],w,'REPLACE')
sm=work.modifiers.new('Continuous anatomical transitions','SMOOTH');sm.factor=1.0;sm.iterations=18;sm.vertex_group=g.name;bpy.ops.object.modifier_apply(modifier=sm.name)
# Use the shaped source, with its armature disabled, for rest-space interpolation.
for m in source.modifiers:m.show_viewport=False;m.show_render=False
for vg in list(work.vertex_groups):work.vertex_groups.remove(vg)
dt=work.modifiers.new('Transfer stable skeleton weights','DATA_TRANSFER');dt.object=source;dt.use_vert_data=True;dt.data_types_verts={'VGROUP_WEIGHTS'};dt.vert_mapping='POLYINTERP_NEAREST';bpy.ops.object.datalayout_transfer(modifier=dt.name);bpy.ops.object.modifier_apply(modifier=dt.name)
dt=work.modifiers.new('Transfer original UV atlas','DATA_TRANSFER');dt.object=source;dt.use_loop_data=True;dt.data_types_loops={'UV'};dt.loop_mapping='POLYINTERP_NEAREST';bpy.ops.object.datalayout_transfer(modifier=dt.name);bpy.ops.object.modifier_apply(modifier=dt.name)
mat=bpy.data.materials['Trex_Refined_PBR'];work.data.materials.clear();work.data.materials.append(mat)
for f in work.data.polygons:f.material_index=0;f.use_smooth=True
# Normalize transferred groups, retain the same skeleton and embedded Actions.
for v in work.data.vertices:
 total=sum(g.weight for g in v.groups)
 if total<.001:raise RuntimeError('Unweighted exterior vertex')
 for g in list(v.groups):work.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
m=work.modifiers.new('Skin','ARMATURE');m.object=rig;work.parent=rig
bpy.data.objects.remove(source,do_unlink=True)
bm=bmesh.new();bm.from_mesh(work.data);bad=sum(not e.is_manifold for e in bm.edges);bm.free()
print('STRUCTURAL_VALIDATION',json.dumps({'vertices':len(work.data.vertices),'nonmanifold_edges':bad,'bones':list(rig.data.bones.keys()),'actions':[a.name for a in bpy.data.actions]}),flush=True)
if bad:raise RuntimeError('Nonmanifold exterior')
bpy.context.scene['trex_structural_revision']=1
bpy.ops.wm.save_as_mainfile(filepath=str(p))
sys.path.insert(0,str(ROOT/'blender'));import export_glb
sys.argv=['export_glb.py','--','--output',str(ROOT/asset['export_path'])];export_glb.main()
