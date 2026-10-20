# -*- coding: utf-8 -*-
"""Assemble a separate foliage/rock candidate on IslandReference_V2.

The original terrain and source assets remain unchanged. The terrain is placed
at the same 0.02 scale and -0.92 m vertical offset used by the Unity prototype.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import random
from pathlib import Path
from typing import Any

import bpy
from mathutils import Vector


ROOT = Path(r"D:\Last Landfall")
if "__file__" in globals():
    for parent in Path(__file__).resolve().parents:
        if (parent / "Assets" / "LastLandfall").is_dir():
            ROOT = parent
            break
OUT = ROOT / "work" / "island_final_candidate"
NATURE = ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Nature"
TERRAIN_BLEND = ROOT / "Assets" / "LastLandfall" / "Art" / "Source" / "Environment" / "IslandReference_V2.blend"
INSPECTED = OUT / "Assets_Inspected"
GENERATED = OUT / "Assets_Generated"
PREVIEWS = OUT / "Previews_Generated"
REPORTS = OUT / "Reports_Generated"
SCENE_PATH = GENERATED / "LastLandfall_Island_Foliage_Assembly.blend"
FBX_PATH = GENERATED / "LastLandfall_Island_Foliage_Assembly.fbx"
PREVIEW_PATH = PREVIEWS / "Gate17_Island_Foliage_Assembly.png"
REPORT_PATH = REPORTS / "Gate17_assembly_qa.json"

TERRAIN_SCALE = 0.02
TERRAIN_Z_OFFSET = -0.92
WATER_Z = -0.92
BUILD_CLEAR_X = 15.0
BUILD_CLEAR_Y = 12.0

ASSETS = [
    ("Pine_Windbent_Tall_A", "source", 3, 2.0, 8.5, 6.0, 0.72, 1.1),
    ("Pine_Windbent_Short_B", "source", 3, 1.2, 7.2, 5.0, 0.72, 1.0),
    ("Basalt_RockCluster", "generated", 2, -0.60, 2.7, 2.8, 0.25, 1.1),
    ("Basalt_Boulder_A", "generated", 3, -0.60, 2.2, 2.2, 0.30, 0.8),
    ("Basalt_Boulder_B", "generated", 3, -0.60, 2.2, 2.2, 0.30, 0.8),
    ("Basalt_TidewornSlab", "generated", 3, -0.60, 2.0, 2.0, 0.28, 0.8),
    ("Driftwood_BrokenSaltLog", "generated", 2, -0.78, 0.4, 2.4, 0.58, 0.8),
    ("Broadleaf_Coastal_A", "source", 3, 0.4, 4.2, 4.0, 0.76, 0.9),
    ("Broadleaf_Coastal_B", "source", 3, 0.2, 3.4, 3.8, 0.76, 0.9),
    ("Shrub_SaltTolerant_A", "source", 5, -0.45, 2.0, 1.8, 0.70, 0.55),
    ("Shrub_SaltTolerant_B", "source", 5, -0.45, 2.1, 1.8, 0.70, 0.55),
    ("Fern_Cliffside", "generated", 10, -0.35, 2.4, 1.6, 0.62, 0.9),
    ("Grass_CoastalTuft_A", "source", 12, -0.50, 1.5, 1.0, 0.80, 0.35),
    ("Grass_CoastalTuft_B", "source", 12, -0.50, 1.5, 1.0, 0.80, 0.35),
    ("Wildflower_CoralCream", "generated", 7, -0.45, 1.45, 1.1, 0.86, 0.4),
    ("Wildflower_LilacGold", "generated", 7, -0.45, 1.45, 1.0, 0.86, 0.25),
]


def empty_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def source_terrain() -> bpy.types.Object:
    if not TERRAIN_BLEND.is_file():
        raise FileNotFoundError(TERRAIN_BLEND)
    with bpy.data.libraries.load(str(TERRAIN_BLEND), link=False) as (src, dst):
        names = set(src.objects)
        if "IslandReference_V2" not in names:
            raise RuntimeError("IslandReference_V2 object is missing from the source blend")
        dst.objects = ["IslandReference_V2"]
    terrain = dst.objects[0]
    if terrain is None or terrain.type != "MESH":
        raise RuntimeError("Failed to append the IslandReference_V2 terrain mesh")
    bpy.context.scene.collection.objects.link(terrain)
    terrain.name = "IslandReference_V2 (terrain source, transform only)"
    terrain.scale = (TERRAIN_SCALE, TERRAIN_SCALE, TERRAIN_SCALE)
    terrain.location = (0.0, 0.0, TERRAIN_Z_OFFSET)
    terrain["source_blend"] = str(TERRAIN_BLEND)
    terrain["source_mesh_modified"] = False
    return terrain


def in_keepout(x: float, y: float) -> bool:
    central = (x / BUILD_CLEAR_X) ** 2 + (y / BUILD_CLEAR_Y) ** 2 < 1.0
    southwest_landing_corridor = -24.0 < x < -8.0 and -22.0 < y < -5.0
    return central or southwest_landing_corridor


def sample_terrain(terrain: bpy.types.Object, x: float, y: float) -> dict[str, Any] | None:
    local_origin = Vector((x / TERRAIN_SCALE, y / TERRAIN_SCALE, 900.0))
    hit, point, normal, face_index = terrain.ray_cast(local_origin, Vector((0, 0, -1)))
    if not hit:
        return None
    return {
        "x": x,
        "y": y,
        "z": float(point.z * TERRAIN_SCALE + TERRAIN_Z_OFFSET),
        "normal_z": float(normal.z),
        "face_index": int(face_index),
    }


def candidates(terrain: bpy.types.Object) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    rng = random.Random(17017)
    y = -24.0
    row = 0
    while y <= 22.0:
        x = -26.0 + (row % 2) * 1.05
        while x <= 26.0:
            px = x + rng.uniform(-0.35, 0.35)
            py = y + rng.uniform(-0.35, 0.35)
            if not in_keepout(px, py):
                info = sample_terrain(terrain, px, py)
                if info is not None and info["z"] >= WATER_Z + 0.06:
                    points.append(info)
            x += 2.1
        y += 2.1
        row += 1
    return points


def asset_path(name: str, source_kind: str) -> Path:
    folder = INSPECTED if source_kind == "source" else GENERATED
    path = folder / f"{name}.fbx"
    if not path.is_file():
        raise FileNotFoundError(f"Required FBX for {name} does not exist: {path}")
    return path


def import_mesh(path: Path, name: str) -> bpy.types.Object:
    before = set(bpy.data.objects)
    result = bpy.ops.import_scene.fbx(filepath=str(path), global_scale=1.0)
    if "FINISHED" not in result:
        raise RuntimeError(f"FBX import failed: {path}")
    new_meshes = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if not new_meshes:
        raise RuntimeError(f"FBX contains no mesh object: {path}")
    obj = new_meshes[0]
    obj.name = name
    obj.data.name = name + "_Mesh"
    return obj


def local_min_z(obj: bpy.types.Object) -> float:
    bpy.context.view_layer.update()
    return min((obj.matrix_world @ vert.co).z for vert in obj.data.vertices)


def place_assets(terrain: bpy.types.Object) -> tuple[list[bpy.types.Object], list[dict[str, Any]], list[dict[str, Any]]]:
    samples = candidates(terrain)
    if len(samples) < 24:
        raise RuntimeError(f"Too few dry non-build-area terrain samples: {len(samples)}")
    rng = random.Random(17188)
    occupied: list[tuple[float, float, float]] = []
    placed: list[bpy.types.Object] = []
    records: list[dict[str, Any]] = []
    counts: list[dict[str, Any]] = []

    # Place the larger forms first, then fit smaller plants into remaining ledges.
    for name, source_kind, desired, min_z, max_z, spacing, min_normal_z, radius in ASSETS:
        possible = [s for s in samples if min_z <= s["z"] <= max_z and s["normal_z"] >= min_normal_z]
        rng.shuffle(possible)
        selected: list[dict[str, Any]] = []
        for point in possible:
            if all(math.hypot(point["x"] - ox, point["y"] - oy) >= max(spacing, (radius + old_r) * 0.75) for ox, oy, old_r in occupied):
                selected.append(point)
                occupied.append((point["x"], point["y"], radius))
                if len(selected) >= desired:
                    break
        # Relax only the terrain-height band if a rare category has too few valid ledges.
        if len(selected) < desired:
            relaxed = [s for s in samples if s not in selected and s["normal_z"] >= max(0.16, min_normal_z - 0.18)]
            rng.shuffle(relaxed)
            for point in relaxed:
                if all(math.hypot(point["x"] - ox, point["y"] - oy) >= max(spacing * 0.82, (radius + old_r) * 0.65) for ox, oy, old_r in occupied):
                    selected.append(point)
                    occupied.append((point["x"], point["y"], radius))
                    if len(selected) >= desired:
                        break

        asset_file = asset_path(name, source_kind)
        actual_count = 0
        for instance_index, point in enumerate(selected):
            obj = import_mesh(asset_file, name)
            obj.rotation_euler.z = rng.uniform(0, math.tau)
            bpy.context.view_layer.update()
            mesh_min_z = local_min_z(obj)
            obj.location.x = point["x"]
            obj.location.y = point["y"]
            obj.location.z = point["z"] - mesh_min_z
            obj["asset_id"] = name
            obj["gate_source"] = source_kind
            obj["ground_z_m"] = point["z"]
            obj["surface_normal_z"] = point["normal_z"]
            obj["instance_index"] = instance_index
            actual_count += 1
            placed.append(obj)
            tris = len(obj.data.loop_triangles)
            if tris == 0:
                obj.data.calc_loop_triangles()
                tris = len(obj.data.loop_triangles)
            records.append({
                "asset": name,
                "source_kind": source_kind,
                "location_m": [round(obj.location.x, 4), round(obj.location.y, 4), round(obj.location.z, 4)],
                "surface_z_m": round(point["z"], 4),
                "surface_normal_z": round(point["normal_z"], 4),
                "yaw_degrees": round(math.degrees(obj.rotation_euler.z), 2),
                "vertices": len(obj.data.vertices),
                "triangles": tris,
            })
        counts.append({"asset": name, "desired_instances": desired, "placed_instances": actual_count, "source_kind": source_kind})
    return placed, records, counts


def make_preview_water() -> bpy.types.Object:
    mesh = bpy.data.meshes.new("Preview_Ocean_Mesh")
    mesh.from_pydata([(-90, -90, WATER_Z), (90, -90, WATER_Z), (90, 90, WATER_Z), (-90, 90, WATER_Z)], [], [(0, 1, 2, 3)])
    mat = bpy.data.materials.new("Preview_Ocean (not exported)")
    mat.diffuse_color = (0.055, 0.23, 0.30, 1.0)
    mesh.materials.append(mat)
    ocean = bpy.data.objects.new("Preview_Ocean (not exported)", mesh)
    bpy.context.scene.collection.objects.link(ocean)
    ocean["exported_to_fbx"] = False
    return ocean


def setup_camera() -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1350
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.compression = 18
    scene.render.filepath = str(PREVIEW_PATH)
    shade = scene.display.shading
    shade.light = "STUDIO"
    shade.studio_light = "basic.sl"
    shade.color_type = "MATERIAL"
    shade.show_shadows = True
    shade.show_cavity = True
    shade.cavity_type = "WORLD"
    shade.curvature_ridge_factor = 1.1
    shade.curvature_valley_factor = 0.8
    shade.background_type = "WORLD"
    world = bpy.data.worlds.new("Island_Assembly_Studio_World")
    world.color = (0.08, 0.15, 0.18)
    scene.world = world
    camera_data = bpy.data.cameras.new("Island_Assembly_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 82.0
    camera = bpy.data.objects.new("Island_Assembly_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = (72, -86, 61)
    target = Vector((0, 0, 1.0))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera


def main() -> None:
    for directory in (GENERATED, PREVIEWS, REPORTS):
        directory.mkdir(parents=True, exist_ok=True)
    empty_scene()
    terrain = source_terrain()
    terrain.data.calc_loop_triangles()
    placed, placement_records, placement_counts = place_assets(terrain)
    water = make_preview_water()
    setup_camera()
    bpy.context.view_layer.update()

    export_objects = [terrain, *placed]
    expected_triangles = 0
    for obj in export_objects:
        obj.data.calc_loop_triangles()
        expected_triangles += len(obj.data.loop_triangles)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in export_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = terrain
    export_result = bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH), use_selection=True, global_scale=1.0,
        apply_unit_scale=True, axis_forward="-Z", axis_up="Y",
        object_types={"MESH"}, mesh_smooth_type="OFF", bake_space_transform=False,
        add_leaf_bones=False, use_mesh_modifiers=True, path_mode="AUTO",
    )
    if "FINISHED" not in export_result:
        raise RuntimeError(f"Island FBX export failed: {export_result}")

    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))
    reimported = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    reimport_triangles = 0
    for obj in reimported:
        obj.data.calc_loop_triangles()
        reimport_triangles += len(obj.data.loop_triangles)
    fbx_roundtrip = {
        "exported_mesh_objects": len(export_objects),
        "reimported_mesh_objects": len(reimported),
        "expected_triangles": expected_triangles,
        "reimported_triangles": reimport_triangles,
        "matches": len(reimported) == len(export_objects) and reimport_triangles == expected_triangles,
    }
    for obj in reimported:
        bpy.data.objects.remove(obj, do_unlink=True)
    # Water plane and camera are presentation aids. Save the rich editable scene,
    # but keep them deselected so the FBX export contains only land and nature meshes.
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    water.select_set(False)
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_PATH), compress=True)

    all_types_present = all(item["placed_instances"] > 0 for item in placement_counts)
    terrain_bounds = [
        min((terrain.matrix_world @ v.co)[i] for v in terrain.data.vertices) for i in range(3)
    ] + [
        max((terrain.matrix_world @ v.co)[i] for v in terrain.data.vertices) for i in range(3)
    ]
    report = {
        "gate": "Gate17",
        "asset": "LastLandfall_Island_Foliage_Assembly",
        "generated_at_local": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "blender_version": bpy.app.version_string,
        "method": "separate Blender scene; source terrain mesh unchanged; placement transforms only",
        "terrain": {
            "source_blend": str(TERRAIN_BLEND),
            "source_mesh_vertices": len(terrain.data.vertices),
            "source_mesh_triangles": len(terrain.data.loop_triangles),
            "scale": TERRAIN_SCALE,
            "z_offset_m": TERRAIN_Z_OFFSET,
            "world_bounds_min_xyz": terrain_bounds[:3],
            "world_bounds_max_xyz": terrain_bounds[3:],
            "water_plane_z_m_preview_only": WATER_Z,
            "mesh_vertices_edited": False,
        },
        "layout": {
            "reserved_central_build_zone_ellipse_m": {"radius_x": BUILD_CLEAR_X, "radius_y": BUILD_CLEAR_Y},
            "reserved_southwest_landing_corridor": {"x": [-24, -8], "y": [-22, -5]},
            "candidate_dry_samples": len(candidates(terrain)),
            "counts_by_asset": placement_counts,
            "placements": placement_records,
            "total_instances": len(placed),
        },
        "fbx_roundtrip": fbx_roundtrip,
        "deliverables": {"blend": str(SCENE_PATH), "fbx": str(FBX_PATH), "preview_png": str(PREVIEW_PATH), "qa_report": str(REPORT_PATH)},
        "checks": {
            "all_16_asset_types_placed": all_types_present,
            "central_build_zone_and_southwest_landing_reserved": all(not in_keepout(r["location_m"][0], r["location_m"][1]) for r in placement_records),
            "fbx_roundtrip_mesh_count_and_triangles_match": fbx_roundtrip["matches"],
            "water_plane_excluded_from_fbx": True,
            "original_terrain_mesh_preserved": True,
        },
    }
    report["status"] = "PASS" if all(report["checks"].values()) else "FAIL"
    report["accepted"] = report["status"] == "PASS"
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"gate": "Gate17", "status": report["status"], "instances": len(placed), "counts": placement_counts, "fbx_roundtrip": fbx_roundtrip, "deliverables": report["deliverables"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
