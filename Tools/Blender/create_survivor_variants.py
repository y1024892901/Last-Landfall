"""Create two articulated low-poly flood survivors, with reusable shoulder and hip pivots."""
import bpy, math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
MODELS=ROOT/'Assets/LastLandfall/Resources/Models/Characters'
SOURCE=ROOT/'Assets/LastLandfall/Art/Source/Characters'
PREVIEWS=ROOT/'Assets/LastLandfall/Art/Previews/Characters'
for directory in (MODELS,SOURCE,PREVIEWS):directory.mkdir(parents=True,exist_ok=True)

def material(name,color,rough=.8,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    node=m.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Roughness'].default_value=rough;node.inputs['Metallic'].default_value=metal
    return m

def attach(obj,parent):
    bpy.context.view_layer.update()
    world=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=world;return obj

def pivot(name,where,parent):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=where;attach(o,parent);return o

def sphere(name,center,dimensions,mat,parent,segments=12,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=center)
    o=bpy.context.object;o.name=name;o.scale=dimensions;o.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return attach(o,parent)

def tapered(name,center,lower,upper,depth,mat,parent,flatten=.88):
    bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=lower,radius2=upper,depth=depth,location=center)
    o=bpy.context.object;o.name=name;o.scale.y=flatten;o.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return attach(o,parent)

def box(name,center,size,mat,parent,bevel=.035):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
    if bevel:
        modifier=o.modifiers.new('Soft durable edges','BEVEL');modifier.width=bevel;modifier.segments=2
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=modifier.name)
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return attach(o,parent)

def combine_static_parts():
    # Join by joint and material: fewer draw calls while each limb stays articulated.
    groups={}
    for o in list(bpy.context.scene.objects):
        if o.type=='MESH' and o.parent is not None and len(o.data.materials)==1:
            groups.setdefault((o.parent,o.data.materials[0]),[]).append(o)
    for objects in groups.values():
        if len(objects)<2:continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        bpy.ops.object.join()

def build(key,coat,vest,skin,hat,gear):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats={
        'skin':material('Survivor | skin',skin),
        'coat':material('Survivor | weathered jacket',coat),
        'vest':material('Survivor | rescue vest',vest),
        'pants':material('Survivor | work trousers',(.22,.25,.24)),
        'boots':material('Survivor | rubber boots',(.075,.10,.105)),
        'hat':material('Survivor | headwear',hat),
        'gear':material('Survivor | reclaimed gear',gear),
        'hair':material('Survivor | hair',(.11,.085,.067)),
        'eye':material('Survivor | face details',(.055,.065,.06)),
        'metal':material('Survivor | buckle',(.48,.52,.49),.35,.55),
    }
    root=bpy.data.objects.new(key+'_Root',None);bpy.context.collection.objects.link(root)
    sphere('Hips',(0,0,.91),(.235,.16,.13),mats['pants'],root)
    tapered('Rain jacket torso',(0,0,1.19),.235,.285,.53,mats['coat'],root,.7)
    sphere('Jacket shoulders',(0,0,1.42),(.28,.19,.10),mats['coat'],root)
    box('Life jacket left',(-.12,-.175,1.22),(.20,.085,.35),mats['vest'],root,.045)
    box('Life jacket right',(.12,-.175,1.22),(.20,.085,.35),mats['vest'],root,.045)
    box('Life jacket back',(0,.15,1.22),(.42,.08,.34),mats['vest'],root,.05)
    box('Vest waist belt',(0,-.227,1.09),(.40,.035,.045),mats['gear'],root,.01)
    box('Vest centre buckle',(0,-.25,1.09),(.065,.025,.065),mats['metal'],root,.008)
    box('Radio',(-.12,-.234,1.33),(.07,.045,.10),mats['boots'],root,.012)
    box('Radio antenna',(-.135,-.24,1.41),(.012,.012,.11),mats['metal'],root,.002)
    box('Utility belt',(0,0,.96),(.48,.33,.08),mats['gear'],root,.022)
    box('Small side pouch',(.25,.02,.93),(.10,.14,.17),mats['gear'],root,.025)
    sphere('Canteen',(-.24,.03,.93),(.06,.07,.10),mats['metal'],root,10,6)
    tapered('High collar',(0,0,1.48),.15,.13,.11,mats['coat'],root,.84)
    head=pivot('Head',(0,0,1.64),root)
    sphere('Head shape',(0,-.005,1.65),(.145,.135,.18),mats['skin'],head)
    sphere('Nose',(0,-.137,1.64),(.027,.028,.035),mats['skin'],head,8,6)
    for s in (-1,1):
        sphere('Eye',(.054*s,-.128,1.686),(.013,.010,.015),mats['eye'],head,8,4)
        sphere('Ear',(.143*s,-.005,1.66),(.022,.027,.044),mats['skin'],head,8,6)
    sphere('Hair',(0,.025,1.76),(.145,.13,.10),mats['hair'],head)
    if 'Technician' in key:
        sphere('Knit cap',(0,.005,1.78),(.155,.14,.09),mats['hat'],head)
        tapered('Cap folded band',(0,0,1.75),.15,.15,.045,mats['hat'],head,.9)
    else:
        sphere('Rescue cap',(0,.01,1.78),(.155,.14,.085),mats['hat'],head)
        box('Cap brim',(0,-.13,1.752),(.20,.14,.035),mats['hat'],head,.015)
    for side,sign in (('Left',-1),('Right',1)):
        arm=pivot('UpperArm_'+side,(sign*.30,0,1.39),root)
        sphere('Shoulder '+side,(sign*.30,0,1.36),(.10,.10,.13),mats['coat'],arm)
        tapered('Sleeve '+side,(sign*.32,0,1.18),.075,.09,.30,mats['coat'],arm,.92)
        tapered('Forearm '+side,(sign*.33,-.015,.98),.068,.075,.18,mats['coat'],arm,.92)
        sphere('Glove '+side,(sign*.33,-.025,.86),(.075,.065,.09),mats['gear'],arm,10,6)
        leg=pivot('UpperLeg_'+side,(sign*.125,0,.86),root)
        tapered('Thigh '+side,(sign*.125,0,.68),.11,.12,.34,mats['pants'],leg,.9)
        sphere('Knee '+side,(sign*.125,-.005,.50),(.105,.095,.105),mats['pants'],leg,10,6)
        tapered('Lower leg '+side,(sign*.125,.005,.31),.085,.10,.30,mats['pants'],leg,.95)
        tapered('Boot shaft '+side,(sign*.125,.005,.17),.095,.09,.20,mats['boots'],leg,1.0)
        box('Boot sole '+side,(sign*.125,-.05,.065),(.19,.31,.13),mats['boots'],leg,.045)
    combine_static_parts()
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(key+'.blend')))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.fbx(filepath=str(MODELS/(key+'.fbx')),use_selection=True,object_types={'EMPTY','MESH'},
        axis_forward='-Z',axis_up='Y',apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',add_leaf_bones=False,bake_anim=False)
    # A neutral, readable front three-quarter preview; preview objects are not exported.
    floor=material('Preview ground',(.22,.27,.26));box('Preview floor',(0,0,-.065),(5,5,.1),floor,root,.01)
    bpy.ops.object.camera_add(location=(2.5,-4.3,2.9));camera=bpy.context.object
    camera.rotation_euler=(Vector((0,0,.95))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=2.35;bpy.context.scene.camera=camera
    bpy.ops.object.light_add(type='AREA',location=(1.5,-3,5));bpy.context.object.data.energy=500;bpy.context.object.data.size=4
    bpy.ops.object.light_add(type='AREA',location=(-3,1,3));bpy.context.object.data.energy=250;bpy.context.object.data.size=3
    scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=800;scene.render.resolution_y=800
    scene.render.resolution_percentage=100
    if scene.world is None:scene.world=bpy.data.worlds.new('Survivor preview world')
    scene.world.color=(.13,.16,.17);scene.render.filepath=str(PREVIEWS/(key+'.png'))
    bpy.ops.render.render(write_still=True)
    print('SURVIVOR_VARIANT_COMPLETE',key,flush=True)

build('Survivor_Rescuer_v2',(.17,.31,.30),(.70,.34,.14),(.72,.53,.41),(.31,.24,.16),(.29,.25,.19))
build('Survivor_Technician_v2',(.20,.29,.35),(.55,.48,.24),(.58,.40,.30),(.40,.25,.18),(.30,.27,.21))
