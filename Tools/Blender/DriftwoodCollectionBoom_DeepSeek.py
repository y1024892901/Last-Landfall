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

for d in [BLEND_DIR, FBX_DIR, PREVIEW_DIR, QA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MODEL_COLLECTION_NAME = "DriftwoodCollectionBoom_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_DriftwoodCollectionBoom"

# When Blender starts without a project file, remove only its three stock
# startup objects. If a .blend is opened before running this script, preserve
# every existing scene object.
if not bpy.data.filepath:
    for startup_name in ("Cube", "Camera", "Light"):
        startup_obj = bpy.data.objects.get(startup_name)
        if startup_obj:
            bpy.data.objects.remove(startup_obj, do_unlink=True)

# Cleanup previous runs (idempotent)
for col_name in [MODEL_COLLECTION_NAME, HELPER_COLLECTION_NAME]:
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

# Create fresh collections
model_col = bpy.data.collections.new(MODEL_COLLECTION_NAME)
bpy.context.scene.collection.children.link(model_col)

helper_col = bpy.data.collections.new(HELPER_COLLECTION_NAME)
bpy.context.scene.collection.children.link(helper_col)

# ==========================================
# 2. Material Creation
# ==========================================
def create_material(name, base_color, roughness=0.8, metallic=0.0):
    # Reuse only this script's explicitly namespaced materials. Never remove
    # or replace a material belonging to another asset in the project.
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default nodes to avoid localized naming issues
    for node in list(nodes):
        nodes.remove(node)
        
    out_node = nodes.new('ShaderNodeOutputMaterial')
    bsdf_node = nodes.new('ShaderNodeBsdfPrincipled')
    
    bsdf_node.inputs['Base Color'].default_value = base_color
    bsdf_node.inputs['Roughness'].default_value = roughness
    bsdf_node.inputs['Metallic'].default_value = metallic
    
    links.new(bsdf_node.outputs['BSDF'], out_node.inputs['Surface'])
    return mat

mat_teal = create_material("Driftwood_DeepSeek_SeaGlassTeal", (0.2, 0.45, 0.45, 1.0), roughness=0.6, metallic=0.1)
mat_wood = create_material("Driftwood_DeepSeek_DriftwoodBrown", (0.45, 0.35, 0.25, 1.0), roughness=0.9, metallic=0.0)
mat_iron = create_material("Driftwood_DeepSeek_IronFitting", (0.12, 0.12, 0.15, 1.0), roughness=0.5, metallic=0.8)
mat_rope = create_material("Driftwood_DeepSeek_RopeNatural", (0.65, 0.55, 0.4, 1.0), roughness=0.95, metallic=0.0)
mat_weight = create_material("Driftwood_DeepSeek_MooringWeight", (0.2, 0.22, 0.25, 1.0), roughness=0.8, metallic=0.2)

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

def add_cylinder(name, radius, depth, location, mat, parent_col, rot=(0,0,0), verts=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=location, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    parent_col.objects.link(obj)
    apply_flat_shading(obj)
    return obj

def add_rope(name, start, end, radius, mat, parent_col, verts=6):
    start_v = Vector(start)
    end_v = Vector(end)
    mid = (start_v + end_v) / 2
    length = (end_v - start_v).length
    if length == 0:
        return None
    
    direction = end_v - start_v
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=length, location=mid)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = direction.to_track_quat('Z', 'Y')
    obj.data.materials.append(mat)
    
    for c in obj.users_collection:
        c.objects.unlink(obj)
    parent_col.objects.link(obj)
    apply_flat_shading(obj)
    return obj

def get_arc_pos(t, y_offset=0.0, z_offset=0.0):
    """Generates positions along the crescent arc."""
    R = 6.9
    max_angle = math.radians(34.8)
    angle = t * max_angle
    x = R * math.sin(angle)
    y = -R * (1 - math.cos(angle)) + y_offset
    return Vector((x, y, z_offset))

# ==========================================
# 4. Modeling - Main Boom Structure
# ==========================================

# --- 4.1 Teal Float Pods ---
# 6 evenly spaced pods along the arc
t_vals = [-0.85, -0.51, -0.17, 0.17, 0.51, 0.85]
for i, t in enumerate(t_vals):
    pos = get_arc_pos(t, z_offset=0.3)
    # Main pod
    add_cylinder(f"Float_Pod_{i}", 0.35, 0.6, pos, mat_teal, model_col, verts=12)
    # Top cap detail
    add_cylinder(f"Float_Pod_{i}_Cap", 0.2, 0.05, pos + Vector((0,0,0.3)), mat_iron, model_col, verts=8)

    # A short wooden saddle bridges each float to both parallel boom logs.
    # Its slight overlap at the contact faces makes the support read as joined.
    saddle = get_arc_pos(t, z_offset=0.61)
    add_box(f"Float_Saddle_{i}", (0.14, 0.62, 0.06), saddle, mat_wood, model_col)

# --- 4.2 Wooden Barrier Logs ---
# Create curves segmented by straight logs
num_segments = 12
log_points_front = []
log_points_back = []

for i in range(num_segments + 1):
    t = (i / num_segments) * 2.0 - 1.0
    # Offset Y to create two parallel logs
    p_front = get_arc_pos(t, y_offset=-0.25, z_offset=0.75)
    p_back = get_arc_pos(t, y_offset=0.25, z_offset=0.75)
    log_points_front.append(p_front)
    log_points_back.append(p_back)

# Generate log segments
for i in range(num_segments):
    # Front log
    add_rope(f"Log_Front_{i}", log_points_front[i], log_points_front[i+1], 0.12, mat_wood, model_col, verts=8)
    # Back log
    add_rope(f"Log_Back_{i}", log_points_back[i], log_points_back[i+1], 0.12, mat_wood, model_col, verts=8)
    
    # Iron Straps / Hinges at joints
    mid_front = (log_points_front[i] + log_points_front[i+1]) / 2
    mid_back = (log_points_back[i] + log_points_back[i+1]) / 2
    
    # Calculate direction for straps
    dir_front = (log_points_front[i+1] - log_points_front[i]).normalized()
    rot_front = dir_front.to_track_quat('Z', 'Y').to_euler()
    
    dir_back = (log_points_back[i+1] - log_points_back[i]).normalized()
    rot_back = dir_back.to_track_quat('Z', 'Y').to_euler()
    
    if i % 2 == 0: # Place every other segment to look practical
        add_cylinder(f"Strap_Front_{i}", 0.14, 0.08, mid_front, mat_iron, model_col, rot=rot_front, verts=8)
        add_cylinder(f"Strap_Back_{i}", 0.14, 0.08, mid_back, mat_iron, model_col, rot=rot_back, verts=8)

# --- 4.3 Collection Pocket ---
# Located at the inner front center (t=0)
pocket_center = get_arc_pos(0, y_offset=-0.5, z_offset=0.4)
# Horizontal frame
add_box("Pocket_Base", (1.0, 0.1, 0.1), pocket_center + Vector((0, 0, -0.2)), mat_wood, model_col)
add_box("Pocket_Top", (1.0, 0.1, 0.1), pocket_center + Vector((0, 0, 0.2)), mat_wood, model_col)

# Vertical slats
for i in range(7):
    x_offset = (i - 3) * 0.15
    add_box(f"Pocket_Slat_{i}", (0.05, 0.05, 0.5), pocket_center + Vector((x_offset, 0, 0)), mat_wood, model_col)

# Attach to main logs
add_rope("Pocket_Mount_L", pocket_center + Vector((-0.5, 0, 0.2)), get_arc_pos(-0.22, y_offset=-0.25, z_offset=0.75), 0.05, mat_rope, model_col)
add_rope("Pocket_Mount_R", pocket_center + Vector((0.5, 0, 0.2)), get_arc_pos(0.22, y_offset=-0.25, z_offset=0.75), 0.05, mat_rope, model_col)

# --- 4.4 Rope Rails & Lashings ---
# Vertical posts along the back log
for i in range(1, num_segments, 2):
    post_pos = log_points_back[i] + Vector((0, 0, 0.15))
    add_cylinder(f"Rail_Post_{i}", 0.03, 0.3, post_pos, mat_wood, model_col, verts=6)
    
# Continuous rope threading through the posts
for i in range(0, len(log_points_back) - 1, 2):
    if i + 1 < len(log_points_back):
        p1 = log_points_back[i] + Vector((0, 0, 0.25))
        p2 = log_points_back[i+1] + Vector((0, 0, 0.25))
        add_rope(f"Rail_Rope_{i}", p1, p2, 0.015, mat_rope, model_col)

# --- 4.5 Mooring Lines and Weights ---
# Outer ends
left_end = log_points_front[0]
right_end = log_points_front[-1]

# Weights (Hexagonal flat stones/iron)
weight_L_pos = left_end + Vector((0.25, -0.45, -0.7)) # Weight centers remain inside the 8.2 m envelope.
weight_R_pos = right_end + Vector((-0.25, -0.45, -0.7))

add_cylinder("Mooring_Weight_L", 0.3, 0.1, Vector((weight_L_pos.x, weight_L_pos.y, 0.05)), mat_weight, model_col, verts=6)
add_cylinder("Mooring_Weight_R", 0.3, 0.1, Vector((weight_R_pos.x, weight_R_pos.y, 0.05)), mat_weight, model_col, verts=6)

# Mooring Ropes (Taut)
add_rope("Mooring_Rope_L", left_end + Vector((0,0,0.1)), Vector((weight_L_pos.x, weight_L_pos.y, 0.1)), 0.04, mat_rope, model_col)
add_rope("Mooring_Rope_R", right_end + Vector((0,0,0.1)), Vector((weight_R_pos.x, weight_R_pos.y, 0.1)), 0.04, mat_rope, model_col)

# Bindings at ends
add_cylinder("End_Binding_L", 0.15, 0.2, left_end, mat_iron, model_col, verts=8)
add_cylinder("End_Binding_R", 0.15, 0.2, right_end, mat_iron, model_col, verts=8)

# ==========================================
# 5. Quality Diagnostic Setup
# ==========================================
def calculate_bounds_and_diagnostics():
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
    
    mesh_objects = [obj for obj in model_col.objects if obj.type == 'MESH']
    non_manifold_count = 0
    
    for obj in mesh_objects:
        # World Bounds
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ Vector(corner)
            min_x = min(min_x, world_corner.x)
            min_y = min(min_y, world_corner.y)
            min_z = min(min_z, world_corner.z)
            max_x = max(max_x, world_corner.x)
            max_y = max(max_y, world_corner.y)
            max_z = max(max_z, world_corner.z)
            
        # Non-manifold check
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

# Keep other scene content intact, but exclude it from these isolated model
# renders so a pre-existing cube or set dressing cannot contaminate QA images.
model_and_helpers = set(model_col.objects) | set(helper_col.objects)
external_render_state = {
    obj: obj.hide_render for obj in scene.objects if obj not in model_and_helpers
}
for obj in external_render_state:
    obj.hide_render = True

# Render Engine
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        pass # Fallback to default

scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'

# World Background (Pale neutral)
world = bpy.data.worlds.get("World")
if not world:
    world = bpy.data.worlds.new("World")
    scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.9, 0.9, 0.9, 1.0)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), math.radians(20), math.radians(30))
for c in sun.users_collection:
    c.objects.unlink(sun)
helper_col.objects.link(sun)

bpy.ops.object.light_add(type='AREA', location=(-4, -6, 5))
area = bpy.context.active_object
area.data.energy = 500
area.data.size = 8
area.rotation_euler = (math.radians(60), 0, math.radians(-45))
for c in area.users_collection:
    c.objects.unlink(area)
helper_col.objects.link(area)

# Camera
bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 9.5 # Fit 8.2m wide asset
for c in cam.users_collection:
    c.objects.unlink(cam)
helper_col.objects.link(cam)
scene.camera = cam

# Render Views
def render_view(offset, rot, filename, ortho_scale=9.5):
    # Center the asset using the middle of its measured depth and height.
    target = Vector((0.0, -0.98, 0.52))
    cam.location = target + Vector(offset)
    cam.rotation_euler = rot
    cam.data.ortho_scale = ortho_scale
    scene.render.filepath = str(QA_DIR / filename)
    bpy.ops.render.render(write_still=True)

# QA Views
render_view((0, -20, 0), (math.radians(90), 0, 0), "DriftwoodCollectionBoom_DeepSeek_Front.png")
render_view((0, 20, 0), (math.radians(90), 0, math.radians(180)), "DriftwoodCollectionBoom_DeepSeek_Back.png")
render_view((-20, 0, 0), (math.radians(90), 0, math.radians(-90)), "DriftwoodCollectionBoom_DeepSeek_Left.png", ortho_scale=3.4)
render_view((20, 0, 0), (math.radians(90), 0, math.radians(90)), "DriftwoodCollectionBoom_DeepSeek_Right.png", ortho_scale=3.4)
render_view((0, 0, 20), (0, 0, 0), "DriftwoodCollectionBoom_DeepSeek_Top.png")
render_view((0, 0, -20), (math.radians(180), 0, 0), "DriftwoodCollectionBoom_DeepSeek_Bottom.png")

# 3/4 Preview
# Position camera, point at center
cam.location = (10, -12, 8)
cam.data.ortho_scale = 8.8
look_target = Vector((0, -0.5, 0.4))
direction = look_target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = str(PREVIEW_DIR / "DriftwoodCollectionBoom_DeepSeek.png")
bpy.ops.render.render(write_still=True)

# Restore original render visibility before saving the editable scene.
for obj, was_hidden in external_render_state.items():
    obj.hide_render = was_hidden

# ==========================================
# 7. Export FBX & Save Blend
# ==========================================
# Select only model collection objects
bpy.ops.object.select_all(action='DESELECT')
for obj in model_col.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

fbx_path = FBX_DIR / "DriftwoodCollectionBoom_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True
)

# Save Blend
blend_path = BLEND_DIR / "DriftwoodCollectionBoom_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# ==========================================
# 8. Execute Diagnostics
# ==========================================
calculate_bounds_and_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved Previews to: {PREVIEW_DIR}")
print(f"Saved QA Renders to: {QA_DIR}")
