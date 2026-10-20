# -*- coding: utf-8 -*-
"""Create a separate grass-surface preview from the Gate17 island assembly."""
from __future__ import annotations

import math
from pathlib import Path

import bpy


ROOT = Path(r"D:\Last Landfall")
OUT = ROOT / "work" / "island_final_candidate"
BASE_BLEND = OUT / "Assets_Generated" / "LastLandfall_Island_Foliage_Assembly.blend"
TEXTURE_PATH = OUT / "Textures" / "Grass_Surface_Albedo_Concept.png"
SCENE_PATH = OUT / "Assets_Generated" / "LastLandfall_Island_GrassTexture_Preview.blend"
PREVIEW_PATH = OUT / "Previews_Generated" / "Gate18_GrassTexture_Coverage.png"
UV_NAME = "Grass_Albedo_Planar"
TILES_ACROSS_ISLAND = 12.0


def find_terrain():
    return next(obj for obj in bpy.data.objects if obj.name.startswith("IslandReference_V2"))


def add_planar_uv(mesh):
    layer = mesh.uv_layers.get(UV_NAME) or mesh.uv_layers.new(name=UV_NAME)
    min_x = min(v.co.x for v in mesh.vertices)
    max_x = max(v.co.x for v in mesh.vertices)
    min_y = min(v.co.y for v in mesh.vertices)
    max_y = max(v.co.y for v in mesh.vertices)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
            u = (vertex.co.x - min_x) / span_x * TILES_ACROSS_ISLAND
            v = (vertex.co.y - min_y) / span_y * TILES_ACROSS_ISLAND
            layer.data[loop_index].uv = (u, v)
    return layer


def get_principled(material):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    principled = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if principled is None:
        principled = nodes.new("ShaderNodeBsdfPrincipled")
    return principled


def make_grass_material(image):
    material = bpy.data.materials.new("Grass_Surface_Albedo_Concept")
    material.diffuse_color = (0.28, 0.37, 0.12, 1.0)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (520, 60)
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (260, 60)
    principled.inputs["Roughness"].default_value = 0.92
    uv = nodes.new("ShaderNodeUVMap")
    uv.uv_map = UV_NAME
    uv.location = (-420, 60)
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.extension = "REPEAT"
    texture.interpolation = "Linear"
    texture.location = (-180, 60)
    links.new(uv.outputs["UV"], texture.inputs["Vector"])
    links.new(texture.outputs["Color"], principled.inputs["Base Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_rock_transition_material(image, original_color):
    material = bpy.data.materials.new("Rock_Grass_Slope_Transition_Concept")
    material.diffuse_color = original_color
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (720, 80)
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (480, 80)
    principled.inputs["Roughness"].default_value = 0.88

    uv = nodes.new("ShaderNodeUVMap")
    uv.uv_map = UV_NAME
    uv.location = (-600, 180)
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.extension = "REPEAT"
    texture.interpolation = "Linear"
    texture.location = (-380, 180)

    geometry = nodes.new("ShaderNodeNewGeometry")
    geometry.location = (-600, -160)
    separate = nodes.new("ShaderNodeSeparateXYZ")
    separate.location = (-380, -160)
    slope = nodes.new("ShaderNodeMapRange")
    slope.location = (-160, -160)
    slope.clamp = True
    slope.inputs["From Min"].default_value = 0.28
    slope.inputs["From Max"].default_value = 0.78
    slope.inputs["To Min"].default_value = 0.0
    slope.inputs["To Max"].default_value = 0.88

    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.location = (100, 100)
    mix.inputs["Color1"].default_value = original_color

    links.new(uv.outputs["UV"], texture.inputs["Vector"])
    links.new(geometry.outputs["Normal"], separate.inputs["Vector"])
    links.new(separate.outputs["Z"], slope.inputs["Value"])
    links.new(slope.outputs["Result"], mix.inputs["Fac"])
    links.new(texture.outputs["Color"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], principled.inputs["Base Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return material


def setup_render(scene):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1350
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.compression = 18
    scene.render.filepath = str(PREVIEW_PATH)
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.3

    world = scene.world or bpy.data.worlds.new("GrassTexturePreview_World")
    scene.world = world
    world.use_nodes = True
    background = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    background.inputs["Color"].default_value = (0.045, 0.075, 0.10, 1.0)
    background.inputs["Strength"].default_value = 0.5

    ocean = bpy.data.objects.get("Preview_Ocean (not exported)")
    if ocean and ocean.data.materials:
        ocean_material = ocean.data.materials[0]
        ocean_material.use_nodes = True
        ocean_bsdf = next(n for n in ocean_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        ocean_bsdf.inputs["Base Color"].default_value = (0.035, 0.17, 0.24, 1.0)
        ocean_bsdf.inputs["Roughness"].default_value = 0.38

    sun_data = bpy.data.lights.new("GrassTexturePreview_Sun", type="SUN")
    sun_data.energy = 2.6
    sun_data.angle = math.radians(18)
    sun = bpy.data.objects.new("GrassTexturePreview_Sun", sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(24), math.radians(-28), math.radians(-32))

    camera = scene.camera
    if camera is None:
        raise RuntimeError("Gate17 scene has no camera")
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 74.0


def main():
    if not BASE_BLEND.is_file():
        raise FileNotFoundError(BASE_BLEND)
    if not TEXTURE_PATH.is_file():
        raise FileNotFoundError(TEXTURE_PATH)

    bpy.ops.wm.open_mainfile(filepath=str(BASE_BLEND))
    terrain = find_terrain()
    add_planar_uv(terrain.data)
    image = bpy.data.images.load(str(TEXTURE_PATH), check_existing=True)
    image.colorspace_settings.name = "sRGB"
    image.pack()

    old_materials = list(terrain.data.materials)
    if len(old_materials) < 2:
        raise RuntimeError(f"Expected terrain grass and rock material slots; got {len(old_materials)}")
    original_rock_color = tuple(old_materials[1].diffuse_color)
    grass_material = make_grass_material(image)
    transition_material = make_rock_transition_material(image, original_rock_color)
    terrain.data.materials[0] = grass_material
    terrain.data.materials[1] = transition_material
    terrain.data.materials[2].name = "Wet_Rock_Kept_Exposed"

    scene = bpy.context.scene
    setup_render(scene)

    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.shading.type = "MATERIAL"

    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCENE_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_PATH), compress=True)
    print(f"PREVIEW={PREVIEW_PATH}")
    print(f"SCENE={SCENE_PATH}")
    print("TEXTURE=Grass_Surface_Albedo_Concept.png")


if __name__ == "__main__":
    main()
