# -*- coding: utf-8 -*-
"""Place the reviewed bamboo asset in Gate25's upper basin woodland.

This can be rerun safely: it removes and rebuilds only its own bamboo collection.
Terrain, creek, pond, buildings, and other vegetation are preserved. On a
passing FBX round trip the ready-to-import project model is updated in-place.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import random
import shutil
from pathlib import Path
from typing import Any

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path(r"D:\Last Landfall")
if not (ROOT / "Assets" / "LastLandfall").is_dir():
    ROOT = Path(r"D:\Last Landfall")
WORK = ROOT / "work" / "island_final_candidate"
BASE_CANDIDATE = WORK / "Assets_Generated" / "LastLandfall_Island_GrassCoverage_Gate25.blend"
PROJECT_BLEND = ROOT / "Assets" / "LastLandfall" / "Art" / "Source" / "Environment" / "IslandReference_Gate25_Bamboo.blend"
BASE_BLEND = PROJECT_BLEND if PROJECT_BLEND.is_file() else BASE_CANDIDATE
BAMBOO_FBX = ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Nature" / "Bamboo_Clump_A.fbx"
if not BAMBOO_FBX.is_file():
    BAMBOO_FBX = WORK / "Assets_Generated" / "Bamboo_Clump_A.fbx"
OUT_DIR = WORK / "Assets_Generated"
PREVIEW_DIR = WORK / "Previews_Generated"
REPORT_DIR = WORK / "Reports_Generated"
OUT_BLEND = OUT_DIR / "LastLandfall_Island_GrassCoverage_Gate25_Bamboo.blend"
OUT_FBX = OUT_DIR / "LastLandfall_Island_GrassCoverage_Gate25_Bamboo.fbx"
OVERVIEW_PREVIEW = PREVIEW_DIR / "Gate34_Gate25_Bamboo_Overview.png"
CLOSEUP_PREVIEW = PREVIEW_DIR / "Gate34_Gate25_Bamboo_Basin_Closeup.png"
REPORT_PATH = REPORT_DIR / "Gate34_Gate25_Bamboo_qa.json"
PROJECT_FBX = ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Environment" / "IslandReference_Gate25.fbx"
PROJECT_PREVIEW = ROOT / "Assets" / "LastLandfall" / "Art" / "Previews" / "Environment" / "IslandReference_Gate25_Bamboo.png"
WATER_Z = -0.92
POND_CENTER = Vector((4.5, -1.8))
POND_CLEARANCE = 3.4
STREAM = [
    (8.6, 8.4), (8.6, 7.0), (8.0, 5.8), (7.6, 4.5), (6.9, 3.3),
    (6.2, 2.3), (5.8, 1.2), (5.0, 0.3), (4.7, -0.2), (4.65, -0.55),
]
TARGET_COUNT = 6
SEED = 3342026


def distance_to_path(x: float, y: float) -> float:
    p = Vector((x, y))
    best = float("inf")
    for a_raw, b_raw in zip(STREAM, STREAM[1:]):
        a, b = Vector(a_raw), Vector(b_raw)
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-8)))
        best = min(best, (p - (a + ab * t)).length)
    return best


def sample_surface(terrain: bpy.types.Object, x: float, y: float) -> dict[str, float] | None:
    inverse = terrain.matrix_world.inverted()
    origin_local = inverse @ Vector((x, y, 40.0))
    direction_local = (inverse.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    # Object.ray_cast expects a distance in local coordinates. Gate25 keeps the
    # source terrain at 0.02 scale, so a world-space 40 m ray is about 2,000
    # local units long.
    hit, local_point, local_normal, _face = terrain.ray_cast(origin_local, direction_local, distance=10000.0)
    if not hit:
        return None
    point = terrain.matrix_world @ local_point
    normal = terrain.matrix_world.to_3x3().inverted().transposed() @ local_normal
    normal.normalize()
    if normal.z < 0.0:
        normal.negate()
    return {"x": x, "y": y, "z": point.z, "normal_z": normal.z}


def make_candidates(terrain: bpy.types.Object, existing: list[bpy.types.Object]) -> list[dict[str, float]]:
    tree_xy = [(o.location.x, o.location.y) for o in existing
               if str(o.get("asset_id", "")).startswith(("Pine_", "Broadleaf_"))]
    other_xy = [(o.location.x, o.location.y) for o in existing
                if str(o.get("asset_id", "")).startswith(("Basalt_", "Fern_", "Shrub_"))]
    candidates = []
    step = 0.42
    row = 0
    y = 0.70
    while y <= 10.0:
        x = -1.0 + (0.5 * step if row % 2 else 0.0)
        while x <= 14.0:
            creek_distance = distance_to_path(x, y)
            pond_distance = math.hypot(x - POND_CENTER.x, y - POND_CENTER.y)
            building_ellipse = (x / 7.2) ** 2 + (y / 5.5) ** 2
            if 1.4 <= creek_distance <= 3.8 and pond_distance >= POND_CLEARANCE and building_ellipse >= 1.0:
                point = sample_surface(terrain, x, y)
                if point and point["z"] >= WATER_Z + 0.30 and point["normal_z"] >= 0.74:
                    nearest_tree = min((math.hypot(x - tx, y - ty) for tx, ty in tree_xy), default=99.0)
                    nearest_other = min((math.hypot(x - ox, y - oy) for ox, oy in other_xy), default=99.0)
                    if nearest_tree >= 1.75 and nearest_other >= 1.0:
                        point["creek_distance"] = creek_distance
                        point["nearest_tree_distance"] = nearest_tree
                        point["nearest_other_distance"] = nearest_other
                        candidates.append(point)
            x += step
        y += step * 0.8660254
        row += 1
    return candidates


def choose_placements(candidates: list[dict[str, float]]) -> list[dict[str, float]]:
    rng = random.Random(SEED)
    bands = [(6.0, 10.0, 3), (3.0, 6.0, 2), (0.7, 3.0, 1)]
    chosen: list[dict[str, float]] = []
    for low_y, high_y, band_count in bands:
        band = [p for p in candidates if low_y <= p["y"] < high_y]
        rng.shuffle(band)
        band.sort(key=lambda p: (
            abs(p["creek_distance"] - 2.45) * 0.9
            + max(0.0, 2.45 - p["nearest_tree_distance"]) * 1.7
            + abs(p["nearest_tree_distance"] - 3.4) * 0.10
            + rng.random() * 0.18
        ))
        added = 0
        for point in band:
            if any(math.hypot(point["x"] - p["x"], point["y"] - p["y"]) < 2.15 for p in chosen):
                continue
            chosen.append(point)
            added += 1
            if added >= band_count:
                break
    if len(chosen) < TARGET_COUNT:
        fallback = [p for p in candidates if p not in chosen]
        rng.shuffle(fallback)
        fallback.sort(key=lambda p: abs(p["creek_distance"] - 2.45) + rng.random() * 0.2)
        for point in fallback:
            if all(math.hypot(point["x"] - p["x"], point["y"] - p["y"]) >= 2.15 for p in chosen):
                chosen.append(point)
            if len(chosen) >= TARGET_COUNT:
                break
    return chosen[:TARGET_COUNT]


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)


def object_min_z(obj: bpy.types.Object) -> float:
    bpy.context.view_layer.update()
    return min((obj.matrix_world @ vertex.co).z for vertex in obj.data.vertices)


def duplicate_bamboo(template: bpy.types.Object, point: dict[str, float], collection: bpy.types.Collection,
                     index: int, rng: random.Random) -> bpy.types.Object:
    obj = template.copy()
    obj.data = template.data.copy()
    collection.objects.link(obj)
    obj.name = f"Bamboo_Basin_Clump_{index:02d}"
    obj.hide_render = False
    obj.hide_set(False)
    obj.location = (point["x"], point["y"], 0.0)
    scale = rng.uniform(0.84, 1.10)
    obj.scale = (scale, scale, scale)
    obj.rotation_euler = (rng.uniform(-0.018, 0.018), rng.uniform(-0.018, 0.018), rng.uniform(0.0, math.tau))
    bpy.context.view_layer.update()
    obj.location.z += point["z"] - object_min_z(obj)
    obj["asset_id"] = "Bamboo_Clump_A"
    obj["gameplay_resource_hint"] = "bamboo"
    obj["harvestable_resource"] = "bamboo"
    obj["harvest_group"] = "Basin_Bamboo_Grove"
    obj["surface_z_m"] = round(point["z"], 4)
    obj["surface_normal_z"] = round(point["normal_z"], 4)
    obj["creek_clearance_m"] = round(point["creek_distance"], 3)
    obj["gate_source"] = "Gate33_Bamboo_Clump_A"
    obj["gate_export"] = True
    return obj


def export_fbx(export_objects: list[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in export_objects:
        obj.select_set(True)
        obj.data.calc_loop_triangles()
    terrain = next(obj for obj in export_objects if obj.name.startswith("IslandReference_V2"))
    bpy.context.view_layer.objects.active = terrain
    result = bpy.ops.export_scene.fbx(
        filepath=str(OUT_FBX), use_selection=True, global_scale=1.0,
        apply_unit_scale=True, axis_forward="-Z", axis_up="Y",
        object_types={"MESH"}, mesh_smooth_type="OFF", bake_space_transform=False,
        add_leaf_bones=False, use_mesh_modifiers=True, path_mode="COPY", embed_textures=True,
        colors_type="SRGB", prioritize_active_color=True,
    )
    if "FINISHED" not in result:
        raise RuntimeError(f"Gate34 FBX export failed: {result}")


def render_closeup(scene: bpy.types.Scene) -> None:
    camera_data = bpy.data.cameras.new("Gate34_Bamboo_Basin_Closeup_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 22.0
    camera = bpy.data.objects.new("Gate34_Bamboo_Basin_Closeup_Camera", camera_data)
    scene.collection.objects.link(camera)
    focus = Vector((6.2, 5.0, 0.7))
    camera.location = Vector((15.0, -14.5, 13.0))
    camera.rotation_euler = (focus - camera.location).to_track_quat("-Z", "Y").to_euler()
    old_camera = scene.camera
    scene.camera = camera
    scene.render.filepath = str(CLOSEUP_PREVIEW)
    bpy.ops.render.render(write_still=True)
    scene.camera = old_camera
    bpy.data.objects.remove(camera, do_unlink=True)


def verify_existing_project_fbx(expected_tree_count: int) -> dict[str, int]:
    """If Windows locks an already imported FBX, confirm it already has this pass."""
    before = set(bpy.data.objects)
    result = bpy.ops.import_scene.fbx(filepath=str(PROJECT_FBX))
    if "FINISHED" not in result:
        raise RuntimeError("Could not read the locked project FBX for verification")
    imported = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    bamboo = [o for o in imported if o.name.startswith("Bamboo_Basin_Clump_")]
    trees = [o for o in imported if o.name.startswith(("Pine_", "Broadleaf_"))]
    for obj in imported:
        obj.data.calc_loop_triangles()
    triangles = sum(len(o.data.loop_triangles) for o in imported)
    result_data = {
        "mesh_objects": len(imported),
        "triangles": triangles,
        "bamboo_clumps": len(bamboo),
        "trees": len(trees),
    }
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)
    if len(bamboo) != TARGET_COUNT or len(trees) != expected_tree_count:
        raise RuntimeError(
            "Project FBX is locked and does not contain the expected bamboo update; "
            f"verification: {result_data}"
        )
    return result_data


def main() -> dict[str, Any]:
    for directory in (OUT_DIR, PREVIEW_DIR, REPORT_DIR, PROJECT_FBX.parent, PROJECT_BLEND.parent, PROJECT_PREVIEW.parent):
        directory.mkdir(parents=True, exist_ok=True)
    if not BASE_BLEND.is_file() or not BAMBOO_FBX.is_file():
        raise FileNotFoundError(f"Missing Gate25 base or Gate33 bamboo asset: {BASE_BLEND}, {BAMBOO_FBX}")
    bpy.ops.wm.open_mainfile(filepath=str(BASE_BLEND))
    scene = bpy.context.scene
    previous_bamboo = bpy.data.collections.get("Gate34_Bamboo_Basin_Resource_Grove")
    if previous_bamboo is not None:
        for obj in list(previous_bamboo.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(previous_bamboo)
    terrain_candidates = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("IslandReference_V2")
                          and o.get("gate_export", False)]
    if not terrain_candidates:
        raise RuntimeError("Could not find the exported Gate25 terrain mesh")
    terrain = max(terrain_candidates, key=lambda o: len(o.data.polygons))
    existing = [o for o in bpy.data.objects if o.type == "MESH" and o.get("gate_export", False)]
    candidates = make_candidates(terrain, existing)
    placements = choose_placements(candidates)
    if len(placements) != TARGET_COUNT:
        raise RuntimeError(f"Only found {len(placements)} valid bamboo bank points; expected {TARGET_COUNT}")

    before = set(bpy.data.objects)
    result = bpy.ops.import_scene.fbx(filepath=str(BAMBOO_FBX), global_scale=1.0)
    if "FINISHED" not in result:
        raise RuntimeError("Could not import the Gate33 bamboo FBX")
    templates = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if len(templates) != 1:
        raise RuntimeError(f"Expected one bamboo mesh template, found {len(templates)}")
    template = templates[0]
    template.name = "TEMPLATE_Bamboo_Clump_A"
    template.hide_render = True
    template.hide_set(True)

    collection = bpy.data.collections.new("Gate34_Bamboo_Basin_Resource_Grove")
    scene.collection.children.link(collection)
    rng = random.Random(SEED + 4)
    records = []
    for index, point in enumerate(placements, start=1):
        obj = duplicate_bamboo(template, point, collection, index, rng)
        records.append({
            "object": obj.name,
            "asset": "Bamboo_Clump_A",
            "location_m": [round(obj.location.x, 3), round(obj.location.y, 3), round(obj.location.z, 3)],
            "uniform_scale": round(obj.scale.x, 3),
            "terrain_normal_z": round(point["normal_z"], 3),
            "creek_clearance_m": round(point["creek_distance"], 3),
            "nearest_tree_clearance_m": round(point["nearest_tree_distance"], 3),
        })
    bpy.data.objects.remove(template, do_unlink=True)
    bpy.context.view_layer.update()

    # Main overview is preserved, with a separate close-up proving where the
    # damp-bank bamboo patch sits relative to the stream and surrounding trees.
    if scene.camera is None:
        raise RuntimeError("Gate25 presentation camera is missing")
    scene.render.filepath = str(OVERVIEW_PREVIEW)
    bpy.ops.render.render(write_still=True)
    render_closeup(scene)

    export_objects = [o for o in bpy.data.objects if o.type == "MESH" and o.get("gate_export", False)]
    expected_triangles = 0
    for obj in export_objects:
        obj.data.calc_loop_triangles()
        expected_triangles += len(obj.data.loop_triangles)
    export_fbx(export_objects)
    file_size = OUT_FBX.stat().st_size

    # Round-trip the combined FBX in Blender to verify mesh and triangle counts.
    old_objects = set(bpy.data.objects)
    result = bpy.ops.import_scene.fbx(filepath=str(OUT_FBX))
    if "FINISHED" not in result:
        raise RuntimeError("Gate34 FBX re-import failed")
    imported = [o for o in bpy.data.objects if o not in old_objects and o.type == "MESH"]
    imported_triangles = 0
    for obj in imported:
        obj.data.calc_loop_triangles()
        imported_triangles += len(obj.data.loop_triangles)
    fbx_roundtrip = {
        "mesh_objects": len(imported),
        "triangles": imported_triangles,
        "source_mesh_objects": len(export_objects),
        "source_triangles": expected_triangles,
        "file_size_bytes": file_size,
        "mesh_count_matches": len(imported) == len(export_objects),
        "triangle_count_matches": imported_triangles == expected_triangles,
    }
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)

    tree_count_before = sum(1 for o in existing if str(o.get("asset_id", "")).startswith(("Pine_", "Broadleaf_")))
    bamboo_count = len(records)
    checks = {
        "all_bamboo_clumps_placed": bamboo_count == TARGET_COUNT,
        "every_clump_above_sea_and_clear_of_creek": all(
            p["z"] >= WATER_Z + 0.30 and 1.4 <= p["creek_distance"] <= 3.8 and p["normal_z"] >= 0.74
            for p in placements
        ),
        "existing_tree_count_preserved": sum(
            1 for o in bpy.data.objects if o.type == "MESH" and str(o.get("asset_id", "")).startswith(("Pine_", "Broadleaf_"))
        ) == tree_count_before,
        "fbx_object_count_roundtrip": fbx_roundtrip["mesh_count_matches"],
        "fbx_triangle_count_roundtrip": fbx_roundtrip["triangle_count_matches"],
        "both_previews_rendered": OVERVIEW_PREVIEW.is_file() and CLOSEUP_PREVIEW.is_file(),
    }
    status = "PASS" if all(checks.values()) else "FAIL"

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND), compress=True)
    report = {
        "gate": "Gate34",
        "asset": "LastLandfall_Island_GrassCoverage_Gate25_Bamboo",
        "generated_at_local": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "blender_version": bpy.app.version_string,
        "source_scene": str(BASE_BLEND),
        "source_bamboo_asset": str(BAMBOO_FBX),
        "placement_design": {
            "zone": "upper basin and creekside woodland; clumps remain on dry, gentle banks",
            "target_count": TARGET_COUNT,
            "mature_culms_per_clump": 6,
            "young_shoots_per_clump": 2,
            "creek_clearance_range_m": [1.4, 3.8],
            "building_clearing_and_pond_kept_clear": True,
            "existing_vegetation_removed": False,
            "bamboo_is_marked_as_harvestable_resource": True,
        },
        "placements": records,
        "tree_count_preserved": tree_count_before,
        "bamboo_clump_count": bamboo_count,
        "fbx_roundtrip": fbx_roundtrip,
        "deliverables": {
            "blend_candidate": str(OUT_BLEND),
            "fbx_candidate": str(OUT_FBX),
            "overview_preview": str(OVERVIEW_PREVIEW),
            "basin_closeup_preview": str(CLOSEUP_PREVIEW),
            "qa_report": str(REPORT_PATH),
        },
        "checks": checks,
        "status": status,
        "ready_for_project_copy": status == "PASS",
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if status == "PASS":
        backup = OUT_DIR / "IslandReference_Gate25_before_Bamboo.fbx"
        if not backup.exists() and PROJECT_FBX.exists():
            shutil.copy2(PROJECT_FBX, backup)
        try:
            shutil.copy2(OUT_FBX, PROJECT_FBX)
            project_fbx_verification = fbx_roundtrip
            project_copy_method = "copied_candidate_fbx"
        except OSError as copy_error:
            if getattr(copy_error, "winerror", None) != 1224:
                raise
            # A Unity or editor process may memory-map the Resources FBX. The
            # current model is accepted only if a read-only FBX import confirms
            # six bamboo clumps and the original 94 trees.
            project_fbx_verification = verify_existing_project_fbx(tree_count_before)
            project_copy_method = "existing_locked_fbx_verified_in_blender"
        shutil.copy2(OUT_BLEND, PROJECT_BLEND)
        shutil.copy2(CLOSEUP_PREVIEW, PROJECT_PREVIEW)
        report["deliverables"].update({
            "project_unity_model": str(PROJECT_FBX),
            "editable_blend_source": str(PROJECT_BLEND),
            "project_preview": str(PROJECT_PREVIEW),
            "backup_before_update": str(backup),
        })
        report["project_fbx_verification"] = project_fbx_verification
        report["project_fbx_copy_method"] = project_copy_method
        report["project_model_updated"] = True
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "gate": "Gate34", "status": status,
        "placements": records, "fbx_roundtrip": fbx_roundtrip,
        "checks": checks, "deliverables": report["deliverables"],
    }, ensure_ascii=False))
    return report


if __name__ == "__main__":
    main()
