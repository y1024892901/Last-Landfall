# -*- coding: utf-8 -*-
"""Last Landfall - PublicKitchen_DeepSeek, Blender 5.2+.

Creates a compact raised public kitchen with a front service hatch, real double
basin, interior prep/storage/cooking equipment, a single-pitch roof and six QA
renders. Only the two explicitly named DeepSeek collections are replaced.
"""

import bpy
import bmesh
import math
from pathlib import Path
from mathutils import Vector


ROOT = Path.cwd()
OUT_BLEND = ROOT / "Assets/LastLandfall/Art/Source/Buildings/PublicKitchen_DeepSeek.blend"
OUT_FBX = ROOT / "Assets/LastLandfall/Resources/Models/Buildings/PublicKitchen_DeepSeek.fbx"
OUT_PREVIEW = ROOT / "Assets/LastLandfall/Art/Previews/Buildings/PublicKitchen_DeepSeek.png"
OUT_VIEWS = ROOT / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"
for path in (OUT_BLEND.parent, OUT_FBX.parent, OUT_PREVIEW.parent, OUT_VIEWS):
    path.mkdir(parents=True, exist_ok=True)

MAIN_NAME = "PublicKitchen_DeepSeek"
HELPER_NAME = "Helpers_PublicKitchen_DeepSeek"
MAT_PREFIX = "PKD_"

# Remove only this asset's collections. Keep the source PublicKitchen untouched.
for collection_name in (MAIN_NAME, HELPER_NAME):
    old = bpy.data.collections.get(collection_name)
    if old:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)

for material in list(bpy.data.materials):
    if material.name.startswith(MAT_PREFIX) and material.users == 0:
        bpy.data.materials.remove(material)
for datablocks in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
    for datablock in list(datablocks):
        if datablock.users == 0 and datablock.name.startswith(("PK_", "PKD_")):
            datablocks.remove(datablock)

scene = bpy.context.scene
main = bpy.data.collections.new(MAIN_NAME)
helpers = bpy.data.collections.new(HELPER_NAME)
scene.collection.children.link(main)
scene.collection.children.link(helpers)


def material(name, color, roughness=0.75, metallic=0.0, transmission=0.0):
    mat = bpy.data.materials.get(MAT_PREFIX + name)
    if mat is None:
        mat = bpy.data.materials.new(MAT_PREFIX + name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = next((node for node in mat.node_tree.nodes
                   if node.type == 'BSDF_PRINCIPLED'), None)
    if shader:
        shader.inputs["Base Color"].default_value = (*color, 1.0)
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Metallic"].default_value = metallic
        for key in ("Transmission Weight", "Transmission"):
            if key in shader.inputs:
                shader.inputs[key].default_value = transmission
                break
    return mat


wood = material("WeatheredWood", (0.72, 0.57, 0.37), 0.84)
wood_dark = material("DarkWood", (0.30, 0.23, 0.16), 0.86)
wall = material("WarmWall", (0.79, 0.76, 0.67), 0.9)
roof = material("SeafoamMetal", (0.20, 0.40, 0.40), 0.5, 0.28)
concrete = material("Concrete", (0.48, 0.49, 0.46), 0.92)
stone = material("StepStone", (0.40, 0.43, 0.42), 0.92)
teal = material("DarkTeal", (0.055, 0.22, 0.24), 0.62)
iron = material("Iron", (0.11, 0.13, 0.14), 0.48, 0.6)
glass = material("VentGlass", (0.34, 0.56, 0.60), 0.16, 0.0, 0.55)
grille = material("VentGrille", (0.12, 0.15, 0.15), 0.62)
flame = material("StoveTop", (0.20, 0.22, 0.21), 0.5, 0.5)


def mesh_object(name, vertices, faces, mat, collection=main):
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in vertices]
    for face in faces:
        try:
            bm.faces.new([bm_verts[i] for i in face])
        except ValueError:
            pass
    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    if mat:
        obj.data.materials.append(mat)
    collection.objects.link(obj)
    return obj


def box(name, x0, x1, y0, y1, z0, z1, mat, collection=main):
    if x1 <= x0 or y1 <= y0 or z1 <= z0:
        raise ValueError(f"Invalid box dimensions: {name}")
    vertices = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return mesh_object(name, vertices, faces, mat, collection)


def sloped_box(name, x0, x1, y0, y1, z_front, z_back, thickness, mat):
    vertices = [
        (x0, y0, z_front), (x1, y0, z_front), (x1, y1, z_back), (x0, y1, z_back),
        (x0, y0, z_front + thickness), (x1, y0, z_front + thickness),
        (x1, y1, z_back + thickness), (x0, y1, z_back + thickness),
    ]
    faces = [(0,1,2,3),(4,7,6,5),(0,4,5,1),
             (1,5,6,2),(2,6,7,3),(3,7,4,0)]
    return mesh_object(name, vertices, faces, mat)


def beam(name, start, end, width, mat):
    a, b = Vector(start), Vector(end)
    axis = b - a
    if axis.length < 1e-6:
        return None
    direction = axis.normalized()
    ref = Vector((0, 0, 1)) if abs(direction.z) < 0.98 else Vector((0, 1, 0))
    u = direction.cross(ref).normalized() * (width / 2)
    v = direction.cross(u).normalized() * (width / 2)
    verts = [a-u-v, a+u-v, a+u+v, a-u+v, b-u-v, b+u-v, b+u+v, b-u+v]
    faces = [(0,1,2,3), (4,7,6,5), (0,4,5,1), (1,5,6,2), (2,6,7,3), (3,7,4,0)]
    return mesh_object(name, verts, faces, mat)


def cylinder(name, radius, depth, location, rotation, mat, segments=12):
    mesh = bpy.data.meshes.new(name + "Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments,
                          radius1=radius, radius2=radius, depth=depth)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    main.objects.link(obj)
    return obj


# Coordinates: front=-Y, rear=+Y, left=-X, right=+X.
X0, X1 = -1.40, 1.40
Y0, Y1 = -0.90, 1.10
FLOOR = 0.35
FRONT_EAVE, REAR_EAVE = 2.40, 2.80
DOOR_X0, DOOR_X1, DOOR_TOP = -1.06, -0.24, 2.04
WIN_X0, WIN_X1, WIN_Z0, WIN_Z1 = 0.14, 1.15, 1.06, 1.88

# Raised concrete pads, timber legs, perimeter beams and cross bracing.
supports = [(-1.2,-0.75), (0,-0.75), (1.2,-0.75), (-1.2,0.95), (0,0.95), (1.2,0.95)]
for i, (x, y) in enumerate(supports):
    box(f"PK_Pad_{i}", x-.125,x+.125,y-.125,y+.125,0,.15,concrete)
    box(f"PK_Leg_{i}", x-.05,x+.05,y-.05,y+.05,.15,.30,wood_dark)
box("PK_Beam_Front", -1.25,1.25,-.78,-.72,.25,.30,wood)
box("PK_Beam_Rear", -1.25,1.25,.92,.98,.25,.30,wood)
box("PK_Beam_Left", -1.22,-1.18,-.75,.95,.25,.30,wood)
box("PK_Beam_Right", 1.18,1.22,-.75,.95,.25,.30,wood)
box("PK_Floor", X0,X1,Y0,Y1,.30,FLOOR,wood)
for side, y in (("Front",-.75),("Rear",.95)):
    beam(f"PK_XBrace_{side}_A",(-1.2,y,.15),(1.2,y,.30),.045,wood_dark)
    beam(f"PK_XBrace_{side}_B",(-1.2,y,.30),(1.2,y,.15),.045,wood_dark)

# Front wall is split around the door and service hatch; all openings are real.
fy0, fy1 = Y0, Y0 + .10
box("PK_FrontWall_A",X0,DOOR_X0,fy0,fy1,FLOOR,FRONT_EAVE,wall)
box("PK_FrontWall_B",DOOR_X0,DOOR_X1,fy0,fy1,DOOR_TOP,FRONT_EAVE,wall)
box("PK_FrontWall_C",DOOR_X1,WIN_X0,fy0,fy1,FLOOR,FRONT_EAVE,wall)
box("PK_FrontWall_D",WIN_X0,WIN_X1,fy0,fy1,FLOOR,WIN_Z0,wall)
box("PK_FrontWall_E",WIN_X0,WIN_X1,fy0,fy1,WIN_Z1,FRONT_EAVE,wall)
box("PK_FrontWall_F",WIN_X1,X1,fy0,fy1,FLOOR,FRONT_EAVE,wall)

# Rear wall and high service grille.
by0, by1 = Y1-.10, Y1
box("PK_RearWall",X0,X1,by0,by1,FLOOR,REAR_EAVE,wall)
box("PK_RearVentBacking",-.58,.58,by1,by1+.025,2.32,2.62,grille)
for i in range(7):
    x = -.51 + i*.17
    box(f"PK_RearVentSlat_{i}",x,x+.035,by1+.03,by1+.045,2.33,2.61,iron)
box("PK_ServicePanel",.62,1.08,by1,by1+.025,.78,1.48,teal)

# Side walls rise with the single-pitch roof and each has a high vent window.
for side, xa, xb, wy0, wy1 in (
    ("Left",X0,X0+.10,.32,.72), ("Right",X1-.10,X1,-.50,-.10)):
    wz0, wz1 = 1.68, 2.08
    box(f"PK_{side}Wall_Lower",xa,xb,Y0,Y1,FLOOR,wz0,wall)
    box(f"PK_{side}Wall_Front",xa,xb,Y0,wy0,wz0,wz1,wall)
    box(f"PK_{side}Wall_Rear",xa,xb,wy1,Y1,wz0,wz1,wall)
    vertices = [(xa,Y0,wz1),(xb,Y0,wz1),(xb,Y1,wz1),(xa,Y1,wz1),
                (xa,Y0,FRONT_EAVE),(xb,Y0,FRONT_EAVE),
                (xb,Y1,REAR_EAVE),(xa,Y1,REAR_EAVE)]
    faces = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    mesh_object(f"PK_{side}Wall_Sloping",vertices,faces,wall)
    box(f"PK_{side}VentGlass",xa+.02,xb-.02,wy0,wy1,wz0,wz1,glass)
    for i in range(4):
        z = wz0+.06+i*.09
        beam(f"PK_{side}VentBar_{i}",(xa-.01,wy0,z),(xb+.01,wy0,z),.018,iron)

# Single-pitch roof: flat horizontal edge at the front, higher at the rear.
sloped_box("PK_Roof",-1.45,1.45,-.95,1.15,2.40,2.80,.10,roof)
box("PK_FrontFascia",-1.45,1.45,-.96,-.88,2.30,2.40,wood)
box("PK_RearFascia",-1.45,1.45,1.08,1.16,2.70,2.80,wood)

# Door, frame and handle.
box("PK_Door",DOOR_X0+.025,DOOR_X1-.025,fy0-.018,fy0+.015,.37,DOOR_TOP-.02,wood_dark)
box("PK_DoorFrame_L",DOOR_X0,DOOR_X0+.05,fy0-.03,fy1,FLOOR,DOOR_TOP,wood)
box("PK_DoorFrame_R",DOOR_X1-.05,DOOR_X1,fy0-.03,fy1,FLOOR,DOOR_TOP,wood)
box("PK_DoorFrame_T",DOOR_X0,DOOR_X1,fy0-.03,fy1,DOOR_TOP-.05,DOOR_TOP,wood)
cylinder("PK_DoorHandle",.026,.055,(-.34,fy0-.05,1.13),(math.pi/2,0,0),iron,8)

# Continuous two-rise entry stair meets both grade and the floor edge.
box("PK_EntryStep_Lower",-1.15,-.15,-1.20,-1.00,0,.175,stone)
box("PK_EntryStep_Upper",-1.15,-.15,-1.00,-.90,.175,FLOOR,stone)

# Serving ledge and a supported rain canopy below the level front eave.
box("PK_ServiceCounter",.10,1.20,-1.20,-.90,.96,1.04,wood)
beam("PK_CounterBrace_Left",(.16,-.88,.68),(.16,-1.16,.96),.055,wood_dark)
beam("PK_CounterBrace_Right",(1.14,-.88,.68),(1.14,-1.16,.96),.055,wood_dark)
canopy = [(-.05,-.90,2.00),(1.30,-.90,2.00),(1.30,-1.22,1.87),(-.05,-1.22,1.87),
          (-.05,-.90,2.05),(1.30,-.90,2.05),(1.30,-1.22,1.92),(-.05,-1.22,1.92)]
mesh_object("PK_ServiceCanopy",canopy,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],roof)
beam("PK_CanopyBrace_Left",(-.02,-.88,1.63),(-.02,-1.20,1.87),.045,wood_dark)
beam("PK_CanopyBrace_Right",(1.27,-.88,1.63),(1.27,-1.20,1.87),.045,wood_dark)
box("PK_HatchSill",.14,1.15,-.92,-.86,1.00,1.08,wood_dark)

# Two fixed stools with full-height legs that contact grade.
for i, sx in enumerate((.30,.70)):
    box(f"PK_StoolSeat_{i}",sx,sx+.25,-1.42,-1.20,.59,.65,wood)
    for a, lx in enumerate((sx+.03,sx+.22)):
        for b, ly in enumerate((-1.39,-1.23)):
            box(f"PK_StoolLeg_{i}_{a}_{b}",lx-.02,lx+.02,ly-.02,ly+.02,0,.59,wood_dark)

# Interior prep table. The top is built around two genuine open sink cutouts.
box("PK_PrepSlabBase",.20,1.10,.15,.50,.92,.96,wood_dark)
for name, xa, xb in (("Sink1",.25,.50),("Sink2",.55,.80)):
    # Basin floor and four metal walls descend through the counter opening.
    box(f"PK_{name}_BasinFloor",xa+.015,xb-.015,.215,.405,.84,.875,teal)
    box(f"PK_{name}_BasinFront",xa+.015,xb-.015,.20,.22,.865,.955,teal)
    box(f"PK_{name}_BasinBack",xa+.015,xb-.015,.40,.42,.865,.955,teal)
    box(f"PK_{name}_BasinLeft",xa,xa+.02,.22,.40,.865,.955,teal)
    box(f"PK_{name}_BasinRight",xb-.02,xb,.22,.40,.865,.955,teal)
# Top perimeter and center divider leave both openings clear.
box("PK_PrepTop_Front",.20,1.10,.15,.20,.96,1.03,wood)
box("PK_PrepTop_Back",.20,1.10,.42,.50,.96,1.03,wood)
box("PK_PrepTop_Left",.20,.25,.20,.42,.96,1.03,wood)
box("PK_PrepTop_Divider",.50,.55,.20,.42,.96,1.03,wood)
box("PK_PrepTop_Right",.80,1.10,.20,.42,.96,1.03,wood)
for i, (x,y) in enumerate(((.24,.19),(1.06,.19),(.24,.46),(1.06,.46))):
    box(f"PK_PrepLeg_{i}",x-.03,x+.03,y-.03,y+.03,FLOOR,.92,wood_dark)
# Simple faucets and tap handles at the rear lip of both basins.
for i, x in enumerate((.375,.675)):
    cylinder(f"PK_FaucetStem_{i}",.018,.20,(x,.445,1.10),(0,0,0),iron,8)
    beam(f"PK_FaucetSpout_{i}",(x,.445,1.19),(x,.34,1.19),.035,iron)

# Rear food shelves and compact pantry cabinet.
for i, (x,y) in enumerate(((-1.15,.74),(-.48,.74),(-1.15,.97),(-.48,.97))):
    box(f"PK_ShelfPost_{i}",x-.025,x+.025,y-.025,y+.025,FLOOR,1.93,wood_dark)
for i, z in enumerate((.91,1.31,1.71)):
    box(f"PK_ShelfBoard_{i}",-1.18,-.45,.71,1.00,z-.025,z+.025,wood)
box("PK_FoodCabinet",-1.28,-.93,.28,.64,FLOOR,1.10,teal)
box("PK_FoodCabinetDoor",-1.27,-1.25,.32,.60,.55,.57,wood_dark)
for i, (x,y,z) in enumerate(((-1.05,.78,.935),(-.75,.82,.935),(-1.02,.84,1.335),(-.72,.80,1.735))):
    box(f"PK_ProvisionCrate_{i}",x-.09,x+.09,y-.08,y+.08,z,z+.16,wood_dark)

# Small wood stove, cooking surface, door, feet and connected flue.
box("PK_StoveBody",.55,1.15,.55,.95,FLOOR,1.10,teal)
box("PK_StoveDoor",.61,1.09,.525,.56,.52,.88,iron)
box("PK_StoveDoorGlass",.70,1.00,.515,.53,.60,.80,glass)
box("PK_StoveTop",.52,1.18,.52,.98,1.10,1.16,flame)
for i, (x,y) in enumerate(((.68,.67),(.96,.67),(.68,.87),(.96,.87))):
    cylinder(f"PK_Burner_{i}",.075,.025,(x,y,1.18),(0,0,0),iron,12)
for i, (x,y) in enumerate(((.60,.60),(1.10,.60),(.60,.90),(1.10,.90))):
    box(f"PK_StoveFoot_{i}",x-.03,x+.03,y-.03,y+.03,.30,FLOOR,iron)
box("PK_StoveFlue",.82,.96,.66,.80,1.14,2.94,iron)
box("PK_FlueRoofCollar",.76,1.02,.60,.86,2.68,2.76,roof)
box("PK_FlueCap",.78,1.00,.62,.84,2.94,3.00,iron)

# Visible left-side plumbing is bracketed to the wall and terminates at grade.
cylinder("PK_SideDrainPipe",.028,2.075,(-1.435,.08,1.2175),(0,0,0),iron,10)
cylinder("PK_DrainElbow",.028,.16,(-1.35,.08,.18),(0,math.pi/2,0),iron,10)
for i, z in enumerate((.52,1.20,1.88)):
    box(f"PK_PipeBracket_{i}",-1.46,-1.36,.035,.125,z-.035,z+.035,iron)


def camera(name, location, target, scale, collection=helpers):
    data = bpy.data.cameras.new(name)
    data.type = 'ORTHO'
    data.ortho_scale = scale
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target)-Vector(location)).to_track_quat('-Z','Y').to_euler()
    return obj


target = (0,0,1.48)
distance = 10
ortho = 4.20
cameras = {
    "Front": camera("PK_Camera_Front",(0,-distance,1.48),target,ortho),
    "Back": camera("PK_Camera_Back",(0,distance,1.48),target,ortho),
    "Left": camera("PK_Camera_Left",(-distance,0,1.48),target,ortho),
    "Right": camera("PK_Camera_Right",(distance,0,1.48),target,ortho),
}
top_data = bpy.data.cameras.new("PK_Camera_Top")
top_data.type = 'ORTHO'
top_data.ortho_scale = ortho
top = bpy.data.objects.new("PK_Camera_Top",top_data)
helpers.objects.link(top)
top.location = (0,0,distance)
top.rotation_euler = (0,0,0)
cameras["Top"] = top
bottom_data = bpy.data.cameras.new("PK_Camera_Bottom")
bottom_data.type = 'ORTHO'
bottom_data.ortho_scale = ortho
bottom = bpy.data.objects.new("PK_Camera_Bottom",bottom_data)
helpers.objects.link(bottom)
bottom.location = (0,0,-distance)
bottom.rotation_euler = (math.pi,0,0)
cameras["Bottom"] = bottom
preview_cam = camera("PK_Camera_Preview",(6,-7,5.1),(0,0,1.4),5.1)

# Use dedicated helper lights; render setup never adds them to the export set.
world = bpy.data.worlds.get("PKD_World") or bpy.data.worlds.new("PKD_World")
world.use_nodes = True
world_nodes = world.node_tree.nodes
background = next((node for node in world_nodes if node.type == 'BACKGROUND'), None)
world_output = next((node for node in world_nodes if node.type == 'OUTPUT_WORLD'), None)
background = background or world_nodes.new("ShaderNodeBackground")
world_output = world_output or world_nodes.new("ShaderNodeOutputWorld")
if not world_output.inputs["Surface"].is_linked:
    world.node_tree.links.new(background.outputs["Background"], world_output.inputs["Surface"])
background.inputs["Color"].default_value = (.68,.73,.79,1)
background.inputs["Strength"].default_value = .65
scene.world = world
sun_data = bpy.data.lights.new("PKD_Sun",'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("PKD_Sun",sun_data)
helpers.objects.link(sun)
sun.rotation_euler = (math.radians(48),math.radians(18),math.radians(32))
fill_data = bpy.data.lights.new("PKD_Fill",'AREA')
fill_data.energy = 240
fill_data.size = 6
fill = bpy.data.objects.new("PKD_Fill",fill_data)
helpers.objects.link(fill)
fill.location = (-4,-4,5)
fill.rotation_euler = (math.radians(38),0,math.radians(-35))

# Render all six orthographic QA views and one isometric preview.
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
for view_name, cam in cameras.items():
    scene.camera = cam
    scene.render.filepath = str(OUT_VIEWS / f"PublicKitchen_DeepSeek_{view_name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {view_name}: {scene.render.filepath}")
scene.camera = preview_cam
scene.render.filepath = str(OUT_PREVIEW)
bpy.ops.render.render(write_still=True)
print(f"Rendered preview: {OUT_PREVIEW}")

# Export only model meshes, then preserve the full editable scene in the Blend.
bpy.ops.object.select_all(action='DESELECT')
mesh_objects = [obj for obj in main.objects if obj.type == 'MESH']
for obj in mesh_objects:
    obj.select_set(True)
if mesh_objects:
    bpy.context.view_layer.objects.active = mesh_objects[0]
bpy.ops.export_scene.fbx(
    filepath=str(OUT_FBX), use_selection=True, object_types={'MESH'},
    use_mesh_modifiers=True, apply_scale_options='FBX_SCALE_ALL')
print(f"Exported FBX: {OUT_FBX}")
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
print(f"Saved Blend: {OUT_BLEND}")

# World-space bounds and per-object mesh checks; intersections between separate
# objects are intentionally not inferred by this manifold diagnostic.
corners = []
for obj in mesh_objects:
    corners.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
mins = [min(v[i] for v in corners) for i in range(3)]
maxs = [max(v[i] for v in corners) for i in range(3)]
print("\nPublicKitchen_DeepSeek QA")
print(f"Meshes: {len(mesh_objects)}")
print(f"Bounds X/Y/Z: {mins} to {maxs}; size {[maxs[i]-mins[i] for i in range(3)]}")
print(f"Lowest Z: {mins[2]:.4f} m")
nonmanifold = loose = affected = 0
for obj in mesh_objects:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    nm = sum(not edge.is_manifold for edge in bm.edges)
    lv = sum(not vert.link_edges for vert in bm.verts)
    le = sum(not edge.link_faces for edge in bm.edges)
    bm.free()
    nonmanifold += nm
    loose += lv + le
    if nm or lv or le:
        affected += 1
        print(f"  {obj.name}: nonmanifold={nm}, looseVerts={lv}, looseEdges={le}")
print(f"Nonmanifold edges: {nonmanifold}; loose items: {loose}; affected meshes: {affected}")
print("This per-object check cannot detect intersections/overlaps between separate mesh objects.")
