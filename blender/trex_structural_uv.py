"""Rebake the existing skin shader after structural remeshing; no new micro-detail."""
import bpy,sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];a=next(a for a in json.loads((ROOT/'config/asset_catalog.json').read_text())['assets'] if a['id']=='dino_trex_master');p=ROOT/a['blender_source'];bpy.ops.wm.open_mainfile(filepath=str(p))
body=bpy.data.objects['Trex_Continuous_Skin'];skin=bpy.data.materials['Trex_PBR_Skin'];body.data.materials.clear();body.data.materials.append(skin)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.5);bpy.ops.object.mode_set(mode='OBJECT')
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.margin=20;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
nodes=skin.node_tree.nodes;links=skin.node_tree.links;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');links.new(bs.outputs[0],out.inputs['Surface']);roughlink=bs.inputs['Roughness'].links[0].from_socket
textures={};dest=ROOT/'blender/dinosaurs/trex/textures';dest.mkdir(exist_ok=True)
for channel,kind in [('albedo','DIFFUSE'),('normal','NORMAL'),('roughness','EMIT')]:
 img=bpy.data.images.new('Trex_structural_'+channel,width=2048,height=2048,alpha=False)
 if channel!='albedo':img.colorspace_settings.name='Non-Color'
 target=nodes.new('ShaderNodeTexImage');target.image=img;nodes.active=target
 if kind=='EMIT':e=nodes.new('ShaderNodeEmission');links.new(roughlink,e.inputs['Color']);links.new(e.outputs[0],out.inputs['Surface'])
 print('BAKE',channel,flush=True);bpy.ops.object.bake(type=kind);img.filepath_raw=str(dest/('structural_'+channel+'.png'));img.file_format='PNG';img.save();img.pack();textures[channel]=img
 if kind=='EMIT':links.new(bs.outputs[0],out.inputs['Surface']);nodes.remove(e)
pbr=bpy.data.materials.new('Trex_Continuous_PBR');pbr.use_nodes=True;n=pbr.node_tree.nodes;l=pbr.node_tree.links;s=n.get('Principled BSDF')
for channel,img in textures.items():
 t=n.new('ShaderNodeTexImage');t.image=img
 if channel=='normal':nm=n.new('ShaderNodeNormalMap');l.new(t.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs[0],s.inputs['Normal'])
 else:l.new(t.outputs['Color'],s.inputs['Base Color' if channel=='albedo' else 'Roughness'])
body.data.materials[0]=pbr;bpy.ops.wm.save_as_mainfile(filepath=str(p));sys.path.insert(0,str(ROOT/'blender'));import export_glb
sys.argv=['export_glb.py','--','--output',str(ROOT/a['export_path'])];export_glb.main()
