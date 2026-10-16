"""Generate the low-poly Storage Depot building for Last Landfall.

Run from the Unity project root, or pass the file directly to Blender:
    blender --background --python Tools/Blender/create_storage_depot.py

The source .blend includes a small preview setup. The exported model contains
only the building, with meshes merged by material for a compact renderer count.
FBX is preferred; Blender's built-in OBJ exporter is used as a fallback.
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
ASSET_NAME = "StorageDepot"
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

    camera_data = bpy.data.cameras.new("Storage depot preview camera")
    camera = bpy.data.objects.new("Storage depot preview camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (2.7, -3.6, 2.5)
    target = Vector((0.0, 0.0, 0.77))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.15
    scene.camera = camera

    light_data = bpy.data.lights.new("Storage depot softbox", type="AREA")
    light = bpy.data.objects.new("Storage depot softbox", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (1.4, -2.5, 3.6)
    light.data.energy = 420.0
    light.data.shape = "DISK"
    light.data.size = 3.2
    light.rotation_euler = (Vector((0.0, 0.0, 0.65)) - light.location).to_track_quat("-Z", "Y").to_euler()

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

    timber_dark = make_material("Timber | tarred", (0.19, 0.13, 0.09))
    timber_mid = make_material("Timber | salt-worn", (0.38, 0.28, 0.18))
    timber_light = make_material("Timber | sun-bleached", (0.58, 0.46, 0.31))
    metal_blue = make_material("Metal | faded sea green", (0.18, 0.34, 0.34), metallic=0.28)
    metal_rust = make_material("Metal | rust patch", (0.48, 0.23, 0.13), metallic=0.18)
    canvas = make_material("Canvas | salvage tan", (0.64, 0.48, 0.28))
    crate_green = make_material("Cargo | painted salvage green", (0.29, 0.39, 0.28))
    shadow = make_material("Hardware | dark iron", (0.105, 0.12, 0.115), metallic=0.42)

    # Compact raised deck; the complete footprint stays within roughly 2 x 2 m.
    for x in (-0.69, 0.69):
        for y in (-0.62, 0.62):
            add_cube("Pier block", (x, y, 0.085), (0.13, 0.13, 0.17), timber_dark, 0.012)
    add_cube("Raised depot floor", (0.0, 0.0, 0.20), (1.72, 1.58, 0.09), timber_mid, 0.012)
    for index, x in enumerate((-0.68, -0.46, -0.24, -0.02, 0.20, 0.42, 0.64)):
        board_material = timber_light if index % 3 == 0 else timber_mid
        add_cube("Deck plank %02d" % index, (x, 0.0, 0.252), (0.20, 1.48, 0.018), board_material)

    # A broad-sided shed and oversized paired doors establish a storage silhouette.
    add_cube("Warehouse wall core", (0.0, 0.015, 0.735), (1.48, 1.22, 0.96), timber_mid)
    for index, x in enumerate((-0.66, -0.51, -0.36, -0.21, -0.06, 0.09, 0.24, 0.39, 0.54, 0.69)):
        board_material = (timber_light, timber_mid, timber_dark, timber_mid)[index % 4]
        add_cube("Front wall plank %02d" % index, (x, -0.607, 0.75), (0.135, 0.025, 0.90), board_material, 0.004)
    for index, y in enumerate((-0.47, -0.29, -0.11, 0.07, 0.25, 0.43, 0.58)):
        side_material = timber_light if index in (1, 4) else timber_mid
        add_cube("Visible right wall plank %02d" % index, (0.755, y, 0.75), (0.025, 0.16, 0.90), side_material, 0.004)
    for z in (0.31, 1.16):
        add_cube("Front tie beam", (0.0, -0.632, z), (1.52, 0.055, 0.07), timber_dark, 0.006)
        add_cube("Right tie beam", (0.77, 0.0, z), (0.055, 1.26, 0.07), timber_dark, 0.006)

    # Double cargo doors with iron straps; the front of the building faces -Y.
    add_cube("Door dark frame", (0.0, -0.650, 0.685), (0.89, 0.055, 0.72), timber_dark, 0.008)
    add_cube("Left cargo door", (-0.205, -0.684, 0.685), (0.39, 0.035, 0.66), metal_blue, 0.008)
    add_cube("Right cargo door", (0.205, -0.684, 0.685), (0.39, 0.035, 0.66), metal_rust, 0.008)
    for x in (-0.39, -0.02, 0.02, 0.39):
        add_cube("Door reinforcing strap", (x, -0.709, 0.685), (0.025, 0.018, 0.68), shadow, 0.003)
    for z in (0.43, 0.93):
        add_cube("Door cross strap", (0.0, -0.712, z), (0.82, 0.018, 0.034), shadow, 0.003)
    add_cylinder("Door latch hub", (0.0, -0.725, 0.69), 0.035, 0.025, metal_rust, vertices=8, rotation=(math.radians(90), 0.0, 0.0))

    # Low pitched patched metal roof with readable seams and irregular repairs.
    roof_rotation = (math.radians(4.0), 0.0, 0.0)
    add_cube("Corrugated roof base", (0.0, 0.0, 1.275), (1.82, 1.62, 0.075), metal_blue, 0.008, roof_rotation)
    for index, x in enumerate((-0.72, -0.48, -0.24, 0.0, 0.24, 0.48, 0.72)):
        add_cube("Roof raised seam %02d" % index, (x, 0.0, 1.318), (0.018, 1.61, 0.024), shadow if index in (0, 6) else metal_blue, 0.003, roof_rotation)
    add_cube("Rust roof repair panel", (0.49, -0.29, 1.326), (0.34, 0.48, 0.022), metal_rust, 0.004, roof_rotation)
    add_cube("Canvas roof patch", (-0.52, 0.35, 1.331), (0.26, 0.32, 0.018), canvas, 0.004, roof_rotation)
    add_cube("Front roof fascia", (0.0, -0.813, 1.245), (1.80, 0.06, 0.10), timber_dark, 0.005)

    # Large inventory marker, formed as simple geometry rather than text.
    add_cube("Depot sign backing", (0.0, -0.674, 1.075), (0.48, 0.035, 0.13), metal_blue, 0.004)
    add_cube("Depot sign cargo mark lower", (0.0, -0.698, 1.055), (0.12, 0.015, 0.035), canvas, 0.002)
    add_cube("Depot sign cargo mark upper left", (-0.035, -0.698, 1.092), (0.05, 0.015, 0.035), canvas, 0.002)
    add_cube("Depot sign cargo mark upper right", (0.035, -0.698, 1.092), (0.05, 0.015, 0.035), canvas, 0.002)

    # A pallet and a small stack of weathered crates signal stored supplies.
    add_cube("Crate pallet", (0.72, -0.39, 0.285), (0.38, 0.39, 0.055), timber_dark, 0.006)
    for x in (0.59, 0.72, 0.85):
        add_cube("Pallet runner", (x, -0.39, 0.25), (0.045, 0.40, 0.04), timber_light)
    add_cube("Lower supply crate", (0.72, -0.39, 0.48), (0.35, 0.34, 0.34), crate_green, 0.008)
    add_cube("Lower crate face slat", (0.72, -0.568, 0.48), (0.29, 0.018, 0.045), timber_light, 0.002)
    add_cube("Lower crate cross mark", (0.72, -0.581, 0.48), (0.04, 0.014, 0.27), timber_light, 0.002)
    add_cube("Upper supply crate", (0.72, -0.39, 0.81), (0.29, 0.30, 0.28), timber_light, 0.008)
    add_cube("Upper crate strap", (0.72, -0.548, 0.81), (0.04, 0.016, 0.26), metal_rust, 0.002)

    # Salvage drum and rope cleat on the left side balance the composition.
    add_cylinder("Waterproof salvage drum", (-0.70, -0.71, 0.405), 0.105, 0.30, metal_rust, vertices=10)
    for z in (0.30, 0.51):
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.103, minor_radius=0.009, major_segments=10, minor_segments=4,
            location=(-0.70, -0.71, z),
        )
        hoop = bpy.context.object
        hoop.name = "Drum reinforcing hoop"
        hoop.data.materials.append(shadow)
        ASSET_OBJECTS.append(hoop)
    add_cube("Rope cleat block", (-0.60, -0.75, 1.12), (0.12, 0.08, 0.055), timber_light, 0.004)
    add_rod("Rope cleat post left", (-0.64, -0.75, 1.13), (-0.64, -0.75, 1.18), 0.012, shadow)
    add_rod("Rope cleat post right", (-0.56, -0.75, 1.13), (-0.56, -0.75, 1.18), 0.012, shadow)

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
