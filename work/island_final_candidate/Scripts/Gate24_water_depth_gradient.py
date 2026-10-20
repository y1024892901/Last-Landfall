# -*- coding: utf-8 -*-
"""Build a basin-woodland candidate with a small pond and stream."""
from __future__ import annotations

import datetime as dt
import json
import math
import random
from pathlib import Path
from typing import Any

import bpy
import numpy as np
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
SCENE_PATH = OUT / "Assets_Generated" / "LastLandfall_Island_GrassCoverage_Gate24.blend"
FBX_PATH = OUT / "Assets_Generated" / "LastLandfall_Island_GrassCoverage_Gate24.fbx"
PREVIEW_PATH = OUT / "Previews_Generated" / "Gate24_GrassCoverage_Zones_TreeClusters.png"
REPORT_PATH = OUT / "Reports_Generated" / "Gate24_grass_coverage_qa.json"
HANDOFF_PATH = OUT / "Gate24_GrassCoverage_Handoff.md"

TERRAIN_SCALE = 0.02
TERRAIN_Z_OFFSET = -0.92
WATER_Z = -0.92
UV_NAME = "Grass_Albedo_Planar"
TEXTURE_TILES = 1.9

# The central lowland remains mostly available for woodland and meadow. A
# modest settlement clearing sits just west of the water system.
BUILD_CLEARING_CENTER = (0.0, 0.0)
BUILD_CLEARING_RADII_M = (6.0, 4.5)
POND_CENTER = (4.5, -1.8)
POND_RADII_M = (2.10, 1.35)
POND_SHAPE_SEED = 417
STREAM_INLET_POINTS = [
    (8.6, 8.4), (8.6, 7.0), (8.0, 5.8), (7.6, 4.5),
    (6.9, 3.3), (6.2, 2.3), (5.8, 1.2), (5.0, 0.3), (4.7, -0.2),
]
STREAM_OUTLET_POINTS = [
    (3.2, -2.4), (2.8, -3.4), (2.8, -4.3),
    (2.1, -5.1), (1.8, -5.9), (0.8, -6.5),
]

# Future building masks are deliberately empty in this preview. Add a rotated
# rectangle per building when its footprint is known, then rerun this script.
BUILDING_FOOTPRINTS_M: list[dict[str, float | str]] = []

# Existing ridge and coastal groves stay as a light outer frame. Broadleaf
# woodland is denser in the moist basin, while the pond, stream, small build
# clearing, and southwest landing corridor remain open.
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
    {"name": "Basin_West_Woodland", "center": (-9.0, 1.0), "radius": 5.0,
     "assets": ["Broadleaf_Coastal_A", "Broadleaf_Coastal_B", "Broadleaf_Coastal_A",
                "Broadleaf_Coastal_B", "Broadleaf_Coastal_A", "Broadleaf_Coastal_B",
                "Broadleaf_Coastal_A", "Broadleaf_Coastal_B", "Broadleaf_Coastal_A", "Broadleaf_Coastal_B"]},
    {"name": "Basin_East_Woodland", "center": (10.0, 1.5), "radius": 5.2,
     "assets": ["Broadleaf_Coastal_B", "Broadleaf_Coastal_A", "Broadleaf_Coastal_B",
                "Broadleaf_Coastal_A", "Broadleaf_Coastal_B", "Broadleaf_Coastal_A",
                "Broadleaf_Coastal_B", "Broadleaf_Coastal_A", "Broadleaf_Coastal_B", "Broadleaf_Coastal_A"]},
    {"name": "Basin_South_Woodland", "center": (3.5, -9.5), "radius": 4.3,
     "assets": ["Broadleaf_Coastal_A", "Broadleaf_Coastal_B", "Broadleaf_Coastal_A",
                "Broadleaf_Coastal_B", "Broadleaf_Coastal_A", "Broadleaf_Coastal_B",
                "Broadleaf_Coastal_A", "Broadleaf_Coastal_B"]},
]

GRASS_PATCHES = [
    ((-5.0, 3.5), 2.9), ((-3.4, -4.8), 2.4), ((4.8, -5.5), 2.7),
    ((0.8, -6.6), 2.4),
    ((11.0, -3.8), 3.4), ((-16.5, 8.0), 3.3), ((17.2, 4.4), 3.6),
    ((-6.0, -14.0), 3.3), ((4.0, -21.0), 3.6), ((-1.5, 13.5), 3.2),
]
GRASS_CLUSTER_COUNT = 36
MAX_GRASS_TUFTS = 270


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
    grow = 1.3 if expanded else 0.0
    rx, ry = BUILD_CLEARING_RADII_M[0] + grow, BUILD_CLEARING_RADII_M[1] + grow
    cx, cy = BUILD_CLEARING_CENTER
    central = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1.0
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


def point_segment_distance(x: float, y: float, a: tuple[float, float], b: tuple[float, float]) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-9:
        return math.hypot(x - a[0], y - a[1])
    t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / length_sq))
    return math.hypot(x - (a[0] + t * dx), y - (a[1] + t * dy))


def distance_to_path(x: float, y: float, points: list[tuple[float, float]]) -> float:
    return min(point_segment_distance(x, y, points[i], points[i + 1]) for i in range(len(points) - 1))


def in_water_system(x: float, y: float, margin: float = 0.0) -> bool:
    pond_rx = POND_RADII_M[0] + margin
    pond_ry = POND_RADII_M[1] + margin
    pond = ((x - POND_CENTER[0]) / pond_rx) ** 2 + ((y - POND_CENTER[1]) / pond_ry) ** 2 <= 1.0
    near_stream = any(
        distance_to_path(x, y, path) <= margin + 0.05
        for path in (STREAM_INLET_POINTS, STREAM_OUTLET_POINTS)
    )
    return pond or near_stream


def distance_array_to_path(x: np.ndarray, y: np.ndarray, points: list[tuple[float, float]]) -> np.ndarray:
    result = np.full(len(x), np.inf, dtype=np.float32)
    path = smoothed_path(points, spacing=0.42)
    for index in range(len(path) - 1):
        ax, ay = path[index]
        bx, by = path[index + 1]
        dx, dy = bx - ax, by - ay
        length_sq = max(dx * dx + dy * dy, 1e-9)
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / length_sq, 0.0, 1.0)
        dist = np.hypot(x - (ax + t * dx), y - (ay + t * dy))
        np.minimum(result, dist, out=result)
    return result


def sculpt_hydrology_channels(terrain: bpy.types.Object) -> dict[str, Any]:
    """Carve a shallow spring-fed pond bowl and stream bed in this candidate only."""
    mesh = terrain.data
    count = len(mesh.vertices)
    coordinates = np.empty((count, 3), dtype=np.float32)
    mesh.vertices.foreach_get("co", coordinates.reshape(-1))
    world_matrix = np.array([[terrain.matrix_world[row][column] for column in range(4)] for row in range(4)], dtype=np.float32)
    world_positions = coordinates @ world_matrix[:3, :3].T + world_matrix[:3, 3]
    x, y = world_positions[:, 0], world_positions[:, 1]
    delta = np.zeros(count, dtype=np.float32)

    pond_r = np.sqrt(
        ((x - POND_CENTER[0]) / POND_RADII_M[0]) ** 2
        + ((y - POND_CENTER[1]) / POND_RADII_M[1]) ** 2
    )
    bowl_t = np.clip((1.12 - pond_r) / 1.12, 0.0, 1.0)
    bowl_weight = bowl_t * bowl_t * (3.0 - 2.0 * bowl_t)
    delta -= 0.27 * bowl_weight
    # A soft low berm retains the pool while keeping a broad marshy transition.
    delta += 0.035 * np.exp(-0.5 * ((pond_r - 1.06) / 0.16) ** 2)

    for path in (STREAM_INLET_POINTS, STREAM_OUTLET_POINTS):
        distance = distance_array_to_path(x, y, path)
        delta -= 0.13 * np.exp(-0.5 * (distance / 0.39) ** 2)
        delta += 0.022 * np.exp(-0.5 * ((distance - 0.58) / 0.19) ** 2)

    changed = np.abs(delta) > 0.003
    coordinates[:, 2] += delta / TERRAIN_SCALE
    mesh.vertices.foreach_set("co", coordinates.reshape(-1))
    mesh.update()
    bpy.context.view_layer.update()
    terrain["mesh_vertices_edited"] = True
    terrain["hydrology_sculpted_in_candidate"] = True
    return {
        "vertices_adjusted": int(np.count_nonzero(changed)),
        "maximum_pond_bowl_depth_m": 0.27,
        "maximum_stream_bed_depth_m": 0.13,
        "source_terrain_mesh_modified": False,
    }


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


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def mix_colors(a: tuple[float, ...], b: tuple[float, ...], weight: float) -> tuple[float, float, float]:
    return tuple(a[index] * (1.0 - weight) + b[index] * weight for index in range(3))


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


def make_vertex_painted_terrain_material(image: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("Island_Continuous_Zone_Paint")
    material.diffuse_color = srgb_hex_to_linear("#788A57")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (560, 40)
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (330, 40)
    principled.inputs["Roughness"].default_value = 0.94
    paint = nodes.new("ShaderNodeVertexColor")
    paint.layer_name = "Island_Zone_Color"
    paint.location = (-390, 130)
    uv = nodes.new("ShaderNodeUVMap")
    uv.uv_map = UV_NAME
    uv.location = (-600, -100)
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.extension = "REPEAT"
    texture.interpolation = "Linear"
    texture.location = (-390, -100)
    detail = nodes.new("ShaderNodeMixRGB")
    detail.blend_type = "MIX"
    detail.inputs["Fac"].default_value = 0.10
    detail.location = (40, 50)
    links.new(paint.outputs["Color"], detail.inputs["Color1"])
    links.new(uv.outputs["UV"], texture.inputs["Vector"])
    links.new(texture.outputs["Color"], detail.inputs["Color2"])
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


def make_stream_material() -> bpy.types.Material:
    material = make_simple_material("Basin_Stream_Water_Matte", "#42666A", 0.68)
    material.diffuse_color = srgb_hex_to_linear("#42666A")
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in principled.inputs:
        principled.inputs["Specular IOR Level"].default_value = 0.16
    if "Coat Weight" in principled.inputs:
        principled.inputs["Coat Weight"].default_value = 0.0
        principled.inputs["Coat Roughness"].default_value = 0.6
    vertex_color = nodes.new("ShaderNodeVertexColor")
    vertex_color.layer_name = "Water_Surface_Gradient"
    vertex_color.location = (-260, 40)
    links.new(vertex_color.outputs["Color"], principled.inputs["Base Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return material


def set_water_vertex_colors(mesh: bpy.types.Mesh, colors: list[tuple[float, float, float, float]]) -> None:
    attribute = mesh.color_attributes.new(name="Water_Surface_Gradient", type="FLOAT_COLOR", domain="POINT")
    attribute.data.foreach_set("color", np.asarray(colors, dtype=np.float32).reshape(-1))
    mesh.color_attributes.active_color = attribute


def smoothed_path(points: list[tuple[float, float]], spacing: float = 0.32) -> list[tuple[float, float]]:
    result: list[tuple[float, float]] = []
    for i in range(len(points) - 1):
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(len(points) - 1, i + 2)]
        segment_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        steps = max(2, int(math.ceil(segment_len / spacing)))
        for step in range(steps):
            t = step / steps
            t2, t3 = t * t, t * t * t
            xy = []
            for axis in range(2):
                value = 0.5 * (
                    2.0 * p1[axis]
                    + (-p0[axis] + p2[axis]) * t
                    + (2.0 * p0[axis] - 5.0 * p1[axis] + 4.0 * p2[axis] - p3[axis]) * t2
                    + (-p0[axis] + 3.0 * p1[axis] - 3.0 * p2[axis] + p3[axis]) * t3
                )
                xy.append(value)
            result.append((xy[0], xy[1]))
    result.append(points[-1])
    return result


def make_ribbon(
    terrain: bpy.types.Object,
    collection: bpy.types.Collection,
    name: str,
    control_points: list[tuple[float, float]],
    material: bpy.types.Material,
    width_start: float,
    width_end: float,
    edge_extra: float,
    surface_offset: float,
) -> bpy.types.Object:
    path = smoothed_path(control_points, spacing=0.22)
    vertices: list[tuple[float, float, float]] = []
    vertex_colors: list[tuple[float, float, float, float]] = []
    rails = (-1.0, -0.5, 0.0, 0.5, 1.0)
    deep_color = srgb_hex_to_linear("#39595E")
    shallow_color = srgb_hex_to_linear("#58787A")
    for index, (x, y) in enumerate(path):
        previous = path[max(0, index - 1)]
        following = path[min(len(path) - 1, index + 1)]
        tangent = Vector((following[0] - previous[0], following[1] - previous[1], 0.0))
        if tangent.length < 1e-6:
            tangent = Vector((1.0, 0.0, 0.0))
        tangent.normalize()
        side = Vector((-tangent.y, tangent.x, 0.0))
        t = index / max(1, len(path) - 1)
        phase = sum(ord(char) for char in name) * 0.017
        width_wobble = 0.060 * math.sin(math.tau * t * 2.7 + phase) + 0.022 * math.sin(math.tau * t * 5.3 + 0.7 * phase)
        half_width = max(0.18, (width_start * (1.0 - t) + width_end * t) * 0.5 + edge_extra + width_wobble)
        for rail in rails:
            sx = x + side.x * half_width * rail
            sy = y + side.y * half_width * rail
            point = sample_terrain(terrain, sx, sy) or sample_terrain(terrain, x, y)
            if point is None:
                raise RuntimeError(f"Stream ribbon leaves the terrain at {(sx, sy)}")
            vertices.append((sx, sy, point["z"] + surface_offset))
            rgb = mix_colors(deep_color, shallow_color, abs(rail) ** 1.5)
            vertex_colors.append((rgb[0], rgb[1], rgb[2], 1.0))
    faces = []
    for index in range(len(path) - 1):
        for rail_index in range(len(rails) - 1):
            left = index * len(rails) + rail_index
            faces.append((left, left + 1, left + len(rails) + 1, left + len(rails)))
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    set_water_vertex_colors(mesh, vertex_colors)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj["gate_export"] = True
    obj["water_system"] = "basin_stream"
    obj["path_sections"] = len(path)
    return obj


def make_pond(terrain: bpy.types.Object, collection: bpy.types.Collection, water_material: bpy.types.Material) -> bpy.types.Object:
    rng = random.Random(POND_SHAPE_SEED)
    segments = 96
    ring: list[tuple[float, float, float]] = []
    for i in range(segments):
        angle = math.tau * i / segments
        irregular = 1.0 + 0.078 * math.sin(3.0 * angle + 0.4) + 0.036 * math.sin(5.0 * angle + 1.7) + 0.014 * math.sin(7.0 * angle + 0.9)
        x = POND_CENTER[0] + math.cos(angle) * POND_RADII_M[0] * irregular
        y = POND_CENTER[1] + math.sin(angle) * POND_RADII_M[1] * irregular
        ring.append((x, y, 0.0))
    center = sample_terrain(terrain, *POND_CENTER)
    if center is None:
        raise RuntimeError("Pond center is outside the island terrain")
    water_z = center["z"] + 0.025
    vertices = [(x, y, water_z) for x, y, _ in ring]
    vertices.append((POND_CENTER[0], POND_CENTER[1], water_z))
    center_index = len(vertices) - 1
    faces = [(center_index, i, (i + 1) % segments) for i in range(segments)]
    mesh = bpy.data.meshes.new("Basin_Pond_Water_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(water_material)
    shallow = srgb_hex_to_linear("#58787A")
    deep = srgb_hex_to_linear("#39595E")
    set_water_vertex_colors(mesh, [shallow] * segments + [deep])
    mesh.update()
    pond = bpy.data.objects.new("Basin_Pond_Water", mesh)
    collection.objects.link(pond)
    pond["gate_export"] = True
    pond["water_system"] = "basin_pond"
    pond["surface_z_m"] = round(water_z, 3)
    pond["approx_dimensions_m"] = [round(POND_RADII_M[0] * 2.0, 2), round(POND_RADII_M[1] * 2.0, 2)]
    return pond


def create_hydrology(terrain: bpy.types.Object, collection: bpy.types.Collection) -> dict[str, Any]:
    water = make_stream_material()
    water_objects: list[bpy.types.Object] = []
    for label, points, widths in (
        ("Inlet", STREAM_INLET_POINTS, (0.44, 0.57)),
        ("Outlet", STREAM_OUTLET_POINTS, (0.57, 0.40)),
    ):
        water_objects.append(make_ribbon(terrain, collection, f"Basin_Stream_Water_{label}", points, water, *widths, 0.0, 0.045))
    pond = make_pond(terrain, collection, water)
    water_objects.append(pond)
    creek_length = sum(
        math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
        for points in (STREAM_INLET_POINTS, STREAM_OUTLET_POINTS)
        for i in range(len(points) - 1)
    )
    return {
        "pond_center_m": list(POND_CENTER),
        "pond_dimensions_m": [round(POND_RADII_M[0] * 2.0, 2), round(POND_RADII_M[1] * 2.0, 2)],
        "creek_approx_length_m": round(creek_length, 2),
        "stream_objects": len(water_objects),
        "water_area_is_localized_within_basin": True,
        "water_surface_uses_exportable_depth_gradient_vertex_colors": True,
        "water_meshes": [obj.name for obj in water_objects],
    }


def assign_zoned_materials(terrain: bpy.types.Object, image: bpy.types.Image) -> dict[str, int]:
    add_planar_uv(terrain.data)
    mesh = terrain.data
    old_material_index = np.empty(len(mesh.polygons), dtype=np.int32)
    mesh.polygons.foreach_get("material_index", old_material_index)
    paint_name = "Island_Zone_Color"
    if mesh.color_attributes.get(paint_name):
        mesh.color_attributes.remove(mesh.color_attributes[paint_name])
    paint = mesh.color_attributes.new(name=paint_name, type="FLOAT_COLOR", domain="CORNER")
    mesh.color_attributes.active_color = paint
    materials = [make_vertex_painted_terrain_material(image), make_wet_rock_material()]
    mesh.materials.clear()
    for material in materials:
        mesh.materials.append(material)
    mesh.polygons.foreach_set("material_index", np.where(old_material_index == 2, 1, 0).astype(np.int32))

    # Calculate paint by vertex, then broadcast to mesh corners in one bulk write.
    vertex_count = len(mesh.vertices)
    loop_count = len(mesh.loops)
    positions = np.empty((vertex_count, 3), dtype=np.float32)
    normals = np.empty((vertex_count, 3), dtype=np.float32)
    loop_vertices = np.empty(loop_count, dtype=np.int32)
    mesh.vertices.foreach_get("co", positions.reshape(-1))
    mesh.vertices.foreach_get("normal", normals.reshape(-1))
    mesh.loops.foreach_get("vertex_index", loop_vertices)
    world_matrix = np.array([[terrain.matrix_world[row][column] for column in range(4)] for row in range(4)], dtype=np.float32)
    world_positions = positions @ world_matrix[:3, :3].T + world_matrix[:3, 3]
    world_normals = normals @ world_matrix[:3, :3].T
    norm_lengths = np.linalg.norm(world_normals, axis=1)
    norm_lengths[norm_lengths < 1e-8] = 1.0
    world_normals /= norm_lengths[:, None]

    altitude = world_positions[:, 2] + 0.17 * np.sin(world_positions[:, 0] * 0.11 + np.sin(world_positions[:, 1] * 0.08))
    dry_weight = smoothstep_array(1.9, 3.65, altitude)
    shore_weight = 1.0 - smoothstep_array(-0.84, -0.49, altitude)
    slope_rock_weight = 1.0 - smoothstep_array(0.53, 0.79, world_normals[:, 2])
    high_rock_weight = 0.78 * smoothstep_array(4.6, 5.8, altitude)
    rock_weight = np.maximum(slope_rock_weight, high_rock_weight)

    meadow = np.array(srgb_hex_to_linear("#788A57")[:3], dtype=np.float32)
    dry = np.array(srgb_hex_to_linear("#898650")[:3], dtype=np.float32)
    sand = np.array(srgb_hex_to_linear("#B0A383")[:3], dtype=np.float32)
    rock = np.array(srgb_hex_to_linear("#626964")[:3], dtype=np.float32)
    colors = meadow[None, :] * (1.0 - dry_weight[:, None]) + dry[None, :] * dry_weight[:, None]
    colors = colors * (1.0 - shore_weight[:, None]) + sand[None, :] * shore_weight[:, None]
    colors = colors * (1.0 - rock_weight[:, None]) + rock[None, :] * rock_weight[:, None]
    stream_distance = np.minimum(
        distance_array_to_path(world_positions[:, 0], world_positions[:, 1], STREAM_INLET_POINTS),
        distance_array_to_path(world_positions[:, 0], world_positions[:, 1], STREAM_OUTLET_POINTS),
    )
    pond_r = np.sqrt(
        ((world_positions[:, 0] - POND_CENTER[0]) / POND_RADII_M[0]) ** 2
        + ((world_positions[:, 1] - POND_CENTER[1]) / POND_RADII_M[1]) ** 2
    )
    stream_wet = 0.42 * np.exp(-0.5 * (stream_distance / 1.05) ** 2)
    pond_wet = 0.42 * np.exp(-0.5 * ((pond_r - 1.08) / 0.42) ** 2)
    wet_weight = np.maximum(stream_wet, pond_wet)[:, None]
    wet_meadow = np.array(srgb_hex_to_linear("#667956")[:3], dtype=np.float32)
    colors = colors * (1.0 - wet_weight) + wet_meadow[None, :] * wet_weight
    stream_silt = 0.34 * np.exp(-0.5 * ((stream_distance - 0.42) / 0.25) ** 2)
    pond_silt = 0.32 * np.exp(-0.5 * ((pond_r - 1.02) / 0.19) ** 2)
    bank_weight = np.maximum(stream_silt, pond_silt)[:, None]
    silt = np.array(srgb_hex_to_linear("#827958")[:3], dtype=np.float32)
    colors = colors * (1.0 - bank_weight) + silt[None, :] * bank_weight
    wash = 0.96 + 0.05 * np.sin(world_positions[:, 0] * 0.075 + np.sin(world_positions[:, 1] * 0.06)) * np.sin(world_positions[:, 1] * 0.09)
    colors *= wash[:, None]
    colors = np.clip(colors, 0.0, 1.0)
    loop_colors = np.ones((loop_count, 4), dtype=np.float32)
    loop_colors[:, :3] = colors[loop_vertices]
    paint.data.foreach_set("color", loop_colors.reshape(-1))

    face_centers = np.empty((len(mesh.polygons), 3), dtype=np.float32)
    face_normals = np.empty((len(mesh.polygons), 3), dtype=np.float32)
    mesh.polygons.foreach_get("center", face_centers.reshape(-1))
    mesh.polygons.foreach_get("normal", face_normals.reshape(-1))
    face_centers = face_centers @ world_matrix[:3, :3].T + world_matrix[:3, 3]
    face_normals = face_normals @ world_matrix[:3, :3].T
    face_lengths = np.linalg.norm(face_normals, axis=1)
    face_lengths[face_lengths < 1e-8] = 1.0
    face_normals /= face_lengths[:, None]
    face_altitude = face_centers[:, 2] + 0.17 * np.sin(face_centers[:, 0] * 0.11 + np.sin(face_centers[:, 1] * 0.08))
    face_dry = smoothstep_array(1.9, 3.65, face_altitude)
    face_shore = 1.0 - smoothstep_array(-0.84, -0.49, face_altitude)
    face_rock = np.maximum(1.0 - smoothstep_array(0.53, 0.79, face_normals[:, 2]), 0.78 * smoothstep_array(4.6, 5.8, face_altitude))
    labels = np.full(len(mesh.polygons), "meadow", dtype=object)
    labels[face_dry > 0.5] = "dry_highland"
    labels[face_rock > 0.5] = "exposed_rock"
    labels[face_shore > 0.5] = "coastal_soil"
    labels[old_material_index == 2] = "wet_rock"
    return {label: int(np.count_nonzero(labels == label)) for label in ("meadow", "dry_highland", "coastal_soil", "exposed_rock", "wet_rock")}


def smoothstep_array(edge0: float, edge1: float, values: np.ndarray) -> np.ndarray:
    t = np.clip((values - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lighten_grass_template(template: bpy.types.Object, asset: str) -> None:
    for index, source in enumerate(list(template.data.materials)):
        if source is None:
            continue
        material = source.copy()
        material.name = f"Gate24_{asset}_{source.name}"
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type != "BSDF_PRINCIPLED" or "Base Color" not in node.inputs:
                    continue
                factor = 1.48 if "shadow" in source.name.lower() else (1.10 if "sun" in source.name.lower() else 1.28)
                color = node.inputs["Base Color"].default_value
                node.inputs["Base Color"].default_value = (min(0.95, color[0] * factor), min(0.95, color[1] * factor), min(0.95, color[2] * factor), color[3])
        diffuse = source.diffuse_color
        material.diffuse_color = (min(0.95, diffuse[0] * 1.24), min(0.95, diffuse[1] * 1.24), min(0.95, diffuse[2] * 1.24), diffuse[3])
        template.data.materials[index] = material


def import_template(asset: str, template_collection: bpy.types.Collection, source_dir: Path | None = None) -> bpy.types.Object:
    path = (source_dir or INSPECTED) / f"{asset}.fbx"
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
        scale = rng.uniform(0.82, 1.18)
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
        obj["grass_patch_system"] = "Gate24_dry_ground_clumps"
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
        min_spacing = 1.82 if grove["name"].startswith("Basin_") else 2.05
        for index, asset in enumerate(grove["assets"]):
            choices = [
                point for point in points
                if math.hypot(point["x"] - center_x, point["y"] - center_y) <= base_radius + 1.8
                and not inside_building_mask(point["x"], point["y"])
                and not in_water_system(point["x"], point["y"], margin=1.3)
                and all(math.hypot(point["x"] - ox, point["y"] - oy) >= min_spacing for ox, oy in used)
                and all(math.hypot(point["x"] - ox, point["y"] - oy) >= 1.55 for ox, oy in fixed)
            ]
            if not choices:
                raise RuntimeError(f"No valid terrain point for {grove['name']} tree {index + 1} ({asset})")
            scale = max(base_radius * 0.82, 1.0)
            weights = [
                math.exp(-0.5 * (math.hypot(point["x"] - center_x, point["y"] - center_y) / scale) ** 2) + 0.035
                for point in choices
            ]
            point = rng.choices(choices, weights=weights, k=1)[0]
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
    return min(0.88, 0.012 + strongest * 0.84)


def place_grass_tufts(
    terrain: bpy.types.Object,
    export_collection: bpy.types.Collection,
    template_collection: bpy.types.Collection,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], dict[str, bpy.types.Object]]:
    assets = ["Grass_CoastalTuft_A", "Grass_CoastalTuft_B"]
    templates = {asset: import_template(asset, template_collection) for asset in assets}
    for asset, template in templates.items():
        lighten_grass_template(template, asset)
    # Build small irregular groups instead of evenly spaced isolated spikes.
    tree_locations = [
        (obj.location.x, obj.location.y) for obj in export_collection.objects
        if obj.type == "MESH" and str(obj.get("asset_id", "")).startswith(("Pine_", "Broadleaf_", "Fern_"))
    ]
    rock_locations = [
        (obj.location.x, obj.location.y) for obj in export_collection.objects
        if obj.type == "MESH" and str(obj.get("asset_id", "")).startswith("Basalt_")
    ]
    centers: list[dict[str, Any]] = []
    for _ in range(GRASS_CLUSTER_COUNT):
        for _attempt in range(180):
            px = rng.uniform(-28.5, 28.0)
            py = rng.uniform(-30.5, 21.5)
            point = sample_terrain(terrain, px, py)
            if not point or not (0.02 <= point["z"] <= 3.85 and point["normal_z"] >= 0.775):
                continue
            if inside_building_mask(px, py) or in_water_system(px, py, margin=0.7):
                continue
            if rng.random() > grass_density(px, py):
                continue
            if any(math.hypot(px - tx, py - ty) < 1.35 for tx, ty in tree_locations):
                continue
            if any(math.hypot(px - rx, py - ry) < 0.72 for rx, ry in rock_locations):
                continue
            if any(math.hypot(px - old["x"], py - old["y"]) < 1.85 for old in centers):
                continue
            centers.append(point)
            break

    selected: list[dict[str, Any]] = []
    cluster_ids: list[int] = []
    for cluster_id, center in enumerate(centers):
        wanted = rng.randint(5, 9)
        added = 0
        for _attempt in range(wanted * 14):
            angle = rng.uniform(0.0, math.tau)
            radius = min(1.35, abs(rng.gauss(0.58, 0.42)))
            px = center["x"] + math.cos(angle) * radius
            py = center["y"] + math.sin(angle) * radius
            point = sample_terrain(terrain, px, py)
            if not point or not (0.02 <= point["z"] <= 3.85 and point["normal_z"] >= 0.775):
                continue
            if inside_building_mask(px, py) or in_water_system(px, py, margin=0.38):
                continue
            if any(math.hypot(px - tx, py - ty) < 0.72 for tx, ty in tree_locations):
                continue
            if any(math.hypot(px - rx, py - ry) < 0.48 for rx, ry in rock_locations):
                continue
            if any(math.hypot(px - old["x"], py - old["y"]) < 0.34 for old in selected):
                continue
            selected.append(point)
            cluster_ids.append(cluster_id)
            added += 1
            if added >= wanted or len(selected) >= MAX_GRASS_TUFTS:
                break
        if len(selected) >= MAX_GRASS_TUFTS:
            break

    records: list[dict[str, Any]] = []
    for index, point in enumerate(selected):
        asset = assets[0] if rng.random() < 0.56 else assets[1]
        obj = make_instance(templates[asset], asset, point, export_collection, rng, align_to_ground=True)
        records.append({
            "asset": asset,
            "cluster_id": cluster_ids[index],
            "location_m": [round(point["x"], 3), round(point["y"], 3), round(obj.location.z, 3)],
            "surface_z_m": round(point["z"], 3),
            "surface_normal_z": round(point["normal_z"], 3),
        })
    return records, templates


def place_riparian_boulders(
    terrain: bpy.types.Object,
    export_collection: bpy.types.Collection,
    template_collection: bpy.types.Collection,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], dict[str, bpy.types.Object]]:
    assets = ["Basalt_RockCluster", "Basalt_TidewornSlab"]
    templates = {asset: import_template(asset, template_collection, OUT / "Assets_Generated") for asset in assets}
    sites = [
        (5.35, -0.45, "inlet_mouth_bank"),
        (7.0, -1.55, "pond_east_bank"),
        (2.05, -3.45, "outlet_bend_bank"),
        (1.05, -5.55, "outlet_wet_meadow"),
    ]
    broad_tree_positions = [
        (obj.location.x, obj.location.y) for obj in export_collection.objects
        if obj.type == "MESH" and str(obj.get("asset_id", "")).startswith(("Pine_", "Broadleaf_"))
    ]
    other_rock_positions = [
        (obj.location.x, obj.location.y) for obj in export_collection.objects
        if obj.type == "MESH" and str(obj.get("asset_id", "")).startswith("Basalt_")
    ]
    records: list[dict[str, Any]] = []
    for index, (x, y, bank_site) in enumerate(sites):
        if in_water_system(x, y, margin=0.48):
            continue
        point = sample_terrain(terrain, x, y)
        if not point or point["normal_z"] < 0.77:
            continue
        if any(math.hypot(x - tx, y - ty) < 1.05 for tx, ty in broad_tree_positions + other_rock_positions):
            continue
        asset = assets[index % len(assets)]
        obj = make_instance(templates[asset], asset, point, export_collection, rng)
        factor = rng.uniform(0.30, 0.40) if asset == "Basalt_RockCluster" else rng.uniform(0.32, 0.43)
        obj.scale = tuple(component * factor for component in obj.scale)
        bpy.context.view_layer.update()
        bottom = min((obj.matrix_world @ vertex.co).z for vertex in obj.data.vertices)
        obj.location.z += point["z"] - bottom
        obj["riparian_stone_site"] = bank_site
        records.append({
            "asset": asset,
            "bank_site": bank_site,
            "location_m": [round(x, 3), round(y, 3), round(obj.location.z, 3)],
            "scale_factor": round(factor, 3),
        })
    return records, templates


def place_riparian_ferns(
    terrain: bpy.types.Object,
    export_collection: bpy.types.Collection,
    template_collection: bpy.types.Collection,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], dict[str, bpy.types.Object]]:
    """Place a few shade-loving ferns on damp banks, away from the waterline."""
    asset = "Fern_Cliffside"
    template = import_template(asset, template_collection)
    paths = [STREAM_INLET_POINTS, STREAM_OUTLET_POINTS]
    tree_locations = [
        (obj.location.x, obj.location.y) for obj in export_collection.objects
        if obj.type == "MESH" and str(obj.get("asset_id", "")).startswith(("Pine_", "Broadleaf_"))
    ]
    rock_locations = [
        (obj.location.x, obj.location.y) for obj in export_collection.objects
        if obj.type == "MESH" and str(obj.get("asset_id", "")).startswith("Basalt_")
    ]
    chosen: list[tuple[float, float]] = []
    records: list[dict[str, Any]] = []
    for fern_index in range(6):
        for _attempt in range(180):
            path = paths[0] if fern_index < 4 else paths[1]
            segment = rng.randrange(len(path) - 1)
            t = rng.uniform(0.2, 0.8)
            bx = path[segment][0] * (1.0 - t) + path[segment + 1][0] * t
            by = path[segment][1] * (1.0 - t) + path[segment + 1][1] * t
            dx, dy = path[segment + 1][0] - path[segment][0], path[segment + 1][1] - path[segment][1]
            length = max(math.hypot(dx, dy), 1e-6)
            offset = rng.choice((-1.0, 1.0)) * rng.uniform(0.8, 1.45)
            px = bx - (dy / length) * offset
            py = by + (dx / length) * offset
            point = sample_terrain(terrain, px, py)
            if not point or not (0.0 <= point["z"] <= 4.7 and point["normal_z"] >= 0.64):
                continue
            if in_reserved_zone(px, py, expanded=True) or in_water_system(px, py, margin=0.58):
                continue
            if any(math.hypot(px - tx, py - ty) < 1.15 for tx, ty in tree_locations):
                continue
            if any(math.hypot(px - rx, py - ry) < 0.9 for rx, ry in rock_locations):
                continue
            if any(math.hypot(px - ox, py - oy) < 1.25 for ox, oy in chosen):
                continue
            obj = make_instance(template, asset, point, export_collection, rng, align_to_ground=True)
            scale = rng.uniform(0.44, 0.62)
            obj.scale = tuple(component * scale for component in obj.scale)
            bpy.context.view_layer.update()
            bottom = min((obj.matrix_world @ vertex.co).z for vertex in obj.data.vertices)
            obj.location.z += point["z"] - bottom
            obj["riparian_plant_zone"] = "moist_shaded_bank"
            records.append({
                "asset": asset,
                "location_m": [round(px, 3), round(py, 3), round(obj.location.z, 3)],
                "scale_factor": round(scale, 3),
                "bank_offset_m": round(abs(offset), 3),
            })
            chosen.append((px, py))
            break
    return records, {asset: template}


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

    world = bpy.data.worlds.new("Gate24_GrassCoverage_World")
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
    sun_data = bpy.data.lights.new("Gate24_Sun", type="SUN")
    sun_data.energy = 2.35
    sun_data.angle = math.radians(32.0)
    sun = bpy.data.objects.new("Gate24_Sun", sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(24), math.radians(-28), math.radians(-32))

    camera = scene.camera
    if camera is None:
        camera_data = bpy.data.cameras.new("Gate24_Overview_Camera")
        camera = bpy.data.objects.new("Gate24_Overview_Camera", camera_data)
        scene.collection.objects.link(camera)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 68.5
    camera.location = (72.0, -86.0, 61.0)
    target = Vector((1.2, -1.6, 1.0))
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
        colors_type="SRGB", prioritize_active_color=True,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Gate24 FBX export failed: {result}")
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

    export_collection = empty_collection("Gate24_Island_Environment_Export")
    template_collection = empty_collection("Gate24_Source_Templates_Hidden")
    template_collection.hide_render = True
    presentation_collection = empty_collection("Gate24_Preview_Only")
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

    bpy.context.view_layer.update()
    original_surface = terrain.copy()
    original_surface.data = terrain.data.copy()
    original_surface.name = "Gate24_OriginalTerrain_HeightSampler"
    template_collection.objects.link(original_surface)
    original_surface["gate_export"] = False
    hydrology = create_hydrology(original_surface, export_collection)
    sculpt_stats = sculpt_hydrology_channels(terrain)
    zone_counts = assign_zoned_materials(terrain, image)

    rng = random.Random(180427)
    tree_placements, tree_templates = place_trees(terrain, export_collection, template_collection, rng)
    riparian_stones, stone_templates = place_riparian_boulders(terrain, export_collection, template_collection, rng)
    hydrology["riparian_stone_count"] = len(riparian_stones)
    hydrology["riparian_stones"] = riparian_stones
    riparian_ferns, fern_templates = place_riparian_ferns(terrain, export_collection, template_collection, rng)
    hydrology["riparian_fern_count"] = len(riparian_ferns)
    hydrology["riparian_ferns"] = riparian_ferns
    grass_records, grass_templates = place_grass_tufts(terrain, export_collection, template_collection, rng)
    template_count = len(tree_templates) + len(stone_templates) + len(fern_templates) + len(grass_templates)
    for obj in list(template_collection.objects):
        obj.hide_render = True
        obj.hide_set(True)

    # A visible scene note carries the future footprint-clearing handoff into Blender.
    mask_note = bpy.data.objects.new("Building_Footprint_Mask_Interface", None)
    presentation_collection.objects.link(mask_note)
    mask_note.empty_display_type = "PLAIN_AXES"
    mask_note.empty_display_size = 0.0
    mask_note["purpose"] = "Add building rectangles to BUILDING_FOOTPRINTS_M in Gate24_basin_woodland_stream.py and rerun to clear 3D grass tufts."
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
        "gate": "Gate24",
        "asset": "LastLandfall_Island_GrassCoverage",
        "generated_at_local": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "blender_version": bpy.app.version_string,
        "source_scene": str(BASE_BLEND),
        "terrain_mesh_vertices_edited": True,
        "terrain_hydrology_sculpt": sculpt_stats,
        "surface_zones_face_counts": zone_counts,
        "surface_design": {
            "zones": ["lowland meadow", "dry highland grass", "coastal sand and soil", "exposed rock", "wet rock"],
            "grass_texture_tiles_across_island": TEXTURE_TILES,
            "grass_texture_detail_mix": 0.10,
            "continuous_surface_material": True,
        },
        "basin_hydrology": hydrology,
        "build_clearing": {
            "center_m": list(BUILD_CLEARING_CENTER),
            "radii_m": list(BUILD_CLEARING_RADII_M),
            "area_kept_clear_of_trees": True,
        },
        "tree_layout": {
            "total": len(tree_placements),
            "counts_by_asset": counts_by_tree,
            "counts_by_grove": counts_by_grove,
            "basin_has_the_highest_tree_count": True,
            "basin_woodland_uses_broadleaf_species_around_stream_and_pond": True,
            "small_build_clearing_and_southwest_landing_corridor_kept_clear_of_trees": True,
            "placements": tree_placements,
        },
        "grass_tufts": {
            "total": len(grass_records),
            "counts_by_asset": counts_by_grass,
            "cluster_count": len({record["cluster_id"] for record in grass_records}),
            "placement": "irregular terrain-sampled groups on dry gentle meadow and basin banks; water and tree trunks remain clear",
            "building_footprint_mask": {
                "interface": "BUILDING_FOOTPRINTS_M in Gate24_carved_water_basin.py",
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
        "status": "PASS" if len(tree_placements) == sum(len(grove["assets"]) for grove in TREE_GROVES) and len(grass_records) > 100 and hydrology["stream_objects"] >= 3 and sculpt_stats["vertices_adjusted"] > 0 else "REVIEW",
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    HANDOFF_PATH.write_text(
        "# Gate24 Basin Woodland and Riparian Handoff\n\n"
        "## Files\n\n"
        f"- Blender scene: `{SCENE_PATH.name}`\n"
        f"- Unity import candidate: `{FBX_PATH.name}` (grass albedo is embedded in the FBX)\n"
        f"- Overview preview: `{PREVIEW_PATH.name}`\n"
        f"- QA and placements: `{REPORT_PATH.name}`\n"
        f"- Grass albedo source: `{TEXTURE_PATH.name}`\n\n"
        "## What changed\n\n"
        "- The terrain uses smoothly blended vertex-painted zones: meadow, dry highland grass, coastal soil, exposed rock, and wet rock. The color attributes travel with the FBX mesh.\n"
        f"- The hand-painted grass image repeats {TEXTURE_TILES:g} times across the island and contributes only 10% surface detail, reducing the previous dense mottling and repetition.\n"
        f"- {len(tree_placements)} trees are arranged with the densest broadleaf woodland in the sheltered basin; the ridge and coast groves remain lighter.\n"
        f"- A small spring-fed pond and narrow, gently meandering creek occupy only part of the basin. A broad damp-meadow and silty-bank color transition softens their edges; the pond bowl and creek bed are carved into this exported candidate mesh. Subtle vertex colors shade shallow edges lighter than the deeper centers, so the water gradient travels in the FBX. {len(riparian_stones)} larger basalt clusters and slabs anchor selected bends, with {len(riparian_ferns)} shade-loving ferns on damp banks. The source terrain remains unchanged.\n"
        f"- {len(grass_records)} linked 3D coastal-grass tufts are grouped into irregular clumps on dry meadow and stream-bank zones.\n\n"
        "## Building footprints\n\n"
        f"A small tree-free meadow remains near `{BUILD_CLEARING_CENTER[0]:.1f}, {BUILD_CLEARING_CENTER[1]:.1f}` m. Add each future footprint to `BUILDING_FOOTPRINTS_M` in `{Path(__file__).name}` with `name`, center `x`/`y`, `half_width_m`, `half_depth_m`, and optional `rotation_degrees`; rerunning clears only 3D grass tufts inside the footprint plus a 0.5 m margin. The continuous terrain material remains underneath, so foundations can cover it.\n\n"
        "## Import note\n\n"
        "The FBX contains the terrain and environment mesh objects, excludes the preview ocean, camera, sun, and hidden source templates, and embeds the grass albedo image. Blender procedural rock shading may simplify to material color during FBX import; the rock zone still has its own exported material slot.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "gate": "Gate24", "status": report["status"], "trees": len(tree_placements),
        "tree_groves": counts_by_grove, "grass_tufts": len(grass_records),
        "grass_clusters": len({record["cluster_id"] for record in grass_records}),
        "hydrology": hydrology,
        "terrain_zones": zone_counts, "fbx": export_stats,
        "preview": str(PREVIEW_PATH), "blend": str(SCENE_PATH),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()






