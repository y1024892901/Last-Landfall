import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from pathlib import Path

# ---------------------------------------------------------
# 初始化和清理
# ---------------------------------------------------------
SCHOOL_COL_NAME = "School_DeepSeek"
HELPERS_COL_NAME = "Helpers_School_DeepSeek"
MAT_PREFIX = "School_DeepSeek_"

def clean_previous():
    # 清理旧集合
    for col_name in [SCHOOL_COL_NAME, HELPERS_COL_NAME]:
        if col_name in bpy.data.collections:
            col = bpy.data.collections[col_name]
            for obj in list(col.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(col)
            
    # 清理无用户材质
    for mat in list(bpy.data.materials):
        if mat.name.startswith(MAT_PREFIX) and mat.users == 0:
            bpy.data.materials.remove(mat)

clean_previous()

# ---------------------------------------------------------
# 目录创建（脚本从任意工作目录运行时仍指向项目根目录）
# ---------------------------------------------------------
base_path = Path(__file__).resolve().parents[2]
paths = {
    "blend": base_path / "Assets/LastLandfall/Art/Source/Buildings",
    "fbx": base_path / "Assets/LastLandfall/Resources/Models/Buildings",
    "preview": base_path / "Assets/LastLandfall/Art/Previews/Buildings",
    "renders": base_path / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"
}
for p in paths.values():
    p.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# 集合创建
# ---------------------------------------------------------
school_col = bpy.data.collections.new(SCHOOL_COL_NAME)
bpy.context.scene.collection.children.link(school_col)

helpers_col = bpy.data.collections.new(HELPERS_COL_NAME)
bpy.context.scene.collection.children.link(helpers_col)

# ---------------------------------------------------------
# 材质创建
# ---------------------------------------------------------
def create_mat(name, base_color, metallic=0.0, roughness=0.5, transmission=0.0):
    mat = bpy.data.materials.new(name=f"{MAT_PREFIX}{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = base_color
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        if 'Transmission Weight' in bsdf.inputs:
            bsdf.inputs['Transmission Weight'].default_value = transmission
    return mat

mat_wood_wall = create_mat("Wood_Wall", (0.55, 0.4, 0.25, 1.0), 0.0, 0.8)
mat_wood_struct = create_mat("Wood_Struct", (0.2, 0.15, 0.1, 1.0), 0.0, 0.9)
mat_metal_roof = create_mat("Metal_Roof", (0.2, 0.4, 0.3, 1.0), 0.6, 0.5)
mat_metal_patch = create_mat("Metal_Patch", (0.3, 0.35, 0.35, 1.0), 0.5, 0.6)
mat_stone = create_mat("Stone", (0.6, 0.6, 0.6, 1.0), 0.0, 0.9)
mat_glass = create_mat("Glass", (0.2, 0.3, 0.4, 1.0), 0.0, 0.1, 0.8)
mat_board = create_mat("Board", (0.6, 0.4, 0.2, 1.0), 0.0, 0.7)

mat_light = bpy.data.materials.new(name=f"{MAT_PREFIX}Light")
mat_light.use_nodes = True
bsdf = mat_light.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs['Base Color'].default_value = (1.0, 0.8, 0.5, 1.0)
    bsdf.inputs['Emission Color'].default_value = (1.0, 0.8, 0.5, 1.0)
    bsdf.inputs['Emission Strength'].default_value = 5.0

# ---------------------------------------------------------
# 辅助建模函数
# ---------------------------------------------------------
def create_box(name, loc, size, mat, collection, bevel=0.01):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    if bevel > 0 and min(size) > bevel * 2:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=1, profile=0.7, affect='EDGES')
    bm.to_mesh(mesh)
    bm.free()
    
    if mat:
        obj.data.materials.append(mat)
    return obj

def create_cylinder(name, loc, radius, depth, mat, collection, segments=12, axis="Z"):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius, depth=depth)
    if axis == "X":
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=bm.verts)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    
    if mat:
        obj.data.materials.append(mat)
    return obj

def create_oriented_box(name, loc, size, mat, collection, rotation_x=0.0, bevel=0.0):
    """Create a box around its local origin, rotate it, then place it in world space."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=1, profile=0.7, affect='EDGES')
    if rotation_x:
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rotation_x, 3, 'X'), verts=bm.verts)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    if mat:
        obj.data.materials.append(mat)
    return obj

def create_roof_gable(name, x_center, depth, y_front, y_back, ridge_y, eave_z, ridge_z, mat, collection):
    """Create a closed triangular gable in the Y/Z elevation at a building end."""
    half_depth = depth * 0.5
    x_left = x_center - half_depth
    x_right = x_center + half_depth
    verts = [
        (x_left,  y_front, eave_z),
        (x_left,  y_back,  eave_z),
        (x_left,  ridge_y, ridge_z),
        (x_right, y_front, eave_z),
        (x_right, y_back,  eave_z),
        (x_right, ridge_y, ridge_z),
    ]
    faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (0, 2, 5, 3), (1, 4, 5, 2)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate(clean_customdata=False)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj

def create_roof_strip(name, x_center, y_center, z_center, width, length, angle, mat, collection, thickness=0.035):
    return create_oriented_box(
        name,
        (x_center, y_center, z_center),
        (width, length, thickness),
        mat,
        collection,
        rotation_x=angle,
        bevel=0.0,
    )

# ---------------------------------------------------------
# 建模：基座结构
# ---------------------------------------------------------
# 石墩 (Z=0 to 0.4)
pier_locs = []
for x in [-3.4, -1.7, 0, 1.7, 3.4]:
    for y in [-1.8, 0.2, 2.0]:
        pier_locs.append((x, y, 0.2))
for x in [-1.2, 0, 1.2]:
    pier_locs.append((x, -3.0, 0.2))

for i, loc in enumerate(pier_locs):
    create_cylinder(f"StonePier_{i}", loc, 0.15, 0.4, mat_stone, school_col)

# 木梁 (Z=0.4 to 0.6)
for i, y in enumerate([-1.8, 0.2, 2.0]):
    create_box(f"Beam_Main_{i}", (0, y, 0.5), (7.2, 0.2, 0.2), mat_wood_struct, school_col)
for i, x in enumerate([-1.2, 0, 1.2]):
    create_box(f"Beam_Porch_{i}", (x, -3.0, 0.5), (0.2, 1.6, 0.2), mat_wood_struct, school_col)

# 地板 (Z=0.6 to 0.7)
create_box("Floor_Main", (0, 0.1, 0.65), (7.2, 4.0, 0.1), mat_wood_struct, school_col)
create_box("Floor_Porch", (0, -2.5, 0.65), (2.4, 1.2, 0.1), mat_wood_struct, school_col)

# ---------------------------------------------------------
# 建模：主体墙和框架
# ---------------------------------------------------------
# 角柱
for x in [-3.5, 3.5]:
    for y in [-1.9, 2.1]:
        create_box(f"Post_Corner_{x}_{y}", (x, y, 1.8), (0.2, 0.2, 2.2), mat_wood_struct, school_col)

# 前墙 (Y = -1.9)
create_box("Wall_Front_L", (-2.1, -1.9, 1.8), (2.8, 0.1, 2.2), mat_wood_wall, school_col)
create_box("Wall_Front_R", (2.1, -1.9, 1.8), (2.8, 0.1, 2.2), mat_wood_wall, school_col)
create_box("Wall_Front_Top", (0, -1.9, 2.8), (1.4, 0.1, 0.2), mat_wood_wall, school_col)

# 后墙 (Y = 2.1)
create_box("Wall_Back_L", (-2.4, 2.1, 1.8), (2.2, 0.1, 2.2), mat_wood_wall, school_col)
create_box("Wall_Back_R", (2.4, 2.1, 1.8), (2.2, 0.1, 2.2), mat_wood_wall, school_col)
create_box("Wall_Back_Mid", (0, 2.1, 1.8), (0.6, 0.1, 2.2), mat_wood_wall, school_col)
create_box("Wall_Back_Bot1", (-0.8, 2.1, 1.1), (1.0, 0.1, 0.8), mat_wood_wall, school_col)
create_box("Wall_Back_Top1", (-0.8, 2.1, 2.5), (1.0, 0.1, 0.8), mat_wood_wall, school_col)
create_box("Wall_Back_Bot2", (0.8, 2.1, 1.1), (1.0, 0.1, 0.8), mat_wood_wall, school_col)
create_box("Wall_Back_Top2", (0.8, 2.1, 2.5), (1.0, 0.1, 0.8), mat_wood_wall, school_col)

# 侧墙 X = 3.5 和 X = -3.5
for side in [-1, 1]:
    sx = 3.5 * side
    # 分段构建
    create_box(f"Wall_Side_{side}_1", (sx, -1.6, 1.8), (0.1, 0.6, 2.2), mat_wood_wall, school_col)
    create_box(f"Wall_Side_{side}_2", (sx, 0, 1.8), (0.1, 0.2, 2.2), mat_wood_wall, school_col)
    create_box(f"Wall_Side_{side}_3", (sx, 1.6, 1.8), (0.1, 0.6, 2.2), mat_wood_wall, school_col)
    # 窗洞下方和上方
    create_box(f"Wall_Side_{side}_Bot1", (sx, -0.7, 0.95), (0.1, 1.2, 0.5), mat_wood_wall, school_col)
    create_box(f"Wall_Side_{side}_Top1", (sx, -0.7, 2.55), (0.1, 1.2, 0.7), mat_wood_wall, school_col)
    create_box(f"Wall_Side_{side}_Bot2", (sx, 0.7, 0.95), (0.1, 1.2, 0.5), mat_wood_wall, school_col)
    create_box(f"Wall_Side_{side}_Top2", (sx, 0.7, 2.55), (0.1, 1.2, 0.7), mat_wood_wall, school_col)

# 顶部横梁
create_box("Beam_Top_Front", (0, -1.9, 2.9), (7.0, 0.15, 0.15), mat_wood_struct, school_col)
create_box("Beam_Top_Back", (0, 2.1, 2.9), (7.0, 0.15, 0.15), mat_wood_struct, school_col)
for side in [-1, 1]:
    create_box(f"Beam_Top_Side_{side}", (3.5 * side, 0.1, 2.9), (0.15, 4.0, 0.15), mat_wood_struct, school_col)

# 人字屋顶的两个端墙，位于左右立面（屋脊沿 X）。
create_roof_gable("Gable_Left", -3.5, 0.10, -3.3, 2.3, -0.5, 2.8, 3.55, mat_wood_wall, school_col)
create_roof_gable("Gable_Right", 3.5, 0.10, -3.3, 2.3, -0.5, 2.8, 3.55, mat_wood_wall, school_col)

# ---------------------------------------------------------
# 建模：门窗
# ---------------------------------------------------------
# 前门
create_box("Door_Frame_L", (-0.65, -1.9, 1.7), (0.1, 0.15, 2.0), mat_wood_struct, school_col)
create_box("Door_Frame_R", (0.65, -1.9, 1.7), (0.1, 0.15, 2.0), mat_wood_struct, school_col)
create_box("Door_Frame_Top", (0, -1.9, 2.7), (1.4, 0.15, 0.1), mat_wood_struct, school_col)

create_box("Door_Left", (-0.3, -1.95, 1.65), (0.55, 0.05, 1.9), mat_wood_wall, school_col)
create_box("Door_Right", (0.3, -1.95, 1.65), (0.55, 0.05, 1.9), mat_wood_wall, school_col)
create_cylinder("Door_Handle", (-0.1, -2.0, 1.6), 0.02, 0.1, mat_metal_patch, school_col, 8)

# 侧窗
for side in [-1, 1]:
    sx = 3.5 * side
    for y_ctr in [-0.7, 0.7]:
        # 玻璃
        create_box(f"Glass_{side}_{y_ctr}", (sx, y_ctr, 1.7), (0.02, 1.0, 0.9), mat_glass, school_col, bevel=0.0)
        # 窗框
        create_box(f"Win_Frame_T_{side}_{y_ctr}", (sx, y_ctr, 2.15), (0.15, 1.1, 0.1), mat_wood_struct, school_col)
        create_box(f"Win_Frame_B_{side}_{y_ctr}", (sx, y_ctr, 1.25), (0.15, 1.1, 0.1), mat_wood_struct, school_col)
        create_box(f"Win_Frame_L_{side}_{y_ctr}", (sx, y_ctr - 0.5, 1.7), (0.15, 0.1, 0.9), mat_wood_struct, school_col)
        create_box(f"Win_Frame_R_{side}_{y_ctr}", (sx, y_ctr + 0.5, 1.7), (0.15, 0.1, 0.9), mat_wood_struct, school_col)
        # 中梃
        create_box(f"Win_Mullion_V_{side}_{y_ctr}", (sx, y_ctr, 1.7), (0.15, 0.05, 0.9), mat_wood_struct, school_col)
        create_box(f"Win_Mullion_H_{side}_{y_ctr}", (sx, y_ctr, 1.7), (0.15, 1.0, 0.05), mat_wood_struct, school_col)

# 后窗
for x_ctr in [-0.8, 0.8]:
    create_box(f"Glass_Back_{x_ctr}", (x_ctr, 2.1, 1.8), (0.8, 0.02, 0.6), mat_glass, school_col, bevel=0.0)
    create_box(f"Win_Back_Frame_T_{x_ctr}", (x_ctr, 2.1, 2.1), (0.9, 0.15, 0.1), mat_wood_struct, school_col)
    create_box(f"Win_Back_Frame_B_{x_ctr}", (x_ctr, 2.1, 1.5), (0.9, 0.15, 0.1), mat_wood_struct, school_col)
    create_box(f"Win_Back_Frame_L_{x_ctr}", (x_ctr - 0.4, 2.1, 1.8), (0.1, 0.15, 0.6), mat_wood_struct, school_col)
    create_box(f"Win_Back_Frame_R_{x_ctr}", (x_ctr + 0.4, 2.1, 1.8), (0.1, 0.15, 0.6), mat_wood_struct, school_col)

# ---------------------------------------------------------
# 建模：门廊、栏杆和台阶
# ---------------------------------------------------------
# 门廊柱子
for x in [-1.2, 1.2]:
    create_box(f"Porch_Post_{x}", (x, -3.0, 1.7), (0.16, 0.16, 2.0), mat_wood_struct, school_col)
    # 柱基
    create_box(f"Porch_Post_Base_{x}", (x, -3.0, 0.75), (0.25, 0.25, 0.1), mat_wood_struct, school_col)
    # 柱顶横梁
    create_box(f"Porch_Beam_{x}", (x, -3.0, 2.65), (0.2, 0.2, 0.12), mat_wood_struct, school_col)

# 栏杆
for x in [-1.2, 1.2]:
    # 扶手
    create_box(f"Railing_Top_{x}", (x, -2.5, 1.5), (0.1, 1.2, 0.1), mat_wood_struct, school_col)
    # 底档
    create_box(f"Railing_Bot_{x}", (x, -2.5, 0.85), (0.1, 1.2, 0.1), mat_wood_struct, school_col)
    # 竖条
    for y in [-2.1, -2.5, -2.9]:
        create_box(f"Railing_Spindle_{x}_{y}", (x, y, 1.15), (0.05, 0.05, 0.6), mat_wood_struct, school_col)

# 四级台阶：略有搭接，前缘保留在总深度限制以内。
step_depth = 0.24
step_run = 0.20
for i in range(4):
    z_top = 0.70 - i * 0.17
    y_center = -3.10 - step_depth * 0.5 - i * step_run
    create_box(f"Step_{i + 1}", (0, y_center, z_top - 0.085), (2.4, step_depth, 0.17), mat_wood_struct, school_col)

# 门廊顶部支撑框架，落在立柱上并收在屋面下方。
create_box("Porch_Roof_Beam_L", (-1.2, -2.5, 2.64), (0.16, 1.2, 0.12), mat_wood_struct, school_col)
create_box("Porch_Roof_Beam_R", (1.2, -2.5, 2.64), (0.16, 1.2, 0.12), mat_wood_struct, school_col)
create_box("Porch_Roof_Beam_F", (0, -3.08, 2.64), (2.4, 0.16, 0.12), mat_wood_struct, school_col)

# ---------------------------------------------------------
# 建模：屋顶
# ---------------------------------------------------------
# 对称人字屋面覆盖教室和门廊；脊高及屋檐高度均留在规格包络内。
roof_width = 7.34
ridge_y = -0.5
ridge_z = 3.55
eave_front_y = -3.3
eave_back_y = 2.3
eave_z = 2.8
half_run = ridge_y - eave_front_y  # 2.8 m；前后坡采用相同水平跨度。
slope_rise = ridge_z - eave_z
slope_length = math.sqrt(half_run ** 2 + slope_rise ** 2)
front_angle = math.atan2(slope_rise, half_run)
back_angle = math.atan2(-slope_rise, half_run)
strip_count = 31
strip_width = roof_width / strip_count
front_center_y = (eave_front_y + ridge_y) * 0.5
back_center_y = (ridge_y + eave_back_y) * 0.5
roof_center_z = (ridge_z + eave_z) * 0.5

for i in range(strip_count):
    x_center = -roof_width * 0.5 + strip_width * (i + 0.5)
    rib_lift = 0.006 if i % 2 == 0 else 0.0
    create_roof_strip(
        f"Roof_Front_{i:02d}", x_center, front_center_y, roof_center_z + rib_lift,
        strip_width * 0.995, slope_length, front_angle, mat_metal_roof, school_col,
    )
    create_roof_strip(
        f"Roof_Back_{i:02d}", x_center, back_center_y, roof_center_z + rib_lift,
        strip_width * 0.995, slope_length, back_angle, mat_metal_roof, school_col,
    )

# 屋脊盖板，长度和高度均受控。
create_box("Roof_Ridge", (0, ridge_y, ridge_z + 0.07), (7.30, 0.20, 0.12), mat_metal_roof, school_col)

# 两块贴合坡面的青灰色修补板。
patch_front_z = ridge_z - slope_rise * abs(-2.0 - ridge_y) / half_run + 0.025
patch_back_z = ridge_z - slope_rise * abs(1.15 - ridge_y) / half_run + 0.025
create_oriented_box("Roof_Patch_Front", (-2.0, -2.0, patch_front_z), (0.72, 0.82, 0.035), mat_metal_patch, school_col, rotation_x=front_angle)
create_oriented_box("Roof_Patch_Back", (2.0, 1.15, patch_back_z), (0.72, 0.82, 0.035), mat_metal_patch, school_col, rotation_x=back_angle)

# 前后排水沟沿 X 轴布置；在网格坐标中旋转后再平移，避免绕世界原点旋转。
create_cylinder("Gutter_Front", (0, eave_front_y, eave_z - 0.04), 0.07, 7.30, mat_metal_patch, school_col, 8, axis="X")
create_cylinder("Gutter_Back", (0, eave_back_y, eave_z - 0.04), 0.07, 7.30, mat_metal_patch, school_col, 8, axis="X")

# 右后角落水管与后檐沟相接。
create_cylinder("Downspout_Back_Right", (3.56, eave_back_y + 0.015, 1.73), 0.045, 1.90, mat_metal_patch, school_col, 8)

# ---------------------------------------------------------
# 建模：附件
# ---------------------------------------------------------
# 公告板 (门左侧 X=-2.0, Y=-1.95, Z=1.5)
create_box("Board_Frame", (-2.0, -1.95, 1.5), (0.9, 0.05, 0.7), mat_wood_struct, school_col)
create_box("Board_Panel", (-2.0, -1.98, 1.5), (0.8, 0.02, 0.6), mat_board, school_col)

# 暖色灯 (门廊柱子)
create_box("Light_Fixture", (1.15, -3.1, 2.4), (0.1, 0.2, 0.1), mat_wood_struct, school_col)
create_box("Light_Bulb", (1.15, -3.2, 2.3), (0.08, 0.08, 0.15), mat_light, school_col)

# ---------------------------------------------------------
# 应用变换并整理
# ---------------------------------------------------------
bpy.context.view_layer.update()

# 计算总包围盒用于诊断
total_meshes = 0
min_z = float('inf')
bbox_min = Vector((float('inf'), float('inf'), float('inf')))
bbox_max = Vector((float('-inf'), float('-inf'), float('-inf')))
non_manifold_edges = 0
loose_verts = 0

for obj in school_col.objects:
    if obj.type == 'MESH':
        total_meshes += 1
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ Vector(corner)
            min_z = min(min_z, world_corner.z)
            bbox_min.x = min(bbox_min.x, world_corner.x)
            bbox_min.y = min(bbox_min.y, world_corner.y)
            bbox_min.z = min(bbox_min.z, world_corner.z)
            bbox_max.x = max(bbox_max.x, world_corner.x)
            bbox_max.y = max(bbox_max.y, world_corner.y)
            bbox_max.z = max(bbox_max.z, world_corner.z)

        bm = bmesh.new()
        bm.from_mesh(obj.data)
        for edge in bm.edges:
            if not edge.is_manifold:
                non_manifold_edges += 1
        for vert in bm.verts:
            if not vert.link_edges:
                loose_verts += 1
        bm.free()

# ---------------------------------------------------------
# 相机和灯光设置 (辅助集合)
# ---------------------------------------------------------
scene = bpy.context.scene

# 备份环境设置
old_engine = scene.render.engine
old_res_x = scene.render.resolution_x
old_res_y = scene.render.resolution_y
old_res_percentage = scene.render.resolution_percentage
old_render_filepath = scene.render.filepath
old_file_format = scene.render.image_settings.file_format
old_film_transparent = scene.render.film_transparent
old_camera = scene.camera
old_world = scene.world

# 设置渲染引擎和基础参数
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except:
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except:
        scene.render.engine = 'CYCLES'

scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False

# 世界背景
world = bpy.data.worlds.new("Helper_World")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.2, 0.2, 0.2, 1.0)
    bg_node.inputs[1].default_value = 1.0

# 灯光
def create_light(name, loc, energy, size=5.0):
    light_data = bpy.data.lights.new(name=name, type='AREA')
    light_data.energy = energy
    light_data.size = size
    light_obj = bpy.data.objects.new(name, light_data)
    helpers_col.objects.link(light_obj)
    light_obj.location = loc
    # 指向中心
    direction = Vector((0, 0, 1.9)) - light_obj.location
    light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return light_obj

create_light("Key_Light", (5, -8, 8), 1500)
create_light("Fill_Light", (-5, -5, 5), 800)
create_light("Back_Light", (0, 8, 6), 1000)

# 相机
cam_data = bpy.data.cameras.new("Helper_Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 9.0
cam_obj = bpy.data.objects.new("Helper_Camera", cam_data)
helpers_col.objects.link(cam_obj)
scene.camera = cam_obj

# 定义渲染函数
def render_view(name, loc, rot):
    cam_obj.location = loc
    cam_obj.rotation_euler = rot
    scene.render.filepath = str(paths["renders"] / f"School_DeepSeek_{name}.png")
    bpy.ops.render.render(write_still=True)

# 六向正交渲染
center_z = 1.9
d = 12.0

render_view("Front", (0, -d, center_z), (math.radians(90), 0, 0))
render_view("Back", (0, d, center_z), (math.radians(90), 0, math.radians(180)))
render_view("Left", (-d, 0, center_z), (math.radians(90), 0, math.radians(-90)))
render_view("Right", (d, 0, center_z), (math.radians(90), 0, math.radians(90)))
render_view("Top", (0, 0, d), (0, 0, 0))
render_view("Bottom", (0, 0, -d), (math.radians(180), 0, 0))

# 三分之四预览渲染
cam_data.type = 'PERSP'
cam_data.lens = 50
cam_obj.location = (8, -10, 6)
direction = Vector((0, 0, 1.5)) - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene.render.filepath = str(paths["preview"] / "School_DeepSeek.png")
bpy.ops.render.render(write_still=True)

# 恢复相机
cam_data.type = 'ORTHO'
cam_obj.location = (0, -d, center_z)
cam_obj.rotation_euler = (math.radians(90), 0, 0)

# ---------------------------------------------------------
# 导出 FBX
# ---------------------------------------------------------
bpy.ops.object.select_all(action='DESELECT')
for obj in school_col.objects:
    if obj.type == 'MESH':
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

fbx_path = paths["fbx"] / "School_DeepSeek.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    object_types={'MESH'},
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Y',
    axis_up='Z'
)

# ---------------------------------------------------------
# 恢复环境并保存 Blend
# ---------------------------------------------------------
scene.render.engine = old_engine
scene.render.resolution_x = old_res_x
scene.render.resolution_y = old_res_y
scene.render.resolution_percentage = old_res_percentage
scene.render.filepath = old_render_filepath
scene.render.image_settings.file_format = old_file_format
scene.render.film_transparent = old_film_transparent
scene.camera = old_camera
scene.world = old_world

# 清理渲染辅助对象
for obj in list(helpers_col.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.data.collections.remove(helpers_col)

# 移除本脚本创建且已无用户的辅助数据块，避免把渲染临时数据留在 Blend 中。
if bpy.data.cameras.get("Helper_Camera") and bpy.data.cameras["Helper_Camera"].users == 0:
    bpy.data.cameras.remove(bpy.data.cameras["Helper_Camera"])
for light_name in ("Key_Light", "Fill_Light", "Back_Light"):
    light_data = bpy.data.lights.get(light_name)
    if light_data and light_data.users == 0:
        bpy.data.lights.remove(light_data)
helper_world = bpy.data.worlds.get("Helper_World")
if helper_world and helper_world.users == 0:
    bpy.data.worlds.remove(helper_world)

# 保存 Blend
blend_path = paths["blend"] / "School_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# ---------------------------------------------------------
# 打印诊断信息
# ---------------------------------------------------------
print("\n--- School_DeepSeek 诊断信息 ---")
print(f"Mesh 数量: {total_meshes}")
print(f"世界空间包围盒 (Min): {bbox_min.x:.2f}, {bbox_min.y:.2f}, {bbox_min.z:.2f}")
print(f"世界空间包围盒 (Max): {bbox_max.x:.2f}, {bbox_max.y:.2f}, {bbox_max.z:.2f}")
print(f"尺寸 (X, Y, Z): {bbox_max.x - bbox_min.x:.2f} x {bbox_max.y - bbox_min.y:.2f} x {bbox_max.z - bbox_min.z:.2f}")
print(f"最低 Z 值: {min_z:.4f}")
print(f"非流形边数: {non_manifold_edges}")
print(f"松散顶点数: {loose_verts}")
print("注意: 逐对象拓扑检查无法检测不同对象之间的穿插。")
print("--------------------------------\n")
