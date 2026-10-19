"""Create a low-poly salvage workshop for Last Landfall.

Run with Blender's bundled Python, from any working directory:
    blender --background --python Tools/Blender/create_salvage_workshop.py

The source .blend keeps its studio preview camera and lights. The Unity model
export contains only the building hierarchy and exports as FBX, with Blender's
built-in OBJ exporter as a fallback.
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
ASSET_NAME = "SalvageWorkshop"
BLEND_PATH = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Buildings" / (ASSET_NAME + ".blend")
FBX_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Buildings" / (ASSET_NAME + ".fbx")
OBJ_FALLBACK_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Buildings" / (ASSET_NAME + "_OBJ.obj")

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


def add_shed_roof(material):
    # A shallow lean-to roof: its front eave faces the local -Y entrance.
    add_cube("Main patched roof", (0.0, 0.30, 1.385), (1.58, 1.20, 0.09), material,
             0.025, (math.radians(-5.0), 0.0, 0.0))
    for index, x in enumerate((-0.58, -0.30, 0.0, 0.30, 0.58)):
        add_cube("Roof corrugation %02d" % index, (x, 0.30, 1.435), (0.025, 1.18, 0.022), material,
                 0.005, (math.radians(-5.0), 0.0, 0.0))


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
    bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0.0, 0.0, 0.0))
    ground = bpy.context.object
    ground.name = "Preview ground (not exported)"
    ground.data.materials.append(make_material("Preview | deep slate", (0.075, 0.12, 0.14)))

    camera_data = bpy.data.cameras.new("Asset preview camera")
    camera = bpy.data.objects.new("Asset preview camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (3.6, -4.8, 3.25)
    direction = Vector((0.0, -0.02, 0.95)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.45
    scene.camera = camera

    light_data = bpy.data.lights.new("Large softbox", type="AREA")
    light = bpy.data.objects.new("Large softbox", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (1.2, -2.7, 4.0)
    light.data.energy = 430.0
    light.data.shape = "DISK"
    light.data.size = 3.4
    light.rotation_euler = (Vector((0.0, 0.0, 0.8)) - light.location).to_track_quat("-Z", "Y").to_euler()

    fill_data = bpy.data.lights.new("Cool fill", type="AREA")
    fill = bpy.data.objects.new("Cool fill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = (-3.0, 1.0, 2.8)
    fill.data.energy = 150.0
    fill.data.color = (0.48, 0.68, 0.78)
    fill.data.size = 3.0
    fill.rotation_euler = (Vector((0.0, 0.0, 0.8)) - fill.location).to_track_quat("-Z", "Y").to_euler()

    scene.render.resolution_x = 960
    scene.render.resolution_y = 800
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

    wood_dark = make_material("Wood | tarred salvage", (0.16, 0.12, 0.085))
    wood_mid = make_material("Wood | salt worn", (0.36, 0.27, 0.18))
    wood_light = make_material("Wood | sun bleached", (0.55, 0.43, 0.28))
    metal_dark = make_material("Metal | oxidized frame", (0.105, 0.18, 0.19), metallic=0.42)
    metal_teal = make_material("Metal | faded sea green", (0.21, 0.36, 0.35), metallic=0.34)
    metal_rust = make_material("Metal | rust repair", (0.50, 0.235, 0.12), metallic=0.25)
    hazard = make_material("Paint | worn amber", (0.78, 0.49, 0.16), metallic=0.12)
    lamp = make_material("Lamp | warm amber", (1.0, 0.43, 0.105), roughness=0.32, emission=1.4)
    shadow = make_material("Interior | deep shadow", (0.055, 0.075, 0.072), metallic=0.15)

    # Footprint is kept below 2 x 2 m. Short stilts lift the workshop above spray.
    for x in (-0.78, 0.0, 0.78):
        for y in (-0.72, 0.38, 0.78):
            add_cube("Piled timber footing", (x, y, 0.075), (0.12, 0.14, 0.15), wood_dark, 0.012)
    add_cube("Workshop deck", (0.0, 0.0, 0.19), (1.84, 1.78, 0.12), wood_mid, 0.018)
    for index, x in enumerate((-0.72, -0.48, -0.24, 0.0, 0.24, 0.48, 0.72)):
        add_cube("Deck plank %02d" % index, (x, 0.0, 0.255), (0.22, 1.73, 0.025),
                 wood_light if index % 3 == 0 else wood_mid, 0.004)

    # Shed occupies the back half. The wide front bay remains open and faces -Y.
    add_cube("Rear wall", (0.0, 0.765, 0.76), (1.42, 0.075, 1.05), wood_mid, 0.012)
    for side in (-1.0, 1.0):
        add_cube("Workshop side wall", (side * 0.685, 0.30, 0.74), (0.09, 0.96, 0.98), wood_mid, 0.012)
        for index, y in enumerate((-0.04, 0.16, 0.36, 0.56, 0.76)):
            panel_material = metal_teal if (index + (side > 0)) % 3 else metal_rust
            add_cube("Side cladding patch", (side * 0.737, y, 0.79), (0.022, 0.16, 0.80), panel_material, 0.004)
        add_cube("Side corner post", (side * 0.72, 0.29, 0.77), (0.12, 1.03, 1.06), wood_dark, 0.012)

    # Front loading bay: heavy jambs, lintel and a visible shadowed press inside.
    for side in (-1.0, 1.0):
        add_cube("Bay timber jamb", (side * 0.665, -0.155, 0.78), (0.13, 0.12, 1.02), wood_dark, 0.014)
        add_cube("Bay warning stripe", (side * 0.665, -0.224, 0.82), (0.10, 0.018, 0.69), hazard, 0.004)
        for index, z in enumerate((0.53, 0.74, 0.95, 1.16)):
            add_cube("Jamb dark stripe", (side * 0.665, -0.237, z), (0.105, 0.012, 0.055), metal_dark, 0.002,
                     (0.0, 0.0, math.radians(32.0)))
    add_cube("Bay lintel", (0.0, -0.15, 1.30), (1.45, 0.15, 0.15), wood_dark, 0.016)
    add_cube("Bay header repair plate", (0.0, -0.236, 1.31), (0.48, 0.025, 0.07), metal_rust, 0.005)
    add_cube("Interior rear shadow", (0.0, 0.60, 0.73), (1.03, 0.025, 0.86), shadow)

    # A chunky hand-operated shear/crusher is the focal point inside the open bay.
    add_cube("Scrap shear pedestal", (0.0, 0.28, 0.45), (0.52, 0.38, 0.35), metal_dark, 0.035)
    add_cube("Shear lower jaw", (0.0, 0.08, 0.66), (0.70, 0.28, 0.10), metal_rust, 0.018)
    add_cube("Shear upper ram", (0.0, 0.33, 0.95), (0.20, 0.22, 0.42), metal_teal, 0.018)
    add_cube("Shear blade", (0.0, 0.08, 0.81), (0.63, 0.045, 0.035), hazard, 0.004)
    add_cylinder("Hydraulic pivot", (0.37, 0.24, 0.84), 0.10, 0.08, metal_rust, vertices=8,
                 rotation=(0.0, math.radians(90.0), 0.0))
    add_cube("Hydraulic ram", (0.26, 0.34, 0.78), (0.075, 0.09, 0.32), metal_dark, 0.012,
             (0.0, math.radians(-22.0), 0.0))

    add_shed_roof(metal_teal)
    # Mismatched panels make the roof read as repeatedly repaired.
    add_cube("Roof rust patch", (0.48, 0.18, 1.455), (0.28, 0.38, 0.025), metal_rust, 0.006,
             (math.radians(-5.0), 0.0, math.radians(-7.0)))
    add_cube("Roof wood patch", (-0.44, 0.55, 1.452), (0.20, 0.27, 0.03), wood_light, 0.006,
             (math.radians(-5.0), 0.0, math.radians(8.0)))

    # Gantry crane stands at the loading edge; its hook and dangling salvage read from above.
    for side in (-1.0, 1.0):
        add_cube("Gantry upright", (side * 0.81, -0.71, 1.13), (0.105, 0.12, 1.75), metal_dark, 0.016)
        add_cube("Gantry foot plate", (side * 0.81, -0.71, 0.29), (0.23, 0.22, 0.08), metal_rust, 0.008)
        add_cube("Gantry brace", (side * 0.72, -0.66, 1.55), (0.26, 0.11, 0.11), metal_teal, 0.01,
                 (0.0, 0.0, math.radians(side * -38.0)))
    add_cube("Gantry crossbeam", (0.0, -0.71, 2.035), (1.72, 0.14, 0.16), metal_teal, 0.02)
    add_cube("Trolley carriage", (0.18, -0.71, 1.91), (0.32, 0.20, 0.16), metal_rust, 0.018)
    add_cylinder("Trolley wheel left", (0.08, -0.71, 1.90), 0.075, 0.065, metal_dark, vertices=8,
                 rotation=(0.0, math.radians(90.0), 0.0))
    add_cylinder("Trolley wheel right", (0.28, -0.71, 1.90), 0.075, 0.065, metal_dark, vertices=8,
                 rotation=(0.0, math.radians(90.0), 0.0))
    add_cube("Hoist chain", (0.18, -0.71, 1.69), (0.025, 0.025, 0.35), metal_dark)
    add_cube("Hoist hook block", (0.18, -0.71, 1.48), (0.17, 0.12, 0.12), hazard, 0.015)
    add_cylinder("Hook shank", (0.18, -0.71, 1.36), 0.026, 0.15, metal_dark, vertices=8)
    add_cylinder("Hook curve", (0.18, -0.71, 1.285), 0.075, 0.035, metal_rust, vertices=8)
    add_cube("Lifted scrap plate", (0.18, -0.71, 1.17), (0.34, 0.19, 0.055), metal_rust, 0.012,
             (0.0, math.radians(12.0), math.radians(-8.0)))

    # Small sorting bins and a bundle of salvaged pipe stay within the two-tile base.
    for index, x in enumerate((-0.62, 0.62)):
        add_cube("Sorting bin body", (x, -0.32, 0.38), (0.30, 0.38, 0.24), metal_dark, 0.018)
        add_cube("Sorting bin rim", (x, -0.32, 0.515), (0.34, 0.42, 0.035), metal_rust, 0.008)
        for rib in (-1.0, 1.0):
            add_cube("Bin corner brace", (x + rib * 0.12, -0.32, 0.40), (0.022, 0.40, 0.20), metal_teal, 0.003)
    for index, z in enumerate((0.34, 0.40, 0.46)):
        add_cylinder("Salvaged pipe bundle %02d" % index, (0.64, 0.39, z), 0.045, 0.50,
                     metal_rust if index == 1 else metal_dark, vertices=8,
                     rotation=(math.radians(90.0), 0.0, 0.0))

    # Hand-painted workshop plate and a single warm task light.
    add_cube("Workshop name board", (0.0, -0.245, 1.20), (0.54, 0.028, 0.13), wood_dark, 0.008)
    add_cube("Workshop marker", (0.0, -0.264, 1.20), (0.14, 0.012, 0.075), hazard, 0.004)
    add_cube("Work lamp housing", (0.49, -0.27, 1.17), (0.10, 0.075, 0.10), metal_dark, 0.01)
    add_cube("Work lamp lens", (0.49, -0.313, 1.17), (0.058, 0.018, 0.055), lamp, 0.004)

    merge_by_material()
    root = bpy.data.objects.new(ASSET_NAME + "_Root", None)
    bpy.context.collection.objects.link(root)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.20
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
