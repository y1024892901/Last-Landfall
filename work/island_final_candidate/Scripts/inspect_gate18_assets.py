import bpy, json
from pathlib import Path
root=Path(r'D:\Last Landfall')
terrain_path=root/'work/island_final_candidate/Assets_Generated/LastLandfall_Island_GrassTexture_Preview.blend'
bpy.ops.wm.open_mainfile(filepath=str(terrain_path))
terrain=next(o for o in bpy.data.objects if o.name.startswith('IslandReference_V2'))
info={'terrain':{'bounds':[list(terrain.dimensions)],'materials':[], 'mesh_material_indices':{}, 'world_z': [min((terrain.matrix_world@v.co).z for v in terrain.data.vertices),max((terrain.matrix_world@v.co).z for v in terrain.data.vertices)]}}
for i,m in enumerate(terrain.data.materials): info['terrain']['materials'].append({'slot':i,'name':m.name,'color':list(m.diffuse_color),'polygons':sum(p.material_index==i for p in terrain.data.polygons)})
for p in terrain.data.polygons: info['terrain']['mesh_material_indices'][str(p.material_index)]=info['terrain']['mesh_material_indices'].get(str(p.material_index),0)+1
for asset in ['Grass_CoastalTuft_A','Grass_CoastalTuft_B','Pine_Windbent_Tall_A','Pine_Windbent_Short_B','Broadleaf_Coastal_A','Broadleaf_Coastal_B']:
 path=root/'work/island_final_candidate/Assets_Inspected'/f'{asset}.fbx'
 bpy.ops.object.select_all(action='DESELECT')
 before=set(bpy.data.objects)
 bpy.ops.import_scene.fbx(filepath=str(path))
 objs=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
 info[asset]=[]
 for obj in objs:
  bpy.context.view_layer.update()
  info[asset].append({'name':obj.name,'dims':list(obj.dimensions),'verts':len(obj.data.vertices),'polys':len(obj.data.polygons),'materials':[m.name if m else None for m in obj.data.materials]})
for obj in list(bpy.data.objects):
 if obj!=terrain and obj.type=='MESH': bpy.data.objects.remove(obj,do_unlink=True)
print(json.dumps(info,ensure_ascii=False,indent=2))
