"""Foot-targeted in-place locomotion on the existing v1 skeletons."""
import bpy, math, shutil
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]

def align(b,head,tail):
    rest=b.bone.tail_local-b.bone.head_local
    rotation=rest.rotation_difference(tail-head).to_matrix().to_4x4()
    b.matrix=Matrix.Translation(head) @ rotation @ b.bone.matrix_local.to_3x3().to_4x4()
    bpy.context.view_layer.update()

for species,actions in [('velociraptor',['stalk','run','flee','attack','react']),('trex',['walk','roar','attack']),('triceratops',['graze','run','defend'])]:
    path=ROOT/f'blender/dinosaurs/{species}/{species}_master.blend'
    backup=path.with_name(path.stem+'_v3.blend')
    if not backup.exists():shutil.copy2(path,backup)
    bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];r.animation_data_clear()
    for a in list(bpy.data.actions):bpy.data.actions.remove(a)
    for family in actions:
        moving=family in ['stalk','run','flee','walk'];raptor=species=='velociraptor'
        frames=(15 if family in ['run','flee'] else 30) if raptor and moving else 60 if family in ['walk','graze'] else 36 if family=='run' else 72
        speed=.8 if family=='stalk' else 1.25 if family=='walk' else 2.3 if family=='run' else 2.6
        action=bpy.data.actions.new('anim_'+('raptor' if raptor else species)+'_'+family);action.use_fake_user=True;r.animation_data_create();r.animation_data.action=action
        for frame in range(1,frames+2):
            t=(frame-1)/frames;phase=t*math.tau
            for b in r.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0)
            bpy.context.view_layer.update()
            if moving:
                for side,offset in [('L',0),('R',.5)]:
                    f=(t+offset)%1;stance=.6;stride=speed*frames/30*stance
                    ankle=r.data.bones['foot_'+side].head_local.copy();hip=r.data.bones['thigh_'+side].head_local.copy();knee=r.data.bones['shin_'+side].head_local.copy()
                    stride=min(stride,.68 if raptor else 1.6)
                    travel=stride*(.5-f/stance) if f<stance else stride*(-.5+(f-stance)/(1-stance))
                    lift=0 if f<stance else (.10 if raptor else .2)*math.sin(math.pi*(f-stance)/(1-stance))
                    ankle.y-=travel;ankle.z+=lift
                    l1=(knee-hip).length;l2=(r.data.bones['foot_'+side].head_local-knee).length
                    delta=ankle-hip;d=min(delta.length,l1+l2-.001);axis=delta.normalized();along=(l1*l1-l2*l2+d*d)/(2*d)
                    perpendicular=Vector((0,-1,0));perpendicular=(perpendicular-axis*perpendicular.dot(axis)).normalized()
                    knee=hip+axis*along+perpendicular*math.sqrt(max(0,l1*l1-along*along))
                    align(r.pose.bones['thigh_'+side],hip,knee);align(r.pose.bones['shin_'+side],knee,ankle)
                    foot=r.pose.bones['foot_'+side];foot.matrix=Matrix.Translation(ankle-foot.bone.head_local) @ foot.bone.matrix_local
                    if species=='triceratops':r.pose.bones['fore_'+side].rotation_euler.x=.16*math.sin(phase+(math.pi if side=='L' else 0))
                r.pose.bones['neck'].rotation_euler.x=.02*math.sin(phase)
            else:
                pulse=math.sin(math.pi*t)**2
                if family=='graze':r.pose.bones['neck'].rotation_euler.x=.16+.08*math.sin(phase);r.pose.bones['jaw'].rotation_euler.x=.05*(1+math.sin(phase*3))
                elif family=='roar':r.pose.bones['neck'].rotation_euler.x=-.28*pulse;r.pose.bones['jaw'].rotation_euler.x=.72*pulse
                elif family=='attack':r.pose.bones['neck'].rotation_euler.x=.38*pulse;r.pose.bones['jaw'].rotation_euler.x=.48*math.sin(math.pi*t*2)**2
                elif family=='react':r.pose.bones['neck'].rotation_euler.x=-.19*pulse;r.pose.bones['head'].rotation_euler.z=.25*math.sin(phase)*pulse
                elif family=='defend':r.pose.bones['neck'].rotation_euler.x=.25*pulse;r.pose.bones['head'].rotation_euler.z=.21*math.sin(phase)*pulse
            for j in range(1,4):r.pose.bones[f'tail_{j:02}'].rotation_euler.z=.024*math.sin(phase-j*.4)
            for b in r.pose.bones:b.keyframe_insert('rotation_euler',frame=frame);b.keyframe_insert('location',frame=frame)
    r.animation_data.action=None
    for b in r.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
    bpy.context.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(path))
    bpy.ops.export_scene.gltf(filepath=str(ROOT/f'web/public/assets/dinosaurs/{species}_master.glb'),export_format='GLB',export_animation_mode='ACTIONS',export_force_sampling=True,export_skins=True)
