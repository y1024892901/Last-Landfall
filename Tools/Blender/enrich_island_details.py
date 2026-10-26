"""Add deterministic terrain-conforming detail layers to the three playable islands.
Original terrain, water, foliage and collision meshes are never saved over.
"""
from pathlib import Path
import bpy,bmesh,math,random,json,collections,uuid,re,sys
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Tools/Blender'))
SOURCE=ROOT/'Assets/LastLandfall/Art/Source/Environment'
MODELS=ROOT/'Assets/LastLandfall/Resources/Models/Environment'
PREVIEW=ROOT/'Assets/LastLandfall/Art/Previews/Environment/IslandDetail'
REPORT=ROOT/'Assets/LastLandfall/Art/Reports/IslandDetail'
for p in (SOURCE,MODELS,PREVIEW,REPORT):p.mkdir(parents=True,exist_ok=True)
STREAM=[(8.6,8.4),(8.6,7),(8,5.8),(7.6,4.5),(6.9,3.3),(6.2,2.3),(5.8,1.2),(5,.3),(4.7,-.2),(4.65,-.55)]
WATER=-.92
COLORS={'Basalt':(.18,.23,.24,1),'Stone':(.33,.37,.35,1),'WetStone':(.12,.19,.19,1),'Moss':(.25,.32,.17,1),'Bark':(.19,.14,.095,1),'WoodEnd':(.39,.32,.21,1),'Fern':(.23,.37,.28,1),'LeafLitter':(.30,.27,.15,1),'DryGrass':(.44,.42,.28,1)}

def distance_path(x,y):
 p=Vector((x,y));best=999
 for a,b in zip(STREAM,STREAM[1:]):
  a=Vector(a);d=Vector(b)-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared));best=min(best,(p-a-d*t).length)
 return best

def meta(path):
 m=Path(str(path)+'.meta')
 if m.exists():return
 guid=uuid.uuid5(uuid.NAMESPACE_URL,'LastLandfall/'+path.relative_to(ROOT).as_posix()).hex
 if path.suffix=='.fbx':
  text=(MODELS/'IslandReference_Gate25.fbx.meta').read_text(encoding='utf-8')
  text=re.sub(r'guid: [a-f0-9]+','guid: '+guid,text,count=1)
  for key,value in [('importCameras',0),('importLights',0),('importAnimation',0),('preserveHierarchy',1),('addColliders',0)]:text=re.sub(r'(\s'+key+r': )\d+',lambda m:m[1]+str(value),text)
 else:text='fileFormatVersion: 2\nguid: '+guid+'\n'
 m.write_text(text,encoding='utf-8')

def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def make_scene():
 s=bpy.context.scene
 for o in list(s.objects):
  if o.type in ('LIGHT','CAMERA'):bpy.data.objects.remove(o,do_unlink=True)
 world=bpy.data.worlds.new('IslandDetail Studio');world.use_nodes=True;next(n for n in world.node_tree.nodes if n.type=='BACKGROUND').inputs[0].default_value=(.32,.40,.44,1);next(n for n in world.node_tree.nodes if n.type=='BACKGROUND').inputs[1].default_value=.65;s.world=world
 light=bpy.data.lights.new('IslandDetail Sun','SUN');light.energy=2.2;light.angle=.18
 obj=bpy.data.objects.new('IslandDetail Sun',light);s.collection.objects.link(obj);obj.rotation_euler=(.5,-.4,-.6)
 bpy.ops.mesh.primitive_plane_add(size=400,location=(0,0,WATER-.035));o=bpy.context.object;o.name='DetailPreview_Ocean'
 m=bpy.data.materials.new('DetailPreview Ocean');m.diffuse_color=(.035,.13,.16,1);m.use_nodes=True;bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.4;o.data.materials.append(m)
 cam=bpy.data.objects.new('IslandDetail Camera',bpy.data.cameras.new('IslandDetail Camera'));s.collection.objects.link(cam);s.camera=cam;cam.data.type='ORTHO'
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1280;s.render.resolution_y=960;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
 s.eevee.taa_render_samples=24
 return s,cam

class Layer:
 def __init__(self,key,terrain,existing):
  self.key=key;self.rng=random.Random({'Main':261101,'West':261102,'East':261103}[key]);self.objects=[];self.records=[];self.counts=collections.Counter()
  self.collection=bpy.data.collections.new('IslandDetail_'+key);bpy.context.scene.collection.children.link(self.collection)
  ev=terrain.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();verts=[terrain.matrix_world@v.co for v in mesh.vertices]
  self.bvh=BVHTree.FromPolygons(verts,[list(p.vertices) for p in mesh.polygons]);ev.to_mesh_clear()
  self.low=[min(v[i] for v in verts) for i in range(3)];self.high=[max(v[i] for v in verts) for i in range(3)]
  self.trees=[o.matrix_world.translation.copy() for o in existing if any(v in o.name.lower() for v in ('broadleaf','pine','bamboo'))]
  bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1);self.rock_template=bpy.data.meshes.new('DetailRockTemplate');bm.to_mesh(self.rock_template);bm.free()
  self.materials={}
  for name,color in COLORS.items():
   m=bpy.data.materials.new('IslandDetail_'+name);m.diffuse_color=color;m.use_nodes=True;n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n.inputs['Base Color'].default_value=color;n.inputs['Roughness'].default_value=.92 if name!='WetStone' else .45;self.materials[name]=m
 def sample(self,x,y):
  p,n,_,_=self.bvh.ray_cast(Vector((x,y,100)),Vector((0,0,-1)),200)
  if p is None:return None
  if n.z<0:n=-n
  return p,n.normalized()
 def protected(self,p):
  if self.key=='Main':
   return (p.x/7.2)**2+(p.y/5.5)**2<1 or math.hypot(p.x-4.5,p.y+1.8)<3.5 or distance_path(p.x,p.y)<.8
  if self.key=='East':return 4.5<p.x<15.5 and 27<p.y<57
  return False
 def add(self,o,kind,mat):
  o.name=f'IslandDetail_{self.key}_{kind}_{len(self.objects):04d}'
  for c in list(o.users_collection):c.objects.unlink(o)
  self.collection.objects.link(o);o.data.materials.clear();o.data.materials.append(self.materials[mat]);o['detail_kind']=kind;self.objects.append(o);self.counts[kind]+=1
  return o
 def rock(self,p,n,r,kind='Talus',mat='Basalt'):
  o=bpy.data.objects.new('DetailRock',self.rock_template.copy());o.location=p-n*r*.12
  o.rotation_mode='QUATERNION';o.rotation_quaternion=n.to_track_quat('Z','Y');o.scale=(r*self.rng.uniform(.9,1.5),r*self.rng.uniform(.65,1.05),r*self.rng.uniform(.35,.65));self.add(o,kind,mat);return o
 def stick(self,a,b,r,mat='Bark',kind='Driftwood'):
  d=b-a;verts=[(math.cos(k*math.tau/7)*r,math.sin(k*math.tau/7)*r,z) for z in (-d.length/2,d.length/2) for k in range(7)]
  faces=[(k,(k+1)%7,(k+1)%7+7,k+7) for k in range(7)]+[tuple(reversed(range(7))),tuple(range(7,14))]
  mesh=bpy.data.meshes.new('DetailBranch');mesh.from_pydata(verts,[],faces);o=bpy.data.objects.new('DetailBranch',mesh);o.location=(a+b)/2
  o.rotation_euler=d.to_track_quat('Z','Y').to_euler();self.add(o,kind,mat)
 def fern(self,p,n,kind='Fern'):
  verts=[];faces=[]
  basis=n.to_track_quat('Z','Y').to_matrix()
  for f in range(5):
   ang=f*math.tau/5+self.rng.uniform(-.3,.3);axis=Vector((math.cos(ang),math.sin(ang),0));side=Vector((-axis.y,axis.x,0))
   previous=None
   for k in range(7):
    t=k/6;center=axis*(.48*t)+Vector((0,0,.52*math.sin(t*1.6)));idx=len(verts)
    verts += [p+basis@(center+side*.009),p+basis@(center-side*.009)]
    if previous is not None:faces.extend([(previous,previous+1,idx),(previous+1,idx+1,idx)])
    previous=idx
   for k in range(1,6):
    t=k/6;center=axis*(.48*t)+Vector((0,0,.52*math.sin(t*1.6)));width=.15*(1-t*.7)
    for sign in (-1,1):
     leaf=[center-axis*.07,center+axis*.08,center+side*width*sign+axis*.015,center+Vector((0,0,.035))]
     idx=len(verts);verts += [p+basis@v for v in leaf];faces.extend([(idx,idx+1,idx+2),(idx,idx+3,idx+1)])
  mesh=bpy.data.meshes.new('FernFronds');mesh.from_pydata(verts,[],faces);o=bpy.data.objects.new('Fern',mesh);bpy.context.scene.collection.objects.link(o);self.add(o,kind,'Fern')
 def patch(self,p,n):
  for k in range(8):
   x=p.x+self.rng.uniform(-.45,.45);y=p.y+self.rng.uniform(-.45,.45);hit=self.sample(x,y)
   if not hit:continue
   q,normal=hit
   if q.z<WATER+.08 or self.protected(q):continue
   self.rock(q+normal*.014,normal,self.rng.uniform(.07,.14),'LeafLitter','LeafLitter').scale.z=.015
 def populate(self):
  candidates={'Shore':[],'Woodland':[],'Rock':[],'Creek':[]}
  step=1.25
  x=self.low[0]+step
  while x<self.high[0]-step:
   y=self.low[1]+step
   while y<self.high[1]-step:
    hit=self.sample(x+self.rng.uniform(-.4,.4),y+self.rng.uniform(-.4,.4))
    if hit:
     p,n=hit
     if p.z>WATER+.08 and not self.protected(p):
      nearest=min(((p.xy-v.xy).length for v in self.trees),default=99)
      if WATER+.08<p.z<WATER+.85 and n.z>.65:candidates['Shore'].append((p,n))
      if .52<n.z<.91 and p.z>WATER+.65:candidates['Rock'].append((p,n))
      if .6<nearest<2.1 and n.z>.82 and p.z>WATER+.8:candidates['Woodland'].append((p,n))
      if self.key=='Main' and .8<distance_path(p.x,p.y)<1.5 and n.z>.73:candidates['Creek'].append((p,n))
    y+=step
   x+=step
  targets={'Main':{'Shore':20,'Rock':22,'Woodland':24,'Creek':14},'West':{'Shore':20,'Rock':42,'Woodland':14,'Creek':0},'East':{'Shore':26,'Rock':28,'Woodland':18,'Creek':0}}[self.key]
  for zone,points in candidates.items():
   self.rng.shuffle(points);chosen=[]
   for p,n in points:
    if len(chosen)>=targets[zone]:break
    if any((p.xy-q.xy).length<1.7 for q in chosen):continue
    chosen.append(p);self.records.append(dict(zone=zone,position=list(p),normal=list(n)))
    if zone in ('Rock','Creek'):
     if zone=='Rock' and p.z>3 and len(chosen)%2==0:
      ledge=self.rock(p,n,self.rng.uniform(.50,.85),'ErodedLedge','Stone');ledge.scale.y*=1.35;ledge.scale.z*=.45
     for j in range(self.rng.randint(4,7)):
      hit=self.sample(p.x+self.rng.uniform(-.65,.65),p.y+self.rng.uniform(-.65,.65))
      if not hit:continue
      q,normal=hit
      if q.z<WATER+.04 or self.protected(q):continue
      stone=self.rock(q,normal,self.rng.uniform(.16,.40) if zone=='Rock' else self.rng.uniform(.10,.24),'Talus' if zone=='Rock' else 'CreekPebble','Basalt' if zone=='Rock' else 'WetStone')
      if j==0 and self.key!='East':
       cap=self.rock(stone.location+normal*stone.scale.z*.8,normal,min(stone.scale.x,stone.scale.y)*.72,'MossCap','Moss');cap.scale.z=.035
    elif zone=='Woodland':
     self.fern(p+n*.015,n);self.patch(p,n)
     if len(chosen)%3==0:
      angle=self.rng.random()*math.tau;d=Vector((math.cos(angle),math.sin(angle),0))*.7
      ends=[self.sample(p.x+v.x,p.y+v.y) for v in (-d,d)]
      if all(ends) and not any(self.protected(e[0]) for e in ends):
       a,b=[e[0]+Vector((0,0,.065)) for e in ends];self.stick(a,b,.075,'Bark','FallenBranch');self.stick(b-(b-a).normalized()*.025,b,.077,'WoodEnd','CutWoodEnd')
    else:
     if len(chosen)%2==0:
      tangent=Vector((-n.y,n.x,0));tangent.normalize()
      if tangent.length<.1:tangent=Vector((1,0,0))
      for j in range(3):
       center=p+Vector((self.rng.uniform(-.3,.3),self.rng.uniform(-.3,.3),0));length=self.rng.uniform(.35,.8)
       ends=[self.sample(center.x+tangent.x*t,center.y+tangent.y*t) for t in (-length,length)]
       if all(ends) and not any(self.protected(e[0]) for e in ends):self.stick(ends[0][0]+Vector((0,0,.045)),ends[1][0]+Vector((0,0,.045)),self.rng.uniform(.035,.065))
     else:
      for j in range(4):
       hit=self.sample(p.x+self.rng.uniform(-.4,.4),p.y+self.rng.uniform(-.4,.4))
       if hit and not self.protected(hit[0]) and hit[0].z>WATER+.04:self.rock(hit[0],hit[1],self.rng.uniform(.12,.25),'ShorePebble','WetStone')
      self.fern(p+n*.015,n,'SaltFern')
  bpy.context.view_layer.update()
  print('DETAIL_PLACED',self.key,len(self.objects),dict(self.counts),flush=True)
  return self
 def export(self):
  # Save individual editable details; source contains no copied terrain or presentation meshes.
  path=SOURCE/f'IslandDetail_{self.key}.blend'
  # Save a separate detail-only scene through a temporary copy of the current scene.
  original=bpy.context.window.scene;detail_scene=bpy.data.scenes.new('IslandDetail_'+self.key);detail_scene.collection.children.link(self.collection)
  bpy.context.window.scene=detail_scene;bpy.context.preferences.filepaths.save_version=0
  # Library write includes only this scene and its dependencies, preserving the presentation scene in memory.
  bpy.data.libraries.write(str(path),{detail_scene},fake_user=True,compress=True)
  bpy.context.window.scene=original;bpy.data.scenes.remove(detail_scene);meta(path)
  groups=collections.defaultdict(list)
  for o in self.objects:
   groups[o.data.materials[0].name].append(o)
  copies=[]
  for material,objects in groups.items():
   bpy.ops.object.select_all(action='DESELECT');batch=[]
   for original in objects:
    mesh=original.data.copy();mesh.transform(original.matrix_world)
    obj=bpy.data.objects.new('ExportDetail',mesh);bpy.context.scene.collection.objects.link(obj);obj.select_set(True);batch.append(obj)
   bpy.context.view_layer.objects.active=batch[0]
   if len(batch)>1:bpy.ops.object.join()
   merged=bpy.context.object;merged.name=f'IslandDetail_{self.key}_{material}';copies.append(merged)
  bpy.ops.object.select_all(action='DESELECT')
  for o in copies:o.select_set(True)
  target=MODELS/f'IslandDetail_{self.key}.fbx'
  bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,global_scale=1,apply_unit_scale=True,axis_forward='-Z',axis_up='Y',object_types={'MESH'},mesh_smooth_type='OFF',bake_space_transform=False,add_leaf_bones=False,use_mesh_modifiers=True,bake_anim=False,use_triangles=True)
  meta(target)
  for o in copies:o.data.calc_loop_triangles()
  record=dict(island=self.key,editable_objects=len(self.objects),export_meshes=len(copies),triangles=sum(len(o.data.loop_triangles) for o in copies),features=dict(self.counts),placements=self.records,source=path.relative_to(ROOT).as_posix(),model=target.relative_to(ROOT).as_posix(),original_terrain_changed=False)
  for o in copies:bpy.data.objects.remove(o,do_unlink=True)
  return record

def render(layer,scene,cam):
 center=Vector(((layer.low[0]+layer.high[0])/2,(layer.low[1]+layer.high[1])/2,1.5));span=max(layer.high[0]-layer.low[0],layer.high[1]-layer.low[1])
 cam.location=center+Vector((span*.62,-span*.94,span*.92));aim(cam,center+Vector((0,0,3)));cam.data.ortho_scale=span*1.18
 for o in layer.objects:o.hide_render=True
 scene.render.filepath=str(PREVIEW/(layer.key+'_Before.png'));bpy.ops.render.render(write_still=True)
 for o in layer.objects:o.hide_render=False
 scene.render.filepath=str(PREVIEW/(layer.key+'_After.png'));bpy.ops.render.render(write_still=True)
 # Focus on a populated border, using an actual accepted anchor rather than an arbitrary point.
 points=[r for r in layer.records if r['zone'] in ('Creek','Rock')]
 point=Vector(points[len(points)//3]['position']) if points else center
 cam.location=point+Vector((8,-12,10));aim(cam,point);cam.data.ortho_scale=15
 scene.render.filepath=str(PREVIEW/(layer.key+'_Detail.png'));bpy.ops.render.render(write_still=True)

records=[]
for key in ('Main','West','East'):
 if '--twins-only' in sys.argv and key=='Main':continue
 if key=='Main':
  base=SOURCE/'IslandReference_Gate25_Natural.blend'
  if not base.exists():base=SOURCE/'IslandReference_Gate25_Bamboo.blend'
  bpy.ops.wm.open_mainfile(filepath=str(base))
  for o in bpy.context.scene.objects:
   if o.type=='MESH' and not o.get('gate_export',False):o.hide_render=True
  terrain=next(o for o in bpy.data.objects if o.type=='MESH' and 'terrain source' in o.name and o.get('gate_export',False))
 else:
  base=MODELS/'BasinTwinIslands_Natural_v2.fbx'
  if not base.exists():base=MODELS/'BasinTwinIslands_Natural.fbx'
  if not base.exists():base=MODELS/'LastLandfall_Basin_TwinIslands_Gate26.fbx'
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(base))
  terrain=next(o for o in bpy.data.objects if 'Basin_Island_'+key+' (terrain source)'==o.name)
 existing=[o for o in bpy.context.scene.objects if o.type=='MESH']
 if key!='Main':
  other='East' if key=='West' else 'West'
  # Keep the other island out of this island's review frame without editing its source.
  for o in existing:
   if other in o.name:o.hide_render=True
 layer=Layer(key,terrain,existing).populate()
 if key!='Main':
  # Unity assigns the exposed-cliff slot its own basalt shader. Reproduce its
  # base color for Blender previews; FBX cannot carry the original procedural shader.
  if base.name.startswith('BasinTwinIslands_Natural'):
   from natural_island_surface import terrain_material
   terrain.data.materials.clear();terrain.data.materials.append(terrain_material())
   for face in terrain.data.polygons:face.material_index=0
  else:
   cliff=terrain.data.materials[1];cliff.diffuse_color=(.33,.35,.34,1)
   shader=next((n for n in cliff.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if cliff.use_nodes else None
   if shader:shader.inputs['Base Color'].default_value=cliff.diffuse_color
  for o in existing:
   if o==terrain:continue
   corners=[o.matrix_world@Vector(v) for v in o.bound_box];center=sum(corners,Vector())/8
   if layer.sample(center.x,center.y) is None:o.hide_render=True
 scene,cam=make_scene();render(layer,scene,cam);records.append(layer.export())
 print('ISLAND_DETAIL_COMPLETE',key,len(layer.objects),dict(layer.counts),flush=True)
old=REPORT/'manifest.json'
index={r['island']:r for r in json.loads(old.read_text(encoding='utf-8'))['islands']} if old.exists() else {}
index.update({r['island']:r for r in records})
records=[index[key] for key in ('Main','West','East') if key in index]
old.write_text(json.dumps(dict(asset_count=len(records),islands=records),ensure_ascii=False,indent=2),encoding='utf-8')
print('ISLAND_DETAIL_ALL_COMPLETE',flush=True)
