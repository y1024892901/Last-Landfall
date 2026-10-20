# -*- coding: utf-8 -*-
"""Build one original low-poly nature asset per invocation in Blender 5.2.2.

Each invocation creates a new mesh from procedural geometry. Existing OBJ/MTL
files are read only for the art palette and target dimensions; no source mesh
geometry is copied or altered.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

import bpy
import bmesh
from mathutils import Vector


ROOT = Path(r"D:\Last Landfall")
if "__file__" in globals():
    for parent in Path(__file__).resolve().parents:
        if (parent / "Assets" / "LastLandfall").is_dir():
            ROOT = parent
            break
NATURE = ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Nature"
OUT = ROOT / "work" / "island_final_candidate"
GEN_DIR = OUT / "Assets_Generated"
SCRIPT_DIR = OUT / "Scripts"
PREVIEW_DIR = OUT / "Previews_Generated"
REPORT_DIR = OUT / "Reports_Generated"


class MeshBuilder:
    def __init__(self) -> None:
        self.vertices: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, int, int]] = []
        self.materials: list[str] = []

    def vertex(self, point: Vector | tuple[float, float, float]) -> int:
        p = Vector(point)
        self.vertices.append((float(p.x), float(p.y), float(p.z)))
        return len(self.vertices) - 1

    def tri(self, a: int, b: int, c: int, material: str) -> None:
        self.faces.append((a, b, c))
        self.materials.append(material)

    def quad(self, a: int, b: int, c: int, d: int, material: str) -> None:
        self.tri(a, b, c, material)
        self.tri(a, c, d, material)


def add_tube(
    mesh: MeshBuilder,
    points: list[Vector],
    radii: list[float],
    material: str,
    sides: int = 6,
    accent: str | None = None,
    phase: float = 0.0,
) -> None:
    if len(points) < 2:
        return
    rings: list[list[int]] = []
    for i, point in enumerate(points):
        tangent = (points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]).normalized()
        reference = Vector((0, 0, 1))
        if abs(tangent.dot(reference)) > 0.92:
            reference = Vector((0, 1, 0))
        axis_u = tangent.cross(reference).normalized()
        axis_v = tangent.cross(axis_u).normalized()
        ring: list[int] = []
        for side in range(sides):
            angle = phase + math.tau * side / sides
            radial = axis_u * math.cos(angle) + axis_v * math.sin(angle)
            ring.append(mesh.vertex(point + radial * radii[i]))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for side in range(sides):
            nxt = (side + 1) % sides
            mat = accent if accent and (side + i) % 4 == 0 else material
            mesh.quad(rings[i][side], rings[i + 1][side], rings[i + 1][nxt], rings[i][nxt], mat)
    start_center = mesh.vertex(points[0])
    end_center = mesh.vertex(points[-1])
    for side in range(sides):
        nxt = (side + 1) % sides
        mesh.tri(start_center, rings[0][nxt], rings[0][side], material)
        mesh.tri(end_center, rings[-1][side], rings[-1][nxt], accent or material)


def add_leaf(
    mesh: MeshBuilder,
    base: Vector,
    tip: Vector,
    width: float,
    front: str,
    back: str,
) -> None:
    axis = tip - base
    if axis.length < 1e-5:
        return
    axis.normalize()
    side = axis.cross(Vector((0, 0, 1)))
    if side.length < 1e-4:
        side = axis.cross(Vector((0, 1, 0)))
    side.normalize()
    normal = side.cross(axis).normalized()
    ridge = base.lerp(tip, 0.52) + normal * width * 0.11
    left = ridge + side * width * 0.5
    right = ridge - side * width * 0.5
    top_points = [base, tip, ridge, left, right]
    bottom_points = [p - normal * max(0.0015, width * 0.07) for p in top_points]
    top = [mesh.vertex(p) for p in top_points]
    bottom = [mesh.vertex(p) for p in bottom_points]
    top_tris = [(0, 3, 2), (3, 1, 2), (2, 1, 4), (4, 0, 2)]
    for a, b, c in top_tris:
        mesh.tri(top[a], top[b], top[c], front)
        mesh.tri(bottom[c], bottom[b], bottom[a], back)
    outline = [0, 3, 1, 4]
    for i, a in enumerate(outline):
        b = outline[(i + 1) % len(outline)]
        mesh.quad(top[a], bottom[a], bottom[b], top[b], back)


def add_icosphere_component(
    mesh: MeshBuilder,
    center: Vector,
    scale: Vector,
    seed: int,
    materials: dict[str, tuple[float, float, float]],
    style: str,
    subdivisions: int = 2,
    rotation: float = 0.0,
) -> None:
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    turn = math.cos(rotation), math.sin(rotation)
    local: list[Vector] = []
    for i, vertex in enumerate(bm.verts):
        p = vertex.co.copy()
        jitter = 1.0 + rng.uniform(-0.16, 0.16)
        p *= jitter
        if style in ("boulder_a", "cluster"):
            p.x *= 1.0 + 0.10 * math.sin(i * 1.7 + seed)
            p.y *= 1.0 + 0.08 * math.cos(i * 2.1 + seed)
            if p.z < -0.22:
                p.z = -0.22 + (p.z + 0.22) * 0.24
        elif style == "boulder_b":
            p.z *= 0.74
            if p.z < -0.40:
                p.z = -0.40 + (p.z + 0.40) * 0.17
            p.x *= 1.10
        elif style == "slab":
            p.z *= 0.31
            p.x *= 1.0 + 0.07 * math.sin(i * 1.9)
            if p.z < -0.18:
                p.z = -0.18 + (p.z + 0.18) * 0.12
        x = p.x * turn[0] - p.y * turn[1]
        y = p.x * turn[1] + p.y * turn[0]
        local.append(center + Vector((x * scale.x, y * scale.y, p.z * scale.z)))
    vertex_map = [mesh.vertex(p) for p in local]
    salt = "rock_salt" if "rock_salt" in materials else "rock_sun"
    base = "rock" if "rock" in materials else next(iter(materials))
    shadow = "rock_shadow" if "rock_shadow" in materials else base
    for face_index, face in enumerate(bm.faces):
        indices = [vertex_map[v.index] for v in face.verts]
        if len(indices) != 3:
            continue
        z_normal = face.normal.z
        roll = rng.random()
        if z_normal > 0.48 and roll < 0.44:
            mat = salt
        elif z_normal > 0.20 and roll < 0.66:
            mat = "rock_sun" if "rock_sun" in materials else base
        elif z_normal < -0.20 and roll < 0.62:
            mat = shadow
        else:
            mat = base
        mesh.tri(indices[0], indices[1], indices[2], mat)
    bm.free()


def select_material(materials: dict[str, tuple[float, float, float]], *hints: str, default: str | None = None) -> str:
    for hint in hints:
        for name in materials:
            if hint.lower() in name.lower():
                return name
    if default and default in materials:
        return default
    return next(iter(materials))


def make_fern(mesh: MeshBuilder, materials: dict[str, tuple[float, float, float]], target: Vector) -> None:
    rng = random.Random(4917)
    grass = select_material(materials, "grass", default="grass")
    sun = select_material(materials, "grass_sun", default=grass)
    deep = select_material(materials, "leaf_deep", default=grass)
    fronds = 8
    for i in range(fronds):
        angle = math.tau * i / fronds + rng.uniform(-0.12, 0.12)
        direction = Vector((math.cos(angle), math.sin(angle), 0))
        lateral = Vector((-direction.y, direction.x, 0))
        length = rng.uniform(0.66, 0.91)
        height = rng.uniform(0.48, 0.62)
        points = []
        for step in range(10):
            t = step / 9
            z = 0.018 + height * (math.sin(t * math.pi * 0.55) ** 1.03)
            points.append(direction * length * t + Vector((0, 0, z)))
        radii = [0.0085 * (1 - step / 10) + 0.0012 for step in range(10)]
        add_tube(mesh, points, radii, grass, sides=6, accent=sun, phase=angle * 0.3)
        for row in range(7):
            t = 0.20 + row * 0.098
            idx = min(round(t * 9), 9)
            joint = points[idx]
            fullness = math.sin(math.pi * t) ** 0.8
            leaflet = (0.15 + 0.19 * fullness) * rng.uniform(0.88, 1.12)
            for side_sign in (-1, 1):
                base = joint + lateral * (side_sign * 0.006)
                tip = joint + lateral * (side_sign * leaflet * 0.82) + direction * (leaflet * 0.29) + Vector((0, 0, leaflet * 0.18))
                front = sun if (row + i) % 4 == 0 else grass
                add_leaf(mesh, base, tip, leaflet * 0.60, front, deep)
    # Two younger central fronds stand more upright to give the clump a readable crown.
    for i in range(2):
        angle = i * math.pi + 0.34
        direction = Vector((math.cos(angle), math.sin(angle), 0))
        lateral = Vector((-direction.y, direction.x, 0))
        length = 0.46 + i * 0.07
        points = [direction * length * t + Vector((0, 0, 0.02 + 0.59 * t)) for t in [j / 9 for j in range(10)]]
        add_tube(mesh, points, [0.007 * (1 - j / 10) + 0.001 for j in range(10)], grass, sides=6, accent=sun)
        for row, t in enumerate((0.24, 0.38, 0.52, 0.66, 0.78)):
            joint = points[round(t * 9)]
            leaflet = 0.13 * math.sin(math.pi * t) + 0.055
            for sign in (-1, 1):
                tip = joint + lateral * (sign * leaflet * 0.78) + direction * (leaflet * 0.27) + Vector((0, 0, leaflet * 0.2))
                add_leaf(mesh, joint, tip, leaflet * 0.38, sun if row % 3 == 0 else grass, deep)


def add_colored_icosphere(
    mesh: MeshBuilder, center: Vector, scale: Vector, material: str,
    seed: int = 1, subdivisions: int = 1, roughness: float = 0.0,
) -> None:
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    positions = []
    for i, vert in enumerate(bm.verts):
        p = vert.co.copy()
        p *= 1.0 + rng.uniform(-roughness, roughness)
        positions.append(center + Vector((p.x * scale.x, p.y * scale.y, p.z * scale.z)))
    mapping = [mesh.vertex(p) for p in positions]
    for face in bm.faces:
        indices = [mapping[v.index] for v in face.verts]
        for i in range(1, len(indices) - 1):
            mesh.tri(indices[0], indices[i], indices[i + 1], material)
    bm.free()


def make_wildflower(
    mesh: MeshBuilder, materials: dict[str, tuple[float, float, float]],
    target: Vector, lilac_gold: bool,
) -> None:
    rng = random.Random(8842 if lilac_gold else 7135)
    grass = select_material(materials, "grass", default=next(iter(materials)))
    grass_sun = select_material(materials, "grass_sun", default=grass)
    stem_mat = select_material(materials, "bark_sun", "stem", default=grass)
    cream = select_material(materials, "flower_cream", default=grass_sun)
    coral = select_material(materials, "flower_lilac" if lilac_gold else "flower_coral", default=cream)
    gold = select_material(materials, "flower_gold", "flower_center", default=cream)
    center_mat = select_material(materials, "flower_center", default=gold)

    stems = [
        (-0.24, -0.18, 0.72), (-0.08, 0.18, 0.89), (0.16, -0.05, 0.78),
        (0.26, 0.16, 0.66), (-0.20, 0.10, 0.59),
    ]
    for stem_index, (ox, oy, height_factor) in enumerate(stems):
        height = target.z * height_factor
        lean = Vector((rng.uniform(-0.07, 0.07), rng.uniform(-0.07, 0.07), 0))
        origin = Vector((ox * target.x, oy * target.y, 0.012))
        path = []
        for step in range(7):
            t = step / 6
            curve = Vector((lean.x * t * t, lean.y * t * t, height * t))
            path.append(origin + curve)
        add_tube(mesh, path, [0.0075 * (1 - i / 7) + 0.0018 for i in range(7)], stem_mat, sides=5, accent=grass_sun)

        # Two staggered pairs of pointed leaves on each stem.
        for leaf_row, t in enumerate((0.18, 0.34, 0.50, 0.64)):
            joint = path[round(t * 6)]
            side_axis = Vector((math.cos(stem_index * 1.2 + leaf_row * 0.6), math.sin(stem_index * 1.2 + leaf_row * 0.6), 0))
            leaf_len = target.z * (0.16 - leaf_row * 0.018) * rng.uniform(0.88, 1.10)
            for sign in (-1, 1):
                tip = joint + side_axis * (sign * leaf_len * 0.76) + Vector((0, 0, leaf_len * 0.23))
                add_leaf(mesh, joint, tip, leaf_len * 0.34, grass_sun if leaf_row == 0 else grass, grass)

        head = path[-1]
        # Alternating coral/cream or lilac/gold flower heads, each with two low-poly petal rings.
        for layer in range(2):
            petals = 8 if layer == 0 else 7
            radius = target.x * (0.092 if layer == 0 else 0.073)
            z = head.z + layer * target.z * 0.012
            for petal in range(petals):
                angle = math.tau * (petal / petals) + layer * 0.23 + stem_index * 0.19
                radial = Vector((math.cos(angle), math.sin(angle), 0))
                base = head + radial * radius * 0.08 + Vector((0, 0, z - head.z))
                tip = head + radial * radius + Vector((0, 0, z - head.z + target.z * 0.012))
                front = coral if ((petal + stem_index + layer) % 3 != 0) else cream
                if lilac_gold and (petal + layer) % 4 == 0:
                    front = gold
                add_leaf(mesh, base, tip, radius * (0.50 if layer == 0 else 0.43), front, cream)
        add_colored_icosphere(
            mesh, head + Vector((0, 0, target.z * 0.014)),
            Vector((target.x * 0.022, target.x * 0.022, target.x * 0.020)),
            center_mat, seed=stem_index + (31 if lilac_gold else 17), subdivisions=2, roughness=0.08,
        )
        # Small green calyx under each flower head.
        add_colored_icosphere(mesh, head - Vector((0, 0, target.z * 0.018)),
                              Vector((target.x * 0.020, target.x * 0.020, target.z * 0.020)),
                              grass, seed=stem_index + 50, subdivisions=1, roughness=0.06)


def make_boulder(
    mesh: MeshBuilder, materials: dict[str, tuple[float, float, float]], target: Vector, variant: str,
) -> None:
    center = Vector((0.0, 0.0, target.z * 0.49))
    scale = Vector((target.x * 0.51, target.y * 0.51, target.z * 0.62))
    style = "boulder_a" if variant == "A" else "boulder_b"
    add_icosphere_component(mesh, center, scale, seed=9201 if variant == "A" else 9217,
                            materials=materials, style=style, subdivisions=3,
                            rotation=0.12 if variant == "A" else -0.20)


def make_tideworn_slab(
    mesh: MeshBuilder, materials: dict[str, tuple[float, float, float]], target: Vector,
) -> None:
    center = Vector((0.0, 0.0, target.z * 0.48))
    scale = Vector((target.x * 0.53, target.y * 0.52, target.z * 0.73))
    add_icosphere_component(mesh, center, scale, seed=17763, materials=materials,
                            style="slab", subdivisions=3, rotation=0.08)


def make_rock_cluster(
    mesh: MeshBuilder, materials: dict[str, tuple[float, float, float]], target: Vector,
) -> None:
    components = [
        (Vector((-0.25, -0.10, 0.28)), Vector((0.34, 0.39, 0.48)), 201, 0.2),
        (Vector((0.22, -0.15, 0.25)), Vector((0.37, 0.34, 0.41)), 202, -0.3),
        (Vector((0.02, 0.22, 0.22)), Vector((0.40, 0.35, 0.38)), 203, 0.5),
        (Vector((-0.10, 0.05, 0.55)), Vector((0.29, 0.30, 0.44)), 204, -0.1),
        (Vector((0.34, 0.20, 0.15)), Vector((0.23, 0.26, 0.31)), 205, 0.7),
    ]
    for center, scale, seed, angle in components:
        add_icosphere_component(mesh, center, scale, seed=seed, materials=materials,
                                style="cluster", subdivisions=2, rotation=angle)


def make_driftwood(
    mesh: MeshBuilder, materials: dict[str, tuple[float, float, float]], target: Vector,
) -> None:
    rng = random.Random(16440)
    bark = select_material(materials, "driftwood", default=next(iter(materials)))
    sun = select_material(materials, "driftwood_sun", default=bark)
    main = [
        Vector((-0.80, 0.02, 0.15)), Vector((-0.60, 0.04, 0.17)),
        Vector((-0.36, 0.02, 0.12)), Vector((-0.10, 0.00, 0.14)),
        Vector((0.17, -0.03, 0.16)), Vector((0.43, -0.06, 0.14)),
        Vector((0.70, -0.08, 0.13)),
    ]
    radii = [0.115, 0.135, 0.126, 0.111, 0.096, 0.078, 0.058]
    add_tube(mesh, main, radii, bark, sides=9, accent=sun, phase=0.17)
    # Two broken branches fork away from the salt-worn main log.
    forks = [
        ([Vector((0.16, -0.02, 0.16)), Vector((0.30, 0.11, 0.22)), Vector((0.46, 0.19, 0.35)), Vector((0.62, 0.20, 0.41))], [0.068, 0.052, 0.029, 0.009]),
        ([Vector((-0.39, 0.03, 0.14)), Vector((-0.47, -0.11, 0.23)), Vector((-0.55, -0.24, 0.30))], [0.061, 0.041, 0.012]),
    ]
    for path, radii_fork in forks:
        add_tube(mesh, path, radii_fork, bark, sides=7, accent=sun, phase=0.29)

    # Raised longitudinal grain strips and knots keep the silhouette readable at game scale.
    for offset_y, offset_z in ((0.0, 0.11), (0.085, 0.07), (-0.085, 0.07)):
        strip = [Vector((p.x, p.y + offset_y, p.z + offset_z)) for p in main]
        add_tube(mesh, strip, [0.0065 * (1 - i / 8) + 0.001 for i in range(len(strip))], sun, sides=5)
    for i, center in enumerate((Vector((-0.48, -0.02, 0.24)), Vector((0.02, 0.04, 0.27)), Vector((0.42, -0.04, 0.22)))):
        add_colored_icosphere(mesh, center, Vector((0.032, 0.018, 0.018)), sun, seed=330 + i, subdivisions=1, roughness=0.16)

    # Splintered fibers at both cut ends; all remain within the requested target envelope after scaling.
    for end_x, direction_sign in ((-0.80, -1), (0.70, 1)):
        for shard in range(5):
            angle = math.tau * shard / 5 + rng.uniform(-0.13, 0.13)
            side = Vector((0, math.cos(angle), math.sin(angle)))
            start = Vector((end_x, -0.08, 0.14)) + side * 0.045
            tip = start + Vector((direction_sign * rng.uniform(0.045, 0.11), side.y * 0.045, side.z * 0.055))
            add_tube(mesh, [start, start.lerp(tip, 0.60), tip], [0.018, 0.009, 0.0015], sun, sides=5)


def read_design_data(asset: str) -> tuple[dict[str, tuple[float, float, float]], dict[str, Any]]:
    mtl_path = NATURE / f"{asset}.mtl"
    manifest_path = NATURE / "asset_manifest.json"
    if not mtl_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(f"Missing design reference material or manifest for {asset}")
    colors: dict[str, tuple[float, float, float]] = {}
    current = None
    for raw in mtl_path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.strip().split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0].lower() == "newmtl" and len(parts) > 1:
            current = " ".join(parts[1:])
        elif parts[0].lower() == "kd" and current and len(parts) >= 4:
            colors[current] = tuple(float(c) for c in parts[1:4])
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = data["assets"] if isinstance(data, dict) else data
    entry = next((item for item in entries if item.get("name") == asset), None)
    if entry is None or not colors:
        raise ValueError(f"No manifest entry or Kd colors found for {asset}")
    entry["_mtl_path"] = str(mtl_path)
    entry["_mtl_sha256"] = hashlib.sha256(mtl_path.read_bytes()).hexdigest()
    return colors, entry


def build_mesh(asset: str, materials: dict[str, tuple[float, float, float]], entry: dict[str, Any]) -> tuple[MeshBuilder, Vector]:
    dims = entry.get("dimensions_m", {})
    # Source manifest uses Y-up; Blender candidates use Z-up.
    target = Vector((float(dims["x"]), float(dims["z"]), float(dims["y"])))
    builder = MeshBuilder()
    if asset == "Fern_Cliffside":
        make_fern(builder, materials, target)
    elif asset == "Wildflower_CoralCream":
        make_wildflower(builder, materials, target, lilac_gold=False)
    elif asset == "Wildflower_LilacGold":
        make_wildflower(builder, materials, target, lilac_gold=True)
    elif asset == "Basalt_Boulder_A":
        make_boulder(builder, materials, target, variant="A")
    elif asset == "Basalt_Boulder_B":
        make_boulder(builder, materials, target, variant="B")
    elif asset == "Basalt_TidewornSlab":
        make_tideworn_slab(builder, materials, target)
    elif asset == "Basalt_RockCluster":
        make_rock_cluster(builder, materials, target)
    elif asset == "Driftwood_BrokenSaltLog":
        make_driftwood(builder, materials, target)
    else:
        raise ValueError(f"No procedural builder is registered for {asset}")
    if not builder.vertices or not builder.faces:
        raise RuntimeError(f"Builder produced an empty mesh: {asset}")
    points = [Vector(v) for v in builder.vertices]
    minimum = [min(p[i] for p in points) for i in range(3)]
    maximum = [max(p[i] for p in points) for i in range(3)]
    size = [maximum[i] - minimum[i] for i in range(3)]
    factors = [target[i] / size[i] if size[i] > 1e-8 else 1.0 for i in range(3)]
    builder.vertices = [
        ((v[0] - minimum[0] * 0.5 - maximum[0] * 0.5) * factors[0],
         (v[1] - minimum[1] * 0.5 - maximum[1] * 0.5) * factors[1],
         (v[2] - minimum[2]) * factors[2])
        for v in builder.vertices
    ]
    return builder, target


def create_blender_material(name: str, rgb: tuple[float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = (*rgb, 1.0)
    mat.roughness = 0.88
    shader = next((node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader:
        shader.inputs["Base Color"].default_value = (*rgb, 1.0)
        shader.inputs["Roughness"].default_value = 0.88
    return mat


def fresh_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.context.preferences.filepaths.save_version = 0


def bounds(obj: bpy.types.Object) -> tuple[list[float], list[float], list[float]]:
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    mins = [min(p[i] for p in points) for i in range(3)]
    maxs = [max(p[i] for p in points) for i in range(3)]
    return mins, maxs, [maxs[i] - mins[i] for i in range(3)]


def render_studio(asset: bpy.types.Object, target: Vector, output: Path) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.compression = 18
    scene.render.film_transparent = False
    scene.render.filepath = str(output)
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.studio_light = "basic.sl"
    shading.color_type = "MATERIAL"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "WORLD"
    shading.curvature_ridge_factor = 1.15
    shading.curvature_valley_factor = 0.9
    shading.background_type = "WORLD"

    world = bpy.data.worlds.new("Generated_Asset_Background")
    scene.world = world
    world.color = (0.84, 0.83, 0.77)
    ground_mesh = bpy.data.meshes.new("Preview_Ground_Mesh")
    ground_mesh.from_pydata([(-6, -6, -0.006), (6, -6, -0.006), (6, 6, -0.006), (-6, 6, -0.006)], [], [(0, 1, 2, 3)])
    ground_mesh.materials.append(create_blender_material("Preview_Ground", (0.90, 0.88, 0.80)))
    ground = bpy.data.objects.new("Preview_Ground (not exported)", ground_mesh)
    bpy.context.collection.objects.link(ground)

    camera_data = bpy.data.cameras.new("Preview_Camera")
    camera_data.type = "ORTHO"
    framing_span = max(target.x, target.y, target.z * 1.7)
    camera_data.ortho_scale = framing_span * 1.5
    camera = bpy.data.objects.new("Preview_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    target_point = Vector((0, 0, target.z * 0.50))
    camera.location = Vector((max(target) * 1.65, -max(target) * 2.1, target.z * 1.7 + 0.8))
    camera.rotation_euler = (target_point - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera


def run(asset: str, gate: str) -> dict[str, Any]:
    for directory in (GEN_DIR, SCRIPT_DIR, PREVIEW_DIR, REPORT_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    colors, entry = read_design_data(asset)
    builder, target = build_mesh(asset, colors, entry)
    fresh_scene()
    mesh = bpy.data.meshes.new(asset)
    mesh.from_pydata(builder.vertices, [], builder.faces)
    mesh.update(calc_edges=True)
    used_materials = list(dict.fromkeys(builder.materials))
    for name in used_materials:
        if name not in colors:
            raise KeyError(f"Generated geometry references missing palette entry {name!r}")
        mesh.materials.append(create_blender_material(name, colors[name]))
    slots = {mat.name: idx for idx, mat in enumerate(mesh.materials)}
    for polygon, material_name in zip(mesh.polygons, builder.materials):
        polygon.material_index = slots[material_name]
        polygon.use_smooth = False
    mesh.calc_loop_triangles()
    obj = bpy.data.objects.new(asset, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)
    obj["model_type"] = "procedurally generated original candidate"
    obj["design_reference"] = "Last Landfall nature asset manifest dimensions and MTL palette only"
    obj["source_mesh_copied"] = False
    obj["origin_z"] = 0.0
    bpy.context.view_layer.update()
    bbox_min, bbox_max, actual_dims = bounds(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    degenerate = sum(1 for face in bm.faces if face.calc_area() <= 1e-12)
    non_manifold = sum(1 for edge in bm.edges if not edge.is_manifold)
    boundary = sum(1 for edge in bm.edges if edge.is_boundary)
    bm.free()
    non_finite = sum(1 for vertex in mesh.vertices if not all(math.isfinite(v) for v in vertex.co))

    material_report = []
    color_match = True
    for mat in mesh.materials:
        expected = colors[mat.name]
        shader = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        observed = tuple(float(v) for v in shader.inputs["Base Color"].default_value[:3]) if shader else tuple(mat.diffuse_color[:3])
        match = all(abs(expected[i] - observed[i]) <= 1e-6 for i in range(3))
        color_match = color_match and match
        material_report.append({"name": mat.name, "mtl_Kd": list(expected), "blender_base_color": list(observed), "match": match})

    gate_number = int(gate.removeprefix("Gate"))
    blend_path = GEN_DIR / f"{asset}.blend"
    fbx_path = GEN_DIR / f"{asset}.fbx"
    preview_path = PREVIEW_DIR / f"{gate}_{asset}.png"
    report_path = REPORT_DIR / f"{gate}_generated_qa.json"

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    export_result = bpy.ops.export_scene.fbx(
        filepath=str(fbx_path), use_selection=True, global_scale=1.0,
        apply_unit_scale=True, axis_forward="-Z", axis_up="Y",
        object_types={"MESH"}, mesh_smooth_type="OFF", bake_space_transform=False,
        add_leaf_bones=False, use_mesh_modifiers=True, path_mode="AUTO",
    )
    if "FINISHED" not in export_result:
        raise RuntimeError(f"FBX export failed for {asset}: {export_result}")
    before_import = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(fbx_path))
    imported = [item for item in bpy.data.objects if item not in before_import and item.type == "MESH"]
    if not imported:
        raise RuntimeError(f"FBX roundtrip created no mesh for {asset}")
    imported[0].data.calc_loop_triangles()
    round_min, round_max, round_dims = bounds(imported[0])
    roundtrip = {
        "vertices": len(imported[0].data.vertices),
        "edges": len(imported[0].data.edges),
        "triangles": len(imported[0].data.loop_triangles),
        "bbox_min_m": round_min,
        "bbox_max_m": round_max,
        "dimensions_m": round_dims,
    }
    fbx_match = (
        roundtrip["vertices"] == len(mesh.vertices)
        and roundtrip["triangles"] == len(mesh.loop_triangles)
        and all(abs(round_dims[i] - actual_dims[i]) <= 1e-4 for i in range(3))
        and all(abs(round_min[i] - bbox_min[i]) <= 1e-4 for i in range(3))
        and all(abs(round_max[i] - bbox_max[i]) <= 1e-4 for i in range(3))
    )
    for item in imported:
        bpy.data.objects.remove(item, do_unlink=True)

    render_studio(obj, target, preview_path)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), compress=True)
    dim_match = all(abs(actual_dims[i] - target[i]) <= 1e-4 for i in range(3))
    floor_pass = abs(bbox_min[2]) <= 0.002
    complexity_pass = len(mesh.loop_triangles) >= 250
    checks = {
        "dimensions_match_manifest_target": dim_match,
        "generated_mesh_has_sufficient_detail": complexity_pass,
        "material_colors_match_source_palette": color_match,
        "no_degenerate_faces": degenerate == 0,
        "all_vertices_finite": non_finite == 0,
        "fbx_reimport_matches": fbx_match,
        "floor_alignment_within_2mm": floor_pass,
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    report = {
        "gate": gate,
        "asset": asset,
        "generated_at_local": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "blender_version": bpy.app.version_string,
        "method": "locally authored procedural Blender Python; new geometry; no Gemini used",
        "source_reference": {
            "manifest_entry": {k: v for k, v in entry.items() if not k.startswith("_")},
            "mtl_path": entry["_mtl_path"],
            "mtl_sha256": entry["_mtl_sha256"],
            "source_mesh_copied": False,
        },
        "generated_mesh": {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
            "triangles": len(mesh.loop_triangles),
            "bbox_min_m": bbox_min,
            "bbox_max_m": bbox_max,
            "dimensions_m": actual_dims,
            "target_dimensions_zup_m": list(target),
            "materials": material_report,
            "topology_diagnostics": {"non_manifold_edges": non_manifold, "boundary_edges": boundary, "degenerate_faces": degenerate},
        },
        "fbx_roundtrip": {**roundtrip, "matches_generated_mesh": fbx_match},
        "floor_alignment": {"min_z_m": bbox_min[2], "tolerance_m": 0.002, "passed": floor_pass},
        "deliverables": {"blend": str(blend_path), "fbx": str(fbx_path), "preview_png": str(preview_path), "qa_report": str(report_path)},
        "checks": checks,
        "accepted": status == "PASS",
        "status": status,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"gate": gate, "asset": asset, "status": status, "checks": checks, "vertices": len(mesh.vertices), "triangles": len(mesh.loop_triangles), "dimensions_m": actual_dims, "deliverables": report["deliverables"]}, ensure_ascii=False))
    return report


def main() -> None:
    args_list = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True)
    parser.add_argument("--gate", required=True)
    parsed = parser.parse_args(args_list)
    run(parsed.asset, parsed.gate)


if __name__ == "__main__":
    main()
