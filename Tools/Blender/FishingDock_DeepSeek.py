import bpy
import bmesh
import math
from mathutils import Vector
from pathlib import Path

# ==========================================
# 1. Setup and Path Management
# ==========================================
PROJECT_ROOT = Path.cwd()
BLEND_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Infrastructure"
FBX_DIR = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Infrastructure"
PREVIEW_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Previews/Infrastructure"
QA_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"

for directory in [BLEND_DIR, FBX_DIR, PREVIEW_DIR, QA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

MODEL_COLLECTION_NAME = "FishingDock_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_FishingDock_DeepSeek"

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
    # Materials are uniquely namespaced to this asset. Reuse its own material
    # on reruns instead of deleting data that may belong to another asset.
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = base_color
    principled.inputs['Roughness'].default_value = roughness
    principled.inputs['Metallic'].default_value = metallic
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    return mat

mat_wood = create_material("FishingDock_DeepSeek_Cedar", (0.45, 0.33, 0.22, 1.0), roughness=0.9)
mat_teal = create_material("FishingDock_DeepSeek_SeaGlass", (0.22, 0.45, 0.45, 1.0), roughness=0.6, metallic=0.1)
mat_iron = create_material("FishingDock_DeepSeek_Iron", (0.12, 0.12, 0.14, 1.0), roughness=0.5, metallic=0.8)
mat_rope = create_material("FishingDock_DeepSeek_Rope", (0.65, 0.55, 0.4, 1.0), roughness=0.95)
mat_net = create_material("FishingDock_DeepSeek_Net", (0.55, 0.48, 0.35, 1.0), roughness=0.95)

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

# --- 4.1 Four flotation drums ---
# Drums run along X and form two separated rows; center height makes each
# drum contact the supporting joists without extending below the waterline.
float_positions = [
    (-1.8, -0.6, 0.4),
    (1.8, -0.6, 0.4),
    (-1.8, 0.6, 0.4),
    (1.8, 0.6, 0.4),
]
for index, position in enumerate(float_positions):
    x, y, z = position
    drum_rotation = (0.0, math.radians(90), 0.0)
    add_cylinder(f"Float_Drum_{index}", 0.4, 1.8, position, mat_teal, model_col, rot=drum_rotation, verts=12)
    # Two dark straps encircle each drum along its long X axis.
    for strap_index, strap_x in enumerate((x - 0.6, x + 0.6)):
        add_cylinder(
            f"Float_Strap_{index}_{strap_index}", 0.42, 0.08,
            (strap_x, y, z + 0.02), mat_iron, model_col,
            rot=drum_rotation, verts=12
        )

# --- 4.2 Cross joists beneath the deck ---
joist_positions = [-2.2, -1.1, 0.0, 1.1, 2.2]
for index, x in enumerate(joist_positions):
    add_box(f"Joist_{index}", (0.15, 2.5, 0.2), (x, 0.0, 0.85), mat_wood, model_col)

# --- 4.3 Open deck planks ---
num_planks = 8
plank_width = 2.6 / num_planks
for index in range(num_planks):
    y = -1.3 + (index + 0.5) * plank_width
    add_box(
        f"Deck_Plank_{index}",
        (5.2, plank_width - 0.02, 0.1),
        (0.0, y, 1.0), mat_wood, model_col
    )

# --- 4.4 Corner bollards ---
bollard_positions = [(-2.4, -1.2), (2.4, -1.2), (-2.4, 1.2), (2.4, 1.2)]
for index, (x, y) in enumerate(bollard_positions):
    add_box(f"Bollard_{index}", (0.35, 0.35, 1.2), (x, y, 1.5), mat_wood, model_col)
    add_box(f"Bollard_Cap_{index}", (0.4, 0.4, 0.1), (x, y, 2.1), mat_iron, model_col)
    add_cylinder(f"Bollard_Rope_{index}", 0.22, 0.15, (x, y, 1.15), mat_rope, model_col, verts=8)

# --- 4.5 Landward access gangway ---
ramp_width = 1.2
ramp_run = 1.7
ramp_drop = 0.95
ramp_angle = math.atan2(ramp_drop, ramp_run)
ramp_length = math.sqrt(ramp_run ** 2 + ramp_drop ** 2)
ramp_center_y = -1.3 - ramp_run / 2
ramp_center_z = 1.0 - ramp_drop / 2
ramp_rotation = (ramp_angle, 0.0, 0.0)
add_box(
    "Ramp_Base", (ramp_width, ramp_length, 0.1),
    (0.0, ramp_center_y, ramp_center_z), mat_wood, model_col, rot=ramp_rotation
)
for side in (-1, 1):
    x_offset = side * (ramp_width / 2 - 0.05)
    add_box(
        f"Ramp_Rail_{side}", (0.1, ramp_length, 0.15),
        (x_offset, ramp_center_y, ramp_center_z + 0.1),
        mat_wood, model_col, rot=ramp_rotation
    )
for index in range(5):
    t = index / 4
    y = -1.3 - t * ramp_run
    z = 1.0 - t * ramp_drop + 0.05
    add_box(
        f"Ramp_Tread_{index}", (ramp_width, 0.1, 0.05),
        (0.0, y, z), mat_wood, model_col, rot=ramp_rotation
    )

# --- 4.6 Side-mounted net-drying rack ---
rack_x = -2.0
rack_y = 0.5
add_box("Rack_Post_1", (0.1, 0.1, 1.2), (rack_x, rack_y - 0.6, 1.6), mat_wood, model_col)
add_box("Rack_Post_2", (0.1, 0.1, 1.2), (rack_x, rack_y + 0.6, 1.6), mat_wood, model_col)
add_box("Rack_TopBar", (0.1, 1.4, 0.1), (rack_x, rack_y, 2.15), mat_wood, model_col)
# Net lies in the Y-Z plane between the two posts: three horizontal and five vertical strands.
for index, z in enumerate((1.35, 1.60, 1.85)):
    add_cylinder(
        f"Net_String_H_{index}", 0.01, 1.0,
        (rack_x, rack_y, z), mat_net, model_col,
        rot=(math.radians(90), 0.0, 0.0), verts=4
    )
for index in range(5):
    y = rack_y - 0.5 + index * 0.25
    add_cylinder(
        f"Net_String_V_{index}", 0.01, 0.8,
        (rack_x, y, 1.6), mat_net, model_col, verts=4
    )

# --- 4.7 Closed bait and catch crate ---
crate_x = 1.8
crate_y = 0.7
add_box("Crate_Base", (0.6, 0.5, 0.4), (crate_x, crate_y, 1.2), mat_wood, model_col)
for index in range(3):
    z = 1.05 + index * 0.15
    add_box(f"Crate_Slat_Front_{index}", (0.6, 0.05, 0.08), (crate_x, crate_y - 0.25, z), mat_wood, model_col)
    add_box(f"Crate_Slat_Back_{index}", (0.6, 0.05, 0.08), (crate_x, crate_y + 0.25, z), mat_wood, model_col)
add_box("Crate_Lid", (0.62, 0.52, 0.05), (crate_x, crate_y, 1.42), mat_wood, model_col)

# --- 4.8 Coiled hand line and short tied end ---
coil_x, coil_y = 1.8, -0.8
for index in range(3):
    add_cylinder(
        f"Rope_Coil_{index}", 0.25 - index * 0.02, 0.08,
        (coil_x, coil_y, 1.1 + index * 0.08), mat_rope, model_col, verts=12
    )
add_rope(
    "Rope_Coil_End",
    (coil_x + 0.2, coil_y - 0.2, 1.1),
    (coil_x + 0.4, coil_y - 0.5, 1.05),
    0.03, mat_rope, model_col
)

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
    print("\n--- Fishing Dock Diagnostic Report ---")
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
external_render_state = {
    obj: obj.hide_render
    for obj in scene.objects
    if obj not in set(model_col.objects) and obj not in set(helper_col.objects)
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

render_world = bpy.data.worlds.new(f"FishingDock_DeepSeek_RenderWorld_{len(bpy.data.worlds)}")
render_world.use_nodes = True
background = next((node for node in render_world.node_tree.nodes if node.type == 'BACKGROUND'), None)
if background:
    background.inputs['Color'].default_value = (0.9, 0.9, 0.9, 1.0)
    background.inputs['Strength'].default_value = 0.8
scene.world = render_world

bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.name = "FishingDock_DeepSeek_Sun"
sun.data.energy = 2.0
sun.rotation_euler = (math.radians(35), math.radians(20), math.radians(25))
for collection in list(sun.users_collection):
    collection.objects.unlink(sun)
helper_col.objects.link(sun)

bpy.ops.object.light_add(type='AREA', location=(-4, -6, 6))
area = bpy.context.active_object
area.name = "FishingDock_DeepSeek_Area"
area.data.energy = 450
area.data.shape = 'DISK'
area.data.size = 7
area.rotation_euler = (math.radians(35), 0.0, math.radians(-35))
for collection in list(area.users_collection):
    collection.objects.unlink(area)
helper_col.objects.link(area)

bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.name = "FishingDock_DeepSeek_Camera"
cam.data.type = 'ORTHO'
for collection in list(cam.users_collection):
    collection.objects.unlink(cam)
helper_col.objects.link(cam)
scene.camera = cam

render_center = Vector((0.0, -0.75, 1.125))
def render_view(offset, rotation, ortho_scale, filename):
    cam.location = render_center + Vector(offset)
    cam.rotation_euler = rotation
    cam.data.ortho_scale = ortho_scale
    scene.render.filepath = str(QA_DIR / filename)
    bpy.ops.render.render(write_still=True)

render_view((0, -20, 0), (math.radians(90), 0, 0), 6.5, "FishingDock_DeepSeek_Front.png")
render_view((0, 20, 0), (math.radians(90), 0, math.radians(180)), 6.5, "FishingDock_DeepSeek_Back.png")
render_view((-20, 0, 0), (math.radians(90), 0, math.radians(-90)), 5.0, "FishingDock_DeepSeek_Left.png")
render_view((20, 0, 0), (math.radians(90), 0, math.radians(90)), 5.0, "FishingDock_DeepSeek_Right.png")
render_view((0, 0, 20), (0, 0, 0), 6.5, "FishingDock_DeepSeek_Top.png")
render_view((0, 0, -20), (math.radians(180), 0, 0), 6.5, "FishingDock_DeepSeek_Bottom.png")

cam.location = (8, -10, 8)
look_target = Vector((0, -0.75, 1.1))
cam.rotation_euler = (look_target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 7.0
scene.render.filepath = str(PREVIEW_DIR / "FishingDock_DeepSeek.png")
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

fbx_path = FBX_DIR / "FishingDock_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True,
)

blend_path = BLEND_DIR / "FishingDock_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
calculate_bounds_and_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved preview to: {PREVIEW_DIR / 'FishingDock_DeepSeek.png'}")
print(f"Saved QA renders to: {QA_DIR}")
