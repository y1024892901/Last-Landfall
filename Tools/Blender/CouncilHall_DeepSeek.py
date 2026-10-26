"""Generate the Council Hall asset for Last Landfall in Blender 5.2.2.

Run from any directory with Blender's background Python. The script writes a
clean Blend, mesh-only FBX, preview, and six orthographic QA renders.
"""

import bpy
import bmesh
import math
from pathlib import Path
from mathutils import Vector


ASSET = "CouncilHall_DeepSeek"
HELPERS = f"Helpers_{ASSET}"
PREFIX = f"{ASSET}_"


def project_root():
    try:
        root = Path(__file__).resolve().parents[2]
        if (root / "Assets" / "LastLandfall").is_dir():
            return root
    except (NameError, IndexError, OSError):
        pass
    return Path.cwd()


ROOT = project_root()
BLEND = ROOT / "Assets/LastLandfall/Art/Source/Buildings/CouncilHall_DeepSeek.blend"
FBX = ROOT / "Assets/LastLandfall/Resources/Models/Buildings/CouncilHall_DeepSeek.fbx"
PREVIEW = ROOT / "Assets/LastLandfall/Art/Previews/Buildings/CouncilHall_DeepSeek.png"
QA_DIR = ROOT / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"
QA_IMAGES = {
    view: QA_DIR / f"CouncilHall_DeepSeek_{view}.png"
    for view in ("Front", "Back", "Left", "Right", "Top", "Bottom")
}

for folder in (BLEND.parent, FBX.parent, PREVIEW.parent, QA_DIR):
    folder.mkdir(parents=True, exist_ok=True)


def remove_owned_data():
    for name in (ASSET, HELPERS):
        col = bpy.data.collections.get(name)
        if col is None:
            continue
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)
    for datablocks in (bpy.data.meshes, bpy.data.curves):
        for datablock in list(datablocks):
            if datablock.name.startswith(PREFIX) and datablock.users == 0:
                datablocks.remove(datablock)
    for material in list(bpy.data.materials):
        if material.name.startswith(PREFIX) and material.users == 0:
            bpy.data.materials.remove(material)


def new_collection(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def assign_to(obj, collection):
    for old_collection in list(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)


def make_material(name, color, roughness=0.72, metallic=0.0, emission=None):
    material = bpy.data.materials.new(f"{PREFIX}{name}")
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if emission:
        shader.inputs["Emission Color"].default_value = (*emission[0], 1.0)
        shader.inputs["Emission Strength"].default_value = emission[1]
    return material


def add_box(name, location, dimensions, material, collection, rotation=(0, 0, 0), bevel=0.012):
    hx, hy, hz = (max(0.001, float(v)) * 0.5 for v in dimensions)
    verts = [
        (-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
        (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz),
    ]
    faces = [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    mesh = bpy.data.meshes.new(f"{PREFIX}{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(f"{PREFIX}{name}", mesh)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    if bevel > 0:
        modifier = obj.modifiers.new("Small edge highlights", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
    return obj


def add_beam(name, start, end, width, thickness, material, collection, bevel=0.008):
    a, b = Vector(start), Vector(end)
    direction = b - a
    if direction.length < 1e-5:
        return None
    obj = add_box(
        name,
        (a + b) * 0.5,
        (width, thickness, direction.length),
        material,
        collection,
        bevel=bevel,
    )
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    return obj


def add_cylinder(name, start, end, radius, material, collection, vertices=10):
    a, b = Vector(start), Vector(end)
    direction = b - a
    if direction.length < 1e-5:
        return None
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=direction.length,
        location=(a + b) * 0.5,
    )
    obj = bpy.context.object
    obj.name = f"{PREFIX}{name}"
    obj.data.name = f"{PREFIX}{name}_Mesh"
    assign_to(obj, collection)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    obj.data.materials.append(material)
    return obj


def add_roof(collection, material):
    # Closed, manifold hip roof: four eave corners and a short centered ridge.
    verts = [
        (-4.72, -4.84, 3.10), (4.72, -4.84, 3.10),
        (4.72, 4.84, 3.10), (-4.72, 4.84, 3.10),
        (0.0, -1.95, 4.02), (0.0, 1.95, 4.02),
    ]
    faces = [
        (0, 1, 4),       # front hip
        (1, 2, 5, 4),    # right slope
        (2, 3, 5),       # rear hip
        (3, 0, 4, 5),    # left slope
        (0, 3, 2, 1),    # underside closes the roof volume
    ]
    mesh = bpy.data.meshes.new(f"{PREFIX}Roof_HipShell_Mesh")
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(f"{PREFIX}Roof_HipShell", mesh)
    collection.objects.link(obj)


def make_window_side(collection, materials, side, center_y, index):
    x_wall = side * 4.30
    x_glass = side * 4.335
    x_frame = side * 4.39
    center_z = 2.08
    width_y, height_z, frame = 1.24, 1.22, 0.12
    add_box(f"Side{side}_Window{index}_Glass", (x_glass, center_y, center_z), (0.035, width_y, height_z), materials["glass"], collection, bevel=0.004)
    for top in (False, True):
        z = center_z + (height_z + frame) * 0.5 * (1 if top else -1)
        add_box(f"Side{side}_Window{index}_FrameH_{int(top)}", (x_frame, center_y, z), (0.12, width_y + 2 * frame, frame), materials["wood_dark"], collection)
    for edge in (-1, 1):
        y = center_y + edge * (width_y + frame) * 0.5
        add_box(f"Side{side}_Window{index}_FrameV_{edge}", (x_frame, y, center_z), (0.12, frame, height_z), materials["wood_dark"], collection)
        shutter_x = side * 4.43
        add_box(f"Side{side}_Window{index}_Shutter_{edge}", (shutter_x, y + edge * 0.12, center_z), (0.09, 0.22, 1.22), materials["wood_light"], collection)
        for slat in range(4):
            z = center_z - 0.42 + slat * 0.27
            add_box(f"Side{side}_Window{index}_Louver_{edge}_{slat}", (side * 4.485, y + edge * 0.12, z), (0.035, 0.24, 0.055), materials["wood_dark"], collection, rotation=(math.radians(-12), 0, 0), bevel=0.004)
    for bar in (-1, 1):
        add_box(f"Side{side}_Window{index}_Mullion_{bar}", (side * 4.395, center_y, center_z + bar * 0.28), (0.10, 1.18, 0.045), materials["wood_dark"], collection, bevel=0.003)


def make_window_front(collection, materials, center_x, index):
    y_glass, y_frame = -4.325, -4.39
    center_z = 2.10
    width_x, height_z, frame = 1.05, 0.96, 0.12
    add_box(f"FrontWindow{index}_Glass", (center_x, y_glass, center_z), (width_x, 0.035, height_z), materials["glass"], collection, bevel=0.004)
    for top in (-1, 1):
        z = center_z + top * (height_z + frame) * 0.5
        add_box(f"FrontWindow{index}_FrameH_{top}", (center_x, y_frame, z), (width_x + 2 * frame, 0.12, frame), materials["wood_dark"], collection)
    for side in (-1, 1):
        x = center_x + side * (width_x + frame) * 0.5
        add_box(f"FrontWindow{index}_FrameV_{side}", (x, y_frame, center_z), (frame, 0.12, height_z), materials["wood_dark"], collection)
    add_box(f"FrontWindow{index}_Mullion", (center_x, -4.405, center_z), (0.045, 0.10, height_z), materials["wood_dark"], collection, bevel=0.003)


def build_model():
    col = new_collection(ASSET)
    mats = {
        "wood_light": make_material("SaltBleached_Wood", (0.47, 0.30, 0.17), 0.82),
        "wood_mid": make_material("Warm_Wood", (0.34, 0.19, 0.105), 0.78),
        "wood_dark": make_material("Reclaimed_Structural_Wood", (0.16, 0.095, 0.055), 0.76),
        "metal": make_material("Faded_SeaGreen_Metal", (0.11, 0.31, 0.28), 0.43, 0.42),
        "patch": make_material("Weathered_GreyGreen_Patch", (0.30, 0.39, 0.37), 0.52, 0.28),
        "stone": make_material("Warm_Grey_Stone", (0.38, 0.37, 0.33), 0.92),
        "glass": make_material("Smoky_Blue_Glass", (0.16, 0.34, 0.43), 0.25, 0.18),
        "board": make_material("Blank_Ochre_Noticeboard", (0.63, 0.39, 0.19), 0.88),
        "lamp": make_material("Warm_Entry_Lamp", (0.9, 0.63, 0.28), 0.3, 0.0, ((1.0, 0.55, 0.2), 2.2)),
        "dark": make_material("Door_Recess", (0.075, 0.052, 0.035), 0.9),
    }

    # Raised stone and timber foundation. The main body spans 8.4 x 8.8 m.
    for ix, x in enumerate((-3.9, -1.3, 1.3, 3.9)):
        for iy, y in enumerate((-4.05, 0.0, 4.05)):
            add_box(f"Foundation_Pier_{ix}_{iy}", (x, y, 0.24), (0.42, 0.42, 0.48), mats["stone"], col)
    for y in (-4.12, 0.0, 4.12):
        add_box(f"Foundation_Beam_X_{y}", (0, y, 0.47), (8.35, 0.24, 0.24), mats["wood_dark"], col)
    for x in (-4.08, 0.0, 4.08):
        add_box(f"Foundation_Beam_Y_{x}", (x, 0, 0.47), (0.24, 8.45, 0.24), mats["wood_dark"], col)
    add_box("Floor_Main", (0, 0, 0.68), (8.40, 8.80, 0.20), mats["wood_mid"], col)
    for i in range(18):
        x = -3.95 + i * (7.90 / 17)
        add_box(f"Floor_Plank_{i:02d}", (x, 0, 0.785), (0.025, 8.60, 0.018), mats["wood_light"], col, bevel=0.002)

    # Porch foundation and platform, tied into the main deck.
    for side in (-1, 1):
        add_box(f"Porch_StonePier_{side}", (side * 1.82, -5.42, 0.22), (0.38, 0.38, 0.44), mats["stone"], col)
    add_box("Porch_Beam_Front", (0, -5.48, 0.45), (3.75, 0.24, 0.20), mats["wood_dark"], col)
    for side in (-1, 1):
        add_box(f"Porch_Beam_Side_{side}", (side * 1.82, -4.95, 0.45), (0.24, 1.30, 0.20), mats["wood_dark"], col)
    add_box("Porch_Deck", (0, -5.02, 0.76), (3.85, 1.62, 0.18), mats["wood_light"], col)
    for i in range(12):
        x = -1.82 + i * (3.64 / 11)
        add_box(f"Porch_DeckBoard_{i:02d}", (x, -5.02, 0.858), (0.025, 1.52, 0.014), mats["wood_mid"], col, bevel=0.002)

    # Main wall shell: segmented around a real central doorway and front windows.
    floor_z, wall_top = 0.88, 2.98
    wall_height = wall_top - floor_z
    wall_center = (wall_top + floor_z) * 0.5
    wall_t = 0.18
    # Front wall low band; leave the door clear.
    low_h = 0.78
    for index, (a, b) in enumerate(((-4.2, -1.0), (1.0, 4.2))):
        add_box(f"Wall_Front_Lower_{index}", ((a+b)*0.5, -4.40, floor_z + low_h*0.5), (b-a, wall_t, low_h), mats["wood_light"], col)
    # Front window zone between sill and head, leaving window openings.
    win_bottom, win_top = 1.58, 2.58
    for index, (a, b) in enumerate(((-4.2,-3.12),(-1.88,-1.0),(1.0,1.88),(3.12,4.2))):
        add_box(f"Wall_Front_WindowZone_{index}", ((a+b)*0.5, -4.40, (win_bottom+win_top)*0.5), (b-a, wall_t, win_top-win_bottom), mats["wood_light"], col)
    add_box("Wall_Front_Header", (0, -4.40, (win_top+wall_top)*0.5), (8.4, wall_t, wall_top-win_top), mats["wood_light"], col)

    # Rear wall with two high clerestory windows and a small central vent.
    rear_openings = [(-2.15, 0.95), (0.0, 0.52), (2.15, 0.95)]
    rear_bottom, rear_top = 2.35, 2.72
    cursor = -4.2
    for i, (center, width) in enumerate(rear_openings):
        left, right = center-width*0.5, center+width*0.5
        if left > cursor:
            add_box(f"Wall_Back_Segment_{i}", ((cursor+left)*0.5, 4.40, wall_center), (left-cursor, wall_t, wall_height), mats["wood_light"], col)
        add_box(f"Wall_Back_Lower_{i}", (center, 4.40, (floor_z+rear_bottom)*0.5), (width, wall_t, rear_bottom-floor_z), mats["wood_light"], col)
        add_box(f"Wall_Back_Upper_{i}", (center, 4.40, (rear_top+wall_top)*0.5), (width, wall_t, wall_top-rear_top), mats["wood_light"], col)
        cursor = right
    if cursor < 4.2:
        add_box("Wall_Back_Segment_End", ((cursor+4.2)*0.5, 4.40, wall_center), (4.2-cursor, wall_t, wall_height), mats["wood_light"], col)

    for index, (center, width) in enumerate(((-2.15,0.95),(0.0,0.52),(2.15,0.95))):
        is_vent = index == 1
        frame_mat = mats["wood_dark"]
        add_box(f"Back_Clerestory_{index}_Glass", (center, 4.31, (rear_bottom+rear_top)*0.5), (width-0.12, 0.035, rear_top-rear_bottom-0.10), mats["dark"] if is_vent else mats["glass"], col, bevel=0.003)
        for side in (-1,1):
            add_box(f"Back_Clerestory_{index}_FrameV_{side}", (center+side*width*0.5, 4.32, (rear_bottom+rear_top)*0.5), (0.09,0.10,rear_top-rear_bottom), frame_mat, col, bevel=0.004)
        for z in (rear_bottom, rear_top):
            add_box(f"Back_Clerestory_{index}_FrameH_{z}", (center,4.32,z), (width,0.10,0.09), frame_mat, col, bevel=0.004)
        if is_vent:
            for slat in range(4):
                z = rear_bottom + 0.07 + slat*0.08
                add_box(f"Back_Vent_Slat_{slat}", (center,4.245,z), (0.40,0.05,0.035), mats["wood_mid"], col, bevel=0.003)

    # Side walls have three genuine glazed openings on both long faces.
    side_centers = (-2.65, 0.0, 2.65)
    side_half_open = 0.72
    for side in (-1, 1):
        x = side * 4.30
        cursor = -4.40
        for index, center_y in enumerate(side_centers):
            left, right = center_y-side_half_open, center_y+side_half_open
            if left > cursor:
                add_box(f"Wall_Side_{side}_PierceSpan_{index}", (x,(cursor+left)*0.5,wall_center), (wall_t,left-cursor,wall_height), mats["wood_light"], col)
            add_box(f"Wall_Side_{side}_Sill_{index}", (x,center_y,(floor_z+1.47)*0.5), (wall_t,2*side_half_open,1.47-floor_z), mats["wood_light"], col)
            add_box(f"Wall_Side_{side}_Head_{index}", (x,center_y,(2.70+wall_top)*0.5), (wall_t,2*side_half_open,wall_top-2.70), mats["wood_light"], col)
            cursor = right
        if cursor < 4.40:
            add_box(f"Wall_Side_{side}_PierceSpan_End", (x,(cursor+4.40)*0.5,wall_center), (wall_t,4.40-cursor,wall_height), mats["wood_light"], col)
        for index, center_y in enumerate(side_centers):
            make_window_side(col, mats, side, center_y, index)

    for index, x in enumerate((-4.18,4.18)):
        for y_side, y in enumerate((-4.38,4.38)):
            add_box(f"Structure_CornerPost_{index}_{y_side}", (x,y,wall_center), (0.22,0.22,wall_height+0.08), mats["wood_dark"], col)
    # Continuous belt beams and visible board seams strengthen the timber frame.
    for z in (0.98, 2.83):
        for side, y in enumerate((-4.43,4.43)):
            add_box(f"Structure_FrontBack_Belt_{z}_{side}", (0,y,z), (8.55,0.16,0.14), mats["wood_dark"], col)
        for side, x in enumerate((-4.33,4.33)):
            add_box(f"Structure_Side_Belt_{z}_{side}", (x,0,z), (0.16,8.80,0.14), mats["wood_dark"], col)
    for side in (-1, 1):
        x = side*4.43
        for index, center_y in enumerate(side_centers):
            for jamb in (-1,1):
                add_box(f"SideWindowJamb_{side}_{index}_{jamb}", (x,center_y+jamb*0.80,2.08), (0.12,0.10,1.30), mats["wood_dark"], col)
    for index, x in enumerate((-3.65,-3.25,3.25,3.65)):
        add_box(f"Front_Siding_Board_{index}", (x,-4.505,1.75), (0.045,0.035,1.85), mats["wood_mid"], col, bevel=0.003)

    # Front entrance, paired timber door leaves, modest glass sidelights and hardware.
    for side in (-1,1):
        add_box(f"DoorFrame_Jamb_{side}", (side*1.05,-4.51,1.69), (0.16,0.18,1.95), mats["wood_dark"], col)
    add_box("DoorFrame_Head", (0,-4.51,2.64), (2.20,0.18,0.16), mats["wood_dark"], col)
    add_box("Door_Recess_Shadow", (0,-4.505,1.66), (1.88,0.035,1.84), mats["dark"], col, bevel=0.002)
    for side in (-1,1):
        door_x = side*0.465
        add_box(f"Door_Leaf_{side}", (door_x,-4.555,1.65), (0.90,0.07,1.78), mats["wood_mid"], col)
        for panel_z in (1.15,2.13):
            add_box(f"Door_Leaf_{side}_Panel_{panel_z}", (door_x,-4.60,panel_z), (0.70,0.025,0.70), mats["wood_light"], col, bevel=0.012)
        for stile in (-1,1):
            add_box(f"Door_Leaf_{side}_Stile_{stile}", (door_x+stile*0.39,-4.605,1.65), (0.05,0.025,1.75), mats["wood_dark"], col, bevel=0.003)
    for side in (-1,1):
        add_box(f"Door_Handle_Mount_{side}", (side*0.10,-4.62,1.58), (0.04,0.08,0.04), mats["patch"], col, bevel=0.003)
        add_cylinder(f"Door_Handle_{side}", (side*0.10,-4.655,1.58), (side*0.10,-4.72,1.58), 0.035, mats["patch"], col, vertices=8)
    for index, x in enumerate((-2.48,2.48)):
        make_window_front(col, mats, x, index)

    # Blank community board and small, warm weatherproof wall lamps.
    add_box("Community_Noticeboard_Back", (-1.57,-4.50,1.96), (0.78,0.10,0.88), mats["wood_dark"], col)
    add_box("Community_Noticeboard_Blank", (-1.57,-4.565,1.96), (0.66,0.035,0.74), mats["board"], col)
    add_box("EntryLamp_Housing", (-1.37,-4.55,2.49), (0.16,0.12,0.23), mats["wood_dark"], col)
    add_box("EntryLamp_Glass", (-1.37,-4.62,2.49), (0.09,0.04,0.13), mats["lamp"], col, bevel=0.006)
    add_box("EntryLamp_Housing_R", (1.38,-4.55,2.49), (0.16,0.12,0.23), mats["wood_dark"], col)
    add_box("EntryLamp_Glass_R", (1.38,-4.62,2.49), (0.09,0.04,0.13), mats["lamp"], col, bevel=0.006)

    # Broad porch, paired square posts, diagonal braces, open handrails and roof.
    for side in (-1,1):
        x = side*1.75
        add_box(f"Porch_Post_{side}", (x,-5.62,1.80), (0.22,0.22,2.12), mats["wood_dark"], col)
        add_beam(f"Porch_KneeBrace_{side}", (x,-5.52,2.15), (side*0.90,-4.70,2.82), 0.13, 0.13, mats["wood_dark"], col)
        add_box(f"Porch_Railing_Post_{side}", (side*1.85,-4.82,1.05), (0.14,0.14,0.60), mats["wood_dark"], col)
        add_beam(f"Porch_SideHandrail_{side}", (side*1.85,-5.50,1.27), (side*1.85,-4.80,1.27), 0.10,0.10,mats["wood_dark"],col)
        add_beam(f"Porch_SideLowerRail_{side}", (side*1.85,-5.48,0.95), (side*1.85,-4.82,0.95), 0.07,0.07,mats["wood_mid"],col)
    add_box("Porch_FrontHeader", (0,-5.72,2.91), (4.05,0.22,0.20), mats["wood_dark"], col)
    add_box("Porch_Canopy", (0,-5.16,3.03), (4.28,1.72,0.15), mats["metal"], col, rotation=(math.radians(12),0,0), bevel=0.018)
    for i in range(10):
        x = -2.02 + i*0.45
        add_box(f"Porch_Canopy_Rib_{i}", (x,-5.16,3.115), (0.035,1.66,0.025), mats["patch"], col, rotation=(math.radians(12),0,0), bevel=0.003)

    # Three broad, low timber treads meet the raised landing and remain within the envelope.
    for index, (y, top_z) in enumerate(((-6.00,0.24),(-5.65,0.48),(-5.30,0.72)), start=1):
        add_box(f"Entry_Step_{index}", (0,y,top_z*0.5), (3.45,0.38,top_z), mats["wood_light"], col)
        add_box(f"Entry_Step_Nosing_{index}", (0,y-0.18,top_z-0.035), (3.48,0.045,0.07), mats["wood_dark"], col, bevel=0.006)

    # Accessible side ramp on +X. Both rails follow the real landing-to-grade slope.
    ramp_x, ramp_width = 3.35, 1.24
    ramp_high = Vector((ramp_x,-4.48,0.75))
    ramp_low = Vector((ramp_x,-6.20,0.10))
    add_beam("Ramp_Deck", ramp_low, ramp_high, ramp_width, 0.14, mats["wood_light"], col, bevel=0.012)
    ramp_vector = ramp_high-ramp_low
    for support in (0.25,0.50,0.75):
        point = ramp_low + ramp_vector*support
        add_beam(f"Ramp_UndersideCrossTie_{support}", (ramp_x-0.76,point.y,point.z-0.14), (ramp_x+0.76,point.y,point.z-0.14), 0.14,0.12,mats["wood_dark"],col)
    for edge in (-1,1):
        rail_x = ramp_x + edge*(ramp_width*0.5-0.06)
        add_beam(f"Ramp_Handrail_{edge}", (rail_x,ramp_low.y,ramp_low.z+0.94), (rail_x,ramp_high.y,ramp_high.z+0.94), 0.10,0.10,mats["wood_dark"],col)
        for i, t in enumerate((0.0,0.34,0.68,1.0)):
            point = ramp_low + ramp_vector*t
            add_beam(f"Ramp_RailPost_{edge}_{i}", (rail_x,point.y,point.z+0.08), (rail_x,point.y,point.z+0.92), 0.09,0.09,mats["wood_dark"],col)
    for i, t in enumerate((0.24,0.52,0.80)):
        point = ramp_low + ramp_vector*t
        add_box(f"Ramp_StoneFoot_{i}", (ramp_x,point.y,0.18), (1.05,0.34,0.36), mats["stone"], col)

    # Hip roof, narrow ridge cap, restrained corrugation, patches and gutters.
    add_roof(col, mats["metal"])
    add_box("Roof_RidgeCap", (0,0,4.045), (0.20,4.30,0.07), mats["patch"], col, bevel=0.012)
    # Long roof planes receive evenly spaced fine raised seams.
    for side in (-1,1):
        for i, y in enumerate((-1.72,-1.28,-0.84,-0.40,0.04,0.48,0.92,1.36,1.80)):
            add_beam(f"Roof_Corrugation_{side}_{i}", (side*4.69,y,3.15), (side*0.08,y,3.98), 0.028,0.024,mats["patch"],col,bevel=0.002)
        for i, x in enumerate((-3.35,-2.52,-1.69,-0.86,0,0.86,1.69,2.52,3.35)):
            edge_z = 3.10 + 0.92*(1.0-abs(x)/4.72)
            add_beam(f"Roof_HipSeam_{side}_{i}", (x,side*4.79,3.12), (x*0.06,side*1.96,3.98), 0.025,0.022,mats["patch"],col,bevel=0.002)
    add_box("Roof_RepairPatch_Front", (2.20,-3.55,3.42), (0.72,0.48,0.035), mats["patch"], col, rotation=(math.radians(18),0,0), bevel=0.006)
    add_box("Roof_RepairPatch_Back", (-2.50,3.62,3.48), (0.64,0.44,0.035), mats["patch"], col, rotation=(math.radians(-18),0,0), bevel=0.006)
    for y in (-4.82,4.82):
        add_beam(f"Roof_Gutter_X_{y}", (-4.65,y,3.06), (4.65,y,3.06), 0.16,0.12,mats["wood_dark"],col)
    for x in (-4.70,4.70):
        add_beam(f"Roof_Gutter_Y_{x}", (x,-4.75,3.06), (x,4.75,3.06), 0.14,0.11,mats["wood_dark"],col)
    for side_x in (-1,1):
        for side_y in (-1,1):
            x, y = side_x*4.60, side_y*4.72
            add_cylinder(f"Downpipe_Vertical_{side_x}_{side_y}", (x,y,0.84), (x,y,3.08), 0.045, mats["patch"], col, vertices=10)
            add_beam(f"Downpipe_Elbow_{side_x}_{side_y}", (x-side_x*0.16,y,3.20), (x,y,3.04), 0.10,0.09,mats["patch"],col,bevel=0.003)
            add_box(f"Downpipe_Shoe_{side_x}_{side_y}", (x-side_x*0.10,y,0.86), (0.16,0.14,0.12), mats["wood_dark"], col, bevel=0.008)

    return col


def create_render_helpers(scene, helper_collection):
    cam_data = bpy.data.cameras.new(f"{PREFIX}TemporaryCameraData")
    cam = bpy.data.objects.new(f"{PREFIX}TemporaryCamera", cam_data)
    helper_collection.objects.link(cam)
    cam_data.type = "ORTHO"
    cam_data.lens = 50
    cam_data.clip_start = 0.05
    cam_data.clip_end = 250
    light_data = bpy.data.lights.new(f"{PREFIX}KeyData", "AREA")
    light = bpy.data.objects.new(f"{PREFIX}KeyLight", light_data)
    helper_collection.objects.link(light)
    light.location = (1,-8,12)
    light_data.energy = 1800
    light_data.shape = "DISK"
    light_data.size = 8
    light.rotation_euler = (Vector((0,0,1.6))-light.location).to_track_quat("-Z","Y").to_euler()
    fill_data = bpy.data.lights.new(f"{PREFIX}FillData", "AREA")
    fill = bpy.data.objects.new(f"{PREFIX}FillLight", fill_data)
    helper_collection.objects.link(fill)
    fill.location = (8,3,7)
    fill_data.energy = 950
    fill_data.size = 7
    fill.rotation_euler = (Vector((0,0,1.7))-fill.location).to_track_quat("-Z","Y").to_euler()
    sun_data = bpy.data.lights.new(f"{PREFIX}SunData", "SUN")
    sun = bpy.data.objects.new(f"{PREFIX}Sun", sun_data)
    helper_collection.objects.link(sun)
    sun_data.energy = 1.1
    sun.rotation_euler = (math.radians(28), math.radians(-18), math.radians(-25))
    return cam


def point_camera(camera, location, target=(0,0,1.95), ortho_scale=14.8):
    camera.location = location
    camera.rotation_euler = (Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.ortho_scale = ortho_scale


def render_outputs(scene, model_collection):
    helper_collection = new_collection(HELPERS)
    camera = create_render_helpers(scene, helper_collection)
    old = {
        "camera": scene.camera,
        "world": scene.world,
        "engine": scene.render.engine,
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y,
        "resolution_percentage": scene.render.resolution_percentage,
        "filepath": scene.render.filepath,
        "file_format": scene.render.image_settings.file_format,
        "color_mode": scene.render.image_settings.color_mode,
        "film_transparent": scene.render.film_transparent,
        "view_transform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "exposure": scene.view_settings.exposure,
        "gamma": scene.view_settings.gamma,
    }
    hide_states = {obj: obj.hide_render for obj in scene.objects}
    try:
        world = bpy.data.worlds.new(f"{PREFIX}TemporaryStudioWorld")
        world.use_nodes = True
        background = world.node_tree.nodes.get("Background")
        background.inputs["Color"].default_value = (0.48,0.52,0.54,1)
        background.inputs["Strength"].default_value = 0.7
        scene.world = world
        scene.camera = camera
        available_engines = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys()
        scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in available_engines else "BLENDER_EEVEE"
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
        scene.render.film_transparent = False
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.exposure = 0
        scene.view_settings.gamma = 1
        for obj in scene.objects:
            if model_collection not in obj.users_collection and helper_collection not in obj.users_collection:
                obj.hide_render = True
        scene.render.resolution_x = 1200
        scene.render.resolution_y = 1200
        target = (0,0,2.0)
        views = {
            "Front": ((0,-21,2.0), 14.2),
            "Back": ((0,21,2.0), 14.2),
            "Left": ((-21,0,2.0), 14.2),
            "Right": ((21,0,2.0), 14.2),
            "Top": ((0,0,23), 13.0),
            "Bottom": ((0,0,-20), 13.0),
        }
        for name, (location, scale) in views.items():
            point_camera(camera, location, target, scale)
            scene.render.filepath = str(QA_IMAGES[name])
            bpy.ops.render.render(write_still=True)
        scene.render.resolution_x = 1500
        scene.render.resolution_y = 1200
        scene.render.filepath = str(PREVIEW)
        point_camera(camera, (16,-20,13), target, 15.4)
        bpy.ops.render.render(write_still=True)
    finally:
        for obj, state in hide_states.items():
            if obj.name in bpy.data.objects:
                obj.hide_render = state
        scene.camera = old["camera"]
        scene.world = old["world"]
        scene.render.engine = old["engine"]
        scene.render.resolution_x = old["resolution_x"]
        scene.render.resolution_y = old["resolution_y"]
        scene.render.resolution_percentage = old["resolution_percentage"]
        scene.render.filepath = old["filepath"]
        scene.render.image_settings.file_format = old["file_format"]
        scene.render.image_settings.color_mode = old["color_mode"]
        scene.render.film_transparent = old["film_transparent"]
        scene.view_settings.view_transform = old["view_transform"]
        scene.view_settings.look = old["look"]
        scene.view_settings.exposure = old["exposure"]
        scene.view_settings.gamma = old["gamma"]
        bpy.data.collections.remove(helper_collection, do_unlink=True)
        for data in list(bpy.data.cameras):
            if data.name.startswith(PREFIX) and data.users == 0:
                bpy.data.cameras.remove(data)
        for data in list(bpy.data.lights):
            if data.name.startswith(PREFIX) and data.users == 0:
                bpy.data.lights.remove(data)
        for world in list(bpy.data.worlds):
            if world.name.startswith(PREFIX) and world.users == 0:
                bpy.data.worlds.remove(world)


def diagnostics(collection):
    meshes = [obj for obj in collection.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("No mesh objects were created")
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    min_v = Vector((min(p.x for p in points),min(p.y for p in points),min(p.z for p in points)))
    max_v = Vector((max(p.x for p in points),max(p.y for p in points),max(p.z for p in points)))
    dims = max_v-min_v
    non_manifold = 0
    loose = 0
    for obj in meshes:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        non_manifold += sum(1 for edge in bm.edges if not edge.is_manifold)
        loose += sum(1 for vertex in bm.verts if not vertex.link_edges)
        bm.free()
    print(f"{ASSET} meshes={len(meshes)}")
    print(f"BOUNDS min=({min_v.x:.4f},{min_v.y:.4f},{min_v.z:.4f}) max=({max_v.x:.4f},{max_v.y:.4f},{max_v.z:.4f}) size=({dims.x:.4f},{dims.y:.4f},{dims.z:.4f})")
    print(f"MIN_Z={min_v.z:.4f} NON_MANIFOLD_EDGES={non_manifold} LOOSE_VERTICES={loose}")
    print("Note: per-object topology checks do not detect intersections between distinct mesh objects.")
    if dims.x > 9.6+1e-3 or dims.y > 12.0+1e-3 or dims.z > 4.1+1e-3 or min_v.z < -1e-3:
        for obj in meshes:
            obj_points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            obj_min_z = min(point.z for point in obj_points)
            obj_max_z = max(point.z for point in obj_points)
            if obj_min_z < -1e-3 or obj_max_z > 4.1+1e-3:
                print(f"ENVELOPE_OBJECT {obj.name} loc={tuple(round(v,4) for v in obj.location)} minZ={obj_min_z:.4f} maxZ={obj_max_z:.4f}")
        raise RuntimeError(f"Council Hall exceeds its approved envelope: {tuple(dims)} minZ={min_v.z}")


def main():
    scene = bpy.context.scene
    prior_selected = list(bpy.context.selected_objects)
    prior_active = bpy.context.view_layer.objects.active
    remove_owned_data()
    model = build_model()
    bpy.context.view_layer.update()
    diagnostics(model)

    # Export only model meshes; the building origin stays at its plan center.
    bpy.ops.object.select_all(action="DESELECT")
    model_meshes = [obj for obj in model.objects if obj.type == "MESH"]
    for obj in model_meshes:
        obj.select_set(True)
    if model_meshes:
        bpy.context.view_layer.objects.active = model_meshes[0]
    bpy.ops.export_scene.fbx(
        filepath=str(FBX),
        use_selection=True,
        object_types={"MESH"},
        apply_scale_options="FBX_SCALE_UNITS",
        use_mesh_modifiers=True,
        axis_forward="-Y",
        axis_up="Z",
        bake_space_transform=False,
        path_mode="AUTO",
    )

    render_outputs(scene, model)
    bpy.ops.object.select_all(action="DESELECT")
    if prior_active and prior_active.name in bpy.data.objects:
        bpy.context.view_layer.objects.active = prior_active
    for obj in prior_selected:
        if obj.name in bpy.data.objects:
            obj.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print(f"Saved {BLEND}")
    print(f"Exported {FBX}")
    print(f"Preview {PREVIEW}")


if __name__ == "__main__":
    main()
