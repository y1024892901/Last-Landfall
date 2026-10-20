import bpy, math, json
from pathlib import Path
from mathutils import Vector
root=Path(r'D:\Last Landfall'); base=root/'work/island_final_candidate/Assets_Generated/LastLandfall_Island_Foliage_Assembly.blend'
bpy.ops.wm.open_mainfile(filepath=str(base)); terrain=next(o for o in bpy.data.objects if o.name.startswith('IslandReference_V2'))
def sample(x,y):
 hit,p,n,face=terrain.ray_cast(Vector((x/.02,y/.02,900)),Vector((0,0,-1)))
 return (p.z*.02-.92,n.z) if hit else None
centers=[(-16,12,6),(0,17,5),(17,6,5),(-22,1,4),(17,-12,4),(4,-22,5),(-18,-1,5),(22,-2,5)]
res={}
for cx,cy,r in centers:
 count=0; elig=[]
 y=cy-r
 while y<=cy+r:
  x=cx-r
  while x<=cx+r:
   if math.hypot(x-cx,y-cy)<=r:
    a=sample(x,y)
    if a:
     count+=1
     if a[0]>.25 and a[1]>.73: elig.append([round(x,1),round(y,1),round(a[0],2),round(a[1],2)])
   x+=.75
  y+=.75
 res[f'{cx},{cy}']={'samples':count,'eligible':len(elig),'examples':elig[:10]}
print(json.dumps(res,indent=2))
