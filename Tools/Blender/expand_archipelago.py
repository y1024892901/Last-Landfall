"""Area-based archipelago expansion. Run with Blender --background --python.

Source FBXs remain untouched; each island exports independently at a shared origin.
The shore is a continuous low rocky apron, never a sandy beach.
"""
import bpy, math, json, random
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / 'Assets/LastLandfall/Resources/Models/Environment'
ART = ROOT / 'Assets/LastLandfall/Art/Source/Environment'
REPORT = ROOT / 'Art/Reports/IslandExpansion'
SEA = -.92
STEP = .40
rng = random.Random(271026)
REPORT.mkdir(parents=True, exist_ok=True)

def smooth(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)

def tree_for(obj):
    vs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return BVHTree.FromPolygons(vs, [list(p.vertices) for p in obj.data.polygons])

def sample(bvh, x, y):
    p, n, _, _ = bvh.ray_cast(Vector((x,y,150)), Vector((0,0,-1)), 300)
    return (p.z, n) if p else (SEA-4, Vector((0,0,1)))

def mountain_stream(xs,ys,h,objects,old,new,scale):
    """A descending channel from the actual mountain flank to the existing pond."""
    pond=next((o for o,a in objects if 'pond' in o.name.lower() and 'water' in o.name.lower()),None)
    if pond is None:return None
    points=[pond.matrix_world@v.co for v in pond.data.vertices]
    center=np.mean(np.array([list(p) for p in points]),axis=0)
    end=(center[:2]-old)*scale+new
    pond_z=SEA+(center[2]-SEA)*1.35
    peak_index=np.unravel_index(np.argmax(h),h.shape)
    peak=np.array([xs[peak_index[1]],ys[peak_index[0]]])
    start=peak+(end-peak)/np.linalg.norm(end-peak)*6
    # Follow a curved descending valley rather than the old stream's unrelated ridge.
    t=np.linspace(0,1,160)
    control1=start+(end-start)*.33+np.array([-1.8,-.6])
    control2=start+(end-start)*.70+np.array([1.4,-1.0])
    curve=(1-t[:,None])**3*start+3*(1-t[:,None])**2*t[:,None]*control1+3*(1-t[:,None])*t[:,None]**2*control2+t[:,None]**3*end
    ix=np.clip(np.rint((curve[:,0]-xs[0])/STEP).astype(int),0,len(xs)-1)
    iy=np.clip(np.rint((curve[:,1]-ys[0])/STEP).astype(int),0,len(ys)-1)
    heights=h[iy,ix].copy()
    heights=np.convolve(np.pad(heights,(4,4),mode='edge'),np.ones(9)/9,mode='valid')
    water=np.maximum(pond_z+.003,np.minimum.accumulate(heights-.035))
    # Blend into the pond's exact water level; no downstream outlet is created.
    blend=smooth(.88,1,t);water=water*(1-blend)+(pond_z+.003)*blend
    widths=.38+.26*t
    xx,yy=np.meshgrid(xs,ys);nearest=np.full(h.shape,np.inf);indices=np.zeros(h.shape,dtype=int)
    for i,p in enumerate(curve):
        d=(xx-p[0])**2+(yy-p[1])**2
        closer=d<nearest;nearest=np.minimum(nearest,d);indices=np.where(closer,i,indices)
    distance=np.sqrt(nearest);local_water=water[indices];local_width=widths[indices]
    bed=np.where(distance<local_width,local_water-.14,local_water+.08+(distance-local_width)*.16)
    influence=1-smooth(local_width+.2,2.4,distance)
    h[:]=h*(1-influence)+bed*influence
    # Preserve the pool instead of growing a raised bank through its interior.
    old_low=np.min(np.array([list(p) for p in points]),axis=0)
    old_high=np.max(np.array([list(p) for p in points]),axis=0)
    radius=(old_high[:2]-old_low[:2])*scale*.49
    pool=((xx-end[0])/radius[0])**2+((yy-end[1])/radius[1])**2<1.06
    h[pool]=np.minimum(h[pool],pond_z-.10)
    return dict(curve=curve,water=water,widths=widths,pond=pond,source=list(start),pond_center=list(end),pond_height=pond_z)

def stream_object(data):
    curve=data['curve'];water=data['water'];widths=data['widths']
    vertices=[];uvs=[]
    for i,p in enumerate(curve):
        direction=curve[min(i+1,len(curve)-1)]-curve[max(0,i-1)]
        direction/=max(np.linalg.norm(direction),.001)
        side=np.array([-direction[1],direction[0]])
        for sign in (-1,1):
            xy=p+side*widths[i]*sign
            vertices.append((float(xy[0]),float(xy[1]),float(water[i])))
            uvs.append(((sign+1)*.5,i*.12))
    faces=[(i*2,i*2+2,i*2+3,i*2+1) for i in range(len(curve)-1)]
    mesh=bpy.data.meshes.new('Mountain spring flowing ribbon');mesh.from_pydata(vertices,[],faces);mesh.update()
    uv=mesh.uv_layers.new()
    for p in mesh.polygons:
        for loop in p.loop_indices:uv.data[loop].uv=uvs[mesh.loops[loop].vertex_index]
    for slot in data['pond'].material_slots:mesh.materials.append(slot.material)
    obj=bpy.data.objects.new('Basin_Stream_Water_MountainSpring',mesh);bpy.context.collection.objects.link(obj)
    return obj

def material():
    m = bpy.data.materials.new('Expanded terrain | grass soil and wet basalt, no sand')
    m.diffuse_color = (.22,.28,.12,1)
    m.use_nodes = True
    n=m.node_tree.nodes; l=m.node_tree.links; bs=n.get('Principled BSDF')
    bs.inputs['Roughness'].default_value=.9
    geo=n.new('ShaderNodeNewGeometry'); sep=n.new('ShaderNodeSeparateXYZ')
    l.new(geo.outputs['Position'],sep.inputs[0])
    ramp=n.new('ShaderNodeMapRange'); ramp.inputs['From Min'].default_value=SEA+.08
    ramp.inputs['From Max'].default_value=SEA+1.4
    l.new(sep.outputs['Z'],ramp.inputs['Value'])
    mix=n.new('ShaderNodeMixRGB'); mix.inputs[1].default_value=(.075,.10,.105,1)
    mix.inputs[2].default_value=(.23,.29,.12,1)
    l.new(ramp.outputs[0],mix.inputs[0]); l.new(mix.outputs[0],bs.inputs['Base Color'])
    return m

def reproject_details(key, old, new, scale, old_bvh, new_bvh, xs, ys, landing):
    """Move individual connected props inside the old material-batched detail layers.
    Weld FBX seam vertices before finding components so hard-edged rocks stay rigid.
    """
    path=MODELS/('IslandDetail_'+key+'.fbx')
    if not path.exists(): return []
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.fbx(filepath=str(path))
    imported=set(bpy.context.scene.objects)-before
    result=[]
    for obj in imported:
        if obj.type!='MESH': continue
        vs=[obj.matrix_world@v.co for v in obj.data.vertices]
        parent=list(range(len(vs)))
        def find(a):
            while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
            return a
        def union(a,b): parent[find(a)]=find(b)
        welded={}
        for i,v in enumerate(vs):
            token=tuple(round(float(c),4) for c in v)
            if token in welded: union(i,welded[token])
            else: welded[token]=i
        for edge in obj.data.edges: union(*edge.vertices)
        groups={}
        for i in range(len(vs)): groups.setdefault(find(i),[]).append(i)
        transformed={}
        for indices in groups.values():
            anchor=Vector(((min(vs[i].x for i in indices)+max(vs[i].x for i in indices))/2,
                (min(vs[i].y for i in indices)+max(vs[i].y for i in indices))/2,min(vs[i].z for i in indices)))
            xy=(np.array([anchor.x,anchor.y])-old)*scale+new
            z,_=sample(new_bvh,*xy)
            i=int((xy[0]-xs[0])/STEP);j=int((xy[1]-ys[0])/STEP)
            if z<SEA+.25 or not(0<=i<len(xs) and 0<=j<len(ys)) or landing[j,i]>-1: continue
            wreck=new+(np.array([10,42])-old)*scale
            if key=='East' and abs(xy[0]-wreck[0])<11 and abs(xy[1]-wreck[1])<20: continue
            old_z,_=sample(old_bvh,anchor.x,anchor.y)
            target=Vector((float(xy[0]),float(xy[1]),z+max(-.25,min(.4,anchor.z-old_z))))
            for index in indices: transformed[index]=vs[index]-anchor+target
        remap={index:i for i,index in enumerate(transformed)}
        faces=[]; slots=[]
        for polygon in obj.data.polygons:
            if all(index in remap for index in polygon.vertices):
                faces.append([remap[index] for index in polygon.vertices]); slots.append(polygon.material_index)
        if not faces: continue
        mesh=bpy.data.meshes.new('Grounded detail '+key)
        mesh.from_pydata(list(transformed.values()),[],faces); mesh.update()
        for slot in obj.material_slots: mesh.materials.append(slot.material)
        for p,slot in zip(mesh.polygons,slots):p.material_index=slot;p.use_smooth=True
        item=bpy.data.objects.new('Grounded detail | '+key+' | '+obj.name,mesh)
        bpy.context.collection.objects.link(item);result.append(item)
    for obj in imported: bpy.data.objects.remove(obj,do_unlink=True)
    return result

def build(key, source, old_center, new_center, ratio, height_scale):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(MODELS/source))
    terrains=[o for o in bpy.context.scene.objects if o.type=='MESH' and 'terrain source' in o.name.lower()]
    chosen=next(o for o in terrains if key=='Main' or key in o.name)
    bvh=tree_for(chosen)
    terrain_bvhs=[(tree_for(t),t) for t in terrains]
    # Select the twin's props by their actual supporting terrain, not object origins.
    objects=[]
    for o in list(bpy.context.scene.objects):
        if o.type!='MESH' or o in terrains: continue
        corners=[o.matrix_world@Vector(v) for v in o.bound_box]
        anchor=Vector(((min(v.x for v in corners)+max(v.x for v in corners))/2,
                       (min(v.y for v in corners)+max(v.y for v in corners))/2,
                       min(v.z for v in corners)))
        if key!='Main':
            hits=[(abs(sample(tb,anchor.x,anchor.y)[0]-anchor.z),t) for tb,t in terrain_bvhs]
            if min(hits,key=lambda q:q[0])[1] != chosen: continue
        objects.append((o,anchor))
    original_area=0
    chosen.data.calc_loop_triangles()
    vv=[chosen.matrix_world@v.co for v in chosen.data.vertices]
    for tri in chosen.data.loop_triangles:
        a,b,c=[vv[i] for i in tri.vertices]
        if (a.z+b.z+c.z)/3>-.9: original_area+=abs((b-a).cross(c-a).z)/2
    scale=math.sqrt(ratio)
    old=np.array(old_center); new=np.array(new_center)
    low=np.min(np.array([list(v) for v in vv]),axis=0)
    high=np.max(np.array([list(v) for v in vv]),axis=0)
    # Iterative area calibration accounts for shoreline rasterisation.
    for attempt in range(2):
        minimum=(low[:2]-old)*scale+new-5
        maximum=(high[:2]-old)*scale+new+5
        xs=np.arange(minimum[0],maximum[0]+STEP,STEP)
        ys=np.arange(minimum[1],maximum[1]+STEP,STEP)
        heights=np.empty((len(ys),len(xs)))
        for j,y in enumerate(ys):
            for i,x in enumerate(xs): heights[j,i]=sample(bvh,*((np.array([x,y])-new)/scale+old))[0]
        mask=heights>SEA+.02
        area=float(mask.sum()*STEP*STEP)
        if attempt==0: scale*=math.sqrt(original_area*ratio/area)
    # Distance inside the coast via repeated 8-connected erosions; continuous terraces.
    xx,yy=np.meshgrid(xs,ys)
    landing=np.full_like(heights,-1000.)
    bays=[]
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        if key=='East' and dx==-1: continue # Keep the wreck's rocky impact shore separate from working docks.
        shore=0.
        for r in np.arange(0,max(high[0]-low[0],high[1]-low[1])*scale,.35):
            xy=new+np.array([dx,dy])*r
            if sample(bvh,*((xy-new)/scale+old))[0]>SEA+.05: shore=r
        center=new+np.array([dx,dy])*(shore-4)
        normal=(xx-center[0])*dx+(yy-center[1])*dy
        tangent=-(xx-center[0])*dy+(yy-center[1])*dx
        qx=np.abs(tangent)-4.5; qy=np.abs(normal)-1.5
        sdf=4.5-np.sqrt(np.maximum(qx,0)**2+np.maximum(qy,0)**2)-np.minimum(np.maximum(qx,qy),0)
        landing=np.maximum(landing,sdf)
        bays.append(dict(center=list(center),outward=[dx,dy],width=18,depth=12))
    mask=mask | (landing>0)
    distance=np.zeros_like(heights); eroded=mask.copy()
    for _ in range(90):
        distance+=eroded*STEP
        eroded=eroded & np.roll(eroded,1,0) & np.roll(eroded,-1,0) & np.roll(eroded,1,1) & np.roll(eroded,-1,1)
        eroded[[0,-1],:]=False; eroded[:,[0,-1]]=False
    raw=SEA+(heights-SEA)*height_scale
    apron=SEA+1.66*smooth(0,5,distance)
    inland=smooth(6,15,distance)*(1-smooth(-5,2,landing))
    h=apron*(1-inland)+raw*inland
    # Sampled offshore bottom joins the shore without an extruded wall.
    outside=np.zeros_like(h); e=~mask
    for _ in range(18):
        outside+=e*STEP
        e=e & np.roll(e,1,0) & np.roll(e,-1,0) & np.roll(e,1,1) & np.roll(e,-1,1)
    h=np.where(mask,h,SEA-.04-3*smooth(0,5,outside))
    stream=mountain_stream(xs,ys,h,objects,old,new,scale) if key=='Main' else None
    vertices=[(float(x),float(y),float(h[j,i])) for j,y in enumerate(ys) for i,x in enumerate(xs)]
    nx=len(xs); faces=[]
    for j in range(len(ys)-1):
        for i in range(nx-1):
            a=j*nx+i; faces.extend([(a,a+1,a+nx+1),(a,a+nx+1,a+nx)])
    mesh=bpy.data.meshes.new(key+'_ExpandedSurface'); mesh.from_pydata(vertices,[],faces); mesh.update()
    terrain=bpy.data.objects.new(('IslandReference_V2' if key=='Main' else 'Basin_Island_'+key)+' (terrain source)',mesh)
    bpy.context.collection.objects.link(terrain); mesh.materials.append(material())
    for p in mesh.polygons: p.use_smooth=True
    new_bvh=tree_for(terrain)
    kept=[]; templates=[]
    for o,anchor in objects:
        name=o.name.lower()
        if stream is not None and ('stream' in name or 'creek' in name):continue
        water=any(k in name for k in ('water','stream','pond','creek'))
        if water:
            world=o.matrix_world.copy(); o.data=o.data.copy()
            for v in o.data.vertices:
                p=world@v.co; xy=(np.array([p.x,p.y])-old)*scale+new
                v.co=(xy[0],xy[1],SEA+(p.z-SEA)*height_scale)
            o.matrix_world=Matrix.Identity(4); kept.append(o); continue
        xy=(np.array([anchor.x,anchor.y])-old)*scale+new
        if stream is not None and np.min(np.sum((stream['curve']-xy)**2,axis=1))<2.8:continue
        z,normal=sample(new_bvh,*xy)
        i=int((xy[0]-xs[0])/STEP); j=int((xy[1]-ys[0])/STEP)
        if z<SEA+.2 or (0<=i<len(xs) and 0<=j<len(ys) and landing[j,i]>-1): continue
        old_z,_=sample(bvh,anchor.x,anchor.y)
        offset=max(-.2,min(.35,anchor.z-old_z))
        world=o.matrix_world.copy(); o.data=o.data.copy()
        for v in o.data.vertices: v.co=world@v.co-anchor
        o.matrix_world=Matrix.Translation(Vector((float(xy[0]),float(xy[1]),z+offset)))
        kept.append(o)
        if any(k in name for k in ('pine','broadleaf','grass','fern','rock','shrub','flower','tuft','bush','boulder')) and len(o.data.vertices)<12000:
            templates.append(o)
    # Add real-sized content while reserving the broad central settlement meadow.
    added=0; desired=max(0,int(len(objects)*ratio)-len(kept))
    is_tree=lambda o:any(k in o.name.lower() for k in ('pine','broadleaf'))
    tree_templates=[o for o in templates if is_tree(o)]
    target_trees=int(sum(is_tree(o) for o,_ in objects)*ratio)
    tree_count=sum(is_tree(o) for o in kept)
    meadow=(15,12) if key=='Main' else (7,5)
    for _ in range(desired*30):
        if added>=desired or not templates: break
        x=rng.uniform(xs[0],xs[-1]); y=rng.uniform(ys[0],ys[-1]); z,n=sample(new_bvh,x,y)
        if stream is not None and np.min(np.sum((stream['curve']-np.array([x,y]))**2,axis=1))<3.0:continue
        i=int((x-xs[0])/STEP); j=int((y-ys[0])/STEP)
        if z<SEA+.9 or n.z<(.88 if key=='Main' else .78) or distance[j,i]<5 or landing[j,i]>-1: continue
        if ((x-new[0])/meadow[0])**2+((y-new[1])/meadow[1])**2<1: continue
        t=rng.choice(tree_templates if tree_templates and tree_count<target_trees and rng.random()<.55 else templates)
        if any(k in t.name.lower() for k in ('pine','broadleaf')):
            if distance[j,i]<8: continue
            if any((q.location.x-x)**2+(q.location.y-y)**2<2.8 for q in kept if any(k in q.name.lower() for k in ('pine','broadleaf'))): continue
        o=bpy.data.objects.new(t.name.split('.')[0]+'_Expansion',t.data)
        bpy.context.collection.objects.link(o); o.location=(x,y,z-.025)
        for slot,source_slot in zip(o.material_slots,t.material_slots):
            slot.link='OBJECT'; slot.material=source_slot.material
        o.rotation_euler.z=rng.uniform(0,math.tau); o.scale=(1,1,1)
        kept.append(o); added+=1
        if is_tree(o): tree_count+=1
    detail_layers=reproject_details(key,old,new,scale,bvh,new_bvh,xs,ys,landing)
    kept.extend(detail_layers)
    if stream is not None:
        kept.append(stream_object(stream))
        spring_material=bpy.data.materials.new('Mountain spring dark fractured rock');spring_material.diffuse_color=(.15,.18,.15,1)
        for i in range(9):
            a=math.pi*i/8;p=np.array(stream['source'])+np.array([math.cos(a)*.95,math.sin(a)*.4])
            z,_=sample(new_bvh,*p)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(float(p[0]),float(p[1]),z+.15))
            rock=bpy.context.object;rock.name='Mountain spring weathered rock';rock.scale=(.42,.35,.38);rock.data.materials.append(spring_material);kept.append(rock)
        report=dict(source=stream['source'],pond_center=stream['pond_center'],pond_height=stream['pond_height'],
            source_height=float(stream['water'][0]),end_height=float(stream['water'][-1]),
            maximum_uphill_step=float(np.max(np.diff(stream['water']))),samples=len(stream['water']),
            maximum_ground_above_stream=max(sample(new_bvh,*p)[0]-float(z) for p,z in zip(stream['curve'],stream['water'])))
        (REPORT/'MountainStream.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    # Only this terrain and this island's props are exported.
    for o in list(bpy.context.scene.objects):
        if o!=terrain and o not in kept: bpy.data.objects.remove(o,do_unlink=True)
    terrain.name=('IslandReference_V2' if key=='Main' else 'Basin_Island_'+key)+' (terrain source)'
    bpy.ops.object.select_all(action='SELECT')
    output='Island_'+key+'_Expanded'
    bpy.ops.wm.save_as_mainfile(filepath=str(ART/(output+'.blend')))
    bpy.ops.export_scene.fbx(filepath=str(MODELS/(output+'.fbx')),use_selection=True,
        object_types={'MESH'},axis_forward='-Z',axis_up='Y',add_leaf_bones=False,bake_anim=False)
    mesh.calc_loop_triangles(); area=0; buildable=0
    for tri in mesh.loop_triangles:
        a,b,c=[mesh.vertices[i].co for i in tri.vertices]
        projected=abs((b-a).cross(c-a).z)/2
        if (a.z+b.z+c.z)/3>-.9:
            area+=projected
            if tri.normal.z>math.cos(math.radians(22)): buildable+=projected
    record=dict(island=key,file=output+'.fbx',old_center=list(old_center),center=list(new_center),scale=scale,
        original_area=original_area,land_area=area,area_ratio=area/original_area,
        slope_suitable_area=buildable,added_props=added,tree_count=tree_count,grounded_detail_layers=len(detail_layers),mesh_objects=len(kept)+1,sea_level=SEA,landing_bays=bays)
    print('EXPANDED_ISLAND',json.dumps(record),flush=True)
    return record

records=[]
for args in [('Main','IslandReference_Gate25_Natural.fbx',(0,0),(0,0),4.5,1.35),
             ('West','BasinTwinIslands_Natural_v2.fbx',(-25.6,44),(-65,102),1.7,1.05),
             ('East','BasinTwinIslands_Natural_v2.fbx',(25,43.5),(65,102),1.7,1.05)]:
    records.append(build(*args))
(REPORT/'ExpansionMetrics.json').write_text(json.dumps(records,indent=2),encoding='utf8')
print('ARCHIPELAGO_EXPANSION_COMPLETE',flush=True)
