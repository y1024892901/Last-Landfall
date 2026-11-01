import bpy
import bmesh
import math
from mathutils import Vector
from pathlib import Path

# ==========================================
# 1. Setup and Path Management
# ==========================================
PROJECT_ROOT = Path.cwd()
SOURCE_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Buildings"
FBX_DIR = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Buildings"
PREVIEW_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Previews/Buildings"
QA_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"

for d in [SOURCE_DIR, FBX_DIR, PREVIEW_DIR, QA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Remove Blender's stock startup objects only when the script is running in a
# fresh, unsaved scene. A loaded user scene is left intact.
if not bpy.data.filepath:
    for stock_name in ("Cube", "Camera", "Light"):
        stock_obj = bpy.data.objects.get(stock_name)
        if stock_obj is not None:
            bpy.data.objects.remove(stock_obj, do_unlink=True)

COLLECTION_NAME = "DesalinationPlant_DeepSeek"
HELPER_COLLECTION_NAME = "Render_Helpers_Desalination"

# Clean up previous runs
for col_name in [COLLECTION_NAME, HELPER_COLLECTION_NAME]:
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

# Create new collections
root_collection = bpy.data.collections.new(COLLECTION_NAME)
bpy.context.scene.collection.children.link(root_collection)

helper_collection = bpy.data.collections.new(HELPER_COLLECTION_NAME)
bpy.context.scene.collection.children.link(helper_collection)

# ==========================================
# 2. Materials
# ==========================================
def create_material(name, color, roughness=0.8, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Clear default nodes
        for node in nodes:
            nodes.remove(node)
            
        # Create explicit nodes
        out_node = nodes.new(type='ShaderNodeOutputMaterial')
        bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
        
        bsdf_node.inputs['Base Color'].default_value = color
        bsdf_node.inputs['Roughness'].default_value = roughness
        bsdf_node.inputs['Metallic'].default_value = metallic
        
        links.new(bsdf_node.outputs['BSDF'], out_node.inputs['Surface'])
    return mat

mat_concrete = create_material("PaleConcrete", (0.48, 0.45, 0.40, 1.0), roughness=0.95)
mat_cedar = create_material("SunBleachedCedar", (0.38, 0.25, 0.14, 1.0), roughness=0.9)
mat_seagreen = create_material("SeaGreenEnamel", (0.16, 0.32, 0.33, 1.0), roughness=0.4, metallic=0.2)
mat_iron = create_material("DarkIron", (0.1, 0.1, 0.12, 1.0), roughness=0.6, metallic=0.8)
mat_rust = create_material("RustCopper", (0.5, 0.25, 0.1, 1.0), roughness=0.7, metallic=0.4)
mat_valve = create_material("ValveRed", (0.7, 0.15, 0.1, 1.0), roughness=0.5)
mat_gauge = create_material("GaugeFace", (0.9, 0.9, 0.85, 1.0), roughness=0.2)

# ==========================================
# 3. Helper Functions
# ==========================================
def apply_flat_shading(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = False

def add_box(name, size, location, mat, col, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    obj.data.materials.append(mat)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    apply_flat_shading(obj)
    return obj

def add_cylinder(name, radius, depth, location, mat, col, rot=(0,0,0), verts=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=location, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    apply_flat_shading(obj)
    return obj

def add_pipe(name, start, end, radius, mat, col, verts=8):
    start_v = Vector(start)
    end_v = Vector(end)
    mid = (start_v + end_v) / 2
    length = (end_v - start_v).length
    direction = end_v - start_v
    
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=length, location=mid)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = direction.to_track_quat('Z', 'Y')
    
    obj.data.materials.append(mat)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    apply_flat_shading(obj)
    return obj

def add_valve_wheel(name, location, mat, col, rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.015, location=location, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    apply_flat_shading(obj)
    
    # Hub
    add_cylinder(f"{name}_Hub", 0.02, 0.04, location, mat, col, rot=rot, verts=8)
    # Spokes
    for i in range(3):
        angle = math.radians(i * 60)
        spk_loc = Vector(location)
        spk_rot = (rot[0], rot[1], rot[2] + angle)
        add_box(f"{name}_Spoke_{i}", (0.15, 0.01, 0.01), spk_loc, mat, col, rot=spk_rot)

def add_gauge(name, location, mat_body, mat_face, col, rot=(math.radians(90), 0, 0)):
    add_cylinder(f"{name}_Body", 0.05, 0.04, location, mat_body, col, rot=rot, verts=12)
    add_cylinder(f"{name}_Face", 0.045, 0.045, location, mat_face, col, rot=rot, verts=12)
    # Stem
    stem_loc = (location[0], location[1] + 0.03, location[2] - 0.05)
    add_cylinder(f"{name}_Stem", 0.015, 0.1, stem_loc, mat_body, col, verts=8)

# ==========================================
# 4. Modeling Components
# ==========================================

# --- 4.1 Base and Skid ---
# Concrete Feet
feet_pos = [(-1.25, -0.8, 0.1), (1.25, -0.8, 0.1), (-1.25, 0.8, 0.1), (1.25, 0.8, 0.1)]
for i, pos in enumerate(feet_pos):
    add_box(f"Concrete_Foot_{i}", (0.3, 0.3, 0.2), pos, mat_concrete, root_collection)

# Timber Skid
add_box("Skid_Long_Left", (2.8, 0.15, 0.15), (0, -0.8, 0.275), mat_cedar, root_collection)
add_box("Skid_Long_Right", (2.8, 0.15, 0.15), (0, 0.8, 0.275), mat_cedar, root_collection)
add_box("Skid_Cross_Front", (0.15, 1.75, 0.15), (-1.25, 0, 0.275), mat_cedar, root_collection)
add_box("Skid_Cross_Back", (0.15, 1.75, 0.15), (1.25, 0, 0.275), mat_cedar, root_collection)
add_box("Skid_Cross_Mid", (0.15, 1.75, 0.15), (0, 0, 0.275), mat_cedar, root_collection)
add_box("Skid_Deck", (2.7, 1.6, 0.05), (0, 0, 0.375), mat_cedar, root_collection)

# --- 4.2 Frame and Canopy ---
# Vertical Posts
post_pos = [(-1.25, -0.8), (1.25, -0.8), (-1.25, 0.8), (1.25, 0.8)]
for i, (x, y) in enumerate(post_pos):
    add_box(f"Post_{i}", (0.15, 0.15, 1.8), (x, y, 1.3), mat_cedar, root_collection)

# Frame crossbars
add_box("Frame_Top_Front", (2.65, 0.1, 0.1), (0, -0.8, 2.15), mat_cedar, root_collection)
add_box("Frame_Top_Back", (2.65, 0.1, 0.1), (0, 0.8, 2.15), mat_cedar, root_collection)
add_box("Frame_Top_Left", (0.1, 1.7, 0.1), (-1.25, 0, 2.15), mat_cedar, root_collection)
add_box("Frame_Top_Right", (0.1, 1.7, 0.1), (1.25, 0, 2.15), mat_cedar, root_collection)

# Slanted Canopy
canopy_rot = (math.radians(-6), 0, 0)
add_box("Canopy_Beam_1", (2.7, 0.09, 0.08), (0, -0.6, 2.23), mat_cedar, root_collection, rot=canopy_rot)
add_box("Canopy_Beam_2", (2.7, 0.09, 0.08), (0, 0.6, 2.23), mat_cedar, root_collection, rot=canopy_rot)
# Planks
for i in range(5):
    y_pos = -0.8 + i * 0.4
    z_pos = 2.23 + (y_pos * math.tan(math.radians(6)))
    add_box(f"Canopy_Plank_{i}", (2.7, 0.35, 0.05), (0, y_pos, z_pos), mat_cedar, root_collection, rot=canopy_rot)

# --- 4.3 Main Components ---
# Horizontal Pressure Membranes
for i in range(2):
    z = 1.15 + i * 0.48
    # Main cylinder
    add_cylinder(f"Membrane_{i}", 0.18, 1.4, (0, 0, z), mat_seagreen, root_collection, rot=(0, math.radians(90), 0), verts=16)
    # End caps
    add_cylinder(f"Membrane_{i}_CapL", 0.20, 0.1, (-0.7, 0, z), mat_iron, root_collection, rot=(0, math.radians(90), 0), verts=16)
    add_cylinder(f"Membrane_{i}_CapR", 0.20, 0.1, (0.7, 0, z), mat_iron, root_collection, rot=(0, math.radians(90), 0), verts=16)
    # Bands
    add_cylinder(f"Membrane_{i}_Band1", 0.19, 0.05, (-0.4, 0, z), mat_rust, root_collection, rot=(0, math.radians(90), 0), verts=16)
    add_cylinder(f"Membrane_{i}_Band2", 0.19, 0.05, (0.4, 0, z), mat_rust, root_collection, rot=(0, math.radians(90), 0), verts=16)
    
    # Supports for membranes
    add_box(f"Membrane_{i}_SupportL", (0.1, 0.2, 0.1), (-0.5, 0, z-0.18), mat_cedar, root_collection)
    add_box(f"Membrane_{i}_SupportR", (0.1, 0.2, 0.1), (0.5, 0, z-0.18), mat_cedar, root_collection)

# Vertical Pre-filter
add_cylinder("PreFilter_Body", 0.18, 0.8, (-1.0, 0, 0.8), mat_seagreen, root_collection, verts=12)
add_cylinder("PreFilter_Top", 0.2, 0.1, (-1.0, 0, 1.25), mat_iron, root_collection, verts=12)
add_cylinder("PreFilter_Bottom", 0.2, 0.1, (-1.0, 0, 0.35), mat_iron, root_collection, verts=12)
# Filter mount
add_box("PreFilter_Mount", (0.3, 0.3, 0.1), (-1.0, 0, 0.4), mat_cedar, root_collection)

# Pump and Motor
add_box("Pump_Base", (0.5, 0.4, 0.2), (0.5, 0, 0.5), mat_iron, root_collection)
add_cylinder("Pump_Motor", 0.15, 0.4, (0.5, 0, 0.7), mat_seagreen, root_collection, rot=(0, math.radians(90), 0), verts=12)
add_cylinder("Pump_Head", 0.18, 0.2, (0.2, 0, 0.5), mat_iron, root_collection, rot=(0, math.radians(90), 0), verts=12)

# --- 4.4 Piping and Valves ---
# Intake (Left side)
add_pipe("Pipe_Intake_1", (-1.4, 0, 0.6), (-1.0, 0, 0.6), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Intake_2", (-1.0, 0, 0.6), (-1.0, 0, 0.35), 0.06, mat_iron, root_collection)

# Pre-filter to Pump
add_pipe("Pipe_Filter_Out", (-1.0, 0, 0.35), (0.1, 0, 0.35), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Pump_In", (0.1, 0, 0.35), (0.1, 0, 0.5), 0.06, mat_iron, root_collection)

# Pump to Membranes (Right side)
add_pipe("Pipe_Pump_Out", (0.7, 0, 0.5), (0.8, 0, 0.5), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Membrane_In", (0.8, 0, 0.5), (0.8, 0, 1.15), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Membrane_In_2", (0.8, 0, 1.15), (0.75, 0, 1.15), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Membrane_Bridge", (0.8, 0, 1.15), (0.8, 0, 1.63), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Membrane_In_3", (0.8, 0, 1.63), (0.75, 0, 1.63), 0.06, mat_iron, root_collection)

# Membranes to Outlet (Left side)
add_pipe("Pipe_Membrane_Out", (-0.70, 0, 1.15), (-0.70, 0.45, 1.15), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Outlet_Elbow_Back", (-0.70, 0.45, 1.15), (-1.15, 0.45, 1.15), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Outlet_Drop", (-1.15, 0.45, 1.15), (-1.15, 0.45, 0.9), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Outlet_Run", (-1.15, 0.45, 0.9), (1.3, 0.45, 0.9), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Outlet_Point", (1.3, 0.45, 0.9), (1.48, 0.45, 0.9), 0.06, mat_iron, root_collection) # Connects to the camp tank
# Stanchions support the treated-water manifold above the skid deck.
for i, x in enumerate((-0.4, 0.0, 1.0)):
    add_box(f"Pipe_Outlet_Stand_{i}", (0.07, 0.07, 0.47), (x, 0.45, 0.635), mat_iron, root_collection)
# Join the upper membrane outlet to the same treated-water manifold.
add_pipe("Pipe_Membrane_Out_Bridge", (-0.70, 0, 1.63), (-0.70, 0.45, 1.63), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Membrane_Out_Elbow_Back", (-0.70, 0.45, 1.63), (-1.15, 0.45, 1.63), 0.06, mat_iron, root_collection)
add_pipe("Pipe_Membrane_Out_Drop", (-1.15, 0.45, 1.63), (-1.15, 0.45, 1.15), 0.06, mat_iron, root_collection)

# Valves
add_valve_wheel("Valve_Intake", (-1.2, 0, 0.6), mat_valve, root_collection, rot=(0, math.radians(90), 0))
add_valve_wheel("Valve_Outlet", (0.5, 0.45, 0.9), mat_valve, root_collection, rot=(0, math.radians(90), 0))

# Gauges
add_gauge("Gauge_PreFilter", (-1.0, -0.23, 1.1), mat_iron, mat_gauge, root_collection, rot=(math.radians(90), 0, 0))
add_gauge("Gauge_Outlet", (-0.5, -0.23, 1.15), mat_iron, mat_gauge, root_collection, rot=(math.radians(90), 0, 0))

# ==========================================
# 5. Quality Diagnostic Setup
# ==========================================
def calculate_bounds_and_diagnostics():
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
    
    mesh_objects = [obj for obj in root_collection.objects if obj.type == 'MESH']
    
    non_manifold_count = 0
    
    for obj in mesh_objects:
        # Bounds
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

    bounds = (
        max_x - min_x,
        max_y - min_y,
        max_z - min_z
    )
    
    print("\n--- Diagnostic Report ---")
    print(f"Mesh Object Count: {len(mesh_objects)}")
    print(f"World-Space Bounds (W, D, H): {bounds[0]:.3f} m, {bounds[1]:.3f} m, {bounds[2]:.3f} m")
    print(f"Minimum Z: {min_z:.3f} m")
    print(f"Non-Manifold Edges: {non_manifold_count}")
    print("Note: This basic topology diagnostic does not detect object-to-object intersections.")
    print("-------------------------\n")

# ==========================================
# 6. Render Preview
# ==========================================
scene = bpy.context.scene

# Use the engine enum verified on this Blender 5.2.2 installation.
scene.render.engine = 'BLENDER_EEVEE'

scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'

# World Background
world = bpy.data.worlds.get("World")
if not world:
    world = bpy.data.worlds.new("World")
    scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.85, 0.85, 0.85, 1.0) # Pale neutral
    bg_node.inputs[1].default_value = 0.65

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 1.8
sun.rotation_euler = (math.radians(45), math.radians(20), math.radians(30))
for c in sun.users_collection:
    c.objects.unlink(sun)
helper_collection.objects.link(sun)

bpy.ops.object.light_add(type='AREA', location=(-4, -4, 5))
area = bpy.context.active_object
area.data.energy = 180
area.data.size = 6
area.rotation_euler = (math.radians(60), 0, math.radians(-45))
for c in area.users_collection:
    c.objects.unlink(area)
helper_collection.objects.link(area)

# Camera
bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 3.8
cam.location = (4, -5, 3.5)
# Look at center (0,0,1.2)
direction = Vector((0, 0, 1.2)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
for c in cam.users_collection:
    c.objects.unlink(cam)
helper_collection.objects.link(cam)
scene.camera = cam

# Render six orthographic inspection views first.
qa_views = {
    "Front": Vector((0, -1, 0)),
    "Back": Vector((0, 1, 0)),
    "Left": Vector((-1, 0, 0)),
    "Right": Vector((1, 0, 0)),
    "Top": Vector((0, 0, 1)),
    "Bottom": Vector((0, 0, -1)),
}
qa_target = Vector((0, 0, 1.2))
scene.render.resolution_x = 512
scene.render.resolution_y = 512
cam.data.ortho_scale = 3.6
for view_name, view_direction in qa_views.items():
    cam.location = qa_target + view_direction * 7.0
    cam.rotation_euler = (qa_target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(QA_DIR / f"DesalinationPlant_DeepSeek_{view_name}.png")
    bpy.ops.render.render(write_still=True)

# Restore the three-quarter camera for the primary preview.
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
cam.data.ortho_scale = 3.8
cam.location = (4, -5, 3.5)
direction = Vector((0, 0, 1.2)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
preview_path = PREVIEW_DIR / "DesalinationPlant_DeepSeek.png"
scene.render.filepath = str(preview_path)
bpy.ops.render.render(write_still=True)

# ==========================================
# 7. Export FBX
# ==========================================
# Select only root collection objects
bpy.ops.object.select_all(action='DESELECT')
for obj in root_collection.objects:
    if obj.type == 'MESH':
        obj.select_set(True)

fbx_path = FBX_DIR / "DesalinationPlant_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH'},
    bake_space_transform=True
)

# ==========================================
# 8. Save Blend File
# ==========================================
blend_path = SOURCE_DIR / "DesalinationPlant_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# ==========================================
# 9. Run Diagnostics
# ==========================================
calculate_bounds_and_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved Preview to: {preview_path}")
