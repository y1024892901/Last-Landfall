"""Render assistant-created scenario building assets from six orthographic views.

Run with Blender 5.2:
    blender --background --python Tools/Blender/render_scenario_building_views.py

This reads the generated .blend files without modifying them. Raw renders are
written to Art/References/ScenarioBuildingViews/_renders for contact-sheet
composition by Tools/Blender/compose_scenario_building_views.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
ART_SOURCE = ROOT / "Assets/LastLandfall/Art/Source"
MANIFEST = ROOT / "Assets/LastLandfall/Art/Previews/Buildings/ScenarioBuildings_Manifest.json"
OUTPUT = ROOT / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"
SIZE = 512

VIEWS = {
    "Front": Vector((0, -1, 0)),
    "Back": Vector((0, 1, 0)),
    "Left": Vector((-1, 0, 0)),
    "Right": Vector((1, 0, 0)),
    "Top": Vector((0, 0, 1)),
    "Iso": Vector((1, -1, 0.78)).normalized(),
}


def object_world_bounds(objects):
    corners = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        if obj.type != "MESH":
            continue
        corners.extend(evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box)
    if not corners:
        raise RuntimeError("No mesh objects found in the asset collection")
    low = Vector(tuple(min(point[i] for point in corners) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in corners) for i in range(3)))
    return low, high


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    principled = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = (*color, 1.0)
    principled.inputs["Roughness"].default_value = 0.86
    return mat


def create_camera(scene, name, target, direction, distance, ortho_scale):
    camera_data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = target + direction.normalized() * distance
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = ortho_scale
    scene.camera = camera
    return camera


def create_ground_and_lights(scene, target, span, ground_z):
    bpy.ops.mesh.primitive_plane_add(size=span * 5.0, location=(target.x, target.y, ground_z - 0.045))
    ground = bpy.context.object
    ground.name = "Inspection ground (render only)"
    ground.data.materials.append(material("Inspection ground | warm gray", (0.63, 0.63, 0.59)))

    world = bpy.data.worlds.new("Scenario building inspection world")
    world.use_nodes = True
    world.node_tree.nodes.clear()
    bg = world.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.46, 0.49, 0.48, 1.0)
    bg.inputs["Strength"].default_value = 0.45
    output = world.node_tree.nodes.new("ShaderNodeOutputWorld")
    world.node_tree.links.new(bg.outputs["Background"], output.inputs["Surface"])
    scene.world = world

    for name, offset, power, size in (
        ("Inspection key", Vector((-0.8, -1.0, 1.65)), 2200, span * 1.15),
        ("Inspection fill", Vector((1.1, 0.8, 1.0)), 1050, span * 1.0),
    ):
        light_data = bpy.data.lights.new(name, "AREA")
        light = bpy.data.objects.new(name, light_data)
        bpy.context.scene.collection.objects.link(light)
        light.location = target + offset * span
        light.data.energy = power
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()


def render_asset(asset):
    blend_path = ART_SOURCE / asset["group"] / (asset["id"] + ".blend")
    if not blend_path.exists():
        print("Missing source file; skipped:", blend_path)
        return

    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    scene = bpy.context.scene
    collection = bpy.data.collections.get(asset["id"])
    if collection is None:
        raise RuntimeError(f"Missing collection {asset['id']} in {blend_path}")

    asset_objects = set(collection.all_objects)
    for obj in bpy.data.objects:
        if obj not in asset_objects:
            obj.hide_render = True

    low, high = object_world_bounds(asset_objects)
    target = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, high.z - low.z, 1.0)
    ortho = span * 1.38

    # Hide old preview cameras/lights and use a consistent inspection setup.
    create_ground_and_lights(scene, target, span, low.z)
    camera = create_camera(scene, "Inspection camera", target, VIEWS["Iso"], span * 3.0, ortho)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.render.resolution_x = SIZE
    scene.render.resolution_y = SIZE
    scene.render.resolution_percentage = 100
    scene.camera.data.lens = 50
    scene.render.image_settings.compression = 18

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for view_name, direction in VIEWS.items():
        # The same camera object is repositioned so all views share framing.
        camera.location = target + direction.normalized() * span * 3.0
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = ortho
        out = OUTPUT / f"{asset['id']}_{view_name}.png"
        scene.render.filepath = str(out)
        bpy.ops.render.render(write_still=True)
        print("Rendered:", out)


def main():
    assets = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for asset in assets:
        render_asset(asset)
    print("Six-view inspection renders finished:", OUTPUT)


if __name__ == "__main__":
    main()
