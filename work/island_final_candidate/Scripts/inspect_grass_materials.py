import bpy,json
from pathlib import Path
p=Path(r'D:\Last Landfall\work\island_final_candidate\Assets_Generated\LastLandfall_Island_GrassCoverage_Gate18.blend')
bpy.ops.wm.open_mainfile(filepath=str(p))
out={}
for o in bpy.data.objects:
 a=o.get('asset_id','')
 if a.startswith('Grass_'):
  out[a]=[]
  for m in o.data.materials:
   if m:
    out[a].append({'name':m.name,'diffuse':list(m.diffuse_color),'bsdf':[(list(n.inputs['Base Color'].default_value) if n.type=='BSDF_PRINCIPLED' and 'Base Color' in n.inputs else None) for n in (m.node_tree.nodes if m.use_nodes else [])]})
  break
print(json.dumps(out,ensure_ascii=False,indent=2))
