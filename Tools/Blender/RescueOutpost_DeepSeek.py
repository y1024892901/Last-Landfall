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

MODEL_COLLECTION_NAME = "RescueOutpost_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_RescueOutpost_DeepSeek"
MATERIAL_PREFIX = "RescueOutpost_DeepSeek_"

scene = bpy.context.scene
original_scene_state = {
    "camera": scene.camera,
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
def create_material(name, base_color, roughness=0.8, metallic=0.0, alpha=1.0, emission_color=None):
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
    
    if emission_color:
        # Handle Blender 4.x/5.x Emission API
        if 'Emission Color' in bsdf_node.inputs:
            bsdf_node.inputs['Emission Color'].default_value = emission_color
        elif 'Emission' in bsdf_node.inputs:
            bsdf_node.inputs['Emission'].default_value = emission_color
        
        if 'Emission Strength' in bsdf_node.inputs:
            bsdf_node.inputs['Emission Strength'].default_value = 2.0
    
    links.new(bsdf_node.outputs['BSDF'], out_node.inputs['Surface'])
    
    if alpha < 1.0:
        if hasattr(mat, 'surface_render_method'):
            mat.surface_render_method = 'DITHERED'
        else:
            mat.blend_method = 'BLEND'
        
    return mat

# Colors based on reference descriptions
mat_wood_light = create_material("WeatheredLightWood", (0.6, 0.5, 0.4, 1.0), roughness=0.9)
mat_wood_dark = create_material("TarDarkWood", (0.18, 0.14, 0.12, 1.0), roughness=0.9)
mat_metal_cyan = create_material("PaleCyanMetal", (0.6, 0.8, 0.8, 1.0), roughness=0.5, metallic=0.4)
mat_wall_green = create_material("SeaGreenWall", (0.25, 0.45, 0.45, 1.0), roughness=0.7)
mat_concrete = create_material("WarmGrayConcrete", (0.6, 0.6, 0.58, 1.0), roughness=0.95)
mat_iron = create_material("DarkIron", (0.12, 0.12, 0.14, 1.0), roughness=0.5, metallic=0.8)
mat_orange = create_material("RescueOrange", (0.8, 0.3, 0.1, 1.0), roughness=0.6)
mat_amber = create_material("AmberLight", (0.9, 0.5, 0.1, 1.0), roughness=0.2, emission_color=(0.9, 0.5, 0.1, 1.0))
mat_glass = create_material("SeaGlassWindow", (0.2, 0.4, 0.4, 0.4), roughness=0.1, alpha=0.4)

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
# Platform: ~1.7m (X) x 1.5m (Y), Z=2.2m.
# Pillars: X = +/- 0.85, Y = +/- 0.75.
# Stairs: Centered on X, starting from Y=-0.75, going to Y=-1.95.
# Cabin: X = +/- 0.65, Y = 0 to 1.2, Z from 2.3 to 3.5.
# Roof: Overhang to X= +/- 0.8, Y = -0.1 to 1.35, Z=3.6.
# Total Y: -1.95 to 1.35 = 3.3m (fits 3.4m limit).
# Total Z: Roof 3.6 + Mast/Light 0.5 = 4.1m (fits 4.2m limit).

# --- 4.1 Foundation & Pillars ---
pillar_positions = [(-0.85, -0.75), (0.85, -0.75), (-0.85, 0.75), (0.85, 0.75)]
for i, (x, y) in enumerate(pillar_positions):
    # Concrete Footing
    add_box(f"Foundation_Footing_{i}", (0.3, 0.3, 0.2), (x, y, 0.1), mat_concrete, model_col)
    # Dark Wood Pillar
    add_box(f"Pillar_Main_{i}", (0.15, 0.15, 2.2), (x, y, 1.1), mat_wood_dark, model_col)

# --- 4.2 Bracing ---
# Horizontal braces
for z in [0.8, 1.6]:
    # Left and Right sides (along Y)
    add_box(f"Brace_H_L_{z}", (0.08, 1.35, 0.08), (-0.85, 0, z), mat_wood_dark, model_col)
    add_box(f"Brace_H_R_{z}", (0.08, 1.35, 0.08), (0.85, 0, z), mat_wood_dark, model_col)
    # Front and Back sides (along X)
    add_box(f"Brace_H_F_{z}", (1.55, 0.08, 0.08), (0, -0.75, z), mat_wood_dark, model_col)
    add_box(f"Brace_H_B_{z}", (1.55, 0.08, 0.08), (0, 0.75, z), mat_wood_dark, model_col)

# Diagonal X-braces on left and right
add_pipe("Brace_X_L1", (-0.85, -0.75, 0.8), (-0.85, 0.75, 1.6), 0.06, mat_wood_dark, model_col)
add_pipe("Brace_X_L2", (-0.85, 0.75, 0.8), (-0.85, -0.75, 1.6), 0.06, mat_wood_dark, model_col)
add_pipe("Brace_X_R1", (0.85, -0.75, 0.8), (0.85, 0.75, 1.6), 0.06, mat_wood_dark, model_col)
add_pipe("Brace_X_R2", (0.85, 0.75, 0.8), (0.85, -0.75, 1.6), 0.06, mat_wood_dark, model_col)

# --- 4.3 Platform Deck ---
# Cross joists under deck
add_box("Platform_Joist_F", (0.1, 1.6, 0.1), (-0.7, 0, 2.15), mat_wood_dark, model_col)
add_box("Platform_Joist_B", (0.1, 1.6, 0.1), (0.7, 0, 2.15), mat_wood_dark, model_col)
add_box("Platform_Joist_M", (0.1, 1.6, 0.1), (0, 0, 2.15), mat_wood_dark, model_col)

# Deck Planks (running along X)
for i in range(9):
    y_pos = -0.7 + (i + 0.5) * (1.4 / 9)
    add_box(f"Platform_Plank_{i}", (1.7, 0.14, 0.08), (0, y_pos, 2.2), mat_wood_light, model_col)

# --- 4.4 Guardrails ---
rail_z = 2.2 + 0.45
rail_thick = 0.05

# Back and Side Rails
add_box("Rail_Back", (1.7, rail_thick, rail_thick), (0, 0.75, 2.2 + 0.9), mat_wood_light, model_col)
add_box("Rail_Left", (rail_thick, 1.5, rail_thick), (-0.85, 0, 2.2 + 0.9), mat_wood_light, model_col)
add_box("Rail_Right", (rail_thick, 1.5, rail_thick), (0.85, 0, 2.2 + 0.9), mat_wood_light, model_col)
add_box("Rail_Front_L", (0.6, rail_thick, rail_thick), (-0.55, -0.75, 2.2 + 0.9), mat_wood_light, model_col)
add_box("Rail_Front_R", (0.6, rail_thick, rail_thick), (0.55, -0.75, 2.2 + 0.9), mat_wood_light, model_col)

# Mid-rails
add_box("Rail_Mid_Back", (1.7, rail_thick, rail_thick), (0, 0.75, 2.2 + 0.5), mat_wood_light, model_col)
add_box("Rail_Mid_Left", (rail_thick, 1.5, rail_thick), (-0.85, 0, 2.2 + 0.5), mat_wood_light, model_col)
add_box("Rail_Mid_Right", (rail_thick, 1.5, rail_thick), (0.85, 0, 2.2 + 0.5), mat_wood_light, model_col)

# Vertical Posts
for x in [-0.85, 0.85]:
    for y in [-0.75, 0.75]:
        add_box(f"Rail_Post_{x}_{y}", (0.06, 0.06, 0.95), (x, y, 2.2 + 0.475), mat_wood_light, model_col)
# Front posts for stair entrance
add_box("Rail_Post_Front_L", (0.06, 0.06, 0.95), (-0.25, -0.75, 2.2 + 0.475), mat_wood_light, model_col)
add_box("Rail_Post_Front_R", (0.06, 0.06, 0.95), (0.25, -0.75, 2.2 + 0.475), mat_wood_light, model_col)

# --- 4.5 Stairs ---
# Stairs run from Y=-1.95/Z=0.05 to the platform edge at Y=-0.75/Z=2.16.
# Stringers and level treads follow the same rising direction.
stair_bottom_y, stair_top_y = -1.95, -0.75
stair_bottom_z, stair_top_z = 0.05, 2.16
stair_run = stair_top_y - stair_bottom_y
stair_rise = stair_top_z - stair_bottom_z
stair_len = math.sqrt(stair_run**2 + stair_rise**2)
stair_angle = math.atan2(stair_rise, stair_run)
stair_center_y = (stair_bottom_y + stair_top_y) / 2
stair_center_z = (stair_bottom_z + stair_top_z) / 2
add_box("Stair_Stringer_L", (0.08, stair_len, 0.12), (-0.3, stair_center_y, stair_center_z), mat_wood_dark, model_col, rot=(stair_angle, 0, 0))
add_box("Stair_Stringer_R", (0.08, stair_len, 0.12), (0.3, stair_center_y, stair_center_z), mat_wood_dark, model_col, rot=(stair_angle, 0, 0))

stair_steps = 8
for i in range(stair_steps):
    step_fraction = (i + 0.5) / stair_steps
    step_z = stair_bottom_z + step_fraction * stair_rise
    step_y = stair_bottom_y + step_fraction * stair_run
    add_box(f"Stair_Tread_{i + 1:02d}", (0.6, 0.18, 0.06), (0, step_y, step_z), mat_wood_light, model_col)

# --- 4.6 Cabin ---
cab_w = 1.3
cab_d = 1.2
cab_h = 1.2
cab_y_center = 0.6
cab_z_base = 2.2
cab_z_center = cab_z_base + cab_h/2

# Base Platform for Cabin
add_box("Cabin_Floor", (cab_w + 0.1, cab_d, 0.1), (0, cab_y_center, cab_z_base + 0.05), mat_wood_dark, model_col)

# Walls
# Back Wall (+Y)
add_box("Cabin_Wall_Back", (cab_w, 0.08, cab_h), (0, cab_y_center + cab_d/2, cab_z_center), mat_wall_green, model_col)
# Side walls have real openings for their observation windows.
for side_name, sign in (("Left", -1), ("Right", 1)):
    side_x = sign * cab_w/2
    add_box(f"Cabin_Wall_{side_name}_Below_Window", (0.08, cab_d, 0.4), (side_x, cab_y_center, cab_z_base + 0.2), mat_wall_green, model_col)
    add_box(f"Cabin_Wall_{side_name}_Above_Window", (0.08, cab_d, 0.4), (side_x, cab_y_center, cab_z_base + 1.0), mat_wall_green, model_col)
    add_box(f"Cabin_Wall_{side_name}_Front_Pier", (0.08, 0.3, 0.4), (side_x, 0.15, cab_z_base + 0.8), mat_wall_green, model_col)
    add_box(f"Cabin_Wall_{side_name}_Back_Pier", (0.08, 0.3, 0.4), (side_x, 1.05, cab_z_base + 0.8), mat_wall_green, model_col)

# Front Wall (-Y) with Door and Window
# Door: X=-0.4 to 0, Z=2.3 to 3.1.
# Window: X=0.1 to 0.5, Z=2.6 to 3.1.
# Left part (before door)
add_box("Cabin_Wall_Front_L", (0.25, 0.08, cab_h), (-cab_w/2 + 0.125, cab_y_center - cab_d/2, cab_z_center), mat_wall_green, model_col)
# Middle part (between door and window)
add_box("Cabin_Wall_Front_M", (0.1, 0.08, cab_h), (0.05, cab_y_center - cab_d/2, cab_z_center), mat_wall_green, model_col)
# Right part (after window)
add_box("Cabin_Wall_Front_R", (0.15, 0.08, cab_h), (0.575, cab_y_center - cab_d/2, cab_z_center), mat_wall_green, model_col)
# Above door
add_box("Cabin_Wall_Front_Top_D", (0.4, 0.08, 0.4), (-0.2, cab_y_center - cab_d/2, cab_z_base + 1.0), mat_wall_green, model_col)
# Below window
add_box("Cabin_Wall_Front_Bot_W", (0.4, 0.08, 0.4), (0.3, cab_y_center - cab_d/2, cab_z_base + 0.2), mat_wall_green, model_col)
# Above window
add_box("Cabin_Wall_Front_Top_W", (0.4, 0.08, 0.4), (0.3, cab_y_center - cab_d/2, cab_z_base + 1.0), mat_wall_green, model_col)

# Cabin Door
add_box("Cabin_Door", (0.38, 0.05, 0.8), (-0.2, cab_y_center - cab_d/2 - 0.05, cab_z_base + 0.4), mat_wood_light, model_col)
add_box("Cabin_Door_Handle", (0.04, 0.04, 0.1), (-0.05, cab_y_center - cab_d/2 - 0.08, cab_z_base + 0.4), mat_iron, model_col)

# Windows (Front and Sides)
# Front Window
add_box("Cabin_Window_Front", (0.38, 0.02, 0.4), (0.3, cab_y_center - cab_d/2 - 0.04, cab_z_base + 0.6), mat_glass, model_col)
for side_name, sign in (("Left", -1), ("Right", 1)):
    side_x = sign * (cab_w/2 + 0.045)
    add_box(f"Cabin_Window_{side_name}", (0.02, 0.54, 0.36), (side_x, cab_y_center, cab_z_base + 0.6), mat_glass, model_col)
    frame_x = sign * (cab_w/2 + 0.06)
    add_box(f"Cabin_Window_{side_name}_Frame_Front", (0.04, 0.04, 0.44), (frame_x, cab_y_center - 0.3, cab_z_base + 0.6), mat_wood_dark, model_col)
    add_box(f"Cabin_Window_{side_name}_Frame_Back", (0.04, 0.04, 0.44), (frame_x, cab_y_center + 0.3, cab_z_base + 0.6), mat_wood_dark, model_col)
    add_box(f"Cabin_Window_{side_name}_Frame_Bottom", (0.04, 0.64, 0.04), (frame_x, cab_y_center, cab_z_base + 0.38), mat_wood_dark, model_col)
    add_box(f"Cabin_Window_{side_name}_Frame_Top", (0.04, 0.64, 0.04), (frame_x, cab_y_center, cab_z_base + 0.82), mat_wood_dark, model_col)

# --- 4.7 Roof ---
roof_w = 1.6
roof_d = 1.5
roof_z = 3.45
add_box("Roof_Main", (roof_w, roof_d, 0.1), (0, cab_y_center, roof_z), mat_metal_cyan, model_col)

# Small roof trim/edge
add_box("Roof_Trim_F", (roof_w, 0.05, 0.15), (0, cab_y_center - roof_d/2, roof_z), mat_metal_cyan, model_col)
add_box("Roof_Trim_B", (roof_w, 0.05, 0.15), (0, cab_y_center + roof_d/2, roof_z), mat_metal_cyan, model_col)
add_box("Roof_Trim_L", (0.05, roof_d, 0.15), (-roof_w/2, cab_y_center, roof_z), mat_metal_cyan, model_col)
add_box("Roof_Trim_R", (0.05, roof_d, 0.15), (roof_w/2, cab_y_center, roof_z), mat_metal_cyan, model_col)

# --- 4.8 Roof Details ---
# Mast
mast_x = 0.4
mast_y = 0.8
mast_z = roof_z + 0.2
add_cylinder("Mast_Pole", 0.03, 0.5, (mast_x, mast_y, mast_z), mat_iron, model_col)

# Signal Light (Amber)
add_cylinder("Signal_Light_Base", 0.04, 0.05, (mast_x, mast_y, roof_z + 0.45), mat_iron, model_col)
add_cylinder("Signal_Light_Glass", 0.035, 0.08, (mast_x, mast_y, roof_z + 0.5), mat_amber, model_col, verts=8)
add_cylinder("Signal_Light_Cap", 0.055, 0.04, (mast_x, mast_y, roof_z + 0.55), mat_metal_cyan, model_col, verts=8)

# Antenna
ant_x = -0.4
ant_y = 0.8
add_pipe("Antenna_Pole", (ant_x, ant_y, roof_z), (ant_x, ant_y, roof_z + 0.6), 0.015, mat_iron, model_col)
add_box("Antenna_Tip", (0.04, 0.04, 0.04), (ant_x, ant_y, roof_z + 0.6), mat_iron, model_col)

# --- 4.9 Front Details ---
# Life Ring on Front Rail
ring_x = -0.55
ring_y = -0.78
ring_z = 2.2 + 0.65
bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.04, location=(ring_x, ring_y, ring_z), rotation=(math.radians(90), 0, 0))
life_ring = bpy.context.active_object
life_ring.name = "LifeRing"
life_ring.data.materials.append(mat_orange)
for c in life_ring.users_collection:
    c.objects.unlink(life_ring)
model_col.objects.link(life_ring)
apply_flat_shading(life_ring)
add_box("LifeRing_Hanger", (0.06, 0.06, 0.18), (ring_x, ring_y, ring_z + 0.19), mat_iron, model_col)

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

# Temporary world for QA renders. The original world is restored before saving.
world = bpy.data.worlds.new("RescueOutpost_DeepSeek_RenderWorld")
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

center_z = 2.0
scale_factor = 5.5

# True Orthographic Views
render_view((0, -15, center_z), (math.radians(90), 0, 0), scale_factor, "RescueOutpost_DeepSeek_Front.png")
render_view((0, 15, center_z), (math.radians(90), 0, math.radians(180)), scale_factor, "RescueOutpost_DeepSeek_Back.png")
render_view((-15, 0, center_z), (math.radians(90), 0, math.radians(-90)), scale_factor, "RescueOutpost_DeepSeek_Left.png")
render_view((15, 0, center_z), (math.radians(90), 0, math.radians(90)), scale_factor, "RescueOutpost_DeepSeek_Right.png")
render_view((0, 0, 15), (0, 0, 0), scale_factor, "RescueOutpost_DeepSeek_Top.png")
render_view((0, 0, -15), (math.radians(180), 0, 0), scale_factor, "RescueOutpost_DeepSeek_Bottom.png")

# 3/4 Preview
cam.location = (6, -8, 6)
look_target = Vector((0, -0.2, 2.0))
direction = look_target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 6.5
scene.render.filepath = str(PREVIEW_DIR / "RescueOutpost_DeepSeek.png")
bpy.ops.render.render(write_still=True)

# ==========================================
# 7. Export FBX & Save Blend
# ==========================================
bpy.ops.object.select_all(action='DESELECT')
for obj in model_col.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

fbx_path = FBX_DIR / "RescueOutpost_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True
)

blend_path = BLEND_DIR / "RescueOutpost_DeepSeek.blend"

# Restore the scene camera, world, and rendering settings before saving.
camera_name = original_scene_state["camera_name"]
scene.camera = bpy.data.objects.get(camera_name) if camera_name else None
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
