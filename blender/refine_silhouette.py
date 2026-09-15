"""Edit existing silhouette: continuous tail skin, deeper predator skulls and smaller eyes."""
import bpy,sys,shutil,math,bmesh
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'))
from bootstrap_assets import tube,parts
for species in ['velociraptor','trex','triceratops']:
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend';backup=path.with_name(path.stem+'_v4.blend')
    if not backup.exists():shutil.copy2(path,backup)
    bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];rex=species=='trex';tri=species=='triceratops'
    h=2.65 if rex else 1.85 if tri else .74;length=1.9 if rex else 2 if tri else .62;width=.8 if rex else 1.05 if tri else .23
    for ob in [o for o in bpy.context.scene.objects if o.type=='MESH']:
        names={g.index:g.name for g in ob.vertex_groups}
        tail={g.index for g in ob.vertex_groups if g.name.startswith('tail')}
        # Remove only tail-dominant vertices; torso, rig and other anatomy remain.
        bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table()
        remove=[bm.verts[v.index] for v in ob.data.vertices if sum(g.weight for g in v.groups if g.group in tail)>.52]
        bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(ob.data);bm.free()
        if not tri:
            for v in ob.data.vertices:
                headweight=sum(g.weight for g in v.groups if names.get(g.group) in ['head','jaw'])
                v.co.z+=(v.co.z-(3.1 if rex else .98))*(.38 if rex else .13)*headweight
                v.co.y+= (v.co.y+(2.4 if rex else .8))*(.15 if rex else .1)*headweight
        ob.data.update()
    skin=next(m for m in bpy.data.materials if m.name.startswith(species+'_pebbled_skin'));parts.clear()
    points=[];radii=[];steps=42;end=6.4 if rex else 4.4 if tri else 2.1;start=length*.65
    for i in range(steps):
        t=i/(steps-1);points.append((0,-start-(end-start)*t,h-.10-t*(.65 if rex or tri else .2)));radii.append(width*.69*(1-t)**1.24+.006)
    ob=tube('Continuous tail skin',points,radii,skin,None,20);ob.parent=rig
    # Smooth blend across stable tail joints, with pelvis influence at the insertion.
    groups={name:ob.vertex_groups.new(name=name) for name in ['pelvis','tail_01','tail_02','tail_03']}
    for v in ob.data.vertices:
        y=v.co.y;anchors=[start,length,length*1.75,length*2.5];idx=0
        while idx<2 and y>anchors[idx+1]:idx+=1
        t=max(0,min(1,(y-anchors[idx])/(anchors[idx+1]-anchors[idx])))
        keys=['pelvis','tail_01','tail_02','tail_03'];groups[keys[idx]].add([v.index],1-t,'REPLACE');groups[keys[idx+1]].add([v.index],t,'REPLACE')
    mod=ob.modifiers.new('Skin','ARMATURE');mod.object=rig
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    sys.argv=['export_glb.py','--','--output',str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb')];import export_glb;export_glb.main()
