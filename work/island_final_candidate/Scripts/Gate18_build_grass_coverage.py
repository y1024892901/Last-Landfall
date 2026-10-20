# -*- coding: utf-8 -*-
"""Build a separate, Unity-friendly grass coverage and clustered-tree candidate."""
from __future__ import annotations

import datetime as dt
import json
import math
import random
from pathlib import Path
from typing import Any

import bpy
from mathutils import Euler, Vector


ROOT = Path(r"D:\Last Landfall")
if "__file__" in globals():
    for parent in Path(__file__).resolve().parents:
        if (parent / "Assets" / "LastLandfall").is_dir():
            ROOT = parent
            break
OUT = ROOT / "work" / "island_final_candidate"
BASE_BLEND = OUT / "Assets_Generated" / "LastLandfall_Island_Foliage_Assembly.blend"
TEXTURE_PATH = OUT / "Textures" / "Grass_Surface_Albedo_Concept.png"
INSPECTED = OUT / "Assets_Inspected"
SCENE_PATH = OUT / "Assets_Generated" / "LastLandfall_Island_GrassCoverage_Gate18.blend"
FBX_PATH = OUT / "Assets_Generated" / "LastLandfall_Island_GrassCoverage_Gate18.fbx"
PREVIEW_PATH = OUT / "Previews_Generated" / "Gate18_GrassCoverage_Zones_TreeClusters.png"
REPORT_PATH = OUT / "Reports_Generated" / "Gate18_grass_coverage_qa.json"
HANDOFF_PATH = OUT / "Gate18_GrassCoverage_Handoff.md"

TERRAIN_SCALE = 0.02
TERRAIN_Z_OFFSET = -0.92
WATER_Z = -0.92
UV_NAME = "Grass_Albedo_Planar"
TEXTURE_TILES = 2.6

# Future building masks are deliberately empty in this preview. Add a rotated
# rectangle per building when its footprint is known, then rerun this script.
BUILDING_FOOTPRINTS_M: list[dict[str, float | str]] = []

# Five groves frame the build meadow while leaving the central building zone and
# southwest landing corridor open to tall vegetation.
TREE_GROVES = [
    {"name": "Northwest_Grove", "center": (-16.0, 12.0), "radius": 6.2,
     "assets": ["Pine_Windbent_Tall_A", "Pine_Windbent_Short_B", "Broadleaf_Coastal_A",
                "Pine_Windbent_Tall_A", "Broadleaf_Coastal_B", "Pine_Windbent_Short_B", "Broadleaf_Coastal_A"]},
    {"name": "North_Ridge_Grove", "center": (0.0, 17.0), "radius": 5.2,
     "assets": ["Pine_Windbent_Tall_A", "Pine_Windbent_Short_B", "Pine_Windbent_Tall_A",
                "Broadleaf_Coastal_B", "Pine_Windbent_Short_B"]},
    {"name": "East_Grove", "center": (17.0, 6.0), "radius": 5.5,
     "assets": ["Pine_Windbent_Tall_A", "Broadleaf_Coastal_A", "Pine_Windbent_Short_B",
                "Broadleaf_Coastal_B", "Pine_Windbent_Tall_A", "Pine_Windbent_Short_B", "Broadleaf_Coastal_A"]},
    {"name": "West_Shelf_Grove", "center": (-18.5, -1.0), "radius": 4.4,
     "assets": ["Broadleaf_Coastal_A", "Broadleaf_Coastal_B", "Broadleaf_Coastal_A"]},
    {"name": "South_Shelf_Grove", "center": (4.0, -22.0), "radius": 5.0,
     "assets": ["Broadleaf_Coastal_A", "Broadleaf_Coastal_B"]},
]

GRASS_PATCHES = [
    ((0.0, -1.0), 6.6), ((-16.0, 8.0), 4.8), ((0.0, 16.0), 4.2),
    ((17.0, 4.0), 4.5), ((-20.0, 1.5), 3.8), ((17.0, -11.5), 3.8),
    ((4.0, -21.0), 4.3), ((-7.0, -13.0), 4.1), ((-3.0, 10.0), 4.3),
]
MAX_GRASS_TUFTS = 280


def empty_collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for old_collection in list(obj.users_collection):
        old_collection.objects.unlink(obj)
    collection.objects.link(obj)


def terrain_object() -> bpy.types.Object:
    return next(obj for obj in bpy.data.objects if obj.name.startswith("IslandReference_V2"))


def in_reserved_zone(x: float, y: float, expanded: bool = False) -> bool:
    rx, ry = (16.5, 13.2) if expanded else (15.0, 12.0)
    central = (x / rx) ** 2 + (y / ry) ** 2 < 1.0
    margin = 1.5 if expanded else 0.0
    southwest_corridor = (-24.0 - margin < x < -8.0 + margin and -22.0 - margin < y < -5.0 + margin)
    return central or southwest_corridor


def inside_building_mask(x: float, y: float) -> bool:
    for footprint in BUILDING_FOOTPRINTS_M:
        dx, dy = x - float(footprint["x"]), y - float(footprint["y"])
        angle = math.radians(float(footprint.get("rotation_degrees", 0.0)))
        lx = dx * math.cos(angle) + dy * math.sin(angle)
        ly = -dx * math.sin(angle) + dy * math.cos(angle)
        if abs(lx) <= float(footprint["half_width_m"]) + 0.5 and abs(ly) <= float(footprint["half_depth_m"]) + 0.5:
            return True
    return False


def sample_terrain(terrain: bpy.types.Object, x: float, y: float) -> dict[str, Any] | None:
    origin = Vector((x / TERRAIN_SCALE, y / TERRAIN_SCALE, 900.0))
    hit, point, normal, face_index = terrain.ray_cast(origin, Vector((0.0, 0.0, -1.0)))
    if not hit:
        return None
    return {
        "x": x,
        "y": y,
        "z": float(point.z * TERRAIN_SCALE + TERRAIN_Z_OFFSET),
        "normal_z": float(normal.z),
        "face_index": int(face_index),
    }


def srgb_hex_to_linear(value: str) -> tuple[float, float, float, float]:
    value = value.lstrip("#")
    srgb = [int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (linear[0], linear[1], linear[2], 1.0)


def add_planar_uv(mesh: bpy.types.Mesh) -> None:
    layer = mesh.uv_layers.get(UV_NAME) or mesh.uv_layers.new(name=UV_NAME)
    min_x = min(vertex.co.x for vertex in mesh.vertices)
    max_x = max(vertex.co.x for vertex in mesh.vertices)
    min_y = min(vertex.co.y for vertex in mesh.vertices)
    max_y = max(vertex.co.y for vertex in mesh.vertices)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
            u = (vertex.co.x - min_x) / span_x * TEXTURE_TILES
            v = (vertex.co.y - min_y) / span_y * TEXTURE_TILES
            layer.data[loop_index].uv = (u, v)


def make_simple_material(name: str, color_hex: str, roughness: float = 0.92) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = srgb_hex_to_linear(color_hex)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = srgb_hex_to_linear(color_hex)
    principled.inputs["Roughness"].default_value = roughness
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_grass_material(name: str, base_hex: str, image: bpy.types.Image, tint: float) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = srgb_hex_to_linear(base_hex)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (560, 40)
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (330, 40)
    principled.inputs["Roughness"].default_value = 0.94
    uv = nodes.new("ShaderNodeUVMap")
    uv.uv_map = UV_NAME
    uv.location = (-600, 70)
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.extension = "REPEAT"
    texture.interpolation = "Linear"
    texture.location = (-390, 70)
    tint_node = nodes.new("ShaderNodeMixRGB")
    tint_node.blend_type = "MULTIPLY"
    tint_node.inputs["Fac"].default_value = 1.0
    tint_node.inputs["Color1"].default_value = srgb_hex_to_linear(base_hex)
    tint_node.location = (-120, 80)
    detail = nodes.new("ShaderNodeMixRGB")
    detail.blend_type = "MIX"
    detail.inputs["Fac"].default_value = tint
    detail.location = (100, 80)
    detail.inputs["Color1"].default_value = srgb_hex_to_linear(base_hex)
    links.new(uv.outputs["UV"], texture.inputs["Vector"])
    links.new(texture.outputs["Color"], tint_node.inputs["Color2"])
    links.new(tint_node.outputs["Color"], detail.inputs["Color2"])
    links.new(detail.outputs["Color"], principled.inputs["Base Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_rock_material() -> bpy.types.Material:
    material = bpy.data.materials.new("Exposed_Basalt_Rock")
    material.diffuse_color = srgb_hex_to_linear("#696C68")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (360, 0)
    principled.inputs["Roughness"].default_value = 0.93
    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-620, 50)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4.2
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.64
    noise.location = (-400, 50)
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = srgb_hex_to_linear("#535958")
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = srgb_hex_to_linear("#8B897B")
    ramp.location = (-130, 50)
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], principled.inputs["Base Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_wet_rock_material() -> bpy.types.Material:
    return make_simple_material("Wet_Rock_Kept_Exposed", "#384448", 0.72)


def assign_zoned_materials(terrain: bpy.types.Object, image: bpy.types.Image) -> dict[str, int]:
    add_planar_uv(terrain.data)
    mesh = terrain.data
    old_material_index = [polygon.material_index for polygon in mesh.polygons]
    materials = [
        make_grass_material("Lowland_Meadow_Grass", "#788A57", image, 0.18),
        make_grass_material("Highland_Dry_Grass", "#918B57", image, 0.12),
        make_simple_material("Coastal_Sand_And_Soil", "#A49A82", 0.96),
        make_rock_material(),
        make_wet_rock_material(),
    ]
    mesh.materials.clear()
    for material in materials:
        mesh.materials.append(material)

    counts = {material.name: 0 for material in materials}
    matrix = terrain.matrix_world
    for polygon, old_index in zip(mesh.polygons, old_material_index):
        center = matrix @ polygon.center
        normal = (matrix.to_3x3() @ polygon.normal).normalized()
        # A slow broad wave softens zone contours without adding speckled patches.
        wave = 0.45 * math.sin(center.x * 0.16 + 0.6 * math.sin(center.y * 0.13))
        wave += 0.28 * math.sin(center.y * 0.21 - center.x * 0.08)
        height = center.z + wave
        if old_index == 2:
            slot = 4
        elif height < -0.63 + wave * 0.10 and normal.z > 0.43:
            slot = 2
        elif normal.z < 0.68 + wave * 0.018 or height > 4.7 + wave:
            slot = 3
        elif height > 2.25 + wave:
            slot = 1
        else:
            slot = 0
        polygon.material_index = slot
        counts[materials[slot].name] += 1
    return counts


def import_template(asset: str, template_collection: bpy.types.Collection) -> bpy.types.Object:
    path = INSPECTED / f"{asset}.fbx"
    if not path.is_file():
        raise FileNotFoundError(path)
    before = set(bpy.data.objects)
    result = bpy.ops.import_scene.fbx(filepath=str(path), global_scale=1.0)
    if "FINISHED" not in result:
        raise RuntimeError(f"FBX import failed for {path}")
    meshes = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh found in {path}")
    template = meshes[0]
    template.name = f"TEMPLATE_{asset}"
    template.location = (0.0, 0.0, 0.0)
    template.rotation_euler = (0.0, 0.0, 0.0)
    template.scale = (1.0, 1.0, 1.0)
    template.hide_render = True
    template.hide_set(True)
    move_to_collection(template, template_collection)
    return template


def make_instance(
    template: bpy.types.Object,
    asset: str,
    point: dict[str, Any],
    collection: bpy.types.Collection,
    rng: random.Random,
    align_to_ground: bool = False,
    grove: str = "",
) -> bpy.types.Object:
    obj = template.copy()
    # Independent mesh datablocks avoid FBX exporter material-slot collisions.
    obj.data = template.data.copy()
    collection.objects.link(obj)
    obj.name = f"{asset}_Instance"
    obj.hide_render = False
    obj.hide_set(False)
    obj.location = (point["x"], point["y"], 0.0)
    if asset.startswith("Pine_"):
        scale = rng.uniform(0.87, 1.16)
    elif asset.startswith("Grass_"):
        scale = rng.uniform(0.68, 1.06)
    else:
        scale = rng.uniform(0.82, 1.22)
    obj.scale = (scale, scale, scale)
    yaw = rng.uniform(0.0, math.tau)
    if align_to_ground:
        n = Vector((0.0, 0.0, 1.0))
        n.z = max(0.76, min(1.0, float(point["normal_z"])))
        n.x = rng.uniform(-0.18, 0.18)
        n.y = rng.uniform(-0.18, 0.18)
        n.normalize()
        align = Vector((0.0, 0.0, 1.0)).rotation_difference(n)
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = align @ Euler((0.0, 0.0, yaw)).to_quaternion()
    else:
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = (rng.uniform(-0.025, 0.025), rng.uniform(-0.025, 0.025), yaw)
    bpy.context.view_layer.update()
    bottom = min((obj.matrix_world @ vertex.co).z for vertex in obj.data.vertices)
    obj.location.z += point["z"] - bottom
    obj["asset_id"] = asset
    obj["surface_z_m"] = round(point["z"], 4)
    obj["surface_normal_z"] = round(point["normal_z"], 4)
    obj["gate_source"] = "source_fbx_linked_instance"
    obj["gate_export"] = True
    if grove:
        obj["tree_grove"] = grove
    if asset.startswith("Grass_"):
        obj["grass_patch_system"] = "Gate18_dry_ground_clumps"
    return obj


def build_tree_candidates(terrain: bpy.types.Object) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    y = -25.0
    row = 0
    while y <= 22.0:
        x = -27.0 + (row % 2) * 0.45
        while x <= 27.0:
            px, py = x + 0.12 * math.sin(y * 0.2), y + 0.12 * math.cos(x * 0.17)
            if not in_reserved_zone(px, py, expanded=True):
                point = sample_terrain(terrain, px, py)
                if point and 0.12 <= point["z"] <= 5.0 and point["normal_z"] >= 0.71:
                    points.append(point)
            x += 0.82
        y += 0.82
        row += 1
    return points


def place_trees(
    terrain: bpy.types.Object,
    export_collection: bpy.types.Collection,
    template_collection: bpy.types.Collection,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], dict[str, bpy.types.Object]]:
    tree_names = {asset for grove in TREE_GROVES for asset in grove["assets"]}
    templates = {asset: import_template(asset, template_collection) for asset in sorted(tree_names)}
    points = build_tree_candidates(terrain)
    fixed = [
        (obj.location.x, obj.location.y)
        for obj in export_collection.objects
        if obj.type == "MESH" and obj.get("asset_id") not in tree_names
        and not str(obj.get("asset_id", "")).startswith("Grass_")
    ]
    used: list[tuple[float, float]] = []
    placements: list[dict[str, Any]] = []
    for grove in TREE_GROVES:
        center_x, center_y = grove["center"]
        base_radius = float(grove["radius"])
        for index, asset in enumerate(grove["assets"]):
            choices = [
                point for point in points
                if math.hypot(point["x"] - center_x, point["y"] - center_y) <= base_radius + 1.8
                and not inside_building_mask(point["x"], point["y"])
                and all(math.hypot(point["x"] - ox, point["y"] - oy) >= 2.25 for ox, oy in used)
                and all(math.hypot(point["x"] - ox, point["y"] - oy) >= 1.55 for ox, oy in fixed)
            ]
            choices.sort(key=lambda point: math.hypot(point["x"] - center_x, point["y"] - center_y) + rng.uniform(0.0, 2.0))
            if not choices:
                raise RuntimeError(f"No valid terrain point for {grove['name']} tree {index + 1} ({asset})")
            point = choices[0]
            obj = make_instance(templates[asset], asset, point, export_collection, rng, grove=grove["name"])
            used.append((point["x"], point["y"]))
            placements.append({
                "asset": asset,
                "grove": grove["name"],
                "location_m": [round(point["x"], 3), round(point["y"], 3), round(obj.location.z, 3)],
                "surface_z_m": round(point["z"], 3),
                "surface_normal_z": round(point["normal_z"], 3),
            })
    return placements, templates


def grass_density(x: float, y: float) -> float:
    strongest = 0.0
    for (cx, cy), radius in GRASS_PATCHES:
        distance = math.hypot(x - cx, y - cy)
        strongest = max(strongest, math.exp(-0.5 * (distance / radius) ** 2))
    return min(0.82, 0.035 + strongest * 0.74)


def place_grass_tufts(
    terrain: bpy.types.Object,
    export_collection: bpy.types.Collection,
    template_collection: bpy.types.Collection,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], dict[str, bpy.types.Object]]:
    assets = ["Grass_CoastalTuft_A", "Grass_CoastalTuft_B"]
    templates = {asset: import_template(asset, template_collection) for asset in assets}
    candidates: list[dict[str, Any]] = []
    for _ in range(6200):
        px = rng.uniform(-28.5, 28.0)
        py = rng.uniform(-30.5, 21.5)
        point = sample_terrain(terrain, px, py)
        if point and 0.02 <= point["z"] <= 3.85 and point["normal_z"] >= 0.775 and not inside_building_mask(px, py):
            if rng.random() < grass_density(px, py):
                candidates.append(point)
    rng.shuffle(candidates)

    # The existing broad trees stay clear of trunks, while the tufts extend
    # through the future build meadow so foundations can replace them later.
    tree_locations = [
        (obj.location.x, obj.location.y) for obj in export_collection.objects
        if obj.type == "MESH" and str(obj.get("asset_id", "")).startswith(("Pine_", "Broadleaf_"))
    ]
    selected: list[dict[str, Any]] = []
    for point in candidates:
        if any(math.hypot(point["x"] - tx, point["y"] - ty) < 0.68 for tx, ty in tree_locations):
            continue
        if any(math.hypot(point["x"] - old["x"], point["y"] - old["y"]) < 0.72 for old in selected):
            continue
        selected.append(point)
        if len(selected) >= MAX_GRASS_TUFTS:
            break

    records: list[dict[str, Any]] = []
    for index, point in enumerate(selected):
        asset = assets[0] if rng.random() < 0.56 else assets[1]
        obj = make_instance(templates[asset], asset, point, export_collection, rng, align_to_ground=True)
        records.append({
            "asset": asset,
            "location_m": [round(point["x"], 3), round(point["y"], 3), round(obj.location.z, 3)],
            "surface_z_m": round(point["z"], 3),
            "surface_normal_z": round(point["normal_z"], 3),
        })
    return records, templates


def setup_presentation(scene: bpy.types.Scene) -> None:
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
    scene.view_settings.exposure = 0.42

    world = bpy.data.worlds.new("Gate18_GrassCoverage_World")
    scene.world = world
    world.use_nodes = True
    background = next(node for node in world.node_tree.nodes if node.type == "BACKGROUND")
    background.inputs["Color"].default_value = (0.045, 0.085, 0.115, 1.0)
    background.inputs["Strength"].default_value = 0.52

    ocean = bpy.data.objects.get("Preview_Ocean (not exported)")
    if ocean:
        ocean.hide_render = False
        ocean.hide_set(False)
        if not ocean.data.materials:
            ocean.data.materials.append(make_simple_material("Preview_Ocean_Not_Exported", "#12505E", 0.37))
        else:
            mat = make_simple_material("Preview_Ocean_Not_Exported", "#12505E", 0.37)
            ocean.data.materials[0] = mat

    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    sun_data = bpy.data.lights.new("Gate18_Sun", type="SUN")
    sun_data.energy = 2.5
    sun_data.angle = math.radians(22.0)
    sun = bpy.data.objects.new("Gate18_Sun", sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(24), math.radians(-28), math.radians(-32))

    camera = scene.camera
    if camera is None:
        camera_data = bpy.data.cameras.new("Gate18_Overview_Camera")
        camera = bpy.data.objects.new("Gate18_Overview_Camera", camera_data)
        scene.collection.objects.link(camera)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 68.5
    camera.location = (72.0, -86.0, 61.0)
    target = Vector((0.0, -1.0, 1.1))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera


def export_fbx(export_collection: bpy.types.Collection) -> dict[str, Any]:
    export_objects = [
        obj for obj in export_collection.objects
        if obj.type == "MESH" and obj.get("gate_export", True)
    ]
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in export_objects:
        obj.select_set(True)
        obj.data.calc_loop_triangles()
    if export_objects:
        bpy.context.view_layer.objects.active = terrain_object()
    result = bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH), use_selection=True, global_scale=1.0,
        apply_unit_scale=True, axis_forward="-Z", axis_up="Y",
        object_types={"MESH"}, mesh_smooth_type="OFF", bake_space_transform=False,
        add_leaf_bones=False, use_mesh_modifiers=True, path_mode="COPY", embed_textures=True,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Gate18 FBX export failed: {result}")
    triangles = sum(len(obj.data.loop_triangles) for obj in export_objects)
    return {"mesh_objects": len(export_objects), "triangles": triangles, "embedded_textures": True}


def main() -> None:
    for directory in (SCENE_PATH.parent, PREVIEW_PATH.parent, REPORT_PATH.parent):
        directory.mkdir(parents=True, exist_ok=True)
    if not BASE_BLEND.is_file():
        raise FileNotFoundError(BASE_BLEND)
    if not TEXTURE_PATH.is_file():
        raise FileNotFoundError(TEXTURE_PATH)
    bpy.ops.wm.open_mainfile(filepath=str(BASE_BLEND))

    terrain = terrain_object()
    terrain.scale = (TERRAIN_SCALE, TERRAIN_SCALE, TERRAIN_SCALE)
    terrain.location = (0.0, 0.0, TERRAIN_Z_OFFSET)
    terrain["gate_export"] = True
    terrain["mesh_vertices_edited"] = False
    image = bpy.data.images.load(str(TEXTURE_PATH), check_existing=True)
    image.colorspace_settings.name = "sRGB"
    image.pack()
    zone_counts = assign_zoned_materials(terrain, image)

    export_collection = empty_collection("Gate18_Island_Environment_Export")
    template_collection = empty_collection("Gate18_Source_Templates_Hidden")
    template_collection.hide_render = True
    presentation_collection = empty_collection("Gate18_Preview_Only")
    water = bpy.data.objects.get("Preview_Ocean (not exported)")

    tree_assets = {asset for grove in TREE_GROVES for asset in grove["assets"]}
    for obj in list(bpy.data.objects):
        if obj == terrain:
            move_to_collection(obj, export_collection)
        elif obj == water:
            move_to_collection(obj, presentation_collection)
            obj["gate_export"] = False
        elif obj.type == "MESH" and obj.get("asset_id") in tree_assets | {"Grass_CoastalTuft_A", "Grass_CoastalTuft_B"}:
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.type == "MESH":
            obj["gate_export"] = True
            move_to_collection(obj, export_collection)
        elif obj.type in {"CAMERA", "LIGHT"}:
            move_to_collection(obj, presentation_collection)

    rng = random.Random(180427)
    tree_placements, tree_templates = place_trees(terrain, export_collection, template_collection, rng)
    grass_records, grass_templates = place_grass_tufts(terrain, export_collection, template_collection, rng)
    template_count = len(tree_templates) + len(grass_templates)
    for obj in list(template_collection.objects):
        obj.hide_render = True
        obj.hide_set(True)

    # A visible scene note carries the future footprint-clearing handoff into Blender.
    mask_note = bpy.data.objects.new("Building_Footprint_Mask_Interface", None)
    presentation_collection.objects.link(mask_note)
    mask_note.empty_display_type = "PLAIN_AXES"
    mask_note.empty_display_size = 0.0
    mask_note["purpose"] = "Add building rectangles to BUILDING_FOOTPRINTS_M in Gate18_build_grass_coverage.py and rerun to clear 3D grass tufts."
    mask_note["grass_tufts_follow_mask"] = True
    mask_note["continuous_ground_material_remains"] = True

    setup_presentation(bpy.context.scene)
    bpy.context.view_layer.update()
    export_stats = export_fbx(export_collection)

    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_PATH), compress=True)

    counts_by_grove: dict[str, int] = {}
    counts_by_tree: dict[str, int] = {}
    for record in tree_placements:
        counts_by_grove[record["grove"]] = counts_by_grove.get(record["grove"], 0) + 1
        counts_by_tree[record["asset"]] = counts_by_tree.get(record["asset"], 0) + 1
    counts_by_grass: dict[str, int] = {}
    for record in grass_records:
        counts_by_grass[record["asset"]] = counts_by_grass.get(record["asset"], 0) + 1

    report = {
        "gate": "Gate18",
        "asset": "LastLandfall_Island_GrassCoverage",
        "generated_at_local": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "blender_version": bpy.app.version_string,
        "source_scene": str(BASE_BLEND),
        "terrain_mesh_vertices_edited": False,
        "surface_zones_face_counts": zone_counts,
        "surface_design": {
            "zones": ["lowland meadow", "dry highland grass", "coastal sand and soil", "exposed rock", "wet rock"],
            "grass_texture_tiles_across_island": TEXTURE_TILES,
            "grass_texture_detail_mix": {"meadow": 0.18, "highland": 0.12},
            "continuous_surface_material": True,
        },
        "tree_layout": {
            "total": len(tree_placements),
            "counts_by_asset": counts_by_tree,
            "counts_by_grove": counts_by_grove,
            "central_build_zone_and_southwest_landing_corridor_kept_clear_of_trees": True,
            "placements": tree_placements,
        },
        "grass_tufts": {
            "total": len(grass_records),
            "counts_by_asset": counts_by_grass,
            "placement": "terrain-sampled linked-mesh tufts on dry gentle grass/scrub zones; grass includes central build meadow",
            "building_footprint_mask": {
                "interface": "BUILDING_FOOTPRINTS_M in Gate18_build_grass_coverage.py",
                "currently_configured_footprints": BUILDING_FOOTPRINTS_M,
                "clears_3d_tufts": True,
                "keeps_continuous_ground_material": True,
            },
            "placements": grass_records,
        },
        "export": export_stats,
        "template_mesh_objects_hidden_in_blend": template_count,
        "deliverables": {
            "blend": str(SCENE_PATH),
            "fbx": str(FBX_PATH),
            "preview_png": str(PREVIEW_PATH),
            "qa_report": str(REPORT_PATH),
            "handoff": str(HANDOFF_PATH),
            "texture_png": str(TEXTURE_PATH),
        },
        "status": "PASS" if len(tree_placements) == sum(len(grove["assets"]) for grove in TREE_GROVES) and len(grass_records) > 100 else "REVIEW",
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    HANDOFF_PATH.write_text(
        "# Gate18 Grass Coverage Handoff\n\n"
        "## Files\n\n"
        f"- Blender scene: `{SCENE_PATH.name}`\n"
        f"- Unity import candidate: `{FBX_PATH.name}` (grass albedo is embedded in the FBX)\n"
        f"- Overview preview: `{PREVIEW_PATH.name}`\n"
        f"- QA and placements: `{REPORT_PATH.name}`\n"
        f"- Grass albedo source: `{TEXTURE_PATH.name}`\n\n"
        "## What changed\n\n"
        "- The terrain has five face-assigned material zones: meadow, dry highland grass, coastal soil, exposed rock, and wet rock. This keeps the main color divisions readable in Blender and when imported from FBX.\n"
        f"- The hand-painted grass image repeats {TEXTURE_TILES:g} times across the island and contributes only a small amount of surface detail, reducing the previous dense mottling and repetition.\n"
        f"- The old 12 scattered trees were replaced by {len(tree_placements)} trees in five irregular groves around the island.\n"
        f"- {len(grass_records)} linked 3D coastal-grass tufts cover suitable dry, gentle ground, including the central build meadow.\n\n"
        "## Building footprints\n\n"
        "Add each future footprint to `BUILDING_FOOTPRINTS_M` in the build script with `name`, center `x`/`y`, `half_width_m`, `half_depth_m`, and optional `rotation_degrees`; rerunning clears only 3D grass tufts inside the footprint plus a 0.5 m margin. The continuous terrain material remains underneath, so foundations can cover it. The empty interface object is included in the Blender scene for identification.\n\n"
        "## Import note\n\n"
        "The FBX contains the terrain and environment mesh objects, excludes the preview ocean, camera, sun, and hidden source templates, and embeds the grass albedo image. Blender procedural rock shading may simplify to material color during FBX import; the rock zone still has its own exported material slot.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "gate": "Gate18", "status": report["status"], "trees": len(tree_placements),
        "tree_groves": counts_by_grove, "grass_tufts": len(grass_records),
        "terrain_zones": zone_counts, "fbx": export_stats,
        "preview": str(PREVIEW_PATH), "blend": str(SCENE_PATH),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
