"""Naturalistic landscape revision: terrain relief, organic crowns and patchy understory.
Original islands remain available; new resources are loaded preferentially by the prototype.
"""
from pathlib import Path
import bpy,bmesh,math,random,json,sys,shutil,datetime
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Tools/Blender'))
helper=ROOT/'Tools/Blender/enrich_island_details.py'
H={'__file__':str(helper)};exec(helper.read_text(encoding='utf-8').split('\nrecords=[]\nfor key')[0],H)
MODELS=H['MODELS'];SOURCE=H['SOURCE'];OUT=ROOT/'Assets/LastLandfall/Art/Previews/Environment/NaturalIslands';OUT.mkdir(parents=True,exist_ok=True)
REPORT=ROOT/'Assets/LastLandfall/Art/Reports/IslandNatural';REPORT.mkdir(parents=True,exist_ok=True)
def smooth(a,b,t):
 t=max(0,min(1,(t-a)/(b-a)));return t*t*(3-2*t)
def noise(x,y):return (math.sin(x*.43+y*.18)+math.sin(x*.17-y*.51+2.1)*.56+math.sin(x*1.31+y*.77)*.21)/1.77
def sample(bvh,x,y):return bvh.ray_cast(Vector((x,y,100)),Vector((0,0,-1)),200)[0]
def bvh(o):return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n.inputs['Base Color'].default_value=m.diffuse_color;n.inputs['Roughness'].default_value=.9;return m

def tree_mesh(pine,variant,mats):
 rng=random.Random(771+variant+pine*100);bm=bmesh.new()
 def branch(a,b,r):
  d=Vector(b)-Vector(a);before=set(bm.faces)
  bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=7,radius1=r,radius2=r*.55,depth=d.length,matrix=Matrix.Translation((Vector(a)+Vector(b))/2)@d.to_track_quat('Z','Y').to_matrix().to_4x4())
  for f in bm.faces:
   if f not in before:f.material_index=0
 branch((0,0,0),(0,0,.83 if pine else .66),.025)
 centers=[]
 if pine:
  for layer in range(5):
   z=.29+layer*.14;radius=.30*(1-layer*.16)
   for k in range(5):
    a=k*math.tau/5+layer*.53;centers.append((Vector((math.cos(a)*radius*.58,math.sin(a)*radius*.58,z)),radius*.65,.15))
 else:
  for k in range(10):
   a=k*2.39996+variant;rad=rng.uniform(.12,.28);centers.append((Vector((math.cos(a)*rad,math.sin(a)*rad,rng.uniform(.48,.83))),rng.uniform(.17,.24),rng.uniform(.17,.25)))
 for i,(c,r,h) in enumerate(centers):
  branch((0,0,c.z*.7),c,.009)
  before=set(bm.faces);created=bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1)['verts']
  for v in created:
   p=v.co.copy();warp=1+.11*math.sin(p.x*8+p.y*13+i)+.07*math.sin(p.z*11-p.y*7)
   v.co=c+Vector((p.x*r*warp,p.y*r*warp,p.z*h*warp))
  for f in bm.faces:
   if f not in before:f.material_index=1+i%3
 mesh=bpy.data.meshes.new(('NaturalPine' if pine else 'NaturalBroadleaf')+str(variant));bm.to_mesh(mesh);bm.free()
 lo=[min(v.co[j] for v in mesh.vertices) for j in range(3)];hi=[max(v.co[j] for v in mesh.vertices) for j in range(3)]
 for v in mesh.vertices:v.co=Vector(((v.co.x-lo[0])/(hi[0]-lo[0])-.5,(v.co.y-lo[1])/(hi[1]-lo[1])-.5,(v.co.z-lo[2])/(hi[2]-lo[2])))
 for p in mesh.polygons:p.use_smooth=True
 for m in mats:mesh.materials.append(m)
 return mesh

from natural_island_surface import terrain_material

records=[]
for group in ('Main','Twins'):
 if '--twins-only' in sys.argv and group=='Main':continue
 if group=='Main':
  bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'IslandReference_Gate25_Bamboo.blend'))
  objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('gate_export',False)]
  for o in bpy.context.scene.objects:
   if o.type=='MESH' and o not in objects:o.hide_render=True
  asset='IslandReference_Gate25_Natural'
 else:
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(MODELS/'LastLandfall_Basin_TwinIslands_Gate26.fbx'));objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];asset='BasinTwinIslands_Natural_v2'
 terrains=[o for o in objects if 'terrain source' in o.name.lower()];old={o.name:bvh(o) for o in terrains}
 # Store review baselines before the new palette, geometry or vegetation distribution.
 scene,cam=H['make_scene']()
 def review(suffix):
  for terrain in terrains:
   key='Main' if group=='Main' else ('East' if 'East' in terrain.name else 'West')
   corners=[terrain.matrix_world@Vector(v) for v in terrain.bound_box];low=[min(p[i] for p in corners) for i in range(3)];high=[max(p[i] for p in corners) for i in range(3)];center=Vector(((low[0]+high[0])/2,(low[1]+high[1])/2,2));span=max(high[0]-low[0],high[1]-low[1])
   saved={o:o.hide_render for o in objects}
   for o in objects:
    if o==terrain:continue
    corners=[o.matrix_world@Vector(v) for v in o.bound_box];p=sum(corners,Vector())/8
    if sample(old[terrain.name],p.x,p.y) is None:o.hide_render=True
   cam.data.ortho_scale=span*1.12;cam.location=center+Vector((span*.55,-span*.9,span*.85));H['aim'](cam,center+Vector((0,0,2)));scene.render.filepath=str(OUT/f'{key}_{suffix}.png');bpy.ops.render.render(write_still=True)
   for o,hidden in saved.items():o.hide_render=hidden
 review('Before')
 changed=0
 for o in terrains:
  inv=o.matrix_world.inverted();normal_matrix=o.matrix_world.to_3x3().inverted().transposed()
  normals=[v.normal.copy() for v in o.data.vertices]
  for index,v in enumerate(o.data.vertices):
   p=o.matrix_world@v.co;n=(normal_matrix@normals[index]).normalized();height=p.z+.92;slope=1-abs(n.z)
   protected=(group=='Main' and ((p.x/7.8)**2+(p.y/6.0)**2<1 or math.hypot(p.x-4.5,p.y+1.8)<4 or H['distance_path'](p.x,p.y)<1.8)) or (group=='Twins' and 'East' in o.name and 4.5<p.x<15.5 and 27<p.y<57)
   w=smooth(2.8,6.5,height)*smooth(.055,.22,slope)
   if group=='Twins':w=max(w,smooth(8,14,height)*.55)
   if protected or w<.001:continue
   amount=.34 if group=='Main' else .82
   q=p.copy();q.x+=noise(p.x*.42,p.y*.33)*amount*w;q.y+=noise(p.y*.37,-p.x*.29)*amount*.68*w
   # Break up the face in all three dimensions. A periodic height-only signal
   # turns the slope mask into artificial horizontal grass terraces.
   q.z+=noise(p.x*1.4+p.z*.31,p.y*1.1-p.z*.47)*amount*.42*w
   if group=='Twins':
    ridge=smooth(5,14,height)
    q.x+=(1.5*math.sin(p.y*.21)+.8*math.sin(p.x*.34+1.2))*ridge
    q.y+=math.sin(p.x*.17+p.y*.08)*ridge
    q.z-=max(0,height-9)*.14*ridge
   v.co=inv@q;changed+=1
  o.data.update();o.data.materials.clear();o.data.materials.append(terrain_material())
  for p in o.data.polygons:p.material_index=0;p.use_smooth=True
  print('NATURAL_TERRAIN_READY',o.name,changed,flush=True)
 bpy.context.view_layer.update();new={o.name:bvh(o) for o in terrains}
 mats=[mat('Natural_Bark',(.15,.105,.065)),mat('Natural_Leaves_Shadow',(.075,.16,.045)),mat('Natural_Leaves_Mid',(.13,.24,.065)),mat('Natural_Leaves_Sun',(.21,.31,.09))]
 templates={(pine,v):tree_mesh(pine,v,mats) for pine in (False,True) for v in range(3)}
 excluded=set();replaced=0;moved=0;shrunk=set()
 for index,o in enumerate(objects):
  if o in terrains or 'water' in o.name.lower():continue
  bounds=[o.matrix_world@Vector(v) for v in o.bound_box];center=sum(bounds,Vector())/8
  root=o.matrix_world.translation.copy()
  if (root.xy-center.xy).length>max(1,(bounds[6]-bounds[0]).length*.6):root=center.copy()
  target=next((t for t in terrains if sample(old[t.name],root.x,root.y) is not None),None)
  if target is not None:
   a=sample(old[target.name],root.x,root.y);b=sample(new[target.name],root.x,root.y)
   if a is not None and b is not None:
    delta=b.z-a.z
    if abs(delta)>.001:
     matrix=o.matrix_world.copy();matrix.translation.z+=delta;o.matrix_world=matrix;moved+=1
  name=o.name.lower()
  if 'broadleaf' in name or 'pine_' in name:
   local_min=[min(v.co[j] for v in o.data.vertices) for j in range(3)];local_max=[max(v.co[j] for v in o.data.vertices) for j in range(3)]
   mesh=templates[('pine_' in name,index%3)].copy()
   for v in mesh.vertices:v.co=Vector((local_min[0]+(v.co.x+.5)*(local_max[0]-local_min[0]),local_min[1]+(v.co.y+.5)*(local_max[1]-local_min[1]),local_min[2]+v.co.z*(local_max[2]-local_min[2])))
   o.data=mesh;replaced+=1
  elif 'grass_' in name or 'wildflower' in name:
   field=noise(center.x*.45,center.y*.45)
   # Continuous patches with quiet gaps replace the evenly scattered carpet.
   if field<-.12 or ('wildflower' in name and index%3!=0):excluded.add(o);o.hide_render=True
   else:
    if o.data not in shrunk:
     low=min(v.co.z for v in o.data.vertices)
     for v in o.data.vertices:v.co.z=low+(v.co.z-low)*.68
     shrunk.add(o.data)
    for m in o.data.materials:
     if m and any(s in m.name.lower() for s in ('grass','leaf')):
      m.diffuse_color=(.17,.26,.10,1)
      bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m.use_nodes else None
      if bs:bs.inputs['Base Color'].default_value=m.diffuse_color
 bpy.context.view_layer.update();review('After')
 export=[o for o in objects if o not in excluded]
 bpy.context.preferences.filepaths.save_version=0;source_path=SOURCE/(asset+'.blend')
 try:bpy.ops.wm.save_as_mainfile(filepath=str(source_path),compress=True)
 except RuntimeError as error:
  temporary=Path(str(source_path)+'@')
  if 'Cannot change old file' not in str(error) or not temporary.exists():raise
  # Windows can hold an existing source open. Preserve the fully written candidate
  # under a fresh name and continue exporting the current in-memory scene.
  source_path=SOURCE/(asset+'_Editable_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')
  shutil.copy2(temporary,source_path)
 bpy.ops.object.select_all(action='DESELECT')
 for o in export:o.select_set(True)
 bpy.context.view_layer.objects.active=terrains[0]
 bpy.ops.export_scene.fbx(filepath=str(MODELS/(asset+'.fbx')),use_selection=True,global_scale=1,apply_unit_scale=True,axis_forward='-Z',axis_up='Y',object_types={'MESH'},mesh_smooth_type='OFF',bake_space_transform=False,add_leaf_bones=False,use_mesh_modifiers=True,path_mode='COPY',embed_textures=True,bake_anim=False)
 H['meta'](source_path);H['meta'](MODELS/(asset+'.fbx'))
 records.append(dict(asset=asset,source=source_path.relative_to(ROOT).as_posix(),terrain_vertices_adjusted=changed,organic_trees=replaced,groundcover_hidden=len(excluded),reprojected_objects=moved,export_objects=len(export)))
 print('NATURAL_ISLAND_COMPLETE',records[-1],flush=True)
manifest=REPORT/'manifest.json'
index={r['asset']:r for r in json.loads(manifest.read_text(encoding='utf-8'))} if manifest.exists() else {}
index.update({r['asset']:r for r in records})
if 'BasinTwinIslands_Natural_v2' in index:index.pop('BasinTwinIslands_Natural',None)
manifest.write_text(json.dumps(list(index.values()),ensure_ascii=False,indent=2),encoding='utf-8')
print('NATURAL_ISLANDS_COMPLETE',flush=True)
