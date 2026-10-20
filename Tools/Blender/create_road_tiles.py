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
import json

import bpy
from mathutils import Vector


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
SOURCE_PATH = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Infrastructure/RoadTiles.blend"
MODEL_DIRECTORY = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Infrastructure"

TILE_SIZE = 1.0
ROAD_WIDTH = 0.50
BOARD_WIDTH = 0.458
BASE_THICKNESS = 0.054
BOARD_THICKNESS = 0.044
BOARD_TOP_Z = 0.083
BOARD_TARGET_LENGTH = 0.115

TILE_PORTS = {
    "RoadStraight": {"North", "South"},
    "RoadCorner": {"South", "East"},
    "RoadTee": {"West", "East", "South"},
    "RoadCross": {"North", "East", "South", "West"},
    "RoadEnd": {"South"},
}
CARDINALS = ("North", "East", "South", "West")

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


def add_cube(name, location, dimensions, material, bevel=0.006):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    bevel_width = min(bevel, min(dimensions) * 0.20)
    if bevel_width > 0.0005:
        modifier = obj.modifiers.new("Soft salt-worn edges", "BEVEL")
        modifier.width = bevel_width
        modifier.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    ASSET_OBJECTS.append(obj)
    return obj


def material_for_board(index, materials):
    # Repeat a legible weathering pattern; the occasional metal plate reads as a repair.
    if index % 7 == 4:
        return materials["patch"]
    return materials["wood_light"] if index % 3 == 0 else materials["wood_mid"]


def add_run(axis, start, end, materials, board_offset=0):
    """Build one arm from crosswise deck planks on three iron-reinforced stringers."""
    if end <= start:
        raise ValueError("Road run end must be greater than its start")
    length = end - start
    along_center = (start + end) * 0.5
    if axis == "y":
        add_cube("Tar-dark road underlay", (0.0, along_center, BASE_THICKNESS * 0.5),
                 (ROAD_WIDTH, length, BASE_THICKNESS), materials["underlay"], bevel=0.003)
        for x in (-0.184, 0.0, 0.184):
            add_cube("Longitudinal timber stringer", (x, along_center, 0.050),
                     (0.052, length, 0.055), materials["support"], bevel=0.004)
        rail_x = ROAD_WIDTH * 0.5 - 0.014
        rail_dims = (0.026, length, 0.020)
        rail_centers = ((-rail_x, along_center, 0.105), (0.0, along_center, 0.105), (rail_x, along_center, 0.105))
    elif axis == "x":
        add_cube("Tar-dark road underlay", (along_center, 0.0, BASE_THICKNESS * 0.5),
                 (length, ROAD_WIDTH, BASE_THICKNESS), materials["underlay"], bevel=0.003)
        for y in (-0.184, 0.0, 0.184):
            add_cube("Longitudinal timber stringer", (along_center, y, 0.050),
                     (length, 0.052, 0.055), materials["support"], bevel=0.004)
        rail_y = ROAD_WIDTH * 0.5 - 0.014
        rail_dims = (length, 0.026, 0.020)
        rail_centers = ((along_center, -rail_y, 0.105), (along_center, 0.0, 0.105), (along_center, rail_y, 0.105))
    else:
        raise ValueError("Road axis must be 'x' or 'y'")

    for center in rail_centers:
        add_cube("Riveted sea-worn iron strap", center, rail_dims, materials["edge"], bevel=0.003)

    segment_count = max(1, int(math.ceil(length / BOARD_TARGET_LENGTH)))
    segment_length = length / segment_count
    gap = min(0.008, segment_length * 0.06)
    for index in range(segment_count):
        along = start + (index + 0.5) * segment_length
        # The first and last deck boards meet the cell edge exactly. Interior
        # seams stay narrow and consistent so neighboring tiles join cleanly.
        plank_gap = 0.0 if index in (0, segment_count - 1) else gap
        plank_length = max(0.025, segment_length - plank_gap)
        z = BOARD_TOP_Z + (0.001 if (index + board_offset) % 4 == 0 else 0.0)
        if axis == "y":
            location = (0.0, along, z)
            dimensions = (BOARD_WIDTH, plank_length, BOARD_THICKNESS)
        else:
            location = (along, 0.0, z)
            dimensions = (plank_length, BOARD_WIDTH, BOARD_THICKNESS)
        board_material = material_for_board(index + board_offset, materials)
        add_cube("Cross-laid salt-worn deck plank", location, dimensions, board_material, bevel=0.004)


def add_junction_patch(materials):
    """Give bends and intersections a reinforced, flush-fitting plank hub."""
    add_cube("Junction underlay", (0.0, 0.0, BASE_THICKNESS * 0.5),
             (ROAD_WIDTH, ROAD_WIDTH, BASE_THICKNESS), materials["underlay"], bevel=0.003)
    patch_size = 0.226
    centers = (
        (-0.116, -0.116, materials["wood_mid"]),
        (0.116, -0.116, materials["wood_light"]),
        (-0.116, 0.116, materials["wood_dark"]),
        (0.116, 0.116, materials["wood_mid"]),
    )
    for x, y, material in centers:
        add_cube("Junction repair plank panel", (x, y, BOARD_TOP_Z),
                 (patch_size, patch_size, BOARD_THICKNESS), material, bevel=0.004)
    for x, y, dimensions in (
        (0.0, -0.12, (0.016, 0.22, 0.020)),
        (0.0, 0.12, (0.016, 0.22, 0.020)),
        (-0.12, 0.0, (0.22, 0.016, 0.020)),
        (0.12, 0.0, (0.22, 0.016, 0.020)),
    ):
        add_cube("Junction iron reinforcement", (x, y, 0.105), dimensions, materials["edge"], bevel=0.003)


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
        "underlay": make_material("Road | tar-dark timber underlay", (0.105, 0.094, 0.078)),
        "support": make_material("Road | reclaimed support timber", (0.205, 0.158, 0.112)),
        "wood_dark": make_material("Road | storm-dark deck boards", (0.235, 0.185, 0.132)),
        "wood_mid": make_material("Road | salt-worn cedar boards", (0.365, 0.270, 0.185)),
        "wood_light": make_material("Road | faded cedar repairs", (0.485, 0.370, 0.255)),
        "edge": make_material("Road | corroded sea-green iron straps", (0.185, 0.285, 0.285), metallic=0.48),
        "patch": make_material("Road | rusted repair plate", (0.43, 0.205, 0.125), metallic=0.28),
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


PORT_VECTORS = {
    "North": (0, 1),
    "East": (1, 0),
    "South": (0, -1),
    "West": (-1, 0),
}


def rotate_port(port, degrees):
    x, y = PORT_VECTORS[port]
    for _ in range((degrees % 360) // 90):
        # Matches BuildPlacementPrototype.RotateDirection and Unity's +Y yaw.
        x, y = y, -x
    return next(name for name, vector in PORT_VECTORS.items() if vector == (x, y))


def shape_for_neighbor_mask(mask):
    ports = {CARDINALS[index] for index in range(4) if mask & (1 << index)}
    count = len(ports)
    if count == 4:
        return "RoadCross", 0
    if count == 3:
        source = {"West", "East", "South"}
        return "RoadTee", next(rotation for rotation in (0, 90, 180, 270)
                                if {rotate_port(port, rotation) for port in source} == ports)
    if count == 2:
        if ports in ({"North", "South"}, {"East", "West"}):
            source = {"North", "South"}
            return "RoadStraight", next(rotation for rotation in (0, 90)
                                        if {rotate_port(port, rotation) for port in source} == ports)
        source = {"South", "East"}
        return "RoadCorner", next(rotation for rotation in (0, 90, 180, 270)
                                   if {rotate_port(port, rotation) for port in source} == ports)
    if count == 1:
        port = next(iter(ports))
        return "RoadEnd", next(rotation for rotation in (0, 90, 180, 270)
                                if rotate_port("South", rotation) == port)
    return "RoadStraight", 0


def surface_at_edge(tile_name, direction, sample_count=25):
    """Check real Blender mesh geometry at a cell edge, above the dark underlay."""
    root = TILE_ASSETS[tile_name]["root"]
    bpy.context.view_layer.update()
    road_children = [obj for obj in root.children_recursive if obj.type == "MESH"]
    if direction in ("West", "East"):
        edge = -0.497 if direction == "West" else 0.497
        points = [(edge, -0.19 + 0.38 * index / (sample_count - 1), 0.30)
                  for index in range(sample_count)]
    else:
        edge = -0.497 if direction == "South" else 0.497
        points = [(-0.19 + 0.38 * index / (sample_count - 1), edge, 0.30)
                  for index in range(sample_count)]

    covered = 0
    for x, y, z in points:
        ray_origin_world = root.matrix_world @ Vector((x, y, z))
        found_deck = False
        for obj in road_children:
            inverse = obj.matrix_world.inverted()
            ray_origin_local = inverse @ ray_origin_world
            ray_direction_local = inverse.to_3x3() @ Vector((0.0, 0.0, -1.0))
            hit, location, _normal, _face = obj.ray_cast(ray_origin_local, ray_direction_local)
            if hit:
                hit_world = obj.matrix_world @ location
                if hit_world.z >= BOARD_TOP_Z + BOARD_THICKNESS * 0.5 - 0.006:
                    found_deck = True
                    break
        if found_deck:
            covered += 1
    return covered, sample_count


def validate_road_topology():
    """Audit four physical edge ports plus all 16 runtime neighbor masks."""
    actual_ports = {}
    edge_samples = {}
    for tile_name, expected in TILE_PORTS.items():
        detected = set()
        edge_samples[tile_name] = {}
        for direction in CARDINALS:
            covered, total = surface_at_edge(tile_name, direction)
            edge_samples[tile_name][direction] = {"covered": covered, "samples": total}
            if covered >= total - 2:
                detected.add(direction)
        if detected != expected:
            raise RuntimeError(
                "%s mesh ports mismatch: expected %s, got %s (%s)" %
                (tile_name, sorted(expected), sorted(detected), edge_samples[tile_name])
            )
        actual_ports[tile_name] = detected

    masks = []
    for mask in range(16):
        tile_name, rotation = shape_for_neighbor_mask(mask)
        neighbors = {CARDINALS[index] for index in range(4) if mask & (1 << index)}
        rotated_ports = {rotate_port(port, rotation) for port in actual_ports[tile_name]}
        if neighbors and rotated_ports != neighbors:
            raise RuntimeError(
                "Neighbor mask %04b selects %s at %d degrees, exposing %s instead of %s" %
                (mask, tile_name, rotation, sorted(rotated_ports), sorted(neighbors))
            )
        masks.append({
            "neighbor_mask_north_east_south_west": format(mask, "04b"),
            "shape": tile_name,
            "rotation_degrees": rotation,
            "connected_edges": sorted(neighbors),
            "model_open_edges": sorted(rotated_ports),
        })

    joins = []
    opposite = {"North": "South", "East": "West", "South": "North", "West": "East"}
    for direction in CARDINALS:
        other_edge = opposite[direction]
        join_tile = "RoadStraight" if direction in ("North", "South") else "RoadTee"
        left = surface_at_edge(join_tile, direction)
        right = surface_at_edge(join_tile, other_edge)
        if left[0] < left[1] - 2 or right[0] < right[1] - 2:
            raise RuntimeError("Two-cell straight join failed at %s / %s" % (direction, other_edge))
        joins.append({
            "direction": direction,
            "neighbor_edge": other_edge,
            "edge_module": join_tile,
            "source_deck_samples": left[0],
            "neighbor_deck_samples": right[0],
            "passed": True,
        })

    report = {
        "road_kit": "Last Landfall reclaimed timber modular roads",
        "tile_size_m": TILE_SIZE,
        "lane_width_m": ROAD_WIDTH,
        "edge_samples_per_side": 25,
        "model_ports": {name: sorted(ports) for name, ports in actual_ports.items()},
        "edge_surface_samples": edge_samples,
        "two_cell_directional_joins": joins,
        "runtime_neighbor_masks": masks,
        "result": "PASS",
    }
    report_path = PROJECT_ROOT / "Assets/LastLandfall/Art/Previews/Infrastructure/RoadTiles_Connectivity_QA.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Road connectivity QA: PASS (5 modules, 4 directions, 16 neighbor masks)")
    print("Road connectivity report:", report_path)


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
    validate_road_topology()
    add_preview_setup(bpy.context.scene)
    export_all()


main()
