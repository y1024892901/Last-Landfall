"""Generate the Rescue Speedboat dynamic 3D vehicle model for Last Landfall.

Run with Blender 5.2 from the project root:
    & "D:\\Blender 5.2\\blender.exe" --background --python Tools/Blender/create_rescue_boat.py
"""

from __future__ import annotations

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
ART_SOURCE = ROOT / "Assets/LastLandfall/Art/Source/Vehicles"
MODELS = ROOT / "Assets/LastLandfall/Resources/Models/Vehicles"
PREVIEWS = ROOT / "Assets/LastLandfall/Art/Previews/Vehicles"

ASSET_ID = "RescueBoat_Speedboat"
BLEND_PATH = ART_SOURCE / f"{ASSET_ID}.blend"
FBX_PATH = MODELS / f"{ASSET_ID}.fbx"
PREVIEW_PATH = PREVIEWS / f"{ASSET_ID}.png"

COLLECTION = None
OBJECTS = []
MATERIALS = {}


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block_group in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(block_group):
            if block.users == 0:
                block_group.remove(block)


def make_material(name, color, metallic=0.0, roughness=0.82):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    output = nodes.new("ShaderNodeOutputMaterial")
    mat.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def setup_materials():
    prefix = f"{ASSET_ID} | "
    return {
        "orange": make_material(prefix + "rescue safety orange", (0.92, 0.38, 0.12), roughness=0.55),
        "hull_white": make_material(prefix + "weathered hull white", (0.84, 0.86, 0.84), roughness=0.6),
        "teal": make_material(prefix + "rescue teal accent", (0.18, 0.42, 0.40), roughness=0.6),
        "dark_iron": make_material(prefix + "outboard & arch iron", (0.12, 0.14, 0.15), metallic=0.7, roughness=0.4),
        "deck_non_skid": make_material(prefix + "deck non-skid gray", (0.32, 0.35, 0.36), roughness=0.88),
        "glass": make_material(prefix + "windshield smoky glass", (0.12, 0.28, 0.30), metallic=0.1, roughness=0.2),
        "rubber": make_material(prefix + "fender bumper rubber", (0.08, 0.09, 0.10), roughness=0.85),
        "beacon_amber": make_material(prefix + "signal amber", (0.98, 0.62, 0.15), roughness=0.3),
        "beacon_blue": make_material(prefix + "emergency blue", (0.15, 0.50, 0.95), roughness=0.3),
        "wood_crate": make_material(prefix + "cargo salvage crate", (0.48, 0.36, 0.22), roughness=0.85),
    }


def add_mesh(name, vertices, faces, mat):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(clean_customdata=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    COLLECTION.objects.link(obj)
    if mat:
        mesh.materials.append(mat)
    for face in mesh.polygons:
        face.use_smooth = False
    OBJECTS.append(obj)
    return obj


def box(name, location, size, mat, rotation=None):
    x, y, z = (float(v) * 0.5 for v in size)
    verts = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
             (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    obj = add_mesh(name, verts, faces, mat)
    obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    return obj


def cylinder(name, location, radius, depth, mat, vertices=10, rotation=None, radius_top=None):
    top_r = radius if radius_top is None else radius_top
    verts = []
    for z, r in ((-depth * 0.5, radius), (depth * 0.5, top_r)):
        for i in range(vertices):
            a = math.tau * i / vertices
            verts.append((math.cos(a) * r, math.sin(a) * r, z))
    faces = [tuple(range(vertices - 1, -1, -1)), tuple(range(vertices, vertices * 2))]
    for i in range(vertices):
        j = (i + 1) % vertices
        faces.append((i, j, vertices + j, vertices + i))
    obj = add_mesh(name, verts, faces, mat)
    obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    return obj


def build_rescue_boat():
    # Sizing: Length ~5.8m, Beam (Width) ~2.3m, Total Height ~2.4m.
    # Orientation: Bow points -Y, Stern points +Y.
    # Waterline: Z = 0.0. Hull bottom reaches Z = -0.36m (submerged draft).
    
    # --- 1. Hydrodynamic Stepped V-Hull ---
    # Stations along Y (from stern +2.6 to bow -2.9)
    # (y, top_half_width, bottom_half_width, deck_z, keel_z)
    stations = [
        (2.60, 1.05, 0.72, 0.58, -0.28),   # Transom (Stern)
        (1.50, 1.14, 0.80, 0.62, -0.34),   # Aft body
        (0.00, 1.15, 0.78, 0.65, -0.38),   # Midships
        (-1.40, 1.00, 0.62, 0.76, -0.32),  # Forward body
        (-2.40, 0.62, 0.32, 0.88, -0.15),  # Bow flare
        (-2.90, 0.08, 0.04, 0.98,  0.08),  # Bow stem
    ]
    
    hull_verts = []
    for y, top_w, bot_w, top_z, bot_z in stations:
        hull_verts.extend([
            (-top_w, y, top_z),  # 0: Port Gunwale
            ( top_w, y, top_z),  # 1: Starboard Gunwale
            (-bot_w, y, bot_z),  # 2: Port Chine/Keel
            ( bot_w, y, bot_z),  # 3: Starboard Chine/Keel
        ])
        
    hull_faces = []
    for i in range(len(stations) - 1):
        a = i * 4
        b = (i + 1) * 4
        # Port topside hull
        hull_faces.append((a, b, b + 2, a + 2))
        # Starboard topside hull
        hull_faces.append((b + 1, a + 1, a + 3, b + 3))
        # Bottom V-keel
        hull_faces.append((a + 2, b + 2, b + 3, a + 3))

    # Transom closure (at stern station 0)
    hull_faces.append((0, 1, 3, 2))
    # Bow closure
    last = (len(stations) - 1) * 4
    hull_faces.append((last + 1, last, last + 2, last + 3))

    hull_mesh = bpy.data.meshes.new("Boat_Hull_Mesh")
    hull_mesh.from_pydata(hull_verts, [], hull_faces)
    hull_mesh.validate(clean_customdata=False)
    hull_mesh.update()
    
    # Recalculate normals
    bm = bmesh.new()
    bm.from_mesh(hull_mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(hull_mesh)
    bm.free()
    
    hull_obj = bpy.data.objects.new("Hull_Main", hull_mesh)
    COLLECTION.objects.link(hull_obj)
    hull_obj.data.materials.append(MATERIALS["orange"])
    for f in hull_mesh.polygons:
        f.use_smooth = False
    OBJECTS.append(hull_obj)

    # --- 2. Lower Hull / Antifouling White Chine ---
    box("Hull_KeelPlate", (0.0, 0.1, -0.32), (0.24, 4.6, 0.14), MATERIALS["hull_white"])

    # --- 3. Gunwale Rub-Rails & Inflatable D-Fenders ---
    for side, sign in (("Port", -1), ("Starboard", 1)):
        # Main heavy rubber bumper along gunwale
        box(f"FenderRail_{side}", (sign * 1.10, 0.35, 0.63), (0.14, 4.4, 0.12), MATERIALS["rubber"])
        # Bow curved bumper
        box(f"BowBumper_{side}", (sign * 0.58, -2.15, 0.86), (0.12, 1.4, 0.12), MATERIALS["rubber"],
            rotation=(0.0, 0.0, sign * math.radians(24)))

    # Bow nose nose-cone bumper
    box("BowNoseCone", (0.0, -2.92, 0.98), (0.32, 0.22, 0.24), MATERIALS["rubber"])

    # --- 4. Main Self-Bailing Deck (Z: 0.38) ---
    box("MainDeck_Floor", (0.0, 0.50, 0.40), (1.92, 3.8, 0.08), MATERIALS["deck_non_skid"])
    box("ForeDeck_CastingPlatform", (0.0, -1.85, 0.72), (1.50, 1.7, 0.10), MATERIALS["teal"])

    # --- 5. Center Console & Cockpit (Y: -0.20 to -0.80) ---
    box("Console_Base", (0.0, -0.50, 0.85), (1.10, 0.85, 0.82), MATERIALS["hull_white"])
    # Dashboard angled top
    box("Console_Dash", (0.0, -0.38, 1.28), (1.06, 0.55, 0.12), MATERIALS["deck_non_skid"],
        rotation=(math.radians(-15), 0.0, 0.0))
    # Marine Navigation / GPS Radar Screen
    box("Console_GPS_Screen", (0.18, -0.42, 1.35), (0.28, 0.04, 0.18), MATERIALS["glass"],
        rotation=(math.radians(-15), 0.0, 0.0))
    # Marine Steering Wheel
    cylinder("Steering_Column", (-0.22, -0.30, 1.25), 0.035, 0.22, MATERIALS["dark_iron"],
             rotation=(math.radians(-65), 0.0, 0.0))
    cylinder("Steering_Wheel", (-0.22, -0.22, 1.34), 0.16, 0.03, MATERIALS["dark_iron"],
             rotation=(math.radians(-65), 0.0, 0.0), vertices=12)
    # Dual Engine Throttles
    box("Throttle_Quadrant", (0.0, -0.32, 1.30), (0.08, 0.12, 0.10), MATERIALS["dark_iron"])

    # Heavy-duty wrap-around polycarbonate windshield
    box("Windshield_Front", (0.0, -0.66, 1.45), (1.04, 0.04, 0.32), MATERIALS["glass"],
        rotation=(math.radians(-12), 0.0, 0.0))
    box("Windshield_Wing_Port", (-0.52, -0.52, 1.45), (0.04, 0.32, 0.32), MATERIALS["glass"],
        rotation=(0.0, 0.0, math.radians(-15)))
    box("Windshield_Wing_Stbd", (0.52, -0.52, 1.45), (0.04, 0.32, 0.32), MATERIALS["glass"],
        rotation=(0.0, 0.0, math.radians(15)))

    # Dual Jockey / Leaning Post Helm Seats
    box("HelmSeat_Base", (0.0, 0.40, 0.72), (0.95, 0.52, 0.56), MATERIALS["hull_white"])
    box("HelmSeat_Cushion_Port", (-0.24, 0.40, 1.02), (0.42, 0.48, 0.10), MATERIALS["teal"])
    box("HelmSeat_Cushion_Stbd", (0.24, 0.40, 1.02), (0.42, 0.48, 0.10), MATERIALS["teal"])

    # --- 6. Heavy-Duty Aluminum Radar / Tow Arch (Rollbar) ---
    for side, sign in (("Port", -1), ("Starboard", 1)):
        # Forward arch pillar
        cylinder(f"Arch_PillarFore_{side}", (sign * 0.75, -0.15, 1.50), 0.045, 1.40, MATERIALS["dark_iron"])
        # Aft angled brace
        cylinder(f"Arch_PillarAft_{side}", (sign * 0.75, 0.45, 1.46), 0.04, 1.35, MATERIALS["dark_iron"],
                 rotation=(math.radians(18), 0.0, 0.0))

    # Top crossbar bridge
    box("Arch_Crossbar", (0.0, -0.15, 2.18), (1.60, 0.12, 0.08), MATERIALS["dark_iron"])
    box("Arch_TowingPoint", (0.0, 0.30, 2.10), (0.16, 0.90, 0.08), MATERIALS["dark_iron"])

    # Radar Radome (dome on arch)
    cylinder("Radar_Dome", (0.0, -0.15, 2.30), 0.22, 0.14, MATERIALS["hull_white"], vertices=12, radius_top=0.18)
    
    # Emergency Flashing Beacons on Arch
    cylinder("Beacon_Amber", (-0.55, -0.15, 2.28), 0.06, 0.12, MATERIALS["beacon_amber"])
    cylinder("Beacon_Blue", (0.55, -0.15, 2.28), 0.06, 0.12, MATERIALS["beacon_blue"])

    # High-intensity LED Searchlight
    box("Searchlight_Housing", (0.0, -0.26, 2.12), (0.22, 0.16, 0.14), MATERIALS["hull_white"])
    box("Searchlight_Lens", (0.0, -0.34, 2.12), (0.18, 0.02, 0.11), MATERIALS["beacon_amber"])

    # VHF Marine Whip Antenna
    cylinder("VHF_Antenna", (0.72, 0.45, 2.45), 0.012, 1.10, MATERIALS["dark_iron"])

    # --- 7. Twin Outboard Marine Engines (Transom Stern) ---
    for engine_side, eng_x in (("Port", -0.48), ("Starboard", 0.48)):
        # Engine bracket attached to transom
        box(f"Outboard_Bracket_{engine_side}", (eng_x, 2.65, 0.45), (0.24, 0.20, 0.28), MATERIALS["dark_iron"])
        # Top motor cowling
        box(f"Outboard_Cowling_{engine_side}", (eng_x, 2.92, 0.68), (0.32, 0.54, 0.42), MATERIALS["dark_iron"])
        box(f"Outboard_TopStripe_{engine_side}", (eng_x, 2.92, 0.85), (0.26, 0.48, 0.06), MATERIALS["orange"])
        # Midsection leg / driveshaft housing
        box(f"Outboard_Leg_{engine_side}", (eng_x, 2.85, 0.15), (0.16, 0.26, 0.70), MATERIALS["dark_iron"])
        # Torpedo lower unit & skeg
        box(f"Outboard_Torpedo_{engine_side}", (eng_x, 2.85, -0.22), (0.18, 0.48, 0.16), MATERIALS["dark_iron"])
        box(f"Outboard_Skeg_{engine_side}", (eng_x, 2.85, -0.36), (0.04, 0.28, 0.18), MATERIALS["dark_iron"])
        # 3-Blade Stainless Propeller
        cylinder(f"Outboard_PropHub_{engine_side}", (eng_x, 3.12, -0.22), 0.06, 0.12, MATERIALS["dark_iron"],
                 rotation=(math.radians(90), 0.0, 0.0))
        for blade_i, blade_ang in enumerate((0, 120, 240)):
            box(f"PropBlade_{engine_side}_{blade_i}", (eng_x, 3.12, -0.22), (0.03, 0.02, 0.26), MATERIALS["dark_iron"],
                rotation=(0.0, math.radians(blade_ang), 0.0))

    # --- 8. Salvage & Rescue Equipment (Cargo & Safety) ---
    # Life Buoy Rings mounted on sides of console
    for ring_side, rx in (("Port", -0.60), ("Starboard", 0.60)):
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.22, minor_radius=0.05,
            location=(rx, -0.50, 0.95), rotation=(0.0, math.radians(90), 0.0),
            major_segments=16, minor_segments=8
        )
        ring_obj = bpy.context.active_object
        ring_obj.name = f"LifeRing_{ring_side}"
        ring_obj.data.materials.append(MATERIALS["orange"])
        for col in list(ring_obj.users_collection):
            col.objects.unlink(ring_obj)
        COLLECTION.objects.link(ring_obj)
        apply_flat_shading(ring_obj)
        OBJECTS.append(ring_obj)

    # Waterproof Cargo & Salvage Crates on rear deck
    box("SalvageCrate_01", (-0.35, 1.40, 0.65), (0.50, 0.50, 0.42), MATERIALS["wood_crate"])
    box("SalvageCrate_02", (0.35, 1.40, 0.60), (0.46, 0.46, 0.34), MATERIALS["orange"])
    # Fuel Jerrycan / Reserve Tank
    box("FuelJerrycan", (0.38, 2.05, 0.62), (0.24, 0.36, 0.36), MATERIALS["orange"])

    # Mooring Cleats
    for cleat_name, (cx, cy, cz) in [
        ("Cleat_Bow", (0.0, -2.60, 0.98)),
        ("Cleat_Stern_Port", (-0.88, 2.30, 0.68)),
        ("Cleat_Stern_Stbd", (0.88, 2.30, 0.68)),
    ]:
        box(cleat_name, (cx, cy, cz), (0.22, 0.08, 0.07), MATERIALS["dark_iron"])


def apply_flat_shading(obj):
    if obj.type == "MESH":
        for face in obj.data.polygons:
            face.use_smooth = False


def setup_lighting_and_camera():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"

    # Water reflection plane for preview
    water_mesh = bpy.data.meshes.new("PreviewWaterMesh")
    water_mesh.from_pydata([(-8, -8, 0), (8, -8, 0), (8, 8, 0), (-8, 8, 0)], [], [(0, 1, 2, 3)])
    water_mesh.update()
    water_obj = bpy.data.objects.new("PreviewWater", water_mesh)
    COLLECTION.objects.link(water_obj)
    water_obj.data.materials.append(make_material("StylizedWater", (0.12, 0.32, 0.40), metallic=0.1, roughness=0.15))

    # Camera
    cam_data = bpy.data.cameras.new("BoatCamera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 7.5
    cam_obj = bpy.data.objects.new("BoatCamera", cam_data)
    COLLECTION.objects.link(cam_obj)
    cam_obj.location = (6.0, -8.0, 6.5)
    target = Vector((0.0, 0.0, 0.6))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam_obj

    # Sun / Key Light
    key_data = bpy.data.lights.new("SunKey", "SUN")
    key_data.energy = 4.0
    key_data.color = (1.0, 0.95, 0.88)
    key_obj = bpy.data.objects.new("SunKey", key_data)
    COLLECTION.objects.link(key_obj)
    key_obj.rotation_euler = (math.radians(45), math.radians(25), math.radians(-40))

    # Sky Fill
    fill_data = bpy.data.lights.new("SkyFill", "SUN")
    fill_data.energy = 1.5
    fill_data.color = (0.7, 0.85, 1.0)
    fill_obj = bpy.data.objects.new("SkyFill", fill_data)
    COLLECTION.objects.link(fill_obj)
    fill_obj.rotation_euler = (math.radians(30), math.radians(-30), math.radians(140))

    return water_obj, cam_obj, [key_obj, fill_obj]


def main():
    global COLLECTION, MATERIALS
    ART_SOURCE.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    PREVIEWS.mkdir(parents=True, exist_ok=True)

    clear_scene()
    COLLECTION = bpy.context.collection
    MATERIALS = setup_materials()
    build_rescue_boat()

    # Create root empty object
    root = bpy.data.objects.new(f"{ASSET_ID}_Root", None)
    COLLECTION.objects.link(root)
    for obj in list(OBJECTS):
        obj.parent = root

    # Render Preview
    water_obj, cam_obj, lights = setup_lighting_and_camera()
    bpy.context.scene.render.resolution_x = 1000
    bpy.context.scene.render.resolution_y = 750
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered boat preview to {PREVIEW_PATH}")

    # Remove preview-only items before export
    bpy.data.objects.remove(water_obj, do_unlink=True)
    bpy.data.objects.remove(cam_obj, do_unlink=True)
    for l in lights:
        bpy.data.objects.remove(l, do_unlink=True)

    # Save .blend
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print(f"Saved .blend to {BLEND_PATH}")

    # Export FBX
    bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH),
        use_selection=False,
        object_types={"EMPTY", "MESH"},
        axis_forward="-Z",
        axis_up="Y",
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="AUTO",
    )
    print(f"Exported FBX to {FBX_PATH}")


if __name__ == "__main__":
    main()
