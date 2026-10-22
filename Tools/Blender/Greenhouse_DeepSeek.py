import bpy
import bmesh
import math
from mathutils import Vector
from pathlib import Path


# Greenhouse_DeepSeek — reviewed and refined from the DeepSeek draft.
PROJECT_ROOT = Path.cwd()
BLEND_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Buildings"
FBX_DIR = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Buildings"
PREVIEW_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Previews/Buildings"
QA_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"
for output_dir in (BLEND_DIR, FBX_DIR, PREVIEW_DIR, QA_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "Greenhouse_DeepSeek"
HELPER_NAME = "Helpers_Greenhouse_DeepSeek"
scene = bpy.context.scene


def replace_owned_collection(name):
    old = bpy.data.collections.get(name)
    if old is None:
        return
    for child in list(old.children):
        old.children.unlink(child)
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)


replace_owned_collection(MODEL_NAME)
replace_owned_collection(HELPER_NAME)
model_col = bpy.data.collections.new(MODEL_NAME)
helper_col = bpy.data.collections.new(HELPER_NAME)
scene.collection.children.link(model_col)
scene.collection.children.link(helper_col)


def material(name, color, roughness=0.8, metallic=0.0, alpha=1.0,
             transmission=0.0):
    full_name = f"{MODEL_NAME}_{name}"
    mat = bpy.data.materials.get(full_name)
    if mat is None:
        mat = bpy.data.materials.new(full_name)
    mat.diffuse_color = color
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = next((node for node in nodes
                 if node.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    output = next((node for node in nodes
                   if node.bl_idname == "ShaderNodeOutputMaterial"), None)
    if output is None:
        output = nodes.new("ShaderNodeOutputMaterial")
    if not any(link.from_node == bsdf and link.to_node == output
               for link in mat.node_tree.links):
        mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Alpha"].default_value = alpha
    trans_socket = bsdf.inputs.get("Transmission Weight") or bsdf.inputs.get("Transmission")
    if trans_socket:
        trans_socket.default_value = transmission
    if alpha < 1.0:
        mat.surface_render_method = "BLENDED"
        mat.show_transparent_back = True
    else:
        mat.surface_render_method = "DITHERED"
    return mat


MAT_WOOD = material("LightTimber", (0.63, 0.43, 0.24, 1.0), 0.84)
MAT_WOOD_LIGHT = material("PaleTimber", (0.82, 0.66, 0.43, 1.0), 0.86)
MAT_WOOD_DARK = material("KickPanelTimber", (0.34, 0.22, 0.13, 1.0), 0.9)
MAT_METAL = material("SeafoamMetal", (0.24, 0.58, 0.56, 1.0), 0.42, 0.36)
MAT_METAL_DARK = material("DarkMetal", (0.12, 0.25, 0.25, 1.0), 0.48, 0.46)
MAT_CONCRETE = material("Concrete", (0.47, 0.48, 0.44, 1.0), 0.93)
MAT_GLASS = material("AquaGlazing", (0.55, 0.84, 0.88, 0.18), 0.22, 0.02, 0.18, 0.04)
MAT_SOIL = material("RichSoil", (0.20, 0.12, 0.065, 1.0), 1.0)
MAT_PLANT = material("SeedlingGreen", (0.22, 0.58, 0.16, 1.0), 0.72)
MAT_PLANT_LIGHT = material("LeafLight", (0.43, 0.73, 0.25, 1.0), 0.73)
MAT_PIPE = material("IrrigationPipe", (0.19, 0.29, 0.28, 1.0), 0.45, 0.42)
MAT_CONTROL = material("ControlCabinet", (0.12, 0.34, 0.31, 1.0), 0.57, 0.28)
MAT_LAMP = material("StatusLamp", (0.42, 0.88, 0.57, 1.0), 0.3, 0.1)


def move_to_collection(obj, collection):
    for linked in list(obj.users_collection):
        linked.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def add_box(name, size, location, mat, collection=model_col,
            rotation=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    move_to_collection(obj, collection)
    if bevel > 0.0:
        modifier = obj.modifiers.new("Small edge chamfers", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def add_cylinder(name, radius, depth, location, mat, collection=model_col,
                 rotation=(0, 0, 0), vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=depth, location=location,
                                        rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    return move_to_collection(obj, collection)


def add_beam(name, start, end, section, mat, collection=model_col):
    a, b = Vector(start), Vector(end)
    delta = b - a
    if delta.length < 0.001:
        return None
    rotation = delta.to_track_quat("Z", "Y").to_euler()
    return add_box(name, (section[0], section[1], delta.length),
                   (a + b) / 2, mat, collection, rotation)


def add_pipe(name, start, end, radius, mat, collection=model_col, vertices=8):
    a, b = Vector(start), Vector(end)
    delta = b - a
    if delta.length < 0.001:
        return None
    obj = add_cylinder(name, radius, delta.length, (a + b) / 2, mat,
                       collection, vertices=vertices)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return obj


def add_prism(name, vertices, normal, thickness, mat):
    """Make a closed thin polygon prism for the sloped glazing panels."""
    normal = Vector(normal).normalized() * (thickness / 2)
    front = [Vector(v) - normal for v in vertices]
    back = [Vector(v) + normal for v in vertices]
    points = front + back
    n = len(vertices)
    faces = [tuple(range(n)), tuple(range(n, 2 * n))[::-1]]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(points, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    model_col.objects.link(obj)
    return obj


def add_leaf(name, location, scale, rotation_z, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=6, ring_count=4, radius=1,
                                         location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler[2] = rotation_z
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    return move_to_collection(obj, model_col)


# -----------------------------------------------------------------------------
# Raised, transportable frame. Ground is Z=0; front/access is -Y. The roof is
# a single plane rising from the low front edge toward the back (+Y).
# -----------------------------------------------------------------------------
HALF_W = 1.9
FRONT_Y, BACK_Y = -1.65, 1.65
ROOF_FRONT_Z, ROOF_BACK_Z = 2.32, 3.14
FLOOR_TOP = 0.60
KICK_TOP = 0.98
ROOF_ANGLE = math.atan2(ROOF_BACK_Z - ROOF_FRONT_Z, BACK_Y - FRONT_Y)
ROOF_LENGTH = math.hypot(BACK_Y - FRONT_Y, ROOF_BACK_Z - ROOF_FRONT_Z)
ROOF_CENTER = (0.0, (FRONT_Y + BACK_Y) / 2,
               (ROOF_FRONT_Z + ROOF_BACK_Z) / 2)

# Concrete pads, timber feet and two perimeter bearers.
for row, y in enumerate((-1.42, 0.0, 1.42)):
    for col, x in enumerate((-1.62, 0.0, 1.62)):
        add_box(f"Foundation_Pad_{row}_{col}", (0.38, 0.38, 0.20),
                (x, y, 0.10), MAT_CONCRETE, bevel=0.025)
        add_box(f"Foundation_ShortPost_{row}_{col}", (0.16, 0.16, 0.12),
                (x, y, 0.26), MAT_WOOD)
for side, x in (("L", -1.62), ("R", 1.62)):
    add_box(f"Foundation_Bearer_{side}", (0.18, 3.12, 0.18),
            (x, 0.0, 0.35), MAT_WOOD)
for i, y in enumerate((-1.42, -0.71, 0.0, 0.71, 1.42)):
    add_box(f"Foundation_Joist_{i:02d}", (3.30, 0.13, 0.12),
            (0.0, y, 0.43), MAT_WOOD_LIGHT)
for side, x in (("L", -1.62), ("R", 1.62)):
    add_beam(f"Foundation_CrossBrace_{side}_A", (x, -1.30, 0.10),
             (x, 1.30, 0.48), (0.09, 0.10), MAT_WOOD)
    add_beam(f"Foundation_CrossBrace_{side}_B", (x, 1.30, 0.10),
             (x, -1.30, 0.48), (0.09, 0.10), MAT_WOOD)
# X bracing under the floor plane; the pair sits below joists and above pads.
add_beam("Foundation_Underside_XBrace_A", (-1.42, -1.18, 0.255),
         (1.42, 1.18, 0.255), (0.09, 0.075), MAT_WOOD)
add_beam("Foundation_Underside_XBrace_B", (-1.42, 1.18, 0.255),
         (1.42, -1.18, 0.255), (0.09, 0.075), MAT_WOOD)
for i in range(17):
    y = -1.55 + i * 0.19
    add_box(f"Floor_Deck_Plank_{i:02d}", (3.68, 0.17, 0.09),
            (0.0, y, 0.555), MAT_WOOD_LIGHT)

# Side and end kick panels. The front leaves a real doorway opening.
for side, x in (("L", -HALF_W), ("R", HALF_W)):
    add_box(f"KickPanel_Side_{side}", (0.10, 3.18, KICK_TOP - FLOOR_TOP),
            (x, 0.0, (KICK_TOP + FLOOR_TOP) / 2), MAT_WOOD_DARK)
add_box("KickPanel_Back", (3.80, 0.10, KICK_TOP - FLOOR_TOP),
        (0, BACK_Y, (KICK_TOP + FLOOR_TOP) / 2), MAT_WOOD_DARK)
for side, x in (("L", -1.35), ("R", 1.35)):
    add_box(f"KickPanel_Front_{side}", (1.10, 0.10, KICK_TOP - FLOOR_TOP),
            (x, FRONT_Y, (KICK_TOP + FLOOR_TOP) / 2), MAT_WOOD_DARK)

# Main timber and seafoam frame.
for label, x in (("L", -HALF_W), ("R", HALF_W)):
    for end, y, roof_z in (("Front", FRONT_Y, ROOF_FRONT_Z),
                           ("Back", BACK_Y, ROOF_BACK_Z)):
        add_box(f"Frame_CornerPost_{label}_{end}", (0.14, 0.14, roof_z - KICK_TOP),
                (x, y, (roof_z + KICK_TOP) / 2), MAT_WOOD_LIGHT)
for label, y in (("Front", FRONT_Y), ("Back", BACK_Y)):
    z = ROOF_FRONT_Z if label == "Front" else ROOF_BACK_Z
    add_box(f"Frame_EndHeader_{label}", (3.82, 0.12, 0.12),
            (0, y, z - 0.02), MAT_METAL)

# Side glazing bays are trapezoids, matching the single pitch without gable ends.
for side, x in (("L", -HALF_W), ("R", HALF_W)):
    normal = (1, 0, 0) if side == "L" else (1, 0, 0)
    for index, (y0, y1) in enumerate(((-1.55, -0.05), (0.05, 1.55))):
        z0 = ROOF_FRONT_Z + (y0 - FRONT_Y) / (BACK_Y - FRONT_Y) * (ROOF_BACK_Z - ROOF_FRONT_Z)
        z1 = ROOF_FRONT_Z + (y1 - FRONT_Y) / (BACK_Y - FRONT_Y) * (ROOF_BACK_Z - ROOF_FRONT_Z)
        add_prism(f"Glazing_Side_{side}_{index}",
                  [(x, y0, KICK_TOP + 0.02), (x, y1, KICK_TOP + 0.02),
                   (x, y1, z1 - 0.08), (x, y0, z0 - 0.08)],
                  normal, 0.025, MAT_GLASS)
    for index, y in enumerate((-0.05, 1.55)):
        z = ROOF_FRONT_Z + (y - FRONT_Y) / (BACK_Y - FRONT_Y) * (ROOF_BACK_Z - ROOF_FRONT_Z)
        add_box(f"Frame_SideStud_{side}_{index}", (0.09, 0.10, z - KICK_TOP),
                (x, y, (z + KICK_TOP) / 2), MAT_WOOD_LIGHT)
    # A mid-height continuous rail keeps the large panes visually supported.
    add_box(f"Frame_SideMidRail_{side}", (0.10, 3.16, 0.09),
            (x, 0.0, 1.57), MAT_WOOD)
    add_beam(f"Frame_SideRoofRail_{side}", (x, FRONT_Y, ROOF_FRONT_Z - 0.04),
             (x, BACK_Y, ROOF_BACK_Z - 0.04), (0.10, 0.11), MAT_METAL)

# Front wall windows and door opening. The front roof edge is horizontal.
front_glass_z0 = KICK_TOP + 0.02
front_glass_z1 = ROOF_FRONT_Z - 0.08
for side, x_center in (("L", -1.25), ("R", 1.25)):
    x0, x1 = ((-1.82, -0.62) if side == "L" else (0.62, 1.82))
    add_prism(f"Glazing_Front_{side}",
              [(x0, FRONT_Y, front_glass_z0), (x1, FRONT_Y, front_glass_z0),
               (x1, FRONT_Y, front_glass_z1), (x0, FRONT_Y, front_glass_z1)],
              (0, 1, 0), 0.025, MAT_GLASS)
    add_box(f"Frame_Front_Mullion_{side}", (0.08, 0.10, front_glass_z1 - front_glass_z0),
            (x_center, FRONT_Y, (front_glass_z0 + front_glass_z1) / 2), MAT_WOOD_LIGHT)

DOOR_W, DOOR_H, DOOR_BOTTOM = 0.92, 1.47, FLOOR_TOP + 0.03
DOOR_TOP = DOOR_BOTTOM + DOOR_H
for side, x in (("L", -DOOR_W / 2 - 0.07), ("R", DOOR_W / 2 + 0.07)):
    add_box(f"Door_Frame_Jamb_{side}", (0.10, 0.14, DOOR_H + 0.12),
            (x, FRONT_Y - 0.035, DOOR_BOTTOM + DOOR_H / 2), MAT_WOOD)
add_box("Door_Frame_Lintel", (DOOR_W + 0.24, 0.14, 0.12),
        (0, FRONT_Y - 0.035, DOOR_TOP + 0.06), MAT_WOOD)
add_box("Door_Leaf", (DOOR_W, 0.07, DOOR_H),
        (0, FRONT_Y - 0.075, DOOR_BOTTOM + DOOR_H / 2), MAT_METAL_DARK, bevel=0.025)
add_box("Door_Glass_Lite", (0.62, 0.018, 0.65),
        (0, FRONT_Y - 0.117, DOOR_BOTTOM + 0.94), MAT_GLASS)
add_box("Door_Lower_Panel", (0.62, 0.02, 0.30),
        (0, FRONT_Y - 0.12, DOOR_BOTTOM + 0.22), MAT_METAL)
add_box("Door_Handle", (0.045, 0.065, 0.16),
        (0.32, FRONT_Y - 0.13, DOOR_BOTTOM + 0.75), MAT_WOOD_LIGHT, bevel=0.012)

# Back glazing divided by simple vertical mullions.
for index, (x0, x1) in enumerate(((-1.82, -0.97), (-0.93, -0.04),
                                  (0.04, 0.93), (0.97, 1.82))):
    add_prism(f"Glazing_Back_{index}",
              [(x0, BACK_Y, KICK_TOP + 0.02), (x1, BACK_Y, KICK_TOP + 0.02),
               (x1, BACK_Y, ROOF_BACK_Z - 0.08), (x0, BACK_Y, ROOF_BACK_Z - 0.08)],
              (0, -1, 0), 0.025, MAT_GLASS)
for index, x in enumerate((-0.95, 0.0, 0.95)):
    add_box(f"Frame_Back_Mullion_{index}", (0.09, 0.10, ROOF_BACK_Z - KICK_TOP),
            (x, BACK_Y, (ROOF_BACK_Z + KICK_TOP) / 2), MAT_WOOD_LIGHT)

# Single-slope transparent roof, timber rafters, edge flashing and high vent.
add_box("Roof_Glazing", (3.94, ROOF_LENGTH, 0.055), ROOF_CENTER,
        MAT_GLASS, rotation=(ROOF_ANGLE, 0, 0))
for index, x in enumerate((-1.82, -0.91, 0.0, 0.91, 1.82)):
    add_box(f"Roof_Rafter_{index}", (0.09, ROOF_LENGTH + 0.04, 0.13),
            (x, ROOF_CENTER[1], ROOF_CENTER[2] + 0.035), MAT_WOOD_LIGHT,
            rotation=(ROOF_ANGLE, 0, 0))
add_box("Roof_Edge_LowFront", (3.96, 0.14, 0.12),
        (0, FRONT_Y, ROOF_FRONT_Z - 0.02), MAT_METAL)
add_box("Roof_Edge_HighBack", (3.96, 0.14, 0.12),
        (0, BACK_Y, ROOF_BACK_Z - 0.02), MAT_WOOD_LIGHT)
for side, x in (("L", -HALF_W), ("R", HALF_W)):
    add_beam(f"Roof_Edge_Side_{side}", (x, FRONT_Y, ROOF_FRONT_Z),
             (x, BACK_Y, ROOF_BACK_Z), (0.08, 0.10), MAT_METAL)
add_box("Roof_HighVent_Housing", (1.55, 0.36, 0.13),
        (0.12, BACK_Y - 0.16, ROOF_BACK_Z + 0.08), MAT_METAL)
for i in range(6):
    x = -0.48 + i * 0.24
    add_box(f"Roof_HighVent_Louver_{i:02d}", (0.13, 0.29, 0.075),
            (x, BACK_Y - 0.15, ROOF_BACK_Z + 0.18), MAT_WOOD_LIGHT,
            rotation=(math.radians(24), 0, 0))

# Two raised growing beds, seedlings, drip rails and compact utility equipment.
for side, x in (("L", -1.03), ("R", 1.03)):
    add_box(f"PlantBed_{side}_Body", (1.18, 2.48, 0.30),
            (x, 0.05, 0.78), MAT_WOOD_DARK, bevel=0.035)
    add_box(f"PlantBed_{side}_Soil", (1.08, 2.36, 0.085),
            (x, 0.05, 0.97), MAT_SOIL)
    for row, y in enumerate((-0.84, -0.19, 0.46, 1.00)):
        for col, dx in enumerate((-0.27, 0.27)):
            px, py, pz = x + dx, y, 1.02
            add_cylinder(f"Seedling_{side}_{row}_{col}_Stem", 0.018, 0.15,
                         (px, py, pz + 0.075), MAT_PLANT, vertices=6)
            for leaf_index, angle in enumerate((0.0, 2.1, 4.2)):
                leaf_x = px + math.cos(angle) * 0.055
                leaf_y = py + math.sin(angle) * 0.055
                add_leaf(f"Seedling_{side}_{row}_{col}_Leaf_{leaf_index}",
                         (leaf_x, leaf_y, pz + 0.12), (0.075, 0.036, 0.018),
                         angle, MAT_PLANT if leaf_index else MAT_PLANT_LIGHT)
    add_pipe_start = (-1.03 if side == "L" else 1.03)
    add_beam(f"DripLine_{side}", (add_pipe_start, -1.05, 1.28),
             (add_pipe_start, 1.15, 1.28), (0.035, 0.035), MAT_PIPE)
    for support_index, y in enumerate((-1.05, 1.15)):
        add_cylinder(f"DripLine_{side}_Support_{support_index}", 0.018, 0.28,
                     (add_pipe_start, y, 1.14), MAT_PIPE, vertices=8)
    for i in range(8):
        y = -0.94 + i * 0.28
        add_cylinder(f"Dripper_{side}_{i:02d}", 0.012, 0.07,
                     (add_pipe_start, y, 1.22), MAT_METAL_DARK, vertices=6)

# A side-mounted rainwater buffer tank and control cabinet; short visible pipe runs.
TANK_X, TANK_Y = 2.23, -0.88
add_box("WaterTank_Foot", (0.56, 0.56, 0.14), (TANK_X, TANK_Y, 0.10), MAT_CONCRETE)
add_cylinder("WaterTank_Body", 0.22, 1.12, (TANK_X, TANK_Y, 0.76), MAT_METAL,
             vertices=16)
add_cylinder("WaterTank_Top", 0.235, 0.08, (TANK_X, TANK_Y, 1.36), MAT_METAL_DARK,
             vertices=16)
add_cylinder("WaterTank_BaseRing", 0.235, 0.08, (TANK_X, TANK_Y, 0.18), MAT_METAL_DARK,
             vertices=16)
for index, z in enumerate((0.48, 1.02)):
    add_cylinder(f"WaterTank_Band_{index}", 0.232, 0.045,
                 (TANK_X, TANK_Y, z), MAT_WOOD_LIGHT, vertices=16)
add_box("ControlCabinet_Footing", (0.52, 0.56, 0.17),
        (2.18, -0.06, 0.085), MAT_CONCRETE, bevel=0.018)
add_box("ControlCabinet_Body", (0.42, 0.46, 0.72),
        (2.18, -0.06, 0.53), MAT_CONTROL, bevel=0.035)
add_box("ControlCabinet_Display", (0.024, 0.24, 0.23),
        (1.958, -0.06, 0.66), MAT_METAL_DARK)
add_box("ControlCabinet_StatusLamp", (0.03, 0.07, 0.07),
        (1.94, -0.06, 0.36), MAT_LAMP)
add_beam("Gutter_LowFront", (-1.85, FRONT_Y - 0.13, ROOF_FRONT_Z - 0.14),
         (1.85, FRONT_Y - 0.13, ROOF_FRONT_Z - 0.14), (0.12, 0.10), MAT_METAL)
add_beam("RainPipe_AlongRight", (1.96, FRONT_Y - 0.13, ROOF_FRONT_Z - 0.14),
         (1.96, -0.88, ROOF_FRONT_Z - 0.14), (0.055, 0.055), MAT_PIPE)
add_beam("RainPipe_Down", (1.96, -0.88, ROOF_FRONT_Z - 0.14),
         (1.96, -0.88, 0.58), (0.055, 0.055), MAT_PIPE)
add_beam("RainPipe_ToTank", (1.96, -0.88, 0.58),
         (TANK_X - 0.20, TANK_Y, 0.58), (0.05, 0.05), MAT_PIPE)
add_beam("Tank_To_Control_Inlet", (TANK_X, TANK_Y + 0.22, 0.42),
         (TANK_X, -0.27, 0.42), (0.055, 0.055), MAT_PIPE)
add_beam("Tank_Overflow", (TANK_X + 0.20, TANK_Y, 1.25),
         (TANK_X + 0.20, TANK_Y + 0.48, 1.25), (0.035, 0.035), MAT_PIPE)

# Two supported access treads connect the ground to the raised floor.
add_box("AccessStep_Lower", (1.05, 0.38, 0.28), (0, -2.05, 0.14), MAT_CONCRETE,
        bevel=0.02)
add_box("AccessStep_Upper", (1.00, 0.36, 0.28), (0, -1.80, 0.42), MAT_WOOD_LIGHT)


def report_diagnostics():
    meshes = [obj for obj in model_col.objects if obj.type == "MESH"]
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    open_edges = 0
    for obj in meshes:
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ Vector(corner)
            for axis in range(3):
                mins[axis] = min(mins[axis], world_corner[axis])
                maxs[axis] = max(maxs[axis], world_corner[axis])
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        open_edges += sum(1 for edge in bm.edges if not edge.is_manifold)
        bm.free()
    dimensions = [maxs[i] - mins[i] for i in range(3)]
    print("\n--- Greenhouse_DeepSeek Diagnostics ---")
    print(f"Mesh Object Count: {len(meshes)}")
    print(f"World Bounds (W, D, H): {dimensions[0]:.3f} m, {dimensions[1]:.3f} m, {dimensions[2]:.3f} m")
    print(f"Minimum Z: {mins[2]:.3f} m")
    print(f"Non-Manifold Edges: {open_edges}")
    print("Note: contact between glass, framing, foundation and greenhouse equipment is intentional.")
    print("The manifold check is per-mesh and does not detect intersections between separate objects.")
    print("----------------------------------------\n")


# -----------------------------------------------------------------------------
# Temporary, isolated render setup. Restore every scene-level setting before
# export/save; no pre-existing object or material is removed or edited.
# -----------------------------------------------------------------------------
original_state = {
    "engine": scene.render.engine,
    "resolution_x": scene.render.resolution_x,
    "resolution_y": scene.render.resolution_y,
    "resolution_percentage": scene.render.resolution_percentage,
    "file_format": scene.render.image_settings.file_format,
    "film_transparent": scene.render.film_transparent,
    "filepath": scene.render.filepath,
    "view_transform": scene.view_settings.view_transform,
    "world": scene.world,
    "camera": scene.camera,
    "active": bpy.context.view_layer.objects.active,
    "selected": list(bpy.context.selected_objects),
}
model_objects = set(model_col.objects)
helper_objects = set(helper_col.objects)
external_render_state = {obj: obj.hide_render for obj in scene.objects
                         if obj not in model_objects and obj not in helper_objects}
for obj in external_render_state:
    obj.hide_render = True

render_world = bpy.data.worlds.new("Greenhouse_DeepSeek_TemporaryRenderWorld")
render_world.use_nodes = True
render_bg = render_world.node_tree.nodes.get("Background")
if render_bg:
    render_bg.inputs["Color"].default_value = (0.82, 0.85, 0.84, 1.0)
    render_bg.inputs["Strength"].default_value = 0.8
try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError:
    scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.view_transform = "Standard"
scene.world = render_world

bpy.ops.object.camera_add()
camera = move_to_collection(bpy.context.object, helper_col)
camera.name = "Greenhouse_DeepSeek_QA_Camera"
camera.data.type = "ORTHO"
scene.camera = camera
for name, light_type, location, energy, size in (
        ("KeyLight", "SUN", (5, -5, 9), 2.4, None),
        ("FrontFill", "AREA", (-5, -6, 6), 260, 8),
        ("BackFill", "AREA", (0, 5, 6), 230, 8),
        ("SideFill", "AREA", (6, 0, 5), 260, 7),
        ("BottomFill", "AREA", (0, 0, -4), 110, 6)):
    bpy.ops.object.light_add(type=light_type, location=location)
    light = move_to_collection(bpy.context.object, helper_col)
    light.name = f"Greenhouse_DeepSeek_{name}"
    light.data.energy = energy
    if size is not None:
        light.data.shape = "DISK"
        light.data.size = size
    if light_type == "SUN":
        light.rotation_euler = (math.radians(34), math.radians(-18), math.radians(-28))
    else:
        light.rotation_euler = (Vector((0, 0, 1.55)) - light.location).to_track_quat("-Z", "Y").to_euler()
    if name == "BottomFill":
        light.hide_render = True


def render_view(location, rotation, filename, scale=5.7, underside=False):
    camera.location = location
    camera.rotation_euler = rotation
    camera.data.ortho_scale = scale
    bottom = bpy.data.objects.get("Greenhouse_DeepSeek_BottomFill")
    if bottom:
        bottom.hide_render = not underside
    scene.render.filepath = str(QA_DIR / filename)
    bpy.ops.render.render(write_still=True)


center_z = 1.65
scale_factor = 5.7
try:
    render_view((0, -18, center_z), (math.radians(90), 0, 0),
                "Greenhouse_DeepSeek_Front.png", scale=scale_factor)
    render_view((0, 18, center_z), (math.radians(90), 0, math.radians(180)),
                "Greenhouse_DeepSeek_Back.png", scale=scale_factor)
    render_view((-18, 0, center_z), (math.radians(90), 0, math.radians(-90)),
                "Greenhouse_DeepSeek_Left.png", scale=scale_factor)
    render_view((18, 0, center_z), (math.radians(90), 0, math.radians(90)),
                "Greenhouse_DeepSeek_Right.png", scale=scale_factor)
    render_view((0, 0, 18), (0, 0, 0), "Greenhouse_DeepSeek_Top.png",
                scale=scale_factor)
    render_view((0, 0, -18), (math.radians(180), 0, 0),
                "Greenhouse_DeepSeek_Bottom.png", scale=scale_factor, underside=True)
    camera.location = (7.5, -9.0, 6.8)
    target = Vector((0, -0.2, 1.62))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = 6.6
    bottom = bpy.data.objects.get("Greenhouse_DeepSeek_BottomFill")
    if bottom:
        bottom.hide_render = True
    scene.render.filepath = str(PREVIEW_DIR / "Greenhouse_DeepSeek.png")
    bpy.ops.render.render(write_still=True)
finally:
    scene.render.engine = original_state["engine"]
    scene.render.resolution_x = original_state["resolution_x"]
    scene.render.resolution_y = original_state["resolution_y"]
    scene.render.resolution_percentage = original_state["resolution_percentage"]
    scene.render.image_settings.file_format = original_state["file_format"]
    scene.render.film_transparent = original_state["film_transparent"]
    scene.render.filepath = original_state["filepath"]
    scene.view_settings.view_transform = original_state["view_transform"]
    scene.world = original_state["world"]
    scene.camera = original_state["camera"]
    for obj, hide_render in external_render_state.items():
        if obj.name in bpy.data.objects:
            obj.hide_render = hide_render
    helper_col.hide_viewport = True
    helper_col.hide_render = True
    if render_world.users == 0:
        bpy.data.worlds.remove(render_world)
    for obj in list(bpy.context.selected_objects):
        obj.select_set(False)
    for obj in original_state["selected"]:
        if obj.name in bpy.data.objects:
            obj.select_set(True)
    active = original_state["active"]
    bpy.context.view_layer.objects.active = active if active and active.name in bpy.data.objects else None


# Export only this asset's geometry; do not export lights/camera or alter others.
for obj in list(bpy.context.selected_objects):
    obj.select_set(False)
for obj in model_col.objects:
    if obj.type == "MESH":
        obj.select_set(True)
fbx_path = FBX_DIR / "Greenhouse_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path), use_selection=True, apply_scale_options="FBX_SCALE_ALL",
    object_types={"MESH"}, bake_space_transform=True,
)
for obj in list(bpy.context.selected_objects):
    obj.select_set(False)
for obj in original_state["selected"]:
    if obj.name in bpy.data.objects:
        obj.select_set(True)
bpy.context.view_layer.objects.active = original_state["active"] if original_state["active"] and original_state["active"].name in bpy.data.objects else None

blend_path = BLEND_DIR / "Greenhouse_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
report_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved preview to: {PREVIEW_DIR / 'Greenhouse_DeepSeek.png'}")
print(f"Saved six QA views to: {QA_DIR}")
