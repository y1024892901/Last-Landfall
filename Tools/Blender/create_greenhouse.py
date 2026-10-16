"""Create a low-poly greenhouse asset for Last Landfall.

Run from any working directory with Blender:
    blender --background --python Tools/Blender/create_greenhouse.py

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
BLEND_PATH = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Greenhouse.blend"
FBX_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Greenhouse.fbx"
OBJ_FALLBACK_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Greenhouse_OBJ.obj"

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
    obj = add_cube(
        name,
        (start + end) * 0.5,
        (width, width, direction.length),
        material,
    )
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


def add_glass_panel(name, corners, glass):
    """Create a single low-poly glazing face from four world-space points."""
    return add_mesh(name, corners, [(0, 1, 2, 3)], glass)


def add_roof_panel(name, side, x0, x1, y0, y1, material):
    ridge_z = 1.58
    eave_z = 1.00
    eave_x = 0.82

    def roof_z(x):
        return ridge_z + (eave_z - ridge_z) * (abs(x) / eave_x) + 0.012

    x_near = side * x0
    x_far = side * x1
    add_glass_panel(
        name,
        [
            (x_near, y0, roof_z(x_near)),
            (x_far, y0, roof_z(x_far)),
            (x_far, y1, roof_z(x_far)),
            (x_near, y1, roof_z(x_near)),
        ],
        material,
    )


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
            merged.name = "Greenhouse_" + material.name.replace(" | ", "_").replace(" ", "_")
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
    camera.location = (3.3, -4.3, 3.0)
    target = Vector((0.0, 0.0, 0.76))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 3.35
    scene.camera = camera

    light_data = bpy.data.lights.new("Large softbox", type="AREA")
    light = bpy.data.objects.new("Large softbox", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (1.4, -2.5, 4.0)
    light.data.energy = 520.0
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
    metal = make_material("Metal | faded sea green", (0.20, 0.36, 0.34), metallic=0.28)
    rust = make_material("Metal | rust repair", (0.52, 0.25, 0.14), metallic=0.22)
    glass = make_material("Glass | storm blue", (0.20, 0.46, 0.49), roughness=0.28, metallic=0.08)
    glass_pale = make_material("Glass | sunlit panel", (0.34, 0.61, 0.59), roughness=0.32, metallic=0.04)

    # Raised 2 x 2 m deck and corner stilts; every part stays above z=0.
    for x in (-0.78, 0.78):
        for y in (-0.78, 0.78):
            add_cube("Deck support post", (x, y, 0.055), (0.10, 0.10, 0.11), wood_dark, 0.008)
    add_cube("Raised timber deck", (0.0, 0.0, 0.105), (1.82, 1.82, 0.09), wood, 0.012)
    for index, x in enumerate((-0.72, -0.48, -0.24, 0.0, 0.24, 0.48, 0.72)):
        add_cube("Deck plank %02d" % index, (x, 0.0, 0.154), (0.22, 1.78, 0.012), wood_light if index % 3 == 0 else wood)

    # Guttered greenhouse frame: a compact timber sill with a metal top rail.
    for x in (-0.78, 0.78):
        add_cube("Long sill", (x, 0.0, 0.25), (0.09, 1.60, 0.12), wood_dark, 0.008)
    for y in (-0.78, 0.78):
        add_cube("End sill", (0.0, y, 0.25), (1.60, 0.09, 0.12), wood_dark, 0.008)

    eave_z = 1.00
    ridge_z = 1.58
    for x in (-0.78, 0.78):
        add_beam("Outer greenhouse post", (x, -0.77, 0.30), (x, -0.77, eave_z), 0.065, wood_light)
        add_beam("Outer greenhouse post", (x, 0.77, 0.30), (x, 0.77, eave_z), 0.065, wood_light)
        add_beam("Side glazing rail", (x, -0.75, 0.63), (x, 0.75, 0.63), 0.035, wood_dark)
        add_beam("Side eave rail", (x, -0.78, eave_z), (x, 0.78, eave_z), 0.07, metal)
        add_beam("Side lower rail", (x, -0.75, 0.34), (x, 0.75, 0.34), 0.035, wood_dark)

    # Side glazing is split into framed panes; the opaque cool tint reads well
    # in an isometric game camera and does not rely on transparency sorting.
    for side in (-1.0, 1.0):
        x = side * 0.765
        for index, (y0, y1) in enumerate(((-0.70, -0.29), (-0.22, 0.22), (0.29, 0.70))):
            add_glass_panel(
                "Side glass pane %02d" % index,
                [(x, y0, 0.37), (x, y1, 0.37), (x, y1, 0.96), (x, y0, 0.96)],
                glass if (index + int(side > 0)) % 2 else glass_pale,
            )
        for y in (-0.73, -0.25, 0.25, 0.73):
            add_beam("Side glazing mullion", (x, y, 0.32), (x, y, eave_z), 0.035, wood_light)

    # The front (-Y) has a clear entry door and two glazed bays.
    front_y = -0.765
    for x0, x1 in ((-0.69, -0.29), (0.29, 0.69)):
        add_glass_panel(
            "Front glass bay",
            [(x0, front_y, 0.36), (x1, front_y, 0.36), (x1, front_y, 0.96), (x0, front_y, 0.96)],
            glass_pale,
        )
    add_cube("Door jamb left", (-0.20, -0.79, 0.59), (0.07, 0.07, 0.56), wood_dark, 0.006)
    add_cube("Door jamb right", (0.20, -0.79, 0.59), (0.07, 0.07, 0.56), wood_dark, 0.006)
    add_cube("Greenhouse door", (0.0, -0.80, 0.59), (0.36, 0.035, 0.53), metal, 0.008)
    add_cube("Door glazing", (0.0, -0.823, 0.68), (0.25, 0.012, 0.28), glass, 0.004)
    add_cube("Door kick plate", (0.0, -0.824, 0.39), (0.27, 0.016, 0.08), rust, 0.003)
    add_cube("Door latch", (0.13, -0.833, 0.55), (0.035, 0.018, 0.06), wood_light, 0.004)
    add_cube("Front sill beam", (0.0, -0.78, 0.97), (1.58, 0.08, 0.06), wood_dark, 0.006)

    # Rear wall glazing, slightly patched so the building feels reclaimed.
    for x0, x1, material in ((-0.69, -0.27, glass), (-0.23, 0.23, glass_pale), (0.27, 0.69, glass)):
        add_glass_panel(
            "Rear glass bay",
            [(x0, 0.765, 0.37), (x1, 0.765, 0.37), (x1, 0.765, 0.96), (x0, 0.765, 0.96)],
            material,
        )
    for x in (-0.76, -0.25, 0.25, 0.76):
        add_beam("Rear glazing mullion", (x, 0.78, 0.31), (x, 0.78, eave_z), 0.035, wood_light)

    # Gable glass and ridge support.
    for y in (-0.77, 0.77):
        add_mesh(
            "Triangular gable glazing",
            [(-0.75, y, 0.99), (0.75, y, 0.99), (0.0, y, 1.55)],
            [(0, 1, 2)],
            glass,
        )
        add_beam("Gable king post", (0.0, y, 1.00), (0.0, y, 1.55), 0.045, wood_light)
        add_beam("Gable left rafter", (-0.76, y, 1.00), (0.0, y, 1.57), 0.045, wood_dark)
        add_beam("Gable right rafter", (0.76, y, 1.00), (0.0, y, 1.57), 0.045, wood_dark)

    # Two pitched glass roofs, interrupted by one rust-red repair patch.
    roof_bands = ((0.055, 0.34), (0.39, 0.59), (0.64, 0.80))
    for side in (-1.0, 1.0):
        for index, (x0, x1) in enumerate(roof_bands):
            material = glass_pale if index == 1 else glass
            if side > 0 and index == 2:
                material = rust
            for y0, y1 in ((-0.71, -0.26), (-0.21, 0.21), (0.26, 0.71)):
                add_roof_panel("Roof glazing panel", side, x0, x1, y0, y1, material)
        for y in (-0.76, -0.26, 0.26, 0.76):
            add_beam("Roof cross rafter", (0.0, y, ridge_z), (side * 0.82, y, eave_z), 0.045, wood_dark)
        add_beam("Roof edge flashing", (side * 0.82, -0.80, eave_z), (side * 0.82, 0.80, eave_z), 0.05, metal)
    add_beam("Ridge cap", (0.0, -0.82, 1.59), (0.0, 0.82, 1.59), 0.07, rust)

    # A simple rain gutter and downspout signal the greenhouse's water use.
    add_cube("Front gutter", (0.0, -0.84, 0.98), (1.55, 0.055, 0.045), metal, 0.008)
    add_beam("Gutter downpipe", (0.72, -0.84, 0.96), (0.72, -0.84, 0.28), 0.035, metal)
    add_cube("Patched gutter bracket", (0.56, -0.845, 0.95), (0.12, 0.018, 0.05), rust, 0.004)

    merge_by_material()
    root = bpy.data.objects.new("Greenhouse_Root", None)
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
    root = bpy.data.objects["Greenhouse_Root"]
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
