import bpy
import bmesh
import mathutils
import math
import os
from pathlib import Path

# ==============================================================================
# Archive_DeepSeek - Blender 5.2.2 Generation Script
# ==============================================================================

def get_project_root():
    """Tools/Blender/<script>.py is two directories below the repository root."""
    try:
        script_path = Path(__file__).resolve()
        root = script_path.parents[2]
        if (root / "Assets" / "LastLandfall").is_dir():
            return root
    except (NameError, IndexError, OSError):
        pass
    return Path.cwd()

PROJECT_ROOT = get_project_root()

# Define output paths
BLEND_PATH = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Buildings/Archive_DeepSeek.blend"
FBX_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Buildings/Archive_DeepSeek.fbx"
PREVIEW_PATH = PROJECT_ROOT / "Assets/LastLandfall/Art/Previews/Buildings/Archive_DeepSeek.png"
REF_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"
REF_PATHS = {
    "Front": REF_DIR / "Archive_DeepSeek_Front.png",
    "Back": REF_DIR / "Archive_DeepSeek_Back.png",
    "Left": REF_DIR / "Archive_DeepSeek_Left.png",
    "Right": REF_DIR / "Archive_DeepSeek_Right.png",
    "Top": REF_DIR / "Archive_DeepSeek_Top.png",
    "Bottom": REF_DIR / "Archive_DeepSeek_Bottom.png"
}

def ensure_dirs():
    """Create necessary directories."""
    for path in [BLEND_PATH.parent, FBX_PATH.parent, PREVIEW_PATH.parent, REF_DIR]:
        path.mkdir(parents=True, exist_ok=True)

def clean_scene():
    """Clean specific collections and unused materials."""
    collections_to_remove = ["Archive_DeepSeek", "Helpers_Archive_DeepSeek"]
    for col_name in collections_to_remove:
        if col_name in bpy.data.collections:
            col = bpy.data.collections[col_name]
            for obj in list(col.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(col)
    
    # Clean materials
    for mat in list(bpy.data.materials):
        if mat.name.startswith("Archive_DeepSeek_") and mat.users == 0:
            bpy.data.materials.remove(mat)

def create_material(name, base_color, metallic=0.0, roughness=0.5, emission=None):
    """Create a Principled BSDF material."""
    mat = bpy.data.materials.new(name=f"Archive_DeepSeek_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = (*base_color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*emission[0], 1.0)
        bsdf.inputs['Emission Strength'].default_value = emission[1]
    return mat

def apply_bevel(obj, width=0.01, segments=1):
    """Apply a small bevel to an object for low-poly highlights."""
    mod = obj.modifiers.new(name="Bevel", type='BEVEL')
    # Thin vent slats need a smaller bevel to avoid collapsed end faces.
    mod.width = min(width, min(obj.dimensions) * 0.2)
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

def add_box(name, loc, scale, mat, collection, bevel=True):
    """Add a cube mesh object."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    if bevel:
        apply_bevel(obj)
    collection.objects.link(obj)
    bpy.context.collection.objects.unlink(obj) # Unlink from default collection
    return obj

def add_cylinder(name, loc, radius, depth, mat, collection, rotation=(0,0,0), vertices=12):
    """Add a cylinder mesh object."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    apply_bevel(obj, width=0.005, segments=1)
    collection.objects.link(obj)
    bpy.context.collection.objects.unlink(obj)
    return obj

def build_model():
    """Build the Archive_DeepSeek model."""
    
    # Collections
    col_archive = bpy.data.collections.new("Archive_DeepSeek")
    bpy.context.scene.collection.children.link(col_archive)
    
    # Materials
    mat_wood_light = create_material("Wood_SaltBleached", (0.55, 0.4, 0.25), roughness=0.8)
    mat_wood_dark = create_material("Wood_DarkStructural", (0.2, 0.12, 0.08), roughness=0.7)
    mat_metal_roof = create_material("Metal_SeaGreen", (0.15, 0.35, 0.3), metallic=0.6, roughness=0.4)
    mat_metal_patch = create_material("Metal_PatchGrey", (0.4, 0.45, 0.45), metallic=0.5, roughness=0.5)
    mat_stone = create_material("Stone_WarmGrey", (0.45, 0.45, 0.4), roughness=0.9)
    mat_glass = create_material("Glass_SmokyBlue", (0.3, 0.5, 0.6), metallic=0.1, roughness=0.1)
    mat_board = create_material("Board_Ochre", (0.7, 0.5, 0.3), roughness=0.8)
    mat_light = create_material("Light_Bulb", (1.0, 0.9, 0.7), emission=((1.0, 0.8, 0.5), 5.0))
    mat_door = create_material("Wood_Door", (0.35, 0.2, 0.15), roughness=0.6)

    # ==========================================================================
    # 1. Base (Foundation & Floor)
    # ==========================================================================
    # Stone Piers
    pier_positions = [
        (-1.6, -1.6), (1.6, -1.6), (-1.6, 1.6), (1.6, 1.6), # Corners
        (0, -1.6), (0, 1.6), (-1.6, 0), (1.6, 0)            # Midpoints
    ]
    for i, (x, y) in enumerate(pier_positions):
        add_box(f"Base_StonePier_{i}", (x, y, 0.2), (0.4, 0.4, 0.4), mat_stone, col_archive)

    # Floor Beams
    add_box("Base_FloorBeam_Front", (0, -1.8, 0.3), (3.8, 0.2, 0.2), mat_wood_dark, col_archive)
    add_box("Base_FloorBeam_Back", (0, 1.8, 0.3), (3.8, 0.2, 0.2), mat_wood_dark, col_archive)
    add_box("Base_FloorBeam_Left", (-1.8, 0, 0.3), (0.2, 3.6, 0.2), mat_wood_dark, col_archive)
    add_box("Base_FloorBeam_Right", (1.8, 0, 0.3), (0.2, 3.6, 0.2), mat_wood_dark, col_archive)
    add_box("Base_FloorBeam_Center", (0, 0, 0.3), (3.6, 0.2, 0.2), mat_wood_dark, col_archive)

    # Floor Platform
    add_box("Base_Floor", (0, 0, 0.4), (3.8, 3.8, 0.1), mat_wood_light, col_archive)

    # Short entrance porch with independent stone supports and a timber frame.
    for side in (-1, 1):
        add_box(f"Porch_Pier_{side}", (side * 0.65, -2.05, 0.2), (0.3, 0.3, 0.4), mat_stone, col_archive)
        add_box(f"Porch_Beam_Side_{side}", (side * 0.65, -2.0, 0.3), (0.18, 0.4, 0.2), mat_wood_dark, col_archive)
    add_box("Porch_Beam_Front", (0, -2.15, 0.3), (1.5, 0.16, 0.2), mat_wood_dark, col_archive)
    add_box("Porch_Deck", (0, -2.0, 0.4), (1.8, 0.4, 0.1), mat_wood_light, col_archive)

    # ==========================================================================
    # 2. Walls & Structure
    # ==========================================================================
    # Main Wall Blocks (to avoid complex booleans, we use separate blocks)
    wall_thickness = 0.15
    wall_height = 1.8
    wall_z_center = 0.4 + wall_height / 2

    # Front Wall (-Y)
    # Left section
    add_box("Wall_Front_Left", (-1.2, -1.8, wall_z_center), (1.2, wall_thickness, wall_height), mat_wood_light, col_archive)
    # Right section
    add_box("Wall_Front_Right", (1.2, -1.8, wall_z_center), (1.2, wall_thickness, wall_height), mat_wood_light, col_archive)
    # Top section above door
    add_box("Wall_Front_Top", (0, -1.8, 1.8), (1.2, wall_thickness, 0.4), mat_wood_light, col_archive)

    # Back Wall (+Y)
    add_box("Wall_Back", (0, 1.8, wall_z_center), (3.6, wall_thickness, wall_height), mat_wood_light, col_archive)

    # Side walls are assembled around actual window openings.
    for side in (-1, 1):
        x = side * 1.8
        for index, (y_center, length) in enumerate(((-1.45, 0.7), (0.0, 1.0), (1.45, 0.7))):
            add_box(f"Wall_Side_{side}_Solid_{index}", (x, y_center, wall_z_center), (wall_thickness, length, wall_height), mat_wood_light, col_archive)
        for index, y_center in enumerate((-0.8, 0.8)):
            add_box(f"Wall_Side_{side}_WindowLower_{index}", (x, y_center, 0.875), (wall_thickness, 0.6, 0.95), mat_wood_light, col_archive)
            add_box(f"Wall_Side_{side}_WindowUpper_{index}", (x, y_center, 2.025), (wall_thickness, 0.6, 0.35), mat_wood_light, col_archive)

    # Corner Posts & Horizontal Beams (Dark Wood)
    # Four vertical corner posts
    for x, y in [(-1.8, -1.8), (1.8, -1.8), (-1.8, 1.8), (1.8, 1.8)]:
        add_box("Post_Corner", (x, y, wall_z_center), (0.2, 0.2, wall_height), mat_wood_dark, col_archive)
    
    # Horizontal framing (Top and Bottom)
    # Top beam
    add_box("Beam_Top_Front", (0, -1.8, 2.2), (3.8, 0.2, 0.15), mat_wood_dark, col_archive)
    add_box("Beam_Top_Back", (0, 1.8, 2.2), (3.8, 0.2, 0.15), mat_wood_dark, col_archive)
    add_box("Beam_Top_Left", (-1.8, 0, 2.2), (0.2, 3.8, 0.15), mat_wood_dark, col_archive)
    add_box("Beam_Top_Right", (1.8, 0, 2.2), (0.2, 3.8, 0.15), mat_wood_dark, col_archive)
    # Bottom beam
    add_box("Beam_Bottom_Front", (0, -1.8, 0.45), (3.8, 0.2, 0.15), mat_wood_dark, col_archive)
    add_box("Beam_Bottom_Back", (0, 1.8, 0.45), (3.8, 0.2, 0.15), mat_wood_dark, col_archive)
    add_box("Beam_Bottom_Left", (-1.8, 0, 0.45), (0.2, 3.8, 0.15), mat_wood_dark, col_archive)
    add_box("Beam_Bottom_Right", (1.8, 0, 0.45), (0.2, 3.8, 0.15), mat_wood_dark, col_archive)

    # Horizontal siding detail (thin strips on walls)
    for z in [0.8, 1.2, 1.6]:
        add_box("Siding_Front", (0, -1.85, z), (3.6, 0.05, 0.05), mat_wood_dark, col_archive)
        add_box("Siding_Back", (0, 1.85, z), (3.6, 0.05, 0.05), mat_wood_dark, col_archive)
        add_box("Siding_Left", (-1.85, 0, z), (0.05, 3.6, 0.05), mat_wood_dark, col_archive)
        add_box("Siding_Right", (1.85, 0, z), (0.05, 3.6, 0.05), mat_wood_dark, col_archive)

    # ==========================================================================
    # 3. Doors & Porch
    # ==========================================================================
    # Door Frame
    add_box("Door_Frame_Left", (-0.65, -1.85, 1.1), (0.1, 0.1, 1.4), mat_wood_dark, col_archive)
    add_box("Door_Frame_Right", (0.65, -1.85, 1.1), (0.1, 0.1, 1.4), mat_wood_dark, col_archive)
    add_box("Door_Frame_Top", (0, -1.85, 1.8), (1.4, 0.1, 0.1), mat_wood_dark, col_archive)

    # Double Doors
    add_box("Door_Left", (-0.3, -1.9, 1.1), (0.6, 0.05, 1.4), mat_door, col_archive)
    add_box("Door_Right", (0.3, -1.9, 1.1), (0.6, 0.05, 1.4), mat_door, col_archive)
    # Door handles (small cylinders)
    add_cylinder("Door_Handle_L", (-0.1, -1.95, 1.1), 0.02, 0.1, mat_wood_dark, col_archive, rotation=(math.radians(90), 0, 0), vertices=8)
    add_cylinder("Door_Handle_R", (0.1, -1.95, 1.1), 0.02, 0.1, mat_wood_dark, col_archive, rotation=(math.radians(90), 0, 0), vertices=8)

    # Three progressively higher treads meet the deck without dipping below Z=0.
    for index, (y_center, top_z) in enumerate(((-2.58, 0.15), (-2.40, 0.30), (-2.22, 0.45)), start=1):
        step_height = 0.15
        add_box(f"Step_{index}", (0, y_center, top_z - step_height * 0.5), (1.6, 0.24, step_height), mat_wood_light, col_archive)

    # Porch Canopy (Awnings)
    # Slanted roof for canopy
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -2.1, 1.95))
    canopy = bpy.context.active_object
    canopy.name = "Porch_Canopy"
    canopy.scale = (1.8, 0.8, 0.05)
    canopy.rotation_euler = (math.radians(15), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    canopy.data.materials.append(mat_metal_roof)
    apply_bevel(canopy)
    col_archive.objects.link(canopy)
    bpy.context.collection.objects.unlink(canopy)

    # Canopy supports land on the porch deck and connect to a front header.
    add_cylinder("Porch_Post_Left", (-0.8, -2.1, 1.125), 0.065, 1.35, mat_wood_dark, col_archive)
    add_cylinder("Porch_Post_Right", (0.8, -2.1, 1.125), 0.065, 1.35, mat_wood_dark, col_archive)
    add_box("Porch_Header", (0, -2.1, 1.84), (1.75, 0.14, 0.12), mat_wood_dark, col_archive)
    # Diagonal braces
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.8, -2.15, 1.6))
    brace_l = bpy.context.active_object
    brace_l.name = "Porch_Brace_Left"
    brace_l.scale = (0.05, 0.6, 0.05)
    brace_l.rotation_euler = (math.radians(-45), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    brace_l.data.materials.append(mat_wood_dark)
    apply_bevel(brace_l)
    col_archive.objects.link(brace_l)
    bpy.context.collection.objects.unlink(brace_l)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.8, -2.15, 1.6))
    brace_r = bpy.context.active_object
    brace_r.name = "Porch_Brace_Right"
    brace_r.scale = (0.05, 0.6, 0.05)
    brace_r.rotation_euler = (math.radians(-45), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    brace_r.data.materials.append(mat_wood_dark)
    apply_bevel(brace_r)
    col_archive.objects.link(brace_r)
    bpy.context.collection.objects.unlink(brace_r)

    # ==========================================================================
    # 4. Windows & Shutters
    # ==========================================================================
    def create_window(name_prefix, loc, size, axis, outward, mat_frame, mat_glass, mat_shutter):
        """Build an oriented framed pane and separate storm shutters."""
        w, h = size
        if axis == "X":
            x, y, z = loc
            normal = x + outward * 0.04
            add_box(f"{name_prefix}_Frame_Top", (normal, y, z + h/2), (0.10, w + 0.10, 0.10), mat_frame, col_archive)
            add_box(f"{name_prefix}_Frame_Bottom", (normal, y, z - h/2), (0.10, w + 0.10, 0.10), mat_frame, col_archive)
            add_box(f"{name_prefix}_Frame_Left", (normal, y - w/2, z), (0.10, 0.10, h), mat_frame, col_archive)
            add_box(f"{name_prefix}_Frame_Right", (normal, y + w/2, z), (0.10, 0.10, h), mat_frame, col_archive)
            add_box(f"{name_prefix}_Glass", (x + outward * 0.02, y, z), (0.035, w, h), mat_glass, col_archive, bevel=False)
            add_box(f"{name_prefix}_Shutter_L", (normal, y - w/2 - 0.15, z), (0.08, 0.18, h), mat_shutter, col_archive)
            add_box(f"{name_prefix}_Shutter_R", (normal, y + w/2 + 0.15, z), (0.08, 0.18, h), mat_shutter, col_archive)
        else:
            x, y, z = loc
            normal = y + outward * 0.04
            add_box(f"{name_prefix}_Frame_Top", (x, normal, z + h/2), (w + 0.10, 0.10, 0.10), mat_frame, col_archive)
            add_box(f"{name_prefix}_Frame_Bottom", (x, normal, z - h/2), (w + 0.10, 0.10, 0.10), mat_frame, col_archive)
            add_box(f"{name_prefix}_Frame_Left", (x - w/2, normal, z), (0.10, 0.10, h), mat_frame, col_archive)
            add_box(f"{name_prefix}_Frame_Right", (x + w/2, normal, z), (0.10, 0.10, h), mat_frame, col_archive)
            add_box(f"{name_prefix}_Glass", (x, y + outward * 0.02, z), (w, 0.035, h), mat_glass, col_archive, bevel=False)
            add_box(f"{name_prefix}_Shutter_L", (x - w/2 - 0.15, normal, z), (0.18, 0.08, h), mat_shutter, col_archive)
            add_box(f"{name_prefix}_Shutter_R", (x + w/2 + 0.15, normal, z), (0.18, 0.08, h), mat_shutter, col_archive)

    # Left Side Windows (X = -1.8)
    create_window("Window_Left_1", (-1.875, -0.8, 1.6), (0.6, 0.5), "X", -1, mat_wood_dark, mat_glass, mat_wood_dark)
    create_window("Window_Left_2", (-1.875, 0.8, 1.6), (0.6, 0.5), "X", -1, mat_wood_dark, mat_glass, mat_wood_dark)

    # Right Side Windows (X = 1.8)
    create_window("Window_Right_1", (1.875, -0.8, 1.6), (0.6, 0.5), "X", 1, mat_wood_dark, mat_glass, mat_wood_dark)
    create_window("Window_Right_2", (1.875, 0.8, 1.6), (0.6, 0.5), "X", 1, mat_wood_dark, mat_glass, mat_wood_dark)

    # Front Windows (flanking the door)
    create_window("Window_Front_Left", (-1.2, -1.875, 1.6), (0.4, 0.4), "Y", -1, mat_wood_dark, mat_glass, mat_wood_dark)
    create_window("Window_Front_Right", (1.2, -1.875, 1.6), (0.4, 0.4), "Y", -1, mat_wood_dark, mat_glass, mat_wood_dark)

    # Back Wall Vent/High Window
    add_box("Back_Vent_Frame", (0, 1.88, 1.8), (0.6, 0.1, 0.3), mat_wood_dark, col_archive)
    add_box("Back_Vent_Grille", (0, 1.84, 1.8), (0.5, 0.05, 0.2), mat_wood_dark, col_archive)
    # Vent slats
    for z_offset in [-0.05, 0.05]:
        add_box("Back_Vent_Slat", (0, 1.82, 1.8 + z_offset), (0.5, 0.02, 0.02), mat_wood_light, col_archive)

    # ==========================================================================
    # 5. Notice Board
    # ==========================================================================
    # Board mounted on the front wall, left side
    add_box("NoticeBoard_Frame", (-1.2, -1.9, 0.9), (0.7, 0.05, 0.9), mat_wood_dark, col_archive)
    add_box("NoticeBoard_Surface", (-1.2, -1.93, 0.9), (0.6, 0.02, 0.8), mat_board, col_archive, bevel=False)
    # Small roof over the board
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.2, -1.95, 1.4))
    board_roof = bpy.context.active_object
    board_roof.name = "NoticeBoard_Roof"
    board_roof.scale = (0.8, 0.3, 0.05)
    board_roof.rotation_euler = (math.radians(15), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    board_roof.data.materials.append(mat_metal_roof)
    apply_bevel(board_roof)
    col_archive.objects.link(board_roof)
    bpy.context.collection.objects.unlink(board_roof)

    # ==========================================================================
    # 6. Roof (Hip Roof)
    # ==========================================================================
    # Create a hip roof using bmesh
    bm = bmesh.new()
    # Base vertices (compact eaves keep the complete asset inside 4.8 m).
    v1 = bm.verts.new((-2.0, -2.0, 2.2))
    v2 = bm.verts.new((2.0, -2.0, 2.2))
    v3 = bm.verts.new((2.0, 2.0, 2.2))
    v4 = bm.verts.new((-2.0, 2.0, 2.2))
    # Top vertices (ridge)
    v5 = bm.verts.new((-0.4, -0.4, 2.68))
    v6 = bm.verts.new((0.4, -0.4, 2.68))
    v7 = bm.verts.new((0.4, 0.4, 2.68))
    v8 = bm.verts.new((-0.4, 0.4, 2.68))
    
    # Create faces
    bm.faces.new((v1, v2, v6, v5)) # Front slope
    bm.faces.new((v2, v3, v7, v6)) # Right slope
    bm.faces.new((v3, v4, v8, v7)) # Back slope
    bm.faces.new((v4, v1, v5, v8)) # Left slope
    bm.faces.new((v5, v6, v7, v8)) # Ridge top
    bm.faces.new((v4, v3, v2, v1)) # Closed underside for manifold topology
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    mesh = bpy.data.meshes.new("Roof_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    roof_obj = bpy.data.objects.new("Roof_Main", mesh)
    col_archive.objects.link(roof_obj)
    roof_obj.data.materials.append(mat_metal_roof)
    # Apply bevel to roof edges
    bpy.context.view_layer.objects.active = roof_obj
    apply_bevel(roof_obj, width=0.03, segments=1)

    # Roof Ridge Cap
    add_box("Roof_RidgeCap", (0, 0, 2.73), (0.9, 0.9, 0.12), mat_metal_roof, col_archive)
    
    # Roof Patch (Metal sheet on one slope)
    patch_y = -1.2
    patch_surface_z = 2.2 + (2.68 - 2.2) * abs(patch_y + 2.0) / 1.6
    bpy.ops.mesh.primitive_cube_add(size=1, location=(1.2, patch_y, patch_surface_z + 0.018))
    patch = bpy.context.active_object
    patch.name = "Roof_Patch"
    patch.scale = (0.7, 0.55, 0.025)
    patch.rotation_euler = (math.atan2(2.68 - 2.2, 1.6), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    patch.data.materials.append(mat_metal_patch)
    apply_bevel(patch)
    col_archive.objects.link(patch)
    bpy.context.collection.objects.unlink(patch)

    # Gutters and Downspout
    # Downspout on the back-right corner
    add_cylinder("Gutter_Downspout", (1.98, 2.0, 1.3), 0.05, 1.8, mat_metal_patch, col_archive, rotation=(0, 0, 0))
    # Downspout elbows
    add_cylinder("Gutter_Elbow_Top", (1.98, 2.0, 2.2), 0.05, 0.2, mat_metal_patch, col_archive, rotation=(math.radians(90), 0, 0))
    add_cylinder("Gutter_Elbow_Bottom", (1.98, 2.0, 0.4), 0.05, 0.2, mat_metal_patch, col_archive, rotation=(math.radians(90), 0, 0))
    # Four rain gutters follow the hip-roof eaves.
    add_cylinder("Gutter_Back", (0, 2.0, 2.2), 0.06, 4.0, mat_metal_patch, col_archive, rotation=(0, math.radians(90), 0))
    add_cylinder("Gutter_Front", (0, -2.0, 2.2), 0.06, 4.0, mat_metal_patch, col_archive, rotation=(0, math.radians(90), 0))
    add_cylinder("Gutter_Left", (-2.0, 0, 2.2), 0.06, 4.0, mat_metal_patch, col_archive, rotation=(math.radians(90), 0, 0))
    add_cylinder("Gutter_Right", (2.0, 0, 2.2), 0.06, 4.0, mat_metal_patch, col_archive, rotation=(math.radians(90), 0, 0))

    # ==========================================================================
    # 7. Details (Lights, etc.)
    # ==========================================================================
    # Entrance Light
    add_box("Entrance_Light_Fixture", (0.8, -2.0, 1.8), (0.1, 0.1, 0.2), mat_wood_dark, col_archive)
    add_cylinder("Entrance_Light_Bulb", (0.8, -2.0, 1.65), 0.08, 0.15, mat_light, col_archive)

# ==============================================================================
# Helper Functions for Rendering and Exporting
# ==============================================================================
INITIAL_SCENE_STATE = None
HELPER_LIGHT_DATA = []
HELPER_CAMERA_DATA = []
HELPER_WORLD = None

def capture_scene_state():
    scene = bpy.context.scene
    active = bpy.context.view_layer.objects.active
    return {
        "engine": scene.render.engine,
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y,
        "resolution_percentage": scene.render.resolution_percentage,
        "filepath": scene.render.filepath,
        "file_format": scene.render.image_settings.file_format,
        "film_transparent": scene.render.film_transparent,
        "camera_name": scene.camera.name if scene.camera else None,
        "world": scene.world,
        "view_transform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "exposure": scene.view_settings.exposure,
        "gamma": scene.view_settings.gamma,
        "visibility": {obj.name: obj.hide_render for obj in scene.objects},
        "selected_names": [obj.name for obj in bpy.context.selected_objects],
        "active_name": active.name if active else None,
    }

def restore_scene_state(state):
    scene = bpy.context.scene
    scene.render.engine = state["engine"]
    scene.render.resolution_x = state["resolution_x"]
    scene.render.resolution_y = state["resolution_y"]
    scene.render.resolution_percentage = state["resolution_percentage"]
    scene.render.filepath = state["filepath"]
    scene.render.image_settings.file_format = state["file_format"]
    scene.render.film_transparent = state["film_transparent"]
    scene.view_settings.view_transform = state["view_transform"]
    scene.view_settings.look = state["look"]
    scene.view_settings.exposure = state["exposure"]
    scene.view_settings.gamma = state["gamma"]
    camera = bpy.data.objects.get(state["camera_name"]) if state["camera_name"] else None
    scene.camera = camera if camera and camera.type == 'CAMERA' and camera.name in scene.objects else None
    scene.world = state["world"]
    for name, hide_render in state["visibility"].items():
        obj = bpy.data.objects.get(name)
        if obj and obj.name in scene.objects:
            obj.hide_render = hide_render
    bpy.ops.object.select_all(action='DESELECT')
    for name in state["selected_names"]:
        obj = bpy.data.objects.get(name)
        if obj and obj.name in scene.objects:
            obj.select_set(True)
    active = bpy.data.objects.get(state["active_name"]) if state["active_name"] else None
    bpy.context.view_layer.objects.active = active if active and active.name in scene.objects else None

def setup_helpers():
    """Setup cameras and lights for rendering."""
    col_helpers = bpy.data.collections.new("Helpers_Archive_DeepSeek")
    bpy.context.scene.collection.children.link(col_helpers)

    # Lights
    # Sun light
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.name = "Helper_Sun"
    sun.data.energy = 3.0
    HELPER_LIGHT_DATA.append(sun.data)
    sun.rotation_euler = (math.radians(45), math.radians(30), math.radians(-45))
    col_helpers.objects.link(sun)
    bpy.context.collection.objects.unlink(sun)

    # Area fill light
    bpy.ops.object.light_add(type='AREA', location=(-5, -5, 5))
    area = bpy.context.active_object
    area.name = "Helper_Area"
    area.data.energy = 500.0
    area.data.size = 5.0
    HELPER_LIGHT_DATA.append(area.data)
    area.rotation_euler = (math.radians(45), 0, math.radians(-45))
    col_helpers.objects.link(area)
    bpy.context.collection.objects.unlink(area)

    # Cameras
    # Orthographic cameras for 6 views
    cam_data = bpy.data.cameras.new("Helper_Cam")
    HELPER_CAMERA_DATA.append(cam_data)
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 6.0
    
    views = {
        "Front": ((0, -10, 1.4), (math.radians(90), 0, 0)),
        "Back": ((0, 10, 1.4), (math.radians(90), 0, math.radians(180))),
        "Left": ((-10, 0, 1.4), (math.radians(90), 0, math.radians(-90))),
        "Right": ((10, 0, 1.4), (math.radians(90), 0, math.radians(90))),
        "Top": ((0, 0, 10), (0, 0, 0)),
        "Bottom": ((0, 0, -10), (math.radians(180), 0, 0))
    }

    for name, (loc, rot) in views.items():
        cam_obj = bpy.data.objects.new(f"Helper_Cam_{name}", cam_data)
        col_helpers.objects.link(cam_obj)
        cam_obj.location = loc
        cam_obj.rotation_euler = rot

    # Perspective camera for preview
    preview_cam_data = bpy.data.cameras.new("Helper_PreviewCam")
    HELPER_CAMERA_DATA.append(preview_cam_data)
    preview_cam_data.type = 'PERSP'
    preview_cam_data.lens = 50
    preview_cam = bpy.data.objects.new("Helper_PreviewCam", preview_cam_data)
    col_helpers.objects.link(preview_cam)
    preview_cam.location = (6.0, -7.0, 4.8)
    preview_target = mathutils.Vector((0.0, 0.0, 1.3))
    preview_cam.rotation_euler = (preview_target - preview_cam.location).to_track_quat('-Z', 'Y').to_euler()

    return col_helpers, views

def render_scene(state):
    """Render only the archive, then put the original scene state back."""
    global HELPER_WORLD
    scene = bpy.context.scene
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except (TypeError, ValueError):
        scene.render.engine = 'BLENDER_EEVEE'

    HELPER_WORLD = bpy.data.worlds.new("Archive_Render_World")
    HELPER_WORLD.use_nodes = True
    bg = HELPER_WORLD.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.78, 0.80, 0.82, 1.0)
        bg.inputs[1].default_value = 0.65
    scene.world = HELPER_WORLD

    archive_objects = set(bpy.data.collections["Archive_DeepSeek"].objects)
    helper_objects = set(bpy.data.collections["Helpers_Archive_DeepSeek"].objects)
    for obj in scene.objects:
        obj.hide_render = obj not in archive_objects and obj not in helper_objects

    views = {
        "Front": ((0, -10, 1.4), (math.radians(90), 0, 0)),
        "Back": ((0, 10, 1.4), (math.radians(90), 0, math.radians(180))),
        "Left": ((-10, 0, 1.4), (math.radians(90), 0, math.radians(-90))),
        "Right": ((10, 0, 1.4), (math.radians(90), 0, math.radians(90))),
        "Top": ((0, 0, 10), (0, 0, 0)),
        "Bottom": ((0, 0, -10), (math.radians(180), 0, 0)),
    }
    try:
        for name in ("Front", "Back", "Left", "Right", "Top", "Bottom"):
            scene.camera = bpy.data.objects[f"Helper_Cam_{name}"]
            scene.render.filepath = str(REF_PATHS[name])
            bpy.ops.render.render(write_still=True)

        scene.camera = bpy.data.objects["Helper_PreviewCam"]
        scene.render.filepath = str(PREVIEW_PATH)
        bpy.ops.render.render(write_still=True)
    finally:
        restore_scene_state(state)

def export_fbx():
    """Export the model to FBX."""
    bpy.ops.object.select_all(action='DESELECT')
    archive_col = bpy.data.collections.get("Archive_DeepSeek")
    selected_meshes = []
    if archive_col:
        for obj in archive_col.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
                selected_meshes.append(obj)
    if selected_meshes:
        bpy.context.view_layer.objects.active = selected_meshes[0]
    bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH),
        use_selection=True,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Y',
        axis_up='Z',
        object_types={'MESH'}
    )

def cleanup_helpers():
    """Remove temporary render objects and only their now-unused data blocks."""
    helper_col = bpy.data.collections.get("Helpers_Archive_DeepSeek")
    if helper_col:
        for obj in list(helper_col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(helper_col)
    for camera_data in HELPER_CAMERA_DATA:
        if camera_data.users == 0:
            bpy.data.cameras.remove(camera_data)
    for light_data in HELPER_LIGHT_DATA:
        if light_data.users == 0:
            bpy.data.lights.remove(light_data)
    if HELPER_WORLD and HELPER_WORLD.users == 0:
        bpy.data.worlds.remove(HELPER_WORLD)
    HELPER_CAMERA_DATA.clear()
    HELPER_LIGHT_DATA.clear()

def save_blend(state):
    """Restore the incoming scene and save only the editable archive asset."""
    restore_scene_state(state)
    cleanup_helpers()
    restore_scene_state(state)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))

def print_diagnostics():
    """Print mesh statistics and bounding box."""
    archive_col = bpy.data.collections.get("Archive_DeepSeek")
    if not archive_col:
        print("Error: Archive_DeepSeek collection not found.")
        return

    mesh_count = 0
    min_z = float('inf')
    max_x = float('-inf')
    min_x = float('inf')
    max_y = float('-inf')
    min_y = float('inf')
    max_z = float('-inf')
    total_non_manifold = 0
    total_loose_verts = 0

    for obj in archive_col.objects:
        if obj.type == 'MESH':
            mesh_count += 1
            
            # Check bounding box in world space
            bbox = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
            for v in bbox:
                min_x = min(min_x, v.x)
                max_x = max(max_x, v.x)
                min_y = min(min_y, v.y)
                max_y = max(max_y, v.y)
                min_z = min(min_z, v.z)
                max_z = max(max_z, v.z)

            # Topology checks using bmesh
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            
            # Non-manifold edges
            non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
            total_non_manifold += len(non_manifold_edges)
            
            # Loose vertices
            loose_verts = [v for v in bm.verts if len(v.link_edges) == 0]
            total_loose_verts += len(loose_verts)
            
            bm.free()

    print("=" * 60)
    print("Archive_DeepSeek Diagnostics")
    print("=" * 60)
    print(f"Mesh Count: {mesh_count}")
    print(f"World Space Bounding Box:")
    print(f"  X: [{min_x:.3f}, {max_x:.3f}] (Width: {max_x - min_x:.3f} m)")
    print(f"  Y: [{min_y:.3f}, {max_y:.3f}] (Depth: {max_y - min_y:.3f} m)")
    print(f"  Z: [{min_z:.3f}, {max_z:.3f}] (Height: {max_z - min_z:.3f} m)")
    print(f"Lowest Z: {min_z:.3f}")
    print(f"Non-Manifold Edges: {total_non_manifold}")
    print(f"Loose Vertices: {total_loose_verts}")
    print("Note: Per-object topology check cannot detect intersections between different objects.")
    print("=" * 60)
    width = max_x - min_x
    depth = max_y - min_y
    height = max_z - min_z
    if min_z < -1e-4 or width > 4.8 + 1e-4 or depth > 4.8 + 1e-4 or height > 2.8 + 1e-4:
        raise RuntimeError(
            f"Archive dimensions exceed the manifest envelope: {width:.3f} x {depth:.3f} x {height:.3f} m, min Z={min_z:.4f}"
        )

# ==============================================================================
# Main Execution
# ==============================================================================
def main():
    global INITIAL_SCENE_STATE
    INITIAL_SCENE_STATE = capture_scene_state()
    ensure_dirs()
    clean_scene()
    build_model()
    setup_helpers()
    render_scene(INITIAL_SCENE_STATE)
    export_fbx()
    save_blend(INITIAL_SCENE_STATE)
    print_diagnostics()

if __name__ == "__main__":
    main()
