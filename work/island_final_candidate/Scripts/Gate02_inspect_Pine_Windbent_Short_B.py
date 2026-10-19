# -*- coding: utf-8 -*-
"""Gate 02: Pine_Windbent_Short_B 单资产原样检视脚本 (Blender 5.2.2)

保存位置: D:/Last Landfall/work/island_final_candidate/Scripts/Gate02_inspect_Pine_Windbent_Short_B.py
执行方式: blender -b --factory-startup -P "D:/Last Landfall/work/island_final_candidate/Scripts/Gate02_inspect_Pine_Windbent_Short_B.py"
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
# 1. 基线常量与路径推导（严格只读输入，只写 Gate02 指定产物）
# ==============================================================================

ASSET_ID: str = "Pine_Windbent_Short_B"
BASELINE_VERTICES: int = 124
BASELINE_TRIANGLES: int = 188
BASELINE_YUP_DIMS: Tuple[float, float, float] = (1.932707, 2.860137, 2.070723)
BASELINE_ZUP_DIMS: Tuple[float, float, float] = (1.932707, 2.070723, 2.860137)
EXPECTED_MIN_Z: float = -0.004137
DIM_TOLERANCE_M: float = 0.002
FLOOR_TOLERANCE_M: float = 0.002

EXPECTED_MATERIAL_NAMES: Tuple[str, ...] = (
    "bark",
    "bark_sun",
    "leaf",
    "leaf_deep",
    "leaf_salt",
    "leaf_shadow",
    "leaf_sun",
)


def resolve_project_root() -> Path:
    """从脚本自身路径向上稳定推导项目根目录 D:\\Last Landfall。"""
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
        "无法从脚本自身位置推导项目根目录，请确认脚本位于 D:\\Last Landfall\\work\\island_final_candidate\\Scripts\\ 下。"
    )


PROJECT_ROOT: Path = resolve_project_root()

NATURE_DIR: Path = (
    PROJECT_ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Nature"
)
SOURCE_OBJ_PATH: Path = NATURE_DIR / f"{ASSET_ID}.obj"
SOURCE_MTL_PATH: Path = NATURE_DIR / f"{ASSET_ID}.mtl"
MANIFEST_PATH: Path = NATURE_DIR / "asset_manifest.json"

OUTPUT_ROOT: Path = PROJECT_ROOT / "work" / "island_final_candidate"
OUT_SCRIPTS_DIR: Path = OUTPUT_ROOT / "Scripts"
OUT_ASSETS_DIR: Path = OUTPUT_ROOT / "Assets_Inspected"
OUT_PREVIEWS_DIR: Path = OUTPUT_ROOT / "Previews"
OUT_REPORTS_DIR: Path = OUTPUT_ROOT / "Reports"

OUT_SCRIPT_PATH: Path = OUT_SCRIPTS_DIR / f"Gate02_inspect_{ASSET_ID}.py"
OUT_BLEND_PATH: Path = OUT_ASSETS_DIR / f"{ASSET_ID}.blend"
OUT_FBX_PATH: Path = OUT_ASSETS_DIR / f"{ASSET_ID}.fbx"
OUT_PREVIEW_PNG_PATH: Path = OUT_PREVIEWS_DIR / f"Gate02_{ASSET_ID}.png"
OUT_REPORT_JSON_PATH: Path = OUT_REPORTS_DIR / "Gate02_qa.json"


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
    """验证源 OBJ、MTL、asset_manifest.json 均存在且非空，并提取该资产的 manifest 记录。"""
    required_inputs: List[Tuple[str, Path]] = [
        ("自然资产源 OBJ", SOURCE_OBJ_PATH),
        ("自然资产源 MTL", SOURCE_MTL_PATH),
        ("自然资产清单 asset_manifest.json", MANIFEST_PATH),
    ]
    for label, path in required_inputs:
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Gate 02 前置校验失败：缺少{label}，具体路径: {path}")
        if path.stat().st_size == 0:
            raise RuntimeError(f"Gate 02 前置校验失败：{label} 文件大小为 0，具体路径: {path}")

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
    """使用标准库解析 MTL 文件中的 newmtl 与 Kd 漫反射 RGB。"""
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
    mat_name: str, rgb: Tuple[float, float, float], roughness: float = 0.85
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
    """原样解析 OBJ 与 MTL，严格执行右手坐标变换 X_bl=X_obj, Y_bl=-Z_obj, Z_bl=Y_obj。

    严禁任何自动贴地平移、重心重置、弯曲或网格修改，100% 保留源坐标与原始拓扑。
    """
    kd_map = parse_mtl_kd(mtl_path)

    verts_yup: List[Tuple[float, float, float]] = []
    verts_zup: List[Tuple[float, float, float]] = []
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
                # 严格右手系转换: X_bl = X_obj, Y_bl = -Z_obj, Z_bl = Y_obj，不做任何偏移
                verts_zup.append((x_obj, -z_obj, y_obj))
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
                        raise ValueError(f"OBJ 顶点索引越界: {token} (当前顶点数={n_v})")
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

    # 计算原始 Y-up 与转换后 Z-up 的包围盒（严禁做任何顶点平移）
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

    # 创建 Blender Mesh 与 Object（保留 OBJ 原点 (0,0,0)）
    mesh = bpy.data.meshes.new(ASSET_ID)
    mesh.from_pydata(verts_zup, [], faces_indices)

    # 按 MTL 定义顺序与 usemtl 建立材质槽（保留全部 7 个材质名与 Kd）
    slot_names: List[str] = []
    for m_name in kd_map.keys():
        if m_name not in slot_names:
            slot_names.append(m_name)
    for m_name in faces_mat_names:
        if m_name not in slot_names:
            slot_names.append(m_name)

    mat_to_slot: Dict[str, int] = {}
    for idx, m_name in enumerate(slot_names):
        rgb = kd_map.get(m_name, (0.5, 0.5, 0.5))
        bl_mat = create_exportable_principled_material(m_name, rgb, roughness=0.85)
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
    obj["gate02_managed"] = True

    parse_meta = {
        "mtllib_declarations": mtllib_declarations,
        "raw_face_records_in_obj": raw_face_record_count,
        "non_triangle_face_records_in_obj": non_triangle_face_records,
        "fan_triangulated_extra_triangles": fan_triangulated_extra_tris,
        "triangulation_note": (
            "All OBJ faces are already triangles (0 non-triangle faces)."
            if non_triangle_face_records == 0
            else f"OBJ contained {non_triangle_face_records} polygon faces which were fan-triangulated without data loss."
        ),
        "source_yup_bbox_min_m": [round(v, 6) for v in yup_min],
        "source_yup_bbox_max_m": [round(v, 6) for v in yup_max],
        "source_yup_dimensions_m": [round(v, 6) for v in yup_dims],
        "source_lowest_y_m": round(yup_min[1], 6),
        "parsed_mtl_materials": {
            k: [round(c, 6) for c in v] for k, v in kd_map.items()
        },
    }
    return obj, parse_meta


# ==============================================================================
# 4. 严格几何/拓扑核验与落地偏差如实报告（先完成测量，写完报告与预览后再决定退出码）
# ==============================================================================


def inspect_and_verify_asset(
    asset_obj: bpy.types.Object, parse_meta: Dict[str, Any]
) -> Dict[str, Any]:
    """实测顶点/边/三角面数、Z-up 尺寸、底面 Z 落地偏差、7 个材质槽及风弯特征只读测量。"""
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

    # 材质槽面数统计并核对 7 个预期材质名
    slot_face_counts: Dict[int, int] = {i: 0 for i in range(len(mesh.materials))}
    for poly in mesh.polygons:
        slot_face_counts[int(poly.material_index)] = (
            slot_face_counts.get(int(poly.material_index), 0) + 1
        )

    materials_report: List[Dict[str, Any]] = []
    trunk_slot_indices: List[int] = []
    foliage_slot_indices: List[int] = []
    actual_mat_names: List[str] = []

    for idx, mat in enumerate(mesh.materials):
        m_name = mat.name if mat else f"Slot_{idx}"
        actual_mat_names.append(m_name)
        rgb = list(mat.diffuse_color[:3]) if mat else [0.5, 0.5, 0.5]
        # 同时读取 Principled BSDF Base Color
        bsdf_rgb = rgb
        if mat and mat.use_nodes and mat.node_tree:
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED" and "Base Color" in node.inputs:
                    val = node.inputs["Base Color"].default_value
                    bsdf_rgb = [float(val[0]), float(val[1]), float(val[2])]
                    break

        f_cnt = slot_face_counts.get(idx, 0)
        materials_report.append(
            {
                "slot_index": idx,
                "material_name": m_name,
                "mtl_kd_rgb": parse_meta["parsed_mtl_materials"].get(m_name, []),
                "principled_base_color_rgb": [round(float(c), 6) for c in bsdf_rgb],
                "triangle_count": f_cnt,
                "triangle_ratio_pct": round(f_cnt * 100.0 / max(1, tri_count), 2),
            }
        )
        lower_name = m_name.lower()
        if "bark" in lower_name or "trunk" in lower_name or "wood" in lower_name:
            trunk_slot_indices.append(idx)
        else:
            foliage_slot_indices.append(idx)

    materials_match_expected = set(actual_mat_names) == set(EXPECTED_MATERIAL_NAMES)

    # 只读 bmesh 拓扑统计（叶片表面允许开放边，不误报为失败）
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

    # ------------------------------------------------------------------
    # 风弯特征客观测量（仅记录树干截面中心偏移与树冠质心，供人工判断，不做自动造型好坏评价）
    # ------------------------------------------------------------------
    trunk_vert_indices = set()
    foliage_vert_indices = set()
    for poly in mesh.polygons:
        if poly.material_index in trunk_slot_indices:
            trunk_vert_indices.update(poly.vertices)
        if poly.material_index in foliage_slot_indices:
            foliage_vert_indices.update(poly.vertices)

    if not trunk_vert_indices:
        trunk_vert_indices = set(range(len(verts_world)))
    if not foliage_vert_indices:
        foliage_vert_indices = set(range(len(verts_world)))

    trunk_verts = [verts_world[i] for i in sorted(trunk_vert_indices)]
    trunk_min_z = min(v.z for v in trunk_verts)
    trunk_max_z = max(v.z for v in trunk_verts)
    trunk_span_z = max(1e-4, trunk_max_z - trunk_min_z)

    slice_fractions = [
        (0.00, 0.15, "base_0_15pct"),
        (0.15, 0.35, "lower_15_35pct"),
        (0.35, 0.60, "mid_35_60pct"),
        (0.60, 0.85, "upper_60_85pct"),
        (0.85, 1.00, "top_85_100pct"),
    ]
    trunk_sections: List[Dict[str, Any]] = []
    base_center_xy: Optional[Tuple[float, float]] = None

    for f_lo, f_hi, label in slice_fractions:
        z_lo = trunk_min_z + f_lo * trunk_span_z - 1e-5
        z_hi = trunk_min_z + f_hi * trunk_span_z + 1e-5
        pts = [v for v in trunk_verts if z_lo <= v.z <= z_hi]
        if not pts:
            continue
        cx = sum(p.x for p in pts) / len(pts)
        cy = sum(p.y for p in pts) / len(pts)
        cz = sum(p.z for p in pts) / len(pts)
        if base_center_xy is None:
            base_center_xy = (cx, cy)
        dx_base = cx - base_center_xy[0]
        dy_base = cy - base_center_xy[1]
        trunk_sections.append(
            {
                "section": label,
                "z_range_m": [round(z_lo, 4), round(z_hi, 4)],
                "vertex_count": len(pts),
                "mean_center_xyz_m": [round(cx, 6), round(cy, 6), round(cz, 6)],
                "xy_offset_from_origin_m": [round(cx, 6), round(cy, 6)],
                "radial_offset_from_origin_m": round(math.hypot(cx, cy), 6),
                "xy_offset_from_trunk_base_m": [round(dx_base, 6), round(dy_base, 6)],
                "radial_offset_from_trunk_base_m": round(math.hypot(dx_base, dy_base), 6),
            }
        )

    max_trunk_radial_drift = (
        max(s["radial_offset_from_trunk_base_m"] for s in trunk_sections)
        if trunk_sections
        else 0.0
    )

    foliage_area_sum = 0.0
    foliage_weighted_centroid = Vector((0.0, 0.0, 0.0))
    for f in bm.faces:
        if f.material_index in foliage_slot_indices:
            area = f.calc_area()
            c_world = mat_world @ f.calc_center_median()
            foliage_area_sum += area
            foliage_weighted_centroid += c_world * area

    if foliage_area_sum > 1e-8:
        crown_centroid = foliage_weighted_centroid / foliage_area_sum
    else:
        f_pts = [verts_world[i] for i in sorted(foliage_vert_indices)]
        crown_centroid = (
            sum(f_pts, Vector((0.0, 0.0, 0.0))) / max(1, len(f_pts))
        )

    foliage_pts = [verts_world[i] for i in sorted(foliage_vert_indices)]
    crown_bbox_center_xy = (
        0.5 * (min(p.x for p in foliage_pts) + max(p.x for p in foliage_pts)),
        0.5 * (min(p.y for p in foliage_pts) + max(p.y for p in foliage_pts)),
    )

    bm.free()

    # ------------------------------------------------------------------
    # 逐项 QA 判定（如实记录 floor-alignment QA FAIL，绝不掩盖）
    # ------------------------------------------------------------------
    dim_errors = (
        abs(measured_dims[0] - BASELINE_ZUP_DIMS[0]),
        abs(measured_dims[1] - BASELINE_ZUP_DIMS[1]),
        abs(measured_dims[2] - BASELINE_ZUP_DIMS[2]),
    )
    dims_pass = all(err <= DIM_TOLERANCE_M for err in dim_errors)
    tris_pass = tri_count == BASELINE_TRIANGLES
    verts_pass = vert_count == BASELINE_VERTICES

    lowest_z_m = bbox_min[2]
    floor_deviation_m = lowest_z_m - 0.0
    floor_alignment_pass = abs(floor_deviation_m) <= FLOOR_TOLERANCE_M

    origin_preserved_pass = (
        asset_obj.location.length <= 1e-6
        and tuple(round(s, 5) for s in asset_obj.scale) == (1.0, 1.0, 1.0)
        and tuple(round(r, 5) for r in asset_obj.rotation_euler) == (0.0, 0.0, 0.0)
    )
    mesh_clean_pass = (
        degenerate_faces == 0 and zero_area_faces == 0 and loose_verts == 0
    )

    checks_summary: Dict[str, str] = {
        "vertex_count_check": "PASS" if verts_pass else "FAIL",
        "triangle_count_check": "PASS" if tris_pass else "FAIL",
        "dimensions_zup_check": "PASS" if dims_pass else "FAIL",
        "floor_alignment_check": "PASS" if floor_alignment_pass else "FAIL",
        "origin_and_transform_preserved_check": "PASS" if origin_preserved_pass else "FAIL",
        "mesh_integrity_check": "PASS" if mesh_clean_pass else "FAIL",
        "materials_7_slots_check": "PASS" if materials_match_expected else "FAIL",
    }

    failure_reasons: List[str] = []
    if not verts_pass:
        failure_reasons.append(
            f"vertex_count_check FAIL: 实测顶点数={vert_count}, 基线={BASELINE_VERTICES} (差值={vert_count - BASELINE_VERTICES:+d})"
        )
    if not tris_pass:
        failure_reasons.append(
            f"triangle_count_check FAIL: 实测三角面数={tri_count}, 基线={BASELINE_TRIANGLES} (差值={tri_count - BASELINE_TRIANGLES:+d})"
        )
    if not dims_pass:
        failure_reasons.append(
            f"dimensions_zup_check FAIL: 实测 Z-up 尺寸={tuple(round(d, 6) for d in measured_dims)}m, "
            f"基线={BASELINE_ZUP_DIMS}m, 逐轴误差={tuple(round(e, 6) for e in dim_errors)}m (容差 ±{DIM_TOLERANCE_M}m)"
        )
    if not floor_alignment_pass:
        failure_reasons.append(
            f"floor_alignment_check FAIL: 源模型最低点 Z={lowest_z_m:.6f}m (源 OBJ 最低 Y={parse_meta['source_lowest_y_m']:.6f}m), "
            f"相对 Z=0.0m 落地偏差={floor_deviation_m:+.6f}m, 超出容差阈值 ±{FLOOR_TOLERANCE_M:.3f}m"
        )
    if not origin_preserved_pass:
        failure_reasons.append(
            f"origin_and_transform_preserved_check FAIL: location={tuple(asset_obj.location)}, scale={tuple(asset_obj.scale)}"
        )
    if not mesh_clean_pass:
        failure_reasons.append(
            f"mesh_integrity_check FAIL: degenerate_faces={degenerate_faces}, zero_area_faces={zero_area_faces}, loose_verts={loose_verts}"
        )
    if not materials_match_expected:
        failure_reasons.append(
            f"materials_7_slots_check FAIL: 实测材质列表={actual_mat_names}, 预期={list(EXPECTED_MATERIAL_NAMES)}"
        )

    overall_pass = len(failure_reasons) == 0

    return {
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
            "polygon_count": poly_count,
            "triangle_count": tri_count,
            "baseline_triangle_count": BASELINE_TRIANGLES,
            "triangle_count_diff": tri_count - BASELINE_TRIANGLES,
            "triangle_count_pass": tris_pass,
        },
        "dimensions_and_bounds_zup": {
            "baseline_yup_dimensions_m": [round(v, 6) for v in BASELINE_YUP_DIMS],
            "target_zup_dimensions_m": [round(v, 6) for v in BASELINE_ZUP_DIMS],
            "measured_zup_dimensions_m": [round(d, 6) for d in measured_dims],
            "axis_errors_m": [round(e, 6) for e in dim_errors],
            "tolerance_m": DIM_TOLERANCE_M,
            "dimensions_pass": dims_pass,
            "bbox_min_m": [round(v, 6) for v in bbox_min],
            "bbox_max_m": [round(v, 6) for v in bbox_max],
        },
        "floor_alignment_qa": {
            "status": "PASS" if floor_alignment_pass else "FAIL",
            "pass": floor_alignment_pass,
            "source_lowest_y_m": parse_meta["source_lowest_y_m"],
            "measured_min_z_m": round(lowest_z_m, 6),
            "target_floor_z_m": 0.0,
            "floor_deviation_m": round(floor_deviation_m, 6),
            "abs_floor_deviation_m": round(abs(floor_deviation_m), 6),
            "tolerance_m": FLOOR_TOLERANCE_M,
            "note": (
                "保持源 OBJ 原点与顶点坐标未做自动贴地平移；"
                f"最低点 Z={lowest_z_m:.6f}m 超出 ±{FLOOR_TOLERANCE_M:.3f}m 阈值，如实报告 FAIL。"
            ),
        },
        "transform_and_origin": {
            "origin_world_xyz_m": [round(float(v), 6) for v in asset_obj.location],
            "rotation_euler_deg": [
                round(math.degrees(float(v)), 4) for v in asset_obj.rotation_euler
            ],
            "scale_xyz": [round(float(v), 6) for v in asset_obj.scale],
            "matrix_world": [
                [round(float(mat_world[r][c]), 6) for c in range(4)] for r in range(4)
            ],
        },
        "topology_integrity": {
            "degenerate_face_count": degenerate_faces,
            "zero_area_face_count": zero_area_faces,
            "loose_vertex_count": loose_verts,
            "loose_edge_count": loose_edges,
            "open_boundary_edge_count": open_boundary_edges,
            "non_boundary_non_manifold_edge_count": non_boundary_non_manifold_edges,
            "open_surface_note": (
                "树冠叶片等表面网格允许存在开放边界边 (open_boundary_edge_count)，不作为失败条件。"
            ),
        },
        "materials_distribution": {
            "expected_material_names": list(EXPECTED_MATERIAL_NAMES),
            "actual_material_names": actual_mat_names,
            "materials_match_expected": materials_match_expected,
            "slots": materials_report,
        },
        "windbent_feature_measurements_for_human_review": {
            "measurement_note": (
                "以下树干截面中心偏移与树冠质心数据仅供人工审阅判断，脚本不做造型好坏自动评价，亦不改形。"
            ),
            "trunk_height_span_m": [round(trunk_min_z, 6), round(trunk_max_z, 6)],
            "trunk_cross_section_centers_by_height": trunk_sections,
            "max_trunk_section_radial_drift_from_base_m": round(
                max_trunk_radial_drift, 6
            ),
            "crown_area_weighted_centroid_xyz_m": [
                round(float(crown_centroid.x), 6),
                round(float(crown_centroid.y), 6),
                round(float(crown_centroid.z), 6),
            ],
            "crown_centroid_xy_offset_from_origin_m": [
                round(float(crown_centroid.x), 6),
                round(float(crown_centroid.y), 6),
            ],
            "crown_centroid_radial_offset_from_origin_m": round(
                math.hypot(float(crown_centroid.x), float(crown_centroid.y)), 6
            ),
            "crown_bbox_center_xy_m": [
                round(crown_bbox_center_xy[0], 6),
                round(crown_bbox_center_xy[1], 6),
            ],
        },
        "source_parsing_meta": parse_meta,
    }


# ==============================================================================
# 5. 四宫格高清预览图生成（底部状态栏完全从本次实测动态生成，明确显示 FLOOR ALIGNMENT FAIL）
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

    1) 1m 标准参照柱（紧邻树侧，Z=0.0 至 Z=1.0m）与高度标尺
    2) 过原点 (0,0,0) 的垂直铅垂参考线与地面 Z=0 十字线
    3) 实测 Z-up 包围盒线框
    4) 3/4 斜视专用的模型拓扑线框叠加层
    5) 双日光灯组与四宫格相机 (Front -Y, Side +X, Top +Z, Oblique 3/4)
    """
    scene = bpy.context.scene
    preview_col = bpy.data.collections.new("Preview_Only")
    scene.collection.children.link(preview_col)

    dims = qa_result["dimensions_and_bounds_zup"]
    b_min = dims["bbox_min_m"]
    b_max = dims["bbox_max_m"]
    min_x, min_y, min_z = float(b_min[0]), float(b_min[1]), float(b_min[2])
    max_x, max_y, max_z = float(b_max[0]), float(b_max[1]), float(b_max[2])

    created_preview_mats: List[bpy.types.Material] = []

    def make_preview_mat(
        name: str, rgb: Tuple[float, float, float], roughness: float = 0.5
    ) -> bpy.types.Material:
        m = create_exportable_principled_material(name, rgb, roughness=roughness)
        created_preview_mats.append(m)
        return m

    mat_scale_orange = make_preview_mat("_Gate02_Preview_Scale1m_Mat", (1.0, 0.48, 0.08), 0.4)
    mat_plumb_cyan = make_preview_mat("_Gate02_Preview_Plumb_Mat", (0.05, 0.92, 1.0), 0.3)
    mat_bbox_gold = make_preview_mat("_Gate02_Preview_BBox_Mat", (0.98, 0.84, 0.18), 0.4)
    mat_ground_grid = make_preview_mat("_Gate02_Preview_GroundAxis_Mat", (0.55, 0.62, 0.70), 0.6)
    mat_wire_overlay = make_preview_mat("_Gate02_Preview_WireOverlay_Mat", (0.06, 0.09, 0.12), 0.4)

    # 1. 1m 参照柱 (放置在 X = min_x - 0.32m, Y = 0.0, Z = 0.0 ~ 1.0m)
    ref_x = min_x - 0.32
    pole_mesh = build_solid_box_mesh(
        "_Gate02_Preview_1m_Pole_Mesh",
        ref_x - 0.038,
        ref_x + 0.038,
        -0.038,
        0.038,
        0.0,
        1.0,
    )
    pole_mesh.materials.append(mat_scale_orange)
    pole_obj = bpy.data.objects.new("Preview_RefPole_1m", pole_mesh)
    preview_col.objects.link(pole_obj)

    # 右侧总高度标尺 (Z = min_z 至 max_z, 标记 0m, 1m, 2m, max_z)
    ruler_x = max_x + 0.30
    ruler_segs: List[Tuple[Vector, Vector]] = [
        (Vector((ref_x - 0.10, 0.0, 0.0)), Vector((ref_x + 0.10, 0.0, 0.0))),
        (Vector((ref_x - 0.10, 0.0, 1.0)), Vector((ref_x + 0.10, 0.0, 1.0))),
        (Vector((ref_x, -0.10, 1.0)), Vector((ref_x, 0.10, 1.0))),
        (Vector((ruler_x, 0.0, min_z)), Vector((ruler_x, 0.0, max_z))),
    ]
    for h_tick in (0.0, 1.0, 2.0, max_z):
        ruler_segs.append(
            (Vector((ruler_x - 0.10, 0.0, h_tick)), Vector((ruler_x + 0.10, 0.0, h_tick)))
        )
        ruler_segs.append(
            (Vector((ruler_x, -0.10, h_tick)), Vector((ruler_x, 0.10, h_tick)))
        )

    ruler_mesh = build_wire_frame_rods_mesh(
        "_Gate02_Preview_HeightRuler_Mesh", ruler_segs, 0.010, mat_scale_orange
    )
    ruler_obj = bpy.data.objects.new("Preview_HeightRuler", ruler_mesh)
    preview_col.objects.link(ruler_obj)

    # 2. 垂直铅垂参考线 (通过原点 (0,0,0)，从 min_z - 0.1m 到 max_z + 0.30m)
    plumb_segs = [
        (Vector((0.0, 0.0, min(0.0, min_z) - 0.10)), Vector((0.0, 0.0, max_z + 0.30))),
        (Vector((-0.13, 0.0, max_z + 0.30)), Vector((0.13, 0.0, max_z + 0.30))),
        (Vector((0.0, -0.13, max_z + 0.30)), Vector((0.0, 0.13, max_z + 0.30))),
    ]
    plumb_mesh = build_wire_frame_rods_mesh(
        "_Gate02_Preview_PlumbLine_Mesh", plumb_segs, 0.011, mat_plumb_cyan
    )
    plumb_obj = bpy.data.objects.new("Preview_VerticalPlumbLine", plumb_mesh)
    preview_col.objects.link(plumb_obj)

    # 3. 地面 Z=0 十字坐标轴基准线
    ground_segs = [
        (Vector((min_x - 0.45, 0.0, 0.0)), Vector((max_x + 0.45, 0.0, 0.0))),
        (Vector((0.0, min_y - 0.45, 0.0)), Vector((0.0, max_y + 0.45, 0.0))),
    ]
    ground_mesh = build_wire_frame_rods_mesh(
        "_Gate02_Preview_GroundCross_Mesh", ground_segs, 0.008, mat_ground_grid
    )
    ground_obj = bpy.data.objects.new("Preview_GroundCross_Z0", ground_mesh)
    preview_col.objects.link(ground_obj)

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
        "_Gate02_Preview_BBoxWire_Mesh", bbox_segs, 0.008, mat_bbox_gold
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
        "_Gate02_Preview_MeshWireOverlay_Mesh", edge_segs, 0.0045, mat_wire_overlay
    )
    wire_overlay_obj = bpy.data.objects.new(
        "Preview_MeshWireframeOverlay", wire_overlay_mesh
    )
    preview_col.objects.link(wire_overlay_obj)

    # 6. 柔和双日光与世界天光
    sun_key_data = bpy.data.lights.new(name="_Gate02_Preview_SunKey", type="SUN")
    sun_key_data.energy = 3.4
    sun_key_data.color = (1.0, 0.98, 0.93)
    sun_key_obj = bpy.data.objects.new("Preview_SunKey", sun_key_data)
    sun_key_obj.location = (3.5, -4.5, 7.0)
    sun_key_obj.rotation_euler = (
        math.radians(48.0),
        math.radians(15.0),
        math.radians(32.0),
    )
    preview_col.objects.link(sun_key_obj)

    sun_fill_data = bpy.data.lights.new(name="_Gate02_Preview_SunFill", type="SUN")
    sun_fill_data.energy = 1.4
    sun_fill_data.color = (0.82, 0.90, 1.0)
    sun_fill_obj = bpy.data.objects.new("Preview_SunFill", sun_fill_data)
    sun_fill_obj.location = (-4.5, 3.5, 5.5)
    sun_fill_obj.rotation_euler = (
        math.radians(58.0),
        math.radians(-18.0),
        math.radians(-135.0),
    )
    preview_col.objects.link(sun_fill_obj)

    if scene.world is None:
        scene.world = bpy.data.worlds.new("Gate02_World")
    scene.world.color = (0.14, 0.17, 0.21)
    scene.world.use_nodes = True
    if scene.world.node_tree:
        for node in scene.world.node_tree.nodes:
            if node.type == "BACKGROUND":
                if "Color" in node.inputs:
                    node.inputs["Color"].default_value = (0.14, 0.17, 0.21, 1.0)
                if "Strength" in node.inputs:
                    node.inputs["Strength"].default_value = 0.9

    # 7. 四台检视相机：正视(-Y)、侧视(+X)、顶视(+Z)、3/4 斜视
    mid_z = 0.5 * (min_z + max_z)
    cameras: Dict[str, bpy.types.Object] = {}

    # (a) 正视图 Front (-Y 朝 +Y 看)
    cam_front_data = bpy.data.cameras.new("_Gate02_Cam_Front")
    cam_front_data.type = "ORTHO"
    cam_front_data.ortho_scale = 5.2
    cam_front = bpy.data.objects.new("Preview_Cam_Front_NegY", cam_front_data)
    cam_front.location = (0.0, -7.0, mid_z + 0.08)
    cam_front.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    preview_col.objects.link(cam_front)
    cameras["front"] = cam_front

    # (b) 侧视图 Side (+X 朝 -X 看)
    cam_side_data = bpy.data.cameras.new("_Gate02_Cam_Side")
    cam_side_data.type = "ORTHO"
    cam_side_data.ortho_scale = 5.2
    cam_side = bpy.data.objects.new("Preview_Cam_Side_PosX", cam_side_data)
    cam_side.location = (7.0, 0.0, mid_z + 0.08)
    cam_side.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))
    preview_col.objects.link(cam_side)
    cameras["side"] = cam_side

    # (c) 正交顶视图 Top (+Z 朝 -Z 看)
    cam_top_data = bpy.data.cameras.new("_Gate02_Cam_Top")
    cam_top_data.type = "ORTHO"
    cam_top_data.ortho_scale = 3.5
    cam_top = bpy.data.objects.new("Preview_Cam_Top_PosZ", cam_top_data)
    cam_top.location = (0.0, 0.0, 8.0)
    cam_top.rotation_euler = (0.0, 0.0, 0.0)
    preview_col.objects.link(cam_top)
    cameras["top"] = cam_top

    # (d) 3/4 斜视图 Oblique (叠加线框)
    cam_oblique_data = bpy.data.cameras.new("_Gate02_Cam_Oblique")
    cam_oblique_data.type = "PERSP"
    cam_oblique_data.lens = 42.0
    cam_oblique = bpy.data.objects.new("Preview_Cam_Oblique_3Q", cam_oblique_data)
    oblique_pos = Vector((4.225, -4.55, 3.28))
    oblique_target = Vector((0.0, 0.0, mid_z + 0.04))
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
    """渲染四宫格视图并拼接为 1600x1200 的单张 PNG 检视图，动态渲染 QA PASS/FAIL 状态。"""
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

        temp_file = out_png_path.parent / f"_temp_gate02_{key}.png"
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

    dims = qa_result["dimensions_and_bounds_zup"]["measured_zup_dimensions_m"]
    g_cnt = qa_result["geometry_counts"]
    floor_qa = qa_result["floor_alignment_qa"]
    checks = qa_result["checks_summary"]
    overall_status = qa_result["overall_status"]

    header_color = (0.96, 0.98, 1.0) if qa_result["overall_pass"] else (1.0, 0.78, 0.32)
    set_text_on_buffer(
        canvas_buf,
        total_w,
        total_h,
        f"GATE 02 AS-IS INSPECTION : {ASSET_ID} | OVERALL QA: {overall_status}",
        24,
        18,
        header_color,
        scale=3,
    )

    # 四个象限标题
    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 12, 68, 540, 30, (0.06, 0.09, 0.13, 0.9)
    )
    set_text_on_buffer(
        canvas_buf,
        total_w,
        total_h,
        "1. FRONT VIEW (-Y) | 1M POLE & PLUMB LINE",
        20,
        76,
        (1.0, 0.86, 0.36),
        scale=2,
    )

    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 812, 68, 540, 30, (0.06, 0.09, 0.13, 0.9)
    )
    set_text_on_buffer(
        canvas_buf,
        total_w,
        total_h,
        f"2. SIDE VIEW (+X) | Z={dims[2]:.4f}M & BBOX WIRE",
        820,
        76,
        (1.0, 0.86, 0.36),
        scale=2,
    )

    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 12, 598, 560, 30, (0.06, 0.09, 0.13, 0.9)
    )
    set_text_on_buffer(
        canvas_buf,
        total_w,
        total_h,
        f"3. TOP VIEW (+Z) | X={dims[0]:.4f}M Y={dims[1]:.4f}M",
        20,
        606,
        (0.45, 0.95, 1.0),
        scale=2,
    )

    fill_rect_on_buffer(
        canvas_buf, total_w, total_h, 812, 598, 600, 30, (0.06, 0.09, 0.13, 0.9)
    )
    set_text_on_buffer(
        canvas_buf,
        total_w,
        total_h,
        f"4. 3/4 OBLIQUE + WIRE ({g_cnt['triangle_count']} TRIS / {g_cnt['vertex_count']} VERTS)",
        820,
        606,
        (0.55, 0.98, 0.68),
        scale=2,
    )

    # 动态生成的底部实测 QA 栏（明确显示实测尺寸、面数状态以及 FLOOR ALIGNMENT FAIL 与实际偏差）
    footer_line_1 = (
        f"MEASURED Z-UP DIMS: X={dims[0]:.6f}M Y={dims[1]:.6f}M Z={dims[2]:.6f}M "
        f"[{checks['dimensions_zup_check']}] | "
        f"VERTS={g_cnt['vertex_count']} [{checks['vertex_count_check']}] "
        f"TRIS={g_cnt['triangle_count']} [{checks['triangle_count_check']}]"
    )
    footer_line_2 = (
        f"FLOOR ALIGNMENT: {floor_qa['status']} (MIN_Z={floor_qa['measured_min_z_m']:+.6f}M, "
        f"DEVIATION={floor_qa['floor_deviation_m']:+.6f}M, TOL=+-{floor_qa['tolerance_m']:.3f}M) | "
        f"MATS=7 [{checks['materials_7_slots_check']}] | OVERALL QA: {overall_status}"
    )

    line2_color = (0.55, 0.98, 0.68) if floor_qa["pass"] else (1.0, 0.42, 0.42)
    set_text_on_buffer(
        canvas_buf, total_w, total_h, footer_line_1, 20, 1132, (0.92, 0.96, 1.0), scale=2
    )
    set_text_on_buffer(
        canvas_buf, total_w, total_h, footer_line_2, 20, 1162, line2_color, scale=2
    )

    out_img = bpy.data.images.new(
        name="_Gate02_QuadSheet", width=total_w, height=total_h, alpha=True
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
# 6. 独立 FBX 导出与可编辑 Blend 保存
# ==============================================================================


def export_single_asset_fbx(
    asset_obj: bpy.types.Object, out_fbx_path: Path
) -> Dict[str, Any]:
    """仅选中并导出 Pine_Windbent_Short_B 树网格（不含参照柱、相机、灯光或其他对象）。"""
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
        raise RuntimeError(f"导出独立资产 FBX 失败: {out_fbx_path}")

    return {
        "path": str(out_fbx_path),
        "size_bytes": out_fbx_path.stat().st_size,
        "exported_object": asset_obj.name,
        "axis_forward": "-Z",
        "axis_up": "Y",
        "unit_scale": "METRIC_1_TO_1",
    }


def save_clean_asset_blend(
    asset_obj: bpy.types.Object,
    preview_col: bpy.types.Collection,
    out_blend_path: Path,
) -> Dict[str, Any]:
    """保存 Assets_Inspected/Pine_Windbent_Short_B.blend，使该树模型成为打开即可单独检视的可见主资产。"""
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
    }


# ==============================================================================
# 7. 主流程执行、完整写盘与按实测结果返回退出状态
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

    # 3. 创建主资产集合并原样解析构建 Pine_Windbent_Short_B（不做任何贴地平移或修形）
    asset_col = bpy.data.collections.new("Asset_Inspected")
    scene.collection.children.link(asset_col)

    asset_obj, parse_meta = parse_obj_and_build_as_is_asset(
        SOURCE_OBJ_PATH, SOURCE_MTL_PATH
    )
    asset_col.objects.link(asset_obj)

    # 4. 执行完整 QA 测量（包含尺寸、面数、材质与 floor-alignment QA FAIL 判定）
    qa_result = inspect_and_verify_asset(asset_obj, parse_meta)

    # 5. 先导出只含该树网格的独立 FBX
    fbx_info = export_single_asset_fbx(asset_obj, OUT_FBX_PATH)

    # 6. 构建 Preview_Only 集合并渲染 1600x1200 四宫格预览图（底部动态呈现 FLOOR ALIGNMENT FAIL）
    preview_col, cameras, wire_overlay_obj, _preview_mats = (
        create_preview_only_collection(asset_obj, qa_result)
    )
    preview_info = render_quad_preview_sheet(
        cameras=cameras,
        wire_overlay_obj=wire_overlay_obj,
        qa_result=qa_result,
        out_png_path=OUT_PREVIEW_PNG_PATH,
    )

    # 7. 保存可单独检视该模型的 Blend 文件
    blend_info = save_clean_asset_blend(asset_obj, preview_col, OUT_BLEND_PATH)

    # 8. 写入完整的 Reports/Gate02_qa.json
    full_report: Dict[str, Any] = {
        "gate": "Gate 02 - Single Nature Asset As-Is Inspection",
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
            "candidate_generated": False,
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

    # 9. 重新核对所有 Gate 02 交付物均存在且非零
    deliverables_to_check = [
        OUT_BLEND_PATH,
        OUT_FBX_PATH,
        OUT_PREVIEW_PNG_PATH,
        OUT_REPORT_JSON_PATH,
    ]
    for p in deliverables_to_check:
        if not p.exists() or p.stat().st_size <= 0:
            raise RuntimeError(f"Gate 02 交付物缺失或文件大小为 0: {p}")

    # 10. 打印关键实测值、各项 PASS/FAIL 与绝对输出路径
    dims_m = qa_result["dimensions_and_bounds_zup"]["measured_zup_dimensions_m"]
    g_cnt = qa_result["geometry_counts"]
    floor_qa = qa_result["floor_alignment_qa"]
    checks = qa_result["checks_summary"]
    wb_m = qa_result["windbent_feature_measurements_for_human_review"]

    print("=" * 80)
    print(f"Gate 02 原样独立资产检视报告 : {ASSET_ID}")
    print("=" * 80)
    print(f"Blender 版本                 : {bpy.app.version_string}")
    print(
        f"实测 Z-up 尺寸 (m)           : X={dims_m[0]:.6f}, Y={dims_m[1]:.6f}, Z={dims_m[2]:.6f} "
        f"(基线: {BASELINE_ZUP_DIMS})"
    )
    print(
        f"实测 Z-up 包围盒 (m)         : min={qa_result['dimensions_and_bounds_zup']['bbox_min_m']}, "
        f"max={qa_result['dimensions_and_bounds_zup']['bbox_max_m']}"
    )
    print(
        f"源最低点与落地偏差           : 源最低 Y={floor_qa['source_lowest_y_m']:+.6f}m -> "
        f"转换后最低 Z={floor_qa['measured_min_z_m']:+.6f}m (偏差={floor_qa['floor_deviation_m']:+.6f}m, "
        f"阈值=±{floor_qa['tolerance_m']:.3f}m)"
    )
    print(
        f"网格统计                     : 顶点={g_cnt['vertex_count']} (基线 {BASELINE_VERTICES}), "
        f"边={g_cnt['edge_count']}, 三角面={g_cnt['triangle_count']} (基线 {BASELINE_TRIANGLES})"
    )
    print(
        f"材质与面数分布 (7 slots)     : "
        f"{[(m['material_name'], m['triangle_count'], m['principled_base_color_rgb']) for m in qa_result['materials_distribution']['slots']]}"
    )
    print(
        f"风弯特征实测 (供人工审阅)    : 树干截面最大水平漂移={wb_m['max_trunk_section_radial_drift_from_base_m']:.6f}m, "
        f"树冠质心偏移={wb_m['crown_centroid_xy_offset_from_origin_m']}m"
    )
    print("-" * 80)
    print("各项 QA 检查结果:")
    for chk_name, chk_status in checks.items():
        print(f"  * {chk_name:<38} : {chk_status}")
    print(f"  => Gate 02 综合状态 (OVERALL QA)         : {qa_result['overall_status']}")
    if qa_result["failure_reasons"]:
        print("失败原因明细:")
        for reason in qa_result["failure_reasons"]:
            print(f"  [FAIL] {reason}")
    print("-" * 80)
    print("Gate 02 交付物绝对路径:")
    for p in deliverables_to_check:
        print(f"  -> {p.resolve()} ({p.stat().st_size} bytes)")
    print("=" * 80)

    # 按要求：先写完所有报告、预览、Blend 与 FBX，若存在 QA FAIL（如 floor-alignment FAIL 或尺寸/面数不符），最后以非零状态退出
    if not qa_result["overall_pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()