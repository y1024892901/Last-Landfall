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

MODEL_COLLECTION_NAME = "Shipyard_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_Shipyard_DeepSeek"
MATERIAL_PREFIX = "Shipyard_DeepSeek_"

scene = bpy.context.scene
original_scene_state = {
    "camera": scene.camera,
    "world": scene.world,
    "engine": scene.render.engine,
    "resolution_x": scene.render.resolution_x,
    "resolution_y": scene.render.resolution_y,
    "resolution_percentage": scene.render.resolution_percentage,
    "filepath": scene.render.filepath,
    "film_transparent": scene.render.film_transparent,
    "file_format": scene.render.image_settings.file_format,
    "color_mode": scene.render.image_settings.color_mode,
    "view_transform": scene.view_settings.view_transform,
    "look": scene.view_settings.look,
    "exposure": scene.view_settings.exposure,
    "gamma": scene.view_settings.gamma,
}

# Clean up previous runs (idempotent)
for col_name in [MODEL_COLLECTION_NAME, HELPER_COLLECTION_NAME]:
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

# Clean up specific materials with prefix that have no users
for mat in list(bpy.data.materials):
    if mat.name.startswith(MATERIAL_PREFIX) and mat.users == 0:
        bpy.data.materials.remove(mat)

# Create new collections
model_col = bpy.data.collections.new(MODEL_COLLECTION_NAME)
bpy.context.scene.collection.children.link(model_col)

helper_col = bpy.data.collections.new(HELPER_COLLECTION_NAME)
bpy.context.scene.collection.children.link(helper_col)

# ==========================================
# 2. Material Creation
# ==========================================
def create_material(name, base_color, roughness=0.8, metallic=0.0, alpha=1.0):
    mat_name = f"{MATERIAL_PREFIX}{name}"
    mat = bpy.data.materials.get(mat_name)
    if mat and mat.users > 0:
        return mat
    if not mat:
        mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default nodes to avoid localization issues
    for node in list(nodes):
        nodes.remove(node)
        
    # Find by bl_idname to avoid localized node names
    out_node = next((n for n in nodes if n.bl_idname == 'ShaderNodeOutputMaterial'), None)
    if not out_node:
        out_node = nodes.new('ShaderNodeOutputMaterial')
        
    bsdf_node = next((n for n in nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'), None)
    if not bsdf_node:
        bsdf_node = nodes.new('ShaderNodeBsdfPrincipled')
    
    bsdf_node.inputs['Base Color'].default_value = base_color
    bsdf_node.inputs['Roughness'].default_value = roughness
    bsdf_node.inputs['Metallic'].default_value = metallic
    bsdf_node.inputs['Alpha'].default_value = alpha
    
    links.new(bsdf_node.outputs['BSDF'], out_node.inputs['Surface'])
    
    if alpha < 1.0:
        mat.blend_method = 'BLEND'
        
    return mat

# Colors based on reference descriptions
mat_wood_light = create_material("WeatheringLightWood", (0.55, 0.45, 0.35, 1.0), roughness=0.9)
mat_wood_dark = create_material("TarDarkWood", (0.2, 0.15, 0.12, 1.0), roughness=0.9)
mat_metal_green = create_material("SeaGreenMetal", (0.25, 0.45, 0.45, 1.0), roughness=0.5, metallic=0.4)
mat_concrete = create_material("WarmGrayConcrete", (0.6, 0.6, 0.58, 1.0), roughness=0.95)
mat_iron = create_material("DarkIron", (0.12, 0.12, 0.14, 1.0), roughness=0.5, metallic=0.8)
mat_rust = create_material("RustOrange", (0.65, 0.25, 0.1, 1.0), roughness=0.8, metallic=0.2)
mat_cyan = create_material("LightCyanMetal", (0.6, 0.8, 0.8, 1.0), roughness=0.6, metallic=0.3)
mat_amber = create_material("AmberLight", (0.9, 0.5, 0.1, 1.0), roughness=0.2, metallic=0.0)

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

def add_pipe(name, start, end, radius, mat, parent_col, verts=8):
    start_v = Vector(start)
    end_v = Vector(end)
    mid = (start_v + end_v) / 2
    length = (end_v - start_v).length
    if length < 0.001:
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

# ==========================================
# 4. Modeling Components
# ==========================================

# --- 4.1 Foundation & Slipway ---
# 6 Concrete Footings
for x in [-2.0, 0, 2.0]:
    for y in [-0.6, 0.6]:
        add_box(f"Foundation_Footing_{x}_{y}", (0.4, 0.4, 0.3), (x, y, 0.15), mat_concrete, model_col)

# 2 Long Rails (along X)
add_box("Slipway_Rail_Left", (4.6, 0.2, 0.2), (0, -0.6, 0.4), mat_wood_dark, model_col)
add_box("Slipway_Rail_Right", (4.6, 0.2, 0.2), (0, 0.6, 0.4), mat_wood_dark, model_col)

# 5 Cross Sleepers
for x in [-1.8, -0.9, 0, 0.9, 1.8]:
    add_box(f"Slipway_Sleeper_{x}", (0.15, 1.6, 0.15), (x, 0, 0.55), mat_wood_light, model_col)

# Boat Cradle Blocks (supporting the hull)
for x in [-1.4, 0, 1.4]:
    for y in [-0.4, 0.4]:
        add_box(f"Cradle_Block_{x}_{y}", (0.2, 0.2, 0.2), (x, y, 0.7), mat_wood_dark, model_col)

# --- 4.2 Unfinished Rescue Boat Hull ---
# Length 3.4m, Width 1.2m. Z from 0.8 to 1.6.
# Making an open frame structure to look unfinished.
hull_z_base = 0.8
hull_z_top = 1.4

# Central Keel
add_box("Hull_Keel", (3.4, 0.1, 0.1), (0, 0, hull_z_base), mat_wood_light, model_col)

# Ribs (Cross frames)
# Simple U-shapes built from boxes
for i, x in enumerate([-1.4, -0.7, 0, 0.7, 1.4]):
    # Bottom plate
    add_box(f"Hull_Rib_Bot_{i}", (0.1, 0.8, 0.05), (x, 0, hull_z_base + 0.05), mat_wood_light, model_col)
    # Side plates (angled)
    add_box(f"Hull_Rib_L_{i}", (0.1, 0.05, 0.5), (x, -0.4, hull_z_base + 0.25), mat_wood_light, model_col, rot=(math.radians(-15), 0, 0))
    add_box(f"Hull_Rib_R_{i}", (0.1, 0.05, 0.5), (x, 0.4, hull_z_base + 0.25), mat_wood_light, model_col, rot=(math.radians(15), 0, 0))

# Longitudinal Stringers (Side planks)
# Only partially planked to show "under construction"
# Lower strake
add_box("Hull_Stringer_L_Low", (3.2, 0.02, 0.2), (0, -0.45, hull_z_base + 0.15), mat_wood_light, model_col, rot=(math.radians(-15), 0, 0))
add_box("Hull_Stringer_R_Low", (3.2, 0.02, 0.2), (0, 0.45, hull_z_base + 0.15), mat_wood_light, model_col, rot=(math.radians(15), 0, 0))
# Upper strake (partial)
add_box("Hull_Stringer_L_High", (1.5, 0.02, 0.2), (-0.8, -0.55, hull_z_base + 0.45), mat_wood_light, model_col, rot=(math.radians(-15), 0, 0))
add_box("Hull_Stringer_R_High", (1.5, 0.02, 0.2), (-0.8, 0.55, hull_z_base + 0.45), mat_wood_light, model_col, rot=(math.radians(15), 0, 0))

# Gunwale (Top edge)
add_box("Hull_Gunwale_L", (3.4, 0.05, 0.05), (0, -0.55, hull_z_top), mat_wood_light, model_col)
add_box("Hull_Gunwale_R", (3.4, 0.05, 0.05), (0, 0.55, hull_z_top), mat_wood_light, model_col)

# The tapered bow is formed by the narrow forward station of the hull mesh.
# Transom (Stern)
add_box("Hull_Transom", (0.05, 1.1, 0.6), (1.7, 0, hull_z_base + 0.3), mat_wood_light, model_col)

# --- 4.3 Gantry Crane ---
# Two posts frame the hull. Their concrete footings and rear anchors give the
# crossbeam and diagonal braces a clear load path into the slipway.
gantry_post_x = (-1.8, 1.8)
for side, x in zip(("L", "R"), gantry_post_x):
    add_box(f"Gantry_Concrete_Footing_{side}", (0.45, 0.45, 0.3), (x, 0, 0.15), mat_concrete, model_col)
    add_box(f"Gantry_Post_{side}", (0.2, 0.2, 3.8), (x, 0, 1.9), mat_metal_green, model_col)
    add_box(f"Gantry_Anchor_Block_{side}", (0.3, 0.55, 0.16), (x, 0.9, 0.48), mat_wood_dark, model_col)
    add_pipe(f"Gantry_Brace_{side}", (x, 0, 3.6), (x, 1.1, 0.56), 0.08, mat_wood_dark, model_col)

# The crossbeam and hoist sit over the center of the unfinished boat.
add_box("Gantry_Crossbeam", (4.0, 0.2, 0.2), (0, 0, 3.8), mat_metal_green, model_col)

# Crane Trolley (Rust Orange)
trolley_pos = (0, 0, 3.8)
add_box("Crane_Trolley", (0.3, 0.4, 0.15), trolley_pos, mat_rust, model_col)
# Trolley wheels/guides
add_box("Crane_Wheel_L", (0.1, 0.05, 0.1), (-0.15, 0, 3.85), mat_iron, model_col)
add_box("Crane_Wheel_R", (0.1, 0.05, 0.1), (0.15, 0, 3.85), mat_iron, model_col)

# Chain
chain_start = Vector((0, 0, 3.7))
chain_end = Vector((0, 0, 2.6))
add_pipe("Crane_Chain", chain_start, chain_end, 0.02, mat_iron, model_col)

# Hook
# Approximating a hook with a torus and a cone, or simple boxes
add_box("Crane_Hook_Base", (0.08, 0.08, 0.08), (0, 0, 2.55), mat_rust, model_col)
bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.02, location=(0, 0, 2.45), rotation=(math.radians(90), 0, 0))
hook_ring = bpy.context.active_object
hook_ring.name = "Crane_Hook_Ring"
hook_ring.data.materials.append(mat_rust)
for c in hook_ring.users_collection:
    c.objects.unlink(hook_ring)
model_col.objects.link(hook_ring)
apply_flat_shading(hook_ring)

# --- 4.4 Tool Shed (+X side) ---
shed_x = 1.8
shed_y = -1.2
shed_w = 1.0
shed_d = 1.6
shed_h = 2.2

# Shed Base/Pad
add_box("Shed_Base", (shed_w + 0.2, shed_d + 0.2, 0.1), (shed_x, shed_y, 0.05), mat_concrete, model_col)

# Shed Walls
add_box("Shed_Wall_Back", (shed_w, 0.1, shed_h), (shed_x, shed_y + shed_d/2, shed_h/2 + 0.1), mat_wood_dark, model_col)
add_box("Shed_Wall_Left", (0.1, shed_d, shed_h), (shed_x - shed_w/2, shed_y, shed_h/2 + 0.1), mat_wood_dark, model_col)
add_box("Shed_Wall_Right", (0.1, shed_d, shed_h), (shed_x + shed_w/2, shed_y, shed_h/2 + 0.1), mat_wood_dark, model_col)
# Front Wall with Door Opening
front_y = shed_y - shed_d/2
add_box("Shed_Wall_Front_L", (0.2, 0.1, shed_h), (shed_x - shed_w/2 + 0.1, front_y, shed_h/2 + 0.1), mat_wood_dark, model_col)
add_box("Shed_Wall_Front_R", (0.2, 0.1, shed_h), (shed_x + shed_w/2 - 0.1, front_y, shed_h/2 + 0.1), mat_wood_dark, model_col)
add_box("Shed_Wall_Front_Top", (shed_w - 0.4, 0.1, 0.4), (shed_x, front_y, shed_h - 0.1), mat_wood_dark, model_col)

# Door
add_box("Shed_Door", (0.6, 0.05, 1.8), (shed_x, front_y - 0.02, 0.1 + 0.9), mat_metal_green, model_col)
# Door Handle
add_box("Shed_Door_Handle", (0.05, 0.05, 0.15), (shed_x + 0.2, front_y - 0.06, 0.1 + 0.9), mat_iron, model_col)

# A compact exterior cabinet keeps repair tools readable in the closed shed view.
cabinet_x = shed_x + shed_w/2 + 0.16
cabinet_y = shed_y
add_box("Shed_Exterior_Tool_Cabinet", (0.32, 0.52, 0.72), (cabinet_x, cabinet_y, 0.92), mat_wood_dark, model_col)
add_box("Shed_Tool_Cabinet_Door_Upper", (0.025, 0.45, 0.30), (cabinet_x + 0.17, cabinet_y, 1.11), mat_metal_green, model_col)
add_box("Shed_Tool_Cabinet_Door_Lower", (0.025, 0.45, 0.30), (cabinet_x + 0.17, cabinet_y, 0.73), mat_metal_green, model_col)
add_box("Shed_Tool_Cabinet_Handle_Upper", (0.035, 0.045, 0.07), (cabinet_x + 0.205, cabinet_y - 0.13, 1.10), mat_iron, model_col)
add_box("Shed_Tool_Cabinet_Handle_Lower", (0.035, 0.045, 0.07), (cabinet_x + 0.205, cabinet_y - 0.13, 0.72), mat_iron, model_col)

# Roof (Light Cyan Metal)
roof_y_overhang = 0.2
roof_x_overhang = 0.2
add_box("Shed_Roof", (shed_w + roof_x_overhang, shed_d + roof_y_overhang, 0.1), (shed_x, shed_y, shed_h + 0.05), mat_cyan, model_col, rot=(math.radians(5), 0, 0))

# Inspection Light (Amber)
add_box("Shed_Light_Mount", (0.1, 0.1, 0.05), (shed_x, front_y - 0.05, shed_h - 0.15), mat_iron, model_col)
add_box("Shed_Light", (0.08, 0.04, 0.08), (shed_x, front_y - 0.1, shed_h - 0.2), mat_amber, model_col)

# ==========================================
# 5. Quality Diagnostic Setup
# ==========================================
def calculate_bounds_and_diagnostics():
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
    
    mesh_objects = [obj for obj in model_col.objects if obj.type == 'MESH']
    non_manifold_count = 0
    loose_verts = 0
    
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
        
        # Check for loose vertices (no connected edges)
        loose_verts += len([v for v in bm.verts if not v.link_edges])
        
        bm.free()

    print("\n--- Diagnostic Report ---")
    print(f"Mesh Object Count: {len(mesh_objects)}")
    print(f"World Bounds (W, D, H): {max_x - min_x:.3f} m, {max_y - min_y:.3f} m, {max_z - min_z:.3f} m")
    print(f"Minimum Z: {min_z:.3f} m")
    print(f"Non-Manifold Edges: {non_manifold_count}")
    print(f"Loose Vertices: {loose_verts}")
    print("Note: Per-object topological checks cannot detect intersections between separate objects.")
    print("-------------------------\n")

# ==========================================
# 6. Render Setup & QA Renders
# ==========================================
scene = bpy.context.scene

try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        pass

scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'

# Temporary World Setup for QA renders
world = bpy.data.worlds.new("Shipyard_DeepSeek_RenderWorld")
scene.world = world
world.use_nodes = True

bg_node = next((n for n in world.node_tree.nodes if n.bl_idname == 'ShaderNodeBackground'), None)
if bg_node:
    bg_node.inputs[0].default_value = (0.62, 0.62, 0.62, 1.0)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 2.0
sun.rotation_euler = (math.radians(45), math.radians(20), math.radians(30))
for c in sun.users_collection:
    c.objects.unlink(sun)
helper_col.objects.link(sun)

bpy.ops.object.light_add(type='AREA', location=(-5, -6, 6))
area = bpy.context.active_object
area.data.energy = 240
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

center_z = 1.9
scale_factor = 6.5

# True Orthographic Views
render_view((0, -15, center_z), (math.radians(90), 0, 0), scale_factor, "Shipyard_DeepSeek_Front.png")
render_view((0, 15, center_z), (math.radians(90), 0, math.radians(180)), scale_factor, "Shipyard_DeepSeek_Back.png")
render_view((-15, 0, center_z), (math.radians(90), 0, math.radians(-90)), scale_factor, "Shipyard_DeepSeek_Left.png")
render_view((15, 0, center_z), (math.radians(90), 0, math.radians(90)), scale_factor, "Shipyard_DeepSeek_Right.png")
render_view((0, 0, 15), (0, 0, 0), scale_factor, "Shipyard_DeepSeek_Top.png")
render_view((0, 0, -15), (math.radians(180), 0, 0), scale_factor, "Shipyard_DeepSeek_Bottom.png")

# 3/4 Preview
cam.location = (8, -10, 8)
look_target = Vector((0, 0, 1.8))
direction = look_target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 7.5
scene.render.filepath = str(PREVIEW_DIR / "Shipyard_DeepSeek.png")
bpy.ops.render.render(write_still=True)

# ==========================================
# 7. Export FBX & Save Blend
# ==========================================
bpy.ops.object.select_all(action='DESELECT')
for obj in model_col.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

fbx_path = FBX_DIR / "Shipyard_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True
)

blend_path = BLEND_DIR / "Shipyard_DeepSeek.blend"

# Restore the original scene state before saving. The temporary render camera
# and lights remain grouped under Helpers_Shipyard_DeepSeek for later inspection.
scene.camera = original_scene_state["camera"]
scene.world = original_scene_state["world"]
scene.render.engine = original_scene_state["engine"]
scene.render.resolution_x = original_scene_state["resolution_x"]
scene.render.resolution_y = original_scene_state["resolution_y"]
scene.render.resolution_percentage = original_scene_state["resolution_percentage"]
scene.render.filepath = original_scene_state["filepath"]
scene.render.film_transparent = original_scene_state["film_transparent"]
scene.render.image_settings.file_format = original_scene_state["file_format"]
scene.render.image_settings.color_mode = original_scene_state["color_mode"]
scene.view_settings.view_transform = original_scene_state["view_transform"]
scene.view_settings.look = original_scene_state["look"]
scene.view_settings.exposure = original_scene_state["exposure"]
scene.view_settings.gamma = original_scene_state["gamma"]
if world.users == 0:
    bpy.data.worlds.remove(world)

bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# ==========================================
# 8. Execute Diagnostics
# ==========================================
calculate_bounds_and_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved Previews to: {PREVIEW_DIR}")
print(f"Saved QA Renders to: {QA_DIR}")
