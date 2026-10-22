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

for d in [BLEND_DIR, FBX_DIR, PREVIEW_DIR, QA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MODEL_COLLECTION_NAME = "ResidentHut_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_ResidentHut_DeepSeek"

# Remove only Blender's untouched startup trio when running without a project.
if not bpy.data.filepath:
    startup_names = {obj.name for obj in bpy.context.scene.objects}
    if startup_names == {"Camera", "Cube", "Light"}:
        for startup_name in ("Cube", "Camera", "Light"):
            startup_obj = bpy.data.objects.get(startup_name)
            if startup_obj:
                bpy.data.objects.remove(startup_obj, do_unlink=True)

# Clean up previous runs (idempotent)
for col_name in [MODEL_COLLECTION_NAME, HELPER_COLLECTION_NAME]:
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

# Create new collections
model_col = bpy.data.collections.new(MODEL_COLLECTION_NAME)
bpy.context.scene.collection.children.link(model_col)

helper_col = bpy.data.collections.new(HELPER_COLLECTION_NAME)
bpy.context.scene.collection.children.link(helper_col)

# ==========================================
# 2. Material Creation
# ==========================================
def create_material(name, base_color, roughness=0.8, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in list(nodes):
        nodes.remove(node)

    out_node = nodes.new('ShaderNodeOutputMaterial')
    bsdf_node = nodes.new('ShaderNodeBsdfPrincipled')

    bsdf_node.inputs['Base Color'].default_value = base_color
    bsdf_node.inputs['Roughness'].default_value = roughness
    bsdf_node.inputs['Metallic'].default_value = metallic

    links.new(bsdf_node.outputs['BSDF'], out_node.inputs['Surface'])
    return mat

mat_wood = create_material("ResidentHut_DeepSeek_Cedar", (0.45, 0.35, 0.25, 1.0), roughness=0.9)
mat_wood_dark = create_material("ResidentHut_DeepSeek_DarkWood", (0.22, 0.15, 0.1, 1.0), roughness=0.9)
mat_roof = create_material("ResidentHut_DeepSeek_RoofMetal", (0.3, 0.35, 0.4, 1.0), roughness=0.6, metallic=0.4)
mat_iron = create_material("ResidentHut_DeepSeek_Iron", (0.12, 0.12, 0.14, 1.0), roughness=0.5, metallic=0.8)

# ==========================================
# 3. Helper Functions
# ==========================================
def apply_flat_shading(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = False

def add_box(name, size, location, mat, parent_col, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    obj.data.materials.append(mat)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    parent_col.objects.link(obj)
    apply_flat_shading(obj)
    return obj

def add_cylinder(name, radius, depth, location, mat, parent_col, rot=(0,0,0), verts=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=location, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    parent_col.objects.link(obj)
    apply_flat_shading(obj)
    return obj

# ==========================================
# 4. Modeling - Main Structure
# ==========================================

# Dimensions Plan:
# Footprint: approx 4.4m (X) x 4.0m (Y) including porch.
# Height: Piles to Z=1.0. Walls to Z=2.5 (front) / 3.3 (back). Roof max Z=3.5.
# Front is -Y, Back is +Y.

# --- 4.1 Foundation & Floor Frame ---
# 4 main piles
pile_positions = [(-1.8, -1.0), (0.0, -1.0), (1.8, -1.0), (-1.8, 1.6), (0.0, 1.6), (1.8, 1.6)]
for i, (x, y) in enumerate(pile_positions):
    # Pile
    add_box(f"Foundation_Pile_{i}", (0.3, 0.3, 1.0), (x, y, 0.5), mat_wood_dark, model_col)
    # Concrete base (optional, but keeps it grounded)
    add_box(f"Foundation_Base_{i}", (0.4, 0.4, 0.1), (x, y, 0.05), mat_wood_dark, model_col)

# Floor Beams (Joists)
for y in [-1.0, 1.6]:
    add_box(f"Floor_Beam_{y}", (3.9, 0.2, 0.2), (0, y, 1.0), mat_wood_dark, model_col)
for x in [-1.8, 0, 1.8]:
    add_box(f"Floor_Joist_{x}", (0.15, 2.8, 0.2), (x, 0.3, 1.0), mat_wood_dark, model_col)

# Cross bracing under the floor
add_box("Foundation_Brace_L", (0.1, 2.6, 0.1), (-1.8, 0.3, 0.5), mat_wood_dark, model_col, rot=(math.radians(18), 0, 0))
add_box("Foundation_Brace_R", (0.1, 2.6, 0.1), (1.8, 0.3, 0.5), mat_wood_dark, model_col, rot=(math.radians(-18), 0, 0))

# Deck Planks (running along X)
# Main floor
for i in range(9):
    y_pos = -1.0 + (i + 0.5) * (2.6 / 9)
    add_box(f"Floor_Plank_Main_{i}", (3.6, 0.28, 0.08), (0, y_pos, 1.14), mat_wood, model_col)

# Porch floor (extends towards -Y)
for i in range(4):
    y_pos = -1.6 + (i + 0.5) * (0.6 / 4)
    add_box(f"Floor_Plank_Porch_{i}", (3.6, 0.14, 0.08), (0, y_pos, 1.14), mat_wood, model_col)

# --- 4.2 Walls ---
# Corner posts
corner_posts = [(-1.8, -1.0), (1.8, -1.0), (-1.8, 1.6), (1.8, 1.6)]
for i, (x, y) in enumerate(corner_posts):
    h = 1.85 if y < 0 else 2.25
    add_box(f"Wall_CornerPost_{i}", (0.2, 0.2, h), (x, y, 1.18 + h/2), mat_wood, model_col)

# Back Wall (+Y)
for i in range(7):
    z_pos = 1.18 + 0.15 + i * 0.3
    add_box(f"Wall_Plank_Back_{i}", (3.6, 0.1, 0.28), (0, 1.6, z_pos), mat_wood, model_col)
# Back Vent
add_box("Vent_Frame", (0.4, 0.05, 0.3), (0, 1.65, 2.8), mat_iron, model_col)

# Side walls rise toward the high rear roof edge. The center section contains a real window opening.
side_sections = [(-0.57, 0.84, 5), (0.30, 0.84, 6), (1.17, 0.84, 7)]
for side in [-1, 1]:
    x_pos = side * 1.8
    for section_index, (y_center, section_length, row_count) in enumerate(side_sections):
        for i in range(row_count):
            if section_index == 1 and i in (2, 3):
                continue
            z_pos = 1.18 + 0.15 + i * 0.3
            add_box(f"Wall_Plank_Side_{side}_{section_index}_{i}", (0.1, section_length, 0.28), (x_pos, y_center, z_pos), mat_wood, model_col)

    # Shuttered side window through the center wall section.
    frame_x = x_pos + side * 0.06
    add_box(f"Window_Frame_{side}", (0.08, 0.78, 0.62), (frame_x, 0.30, 2.03), mat_wood_dark, model_col)
    add_box(f"Window_Glass_{side}", (0.035, 0.62, 0.46), (x_pos + side * 0.105, 0.30, 2.03), mat_iron, model_col)
    for panel, y_offset in (("L", -0.48), ("R", 0.48)):
        add_box(f"Window_Shutter_{panel}_{side}", (0.045, 0.25, 0.62), (x_pos + side * 0.12, 0.30 + y_offset, 2.03), mat_wood, model_col)

# Front Wall (-Y)
# Left and right of door
for side in [-1, 1]:
    start_x = side * 1.8
    end_x = side * 0.5
    width = abs(start_x - end_x)
    center_x = (start_x + end_x) / 2
    for i in range(5):
        z_pos = 1.18 + 0.15 + i * 0.3
        add_box(f"Wall_Plank_Front_{side}_{i}", (width, 0.1, 0.28), (center_x, -1.0, z_pos), mat_wood, model_col)

# Short lintel plank above the door, kept below the low roof edge.
add_box("Wall_Plank_Front_Top_0", (1.0, 0.1, 0.28), (0, -1.0, 2.82), mat_wood, model_col)

# Door
add_box("Door_Main", (0.9, 0.1, 1.64), (0, -1.07, 2.00), mat_wood_dark, model_col)
# Door frame: jambs and a simple lintel with dark iron hardware.
for side in (-1, 1):
    add_box(f"Door_Jamb_{side}", (0.10, 0.12, 1.78), (side * 0.53, -1.08, 2.05), mat_wood, model_col)
add_box("Door_Lintel", (1.15, 0.12, 0.12), (0, -1.08, 2.88), mat_wood, model_col)
# Door Handle
add_box("Door_Handle", (0.05, 0.08, 0.15), (0.3, -1.12, 2.0), mat_iron, model_col)
# Door Hinges
for i in range(2):
    add_box(f"Door_Hinge_{i}", (0.1, 0.05, 0.1), (-0.35, -1.14, 1.55 + i*0.8), mat_iron, model_col)

# --- 4.3 Roof ---
# Single slope, high at +Y (Z=3.5), low at -Y (Z=2.5)
# Overhang: X +/- 2.1, Y -1.8 to 1.9
roof_w = 4.4
roof_len_y = 3.7
roof_z_front = 2.85
roof_z_back = 3.55

roof_angle = math.atan2(roof_z_back - roof_z_front, roof_len_y)
roof_len_true = math.sqrt(roof_len_y**2 + (roof_z_back - roof_z_front)**2)
roof_center_y = 0.05
roof_center_z = (roof_z_front + roof_z_back) / 2

# Main Roof Panel
add_box("Roof_Panel", (roof_w, roof_len_true, 0.05), (0, roof_center_y, roof_center_z), mat_roof, model_col, rot=(roof_angle, 0, 0))

# Corrugated Ribs
num_ribs = 15
for i in range(num_ribs):
    x_pos = -roof_w/2 + 0.15 + i * (roof_w - 0.3) / (num_ribs - 1)
    add_box(f"Roof_Rib_{i}", (0.08, roof_len_true, 0.06), (x_pos, roof_center_y, roof_center_z + 0.03), mat_roof, model_col, rot=(roof_angle, 0, 0))

# Gutters along low edge (-Y)
gutter_y = -1.8
gutter_z = roof_z_front - 0.08
add_cylinder("Gutter_Main", 0.08, roof_w, (0, gutter_y, gutter_z), mat_roof, model_col, rot=(0, math.radians(90), 0), verts=8)
# Downspouts
add_cylinder("Gutter_Down_L", 0.06, 1.2, (-2.1, gutter_y, gutter_z - 0.6), mat_roof, model_col, verts=8)
add_cylinder("Gutter_Down_R", 0.06, 1.2, (2.1, gutter_y, gutter_z - 0.6), mat_roof, model_col, verts=8)

# --- 4.4 Stairs and Porch Details ---
# Five supported stair treads rise from ground to the porch without a gap.
stairs_w = 1.0
stair_front_y = -2.25
stair_y_step = 0.16
stair_rise = 0.24
first_tread_top = 0.20
for i in range(5):
    y_pos = stair_front_y + i * stair_y_step
    tread_top = first_tread_top + i * stair_rise
    add_box(f"Stair_Step_{i}", (stairs_w, 0.34, 0.08), (0, y_pos, tread_top - 0.04), mat_wood, model_col)
    riser_bottom = 0.0 if i == 0 else first_tread_top + (i - 1) * stair_rise
    riser_height = tread_top - riser_bottom
    add_box(f"Stair_Riser_{i}", (stairs_w, 0.05, riser_height), (0, y_pos - 0.17, riser_bottom + riser_height / 2), mat_wood_dark, model_col)

# Sloped handrails rise toward the porch and meet the top tread.
rail_angle = math.atan2(1.0, 0.95)
for side, x in (("L", -0.54), ("R", 0.54)):
    add_box(f"Stair_Rail_{side}", (0.07, 1.28, 0.07), (x, -1.93, 0.75), mat_wood, model_col, rot=(rail_angle, 0, 0))

# Porch Rails (Sides)
for side, x in (("L", -1.73), ("R", 1.73)):
    add_box(f"Porch_Rail_Post_{side}", (0.08, 0.08, 0.72), (x, -1.3, 1.54), mat_wood_dark, model_col)
    add_box(f"Porch_Rail_Upper_{side}", (0.07, 0.62, 0.07), (x, -1.3, 1.82), mat_wood, model_col)
    add_box(f"Porch_Rail_Lower_{side}", (0.06, 0.62, 0.06), (x, -1.3, 1.48), mat_wood, model_col)

# ==========================================
# 5. Quality Diagnostic Setup
# ==========================================
def calculate_bounds_and_diagnostics():
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')

    mesh_objects = [obj for obj in model_col.objects if obj.type == 'MESH']
    non_manifold_count = 0

    for obj in mesh_objects:
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ Vector(corner)
            min_x = min(min_x, world_corner.x)
            min_y = min(min_y, world_corner.y)
            min_z = min(min_z, world_corner.z)
            max_x = max(max_x, world_corner.x)
            max_y = max(max_y, world_corner.y)
            max_z = max(max_z, world_corner.z)

        bm = bmesh.new()
        bm.from_mesh(obj.data)
        non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
        non_manifold_count += len(non_manifold_edges)
        bm.free()

    print("\n--- Diagnostic Report ---")
    print(f"Mesh Object Count: {len(mesh_objects)}")
    print(f"World Bounds (W, D, H): {max_x - min_x:.3f} m, {max_y - min_y:.3f} m, {max_z - min_z:.3f} m")
    print(f"Minimum Z: {min_z:.3f} m")
    print(f"Non-Manifold Edges: {non_manifold_count}")
    print("Note: Non-manifold check detects open edges; it does NOT detect object-to-object intersections.")
    print("-------------------------\n")

# ==========================================
# 6. Render Setup & QA Renders
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

# A temporary render world keeps the project world untouched.
render_world = bpy.data.worlds.new(f"ResidentHut_DeepSeek_RenderWorld_{len(bpy.data.worlds)}")
render_world.use_nodes = True
bg_node = render_world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.86, 0.86, 0.86, 1.0)
    bg_node.inputs[1].default_value = 0.8
scene.world = render_world

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), math.radians(20), math.radians(30))
for c in sun.users_collection:
    c.objects.unlink(sun)
helper_col.objects.link(sun)

bpy.ops.object.light_add(type='AREA', location=(-5, -6, 6))
area = bpy.context.active_object
area.data.energy = 500
area.data.size = 10
area.rotation_euler = (math.radians(60), 0, math.radians(-45))
for c in area.users_collection:
    c.objects.unlink(area)
helper_col.objects.link(area)

# Camera
bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.data.type = 'ORTHO'
for c in cam.users_collection:
    c.objects.unlink(cam)
helper_col.objects.link(cam)
scene.camera = cam

def render_view(loc, rot, ortho_scale, filename):
    cam.location = loc
    cam.rotation_euler = rot
    cam.data.ortho_scale = ortho_scale
    scene.render.filepath = str(QA_DIR / filename)
    bpy.ops.render.render(write_still=True)

center_z = 1.8
scale_factor = 6.0
try:
    # Six full-asset orthographic views.
    render_view((0, -20, center_z), (math.radians(90), 0, 0), scale_factor, "ResidentHut_DeepSeek_Front.png")
    render_view((0, 20, center_z), (math.radians(90), 0, math.radians(180)), scale_factor, "ResidentHut_DeepSeek_Back.png")
    render_view((-20, 0, center_z), (math.radians(90), 0, math.radians(-90)), scale_factor, "ResidentHut_DeepSeek_Left.png")
    render_view((20, 0, center_z), (math.radians(90), 0, math.radians(90)), scale_factor, "ResidentHut_DeepSeek_Right.png")
    render_view((0, 0, 20), (0, 0, 0), scale_factor, "ResidentHut_DeepSeek_Top.png")
    render_view((0, 0, -20), (math.radians(180), 0, 0), scale_factor, "ResidentHut_DeepSeek_Bottom.png")

    # Three-quarter preview from the boat/sea side so the porch and side windows read clearly.
    cam.location = (8, -10, 8)
    look_target = Vector((0, 0.2, 1.8))
    direction = look_target - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = 7.0
    scene.render.filepath = str(PREVIEW_DIR / "ResidentHut_DeepSeek.png")
    bpy.ops.render.render(write_still=True)
finally:
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
# 7. Export FBX & Save Blend
# ==========================================
bpy.ops.object.select_all(action='DESELECT')
for obj in model_col.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

fbx_path = FBX_DIR / "ResidentHut_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True
)

blend_path = BLEND_DIR / "ResidentHut_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# ==========================================
# 8. Execute Diagnostics
# ==========================================
calculate_bounds_and_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved Previews to: {PREVIEW_DIR}")
print(f"Saved QA Renders to: {QA_DIR}")
