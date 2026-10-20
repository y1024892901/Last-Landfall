# -*- coding: utf-8 -*-
"""Gate 09: locally authored Blender inspection/export for Fern_Cliffside.

Run with Blender 5.2.2:
  blender.exe -b --factory-startup -P <this file>

The source OBJ is read only. Geometry is copied 1:1 to a Z-up Blender mesh;
only the Y-up to Z-up coordinate basis conversion is applied. The FBX is
exported in Unity-friendly Y-up coordinates and re-imported for verification.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import bpy
import bmesh
from mathutils import Vector


ASSET = "Fern_Cliffside"
GATE = "Gate09"
DIM_TOL = 0.002
FLOOR_TOL = 0.002
COLOR_TOL = 1e-5


def project_root() -> Path:
    if "__file__" in globals():
        script_path = Path(__file__).resolve()
        for parent in script_path.parents:
            if (parent / "Assets" / "LastLandfall").is_dir():
                return parent
    fallback = Path(r"D:\Last Landfall")
    if (fallback / "Assets" / "LastLandfall").is_dir():
        return fallback
    raise RuntimeError("Cannot locate the Last Landfall project root")


ROOT = project_root()
NATURE = ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Nature"
OBJ = NATURE / f"{ASSET}.obj"
MTL = NATURE / f"{ASSET}.mtl"
MANIFEST = NATURE / "asset_manifest.json"
OUT = ROOT / "work" / "island_final_candidate"
SCRIPTS = OUT / "Scripts"
ASSETS = OUT / "Assets_Inspected"
PREVIEWS = OUT / "Previews"
REPORTS = OUT / "Reports"
BLEND = ASSETS / f"{ASSET}.blend"
FBX = ASSETS / f"{ASSET}.fbx"
PNG = PREVIEWS / f"{GATE}_{ASSET}.png"
REPORT = REPORTS / f"{GATE}_qa.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_inputs() -> tuple[dict[str, tuple[float, float, float]], dict[str, Any]]:
    for path in (OBJ, MTL, MANIFEST):
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Required source is missing or empty: {path}")
    material_colors: dict[str, tuple[float, float, float]] = {}
    current = None
    for raw in MTL.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.strip().split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0].lower() == "newmtl" and len(parts) > 1:
            current = " ".join(parts[1:])
        elif parts[0].lower() == "kd" and current and len(parts) >= 4:
            material_colors[current] = tuple(float(v) for v in parts[1:4])
    manifest_data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = manifest_data.get("assets", manifest_data) if isinstance(manifest_data, dict) else manifest_data
    entry = next((item for item in entries if isinstance(item, dict) and item.get("name") == ASSET), None)
    if entry is None:
        raise RuntimeError(f"{ASSET} is not listed in {MANIFEST}")
    return material_colors, entry


def parse_obj() -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]], list[str], dict[str, Any]]:
    yup: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    face_materials: list[str] = []
    current_material = ""
    nontri_faces = 0
    declared_mtllibs: list[str] = []
    raw = OBJ.read_text(encoding="utf-8", errors="replace")
    for line_number, line in enumerate(raw.splitlines(), 1):
        parts = line.strip().split()
        if not parts or parts[0].startswith("#"):
            continue
        cmd = parts[0]
        if cmd == "v" and len(parts) >= 4:
            yup.append(tuple(float(v) for v in parts[1:4]))
        elif cmd == "usemtl" and len(parts) >= 2:
            current_material = " ".join(parts[1:])
        elif cmd == "mtllib" and len(parts) >= 2:
            declared_mtllibs.append(" ".join(parts[1:]))
        elif cmd == "f" and len(parts) >= 4:
            face_indices: list[int] = []
            for token in parts[1:]:
                index = int(token.split("/")[0])
                index = len(yup) + index if index < 0 else index - 1
                if index < 0 or index >= len(yup):
                    raise ValueError(f"OBJ index out of range on line {line_number}: {token}")
                face_indices.append(index)
            if len(face_indices) != 3:
                nontri_faces += 1
            # Preserve the source polygon; Blender calculates triangles for QA/FBX.
            faces.append(tuple(face_indices))
            face_materials.append(current_material)
    if not yup or not faces:
        raise RuntimeError(f"OBJ contained no vertices or faces: {OBJ}")
    if any(not material for material in face_materials):
        raise RuntimeError("OBJ has faces without an active usemtl material")
    return yup, faces, face_materials, {
        "mtllib_declarations": declared_mtllibs,
        "face_records": len(faces),
        "non_triangle_face_records": nontri_faces,
    }


def bounds(points: list[Vector]) -> tuple[list[float], list[float], list[float]]:
    mins = [min(point[i] for point in points) for i in range(3)]
    maxs = [max(point[i] for point in points) for i in range(3)]
    return mins, maxs, [maxs[i] - mins[i] for i in range(3)]


def make_material(name: str, rgb: tuple[float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = (*rgb, 1.0)
    mat.roughness = 0.86
    shader = next((node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader:
        shader.inputs["Base Color"].default_value = (*rgb, 1.0)
        shader.inputs["Roughness"].default_value = 0.86
    return mat


def clear_factory_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    bpy.context.preferences.filepaths.save_version = 0


def world_bounds(obj: bpy.types.Object) -> tuple[list[float], list[float], list[float]]:
    bpy.context.view_layer.update()
    return bounds([obj.matrix_world @ vertex.co for vertex in obj.data.vertices])


def make_scene(asset: bpy.types.Object) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(PNG)
    scene.render.image_settings.compression = 18
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.studio_light = "paint.sl"
    shading.color_type = "MATERIAL"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "WORLD"
    shading.curvature_ridge_factor = 1.1
    shading.curvature_valley_factor = 1.0
    shading.background_type = "WORLD"
    # Neutral studio floor is for preview only and is excluded from the FBX.
    floor_mesh = bpy.data.meshes.new("Preview_Ground_Mesh")
    floor_mesh.from_pydata([(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)], [], [(0, 1, 2, 3)])
    floor_mesh.materials.append(make_material("Preview_Ground_Matte", (0.105, 0.135, 0.125)))
    floor = bpy.data.objects.new("Preview_Ground (not exported)", floor_mesh)
    bpy.context.collection.objects.link(floor)

    world = bpy.data.worlds.new("Studio_World") if not bpy.data.worlds else bpy.data.worlds[0]
    scene.world = world
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.045, 0.058, 0.055, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25

    def point_at(obj: bpy.types.Object, target: Vector) -> None:
        obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()

    target = Vector((0.11, -0.04, 0.33))
    camera_data = bpy.data.cameras.new("Preview_Camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 2.9
    camera_data.lens = 50
    camera = bpy.data.objects.new("Preview_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (2.55, -3.0, 2.0)
    point_at(camera, target)
    scene.camera = camera

    for name, location, energy, size in (
        ("Key", (-2.2, -2.5, 3.4), 180, 3.0),
        ("Fill", (2.6, -0.6, 2.4), 85, 2.2),
        ("Rim", (0.2, 2.4, 2.8), 95, 2.0),
    ):
        light_data = bpy.data.lights.new(name, type="AREA")
        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size
        light = bpy.data.objects.new(name, light_data)
        bpy.context.collection.objects.link(light)
        light.location = location
        point_at(light, target)


def main() -> None:
    for directory in (SCRIPTS, ASSETS, PREVIEWS, REPORTS):
        directory.mkdir(parents=True, exist_ok=True)
    colors, manifest_entry = read_inputs()
    yup_vertices, faces, face_materials, obj_meta = parse_obj()
    yup_vectors = [Vector(v) for v in yup_vertices]
    yup_min, yup_max, yup_dims = bounds(yup_vectors)
    # OBJ Y-up to Blender Z-up, a pure +90 degree X rotation with unchanged origin/scale.
    zup_vertices = [(x, -z, y) for x, y, z in yup_vertices]
    zup_min, zup_max, zup_dims = bounds([Vector(v) for v in zup_vertices])

    edge_set: set[tuple[int, int]] = set()
    source_material_counts: dict[str, int] = {}
    for face, material in zip(faces, face_materials):
        source_material_counts[material] = source_material_counts.get(material, 0) + len(face) - 2
        for i, a in enumerate(face):
            b = face[(i + 1) % len(face)]
            edge_set.add((min(a, b), max(a, b)))
    manifest_dims = manifest_entry.get("dimensions_m", {})
    manifest_yup_dims = [float(manifest_dims.get(axis, float("nan"))) for axis in ("x", "y", "z")]
    manifest_zup_dims = [manifest_yup_dims[0], manifest_yup_dims[2], manifest_yup_dims[1]]

    clear_factory_scene()
    mesh = bpy.data.meshes.new(ASSET)
    mesh.from_pydata(zup_vertices, [], faces)
    mesh.update(calc_edges=True)
    for material_name, rgb in colors.items():
        if material_name in source_material_counts:
            mesh.materials.append(make_material(material_name, rgb))
    material_index = {mat.name: index for index, mat in enumerate(mesh.materials)}
    for polygon, material_name in zip(mesh.polygons, face_materials):
        polygon.material_index = material_index[material_name]
        polygon.use_smooth = False
    asset = bpy.data.objects.new(ASSET, mesh)
    bpy.context.collection.objects.link(asset)
    asset.location = (0.0, 0.0, 0.0)
    asset.rotation_euler = (0.0, 0.0, 0.0)
    asset.scale = (1.0, 1.0, 1.0)
    asset["source_obj"] = str(OBJ)
    asset["coordinate_conversion"] = "OBJ Y-up -> Blender Z-up: (x, y, z) => (x, -z, y)"
    asset["source_geometry_preserved"] = True

    bpy.context.view_layer.update()
    mesh.calc_loop_triangles()
    actual_min, actual_max, actual_dims = world_bounds(asset)
    actual_material_counts: dict[str, int] = {mat.name: 0 for mat in mesh.materials}
    for polygon in mesh.polygons:
        actual_material_counts[mesh.materials[polygon.material_index].name] += len(polygon.vertices) - 2

    bm = bmesh.new()
    bm.from_mesh(mesh)
    non_manifold_edges = sum(1 for edge in bm.edges if not edge.is_manifold)
    boundary_edges = sum(1 for edge in bm.edges if edge.is_boundary)
    degenerate_faces = sum(1 for face in bm.faces if face.calc_area() <= 1e-12)
    bm.free()
    non_finite_vertices = sum(1 for vertex in mesh.vertices if not all(math.isfinite(c) for c in vertex.co))

    source_material_report = []
    all_colors_match = True
    for name, expected_rgb in colors.items():
        if name not in source_material_counts:
            continue
        material = bpy.data.materials.get(name)
        observed_rgb = list(material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value[:3])
        matches = all(abs(float(a) - float(b)) <= COLOR_TOL for a, b in zip(expected_rgb, observed_rgb))
        all_colors_match = all_colors_match and matches
        source_material_report.append({
            "name": name,
            "mtl_Kd_srgb": list(expected_rgb),
            "blender_base_color": observed_rgb,
            "triangles": actual_material_counts.get(name, 0),
            "color_match": matches,
        })

    # Export just the plant mesh. Re-import into Blender to verify the handoff artifact.
    bpy.ops.object.select_all(action="DESELECT")
    asset.select_set(True)
    bpy.context.view_layer.objects.active = asset
    export_result = bpy.ops.export_scene.fbx(
        filepath=str(FBX), use_selection=True, global_scale=1.0,
        apply_unit_scale=True, axis_forward="-Z", axis_up="Y",
        object_types={"MESH"}, mesh_smooth_type="OFF", bake_space_transform=False,
        add_leaf_bones=False, use_mesh_modifiers=True, path_mode="AUTO",
    )
    if "FINISHED" not in export_result or not FBX.is_file():
        raise RuntimeError(f"FBX export did not finish: {export_result}")
    before_import = set(bpy.data.objects)
    import_result = bpy.ops.import_scene.fbx(filepath=str(FBX))
    if "FINISHED" not in import_result:
        raise RuntimeError(f"FBX re-import did not finish: {import_result}")
    imported = [obj for obj in bpy.data.objects if obj not in before_import and obj.type == "MESH"]
    if not imported:
        raise RuntimeError("FBX re-import created no mesh object")
    imported_obj = imported[0]
    imported_obj.data.calc_loop_triangles()
    imported_min, imported_max, imported_dims = world_bounds(imported_obj)
    roundtrip = {
        "imported_mesh_objects": len(imported),
        "vertices": len(imported_obj.data.vertices),
        "edges": len(imported_obj.data.edges),
        "polygons": len(imported_obj.data.polygons),
        "triangles": len(imported_obj.data.loop_triangles),
        "bbox_min": imported_min,
        "bbox_max": imported_max,
        "dimensions": imported_dims,
    }
    fbx_match = (
        roundtrip["vertices"] == len(mesh.vertices)
        and roundtrip["triangles"] == len(mesh.loop_triangles)
        and all(abs(roundtrip["dimensions"][i] - actual_dims[i]) <= 1e-4 for i in range(3))
        and all(abs(roundtrip["bbox_min"][i] - actual_min[i]) <= 1e-4 for i in range(3))
        and all(abs(roundtrip["bbox_max"][i] - actual_max[i]) <= 1e-4 for i in range(3))
    )
    for obj in imported:
        bpy.data.objects.remove(obj, do_unlink=True)

    # Generate a clean studio render, save editable Blender source, and write a factual QA report.
    make_scene(asset)
    bpy.context.scene.render.filepath = str(PNG)
    bpy.ops.render.render(write_still=True)
    if not PNG.is_file() or PNG.stat().st_size == 0:
        raise RuntimeError(f"Preview render was not written: {PNG}")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)

    manifest_match = (
        int(manifest_entry.get("vertices", -1)) == len(yup_vertices)
        and int(manifest_entry.get("triangles", -1)) == len(mesh.loop_triangles)
        and all(abs(manifest_zup_dims[i] - zup_dims[i]) <= DIM_TOL for i in range(3))
    )
    geometry_match = (
        len(mesh.vertices) == len(yup_vertices)
        and len(mesh.edges) == len(edge_set)
        and len(mesh.loop_triangles) == sum(len(face) - 2 for face in faces)
        and all(abs(actual_dims[i] - zup_dims[i]) <= 1e-6 for i in range(3))
        and all(abs(actual_min[i] - zup_min[i]) <= 1e-6 for i in range(3))
        and all(abs(actual_max[i] - zup_max[i]) <= 1e-6 for i in range(3))
    )
    floor_deviation = actual_min[2]
    floor_match = abs(floor_deviation) <= FLOOR_TOL
    report = {
        "gate": GATE,
        "asset": ASSET,
        "generated_at_local": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "blender_version": bpy.app.version_string,
        "method": "locally authored Blender Python; original OBJ read-only; no Gemini used",
        "source": {
            "obj": {"path": str(OBJ), "bytes": OBJ.stat().st_size, "sha256": sha256(OBJ)},
            "mtl": {"path": str(MTL), "bytes": MTL.stat().st_size, "sha256": sha256(MTL)},
            "manifest_entry": manifest_entry,
            "obj_parse": obj_meta,
        },
        "source_geometry": {
            "vertices": len(yup_vertices),
            "unique_edges": len(edge_set),
            "triangles": len(mesh.loop_triangles),
            "material_triangle_counts": source_material_counts,
            "y_up_bbox_min_m": yup_min,
            "y_up_bbox_max_m": yup_max,
            "y_up_dimensions_m": yup_dims,
            "z_up_bbox_min_m": zup_min,
            "z_up_bbox_max_m": zup_max,
            "z_up_dimensions_m": zup_dims,
            "expected_z_up_dimensions_from_manifest_m": manifest_zup_dims,
        },
        "blender_mesh": {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
            "triangles": len(mesh.loop_triangles),
            "bbox_min_m": actual_min,
            "bbox_max_m": actual_max,
            "dimensions_m": actual_dims,
            "material_triangle_counts": actual_material_counts,
            "materials": source_material_report,
            "topology_diagnostics": {
                "non_manifold_edges": non_manifold_edges,
                "boundary_edges": boundary_edges,
                "degenerate_faces": degenerate_faces,
                "non_finite_vertices": non_finite_vertices,
            },
        },
        "fbx_roundtrip": {**roundtrip, "matches_blender_mesh": fbx_match},
        "deliverables": {
            "blend": str(BLEND), "fbx": str(FBX), "preview_png": str(PNG), "qa_report": str(REPORT),
        },
        "checks": {
            "manifest_matches_source": manifest_match,
            "source_geometry_preserved_in_blender": geometry_match,
            "material_colors_match_mtl": all_colors_match,
            "no_degenerate_faces": degenerate_faces == 0,
            "all_vertices_finite": non_finite_vertices == 0,
            "fbx_reimport_matches": fbx_match,
            "floor_alignment_within_2mm": floor_match,
        },
        "floor_alignment": {
            "source_minimum_y_m": yup_min[1],
            "converted_minimum_z_m": floor_deviation,
            "tolerance_m": FLOOR_TOL,
            "passed": floor_match,
            "note": "The source origin/geometry is intentionally preserved; no vertex was snapped to the floor.",
        },
        "accepted": False,
        "status": "PASS" if all((manifest_match, geometry_match, all_colors_match, degenerate_faces == 0, non_finite_vertices == 0, fbx_match, floor_match)) else "FAIL",
    }
    report["accepted"] = report["status"] == "PASS"
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"asset": ASSET, "status": report["status"], "accepted": report["accepted"], "checks": report["checks"], "deliverables": report["deliverables"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
