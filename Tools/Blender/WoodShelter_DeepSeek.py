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

MODEL_COLLECTION_NAME = "WoodShelter_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_WoodShelter_DeepSeek"
MATERIAL_PREFIX = "WoodShelter_DeepSeek_"

# Preserve the active scene state before replacing this script's previous
# collections or changing temporary render settings.
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
            # Keep any same-prefix material still used elsewhere untouched.
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
            bsdf_node.inputs['Emission Strength'].default_value = 0.8
    
    links.new(bsdf_node.outputs['BSDF'], out_node.inputs['Surface'])
    
    if alpha < 1.0:
        mat.blend_method = 'BLEND'
        
    return mat

mat_wood_light = create_material("WeatheredLightWood", (0.6, 0.5, 0.4, 1.0), roughness=0.9)
mat_wood_dark = create_material("TarDarkWood", (0.18, 0.14, 0.12, 1.0), roughness=0.9)
mat_canvas = create_material("CreamCanvas", (0.85, 0.82, 0.75, 1.0), roughness=1.0)
mat_patch = create_material("SeaGlassPatch", (0.3, 0.5, 0.5, 1.0), roughness=0.9)
mat_iron = create_material("DarkIron", (0.12, 0.12, 0.14, 1.0), roughness=0.5, metallic=0.8)
mat_amber = create_material("AmberLight", (0.8, 0.32, 0.08, 1.0), roughness=0.35, emission_color=(0.8, 0.32, 0.08, 1.0))
mat_rope = create_material("Rope", (0.55, 0.45, 0.3, 1.0), roughness=1.0)

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
# Width (X): 1.9m. Depth (Y): 1.7m. Height (Z): 1.7m.
# High side at -X; the roof descends toward +X.
# Front open towards -Y, Back wall at +Y.

# --- 4.1 Foundation & Floor ---
# Footings (4 corners)
footing_pos = [(-0.8, -0.7), (0.8, -0.7), (-0.8, 0.7), (0.8, 0.7)]
for i, (x, y) in enumerate(footing_pos):
    add_box(f"Foundation_Footing_{i}", (0.15, 0.15, 0.15), (x, y, 0.075), mat_wood_dark, model_col)

# Base Beams (along Y)
add_box("Foundation_Beam_L", (0.1, 1.5, 0.1), (-0.8, 0, 0.2), mat_wood_dark, model_col)
add_box("Foundation_Beam_R", (0.1, 1.5, 0.1), (0.8, 0, 0.2), mat_wood_dark, model_col)

# Cross Joists (along X)
add_box("Foundation_Joist_F", (1.7, 0.1, 0.1), (0, -0.7, 0.25), mat_wood_dark, model_col)
add_box("Foundation_Joist_B", (1.7, 0.1, 0.1), (0, 0.7, 0.25), mat_wood_dark, model_col)
add_box("Foundation_Joist_M", (1.7, 0.1, 0.1), (0, 0, 0.25), mat_wood_dark, model_col)

# Floor Planks (along Y)
for i in range(8):
    x_pos = -0.7 + i * 0.2
    add_box(f"Floor_Plank_{i}", (0.18, 1.6, 0.05), (x_pos, 0, 0.325), mat_wood_light, model_col)

# --- 4.2 Frame & Supports ---
# Corner Posts
# High side (-X)
add_box("Frame_Post_High_F", (0.1, 0.1, 1.3), (-0.8, -0.7, 0.35 + 0.65), mat_wood_dark, model_col)
add_box("Frame_Post_High_B", (0.1, 0.1, 1.3), (-0.8, 0.7, 0.35 + 0.65), mat_wood_dark, model_col)
# Low side (+X)
add_box("Frame_Post_Low_F", (0.1, 0.1, 0.7), (0.8, -0.7, 0.35 + 0.35), mat_wood_dark, model_col)
add_box("Frame_Post_Low_B", (0.1, 0.1, 0.7), (0.8, 0.7, 0.35 + 0.35), mat_wood_dark, model_col)

# Main Beams (along Y)
# High beam at -X, Z = 1.65. Low beam at +X, Z = 1.05.
add_box("Frame_Beam_High", (0.1, 1.7, 0.1), (-0.8, 0, 1.65), mat_wood_dark, model_col)
add_box("Frame_Beam_Low", (0.1, 1.7, 0.1), (0.8, 0, 1.05), mat_wood_dark, model_col)

# End Crossbars (along X) at the top
add_box("Frame_Cross_F_Top", (1.6, 0.1, 0.1), (0, -0.7, 1.35), mat_wood_light, model_col, rot=(0, math.atan2(0.6, 1.6), 0))
add_box("Frame_Cross_B_Top", (1.6, 0.1, 0.1), (0, 0.7, 1.35), mat_wood_light, model_col, rot=(0, math.atan2(0.6, 1.6), 0))

# A-frame side supports. The entrance at -Y and rear windbreak stay clear.
add_pipe("Brace_High_Front", (-0.8, -0.7, 0.35), (-0.8, 0.0, 1.65), 0.06, mat_wood_light, model_col)
add_pipe("Brace_High_Back", (-0.8, 0.7, 0.35), (-0.8, 0.0, 1.65), 0.06, mat_wood_light, model_col)
add_box("Brace_High_Tie", (0.1, 1.4, 0.08), (-0.8, 0.0, 0.8), mat_wood_light, model_col)
add_pipe("Brace_Low_Front", (0.8, -0.7, 0.35), (0.8, 0.0, 1.05), 0.06, mat_wood_light, model_col)
add_pipe("Brace_Low_Back", (0.8, 0.7, 0.35), (0.8, 0.0, 1.05), 0.06, mat_wood_light, model_col)
add_box("Brace_Low_Tie", (0.1, 1.4, 0.08), (0.8, 0.0, 0.65), mat_wood_light, model_col)

# --- 4.3 Canvas Roof ---
# Main canvas plane
canvas_len = math.sqrt(1.6**2 + 0.6**2) + 0.2 # add overhang
canvas_angle = math.atan2(0.6, 1.6)
roof_rotation = (0, canvas_angle, 0)
add_box("Roof_Canvas", (canvas_len, 1.7, 0.02), (0, 0, 1.38), mat_canvas, model_col, rot=roof_rotation)

# Canvas Patch
patch_local_offset = Vector((-0.2, 0.2, 0.02))
patch_location = Vector((0, 0, 1.38)) + Vector((patch_local_offset.x * math.cos(canvas_angle) + patch_local_offset.z * math.sin(canvas_angle), patch_local_offset.y, -patch_local_offset.x * math.sin(canvas_angle) + patch_local_offset.z * math.cos(canvas_angle)))
add_box("Roof_Patch", (0.4, 0.5, 0.025), patch_location, mat_patch, model_col, rot=roof_rotation)

# --- 4.4 Back Windbreaks (+Y) ---
# Vertical boards
for i in range(3):
    x_pos = -0.55 + i * 0.55
    add_box(f"Back_Windbreak_{i}", (0.25, 0.05, 0.9), (x_pos, 0.84, 0.35 + 0.45), mat_wood_light, model_col)
add_box("Back_Windbreak_Rail_Low", (1.6, 0.05, 0.05), (0, 0.84, 0.42), mat_wood_dark, model_col)
add_box("Back_Windbreak_Rail_High", (1.6, 0.05, 0.05), (0, 0.84, 1.21), mat_wood_dark, model_col)

# --- 4.5 Supply Crate ---
# Placed inside, on the left (-X), towards the back (+Y)
crate_x = -0.4
crate_y = 0.3
crate_z = 0.35 + 0.15
add_box("Crate_Base", (0.4, 0.4, 0.3), (crate_x, crate_y, crate_z), mat_wood_dark, model_col)
add_box("Crate_Lid", (0.42, 0.42, 0.05), (crate_x, crate_y, crate_z + 0.17), mat_wood_dark, model_col)
# Straps
add_box("Crate_Strap_X", (0.44, 0.05, 0.05), (crate_x, crate_y, crate_z + 0.2), mat_iron, model_col)
add_box("Crate_Strap_Y", (0.05, 0.44, 0.05), (crate_x, crate_y, crate_z + 0.2), mat_iron, model_col)

# --- 4.6 Amber Lantern ---
# Hanging from the low beam at the front (-Y)
lantern_x = 0.8
lantern_y = -0.5
lantern_z = 1.05
# Mount
add_box("Lantern_Mount", (0.1, 0.1, 0.05), (lantern_x, lantern_y, lantern_z), mat_iron, model_col)
# Chain/String
add_cylinder("Lantern_String", 0.01, 0.15, (lantern_x, lantern_y, lantern_z - 0.075), mat_iron, model_col, verts=6)
# Lantern Body
add_cylinder("Lantern_Body", 0.06, 0.15, (lantern_x, lantern_y, lantern_z - 0.2), mat_amber, model_col, verts=8)
# Cap
add_cylinder("Lantern_Cap", 0.08, 0.03, (lantern_x, lantern_y, lantern_z - 0.115), mat_iron, model_col, verts=8)

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

# Use a temporary render world so no pre-existing scene/world datablock changes.
world = bpy.data.worlds.new(f"{MATERIAL_PREFIX}TemporaryRenderWorld")
world.use_nodes = True
scene.world = world
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

# Isolate previews to this asset while preserving other scene objects and
# their visibility settings for the saved project.
for obj, _hide_render in original_render_visibility:
    obj.hide_render = True

def render_view(loc, rot, ortho_scale, filename):
    cam.location = loc
    cam.rotation_euler = rot
    cam.data.ortho_scale = ortho_scale
    scene.render.filepath = str(QA_DIR / filename)
    bpy.ops.render.render(write_still=True)

center_z = 0.85
scale_factor = 3.0

# True Orthographic Views
render_view((0, -10, center_z), (math.radians(90), 0, 0), scale_factor, "WoodShelter_DeepSeek_Front.png")
render_view((0, 10, center_z), (math.radians(90), 0, math.radians(180)), scale_factor, "WoodShelter_DeepSeek_Back.png")
render_view((-10, 0, center_z), (math.radians(90), 0, math.radians(-90)), scale_factor, "WoodShelter_DeepSeek_Left.png")
render_view((10, 0, center_z), (math.radians(90), 0, math.radians(90)), scale_factor, "WoodShelter_DeepSeek_Right.png")
render_view((0, 0, 10), (0, 0, 0), scale_factor, "WoodShelter_DeepSeek_Top.png")
render_view((0, 0, -10), (math.radians(180), 0, 0), scale_factor, "WoodShelter_DeepSeek_Bottom.png")

# 3/4 Preview
cam.location = (4, -5, 4)
look_target = Vector((0, 0, 0.85))
direction = look_target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 3.5
scene.render.filepath = str(PREVIEW_DIR / "WoodShelter_DeepSeek.png")
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

fbx_path = FBX_DIR / "WoodShelter_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True
)

blend_path = BLEND_DIR / "WoodShelter_DeepSeek.blend"

# Restore the scene state before saving the model file. Generated helper
# cameras and lights remain isolated in the helper collection.
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
