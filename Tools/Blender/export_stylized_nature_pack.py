"""Build an original, game-ready low-poly nature set for Last Landfall.

This is an art-directed mesh generator, not a Blender add-on. It writes OBJ/MTL
assets with metre-scale dimensions and a Unity-friendly Y-up axis, plus a PNG
contact sheet. Run from the project root with:

    python Tools/Blender/export_stylized_nature_pack.py

The models are original and are not copies of any marketplace pack.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Nature"
PREVIEW_PATH = ROOT / "Assets" / "LastLandfall" / "Art" / "Previews" / "Nature" / "StylizedNaturePack.png"

# Muted coastal colours with deliberate light-side accents. Values are linear-ish
# display colours; each face gets one palette entry so the models stay readable
# without relying on Blender-only procedural shaders.
PALETTE = {
    "bark_shadow": (0.20, 0.16, 0.13),
    "bark": (0.34, 0.25, 0.18),
    "bark_sun": (0.48, 0.36, 0.24),
    "leaf_shadow": (0.14, 0.29, 0.23),
    "leaf_deep": (0.20, 0.39, 0.29),
    "leaf": (0.31, 0.50, 0.34),
    "leaf_sun": (0.48, 0.62, 0.39),
    "leaf_salt": (0.64, 0.68, 0.48),
    "grass_shadow": (0.24, 0.37, 0.26),
    "grass": (0.40, 0.53, 0.31),
    "grass_sun": (0.64, 0.67, 0.38),
    "flower_coral": (0.78, 0.37, 0.25),
    "flower_gold": (0.88, 0.66, 0.30),
    "flower_cream": (0.89, 0.79, 0.54),
    "flower_lilac": (0.55, 0.48, 0.63),
    "flower_center": (0.93, 0.75, 0.34),
    "rock_shadow": (0.20, 0.25, 0.25),
    "rock": (0.32, 0.38, 0.37),
    "rock_sun": (0.48, 0.52, 0.48),
    "rock_salt": (0.63, 0.63, 0.54),
    "driftwood": (0.39, 0.34, 0.27),
    "driftwood_sun": (0.57, 0.49, 0.37),
}


Vec3 = tuple[float, float, float]
Face = tuple[tuple[int, int, int], str]


@dataclass
class Mesh:
    name: str
    vertices: list[Vec3] = field(default_factory=list)
    faces: list[Face] = field(default_factory=list)
    used_materials: set[str] = field(default_factory=set)

    def vertex(self, point: Vec3) -> int:
        self.vertices.append(tuple(float(v) for v in point))
        return len(self.vertices) - 1

    def triangle(self, a: int, b: int, c: int, material: str,
                 outward: Vec3 | None = None) -> None:
        if outward is not None:
            pa, pb, pc = self.vertices[a], self.vertices[b], self.vertices[c]
            normal = cross(sub(pb, pa), sub(pc, pa))
            if dot(normal, outward) < 0.0:
                b, c = c, b
        self.faces.append(((a, b, c), material))
        self.used_materials.add(material)


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(v: Vec3, k: float) -> Vec3:
    return (v[0] * k, v[1] * k, v[2] * k)


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def length(v: Vec3) -> float:
    return math.sqrt(dot(v, v))


def normalize(v: Vec3) -> Vec3:
    n = length(v)
    if n < 1e-9:
        return (0.0, 1.0, 0.0)
    return (v[0] / n, v[1] / n, v[2] / n)


def mix(a: Vec3, b: Vec3, t: float) -> Vec3:
    return (a[0] * (1 - t) + b[0] * t,
            a[1] * (1 - t) + b[1] * t,
            a[2] * (1 - t) + b[2] * t)


def add_tapered_stem(mesh: Mesh, start: Vec3, end: Vec3, radius_start: float,
                     radius_end: float, material: str, rng: random.Random,
                     sides: int = 5, alternate: str | None = None) -> None:
    axis = normalize(sub(end, start))
    reference = (0.0, 0.0, 1.0) if abs(axis[1]) > 0.92 else (0.0, 1.0, 0.0)
    tangent = normalize(cross(axis, reference))
    bitangent = normalize(cross(axis, tangent))
    phase = rng.uniform(0.0, math.tau)
    lower, upper = [], []
    for center, radius, ring in ((start, radius_start, lower), (end, radius_end, upper)):
        for side in range(sides):
            angle = phase + math.tau * side / sides
            wobble = rng.uniform(0.94, 1.06)
            radial = add(mul(tangent, math.cos(angle)), mul(bitangent, math.sin(angle)))
            ring.append(mesh.vertex(add(center, mul(radial, radius * wobble))))
    center_start = mesh.vertex(start)
    center_end = mesh.vertex(end)
    for side in range(sides):
        nxt = (side + 1) % sides
        midpoint = mix(start, end, 0.5)
        radial = normalize(sub(mix(mesh.vertices[lower[side]], mesh.vertices[upper[nxt]], 0.5), midpoint))
        mat = alternate if alternate is not None and side in (1, 4) else material
        mesh.triangle(lower[side], lower[nxt], upper[nxt], mat, radial)
        mesh.triangle(lower[side], upper[nxt], upper[side], mat, radial)
        mesh.triangle(center_start, lower[nxt], lower[side], material, mul(axis, -1.0))
        mesh.triangle(center_end, upper[side], upper[nxt], alternate or material, axis)


def _ico_base() -> tuple[list[Vec3], list[tuple[int, int, int]]]:
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    vertices = [(-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
                (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
                (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1)]
    vertices = [normalize(tuple(map(float, v))) for v in vertices]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
             (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
             (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
             (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    return vertices, faces


def add_icosphere(mesh: Mesh, center: Vec3, radii: Vec3, rng: random.Random,
                  materials: tuple[str, ...], subdivisions: int = 1,
                  roughness: float = 0.08, yaw: float = 0.0) -> None:
    unit_vertices, faces = _ico_base()
    for _ in range(subdivisions):
        midpoint_cache: dict[tuple[int, int], int] = {}

        def midpoint(i: int, j: int) -> int:
            key = (min(i, j), max(i, j))
            if key not in midpoint_cache:
                p = normalize(mix(unit_vertices[i], unit_vertices[j], 0.5))
                midpoint_cache[key] = len(unit_vertices)
                unit_vertices.append(p)
            return midpoint_cache[key]

        refined = []
        for a, b, c in faces:
            ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
            refined.extend(((a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)))
        faces = refined

    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    deformed = []
    for x, y, z in unit_vertices:
        wobble = 1.0 + rng.uniform(-roughness, roughness)
        x, z = x * cos_y - z * sin_y, x * sin_y + z * cos_y
        deformed.append((center[0] + x * radii[0] * wobble,
                         center[1] + y * radii[1] * wobble,
                         center[2] + z * radii[2] * wobble))

    base = len(mesh.vertices)
    mesh.vertices.extend(deformed)
    light = normalize((-0.45, 0.82, 0.34))
    for a, b, c in faces:
        pa, pb, pc = deformed[a], deformed[b], deformed[c]
        face_normal = normalize(cross(sub(pb, pa), sub(pc, pa)))
        local_center = (center[0], center[1], center[2])
        outward = normalize(sub(mix(mix(pa, pb, 0.5), pc, 1 / 3), local_center))
        if dot(face_normal, outward) < 0:
            b, c = c, b
            face_normal = mul(face_normal, -1)
        shade = dot(face_normal, light)
        if shade > 0.48:
            mat = materials[-1]
        elif shade < -0.28:
            mat = materials[0]
        elif rng.random() < 0.12:
            mat = materials[rng.randrange(len(materials))]
        else:
            mat = materials[min(len(materials) - 1, max(0, int((shade + 0.55) * len(materials) / 1.45)))]
        mesh.triangle(base + a, base + b, base + c, mat, outward)


def add_conifer_tier(mesh: Mesh, base_y: float, radius: float, height: float,
                     wind: tuple[float, float], rng: random.Random,
                     tier_index: int) -> None:
    sides = 7
    phase = rng.uniform(0.0, math.tau)
    lower, shoulder = [], []
    for ring_index, (y, ring_radius) in enumerate(((base_y, radius),
                                                    (base_y + height * 0.33, radius * 0.68))):
        ring = lower if ring_index == 0 else shoulder
        for side in range(sides):
            angle = phase + math.tau * side / sides
            irregular = rng.uniform(0.90, 1.10)
            y_irregular = rng.uniform(-0.04, 0.03) * height if ring_index == 0 else 0.0
            shift = (wind[0] * (y - base_y), wind[1] * (y - base_y))
            ring.append(mesh.vertex((shift[0] + math.cos(angle) * ring_radius * irregular,
                                     y + y_irregular,
                                     shift[1] + math.sin(angle) * ring_radius * irregular)))
    tip_center = (wind[0] * height, base_y + height, wind[1] * height)
    tip = mesh.vertex(tip_center)
    palette = ("leaf_shadow", "leaf_deep", "leaf", "leaf_sun", "leaf_salt")
    for side in range(sides):
        nxt = (side + 1) % sides
        for lower_idx, upper_idx in ((lower, shoulder), (shoulder, [tip] * sides)):
            a = lower_idx[side]
            b = lower_idx[nxt]
            c = upper_idx[nxt]
            d = upper_idx[side]
            p = mesh.vertices[a]
            q = mesh.vertices[b]
            radial = normalize((p[0] + q[0], 0.0, p[2] + q[2]))
            material = palette[(side + tier_index + (1 if side % 3 == 0 else 0)) % len(palette)]
            if upper_idx is not None and upper_idx[side] == tip:
                mesh.triangle(a, b, tip, "leaf_sun" if side % 3 == 0 else "leaf", radial)
            else:
                mesh.triangle(a, b, c, material, radial)
                mesh.triangle(a, c, d, "leaf_sun" if (side + tier_index) % 4 == 0 else material, radial)


def build_pine(name: str, height: float, seed: int, lean: float,
               crown_width: float) -> Mesh:
    rng = random.Random(seed)
    mesh = Mesh(name)
    trunk_h = height * 0.88
    radius = height * 0.045
    add_tapered_stem(mesh, (0, 0, 0), (lean * 0.35, trunk_h, 0.0), radius,
                     radius * 0.23, "bark", rng, sides=6, alternate="bark_sun")
    tier_specs = ((0.21, 1.00, 0.36), (0.39, 0.82, 0.36),
                  (0.57, 0.64, 0.35), (0.74, 0.44, 0.31))
    for tier_index, (base_factor, radius_factor, h_factor) in enumerate(tier_specs):
        base = base_factor * height
        add_conifer_tier(mesh, base, crown_width * radius_factor,
                         h_factor * height, (lean / height * 0.22, 0.025),
                         rng, tier_index)
    # A few exposed, downward-swept branch tips break up the textbook cone.
    for branch_index in range(5):
        angle = math.tau * branch_index / 5 + rng.uniform(-0.18, 0.18)
        y = rng.uniform(0.24, 0.47) * height
        end = (math.cos(angle) * crown_width * 0.54 + lean * y / height,
               y - 0.07 * height,
               math.sin(angle) * crown_width * 0.54)
        add_tapered_stem(mesh, (lean * y / height * 0.30, y + 0.04 * height, 0), end,
                         radius * 0.38, radius * 0.10, "bark", rng, sides=4)
    return mesh


def build_broadleaf(name: str, seed: int, height: float, wind_x: float,
                    crown_scale: float, salt_tips: bool = False) -> Mesh:
    rng = random.Random(seed)
    mesh = Mesh(name)
    trunk_h = height * 0.48
    trunk_x = wind_x * 0.13
    add_tapered_stem(mesh, (0, 0, 0), (trunk_x, trunk_h, 0),
                     0.105, 0.045, "bark", rng, sides=6, alternate="bark_sun")
    crown_y = trunk_h + height * 0.24
    # Distinct lobe placements create a windswept, irregular silhouette rather
    # than a stack of generic spheres.
    if seed == 2201:
        lobes = [(-0.52, 0.02, 0.08, 0.53, 0.52, 0.48),
                 (0.10, 0.12, -0.12, 0.68, 0.57, 0.54),
                 (0.70, -0.05, 0.02, 0.48, 0.45, 0.41),
                 (0.08, 0.43, 0.02, 0.48, 0.49, 0.42)]
    else:
        lobes = [(-0.26, 0.08, 0.12, 0.56, 0.54, 0.52),
                 (0.26, -0.02, -0.14, 0.58, 0.53, 0.50),
                 (0.02, 0.38, 0.04, 0.48, 0.47, 0.44),
                 (-0.30, -0.15, -0.02, 0.42, 0.41, 0.39)]
    for idx, (x, y, z, rx, ry, rz) in enumerate(lobes):
        center = (trunk_x + x * crown_scale, crown_y + y * crown_scale,
                  z * crown_scale)
        colors = ("leaf_shadow", "leaf_deep", "leaf", "leaf_salt" if salt_tips and idx == 2 else "leaf_sun")
        add_icosphere(mesh, center,
                      (rx * crown_scale, ry * crown_scale, rz * crown_scale),
                      rng, colors, subdivisions=1, roughness=0.06, yaw=idx * 0.37)
    for branch_index in range(4):
        angle = math.tau * branch_index / 4 + 0.4
        reach = crown_scale * rng.uniform(0.38, 0.64)
        start = (trunk_x * 0.55, trunk_h * rng.uniform(0.66, 0.94), 0)
        end = (trunk_x + math.cos(angle) * reach + wind_x * 0.12,
               crown_y + rng.uniform(-0.04, 0.17), math.sin(angle) * reach)
        add_tapered_stem(mesh, start, end, 0.045 * crown_scale,
                         0.018 * crown_scale, "bark", rng, sides=5)
    return mesh


def build_shrub(name: str, seed: int, scale: float, colorway: int = 0) -> Mesh:
    rng = random.Random(seed)
    mesh = Mesh(name)
    stems = [(-0.25, 0.18, 0.00), (0.05, 0.24, 0.18),
             (0.24, 0.19, -0.17), (0.02, 0.29, -0.06), (-0.30, 0.13, -0.16)]
    for idx, (x, y, z) in enumerate(stems):
        start = (x * scale * 0.35, 0.03 * scale, z * scale * 0.35)
        end = (x * scale, y * scale, z * scale)
        add_tapered_stem(mesh, start, end, 0.035 * scale, 0.012 * scale,
                         "bark", rng, sides=4)
        colors = ("leaf_shadow", "leaf_deep", "leaf", "leaf_salt" if colorway and idx == 2 else "leaf_sun")
        add_icosphere(mesh, (x * scale, y * scale, z * scale),
                      (0.28 * scale, 0.25 * scale, 0.27 * scale), rng,
                      colors, subdivisions=1, roughness=0.1, yaw=idx * 0.61)
    return mesh


def add_leaf_blade(mesh: Mesh, start: Vec3, tip: Vec3, width: float,
                   material: str, rng: random.Random) -> None:
    direction = normalize(sub(tip, start))
    side = normalize((-direction[2], 0.0, direction[0]))
    if length(side) < 0.1:
        side = (1.0, 0.0, 0.0)
    thickness_axis = normalize(cross(direction, side))
    points = [
        (start, width * 0.53, 0.010),
        (mix(start, tip, 0.53), width, 0.014),
        (mix(start, tip, 0.86), width * 0.34, 0.009),
    ]
    rings: list[list[int]] = []
    for center, half_width, half_thickness in points:
        ring = []
        for point in (add(add(center, mul(side, half_width)), mul(thickness_axis, half_thickness)),
                      add(add(center, mul(side, half_width)), mul(thickness_axis, -half_thickness)),
                      add(add(center, mul(side, -half_width)), mul(thickness_axis, -half_thickness)),
                      add(add(center, mul(side, -half_width)), mul(thickness_axis, half_thickness))):
            ring.append(mesh.vertex(point))
        rings.append(ring)
    tip_idx = mesh.vertex(tip)
    centerline = mix(start, tip, 0.5)
    for section in range(2):
        for side_idx in range(4):
            nxt = (side_idx + 1) % 4
            a, b = rings[section][side_idx], rings[section][nxt]
            c, d = rings[section + 1][nxt], rings[section + 1][side_idx]
            outward = normalize(sub(mix(mesh.vertices[a], mesh.vertices[b], 0.5), centerline))
            shade_material = material if (side_idx + section) % 3 else "grass_sun"
            mesh.triangle(a, b, c, shade_material, outward)
            mesh.triangle(a, c, d, shade_material, outward)
    for side_idx in range(4):
        nxt = (side_idx + 1) % 4
        a, b = rings[-1][side_idx], rings[-1][nxt]
        outward = normalize(sub(mix(mesh.vertices[a], mesh.vertices[b], 0.5), centerline))
        mesh.triangle(a, b, tip_idx, "grass_sun" if side_idx == 0 else material, outward)
    base_center = mesh.vertex(start)
    for side_idx in range(4):
        nxt = (side_idx + 1) % 4
        outward = mul(direction, -1.0)
        mesh.triangle(base_center, rings[0][nxt], rings[0][side_idx], material, outward)


def build_grass(name: str, seed: int, scale: float, blade_count: int,
                dry_tips: bool = False) -> Mesh:
    rng = random.Random(seed)
    mesh = Mesh(name)
    for idx in range(blade_count):
        angle = math.tau * idx / blade_count + rng.uniform(-0.18, 0.18)
        base_r = rng.uniform(0.03, 0.20) * scale
        base = (math.cos(angle) * base_r, 0.015 * scale, math.sin(angle) * base_r)
        height = rng.uniform(0.44, 0.79) * scale
        wind = rng.uniform(0.12, 0.30) * scale
        tip = (base[0] + math.cos(angle) * wind + 0.08 * scale,
               height,
               base[2] + math.sin(angle) * wind)
        material = "grass_shadow" if idx % 4 == 0 else "grass"
        add_leaf_blade(mesh, base, tip, rng.uniform(0.055, 0.095) * scale,
                       material, rng)
        if dry_tips and idx % 3 == 0:
            # Small pale segment at the blade tip gives salt-burned coastal grass.
            sub_tip = mix(base, tip, 0.84)
            add_leaf_blade(mesh, sub_tip, tip, 0.035 * scale, "leaf_salt", rng)
    return mesh


def build_fern(name: str, seed: int, scale: float) -> Mesh:
    rng = random.Random(seed)
    mesh = Mesh(name)
    for frond in range(5):
        yaw = math.tau * frond / 5 + rng.uniform(-0.2, 0.2)
        reach = rng.uniform(0.68, 0.94) * scale
        rise = rng.uniform(0.45, 0.64) * scale
        base = (0.0, 0.025 * scale, 0.0)
        end = (math.cos(yaw) * reach, rise, math.sin(yaw) * reach)
        mid = mix(base, end, 0.55)
        mid = (mid[0], mid[1] + 0.17 * scale, mid[2])
        add_tapered_stem(mesh, base, mid, 0.025 * scale, 0.016 * scale,
                         "leaf_deep", rng, sides=4)
        add_tapered_stem(mesh, mid, end, 0.016 * scale, 0.004 * scale,
                         "leaf_deep", rng, sides=4)
        side = normalize((-math.sin(yaw), 0, math.cos(yaw)))
        for pair in range(1, 8):
            t = pair / 9.0
            anchor = mix(base, end, t)
            anchor = (anchor[0], anchor[1] + 0.15 * scale * math.sin(math.pi * t), anchor[2])
            leaflet_width = math.sin(math.pi * t) * 0.16 * scale
            for sign in (-1, 1):
                direction = add(mul(side, sign * leaflet_width),
                                 (0, 0.045 * scale * math.sin(math.pi * t), 0))
                tip = add(anchor, direction)
                tip = (tip[0], tip[1] + 0.035 * scale, tip[2])
                add_leaf_blade(mesh, anchor, tip, 0.036 * scale,
                               "grass" if pair % 3 else "grass_sun", rng)
    return mesh


def add_flower_head(mesh: Mesh, center: Vec3, petals: int,
                    petal_material: str, seed: int, size: float) -> None:
    rng = random.Random(seed)
    for idx in range(petals):
        angle = math.tau * idx / petals + 0.15
        radial = size * 0.52
        petal_center = (center[0] + math.cos(angle) * radial,
                        center[1] + rng.uniform(-0.012, 0.012) * size,
                        center[2] + math.sin(angle) * radial)
        add_icosphere(mesh, petal_center, (size * 0.43, size * 0.12, size * 0.25),
                      rng, (petal_material, petal_material,
                            "flower_cream" if petal_material != "flower_cream" else "flower_gold"),
                      subdivisions=0, roughness=0.06, yaw=angle)
    add_icosphere(mesh, center, (size * 0.22, size * 0.18, size * 0.22), rng,
                  ("flower_center", "flower_gold"), subdivisions=0, roughness=0.02)


def build_wildflowers(name: str, seed: int, scale: float,
                      materials: tuple[str, ...]) -> Mesh:
    rng = random.Random(seed)
    mesh = Mesh(name)
    count = 4
    for idx in range(count):
        x = rng.uniform(-0.35, 0.35) * scale
        z = rng.uniform(-0.27, 0.27) * scale
        stem_h = rng.uniform(0.42, 0.74) * scale
        head_y = stem_h
        lean_x = rng.uniform(-0.08, 0.12) * scale
        add_tapered_stem(mesh, (x, 0, z), (x + lean_x, stem_h, z),
                         0.018 * scale, 0.009 * scale,
                         "grass" if idx % 2 else "bark_sun", rng, sides=4)
        # Two narrow leaves on each stem keep the flower clump grounded.
        for sign in (-1, 1):
            leaf_start = (x + lean_x * 0.22, stem_h * 0.39, z)
            leaf_tip = (x + lean_x * 0.22 + sign * 0.16 * scale,
                        stem_h * 0.48, z + (0.10 if sign > 0 else -0.10) * scale)
            add_leaf_blade(mesh, leaf_start, leaf_tip, 0.035 * scale,
                           "grass" if idx % 2 else "grass_sun", rng)
        head = (x + lean_x, head_y, z)
        add_flower_head(mesh, head, petals=5 + idx % 2,
                        petal_material=materials[idx % len(materials)],
                        seed=seed * 17 + idx, size=rng.uniform(0.12, 0.16) * scale)
    return mesh


def build_rock(name: str, seed: int, scale: Vec3, flat: bool = False) -> Mesh:
    rng = random.Random(seed)
    mesh = Mesh(name)
    if flat:
        add_icosphere(mesh, (0, scale[1] * 0.60, 0), scale, rng,
                      ("rock_shadow", "rock", "rock_sun", "rock_salt"),
                      subdivisions=1, roughness=0.15, yaw=rng.uniform(0, math.tau))
    else:
        add_icosphere(mesh, (0, scale[1], 0), scale, rng,
                      ("rock_shadow", "rock", "rock_sun", "rock_salt"),
                      subdivisions=1, roughness=0.20, yaw=rng.uniform(0, math.tau))
    return mesh


def build_rock_cluster(name: str, seed: int) -> Mesh:
    rng = random.Random(seed)
    mesh = Mesh(name)
    stones = [((-0.43, 0.27, 0.00), (0.48, 0.47, 0.43)),
              ((0.05, 0.36, 0.20), (0.55, 0.61, 0.48)),
              ((0.52, 0.20, -0.12), (0.38, 0.37, 0.42)),
              ((-0.05, 0.19, -0.43), (0.45, 0.33, 0.38))]
    for idx, (center, radii) in enumerate(stones):
        add_icosphere(mesh, center, radii, rng,
                      ("rock_shadow", "rock", "rock_sun", "rock_salt"),
                      subdivisions=1, roughness=0.16, yaw=idx * 0.51)
    return mesh


def build_driftwood(name: str, seed: int) -> Mesh:
    rng = random.Random(seed)
    mesh = Mesh(name)
    start = (-0.75, 0.17, -0.03)
    middle = (0.05, 0.21, 0.02)
    end = (0.68, 0.12, 0.12)
    add_tapered_stem(mesh, start, middle, 0.11, 0.085,
                     "driftwood", rng, sides=5, alternate="driftwood_sun")
    add_tapered_stem(mesh, middle, end, 0.085, 0.036,
                     "driftwood", rng, sides=5, alternate="driftwood_sun")
    add_tapered_stem(mesh, (-0.06, 0.19, 0.02), (0.18, 0.48, 0.08),
                     0.055, 0.018, "driftwood", rng, sides=4, alternate="driftwood_sun")
    return mesh


def build_models() -> list[Mesh]:
    return [
        build_pine("Pine_Windbent_Tall_A", 3.60, 1101, 0.40, 1.34),
        build_pine("Pine_Windbent_Short_B", 2.72, 1102, 0.24, 1.02),
        build_broadleaf("Broadleaf_Coastal_A", 2201, 3.00, 0.52, 1.00, True),
        build_broadleaf("Broadleaf_Coastal_B", 2202, 2.55, 0.36, 0.88, False),
        build_shrub("Shrub_SaltTolerant_A", 3301, 1.00, 1),
        build_shrub("Shrub_SaltTolerant_B", 3302, 0.86, 0),
        build_grass("Grass_CoastalTuft_A", 4401, 1.00, 9, True),
        build_grass("Grass_CoastalTuft_B", 4402, 0.82, 7, False),
        build_fern("Fern_Cliffside", 5501, 1.0),
        build_wildflowers("Wildflower_CoralCream", 6601, 1.0,
                          ("flower_coral", "flower_cream", "flower_gold")),
        build_wildflowers("Wildflower_LilacGold", 6602, 0.86,
                          ("flower_lilac", "flower_gold", "flower_cream")),
        build_rock("Basalt_Boulder_A", 7701, (0.62, 0.54, 0.58)),
        build_rock("Basalt_Boulder_B", 7702, (0.49, 0.43, 0.67)),
        build_rock("Basalt_TidewornSlab", 7703, (0.78, 0.25, 0.58), flat=True),
        build_rock_cluster("Basalt_RockCluster", 7704),
        build_driftwood("Driftwood_BrokenSaltLog", 8801),
    ]


def write_mtl(path: Path, materials: Iterable[str]) -> None:
    lines = ["# Last Landfall original stylized nature materials"]
    for name in sorted(materials):
        color = PALETTE[name]
        lines.extend((f"newmtl {name}",
                      "Ka 0.08 0.08 0.08",
                      "Kd %.5f %.5f %.5f" % color,
                      "Ks 0.025 0.025 0.025",
                      "Ns 8.0",
                      "d 1.0",
                      "illum 2",
                      ""))
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_obj(mesh: Mesh, output_dir: Path) -> tuple[float, float, float]:
    obj_path = output_dir / f"{mesh.name}.obj"
    mtl_path = output_dir / f"{mesh.name}.mtl"
    write_mtl(mtl_path, mesh.used_materials)
    lines = [f"# Original Last Landfall stylized asset: {mesh.name}",
             f"mtllib {mtl_path.name}", f"o {mesh.name}"]
    lines.extend("v %.6f %.6f %.6f" % v for v in mesh.vertices)
    current_material = None
    for indices, material in mesh.faces:
        if material != current_material:
            lines.append(f"usemtl {material}")
            current_material = material
        lines.append("f %d %d %d" % tuple(index + 1 for index in indices))
    obj_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    mins = tuple(min(v[i] for v in mesh.vertices) for i in range(3))
    maxs = tuple(max(v[i] for v in mesh.vertices) for i in range(3))
    dimensions = tuple(round(maxs[i] - mins[i], 3) for i in range(3))
    return dimensions


def render_contact_sheet(models: list[Mesh], path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return

    columns, rows = 4, math.ceil(len(models) / 4)
    cell_w, cell_h = 320, 360
    image = Image.new("RGB", (columns * cell_w, rows * cell_h + 90), (237, 234, 218))
    draw = ImageDraw.Draw(image)
    try:
        title_font = ImageFont.truetype("arial.ttf", 31)
        label_font = ImageFont.truetype("arial.ttf", 17)
    except OSError:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
    draw.text((28, 22), "LAST LANDFALL  /  COASTAL LOW-POLY NATURE", fill=(36, 57, 47), font=title_font)

    camera_from = normalize((6.5, 5.0, 8.5))
    world_up = (0.0, 1.0, 0.0)
    forward = mul(camera_from, -1.0)
    right = normalize(cross(forward, world_up))
    up = normalize(cross(right, forward))
    light = normalize((-0.42, 0.82, 0.37))

    for idx, mesh in enumerate(models):
        col, row = idx % columns, idx // columns
        x0 = col * cell_w
        y0 = 90 + row * cell_h
        draw.rounded_rectangle((x0 + 10, y0 + 8, x0 + cell_w - 10, y0 + cell_h - 10),
                               radius=14, fill=(249, 247, 235), outline=(211, 209, 194), width=2)
        mins = tuple(min(v[a] for v in mesh.vertices) for a in range(3))
        maxs = tuple(max(v[a] for v in mesh.vertices) for a in range(3))
        target = tuple((mins[a] + maxs[a]) * 0.5 for a in range(3))
        projected = []
        depths = []
        for v in mesh.vertices:
            rel = sub(v, target)
            projected.append((dot(rel, right), dot(rel, up)))
            depths.append(dot(rel, forward))
        extent_x = max(p[0] for p in projected) - min(p[0] for p in projected)
        extent_y = max(p[1] for p in projected) - min(p[1] for p in projected)
        scale = min(220 / max(extent_x, 0.05), 235 / max(extent_y, 0.05))
        center_x, center_y = x0 + cell_w * 0.5, y0 + 166
        points = [(center_x + p[0] * scale, center_y - p[1] * scale) for p in projected]
        draw.ellipse((center_x - 78, y0 + 277, center_x + 78, y0 + 293), fill=(222, 221, 207))

        ordered_faces = sorted(mesh.faces,
                               key=lambda face: sum(depths[v] for v in face[0]) / 3.0)
        for face_indices, material in ordered_faces:
            a, b, c = (mesh.vertices[face_indices[0]], mesh.vertices[face_indices[1]],
                       mesh.vertices[face_indices[2]])
            normal = normalize(cross(sub(b, a), sub(c, a)))
            brightness = 0.82 + 0.22 * max(-0.30, dot(normal, light))
            base = PALETTE[material]
            color = tuple(max(0, min(255, int(channel * brightness * 255))) for channel in base)
            poly = [points[v] for v in face_indices]
            draw.polygon(poly, fill=color)
        draw.text((x0 + 22, y0 + cell_h - 44), mesh.name.replace("_", " "),
                  fill=(44, 57, 47), font=label_font)

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    models = build_models()
    manifest = []
    for mesh in models:
        dimensions = write_obj(mesh, OUTPUT_DIR)
        manifest.append({
            "name": mesh.name,
            "obj": f"{mesh.name}.obj",
            "materials": f"{mesh.name}.mtl",
            "vertices": len(mesh.vertices),
            "triangles": len(mesh.faces),
            "dimensions_m": {"x": dimensions[0], "y": dimensions[1], "z": dimensions[2]},
            "origin": "ground centre",
        })
    (OUTPUT_DIR / "asset_manifest.json").write_text(
        json.dumps({"units": "metres", "up_axis": "Y", "assets": manifest},
                   indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    render_contact_sheet(models, PREVIEW_PATH)
    print(f"Wrote {len(models)} models to {OUTPUT_DIR}")
    print(f"Preview: {PREVIEW_PATH}")
    print(f"Triangles: {sum(len(mesh.faces) for mesh in models):,} total")


if __name__ == "__main__":
    main()
