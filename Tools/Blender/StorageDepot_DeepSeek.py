import bpy
import bmesh
import math
from mathutils import Vector
from pathlib import Path

# ==========================================
# 1. Setup and Path Management
# ==========================================
PROJECT_ROOT = Path.cwd()
BLEND_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Buildings"
FBX_DIR = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Buildings"
PREVIEW_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Previews/Buildings"
QA_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"

for directory in [BLEND_DIR, FBX_DIR, PREVIEW_DIR, QA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

MODEL_COLLECTION_NAME = "StorageDepot_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_StorageDepot_DeepSeek"

# Remove only Blender's untouched startup trio when running without a project.
# Any custom scene or opened .blend is left intact.
if not bpy.data.filepath:
    startup_names = {obj.name for obj in bpy.context.scene.objects}
    if startup_names == {"Camera", "Cube", "Light"}:
        for startup_name in ("Cube", "Camera", "Light"):
            startup_obj = bpy.data.objects.get(startup_name)
            if startup_obj:
                bpy.data.objects.remove(startup_obj, do_unlink=True)

# Idempotent cleanup: remove only this script's exact collections.
for collection_name in (MODEL_COLLECTION_NAME, HELPER_COLLECTION_NAME):
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)

model_col = bpy.data.collections.new(MODEL_COLLECTION_NAME)
bpy.context.scene.collection.children.link(model_col)
helper_col = bpy.data.collections.new(HELPER_COLLECTION_NAME)
bpy.context.scene.collection.children.link(helper_col)

# ==========================================
# 2. Material Creation
# ==========================================
def create_material(name, base_color, roughness=0.8, metallic=0.0):
    # Reuse only this asset's namespaced materials; do not delete shared data.
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    output = nodes.new('ShaderNodeOutputMaterial')
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Base Color'].default_value = base_color
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    return mat

mat_wood = create_material('StorageDepot_DeepSeek_Cedar', (0.38, 0.27, 0.17, 1.0), 0.9)
mat_wood_light = create_material('StorageDepot_DeepSeek_SunbleachedWood', (0.52, 0.39, 0.25, 1.0), 0.92)
mat_wood_dark = create_material('StorageDepot_DeepSeek_DarkTimber', (0.22, 0.16, 0.11, 1.0), 0.9)
mat_metal = create_material('StorageDepot_DeepSeek_BlueGrayMetal', (0.20, 0.29, 0.34, 1.0), 0.65, 0.35)
mat_rust = create_material('StorageDepot_DeepSeek_Rust', (0.34, 0.17, 0.10, 1.0), 0.85, 0.15)
mat_stone = create_material('StorageDepot_DeepSeek_Stone', (0.32, 0.32, 0.30, 1.0), 0.95)
mat_teal = create_material('StorageDepot_DeepSeek_TealDrum', (0.16, 0.34, 0.35, 1.0), 0.65, 0.1)

# ==========================================
# 3. Helper Functions
# ==========================================
def apply_flat_shading(obj):
    for polygon in obj.data.polygons:
        polygon.use_smooth = False


def add_box(name, size, location, mat, parent_col, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    parent_col.objects.link(obj)
    apply_flat_shading(obj)
    return obj


def add_cylinder(name, radius, depth, location, mat, parent_col, rot=(0.0, 0.0, 0.0), verts=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=location, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    parent_col.objects.link(obj)
    apply_flat_shading(obj)
    return obj


def add_rope(name, start, end, radius, mat, parent_col, verts=6):
    start_v = Vector(start)
    end_v = Vector(end)
    delta = end_v - start_v
    length = delta.length
    if length < 0.001:
        return None
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=length, location=(start_v + end_v) / 2)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = delta.to_track_quat('Z', 'Y')
    obj.data.materials.append(mat)
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    parent_col.objects.link(obj)
    apply_flat_shading(obj)
    return obj

# ==========================================
# 4. Modeling - Main Structure
# ==========================================

# Dimensions and orientation: front is -Y, rear is +Y, +Z is up.
W = 5.4
D = 4.6
Z_FLOOR = 0.50
H_FRONT = 2.80
H_BACK = 3.80
WALL_COURSE = 0.22

# --- 4.1 Raised stone-and-timber foundation ---
pier_positions = [(-2.4, -1.9), (0.0, -1.9), (2.4, -1.9), (-2.4, 1.9), (0.0, 1.9), (2.4, 1.9)]
for i, (x, y) in enumerate(pier_positions):
    add_box(f'Foundation_Pier_{i}', (0.42, 0.42, 0.30), (x, y, 0.15), mat_stone, model_col)
    add_box(f'Foundation_Cap_{i}', (0.28, 0.28, 0.10), (x, y, 0.35), mat_wood_dark, model_col)

# A supported loading apron gives the exterior crates and awning posts a solid footing.
for i, (x, y) in enumerate([(-2.25, -2.98), (2.25, -2.98), (-2.25, -2.52), (2.25, -2.52)]):
    add_box(f'Loading_Platform_Pier_{i}', (0.34, 0.34, 0.30), (x, y, 0.15), mat_stone, model_col)
    add_box(f'Loading_Platform_Post_{i}', (0.18, 0.18, 0.12), (x, y, 0.36), mat_wood_dark, model_col)
for i, y in enumerate((-3.00, -2.55)):
    add_box(f'Loading_Platform_Joist_{i}', (5.10, 0.14, 0.14), (0.0, y, 0.35), mat_wood_dark, model_col)
for i in range(5):
    y = -3.08 + i * 0.18
    add_box(f'Loading_Platform_Board_{i}', (5.28, 0.17, 0.08), (0.0, y, 0.46), mat_wood_light if i % 3 == 0 else mat_wood, model_col)

# Five joists support the raised floor; the boards intentionally rest on them.
for i in range(5):
    y = -1.84 + i * 0.92
    add_box(f'Floor_Joist_{i}', (5.10, 0.16, 0.15), (0.0, y, 0.425), mat_wood_dark, model_col)
for i in range(12):
    x = -2.475 + i * 0.45
    board_mat = mat_wood_light if i % 4 == 0 else mat_wood
    add_box(f'Floor_Board_{i}', (0.42, 4.58, 0.08), (x, 0.0, 0.46), board_mat, model_col)

# --- 4.2 Timber frame and plank walls ---
# Corner posts fit inside the nominal 5.4 x 4.6 m wall footprint.
for i, (x, y) in enumerate([(-2.60, -2.20), (2.60, -2.20), (-2.60, 2.20), (2.60, 2.20)]):
    top = H_FRONT if y < 0 else H_BACK
    add_box(f'Wall_CornerPost_{i}', (0.20, 0.20, top - Z_FLOOR), (x, y, (top + Z_FLOOR) / 2), mat_wood_dark, model_col)
add_box('Wall_SideStud_Left_Mid', (0.16, 0.16, 2.80), (-2.60, 0.0, 1.90), mat_wood_dark, model_col)
add_box('Wall_SideStud_Right_Mid', (0.16, 0.16, 2.80), (2.60, 0.0, 1.90), mat_wood_dark, model_col)

# Front wall courses leave a clear centered double-door opening.
door_width = 1.80
door_height = 1.85
door_top = Z_FLOOR + door_height
front_y = -D / 2
course_count_front = int((H_FRONT - Z_FLOOR) / WALL_COURSE)
for i in range(course_count_front):
    z = Z_FLOOR + (i + 0.5) * WALL_COURSE
    plank_h = WALL_COURSE - 0.025
    plank_mat = mat_wood_light if i % 4 == 1 else mat_wood
    add_box(f'Wall_Front_Plank_Left_{i}', (1.80, 0.12, plank_h), (-1.80, front_y, z), plank_mat, model_col)
    add_box(f'Wall_Front_Plank_Right_{i}', (1.80, 0.12, plank_h), (1.80, front_y, z), plank_mat, model_col)
    if z - plank_h / 2 >= door_top:
        add_box(f'Wall_Front_Plank_AboveDoor_{i}', (1.80, 0.12, plank_h), (0.0, front_y, z), plank_mat, model_col)
# Door jambs and lintel make a readable, supported opening.
add_box('Door_Frame_Left', (0.14, 0.18, door_height + 0.08), (-0.96, front_y - 0.01, Z_FLOOR + door_height / 2), mat_wood_dark, model_col)
add_box('Door_Frame_Right', (0.14, 0.18, door_height + 0.08), (0.96, front_y - 0.01, Z_FLOOR + door_height / 2), mat_wood_dark, model_col)
add_box('Door_Header', (2.05, 0.18, 0.16), (0.0, front_y - 0.01, door_top + 0.07), mat_wood_dark, model_col)

# Rear courses are split around a small high vent opening.
back_y = D / 2
vent_center_z = 3.32
for i in range(int((H_BACK - Z_FLOOR) / WALL_COURSE)):
    z = Z_FLOOR + (i + 0.5) * WALL_COURSE
    plank_h = WALL_COURSE - 0.025
    plank_mat = mat_wood_light if i % 5 == 2 else mat_wood
    in_vent = abs(z - vent_center_z) < 0.28
    if in_vent:
        add_box(f'Wall_Back_Plank_Left_{i}', (2.30, 0.12, plank_h), (-1.55, back_y, z), plank_mat, model_col)
        add_box(f'Wall_Back_Plank_Right_{i}', (2.30, 0.12, plank_h), (1.55, back_y, z), plank_mat, model_col)
    else:
        add_box(f'Wall_Back_Plank_{i}', (W, 0.12, plank_h), (0.0, back_y, z), plank_mat, model_col)

# Side walls use stacked boards whose rear ends rise with the shed roof.
for side_name, x in [('Left', -2.60), ('Right', 2.60)]:
    for i in range(15):
        z = Z_FLOOR + (i + 0.5) * WALL_COURSE
        course_top = z + (WALL_COURSE - 0.025) / 2
        if course_top <= H_FRONT:
            y_start = -D / 2
        elif course_top >= H_BACK:
            continue
        else:
            y_start = -D / 2 + D * (course_top - H_FRONT) / (H_BACK - H_FRONT)
        plank_depth = D / 2 - y_start
        if plank_depth > 0.12:
            plank_mat = mat_wood_light if i % 5 == 1 else mat_wood
            add_box(f'Wall_{side_name}_Course_{i}', (0.12, plank_depth, WALL_COURSE - 0.025), (x, (y_start + D / 2) / 2, z), plank_mat, model_col)

# Rear vent frame and louvers remain separate, named pieces.
vent_y = back_y + 0.08
add_box('Vent_Frame_Top', (0.82, 0.12, 0.08), (0.0, vent_y, vent_center_z + 0.25), mat_wood_dark, model_col)
add_box('Vent_Frame_Bottom', (0.82, 0.12, 0.08), (0.0, vent_y, vent_center_z - 0.25), mat_wood_dark, model_col)
add_box('Vent_Frame_Left', (0.08, 0.12, 0.42), (-0.37, vent_y, vent_center_z), mat_wood_dark, model_col)
add_box('Vent_Frame_Right', (0.08, 0.12, 0.42), (0.37, vent_y, vent_center_z), mat_wood_dark, model_col)
for i in range(4):
    add_box(f'Vent_Louver_{i}', (0.64, 0.06, 0.045), (0.0, vent_y + 0.06, vent_center_z - 0.15 + i * 0.10), mat_wood_light, model_col, rot=(math.radians(22), 0.0, 0.0))

# --- 4.3 Double cargo doors, braces and iron hardware ---
for leaf_index, center_x in enumerate((-0.44, 0.44)):
    add_box(f'Door_Panel_{leaf_index}', (0.86, 0.10, door_height), (center_x, front_y - 0.11, Z_FLOOR + door_height / 2), mat_wood, model_col)
    # Three raised boards per leaf reinforce the planked construction.
    for board_index in range(3):
        board_x = center_x - 0.28 + board_index * 0.28
        add_box(f'Door_Leaf_{leaf_index}_Board_{board_index}', (0.22, 0.035, door_height - 0.10), (board_x, front_y - 0.18, Z_FLOOR + door_height / 2), mat_wood_light if board_index == 1 else mat_wood, model_col)
    brace_len = math.sqrt((0.72 ** 2) + (1.52 ** 2))
    brace_angle = math.atan2(1.52, 0.72)
    add_box(f'Door_DiagonalBrace_{leaf_index}', (brace_len, 0.07, 0.08), (center_x, front_y - 0.23, Z_FLOOR + door_height / 2), mat_wood_dark, model_col, rot=(0.0, brace_angle if leaf_index == 0 else -brace_angle, 0.0))

# Three hinges per door stay within the door height; plates touch both leaf and jamb.
for hinge_index, z in enumerate((0.82, 1.42, 2.02)):
    for side, x in [('L', -0.86), ('R', 0.86)]:
        add_box(f'Door_Hinge_{side}_{hinge_index}', (0.12, 0.035, 0.14), (x, front_y - 0.24, z), mat_metal, model_col)
        add_cylinder(f'Door_HingePin_{side}_{hinge_index}', 0.035, 0.16, (x, front_y - 0.26, z), mat_metal, model_col, verts=8)
add_box('Door_Latch_Bar', (0.22, 0.05, 0.07), (0.0, front_y - 0.25, 1.52), mat_metal, model_col)
add_box('Door_Latch_Handle', (0.07, 0.07, 0.18), (0.0, front_y - 0.29, 1.39), mat_metal, model_col)

# --- 4.4 Salvaged mono-pitch corrugated roof ---
roof_overhang = 0.40
roof_width = W + 2 * roof_overhang
roof_angle = math.atan2(H_BACK - H_FRONT, D)
roof_length = math.sqrt(D ** 2 + (H_BACK - H_FRONT) ** 2) + 2 * roof_overhang
roof_center_y = 0.0
roof_center_z = (H_FRONT + H_BACK) / 2
roof_rotation = (roof_angle, 0.0, 0.0)
add_box('Roof_MainPanel', (roof_width, roof_length, 0.12), (0.0, roof_center_y, roof_center_z), mat_metal, model_col, rot=roof_rotation)
for i in range(17):
    x = -roof_width / 2 + 0.12 + i * (roof_width - 0.24) / 16
    rib_mat = mat_rust if i in (3, 13) else mat_metal
    add_box(f'Roof_CorrugationRib_{i}', (0.055, roof_length, 0.045), (x, roof_center_y, roof_center_z + 0.075), rib_mat, model_col, rot=roof_rotation)
for side, x in [('Left', -roof_width / 2 + 0.04), ('Right', roof_width / 2 - 0.04)]:
    add_box(f'Roof_SideFascia_{side}', (0.12, roof_length, 0.13), (x, roof_center_y, roof_center_z - 0.05), mat_wood_dark, model_col, rot=roof_rotation)

# --- 4.5 Loading awning and safe access ramp ---
awning_width = 2.45
awning_length = 1.18
awning_angle = math.radians(13)
awning_center_y = -2.78
awning_center_z = 2.45
awning_rotation = (awning_angle, 0.0, 0.0)
add_box('Loading_Awning_Panel', (awning_width, awning_length, 0.07), (0.0, awning_center_y, awning_center_z), mat_metal, model_col, rot=awning_rotation)
for i in range(8):
    x = -awning_width / 2 + 0.10 + i * (awning_width - 0.20) / 7
    add_box(f'Awning_Corrugation_{i}', (0.045, awning_length, 0.035), (x, awning_center_y, awning_center_z + 0.045), mat_metal, model_col, rot=awning_rotation)
for side, x in [('Left', -1.08), ('Right', 1.08)]:
    add_box(f'Awning_Post_{side}', (0.14, 0.14, 1.84), (x, -3.00, 1.42), mat_wood_dark, model_col)
    add_box(f'Awning_Brace_{side}', (0.62, 0.10, 0.10), (x * 0.82, -2.83, 2.25), mat_wood, model_col, rot=(math.radians(18), 0.0, math.radians(28 if x < 0 else -28)))

# The ramp slopes between ground and the raised floor while keeping its underside at Z=0.
ramp_width = 1.45
ramp_run = 0.85
ramp_rise = 0.43
ramp_length = math.sqrt(ramp_run ** 2 + ramp_rise ** 2)
ramp_angle = math.atan2(ramp_rise, ramp_run)
ramp_low_center_z = 0.06
ramp_center_y = -3.17 - ramp_run / 2
ramp_center_z = ramp_low_center_z + ramp_rise / 2
add_box('Access_Ramp_Base', (ramp_width, ramp_length, 0.12), (0.0, ramp_center_y, ramp_center_z), mat_wood_dark, model_col, rot=(ramp_angle, 0.0, 0.0))
for side, x in [('Left', -ramp_width / 2 + 0.06), ('Right', ramp_width / 2 - 0.06)]:
    add_box(f'Access_Ramp_Rail_{side}', (0.10, ramp_length, 0.14), (x, ramp_center_y, ramp_center_z + 0.10), mat_wood, model_col, rot=(ramp_angle, 0.0, 0.0))
for i in range(5):
    t = (i + 0.5) / 5
    y = -3.17 - t * ramp_run
    z = Z_FLOOR - t * ramp_rise + 0.015
    add_box(f'Access_Ramp_Tread_{i}', (ramp_width - 0.12, 0.07, 0.035), (0.0, y, z), mat_wood_light, model_col, rot=(ramp_angle, 0.0, 0.0))

# --- 4.6 Gutter, downpipe, and rain barrel ---
# The front edge is the low eave; compute its world-space position from the roof plane.
roof_front_y = -(roof_length / 2) * math.cos(roof_angle)
roof_front_z = roof_center_z - (roof_length / 2) * math.sin(roof_angle) - 0.07
add_box('Gutter_Bottom', (roof_width, 0.16, 0.055), (0.0, roof_front_y, roof_front_z), mat_metal, model_col)
add_box('Gutter_OuterLip', (roof_width, 0.045, 0.14), (0.0, roof_front_y - 0.075, roof_front_z + 0.055), mat_metal, model_col)
add_box('Gutter_InnerLip', (roof_width, 0.045, 0.14), (0.0, roof_front_y + 0.075, roof_front_z + 0.055), mat_metal, model_col)
pipe_x = -roof_width / 2 + 0.16
add_rope('Gutter_Downpipe_Vertical', (pipe_x, roof_front_y, roof_front_z + 0.03), (pipe_x, roof_front_y, 0.82), 0.055, mat_metal, model_col)
barrel_pos = (-3.25, -2.60, 0.40)
add_rope('Gutter_Downpipe_Elbow', (pipe_x, roof_front_y, 0.82), (barrel_pos[0] + 0.25, barrel_pos[1], 0.76), 0.055, mat_metal, model_col)
add_cylinder('RainBarrel_Body', 0.25, 0.80, barrel_pos, mat_teal, model_col, verts=12)
add_cylinder('RainBarrel_Lid', 0.26, 0.055, (barrel_pos[0], barrel_pos[1], 0.83), mat_metal, model_col, verts=12)
for i, z in enumerate((0.22, 0.57)):
    add_cylinder(f'RainBarrel_Band_{i}', 0.265, 0.045, (barrel_pos[0], barrel_pos[1], z), mat_metal, model_col, verts=12)

# --- 4.7 Weatherproof cargo props near the loading area ---
crate_positions = [(-1.95, -2.72, 0.80), (1.75, -2.70, 0.76)]
crate_sizes = [(0.62, 0.56, 0.60), (0.70, 0.48, 0.52)]
for i, ((x, y, z), (sx, sy, sz)) in enumerate(zip(crate_positions, crate_sizes)):
    add_box(f'Cargo_Crate_{i}_Body', (sx, sy, sz), (x, y, z), mat_wood, model_col)
    add_box(f'Cargo_Crate_{i}_Lid', (sx + 0.05, sy + 0.05, 0.06), (x, y, z + sz / 2 + 0.03), mat_wood_dark, model_col)
    for brace_index, x_side in enumerate((-1, 1)):
        add_box(f'Cargo_Crate_{i}_CornerBrace_{brace_index}', (0.07, sy + 0.02, sz - 0.06), (x + x_side * (sx / 2 - 0.035), y, z), mat_wood_light, model_col)

cargo_drum_pos = (2.40, -2.70, Z_FLOOR + 0.40)
add_cylinder('Cargo_Drum_Body', 0.25, 0.80, cargo_drum_pos, mat_teal, model_col, verts=12)
add_cylinder('Cargo_Drum_Lid', 0.26, 0.055, (cargo_drum_pos[0], cargo_drum_pos[1], cargo_drum_pos[2] + 0.41), mat_metal, model_col, verts=12)
for i, z in enumerate((cargo_drum_pos[2] - 0.22, cargo_drum_pos[2] + 0.22)):
    add_cylinder(f'Cargo_Drum_Band_{i}', 0.265, 0.045, (cargo_drum_pos[0], cargo_drum_pos[1], z), mat_metal, model_col, verts=12)
# ==========================================
# 5. Quality Diagnostics
# ==========================================
def calculate_bounds_and_diagnostics():
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
    mesh_objects = [obj for obj in model_col.objects if obj.type == 'MESH']
    non_manifold_count = 0
    for obj in mesh_objects:
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            min_x, min_y, min_z = min(min_x, point.x), min(min_y, point.y), min(min_z, point.z)
            max_x, max_y, max_z = max(max_x, point.x), max(max_y, point.y), max(max_z, point.z)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        non_manifold_count += sum(1 for edge in bm.edges if not edge.is_manifold)
        bm.free()
    print("\n--- Storage Depot Diagnostic Report ---")
    print(f"Mesh Object Count: {len(mesh_objects)}")
    print(f"World Bounds (W, D, H): {max_x - min_x:.3f} m, {max_y - min_y:.3f} m, {max_z - min_z:.3f} m")
    print(f"Minimum Z: {min_z:.3f} m")
    print(f"Non-Manifold Edges: {non_manifold_count}")
    print("Note: non-manifold checking does not detect intersections between separate objects.")
    print("--------------------------------------\n")

# ==========================================
# 6. Render Setup and Orthographic QA Views
# ==========================================
scene = bpy.context.scene
original_scene_state = {
    "engine": scene.render.engine,
    "resolution_x": scene.render.resolution_x,
    "resolution_y": scene.render.resolution_y,
    "resolution_percentage": scene.render.resolution_percentage,
    "film_transparent": scene.render.film_transparent,
    "filepath": scene.render.filepath,
    "view_transform": scene.view_settings.view_transform,
    "world": scene.world,
    "camera": scene.camera,
}
model_objects = set(model_col.objects)
helper_objects = set(helper_col.objects)
external_render_state = {
    obj: obj.hide_render
    for obj in scene.objects
    if obj not in model_objects and obj not in helper_objects
}
for obj in external_render_state:
    obj.hide_render = True

try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        pass
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'

render_world = bpy.data.worlds.new(f"StorageDepot_DeepSeek_RenderWorld_{len(bpy.data.worlds)}")
render_world.use_nodes = True
background = next((node for node in render_world.node_tree.nodes if node.type == 'BACKGROUND'), None)
if background:
    background.inputs['Color'].default_value = (0.9, 0.9, 0.9, 1.0)
    background.inputs['Strength'].default_value = 0.8
scene.world = render_world

bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.name = "StorageDepot_DeepSeek_Sun"
sun.data.energy = 2.0
sun.rotation_euler = (math.radians(35), math.radians(20), math.radians(25))
for collection in list(sun.users_collection):
    collection.objects.unlink(sun)
helper_col.objects.link(sun)

bpy.ops.object.light_add(type='AREA', location=(-4, -6, 6))
area = bpy.context.active_object
area.name = "StorageDepot_DeepSeek_Area"
area.data.energy = 450
area.data.shape = 'DISK'
area.data.size = 7
area.rotation_euler = (math.radians(35), 0.0, math.radians(-35))
for collection in list(area.users_collection):
    collection.objects.unlink(area)
helper_col.objects.link(area)

bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.name = "StorageDepot_DeepSeek_Camera"
cam.data.type = 'ORTHO'
for collection in list(cam.users_collection):
    collection.objects.unlink(cam)
helper_col.objects.link(cam)
scene.camera = cam

render_center = Vector((0.0, -0.67, 2.0))
def render_view(offset, rotation, ortho_scale, filename):
    cam.location = render_center + Vector(offset)
    cam.rotation_euler = rotation
    cam.data.ortho_scale = ortho_scale
    scene.render.filepath = str(QA_DIR / filename)
    bpy.ops.render.render(write_still=True)

render_view((0, -20, 0), (math.radians(90), 0, 0), 7.8, "StorageDepot_DeepSeek_Front.png")
render_view((0, 20, 0), (math.radians(90), 0, math.radians(180)), 7.8, "StorageDepot_DeepSeek_Back.png")
render_view((-20, 0, 0), (math.radians(90), 0, math.radians(-90)), 7.6, "StorageDepot_DeepSeek_Left.png")
render_view((20, 0, 0), (math.radians(90), 0, math.radians(90)), 7.6, "StorageDepot_DeepSeek_Right.png")
render_view((0, 0, 20), (0, 0, 0), 7.8, "StorageDepot_DeepSeek_Top.png")
render_view((0, 0, -20), (math.radians(180), 0, 0), 7.8, "StorageDepot_DeepSeek_Bottom.png")

cam.location = (9, -14, 9)
look_target = Vector((0, -0.67, 2.0))
cam.rotation_euler = (look_target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 8.8
scene.render.filepath = str(PREVIEW_DIR / "StorageDepot_DeepSeek.png")
bpy.ops.render.render(write_still=True)

# Restore original render visibility and scene settings before saving.
for obj, hidden in external_render_state.items():
    if obj.name in bpy.data.objects:
        obj.hide_render = hidden
scene.render.engine = original_scene_state["engine"]
scene.render.resolution_x = original_scene_state["resolution_x"]
scene.render.resolution_y = original_scene_state["resolution_y"]
scene.render.resolution_percentage = original_scene_state["resolution_percentage"]
scene.render.film_transparent = original_scene_state["film_transparent"]
scene.render.filepath = original_scene_state["filepath"]
scene.view_settings.view_transform = original_scene_state["view_transform"]
scene.world = original_scene_state["world"]
scene.camera = original_scene_state["camera"]
if render_world.users == 0:
    bpy.data.worlds.remove(render_world)

# ==========================================
# 7. Export FBX and Save Blend
# ==========================================
bpy.ops.object.select_all(action='DESELECT')
for obj in model_col.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

fbx_path = FBX_DIR / "StorageDepot_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True,
)

blend_path = BLEND_DIR / "StorageDepot_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
calculate_bounds_and_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved preview to: {PREVIEW_DIR / 'StorageDepot_DeepSeek.png'}")
print(f"Saved QA renders to: {QA_DIR}")



