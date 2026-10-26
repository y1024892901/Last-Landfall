"""Export named construction parts and schedules for Unity; no baked FBX clips required."""
from pathlib import Path
import bpy,json,sys,uuid,re
ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'Assets/LastLandfall/Art/Reports/Construction'
MODELS=ROOT/'Assets/LastLandfall/Resources/Models/Construction'
DATA=ROOT/'Assets/LastLandfall/Resources/Construction'
MODELS.mkdir(parents=True,exist_ok=True);DATA.mkdir(parents=True,exist_ok=True)

def unity_meta(path):
    meta=Path(str(path)+'.meta')
    if meta.exists():return
    guid=uuid.uuid5(uuid.NAMESPACE_URL,'LastLandfall/'+path.relative_to(ROOT).as_posix()).hex
    if path.is_dir():
        text=f'fileFormatVersion: 2\nguid: {guid}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n'
    elif path.suffix=='.fbx':
        text=(ROOT/'Assets/LastLandfall/Resources/Models/Infrastructure/RescueDock.fbx.meta').read_text(encoding='utf-8')
        text=re.sub(r'guid: [0-9a-f]+','guid: '+guid,text,count=1)
        for key,value in [('importCameras',0),('importLights',0),('preserveHierarchy',1),('importAnimation',0)]:
            text=re.sub(r'(\s'+key+r': )\d+',lambda m:m[1]+str(value),text)
    else:
        text=f'fileFormatVersion: 2\nguid: {guid}\nTextScriptImporter:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n'
    meta.write_text(text,encoding='utf-8')

for folder in (MODELS,DATA):unity_meta(folder)
records=json.loads((REPORT/'catalog.json').read_text(encoding='utf-8'))
entries=[]
for r in records:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/r['blend']))
    scene=bpy.context.scene;scene.frame_set(r['frames'])
    bpy.ops.object.select_all(action='DESELECT')
    parts=[];meshes=[]
    for phase in r['phases']:
        for p in phase['parts']:
            obj=bpy.data.objects[p['object']]
            ident=f"LLC_{len(parts):04d}"
            obj.animation_data_clear();obj.hide_render=False;obj.hide_viewport=False
            obj.name=ident;obj.select_set(True);meshes.append(obj)
            parts.append(dict(id=ident,sourceName=p['object'],start=p['start'],end=p['end'],mode=p['mode']))
    # Match the optimized static-model exporter exactly for axis and unit settings.
    target=MODELS/(r['clip']+'.fbx')
    bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'MESH'},apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False,use_triangles=True)
    unity_meta(target)
    category='Infrastructure' if r['asset'] in {'DirtRoadTiles_DeepSeek','DriftwoodCollectionBoom_DeepSeek','FishingDock_DeepSeek','RescueDock_DeepSeek','Shipyard_DeepSeek','WeatherTideBuoy_DeepSeek'} else 'Buildings'
    key=r['clip'];final='Models/'+category+'/'+key
    corners=[o.matrix_world@v for o in meshes for v in map(__import__('mathutils').Vector,o.bound_box)]
    span=max(max(v[i] for v in corners)-min(v[i] for v in corners) for i in range(3))
    schedule=dict(schemaVersion=1,key=key,fps=24,frames=r['frames'],motionDistance=max(.10,min(span*.16,.65)),parts=parts,phases=[dict(name=p['title'],start=p['start'],end=p['end']) for p in r['phases']])
    (DATA/(key+'.json')).write_text(json.dumps(schedule,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    unity_meta(DATA/(key+'.json'))
    aliases=[key]
    if key.startswith('DirtRoad'):aliases.append(key.replace('DirtRoad','Road').replace('_DeepSeek',''))
    if key=='RescueDock_DeepSeek':aliases.append('RescueDock')
    entries.append(dict(key=key,aliases=aliases,modelResource='Models/Construction/'+key,finalResource=final,scheduleResource='Construction/'+key))
    print('UNITY_CONSTRUCTION_EXPORT',key,len(parts),flush=True)
(DATA/'Catalog.json').write_text(json.dumps(dict(schemaVersion=1,entries=entries),ensure_ascii=False,indent=2),encoding='utf-8')
unity_meta(DATA/'Catalog.json')
print('UNITY_CONSTRUCTION_EXPORT_COMPLETE',len(entries),flush=True)
