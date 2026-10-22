import bpy
import bmesh
import math
from mathutils import Vector
from pathlib import Path


# MedicalStation_DeepSeek — reviewed and refined from the DeepSeek draft.
PROJECT_ROOT = Path.cwd()
BLEND_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Buildings"
FBX_DIR = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Buildings"
PREVIEW_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Previews/Buildings"
QA_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"
for output_dir in (BLEND_DIR, FBX_DIR, PREVIEW_DIR, QA_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "MedicalStation_DeepSeek"
HELPER_NAME = "Helpers_MedicalStation_DeepSeek"


def replace_owned_collection(name):
    """Replace only this asset's exact collection; leave the rest of the scene alone."""
    old = bpy.data.collections.get(name)
    if old is None:
        return
    for child in list(old.children):
        old.children.unlink(child)
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)


replace_owned_collection(MODEL_NAME)
replace_owned_collection(HELPER_NAME)
scene = bpy.context.scene
model_col = bpy.data.collections.new(MODEL_NAME)
helper_col = bpy.data.collections.new(HELPER_NAME)
scene.collection.children.link(model_col)
scene.collection.children.link(helper_col)


def material(name, color, roughness=0.8, metallic=0.0):
    """Create or refresh only this asset's namespaced material."""
    full_name = f"{MODEL_NAME}_{name}"
    mat = bpy.data.materials.get(full_name)
    if mat is None:
        mat = bpy.data.materials.new(full_name)
        mat.use_nodes = True
    mat.diffuse_color = color
    bsdf = next((node for node in mat.node_tree.nodes
                 if node.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


MAT_PANEL = material("CreamPanel", (0.82, 0.77, 0.63, 1.0), 0.82)
MAT_ROOF = material("SeafoamRoof", (0.16, 0.46, 0.40, 1.0), 0.58, 0.22)
MAT_WOOD = material("LightTimber", (0.34, 0.19, 0.075, 1.0), 0.92)
MAT_WOOD_LIGHT = material("PorchTimber", (0.56, 0.36, 0.16, 1.0), 0.9)
MAT_CONCRETE = material("Concrete", (0.34, 0.36, 0.34, 1.0), 0.95)
MAT_GLASS = material("DarkTealGlass", (0.015, 0.075, 0.095, 1.0), 0.24, 0.12)
MAT_METAL = material("TrimMetal", (0.14, 0.22, 0.21, 1.0), 0.55, 0.55)
MAT_RED = material("MedicalRed", (0.78, 0.035, 0.025, 1.0), 0.65)
MAT_CABINET = material("UtilityCabinet", (0.08, 0.27, 0.23, 1.0), 0.68, 0.28)


def move_to_collection(obj, collection):
    for linked in list(obj.users_collection):
        linked.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def add_box(name, size, location, mat, collection=model_col, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    # Set local dimensions before applying scale; assigning Object.dimensions on a
    # rotated object targets its world-space bounding box and distorts sloped parts.
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    return move_to_collection(obj, collection)


def add_cylinder(name, radius, depth, location, mat, collection=model_col,
                 rotation=(0, 0, 0), vertices=10):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    return move_to_collection(obj, collection)


def add_beam(name, start, end, section, mat, collection=model_col):
    start_v, end_v = Vector(start), Vector(end)
    delta = end_v - start_v
    if delta.length < 0.001:
        return None
    rotation = delta.to_track_quat("Z", "Y").to_euler()
    return add_box(name, (section[0], section[1], delta.length),
                   (start_v + end_v) / 2, mat, collection, rotation)


def add_gable(name, front_y, back_y, half_width, eave_z, peak_z, mat):
    verts = [
        (-half_width, front_y, eave_z), (half_width, front_y, eave_z),
        (0.0, front_y, peak_z),
        (-half_width, back_y, eave_z), (half_width, back_y, eave_z),
        (0.0, back_y, peak_z),
    ]
    faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    model_col.objects.link(obj)
    return obj


# -----------------------------------------------------------------------------
# 1. Raised foundation and plank floor. Gaps between boards keep the underside
#    frame visible in the true bottom QA view.
# -----------------------------------------------------------------------------
FOOTING_TOP = 0.48
FLOOR_BOTTOM = 0.62
FLOOR_TOP = 0.72
footing_rows = (-1.95, -1.15, 1.15)
for row, y in enumerate(footing_rows):
    for col, x in enumerate((-1.65, 0.0, 1.65)):
        add_box(f"Foundation_Footing_{row}_{col}", (0.36, 0.36, FOOTING_TOP),
                (x, y, FOOTING_TOP / 2), MAT_CONCRETE)
        add_box(f"Foundation_Post_{row}_{col}", (0.14, 0.14, 0.06),
                (x, y, 0.51), MAT_WOOD)

for row, y in enumerate(footing_rows):
    add_box(f"Foundation_Beam_Row_{row}", (3.55, 0.15, 0.14),
            (0.0, y, 0.55), MAT_WOOD)

for col, x in enumerate((-1.65, -0.825, 0.0, 0.825, 1.65)):
    add_box(f"Foundation_Joist_{col}", (0.13, 3.10, 0.10),
            (x, -0.40, 0.56), MAT_WOOD)

# Bracing under the main cabin footprint; all brace ends meet beams/supports.
for side, x in (("L", -1.65), ("R", 1.65)):
    add_beam(f"Foundation_Brace_{side}_A", (x, -1.15, 0.08), (x, 1.15, 0.48),
             (0.09, 0.09), MAT_WOOD)
    add_beam(f"Foundation_Brace_{side}_B", (x, 1.15, 0.08), (x, -1.15, 0.48),
             (0.09, 0.09), MAT_WOOD)

# Cabin floor boards, aligned along X with small gaps between each board.
for i in range(14):
    y = -1.30 + i * 0.20
    add_box(f"Floor_Deck_Plank_{i:02d}", (3.88, 0.18, 0.10),
            (0.0, y, 0.67), MAT_WOOD_LIGHT)

# Covered front veranda boards (front/access side is -Y).
for i in range(5):
    y = -2.08 + i * 0.15
    add_box(f"Porch_Deck_Plank_{i:02d}", (3.78, 0.14, 0.10),
            (0.0, y, 0.67), MAT_WOOD_LIGHT)


# -----------------------------------------------------------------------------
# 2. Insulated walls with actual openings for the door and observation window.
# -----------------------------------------------------------------------------
WALL_BOTTOM = FLOOR_TOP
WALL_TOP = 2.75
WALL_H = WALL_TOP - WALL_BOTTOM
WALL_Z = (WALL_TOP + WALL_BOTTOM) / 2
HALF_X = 1.90
FRONT_Y = -1.40
BACK_Y = 1.40
WALL_THICK = 0.12

add_box("Wall_Back", (3.80, WALL_THICK, WALL_H), (0, BACK_Y, WALL_Z), MAT_PANEL)
add_box("Wall_Left", (WALL_THICK, 2.80, WALL_H), (-HALF_X, 0, WALL_Z), MAT_PANEL)
add_box("Wall_Right", (WALL_THICK, 2.80, WALL_H), (HALF_X, 0, WALL_Z), MAT_PANEL)

# Front wall left/right strips around the entry and window.
for name, width, x in (
    ("Wall_Front_Left", 0.65, -1.575),
    ("Wall_Front_Middle", 0.60, -0.15),
    ("Wall_Front_Right", 0.55, 1.625),
):
    add_box(name, (width, WALL_THICK, WALL_H), (x, FRONT_Y, WALL_Z), MAT_PANEL)

# Lintel above the door; lower and upper panels around the window.
add_box("Wall_Front_Door_Lintel", (0.80, WALL_THICK, 0.25),
        (-0.85, FRONT_Y, 2.625), MAT_PANEL)
add_box("Wall_Front_Window_SillPanel", (1.20, WALL_THICK, 0.58),
        (0.75, FRONT_Y, 1.01), MAT_PANEL)
add_box("Wall_Front_Window_Lintel", (1.20, WALL_THICK, 0.65),
        (0.75, FRONT_Y, 2.425), MAT_PANEL)

# Small modular seams on the plain walls; kept away from openings and fixtures.
for i, x in enumerate((-1.25, -0.45, 0.55, 1.45)):
    add_box(f"Wall_Back_Joint_{i}", (0.025, 0.025, WALL_H),
            (x, 1.466, WALL_Z), MAT_METAL)
for i, y in enumerate((-0.85, 0.0, 0.85)):
    add_box(f"Wall_Left_Joint_{i}", (0.025, 0.025, WALL_H),
            (-1.966, y, WALL_Z), MAT_METAL)
    if y != 0.0:
        add_box(f"Wall_Right_Joint_{i}", (0.025, 0.025, WALL_H),
                (1.966, y, WALL_Z), MAT_METAL)

# Gable infill panels align with the front and rear wall planes.
add_gable("Wall_Gable_Front", -1.46, -1.34, HALF_X, WALL_TOP, 3.55, MAT_PANEL)
add_gable("Wall_Gable_Back", 1.34, 1.46, HALF_X, WALL_TOP, 3.55, MAT_PANEL)


# -----------------------------------------------------------------------------
# 3. Door, observation window, medical sign and veranda access.
# -----------------------------------------------------------------------------
# Entry door, at X=-0.85 on the -Y face.
door_y = -1.485
for side, x in (("L", -1.29), ("R", -0.41)):
    add_box(f"Door_Frame_{side}", (0.06, 0.08, 1.82), (x, door_y, 1.63), MAT_METAL)
add_box("Door_Frame_Top", (0.88, 0.08, 0.06), (-0.85, door_y, 2.54), MAT_METAL)
add_box("Door_Threshold", (0.82, 0.16, 0.05), (-0.85, -1.48, 0.735), MAT_METAL)
add_box("Door_Panel", (0.76, 0.055, 1.76), (-0.85, -1.49, 1.60), MAT_WOOD)
add_box("Door_Glass_Slit", (0.24, 0.025, 0.36), (-0.85, -1.525, 1.98), MAT_GLASS)
add_box("Door_Handle", (0.045, 0.045, 0.14), (-0.56, -1.535, 1.55), MAT_METAL)

# Broad front observation window with a single vertical mullion.
window_x, window_z = 0.75, 1.70
add_box("Window_Frame_Left", (0.055, 0.08, 0.86), (0.12, -1.485, window_z), MAT_METAL)
add_box("Window_Frame_Right", (0.055, 0.08, 0.86), (1.38, -1.485, window_z), MAT_METAL)
add_box("Window_Frame_Top", (1.26, 0.08, 0.055), (window_x, -1.485, 2.13), MAT_METAL)
add_box("Window_Frame_Sill", (1.26, 0.10, 0.07), (window_x, -1.49, 1.27), MAT_METAL)
add_box("Window_Glass", (1.14, 0.035, 0.74), (window_x, -1.49, window_z), MAT_GLASS)
add_box("Window_Mullion", (0.035, 0.05, 0.74), (window_x, -1.52, window_z), MAT_METAL)

# Small geometric medical cross above the window.
add_box("MedicalSign_Vertical", (0.14, 0.055, 0.34), (window_x, -1.50, 2.34), MAT_RED)
add_box("MedicalSign_Horizontal", (0.34, 0.055, 0.12), (window_x, -1.50, 2.34), MAT_RED)

# Lean-to canopy, supported from the veranda deck by two timber posts.
porch_slope = math.atan2(0.30, 0.98)  # rises toward the cabin (+Y)
add_box("Porch_Roof", (4.10, 0.98, 0.09),
        (0.0, -1.83, 2.77), MAT_ROOF, rotation=(porch_slope, 0, 0))
add_box("Porch_Roof_FrontFascia", (4.12, 0.055, 0.12),
        (0.0, -2.33, 2.62), MAT_METAL)
for side, x in (("L", -1.72), ("R", 1.72)):
    add_box(f"Porch_Post_{side}", (0.10, 0.10, 1.88), (x, -2.23, 1.66), MAT_WOOD)
    add_box(f"Porch_Rail_{side}", (0.07, 0.44, 0.07), (x, -1.94, 1.06), MAT_WOOD_LIGHT)
    for j, y in enumerate((-2.12, -1.76)):
        add_box(f"Porch_Rail_Baluster_{side}_{j}", (0.06, 0.06, 0.34),
                (x, y, 0.89), MAT_WOOD_LIGHT)

# Three broad, non-overlapping steps align with the door and meet the porch edge.
for i, (y, z) in enumerate(((-2.74, 0.12), (-2.52, 0.36), (-2.30, 0.60))):
    add_box(f"Porch_Step_{i}", (0.92, 0.22, 0.24), (-0.85, y, z), MAT_WOOD_LIGHT)

# Restrained field-supply crates on the open side of the veranda.
add_box("MedicalSupply_Crate_L", (0.34, 0.34, 0.36), (-1.48, -1.86, 0.90), MAT_WOOD)
add_box("MedicalSupply_Crate_R", (0.30, 0.30, 0.30), (1.48, -1.86, 0.87), MAT_WOOD_LIGHT)


# -----------------------------------------------------------------------------
# 4. Gable roof, rainwater details and exterior utility cabinet.
# -----------------------------------------------------------------------------
roof_angle = math.atan2(0.80, 2.15)
roof_slope_len = math.sqrt(2.15 ** 2 + 0.80 ** 2)
roof_y_len = 3.20
roof_center_z = 3.15
roof_center_x = 1.075

# Correctly sized roof halves meet at the ridge; the right half slopes down to +X.
add_box("Roof_Panel_Left", (roof_slope_len, roof_y_len, 0.10),
        (-roof_center_x, 0.0, roof_center_z), MAT_ROOF,
        rotation=(0, -roof_angle, 0))
add_box("Roof_Panel_Right", (roof_slope_len, roof_y_len, 0.10),
        (roof_center_x, 0.0, roof_center_z), MAT_ROOF,
        rotation=(0, roof_angle, 0))
add_box("Roof_Ridge_Cap", (0.13, roof_y_len, 0.07), (0, 0, 3.57), MAT_METAL)

# Raised standing seams run down each roof slope.
for side, x, angle in (("L", -roof_center_x, -roof_angle), ("R", roof_center_x, roof_angle)):
    for i, y in enumerate((-1.28, -0.64, 0.0, 0.64, 1.28)):
        add_box(f"Roof_Seam_{side}_{i}", (roof_slope_len - 0.10, 0.025, 0.025),
                (x, y, roof_center_z), MAT_METAL, rotation=(0, angle, 0))

# Gutters sit at the low eaves; downpipes meet their short outlet elbows.
for side, x in (("L", -2.15), ("R", 2.15)):
    add_cylinder(f"Gutter_{side}", 0.055, roof_y_len, (x, 0.0, 2.73), MAT_METAL,
                 rotation=(math.radians(90), 0, 0), vertices=10)
    for end, y in (("Front", -1.38), ("Back", 1.38)):
        add_cylinder(f"Downpipe_{side}_{end}", 0.035, 1.94,
                     (x * 0.93, y, 1.70), MAT_METAL, vertices=8)
        add_beam(f"Gutter_Outlet_{side}_{end}", (x, y, 2.73), (x * 0.93, y, 2.73),
                 (0.055, 0.055), MAT_METAL)

# Compact wall-mounted cabinet on the +X side, with simple access panel and fittings.
cab_x, cab_y, cab_z = 2.07, 0.34, 1.42
add_box("Utility_Cabinet_Body", (0.30, 0.64, 0.72), (cab_x, cab_y, cab_z), MAT_CABINET)
add_box("Utility_Cabinet_Door", (0.025, 0.54, 0.61), (2.235, cab_y, cab_z), MAT_METAL)
add_box("Utility_Cabinet_Handle", (0.035, 0.045, 0.13), (2.255, 0.10, cab_z), MAT_WOOD_LIGHT)
for i in range(3):
    add_box(f"Utility_Cabinet_Louver_{i}", (0.025, 0.34, 0.035),
            (2.255, 0.39, 1.53 + i * 0.10), MAT_CABINET)
add_cylinder("Utility_Conduit_Vertical", 0.025, 0.48, (1.99, 0.78, 1.05), MAT_METAL, vertices=8)
add_beam("Utility_Conduit_Entry", (1.99, 0.78, 1.28), (1.99, 0.55, 1.28),
         (0.05, 0.05), MAT_METAL)


# -----------------------------------------------------------------------------
# 5. Diagnostics.
# -----------------------------------------------------------------------------
def report_diagnostics():
    bpy.context.view_layer.update()
    meshes = [obj for obj in model_col.objects if obj.type == "MESH"]
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    open_edges = 0
    for obj in meshes:
        for corner in obj.bound_box:
            p = obj.matrix_world @ Vector(corner)
            for axis in range(3):
                mins[axis] = min(mins[axis], p[axis])
                maxs[axis] = max(maxs[axis], p[axis])
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        open_edges += sum(1 for edge in bm.edges if not edge.is_manifold)
        bm.free()
    dims = [maxs[i] - mins[i] for i in range(3)]
    print("\n--- MedicalStation_DeepSeek Diagnostics ---")
    print(f"Mesh Object Count: {len(meshes)}")
    print(f"World Bounds (W, D, H): {dims[0]:.3f} m, {dims[1]:.3f} m, {dims[2]:.3f} m")
    print(f"Minimum Z: {mins[2]:.3f} m")
    print(f"Non-Manifold Edges: {open_edges}")
    print("Note: manifold checks inspect each mesh separately; they do not detect intersections between separate objects.")
    print("Front wall openings are modeled as clear door/window gaps; roof and frame contacts are intentional.")
    print("--------------------------------------------\n")


# -----------------------------------------------------------------------------
# 6. Temporary render setup. Existing objects, world and render settings are
#    restored before export/save. The exact asset collections are isolated.
# -----------------------------------------------------------------------------
original_state = {
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
    "active": bpy.context.view_layer.objects.active,
    "selected": list(bpy.context.selected_objects),
}
model_objects = set(model_col.objects)
external_render_state = {obj: obj.hide_render for obj in scene.objects
                         if obj not in model_objects and obj not in set(helper_col.objects)}
for obj in external_render_state:
    obj.hide_render = True

render_world = bpy.data.worlds.new("MedicalStation_DeepSeek_TemporaryRenderWorld")
render_world.use_nodes = True
render_bg = render_world.node_tree.nodes.get("Background")
if render_bg:
    render_bg.inputs["Color"].default_value = (0.82, 0.84, 0.84, 1.0)
    render_bg.inputs["Strength"].default_value = 0.8

try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError:
    scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.view_transform = "Standard"
scene.world = render_world

bpy.ops.object.camera_add()
camera = move_to_collection(bpy.context.object, helper_col)
camera.name = "MedicalStation_DeepSeek_QA_Camera"
camera.data.type = "ORTHO"
scene.camera = camera

bpy.ops.object.light_add(type="SUN", location=(5, -5, 9))
sun = move_to_collection(bpy.context.object, helper_col)
sun.name = "MedicalStation_DeepSeek_KeyLight"
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(34), math.radians(-18), math.radians(-28))

bpy.ops.object.light_add(type="AREA", location=(-5, -6, 6))
fill = move_to_collection(bpy.context.object, helper_col)
fill.name = "MedicalStation_DeepSeek_FillLight"
fill.data.energy = 180
fill.data.shape = "DISK"
fill.data.size = 8
fill.rotation_euler = (Vector((0, 0, 1.65)) - fill.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.light_add(type="AREA", location=(0, 5, 5.5))
back_fill = move_to_collection(bpy.context.object, helper_col)
back_fill.name = "MedicalStation_DeepSeek_BackFillLight"
back_fill.data.energy = 220
back_fill.data.shape = "DISK"
back_fill.data.size = 8
back_fill.rotation_euler = (Vector((0, 0, 1.65)) - back_fill.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.light_add(type="AREA", location=(6, 0, 5))
side_fill = move_to_collection(bpy.context.object, helper_col)
side_fill.name = "MedicalStation_DeepSeek_SideFillLight"
side_fill.data.energy = 260
side_fill.data.shape = "DISK"
side_fill.data.size = 7
side_fill.rotation_euler = (Vector((0, 0, 1.65)) - side_fill.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.light_add(type="AREA", location=(0, 0, -4))
underlight = move_to_collection(bpy.context.object, helper_col)
underlight.name = "MedicalStation_DeepSeek_UndersideLight"
underlight.data.energy = 90
underlight.data.shape = "DISK"
underlight.data.size = 6
underlight.rotation_euler = (math.radians(180), 0, 0)
underlight.hide_render = True


def render_view(location, rotation, filename, scale=5.7, underside=False):
    camera.location = location
    camera.rotation_euler = rotation
    camera.data.ortho_scale = scale
    underlight.hide_render = not underside
    scene.render.filepath = str(QA_DIR / filename)
    bpy.ops.render.render(write_still=True)


center_z = 1.78
scale_factor = 5.7
try:
    render_view((0, -18, center_z), (math.radians(90), 0, 0),
                "MedicalStation_DeepSeek_Front.png", scale=scale_factor)
    render_view((0, 18, center_z), (math.radians(90), 0, math.radians(180)),
                "MedicalStation_DeepSeek_Back.png", scale=scale_factor)
    render_view((-18, 0, center_z), (math.radians(90), 0, math.radians(-90)),
                "MedicalStation_DeepSeek_Left.png", scale=scale_factor)
    render_view((18, 0, center_z), (math.radians(90), 0, math.radians(90)),
                "MedicalStation_DeepSeek_Right.png", scale=scale_factor)
    render_view((0, 0, 18), (0, 0, 0), "MedicalStation_DeepSeek_Top.png",
                scale=scale_factor)
    render_view((0, 0, -18), (math.radians(180), 0, 0),
                "MedicalStation_DeepSeek_Bottom.png", scale=scale_factor, underside=True)

    camera.location = (7.5, -9.0, 6.8)
    target = Vector((0, -0.35, 1.75))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = 6.5
    underlight.hide_render = True
    scene.render.filepath = str(PREVIEW_DIR / "MedicalStation_DeepSeek.png")
    bpy.ops.render.render(write_still=True)
finally:
    scene.render.engine = original_state["engine"]
    scene.render.resolution_x = original_state["resolution_x"]
    scene.render.resolution_y = original_state["resolution_y"]
    scene.render.resolution_percentage = original_state["resolution_percentage"]
    scene.render.image_settings.file_format = original_state["file_format"]
    scene.render.film_transparent = original_state["film_transparent"]
    scene.render.filepath = original_state["filepath"]
    scene.view_settings.view_transform = original_state["view_transform"]
    scene.world = original_state["world"]
    scene.camera = original_state["camera"]
    for obj, hide_render in external_render_state.items():
        if obj.name in bpy.data.objects:
            obj.hide_render = hide_render
    helper_col.hide_viewport = True
    helper_col.hide_render = True
    if render_world.users == 0:
        bpy.data.worlds.remove(render_world)
    for obj in list(bpy.context.selected_objects):
        obj.select_set(False)
    for obj in original_state["selected"]:
        if obj.name in bpy.data.objects:
            obj.select_set(True)
    active = original_state["active"]
    bpy.context.view_layer.objects.active = active if active and active.name in bpy.data.objects else None


# Export only this asset's meshes; restore the user's selection afterwards.
for obj in list(bpy.context.selected_objects):
    obj.select_set(False)
for obj in model_col.objects:
    if obj.type == "MESH":
        obj.select_set(True)
fbx_path = FBX_DIR / "MedicalStation_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path), use_selection=True, apply_scale_options="FBX_SCALE_ALL",
    object_types={"MESH"}, bake_space_transform=True,
)
for obj in list(bpy.context.selected_objects):
    obj.select_set(False)
for obj in original_state["selected"]:
    if obj.name in bpy.data.objects:
        obj.select_set(True)
bpy.context.view_layer.objects.active = original_state["active"] if original_state["active"] and original_state["active"].name in bpy.data.objects else None

blend_path = BLEND_DIR / "MedicalStation_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
report_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX to: {fbx_path}")
print(f"Saved preview to: {PREVIEW_DIR / 'MedicalStation_DeepSeek.png'}")
print(f"Saved six QA views to: {QA_DIR}")
