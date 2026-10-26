"""Render matched source/FBX front and rear views for all 25 building assets."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path.cwd();OUT=ROOT/'Assets/LastLandfall/Art/Reports/BuildingAudit'
helpers={}
exec((ROOT/'Tools/Blender/render_building_icon.py').read_text(encoding='utf-8').split('arguments = argv_after_separator()')[0],helpers)
report=json.loads((OUT/'optimization_report.json').read_text(encoding='utf-8'))
assets={}
for row in report['exports']:assets.setdefault(row['asset'],[]).append(row)
for asset,exports in assets.items():
    category=Path(exports[0]['file']).parent.name
    source=ROOT/'Assets/LastLandfall/Art/Source'/category/(asset+'.blend')
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene;col=bpy.data.collections[asset]
    parts=[o for o in col.all_objects if o.type=='MESH']
    source_mats={s.material.name:s.material for o in parts for s in o.material_slots if s.material}
    for o in scene.objects:o.hide_render=o not in parts
    bpy.context.view_layer.update()
    lo,hi,_=helpers['world_bounds'](parts)
    center,sx,sy,sz,tile,corners=helpers['add_stage'](scene,lo,hi)
    span=max(sx,sy,sz,tile,2.4)
    helpers['add_studio_lighting'](scene,center,span)
    camera=helpers['camera_frame'](scene,corners,center+Vector((0,0,sz*.04)),span)
    scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=24
    scene.render.resolution_x=384;scene.render.resolution_y=384;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.view_settings.view_transform='Standard'
    folder=OUT/'Visuals'/asset;folder.mkdir(parents=True,exist_ok=True)
    front_location=camera.location.copy();front_rotation=camera.rotation_euler.copy()
    for variant in ['Source','Optimized']:
        if variant=='Optimized':
            for o in parts:o.hide_render=True
            for entry in exports:
                prior=set(scene.objects)
                bpy.ops.import_scene.fbx(filepath=str(ROOT/entry['file']),use_anim=False)
                imported=[o for o in scene.objects if o not in prior and o.type=='MESH']
                if asset=='DirtRoadTiles_DeepSeek':
                    rootname=Path(entry['file']).stem.replace('_DeepSeek','')
                    offset=bpy.data.objects[rootname].matrix_world.translation.copy()
                    for o in imported:o.location+=offset
                for o in imported:
                    o.hide_render=False
                    for slot in o.material_slots:
                        name=slot.material.name
                        while name not in source_mats and name[-4:-3]=='.' and name[-3:].isdigit():name=name[:-4]
                        assert name in source_mats,(asset,name)
                        slot.material=source_mats[name]
        camera.location=front_location;camera.rotation_euler=front_rotation
        for view in ['Front','Rear']:
            if view=='Rear':
                target=(lo+hi)*.5
                camera.location=target+Vector((-1,1.28,.88)).normalized()*span*3.4
                helpers['aim_at'](camera,target)
            scene.render.filepath=str(folder/(variant+'_'+view+'.png'))
            bpy.ops.render.render(write_still=True)
    print('VISUAL_REVIEW',asset,flush=True)

if '--update-icons' in sys.argv:
    changed=set(json.loads((OUT/'structural_repairs.json').read_text(encoding='utf-8')))
    changed.add('Archive_DeepSeek')
    for asset in sorted(changed):
        source=next((ROOT/'Assets/LastLandfall/Art/Source').glob('*/'+asset+'.blend'))
        bpy.ops.wm.open_mainfile(filepath=str(source))
        helpers['render_icon'](ROOT/'Assets/LastLandfall/Resources/UI/BuildIcons')
