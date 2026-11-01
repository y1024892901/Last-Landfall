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

MODEL_COLLECTION_NAME = "WeatherTideBuoy_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_WeatherTideBuoy_DeepSeek"
MATERIAL_PREFIX = "WeatherTideBuoy_DeepSeek_"

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
def create_material(name, base_color, roughness=0.8, metallic=0.0, alpha=1.0, emission=None):
    mat_name = f"{MATERIAL_PREFIX}{name}"
    mat = bpy.data.materials.get(mat_name)
    if mat:
        # Do not alter a matching material still used outside this asset.
        if mat.users > 0:
            return mat
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default nodes
    for node in list(nodes):
        nodes.remove(node)
        
    # Find by bl_idname to avoid localization issues
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
    
    if emission:
        bsdf_node.inputs['Emission Color'].default_value = emission
        bsdf_node.inputs['Emission Strength'].default_value = 1.0
    
    links.new(bsdf_node.outputs['BSDF'], out_node.inputs['Surface'])
    
    if alpha < 1.0:
        if hasattr(mat, 'surface_render_method'):
            mat.surface_render_method = 'DITHERED'
        else:
            mat.blend_method = 'BLEND'
        
    return mat

mat_teal = create_material("SeaGlassTeal", (0.2, 0.45, 0.45, 1.0), roughness=0.6)
mat_deck = create_material("LightSeaFoamDeck", (0.6, 0.75, 0.75, 1.0), roughness=0.8)
mat_dark_metal = create_material("DarkTealGrayMetal", (0.15, 0.2, 0.22, 1.0), roughness=0.5, metallic=0.7)
mat_wood = create_material("WeatheredLightWood", (0.55, 0.45, 0.35, 1.0), roughness=0.9)
mat_rust = create_material("RustOrange", (0.65, 0.25, 0.1, 1.0), roughness=0.8, metallic=0.2)
mat_amber = create_material("AmberLight", (0.9, 0.5, 0.1, 1.0), roughness=0.2, emission=(0.9, 0.5, 0.1, 1.0))
mat_solar = create_material("SolarPanel", (0.05, 0.1, 0.2, 1.0), roughness=0.2, metallic=0.8)

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

# Dimensions:
# Float: Diameter 0.92m, hull from Z=0.05 to Z=0.41. Top deck at Z=0.42.
# Mast: Up to Z=2.5. Light at Z=2.6.
# Max width: ~1.02m. Max height: ~2.7m.

# --- 4.1 Main Float Body ---
# 8-sided cylinder
float_center = Vector((0, 0, 0.23))
add_cylinder("Float_Body", 0.46, 0.36, float_center, mat_teal, model_col, verts=8)
# Top Deck
add_cylinder("Float_Deck", 0.47, 0.05, (0, 0, 0.42), mat_deck, model_col, verts=8)
# Open perimeter keel / ballast ring leaves the tide transducer visible from below.
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.37,
    minor_radius=0.05,
    major_segments=12,
    minor_segments=6,
    location=(0, 0, 0.05),
)
ballast = bpy.context.active_object
ballast.name = "Float_Ballast_Ring"
ballast.data.materials.append(mat_dark_metal)
for c in ballast.users_collection:
    c.objects.unlink(ballast)
model_col.objects.link(ballast)
apply_flat_shading(ballast)

# Impact Bumpers (Rust Orange)
# Placed symmetrically on 4 of the 8 faces
# Face angles: 0, 45, 90, 135, 180, 225, 270, 315
# Placing at 45, 135, 225, 315
bumper_angles = [45, 135, 225, 315]
for i, angle in enumerate(bumper_angles):
    rad = math.radians(angle)
    # Distance from center to edge of octagon is R * cos(pi/8) = 0.46 * 0.9238 = 0.425
    # Place bumper centered at the face
    x = 0.425 * math.cos(rad)
    y = 0.425 * math.sin(rad)
    rot_z = rad + math.radians(90) # Face outward
    add_box(f"Float_Bumper_{i}", (0.1, 0.15, 0.25), (x, y, 0.2), mat_rust, model_col, rot=(0, 0, rot_z))

# Mooring Ears (3x on bottom edge)
mooring_angles = [-90, 30, 150] # Front, Right-Back, Left-Back
for i, angle in enumerate(mooring_angles):
    rad = math.radians(angle)
    x = 0.44 * math.cos(rad)
    y = 0.44 * math.sin(rad)
    # Base pad
    add_box(f"Mooring_Pad_{i}", (0.1, 0.12, 0.06), (x, y, 0.05), mat_dark_metal, model_col, rot=(0,0,rad+math.radians(90)))
    # Ring
    bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.015, location=(x, y, 0.075), rotation=(0, 0, rad+math.radians(90)))
    ring = bpy.context.active_object
    ring.name = f"Mooring_Ring_{i}"
    ring.data.materials.append(mat_dark_metal)
    for c in ring.users_collection:
        c.objects.unlink(ring)
    model_col.objects.link(ring)
    apply_flat_shading(ring)

# --- 4.2 Mast System ---
# Base
add_cylinder("Mast_Base", 0.15, 0.1, (0, 0, 0.47), mat_dark_metal, model_col, verts=12)
# Main Mast (tapered look by stacking)
add_cylinder("Mast_Main", 0.04, 2.0, (0, 0, 1.5), mat_dark_metal, model_col, verts=12)
# Reinforcing Rings
add_cylinder("Mast_Ring_1", 0.05, 0.04, (0, 0, 1.0), mat_dark_metal, model_col, verts=12)
add_cylinder("Mast_Ring_2", 0.05, 0.04, (0, 0, 1.8), mat_dark_metal, model_col, verts=12)

# Diagonal Braces
for i in range(4):
    angle = math.radians(45 + i * 90)
    x = 0.15 * math.cos(angle)
    y = 0.15 * math.sin(angle)
    add_pipe(f"Mast_Brace_{i}", (x, y, 0.45), (x*0.3, y*0.3, 0.9), 0.015, mat_dark_metal, model_col)

# --- 4.3 Top Instruments ---
# Anemometer (Wind speed)
anemo_z = 2.3
add_cylinder("Anemo_Hub", 0.03, 0.08, (0, 0, anemo_z), mat_dark_metal, model_col, verts=8)
for i in range(3):
    angle = math.radians(i * 120)
    arm_x = 0.12 * math.cos(angle)
    arm_y = 0.12 * math.sin(angle)
    add_pipe(f"Anemo_Arm_{i}", (0, 0, anemo_z), (arm_x, arm_y, anemo_z), 0.008, mat_dark_metal, model_col)
    # Cups
    add_cylinder(f"Anemo_Cup_{i}", 0.03, 0.04, (arm_x, arm_y, anemo_z), mat_deck, model_col, verts=6)

# Wind Vane (Direction)
vane_z = 2.1
add_pipe("Vane_Arm", (0, 0, vane_z), (0, -0.2, vane_z), 0.01, mat_dark_metal, model_col) # Pointing -Y
add_box("Vane_Arrow", (0.05, 0.1, 0.02), (0, -0.25, vane_z), mat_rust, model_col)
add_box("Vane_Tail", (0.02, 0.15, 0.08), (0, 0.15, vane_z), mat_rust, model_col)
add_pipe("Vane_Tail_Arm", (0,0,vane_z), (0,0.15,vane_z), 0.01, mat_dark_metal, model_col)

# Weather Sensor Box
add_box("Sensor_Box", (0.12, 0.1, 0.15), (0, -0.08, 1.7), mat_deck, model_col)
add_pipe("Sensor_Box_Mount", (0, 0, 1.7), (0, -0.03, 1.7), 0.015, mat_dark_metal, model_col)

# Nav Light (Amber)
light_z = 2.525
add_cylinder("NavLight_Base", 0.04, 0.05, (0, 0, light_z), mat_dark_metal, model_col)
add_cylinder("NavLight_Glass", 0.035, 0.08, (0, 0, light_z + 0.065), mat_amber, model_col, verts=8)
# Cap
add_cylinder("NavLight_Cap", 0.05, 0.02, (0, 0, light_z + 0.115), mat_wood, model_col, verts=8)

# --- 4.4 Deck Equipment ---
# Solar Panel
# Placed on the front-left side, angled slightly towards -Y
solar_x = -0.25
solar_y = -0.25
solar_z = 0.55
# Mounting Post
add_cylinder("Solar_Post", 0.02, 0.2, (solar_x, solar_y, 0.52), mat_dark_metal, model_col)
# Panel Frame
add_box("Solar_Frame", (0.35, 0.25, 0.02), (solar_x, solar_y, solar_z), mat_dark_metal, model_col, rot=(math.radians(15), 0, 0))
# Panel Glass
add_box("Solar_Glass", (0.32, 0.22, 0.01), (solar_x, solar_y - 0.01, solar_z + 0.015), mat_solar, model_col, rot=(math.radians(15), 0, 0))

# Radio Antenna
ant_x = 0.25
ant_y = 0.2
add_cylinder("Radio_Base", 0.04, 0.1, (ant_x, ant_y, 0.5), mat_dark_metal, model_col)
add_cylinder("Radio_Whip", 0.01, 0.6, (ant_x, ant_y, 0.85), mat_dark_metal, model_col, verts=6)

# --- 4.5 Tide Gauge (Side) ---
# Placed on the Right side (+X)
gauge_x = 0.46
gauge_y = 0
# Mounting Arm
add_pipe("Tide_Arm", (0.4, 0, 0.2), (gauge_x + 0.05, 0, 0.2), 0.02, mat_dark_metal, model_col)
# Vertical Scale Pole
add_box("Tide_Scale", (0.04, 0.04, 0.5), (gauge_x + 0.05, 0, 0.25), mat_wood, model_col)
# Ticks (simulated with thin boxes)
for i in range(5):
    z_tick = 0.05 + i * 0.1
    add_box(f"Tide_Tick_{i}", (0.06, 0.02, 0.01), (gauge_x + 0.05, -0.02, z_tick), mat_dark_metal, model_col)
# Probe Interface
add_cylinder("Tide_Probe", 0.03, 0.1, (gauge_x + 0.05, 0, 0.05), mat_rust, model_col)

# --- 4.6 Bottom Components ---
# Acoustic Tide Transducer & Guard
add_cylinder("Transducer", 0.1, 0.1, (0, 0, 0.05), mat_dark_metal, model_col, verts=12)
# Guard Cage
for i in range(4):
    angle = math.radians(i * 90)
    x = 0.12 * math.cos(angle)
    y = 0.12 * math.sin(angle)
    add_pipe(f"Guard_Post_{i}", (x, y, 0.0), (x, y, 0.15), 0.01, mat_dark_metal, model_col)
# Guard Ring
bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.01, location=(0, 0, 0.02))
g_ring = bpy.context.active_object
g_ring.name = "Guard_Ring"
g_ring.data.materials.append(mat_dark_metal)
for c in g_ring.users_collection:
    c.objects.unlink(g_ring)
model_col.objects.link(g_ring)
apply_flat_shading(g_ring)

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

# Preserve scene settings while rendering with a temporary studio setup.
original_camera = scene.camera
original_world = scene.world
original_engine = scene.render.engine
original_resolution_x = scene.render.resolution_x
original_resolution_y = scene.render.resolution_y
original_filepath = scene.render.filepath
original_film_transparent = scene.render.film_transparent
original_view_transform = scene.view_settings.view_transform

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
scene.view_settings.view_transform = 'Standard'

# Dedicated temporary world: do not modify an existing scene's world.
render_world = bpy.data.worlds.new("WeatherTideBuoy_DeepSeek_RenderWorld")
render_world.use_nodes = True
bg_node = next((n for n in render_world.node_tree.nodes if n.bl_idname == 'ShaderNodeBackground'), None)
if bg_node is None:
    bg_node = render_world.node_tree.nodes.new('ShaderNodeBackground')
output_node = next((n for n in render_world.node_tree.nodes if n.bl_idname == 'ShaderNodeOutputWorld'), None)
if output_node is None:
    output_node = render_world.node_tree.nodes.new('ShaderNodeOutputWorld')
if not any(link.from_node == bg_node and link.to_node == output_node for link in render_world.node_tree.links):
    render_world.node_tree.links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])
bg_node.inputs['Color'].default_value = (0.85, 0.85, 0.85, 1.0)
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

center_z = 1.3
scale_factor = 3.2

# True Orthographic Views
render_view((0, -15, center_z), (math.radians(90), 0, 0), scale_factor, "WeatherTideBuoy_DeepSeek_Front.png")
render_view((0, 15, center_z), (math.radians(90), 0, math.radians(180)), scale_factor, "WeatherTideBuoy_DeepSeek_Back.png")
render_view((-15, 0, center_z), (math.radians(90), 0, math.radians(-90)), scale_factor, "WeatherTideBuoy_DeepSeek_Left.png")
render_view((15, 0, center_z), (math.radians(90), 0, math.radians(90)), scale_factor, "WeatherTideBuoy_DeepSeek_Right.png")
render_view((0, 0, 15), (0, 0, 0), scale_factor, "WeatherTideBuoy_DeepSeek_Top.png")
render_view((0, 0, -15), (math.radians(180), 0, 0), scale_factor, "WeatherTideBuoy_DeepSeek_Bottom.png")

# 3/4 Preview
cam.location = (5, -6, 5)
look_target = Vector((0, 0, 1.2))
direction = look_target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 3.5
scene.render.filepath = str(PREVIEW_DIR / "WeatherTideBuoy_DeepSeek.png")
bpy.ops.render.render(write_still=True)

# Restore the caller's camera, world, and render settings before saving.
scene.camera = original_camera
scene.world = original_world
scene.render.engine = original_engine
scene.render.resolution_x = original_resolution_x
scene.render.resolution_y = original_resolution_y
scene.render.filepath = original_filepath
scene.render.film_transparent = original_film_transparent
scene.view_settings.view_transform = original_view_transform
if render_world.users == 0:
    bpy.data.worlds.remove(render_world)

# ==========================================
# 7. Export FBX & Save Blend
# ==========================================
bpy.ops.object.select_all(action='DESELECT')
for obj in model_col.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

fbx_path = FBX_DIR / "WeatherTideBuoy_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True
)

blend_path = BLEND_DIR / "WeatherTideBuoy_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# ==========================================
# 8. Execute Diagnostics
# ==========================================
calculate_bounds_and_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved Previews to: {PREVIEW_DIR}")
print(f"Saved QA Renders to: {QA_DIR}")
