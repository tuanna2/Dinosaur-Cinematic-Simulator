"""Re-transfer remeshed skin weights from the authoritative original surface.
Clear every pre-existing weight first; keep at most four normalized influences.
"""
import bpy,sys,shutil
from pathlib import Path
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'));import export_glb
for species in ['velociraptor','trex','triceratops']:
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend';backup=path.with_name(path.stem+'_pre_weight_repair.blend')
    if not backup.exists():shutil.copy2(path,backup)
    bpy.ops.wm.open_mainfile(filepath=str(path));targets=[]
    for ob in bpy.context.scene.objects:
        if ob.type=='MESH' and not ob.name.startswith(('Joint bridge','Continuous tail','Scalloped')) and ob.data.polygons and all('pebbled_skin' in ob.data.materials[i].name for i in {p.material_index for p in ob.data.polygons}):targets.append(ob)
    with bpy.data.libraries.load(str(path.with_name(path.stem+'_v1.blend')),link=False) as (a,b):b.objects=['Skinned_Anatomy']
    ref=b.objects[0];kd=KDTree(len(ref.data.vertices));weights=[];names={g.index:g.name for g in ref.vertex_groups}
    for v in ref.data.vertices:kd.insert(v.co,v.index);weights.append([(names[g.group],g.weight) for g in v.groups])
    kd.balance()
    for ob in targets:
        print('TRANSFER',species,ob.name,len(ob.data.vertices));indices=list(range(len(ob.data.vertices)))
        for g in ob.vertex_groups:g.remove(indices)
        for v in ob.data.vertices:
            values={}
            for co,i,d in kd.find_n(v.co,4):
                for name,w in weights[i]:values[name]=values.get(name,0)+w/(d+.006)**2
            values=dict(sorted(values.items(),key=lambda x:x[1],reverse=True)[:4]);total=sum(values.values())
            for name,w in values.items():
                g=ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name);g.add([v.index],w/total,'REPLACE')
        assert all(abs(sum(g.weight for g in v.groups)-1)<.0001 for v in ob.data.vertices)
    bpy.data.objects.remove(ref,do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.argv=['export_glb.py','--','--output',str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb')];export_glb.main()
