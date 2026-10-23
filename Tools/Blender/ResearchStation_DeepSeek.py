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

MODEL_COLLECTION_NAME = "ResearchStation_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_ResearchStation_DeepSeek"
MATERIAL_PREFIX = "ResearchStation_DeepSeek_"

scene = bpy.context.scene
original_scene_state = {
    "camera_name": scene.camera.name if scene.camera else None,
    "world": scene.world,
    "engine": scene.render.engine,
    "resolution_x": scene.render.resolution_x,
    "resolution_y": scene.render.resolution_y,
    "resolution_percentage": scene.render.resolution_percentage,
    "filepath": scene.render.filepath,
    "film_transparent": scene.render.film_transparent,
    "file_format": scene.render.image_settings.file_format,
    "color_mode": scene.render.image_settings.color_mode,
    "color_depth": scene.render.image_settings.color_depth,
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
original_render_visibility = [(obj, obj.hide_render) for obj in scene.objects]

# ==========================================
# 2. Material Creation
# ==========================================
def create_material(name, base_color, roughness=0.8, metallic=0.0, alpha=1.0, emission_color=None):
    mat_name = f"{MATERIAL_PREFIX}{name}"
    mat = bpy.data.materials.get(mat_name)
    if mat:
        if mat.users == 0:
            bpy.data.materials.remove(mat)
        else:
            suffix = 1
            while bpy.data.materials.get(f"{mat_name}_Generated{suffix:02d}"):
                suffix += 1
            mat_name = f"{mat_name}_Generated{suffix:02d}"
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
        mat.blend_method = 'BLEND'
        
    return mat

# Colors based on reference descriptions
mat_wall = create_material("SeaGlassWall", (0.25, 0.45, 0.45, 1.0), roughness=0.7)
mat_roof = create_material("PaleCyanMetal", (0.6, 0.8, 0.8, 1.0), roughness=0.5, metallic=0.4)
mat_wood = create_material("WeatheredLightWood", (0.6, 0.5, 0.4, 1.0), roughness=0.9)
mat_concrete = create_material("WarmGrayConcrete", (0.6, 0.6, 0.58, 1.0), roughness=0.95)
mat_iron = create_material("DarkIron", (0.12, 0.12, 0.14, 1.0), roughness=0.5, metallic=0.8)
mat_amber = create_material("AmberMark", (0.9, 0.5, 0.1, 1.0), roughness=0.6)
mat_rust = create_material("RustOrange", (0.58, 0.23, 0.09, 1.0), roughness=0.8)
mat_glass = create_material("SeaGlassWindow", (0.3, 0.6, 0.6, 0.4), roughness=0.1, alpha=0.4)
mat_bottle = create_material("SampleBottle", (0.8, 0.9, 0.9, 0.6), roughness=0.2, alpha=0.6)
mat_board = create_material("RecordBoard", (0.8, 0.8, 0.75, 1.0), roughness=0.9)

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

def add_gable_prism(name, x_center, thickness, parent_col):
    x0 = x_center - thickness * 0.5
    x1 = x_center + thickness * 0.5
    profile = [(-0.95, 1.95), (0.0, 2.30), (0.95, 1.95)]
    vertices = [(x0, y, z) for y, z in profile] + [(x1, y, z) for y, z in profile]
    faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    parent_col.objects.link(obj)
    obj.data.materials.append(mat_wall)
    apply_flat_shading(obj)
    return obj

# ==========================================
# 4. Modeling Components
# ==========================================

# Dimensions Plan:
# Base: 2.35 (X) x 2.05 (Y) x 0.15 (Z)
# Walls: 2.2 (X) x 1.9 (Y) x 1.8 (Z) from Z=0.15 to Z=1.95
# Roof: Gable along X, ridge at Z=2.3, overhang to Y=±1.1
# Total height: ~2.75 (including weather mast)

# --- 4.1 Foundation ---
add_box("Foundation_Base", (2.35, 2.05, 0.15), (0, 0, 0.075), mat_concrete, model_col)

# --- 4.2 Walls & Corner Posts ---
# Corner Posts
post_pos = [(-1.1, -0.95), (1.1, -0.95), (-1.1, 0.95), (1.1, 0.95)]
for i, (x, y) in enumerate(post_pos):
    add_box(f"Wall_CornerPost_{i}", (0.1, 0.1, 1.85), (x, y, 0.15 + 0.925), mat_wood, model_col)

# Back Wall (+Y)
add_box("Wall_Back", (2.2, 0.05, 1.8), (0, 0.95, 0.15 + 0.9), mat_wall, model_col)

# Left Wall (-X)
add_box("Wall_Left", (0.05, 1.9, 1.8), (-1.1, 0, 0.15 + 0.9), mat_wall, model_col)

# Right Wall (+X)
add_box("Wall_Right", (0.05, 1.9, 1.8), (1.1, 0, 0.15 + 0.9), mat_wall, model_col)

# Close the triangular gable ends beneath the ridge.
add_gable_prism("Wall_Gable_Left", -1.1, 0.05, model_col)
add_gable_prism("Wall_Gable_Right", 1.1, 0.05, model_col)

# Front Wall (-Y) with cutouts
# Left part (before door)
add_box("Wall_Front_L", (0.4, 0.05, 1.8), (-0.9, -0.95, 0.15 + 0.9), mat_wall, model_col)
# Door (X=-0.7 to -0.1, Z=0.15 to 1.55)
add_box("Wall_Front_Top_Door", (0.6, 0.05, 0.4), (-0.4, -0.95, 1.55 + 0.2), mat_wall, model_col)
# Middle part (between door and window)
add_box("Wall_Front_Mid", (0.1, 0.05, 1.8), (-0.05, -0.95, 0.15 + 0.9), mat_wall, model_col)
# Window (X=0.0 to 0.8, Z=0.7 to 1.5)
add_box("Wall_Front_Bot_Win", (0.8, 0.05, 0.55), (0.4, -0.95, 0.15 + 0.275), mat_wall, model_col)
add_box("Wall_Front_Top_Win", (0.8, 0.05, 0.45), (0.4, -0.95, 1.5 + 0.225), mat_wall, model_col)
# Right part (after window)
add_box("Wall_Front_R", (0.3, 0.05, 1.8), (0.95, -0.95, 0.15 + 0.9), mat_wall, model_col)

# --- 4.3 Door & Window ---
# Door
add_box("Door_Panel", (0.6, 0.05, 1.4), (-0.4, -0.97, 0.15 + 0.7), mat_wood, model_col)
add_box("Door_Handle", (0.05, 0.05, 0.1), (-0.15, -1.01, 0.15 + 0.7), mat_iron, model_col)
add_box("Door_Sign", (0.15, 0.02, 0.05), (-0.4, -1.0, 1.4), mat_amber, model_col)

# Window
add_box("Window_Glass", (0.8, 0.02, 0.8), (0.4, -0.97, 1.1), mat_glass, model_col)
add_box("Window_Frame_H_Top", (0.85, 0.05, 0.05), (0.4, -0.98, 1.5), mat_wood, model_col)
add_box("Window_Frame_H_Bot", (0.85, 0.05, 0.05), (0.4, -0.98, 0.7), mat_wood, model_col)
add_box("Window_Frame_V_L", (0.05, 0.05, 0.8), (0.0, -0.98, 1.1), mat_wood, model_col)
add_box("Window_Frame_V_R", (0.05, 0.05, 0.8), (0.8, -0.98, 1.1), mat_wood, model_col)
add_box("Window_Mullion", (0.04, 0.05, 0.8), (0.4, -0.98, 1.1), mat_wood, model_col)

# --- 4.4 Roof ---
# Ridge along X, slope down towards +Y and -Y
roof_w = 2.5
roof_slope_len = math.sqrt(1.0**2 + 0.35**2) # from Y=0 to Y=1.0, Z drops 0.35
roof_angle = math.atan2(0.35, 1.0)

# Roof Panels
add_box("Roof_Panel_Front", (roof_w, roof_slope_len, 0.05), (0, -0.5, 1.95 + 0.175), mat_roof, model_col, rot=(roof_angle, 0, 0))
add_box("Roof_Panel_Back", (roof_w, roof_slope_len, 0.05), (0, 0.5, 1.95 + 0.175), mat_roof, model_col, rot=(-roof_angle, 0, 0))

# Ridge Cap
add_box("Roof_Ridge", (roof_w + 0.05, 0.2, 0.08), (0, 0, 2.3), mat_roof, model_col)

# Standing Seams (Ribs)
for x in [-1.0, -0.5, 0, 0.5, 1.0]:
    add_box(f"Roof_Seam_F_{x}", (0.04, roof_slope_len, 0.06), (x, -0.5, 1.95 + 0.175), mat_roof, model_col, rot=(roof_angle, 0, 0))
    add_box(f"Roof_Seam_B_{x}", (0.04, roof_slope_len, 0.06), (x, 0.5, 1.95 + 0.175), mat_roof, model_col, rot=(-roof_angle, 0, 0))

# --- 4.5 Front Sample Table ---
# Table under the window
table_x = 0.4
table_y = -1.2
table_z = 0.9
# Table Top
add_box("SampleTable_Top", (0.9, 0.5, 0.05), (table_x, table_y, table_z), mat_wood, model_col)
# Legs (attached to base)
add_box("SampleTable_Leg_L", (0.05, 0.05, table_z - 0.15), (table_x - 0.35, table_y + 0.15, 0.15 + (table_z - 0.15)/2), mat_wood, model_col)
add_box("SampleTable_Leg_R", (0.05, 0.05, table_z - 0.15), (table_x + 0.35, table_y + 0.15, 0.15 + (table_z - 0.15)/2), mat_wood, model_col)

# Sample Bottles (4)
for i in range(4):
    x_pos = table_x - 0.3 + i * 0.2
    add_cylinder(f"SampleBottle_{i}", 0.04, 0.15, (x_pos, table_y, table_z + 0.1), mat_bottle, model_col, verts=8)
    add_cylinder(f"SampleBottle_Cap_{i}", 0.045, 0.02, (x_pos, table_y, table_z + 0.18), mat_iron, model_col, verts=8)

# --- 4.6 Roof Weather Station (+Y side) ---
mast_base_x = 0.0
mast_base_y = 0.72
mast_base_z = 2.3 - 0.35 * mast_base_y

# A broad foot plate bridges the mast onto the sloped roof panel.
add_box("Weather_Mast_Foot", (0.18, 0.18, 0.05), (mast_base_x, mast_base_y, mast_base_z + 0.02), mat_iron, model_col)
mast_start_z = mast_base_z + 0.045
mast_top_z = 2.55
add_cylinder("Weather_Mast", 0.03, mast_top_z - mast_start_z, (mast_base_x, mast_base_y, (mast_start_z + mast_top_z) * 0.5), mat_iron, model_col, verts=8)

# The rain cup is carried by a short arm fixed to the mast.
rain_z = 2.49
add_pipe("Weather_RainGauge_Arm", (mast_base_x, mast_base_y, rain_z - 0.02), (mast_base_x + 0.18, mast_base_y, rain_z - 0.02), 0.018, mat_iron, model_col)
add_cylinder("Weather_RainGauge", 0.08, 0.12, (mast_base_x + 0.18, mast_base_y, rain_z), mat_wood, model_col, verts=8)

# Directional vane: a horizontal pointer, with a broad tail at the +X end.
add_pipe("Weather_Vane_Pivot", (mast_base_x, mast_base_y, mast_top_z - 0.02), (mast_base_x, mast_base_y, mast_top_z + 0.06), 0.015, mat_iron, model_col)
add_pipe("Weather_Vane_Rod", (mast_base_x - 0.28, mast_base_y, mast_top_z + 0.06), (mast_base_x + 0.25, mast_base_y, mast_top_z + 0.06), 0.012, mat_iron, model_col)
add_box("Weather_Vane_Tail", (0.10, 0.025, 0.10), (mast_base_x + 0.20, mast_base_y, mast_top_z + 0.06), mat_rust, model_col)
add_box("Weather_Vane_Arrow", (0.08, 0.025, 0.025), (mast_base_x - 0.30, mast_base_y, mast_top_z + 0.06), mat_rust, model_col)

# --- 4.7 Side Mounted Equipment ---
# Left Wall (-X): Record Board
board_x = -1.14
board_y = 0
board_z = 1.2
add_box("SideBoard_Frame", (0.04, 0.5, 0.7), (board_x, board_y, board_z), mat_wood, model_col)
add_box("SideBoard_Surface", (0.02, 0.4, 0.6), (board_x - 0.03, board_y, board_z), mat_board, model_col)
# Geometric data lines (no text)
add_box("SideBoard_Data_1", (0.01, 0.3, 0.02), (board_x - 0.04, board_y - 0.05, board_z + 0.15), mat_amber, model_col)
add_box("SideBoard_Data_2", (0.01, 0.2, 0.02), (board_x - 0.04, board_y + 0.05, board_z + 0.05), mat_iron, model_col)
add_box("SideBoard_Data_3", (0.01, 0.25, 0.02), (board_x - 0.04, board_y - 0.05, board_z - 0.05), mat_iron, model_col)

# Right Wall (+X): Reader box and scale
box_x = 1.13
box_y = 0.2
box_z = 1.0
add_box("SideBox_Arm", (0.1, 0.1, 0.05), (box_x - 0.05, box_y, box_z + 0.1), mat_iron, model_col)
add_box("SideBox_Main", (0.15, 0.2, 0.15), (box_x + 0.05, box_y, box_z), mat_wood, model_col)
add_box("SideBox_Screen", (0.01, 0.1, 0.08), (box_x + 0.13, box_y, box_z), mat_glass, model_col)
# Scale column
add_box("SideScale_Column", (0.03, 0.03, 0.5), (1.13, -0.3, 0.15 + 0.25), mat_iron, model_col)
for i in range(4):
    add_box(f"SideScale_Tick_{i}", (0.04, 0.06, 0.01), (1.13, -0.3, 0.15 + 0.1 + i*0.1), mat_amber, model_col)

# --- 4.8 Back Transport Box ---
box_b_x = -0.6
box_b_y = 0.72
add_box("TransportBox_Base", (0.4, 0.3, 0.3), (box_b_x, box_b_y, 0.15 + 0.15), mat_wood, model_col)
add_box("TransportBox_Lid", (0.42, 0.32, 0.05), (box_b_x, box_b_y, 0.15 + 0.325), mat_wood, model_col)
# Straps
add_box("TransportBox_Strap_1", (0.05, 0.34, 0.35), (box_b_x - 0.1, box_b_y, 0.15 + 0.175), mat_iron, model_col)
add_box("TransportBox_Strap_2", (0.05, 0.34, 0.35), (box_b_x + 0.1, box_b_y, 0.15 + 0.175), mat_iron, model_col)

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

# A temporary render world avoids changing a world shared with other scenes.
world = bpy.data.worlds.new(f"{MATERIAL_PREFIX}TemporaryRenderWorld")
scene.world = world
world.use_nodes = True

bg_node = next((n for n in world.node_tree.nodes if n.bl_idname == 'ShaderNodeBackground'), None)
if bg_node is None:
    bg_node = world.node_tree.nodes.new('ShaderNodeBackground')
bg_node.inputs['Color'].default_value = (0.62, 0.62, 0.62, 1.0)

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

# Hide pre-existing scene objects only during asset renders; restore them
# before saving so the user's scene remains intact.
for obj, _hide_render in original_render_visibility:
    obj.hide_render = True

def render_view(loc, rot, ortho_scale, filename):
    cam.location = loc
    cam.rotation_euler = rot
    cam.data.ortho_scale = ortho_scale
    scene.render.filepath = str(QA_DIR / filename)
    bpy.ops.render.render(write_still=True)

center_z = 1.3
scale_factor = 4.0

# True Orthographic Views
render_view((0, -15, center_z), (math.radians(90), 0, 0), scale_factor, "ResearchStation_DeepSeek_Front.png")
render_view((0, 15, center_z), (math.radians(90), 0, math.radians(180)), scale_factor, "ResearchStation_DeepSeek_Back.png")
render_view((-15, 0, center_z), (math.radians(90), 0, math.radians(-90)), scale_factor, "ResearchStation_DeepSeek_Left.png")
render_view((15, 0, center_z), (math.radians(90), 0, math.radians(90)), scale_factor, "ResearchStation_DeepSeek_Right.png")
render_view((0, 0, 15), (0, 0, 0), scale_factor, "ResearchStation_DeepSeek_Top.png")
render_view((0, 0, -15), (math.radians(180), 0, 0), scale_factor, "ResearchStation_DeepSeek_Bottom.png")

# 3/4 Preview
cam.location = (5, -6, 5)
look_target = Vector((0, 0, 1.2))
direction = look_target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 4.5
scene.render.filepath = str(PREVIEW_DIR / "ResearchStation_DeepSeek.png")
bpy.ops.render.render(write_still=True)

for obj, hide_render in original_render_visibility:
    if obj.name in bpy.data.objects:
        obj.hide_render = hide_render

# ==========================================
# 7. Export FBX & Save Blend
# ==========================================
bpy.ops.object.select_all(action='DESELECT')
for obj in model_col.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

fbx_path = FBX_DIR / "ResearchStation_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True
)

blend_path = BLEND_DIR / "ResearchStation_DeepSeek.blend"

# Restore original scene state before saving the model file.
scene.camera = bpy.data.objects.get(original_scene_state["camera_name"]) if original_scene_state["camera_name"] else None
scene.world = original_scene_state["world"]
scene.render.engine = original_scene_state["engine"]
scene.render.resolution_x = original_scene_state["resolution_x"]
scene.render.resolution_y = original_scene_state["resolution_y"]
scene.render.resolution_percentage = original_scene_state["resolution_percentage"]
scene.render.filepath = original_scene_state["filepath"]
scene.render.film_transparent = original_scene_state["film_transparent"]
scene.render.image_settings.file_format = original_scene_state["file_format"]
scene.render.image_settings.color_mode = original_scene_state["color_mode"]
scene.render.image_settings.color_depth = original_scene_state["color_depth"]
scene.view_settings.view_transform = original_scene_state["view_transform"]
scene.view_settings.look = original_scene_state["look"]
scene.view_settings.exposure = original_scene_state["exposure"]
scene.view_settings.gamma = original_scene_state["gamma"]
if world is not original_scene_state["world"] and world.users == 0:
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
