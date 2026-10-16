"""Create modular 1 x 1 m low-poly road tiles for Last Landfall.

Run with Blender from the Unity project root:
    blender --background --python Tools/Blender/create_road_tiles.py

One editable source file contains five staged modules: straight, corner, T,
cross, and dead-end. Each exported model is centered on its own tile origin and
contains only that tile. The modules are built from salt-worn boards, dark
underlay, and patched metal edging. No add-on is required for the OBJ fallback.
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
SOURCE_PATH = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/RoadTiles.blend"
MODEL_DIRECTORY = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models"

TILE_SIZE = 1.0
ROAD_WIDTH = 0.50
BOARD_WIDTH = 0.43
BASE_THICKNESS = 0.068
BOARD_THICKNESS = 0.042
BOARD_TOP_Z = 0.082
BOARD_TARGET_LENGTH = 0.175

ASSET_OBJECTS = []
TILE_ASSETS = {}


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def make_material(name, color, roughness=0.86, metallic=0.0):
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


def add_cube(name, location, dimensions, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    ASSET_OBJECTS.append(obj)
    return obj


def material_for_board(index, materials):
    # Repeat a legible weathering pattern; the occasional metal plate reads as a repair.
    if index % 7 == 4:
        return materials["patch"]
    return materials["wood_light"] if index % 3 == 0 else materials["wood_mid"]


def add_run(axis, start, end, materials, board_offset=0):
    """Build one straight road arm between coordinates along X or Y.

    The underlay and edge strips terminate exactly at tile boundaries. Top
    planks are inset slightly so adjacent rotated tiles do not z-fight.
    """
    if end <= start:
        raise ValueError("Road run end must be greater than its start")
    length = end - start
    along_center = (start + end) * 0.5
    if axis == "y":
        add_cube("Road underlay", (0.0, along_center, BASE_THICKNESS * 0.5),
                 (ROAD_WIDTH, length, BASE_THICKNESS), materials["underlay"])
        rail_x = ROAD_WIDTH * 0.5 - 0.014
        rail_dims = (0.026, length, 0.040)
        rail_centers = ((-rail_x, along_center, 0.078), (rail_x, along_center, 0.078))
    elif axis == "x":
        add_cube("Road underlay", (along_center, 0.0, BASE_THICKNESS * 0.5),
                 (length, ROAD_WIDTH, BASE_THICKNESS), materials["underlay"])
        rail_y = ROAD_WIDTH * 0.5 - 0.014
        rail_dims = (length, 0.026, 0.040)
        rail_centers = ((along_center, -rail_y, 0.078), (along_center, rail_y, 0.078))
    else:
        raise ValueError("Road axis must be 'x' or 'y'")

    for center in rail_centers:
        add_cube("Patched metal road edging", center, rail_dims, materials["edge"])

    segment_count = max(1, int(math.ceil(length / BOARD_TARGET_LENGTH)))
    segment_length = length / segment_count
    gap = min(0.012, segment_length * 0.08)
    for index in range(segment_count):
        along = start + (index + 0.5) * segment_length
        plank_length = max(0.025, segment_length - gap)
        if axis == "y":
            location = (0.0, along, BOARD_TOP_Z)
            dimensions = (BOARD_WIDTH, plank_length, BOARD_THICKNESS)
        else:
            location = (along, 0.0, BOARD_TOP_Z)
            dimensions = (plank_length, BOARD_WIDTH, BOARD_THICKNESS)
        board_material = material_for_board(index + board_offset, materials)
        add_cube("Salt-worn road plank", location, dimensions, board_material)


def add_junction_patch(materials):
    """Cover the half-meter-wide crossing with four tight-fitting repair slabs."""
    add_cube("Junction underlay", (0.0, 0.0, BASE_THICKNESS * 0.5),
             (ROAD_WIDTH, ROAD_WIDTH, BASE_THICKNESS), materials["underlay"])
    patch_size = 0.235
    centers = (
        (-0.12, -0.12, materials["wood_mid"]),
        (0.12, -0.12, materials["patch"]),
        (-0.12, 0.12, materials["stone"]),
        (0.12, 0.12, materials["wood_light"]),
    )
    for x, y, material in centers:
        add_cube("Junction repair slab", (x, y, BOARD_TOP_Z),
                 (patch_size, patch_size, BOARD_THICKNESS), material)


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
            merged.name = "RoadTile_" + material.name.replace(" | ", "_").replace(" ", "_")
            merged_objects.append(merged)
        else:
            merged_objects.append(objects[0])
    ASSET_OBJECTS.clear()
    ASSET_OBJECTS.extend(merged_objects)


def make_tile_materials():
    return {
        "underlay": make_material("Road | tar-dark timber", (0.16, 0.14, 0.115)),
        "wood_mid": make_material("Road | salt-worn timber", (0.39, 0.29, 0.19)),
        "wood_light": make_material("Road | sun-bleached planks", (0.60, 0.48, 0.32)),
        "edge": make_material("Road | faded sea-green iron", (0.19, 0.35, 0.35), metallic=0.34),
        "patch": make_material("Road | rusted repair plate", (0.54, 0.25, 0.14), metallic=0.24),
        "stone": make_material("Road | salt-stained stone", (0.42, 0.44, 0.40), roughness=0.94),
    }


def finish_tile(name, display_location):
    merge_by_material()
    root = bpy.data.objects.new(name + "_Root", None)
    bpy.context.collection.objects.link(root)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.12
    root["tile_size_m"] = TILE_SIZE
    root["tile_origin"] = "center of 1 x 1 m cell"
    root["front_direction"] = "-Y"
    root["road_module"] = name
    for obj in ASSET_OBJECTS:
        obj.parent = root
        obj.matrix_parent_inverse = root.matrix_world.inverted()

    # Keep mesh-local coordinates centered on the tile; only the source preview
    # staging empty receives a display offset.
    root.location = display_location
    TILE_ASSETS[name] = {"root": root, "objects": list(ASSET_OBJECTS)}
    ASSET_OBJECTS.clear()


def build_straight(materials):
    add_run("y", -0.5, 0.5, materials)


def build_corner(materials):
    # Connect the south and east tile edges. Rotate this module for other corners.
    add_run("y", -0.5, -0.25, materials)
    add_run("x", 0.25, 0.5, materials, board_offset=2)
    add_junction_patch(materials)


def build_tee(materials):
    # Main road runs east-west; the branch opens on the south edge.
    add_run("x", -0.5, 0.5, materials)
    add_run("y", -0.5, -0.25, materials, board_offset=2)
    add_junction_patch(materials)


def build_cross(materials):
    add_run("x", -0.5, 0.5, materials)
    add_run("y", -0.5, -0.25, materials, board_offset=1)
    add_run("y", 0.25, 0.5, materials, board_offset=4)
    add_junction_patch(materials)


def build_end(materials):
    # This cap accepts traffic from the south and closes at the tile center.
    add_run("y", -0.5, -0.025, materials)
    add_cube("Rusted road end barrier", (0.0, -0.022, 0.105),
             (ROAD_WIDTH, 0.045, 0.086), materials["patch"])
    for x in (-0.17, 0.17):
        add_cube("End barrier reflector", (x, -0.048, 0.11),
                 (0.045, 0.012, 0.055), materials["wood_light"])


def build_all_tiles():
    # The source file is laid out with spacing so each 1 m tile is easy to inspect.
    tile_specs = (
        ("RoadStraight", build_straight, (-0.70, -0.70, 0.0)),
        ("RoadCorner", build_corner, (0.70, -0.70, 0.0)),
        ("RoadTee", build_tee, (-1.40, 0.70, 0.0)),
        ("RoadCross", build_cross, (0.0, 0.70, 0.0)),
        ("RoadEnd", build_end, (1.40, 0.70, 0.0)),
    )
    for name, builder, display_location in tile_specs:
        ASSET_OBJECTS.clear()
        builder(make_tile_materials())
        finish_tile(name, display_location)


def add_preview_setup(scene):
    preview_material = make_material("Preview | deep water", (0.055, 0.105, 0.12), roughness=0.96)
    bpy.ops.mesh.primitive_plane_add(size=4.7, location=(0.0, 0.0, -0.008))
    ground = bpy.context.object
    ground.name = "Preview water floor (not exported)"
    ground.data.materials.append(preview_material)

    camera_data = bpy.data.cameras.new("Road tiles preview camera")
    camera = bpy.data.objects.new("Road tiles preview camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (3.5, -4.5, 5.5)
    target = Vector((0.0, 0.0, 0.10))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 5.4
    scene.camera = camera

    light_data = bpy.data.lights.new("Road tiles preview softbox", type="AREA")
    light = bpy.data.objects.new("Road tiles preview softbox", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (1.0, -2.7, 5.0)
    light.data.energy = 650.0
    light.data.shape = "DISK"
    light.data.size = 4.0
    light.rotation_euler = (Vector((0.0, 0.0, 0.0)) - light.location).to_track_quat("-Z", "Y").to_euler()

    scene.render.resolution_x = 1300
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.world.color = (0.045, 0.065, 0.075)

    bpy.ops.object.select_all(action="DESELECT")
    for tile in TILE_ASSETS.values():
        tile["root"].select_set(True)
        for obj in tile["objects"]:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = TILE_ASSETS["RoadStraight"]["root"]


def operator_is_available(operator):
    try:
        operator.get_rna_type()
        return True
    except (AttributeError, RuntimeError):
        return False


def select_tile_for_export(tile):
    bpy.ops.object.select_all(action="DESELECT")
    root = tile["root"]
    root.select_set(True)
    for obj in tile["objects"]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root


def export_tile(name, tile):
    root = tile["root"]
    display_location = root.location.copy()
    root.location = (0.0, 0.0, 0.0)
    select_tile_for_export(tile)

    fbx_path = MODEL_DIRECTORY / (name + ".fbx")
    obj_path = MODEL_DIRECTORY / (name + "_OBJ.obj")
    if operator_is_available(bpy.ops.export_scene.fbx):
        bpy.ops.export_scene.fbx(
            filepath=str(fbx_path),
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
        print("Exported FBX:", fbx_path)
    elif operator_is_available(bpy.ops.wm.obj_export):
        bpy.ops.wm.obj_export(
            filepath=str(obj_path),
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
        print("Exported OBJ fallback:", obj_path)
    else:
        root.location = display_location
        raise RuntimeError("No supported model exporter. Use a Blender build with FBX or built-in OBJ export.")

    root.location = display_location


def export_all():
    SOURCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_DIRECTORY.mkdir(parents=True, exist_ok=True)
    # Save the source with the complete preview arrangement before repositioning
    # individual roots at the origin for clean, centered model exports.
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE_PATH))
    for name, tile in TILE_ASSETS.items():
        export_tile(name, tile)
    print("Created Blender source:", SOURCE_PATH)


def main():
    clear_scene()
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    build_all_tiles()
    add_preview_setup(bpy.context.scene)
    export_all()


main()
