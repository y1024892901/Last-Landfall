# -*- coding: utf-8 -*-
"""Generate game-ready Stylized Puffed Grass Clumps for Last Landfall.

Features:
- Broad, curved stylized blades (anime / Zelda style, 24-36 polygons per clump)
- Spherical Normals for soft, cloud-like lighting (no harsh dark shadows or hedgehog spikes)
- Vertex Colors:
  - Alpha: 0.0 at root, 1.0 at tip (drives wind sway in GrassBlades.shader)
  - RGB: Smooth warm gradient from deep turf moss to sunlit lime
- Pivot strictly grounded at Z=0
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Euler

ROOT = Path(__file__).resolve().parents[2] / "Last-Landfall"
if not ROOT.exists():
    ROOT = Path(r"D:\game\Last-Landfall")

FBX_DIR = ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Nature"
BLEND_DIR = ROOT / "Assets" / "LastLandfall" / "Art" / "Source" / "Nature"
PREVIEW_DIR = ROOT / "Assets" / "LastLandfall" / "Art" / "Previews" / "Nature"


def setup_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes: bpy.data.meshes.remove(block)
    for block in bpy.data.materials: bpy.data.materials.remove(block)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.context.preferences.filepaths.save_version = 0


def create_puffed_blade(bm, height, base_width, segments, bend, rot_z, offset_radial):
    """Create a broad, gently curved leaf with volumetric profile."""
    rad_dir = Vector((math.cos(rot_z), math.sin(rot_z), 0.0))
    side_dir = Vector((-math.sin(rot_z), math.cos(rot_z), 0.0))
    base_pos = rad_dir * offset_radial

    blade_l = []
    blade_r = []

    for i in range(segments + 1):
        t = i / segments  # 0.0 -> 1.0
        # Gentle taper, keeping cartoon width
        w = (1.0 - t * 0.65) * (base_width * 0.5)

        # Smooth outward parabola curve
        lean_dist = (t ** 1.6) * math.sin(bend) * height
        z = t * math.cos(bend) * height

        center_pos = base_pos + rad_dir * lean_dist + Vector((0, 0, z))
        vl = bm.verts.new(center_pos - side_dir * w)
        vr = bm.verts.new(center_pos + side_dir * w)
        blade_l.append(vl)
        blade_r.append(vr)

    # Tip vertex
    tip_dist = (1.04 ** 1.6) * math.sin(bend) * height
    tip_z = 1.04 * math.cos(bend) * height
    tip_pos = base_pos + rad_dir * tip_dist + Vector((0, 0, tip_z))
    tip_v = bm.verts.new(tip_pos)

    # Faces
    for i in range(segments):
        bm.faces.new([blade_l[i], blade_r[i], blade_r[i+1], blade_l[i+1]])
    bm.faces.new([blade_l[segments], blade_r[segments], tip_v])


def generate_stylized_clump(name, blade_count=6, base_height=0.48, base_width=0.08, seed=42):
    rng = random.Random(seed)
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    for b in range(blade_count):
        angle = (b / blade_count) * math.pi * 2.0 + rng.uniform(-0.25, 0.25)
        h = base_height * rng.uniform(0.85, 1.15)
        w = base_width * rng.uniform(0.9, 1.1)
        bend = rng.uniform(0.35, 0.62)
        radial_r = rng.uniform(0.04, 0.09)
        create_puffed_blade(bm, h, w, segments=2, bend=bend, rot_z=angle, offset_radial=radial_r)

    bm.to_mesh(mesh)
    bm.free()

    # 1. Vertex Colors for Wind Sway (Alpha) & Warm Tint (RGB)
    color_layer = mesh.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
    z_coords = [v.co.z for v in mesh.vertices]
    max_z = max(z_coords) if z_coords else 0.5

    c_root = Vector((0.36, 0.48, 0.20))
    c_tip = Vector((0.65, 0.76, 0.30))

    for v, col_data in zip(mesh.vertices, color_layer.data):
        weight = min(max(v.co.z / max_z, 0.0), 1.0)
        c = c_root.lerp(c_tip, weight)
        # RGBA: Alpha is strictly weight (0 at root, 1 at tip) for shader wind
        col_data.color = (c.x, c.y, c.z, weight)

    # 2. Spherical Normals for Volumetric Puffiness
    # Instead of flat planar face normals, point normals outward from a virtual sphere center
    sphere_center = Vector((0.0, 0.0, -0.15))
    mesh.normals_split_custom_set_from_vertices([
        ((v.co - sphere_center).normalized()) for v in mesh.vertices
    ])

    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Stylized material for preview
    mat = bpy.data.materials.new(name=f"M_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.42, 0.62, 0.24, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.8
    mesh.materials.append(mat)
    return obj


def export_asset(obj, name):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    fbx_path = FBX_DIR / f"{name}.fbx"
    blend_path = BLEND_DIR / f"{name}.blend"

    FBX_DIR.mkdir(parents=True, exist_ok=True)
    BLEND_DIR.mkdir(parents=True, exist_ok=True)

    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path),
        use_selection=True,
        global_scale=1.0,
        apply_unit_scale=True,
        axis_forward="-Z",
        axis_up="Y",
        object_types={"MESH"},
        mesh_smooth_type="OFF",
        colors_type="SRGB",
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), compress=True)
    print(f"Exported {name}: {len(obj.data.polygons)} polygons -> {fbx_path.name}")


def main():
    setup_scene()
    obj_a = generate_stylized_clump("Grass_Tuft_Stylized_A", blade_count=6, base_height=0.42, base_width=0.075, seed=101)
    export_asset(obj_a, "Grass_Tuft_Stylized_A")

    setup_scene()
    obj_b = generate_stylized_clump("Grass_Tuft_Stylized_B", blade_count=8, base_height=0.52, base_width=0.085, seed=202)
    export_asset(obj_b, "Grass_Tuft_Stylized_B")
    print("ALL PUFFED GRASS CLUMPS GENERATED SUCCESSFULLY")


if __name__ == "__main__":
    main()
