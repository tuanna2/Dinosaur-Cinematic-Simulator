"""Replace only the existing skull/mandible surfaces with authored anatomical loops.
Keep torso, stable skeleton names, embedded action library and source revision history.
"""
import bpy,bmesh,sys,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'))
from bootstrap_assets import mesh,tube,ell,material
path=ROOT/'blender/dinosaurs/trex/trex_quality_candidate.blend';bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
# Remove old head accessories by their existing rigid bone groups.
for ob in list(bpy.context.scene.objects):
 if ob.type!='MESH' or ob.name=='Trex_Atlas_Skin':continue
 ids={g.index for g in ob.vertex_groups if g.name in ['head','jaw']};bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table()
 delete=[bm.verts[v.index] for v in ob.data.vertices if sum(g.weight for g in v.groups if g.group in ids)>.95]
 bmesh.ops.delete(bm,geom=delete,context='VERTS');bm.to_mesh(ob.data);bm.free()
# Cut at a reusable neck insertion; do not remesh or regenerate the intact torso.
body=bpy.data.objects['Trex_Atlas_Skin'];bm=bmesh.new();bm.from_mesh(body.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,-1.91,0),plane_no=(0,-1,0),clear_outer=True)
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bm.to_mesh(body.data);bm.free()
# Hinge moves with the revised anatomical skull; all action/bone names remain stable.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
rig.data.edit_bones['jaw'].head=(0,-2.10,3.04);rig.data.edit_bones['jaw'].tail=(0,-3.35,3.04);bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False)
skin=bpy.data.materials['Trex_PBR_Skin'];dark=material('Oral mucosa',(.035,.006,.008),.5);ivory=material('Dentine',(.57,.49,.34),.36);iris=material('Natural amber iris',(.19,.085,.009),.25);black=material('Eye pupil and nares',(.005,.004,.003),.3);tongue=material('Tongue',(.105,.025,.027),.5)
created=[]
def attach(ob,bone):
 if bone not in ob.vertex_groups:ob.vertex_groups.new(name=bone).add(list(range(len(ob.data.vertices))),1,'REPLACE')
 ob.parent=rig;m=ob.modifiers.new('Skin','ARMATURE');m.object=rig
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(ob.data);bm.free();created.append(ob);return ob

def cat(a,b,c,d,t):return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
def loft(name,controls,bone):
 # Controls: forward, centre height, half width, upper half-height, lower half-height.
 rows=[]
 for i in range(len(controls)-1):
  for j in range(7):rows.append([cat(controls[max(0,i-1)][k],controls[i][k],controls[i+1][k],controls[min(len(controls)-1,i+2)][k],j/7) for k in range(5)])
 rows.append(controls[-1]);verts=[];faces=[];N=40
 for f,z,w,up,down in rows:
  for j in range(N):
   a=j*math.tau/N;co=math.cos(a);si=math.sin(a);x=math.copysign(w*abs(co)**.64,co);zz=z+math.copysign((up if si>0 else down)*abs(si)**.72,si)
   if bone=='head':
    # Recess the eye socket and antorbital cheek; raise a continuous brow.
    side=abs(x)/max(.001,w);recess=.10*math.exp(-((f-2.31)/.18)**2-((zz-3.53)/.14)**2)
    recess+=.04*math.exp(-((f-2.75)/.30)**2-((zz-3.39)/.17)**2)
    ridge=.055*math.exp(-((f-2.28)/.28)**2-((zz-3.75)/.11)**2)
    x+=math.copysign((ridge-recess)*side,x)
   verts.append((x,f,zz))
 for i in range(len(rows)-1):
  for j in range(N):k=i*N+j;l=i*N+(j+1)%N;faces.append((k,l,l+N,k+N))
 faces.extend([tuple(range(N-1,-1,-1)),tuple((len(rows)-1)*N+j for j in range(N))])
 return attach(mesh(name,verts,faces,skin),bone)
upper=loft('Anatomical skull',[(1.68,3.02,.36,.42,.36),(1.94,3.27,.50,.49,.34),(2.20,3.40,.65,.46,.37),(2.48,3.42,.72,.39,.35),(2.8,3.38,.65,.32,.28),(3.15,3.36,.56,.29,.25),(3.55,3.31,.45,.27,.23),(3.76,3.26,.27,.22,.18),(3.82,3.24,.025,.03,.03)],'head')
lower=loft('Anatomical mandible',[(2.03,3.00,.52,.15,.18),(2.30,2.94,.58,.10,.20),(2.65,2.92,.58,.08,.18),(3.05,2.94,.51,.08,.15),(3.45,2.99,.40,.08,.12),(3.70,3.02,.22,.07,.09),(3.77,3.02,.015,.015,.02)],'jaw')
for sign in [-1,1]:
 attach(ell('Recessed eye',(sign*.65,2.29,3.54),(.038,.060,.055),iris),'head')
 attach(ell('Pupil',(sign*.684,2.291,3.54),(.008,.023,.037),black),'head')
 attach(ell('Naris',(sign*.48,3.42,3.46),(.012,.095,.039),black),'head')
 # Sculpted orbital rim follows the skull surface rather than a separate floating sphere.
 attach(tube('Orbital ridge',[(sign*.57,2.04,3.67),(sign*.68,2.23,3.75),(sign*.73,2.47,3.73),(sign*.67,2.61,3.64)],[.065,.083,.070,.035],skin,None,12),'head')
 for j in range(14):
  f=2.48+j*.083;w=.65-(f-2.48)*.21;z=3.075+.014*(f-2.5);size=.11+.08*math.sin(math.pi*(j+1)/15)
  attach(tube('Upper tooth',[(sign*w,f,z),(sign*(w-.015),f-.014,z-size*.6),(sign*(w-.02),f-.045,z-size)],[.042,.026,.001],ivory,None,10),'head')
  attach(tube('Lower tooth',[(sign*(w-.04),f,3.025),(sign*(w-.045),f-.012,3.10),(sign*(w-.05),f-.03,3.145)],[.029,.020,.001],ivory,None,10),'jaw')
attach(ell('Palate',(0,2.95,3.10),(.45,.67,.035),dark),'head');attach(ell('Tongue',(0,2.94,3.015),(.40,.65,.027),tongue),'jaw')
# Reuse and tune the source PBR material, reducing the sandy high-frequency relief.
ns=skin.node_tree.nodes
for n in ns:
 if n.bl_idname=='ShaderNodeTexVoronoi':n.inputs['Scale'].default_value=28
 if n.bl_idname=='ShaderNodeBump':n.inputs['Distance'].default_value*=.32;n.inputs['Strength'].default_value*=.65
# Atlas all skin surfaces; no destructive surface fusion.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in created:
 if o.data.materials[0]==skin:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body=bpy.context.object
body.data.materials.clear();body.data.materials.append(skin)
for p in body.data.polygons:p.material_index=0;p.use_smooth=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.5);bpy.ops.object.mode_set(mode='OBJECT')
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.margin=16;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
nodes=skin.node_tree.nodes;links=skin.node_tree.links;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');roughlink=bs.inputs['Roughness'].links[0].from_socket
textures={};dest=ROOT/'blender/dinosaurs/trex/textures'
for channel,kind in [('albedo','DIFFUSE'),('normal','NORMAL'),('roughness','EMIT')]:
 img=bpy.data.images.new('Trex_refined_'+channel,width=2048,height=2048,alpha=False)
 if channel!='albedo':img.colorspace_settings.name='Non-Color'
 target=nodes.new('ShaderNodeTexImage');target.image=img;nodes.active=target
 if kind=='EMIT':e=nodes.new('ShaderNodeEmission');links.new(roughlink,e.inputs['Color']);links.new(e.outputs[0],out.inputs['Surface'])
 print('BAKE',channel,flush=True);bpy.ops.object.bake(type=kind);img.filepath_raw=str(dest/(channel+'.png'));img.file_format='PNG';img.save();img.pack();textures[channel]=img
 if kind=='EMIT':links.new(bs.outputs[0],out.inputs['Surface'])
pbr=bpy.data.materials.new('Trex_Refined_PBR');pbr.use_nodes=True;n=pbr.node_tree.nodes;l=pbr.node_tree.links;s=n.get('Principled BSDF')
for channel,img in textures.items():
 t=n.new('ShaderNodeTexImage');t.image=img
 if channel=='normal':nm=n.new('ShaderNodeNormalMap');l.new(t.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs[0],s.inputs['Normal'])
 else:l.new(t.outputs['Color'],s.inputs['Base Color' if channel=='albedo' else 'Roughness'])
body.data.materials[0]=pbr;body.data.validate();bpy.ops.wm.save_as_mainfile(filepath=str(path))
import export_glb;sys.argv=['export_glb.py','--','--output',str(ROOT/'web/public/assets/dinosaurs/trex_master.glb')];export_glb.main()
