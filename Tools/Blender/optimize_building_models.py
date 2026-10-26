"""Optimize the 25 approved building assets without flattening editable sources.
Run after generating models: blender --background --python Tools/Blender/optimize_building_models.py
"""
import bpy, bmesh, json, hashlib, sys
from pathlib import Path
from collections import defaultdict, Counter
from itertools import permutations
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

ROOT=Path.cwd()
OUT=ROOT/'Assets/LastLandfall/Art/Reports/BuildingAudit'
if '--report-dir' in sys.argv:
    OUT=ROOT/sys.argv[sys.argv.index('--report-dir')+1]
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'Assets/LastLandfall/Art/Source'
MODELS=ROOT/'Assets/LastLandfall/Resources/Models'
paths=sorted(SOURCE.glob('*/*_DeepSeek.blend'))+[SOURCE/'Buildings/WaterStorageTank.blend']
assert len(paths)==25
SURFACES={}

def snapshot(objects):
    triangles=[]; points=[]; counts=Counter()
    for o in objects:
        m=o.data; m.calc_loop_triangles()
        for t in m.loop_triangles:
            coords=tuple(sorted(tuple(round(c*10000) for c in (o.matrix_world@m.vertices[i].co)) for i in t.vertices))
            triangles.append(coords)
            points.extend(coords)
            slot=o.material_slots[t.material_index]
            counts[slot.material.name if slot.material else '__none__']+=1
    low=[min(v[i] for v in points)/10000 for i in range(3)]
    high=[max(v[i] for v in points)/10000 for i in range(3)]
    digest=hashlib.sha256(repr(sorted(triangles)).encode()).hexdigest()
    SURFACES[digest]=triangles
    return {'meshes':len(objects),'triangles':len(triangles),'surface_hash':digest,'min':low,'max':high,'material_triangles':dict(sorted(counts.items()))}

def same_surface(expected, actual):
    if expected['surface_hash']==actual['surface_hash']:return True
    left=Counter(SURFACES[expected['surface_hash']]);right=Counter(SURFACES[actual['surface_hash']])
    missing=list((left-right).elements());extra=list((right-left).elements())
    if len(missing)!=len(extra):return False
    tree=KDTree(len(extra))
    for index,tri in enumerate(extra):tree.insert(sum((Vector(v) for v in tri),Vector())/3,index)
    tree.balance();used=set()
    for tri in missing:
        center=sum((Vector(v) for v in tri),Vector())/3
        for _,index,_ in tree.find_range(center,4):
            if index in used:continue
            if any(all((Vector(a)-Vector(b)).length<=2 for a,b in zip(tri,order)) for order in permutations(extra[index])):
                used.add(index);break
        else:return False
    return True

previous=OUT/'optimization_report.json'
exports=[];fixes=json.loads(previous.read_text(encoding='utf-8')).get('source_fixes',[]) if previous.exists() else []
material_settings={}

def material_properties(mat):
    shader=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if mat.use_nodes else None
    color=list(shader.inputs['Base Color'].default_value) if shader else list(mat.diffuse_color)
    if shader:color[3]=shader.inputs['Alpha'].default_value
    emission=shader.inputs.get('Emission Color') if shader else None
    strength=shader.inputs.get('Emission Strength') if shader else None
    return {'name':mat.name,'color':color,'metallic':shader.inputs['Metallic'].default_value if shader else mat.metallic,'smoothness':1-(shader.inputs['Roughness'].default_value if shader else mat.roughness),'emission':[v*(strength.default_value if strength else 1) for v in emission.default_value[:3]] if emission else [0,0,0]}
for path in paths:
    bpy.ops.wm.open_mainfile(filepath=str(path))
    bpy.context.preferences.filepaths.save_version=0
    key=path.stem; col=bpy.data.collections[key]
    objects=[o for o in col.all_objects if o.type=='MESH']
    if key=='Archive_DeepSeek':
        source_changed=False
        for obj in objects:
            if not obj.name.startswith('Back_Vent_Slat'):continue
            bm=bmesh.new();bm.from_mesh(obj.data)
            old=sum(f.calc_area()<1e-12 for f in bm.faces)
            if old:
                bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
                assert not any(not e.is_manifold for e in bm.edges)
                assert not any(f.calc_area()<1e-12 for f in bm.faces)
                bm.to_mesh(obj.data);obj.data.update()
                fixes.append({'asset':key,'object':obj.name,'removed_degenerate_faces':old})
                source_changed=True
            bm.free()
        if source_changed:bpy.ops.wm.save_as_mainfile(filepath=str(path))
    if key=='DirtRoadTiles_DeepSeek':
        roots=[o for o in col.all_objects if o.type=='EMPTY' and o.name.startswith('DirtRoad')]
        jobs=[(o.name,[c for c in o.children_recursive if c.type=='MESH'],-o.matrix_world.translation) for o in roots]
        assert len(jobs)==5
    else:jobs=[(key,objects,Vector((0,0,0)))]
    for name,parts,offset in jobs:
        stage=bpy.data.collections.new('OptimizationExport');bpy.context.scene.collection.children.link(stage)
        copies=[];deps=bpy.context.evaluated_depsgraph_get()
        for obj in parts:
            mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
            mesh.transform(Matrix.Translation(offset)@obj.matrix_world)
            bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
            copy=bpy.data.objects.new(obj.name+'_Export',mesh);stage.objects.link(copy);copies.append(copy)
        before=snapshot(copies)
        groups=defaultdict(list)
        for o in copies:
            used={p.material_index for p in o.data.polygons}
            assert len(used)==1, 'Unexpected multimaterial source '+o.name
            mat=o.material_slots[next(iter(used))].material
            properties=material_properties(mat)
            material_settings[mat.name]=properties
            # Glass panes keep separate renderers for transparent depth sorting.
            groups[(mat,o.name if properties['color'][3]<0.999 else '')].append(o)
        optimized=[]
        for (mat,_),group in groups.items():
            bpy.ops.object.select_all(action='DESELECT')
            for o in group:o.select_set(True)
            bpy.context.view_layer.objects.active=group[0]
            if len(group)>1:bpy.ops.object.join()
            o=bpy.context.object;o.name=name+'__'+(mat.name if mat else 'Unassigned')
            optimized.append(o)
        after=snapshot(optimized)
        assert before['surface_hash']==after['surface_hash'],name+' changed surfaces'
        assert before['material_triangles']==after['material_triangles'],name+' changed materials'
        bpy.ops.object.select_all(action='DESELECT')
        for o in optimized:o.select_set(True)
        target=MODELS/path.parent.name/(name+'_DeepSeek.fbx' if key=='DirtRoadTiles_DeepSeek' and not name.endswith('_DeepSeek') else name+'.fbx')
        bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'MESH'},apply_scale_options='FBX_SCALE_ALL',bake_space_transform=True,axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False,use_triangles=True)
        exports.append({'asset':key,'file':str(target.relative_to(ROOT)).replace('\\','/'),'before':before,'after':after})
        for o in list(stage.objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(stage)
        print('OPTIMIZED',name,before['meshes'],'->',after['meshes'],flush=True)

for row in exports:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(ROOT/row['file']),use_anim=False)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    actual=snapshot(meshes);expected=row['after']
    checks={'mesh_count':actual['meshes']==expected['meshes'],'triangle_count':actual['triangles']==expected['triangles'],'surface_geometry':same_surface(expected,actual),'materials':actual['material_triangles']==expected['material_triangles'],'no_camera_light':not any(o.type in {'CAMERA','LIGHT'} for o in bpy.context.scene.objects)}
    row['roundtrip_checks']=checks
    row['passed']=all(checks.values())
    print('ROUNDTRIP',row['file'],checks,flush=True)
report={'asset_count':25,'export_count':len(exports),'geometry_tolerance_m':0.0002,'source_fixes':fixes,'exports':exports,'all_passed':all(r['passed'] for r in exports)}
(OUT/'optimization_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'material_manifest.json').write_text(json.dumps({'materials':list(material_settings.values())},ensure_ascii=False,indent=2),encoding='utf-8')
central_manifest=ROOT/'Assets/LastLandfall/Art/Reports/BuildingAudit/material_manifest.json'
if central_manifest!=OUT/'material_manifest.json':
    central_manifest.write_text(json.dumps({'materials':list(material_settings.values())},ensure_ascii=False,indent=2),encoding='utf-8')
assert report['all_passed'],'FBX verification failed; inspect optimization_report.json'
print('OPTIMIZATION_COMPLETE',len(exports),flush=True)
