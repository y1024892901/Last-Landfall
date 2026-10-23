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

MODEL_COLLECTION_NAME = "MedicalTent_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_MedicalTent_DeepSeek"
MATERIAL_PREFIX = "MedicalTent_DeepSeek_"

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
        mat.blend_method = 'BLEND'
        
    return mat

# Colors based on reference descriptions
mat_canvas = create_material("CanvasIvory", (0.85, 0.82, 0.75, 1.0), roughness=0.9)
mat_canvas_teal = create_material("CanvasTeal", (0.5, 0.7, 0.7, 1.0), roughness=0.9)
mat_wood = create_material("LightWood", (0.6, 0.5, 0.4, 1.0), roughness=0.9)
mat_wood_dark = create_material("CharredWood", (0.2, 0.15, 0.1, 1.0), roughness=0.9)
mat_iron = create_material("IronFittings", (0.12, 0.12, 0.14, 1.0), roughness=0.5, metallic=0.8)
mat_cross = create_material("MedicalCross", (0.9, 0.5, 0.5, 1.0), roughness=0.7)
mat_bed = create_material("BedCanvas", (0.4, 0.6, 0.6, 1.0), roughness=0.9)
mat_bag = create_material("MedicalBag", (0.3, 0.4, 0.3, 1.0), roughness=0.8)

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

def add_xz_prism(name, outline, y, depth, mat, parent_col):
    """Create a closed, thin fabric panel from a polygon in the X/Z plane."""
    count = len(outline)
    verts = [(x, y - depth * 0.5, z) for x, z in outline]
    verts += [(x, y + depth * 0.5, z) for x, z in outline]
    faces = [tuple(range(count)), tuple(range(count, count * 2))[::-1]]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, j + count, i + count))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    parent_col.objects.link(obj)
    apply_flat_shading(obj)
    return obj

# ==========================================
# 4. Modeling Components
# ==========================================

# Dimensions Plan:
# Platform: 2.0 (X) x 1.9 (Y) x 0.15 (Z)
# Ridge: Z = 2.15
# Entrance: -Y
# Total Height: 2.25 (including ridge beam and canvas thickness)

# --- 4.1 Foundation / Platform ---
# Corner Footings
foot_pos = [(-0.95, -0.9), (0.95, -0.9), (-0.95, 0.9), (0.95, 0.9)]
for i, (x, y) in enumerate(foot_pos):
    add_box(f"Platform_Footing_{i}", (0.15, 0.15, 0.1), (x, y, 0.05), mat_wood_dark, model_col)

# Base Beams
add_box("Platform_Beam_L", (0.1, 1.9, 0.1), (-0.95, 0, 0.15), mat_wood, model_col)
add_box("Platform_Beam_R", (0.1, 1.9, 0.1), (0.95, 0, 0.15), mat_wood, model_col)
add_box("Platform_Beam_F", (2.0, 0.1, 0.1), (0, -0.9, 0.15), mat_wood, model_col)
add_box("Platform_Beam_B", (2.0, 0.1, 0.1), (0, 0.9, 0.15), mat_wood, model_col)

# Deck Planks (along Y)
for i in range(9):
    x_pos = -0.85 + i * 0.2125
    add_box(f"Platform_Plank_{i}", (0.2, 1.8, 0.05), (x_pos, 0, 0.225), mat_wood, model_col)

# --- 4.2 A-Frame Structure ---
# Ridge Beam
ridge_z = 2.15
add_box("Frame_RidgeBeam", (0.1, 2.1, 0.1), (0, 0, ridge_z), mat_wood_dark, model_col)

# Front A-Frame (-Y)
# Legs go from (X=±0.9, Y=-0.9, Z=0.25) to (X=0, Y=-0.9, Z=2.15)
add_pipe("Frame_Leg_F_L", (-0.9, -0.9, 0.25), (0, -0.9, ridge_z), 0.06, mat_wood_dark, model_col)
add_pipe("Frame_Leg_F_R", (0.9, -0.9, 0.25), (0, -0.9, ridge_z), 0.06, mat_wood_dark, model_col)

# Back A-Frame (+Y)
add_pipe("Frame_Leg_B_L", (-0.9, 0.9, 0.25), (0, 0.9, ridge_z), 0.06, mat_wood_dark, model_col)
add_pipe("Frame_Leg_B_R", (0.9, 0.9, 0.25), (0, 0.9, ridge_z), 0.06, mat_wood_dark, model_col)

# Side rails and crossed braces sit below the roof slope and meet the A-frame legs.
for side in (-1, 1):
    x = side * 0.46
    for end in (-1, 1):
        add_box(f"Frame_SidePost_{side}_{end}", (0.055, 0.055, 0.92), (x, end * 0.88, 0.71), mat_wood_dark, model_col)
    add_box(f"Frame_Rail_{side}", (0.05, 1.76, 0.05), (x, 0, 1.14), mat_wood, model_col)
    add_pipe(f"Frame_Brace_{side}_A", (x, -0.88, 0.30), (x, 0.88, 1.10), 0.024, mat_wood, model_col)
    add_pipe(f"Frame_Brace_{side}_B", (x, 0.88, 0.30), (x, -0.88, 1.10), 0.024, mat_wood, model_col)

# --- 4.3 Canvas Roof ---
# We use a slight thickness (0.02) for the canvas
# Roof dimensions: width is roughly sqrt(0.9^2 + 1.9^2) = 2.1. Length is 2.0.
canvas_len = math.sqrt(0.9**2 + (ridge_z - 0.25)**2)
canvas_angle = math.atan2(ridge_z - 0.25, 0.9)

# Left Slope
add_box("Canvas_Roof_L", (canvas_len, 2.0, 0.02), (-0.45, 0, (ridge_z + 0.25)/2), mat_canvas, model_col, rot=(0, -canvas_angle, 0))
# Right Slope
add_box("Canvas_Roof_R", (canvas_len, 2.0, 0.02), (0.45, 0, (ridge_z + 0.25)/2), mat_canvas, model_col, rot=(0, canvas_angle, 0))

# Back Wall (+Y)
add_xz_prism("Canvas_Back", [(-0.9, 0.25), (0.9, 0.25), (0, ridge_z - 0.03)], 0.9, 0.025, mat_canvas, model_col)

# Front Wall (-Y) with Entrance Opening
# Triangular side panels leave a usable central doorway open.
add_xz_prism("Canvas_Flap_L", [(-0.9, 0.25), (0, ridge_z - 0.03), (-0.36, 1.48), (-0.36, 0.25)], -0.9, 0.025, mat_canvas, model_col)
add_xz_prism("Canvas_Flap_R", [(0, ridge_z - 0.03), (0.9, 0.25), (0.36, 0.25), (0.36, 1.48)], -0.9, 0.025, mat_canvas, model_col)
# Folded teal door flap is tied to one side so the entrance remains clear.
add_box("Canvas_InnerCurtain", (0.13, 0.035, 1.22), (0.29, -0.87, 0.86), mat_canvas_teal, model_col)
add_box("Canvas_FlapTie", (0.19, 0.055, 0.045), (0.29, -0.91, 1.40), mat_wood_dark, model_col)

# --- 4.4 Medical Sign (Front) ---
# Sign Board
sign_y = -0.92
sign_z = 1.65
add_box("Frame_SignSupport", (0.52, 0.08, 0.07), (0, -0.9, 1.88), mat_wood_dark, model_col)
add_box("MedicalSign_Board", (0.4, 0.05, 0.4), (0, sign_y, sign_z), mat_wood, model_col)
# Cross (Vertical)
add_box("MedicalSign_CrossV", (0.1, 0.06, 0.25), (0, sign_y - 0.02, sign_z), mat_cross, model_col)
# Cross (Horizontal)
add_box("MedicalSign_CrossH", (0.25, 0.06, 0.1), (0, sign_y - 0.02, sign_z), mat_cross, model_col)

# --- 4.5 Interior Items ---
# Folding Bed / Stretcher
bed_x = 0.0
bed_y = 0
bed_z = 0.25
# Bed legs
for x in [-0.25, 0.25]:
    for y in [-0.6, 0.6]:
        add_box(f"Bed_Leg_{x}_{y}", (0.05, 0.05, 0.3), (x, y, 0.25 + 0.15), mat_iron, model_col)
# Bed frame
add_box("Bed_Frame", (0.7, 1.4, 0.05), (bed_x, bed_y, bed_z + 0.3), mat_iron, model_col)
# Teal mattress
add_box("Bed_Mattress", (0.65, 1.35, 0.1), (bed_x, bed_y, bed_z + 0.35), mat_bed, model_col)

# Medical Bag (on the right side)
bag_x = 0.5
bag_y = 0.5
bag_z = 0.25
add_box("MedicalBag_Body", (0.3, 0.2, 0.2), (bag_x, bag_y, bag_z + 0.1), mat_bag, model_col)
# Handle
bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.015, location=(bag_x, bag_y, bag_z + 0.22), rotation=(math.radians(90), 0, 0))
handle = bpy.context.active_object
handle.name = "MedicalBag_Handle"
handle.data.materials.append(mat_iron)
for c in handle.users_collection:
    c.objects.unlink(handle)
model_col.objects.link(handle)
apply_flat_shading(handle)

# --- 4.6 Side Supply Crate ---
# Placed on the platform, tucked to the side
crate_x = 0.7
crate_y = -0.5
crate_z = 0.25
add_box("SideCrate_Base", (0.3, 0.4, 0.25), (crate_x, crate_y, crate_z + 0.125), mat_wood, model_col)
add_box("SideCrate_Lid", (0.32, 0.42, 0.05), (crate_x, crate_y, crate_z + 0.275), mat_wood_dark, model_col)
# Straps
add_box("SideCrate_Strap", (0.05, 0.44, 0.3), (crate_x - 0.1, crate_y, crate_z + 0.15), mat_iron, model_col)

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

# Hide scene objects outside this asset while rendering, then restore their state.
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

center_z = 1.1
scale_factor = 3.2

# True Orthographic Views
render_view((0, -10, center_z), (math.radians(90), 0, 0), scale_factor, "MedicalTent_DeepSeek_Front.png")
render_view((0, 10, center_z), (math.radians(90), 0, math.radians(180)), scale_factor, "MedicalTent_DeepSeek_Back.png")
render_view((-10, 0, center_z), (math.radians(90), 0, math.radians(-90)), scale_factor, "MedicalTent_DeepSeek_Left.png")
render_view((10, 0, center_z), (math.radians(90), 0, math.radians(90)), scale_factor, "MedicalTent_DeepSeek_Right.png")
render_view((0, 0, 10), (0, 0, 0), scale_factor, "MedicalTent_DeepSeek_Top.png")
render_view((0, 0, -10), (math.radians(180), 0, 0), scale_factor, "MedicalTent_DeepSeek_Bottom.png")

# 3/4 Preview
cam.location = (4, -5, 4)
look_target = Vector((0, 0, 1.0))
direction = look_target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 3.5
scene.render.filepath = str(PREVIEW_DIR / "MedicalTent_DeepSeek.png")
bpy.ops.render.render(write_still=True)

# ==========================================
# 7. Export FBX & Save Blend
# ==========================================
bpy.ops.object.select_all(action='DESELECT')
for obj in model_col.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

fbx_path = FBX_DIR / "MedicalTent_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True
)

blend_path = BLEND_DIR / "MedicalTent_DeepSeek.blend"
# Restore every temporary scene change before saving the editable source file.
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
