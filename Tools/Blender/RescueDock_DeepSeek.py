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

MODEL_COLLECTION_NAME = "RescueDock_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_RescueDock_DeepSeek"

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
    # Reuse this asset's namespaced materials without deleting shared data.
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

mat_wood = create_material('RescueDock_DeepSeek_WoodDeck', (0.54, 0.39, 0.24, 1.0), 0.9)
mat_pile = create_material('RescueDock_DeepSeek_WoodPile', (0.20, 0.16, 0.12, 1.0), 0.95)
mat_iron = create_material('RescueDock_DeepSeek_Iron', (0.15, 0.16, 0.17, 1.0), 0.5, 0.75)
mat_orange = create_material('RescueDock_DeepSeek_RescueOrange', (0.76, 0.20, 0.08, 1.0), 0.62)
mat_teal = create_material('RescueDock_DeepSeek_TealTrim', (0.18, 0.34, 0.35, 1.0), 0.58)
mat_rope = create_material('RescueDock_DeepSeek_Rope', (0.58, 0.47, 0.33, 1.0), 0.95)
mat_cockpit = create_material('RescueDock_DeepSeek_Cockpit', (0.12, 0.16, 0.17, 1.0), 0.82)
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

# --- 4.1 Fixed piles, cross-beams, and open deck ---
# Six pile supports reach the waterline (Z=0); beams and decking sit above them.
pile_positions = [(-2.8, -1.8), (0.0, -1.8), (2.8, -1.8), (-2.8, 1.8), (0.0, 1.8), (2.8, 1.8)]
for i, (x, y) in enumerate(pile_positions):
    add_cylinder(f'Dock_Pile_{i}', 0.25, 1.8, (x, y, 0.9), mat_pile, model_col, verts=12)

for i, y in enumerate((-1.8, 0.0, 1.8)):
    add_box(f'Dock_CrossBeam_{i}', (6.0, 0.22, 0.25), (0.0, y, 1.57), mat_wood, model_col)
for side, x in [('Left', -2.75), ('Right', 2.75)]:
    add_box(f'Dock_LongBeam_{side}', (0.24, 3.7, 0.26), (x, 0.0, 1.57), mat_wood, model_col)

for i in range(12):
    plank_width = 4.2 / 12
    y = -2.1 + (i + 0.5) * plank_width
    add_box(f'Deck_Plank_{i}', (6.2, plank_width - 0.025, 0.08), (0.0, y, 1.68), mat_wood, model_col)

# --- 4.2 Mooring posts, iron caps, and cleats ---
corner_posts = [(-2.8, -1.8), (2.8, -1.8), (-2.8, 1.8), (2.8, 1.8)]
for i, (x, y) in enumerate(corner_posts):
    add_cylinder(f'MooringPost_{i}', 0.30, 2.2, (x, y, 1.1), mat_pile, model_col, verts=12)
    add_cylinder(f'MooringPost_Cap_{i}', 0.35, 0.15, (x, y, 2.25), mat_iron, model_col, verts=12)
    add_box(f'MooringPost_Cleat_{i}', (0.58, 0.14, 0.10), (x, y, 2.03), mat_iron, model_col)
    add_box(f'MooringPost_Cleat_Cross_{i}', (0.12, 0.38, 0.10), (x, y, 2.03), mat_iron, model_col)

# Heavy tie rings face toward the open water/boat side of the platform.
for i, (x, y) in enumerate(((-2.8, -1.8), (2.8, -1.8), (-2.8, 1.8), (2.8, 1.8))):
    outward_sign = -1 if y < 0 else 1
    ring_y = y + outward_sign * 0.27
    bpy.ops.mesh.primitive_torus_add(major_radius=0.09, minor_radius=0.025, location=(x, ring_y, 1.82), rotation=(math.radians(-90 if y > 0 else 90), 0.0, 0.0), major_segments=12, minor_segments=6)
    ring = bpy.context.active_object
    ring.name = f'Dock_TieRing_{i}'
    ring.data.materials.append(mat_iron)
    for collection in list(ring.users_collection):
        collection.objects.unlink(ring)
    model_col.objects.link(ring)
    apply_flat_shading(ring)

# --- 4.3 Boarding ladder on the front (-Y) edge ---
ladder_y = -2.20
for side, x in [('Left', -0.32), ('Right', 0.32)]:
    add_cylinder(f'Ladder_Rail_{side}', 0.055, 1.62, (x, ladder_y, 0.91), mat_wood_dark if 'mat_wood_dark' in globals() else mat_pile, model_col, verts=8)
for i, z in enumerate((0.20, 0.53, 0.86, 1.19, 1.52)):
    add_cylinder(f'Ladder_Rung_{i}', 0.045, 0.64, (0.0, ladder_y, z), mat_wood, model_col, rot=(0.0, math.radians(90), 0.0), verts=8)

# --- 4.4 Rescue life ring on the landward rear-left post ---
ring_post_x, ring_post_y = -2.1, 1.35
add_cylinder('LifeRing_Post', 0.07, 0.62, (ring_post_x, ring_post_y, 1.98), mat_wood, model_col, verts=8)
life_ring_y = ring_post_y
life_ring_z = 2.08
bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.065, location=(ring_post_x, life_ring_y, life_ring_z), rotation=(math.radians(90), 0.0, 0.0), major_segments=16, minor_segments=8)
life_ring = bpy.context.active_object
life_ring.name = 'LifeRing_Main'
life_ring.data.materials.append(mat_orange)
for collection in list(life_ring.users_collection):
    collection.objects.unlink(life_ring)
model_col.objects.link(life_ring)
apply_flat_shading(life_ring)
# Four small pale sections make the ring readable without text or labels.
for i, angle in enumerate((0.0, math.pi / 2, math.pi, 3 * math.pi / 2)):
    x = ring_post_x + math.cos(angle) * 0.25
    z = life_ring_z + math.sin(angle) * 0.25
    add_box(f'LifeRing_Segment_{i}', (0.16, 0.10, 0.08), (x, life_ring_y, z), mat_wood, model_col, rot=(0.0, 0.0, angle))

# --- 5.1 Separate rescue runabout hull; bow points +X, stern/outboard -X ---
boat_cx = 0.45
boat_cy = 2.95
# Each station has top port/starboard and lower port/starboard vertices.
boat_stations = [(-2.30, 0.42, 0.34), (-1.55, 0.69, 0.42), (0.70, 0.61, 0.39), (1.90, 0.39, 0.27), (2.30, 0.07, 0.05)]
boat_vertices = []
for x, top_half_width, bottom_half_width in boat_stations:
    world_x = boat_cx + x
    top_z = 0.88 if x < 1.8 else 0.76
    bottom_z = 0.24 if x < 1.8 else 0.48
    boat_vertices.extend([
        (world_x, boat_cy - top_half_width, top_z),
        (world_x, boat_cy + top_half_width, top_z),
        (world_x, boat_cy - bottom_half_width, bottom_z),
        (world_x, boat_cy + bottom_half_width, bottom_z),
    ])
boat_faces = []
for i in range(len(boat_stations) - 1):
    a = i * 4
    b = (i + 1) * 4
    boat_faces.extend([
        (a, b, b + 1, a + 1),
        (a, a + 2, b + 2, b),
        (a + 1, b + 1, b + 3, a + 3),
        (a + 2, a + 3, b + 3, b + 2),
    ])
boat_faces.extend([(0, 1, 3, 2), ((len(boat_stations)-1)*4, (len(boat_stations)-1)*4+2, (len(boat_stations)-1)*4+3, (len(boat_stations)-1)*4+1)])
boat_mesh = bpy.data.meshes.new('Boat_Hull_Mesh')
boat_mesh.from_pydata(boat_vertices, [], boat_faces)
boat_mesh.update()
boat_bm = bmesh.new()
boat_bm.from_mesh(boat_mesh)
bmesh.ops.recalc_face_normals(boat_bm, faces=boat_bm.faces)
boat_bm.to_mesh(boat_mesh)
boat_bm.free()
boat_hull = bpy.data.objects.new('Boat_Hull', boat_mesh)
model_col.objects.link(boat_hull)
boat_hull.data.materials.append(mat_orange)
apply_flat_shading(boat_hull)

# Gunwales and cockpit are separate parts sitting on the hull, not fused to the pier.
for side, y in [('Port', boat_cy - 0.61), ('Starboard', boat_cy + 0.61)]:
    add_box(f'Boat_Gunwale_{side}', (3.85, 0.08, 0.10), (boat_cx - 0.12, y, 0.91), mat_teal, model_col)
add_box('Boat_Cockpit_Well', (2.30, 0.88, 0.10), (boat_cx - 0.05, boat_cy, 0.94), mat_cockpit, model_col)
add_box('Boat_Seat_Aft', (0.52, 0.72, 0.16), (boat_cx - 0.72, boat_cy, 1.06), mat_teal, model_col)
add_box('Boat_Seat_Fore', (0.52, 0.72, 0.16), (boat_cx + 0.20, boat_cy, 1.06), mat_teal, model_col)
add_box('Boat_Console', (0.32, 0.60, 0.44), (boat_cx + 0.95, boat_cy, 1.16), mat_cockpit, model_col)
add_box('Boat_Windshield', (0.06, 0.90, 0.32), (boat_cx + 1.30, boat_cy, 1.31), mat_teal, model_col, rot=(0.0, math.radians(-12), 0.0))
add_cylinder('Boat_SteeringWheel', 0.13, 0.045, (boat_cx + 0.95, boat_cy - 0.34, 1.42), mat_iron, model_col, rot=(math.radians(90), 0.0, 0.0), verts=12)

# Compact outboard at the -X transom.
motor_x = boat_cx - 2.36
add_box('Boat_Motor_Mount', (0.20, 0.32, 0.28), (motor_x, boat_cy, 0.78), mat_iron, model_col)
add_box('Boat_Motor_Cowl', (0.42, 0.34, 0.40), (motor_x - 0.12, boat_cy, 1.00), mat_iron, model_col)
add_cylinder('Boat_Motor_Leg', 0.075, 0.66, (motor_x - 0.12, boat_cy, 0.48), mat_iron, model_col, verts=8)
add_box('Boat_Motor_Skeg', (0.38, 0.10, 0.08), (motor_x - 0.12, boat_cy, 0.15), mat_iron, model_col)

# Boat cleats and two taut lines to the outer (+Y) dock posts.
boat_cleat_a = (boat_cx - 1.45, boat_cy - 0.67, 0.98)
boat_cleat_b = (boat_cx + 1.55, boat_cy - 0.60, 0.98)
for i, (x, y, z) in enumerate((boat_cleat_a, boat_cleat_b)):
    add_box(f'Boat_Cleat_{i}', (0.20, 0.08, 0.08), (x, y, z), mat_iron, model_col)
# Lines leave the outer face above the deck edge so they do not cut through planks or beams.
add_rope('MooringLine_Bow', (2.8, 2.20, 1.82), boat_cleat_b, 0.032, mat_rope, model_col)
add_rope('MooringLine_Stern', (-2.8, 2.20, 1.82), boat_cleat_a, 0.032, mat_rope, model_col)
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
    print("\n--- Rescue Dock Diagnostic Report ---")
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

render_world = bpy.data.worlds.new(f"RescueDock_DeepSeek_RenderWorld_{len(bpy.data.worlds)}")
render_world.use_nodes = True
background = next((node for node in render_world.node_tree.nodes if node.type == 'BACKGROUND'), None)
if background:
    background.inputs['Color'].default_value = (0.9, 0.9, 0.9, 1.0)
    background.inputs['Strength'].default_value = 0.8
scene.world = render_world

bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.name = "RescueDock_DeepSeek_Sun"
sun.data.energy = 2.0
sun.rotation_euler = (math.radians(35), math.radians(20), math.radians(25))
for collection in list(sun.users_collection):
    collection.objects.unlink(sun)
helper_col.objects.link(sun)

bpy.ops.object.light_add(type='AREA', location=(-4, -6, 6))
area = bpy.context.active_object
area.name = "RescueDock_DeepSeek_Area"
area.data.energy = 450
area.data.shape = 'DISK'
area.data.size = 7
area.rotation_euler = (math.radians(35), 0.0, math.radians(-35))
for collection in list(area.users_collection):
    collection.objects.unlink(area)
helper_col.objects.link(area)

bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.name = "RescueDock_DeepSeek_Camera"
cam.data.type = 'ORTHO'
for collection in list(cam.users_collection):
    collection.objects.unlink(cam)
helper_col.objects.link(cam)
scene.camera = cam

render_center = Vector((0.0, 0.80, 1.20))
def render_view(offset, rotation, ortho_scale, filename):
    cam.location = render_center + Vector(offset)
    cam.rotation_euler = rotation
    cam.data.ortho_scale = ortho_scale
    scene.render.filepath = str(QA_DIR / filename)
    bpy.ops.render.render(write_still=True)

render_view((0, -20, 0), (math.radians(90), 0, 0), 7.5, "RescueDock_DeepSeek_Front.png")
render_view((0, 20, 0), (math.radians(90), 0, math.radians(180)), 7.5, "RescueDock_DeepSeek_Back.png")
render_view((-20, 0, 0), (math.radians(90), 0, math.radians(-90)), 7.5, "RescueDock_DeepSeek_Left.png")
render_view((20, 0, 0), (math.radians(90), 0, math.radians(90)), 7.5, "RescueDock_DeepSeek_Right.png")
render_view((0, 0, 20), (0, 0, 0), 7.5, "RescueDock_DeepSeek_Top.png")
render_view((0, 0, -20), (math.radians(180), 0, 0), 7.5, "RescueDock_DeepSeek_Bottom.png")

cam.location = (8, 12, 9)
look_target = Vector((0, 0.85, 1.15))
cam.rotation_euler = (look_target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 9.0
scene.render.filepath = str(PREVIEW_DIR / "RescueDock_DeepSeek.png")
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

fbx_path = FBX_DIR / "RescueDock_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True,
)

blend_path = BLEND_DIR / "RescueDock_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
calculate_bounds_and_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved preview to: {PREVIEW_DIR / 'RescueDock_DeepSeek.png'}")
print(f"Saved QA renders to: {QA_DIR}")

