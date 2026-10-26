"""Detached flood-survivor lighthouse reef and five reversible construction stages."""
import bpy, math, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Assets/LastLandfall/Resources/Models/Lighthouse';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'Assets/LastLandfall/Art/Source/Environment/Lighthouse_Stages.blend'
random.seed(271027)
bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(name,color,rough=.8,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    return m
rock=mat('Lighthouse | wet basalt',(.15,.19,.19));stone=mat('Lighthouse | old stone',(.43,.43,.37))
white=mat('Lighthouse | salt weathered ivory',(.70,.70,.60));red=mat('Lighthouse | faded rescue red',(.38,.12,.075))
iron=mat('Lighthouse | dark marine iron',(.075,.12,.13),.45,.65);wood=mat('Lighthouse | reclaimed timber',(.29,.22,.13))
glass=mat('Lighthouse | lantern blue glass',(.13,.32,.36),.2,.35);gold=mat('Lighthouse | brass lens',(.65,.47,.17),.3,.65)
lantern_glass=mat('Lighthouse | lantern glazing',(.19,.37,.38),.12,.05)
def cube(name,loc,scale,m,rot=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.rotation_euler.z=rot;o.data.materials.append(m)
    mod=o.modifiers.new('Soft worn edges','BEVEL');mod.width=.025;mod.segments=2
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    return o
def cylinder(name,r1,r2,h,z,m,xy=(0,0),segments=48):
    bpy.ops.mesh.primitive_cone_add(vertices=segments,radius1=r1,radius2=r2,depth=h,location=(*xy,z))
    o=bpy.context.object;o.name=name;o.data.materials.append(m)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o
def rail(radius,z):
    for i in range(24):
        a=math.tau*i/24;b=math.tau*(i+1)/24
        p=Vector((math.cos(a)*radius,math.sin(a)*radius,z));q=Vector((math.cos(b)*radius,math.sin(b)*radius,z))
        o=cube('Gallery rail',tuple((p+q)*.5),(float((q-p).length),.055,.065),iron,math.atan2(q.y-p.y,q.x-p.x))
        if i%2==0:cube('Gallery baluster',(p.x,p.y,z-.43),(.06,.06,.9),iron)
def export(name,items):
    bpy.ops.object.select_all(action='DESELECT')
    for o in items:o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False)
reef=[]
for i in range(18):
    a=random.uniform(0,math.tau);r=random.uniform(1,6)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(math.cos(a)*r,math.sin(a)*r,random.uniform(-1.3,-.7)))
    o=bpy.context.object;o.name='Flood-worn lighthouse reef';o.scale=(random.uniform(1.3,3),random.uniform(1.3,3),random.uniform(.9,1.5));o.data.materials.append(rock);reef.append(o)
export('Lighthouse_Reef',reef)
stages=[]
for stage in range(5):
    before=set(bpy.context.scene.objects)
    cylinder('Stone foundation footing',3.7,3.4,.6,.65,stone)
    cylinder('Foundation landing',3.4,3.4,.18,1.02,white)
    for i in range(6):cube('Stone access step',(0,-3.1-i*.33,.85-i*.13),(1.8,.4,.22),stone)
    if stage==0:
        cylinder('Foundation anchor ring',2.05,2.05,.32,1.25,iron)
        for i in range(8):
            a=i*math.tau/8;cylinder('Anchor bolt',.07,.07,.35,1.5,iron,(math.cos(a)*2,math.sin(a)*2),12)
        cube('Salvaged survey chest',(2.2,1.1,1.45),(.65,.8,.65),wood)
    if stage>=1:
        cylinder('Masonry plinth',2.65,2.4,1.4,1.8,stone)
        for i in range(16):
            a=i*math.tau/16;cube('Plinth dressed stone',(math.cos(a)*2.48,math.sin(a)*2.48,1.6),(.85,.28,.65),stone,a+math.pi/2)
    if stage==1:
        cylinder('Tower setting out ring',1.95,1.95,.12,2.55,iron)
        for i in range(7):cube('Reclaimed beam stock',(2.8,0,1.35+i*.13),(.14,2.8,.13),wood)
    if stage>=2:
        height=7 if stage==2 else 14.5
        for course in range(int(height/.5)):
            z=2.5+course*.5;r=2.2-(z-2.5)*.035
            m=stone if stage==2 else (red if 8.5<z<10.6 else white)
            cylinder('Tower masonry course',r,r-.018,.49,z+.245,m)
        cube('Iron entrance door',(0,-2.2,3.4),(.95,.11,1.8),iron)
        for z in (5.5,9.5,13.5):
            if z<height+2:cube('Recessed tower window',(0,-(2.2-(z-2.5)*.035),z),(.38,.12,.65),glass)
    if stage==2:
        for a in (0,math.pi/2,math.pi,3*math.pi/2):
            x,y=math.cos(a)*2.9,math.sin(a)*2.9;cube('Scaffold upright',(x,y,5.4),(.13,.13,8),wood)
            for z in (3.5,5.5,7.5):cube('Scaffold plank',(x,y,z),(3.3,.22,.1),wood,a+math.pi/2)
    if stage>=3:
        cylinder('Gallery support',1.8,2.7,.6,17.15,stone)
        cylinder('Gallery platform',2.75,2.75,.2,17.55,white)
        rail(2.55,18.6)
        cylinder('Lantern sill',1.5,1.5,.25,17.82,iron)
        cylinder('Lantern glazing',1.35,1.35,1.9,18.85,lantern_glass,segments=12)
        for i in range(12):
            a=i*math.tau/12;cube('Lantern mullion',(math.cos(a)*1.38,math.sin(a)*1.38,18.85),(.065,.065,2.0),iron)
        cylinder('Lantern roof brim',1.7,1.7,.16,19.95,iron)
        cylinder('Lantern roof',1.65,.15,.9,20.45,red,segments=24)
        cylinder('Lightning rod',.045,.045,1.1,21.25,iron,segments=12)
        if stage==4:
            cylinder('Operating Fresnel lens',.5,.5,1.2,18.8,gold,segments=24)
            cube('Solar battery cabinet',(2.2,1,1.65),(.6,.8,1.1),iron)
            solar=cube('Solar supply panel',(-2.7,.6,1.8),(1.0,1.8,.08),glass);solar.rotation_euler.y=.3
    items=list(set(bpy.context.scene.objects)-before)
    for o in items:o['construction_stage']=stage
    stages.append(items);export('Lighthouse_Stage_'+str(stage),items)
for i,items in enumerate(stages):
    for o in items:o.hide_set(i!=0)
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
print('LIGHTHOUSE_MODELS_COMPLETE: reef + five independent stages',flush=True)
