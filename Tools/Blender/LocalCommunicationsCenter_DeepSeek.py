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

MODEL_COLLECTION_NAME = "LocalCommunicationsCenter_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_LocalCommunicationsCenter_DeepSeek"
MATERIAL_PREFIX = "LocalCommunicationsCenter_DeepSeek_"

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
def create_material(name, base_color, roughness=0.8, metallic=0.0, alpha=1.0, emission_color=None):
    mat_name = f"{MATERIAL_PREFIX}{name}"
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
    
    if emission_color:
        if 'Emission Color' in bsdf_node.inputs:
            bsdf_node.inputs['Emission Color'].default_value = emission_color
        elif 'Emission' in bsdf_node.inputs:
            bsdf_node.inputs['Emission'].default_value = emission_color
        
        if 'Emission Strength' in bsdf_node.inputs:
            bsdf_node.inputs['Emission Strength'].default_value = 2.0
    
    links.new(bsdf_node.outputs['BSDF'], out_node.inputs['Surface'])
    
    if alpha < 1.0:
        try:
            mat.surface_render_method = 'DITHERED'
        except AttributeError:
            mat.blend_method = 'BLEND'
        
    return mat

# Colors based on reference descriptions
mat_wall = create_material("SaltBleachedWood", (0.6, 0.5, 0.4, 1.0), roughness=0.9)
mat_frame = create_material("TarDarkWood", (0.18, 0.14, 0.12, 1.0), roughness=0.9)
mat_roof_green = create_material("SeaGreenMetal", (0.3, 0.5, 0.5, 1.0), roughness=0.5, metallic=0.4)
mat_roof_gray = create_material("PatchyGrayMetal", (0.4, 0.5, 0.5, 1.0), roughness=0.6, metallic=0.3)
mat_base = create_material("WarmLightGrayStone", (0.65, 0.65, 0.62, 1.0), roughness=0.95)
mat_glass = create_material("SmokeBlueGlass", (0.2, 0.3, 0.4, 0.5), roughness=0.1, alpha=0.5)
mat_rust = create_material("RustOrangePatch", (0.65, 0.25, 0.1, 1.0), roughness=0.8, metallic=0.2)
mat_amber = create_material("AmberBeacon", (0.9, 0.5, 0.1, 1.0), roughness=0.2, emission_color=(0.9, 0.5, 0.1, 1.0))
mat_iron = create_material("DarkIron", (0.12, 0.12, 0.14, 1.0), roughness=0.5, metallic=0.8)
mat_cable = create_material("CableBlack", (0.05, 0.05, 0.05, 1.0), roughness=0.9)

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

# Dimensions Plan:
# Base: 2.3 (X) x 2.0 (Y) x 0.2 (Z)
# Walls: 2.3 (X) x 2.0 (Y) x 1.7 (Z) from Z=0.3 to Z=2.0
# Roof: Ridge at Z=2.6, overhang to X=±1.25, Y=±1.2
# Total height: ~3.0 (including antenna)

# --- 4.1 Base & Floor ---
add_box("Base_Stone", (2.3, 2.0, 0.2), (0, 0, 0.1), mat_base, model_col)
add_box("Floor_Wood", (2.3, 2.0, 0.1), (0, 0, 0.25), mat_wall, model_col)

# --- 4.2 Walls & Frame ---
# Corner Posts
post_pos = [(-1.15, -1.0), (1.15, -1.0), (-1.15, 1.0), (1.15, 1.0)]
for i, (x, y) in enumerate(post_pos):
    add_box(f"Frame_CornerPost_{i}", (0.15, 0.15, 1.7), (x, y, 1.15), mat_frame, model_col)

# Back Wall (+Y)
add_box("Wall_Back", (2.3, 0.1, 1.7), (0, 1.0, 1.15), mat_wall, model_col)

# Left Wall (-X)
add_box("Wall_Left", (0.1, 2.0, 1.7), (-1.15, 0, 1.15), mat_wall, model_col)

# Right Wall (+X)
add_box("Wall_Right", (0.1, 2.0, 1.7), (1.15, 0, 1.15), mat_wall, model_col)

# Front Wall (-Y) with Cutouts
# Left segment (before door)
add_box("Wall_Front_L", (0.25, 0.1, 1.7), (-1.025, -1.0, 1.15), mat_wall, model_col)
# Above door (Door: X -0.9 to -0.3, Z 0.3 to 1.7)
add_box("Wall_Front_Top_Door", (0.6, 0.1, 0.3), (-0.6, -1.0, 1.85), mat_wall, model_col)
# Middle segment (between door and window)
add_box("Wall_Front_Mid", (0.4, 0.1, 1.7), (-0.1, -1.0, 1.15), mat_wall, model_col)
# Below window (Window: X 0.1 to 0.9, Z 0.9 to 1.6)
add_box("Wall_Front_Bot_Win", (0.8, 0.1, 0.6), (0.5, -1.0, 0.6), mat_wall, model_col)
# Above window
add_box("Wall_Front_Top_Win", (0.8, 0.1, 0.4), (0.5, -1.0, 1.8), mat_wall, model_col)
# Right segment (after window)
add_box("Wall_Front_R", (0.25, 0.1, 1.7), (1.025, -1.0, 1.15), mat_wall, model_col)

# --- 4.3 Door & Window ---
# Door
add_box("Door_Panel", (0.6, 0.05, 1.4), (-0.6, -1.05, 1.0), mat_wall, model_col)
add_box("Door_Patch", (0.2, 0.06, 0.3), (-0.6, -1.08, 0.6), mat_rust, model_col)
add_box("Door_Handle", (0.05, 0.05, 0.1), (-0.35, -1.08, 1.0), mat_iron, model_col)

# Window
add_box("Window_Glass", (0.8, 0.02, 0.7), (0.5, -1.05, 1.25), mat_glass, model_col)
add_box("Window_Frame_H", (0.85, 0.08, 0.08), (0.5, -1.05, 1.6), mat_frame, model_col)
add_box("Window_Frame_H_Bot", (0.85, 0.08, 0.08), (0.5, -1.05, 0.9), mat_frame, model_col)
add_box("Window_Frame_V_L", (0.08, 0.08, 0.7), (0.1, -1.05, 1.25), mat_frame, model_col)
add_box("Window_Frame_V_R", (0.08, 0.08, 0.7), (0.9, -1.05, 1.25), mat_frame, model_col)
add_box("Window_Mullion", (0.04, 0.06, 0.7), (0.5, -1.05, 1.25), mat_frame, model_col)

# --- 4.4 Roof ---
# Gable roof with ridge along X
roof_w = 2.5
roof_len = 1.25
roof_z_front = 2.0
roof_z_back = 2.0
ridge_z = 2.6

roof_angle = math.atan2(ridge_z - 2.0, 1.0)
roof_slope_len = math.sqrt(1.0**2 + (ridge_z - 2.0)**2) + 0.2

# Front Roof Panel (-Y)
add_box("Roof_Panel_Front", (roof_w, roof_slope_len, 0.05), (0, -0.6, (roof_z_front + ridge_z)/2), mat_roof_green, model_col, rot=(roof_angle, 0, 0))
# Back Roof Panel (+Y)
add_box("Roof_Panel_Back", (roof_w, roof_slope_len, 0.05), (0, 0.6, (roof_z_back + ridge_z)/2), mat_roof_gray, model_col, rot=(-roof_angle, 0, 0))

# Ridge Cap
add_box("Roof_Ridge", (roof_w + 0.1, 0.2, 0.08), (0, 0, ridge_z + 0.02), mat_roof_green, model_col)

# Standing Seams (simple ribs)
for x in [-1.0, -0.5, 0, 0.5, 1.0]:
    add_box(f"Roof_Seam_F_{x}", (0.04, roof_slope_len, 0.06), (x, -0.6, (roof_z_front + ridge_z)/2 + 0.02), mat_roof_gray, model_col, rot=(roof_angle, 0, 0))
    add_box(f"Roof_Seam_B_{x}", (0.04, roof_slope_len, 0.06), (x, 0.6, (roof_z_back + ridge_z)/2 + 0.02), mat_roof_green, model_col, rot=(-roof_angle, 0, 0))

# --- 4.5 Antenna System (+Y) ---
# Base on the back roof slope
ant_base_x = 0
ant_base_y = 0.5
ant_base_z = 2.35
# Calculate slope offset
ant_z_offset = (ant_base_y * math.tan(roof_angle))
ant_base_z = ridge_z - ant_z_offset

# Mast Base
add_box("Antenna_Base", (0.2, 0.2, 0.1), (ant_base_x, ant_base_y, ant_base_z + 0.05), mat_iron, model_col)
# Main Mast
mast_h = 0.6
add_cylinder("Antenna_Mast", 0.03, mast_h, (ant_base_x, ant_base_y, ant_base_z + 0.1 + mast_h/2), mat_iron, model_col, verts=8)
# Dipoles / Crossbars
for i, z_off in enumerate([0.3, 0.5]):
    z_pos = ant_base_z + 0.1 + z_off
    add_box(f"Antenna_Dipole_{i}", (0.6, 0.02, 0.02), (ant_base_x, ant_base_y, z_pos), mat_iron, model_col)
    # Short Diagonal Braces
    if i == 0:
        add_pipe("Antenna_Brace_1", (ant_base_x, ant_base_y, ant_base_z + 0.1), (ant_base_x - 0.2, ant_base_y - 0.15, z_pos), 0.015, mat_iron, model_col)
        add_pipe("Antenna_Brace_2", (ant_base_x, ant_base_y, ant_base_z + 0.1), (ant_base_x + 0.2, ant_base_y - 0.15, z_pos), 0.015, mat_iron, model_col)

# --- 4.6 Beacon (Front -Y) ---
beacon_x = 0
beacon_y = -0.7
beacon_z = ridge_z - (0.7 * math.tan(roof_angle))
# Mount
add_box("Beacon_Mount", (0.1, 0.1, 0.05), (beacon_x, beacon_y, beacon_z), mat_iron, model_col)
# Light
add_cylinder("Beacon_Light", 0.05, 0.1, (beacon_x, beacon_y, beacon_z + 0.08), mat_amber, model_col, verts=8)
# Cap
add_cylinder("Beacon_Cap", 0.07, 0.03, (beacon_x, beacon_y, beacon_z + 0.145), mat_rust, model_col, verts=8)

# --- 4.7 Side Equipment (+X Wall) ---
# Battery Box
add_box("Battery_Box", (0.3, 0.4, 0.5), (1.3, 0.4, 0.9), mat_iron, model_col)
add_box("Battery_Band", (0.32, 0.05, 0.52), (1.3, 0.4, 0.9), mat_rust, model_col)

# Cable Reel
reel_x = 1.15
reel_y = -0.4
reel_z = 1.2
# Wall plate and a lower shelf carry the spool against the cabin wall.
add_box("Reel_WallPlate", (0.12, 0.64, 0.52), (reel_x + 0.05, reel_y, reel_z), mat_iron, model_col)
add_box("Reel_SupportShelf", (0.36, 0.62, 0.08), (reel_x + 0.17, reel_y, 1.0), mat_iron, model_col)
add_pipe("Reel_BracketBrace_A", (reel_x + 0.04, reel_y - 0.24, 1.0), (reel_x + 0.17, reel_y - 0.24, 1.17), 0.025, mat_iron, model_col)
add_pipe("Reel_BracketBrace_B", (reel_x + 0.04, reel_y + 0.24, 1.0), (reel_x + 0.17, reel_y + 0.24, 1.17), 0.025, mat_iron, model_col)
# Axle
add_cylinder("Reel_Axle", 0.04, 0.3, (reel_x + 0.16, reel_y, reel_z), mat_iron, model_col, rot=(0, math.radians(90), 0), verts=8)
# Flanges
add_cylinder("Reel_Flange_1", 0.2, 0.02, (reel_x + 0.03, reel_y, reel_z), mat_iron, model_col, rot=(0, math.radians(90), 0), verts=12)
add_cylinder("Reel_Flange_2", 0.2, 0.02, (reel_x + 0.29, reel_y, reel_z), mat_iron, model_col, rot=(0, math.radians(90), 0), verts=12)
# Cable wrap (simulated by slightly smaller cylinder)
add_cylinder("Reel_Cable", 0.16, 0.24, (reel_x + 0.16, reel_y, reel_z), mat_cable, model_col, rot=(0, math.radians(90), 0), verts=12)

# Inspection Panel (on -X wall)
panel_x = -1.16
panel_y = 0.4
panel_z = 1.2
add_box("Panel_Board", (0.02, 0.5, 0.4), (panel_x, panel_y, panel_z), mat_wall, model_col)
add_box("Panel_Data_1", (0.01, 0.3, 0.02), (panel_x - 0.01, panel_y - 0.05, panel_z + 0.1), mat_rust, model_col)
add_box("Panel_Data_2", (0.01, 0.2, 0.02), (panel_x - 0.01, panel_y + 0.05, panel_z - 0.05), mat_iron, model_col)

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
original_scene_camera = scene.camera
original_scene_world = scene.world
original_render_settings = {
    "engine": scene.render.engine,
    "filepath": scene.render.filepath,
    "resolution_x": scene.render.resolution_x,
    "resolution_y": scene.render.resolution_y,
    "resolution_percentage": scene.render.resolution_percentage,
    "film_transparent": scene.render.film_transparent,
    "file_format": scene.render.image_settings.file_format,
    "view_transform": scene.view_settings.view_transform,
}
original_active_object = bpy.context.view_layer.objects.active
original_selection = {obj: obj.select_get() for obj in bpy.context.view_layer.objects}

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
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'

# Use a dedicated temporary render world so existing scene worlds remain untouched.
world = bpy.data.worlds.new(f"{MODEL_COLLECTION_NAME}_RenderWorld")
world.use_nodes = True

bg_node = next((n for n in world.node_tree.nodes if n.bl_idname == 'ShaderNodeBackground'), None)
if bg_node:
    bg_node.inputs[0].default_value = (0.72, 0.74, 0.75, 1.0)
    bg_node.inputs[1].default_value = 0.62
scene.world = world

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

# Hide objects outside this asset for the render pass, then restore their visibility.
asset_objects = set(model_col.objects) | set(helper_col.objects)
external_visibility = {obj: obj.hide_render for obj in scene.objects if obj not in asset_objects}
for obj in external_visibility:
    obj.hide_render = True

def render_view(loc, rot, ortho_scale, filename):
    cam.location = loc
    cam.rotation_euler = rot
    cam.data.ortho_scale = ortho_scale
    scene.render.filepath = str(QA_DIR / filename)
    bpy.ops.render.render(write_still=True)

center_z = 1.5
scale_factor = 4.5

# True Orthographic Views
render_view((0, -15, center_z), (math.radians(90), 0, 0), scale_factor, "LocalCommunicationsCenter_DeepSeek_Front.png")
render_view((0, 15, center_z), (math.radians(90), 0, math.radians(180)), scale_factor, "LocalCommunicationsCenter_DeepSeek_Back.png")
render_view((-15, 0, center_z), (math.radians(90), 0, math.radians(-90)), scale_factor, "LocalCommunicationsCenter_DeepSeek_Left.png")
render_view((15, 0, center_z), (math.radians(90), 0, math.radians(90)), scale_factor, "LocalCommunicationsCenter_DeepSeek_Right.png")
render_view((0, 0, 15), (0, 0, 0), scale_factor, "LocalCommunicationsCenter_DeepSeek_Top.png")
render_view((0, 0, -15), (math.radians(180), 0, 0), scale_factor, "LocalCommunicationsCenter_DeepSeek_Bottom.png")

# 3/4 Preview
cam.location = (5, -6, 5)
look_target = Vector((0, 0, 1.3))
direction = look_target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 5.0
scene.render.filepath = str(PREVIEW_DIR / "LocalCommunicationsCenter_DeepSeek.png")
bpy.ops.render.render(write_still=True)

# ==========================================
# 7. Export FBX & Save Blend
# ==========================================
bpy.ops.object.select_all(action='DESELECT')
for obj in model_col.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

fbx_path = FBX_DIR / "LocalCommunicationsCenter_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True
)

blend_path = BLEND_DIR / "LocalCommunicationsCenter_DeepSeek.blend"
# Restore all temporary scene state before saving the editable source file.
for obj, was_hidden in external_visibility.items():
    obj.hide_render = was_hidden
scene.camera = original_scene_camera
scene.world = original_scene_world
scene.render.engine = original_render_settings["engine"]
scene.render.filepath = original_render_settings["filepath"]
scene.render.resolution_x = original_render_settings["resolution_x"]
scene.render.resolution_y = original_render_settings["resolution_y"]
scene.render.resolution_percentage = original_render_settings["resolution_percentage"]
scene.render.film_transparent = original_render_settings["film_transparent"]
scene.render.image_settings.file_format = original_render_settings["file_format"]
scene.view_settings.view_transform = original_render_settings["view_transform"]
for obj, was_selected in original_selection.items():
    if obj.name in bpy.data.objects:
        obj.select_set(was_selected)
if original_active_object and original_active_object.name in bpy.data.objects:
    bpy.context.view_layer.objects.active = original_active_object
else:
    bpy.context.view_layer.objects.active = None
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# ==========================================
# 8. Execute Diagnostics
# ==========================================
calculate_bounds_and_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved Previews to: {PREVIEW_DIR}")
print(f"Saved QA Renders to: {QA_DIR}")
