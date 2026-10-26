import bpy,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path.cwd();folder=ROOT/'Assets/LastLandfall/Art/Reports/BuildingAudit'
if '--report-dir' in sys.argv:
 folder=ROOT/sys.argv[sys.argv.index('--report-dir')+1]
rows=json.loads((folder/'source_audit.json').read_text());out=[]
for row in rows:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/row['source']))
 objects=[o for o in bpy.data.collections[row['asset']].all_objects if o.type=='MESH']
 bounds=[]
 for o in objects:
  p=[o.matrix_world@Vector(c) for c in o.bound_box];bounds.append(([min(v[k] for v in p) for k in range(3)],[max(v[k] for v in p) for k in range(3)]))
 parent=list(range(len(objects)))
 def root(i):
  while parent[i]!=i:i=parent[i]
  return i
 for i,(lo,hi) in enumerate(bounds):
  for j in range(i):
   low,high=bounds[j]
   if all(hi[k]+.015>=low[k] and high[k]+.015>=lo[k] for k in range(3)):parent[root(i)]=root(j)
 groups={}
 for i in range(len(objects)):groups.setdefault(root(i),[]).append(i)
 floating=[]
 for indices in groups.values():
  z=min(bounds[i][0][2] for i in indices)
  if z>.03:floating.append({'objects':[objects[i].name for i in indices],'lowest_z_m':z})
 out.append({'asset':row['asset'],'disconnected_bounds_groups':floating})
 print('SUPPORT',row['asset'],floating,flush=True)
(folder/'support_candidates.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
