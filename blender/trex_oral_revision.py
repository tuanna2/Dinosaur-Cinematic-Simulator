"""Fit visible eye surfaces and dental roots on the existing candidate, retaining UVs/rig."""
import bpy,bmesh,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'))
from bootstrap_assets import ell,tube,material
path=ROOT/'blender/dinosaurs/trex/trex_quality_candidate.blend'
bpy.ops.wm.open_mainfile(filepath=str(path));body=bpy.data.objects['Trex_Atlas_Skin'];rig=bpy.data.objects['Rig']
rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
# Remove the obscured eye and dental primitives; retain all baked skin vertices.
slots={i for i,m in enumerate(body.data.materials) if m and m.name in ['Natural amber iris','Dentine']}
black={i for i,m in enumerate(body.data.materials) if m and m.name=='Eye pupil and nares'}
bm=bmesh.new();bm.from_mesh(body.data)
faces=[f for f in bm.faces if f.material_index in slots or (f.material_index in black and sum(v.co.y for v in f.verts)/len(f.verts)>-2.6)]
bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(body.data);bm.free()
iris=material('Fitted amber eye',(.32,.15,.027),.22);pupil=material('Fitted pupil',(.002,.003,.002),.18);lid=material('Orbital skin',(.105,.075,.035),.62);tooth=material('Tapered dentine',(.46,.39,.25),.4);gum=material('Gingival edge',(.085,.043,.027),.63)
created=[]
def attach(ob,bone):
 ob.vertex_groups.new(name=bone).add(list(range(len(ob.data.vertices))),1,'REPLACE');ob.parent=rig;m=ob.modifiers.new('Skin','ARMATURE');m.object=rig
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(ob.data);bm.free();created.append(ob)
for sign in [-1,1]:
 attach(ell('Eye globe',(sign*.732,2.32,3.55),(.057,.092,.070),iris),'head')
 attach(ell('Eye pupil',(sign*.784,2.326,3.552),(.009,.034,.045),pupil),'head')
 pts=[(sign*(.753+.02*math.sin(i*math.pi/12)),2.32+.094*math.cos(i*math.pi/12),3.55+.072*math.sin(i*math.pi/12)) for i in range(13)]
 attach(tube('Upper eyelid',pts,[.018]*13,lid,None,10),'head')
 for j in range(13):
  f=2.49+j*.084;w=(.65-(f-2.48)*.21)*.82;z=3.18;length=.12+.07*math.sin(math.pi*(j+1)/14)
  attach(tube('Upper dental',[(sign*w,f,z),(sign*(w-.004),f-.003,z-length*.38),(sign*(w-.012),f-.023,z-length*.76),(sign*(w-.018),f-.046,z-length)],[.030,.027,.016,.001],tooth,None,12),'head')
  wl=(.61-(f-2.48)*.21)*.85;zl=2.995
  attach(tube('Lower dental',[(sign*wl,f,zl),(sign*wl,f-.009,zl+.054),(sign*(wl-.008),f-.032,zl+.105)],[.026,.019,.001],tooth,None,12),'jaw')
 pts=[(sign*(.65-(2.46+i*.045-2.48)*.21)*.82,2.46+i*.045,3.176) for i in range(25)]
 attach(tube('Upper gingiva',pts,[.037]*25,gum,None,12),'head')
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for ob in created:ob.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
bpy.ops.wm.save_as_mainfile(filepath=str(path))
import export_glb
sys.argv=['export_glb.py','--','--output',str(ROOT/'web/public/assets/dinosaurs/trex_master.glb')];export_glb.main()
