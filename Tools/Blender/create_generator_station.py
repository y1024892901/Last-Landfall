"""Create a low-poly generator station for Last Landfall.

Run with Blender's bundled Python, from any working directory:
    blender --background --python Tools/Blender/create_generator_station.py

The source .blend keeps a small studio preview setup. The Unity model export
contains only the station hierarchy and uses Blender's built-in OBJ exporter
if the FBX exporter is unavailable.
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
ASSET_NAME = "GeneratorStation"
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


def make_material(name, color, roughness=0.84, metallic=0.0, emission=0.0):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = next((node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if shader is None:
        shader = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    emission_input = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
    if emission_input is not None and emission > 0.0:
        emission_input.default_value = (*color, 1.0)
        strength = shader.inputs.get("Emission Strength")
        if strength is not None:
            strength.default_value = emission
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
        modifier = obj.modifiers.new(name="Worn chamfer", type="BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.data.materials.append(material)
    ASSET_OBJECTS.append(obj)
    return obj


def add_cylinder(name, location, radius, depth, material, vertices=10, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    if rotation is not None:
        obj.rotation_euler = rotation
    obj.data.materials.append(material)
    ASSET_OBJECTS.append(obj)
    return obj


def merge_by_material():
    grouped = {}
    for obj in ASSET_OBJECTS:
        material = obj.data.materials[0]
        grouped.setdefault(material, []).append(obj)
    merged_objects = []
    for material, objects in grouped.items():
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


def add_preview(scene, root):
    bpy.ops.mesh.primitive_plane_add(size=3.4, location=(0.0, 0.0, 0.0))
    ground = bpy.context.object
    ground.name = "Preview ground (not exported)"
    ground.data.materials.append(make_material("Preview | deep slate", (0.075, 0.12, 0.14)))

    camera_data = bpy.data.cameras.new("Asset preview camera")
    camera = bpy.data.objects.new("Asset preview camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (2.9, -4.0, 2.65)
    direction = Vector((0.0, -0.02, 0.85)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.75
    scene.camera = camera

    light_data = bpy.data.lights.new("Large softbox", type="AREA")
    light = bpy.data.objects.new("Large softbox", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (1.0, -2.5, 3.6)
    light.data.energy = 330.0
    light.data.shape = "DISK"
    light.data.size = 2.8
    light.rotation_euler = (Vector((0.0, 0.0, 0.75)) - light.location).to_track_quat("-Z", "Y").to_euler()

    fill_data = bpy.data.lights.new("Cool fill", type="AREA")
    fill = bpy.data.objects.new("Cool fill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = (-2.2, 1.0, 2.6)
    fill.data.energy = 105.0
    fill.data.color = (0.48, 0.68, 0.78)
    fill.data.size = 2.6
    fill.rotation_euler = (Vector((0.0, 0.0, 0.75)) - fill.location).to_track_quat("-Z", "Y").to_euler()

    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.world.color = (0.055, 0.075, 0.085)

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

    wood_dark = make_material("Wood | tarred salvage", (0.15, 0.115, 0.08))
    wood_mid = make_material("Wood | salt worn", (0.34, 0.25, 0.16))
    wood_light = make_material("Wood | sun bleached", (0.52, 0.41, 0.27))
    metal_dark = make_material("Metal | oxidized frame", (0.095, 0.16, 0.17), metallic=0.45)
    metal_teal = make_material("Metal | faded sea green", (0.20, 0.34, 0.33), metallic=0.34)
    metal_rust = make_material("Metal | rust repair", (0.48, 0.22, 0.12), metallic=0.26)
    cream = make_material("Paint | faded signal cream", (0.67, 0.57, 0.37), metallic=0.08)
    lamp = make_material("Lamp | warm amber", (1.0, 0.42, 0.10), roughness=0.32, emission=1.5)
    glass = make_material("Gauge | cloudy blue glass", (0.17, 0.42, 0.46), roughness=0.35, metallic=0.16)
    shadow = make_material("Vent | deep shadow", (0.035, 0.055, 0.055), metallic=0.18)

    # Narrow 1 x 2 tile base; the exhaust stack rises above the compact shed.
    for x in (-0.34, 0.34):
        for y in (-0.73, 0.0, 0.73):
            add_cube("Timber pile", (x, y, 0.065), (0.10, 0.13, 0.13), wood_dark, 0.009)
    add_cube("Raised service deck", (0.0, 0.0, 0.16), (0.86, 1.84, 0.10), wood_mid, 0.014)
    for index, x in enumerate((-0.31, -0.10, 0.11, 0.32)):
        add_cube("Deck plank %02d" % index, (x, 0.0, 0.215), (0.19, 1.80, 0.018),
                 wood_light if index in (0, 3) else wood_mid, 0.003)
    for y in (-0.54, 0.0, 0.54):
        add_cube("Deck cross brace", (0.0, y, 0.12), (0.89, 0.09, 0.07), wood_dark, 0.008)

    # Salt-worn generator enclosure with distinct front radiator and side louvers.
    add_cube("Engine housing core", (0.0, 0.12, 0.625), (0.66, 1.18, 0.82), metal_dark, 0.04)
    add_cube("Front housing panel", (0.0, -0.492, 0.66), (0.60, 0.035, 0.72), metal_teal, 0.018)
    add_cube("Rear patch panel", (0.0, 0.72, 0.64), (0.52, 0.025, 0.50), metal_rust, 0.008)
    add_cube("Enclosure roof", (0.0, 0.12, 1.075), (0.77, 1.31, 0.10), wood_dark, 0.025)
    add_cube("Roof repair sheet", (0.18, 0.20, 1.132), (0.35, 0.59, 0.025), metal_rust, 0.006,
             (0.0, 0.0, math.radians(-4.0)))
    add_cube("Roof seam", (-0.18, 0.12, 1.134), (0.022, 1.20, 0.024), metal_teal, 0.003)

    # Front radiator: dark aperture, horizontal metal slats and a worn safety frame.
    add_cube("Radiator cavity", (-0.13, -0.516, 0.62), (0.31, 0.022, 0.43), shadow, 0.005)
    for index, z in enumerate((0.45, 0.52, 0.59, 0.66, 0.73, 0.80)):
        add_cube("Radiator louver %02d" % index, (-0.13, -0.535, z), (0.29, 0.022, 0.027),
                 metal_rust if index == 0 else metal_dark, 0.003)
    for x in (-0.31, 0.05):
        add_cube("Radiator frame upright", (x, -0.537, 0.62), (0.025, 0.025, 0.48), cream, 0.003)
    add_cube("Front service door", (0.20, -0.517, 0.67), (0.20, 0.035, 0.44), wood_mid, 0.012)
    add_cube("Service door patch", (0.20, -0.541, 0.69), (0.11, 0.018, 0.22), metal_rust, 0.004)
    add_cylinder("Door latch", (0.255, -0.56, 0.67), 0.025, 0.018, cream, vertices=8,
                 rotation=(math.radians(90.0), 0.0, 0.0))

    # Long-side cooling louvers are visible in an isometric view.
    for side in (-1.0, 1.0):
        add_cube("Side vent dark panel", (side * 0.337, 0.13, 0.68), (0.022, 0.65, 0.39), shadow, 0.004)
        for index, y in enumerate((-0.13, -0.03, 0.07, 0.17, 0.27, 0.37, 0.47)):
            add_cube("Cooling fin %02d" % index, (side * 0.355, y, 0.68), (0.028, 0.035, 0.34),
                     metal_teal if index % 3 else metal_rust, 0.004)
        add_cube("Side belt", (side * 0.365, 0.16, 0.35), (0.025, 0.84, 0.06), wood_dark, 0.006)

    # Exhaust stack, rain hood, insulated muffler and a small side fuel tank.
    add_cube("Exhaust lower mount", (0.20, 0.53, 1.18), (0.22, 0.22, 0.15), metal_dark, 0.018)
    add_cylinder("Exhaust stack", (0.20, 0.53, 1.53), 0.07, 0.62, metal_rust, vertices=8)
    add_cylinder("Stack collar", (0.20, 0.53, 1.30), 0.095, 0.075, metal_dark, vertices=8)
    add_cylinder("Stack cap", (0.20, 0.53, 1.855), 0.115, 0.055, metal_teal, vertices=8)
    add_cube("Stack rain hood", (0.20, 0.53, 1.90), (0.25, 0.20, 0.04), metal_dark, 0.008)
    add_cylinder("Fuel tank", (-0.20, 0.53, 0.48), 0.14, 0.45, metal_rust, vertices=10,
                 rotation=(math.radians(90.0), 0.0, 0.0))
    for y in (0.34, 0.72):
        add_cylinder("Fuel tank band", (-0.20, y, 0.48), 0.148, 0.035, metal_dark, vertices=10,
                     rotation=(math.radians(90.0), 0.0, 0.0))
    add_cylinder("Fuel filler cap", (-0.20, 0.53, 0.625), 0.045, 0.04, cream, vertices=8)

    # Compact switchgear cabinet and ceramic insulators imply power distribution.
    add_cube("Switchgear side cabinet", (-0.275, -0.10, 0.50), (0.20, 0.43, 0.52), wood_light, 0.018)
    add_cube("Switchgear front", (-0.275, -0.322, 0.51), (0.16, 0.025, 0.39), metal_teal, 0.008)
    add_cube("Switchgear warning label", (-0.275, -0.34, 0.59), (0.10, 0.014, 0.08), cream, 0.003)
    for z, material in ((0.43, lamp), (0.53, glass)):
        add_cylinder("Status indicator", (-0.275, -0.357, z), 0.027, 0.025, material, vertices=8,
                     rotation=(math.radians(90.0), 0.0, 0.0))
    for x in (-0.34, -0.22, -0.10):
        add_cylinder("Ceramic insulator", (x, 0.0, 1.12), 0.038, 0.14, cream, vertices=8)
        add_cylinder("Insulator cap", (x, 0.0, 1.205), 0.05, 0.035, metal_dark, vertices=8)
    add_cube("Switchgear conduit", (-0.28, 0.12, 0.82), (0.045, 0.045, 0.46), metal_dark, 0.008)

    # A little amber pilot lamp is the only bright source on the station.
    add_cube("Beacon mount", (0.0, -0.40, 1.16), (0.22, 0.16, 0.10), metal_dark, 0.012)
    add_cylinder("Beacon base", (0.0, -0.40, 1.245), 0.075, 0.055, metal_rust, vertices=8)
    add_cylinder("Beacon lens", (0.0, -0.40, 1.30), 0.055, 0.075, lamp, vertices=8)
    add_cube("Side name plate", (0.0, -0.572, 0.93), (0.34, 0.018, 0.09), wood_dark, 0.004)
    add_cube("Lightning mark", (0.0, -0.586, 0.93), (0.08, 0.012, 0.055), cream, 0.002,
             (0.0, 0.0, math.radians(-18.0)))

    merge_by_material()
    root = bpy.data.objects.new(ASSET_NAME + "_Root", None)
    bpy.context.collection.objects.link(root)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.16
    for obj in ASSET_OBJECTS:
        obj.parent = root
        obj.matrix_parent_inverse = root.matrix_world.inverted()
    add_preview(scene, root)


def select_export_objects():
    bpy.ops.object.select_all(action="DESELECT")
    root = bpy.data.objects[ASSET_NAME + "_Root"]
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
        model_path, model_format = FBX_PATH, "FBX"
    elif operator_is_available(bpy.ops.wm.obj_export):
        bpy.ops.wm.obj_export(
            filepath=str(OBJ_FALLBACK_PATH), export_selected_objects=True,
            forward_axis="NEGATIVE_Z", up_axis="Y", global_scale=1.0,
            apply_modifiers=True, export_materials=True, export_object_groups=True,
            export_material_groups=True, path_mode="AUTO",
        )
        model_path, model_format = OBJ_FALLBACK_PATH, "OBJ fallback"
    else:
        raise RuntimeError("No FBX exporter or built-in OBJ exporter is available in this Blender build.")
    print("Created Blender source:", BLEND_PATH)
    print("Exported", model_format + ":", model_path)


make_asset()
export_asset()
