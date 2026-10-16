"""Create the first Last Landfall building asset in Blender.

Run from the Unity project root with:
    blender --background --python Tools/Blender/create_resident_hut.py

The script writes a Blender source file and a Unity-ready model. It exports FBX
when Blender's FBX exporter is available and falls back to Blender's built-in
OBJ exporter otherwise.
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
BLEND_PATH = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/ResidentHut.blend"
FBX_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/ResidentHut.fbx"
OBJ_FALLBACK_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/ResidentHut_OBJ.obj"

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
        modifier = obj.modifiers.new(name="Small worn edges", type="BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
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


def add_gable(name, y_center, depth, material):
    half_width = 0.32
    eave_z = 0.68
    ridge_z = 0.98
    front_y = y_center - depth * 0.5
    back_y = y_center + depth * 0.5
    vertices = [
        (-half_width, front_y, eave_z), (half_width, front_y, eave_z), (0.0, front_y, ridge_z),
        (-half_width, back_y, eave_z), (half_width, back_y, eave_z), (0.0, back_y, ridge_z),
    ]
    faces = [
        (0, 1, 2), (3, 5, 4),
        (0, 3, 4, 1), (0, 2, 5, 3), (1, 4, 5, 2),
    ]
    return add_mesh(name, vertices, faces, material)


def add_roof_slope(name, side, material):
    eave_x = side * 0.45
    ridge_x = 0.0
    eave_z = 0.68
    ridge_z = 0.98
    front_y = -0.43
    back_y = 0.43
    thickness = 0.04
    top = [
        (eave_x, front_y, eave_z), (ridge_x, front_y, ridge_z),
        (ridge_x, back_y, ridge_z), (eave_x, back_y, eave_z),
    ]
    bottom = [(x, y, z - thickness) for x, y, z in top]
    vertices = top + bottom
    faces = [
        (0, 1, 2, 3), (7, 6, 5, 4),
        (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0),
    ]
    return add_mesh(name, vertices, faces, material)


def add_window_frame(side_x, center_y, center_z, wood):
    frame_x = side_x
    add_cube("Window frame - left", (frame_x, center_y - 0.105, center_z), (0.035, 0.025, 0.19), wood, 0.006)
    add_cube("Window frame - right", (frame_x, center_y + 0.105, center_z), (0.035, 0.025, 0.19), wood, 0.006)
    add_cube("Window frame - lintel", (frame_x, center_y, center_z + 0.082), (0.035, 0.235, 0.025), wood, 0.005)
    add_cube("Window frame - sill", (frame_x, center_y, center_z - 0.082), (0.045, 0.235, 0.03), wood, 0.005)


def make_asset():
    clear_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    wood_dark = make_material("Wood | weathered dark", (0.22, 0.15, 0.10))
    wood_mid = make_material("Wood | salt-worn", (0.43, 0.30, 0.18))
    wood_light = make_material("Wood | sun-bleached", (0.58, 0.44, 0.27))
    roof_metal = make_material("Roof | faded sea green", (0.20, 0.35, 0.34), metallic=0.32)
    roof_rust = make_material("Roof | rust repair", (0.50, 0.24, 0.12), metallic=0.24)
    glass = make_material("Window | blue glass", (0.18, 0.43, 0.48), roughness=0.32, metallic=0.1)
    lamp = make_material("Lantern | warm glass", (0.95, 0.56, 0.20), roughness=0.3)

    # Stilted timber floor: the cabin sits safely above seasonal splash water.
    for x in (-0.30, 0.30):
        for y in (-0.30, 0.30):
            add_cube("Foundation timber", (x, y, 0.12), (0.075, 0.075, 0.20), wood_dark, 0.008)
    add_cube("Raised plank floor", (0.0, 0.0, 0.235), (0.76, 0.76, 0.07), wood_mid, 0.012)
    for index, x in enumerate((-0.27, -0.09, 0.09, 0.27)):
        add_cube("Deck board %02d" % index, (x, 0.0, 0.275), (0.17, 0.73, 0.018), wood_light if index % 2 == 0 else wood_mid)

    # Wall core, timber cladding and simple framing.
    add_cube("Cabin wall core", (0.0, 0.0, 0.475), (0.64, 0.60, 0.41), wood_mid)
    for index, x in enumerate((-0.27, -0.18, -0.09, 0.0, 0.09, 0.18, 0.27)):
        material = (wood_light, wood_mid, wood_light, wood_dark)[index % 4]
        add_cube("Front vertical board %02d" % index, (x, -0.307, 0.485), (0.082, 0.018, 0.38), material)
        add_cube("Rear vertical board %02d" % index, (x, 0.307, 0.485), (0.082, 0.018, 0.38), wood_mid)
    for index, y in enumerate((-0.24, -0.12, 0.0, 0.12, 0.24)):
        material = wood_light if index % 2 == 0 else wood_mid
        add_cube("Visible side board %02d" % index, (0.327, y, 0.485), (0.018, 0.108, 0.38), material)
    for z in (0.31, 0.66):
        add_cube("Front crossbeam", (0.0, -0.323, z), (0.67, 0.035, 0.055), wood_dark, 0.006)
        add_cube("Visible side crossbeam", (0.34, 0.0, z), (0.035, 0.62, 0.055), wood_dark, 0.006)

    # Front and rear gable ends beneath the roof.
    add_gable("Front gable", -0.005, 0.61, wood_mid)

    # A patched corrugated roof, kept inside the 1 m build tile.
    add_roof_slope("Left roof sheet", -1.0, roof_metal)
    add_roof_slope("Right roof sheet", 1.0, roof_metal)
    for side in (-1.0, 1.0):
        angle = math.radians(-34.0 if side < 0 else 34.0)
        for index, y in enumerate((-0.29, -0.10, 0.10, 0.29)):
            x = side * (0.14 + (index % 2) * 0.12)
            z = 0.98 - 0.30 * abs(x) / 0.45
            add_cube("Roof raised seam", (x, y, z), (0.018, 0.84, 0.022), roof_metal, 0.003, (0.0, angle, 0.0))
    add_cube(
        "Rust-red roof repair panel",
        (0.265, 0.11, 0.785),
        (0.17, 0.22, 0.025),
        roof_rust,
        0.006,
        (0.0, math.radians(34.0), 0.0),
    )
    add_cube("Ridge cap", (0.0, 0.0, 0.99), (0.075, 0.89, 0.035), roof_rust, 0.008)

    # Door and one side window read clearly from the game's isometric camera.
    add_cube("Door frame", (0.0, -0.329, 0.455), (0.245, 0.04, 0.37), wood_dark, 0.008)
    add_cube("Front door", (0.0, -0.353, 0.445), (0.205, 0.025, 0.325), wood_light, 0.006)
    add_cube("Door lower brace", (0.0, -0.369, 0.36), (0.19, 0.012, 0.025), wood_dark)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.018, location=(0.071, -0.374, 0.455))
    knob = bpy.context.object
    knob.name = "Door handle"
    knob.data.materials.append(roof_rust)
    ASSET_OBJECTS.append(knob)
    add_cube("Side window glass", (0.342, 0.07, 0.525), (0.025, 0.16, 0.13), glass)
    add_window_frame(0.353, 0.07, 0.525, wood_dark)
    add_cube("Window crossbar", (0.36, 0.07, 0.525), (0.012, 0.018, 0.13), wood_light)

    # Small porch step, lantern and rain barrel add scale without crowding the tile.
    add_cube("Porch step lower", (0.0, -0.44, 0.30), (0.34, 0.13, 0.055), wood_dark, 0.008)
    add_cube("Porch step upper", (0.0, -0.385, 0.325), (0.29, 0.09, 0.045), wood_light, 0.006)
    add_cube("Lantern bracket", (-0.20, -0.35, 0.59), (0.08, 0.025, 0.018), wood_dark)
    add_cube("Lantern housing", (-0.20, -0.375, 0.55), (0.055, 0.045, 0.075), wood_dark, 0.008)
    add_cube("Lantern glass", (-0.20, -0.401, 0.55), (0.032, 0.012, 0.047), lamp, 0.004)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.075, depth=0.16, location=(-0.33, 0.18, 0.37))
    barrel = bpy.context.object
    barrel.name = "Rain barrel"
    barrel.data.materials.append(wood_dark)
    ASSET_OBJECTS.append(barrel)
    for z in (0.31, 0.43):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.076, minor_radius=0.008, major_segments=10, minor_segments=4, location=(-0.33, 0.18, z))
        hoop = bpy.context.object
        hoop.name = "Rain barrel hoop"
        hoop.data.materials.append(roof_rust)
        ASSET_OBJECTS.append(hoop)

    # Merge by material so the imported building uses only a handful of renderers.
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
            merged.name = "ResidentHut_" + material.name.replace(" | ", "_").replace(" ", "_")
            merged_objects.append(merged)
        else:
            merged_objects.append(objects[0])
    ASSET_OBJECTS.clear()
    ASSET_OBJECTS.extend(merged_objects)

    root = bpy.data.objects.new("ResidentHut_Root", None)
    bpy.context.collection.objects.link(root)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.12
    for obj in ASSET_OBJECTS:
        obj.parent = root
        obj.matrix_parent_inverse = root.matrix_world.inverted()

    # A small studio setup is kept in the .blend but excluded from the FBX.
    bpy.ops.mesh.primitive_plane_add(size=3.0, location=(0.0, 0.0, 0.0))
    ground = bpy.context.object
    ground.name = "Preview ground (not exported)"
    ground.data.materials.append(make_material("Preview ground", (0.12, 0.19, 0.20)))
    camera_data = bpy.data.cameras.new("Asset preview camera")
    camera = bpy.data.objects.new("Asset preview camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (2.0, -2.7, 1.9)
    direction = Vector((0.0, 0.0, 0.48)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.8
    scene.camera = camera
    light_data = bpy.data.lights.new("Large softbox", type="AREA")
    light = bpy.data.objects.new("Large softbox", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (1.0, -2.0, 3.0)
    light.data.energy = 320.0
    light.data.shape = "DISK"
    light.data.size = 3.0
    light.rotation_euler = (Vector((0.0, 0.0, 0.4)) - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.world.color = (0.075, 0.095, 0.10)

    # Leave the model selected in the saved source file for convenient editing.
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for obj in ASSET_OBJECTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root


def select_export_objects():
    bpy.ops.object.select_all(action="DESELECT")
    root = bpy.data.objects["ResidentHut_Root"]
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


def export_fbx():
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
    return FBX_PATH


def export_obj_fallback():
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
    return OBJ_FALLBACK_PATH


def export_asset():
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    FBX_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))

    select_export_objects()
    if operator_is_available(bpy.ops.export_scene.fbx):
        model_path = export_fbx()
        model_format = "FBX"
    elif operator_is_available(bpy.ops.wm.obj_export):
        model_path = export_obj_fallback()
        model_format = "OBJ fallback (FBX exporter is not enabled)"
    else:
        raise RuntimeError(
            "No supported model exporter is available. Use a Blender build with "
            "the FBX extension enabled or the built-in OBJ exporter."
        )

    print("Created Blender source:", BLEND_PATH)
    print("Exported", model_format + ":", model_path)


make_asset()
export_asset()
