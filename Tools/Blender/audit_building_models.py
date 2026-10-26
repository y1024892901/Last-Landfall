import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path.cwd()
OUT=ROOT/'Assets/LastLandfall/Art/Reports/BuildingAudit'
OUT.mkdir(parents=True,exist_ok=True)
paths=sorted((ROOT/'Assets/LastLandfall/Art/Source').glob('*/*_DeepSeek.blend'))
paths.append(ROOT/'Assets/LastLandfall/Art/Source/Buildings/WaterStorageTank.blend')
reports=[]
for path in paths:
    bpy.ops.wm.open_mainfile(filepath=str(path))
    key=path.stem
    col=bpy.data.collections.get(key)
    if col is None:
        raise RuntimeError('Missing model collection '+key)
    objs=[o for o in col.all_objects if o.type=='MESH']
    deps=bpy.context.evaluated_depsgraph_get()
    corners=[]; tri=0; draws=0; bad=[]; signatures={}; duplicates=[]; materials=set(); base_tri=0
    for obj in objs:
        corners.extend(obj.matrix_world@Vector(p) for p in obj.bound_box)
        bm=bmesh.new();bm.from_mesh(obj.data)
        issues={'nonmanifold':sum(not e.is_manifold for e in bm.edges),'loose_vertices':sum(not v.link_edges for v in bm.verts),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
        bm.free()
        if any(issues.values()): bad.append({'object':obj.name,**issues})
        obj.data.calc_loop_triangles();base_tri+=len(obj.data.loop_triangles)
        ev=obj.evaluated_get(deps); mesh=ev.to_mesh();mesh.calc_loop_triangles();tri+=len(mesh.loop_triangles)
        used=set(p.material_index for p in mesh.polygons); draws+=len(used)
        materials.update(obj.material_slots[i].material.name for i in used if i<len(obj.material_slots) and obj.material_slots[i].material)
        sig=tuple(sorted(tuple(round(c,6) for c in (obj.matrix_world@v.co)) for v in mesh.vertices))
        if sig in signatures: duplicates.append([signatures[sig],obj.name])
        else:signatures[sig]=obj.name
        ev.to_mesh_clear()
    low=[min(p[i] for p in corners) for i in range(3)];high=[max(p[i] for p in corners) for i in range(3)]
    record={'asset':key,'source':str(path.relative_to(ROOT)).replace('\\','/'),'meshes':len(objs),'material_groups':len(materials),'draw_sections':draws,'base_triangles':base_tri,'evaluated_triangles':tri,'min':low,'max':high,'dimensions':[high[i]-low[i] for i in range(3)],'mesh_issues':bad,'duplicate_objects':duplicates,'animated_objects':[o.name for o in objs if o.animation_data], 'negative_scale_objects':[o.name for o in objs if any(s<0 for s in o.scale)]}
    reports.append(record)
    print('AUDIT',key,'meshes',len(objs),'triangles',tri,'draws',draws,'issues',len(bad),'duplicates',len(duplicates),flush=True)
(OUT/'source_audit.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
print('AUDIT_COMPLETE',len(reports),flush=True)
