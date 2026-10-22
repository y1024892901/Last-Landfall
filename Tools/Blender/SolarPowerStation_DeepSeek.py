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

# Remove only Blender's untouched startup trio when running without a project.
if not bpy.data.filepath:
    startup_names = {obj.name for obj in bpy.context.scene.objects}
    if startup_names == {"Camera", "Cube", "Light"}:
        for startup_name in ("Cube", "Camera", "Light"):
            startup_obj = bpy.data.objects.get(startup_name)
            if startup_obj:
                bpy.data.objects.remove(startup_obj, do_unlink=True)

MODEL_COLLECTION_NAME = "SolarPowerStation_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_SolarPowerStation_DeepSeek"

# Clean up previous runs (idempotent)
for col_name in [MODEL_COLLECTION_NAME, HELPER_COLLECTION_NAME]:
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

# Create new collections
model_col = bpy.data.collections.new(MODEL_COLLECTION_NAME)
bpy.context.scene.collection.children.link(model_col)

helper_col = bpy.data.collections.new(HELPER_COLLECTION_NAME)
bpy.context.scene.collection.children.link(helper_col)

# ==========================================
# 2. Material Creation
# ==========================================
def create_material(name, base_color, roughness=0.8, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    for node in list(nodes):
        nodes.remove(node)
        
    out_node = nodes.new('ShaderNodeOutputMaterial')
    bsdf_node = nodes.new('ShaderNodeBsdfPrincipled')
    
    bsdf_node.inputs['Base Color'].default_value = base_color
    bsdf_node.inputs['Roughness'].default_value = roughness
    bsdf_node.inputs['Metallic'].default_value = metallic
    
    links.new(bsdf_node.outputs['BSDF'], out_node.inputs['Surface'])
    return mat

mat_concrete = create_material("SolarPowerStation_DeepSeek_Concrete", (0.7, 0.7, 0.68, 1.0), roughness=0.95)
mat_steel = create_material("SolarPowerStation_DeepSeek_Steel", (0.2, 0.22, 0.25, 1.0), roughness=0.6, metallic=0.7)
mat_glass = create_material("SolarPowerStation_DeepSeek_Glass", (0.05, 0.1, 0.2, 1.0), roughness=0.2, metallic=0.8)
mat_cell = create_material("SolarPowerStation_DeepSeek_CellLines", (0.7, 0.8, 0.85, 1.0), roughness=0.6, metallic=0.15)
mat_cabinet = create_material("SolarPowerStation_DeepSeek_Cabinet", (0.3, 0.42, 0.42, 1.0), roughness=0.7, metallic=0.3)
mat_amber = create_material("SolarPowerStation_DeepSeek_Amber", (0.9, 0.45, 0.1, 1.0), roughness=0.4)
mat_cable = create_material("SolarPowerStation_DeepSeek_Cable", (0.1, 0.1, 0.1, 1.0), roughness=0.9)

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

def add_pipe(name, start, end, radius, mat, parent_col, verts=6):
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

# --- 4.1 Concrete Pad ---
pad_w = 4.6
pad_d = 3.6
pad_h = 0.2  # Upper surface of the slab; keep all equipment coordinates referenced to this level.
pad_bottom = 0.08
pad_thickness = pad_h - pad_bottom
add_box("Foundation_Pad", (pad_w, pad_d, pad_thickness), (0, 0, (pad_h + pad_bottom)/2), mat_concrete, model_col)

# Four low plinths raise the electrical pad above damp ground. Their steel sole plates
# rest exactly on Z=0, while the visible underside rails carry the frame between plinths.
foundation_positions = [(-2.0, -1.5), (2.0, -1.5), (-2.0, 1.5), (2.0, 1.5)]
for i, (x, y) in enumerate(foundation_positions):
    add_box(f"Foundation_Underside_FootPlate_{i}", (0.44, 0.44, 0.02), (x, y, 0.01), mat_steel, model_col)
    add_box(f"Foundation_PlinthFoot_{i}", (0.38, 0.38, pad_bottom - 0.02), (x, y, (pad_bottom + 0.02)/2), mat_concrete, model_col)

for i, y in enumerate((-1.5, 1.5)):
    add_box(f"Foundation_Underside_Rail_X_{i}", (3.62, 0.08, 0.04), (0, y, 0.06), mat_steel, model_col)
for i, x in enumerate((-2.0, 2.0)):
    add_box(f"Foundation_Underside_Rail_Y_{i}", (0.08, 2.62, 0.04), (x, 0, 0.06), mat_steel, model_col)

# Expansion seams (simple indentations)
add_box("Foundation_Seam_X", (pad_w - 0.2, 0.012, 0.004), (0, 0, pad_h + 0.002), mat_steel, model_col)
add_box("Foundation_Seam_Y", (0.012, pad_d - 0.2, 0.004), (0, 0, pad_h + 0.002), mat_steel, model_col)

# Anchor bolts at corners
for x in [-2.0, 2.0]:
    for y in [-1.5, 1.5]:
        add_cylinder(f"Foundation_Anchor_{x}_{y}", 0.04, 0.05, (x, y, pad_h + 0.025), mat_steel, model_col)

# A sealed gland on each side of the pad shows the power cable's entry route from above and below.
add_cylinder("Pad_CableEntry_Underside", 0.10, 0.04, (0, 0.5, pad_bottom - 0.02), mat_steel, model_col, verts=12)
add_pipe("Conduit_Pad_Penetration", (0, 0.5, pad_h + 0.05), (0, 0.5, pad_bottom), 0.04, mat_cable, model_col)

# --- 4.2 Solar Panels & Racks ---
# 8 panels in 2 rows of 4. Tilted 18 degrees towards +Y.
# Dimensions: Panel is 1.0m wide, 1.4m long.

panel_w = 0.75
panel_l = 1.4
panel_t = 0.04
tilt_angle = math.radians(18)
tilt_sin = math.sin(tilt_angle)
tilt_cos = math.cos(tilt_angle)

# X positions for the 4 columns
x_positions = [-1.75, -0.9, 0.9, 1.75]
# Y positions for the 2 rows (Front row, Back row)
y_rows = [-0.9, 0.9]

for row_idx, y_center in enumerate(y_rows):
    for col_idx, x_center in enumerate(x_positions):
        # Panel Center height (approx)
        z_base = 0.8 + row_idx * 0.3
        
        # Calculate panel center based on tilt
        # The panel pivots around its center.
        panel_center = Vector((x_center, y_center, z_base))
        
        # 1. Panel Glass
        panel_glass = add_box(f"Panel_Glass_{row_idx}_{col_idx}", (panel_w - 0.06, panel_l - 0.06, panel_t), panel_center, mat_glass, model_col)
        panel_glass.rotation_euler = (tilt_angle, 0, 0)
        
        # 2. Panel Frame
        # We'll build the frame as 4 thin boxes attached to the glass
        # Easiest way is to create a slightly larger box, and then a slightly smaller glass box on top.
        # But since it's low poly, let's just use a frame base and put the glass on it.
        frame_base = add_box(f"Panel_Frame_{row_idx}_{col_idx}", (panel_w, panel_l, panel_t - 0.01), panel_center, mat_steel, model_col)
        frame_base.rotation_euler = (tilt_angle, 0, 0)
        
        # Push glass slightly up along the local Z axis of the panel
        local_up = Vector((0, -tilt_sin, tilt_cos))
        panel_glass.location += local_up * 0.015
        
        # 3. Silver Cell Dividers (Simple cross lines on top of glass)
        # Vertical divider (along local Y)
        div_v = add_box(f"Panel_Div_V_{row_idx}_{col_idx}", (0.02, panel_l - 0.1, 0.005), panel_center + local_up * 0.043, mat_cell, model_col)
        div_v.rotation_euler = (tilt_angle, 0, 0)
        # Horizontal divider (along local X)
        div_h = add_box(f"Panel_Div_H_{row_idx}_{col_idx}", (panel_w - 0.1, 0.02, 0.005), panel_center + local_up * 0.043, mat_cell, model_col)
        div_h.rotation_euler = (tilt_angle, 0, 0)

        # 4. Racks and Supports
        # We need 2 posts supporting the panel (front and back).
        # Front post is lower, back post is higher.
        
        # Calculate local offset for the posts (under the panel)
        # Front edge is at local Y = -panel_l/2, Back edge is at local Y = panel_l/2
        # Wait, the panel is rotated. The Y-axis of the panel points roughly towards +Y and +Z.
        # Let's calculate world positions of the front and back edges.
        
        front_edge_y = panel_center.y - (panel_l/2) * tilt_cos
        front_edge_z = panel_center.z - (panel_l/2) * tilt_sin
        
        back_edge_y = panel_center.y + (panel_l/2) * tilt_cos
        back_edge_z = panel_center.z + (panel_l/2) * tilt_sin
        
        # Place posts slightly inward from the edges
        post_offset = 0.1
        f_y = front_edge_y + post_offset * tilt_cos
        f_z = front_edge_z + post_offset * tilt_sin
        b_y = back_edge_y - post_offset * tilt_cos
        b_z = back_edge_z - post_offset * tilt_sin
        
        # Left and Right sides of the panel
        for side in [-1, 1]:
            x_post = x_center + side * (panel_w/2 - 0.1)
            
            # Front Post
            post_h_front = f_z - pad_h
            add_box(f"Rack_Post_F_{row_idx}_{col_idx}_{side}", (0.08, 0.08, post_h_front), (x_post, f_y, pad_h + post_h_front/2), mat_steel, model_col)
            # Back Post
            post_h_back = b_z - pad_h
            add_box(f"Rack_Post_B_{row_idx}_{col_idx}_{side}", (0.08, 0.08, post_h_back), (x_post, b_y, pad_h + post_h_back/2), mat_steel, model_col)
            
            # Diagonal brace (connecting front post to back post)
            brace_start = Vector((x_post, f_y, f_z - 0.1))
            brace_end = Vector((x_post, b_y, b_z - 0.1))
            add_pipe(f"Rack_Brace_{row_idx}_{col_idx}_{side}", brace_start, brace_end, 0.03, mat_steel, model_col)

        # Cross rails (along X) supporting the panel
        add_box(f"Rack_Rail_F_{row_idx}_{col_idx}", (panel_w, 0.05, 0.05), (x_center, f_y, f_z - 0.05), mat_steel, model_col)
        add_box(f"Rack_Rail_B_{row_idx}_{col_idx}", (panel_w, 0.05, 0.05), (x_center, b_y, b_z - 0.05), mat_steel, model_col)

        # Base plates
        for side in [-1, 1]:
            x_post = x_center + side * (panel_w/2 - 0.1)
            add_box(f"Rack_BasePlate_F_{row_idx}_{col_idx}_{side}", (0.15, 0.15, 0.02), (x_post, f_y, pad_h + 0.01), mat_steel, model_col)
            add_box(f"Rack_BasePlate_B_{row_idx}_{col_idx}_{side}", (0.15, 0.15, 0.02), (x_post, b_y, pad_h + 0.01), mat_steel, model_col)

# --- 4.3 Inverter/Battery Cabinet ---
# Placed centrally between the two rows. Y=0. Center X=0.
cab_w = 0.8
cab_d = 0.6
cab_h = 1.2
cab_pos = (0, 0, pad_h + cab_h/2)

add_box("Cabinet_Main", (cab_w, cab_d, cab_h), cab_pos, mat_cabinet, model_col)

# Cabinet Door (facing -Y)
add_box("Cabinet_Door", (cab_w - 0.1, 0.05, cab_h - 0.1), (0, -cab_d/2 - 0.025, cab_pos[2]), mat_cabinet, model_col)
# Hinges
add_box("Cabinet_Hinge_1", (0.05, 0.05, 0.1), (-cab_w/2 + 0.1, -cab_d/2 - 0.05, cab_pos[2] - 0.3), mat_steel, model_col)
add_box("Cabinet_Hinge_2", (0.05, 0.05, 0.1), (-cab_w/2 + 0.1, -cab_d/2 - 0.05, cab_pos[2] + 0.3), mat_steel, model_col)
# Handle
add_box("Cabinet_Handle", (0.05, 0.08, 0.15), (cab_w/2 - 0.1, -cab_d/2 - 0.05, cab_pos[2]), mat_steel, model_col)

# Ventilation Louvers (on left side)
for i in range(4):
    z_louv = cab_pos[2] - 0.3 + i * 0.15
    add_box(f"Cabinet_Louver_{i}", (0.02, 0.4, 0.05), (-cab_w/2 - 0.01, 0, z_louv), mat_steel, model_col)

# Status Lights (Amber) on door
add_box("Cabinet_Light_1", (0.05, 0.02, 0.05), (cab_w/2 - 0.2, -cab_d/2 - 0.06, cab_pos[2] + 0.4), mat_amber, model_col)
add_box("Cabinet_Light_2", (0.05, 0.02, 0.05), (cab_w/2 - 0.3, -cab_d/2 - 0.06, cab_pos[2] + 0.4), mat_steel, model_col) # Dark/Off light

# Electrical Disconnect Box (mounted on side or bottom)
add_box("Cabinet_Disconnect", (0.15, 0.15, 0.25), (cab_w/2 + 0.05, -cab_d/4, pad_h + 0.3), mat_steel, model_col)
add_box("Cabinet_Disconnect_Switch", (0.1, 0.05, 0.05), (cab_w/2 + 0.05, -cab_d/4 - 0.1, pad_h + 0.3), mat_amber, model_col)

# Cable Entry Point (Central on pad)
add_cylinder("Pad_CableEntry", 0.15, 0.05, (0, 0.5, pad_h + 0.025), mat_steel, model_col, verts=12)

# --- 4.4 Conduits ---
# Route cables from the back of the panels to the cabinet.
for col_idx, x_center in enumerate(x_positions):
    # We'll route from the back post of the front row and the back post of the back row.
    # Back post of back row (Y ~ 1.5)
    b_y_back = y_rows[1] + (panel_l/2) * tilt_cos - 0.1 * tilt_cos
    b_z_back = 0.8 + 0.3 + (panel_l/2) * tilt_sin - 0.1 * tilt_sin
    
    # Front post of back row
    f_y_back = y_rows[1] - (panel_l/2) * tilt_cos + 0.1 * tilt_cos
    f_z_back = 0.8 + 0.3 - (panel_l/2) * tilt_sin + 0.1 * tilt_sin

    # Route to central cabinet
    # Drop down from panel frame to pad, then route along pad to cabinet.
    start_p = Vector((x_center, b_y_back, b_z_back - 0.2))
    mid_p = Vector((x_center, b_y_back, pad_h + 0.03))
    end_p = Vector((x_center * 0.5, 0, pad_h + 0.03)) # Converge towards center
    
    add_pipe(f"Conduit_Back_Drop_{col_idx}", start_p, mid_p, 0.03, mat_cable, model_col)
    add_pipe(f"Conduit_Back_Pad_{col_idx}", mid_p, end_p, 0.03, mat_cable, model_col)
    
    # Route from front row
    b_y_front = y_rows[0] + (panel_l/2) * tilt_cos - 0.1 * tilt_cos
    b_z_front = 0.8 + (panel_l/2) * tilt_sin - 0.1 * tilt_sin
    
    start_p_f = Vector((x_center, b_y_front, b_z_front - 0.2))
    mid_p_f = Vector((x_center, b_y_front, pad_h + 0.03))
    end_p_f = Vector((x_center * 0.5, 0, pad_h + 0.03))
    
    add_pipe(f"Conduit_Front_Drop_{col_idx}", start_p_f, mid_p_f, 0.03, mat_cable, model_col)
    add_pipe(f"Conduit_Front_Pad_{col_idx}", mid_p_f, end_p_f, 0.03, mat_cable, model_col)

# Connect cabinet to pad entry
add_pipe("Conduit_Cabinet_to_Entry", (0, 0.3, pad_h + 0.03), (0, 0.5, pad_h + 0.03), 0.04, mat_cable, model_col)


# ==========================================
# 5. Quality Diagnostic Setup
# ==========================================
def calculate_bounds_and_diagnostics():
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
    
    mesh_objects = [obj for obj in model_col.objects if obj.type == 'MESH']
    non_manifold_count = 0
    
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
original_scene_state = {
    "engine": scene.render.engine,
    "resolution_x": scene.render.resolution_x,
    "resolution_y": scene.render.resolution_y,
    "resolution_percentage": scene.render.resolution_percentage,
    "file_format": scene.render.image_settings.file_format,
    "film_transparent": scene.render.film_transparent,
    "filepath": scene.render.filepath,
    "view_transform": scene.view_settings.view_transform,
    "world": scene.world,
    "camera": scene.camera,
}
model_objects = set(model_col.objects)
helper_objects = set(helper_col.objects)
external_render_state = {
    obj: obj.hide_render
    for obj in scene.objects
    if obj not in model_objects and obj not in helper_objects
}

for obj in external_render_state:
    obj.hide_render = True

try:
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE'

    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Standard'

    # Use an asset-owned temporary world instead of modifying the user's world.
    render_world = bpy.data.worlds.get("SolarPowerStation_DeepSeek_RenderWorld")
    if not render_world:
        render_world = bpy.data.worlds.new("SolarPowerStation_DeepSeek_RenderWorld")
    render_world.use_nodes = True
    bg_node = render_world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs[0].default_value = (0.85, 0.85, 0.85, 1.0)
    scene.world = render_world

    # Lighting
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(45), math.radians(20), math.radians(30))
    for c in list(sun.users_collection):
        c.objects.unlink(sun)
    helper_col.objects.link(sun)

    bpy.ops.object.light_add(type='AREA', location=(-5, -6, 6))
    area = bpy.context.active_object
    area.data.energy = 500
    area.data.size = 10
    area.rotation_euler = (math.radians(60), 0, math.radians(-45))
    for c in list(area.users_collection):
        c.objects.unlink(area)
    helper_col.objects.link(area)

    # Camera
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.data.type = 'ORTHO'
    for c in list(cam.users_collection):
        c.objects.unlink(cam)
    helper_col.objects.link(cam)
    scene.camera = cam

    def render_view(loc, rot, ortho_scale, filename):
        cam.location = loc
        cam.rotation_euler = rot
        cam.data.ortho_scale = ortho_scale
        scene.render.filepath = str(QA_DIR / filename)
        underside_light = None
        if filename.endswith("_Bottom.png"):
            # The standard top lighting leaves downward-facing faces nearly black.
            # Add a temporary fill light so the underside QA image exposes the feet,
            # cross rails, and cable gland instead of only their silhouettes.
            bpy.ops.object.light_add(type='AREA', location=(0, 0, -4))
            underside_light = bpy.context.active_object
            underside_light.data.energy = 120
            underside_light.data.shape = 'DISK'
            underside_light.data.size = 5
            underside_light.rotation_euler = (math.radians(180), 0, 0)
            for collection in list(underside_light.users_collection):
                collection.objects.unlink(underside_light)
            helper_col.objects.link(underside_light)
        try:
            bpy.ops.render.render(write_still=True)
        finally:
            if underside_light:
                bpy.data.objects.remove(underside_light, do_unlink=True)

    center_z = 0.9
    scale_factor = 5.5

    # True Orthographic Views
    render_view((0, -20, center_z), (math.radians(90), 0, 0), scale_factor, "SolarPowerStation_DeepSeek_Front.png")
    render_view((0, 20, center_z), (math.radians(90), 0, math.radians(180)), scale_factor, "SolarPowerStation_DeepSeek_Back.png")
    render_view((-20, 0, center_z), (math.radians(90), 0, math.radians(-90)), scale_factor, "SolarPowerStation_DeepSeek_Left.png")
    render_view((20, 0, center_z), (math.radians(90), 0, math.radians(90)), scale_factor, "SolarPowerStation_DeepSeek_Right.png")
    render_view((0, 0, 20), (0, 0, 0), scale_factor, "SolarPowerStation_DeepSeek_Top.png")
    render_view((0, 0, -20), (math.radians(180), 0, 0), scale_factor, "SolarPowerStation_DeepSeek_Bottom.png")

    # 3/4 Preview
    cam.location = (8, -10, 8)
    look_target = Vector((0, 0, 0.9))
    direction = look_target - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = 6.5
    scene.render.filepath = str(PREVIEW_DIR / "SolarPowerStation_DeepSeek.png")
    bpy.ops.render.render(write_still=True)
finally:
    scene.render.engine = original_scene_state["engine"]
    scene.render.resolution_x = original_scene_state["resolution_x"]
    scene.render.resolution_y = original_scene_state["resolution_y"]
    scene.render.resolution_percentage = original_scene_state["resolution_percentage"]
    scene.render.image_settings.file_format = original_scene_state["file_format"]
    scene.render.film_transparent = original_scene_state["film_transparent"]
    scene.render.filepath = original_scene_state["filepath"]
    scene.view_settings.view_transform = original_scene_state["view_transform"]
    scene.world = original_scene_state["world"]
    original_camera = original_scene_state["camera"]
    scene.camera = original_camera if original_camera and original_camera.name in bpy.data.objects else None
    for obj, hide_render in external_render_state.items():
        if obj.name in bpy.data.objects:
            obj.hide_render = hide_render
    for helper_obj in helper_col.objects:
        helper_obj.hide_render = True

# ==========================================
# 7. Export FBX & Save Blend
# ==========================================
bpy.ops.object.select_all(action='DESELECT')
for obj in model_col.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

fbx_path = FBX_DIR / "SolarPowerStation_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True
)

blend_path = BLEND_DIR / "SolarPowerStation_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# ==========================================
# 8. Execute Diagnostics
# ==========================================
calculate_bounds_and_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved Previews to: {PREVIEW_DIR}")
print(f"Saved QA Renders to: {QA_DIR}")
