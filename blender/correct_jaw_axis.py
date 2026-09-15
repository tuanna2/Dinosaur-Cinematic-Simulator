"""Correct authored jaw/neck pitch for stable bones whose local X points world -X."""
import bpy,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'));import export_glb
for species in ['velociraptor','trex','triceratops']:
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend';backup=path.with_name(path.stem+'_pre_axis_repair.blend')
    if not backup.exists():shutil.copy2(path,backup)
    bpy.ops.wm.open_mainfile(filepath=str(path))
    for a in bpy.data.actions:
        for layer in a.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        if curve.array_index==0 and curve.data_path in ['pose.bones["jaw"].rotation_euler','pose.bones["neck"].rotation_euler']:
                            factor=-.3 if species=='velociraptor' and 'jaw' in curve.data_path else -1
                            for k in curve.keyframe_points:
                                k.co.y*=factor;k.handle_left.y*=factor;k.handle_right.y*=factor
    bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.argv=['export_glb.py','--','--output',str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb')];export_glb.main()
