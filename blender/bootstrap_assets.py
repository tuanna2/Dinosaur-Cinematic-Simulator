"""Original procedural master workshop. Run once; subsequent revisions edit saved blends.
Blender coordinates: X right, -Y forward, Z up. All dimensions in metres.
"""
import bpy, math, random, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
random.seed(1947)

def pt(p): return Vector((p[0],-p[1],p[2]))
def clean():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)
def material(name,color,rough=.7):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    s=m.node_tree.nodes.get('Principled BSDF'); s.inputs['Base Color'].default_value=(*color,1); s.inputs['Roughness'].default_value=rough
    return m

def skin_material(name,base):
    import numpy as np
    n=1024; yy,xx=np.mgrid[0:n,0:n]; rng=np.random.default_rng(471)
    # Packed original scale albedo: irregular staggered cells, mottling and dorsal stripes.
    row=yy//13; dx=((xx+(row%2)*7)%15-7)/7; dy=(yy%13-6)/6
    edge=np.clip((dx*dx+dy*dy-.55)*2,0,1)
    noise=rng.random((n,n)); bands=(np.sin(xx/n*math.pi*18+np.sin(yy/n*18)*1.3)>.3)
    shade=.8+.15*np.sin(xx*.021)*np.sin(yy*.032)-.2*edge-.17*bands+.07*noise
    arr=np.ones((n,n,4),dtype=np.float32)
    for c,b in enumerate(base): arr[:,:,c]=np.clip(b*shade,0,1)
    img=bpy.data.images.new(name+'_scales',width=n,height=n); img.pixels.foreach_set(arr.ravel()); img.pack()
    m=material(name,base,.57); ns=m.node_tree.nodes; tex=ns.new('ShaderNodeTexImage'); tex.image=img
    m.node_tree.links.new(tex.outputs['Color'],ns.get('Principled BSDF').inputs['Base Color'])
    return m

parts=[]
def mesh(name,verts,faces,mat,bone=None):
    me=bpy.data.meshes.new(name); me.from_pydata([pt(v) for v in verts],[],faces); me.update()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat)
    for f in me.polygons: f.use_smooth=True
    if bone: ob.vertex_groups.new(name=bone).add(list(range(len(verts))),1,'REPLACE'); parts.append(ob)
    uv=me.uv_layers.new(name='SkinUV')
    for poly in me.polygons:
        for li in poly.loop_indices:
            v=verts[me.loops[li].vertex_index]; uv.data[li].uv=(v[1]*.15+v[0]*.1,v[2]*.25)
    return ob

def ell(name,c,s,mat,bone=None):
    verts=[]; faces=[]; nr=16; ns=24
    for i in range(nr+1):
        a=math.pi*i/nr
        for j in range(ns):
            b=math.tau*j/ns; verts.append((c[0]+s[0]*math.sin(a)*math.cos(b),c[1]+s[1]*math.sin(a)*math.sin(b),c[2]+s[2]*math.cos(a)))
    for i in range(nr):
        for j in range(ns):
            k=i*ns+j; l=i*ns+(j+1)%ns; faces.append((k,l,l+ns,k+ns))
    return mesh(name,verts,faces,mat,bone)

def tube(name,points,radii,mat,bone=None,sides=12):
    verts=[]; faces=[]
    for i,p in enumerate(points):
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        tangent.normalize(); a=tangent.cross(Vector((1,0,0)))
        if a.length<.01: a=tangent.cross(Vector((0,1,0)))
        a.normalize(); b=tangent.cross(a).normalized()
        r=radii[i]; r=(r,r) if isinstance(r,(float,int)) else r
        for j in range(sides):
            q=Vector(p)+a*math.cos(j*math.tau/sides)*r[0]+b*math.sin(j*math.tau/sides)*r[1]; verts.append(q)
    for i in range(len(points)-1):
        for j in range(sides):
            k=i*sides+j; l=i*sides+(j+1)%sides; faces.append((k,l,l+sides,k+sides))
    faces.extend([tuple(range(sides-1,-1,-1)),tuple((len(points)-1)*sides+j for j in range(sides))])
    return mesh(name,verts,faces,mat,bone)

def rig(bones):
    ar=bpy.data.armatures.new('DinosaurSkeleton_v1'); ob=bpy.data.objects.new('Rig',ar); bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active=ob; ob.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    for name,a,b,parent in bones:
        eb=ar.edit_bones.new(name); eb.head=pt(a); eb.tail=pt(b)
        if parent: eb.parent=ar.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT'); ob.select_set(False)
    return ob

def finish_mesh(r):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in parts: ob.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join(); body=bpy.context.object; body.name='Skinned_Anatomy'
    mod=body.modifiers.new('Skin','ARMATURE'); mod.object=r; body.parent=r
    return body

def animate(r,species,families):
    scene=bpy.context.scene; scene.render.fps=30
    for family in families:
        length=60 if family in ('graze','stalk','walk') else 30 if family in ('run','flee') else 72
        action=bpy.data.actions.new('anim_'+species+'_'+family); action.use_fake_user=True
        r.animation_data_create(); r.animation_data.action=action
        for frame in range(1,length+2,3):
            t=(frame-1)/length; phase=math.tau*t
            for b in r.pose.bones: b.rotation_mode='XYZ'; b.rotation_euler=(0,0,0); b.location=(0,0,0)
            locomotion=family in ('stalk','walk','run','flee')
            if locomotion:
                amp=.23 if family=='stalk' else .36 if family=='walk' else .55
                for side,off in [('L',0),('R',math.pi)]:
                    q=math.sin(phase+off)
                    r.pose.bones['thigh_'+side].rotation_euler.x=amp*q
                    r.pose.bones['shin_'+side].rotation_euler.x=-amp*.8*max(0,-q)
                    r.pose.bones['foot_'+side].rotation_euler.x=-amp*.5*q
                    if 'fore_'+side in r.pose.bones: r.pose.bones['fore_'+side].rotation_euler.x=-amp*.65*q
                r.pose.bones['pelvis'].location.y=.025*(1-math.cos(2*phase))
                r.pose.bones['neck'].rotation_euler.x=.025*math.sin(phase)
            else:
                pulse=math.sin(math.pi*t)**2
                if family=='graze': r.pose.bones['neck'].rotation_euler.x=.16+.09*math.sin(phase); r.pose.bones['jaw'].rotation_euler.x=.06*(1+math.sin(phase*3))
                if family in ('roar','attack','react','defend'):
                    r.pose.bones['neck'].rotation_euler.x=(-.3 if family=='roar' else .25)*pulse
                    r.pose.bones['head'].rotation_euler.z=.12*math.sin(phase)*pulse
                    r.pose.bones['jaw'].rotation_euler.x=(.6 if family=='roar' else .35)*pulse
            for name in ('tail_01','tail_02','tail_03'): r.pose.bones[name].rotation_euler.z=.035*math.sin(phase-int(name[-2:])*.5)
            for b in r.pose.bones:
                b.keyframe_insert('rotation_euler',frame=frame); b.keyframe_insert('location',frame=frame)
        # exact seam/end, including lengths not divisible by sampling interval
        for b in r.pose.bones:
            if family!='graze': b.rotation_euler=(0,0,0); b.location=(0,0,0)
            b.keyframe_insert('rotation_euler',frame=length+1); b.keyframe_insert('location',frame=length+1)
    r.animation_data.action=None
    for b in r.pose.bones: b.rotation_euler=(0,0,0); b.location=(0,0,0)
    scene.frame_set(1)

def save_export(source,out):
    source=ROOT/source; out=ROOT/out; source.parent.mkdir(parents=True,exist_ok=True); out.parent.mkdir(parents=True,exist_ok=True)
    if source.exists(): raise RuntimeError('Refusing to regenerate existing master '+str(source))
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_skins=True,export_lights=False,export_cameras=False)

def dinosaur(species):
    clean(); parts.clear(); tri=species=='triceratops'; rex=species=='trex'
    # Human-readable anatomical landmark table; no shot-specific root transforms.
    h=2.65 if rex else 1.85 if tri else .74
    bodylen=1.9 if rex else 2 if tri else .62
    width=.8 if rex else 1.05 if tri else .23
    skin=skin_material(species+'_pebbled_skin',(.31,.29,.20) if rex else (.32,.24,.16) if tri else (.28,.34,.23))
    pale=material('Horn and claw keratin',(.36,.31,.20),.48); tooth=material('Ivory',(.73,.68,.49),.4)
    dark=material('Mouth and nostril',(.045,.024,.021),.7); eye=material('Amber iris',(.55,.28,.025),.24); pupil=material('Obsidian pupil',(.008,.009,.006),.13)
    heady=2.75 if rex else 2.45 if tri else .98; headz=3.1 if rex else 1.45 if tri else .98
    necky=1.25 if rex else 1.4 if tri else .65
    bones=[('root',(0,0,0),(0,0,.3),None),('pelvis',(0,0,h),(0,.5,h),'root'),('neck',(0,necky,h),(0,heady-.3,headz),'pelvis'),('head',(0,heady-.35,headz),(0,heady+.4,headz),'neck'),('jaw',(0,heady-.3,headz-.22),(0,heady+.4,headz-.22),'head')]
    for i in range(3): bones.append((f'tail_{i+1:02}',(0,-bodylen-i*bodylen*.75,h-.1-i*.12),(0,-bodylen-(i+1)*bodylen*.75,h-.22-i*.12),'pelvis' if i==0 else f'tail_{i:02}'))
    for side,sign in [('L',-1),('R',1)]:
        x=sign*width*.82; knee=(x,.45,h*.48); ankle=(x,-.1,h*.14)
        bones += [('thigh_'+side,(x,0,h),knee,'pelvis'),('shin_'+side,knee,ankle,'thigh_'+side),('foot_'+side,ankle,(x,.55,.08),'shin_'+side),('fore_'+side,(sign*width*.8,1.15,h*.85),(sign*width,1.5,.15 if tri else h*.55),'neck')]
    r=rig(bones)
    ell('Ribcage',(0,0,h),(width,bodylen,h*.4),skin,'pelvis')
    tube('Neck',[(0,.55,h),(0,necky,h+.08),(0,heady-.3,headz)],[width*.72,width*.55,width*.47],skin,'neck',24)
    # Tapered, segmented muscular tail.
    for i in range(3):
        start=-bodylen-i*bodylen*.75; rad=width*.68*(1-i*.31)
        tube('Tail',[(0,start+.25,h-.1-i*.12),(0,start-bodylen*.38,h-.16-i*.12),(0,start-bodylen*.8,h-.22-i*.12)],[rad,rad*.66,max(.013,rad*.36 if i<2 else .014)],skin,f'tail_{i+1:02}',20)
    if tri:
        ell('Skull',(0,heady,headz),(.67,.95,.53),skin,'head')
        ell('Beak',(0,heady+.75,headz-.18),(.33,.36,.3),pale,'jaw')
        # Broad scalloped bony frill, tilted back from the skull.
        verts=[(0,heady-.6,headz+.35)]; N=64
        for i in range(N):
            a=i*math.tau/N; scallop=1+.035*math.cos(a*16)
            verts.append((1.13*math.cos(a)*scallop,heady-.62-.32*math.sin(a),headz+.48+.97*math.sin(a)*scallop))
        frill=mesh('Scalloped parietal frill',verts,[(0,i+1,(i+1)%N+1) for i in range(N)],skin,'head')
        sol=frill.modifiers.new('Frill thickness','SOLIDIFY'); sol.thickness=.1
        for sign in [-1,1]:
            tube('Brow horn',[(sign*.42,heady+.1,headz+.36),(sign*.44,heady+.65,headz+1.1),(sign*.38,heady+1.15,headz+1.28)],[.17,.095,.008],tooth,'head')
        tube('Nasal horn',[(0,heady+.67,headz+.2),(0,heady+.98,headz+.65)],[.16,.008],pale,'head')
    else:
        size=(.61,.87,.43) if rex else (.18,.36,.14)
        ell('Cranium',(0,heady-.2,headz),size,skin,'head')
        ell('Upper muzzle',(0,heady+size[1]*.46,headz-.05),(size[0]*.8,size[1]*.65,size[2]*.65),skin,'head')
        ell('Mouth opening',(0,heady+.13,headz-size[2]*.46),(size[0]*.75,size[1]*.85,.065 if rex else .021),dark,'head')
        ell('Lower jaw',(0,heady+.12,headz-size[2]*.65),(size[0]*.74,size[1]*.8,size[2]*.28),skin,'jaw')
        for sign in [-1,1]:
            for j in range(11 if rex else 7):
                y=heady-size[1]*.4+j*size[1]*1.15/(10 if rex else 6)
                z=headz-size[2]*.34
                tube('Tooth',[(sign*size[0]*.64,y,z),(sign*size[0]*.62,y,z-(.13 if rex else .026))],[.042 if rex else .011,.001],tooth,'head',8)
    for sign in [-1,1]:
        ex=.58 if rex else .56 if tri else .168; ey=heady-.32; ez=headz+.15 if rex else headz+.2 if tri else headz+.055; er=.09 if rex else .08 if tri else .032
        ell('Eye socket',(sign*ex,ey,ez),(er*.8,er*1.7,er*1.35),dark,'head')
        ell('Eye',(sign*(ex+er*.38),ey+.014,ez),(er*.7,er,er),eye,'head')
        ell('Pupil',(sign*(ex+er*.86),ey+.025,ez),(er*.12,er*.48,er*.72),pupil,'head')
        ell('Brow',(sign*ex,ey-.025,ez+er),(er,er*1.9,er*.65),skin,'head')
        side='L' if sign<0 else 'R'; x=sign*width*.82
        ell('Haunch',(x,-.1,h*.8),(width*.47,bodylen*.43,h*.47),skin,'thigh_'+side)
        tube('Calf',[(x,.45,h*.48),(x,.22,h*.3),(x,-.1,h*.14)],[width*.27,width*.2,width*.12],skin,'shin_'+side)
        ell('Heel',(x,0,.14 if rex or tri else .05),(width*.18,.24 if rex or tri else .1,.14 if rex or tri else .05),skin,'foot_'+side)
        for j in [-1,0,1]:
            tx=x+j*width*.18; end=.68 if rex or tri else .27
            tube('Toe',[(x,0,.11 if rex or tri else .055),(tx,end*.6,.075),(tx,end,.06)],[width*.12,width*.075,.018],skin,'foot_'+side)
            tube('Toe claw',[(tx,end-.02,.075),(tx,end+.14 if rex or tri else end+.06,.025)],[width*.07,.001],pale,'foot_'+side)
        if tri:
            tube('Front limb',[(sign*.85,1.12,h*.86),(sign*.88,1.3,.65),(sign*.85,1.55,.12)],[.35,.24,.21],skin,'fore_'+side)
            ell('Front foot',(sign*.85,1.64,.17),(.3,.37,.18),skin,'fore_'+side)
        else:
            armend=(sign*(width+.15),necky+.5,h*.62)
            tube('Arm',[(sign*width*.7,necky,h*.92),(sign*(width+.12),necky+.15,h*.68),armend],[width*.16,width*.1,width*.07],skin,'fore_'+side)
            for j in range(2 if rex else 3):
                tube('Finger',[armend,(armend[0]+j*.035,armend[1]+.2,armend[2]-.06)],[width*.04,.006],pale,'fore_'+side,8)
        if not rex and not tri:
            # Pennaceous forearm and tail feathers distinguish the small dromaeosaur.
            for j in range(9):
                a=(sign*.31,.6-j*.025,.63); b=(sign*(.52+j*.018),.32-j*.035,.54)
                tube('Forearm feather',[a,b],[.027,.002],skin,'fore_'+side,6)
    finish_mesh(r)
    families=['walk','roar','attack'] if rex else ['graze','run','defend'] if tri else ['stalk','run','attack','react','flee']
    animate(r,'raptor' if species=='velociraptor' else species,families)
    save_export(f'blender/dinosaurs/{species}/{species}_master.blend',f'web/public/assets/dinosaurs/{species}_master.glb')

def environment():
    clean(); parts.clear()
    soil=material('Rain-dark loam',(.065,.08,.045),.42); bark=material('Wet buttress bark',(.10,.075,.044),.86)
    leaf=[material('Canopy '+str(i),c,.64) for i,c in enumerate([(.045,.115,.027),(.09,.18,.042),(.14,.23,.065)])]
    grass=material('Grassland blades',(.20,.25,.08),.8); rock=material('Mossy basalt',(.15,.17,.12),.81)
    water=material('Shallow puddles',(.12,.17,.15),.13)
    mesh('Continuous wet terrain',[(-420,-220,-.04),(160,-220,-.04),(160,220,-.04),(-420,220,-.04)],[(0,1,2,3)],soil)
    # Leaf geometry: tapered, folded broad leaves, batched by material for browser draw calls.
    buckets=[([],[]) for _ in range(4)]
    def blade(c,angle,length,width,slot,tilt=.4):
        vs,fs=buckets[slot]; start=len(vs); x,y,z=c; dx=math.cos(angle); dy=math.sin(angle)
        vs.extend([(x,y,z),(x+dx*length*.45-dy*width,y+dy*length*.45+dx*width,z+length*tilt*.65),(x+dx*length*.55,y+dy*length*.55,z+length*tilt),(x+dx*length*.45+dy*width,y+dy*length*.45-dx*width,z+length*tilt*.65),(x+dx*length,y+dy*length,z+length*tilt*.7)])
        fs.extend([tuple(start+i for i in f) for f in [(0,1,2),(0,2,3),(1,4,2),(2,4,3)]])
    for i in range(200):
        x=random.uniform(-260,95); y=random.uniform(-90,100)
        # Open central migration corridor, dense layered jungle edges.
        if -20<y<22: continue
        height=random.uniform(10,21); rad=random.uniform(.22,.65)
        tube('Rainforest trunk',[(x,y,0),(x+.2,y,height*.5),(x-.4,y,height)],[rad*1.7,rad,rad*.35],bark,None,9)
        for j in range(4):
            a=j*math.tau/4; tube('Buttress root',[(x+math.cos(a)*rad*4,y+math.sin(a)*rad*4,0),(x,y,2)],[rad*.4,rad*.5],bark,None,6)
        for j in range(6):
            a=random.random()*math.tau; c=(x+math.cos(a)*2,y+math.sin(a)*2,height-random.random()*3)
            tube('Crown branch',[(x,y,height*.7),c],[rad*.4,.055],bark,None,6)
            for k in range(16): blade((c[0]+random.uniform(-2,2),c[1]+random.uniform(-2,2),c[2]+random.uniform(-.6,.6)),random.random()*math.tau,random.uniform(1.2,2.7),.35,k%3,.05)
    for i in range(1600):
        x=random.uniform(-270,90); y=random.uniform(-65,85)
        if -10<y<15 and random.random()<.75: continue
        for j in range(7): blade((x,y,.015),j*math.tau/7,random.uniform(.3,1.3),.10,j%3,.65)
    for i in range(12000):
        x=random.uniform(-340,95); y=random.uniform(-65,85)
        blade((x,y,.005),random.random()*math.tau,random.uniform(.15,.5),.025,3,1.4)
    for i in range(110):
        x=random.uniform(-280,85); y=random.choice([-1,1])*random.uniform(16,65)
        ell('River stone',(x,y,.15),(random.uniform(.3,1.1),random.uniform(.3,.9),random.uniform(.2,.5)),rock)
    for i in range(40):
        x=random.uniform(-280,80); y=random.uniform(-55,60)
        ell('Rain pool',(x,y,-.026),(random.uniform(.4,2),random.uniform(.5,2.5),.016),water)
    for i in range(12):
        x=random.uniform(-240,65); y=random.choice([-1,1])*random.uniform(17,38)
        tube('Fallen log',[(x,y,.35),(x+4,y+1,.4)],[.4,.29],bark,None,12)
    for i,(vs,fs) in enumerate(buckets):
        ob=mesh('Broadleaf clusters' if i<3 else 'Meadow grass',vs,fs,leaf[i] if i<3 else grass)
        ob.data.materials[0].use_backface_culling=False
    # Merge static geometry by material, preserving editable object modules in source via collection copy.
    save_export('blender/environments/tropical_rainforest.blend','web/public/assets/environments/tropical_rainforest.glb')

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    for s in args or ['velociraptor','trex','triceratops','environment']:
        environment() if s=='environment' else dinosaur(s)
