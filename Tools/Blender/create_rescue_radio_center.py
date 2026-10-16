"""Generate the low-poly Rescue Radio Center for Last Landfall.

Run from the Unity project root, or pass the file directly to Blender:
    blender --background --python Tools/Blender/create_rescue_radio_center.py

The source .blend includes a preview camera and lights. Only the building model
is exported. Meshes are joined by material so Unity receives a small renderer
count. FBX is preferred, with Blender's built-in OBJ exporter as a fallback.
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
ASSET_NAME = "RescueRadioCenter"
BLEND_PATH = PROJECT_ROOT / "Assets/LastLandfall/Art/Source" / (ASSET_NAME + ".blend")
FBX_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models" / (ASSET_NAME + ".fbx")
OBJ_FALLBACK_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models" / (ASSET_NAME + "_OBJ.obj")

ASSET_OBJECTS = []


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def make_material(name, color, roughness=0.84, metallic=0.0):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
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
        modifier = obj.modifiers.new(name="Worn edges", type="BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.data.materials.append(material)
    ASSET_OBJECTS.append(obj)
    return obj


def add_cylinder(name, location, radius, depth, material, vertices=10, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location,
        rotation=rotation or (0.0, 0.0, 0.0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    ASSET_OBJECTS.append(obj)
    return obj


def add_rod(name, start, end, radius, material, vertices=8):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=direction.length,
        location=(start + end) * 0.5,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
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
            merged.name = ASSET_NAME + "_" + material.name.replace(" | ", "_").replace(" ", "_")
            merged_objects.append(merged)
        else:
            merged_objects.append(objects[0])
    ASSET_OBJECTS.clear()
    ASSET_OBJECTS.extend(merged_objects)


def add_preview_setup(scene, root):
    ground_material = make_material("Preview ground | not exported", (0.075, 0.13, 0.14))
    bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0.0, 0.0, -0.006))
    ground = bpy.context.object
    ground.name = "Preview ground (not exported)"
    ground.data.materials.append(ground_material)

    camera_data = bpy.data.cameras.new("Rescue radio center preview camera")
    camera = bpy.data.objects.new("Rescue radio center preview camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (3.1, -4.1, 2.8)
    target = Vector((0.0, 0.0, 1.0))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.8
    scene.camera = camera

    light_data = bpy.data.lights.new("Rescue radio center softbox", type="AREA")
    light = bpy.data.objects.new("Rescue radio center softbox", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (1.2, -2.7, 4.0)
    light.data.energy = 500.0
    light.data.shape = "DISK"
    light.data.size = 3.4
    light.rotation_euler = (Vector((0.0, 0.0, 0.9)) - light.location).to_track_quat("-Z", "Y").to_euler()

    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.world.color = (0.055, 0.075, 0.08)

    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for obj in ASSET_OBJECTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root


def make_asset():
    clear_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    timber_dark = make_material("Timber | tarred", (0.18, 0.12, 0.085))
    timber_mid = make_material("Timber | salt-worn", (0.39, 0.29, 0.19))
    timber_light = make_material("Timber | sun-bleached", (0.61, 0.48, 0.32))
    metal_blue = make_material("Metal | faded sea green", (0.18, 0.34, 0.35), metallic=0.3)
    metal_rust = make_material("Metal | rescue orange", (0.72, 0.25, 0.10), metallic=0.15)
    iron = make_material("Hardware | dark iron", (0.10, 0.13, 0.13), metallic=0.45)
    glass = make_material("Window | storm blue", (0.13, 0.34, 0.40), roughness=0.4, metallic=0.08)
    ivory = make_material("Rescue mark | aged ivory", (0.82, 0.77, 0.61))
    amber = make_material("Beacon | amber lens", (0.98, 0.57, 0.12), roughness=0.34)

    # Raised 1.7 m deck and compact operations hut, front facing -Y.
    for x in (-0.68, 0.68):
        for y in (-0.58, 0.58):
            add_cube("Raised timber pier", (x, y, 0.085), (0.12, 0.12, 0.17), timber_dark, 0.01)
    add_cube("Radio center deck", (0.0, 0.0, 0.195), (1.72, 1.52, 0.09), timber_mid, 0.012)
    for index, x in enumerate((-0.65, -0.43, -0.21, 0.01, 0.23, 0.45, 0.67)):
        plank = timber_light if index in (0, 3, 6) else timber_mid
        add_cube("Radio center deck plank %02d" % index, (x, 0.0, 0.245), (0.20, 1.42, 0.018), plank)

    # The room is low and broad; a door, storm shutters and rescue emblem read clearly at game scale.
    add_cube("Operations room wall core", (0.0, 0.0, 0.675), (1.40, 1.20, 0.86), timber_mid)
    for index, x in enumerate((-0.62, -0.47, -0.32, -0.17, -0.02, 0.13, 0.28, 0.43, 0.58)):
        board = (timber_light, timber_mid, timber_dark)[index % 3]
        add_cube("Front cladding plank %02d" % index, (x, -0.609, 0.69), (0.135, 0.025, 0.80), board, 0.004)
    for index, y in enumerate((-0.45, -0.27, -0.09, 0.09, 0.27, 0.45)):
        board = timber_light if index in (1, 4) else timber_mid
        add_cube("Right cladding plank %02d" % index, (0.715, y, 0.69), (0.025, 0.16, 0.80), board, 0.004)
    for z in (0.31, 1.06):
        add_cube("Front wall tie", (0.0, -0.632, z), (1.45, 0.05, 0.06), timber_dark, 0.004)
        add_cube("Right wall tie", (0.737, 0.0, z), (0.05, 1.22, 0.06), timber_dark, 0.004)

    # Front entrance on the left, protected radio window on the right.
    add_cube("Entrance frame", (-0.39, -0.649, 0.625), (0.43, 0.05, 0.68), timber_dark, 0.006)
    add_cube("Entrance door", (-0.39, -0.680, 0.625), (0.36, 0.035, 0.62), metal_blue, 0.006)
    add_cube("Door repair plank", (-0.39, -0.704, 0.625), (0.075, 0.018, 0.59), timber_light, 0.003)
    add_cube("Door latch", (-0.25, -0.713, 0.63), (0.045, 0.018, 0.07), metal_rust, 0.004)
    add_cube("Radio window glass", (0.29, -0.650, 0.77), (0.42, 0.045, 0.30), glass, 0.004)
    for x in (0.065, 0.515):
        add_cube("Radio window upright", (x, -0.681, 0.77), (0.035, 0.028, 0.37), timber_dark, 0.003)
    for z in (0.585, 0.955):
        add_cube("Radio window rail", (0.29, -0.681, z), (0.48, 0.028, 0.035), timber_dark, 0.003)
    add_cube("Radio window crossbar", (0.29, -0.699, 0.77), (0.025, 0.018, 0.28), timber_light, 0.002)
    add_cube("Radio window sill", (0.29, -0.708, 0.56), (0.53, 0.10, 0.055), timber_light, 0.004)

    # Large rescue cross on a rust-red field: a readable landmark for visitors.
    add_cube("Rescue emblem backing", (0.48, -0.651, 1.005), (0.22, 0.035, 0.18), metal_rust, 0.004)
    add_cube("Rescue emblem vertical", (0.48, -0.676, 1.005), (0.045, 0.018, 0.135), ivory, 0.002)
    add_cube("Rescue emblem horizontal", (0.48, -0.677, 1.005), (0.145, 0.018, 0.045), ivory, 0.002)

    # Patched roof with metal seams; roof extent remains near the 2 x 2 m cell.
    roof_rotation = (math.radians(3.0), 0.0, 0.0)
    add_cube("Radio center roof", (0.0, 0.0, 1.17), (1.76, 1.58, 0.075), metal_blue, 0.008, roof_rotation)
    for index, x in enumerate((-0.68, -0.43, -0.18, 0.07, 0.32, 0.57, 0.78)):
        seam_material = metal_rust if index == 6 else iron
        add_cube("Roof seam %02d" % index, (x, 0.0, 1.214), (0.018, 1.57, 0.018), seam_material, 0.002, roof_rotation)
    add_cube("Roof salvage patch", (-0.48, -0.22, 1.221), (0.36, 0.40, 0.022), metal_rust, 0.004, roof_rotation)
    add_cube("Front roof fascia", (0.0, -0.786, 1.14), (1.77, 0.055, 0.09), timber_dark, 0.004)

    # Roof beacon: small warm lens above a sturdy iron mount.
    add_cube("Beacon mount", (-0.48, 0.25, 1.245), (0.20, 0.18, 0.08), iron, 0.006)
    add_cylinder("Beacon base", (-0.48, 0.25, 1.315), 0.09, 0.07, metal_rust, vertices=8)
    add_cylinder("Beacon lens", (-0.48, 0.25, 1.39), 0.065, 0.09, amber, vertices=8)
    add_cube("Beacon cap", (-0.48, 0.25, 1.44), (0.11, 0.11, 0.025), metal_rust, 0.004)

    # Tall shortwave mast and three-element directional aerial give the building its silhouette.
    mast_x = 0.39
    mast_y = 0.46
    add_cube("Antenna roof plinth", (mast_x, mast_y, 1.245), (0.28, 0.28, 0.07), timber_dark, 0.008)
    add_cylinder("Antenna mast", (mast_x, mast_y, 1.78), 0.027, 1.02, iron, vertices=8)
    for z in (1.58, 2.12):
        add_cylinder("Antenna hazard band", (mast_x, mast_y, z), 0.039, 0.045, metal_rust, vertices=8)
    add_cylinder("Mast tip cap", (mast_x, mast_y, 2.315), 0.034, 0.05, timber_light, vertices=8)
    # Triangular braces are anchored at the plinth and meet the mast above the roof.
    for side in (-1.0, 1.0):
        add_rod(
            "Antenna support brace",
            (mast_x + side * 0.24, mast_y - 0.08, 1.29),
            (mast_x, mast_y - 0.08, 1.90),
            0.018,
            metal_blue,
        )
    add_rod("Aerial boom", (mast_x, 0.045, 2.00), (mast_x, 0.875, 2.00), 0.018, metal_rust)
    for index, (y, half_span) in enumerate(((0.12, 0.30), (0.46, 0.49), (0.80, 0.32))):
        add_rod(
            "Shortwave aerial element %02d" % index,
            (mast_x - half_span, y, 2.00),
            (mast_x + half_span, y, 2.00),
            0.014,
            ivory if index == 1 else metal_blue,
        )
    # Ground straps/cables are deliberately short and thick enough to read at game scale.
    add_rod("Aerial cable to roof", (mast_x - 0.08, mast_y - 0.16, 1.36), (0.13, 0.20, 1.23), 0.009, metal_rust)
    add_rod("Aerial cable to roof 2", (mast_x + 0.08, mast_y - 0.16, 1.36), (0.68, 0.20, 1.23), 0.009, metal_rust)

    # Shore-power radio battery box and a small cable reel beside the entrance.
    add_cube("Radio battery cabinet", (-0.69, 0.18, 0.40), (0.28, 0.34, 0.30), metal_blue, 0.008)
    add_cube("Battery warning panel", (-0.69, -0.001, 0.42), (0.17, 0.02, 0.16), metal_rust, 0.003)
    add_cube("Battery symbol vertical", (-0.69, -0.017, 0.42), (0.035, 0.012, 0.11), ivory, 0.002)
    add_cube("Battery symbol horizontal", (-0.69, -0.018, 0.42), (0.10, 0.012, 0.035), ivory, 0.002)
    add_cylinder("Cable reel core", (0.68, 0.30, 0.38), 0.085, 0.27, timber_dark, vertices=10, rotation=(0.0, math.radians(90.0), 0.0))
    for x in (0.52, 0.84):
        add_cylinder("Cable reel flange", (x, 0.30, 0.38), 0.14, 0.035, timber_light, vertices=10, rotation=(0.0, math.radians(90.0), 0.0))

    merge_by_material()
    root = bpy.data.objects.new(ASSET_NAME + "_Root", None)
    bpy.context.collection.objects.link(root)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.16
    for obj in ASSET_OBJECTS:
        obj.parent = root
        obj.matrix_parent_inverse = root.matrix_world.inverted()

    add_preview_setup(scene, root)


def operator_is_available(operator):
    try:
        operator.get_rna_type()
        return True
    except (AttributeError, RuntimeError):
        return False


def select_export_objects():
    bpy.ops.object.select_all(action="DESELECT")
    root = bpy.data.objects[ASSET_NAME + "_Root"]
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
            filepath=str(FBX_PATH), use_selection=True, object_types={"EMPTY", "MESH"},
            axis_forward="-Z", axis_up="Y", apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_ALL", use_mesh_modifiers=True,
            add_leaf_bones=False, bake_anim=False, path_mode="AUTO",
        )
        model_path = FBX_PATH
        model_format = "FBX"
    elif operator_is_available(bpy.ops.wm.obj_export):
        bpy.ops.wm.obj_export(
            filepath=str(OBJ_FALLBACK_PATH), export_selected_objects=True,
            forward_axis="NEGATIVE_Z", up_axis="Y", global_scale=1.0,
            apply_modifiers=True, export_materials=True,
            export_object_groups=True, export_material_groups=True, path_mode="AUTO",
        )
        model_path = OBJ_FALLBACK_PATH
        model_format = "OBJ fallback (FBX exporter unavailable)"
    else:
        raise RuntimeError("No supported exporter: enable FBX or use Blender's built-in OBJ exporter.")

    print("Created Blender source:", BLEND_PATH)
    print("Exported", model_format + ":", model_path)


make_asset()
export_asset()
