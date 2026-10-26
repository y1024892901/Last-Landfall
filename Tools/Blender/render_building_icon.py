"""Render a model-derived, square in-game icon from the currently opened blend."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def argv_after_separator():
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def move_to_collection(obj, collection):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def make_material(name, color, roughness=0.82):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader is not None:
        shader.inputs["Base Color"].default_value = color
        shader.inputs["Roughness"].default_value = roughness
    return material


def aim_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_bounds(mesh_objects):
    corners = []
    for obj in mesh_objects:
        for corner in obj.bound_box:
            corners.append(obj.matrix_world @ Vector(corner))
    if not corners:
        raise RuntimeError("No renderable mesh objects were found in the source scene")
    mins = Vector((min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners)))
    maxs = Vector((max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners)))
    return mins, maxs, corners


def add_stage(scene, mins, maxs):
    center = (mins + maxs) * 0.5
    span_x = max(maxs.x - mins.x, 1.0)
    span_y = max(maxs.y - mins.y, 1.0)
    span_z = max(maxs.z - mins.z, 1.0)
    tile_size = max(span_x, span_y, 2.4) * 1.08
    tile_thickness = max(tile_size * 0.028, 0.075)
    tile_top = mins.z - max(tile_thickness * 0.28, 0.025)

    studio = bpy.data.collections.new("IconRender_Studio")
    scene.collection.children.link(studio)

    side_material = make_material("Icon Tile | deep teal edge", (0.025, 0.065, 0.075, 1.0))
    top_material = make_material("Icon Tile | sea-glass surface", (0.06, 0.15, 0.17, 1.0))
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(center.x, center.y, tile_top - tile_thickness * 0.5),
    )
    tile = bpy.context.object
    tile.name = "IconRender_TealDisplayTile"
    tile.dimensions = (tile_size, tile_size, tile_thickness)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to_collection(tile, studio)
    tile.data.materials.clear()
    tile.data.materials.append(side_material)
    tile.data.materials.append(top_material)
    for polygon in tile.data.polygons:
        polygon.material_index = 1 if polygon.normal.z > 0.999 else 0
    bevel = tile.modifiers.new("Soft tile edge", "BEVEL")
    bevel.width = min(tile_thickness * 0.22, tile_size * 0.018)
    bevel.segments = 3
    bevel.profile = 0.5

    # Capture the display tile's evaluated bounds as part of the icon framing.
    bpy.context.view_layer.update()
    tile_corners = [tile.matrix_world @ Vector(corner) for corner in tile.bound_box]
    all_corners = [
        *[obj.matrix_world @ Vector(corner) for obj in bpy.context.scene.objects
          if obj.type == "MESH" and obj is not tile and not obj.hide_render
          for corner in obj.bound_box],
        *tile_corners,
    ]
    return center, span_x, span_y, span_z, tile_size, all_corners


def add_studio_lighting(scene, center, scale):
    studio = bpy.data.collections.get("IconRender_Studio")
    world = bpy.data.worlds.new("IconRender_CharcoalWorld")
    world.use_nodes = True
    if world.node_tree is None:
        world.node_tree = bpy.data.node_groups.new("IconRender_WorldNodes", "ShaderNodeTree")
    nodes = world.node_tree.nodes
    background = next((node for node in nodes if node.type == "BACKGROUND"), None)
    if background is None:
        background = nodes.new("ShaderNodeBackground")
    output = next((node for node in nodes if node.type == "OUTPUT_WORLD"), None)
    if output is None:
        output = nodes.new("ShaderNodeOutputWorld")
    if not any(link.from_node == background and link.to_node == output for link in world.node_tree.links):
        world.node_tree.links.new(background.outputs["Background"], output.inputs["Surface"])
    background.inputs["Color"].default_value = (0.045, 0.055, 0.062, 1.0)
    background.inputs["Strength"].default_value = 0.9
    scene.world = world

    sun_data = bpy.data.lights.new("IconRender_SunData", "SUN")
    sun = bpy.data.objects.new("IconRender_Sun", sun_data)
    studio.objects.link(sun)
    sun_data.energy = 2.4
    sun.rotation_euler = (math.radians(28), math.radians(-18), math.radians(-25))

    key_data = bpy.data.lights.new("IconRender_KeyData", "AREA")
    key = bpy.data.objects.new("IconRender_Key", key_data)
    studio.objects.link(key)
    key.location = center + Vector((-0.75 * scale, -0.9 * scale, 1.4 * scale))
    key_data.energy = 420.0 * (scale / 6.0) ** 2
    key_data.shape = "DISK"
    key_data.size = 1.4 * scale
    aim_at(key, center)

    fill_data = bpy.data.lights.new("IconRender_FillData", "AREA")
    fill = bpy.data.objects.new("IconRender_Fill", fill_data)
    studio.objects.link(fill)
    fill.location = center + Vector((-0.4 * scale, 0.85 * scale, 1.0 * scale))
    fill_data.energy = 260.0 * (scale / 6.0) ** 2
    fill_data.shape = "DISK"
    fill_data.size = 1.8 * scale
    aim_at(fill, center)

    rim_data = bpy.data.lights.new("IconRender_RimData", "AREA")
    rim = bpy.data.objects.new("IconRender_Rim", rim_data)
    studio.objects.link(rim)
    rim.location = center + Vector((1.1 * scale, -0.25 * scale, 0.9 * scale))
    rim_data.energy = 290.0 * (scale / 6.0) ** 2
    rim_data.shape = "DISK"
    rim_data.size = 1.6 * scale
    aim_at(rim, center)


def camera_frame(scene, corners, center, scale):
    direction = Vector((1.0, -1.28, 0.88)).normalized()
    camera_data = bpy.data.cameras.new("IconRender_CameraData")
    camera = bpy.data.objects.new("IconRender_Camera", camera_data)
    bpy.data.collections["IconRender_Studio"].objects.link(camera)
    target = center.copy()
    camera.location = target + direction * (scale * 3.4)
    aim_at(camera, target)
    camera_data.type = "ORTHO"
    camera_data.lens = 50.0
    camera_data.clip_start = 0.01
    camera_data.clip_end = max(250.0, scale * 20.0)
    scene.camera = camera

    # Center the projected model and tile together, then fit the complete icon.
    rotation = camera.rotation_euler.to_matrix()
    projected = [rotation.inverted() @ (point - camera.location) for point in corners]
    left = min(point.x for point in projected)
    right = max(point.x for point in projected)
    bottom = min(point.y for point in projected)
    top = max(point.y for point in projected)
    offset = rotation @ Vector(((left + right) * 0.5, (bottom + top) * 0.5, 0.0))
    camera.location += offset
    camera_data.ortho_scale = max(right - left, top - bottom) * 1.13
    return camera


def render_icon(output_dir):
    source_path = Path(bpy.data.filepath)
    if not source_path.is_file():
        raise RuntimeError("Open a saved Blender model before running this script")

    output_name = source_path.stem
    if output_name == "DirtRoadTiles_DeepSeek":
        output_name = "RoadTiles_DeepSeek"
    elif output_name == "WaterStorageTank":
        output_name = "WaterStorageTank_DeepSeek"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / (output_name + ".png")

    scene = bpy.context.scene
    model_collection = bpy.data.collections.get(source_path.stem)
    if model_collection is None:
        candidates = [collection for collection in bpy.data.collections if any(obj.type == "MESH" for obj in collection.all_objects)]
        if not candidates:
            raise RuntimeError("No model collection with mesh objects was found")
        model_collection = max(candidates, key=lambda collection: sum(obj.type == "MESH" for obj in collection.all_objects))
    if source_path.stem == "DirtRoadTiles_DeepSeek":
        road_layout = {
            "DirtRoadStraight": (-1.15, 0.58),
            "DirtRoadCorner": (0.0, 0.58),
            "DirtRoadTee": (1.15, 0.58),
            "DirtRoadCross": (-0.575, -0.58),
            "DirtRoadEnd": (0.575, -0.58),
        }
        for root_name, (x, y) in road_layout.items():
            root = model_collection.objects.get(root_name)
            if root is None:
                raise RuntimeError(f"Road kit is missing tile root {root_name!r}")
            root.location.x = x
            root.location.y = y
    mesh_objects = [obj for obj in model_collection.all_objects if obj.type == "MESH" and not obj.hide_render]
    if not mesh_objects:
        raise RuntimeError(f"Model collection {model_collection.name!r} has no visible mesh objects")
    model_set = set(model_collection.all_objects)
    for obj in scene.objects:
        if obj not in model_set:
            obj.hide_render = True
    for material in bpy.data.materials:
        if not material.use_nodes:
            material.use_nodes = True

    bpy.context.view_layer.update()
    mins, maxs, _ = world_bounds(mesh_objects)
    center, span_x, span_y, span_z, tile_size, corners = add_stage(scene, mins, maxs)
    scene_scale = max(span_x, span_y, span_z, tile_size, 2.4)
    add_studio_lighting(scene, center, scene_scale)
    camera_frame(scene, corners, center + Vector((0.0, 0.0, span_z * 0.04)), scene_scale)

    available_engines = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys()
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in available_engines else "BLENDER_EEVEE"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 18
    scene.render.film_transparent = False
    scene.render.filepath = str(output_path)
    scene.render.use_file_extension = True
    scene.view_settings.view_transform = "Standard"
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 48

    bpy.ops.render.render(write_still=True)
    print(
        "ICON_RENDER_OK",
        output_name,
        "collection=" + model_collection.name,
        "meshes=" + str(len(mesh_objects)),
        "bounds=" + "x".join(f"{value:.3f}" for value in (span_x, span_y, span_z)),
        "path=" + str(output_path),
    )


arguments = argv_after_separator()
if len(arguments) != 1:
    raise RuntimeError("Usage: blender --background MODEL.blend --python render_building_icon.py -- OUTPUT_DIRECTORY")
render_icon(Path(arguments[0]).resolve())
