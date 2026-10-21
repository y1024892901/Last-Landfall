# -*- coding: utf-8 -*-
"""Create a standalone, game-scale low-poly bamboo clump for Last Landfall.

Run with Blender 5.2.2:
    blender --background --python work/island_final_candidate/Scripts/Gate33_generate_Bamboo_Clump_A.py

The output is an independently reviewable .blend/.fbx candidate with a render
preview and an FBX round-trip QA report. No existing island or plant mesh is
modified by this gate.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import random
import shutil
from pathlib import Path
from typing import Iterable

import bpy
import bmesh
from mathutils import Vector


ROOT = Path(r"D:\Last Landfall")
if "__file__" in globals():
    for parent in Path(__file__).resolve().parents:
        if (parent / "Assets" / "LastLandfall").is_dir():
            ROOT = parent
            break
WORK = ROOT / "work" / "island_final_candidate"
GEN_DIR = WORK / "Assets_Generated"
PREVIEW_DIR = WORK / "Previews_Generated"
REPORT_DIR = WORK / "Reports_Generated"
ASSET = "Bamboo_Clump_A"
GATE = "Gate33"
TARGET = Vector((2.45, 2.25, 4.10))  # Blender XYZ; metres; ground at Z=0.
PREVIEW_PATH = PREVIEW_DIR / f"{GATE}_{ASSET}.png"
FBX_PATH = GEN_DIR / f"{ASSET}.fbx"
BLEND_PATH = GEN_DIR / f"{ASSET}.blend"
REPORT_PATH = REPORT_DIR / f"{GATE}_{ASSET}_qa.json"
PROJECT_FBX = ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Nature" / f"{ASSET}.fbx"
PROJECT_BLEND = ROOT / "Assets" / "LastLandfall" / "Art" / "Source" / "Nature" / f"{ASSET}.blend"
PROJECT_PREVIEW = ROOT / "Assets" / "LastLandfall" / "Art" / "Previews" / "Nature" / f"{ASSET}.png"

PALETTE = {
    "culm_shadow": (0.17, 0.30, 0.21),
    "culm_dark": (0.22, 0.38, 0.25),
    "culm": (0.31, 0.48, 0.29),
    "culm_sun": (0.46, 0.59, 0.34),
    "bamboo_node": (0.52, 0.59, 0.38),
    "bamboo_sheath": (0.49, 0.48, 0.30),
    "bamboo_twig": (0.31, 0.43, 0.27),
    "leaf_shadow": (0.14, 0.29, 0.22),
    "leaf": (0.24, 0.42, 0.27),
    "leaf_sun": (0.45, 0.60, 0.35),
}


class MeshBuilder:
    def __init__(self) -> None:
        self.vertices: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, int, int]] = []
        self.materials: list[str] = []

    def vertex(self, p: Vector) -> int:
        self.vertices.append((float(p.x), float(p.y), float(p.z)))
        return len(self.vertices) - 1

    def tri(self, a: int, b: int, c: int, material: str) -> None:
        self.faces.append((a, b, c))
        self.materials.append(material)

    def quad(self, a: int, b: int, c: int, d: int, material: str) -> None:
        self.tri(a, b, c, material)
        self.tri(a, c, d, material)


def make_material(name: str, color: tuple[float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = (*color, 1.0)
    mat.roughness = 0.88
    mat.use_nodes = True
    shader = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if shader:
        shader.inputs["Base Color"].default_value = (*color, 1.0)
        shader.inputs["Roughness"].default_value = 0.88
    return mat


def add_stalk(mesh: MeshBuilder, base: Vector, height: float, lean: Vector,
              base_radius: float, seed: int) -> tuple[Vector, list[float]]:
    """Build one ring-jointed culm with slight taper and a natural lean."""
    rng = random.Random(seed)
    sides = 8
    segment_count = max(5, round(height / 0.48))
    segment = height / segment_count

    def center(z: float) -> Vector:
        t = z / height
        sway = 0.025 * math.sin(t * math.pi * 1.7 + seed * 0.19) * t
        return base + Vector((lean.x * t ** 1.65 + sway,
                              lean.y * t ** 1.65 - sway * 0.34, z))

    def radius_at(z: float) -> float:
        return base_radius * (1.0 - 0.50 * (z / height))

    # Paired profile rings form a raised, pale node collar at each joint.
    profile: list[tuple[float, float, bool]] = [(0.0, base_radius * 1.06, False)]
    for node in range(1, segment_count):
        z = node * segment
        r = radius_at(z)
        profile.extend(((z - 0.024, r, False),
                        (z - 0.010, r * 1.08, True),
                        (z + 0.010, r * 1.08, True),
                        (z + 0.024, r * 0.985, False)))
    profile.extend(((height * 0.94, base_radius * 0.31, False),
                    (height, max(0.002, base_radius * 0.055), False)))

    rings: list[list[int]] = []
    for ring_index, (z, radius, is_node) in enumerate(profile):
        ring: list[int] = []
        c = center(z)
        phase = seed * 0.73
        for side in range(sides):
            angle = math.tau * side / sides + phase
            irregular = 1.0 + rng.uniform(-0.025, 0.025)
            point = c + Vector((math.cos(angle) * radius * irregular,
                                math.sin(angle) * radius * irregular, 0.0))
            ring.append(mesh.vertex(point))
        rings.append(ring)

    for ring_index in range(len(rings) - 1):
        z_mid = (profile[ring_index][0] + profile[ring_index + 1][0]) * 0.5
        node_band = profile[ring_index][2] or profile[ring_index + 1][2]
        for side in range(sides):
            nxt = (side + 1) % sides
            if node_band:
                material = "bamboo_node"
            else:
                light_side = math.cos(math.tau * side / sides + seed * 0.73)
                if light_side > 0.58:
                    material = "culm_sun"
                elif light_side < -0.58:
                    material = "culm_shadow"
                else:
                    material = "culm_dark" if (ring_index + side) % 5 == 0 else "culm"
                # Occasional pale vertical streaks evoke the waxy outer skin.
                if side == (seed % sides) and z_mid > height * 0.24:
                    material = "culm_sun"
            mesh.quad(rings[ring_index][side], rings[ring_index][nxt],
                      rings[ring_index + 1][nxt], rings[ring_index + 1][side], material)

    bottom_center = mesh.vertex(center(0.0))
    top_center = mesh.vertex(center(height))
    for side in range(sides):
        nxt = (side + 1) % sides
        mesh.tri(bottom_center, rings[0][nxt], rings[0][side], "culm_shadow")
        mesh.tri(top_center, rings[-1][side], rings[-1][nxt], "culm_sun")

    joints = [node * segment for node in range(1, segment_count)]
    return center(height), joints


def add_twig(mesh: MeshBuilder, points: list[Vector], radii: list[float], seed: int) -> None:
    """Create a closed, tapered hexagonal twig."""
    sides = 6
    rings: list[list[int]] = []
    for ring_index, (point, radius) in enumerate(zip(points, radii)):
        tangent = (points[min(ring_index + 1, len(points) - 1)] -
                   points[max(ring_index - 1, 0)]).normalized()
        reference = Vector((0.0, 0.0, 1.0))
        if abs(tangent.dot(reference)) > 0.92:
            reference = Vector((0.0, 1.0, 0.0))
        axis_u = tangent.cross(reference).normalized()
        axis_v = tangent.cross(axis_u).normalized()
        ring = []
        phase = seed * 0.21
        for side in range(sides):
            angle = phase + math.tau * side / sides
            ring.append(mesh.vertex(point + (axis_u * math.cos(angle) + axis_v * math.sin(angle)) * radius))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for side in range(sides):
            nxt = (side + 1) % sides
            mesh.quad(rings[i][side], rings[i][nxt], rings[i + 1][nxt], rings[i + 1][side], "bamboo_twig")
    start = mesh.vertex(points[0])
    end = mesh.vertex(points[-1])
    for side in range(sides):
        nxt = (side + 1) % sides
        mesh.tri(start, rings[0][nxt], rings[0][side], "bamboo_twig")
        mesh.tri(end, rings[-1][side], rings[-1][nxt], "bamboo_twig")


def add_leaf(mesh: MeshBuilder, base: Vector, tip: Vector, width: float,
             seed: int, upward_bias: float = 0.0) -> None:
    """A curved, pointed blade with double-sided faces and a subtle midrib."""
    axis = tip - base
    length = axis.length
    if length < 0.03:
        return
    direction = axis.normalized()
    plane_normal = direction.cross(Vector((0.0, 0.0, 1.0)))
    if plane_normal.length < 1e-4:
        plane_normal = direction.cross(Vector((0.0, 1.0, 0.0)))
    plane_normal.normalize()
    side_vector = plane_normal.cross(direction).normalized()
    centerline = []
    widths = []
    for row, t in enumerate((0.04, 0.32, 0.64, 0.91, 0.995)):
        curve = math.sin(math.pi * t) * length * (0.025 + upward_bias * 0.045)
        centerline.append(base.lerp(tip, t) + plane_normal * curve)
        shape = math.sin(math.pi * t) ** 0.72
        widths.append(max(width * 0.035, width * shape * (1.0 - 0.22 * t)))

    top_rows: list[tuple[int, int, int]] = []
    bottom_rows: list[tuple[int, int, int]] = []
    thickness = max(0.0015, width * 0.055)
    for center, half_width in zip(centerline, widths):
        left = center + side_vector * half_width
        right = center - side_vector * half_width
        top_center = center + plane_normal * thickness
        bottom_center = center - plane_normal * thickness
        top_rows.append((mesh.vertex(left + plane_normal * thickness),
                         mesh.vertex(top_center),
                         mesh.vertex(right + plane_normal * thickness)))
        bottom_rows.append((mesh.vertex(left - plane_normal * thickness),
                            mesh.vertex(bottom_center),
                            mesh.vertex(right - plane_normal * thickness)))

    for row in range(len(top_rows) - 1):
        l0, c0, r0 = top_rows[row]
        l1, c1, r1 = top_rows[row + 1]
        bl0, bc0, br0 = bottom_rows[row]
        bl1, bc1, br1 = bottom_rows[row + 1]
        front = "leaf_sun" if (seed + row) % 4 == 0 else "leaf"
        mesh.quad(l0, l1, c1, c0, front)
        mesh.quad(c0, c1, r1, r0, front)
        mesh.quad(bc0, bc1, bl1, bl0, "leaf_shadow")
        mesh.quad(br0, br1, bc1, bc0, "leaf_shadow")
        mesh.quad(l0, bl0, bl1, l1, "leaf_shadow")
        mesh.quad(r1, br1, br0, r0, "leaf_shadow")
        # Narrow raised center rib catches light at normal game camera distance.
        if row < len(top_rows) - 2:
            next_center = centerline[row + 1]
            rib_a = centerline[row] + plane_normal * (thickness * 1.12)
            rib_b = next_center + plane_normal * (thickness * 1.12)
            mesh.tri(mesh.vertex(rib_a - side_vector * width * 0.012),
                     mesh.vertex(rib_b), mesh.vertex(rib_a + side_vector * width * 0.012), "leaf_sun")


def make_fan(mesh: MeshBuilder, origin: Vector, seed: int, spread: float = 1.0) -> None:
    """Make a branching spray of narrow bamboo leaves."""
    rng = random.Random(seed)
    base_angle = rng.uniform(0.0, math.tau)
    for branch_index in range(3):
        angle = base_angle + branch_index * math.tau / 3 + rng.uniform(-0.16, 0.16)
        radial = Vector((math.cos(angle), math.sin(angle), 0.0))
        branch_length = rng.uniform(0.24, 0.37) * spread
        branch_end = origin + radial * branch_length + Vector((0.0, 0.0, rng.uniform(0.10, 0.22) * spread))
        branch_mid = origin.lerp(branch_end, 0.56) + Vector((0.0, 0.0, 0.035))
        add_twig(mesh, [origin, branch_mid, branch_end], [0.011, 0.0065, 0.003], seed + branch_index)
        # Leaflets fan from several points along each branch, not just one ball.
        for leaf_index in range(2):
            t = 0.31 + leaf_index * 0.34
            attachment = origin.lerp(branch_end, t)
            side_sign = -1 if leaf_index % 2 else 1
            side = Vector((-radial.y, radial.x, 0.0)) * side_sign
            direction = (radial * rng.uniform(0.35, 0.70) + side * rng.uniform(0.48, 0.85) +
                         Vector((0.0, 0.0, rng.uniform(-0.10, 0.20)))).normalized()
            blade_length = rng.uniform(0.43, 0.66) * spread
            tip = attachment + direction * blade_length + Vector((0.0, 0.0, -rng.uniform(0.0, 0.10)))
            add_leaf(mesh, attachment, tip, rng.uniform(0.042, 0.062) * spread,
                     seed * 7 + branch_index * 13 + leaf_index, upward_bias=rng.uniform(-0.1, 0.4))


def make_new_shoot(mesh: MeshBuilder, base: Vector, height: float, radius: float, seed: int) -> None:
    """Build a young pointed culm with two subtle protective sheaths."""
    rng = random.Random(seed)
    sides = 7
    levels = [(0.0, radius), (height * 0.28, radius * 0.75),
              (height * 0.58, radius * 0.44), (height * 0.84, radius * 0.18), (height, 0.003)]
    rings = []
    for z, r in levels[:-1]:
        phase = seed * 0.37
        ring = [mesh.vertex(base + Vector((math.cos(math.tau * i / sides + phase) * r,
                                           math.sin(math.tau * i / sides + phase) * r, z)))
                for i in range(sides)]
        rings.append(ring)
    tip = mesh.vertex(base + Vector((0.0, 0.0, height)))
    for level in range(len(rings) - 1):
        for side in range(sides):
            nxt = (side + 1) % sides
            material = "bamboo_sheath" if (side + level + seed) % 4 == 0 else "culm_dark"
            mesh.quad(rings[level][side], rings[level][nxt], rings[level + 1][nxt], rings[level + 1][side], material)
    for side in range(sides):
        nxt = (side + 1) % sides
        mesh.tri(rings[-1][side], rings[-1][nxt], tip, "culm_sun" if side % 3 == 0 else "culm")
    base_center = mesh.vertex(base)
    for side in range(sides):
        mesh.tri(base_center, rings[0][(side + 1) % sides], rings[0][side], "culm_shadow")
    # Two tapered sheaths flare away from the shoot and make the new growth legible.
    for sheath_index in range(2):
        angle = seed * 0.5 + sheath_index * math.pi + rng.uniform(-0.2, 0.2)
        radial = Vector((math.cos(angle), math.sin(angle), 0.0))
        start = base + radial * radius * 0.42 + Vector((0.0, 0.0, height * 0.12))
        end = base + radial * radius * 1.9 + Vector((0.0, 0.0, height * 0.55))
        point = start.lerp(end, 0.72) + Vector((0.0, 0.0, height * 0.08))
        add_leaf(mesh, start, point, radius * 0.50, seed + sheath_index, upward_bias=0.5)


def build_bamboo() -> MeshBuilder:
    mesh = MeshBuilder()
    # Mature canes form an uneven ring so the clump reads as one harvestable
    # resource while leaving small gaps through which stems remain visible.
    culms = [
        ((-0.38, -0.18), 3.62, (-0.08, -0.01), 0.055),
        ((0.26, -0.30), 4.08, (0.10, -0.02), 0.061),
        ((0.45, 0.16), 3.47, (0.06, 0.11), 0.052),
        ((-0.18, 0.36), 3.84, (-0.03, 0.08), 0.057),
        ((-0.48, 0.21), 3.25, (-0.11, 0.05), 0.050),
        ((0.06, 0.13), 3.56, (0.02, 0.04), 0.053),
    ]
    for index, (xy, height, lean_xy, radius) in enumerate(culms):
        base = Vector((xy[0], xy[1], 0.0))
        lean = Vector((lean_xy[0], lean_xy[1], 0.0))
        tip, joints = add_stalk(mesh, base, height, lean, radius, 3301 + index * 17)
        # Two sparse, elevated leaf sprays per mature culm preserve the clean
        # vertical silhouette while making the clump unmistakably bamboo.
        upper = [z for z in joints if z >= height * 0.61]
        if upper:
            make_fan(mesh, Vector((tip.x, tip.y, height * 0.78)), 6100 + index * 11, spread=0.90)
            if len(upper) > 1:
                z = upper[-2]
                t = z / height
                joint_origin = base + Vector((lean.x * t ** 1.65, lean.y * t ** 1.65, z))
                make_fan(mesh, joint_origin, 7100 + index * 13, spread=0.76)

    # A couple of slender shoots at different growth stages reinforce that this
    # is a living, harvestable bamboo stand rather than a bundle of poles.
    make_new_shoot(mesh, Vector((-0.56, -0.31, 0.0)), 1.18, 0.082, 8101)
    make_new_shoot(mesh, Vector((0.50, -0.36, 0.0)), 1.54, 0.073, 8107)
    return mesh


def normalize_to_target(builder: MeshBuilder) -> None:
    points = [Vector(p) for p in builder.vertices]
    mins = [min(point[i] for point in points) for i in range(3)]
    maxs = [max(point[i] for point in points) for i in range(3)]
    sizes = [maxs[i] - mins[i] for i in range(3)]
    factors = [TARGET[i] / sizes[i] for i in range(3)]
    builder.vertices = [((p[0] - (mins[0] + maxs[0]) * 0.5) * factors[0],
                         (p[1] - (mins[1] + maxs[1]) * 0.5) * factors[1],
                         (p[2] - mins[2]) * factors[2]) for p in builder.vertices]


def render_preview(obj: bpy.types.Object, output: Path) -> None:
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
    scene.display.shading.light = "STUDIO"
    scene.display.shading.studio_light = "paint.sl"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.curvature_ridge_factor = 1.2
    scene.display.shading.curvature_valley_factor = 0.9
    scene.display.shading.background_type = "WORLD"
    world = bpy.data.worlds.new("Gate33_Bamboo_Background")
    world.color = (0.72, 0.75, 0.70)
    scene.world = world

    ground_mesh = bpy.data.meshes.new("Preview_Ground_Mesh")
    ground_mesh.from_pydata([(-5, -5, -0.006), (5, -5, -0.006), (5, 5, -0.006), (-5, 5, -0.006)], [], [(0, 1, 2, 3)])
    ground_mesh.materials.append(make_material("Preview_Ground", (0.77, 0.75, 0.66)))
    ground = bpy.data.objects.new("Preview_Ground (not exported)", ground_mesh)
    bpy.context.collection.objects.link(ground)
    ground.hide_select = True

    camera_data = bpy.data.cameras.new("Gate33_Bamboo_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 6.5
    camera = bpy.data.objects.new("Gate33_Bamboo_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    look_at = Vector((0.0, 0.0, TARGET.z * 0.47))
    camera.location = Vector((6.7, -8.2, 6.9))
    camera.rotation_euler = (look_at - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera

    # An orthographic top-front camera shows culm joints, leaf fans, and the
    # young shoots together in one asset-review image.
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"


def get_bounds(obj: bpy.types.Object) -> tuple[list[float], list[float], list[float]]:
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    mins = [min(p[i] for p in points) for i in range(3)]
    maxs = [max(p[i] for p in points) for i in range(3)]
    return mins, maxs, [maxs[i] - mins[i] for i in range(3)]


def run() -> dict[str, object]:
    for directory in (GEN_DIR, PREVIEW_DIR, REPORT_DIR, PROJECT_FBX.parent,
                      PROJECT_BLEND.parent, PROJECT_PREVIEW.parent):
        directory.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.context.preferences.filepaths.save_version = 0

    builder = build_bamboo()
    normalize_to_target(builder)
    mesh = bpy.data.meshes.new(ASSET)
    mesh.from_pydata(builder.vertices, [], builder.faces)
    normal_mesh = bmesh.new()
    normal_mesh.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(normal_mesh, faces=normal_mesh.faces)
    normal_mesh.to_mesh(mesh)
    normal_mesh.free()
    mesh.update(calc_edges=True)
    used_materials = list(dict.fromkeys(builder.materials))
    for name in used_materials:
        mesh.materials.append(make_material(name, PALETTE[name]))
    material_slots = {mat.name: index for index, mat in enumerate(mesh.materials)}
    for polygon, name in zip(mesh.polygons, builder.materials):
        polygon.material_index = material_slots[name]
        polygon.use_smooth = False
    mesh.calc_loop_triangles()
    obj = bpy.data.objects.new(ASSET, mesh)
    bpy.context.collection.objects.link(obj)
    obj["model_type"] = "original procedural low-poly bamboo clump"
    obj["gameplay_resource_hint"] = "bamboo"
    obj["origin_z"] = 0.0
    obj["unit_scale"] = "metres"
    obj["source_mesh_copied"] = False
    bpy.context.view_layer.update()
    bbox_min, bbox_max, dimensions = get_bounds(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    degenerate = sum(1 for face in bm.faces if face.calc_area() <= 1e-12)
    non_manifold = sum(1 for edge in bm.edges if not edge.is_manifold)
    boundary = sum(1 for edge in bm.edges if edge.is_boundary)
    bm.free()
    non_finite = sum(1 for vertex in mesh.vertices if not all(math.isfinite(v) for v in vertex.co))
    triangle_count = len(mesh.loop_triangles)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    export_result = bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH), use_selection=True, global_scale=1.0,
        apply_unit_scale=True, axis_forward="-Z", axis_up="Y",
        object_types={"MESH"}, mesh_smooth_type="OFF", bake_space_transform=False,
        add_leaf_bones=False, use_mesh_modifiers=True, path_mode="AUTO",
    )
    if "FINISHED" not in export_result:
        raise RuntimeError(f"FBX export failed: {export_result}")

    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))
    imported = [item for item in bpy.data.objects if item not in before and item.type == "MESH"]
    if len(imported) != 1:
        raise RuntimeError(f"Expected one FBX mesh on re-import; found {len(imported)}")
    imported_obj = imported[0]
    imported_obj.data.calc_loop_triangles()
    round_min, round_max, round_dims = get_bounds(imported_obj)
    fbx_match = (
        len(imported_obj.data.vertices) == len(mesh.vertices)
        and len(imported_obj.data.loop_triangles) == triangle_count
        and all(abs(round_dims[i] - dimensions[i]) <= 1e-4 for i in range(3))
        and all(abs(round_min[i] - bbox_min[i]) <= 1e-4 for i in range(3))
        and all(abs(round_max[i] - bbox_max[i]) <= 1e-4 for i in range(3))
        and len(imported_obj.data.materials) == len(mesh.materials)
    )
    roundtrip_metrics = {
        "vertices": len(imported_obj.data.vertices),
        "triangles": len(imported_obj.data.loop_triangles),
        "bbox_min_m_xyz": round_min,
        "bbox_max_m_xyz": round_max,
        "dimensions_m_xyz": round_dims,
        "material_slot_count": len(imported_obj.data.materials),
        "matches_generated_mesh": fbx_match,
    }
    for item in imported:
        bpy.data.objects.remove(item, do_unlink=True)

    render_preview(obj, PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), compress=True)

    exact_dimensions = all(abs(dimensions[i] - TARGET[i]) <= 1e-4 for i in range(3))
    floor_pass = abs(bbox_min[2]) <= 0.002
    checks = {
        "dimensions_match_target": exact_dimensions,
        "game_scale_detail_sufficient": triangle_count >= 1600,
        "palette_materials_present": len(mesh.materials) >= 8,
        "no_degenerate_faces": degenerate == 0,
        "all_vertices_finite": non_finite == 0,
        "fbx_roundtrip_matches": fbx_match,
        "ground_alignment_within_2mm": floor_pass,
    }
    report = {
        "gate": GATE,
        "asset": ASSET,
        "generated_at_local": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "blender_version": bpy.app.version_string,
        "method": "locally authored procedural Blender Python; independent asset; no existing mesh modified",
        "design": {
            "silhouette": "six mature jointed culms with two young shoots and irregular upper leaf sprays",
            "materials": PALETTE,
            "gameplay_resource_hint": "bamboo",
            "target_dimensions_m_xyz": list(TARGET),
        },
        "generated_mesh": {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
            "triangles": triangle_count,
            "bbox_min_m_xyz": bbox_min,
            "bbox_max_m_xyz": bbox_max,
            "dimensions_m_xyz": dimensions,
            "materials": used_materials,
            "topology_diagnostics": {
                "non_manifold_edges": non_manifold,
                "boundary_edges": boundary,
                "degenerate_faces": degenerate,
            },
        },
        "fbx_roundtrip": roundtrip_metrics,
        "floor_alignment": {"min_z_m": bbox_min[2], "tolerance_m": 0.002, "passed": floor_pass},
        "deliverables": {
            "blend": str(BLEND_PATH),
            "fbx": str(FBX_PATH),
            "preview_png": str(PREVIEW_PATH),
            "qa_report": str(REPORT_PATH),
        },
        "checks": checks,
        "accepted": all(checks.values()),
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if report["accepted"]:
        shutil.copy2(BLEND_PATH, PROJECT_BLEND)
        shutil.copy2(FBX_PATH, PROJECT_FBX)
        shutil.copy2(PREVIEW_PATH, PROJECT_PREVIEW)
        report["deliverables"].update({
            "project_blend_source": str(PROJECT_BLEND),
            "project_unity_model": str(PROJECT_FBX),
            "project_preview_png": str(PROJECT_PREVIEW),
        })
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "gate": GATE, "asset": ASSET, "status": report["status"],
        "vertices": len(mesh.vertices), "triangles": triangle_count,
        "dimensions_m_xyz": dimensions, "checks": checks,
        "deliverables": report["deliverables"],
    }, ensure_ascii=False))
    return report


if __name__ == "__main__":
    run()
