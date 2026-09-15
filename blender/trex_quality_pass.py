"""Non-destructive proportion and PBR revision of the existing T-Rex master.
No new skeleton, no replacement runtime. Save candidate for browser review.
"""
import bpy, math, shutil, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'blender/dinosaurs/trex/trex_master.blend'
BACKUP=SOURCE.with_name('trex_master_before_quality.blend')
if not BACKUP.exists():shutil.copy2(SOURCE,BACKUP)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
bpy.context.scene.frame_set(1)

def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def sculpt(v):
    x,y,z=v;f=-y
    # Flatten the inflated barrel, retaining the hip/foot landmarks and neck insertion.
    body=(1-smooth((abs(f)-.9)/1.3))*smooth((z-1.15)/.65)
    z+=(2.5-z)*.24*body
    # A deep, broad tyrannosaur skull rather than a round bird-like head.
    head=smooth((f-1.75)/.85)
    sx=math.copysign(.73*(abs(x)/.61)**.78,x) if x else 0
    zz=z-3.10;sz=3.10+math.copysign(abs(zz)**.86*1.28,zz)
    x+=(sx-x)*head;z+=(sz-z)*head
    z+=head*.08*math.exp(-((f-3.3)/.5)**2)
    return Vector((x,y,z))

# Reduce eye/socket size before applying the common anatomical deformation.
for ob in [o for o in bpy.context.scene.objects if o.type=='MESH']:
    eyeverts=set();socketverts=set()
    for p in ob.data.polygons:
        name=ob.data.materials[p.material_index].name
        if 'Amber iris' in name or 'Obsidian pupil' in name:eyeverts.update(p.vertices)
        if 'Mouth and nostril' in name:socketverts.update(p.vertices)
    for sign in [-1,1]:
        ids=[i for i in eyeverts if ob.data.vertices[i].co.x*sign>0]
        if ids:
            center=sum((ob.data.vertices[i].co for i in ids),Vector())/len(ids)
            for i in ids:ob.data.vertices[i].co=center+(ob.data.vertices[i].co-center)*.52
        c=Vector((sign*.58,-2.43,3.25))
        for i in socketverts:
            v=ob.data.vertices[i]
            if (v.co-c).length<.23:v.co=c+(v.co-c)*.58
    for v in ob.data.vertices:v.co=sculpt(v.co)
    ob.data.update()

# Hide the flat insertion cap inside the existing thigh mass, preserving lower joint bridges.
for ob in bpy.context.scene.objects:
    if ob.name.startswith('Joint bridge'):
        for i in range(40):
            v=ob.data.vertices[i];ring=i//20
            c=sculpt(Vector((-.656 if ob.name.endswith('L') else .656,-(.06 if ring else 0),2.65*(.84 if ring else 1))))
            v.co=c+(v.co-c)*(.73 if ring==0 else .82)

# Join skin surfaces for a single packed UV atlas, without remeshing or deleting anatomy.
skins=[]
for ob in bpy.context.scene.objects:
    if ob.type=='MESH' and ob.data.polygons and all('pebbled_skin' in ob.data.materials[i].name for i in {p.material_index for p in ob.data.polygons}):skins.append(ob)
bpy.ops.object.select_all(action='DESELECT')
for ob in skins:ob.select_set(True)
bpy.context.view_layer.objects.active=skins[0];bpy.ops.object.join();body=bpy.context.object;body.name='Trex_Atlas_Skin'
mat=next(m for m in body.data.materials if 'pebbled_skin' in m.name)
body.data.materials.clear();body.data.materials.append(mat)
for p in body.data.polygons:p.material_index=0;p.use_smooth=True
# UV islands follow existing continuous regions; generated textures are baked into this atlas.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.5);bpy.ops.object.mode_set(mode='OBJECT')

mat.name='Trex_PBR_Skin';mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
out=nodes.new('ShaderNodeOutputMaterial');bs=nodes.new('ShaderNodeBsdfPrincipled');links.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Roughness'].default_value=.62
coord=nodes.new('ShaderNodeTexCoord')
def node(kind,**attrs):
 n=nodes.new(kind)
 for k,v in attrs.items():setattr(n,k,v)
 return n
def noise(scale,detail=3):
 n=node('ShaderNodeTexNoise');n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=detail;n.inputs['Roughness'].default_value=.68;links.new(coord.outputs['Object'],n.inputs['Vector']);return n
macro=noise(1.7,4);ramp=node('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.24;ramp.color_ramp.elements[0].color=(.036,.045,.035,1);ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(.19,.145,.087,1);links.new(macro.outputs['Fac'],ramp.inputs[0])
geo=node('ShaderNodeNewGeometry');sep=node('ShaderNodeSeparateXYZ');links.new(geo.outputs['Normal'],sep.inputs[0]);under=node('ShaderNodeMapRange');under.inputs['From Min'].default_value=-.8;under.inputs['From Max'].default_value=.1;under.inputs['To Min'].default_value=.7;under.inputs['To Max'].default_value=0;links.new(sep.outputs['Z'],under.inputs['Value'])
mix=node('ShaderNodeMixRGB',blend_type='MIX');links.new(under.outputs[0],mix.inputs[0]);links.new(ramp.outputs[0],mix.inputs[1]);mix.inputs[2].default_value=(.28,.205,.13,1);links.new(mix.outputs[0],bs.inputs['Base Color'])
# Cell-scale relief, fine grain and broader irregular skin folds.
voro=node('ShaderNodeTexVoronoi',feature='DISTANCE_TO_EDGE');voro.inputs['Scale'].default_value=40;links.new(coord.outputs['Object'],voro.inputs['Vector'])
cell=node('ShaderNodeMapRange');cell.interpolation_type='SMOOTHERSTEP';cell.inputs['From Min'].default_value=.015;cell.inputs['From Max'].default_value=.12;links.new(voro.outputs['Distance'],cell.inputs['Value'])
bump=node('ShaderNodeBump');bump.inputs['Strength'].default_value=.48;bump.inputs['Distance'].default_value=.015;links.new(cell.outputs[0],bump.inputs['Height'])
grain=noise(170,2);fine=node('ShaderNodeBump');fine.inputs['Strength'].default_value=.2;fine.inputs['Distance'].default_value=.002;links.new(grain.outputs['Fac'],fine.inputs['Height']);links.new(bump.outputs[0],fine.inputs['Normal'])
fold=noise(7,5);foldb=node('ShaderNodeBump');foldb.inputs['Strength'].default_value=.24;foldb.inputs['Distance'].default_value=.02;links.new(fold.outputs['Fac'],foldb.inputs['Height']);links.new(fine.outputs[0],foldb.inputs['Normal']);links.new(foldb.outputs[0],bs.inputs['Normal'])
rough=node('ShaderNodeMapRange');rough.inputs['To Min'].default_value=.43;rough.inputs['To Max'].default_value=.76;links.new(macro.outputs['Fac'],rough.inputs['Value']);links.new(rough.outputs[0],bs.inputs['Roughness'])

scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.device='CPU';scene.render.bake.margin=16
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
textures={};dest=ROOT/'blender/dinosaurs/trex/textures';dest.mkdir(parents=True,exist_ok=True)
for channel,kind in [('albedo','DIFFUSE'),('normal','NORMAL'),('roughness','EMIT')]:
 img=bpy.data.images.new('Trex_'+channel+'_2k',width=2048,height=2048,alpha=False)
 if channel!='albedo':img.colorspace_settings.name='Non-Color'
 target=node('ShaderNodeTexImage');target.image=img;nodes.active=target;target.select=True
 if kind=='EMIT':
  emission=node('ShaderNodeEmission');links.new(rough.outputs[0],emission.inputs['Color']);links.new(emission.outputs[0],out.inputs['Surface'])
 print('BAKING',channel,flush=True);bpy.ops.object.bake(type=kind)
 img.filepath_raw=str(dest/(channel+'.png'));img.file_format='PNG';img.save();img.pack();textures[channel]=img
 if kind=='EMIT':links.new(bs.outputs['BSDF'],out.inputs['Surface'])
# Export only glTF-compatible PBR nodes. Keep procedural material as an editable source.
mat.use_fake_user=True;pbr=bpy.data.materials.new('Trex_Baked_PBR');pbr.use_nodes=True;n=pbr.node_tree.nodes;l=pbr.node_tree.links;s=n.get('Principled BSDF')
for channel,img in textures.items():
 t=n.new('ShaderNodeTexImage');t.image=img
 if channel=='normal':
  nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=1;l.new(t.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],s.inputs['Normal'])
 else:l.new(t.outputs['Color'],s.inputs['Base Color' if channel=='albedo' else 'Roughness'])
body.data.materials[0]=pbr
# Keep the original bones and original action identities.
candidate=SOURCE.with_name('trex_quality_candidate.blend');bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
sys.path.insert(0,str(ROOT/'blender'));import export_glb
sys.argv=['export_glb.py','--','--output',str(ROOT/'web/public/assets/dinosaurs/trex_master.glb')];export_glb.main()
