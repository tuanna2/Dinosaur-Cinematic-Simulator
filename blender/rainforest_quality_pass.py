"""Revise the saved biome: PBR soil, fine grass, layered forest edges and fern modules."""
import bpy,bmesh,math,random,shutil,sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'));from bootstrap_assets import mesh,tube,material
source=ROOT/'blender/environments/tropical_rainforest.blend';backup=source.with_name('tropical_rainforest_before_quality.blend')
if not backup.exists():shutil.copy2(source,backup)
bpy.ops.wm.open_mainfile(filepath=str(source));random.seed(12183)
# Remove the coarse grass/kite understory, retain the detailed tree and fern source modules.
for ob in list(bpy.context.scene.objects):
 if ob.name.startswith(('Meadow grass','Broadleaf clusters','Understory fern layer')):bpy.data.objects.remove(ob,do_unlink=True)

def packed(name,rgb,noncolor=False):
 n=rgb.shape[0];a=np.ones((n,n,4),dtype=np.float32);a[:,:,:3]=rgb
 im=bpy.data.images.new(name,width=n,height=n,alpha=False)
 if noncolor:im.colorspace_settings.name='Non-Color'
 im.pixels.foreach_set(a.ravel());im.pack();return im
n=1024;rng=np.random.default_rng(703)
fy=np.fft.fftfreq(n)[:,None];fx=np.fft.rfftfreq(n)[None,:];freq=np.sqrt(fx*fx+fy*fy)
def field(cut):
 noise=rng.normal(size=(n,n));f=np.fft.rfft2(noise);f*=np.exp(-(freq/cut)**2);a=np.fft.irfft2(f,s=(n,n));return (a-a.min())/(a.max()-a.min())
macro=field(.009);mid=field(.045);fine=field(.25);moss=np.clip((macro-.48)*3,0,.75);wet=np.clip((.40-macro)*4,0,1)
base=np.zeros((n,n,3),np.float32)
for i,(soil,green) in enumerate(zip([.255,.221,.166],[.21,.255,.13])):base[:,:,i]=(soil*(1-moss)+green*moss)*(.72+.28*mid)* (1-.32*wet)
height=.5*mid+.09*fine;dy,dx=np.gradient(height);normal=np.stack([-dx*4,-dy*4,np.ones_like(dx)],axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True);normal=normal*.5+.5
rough=np.repeat((.87-.44*wet+.05*fine)[:,:,None],3,axis=2)
soil=bpy.data.materials['Rain-dark loam'];soil.use_nodes=True;nodes=soil.node_tree.nodes;nodes.clear();links=soil.node_tree.links;bs=nodes.new('ShaderNodeBsdfPrincipled');out=nodes.new('ShaderNodeOutputMaterial');links.new(bs.outputs[0],out.inputs['Surface'])
for name,data,color in [('Forest soil albedo',base,False),('Forest soil normal',normal,True),('Forest soil roughness',rough,True)]:
 im=packed(name,data,color);t=nodes.new('ShaderNodeTexImage');t.image=im
 if 'normal' in name:nm=nodes.new('ShaderNodeNormalMap');links.new(t.outputs[0],nm.inputs['Color']);links.new(nm.outputs[0],bs.inputs['Normal'])
 else:links.new(t.outputs[0],bs.inputs['Roughness' if 'roughness' in name else 'Base Color'])
ground=bpy.data.objects['Continuous wet terrain'];uv=ground.data.uv_layers.active
for p in ground.data.polygons:
 if p.normal.z<0:p.flip()
 for li in p.loop_indices:
  v=ground.data.vertices[ground.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x/8,v.y/8)

# Fine grass in reusable material batches. Dense only near the hero clearing,
# with a cheaper surrounding carpet retained for the long migration corridor.
grassm=[material('Living grass '+str(i),c,.8) for i,c in enumerate([(.085,.14,.032),(.12,.19,.045),(.16,.20,.065)])]
buckets=[([],[]) for _ in grassm]
for i in range(65000):
 if i<42000:x=random.uniform(-32,35);y=random.uniform(-28,32)
 else:x=random.uniform(-290,85);y=random.uniform(-65,85)
 # Organic thin patches and denser margins; no perfect rectangular lawn edge.
 if math.sin(x*.25)+math.cos(y*.36)>1.1 and random.random()<.8:continue
 a=random.random()*math.tau;dx=math.cos(a);dy=math.sin(a);h=random.uniform(.12,.34);w=random.uniform(.005,.013);lean=random.uniform(.025,.12)
 vs,fs=buckets[i%3];k=len(vs)
 for j in range(4):
  t=j/3;ww=w*(1-t*.85)
  vs.extend([(x+dx*lean*t*t-dy*ww,y+dy*lean*t*t+dx*ww,h*t),(x+dx*lean*t*t+dy*ww,y+dy*lean*t*t-dx*ww,h*t)])
 vs.append((x+dx*lean,y+dy*lean,h*1.08))
 fs.extend([(k+j*2,k+j*2+1,k+j*2+3,k+j*2+2) for j in range(3)]);fs.append((k+6,k+7,k+8))
for i,(v,f) in enumerate(buckets):mesh('Fine curved grass '+str(i),v,f,grassm[i])

leafm=[material('Rainforest leaf '+str(i),c,.63) for i,c in enumerate([(.025,.075,.018),(.045,.12,.025),(.075,.15,.035)])];buckets=[([],[]) for _ in leafm]
def leaf(c,a,length,width,slot,rise=.18):
 vs,fs=buckets[slot];k=len(vs);dx=math.cos(a);dy=math.sin(a)
 for j in range(6):
  t=j/5;w=math.sin(math.pi*t)**.8*width;z=c[2]+math.sin(t*math.pi)*rise-t*t*rise*.45
  for s in [-1,0,1]:vs.append((c[0]+dx*length*t-dy*w*s,c[1]+dy*length*t+dx*w*s,z+(.045*length*math.sin(math.pi*t) if s==0 else 0)))
 for j in range(5):
  for s in range(2):fs.append((k+j*3+s,k+(j+1)*3+s,k+(j+1)*3+s+1,k+j*3+s+1))
# Reusable broadleaf trees along the clearing's near edges.
bark=bpy.data.materials['Wet buttress bark']
for ix in range(7):
 for row in [-1,1]:
  x=-25+ix*8+random.uniform(-2,2);y=row*random.uniform(17,25);h=random.uniform(10,16);rad=random.uniform(.22,.42)
  tube('Canopy edge trunk',[(x,y,0),(x+.2,y,h*.5),(x-.35,y+.15,h)],[rad*1.7,rad,rad*.3],bark,None,12)
  for j in range(5):
   a=j*math.tau/5;tube('Buttress',[(x+math.cos(a)*rad*4,y+math.sin(a)*rad*4,.025),(x,y,1.7)],[rad*.35,rad*.45],bark,None,8)
  for j in range(8):
   a=j*math.tau/8;c=(x+math.cos(a)*2.8,y+math.sin(a)*2.8,h-random.random()*2.4)
   tube('Canopy edge branch',[(x,y,h*.66),c],[rad*.36,.04],bark,None,8)
   for k in range(45):
    aa=random.random()*math.tau;rr=random.random()**.5*2.2;leaf((c[0]+math.cos(aa)*rr,c[1]+math.sin(aa)*rr,c[2]+random.uniform(-.5,.5)),aa,random.uniform(.5,1.2),random.uniform(.12,.26),k%3)
# Low pinnate fern modules and taller plants at the margins.
for i in range(150):
 x=random.uniform(-28,32);y=random.uniform(-25,27)
 if abs(x)<4 and abs(y)<5:continue
 for j in range(8):
  a=j*math.tau/8;length=random.uniform(.65,1.5)
  for k in range(9):
   t=k/9;c=(x+math.cos(a)*length*t,y+math.sin(a)*length*t,.07+math.sin(math.pi*t)*length*.45)
   for s in [-1,1]:leaf(c,a+s*.8,.30*(1-t)+.06,.045,j%3,.05)
for i,(v,f) in enumerate(buckets):
 ob=mesh('Layered edge foliage '+str(i),v,f,leafm[i]);bm=bmesh.new();bm.from_mesh(ob.data)
 # Open leaf surfaces should face the skylight on their upper side.
 for face in bm.faces:
  if face.normal.z<0:face.normal_flip()
 bm.to_mesh(ob.data);bm.free()
# Preserve detailed source. Only the export copy is reduced and batched.
candidate=source.with_name('tropical_rainforest_quality_candidate.blend');bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
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
