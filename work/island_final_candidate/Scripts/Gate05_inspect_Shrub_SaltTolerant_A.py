# -*- coding: utf-8 -*-
"""Gate 05: Shrub_SaltTolerant_A 单资产原样检视脚本 (Blender 5.2.2)

保存位置: D:/Last Landfall/work/island_final_candidate/Scripts/Gate05_inspect_Shrub_SaltTolerant_A.py
执行方式: blender -b --factory-startup -P "D:/Last Landfall/work/island_final_candidate/Scripts/Gate05_inspect_Shrub_SaltTolerant_A.py"
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import bmesh
import bpy
from mathutils import Vector


# ==============================================================================
# 1. 基线常量与路径推导（严格只读输入，只写 Gate05 指定产物）
# ==============================================================================

ASSET_ID: str = "Shrub_SaltTolerant_A"
BASELINE_VERTICES: int = 260
BASELINE_EDGES: int = 720
BASELINE_TRIANGLES: int = 480

BASELINE_YUP_MIN: Tuple[float, float, float] = (-0.564236, -0.102168, -0.434761)
BASELINE_YUP_MAX: Tuple[float, float, float] = (0.521398, 0.539693, 0.451435)
BASELINE_YUP_DIMS: Tuple[float, float, float] = (1.085634, 0.641861, 0.886196)

BASELINE_ZUP_MIN: Tuple[float, float, float] = (-0.564236, -0.451435, -0.102168)
BASELINE_ZUP_MAX: Tuple[float, float, float] = (0.521398, 0.434761, 0.539693)
BASELINE_ZUP_DIMS: Tuple[float, float, float] = (1.085634, 0.886196, 0.641861)
EXPECTED_MIN_Z: float = -0.102168

MANIFEST_ROUNDED_YUP_DIMS: Tuple[float, float, float] = (1.086, 0.642, 0.886)
MANIFEST_ORIGIN_LABEL: str = "ground centre"

DIM_TOLERANCE_M: float = 0.002
FLOOR_TOLERANCE_M: float = 0.002
KD_TOLERANCE: float = 0.005

EXPECTED_MATERIAL_TRI_COUNTS: Dict[str, int] = {
    "bark": 80,
    "leaf_sun": 96,
    "leaf": 61,
    "leaf_shadow": 165,
    "leaf_deep": 53,
    "leaf_salt": 25,
}

EXPECTED_MATERIAL_KD: Dict[str, Tuple[float, float, float]] = {
    "bark": (0.34, 0.25, 0.18),
    "leaf": (0.31, 0.50, 0.34),
    "leaf_deep": (0.20, 0.39, 0.29),
    "leaf_salt": (0.64, 0.68, 0.48),
    "leaf_shadow": (0.14, 0.29, 0.23),
    "leaf_sun": (0.48, 0.62, 0.39),
}


def resolve_project_root() -> Path:
    """从脚本自身路径向上稳定推导项目根目录 D:/Last Landfall。"""
    if "__file__" in globals() and globals()["__file__"]:
        script_path = Path(globals()["__file__"]).resolve()
        for parent in script_path.parents:
            if (parent / "Assets").is_dir() and (parent / "Tools" / "Blender").is_dir():
                return parent
        if len(script_path.parents) >= 4:
            cand = script_path.parents[3]
            if cand.exists():
                return cand
    fallback = Path(r"D:\Last Landfall")
    if fallback.exists():
        return fallback
    raise RuntimeError(
        "无法从脚本自身位置推导项目根目录，请确认脚本位于 D:/Last Landfall/work/island_final_candidate/Scripts/ 下。"
    )


PROJECT_ROOT: Path = resolve_project_root()

NATURE_DIR: Path = (
    PROJECT_ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Nature"
)
SOURCE_OBJ_PATH: Path = (NATURE_DIR / f"{ASSET_ID}.obj").resolve()
SOURCE_MTL_PATH: Path = (NATURE_DIR / f"{ASSET_ID}.mtl").resolve()
MANIFEST_PATH: Path = (NATURE_DIR / "asset_manifest.json").resolve()

OUTPUT_ROOT: Path = (PROJECT_ROOT / "work" / "island_final_candidate").resolve()
OUT_SCRIPTS_DIR: Path = OUTPUT_ROOT / "Scripts"
OUT_ASSETS_DIR: Path = OUTPUT_ROOT / "Assets_Inspected"
OUT_PREVIEWS_DIR: Path = OUTPUT_ROOT / "Previews"
OUT_REPORTS_DIR: Path = OUTPUT_ROOT / "Reports"

OUT_BLEND_PATH: Path = (OUT_ASSETS_DIR / f"{ASSET_ID}.blend").resolve()
OUT_FBX_PATH: Path = (OUT_ASSETS_DIR / f"{ASSET_ID}.fbx").resolve()
OUT_PREVIEW_PNG_PATH: Path = (OUT_PREVIEWS_DIR / f"Gate05_{ASSET_ID}.png").resolve()
OUT_REPORT_JSON_PATH: Path = (OUT_REPORTS_DIR / "Gate05_qa.json").resolve()


# ==============================================================================
# 2. 输入校验、SHA-256 计算与 Manifest 读取
# ==============================================================================


def compute_sha256(filepath: Path) -> str:
    """使用标准库 hashlib 计算文件 SHA-256 摘要。"""
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def verify_inputs_and_load_manifest() -> Dict[str, Any]:
    """验证源 OBJ、MTL、asset_manifest.json 均存在且非空，缺失时抛出包含具体绝对路径的异常。"""
    required_inputs: List[Tuple[str, Path]] = [
        ("自然资产源 OBJ", SOURCE_OBJ_PATH),
        ("自然资产源 MTL", SOURCE_MTL_PATH),
        ("自然资产清单 asset_manifest.json", MANIFEST_PATH),
    ]
    for label, path in required_inputs:
        abs_path = path.resolve()
        if not abs_path.exists() or not abs_path.is_file():
            raise FileNotFoundError(
                f"Gate 05 前置校验失败：缺少{label}，绝对路径: {abs_path}"
            )
        if abs_path.stat().st_size == 0:
            raise RuntimeError(
                f"Gate 05 前置校验失败：{label} 文件大小为 0，绝对路径: {abs_path}"
            )

    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest_raw = json.load(f)

    manifest_entry: Optional[Dict[str, Any]] = None
    if isinstance(manifest_raw, list):
        for item in manifest_raw:
            if isinstance(item, dict) and str(
                item.get("id") or item.get("name") or item.get("asset_id") or ""
            ).startswith(ASSET_ID):
                manifest_entry = item
                break
    elif isinstance(manifest_raw, dict):
        if ASSET_ID in manifest_raw and isinstance(manifest_raw[ASSET_ID], dict):
            manifest_entry = manifest_raw[ASSET_ID]
        else:
            for k in ("assets", "models", "items", "entries", "nature_assets"):
                sub = manifest_raw.get(k)
                if isinstance(sub, list):
                    for item in sub:
                        if isinstance(item, dict):
                            ident = str(
                                item.get("id")
                                or item.get("name")
                                or item.get("asset_id")
                                or item.get("file")
                                or ""
                            )
                            if ASSET_ID in ident:
                                manifest_entry = item
                                break
                elif isinstance(sub, dict) and ASSET_ID in sub:
                    manifest_entry = sub[ASSET_ID]
                    break

    return {
        "obj": {
            "path": str(SOURCE_OBJ_PATH),
            "size_bytes": SOURCE_OBJ_PATH.stat().st_size,
            "sha256": compute_sha256(SOURCE_OBJ_PATH),
        },
        "mtl": {
            "path": str(SOURCE_MTL_PATH),
            "size_bytes": SOURCE_MTL_PATH.stat().st_size,
            "sha256": compute_sha256(SOURCE_MTL_PATH),
        },
        "manifest": {
            "path": str(MANIFEST_PATH),
            "size_bytes": MANIFEST_PATH.stat().st_size,
            "sha256": compute_sha256(MANIFEST_PATH),
            "matched_entry": manifest_entry,
        },
    }


# ==============================================================================
# 3. OBJ / MTL 原样解析与 Z-up (1:1 米制，零位移零修形) 网格构建
# ==============================================================================


def parse_mtl_kd(mtl_path: Path) -> Dict[str, Tuple[float, float, float]]:
    """使用标准库从源 MTL 文件读取全部 newmtl 与 Kd 漫反射 RGB（严禁硬编码覆盖）。"""
    kd_map: Dict[str, Tuple[float, float, float]] = {}
    current_mtl: Optional[str] = None

    with mtl_path.open("r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            cmd = parts[0].lower()
            if cmd == "newmtl" and len(parts) >= 2:
                current_mtl = " ".join(parts[1:]).strip()
                kd_map.setdefault(current_mtl, (0.5, 0.5, 0.5))
            elif cmd == "kd" and current_mtl is not None and len(parts) >= 4:
                r = float(parts[1])
                g = float(parts[2])
                b = float(parts[3])
                kd_map[current_mtl] = (r, g, b)

    if not kd_map:
        raise RuntimeError(f"MTL 文件未解析出任何 newmtl/Kd 定义: {mtl_path}")
    return kd_map


def create_exportable_principled_material(
    mat_name: str, rgb: Tuple[float, float, float], roughness: float = 0.88
) -> bpy.types.Material:
    """创建包含 Principled BSDF Base Color 的可导出材质。"""
    existing = bpy.data.materials.get(mat_name)
    if existing is not None:
        bpy.data.materials.remove(existing, do_unlink=True)

    mat = bpy.data.materials.new(name=mat_name)
    r, g, b = float(rgb[0]), float(rgb[1]), float(rgb[2])
    mat.diffuse_color = (r, g, b, 1.0)
    mat.roughness = roughness
    mat.metallic = 0.0
    mat.use_nodes = True

    if mat.node_tree is not None:
        nodes = mat.node_tree.nodes
        bsdf = None
        for node in nodes:
            if node.type == "BSDF_PRINCIPLED":
                bsdf = node
                break
        if bsdf is None:
            bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
            out_node = None
            for node in nodes:
                if node.type == "OUTPUT_MATERIAL":
                    out_node = node
                    break
            if out_node is None:
                out_node = nodes.new(type="ShaderNodeOutputMaterial")
            if "BSDF" in bsdf.outputs and "Surface" in out_node.inputs:
                mat.node_tree.links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0

    return mat


def parse_obj_and_build_as_is_asset(
    obj_path: Path, mtl_path: Path
) -> Tuple[bpy.types.Object, Dict[str, Any]]:
    """标准库解析 OBJ 的 v/vt/vn/mtllib/usemtl/f，支持正负索引与多边形面扇三角化。

    执行右手变换 X_bl=X_obj, Y_bl=-Z_obj, Z_bl=Y_obj，保持 1:1 米制与源原点 (0,0,0)。
    仅关闭平滑以呈现原有低多边形硬边，绝不改动顶点坐标或拓扑。
    """
    kd_map = parse_mtl_kd(mtl_path)

    verts_yup: List[Tuple[float, float, float]] = []
    verts_zup: List[Tuple[float, float, float]] = []
    vt_coords: List[Tuple[float, ...]] = []
    vn_coords: List[Tuple[float, float, float]] = []
    faces_indices: List[Tuple[int, int, int]] = []
    faces_mat_names: List[str] = []
    mtllib_declarations: List[str] = []
    current_mat: str = next(iter(kd_map.keys()))

    raw_face_record_count = 0
    non_triangle_face_records = 0
    fan_triangulated_extra_tris = 0

    with obj_path.open("r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            cmd = parts[0]
            if cmd == "v" and len(parts) >= 4:
                x_obj = float(parts[1])
                y_obj = float(parts[2])
                z_obj = float(parts[3])
                verts_yup.append((x_obj, y_obj, z_obj))
                # 右手坐标映射: X_bl = X_obj, Y_bl = -Z_obj, Z_bl = Y_obj
                verts_zup.append((x_obj, -z_obj, y_obj))
            elif cmd == "vt" and len(parts) >= 3:
                vt_coords.append(tuple(float(x) for x in parts[1:]))
            elif cmd == "vn" and len(parts) >= 4:
                nx = float(parts[1])
                ny = float(parts[2])
                nz = float(parts[3])
                vn_coords.append((nx, -nz, ny))
            elif cmd == "mtllib" and len(parts) >= 2:
                mtllib_declarations.append(" ".join(parts[1:]).strip())
            elif cmd == "usemtl" and len(parts) >= 2:
                current_mat = " ".join(parts[1:]).strip()
            elif cmd == "f" and len(parts) >= 4:
                raw_face_record_count += 1
                n_v = len(verts_zup)
                poly_verts: List[int] = []
                for token in parts[1:]:
                    v_str = token.split("/")[0]
                    idx = int(v_str)
                    idx = (n_v + idx) if idx < 0 else (idx - 1)
                    if idx < 0 or idx >= n_v:
                        raise ValueError(
                            f"OBJ 顶点索引越界: {token} (当前已解析顶点数={n_v})"
                        )
                    poly_verts.append(idx)
                if len(poly_verts) == 3:
                    faces_indices.append((poly_verts[0], poly_verts[1], poly_verts[2]))
                    faces_mat_names.append(current_mat)
                else:
                    non_triangle_face_records += 1
                    fan_triangulated_extra_tris += len(poly_verts) - 3
                    for i in range(1, len(poly_verts) - 1):
                        faces_indices.append(
                            (poly_verts[0], poly_verts[i], poly_verts[i + 1])
                        )
                        faces_mat_names.append(current_mat)

    if not verts_zup or not faces_indices:
        raise RuntimeError(f"OBJ 解析为空: {obj_path}")

    # 计算源 Y-up 包围盒与尺寸（直接根据实际 OBJ 顶点计算）
    yup_xs = [v[0] for v in verts_yup]
    yup_ys = [v[1] for v in verts_yup]
    yup_zs = [v[2] for v in verts_yup]
    yup_min = (min(yup_xs), min(yup_ys), min(yup_zs))
    yup_max = (max(yup_xs), max(yup_ys), max(yup_zs))
    yup_dims = (
        yup_max[0] - yup_min[0],
        yup_max[1] - yup_min[1],
        yup_max[2] - yup_min[2],
    )

    # 统计源 OBJ 中的唯一无向边数量
    unique_obj_edges = set()
    for v0, v1, v2 in faces_indices:
        unique_obj_edges.add((min(v0, v1), max(v0, v1)))
        unique_obj_edges.add((min(v1, v2), max(v1, v2)))
        unique_obj_edges.add((min(v2, v0), max(v2, v0)))

    # 创建独立清晰命名的 Blender Mesh 与 Object（原点、位置、旋转、缩放严格保持默认）
    mesh = bpy.data.meshes.new(ASSET_ID)
    mesh.from_pydata(verts_zup, [], faces_indices)

    # 按 MTL 定义顺序与 usemtl 建立材质槽
    slot_names: List[str] = []
    for m_name in kd_map.keys():
        if m_name in faces_mat_names and m_name not in slot_names:
            slot_names.append(m_name)
    for m_name in faces_mat_names:
        if m_name not in slot_names:
            slot_names.append(m_name)

    mat_to_slot: Dict[str, int] = {}
    for idx, m_name in enumerate(slot_names):
        if m_name not in kd_map:
            raise KeyError(f"OBJ 中使用的材质 '{m_name}' 在 MTL ({mtl_path}) 中未定义。")
        rgb = kd_map[m_name]
        bl_mat = create_exportable_principled_material(m_name, rgb, roughness=0.88)
        mesh.materials.append(bl_mat)
        mat_to_slot[m_name] = idx

    for poly_idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_to_slot[faces_mat_names[poly_idx]]
        poly.use_smooth = False

    mesh.update()

    obj = bpy.data.objects.new(ASSET_ID, mesh)
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj["gate05_managed"] = True

    parse_meta = {
        "mtllib_declarations": mtllib_declarations,
        "parsed_vt_count": len(vt_coords),
        "parsed_vn_count": len(vn_coords),
        "raw_face_records_in_obj": raw_face_record_count,
        "non_triangle_face_records_in_obj": non_triangle_face_records,
        "fan_triangulated_extra_triangles": fan_triangulated_extra_tris,
        "unique_edges_in_obj": len(unique_obj_edges),
        "triangulation_note": (
            "All 480 OBJ source faces are triangles (0 non-triangle faces)."
            if non_triangle_face_records == 0
            else f"OBJ contained {non_triangle_face_records} polygon faces fan-triangulated."
        ),
        "source_yup_bbox_min_m": [round(v, 6) for v in yup_min],
        "source_yup_bbox_max_m": [round(v, 6) for v in yup_max],
        "source_yup_dimensions_m": [round(v, 6) for v in yup_dims],
        "source_lowest_y_m": round(yup_min[1], 6),
        "parsed_mtl_materials_kd": {
            k: [round(c, 6) for c in v] for k, v in kd_map.items()
        },
    }
    return obj, parse_meta


# ==============================================================================
# 4. 严格几何/材质/拓扑 QA 核验（如实报告 floor alignment FAIL 与 manifest 差异，不中止写盘）
# ==============================================================================


def inspect_and_verify_asset(
    asset_obj: bpy.types.Object,
    parse_meta: Dict[str, Any],
    manifest_entry: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """实测顶点/边/多边形/三角面数、Z-up 包围盒与尺寸、逐材质 Kd 与面数分布、拓扑诊断及落地偏差。"""
    bpy.context.view_layer.update()
    mesh: bpy.types.Mesh = asset_obj.data
    mat_world = asset_obj.matrix_world.copy()

    verts_world = [mat_world @ v.co for v in mesh.vertices]
    xs = [v.x for v in verts_world]
    ys = [v.y for v in verts_world]
    zs = [v.z for v in verts_world]

    bbox_min = (min(xs), min(ys), min(zs))
    bbox_max = (max(xs), max(ys), max(zs))
    measured_dims = (
        bbox_max[0] - bbox_min[0],
        bbox_max[1] - bbox_min[1],
        bbox_max[2] - bbox_min[2],
    )

    vert_count = len(mesh.vertices)
    edge_count = len(mesh.edges)
    poly_count = len(mesh.polygons)
    tri_count = len(mesh.loop_triangles)

    # 材质槽面数与 Kd 颜色核对
    slot_face_counts: Dict[int, int] = {i: 0 for i in range(len(mesh.materials))}
    for poly in mesh.polygons:
        slot_face_counts[int(poly.material_index)] = (
            slot_face_counts.get(int(poly.material_index), 0) + 1
        )

    materials_report: List[Dict[str, Any]] = []
    actual_mat_tri_map: Dict[str, int] = {}
    material_count_diffs: Dict[str, int] = {}
    total_material_tris = 0
    all_kd_match = True

    for idx, mat in enumerate(mesh.materials):
        m_name = mat.name if mat else f"Slot_{idx}"
        parsed_kd = parse_meta["parsed_mtl_materials_kd"].get(m_name, [0.5, 0.5, 0.5])
        expected_kd = EXPECTED_MATERIAL_KD.get(m_name)

        bsdf_rgb = list(mat.diffuse_color[:3]) if mat else [0.5, 0.5, 0.5]
        if mat and mat.use_nodes and mat.node_tree:
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED" and "Base Color" in node.inputs:
                    val = node.inputs["Base Color"].default_value
                    bsdf_rgb = [float(val[0]), float(val[1]), float(val[2])]
                    break

        kd_match_this = False
        if expected_kd is not None and len(parsed_kd) >= 3:
            kd_match_this = all(
                abs(float(parsed_kd[c]) - float(expected_kd[c])) <= KD_TOLERANCE
                for c in range(3)
            ) and all(
                abs(float(bsdf_rgb[c]) - float(parsed_kd[c])) <= 1e-5
                for c in range(3)
            )
        if not kd_match_this:
            all_kd_match = False

        f_cnt = slot_face_counts.get(idx, 0)
        total_material_tris += f_cnt
        actual_mat_tri_map[m_name] = f_cnt
        expected_cnt = EXPECTED_MATERIAL_TRI_COUNTS.get(m_name, 0)
        diff_cnt = f_cnt - expected_cnt
        material_count_diffs[m_name] = diff_cnt

        materials_report.append(
            {
                "slot_index": idx,
                "material_name": m_name,
                "mtl_kd_rgb": [round(float(c), 6) for c in parsed_kd],
                "expected_kd_rgb": list(expected_kd) if expected_kd else None,
                "principled_base_color_rgb": [round(float(c), 6) for c in bsdf_rgb],
                "kd_matches_expected": kd_match_this,
                "triangle_count": f_cnt,
                "expected_triangle_count": expected_cnt,
                "triangle_count_diff": diff_cnt,
                "triangle_count_match": (f_cnt == expected_cnt),
                "triangle_ratio_pct": round(f_cnt * 100.0 / max(1, tri_count), 2),
            }
        )

    for exp_name, exp_cnt in EXPECTED_MATERIAL_TRI_COUNTS.items():
        if exp_name not in actual_mat_tri_map:
            material_count_diffs[exp_name] = -exp_cnt
            all_kd_match = False

    materials_distribution_pass = (
        actual_mat_tri_map == EXPECTED_MATERIAL_TRI_COUNTS
        and total_material_tris == BASELINE_TRIANGLES
        and len(mesh.materials) == len(EXPECTED_MATERIAL_TRI_COUNTS)
    )
    materials_kd_pass = all_kd_match

    # 只读 bmesh 拓扑自检（绝不写回或修改源网格；叶片开放边只作诊断，不因此判失败或填洞）
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    loose_verts = sum(1 for v in bm.verts if len(v.link_edges) == 0)
    loose_edges = sum(1 for e in bm.edges if len(e.link_faces) == 0)
    open_boundary_edges = sum(1 for e in bm.edges if e.is_boundary)
    non_boundary_non_manifold_edges = sum(
        1 for e in bm.edges if (not e.is_boundary and not e.is_manifold)
    )
    zero_area_faces = sum(1 for f in bm.faces if f.calc_area() <= 1e-8)
    degenerate_faces = sum(
        1
        for f in bm.faces
        if len(set(v.index for v in f.verts)) < 3 or f.calc_area() <= 1e-8
    )

    seen_face_keys = set()
    duplicate_faces = 0
    for f in bm.faces:
        key = tuple(sorted(v.index for v in f.verts))
        if key in seen_face_keys:
            duplicate_faces += 1
        else:
            seen_face_keys.add(key)

    bm.free()

    # 逐项基线核对
    dim_errors = (
        abs(measured_dims[0] - BASELINE_ZUP_DIMS[0]),
        abs(measured_dims[1] - BASELINE_ZUP_DIMS[1]),
        abs(measured_dims[2] - BASELINE_ZUP_DIMS[2]),
    )
    bbox_min_errors = (
        abs(bbox_min[0] - BASELINE_ZUP_MIN[0]),
        abs(bbox_min[1] - BASELINE_ZUP_MIN[1]),
        abs(bbox_min[2] - BASELINE_ZUP_MIN[2]),
    )
    bbox_max_errors = (
        abs(bbox_max[0] - BASELINE_ZUP_MAX[0]),
        abs(bbox_max[1] - BASELINE_ZUP_MAX[1]),
        abs(bbox_max[2] - BASELINE_ZUP_MAX[2]),
    )

    dims_pass = all(err <= DIM_TOLERANCE_M for err in dim_errors) and all(
        err <= DIM_TOLERANCE_M for err in bbox_min_errors
    ) and all(err <= DIM_TOLERANCE_M for err in bbox_max_errors)
    verts_pass = vert_count == BASELINE_VERTICES
    edges_pass = edge_count == BASELINE_EDGES
    tris_pass = (
        tri_count == BASELINE_TRIANGLES
        and poly_count == BASELINE_TRIANGLES
        and parse_meta["non_triangle_face_records_in_obj"] == 0
    )

    # 落地偏差核对：源 OBJ 实测最低 Y = -0.102168m -> 转换后最低 Z = -0.102168m，
    # 在 ±0.002m 地面容差下必须报告 FAIL（低于零面 102.168mm）
    lowest_z_m = bbox_min[2]
    floor_deviation_m = lowest_z_m - 0.0
    floor_deviation_mm = floor_deviation_m * 1000.0
    floor_alignment_pass = abs(floor_deviation_m) <= FLOOR_TOLERANCE_M

    origin_preserved_pass = (
        asset_obj.location.length <= 1e-6
        and tuple(round(s, 5) for s in asset_obj.scale) == (1.0, 1.0, 1.0)
        and tuple(round(r, 5) for r in asset_obj.rotation_euler) == (0.0, 0.0, 0.0)
    )
    mesh_clean_pass = (
        degenerate_faces == 0
        and zero_area_faces == 0
        and duplicate_faces == 0
        and loose_verts == 0
    )

    checks_summary: Dict[str, str] = {
        "vertex_count_check": "PASS" if verts_pass else "FAIL",
        "edge_count_check": "PASS" if edges_pass else "FAIL",
        "triangle_count_check": "PASS" if tris_pass else "FAIL",
        "dimensions_and_bbox_zup_check": "PASS" if dims_pass else "FAIL",
        "materials_6_slots_distribution_check": "PASS" if materials_distribution_pass else "FAIL",
        "materials_kd_color_check": "PASS" if materials_kd_pass else "FAIL",
        "origin_and_transform_preserved_check": "PASS" if origin_preserved_pass else "FAIL",
        "mesh_integrity_check": "PASS" if mesh_clean_pass else "FAIL",
        "floor_alignment_check": "PASS" if floor_alignment_pass else "FAIL",
    }

    failure_reasons: List[str] = []
    if not verts_pass:
        failure_reasons.append(
            f"vertex_count_check FAIL: 实测顶点数={vert_count}, 基线={BASELINE_VERTICES} (差值={vert_count - BASELINE_VERTICES:+d})"
        )
    if not edges_pass:
        failure_reasons.append(
            f"edge_count_check FAIL: 实测唯一边数={edge_count}, 基线={BASELINE_EDGES} (差值={edge_count - BASELINE_EDGES:+d})"
        )
    if not tris_pass:
        failure_reasons.append(
            f"triangle_count_check FAIL: 实测三角面数={tri_count} (多边形数={poly_count}), 基线={BASELINE_TRIANGLES}"
        )
    if not dims_pass:
        failure_reasons.append(
            f"dimensions_and_bbox_zup_check FAIL: 实测 Z-up 尺寸={tuple(round(d, 6) for d in measured_dims)}m, "
            f"预期={BASELINE_ZUP_DIMS}m, 逐轴误差={tuple(round(e, 6) for e in dim_errors)}m (容差 ±{DIM_TOLERANCE_M}m)"
        )
    if not materials_distribution_pass:
        failure_reasons.append(
            f"materials_6_slots_distribution_check FAIL: 实测材质面数={actual_mat_tri_map} (总计={total_material_tris}), "
            f"预期={EXPECTED_MATERIAL_TRI_COUNTS} (总计={BASELINE_TRIANGLES}), 差异={material_count_diffs}"
        )
    if not materials_kd_pass:
        failure_reasons.append(
            "materials_kd_color_check FAIL: MTL 解析出的 Kd 与预期材质颜色存在偏差。"
        )
    if not origin_preserved_pass:
        failure_reasons.append(
            f"origin_and_transform_preserved_check FAIL: location={tuple(asset_obj.location)}, scale={tuple(asset_obj.scale)}"
        )
    if not mesh_clean_pass:
        failure_reasons.append(
            f"mesh_integrity_check FAIL: degenerate_faces={degenerate_faces}, zero_area_faces={zero_area_faces}, "
            f"duplicate_faces={duplicate_faces}, loose_verts={loose_verts}"
        )
    if not floor_alignment_pass:
        failure_reasons.append(
            f"floor_alignment_check FAIL: manifest 标记 origin 为 '{MANIFEST_ORIGIN_LABEL}'，但源 OBJ 实测最低 Y={parse_meta['source_lowest_y_m']:+.6f}m，"
            f"转换后最低 Z={lowest_z_m:+.6f}m (低于零面 {abs(floor_deviation_mm):.3f}mm)，超出地面容差 ±{FLOOR_TOLERANCE_M:.3f}m；"
            "严格保留源顶点与对象原点 (0,0,0) 未移动或修形。"
        )

    overall_pass = len(failure_reasons) == 0

    return {
        "model_name": ASSET_ID,
        "coordinate_mapping": "X_bl = X_obj, Y_bl = -Z_obj, Z_bl = Y_obj (Right-handed Y-up to Blender Z-up)",
        "unit_system": "METRIC (1:1 meters)",
        "overall_status": "PASS" if overall_pass else "FAIL",
        "overall_pass": overall_pass,
        "checks_summary": checks_summary,
        "failure_reasons": failure_reasons,
        "geometry_counts": {
            "vertex_count": vert_count,
            "baseline_vertex_count": BASELINE_VERTICES,
            "vertex_count_diff": vert_count - BASELINE_VERTICES,
            "vertex_count_pass": verts_pass,
            "edge_count": edge_count,
            "baseline_edge_count": BASELINE_EDGES,
            "edge_count_diff": edge_count - BASELINE_EDGES,
            "edge_count_pass": edges_pass,
            "polygon_count": poly_count,
            "triangle_count": tri_count,
            "baseline_triangle_count": BASELINE_TRIANGLES,
            "triangle_count_diff": tri_count - BASELINE_TRIANGLES,
            "all_source_faces_are_triangles": (
                parse_meta["non_triangle_face_records_in_obj"] == 0
                and poly_count == tri_count
            ),
            "triangle_count_pass": tris_pass,
        },
        "dimensions_and_bounds": {
            "manifest_rounded_yup_dimensions_m": list(MANIFEST_ROUNDED_YUP_DIMS),
            "source_yup_bbox_min_m": parse_meta["source_yup_bbox_min_m"],
            "source_yup_bbox_max_m": parse_meta["source_yup_bbox_max_m"],
            "source_yup_dimensions_m": parse_meta["source_yup_dimensions_m"],
            "expected_zup_bbox_min_m": [round(v, 6) for v in BASELINE_ZUP_MIN],
            "expected_zup_bbox_max_m": [round(v, 6) for v in BASELINE_ZUP_MAX],
            "expected_zup_dimensions_m": [round(v, 6) for v in BASELINE_ZUP_DIMS],
            "measured_zup_bbox_min_m": [round(v, 6) for v in bbox_min],
            "measured_zup_bbox_max_m": [round(v, 6) for v in bbox_max],
            "measured_zup_dimensions_m": [round(d, 6) for d in measured_dims],
            "bbox_min_errors_m": [round(e, 6) for e in bbox_min_errors],
            "bbox_max_errors_m": [round(e, 6) for e in bbox_max_errors],
            "axis_dimension_errors_m": [round(e, 6) for e in dim_errors],
            "dimension_tolerance_m": DIM_TOLERANCE_M,
            "dimensions_pass": dims_pass,
        },
        "manifest_vs_source_geometry_discrepancy": {
            "manifest_entry": manifest_entry,
            "manifest_declared_origin": MANIFEST_ORIGIN_LABEL,
            "manifest_rounded_dimensions_yup_m": list(MANIFEST_ROUNDED_YUP_DIMS),
            "measured_exact_dimensions_yup_m": parse_meta["source_yup_dimensions_m"],
            "measured_source_lowest_y_m": parse_meta["source_lowest_y_m"],
            "measured_converted_lowest_z_m": round(lowest_z_m, 6),
            "discrepancy_explanation": (
                "asset_manifest.json 将尺寸四舍五入为 (1.086, 0.642, 0.886)m 并标注 origin 为 'ground centre'，"
                "但源 OBJ 实际顶点最低点为 Y = -0.102168m（转换至 Blender Z-up 后最低点 Z = -0.102168m，低于 Z=0 地面 102.168mm）。"
                "按原样检视要求，严禁移动对象或修改顶点掩盖该差异，如实记录并标记 floor_alignment_check 为 FAIL。"
            ),
        },
        "origin_and_floor_alignment_qa": {
            "status": "PASS" if floor_alignment_pass else "FAIL",
            "pass": floor_alignment_pass,
            "object_origin_world_xyz_m": [
                round(float(v), 6) for v in asset_obj.location
            ],
            "source_obj_origin_xyz_m": [0.0, 0.0, 0.0],
            "source_lowest_y_m": parse_meta["source_lowest_y_m"],
            "converted_lowest_z_m": round(lowest_z_m, 6),
            "target_ground_z_m": 0.0,
            "floor_deviation_m": round(floor_deviation_m, 6),
            "floor_deviation_mm": round(floor_deviation_mm, 3),
            "floor_tolerance_m": FLOOR_TOLERANCE_M,
            "diagnostic_note": (
                f"对象位置保持 (0,0,0)，源最低点转换后 Z={lowest_z_m:+.6f}m "
                f"(低于零面 {abs(floor_deviation_mm):.3f}mm)，超出 ±{FLOOR_TOLERANCE_M:.3f}m 容差，floor alignment 判定为 FAIL。"
            ),
        },
        "world_transform": {
            "location_xyz_m": [round(float(v), 6) for v in asset_obj.location],
            "rotation_euler_deg": [
                round(math.degrees(float(v)), 4) for v in asset_obj.rotation_euler
            ],
            "scale_xyz": [round(float(v), 6) for v in asset_obj.scale],
            "matrix_world": [
                [round(float(mat_world[r][c]), 6) for c in range(4)] for r in range(4)
            ],
        },
        "materials_statistics": {
            "material_slot_count": len(mesh.materials),
            "expected_material_slot_count": len(EXPECTED_MATERIAL_TRI_COUNTS),
            "total_material_triangles": total_material_tris,
            "expected_material_triangle_counts": EXPECTED_MATERIAL_TRI_COUNTS,
            "actual_material_triangle_counts": actual_mat_tri_map,
            "material_triangle_count_differences": material_count_diffs,
            "materials_distribution_pass": materials_distribution_pass,
            "materials_kd_pass": materials_kd_pass,
            "slots": materials_report,
        },
        "topology_diagnostics": {
            "degenerate_triangle_count": degenerate_faces,
            "zero_area_triangle_count": zero_area_faces,
            "duplicate_face_count": duplicate_faces,
            "loose_vertex_count": loose_verts,
            "loose_edge_count": loose_edges,
            "open_boundary_edge_count": open_boundary_edges,
            "non_boundary_non_manifold_edge_count": non_boundary_non_manifold_edges,
            "diagnostic_note": (
                "植物叶片/枝干表面允许存在开放边界边 (open_boundary_edge_count)，仅作为诊断信息报告，不因此判失败或执行填洞。"
            ),
        },
        "source_parsing_meta": parse_meta,
    }


# ==============================================================================
# 5. 独立 FBX 导出与再次导入临时核验（不污染交付 Blend 或 FBX）
# ==============================================================================


def export_and_reimport_verify_fbx(
    asset_obj: bpy.types.Object, out_fbx_path: Path
) -> Dict[str, Any]:
    """仅选中并导出 Shrub_SaltTolerant_A 灌木网格与 6 个材质槽，

    随后在 Blender 5.2.2 中临时重导入该 FBX 核对 1 个网格对象、260 顶点、480 三角面与 6 个材质槽，
    并彻底清理临时导入对象，绝不写入交付 Blend。
    """
    out_fbx_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="DESELECT")
    asset_obj.hide_set(False)
    asset_obj.hide_viewport = False
    asset_obj.select_set(True)
    bpy.context.view_layer.objects.active = asset_obj

    bpy.ops.export_scene.fbx(
        filepath=str(out_fbx_path),
        use_selection=True,
        object_types={"MESH"},
        axis_forward="-Z",
        axis_up="Y",
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=False,
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="AUTO",
    )

    if not out_fbx_path.exists() or out_fbx_path.stat().st_size <= 256:
        raise RuntimeError(f"导出独立资产 FBX 失败或文件大小异常: {out_fbx_path}")

    before_objs = set(bpy.data.objects)
    before_meshes = set(bpy.data.meshes)
    before_mats = set(bpy.data.materials)

    bpy.ops.import_scene.fbx(filepath=str(out_fbx_path))

    imported_objs = [o for o in bpy.data.objects if o not in before_objs]
    imported_mesh_objs = [
        o for o in imported_objs if o.type == "MESH" and o.data is not None
    ]

    if len(imported_mesh_objs) != 1:
        for o in imported_objs:
            bpy.data.objects.remove(o, do_unlink=True)
        raise RuntimeError(
            f"FBX 重导入核验失败：预期只包含 1 个 MESH 对象，实际导入了 {len(imported_mesh_objs)} 个。"
        )

    imp_obj = imported_mesh_objs[0]
    imp_mesh: bpy.types.Mesh = imp_obj.data
    imp_verts = len(imp_mesh.vertices)
    imp_edges = len(imp_mesh.edges)
    imp_polys = len(imp_mesh.polygons)
    imp_tris = len(imp_mesh.loop_triangles)
    imp_mats = len(imp_mesh.materials)
    imp_mat_names = [m.name.split(".")[0] if m else "" for m in imp_mesh.materials]

    reimport_pass = (
        len(imported_mesh_objs) == 1
        and imp_verts == BASELINE_VERTICES
        and imp_tris == BASELINE_TRIANGLES
        and imp_mats == len(EXPECTED_MATERIAL_TRI_COUNTS)
    )

    # 彻底清理临时重导入生成的对象、网格与材质，绝不写进交付 Blend
    for o in imported_objs:
        if o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        if m not in before_meshes:
            bpy.data.meshes.remove(m, do_unlink=True)
    for mat in list(bpy.data.materials):
        if mat not in before_mats:
            bpy.data.materials.remove(mat, do_unlink=True)

    bpy.ops.object.select_all(action="DESELECT")
    asset_obj.select_set(True)
    bpy.context.view_layer.objects.active = asset_obj

    if not reimport_pass:
        raise RuntimeError(
            f"FBX 重导入验证不匹配: mesh_objs={len(imported_mesh_objs)} (预期 1), "
            f"verts={imp_verts} (预期 {BASELINE_VERTICES}), "
            f"tris={imp_tris} (预期 {BASELINE_TRIANGLES}), "
            f"mats={imp_mats} (预期 {len(EXPECTED_MATERIAL_TRI_COUNTS)})"
        )

    return {
        "path": str(out_fbx_path),
        "size_bytes": out_fbx_path.stat().st_size,
        "exported_object": asset_obj.name,
        "axis_forward": "-Z",
        "axis_up": "Y",
        "unit_scale": "METRIC_1_TO_1",
        "reimport_verification": {
            "status": "PASS" if reimport_pass else "FAIL",
            "pass": reimport_pass,
            "imported_mesh_object_count": len(imported_mesh_objs),
            "imported_vertex_count": imp_verts,
            "imported_edge_count": imp_edges,
            "imported_polygon_count": imp_polys,
            "imported_triangle_count": imp_tris,
            "imported_material_slot_count": imp_mats,
            "imported_material_base_names": imp_mat_names,
            "temporary_imported_objects_cleaned": True,
        },
    }


# ==============================================================================
# 6. 四宫格高清预览图生成 (正视 -Y / 侧视 +X / 顶视 +Z / 3/4 斜视 + 线框 & 1m 参照柱)
# ==============================================================================

FONT_5X7: Dict[str, Tuple[str, ...]] = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def build_solid_box_mesh(
    name: str, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float
) -> bpy.types.Mesh:
    """构建长方体辅助网格，用于 Preview_Only 中的 1m 参照柱。"""
    verts = [
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    m = bpy.data.meshes.new(name)
    m.from_pydata(verts, [], faces)
    m.update()
    return m


def build_wire_frame_rods_mesh(
    name: str,
    segments: Sequence[Tuple[Vector, Vector]],
    half_thickness: float,
    mat: bpy.types.Material,
) -> bpy.types.Mesh:
    """将一组 3D 线段构建为细长实体棱柱网格，使所有渲染引擎下线框、标尺、铅垂线与包围盒清晰可见。"""
    verts: List[Tuple[float, float, float]] = []
    faces: List[Tuple[int, int, int, int]] = []
    up_ref = Vector((0.0, 0.0, 1.0))
    side_ref = Vector((1.0, 0.0, 0.0))

    for p0, p1 in segments:
        d = p1 - p0
        length = d.length
        if length <= 1e-6:
            continue
        dn = d / length
        n1 = dn.cross(up_ref)
        if n1.length < 1e-4:
            n1 = dn.cross(side_ref)
        n1.normalize()
        n2 = dn.cross(n1).normalized()
        u = n1 * half_thickness
        v = n2 * half_thickness

        base = len(verts)
        for p in (p0, p1):
            verts.append(tuple(p - u - v))
            verts.append(tuple(p + u - v))
            verts.append(tuple(p + u + v))
            verts.append(tuple(p - u + v))

        faces.extend(
            [
                (base + 0, base + 1, base + 5, base + 4),
                (base + 1, base + 2, base + 6, base + 5),
                (base + 2, base + 3, base + 7, base + 6),
                (base + 3, base + 0, base + 4, base + 7),
            ]
        )

    m = bpy.data.meshes.new(name)
    m.from_pydata(verts, [], faces)
    m.materials.append(mat)
    m.update()
    return m


def create_preview_only_collection(
    asset_obj: bpy.types.Object, qa_result: Dict[str, Any]
) -> Tuple[
    bpy.types.Collection,
    Dict[str, bpy.types.Object],
    bpy.types.Object,
    List[bpy.types.Material],
]:
    """在单独的 Preview_Only 集合中创建：

    1) 1m 标准参照柱（Z=0.0 至 Z=1.0m，带 0m、0.5m、1.0m 刻度与 min_z、max_z 标注线）
    2) 过原点 (0,0,0) 的垂直铅垂参考线与地面 Z=0 十字基准线
    3) 实测 Z-up 包围盒线框 (1.085634 × 0.886196 × 0.641861 m)
    4) 3/4 斜视专用的模型拓扑线框叠加层
    5) 双日光灯组与四宫格相机，留出 ≥22% 充足安全边距确保不裁切枝叶或遮挡树冠/参照柱
    """
    scene = bpy.context.scene
    preview_col = bpy.data.collections.new("Preview_Only")
    scene.collection.children.link(preview_col)

    dims = qa_result["dimensions_and_bounds"]
    b_min = dims["measured_zup_bbox_min_m"]
    b_max = dims["measured_zup_bbox_max_m"]
    min_x, min_y, min_z = float(b_min[0]), float(b_min[1]), float(b_min[2])
    max_x, max_y, max_z = float(b_max[0]), float(b_max[1]), float(b_max[2])
    cx = 0.5 * (min_x + max_x)
    cy = 0.5 * (min_y + max_y)

    created_preview_mats: List[bpy.types.Material] = []

    def make_preview_mat(
        name: str, rgb: Tuple[float, float, float], roughness: float = 0.5
    ) -> bpy.types.Material:
        m = create_exportable_principled_material(name, rgb, roughness=roughness)
        created_preview_mats.append(m)
        return m

    mat_scale_orange = make_preview_mat(
        "_Gate05_Preview_Scale1m_Mat", (1.0, 0.48, 0.08), 0.4
    )
    mat_plumb_cyan = make_preview_mat(
        "_Gate05_Preview_Plumb_Mat", (0.05, 0.92, 1.0), 0.3
    )
    mat_bbox_gold = make_preview_mat(
        "_Gate05_Preview_BBox_Mat", (0.98, 0.84, 0.18), 0.4
    )
    mat_ground_grid = make_preview_mat(
        "_Gate05_Preview_GroundAxis_Mat", (0.55, 0.62, 0.70), 0.6
    )
    mat_floor_fail_red = make_preview_mat(
        "_Gate05_Preview_FloorFail_Mat", (1.0, 0.25, 0.25), 0.4
    )
    mat_wire_overlay = make_preview_mat(
        "_Gate05_Preview_WireOverlay_Mat", (0.06, 0.09, 0.12), 0.4
    )

    # 1. 1m 参照柱 (放置在 X = min_x - 0.24m, Y = cy, Z = 0.0 ~ 1.0m)
    ref_x = min_x - 0.24
    pole_mesh = build_solid_box_mesh(
        "_Gate05_Preview_1m_Pole_Mesh",
        ref_x - 0.024,
        ref_x + 0.024,
        cy - 0.024,
        cy + 0.024,
        0.0,
        1.0,
    )
    pole_mesh.materials.append(mat_scale_orange)
    pole_obj = bpy.data.objects.new("Preview_RefPole_1m", pole_mesh)
    preview_col.objects.link(pole_obj)

    # 右侧高度标尺 (Z = min_z 至 1.0m, 标记 min_z=-0.102m, 0.0m, 0.5m, max_z=0.540m, 1.0m)
    ruler_x = max_x + 0.22
    ruler_segs: List[Tuple[Vector, Vector]] = [
        (Vector((ref_x - 0.07, cy, 0.0)), Vector((ref_x + 0.07, cy, 0.0))),
        (Vector((ref_x - 0.07, cy, 0.5)), Vector((ref_x + 0.07, cy, 0.5))),
        (Vector((ref_x - 0.07, cy, 1.0)), Vector((ref_x + 0.07, cy, 1.0))),
        (Vector((ref_x, cy - 0.07, 1.0)), Vector((ref_x, cy + 0.07, 1.0))),
        (Vector((ruler_x, cy, min_z)), Vector((ruler_x, cy, 1.0))),
    ]
    for h_tick in (min_z, 0.0, 0.5, max_z, 1.0):
        ruler_segs.append(
            (Vector((ruler_x - 0.07, cy, h_tick)), Vector((ruler_x + 0.07, cy, h_tick)))
        )
        ruler_segs.append(
            (Vector((ruler_x, cy - 0.07, h_tick)), Vector((ruler_x, cy + 0.07, h_tick)))
        )

    ruler_mesh = build_wire_frame_rods_mesh(
        "_Gate05_Preview_HeightRuler_Mesh", ruler_segs, 0.0065, mat_scale_orange
    )
    ruler_obj = bpy.data.objects.new("Preview_HeightRuler", ruler_mesh)
    preview_col.objects.link(ruler_obj)

    # 2. 垂直铅垂参考线 (通过原点 (0,0,0)，从 Z = min_z - 0.08m 到 Z = 1.06m)
    plumb_top_z = 1.06
    plumb_segs = [
        (Vector((0.0, 0.0, min_z - 0.08)), Vector((0.0, 0.0, plumb_top_z))),
        (Vector((-0.08, 0.0, plumb_top_z)), Vector((0.08, 0.0, plumb_top_z))),
        (Vector((0.0, -0.08, plumb_top_z)), Vector((0.0, 0.08, plumb_top_z))),
    ]
    plumb_mesh = build_wire_frame_rods_mesh(
        "_Gate05_Preview_PlumbLine_Mesh", plumb_segs, 0.007, mat_plumb_cyan
    )
    plumb_obj = bpy.data.objects.new("Preview_VerticalPlumbLine", plumb_mesh)
    preview_col.objects.link(plumb_obj)

    # 3. 地面 Z=0 十字坐标轴基准线 + Z=min_z (-0.102168m) 底部偏差红线
    ground_segs = [
        (Vector((min_x - 0.36, 0.0, 0.0)), Vector((max_x + 0.34, 0.0, 0.0))),
        (Vector((0.0, min_y - 0.34, 0.0)), Vector((0.0, max_y + 0.34, 0.0))),
    ]
    ground_mesh = build_wire_frame_rods_mesh(
        "_Gate05_Preview_GroundCross_Mesh", ground_segs, 0.006, mat_ground_grid
    )
    ground_obj = bpy.data.objects.new("Preview_GroundCross_Z0", ground_mesh)
    preview_col.objects.link(ground_obj)

    floor_fail_segs = [
        (Vector((min_x - 0.12, cy, min_z)), Vector((max_x + 0.12, cy, min_z))),
        (Vector((cx, min_y - 0.12, min_z)), Vector((cx, max_y + 0.12, min_z))),
    ]
    floor_fail_mesh = build_wire_frame_rods_mesh(
        "_Gate05_Preview_FloorDeviation_Mesh", floor_fail_segs, 0.0055, mat_floor_fail_red
    )
    floor_fail_obj = bpy.data.objects.new(
        "Preview_LowestZ_Minus102mm_Line", floor_fail_mesh
    )
    preview_col.objects.link(floor_fail_obj)

    # 4. 实测 Z-up 包围盒 12 条棱线
    c000 = Vector((min_x, min_y, min_z))
    c100 = Vector((max_x, min_y, min_z))
    c110 = Vector((max_x, max_y, min_z))
    c010 = Vector((min_x, max_y, min_z))
    c001 = Vector((min_x, min_y, max_z))
    c101 = Vector((max_x, min_y, max_z))
    c111 = Vector((max_x, max_y, max_z))
    c011 = Vector((min_x, max_y, max_z))
    bbox_segs = [
        (c000, c100),
        (c100, c110),
        (c110, c010),
        (c010, c000),
        (c001, c101),
        (c101, c111),
        (c111, c011),
        (c011, c001),
        (c000, c001),
        (c100, c101),
        (c110, c111),
        (c010, c011),
    ]
    bbox_mesh = build_wire_frame_rods_mesh(
        "_Gate05_Preview_BBoxWire_Mesh", bbox_segs, 0.006, mat_bbox_gold
    )
    bbox_obj = bpy.data.objects.new("Preview_BoundingBox", bbox_mesh)
    preview_col.objects.link(bbox_obj)

    # 5. 3/4 斜视图专用的模型三角网线框叠加层
    src_mesh: bpy.types.Mesh = asset_obj.data
    edge_segs: List[Tuple[Vector, Vector]] = []
    for e in src_mesh.edges:
        v0 = asset_obj.matrix_world @ src_mesh.vertices[e.vertices[0]].co
        v1 = asset_obj.matrix_world @ src_mesh.vertices[e.vertices[1]].co
        edge_segs.append((v0, v1))
    wire_overlay_mesh = build_wire_frame_rods_mesh(
        "_Gate05_Preview_MeshWireOverlay_Mesh", edge_segs, 0.0030, mat_wire_overlay
    )
    wire_overlay_obj = bpy.data.objects.new(
        "Preview_MeshWireframeOverlay", wire_overlay_mesh
    )
    preview_col.objects.link(wire_overlay_obj)

    # 6. 柔和双日光与世界天光
    sun_key_data = bpy.data.lights.new(name="_Gate05_Preview_SunKey", type="SUN")
    sun_key_data.energy = 3.5
    sun_key_data.color = (1.0, 0.98, 0.93)
    sun_key_obj = bpy.data.objects.new("Preview_SunKey", sun_key_data)
    sun_key_obj.location = (3.0, -3.5, 5.5)
    sun_key_obj.rotation_euler = (
        math.radians(46.0),
        math.radians(16.0),
        math.radians(34.0),
    )
    preview_col.objects.link(sun_key_obj)

    sun_fill_data = bpy.data.lights.new(name="_Gate05_Preview_SunFill", type="SUN")
    sun_fill_data.energy = 1.5
    sun_fill_data.color = (0.84, 0.91, 1.0)
    sun_fill_obj = bpy.data.objects.new("Preview_SunFill", sun_fill_data)
    sun_fill_obj.location = (-3.5, 3.0, 4.5)
    sun_fill_obj.rotation_euler = (
        math.radians(56.0),
        math.radians(-18.0),
        math.radians(-135.0),
    )
    preview_col.objects.link(sun_fill_obj)

    if scene.world is None:
        scene.world = bpy.data.worlds.new("Gate05_World")
    scene.world.color = (0.14, 0.17, 0.21)
    scene.world.use_nodes = True
    if scene.world.node_tree:
        for node in scene.world.node_tree.nodes:
            if node.type == "BACKGROUND":
                if "Color" in node.inputs:
                    node.inputs["Color"].default_value = (0.14, 0.17, 0.21, 1.0)
                if "Strength" in node.inputs:
                    node.inputs["Strength"].default_value = 0.9

    # 7. 四台检视相机：完整包含模型 (Z=-0.102m..0.540m) 与 1m 参照柱 (Z=0..1.0m)，并留出 >22% 顶部/四周安全边距
    # 垂直可视范围涵盖 Z = -0.18m 至 1.08m（总跨度 1.26m），将相机中心设在 Z = 0.44m，
    # 正交宽度 ortho_scale = 2.65m -> 垂直视口高度 = 2.65 * (530/800) = 1.755m，上下各留 >20% 安全边距，绝不遮挡标题或裁切枝叶
    view_center_z = 0.42
    cameras: Dict[str, bpy.types.Object] = {}

    # (a) 正视图 Front (-Y 朝 +Y 看)
    cam_front_data = bpy.data.cameras.new("_Gate05_Cam_Front")
    cam_front_data.type = "ORTHO"
    cam_front_data.ortho_scale = 2.65
    cam_front = bpy.data.objects.new("Preview_Cam_Front_NegY", cam_front_data)
    cam_front.location = (cx - 0.02, -5.0, view_center_z)
    cam_front.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    preview_col.objects.link(cam_front)
    cameras["front"] = cam_front

    # (b) 侧视图 Side (+X 朝 -X 看)
    cam_side_data = bpy.data.cameras.new("_Gate05_Cam_Side")
    cam_side_data.type = "ORTHO"
    cam_side_data.ortho_scale = 2.65
    cam_side = bpy.data.objects.new("Preview_Cam_Side_PosX", cam_side_data)
    cam_side.location = (5.0, cy, view_center_z)
    cam_side.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))
    preview_col.objects.link(cam_side)
    cameras["side"] = cam_side

    # (c) 正交顶视图 Top (+Z 朝 -Z 看)
    cam_top_data = bpy.data.cameras.new("_Gate05_Cam_Top")
    cam_top_data.type = "ORTHO"
    cam_top_data.ortho_scale = 2.40
    cam_top = bpy.data.objects.new("Preview_Cam_Top_PosZ", cam_top_data)
    cam_top.location = (cx - 0.02, cy, 5.0)
    cam_top.rotation_euler = (0.0, 0.0, 0.0)
    preview_col.objects.link(cam_top)
    cameras["top"] = cam_top

    # (d) 3/4 斜视图 Oblique (叠加线框)
    cam_oblique_data = bpy.data.cameras.new("_Gate05_Cam_Oblique")
    cam_oblique_data.type = "PERSP"
    cam_oblique_data.lens = 42.0
    cam_oblique = bpy.data.objects.new("Preview_Cam_Oblique_3Q", cam_oblique_data)
    oblique_pos = Vector((cx + 1.95, cy - 2.15, 1.45))
    oblique_target = Vector((cx - 0.02, cy, 0.36))
    cam_oblique.location = oblique_pos
    cam_oblique.rotation_euler = (
        (oblique_target - oblique_pos)
        .normalized()
        .to_track_quat("-Z", "Y")
        .to_euler("XYZ")
    )
    preview_col.objects.link(cam_oblique)
    cameras["oblique"] = cam_oblique

    scene.camera = cam_oblique
    return preview_col, cameras, wire_overlay_obj, created_preview_mats


def set_text_on_buffer(
    buf: List[float],
    width: int,
    height: int,
    text: str,
    x: int,
    top_y: int,
    rgb: Tuple[float, float, float],
    scale: int = 2,
) -> None:
    """使用纯 Python 标准库在 RGBA 一维像素缓冲 (bottom-left 原点) 上绘制点阵文本。"""
    cursor_x = x
    r, g, b = float(rgb[0]), float(rgb[1]), float(rgb[2])
    for ch in text.upper():
        glyph = FONT_5X7.get(ch, FONT_5X7[" "])
        for row_idx, row_str in enumerate(glyph):
            for col_idx, bit in enumerate(row_str):
                if bit != "1":
                    continue
                for sy in range(scale):
                    py_top = top_y + row_idx * scale + sy
                    py = height - 1 - py_top
                    if py < 0 or py >= height:
                        continue
                    row_offset = py * width * 4
                    for sx in range(scale):
                        px = cursor_x + col_idx * scale + sx
                        if 0 <= px < width:
                            idx = row_offset + px * 4
                            buf[idx] = r
                            buf[idx + 1] = g
                            buf[idx + 2] = b
                            buf[idx + 3] = 1.0
        cursor_x += 6 * scale


def fill_rect_on_buffer(
    buf: List[float],
    width: int,
    height: int,
    x0: int,
    top_y0: int,
    w: int,
    h: int,
    rgba: Tuple[float, float, float, float],
) -> None:
    """在 RGBA 像素缓冲上填充矩形背景框或分隔线。"""
    r, g, b, a = rgba
    for ty in range(top_y0, top_y0 + h):
        py = height - 1 - ty
        if py < 0 or py >= height:
            continue
        row_base = py * width * 4
        for px in range(max(0, x0), min(width, x0 + w)):
            idx = row_base + px * 4
            buf[idx] = r
            buf[idx + 1] = g
            buf[idx + 2] = b
            buf[idx + 3] = a


def render_quad_preview_sheet(
    cameras: Dict[str, bpy.types.Object],
    wire_overlay_obj: bpy.types.Object,
    qa_result: Dict[str, Any],
    out_png_path: Path,
) -> Dict[str, Any]:
    """渲染四宫格视图并拼接为 1600x1200 的单张 PNG 检视图，动态渲染 QA 状态与 -0.102168m 落地 FAIL。"""
    out_png_path.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene

    panel_w, panel_h = 800, 530
    total_w, total_h = 1600, 1200

    available_engines = [
        item.identifier
        for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    ]
    preferred_engines = [
        e
        for e in (
            "BLENDER_EEVEE_NEXT",
            "BLENDER_EEVEE",
            "CYCLES",
            "BLENDER_WORKBENCH",
        )
        if e in available_engines
    ]
    if not preferred_engines:
        preferred_engines = available_engines

    scene.render.resolution_x = panel_w
    scene.render.resolution_y = panel_h
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"

    # dst_y 为 bottom-left 原点下的像素行起点：
    # 底部页脚高 80px (0..79)，下排面板占 80..609，上排面板占 610..1139，顶部标题栏占 1140..1199
    panel_specs = [
        ("front", False, 0, 610),
        ("side", False, 800, 610),
        ("top", False, 0, 80),
        ("oblique", True, 800, 80),
    ]

    canvas_buf: List[float] = [0.09, 0.11, 0.14, 1.0] * (total_w * total_h)
    used_engine = preferred_engines[0]

    for key, show_wire, dst_x, dst_y in panel_specs:
        wire_overlay_obj.hide_render = not show_wire
        wire_overlay_obj.hide_viewport = not show_wire
        scene.camera = cameras[key]

        temp_file = out_png_path.parent / f"_temp_gate05_{key}.png"
        scene.render.filepath = str(temp_file)

        rendered_ok = False
        last_err: Optional[Exception] = None
        for eng in preferred_engines:
            try:
                scene.render.engine = eng
                if eng == "CYCLES" and hasattr(scene, "cycles"):
                    scene.cycles.device = "CPU"
                    scene.cycles.samples = 20
                    if hasattr(scene.cycles, "use_denoising"):
                        scene.cycles.use_denoising = False
                bpy.ops.render.render(write_still=True)
                if temp_file.exists() and temp_file.stat().st_size > 512:
                    used_engine = eng
                    rendered_ok = True
                    break
            except Exception as exc:
                last_err = exc
                continue

        if not rendered_ok:
            raise RuntimeError(f"渲染面板 {key} 失败: {last_err}")

        img = bpy.data.images.load(str(temp_file), check_existing=False)
        panel_pixels = list(img.pixels)
        bpy.data.images.remove(img)
        try:
            temp_file.unlink()
        except OSError:
            pass

        for py in range(panel_h):
            src_row_start = py * panel_w * 4
            dst_row_start = ((dst_y + py) * total_w + dst_x) * 4
            canvas_buf[dst_row_start : dst_row_start + panel_w * 4] = panel_pixels[
                src_row_start : src_row_start + panel_w * 4
            ]

    wire_overlay_obj.hide_render = False
    wire_overlay_obj.hide_viewport = False
    scene.camera = cameras["oblique"]

    # 顶部标题栏 (top_y: 0..59) 与底部动态 QA 状态栏 (top_y: 1120..1199)
    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 0, 0, total_w, 60, (0.05, 0.07, 0.10, 1.0)
    )
    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 0, 1120, total_w, 80, (0.05, 0.07, 0.10, 1.0)
    )
    # 十字分割线
    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 798, 60, 4, 1060, (0.28, 0.34, 0.42, 1.0)
    )
    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 0, 588, total_w, 4, (0.28, 0.34, 0.42, 1.0)
    )

    dims = qa_result["dimensions_and_bounds"]["measured_zup_dimensions_m"]
    g_cnt = qa_result["geometry_counts"]
    floor_qa = qa_result["origin_and_floor_alignment_qa"]
    checks = qa_result["checks_summary"]
    overall_status = qa_result["overall_status"]

    header_color = (0.96, 0.98, 1.0) if qa_result["overall_pass"] else (1.0, 0.78, 0.32)
    set_text_on_buffer(
        canvas_buf,
        total_w,
        total_h,
        f"GATE 05 AS-IS INSPECTION : {ASSET_ID} | OVERALL QA: {overall_status}",
        24,
        18,
        header_color,
        scale=3,
    )

    # 四个象限标题（放置在面板顶部边缘，配合相机 >22% 边距绝不遮挡树冠）
    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 12, 66, 620, 28, (0.06, 0.09, 0.13, 0.88)
    )
    set_text_on_buffer(
        canvas_buf,
        total_w,
        total_h,
        f"1. FRONT VIEW (-Y) | X={dims[0]:.4f}M Z={dims[2]:.4f}M & 1M POLE",
        20,
        73,
        (1.0, 0.86, 0.36),
        scale=2,
    )

    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 812, 66, 620, 28, (0.06, 0.09, 0.13, 0.88)
    )
    set_text_on_buffer(
        canvas_buf,
        total_w,
        total_h,
        f"2. SIDE VIEW (+X) | Y={dims[1]:.4f}M Z={dims[2]:.4f}M & BBOX",
        820,
        73,
        (1.0, 0.86, 0.36),
        scale=2,
    )

    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 12, 596, 620, 28, (0.06, 0.09, 0.13, 0.88)
    )
    set_text_on_buffer(
        canvas_buf,
        total_w,
        total_h,
        f"3. TOP VIEW (+Z) | X={dims[0]:.4f}M Y={dims[1]:.4f}M",
        20,
        603,
        (0.45, 0.95, 1.0),
        scale=2,
    )

    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 812, 596, 660, 28, (0.06, 0.09, 0.13, 0.88)
    )
    set_text_on_buffer(
        canvas_buf,
        total_w,
        total_h,
        f"4. 3/4 OBLIQUE + WIRE ({g_cnt['vertex_count']} VERTS / {g_cnt['triangle_count']} TRIS)",
        820,
        603,
        (0.55, 0.98, 0.68),
        scale=2,
    )

    # 动态生成的底部实测 QA 摘要栏（明确显示 260 verts / 480 tris / 实测尺寸 / floor alignment FAIL (-0.102168m)）
    footer_line_1 = (
        f"MEASURED Z-UP DIMS: X={dims[0]:.6f}M Y={dims[1]:.6f}M Z={dims[2]:.6f}M "
        f"[{checks['dimensions_and_bbox_zup_check']}] | "
        f"{g_cnt['vertex_count']} VERTS [{checks['vertex_count_check']}] / "
        f"{g_cnt['triangle_count']} TRIS [{checks['triangle_count_check']}] / "
        f"{g_cnt['edge_count']} EDGES"
    )
    footer_line_2 = (
        f"FLOOR ALIGNMENT: {floor_qa['status']} "
        f"({floor_qa['converted_lowest_z_m']:+.6f}M / {floor_qa['floor_deviation_mm']:+.3f}MM BELOW Z=0, "
        f"TOL=+-{floor_qa['floor_tolerance_m']:.3f}M) | "
        f"MATS=6 [{checks['materials_6_slots_distribution_check']}] | OVERALL: {overall_status}"
    )

    line2_color = (0.55, 0.98, 0.68) if floor_qa["pass"] else (1.0, 0.42, 0.42)
    set_text_on_buffer(
        canvas_buf, total_w, total_h, footer_line_1, 20, 1132, (0.92, 0.96, 1.0), scale=2
    )
    set_text_on_buffer(
        canvas_buf, total_w, total_h, footer_line_2, 20, 1162, line2_color, scale=2
    )

    out_img = bpy.data.images.new(
        name="_Gate05_QuadSheet", width=total_w, height=total_h, alpha=True
    )
    out_img.pixels.foreach_set(canvas_buf)
    out_img.filepath_raw = str(out_png_path)
    out_img.file_format = "PNG"
    out_img.save()
    bpy.data.images.remove(out_img)

    if not out_png_path.exists() or out_png_path.stat().st_size <= 1024:
        raise RuntimeError(f"保存四宫格预览图失败: {out_png_path}")

    return {
        "path": str(out_png_path),
        "size_bytes": out_png_path.stat().st_size,
        "resolution": [total_w, total_h],
        "render_engine_used": used_engine,
    }


# ==============================================================================
# 7. 可编辑 Blend 保存（仅含独立灌木模型与隐藏的 Preview_Only 集合，打开直接可见）
# ==============================================================================


def save_clean_asset_blend(
    asset_obj: bpy.types.Object,
    preview_col: bpy.types.Collection,
    out_blend_path: Path,
) -> Dict[str, Any]:
    """保存 Assets_Inspected/Shrub_SaltTolerant_A.blend，使打开文件时直接看到独立灌木模型。"""
    out_blend_path.parent.mkdir(parents=True, exist_ok=True)

    preview_col.hide_viewport = True
    preview_col.hide_render = True

    asset_obj.hide_set(False)
    asset_obj.hide_viewport = False
    asset_obj.hide_render = False
    bpy.ops.object.select_all(action="DESELECT")
    asset_obj.select_set(True)
    bpy.context.view_layer.objects.active = asset_obj

    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend_path), compress=True)
    if not out_blend_path.exists() or out_blend_path.stat().st_size <= 512:
        raise RuntimeError(f"保存独立资产 Blend 失败: {out_blend_path}")

    return {
        "path": str(out_blend_path),
        "size_bytes": out_blend_path.stat().st_size,
        "primary_visible_object": asset_obj.name,
        "collections_in_blend": [c.name for c in bpy.data.collections],
    }


# ==============================================================================
# 8. 主流程执行、交付物验证与报告打印
# ==============================================================================


def main() -> None:
    # 1. 验证只读输入存在性并读取 SHA-256 与 manifest
    inputs_info = verify_inputs_and_load_manifest()

    # 只通过 mkdir 创建输出目录，绝不清空或删除任何目录
    OUT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 2. 重置为洁净的 factory-startup 空场景并设置 1:1 公制单位
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    # 3. 创建主资产集合并原样解析构建 Shrub_SaltTolerant_A
    asset_col = bpy.data.collections.new("Asset_Inspected")
    scene.collection.children.link(asset_col)

    asset_obj, parse_meta = parse_obj_and_build_as_is_asset(
        SOURCE_OBJ_PATH, SOURCE_MTL_PATH
    )
    asset_col.objects.link(asset_obj)

    # 4. 执行完整 QA 测量（含尺寸、260顶点/480三角面/720边、6个材质 Kd 与分布、拓扑诊断及 floor alignment FAIL）
    qa_result = inspect_and_verify_asset(
        asset_obj, parse_meta, inputs_info["manifest"]["matched_entry"]
    )

    # 5. 先导出仅含该灌木网格与六个材质槽的独立 FBX，并在 Blender 中重导入临时验证后清理临时对象
    fbx_info = export_and_reimport_verify_fbx(asset_obj, OUT_FBX_PATH)
    qa_result["checks_summary"]["fbx_reimport_verification_check"] = (
        fbx_info["reimport_verification"]["status"]
    )

    # 6. 构建 Preview_Only 集合并渲染 1600x1200 四宫格预览图
    preview_col, cameras, wire_overlay_obj, _preview_mats = (
        create_preview_only_collection(asset_obj, qa_result)
    )
    preview_info = render_quad_preview_sheet(
        cameras=cameras,
        wire_overlay_obj=wire_overlay_obj,
        qa_result=qa_result,
        out_png_path=OUT_PREVIEW_PNG_PATH,
    )

    # 7. 保存可单独检视该灌木模型的 Blend 文件（只含灌木与隐藏的 Preview_Only 辅助集合）
    blend_info = save_clean_asset_blend(asset_obj, preview_col, OUT_BLEND_PATH)

    # 8. 写入完整的 Reports/Gate05_qa.json
    full_report: Dict[str, Any] = {
        "gate": "Gate 05 - Single Nature Asset As-Is Inspection",
        "asset_id": ASSET_ID,
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "blender_version": bpy.app.version_string,
        "blender_version_tuple": list(bpy.app.version),
        "strict_as_is_compliance": {
            "source_files_modified": False,
            "geometry_reshaped_or_bent": False,
            "vertex_translated_or_floor_snapped": False,
            "origin_preserved_from_obj": True,
            "triangles_added_or_removed": False,
            "vertices_welded": False,
            "candidate_generated": False,
            "flat_shading_applied_for_low_poly_edges": True,
            "coordinate_conversion": "X_bl = X_obj, Y_bl = -Z_obj, Z_bl = Y_obj (Right-handed Y-up to Z-up, 1:1 metric)",
        },
        "inputs": inputs_info,
        "qa_verification": qa_result,
        "deliverables": {
            "asset_blend": blend_info,
            "asset_fbx": fbx_info,
            "preview_png": preview_info,
            "qa_report_json": {
                "path": str(OUT_REPORT_JSON_PATH),
            },
        },
    }

    OUT_REPORT_JSON_PATH.write_text(
        json.dumps(full_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    full_report["deliverables"]["qa_report_json"][
        "size_bytes"
    ] = OUT_REPORT_JSON_PATH.stat().st_size
    OUT_REPORT_JSON_PATH.write_text(
        json.dumps(full_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 9. 重新检查所有 Gate 05 交付物存在且非零
    deliverables_to_check = [
        OUT_BLEND_PATH,
        OUT_FBX_PATH,
        OUT_PREVIEW_PNG_PATH,
        OUT_REPORT_JSON_PATH,
    ]
    for p in deliverables_to_check:
        if not p.exists() or p.stat().st_size <= 0:
            raise RuntimeError(f"Gate 05 交付物缺失或文件大小为 0: {p}")

    # 10. 打印尺寸、顶点/边/三角面、材质分配、各项 PASS/FAIL 与交付绝对路径
    dims_info = qa_result["dimensions_and_bounds"]
    dims_m = dims_info["measured_zup_dimensions_m"]
    g_cnt = qa_result["geometry_counts"]
    floor_qa = qa_result["origin_and_floor_alignment_qa"]
    topo_diag = qa_result["topology_diagnostics"]
    checks = qa_result["checks_summary"]

    print("=" * 86)
    print(f"Gate 05 原样独立资产检视报告 : {ASSET_ID}")
    print("=" * 86)
    print(f"Blender 版本                 : {bpy.app.version_string}")
    print(
        f"源 Y-up 包围盒 (m)           : min={dims_info['source_yup_bbox_min_m']}, "
        f"max={dims_info['source_yup_bbox_max_m']}, dims={dims_info['source_yup_dimensions_m']}"
    )
    print(
        f"实测 Z-up 包围盒 (m)         : min={dims_info['measured_zup_bbox_min_m']}, "
        f"max={dims_info['measured_zup_bbox_max_m']}"
    )
    print(
        f"实测 Z-up 尺寸 (m)           : X={dims_m[0]:.6f}, Y={dims_m[1]:.6f}, Z={dims_m[2]:.6f} "
        f"(预期: {BASELINE_ZUP_DIMS})"
    )
    print(
        f"Manifest 与源几何差异        : Manifest 标注 origin='{MANIFEST_ORIGIN_LABEL}', 尺寸={MANIFEST_ROUNDED_YUP_DIMS}m; "
        f"实测源最低 Y={floor_qa['source_lowest_y_m']:+.6f}m"
    )
    print(
        f"底点高度与落地偏差           : 原点={floor_qa['object_origin_world_xyz_m']}, "
        f"转换后最低点 Z={floor_qa['converted_lowest_z_m']:+.6f}m "
        f"({floor_qa['floor_deviation_mm']:+.3f}mm, 容差=±{floor_qa['floor_tolerance_m']:.3f}m)"
    )
    print(
        f"网格统计                     : 顶点={g_cnt['vertex_count']} (基线 {BASELINE_VERTICES}), "
        f"唯一边={g_cnt['edge_count']} (基线 {BASELINE_EDGES}), 多边形={g_cnt['polygon_count']}, "
        f"三角面={g_cnt['triangle_count']} (基线 {BASELINE_TRIANGLES})"
    )
    print(
        f"拓扑诊断                     : 退化面={topo_diag['degenerate_triangle_count']}, "
        f"零面积面={topo_diag['zero_area_triangle_count']}, 重复面={topo_diag['duplicate_face_count']}, "
        f"孤立点={topo_diag['loose_vertex_count']}, 开放边={topo_diag['open_boundary_edge_count']}, "
        f"非边界非流形边={topo_diag['non_boundary_non_manifold_edge_count']}"
    )
    print("材质槽与三角面分配 (6 slots, 总计 480):")
    for m_slot in qa_result["materials_statistics"]["slots"]:
        print(
            f"  - {m_slot['material_name']:<14} : {m_slot['triangle_count']:>3} tris "
            f"(预期 {m_slot['expected_triangle_count']:>3}, diff={m_slot['triangle_count_diff']:+d}) | "
            f"Kd={m_slot['mtl_kd_rgb']} (match={m_slot['kd_matches_expected']})"
        )
    print("-" * 86)
    print("各项 QA 检查结果:")
    for chk_name, chk_status in checks.items():
        print(f"  * {chk_name:<42} : {chk_status}")
    print(f"  => Gate 05 综合状态 (OVERALL QA)             : {qa_result['overall_status']}")
    if qa_result["failure_reasons"]:
        print("失败原因明细:")
        for reason in qa_result["failure_reasons"]:
            print(f"  [FAIL] {reason}")
    print("-" * 86)
    print("Gate 05 交付物绝对路径与文件大小:")
    for p in deliverables_to_check:
        print(f"  -> {p.resolve()} ({p.stat().st_size} bytes)")
    print("=" * 86)


if __name__ == "__main__":
    main()
