# -*- coding: utf-8 -*-
"""Gate 00: IslandReference_V2 现有地形基准只读复核脚本 (Blender 5.2.2)

保存位置: work/island_final_candidate/Scripts/Gate00_inspect_terrain.py
执行方式: blender -b -P
"D:/Last Landfall/work/island_final_candidate/Scripts/Gate00_inspect_terrain.py"
"""

from __future__ import annotations

import datetime
import inspect
import json
import math
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple
import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np


# ==============================================================================
# 1. 路径推导与严格前置存在性校验（只读边界，不修改 Assets 下任何文件）
# ==============================================================================

TERRAIN_OBJ_NAME: str = "IslandReference_V2"
COAST_SEED: int = 9
MASK_SAMPLE_STEP_M: float = 10.0


def resolve_project_root() -> Path:
  """从脚本自身位置向上推导项目根目录，兼容 Scripts 子目录或任意工程子目录。"""
  if "__file__" in globals() and globals()["__file__"]:
    script_path = Path(globals()["__file__"]).resolve()
    for parent in script_path.parents:
      if (parent / "Assets").is_dir() and (
          parent / "Tools" / "Blender"
      ).is_dir():
        return parent
    if len(script_path.parents) >= 4:
      cand = script_path.parents[3]
      if cand.exists():
        return cand
  fallback = Path(r"D:\Last Landfall")
  if fallback.exists():
    return fallback
  raise RuntimeError(
      "无法从脚本路径推导项目根目录，请确认脚本位于 D:\\Last Landfall 工程目录内。"
  )


PROJECT_ROOT: Path = resolve_project_root()

SOURCE_BLEND_PATH: Path = (
    PROJECT_ROOT
    / "Assets"
    / "LastLandfall"
    / "Art"
    / "Source"
    / "Environment"
    / "IslandReference_V2.blend"
)
SOURCE_FBX_PATH: Path = (
    PROJECT_ROOT
    / "Assets"
    / "LastLandfall"
    / "Resources"
    / "Models"
    / "Environment"
    / "IslandReference_V2.fbx"
)
TOOLS_BLENDER_DIR: Path = PROJECT_ROOT / "Tools" / "Blender"
MOD_V2_PATH: Path = TOOLS_BLENDER_DIR / "build_island_reference_v2.py"
MOD_LANDFORM_PATH: Path = TOOLS_BLENDER_DIR / "island_reference_landform.py"
MOD_LOOKDEV_PATH: Path = TOOLS_BLENDER_DIR / "island_reference_lookdev.py"

OUTPUT_ROOT: Path = PROJECT_ROOT / "work" / "island_final_candidate"
OUT_TERRAIN_DIR: Path = OUTPUT_ROOT / "Terrain"
OUT_PREVIEWS_DIR: Path = OUTPUT_ROOT / "Previews"
OUT_REPORTS_DIR: Path = OUTPUT_ROOT / "Reports"

OUT_BLEND_PATH: Path = OUT_TERRAIN_DIR / "IslandReference_V2.blend"
OUT_FBX_PATH: Path = OUT_TERRAIN_DIR / "IslandReference_V2.fbx"
OUT_PREVIEW_PNG_PATH: Path = OUT_PREVIEWS_DIR / "Gate00_Terrain_Review.png"
OUT_REPORT_JSON_PATH: Path = OUT_REPORTS_DIR / "Gate00_terrain_qa.json"


def verify_required_inputs_and_import_modules() -> Tuple[Any, Any, Any]:
  """验证源 Blend、源 FBX 及三个地形模块存在并安全导入（绝不调用任何生成/写入函数）。"""
  required_files: List[Tuple[str, Path]] = [
      ("现有地形源 Blend", SOURCE_BLEND_PATH),
      ("现有 Terrain FBX", SOURCE_FBX_PATH),
      ("地形构建模块 build_island_reference_v2.py", MOD_V2_PATH),
      ("地形造型模块 island_reference_landform.py", MOD_LANDFORM_PATH),
      ("地形外观模块 island_reference_lookdev.py", MOD_LOOKDEV_PATH),
  ]
  for label, path in required_files:
    if not path.exists() or not path.is_file():
      raise FileNotFoundError(f"Gate 00 前置校验失败：缺少{label}，具体路径: {path}")
    if path.stat().st_size == 0:
      raise RuntimeError(f"Gate 00 前置校验失败：{label} 文件大小为 0，具体路径: {path}")

  tools_str = str(TOOLS_BLENDER_DIR)
  if tools_str not in sys.path:
    sys.path.insert(0, tools_str)

  import island_reference_landform as landform_mod
  import island_reference_lookdev as lookdev_mod
  import build_island_reference_v2 as v2_mod

  if not hasattr(v2_mod, "coast_polygon") and not hasattr(
      landform_mod, "coast_polygon"
  ):
    raise AttributeError(
        f"模块缺少 coast_polygon 函数: {MOD_V2_PATH} / {MOD_LANDFORM_PATH}"
    )
  if not hasattr(landform_mod, "terrain_fields"):
    raise AttributeError(
        f"模块缺少 terrain_fields(x, y) 函数: {MOD_LANDFORM_PATH}"
    )

  return v2_mod, landform_mod, lookdev_mod


# ==============================================================================
# 2. 只读加载源 Blend 并提取网格、材质与拓扑指标（绝不修改 Mesh 数据）
# ==============================================================================


def inspect_terrain_object_and_topology(
    v2_mod: Any, landform_mod: Any
) -> Tuple[
    bpy.types.Object,
    BVHTree,
    List[Tuple[float, float]],
    List[Tuple[Vector, Vector]],
    Dict[str, Any],
]:
  """在只读模式下检查 IslandReference_V2 的几何、材质分布与 bmesh 拓扑边界。"""
  terrain_obj = bpy.data.objects.get(TERRAIN_OBJ_NAME)
  if terrain_obj is None:
    raise RuntimeError(
        f"在源 Blend ({SOURCE_BLEND_PATH}) 中找不到目标地形对象 '{TERRAIN_OBJ_NAME}'。"
    )
  if terrain_obj.type != "MESH" or terrain_obj.data is None:
    raise RuntimeError(
        f"对象 '{TERRAIN_OBJ_NAME}' 类型不是 MESH (实际为 {terrain_obj.type})。"
    )

  bpy.context.view_layer.update()
  mesh: bpy.types.Mesh = terrain_obj.data
  mat_world = terrain_obj.matrix_world.copy()

  # 世界空间与局部空间顶点坐标
  local_coords = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
  mesh.vertices.foreach_get("co", local_coords)
  local_coords = local_coords.reshape((-1, 3))

  rot_scale = np.array(
      [
          [mat_world[0][0], mat_world[0][1], mat_world[0][2]],
          [mat_world[1][0], mat_world[1][1], mat_world[1][2]],
          [mat_world[2][0], mat_world[2][1], mat_world[2][2]],
      ],
      dtype=np.float64,
  )
  translation = np.array(
      [mat_world[0][3], mat_world[1][3], mat_world[2][3]], dtype=np.float64
  )
  world_coords = local_coords @ rot_scale.T + translation

  local_min = local_coords.min(axis=0)
  local_max = local_coords.max(axis=0)
  world_min = world_coords.min(axis=0)
  world_max = world_coords.max(axis=0)
  world_span = world_max - world_min

  # 三角面统计（只读访问 loop_triangles，不修改源网格）
  loop_tris = mesh.loop_triangles
  tri_count = len(loop_tris)
  poly_count = len(mesh.polygons)
  vert_count = len(mesh.vertices)
  edge_count = len(mesh.edges)

  # 材质槽与各材质面数/三角面数分布
  slot_poly_counts: Dict[int, int] = {
      i: 0 for i in range(max(1, len(mesh.materials)))
  }
  slot_tri_counts: Dict[int, int] = {
      i: 0 for i in range(max(1, len(mesh.materials)))
  }
  non_tri_polygons = 0

  for poly in mesh.polygons:
    m_idx = int(poly.material_index)
    slot_poly_counts[m_idx] = slot_poly_counts.get(m_idx, 0) + 1
    n_v = len(poly.vertices)
    if n_v != 3:
      non_tri_polygons += 1
    slot_tri_counts[m_idx] = slot_tri_counts.get(m_idx, 0) + max(1, n_v - 2)

  material_distribution: List[Dict[str, Any]] = []
  for slot_idx in sorted(slot_poly_counts.keys()):
    mat_name = None
    diffuse_rgba = None
    if slot_idx < len(mesh.materials) and mesh.materials[slot_idx] is not None:
      mat = mesh.materials[slot_idx]
      mat_name = mat.name
      diffuse_rgba = [round(float(c), 4) for c in mat.diffuse_color]
    p_cnt = slot_poly_counts[slot_idx]
    t_cnt = slot_tri_counts[slot_idx]
    material_distribution.append({
        "slot_index": slot_idx,
        "material_name": mat_name,
        "viewport_diffuse_rgba": diffuse_rgba,
        "polygon_count": p_cnt,
        "triangle_count": t_cnt,
        "polygon_ratio_pct": (
            round(p_cnt * 100.0 / poly_count, 3) if poly_count else 0.0
        ),
    })

  # 海岸多边形预期边界段数
  coast_fn = getattr(v2_mod, "coast_polygon", None) or getattr(
      landform_mod, "coast_polygon"
  )
  raw_coast = coast_fn(COAST_SEED)
  coast_pts: List[Tuple[float, float]] = [
      (float(p[0]), float(p[1])) for p in raw_coast
  ]
  if len(coast_pts) >= 2 and (
      math.hypot(
          coast_pts[0][0] - coast_pts[-1][0], coast_pts[0][1] - coast_pts[-1][1]
      )
      < 1e-5
  ):
    expected_coast_segments = len(coast_pts) - 1
  else:
    expected_coast_segments = len(coast_pts)

  # 只读 bmesh 拓扑核验（绝不写回 mesh，不调用 validate/重算法线）
  bm = bmesh.new()
  bm.from_mesh(mesh)
  bm.verts.ensure_lookup_table()
  bm.edges.ensure_lookup_table()
  bm.faces.ensure_lookup_table()

  boundary_edges_world: List[Tuple[Vector, Vector]] = []
  boundary_edge_count = 0
  non_boundary_non_manifold_count = 0
  wire_edge_count = 0
  multi_face_edge_count = 0
  non_contiguous_internal_edge_count = 0

  for e in bm.edges:
    if e.is_boundary:
      boundary_edge_count += 1
      v0_w = mat_world @ e.verts[0].co
      v1_w = mat_world @ e.verts[1].co
      boundary_edges_world.append((v0_w, v1_w))
    elif not e.is_manifold:
      non_boundary_non_manifold_count += 1
      n_f = len(e.link_faces)
      if n_f == 0:
        wire_edge_count += 1
      elif n_f > 2:
        multi_face_edge_count += 1
      elif not e.is_contiguous:
        non_contiguous_internal_edge_count += 1

  loose_vert_count = sum(1 for v in bm.verts if len(v.link_edges) == 0)
  degenerate_face_count = sum(1 for f in bm.faces if f.calc_area() <= 1e-10)

  # 构建世界空间 BVHTree 供高度与坡度只读核验
  world_verts_vec = [Vector(( float(c[0]), float(c[1]), float(c[2]) )) for c in world_coords]
  polys_indices = [tuple(p.vertices) for p in mesh.polygons]
  bvh = BVHTree.FromPolygons(world_verts_vec, polys_indices, all_triangles=False)

  bm.free()

  boundary_matches_coast = boundary_edge_count == expected_coast_segments
  topology_clean = (
      non_boundary_non_manifold_count == 0
      and loose_vert_count == 0
      and degenerate_face_count == 0
      and non_tri_polygons == 0
  )

  inspection_data: Dict[str, Any] = {
      "object_name": terrain_obj.name,
      "world_transform": {
          "location": [round(float(v), 5) for v in terrain_obj.location],
          "rotation_euler_rad": [
              round(float(v), 5) for v in terrain_obj.rotation_euler
          ],
          "rotation_euler_deg": [
              round(math.degrees(float(v)), 4)
              for v in terrain_obj.rotation_euler
          ],
          "scale": [round(float(v), 5) for v in terrain_obj.scale],
          "matrix_world": [
              [round(float(mat_world[r][c]), 6) for c in range(4)]
              for r in range(4)
          ],
      },
      "dimensions_and_bounds": {
          "object_dimensions_m": [
              round(float(v), 3) for v in terrain_obj.dimensions
          ],
          "local_bbox_min": [round(float(v), 3) for v in local_min],
          "local_bbox_max": [round(float(v), 3) for v in local_max],
          "world_bbox_min": [round(float(v), 3) for v in world_min],
          "world_bbox_max": [round(float(v), 3) for v in world_max],
          "world_span_xyz_m": [round(float(v), 3) for v in world_span],
      },
      "mesh_statistics": {
          "vertex_count": vert_count,
          "edge_count": edge_count,
          "polygon_count": poly_count,
          "triangle_count": tri_count,
          "non_triangular_polygon_count": non_tri_polygons,
          "material_slot_count": len(mesh.materials),
          "material_distribution": material_distribution,
      },
      "topology_verification": {
          "coast_seed": COAST_SEED,
          "expected_coast_polygon_segments": expected_coast_segments,
          "actual_boundary_edges": boundary_edge_count,
          "boundary_matches_expected_coast": boundary_matches_coast,
          "design_open_boundary_note": (
              "海岸线外边界在设计上为开放边（Open Boundary Edges），"
              "actual_boundary_edges 与 coast_polygon(9) 段数比对用于确认海岸开边完整性，"
              "不作为拓扑缺陷报错。"
          ),
          "boundary_mismatch_flag": (not boundary_matches_coast),
          "non_boundary_non_manifold_edges": non_boundary_non_manifold_count,
          "wire_edges": wire_edge_count,
          "multi_face_edges_gt2": multi_face_edge_count,
          "non_contiguous_internal_edges": non_contiguous_internal_edge_count,
          "loose_vertices": loose_vert_count,
          "zero_area_degenerate_faces": degenerate_face_count,
          "internal_manifold_clean": topology_clean,
      },
  }

  return (
      terrain_obj,
      bvh,
      coast_pts,
      boundary_edges_world,
      inspection_data,
  )


# ==============================================================================
# 3. 生态遮罩网格采样核验 (terrain_fields: valley_mask & buildable_mask)
# ==============================================================================


def make_terrain_fields_evaluator(landform_mod: Any):
  """包装 island_reference_landform.terrain_fields(x, y)，自适应参数签名与返回结构。"""
  tf_fn = getattr(landform_mod, "terrain_fields")
  sig = inspect.signature(tf_fn)
  req_pos = [
      p
      for p in sig.parameters.values()
      if p.default is inspect.Parameter.empty
      and p.kind
      in (
          inspect.Parameter.POSITIONAL_ONLY,
          inspect.Parameter.POSITIONAL_OR_KEYWORD,
      )
  ]
  needs_seed = len(req_pos) >= 3

  def evaluate(x: Any, y: Any) -> Dict[str, Any]:
    raw = (
        tf_fn(x, y, COAST_SEED)
        if needs_seed
        else tf_fn(x, y)
    )
    if isinstance(raw, dict):
      return dict(raw)
    out: Dict[str, Any] = {}
    for attr in dir(raw):
      if not attr.startswith("_"):
        val = getattr(raw, attr)
        if not callable(val):
          out[attr] = val
    return out

  return evaluate


def summarize_mask_region(
    mask_name: str,
    threshold: float,
    xs: List[float],
    ys: List[float],
    zs: List[float],
    slopes: List[float],
    cell_area_m2: float,
) -> Dict[str, Any]:
  """计算指定阈值下掩膜区域的有效面积、覆盖范围、海拔与坡度统计。"""
  count = len(xs)
  if count == 0:
    return {
        "mask_name": mask_name,
        "threshold": threshold,
        "sample_count": 0,
        "estimated_area_m2": 0.0,
        "estimated_area_hectares": 0.0,
        "xy_bounds_min": None,
        "xy_bounds_max": None,
        "xy_span_m": [0.0, 0.0],
        "elevation_z_m": None,
        "slope_deg": None,
    }

  x_arr = np.array(xs, dtype=np.float64)
  y_arr = np.array(ys, dtype=np.float64)
  z_arr = np.array(zs, dtype=np.float64)
  s_arr = np.array(slopes, dtype=np.float64)
  area_m2 = float(count * cell_area_m2)

  return {
      "mask_name": mask_name,
      "threshold": threshold,
      "sample_count": count,
      "estimated_area_m2": round(area_m2, 1),
      "estimated_area_hectares": round(area_m2 / 10000.0, 3),
      "xy_bounds_min": [round(float(x_arr.min()), 2), round(float(y_arr.min()), 2)],
      "xy_bounds_max": [round(float(x_arr.max()), 2), round(float(y_arr.max()), 2)],
      "xy_span_m": [
          round(float(x_arr.max() - x_arr.min()), 2),
          round(float(y_arr.max() - y_arr.min()), 2),
      ],
      "elevation_z_m": {
          "min": round(float(z_arr.min()), 3),
          "max": round(float(z_arr.max()), 3),
          "mean": round(float(z_arr.mean()), 3),
          "median": round(float(np.median(z_arr)), 3),
          "std": round(float(z_arr.std()), 3),
      },
      "slope_deg": {
          "min": round(float(s_arr.min()), 3),
          "max": round(float(s_arr.max()), 3),
          "mean": round(float(s_arr.mean()), 3),
          "median": round(float(np.median(s_arr)), 3),
          "p95": round(float(np.percentile(s_arr, 95)), 3),
      },
  }


def sample_ecological_masks_and_surface(
    bvh: BVHTree,
    landform_mod: Any,
    world_bbox_min: Sequence[float],
    world_bbox_max: Sequence[float],
    step_m: float = MASK_SAMPLE_STEP_M,
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
  """在地形 XY 包围盒内按均匀网格采样真实网格表面与 terrain_fields(x, y) 遮罩数据。"""
  eval_fields = make_terrain_fields_evaluator(landform_mod)

  min_x, min_y = float(world_bbox_min[0]), float(world_bbox_min[1])
  max_x, max_y = float(world_bbox_max[0]), float(world_bbox_max[1])

  xs_grid = np.arange(min_x, max_x + 0.5 * step_m, step_m, dtype=np.float64)
  ys_grid = np.arange(min_y, max_y + 0.5 * step_m, step_m, dtype=np.float64)
  nx = len(xs_grid)
  ny = len(ys_grid)
  cell_area = step_m * step_m

  # 二维栅格缓存，用于生成高清 QA 俯视图
  valid_grid = np.zeros((ny, nx), dtype=bool)
  z_grid = np.full((ny, nx), np.nan, dtype=np.float64)
  slope_grid = np.full((ny, nx), np.nan, dtype=np.float64)
  normal_x_grid = np.zeros((ny, nx), dtype=np.float64)
  normal_y_grid = np.zeros((ny, nx), dtype=np.float64)
  normal_z_grid = np.ones((ny, nx), dtype=np.float64)
  valley_grid = np.zeros((ny, nx), dtype=np.float64)
  buildable_grid = np.zeros((ny, nx), dtype=np.float64)

  # terrain_fields is NumPy-vectorized: compute masks for the full XY grid once.
  # BVH still verifies actual terrain presence and supplies surface normals/heights.
  x_mesh, y_mesh = np.meshgrid(xs_grid, ys_grid, indexing="xy")
  fields_grid = eval_fields(x_mesh, y_mesh)
  available_field_keys = sorted(list(fields_grid.keys()))
  valley_values_grid = np.asarray(
      fields_grid.get("valley_mask", fields_grid.get("valley", np.zeros_like(x_mesh))),
      dtype=np.float64,
  )
  buildable_values_grid = np.asarray(
      fields_grid.get("buildable_mask", fields_grid.get("buildable", np.zeros_like(x_mesh))),
      dtype=np.float64,
  )
  if valley_values_grid.shape != x_mesh.shape or buildable_values_grid.shape != x_mesh.shape:
    raise ValueError(
        "terrain_fields mask shapes do not match the XY sample grid: "
        f"{valley_values_grid.shape}, {buildable_values_grid.shape}, expected {x_mesh.shape}"
    )

  # 检查 terrain_fields 是否自带任何走廊/通道字段（严禁猜测坐标）
  corridor_field_keys = [
      k
      for k in available_field_keys
      if any(
          token in k.lower()
          for token in ("corridor", "rescue", "walkway", "pathway", "route")
      )
  ]

  val_50_x, val_50_y, val_50_z, val_50_s = [], [], [], []
  val_15_x, val_15_y, val_15_z, val_15_s = [], [], [], []
  bld_50_x, bld_50_y, bld_50_z, bld_50_s = [], [], [], []
  bld_15_x, bld_15_y, bld_15_z, bld_15_s = [], [], [], []

  all_land_z: List[float] = []
  all_land_slope: List[float] = []
  all_valley_vals: List[float] = []
  all_buildable_vals: List[float] = []

  ray_dir = Vector((0.0, 0.0, -1.0))

  for iy, y in enumerate(ys_grid):
    for ix, x in enumerate(xs_grid):
      origin = Vector((float(x), float(y), 2500.0))
      loc, normal, _f_idx, _dist = bvh.ray_cast(origin, ray_dir, 5000.0)
      if loc is None or normal is None:
        continue

      n = normal.normalized()
      if n.z < 0.0:
        n = -n
      cos_t = max(-1.0, min(1.0, float(n.z)))
      slope_deg = math.degrees(math.acos(cos_t))
      z_val = float(loc.z)

      v_mask = float(valley_values_grid[iy, ix])
      b_mask = float(buildable_values_grid[iy, ix])

      valid_grid[iy, ix] = True
      z_grid[iy, ix] = z_val
      slope_grid[iy, ix] = slope_deg
      normal_x_grid[iy, ix] = float(n.x)
      normal_y_grid[iy, ix] = float(n.y)
      normal_z_grid[iy, ix] = float(n.z)
      valley_grid[iy, ix] = v_mask
      buildable_grid[iy, ix] = b_mask

      all_land_z.append(z_val)
      all_land_slope.append(slope_deg)
      all_valley_vals.append(v_mask)
      all_buildable_vals.append(b_mask)

      if v_mask >= 0.5:
        val_50_x.append(float(x))
        val_50_y.append(float(y))
        val_50_z.append(z_val)
        val_50_s.append(slope_deg)
      if v_mask >= 0.15:
        val_15_x.append(float(x))
        val_15_y.append(float(y))
        val_15_z.append(z_val)
        val_15_s.append(slope_deg)

      if b_mask >= 0.5:
        bld_50_x.append(float(x))
        bld_50_y.append(float(y))
        bld_50_z.append(z_val)
        bld_50_s.append(slope_deg)
      if b_mask >= 0.15:
        bld_15_x.append(float(x))
        bld_15_y.append(float(y))
        bld_15_z.append(z_val)
        bld_15_s.append(slope_deg)

  if corridor_field_keys:
    corridor_status = {
        "has_explicit_corridor_field_in_terrain_fields": True,
        "corridor_field_keys": corridor_field_keys,
        "note": (
            "terrain_fields 包含显式走廊字段，总装阶段将结合实际网格核验使用。"
        ),
    }
  else:
    corridor_status = {
        "has_explicit_corridor_field_in_terrain_fields": False,
        "corridor_field_keys": [],
        "note": (
            "走廊轨迹留待总装阶段依据实际网格高程/坡度提取并人工确认"
        ),
    }

  mask_report: Dict[str, Any] = {
      "sampling_step_m": step_m,
      "grid_dimensions_nx_ny": [nx, ny],
      "total_grid_points": int(nx * ny),
      "valid_terrain_mesh_samples": len(all_land_z),
      "estimated_total_island_mesh_area_m2": round(
          len(all_land_z) * cell_area, 1
      ),
      "terrain_fields_available_keys": available_field_keys,
      "valley_mask_value_range": {
          "min": round(float(min(all_valley_vals)), 4) if all_valley_vals else 0.0,
          "max": round(float(max(all_valley_vals)), 4) if all_valley_vals else 0.0,
          "mean": round(float(np.mean(all_valley_vals)), 4) if all_valley_vals else 0.0,
      },
      "buildable_mask_value_range": {
          "min": round(float(min(all_buildable_vals)), 4) if all_buildable_vals else 0.0,
          "max": round(float(max(all_buildable_vals)), 4) if all_buildable_vals else 0.0,
          "mean": round(float(np.mean(all_buildable_vals)), 4) if all_buildable_vals else 0.0,
      },
      "valley_mask_core_gt_0_50": summarize_mask_region(
          "valley_mask", 0.50, val_50_x, val_50_y, val_50_z, val_50_s, cell_area
      ),
      "valley_mask_effective_gt_0_15": summarize_mask_region(
          "valley_mask", 0.15, val_15_x, val_15_y, val_15_z, val_15_s, cell_area
      ),
      "buildable_mask_core_gt_0_50": summarize_mask_region(
          "buildable_mask",
          0.50,
          bld_50_x,
          bld_50_y,
          bld_50_z,
          bld_50_s,
          cell_area,
      ),
      "buildable_mask_effective_gt_0_15": summarize_mask_region(
          "buildable_mask",
          0.15,
          bld_15_x,
          bld_15_y,
          bld_15_z,
          bld_15_s,
          cell_area,
      ),
      "southwest_rescue_corridor": corridor_status,
  }

  grids = {
      "xs_grid": xs_grid,
      "ys_grid": ys_grid,
      "valid_grid": valid_grid,
      "z_grid": z_grid,
      "slope_grid": slope_grid,
      "normal_x_grid": normal_x_grid,
      "normal_y_grid": normal_y_grid,
      "normal_z_grid": normal_z_grid,
      "valley_grid": valley_grid,
      "buildable_grid": buildable_grid,
  }

  return mask_report, grids


# ==============================================================================
# 4. 导出只读 Blend 副本与独立 Terrain FBX
# ==============================================================================


def copy_readonly_source_blend(src_blend: Path, dst_blend: Path) -> Dict[str, Any]:
  """直接复制源 Blend 作为只读交付副本，确保不改变其中任何对象与状态。"""
  dst_blend.parent.mkdir(parents=True, exist_ok=True)
  shutil.copy2(src_blend, dst_blend)
  if not dst_blend.exists() or dst_blend.stat().st_size == 0:
    raise RuntimeError(f"复制源 Blend 副本失败: {dst_blend}")
  return {
      "path": str(dst_blend),
      "source_copied_from": str(src_blend),
      "size_bytes": dst_blend.stat().st_size,
      "exact_size_match": dst_blend.stat().st_size == src_blend.stat().st_size,
  }


def export_terrain_only_fbx(
    terrain_obj: bpy.types.Object, out_fbx: Path
) -> Dict[str, Any]:
  """单独选中 IslandReference_V2 导出纯净 Terrain FBX（不含水/植物/灯光/相机）。"""
  out_fbx.parent.mkdir(parents=True, exist_ok=True)

  bpy.ops.object.select_all(action="DESELECT")
  terrain_obj.hide_set(False)
  terrain_obj.hide_viewport = False
  terrain_obj.select_set(True)
  bpy.context.view_layer.objects.active = terrain_obj

  bpy.ops.export_scene.fbx(
      filepath=str(out_fbx),
      use_selection=True,
      object_types={"MESH"},
      axis_forward="-Z",
      axis_up="Y",
      global_scale=1.0,
      apply_unit_scale=True,
      apply_scale_options="FBX_SCALE_ALL",
      bake_space_transform=False,
      use_mesh_modifiers=False,
      mesh_smooth_type="FACE",
      add_leaf_bones=False,
      bake_anim=False,
      path_mode="AUTO",
  )

  if not out_fbx.exists() or out_fbx.stat().st_size <= 512:
    raise RuntimeError(f"导出 Terrain FBX 失败或文件大小异常: {out_fbx}")

  return {
      "path": str(out_fbx),
      "size_bytes": out_fbx.stat().st_size,
      "exported_object": terrain_obj.name,
      "axis_forward": "-Z",
      "axis_up": "Y",
      "unit_system": "METRIC",
  }


# ==============================================================================
# 5. 生成 Gate 00 地形 + 海岸边界 + Valley/Buildable 掩膜综合 QA 俯视/斜视预览图
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
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "<": ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def draw_text_on_canvas(
    canvas: np.ndarray,
    text: str,
    x: int,
    top_y: int,
    color: Tuple[float, float, float],
    scale: int = 2,
) -> None:
  """在 RGBA 浮点画布 (H, W, 4, origin=bottom-left) 上绘制点阵文本。"""
  h, w, _ = canvas.shape
  cursor_x = x
  for ch in text.upper():
    glyph = FONT_5X7.get(ch, FONT_5X7[" "])
    for row_idx, row_str in enumerate(glyph):
      for col_idx, bit in enumerate(row_str):
        if bit == "1":
          py_top = top_y + row_idx * scale
          px_left = cursor_x + col_idx * scale
          y0 = max(0, h - 1 - (py_top + scale - 1))
          y1 = min(h, h - py_top)
          x0 = max(0, px_left)
          x1 = min(w, px_left + scale)
          if y0 < y1 and x0 < x1:
            canvas[y0:y1, x0:x1, 0] = color[0]
            canvas[y0:y1, x0:x1, 1] = color[1]
            canvas[y0:y1, x0:x1, 2] = color[2]
            canvas[y0:y1, x0:x1, 3] = 1.0
    cursor_x += 6 * scale


def draw_segment_on_canvas(
    canvas: np.ndarray,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    color: Tuple[float, float, float],
    radius: int = 1,
) -> None:
  """在画布 (origin=bottom-left) 上绘制抗锯齿/加粗线段。"""
  h, w, _ = canvas.shape
  dist = max(1, int(math.hypot(x1 - x0, y1 - y0) * 1.5))
  ts = np.linspace(0.0, 1.0, dist + 1)
  xs = np.clip(np.round(x0 + (x1 - x0) * ts).astype(np.int32), 0, w - 1)
  ys = np.clip(np.round(y0 + (y1 - y0) * ts).astype(np.int32), 0, h - 1)
  for dx in range(-radius, radius + 1):
    for dy in range(-radius, radius + 1):
      px = np.clip(xs + dx, 0, w - 1)
      py = np.clip(ys + dy, 0, h - 1)
      canvas[py, px, 0] = color[0]
      canvas[py, px, 1] = color[1]
      canvas[py, px, 2] = color[2]
      canvas[py, px, 3] = 1.0


def try_render_3d_oblique_panel(
    terrain_obj: bpy.types.Object,
    world_bbox_min: Sequence[float],
    world_bbox_max: Sequence[float],
    panel_w: int,
    panel_h: int,
    temp_png_path: Path,
) -> Optional[np.ndarray]:
  """尝试使用 Blender 渲染真实 3D 场景斜视图，并在渲染后清理临时相机/灯光，不保存至源 Blend。"""
  scene = bpy.context.scene
  orig_cam = scene.camera
  orig_engine = scene.render.engine
  orig_res_x = scene.render.resolution_x
  orig_res_y = scene.render.resolution_y
  orig_filepath = scene.render.filepath

  temp_objs: List[bpy.types.Object] = []
  temp_data: List[Any] = []

  try:
    min_x, min_y, _min_z = world_bbox_min
    max_x, max_y, max_z = world_bbox_max
    cx = 0.5 * (min_x + max_x)
    cy = 0.5 * (min_y + max_y)
    span = max(max_x - min_x, max_y - min_y)

    # 仅在场景缺少灯光时添加临时日光
    existing_lights = [o for o in scene.objects if o.type == "LIGHT"]
    if not existing_lights:
      sun_data = bpy.data.lights.new(name="_Gate00_TempSun", type="SUN")
      sun_data.energy = 3.5
      sun_data.color = (1.0, 0.97, 0.92)
      sun_obj = bpy.data.objects.new("_Gate00_TempSunObj", sun_data)
      sun_obj.location = (cx - 500.0, cy - 500.0, 1200.0)
      sun_obj.rotation_euler = (
          math.radians(48.0),
          math.radians(16.0),
          math.radians(-35.0),
      )
      scene.collection.objects.link(sun_obj)
      temp_objs.append(sun_obj)
      temp_data.append(sun_data)

    cam_data = bpy.data.cameras.new(name="_Gate00_TempCam")
    cam_data.type = "PERSP"
    cam_data.lens = 36.0
    cam_data.clip_start = 2.0
    cam_data.clip_end = 15000.0
    cam_obj = bpy.data.objects.new("_Gate00_TempCamObj", cam_data)

    cam_pos = Vector((cx - span * 0.66, cy - span * 0.84, max_z + span * 0.56))
    target_pt = Vector((cx, cy - 30.0, 45.0))
    cam_obj.location = cam_pos
    cam_obj.rotation_euler = (
        (target_pt - cam_pos).normalized().to_track_quat("-Z", "Y").to_euler("XYZ")
    )
    scene.collection.objects.link(cam_obj)
    temp_objs.append(cam_obj)
    temp_data.append(cam_data)

    scene.camera = cam_obj
    scene.render.resolution_x = panel_w
    scene.render.resolution_y = panel_h
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(temp_png_path)

    available_engines = [
        item.identifier
        for item in bpy.types.RenderSettings.bl_rna.properties[
            "engine"
        ].enum_items
    ]
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES", "BLENDER_WORKBENCH"):
      if eng not in available_engines:
        continue
      try:
        scene.render.engine = eng
        if eng == "CYCLES" and hasattr(scene, "cycles"):
          scene.cycles.device = "CPU"
          scene.cycles.samples = 16
          if hasattr(scene.cycles, "use_denoising"):
            scene.cycles.use_denoising = False
        bpy.ops.render.render(write_still=True)
        if temp_png_path.exists() and temp_png_path.stat().st_size > 1024:
          img = bpy.data.images.load(str(temp_png_path), check_existing=False)
          pixels = np.empty(panel_w * panel_h * 4, dtype=np.float32)
          img.pixels.foreach_get(pixels)
          bpy.data.images.remove(img)
          try:
            temp_png_path.unlink()
          except OSError:
            pass
          return pixels.reshape((panel_h, panel_w, 4))
      except Exception:
        continue
  finally:
    scene.camera = orig_cam
    scene.render.engine = orig_engine
    scene.render.resolution_x = orig_res_x
    scene.render.resolution_y = orig_res_y
    scene.render.filepath = orig_filepath
    for obj in temp_objs:
      if obj.name in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for d in temp_data:
      if isinstance(d, bpy.types.Camera) and d.name in bpy.data.cameras:
        bpy.data.cameras.remove(d)
      elif isinstance(d, bpy.types.Light) and d.name in bpy.data.lights:
        bpy.data.lights.remove(d)

  return None


def generate_gate00_qa_review_image(
    terrain_obj: bpy.types.Object,
    coast_pts: Sequence[Tuple[float, float]],
    boundary_edges_world: Sequence[Tuple[Vector, Vector]],
    inspection_data: Dict[str, Any],
    mask_report: Dict[str, Any],
    grids: Dict[str, np.ndarray],
    out_png_path: Path,
) -> Dict[str, Any]:
  """生成 2000x1200 的 Gate 00 地形 QA 综合复核图：

  左幅：真实地形正交俯视高程晕渲 + 海岸边界 + 实际网格开放边；
  右幅：真实地形 + valley_mask (青蓝) + buildable_mask (亮绿) 生态遮罩叠加俯视图 + 3D 渲染缩略图与指标面板。
  """
  out_png_path.parent.mkdir(parents=True, exist_ok=True)

  width, height = 2000, 1200
  canvas = np.zeros((height, width, 4), dtype=np.float32)
  # 深海蓝灰背景
  canvas[:, :, 0] = 0.08
  canvas[:, :, 1] = 0.11
  canvas[:, :, 2] = 0.15
  canvas[:, :, 3] = 1.0

  xs_grid = grids["xs_grid"]
  ys_grid = grids["ys_grid"]
  valid_grid = grids["valid_grid"]
  z_grid = grids["z_grid"]
  nx_grid = grids["normal_x_grid"]
  ny_grid = grids["normal_y_grid"]
  nz_grid = grids["normal_z_grid"]
  valley_grid = grids["valley_grid"]
  buildable_grid = grids["buildable_grid"]

  min_x, max_x = float(xs_grid[0]), float(xs_grid[-1])
  min_y, max_y = float(ys_grid[0]), float(ys_grid[-1])
  span_x = max(1.0, max_x - min_x)
  span_y = max(1.0, max_y - min_y)

  # 太阳光照方向用于地形法线明暗晕渲
  light_dir = np.array([-0.48, -0.45, 0.75], dtype=np.float64)
  light_dir /= np.linalg.norm(light_dir)

  def render_map_into_rect(
      rect_x0: int,
      rect_y0: int,
      rect_w: int,
      rect_h: int,
      overlay_masks: bool,
  ) -> Tuple[float, float, float]:
    """将采样栅格与海岸线/开放边绘制到指定矩形框内，返回 (scale_px_per_m, origin_px_x, origin_px_y)。"""
    pad = 36
    avail_w = rect_w - 2 * pad
    avail_h = rect_h - 2 * pad
    scale = min(avail_w / span_x, avail_h / span_y)
    draw_w = int(round(span_x * scale))
    draw_h = int(round(span_y * scale))
    ox = rect_x0 + (rect_w - draw_w) // 2
    oy = rect_y0 + (rect_h - draw_h) // 2

    # 面板底色（深海水色）
    canvas[rect_y0 : rect_y0 + rect_h, rect_x0 : rect_x0 + rect_w, 0] = 0.06
    canvas[rect_y0 : rect_y0 + rect_h, rect_x0 : rect_x0 + rect_w, 1] = 0.14
    canvas[rect_y0 : rect_y0 + rect_h, rect_x0 : rect_x0 + rect_w, 2] = 0.21

    # 向量化重采样到像素网格
    py_indices = np.arange(draw_h, dtype=np.float64)
    px_indices = np.arange(draw_w, dtype=np.float64)
    wx = min_x + (px_indices / max(1, draw_w - 1)) * span_x
    wy = min_y + (py_indices / max(1, draw_h - 1)) * span_y

    ix = np.clip(
        np.round((wx - min_x) / (xs_grid[1] - xs_grid[0])).astype(np.int32),
        0,
        len(xs_grid) - 1,
    )
    iy = np.clip(
        np.round((wy - min_y) / (ys_grid[1] - ys_grid[0])).astype(np.int32),
        0,
        len(ys_grid) - 1,
    )

    iy_2d, ix_2d = np.meshgrid(iy, ix, indexing="ij")
    v_mask = valid_grid[iy_2d, ix_2d]
    z_sub = np.where(v_mask, z_grid[iy_2d, ix_2d], 0.0)
    nx_sub = nx_grid[iy_2d, ix_2d]
    ny_sub = ny_grid[iy_2d, ix_2d]
    nz_sub = nz_grid[iy_2d, ix_2d]
    val_sub = valley_grid[iy_2d, ix_2d]
    bld_sub = buildable_grid[iy_2d, ix_2d]

    shade = np.clip(
        nx_sub * light_dir[0] + ny_sub * light_dir[1] + nz_sub * light_dir[2],
        0.22,
        1.05,
    )

    # 基于高程的分层设色（礁岸 -> 低坡草地 -> 中坡林地 -> 高山裸岩）
    r_col = np.full_like(z_sub, 0.06)
    g_col = np.full_like(z_sub, 0.14)
    b_col = np.full_like(z_sub, 0.21)

    t_low = np.clip(z_sub / 55.0, 0.0, 1.0)
    t_high = np.clip((z_sub - 55.0) / 150.0, 0.0, 1.0)

    land_r = np.where(
        z_sub < 55.0,
        0.26 + 0.10 * t_low,
        0.36 + 0.22 * t_high,
    )
    land_g = np.where(
        z_sub < 55.0,
        0.38 + 0.14 * t_low,
        0.52 - 0.06 * t_high,
    )
    land_b = np.where(
        z_sub < 55.0,
        0.24 + 0.06 * t_low,
        0.30 + 0.16 * t_high,
    )

    # 20m 等高线微暗刻线
    contour_20m = np.abs((z_sub % 20.0) - 10.0) < 0.75
    contour_factor = np.where(contour_20m & v_mask, 0.84, 1.0)

    r_col = np.where(v_mask, np.clip(land_r * shade * contour_factor, 0.0, 1.0), r_col)
    g_col = np.where(v_mask, np.clip(land_g * shade * contour_factor, 0.0, 1.0), g_col)
    b_col = np.where(v_mask, np.clip(land_b * shade * contour_factor, 0.0, 1.0), b_col)

    if overlay_masks:
      # 叠加 valley_mask (青蓝色半透明)
      v_alpha = np.clip(val_sub * 0.58, 0.0, 0.65) * v_mask
      r_col = r_col * (1.0 - v_alpha) + 0.12 * v_alpha
      g_col = g_col * (1.0 - v_alpha) + 0.76 * v_alpha
      b_col = b_col * (1.0 - v_alpha) + 0.96 * v_alpha

      # 叠加 buildable_mask (亮黄绿半透明)
      b_alpha = np.clip(bld_sub * 0.68, 0.0, 0.75) * v_mask
      r_col = r_col * (1.0 - b_alpha) + 0.96 * b_alpha
      g_col = g_col * (1.0 - b_alpha) + 0.86 * b_alpha
      b_col = b_col * (1.0 - b_alpha) + 0.15 * b_alpha

      # 绘制 valley_mask = 0.15 与 buildable_mask = 0.50 边界高亮等值线
      v_edge = (val_sub >= 0.14) & (val_sub <= 0.22) & v_mask
      b_edge = (bld_sub >= 0.45) & (bld_sub <= 0.56) & v_mask
      r_col = np.where(v_edge, 0.05, r_col)
      g_col = np.where(v_edge, 0.95, g_col)
      b_col = np.where(v_edge, 1.00, b_col)
      r_col = np.where(b_edge, 1.00, r_col)
      g_col = np.where(b_edge, 0.28, g_col)
      b_col = np.where(b_edge, 0.10, b_col)

    canvas[oy : oy + draw_h, ox : ox + draw_w, 0] = r_col
    canvas[oy : oy + draw_h, ox : ox + draw_w, 1] = g_col
    canvas[oy : oy + draw_h, ox : ox + draw_w, 2] = b_col

    # 绘制原点十字坐标轴 (X=0, Y=0)
    zero_px = int(round(ox + (0.0 - min_x) * scale))
    zero_py = int(round(oy + (0.0 - min_y) * scale))
    if ox <= zero_px < ox + draw_w:
      canvas[oy : oy + draw_h, zero_px : zero_px + 1, :3] = 0.45
    if oy <= zero_py < oy + draw_h:
      canvas[zero_py : zero_py + 1, ox : ox + draw_w, :3] = 0.45

    if not overlay_masks:
      # 左图：绘制实际网格开放边界边 (boundary_edges_world) 与 coast_polygon(9)
      for v0, v1 in boundary_edges_world:
        px0 = ox + (v0.x - min_x) * scale
        py0 = oy + (v0.y - min_y) * scale
        px1 = ox + (v1.x - min_x) * scale
        py1 = oy + (v1.y - min_y) * scale
        draw_segment_on_canvas(canvas, px0, py0, px1, py1, (1.0, 0.58, 0.14), radius=1)
    else:
      # 右图：绘制 coast_polygon(9) 白色参考海岸线
      n_c = len(coast_pts)
      for i in range(n_c):
        cx0, cy0 = coast_pts[i]
        cx1, cy1 = coast_pts[(i + 1) % n_c]
        px0 = ox + (cx0 - min_x) * scale
        py0 = oy + (cy0 - min_y) * scale
        px1 = ox + (cx1 - min_x) * scale
        py1 = oy + (cy1 - min_y) * scale
        draw_segment_on_canvas(canvas, px0, py0, px1, py1, (0.95, 0.95, 0.95), radius=1)

    return scale, float(ox), float(oy)

  # 绘制左右两个主俯视 QA 面板
  render_map_into_rect(30, 80, 680, 980, overlay_masks=False)
  render_map_into_rect(730, 80, 680, 980, overlay_masks=True)

  # 右侧第 3 栏：3D 斜视真实渲染面板 + 关键 QA 指标文本
  oblique_w, oblique_h = 530, 420
  temp_render_file = out_png_path.parent / "_temp_gate00_oblique.png"
  oblique_pixels = try_render_3d_oblique_panel(
      terrain_obj=terrain_obj,
      world_bbox_min=inspection_data["dimensions_and_bounds"]["world_bbox_min"],
      world_bbox_max=inspection_data["dimensions_and_bounds"]["world_bbox_max"],
      panel_w=oblique_w,
      panel_h=oblique_h,
      temp_png_path=temp_render_file,
  )
  rx0, ry0 = 1435, 640
  if oblique_pixels is not None:
    canvas[ry0 : ry0 + oblique_h, rx0 : rx0 + oblique_w, :] = oblique_pixels

  # 顶部标题与各面板图例标注
  draw_text_on_canvas(
      canvas,
      "GATE 00 QA REVIEW : ISLANDREFERENCE_V2 (READ-ONLY BENCHMARK)",
      35,
      22,
      (0.96, 0.98, 1.0),
      scale=3,
  )
  draw_text_on_canvas(
      canvas,
      "1. TOPOGRAPHY + MESH OPEN COAST BOUNDARY (ORANGE)",
      45,
      105,
      (1.0, 0.78, 0.35),
      scale=2,
  )
  draw_text_on_canvas(
      canvas,
      "2. MASKS: VALLEY (CYAN) + BUILDABLE (LIME)",
      745,
      105,
      (0.45, 0.95, 0.95),
      scale=2,
  )
  draw_text_on_canvas(
      canvas,
      "3. 3D SCENE RENDER & QA METRICS",
      1440,
      105,
      (0.92, 0.95, 1.0),
      scale=2,
  )

  # 右下角绘制实测 QA 数据摘要卡
  topo = inspection_data["topology_verification"]
  m_stats = inspection_data["mesh_statistics"]
  b_stats = inspection_data["dimensions_and_bounds"]
  v_core = mask_report["valley_mask_effective_gt_0_15"]
  b_core = mask_report["buildable_mask_core_gt_0_50"]

  summary_lines = [
      f"BLENDER : {bpy.app.version_string}",
      f"OBJECT  : {inspection_data['object_name']}",
      f"VERTS   : {m_stats['vertex_count']}   TRIS : {m_stats['triangle_count']}",
      f"EDGES   : {m_stats['edge_count']}   MATS : {m_stats['material_slot_count']}",
      f"SPAN XY : {b_stats['world_span_xyz_m'][0]:.1f} X {b_stats['world_span_xyz_m'][1]:.1f} M",
      f"ELEV Z  : {b_stats['world_bbox_min'][2]:.2f} TO {b_stats['world_bbox_max'][2]:.2f} M",
      f"COAST SEGMENTS EXPECTED : {topo['expected_coast_polygon_segments']}",
      f"ACTUAL BOUNDARY EDGES   : {topo['actual_boundary_edges']}",
      f"BOUNDARY MATCH          : {topo['boundary_matches_expected_coast']}",
      f"NON-MANIFOLD INTERNAL   : {topo['non_boundary_non_manifold_edges']}",
      f"VALLEY MASK (>0.15)     : {v_core['estimated_area_hectares']:.2f} HA",
      f"VALLEY SPAN XY          : {v_core['xy_span_m'][0]:.0f} X {v_core['xy_span_m'][1]:.0f} M",
      f"BUILDABLE MASK (>0.50)  : {b_core['estimated_area_hectares']:.2f} HA",
      f"BUILDABLE SPAN XY       : {b_core['xy_span_m'][0]:.0f} X {b_core['xy_span_m'][1]:.0f} M",
      "SW CORRIDOR : DEFERRED TO FINAL ASSEMBLY",
  ]
  text_top_y = 600
  for idx, line in enumerate(summary_lines):
    draw_text_on_canvas(
        canvas,
        line,
        1440,
        text_top_y + idx * 32,
        (0.88, 0.94, 0.98),
        scale=2,
    )

  # 通过 bpy.data.images 保存 PNG
  img_name = "_Gate00_QA_Sheet"
  if img_name in bpy.data.images:
    bpy.data.images.remove(bpy.data.images[img_name])
  bl_img = bpy.data.images.new(
      name=img_name, width=width, height=height, alpha=True
  )
  bl_img.pixels.foreach_set(canvas.ravel())
  bl_img.filepath_raw = str(out_png_path)
  bl_img.file_format = "PNG"
  bl_img.save()
  bpy.data.images.remove(bl_img)

  if not out_png_path.exists() or out_png_path.stat().st_size <= 1024:
    raise RuntimeError(f"保存 Gate 00 QA 预览图失败: {out_png_path}")

  return {
      "path": str(out_png_path),
      "size_bytes": out_png_path.stat().st_size,
      "resolution": [width, height],
      "includes_3d_render_panel": oblique_pixels is not None,
  }


# ==============================================================================
# 6. 主入口：执行只读复核、生成交付物并输出 QA 报告
# ==============================================================================


def main() -> None:
  # 1. 验证所有源文件与模块存在
  v2_mod, landform_mod, _lookdev_mod = verify_required_inputs_and_import_modules()

  # 仅使用 mkdir 创建输出目录，绝不删除或清空任何已有目录
  OUT_TERRAIN_DIR.mkdir(parents=True, exist_ok=True)
  OUT_PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
  OUT_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

  # 2. 先将源 Blend 原样复制为只读交付副本 Terrain/IslandReference_V2.blend
  blend_copy_info = copy_readonly_source_blend(
      SOURCE_BLEND_PATH, OUT_BLEND_PATH
  )

  # 3. 在 Blender 中打开源 Blend（只读检视，绝不写回源 Blend）
  bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND_PATH))

  # 4. 检查 IslandReference_V2 网格属性与 bmesh 海岸边界拓扑
  (
      terrain_obj,
      bvh,
      coast_pts,
      boundary_edges_world,
      inspection_data,
  ) = inspect_terrain_object_and_topology(v2_mod, landform_mod)

  # 5. 单独选中 IslandReference_V2 导出 Terrain/IslandReference_V2.fbx
  fbx_export_info = export_terrain_only_fbx(terrain_obj, OUT_FBX_PATH)

  # 6. 采样 terrain_fields(x, y) 核验 valley_mask 与 buildable_mask
  mask_report, grids = sample_ecological_masks_and_surface(
      bvh=bvh,
      landform_mod=landform_mod,
      world_bbox_min=inspection_data["dimensions_and_bounds"]["world_bbox_min"],
      world_bbox_max=inspection_data["dimensions_and_bounds"]["world_bbox_max"],
      step_m=MASK_SAMPLE_STEP_M,
  )

  # 7. 生成 Gate 00 地形 + 遮罩 QA 预览图 Previews/Gate00_Terrain_Review.png
  preview_info = generate_gate00_qa_review_image(
      terrain_obj=terrain_obj,
      coast_pts=coast_pts,
      boundary_edges_world=boundary_edges_world,
      inspection_data=inspection_data,
      mask_report=mask_report,
      grids=grids,
      out_png_path=OUT_PREVIEW_PNG_PATH,
  )

  # 8. 组装并写入 Reports/Gate00_terrain_qa.json
  qa_report: Dict[str, Any] = {
      "gate": "Gate 00 - IslandReference_V2 Terrain Benchmark Read-Only Review",
      "generated_at_utc": (
          datetime.datetime.now(datetime.timezone.utc).isoformat()
      ),
      "blender_version": bpy.app.version_string,
      "blender_version_tuple": list(bpy.app.version),
      "read_only_compliance": {
          "source_assets_modified": False,
          "terrain_rebuilt_or_validated_in_place": False,
          "southwest_corridor_note": (
              "走廊轨迹留待总装阶段依据实际网格高程/坡度提取并人工确认"
          ),
      },
      "source_files": {
          "source_blend": {
              "path": str(SOURCE_BLEND_PATH),
              "size_bytes": SOURCE_BLEND_PATH.stat().st_size,
          },
          "source_fbx": {
              "path": str(SOURCE_FBX_PATH),
              "size_bytes": SOURCE_FBX_PATH.stat().st_size,
          },
          "module_build_v2": {
              "path": str(MOD_V2_PATH),
              "size_bytes": MOD_V2_PATH.stat().st_size,
          },
          "module_landform": {
              "path": str(MOD_LANDFORM_PATH),
              "size_bytes": MOD_LANDFORM_PATH.stat().st_size,
          },
          "module_lookdev": {
              "path": str(MOD_LOOKDEV_PATH),
              "size_bytes": MOD_LOOKDEV_PATH.stat().st_size,
          },
      },
      "terrain_inspection": inspection_data,
      "ecological_mask_verification": mask_report,
      "deliverables": {
          "terrain_blend_readonly_copy": blend_copy_info,
          "terrain_only_fbx": fbx_export_info,
          "qa_review_preview_png": preview_info,
          "qa_report_json": {
              "path": str(OUT_REPORT_JSON_PATH),
          },
      },
  }

  OUT_REPORT_JSON_PATH.write_text(
      json.dumps(qa_report, ensure_ascii=False, indent=2),
      encoding="utf-8",
  )
  qa_report["deliverables"]["qa_report_json"][
      "size_bytes"
  ] = OUT_REPORT_JSON_PATH.stat().st_size
  OUT_REPORT_JSON_PATH.write_text(
      json.dumps(qa_report, ensure_ascii=False, indent=2),
      encoding="utf-8",
  )

  # 9. 最终交付物完整性校验与控制台摘要打印
  deliverable_paths = [
      OUT_BLEND_PATH,
      OUT_FBX_PATH,
      OUT_PREVIEW_PNG_PATH,
      OUT_REPORT_JSON_PATH,
  ]
  for d_path in deliverable_paths:
    if not d_path.exists() or d_path.stat().st_size <= 0:
      raise RuntimeError(f"Gate 00 交付物缺失或为空文件: {d_path}")

  m_stats = inspection_data["mesh_statistics"]
  b_stats = inspection_data["dimensions_and_bounds"]
  topo = inspection_data["topology_verification"]
  v_eff = mask_report["valley_mask_effective_gt_0_15"]
  b_core = mask_report["buildable_mask_core_gt_0_50"]

  print("=" * 78)
  print("Gate 00 : IslandReference_V2 现有地形基准只读复核完成")
  print("=" * 78)
  print(f"Blender 版本              : {bpy.app.version_string}")
  print(f"源 Blend 路径             : {SOURCE_BLEND_PATH}")
  print(
      f"地形尺寸 (World Span XYZ) : {b_stats['world_span_xyz_m'][0]}m x "
      f"{b_stats['world_span_xyz_m'][1]}m x {b_stats['world_span_xyz_m'][2]}m"
  )
  print(
      f"网格统计                  : 顶点={m_stats['vertex_count']}, "
      f"三角面={m_stats['triangle_count']}, 边={m_stats['edge_count']}, "
      f"材质槽={m_stats['material_slot_count']}"
  )
  print(
      f"海岸开放边界核验          : 预期段数={topo['expected_coast_polygon_segments']}, "
      f"实际开放边={topo['actual_boundary_edges']}, "
      f"一致={topo['boundary_matches_expected_coast']}"
  )
  print(
      f"非边界非流形边数          : {topo['non_boundary_non_manifold_edges']} "
      f"(内部流形洁净={topo['internal_manifold_clean']})"
  )
  print(
      f"valley_mask (>0.15)       : 面积≈{v_eff['estimated_area_hectares']} ha "
      f"({v_eff['estimated_area_m2']} m²), 跨度={v_eff['xy_span_m']} m"
  )
  print(
      f"buildable_mask (>0.50)    : 面积≈{b_core['estimated_area_hectares']} ha "
      f"({b_core['estimated_area_m2']} m²), 跨度={b_core['xy_span_m']} m"
  )
  print(
      f"西南走廊说明              : {mask_report['southwest_rescue_corridor']['note']}"
  )
  print("-" * 78)
  print("Gate 00 交付物输出路径:")
  for d_path in deliverable_paths:
    print(f"  -> {d_path} ({d_path.stat().st_size} bytes)")
  print("=" * 78)


if __name__ == "__main__":
  main()
