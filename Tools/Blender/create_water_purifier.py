"""Create a low-poly water collection and purification station for Last Landfall.

Run from any working directory with Blender:
    blender --background --python Tools/Blender/create_water_purifier.py

The generated 2 x 2 m building is centered on the origin, rests on z=0, and
faces local -Y. The .blend keeps a small preview setup; exports select only
the model. FBX is preferred, with Blender's built-in OBJ exporter as fallback.
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
BLEND_PATH = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Buildings/WaterPurifier.blend"
FBX_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Buildings/WaterPurifier.fbx"
OBJ_FALLBACK_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Buildings/WaterPurifier_OBJ.obj"

ASSET_OBJECTS = []


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def make_material(name, color, roughness=0.82, metallic=0.0):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = next((node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if shader is None:
        shader = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return material


def add_cube(name, location, dimensions, material, bevel=0.0, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rotation is not None:
        obj.rotation_euler = rotation
    if bevel > 0.0:
        modifier = obj.modifiers.new(name="Soft worn edges", type="BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.data.materials.append(material)
    ASSET_OBJECTS.append(obj)
    return obj


def add_beam(name, start, end, width, material):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    obj = add_cube(name, (start + end) * 0.5, (width, width, direction.length), material)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def add_mesh(name, vertices, faces, material):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(clean_customdata=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    ASSET_OBJECTS.append(obj)
    return obj


def add_cylinder(name, location, radius, depth, material, vertices=12, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        end_fill_type="NGON",
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    if rotation is not None:
        obj.rotation_euler = rotation
    obj.data.materials.append(material)
    ASSET_OBJECTS.append(obj)
    return obj


def add_torus(name, location, major_radius, minor_radius, material, rotation=None):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=12,
        minor_segments=4,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    if rotation is not None:
        obj.rotation_euler = rotation
    obj.data.materials.append(material)
    ASSET_OBJECTS.append(obj)
    return obj


def merge_by_material():
    grouped_objects = {}
    for obj in ASSET_OBJECTS:
        material = obj.data.materials[0]
        grouped_objects.setdefault(material, []).append(obj)

    merged_objects = []
    for material, objects in grouped_objects.items():
        if len(objects) > 1:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = objects[0]
            bpy.ops.object.join()
            merged = bpy.context.view_layer.objects.active
            merged.name = "WaterPurifier_" + material.name.replace(" | ", "_").replace(" ", "_")
            merged_objects.append(merged)
        else:
            merged_objects.append(objects[0])
    ASSET_OBJECTS.clear()
    ASSET_OBJECTS.extend(merged_objects)


def add_preview_setup(scene):
    preview_ground = make_material("Preview | deep sea slate", (0.075, 0.12, 0.13))
    bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0.0, 0.0, -0.015))
    ground = bpy.context.object
    ground.name = "Preview ground (not exported)"
    ground.data.materials.append(preview_ground)

    camera_data = bpy.data.cameras.new("Asset preview camera")
    camera = bpy.data.objects.new("Asset preview camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (3.4, -4.5, 3.0)
    target = Vector((0.0, 0.0, 0.67))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.45
    scene.camera = camera

    light_data = bpy.data.lights.new("Large softbox", type="AREA")
    light = bpy.data.objects.new("Large softbox", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (1.4, -2.5, 4.0)
    light.data.energy = 540.0
    light.data.shape = "DISK"
    light.data.size = 3.5
    light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.world.color = (0.08, 0.10, 0.11)


def make_asset():
    clear_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    wood_dark = make_material("Wood | tarred frame", (0.20, 0.15, 0.11))
    wood = make_material("Wood | salt-worn cedar", (0.43, 0.31, 0.20))
    wood_light = make_material("Wood | sun-bleached boards", (0.61, 0.49, 0.32))
    metal = make_material("Metal | faded sea green", (0.20, 0.36, 0.34), metallic=0.30)
    metal_light = make_material("Metal | patched zinc", (0.49, 0.55, 0.50), metallic=0.36)
    metal_dark = make_material("Metal | tarred fittings", (0.12, 0.20, 0.19), metallic=0.28)
    rust = make_material("Metal | rust repair", (0.52, 0.25, 0.14), metallic=0.24)
    water = make_material("Tank | cloudy blue enamel", (0.23, 0.49, 0.53), roughness=0.42, metallic=0.16)
    glass = make_material("Gauge | dark blue glass", (0.08, 0.25, 0.29), roughness=0.28, metallic=0.1)
    signal = make_material("Indicator | warm amber", (0.96, 0.56, 0.18), roughness=0.3)

    # Compact raised platform fits a 2 x 2 m build area and sits on z=0.
    for x in (-0.78, 0.78):
        for y in (-0.78, 0.78):
            add_cube("Deck support post", (x, y, 0.055), (0.10, 0.10, 0.11), wood_dark, 0.008)
    add_cube("Raised service platform", (0.0, 0.0, 0.105), (1.82, 1.82, 0.09), wood, 0.012)
    for index, x in enumerate((-0.72, -0.48, -0.24, 0.0, 0.24, 0.48, 0.72)):
        add_cube("Deck plank %02d" % index, (x, 0.0, 0.154), (0.22, 1.78, 0.012), wood_light if index % 3 == 0 else wood)
    for y in (-0.78, 0.78):
        add_cube("Safety deck edge", (0.0, y, 0.18), (1.76, 0.045, 0.045), wood_dark, 0.006)

    # Main pump room occupies the left half; the front is local -Y.
    room_x = -0.34
    room_y = 0.13
    left = room_x - 0.50
    right = room_x + 0.50
    front = room_y - 0.54
    back = room_y + 0.54
    add_cube("Pump room foundation plate", (room_x, room_y, 0.19), (1.03, 1.10, 0.07), wood_dark, 0.008)
    add_cube("Pump room wall core", (room_x, room_y, 0.62), (0.98, 1.05, 0.78), wood, 0.012)
    add_cube("Front wall metal cladding", (room_x, front - 0.012, 0.63), (0.98, 0.025, 0.77), metal, 0.008)
    # Salt-worn vertical repair panels make the shed read as a reclaimed utility building.
    for index, x in enumerate((left + 0.08, left + 0.20, right - 0.13, right - 0.04)):
        add_cube("Front patched siding", (x, front - 0.031, 0.62), (0.09, 0.018, 0.73), wood_light if index % 2 == 0 else rust, 0.003)
    for x in (left, right):
        add_cube("Room corner post", (x, room_y, 0.62), (0.065, 1.10, 0.82), wood_dark, 0.006)
    for y in (front, back):
        add_cube("Room wall plate", (room_x, y, 1.00), (1.06, 0.07, 0.07), wood_dark, 0.006)

    # Door, service window and simple pump status lamps.
    add_cube("Door frame", (room_x - 0.17, front - 0.055, 0.58), (0.35, 0.07, 0.68), wood_dark, 0.008)
    add_cube("Service door", (room_x - 0.17, front - 0.095, 0.57), (0.29, 0.035, 0.62), wood_light, 0.006)
    add_cube("Door lower rust patch", (room_x - 0.17, front - 0.118, 0.36), (0.24, 0.012, 0.13), rust, 0.003)
    add_cube("Door handle", (room_x - 0.07, front - 0.126, 0.59), (0.025, 0.02, 0.075), metal_light, 0.004)
    add_cube("Service window frame", (room_x + 0.26, front - 0.045, 0.71), (0.22, 0.045, 0.20), wood_dark, 0.006)
    add_cube("Service window", (room_x + 0.26, front - 0.072, 0.71), (0.17, 0.018, 0.14), glass, 0.004)
    for index, x in enumerate((room_x + 0.20, room_x + 0.31, room_x + 0.42)):
        add_cylinder("Pump status lamp %02d" % index, (x, front - 0.055, 0.91), 0.025, 0.035, signal if index == 0 else metal_light, vertices=8)

    # Shallow, single-pitch patched roof with a collection gutter facing front.
    roof_angle = math.radians(-4.0)
    add_cube("Pump room roof", (room_x, room_y, 1.09), (1.18, 1.27, 0.10), metal_light, 0.012, (roof_angle, 0.0, 0.0))
    add_cube("Roof rust repair sheet", (left + 0.18, front + 0.12, 1.145), (0.32, 0.34, 0.025), rust, 0.004, (roof_angle, 0.0, 0.0))
    for x in (left - 0.02, right + 0.02):
        add_beam("Roof support", (x, front, 0.99), (x, back, 1.08), 0.045, wood_dark)
    add_cube("Rain collection gutter", (room_x, front - 0.13, 1.04), (1.20, 0.07, 0.055), metal, 0.008)

    # Main clean-water cistern: broad bands, lid, vent and a readable water mark.
    tank_x = 0.56
    tank_y = 0.20
    tank_radius = 0.30
    tank_bottom = 0.20
    tank_top = 0.92
    add_cylinder("Clean water cistern", (tank_x, tank_y, (tank_bottom + tank_top) * 0.5), tank_radius, tank_top - tank_bottom, water, vertices=12)
    add_cylinder("Cistern lid", (tank_x, tank_y, tank_top + 0.018), tank_radius + 0.018, 0.045, metal_light, vertices=12)
    for z in (0.30, 0.49, 0.72, 0.87):
        add_torus("Cistern retaining hoop", (tank_x, tank_y, z), tank_radius + 0.008, 0.018, metal)
    add_cylinder("Cistern vent", (tank_x, tank_y, 1.01), 0.045, 0.14, metal, vertices=8)
    add_cylinder("Vent cap", (tank_x, tank_y, 1.09), 0.07, 0.035, rust, vertices=8)

    # Flat enamel sign facing -Y with a raised geometric drop icon.
    add_cube("Water service badge", (tank_x, tank_y - tank_radius - 0.075, 0.62), (0.30, 0.028, 0.31), metal_light, 0.014)
    drop_y = tank_y - tank_radius - 0.092
    add_mesh(
        "Enamel water drop symbol",
        [
            (tank_x, drop_y, 0.78),
            (tank_x - 0.075, drop_y, 0.66),
            (tank_x - 0.06, drop_y, 0.58),
            (tank_x, drop_y, 0.55),
            (tank_x + 0.06, drop_y, 0.58),
            (tank_x + 0.075, drop_y, 0.66),
        ],
        [(0, 1, 2, 3, 4, 5)],
        glass,
    )

    # Two upright filter vessels and the inlet/outlet piping.
    filter_positions = ((0.20, -0.48), (0.43, -0.48))
    for index, (x, y) in enumerate(filter_positions):
        add_cylinder("Filter vessel %02d" % index, (x, y, 0.43), 0.085, 0.48, metal_light if index == 0 else metal, vertices=10)
        add_cylinder("Filter vessel top %02d" % index, (x, y, 0.69), 0.095, 0.045, rust if index == 1 else metal_dark, vertices=10)
        add_torus("Filter vessel collar %02d" % index, (x, y, 0.28), 0.086, 0.012, wood_dark)
        add_cube("Filter label plate %02d" % index, (x, y - 0.09, 0.46), (0.07, 0.018, 0.12), glass, 0.003)

    # Downpipe from the roof feeds a small raw-water collector; a short manifold
    # connects the filters to the large cistern.
    add_beam("Gutter downpipe", (left + 0.02, front - 0.13, 1.02), (left + 0.02, front - 0.13, 0.46), 0.045, metal)
    add_cube("Raw-water collection box", (left + 0.12, front - 0.10, 0.31), (0.27, 0.28, 0.22), metal, 0.018)
    add_cube("Collection box lid", (left + 0.12, front - 0.10, 0.43), (0.30, 0.30, 0.035), rust, 0.006)
    add_beam("Low filter manifold", (0.19, -0.48, 0.28), (0.45, -0.48, 0.28), 0.035, metal)
    add_beam("Tank inlet pipe", (0.45, -0.48, 0.68), (0.56, -0.12, 0.68), 0.038, metal)
    add_beam("Room inlet pipe", (0.12, -0.36, 0.47), (-0.02, -0.36, 0.47), 0.035, rust)
    add_cube("Pipe valve handle", (0.04, -0.36, 0.52), (0.12, 0.025, 0.022), rust, 0.004)

    # A small pressure gauge faces the player on the pump-room front.
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=0.085,
        depth=0.035,
        location=(left + 0.12, front - 0.055, 0.82),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    gauge = bpy.context.object
    gauge.name = "Pressure gauge bezel"
    gauge.data.materials.append(rust)
    ASSET_OBJECTS.append(gauge)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=0.061,
        depth=0.012,
        location=(left + 0.12, front - 0.078, 0.82),
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    gauge_face = bpy.context.object
    gauge_face.name = "Pressure gauge face"
    gauge_face.data.materials.append(glass)
    ASSET_OBJECTS.append(gauge_face)
    add_cube("Gauge needle", (left + 0.12, front - 0.089, 0.83), (0.012, 0.012, 0.055), signal, 0.002, (0.0, math.radians(-28.0), 0.0))

    # A rain barrel/cistern sits at the front right, visually separate from the
    # clean-water tank and within the overall 2 m square footprint.
    add_cylinder("Rain reserve barrel", (0.70, -0.59, 0.36), 0.16, 0.42, metal, vertices=10)
    add_cylinder("Rain reserve lid", (0.70, -0.59, 0.59), 0.17, 0.035, metal_light, vertices=10)
    for z in (0.23, 0.49):
        add_torus("Rain barrel hoop", (0.70, -0.59, z), 0.164, 0.014, rust)
    add_cylinder("Reserve spigot", (0.70, -0.76, 0.32), 0.035, 0.11, metal_light, vertices=8, rotation=(math.radians(90.0), 0.0, 0.0))

    merge_by_material()
    root = bpy.data.objects.new("WaterPurifier_Root", None)
    bpy.context.collection.objects.link(root)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.18
    for obj in ASSET_OBJECTS:
        obj.parent = root
        obj.matrix_parent_inverse = root.matrix_world.inverted()

    add_preview_setup(scene)
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for obj in ASSET_OBJECTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root


def operator_is_available(operator):
    try:
        operator.get_rna_type()
        return True
    except (AttributeError, RuntimeError):
        return False


def select_export_objects():
    bpy.ops.object.select_all(action="DESELECT")
    root = bpy.data.objects["WaterPurifier_Root"]
    root.select_set(True)
    for obj in ASSET_OBJECTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root


def export_asset():
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    FBX_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    select_export_objects()

    if operator_is_available(bpy.ops.export_scene.fbx):
        bpy.ops.export_scene.fbx(
            filepath=str(FBX_PATH),
            use_selection=True,
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
        print("Created Blender source:", BLEND_PATH)
        print("Exported FBX:", FBX_PATH)
    elif operator_is_available(bpy.ops.wm.obj_export):
        bpy.ops.wm.obj_export(
            filepath=str(OBJ_FALLBACK_PATH),
            export_selected_objects=True,
            forward_axis="NEGATIVE_Z",
            up_axis="Y",
            global_scale=1.0,
            apply_modifiers=True,
            export_materials=True,
            export_object_groups=True,
            export_material_groups=True,
            path_mode="AUTO",
        )
        print("Created Blender source:", BLEND_PATH)
        print("Exported OBJ fallback (FBX exporter unavailable):", OBJ_FALLBACK_PATH)
    else:
        raise RuntimeError("No supported model exporter is available; use Blender with FBX or built-in OBJ export support.")


make_asset()
export_asset()
