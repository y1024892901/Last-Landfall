"""Matched renders of the pre-detail sources and enriched building sources."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path.cwd();OUT=ROOT/'Assets/LastLandfall/Art/Reports/BuildingDetail'
helpers={}
exec((ROOT/'Tools/Blender/render_building_icon.py').read_text(encoding='utf-8').split('arguments = argv_after_separator()')[0],helpers)
records=json.loads((OUT/'detail_manifest.json').read_text(encoding='utf-8'))
selected=[v.split('=',1)[1] for v in sys.argv if v.startswith('--asset=')]
if selected:records=[r for r in records if r['asset'] in selected]
for record in records:
    asset=record['asset'];source=ROOT/record['source'];baseline=ROOT/'work/BuildingDetail_Before/Source'/source.parent.name/source.name
    folder=OUT/'Visuals'/asset;folder.mkdir(parents=True,exist_ok=True)
    for variant,path in [('Before',baseline),('After',source)]:
        bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene;col=bpy.data.collections[asset]
        parts=[o for o in col.all_objects if o.type=='MESH' and not o.hide_render]
        for o in scene.objects:o.hide_render=o not in parts
        bpy.context.view_layer.update()
        if variant=='Before':
            lo,hi,corners=helpers['world_bounds'](parts)
        center,sx,sy,sz,tile,stage_corners=helpers['add_stage'](scene,lo,hi)
        span=max(sx,sy,sz,tile,2.4)
        helpers['add_studio_lighting'](scene,center,span)
        camera=helpers['camera_frame'](scene,stage_corners,center+Vector((0,0,sz*.04)),span)
        scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=32
        scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.film_transparent=False
        scene.view_settings.view_transform='Standard'
        for view in ['Front','Rear']:
            if view=='Rear':
                target=(lo+hi)*.5;camera.location=target+Vector((-1,1.28,.88)).normalized()*span*3.4
                helpers['aim_at'](camera,target)
            scene.render.filepath=str(folder/(variant+'_'+view+'.png'));bpy.ops.render.render(write_still=True)
    print('DETAIL_VISUAL',asset,flush=True)
if '--update-icons' in sys.argv:
    for record in records:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/record['source']))
        helpers['render_icon'](ROOT/'Assets/LastLandfall/Resources/UI/BuildIcons')
