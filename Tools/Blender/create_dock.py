"""Create the modular settlement dock for Last Landfall.

Run from the Unity project root with:
    blender --background --python Tools/Blender/create_dock.py

The model origin is at the center of the land-side footprint. The pier extends
toward local -Y (the sea side) so the dock can be rotated to match a shoreline.
"""

from pathlib import Path
from mathutils import Vector

import bpy


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
NAME = "RescueDock"
BLEND_PATH = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/RescueDock.blend"
FBX_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/RescueDock.fbx"
OBJ_PATH = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/RescueDock_OBJ.obj"
ASSET_OBJECTS = []


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block_group in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                        bpy.data.cameras, bpy.data.lights):
        for block in list(block_group):
            if block.users == 0:
                block_group.remove(block)


def material(name, color, metallic=0.0, roughness=0.82):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = next((node for node in mat.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if shader is None:
        shader = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def add_cube(name, location, dimensions, mat, bevel=0.0, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rotation is not None:
        obj.rotation_euler = rotation
    if bevel > 0:
        mod = obj.modifiers.new("Soft worn edges", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.data.materials.append(mat)
    ASSET_OBJECTS.append(obj)
    return obj


def add_cylinder(name, location, radius, depth, mat, vertices=8, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=location, rotation=rotation or (0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    ASSET_OBJECTS.append(obj)
    return obj


def add_torus(name, location, major_radius, minor_radius, mat, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius,
                                     major_segments=10, minor_segments=4,
                                     location=location, rotation=rotation or (0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    ASSET_OBJECTS.append(obj)
    return obj


def add_beam(name, start, end, thickness, mat):
    a, b = Vector(start), Vector(end)
    delta = b - a
    obj = add_cube(name, (a + b) * 0.5,
                   (thickness, thickness, delta.length), mat, bevel=0.008)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def merge_by_material():
    grouped = {}
    for obj in ASSET_OBJECTS:
        grouped.setdefault(obj.data.materials[0], []).append(obj)
    merged = []
    for mat, objects in grouped.items():
        if len(objects) == 1:
            merged.append(objects[0])
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        obj = bpy.context.view_layer.objects.active
        obj.name = NAME + "_" + mat.name.replace(" | ", "_").replace(" ", "_")
        merged.append(obj)
    ASSET_OBJECTS.clear()
    ASSET_OBJECTS.extend(merged)


def build_asset():
    clear_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    timber = material("Dock | salt-worn timber", (0.40, 0.29, 0.18))
    timber_light = material("Dock | sun-bleached boards", (0.58, 0.45, 0.29))
    timber_dark = material("Dock | dark structural wood", (0.22, 0.17, 0.12))
    stone = material("Dock | old concrete", (0.38, 0.42, 0.39))
    metal = material("Dock | corroded hardware", (0.27, 0.34, 0.32), metallic=0.45)
    rust = material("Dock | rust orange", (0.57, 0.27, 0.13), metallic=0.22)
    rubber = material("Dock | salvaged tire", (0.09, 0.12, 0.12))
    rope = material("Dock | faded rope", (0.63, 0.52, 0.34))

    # Land-side abutment and a short raised landing.
    add_cube("Stone landing abutment", (0.0, 0.38, 0.12), (1.45, 0.72, 0.24), stone, 0.06)
    add_cube("Timber landing deck", (0.0, 0.22, 0.27), (1.42, 0.70, 0.08), timber, 0.018)

    # Narrow pier extends out from the land into the water along local -Y.
    pier_start, pier_end = 0.0, -2.05
    for x in (-0.52, 0.0, 0.52):
        for index in range(5):
            y = -0.18 - index * 0.40
            add_cube("Pier deck plank", (x, y, 0.30), (0.49, 0.38, 0.07),
                     timber_light if (index + int((x + 1) * 10)) % 3 else timber, 0.012)
    for x in (-0.58, 0.58):
        for y in (-0.18, -0.88, -1.58, -2.08):
            add_cylinder("Pier support pile", (x, y, -0.12), 0.075, 0.92, timber_dark)
            add_cylinder("Pile cap", (x, y, 0.32), 0.11, 0.09, timber)

    # Safety posts, a repaired handrail and mooring cleats make the purpose clear.
    for x in (-0.66, 0.66):
        for y in (0.38, -0.10, -0.62):
            add_cube("Dock bollard", (x, y, 0.54), (0.12, 0.12, 0.42), timber_dark, 0.02)
            add_cube("Bollard cap", (x, y, 0.76), (0.19, 0.15, 0.07), rust, 0.015)
    for y in (0.48, -0.02):
        add_beam("Landing safety rail", (-0.67, y, 0.83), (0.67, y, 0.83), 0.055, timber)
    for x in (-0.66, 0.66):
        add_cube("Rail upright", (x, 0.23, 0.58), (0.055, 0.055, 0.56), timber_dark, 0.008)

    # A simple ladder down the exposed end; visible from the isometric camera.
    for x in (-0.25, 0.25):
        add_cube("Ladder side rail", (x, -2.04, -0.03), (0.045, 0.055, 0.62), metal, 0.008)
    for z in (0.18, 0.04, -0.10, -0.24, -0.38):
        add_cube("Ladder rung", (0.0, -2.04, z), (0.54, 0.07, 0.045), rust, 0.006)

    # Salvaged tire bumpers and metal tie-off rings.
    for x, y in ((-0.68, -0.92), (0.68, -1.35)):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.055,
                                         major_segments=10, minor_segments=5,
                                         location=(x, y, 0.24), rotation=(0, 1.5708, 0))
        tire = bpy.context.object
        tire.name = "Reused tire bumper"
        tire.data.materials.append(rubber)
        ASSET_OBJECTS.append(tire)
    for x in (-0.43, 0.43):
        add_torus("Mooring ring", (x, 0.40, 0.42), 0.055, 0.012, metal,
                  rotation=(1.5708, 0, 0))

    # A small patched warning placard and warm signal lamp give the dock character.
    add_cube("Dock warning placard", (0.0, 0.55, 0.93), (0.48, 0.055, 0.28), rust, 0.025)
    add_cube("Placard pale stripe", (0.0, 0.515, 0.93), (0.32, 0.018, 0.045), timber_light)
    add_cylinder("Signal lamp housing", (0.56, 0.43, 1.02), 0.07, 0.13, metal)
    add_cylinder("Signal lamp glass", (0.56, 0.43, 1.10), 0.05, 0.045,
                 material("Dock | amber signal glass", (0.98, 0.56, 0.18), roughness=0.3))

    merge_by_material()
    root = bpy.data.objects.new(NAME + "_Root", None)
    bpy.context.collection.objects.link(root)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.25
    for obj in ASSET_OBJECTS:
        obj.parent = root
        obj.matrix_parent_inverse = root.matrix_world.inverted()

    # Preview-only objects are not selected for export.
    bpy.ops.mesh.primitive_plane_add(size=5.5, location=(0.0, -0.8, -0.48))
    water = bpy.context.object
    water.name = "Preview water (not exported)"
    water.data.materials.append(material("Preview water", (0.055, 0.22, 0.29), roughness=0.38))
    camera_data = bpy.data.cameras.new("Dock preview camera")
    camera = bpy.data.objects.new("Dock preview camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (3.7, -4.3, 3.25)
    camera.rotation_euler = (Vector((0.0, -0.65, 0.20)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 4.6
    scene.camera = camera
    light_data = bpy.data.lights.new("Dock softbox", type="AREA")
    light = bpy.data.objects.new("Dock softbox", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (1.0, -1.0, 4.0)
    light.data.energy = 450
    light.data.shape = "DISK"
    light.data.size = 4.0
    light.rotation_euler = (Vector((0.0, -0.7, 0.0)) - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.world.color = (0.07, 0.09, 0.10)

    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for obj in ASSET_OBJECTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root


def operator_available(operator):
    try:
        operator.get_rna_type()
        return True
    except (AttributeError, RuntimeError):
        return False


def export_asset():
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    FBX_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    if operator_available(bpy.ops.export_scene.fbx):
        bpy.ops.export_scene.fbx(filepath=str(FBX_PATH), use_selection=True,
                                 object_types={"EMPTY", "MESH"}, axis_forward="-Z", axis_up="Y",
                                 apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                                 use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False,
                                 path_mode="AUTO")
        print("Exported FBX:", FBX_PATH)
    elif operator_available(bpy.ops.wm.obj_export):
        bpy.ops.wm.obj_export(filepath=str(OBJ_PATH), export_selected_objects=True,
                              forward_axis="NEGATIVE_Z", up_axis="Y", global_scale=1.0,
                              apply_modifiers=True, export_materials=True,
                              export_object_groups=True, export_material_groups=True,
                              path_mode="AUTO")
        print("Exported OBJ fallback:", OBJ_PATH)
    else:
        raise RuntimeError("No supported exporter is available; enable Blender's FBX extension.")
    print("Created Blender source:", BLEND_PATH)


build_asset()
export_asset()
