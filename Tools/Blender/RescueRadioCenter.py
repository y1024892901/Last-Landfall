# -*- coding: utf-8 -*-
"""
RescueRadioCenter_DeepSeek — Last Landfall 4级区域救援设施
Blender 5.2.2 生成脚本。从项目根目录运行。
只删除/替换 RescueRadioCenter_DeepSeek 与 Helpers_RescueRadioCenter_DeepSeek 两个集合。
不覆盖现有 RescueRadioCenter 原版资产。
"""

import bpy
import bmesh
import math
import mathutils
from pathlib import Path

# ===================== 路径 =====================
ROOT = Path.cwd()
OUT_BLEND = ROOT / "Assets" / "LastLandfall" / "Art" / "Source" / "Buildings" / "RescueRadioCenter_DeepSeek.blend"
OUT_FBX = ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Buildings" / "RescueRadioCenter_DeepSeek.fbx"
OUT_PREVIEW = ROOT / "Assets" / "LastLandfall" / "Art" / "Previews" / "Buildings" / "RescueRadioCenter_DeepSeek.png"
OUT_VIEWS = ROOT / "Assets" / "LastLandfall" / "Art" / "References" / "ScenarioBuildingViews" / "_renders"

for p in [OUT_BLEND.parent, OUT_FBX.parent, OUT_PREVIEW.parent, OUT_VIEWS]:
    p.mkdir(parents=True, exist_ok=True)

# ===================== 常量 =====================
MAIN_COL = "RescueRadioCenter_DeepSeek"
HELPER_COL = "Helpers_RescueRadioCenter_DeepSeek"
MAT_PREFIX = "RRC_"

# ===================== 清理专属集合与材质 =====================
old_mats = set()
for col_name in [MAIN_COL, HELPER_COL]:
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
        for obj in list(col.objects):
            if obj.type == 'MESH' and obj.data:
                for slot in obj.material_slots:
                    if slot.material and slot.material.name.startswith(MAT_PREFIX):
                        old_mats.add(slot.material)
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

for mat in old_mats:
    if mat and mat.name.startswith(MAT_PREFIX) and mat.users == 0:
        try:
            bpy.data.materials.remove(mat)
        except Exception:
            pass

# ===================== 集合 =====================
main_col = bpy.data.collections.new(MAIN_COL)
bpy.context.scene.collection.children.link(main_col)

helper_col = bpy.data.collections.new(HELPER_COL)
bpy.context.scene.collection.children.link(helper_col)

# ===================== Principled / Background 查找 =====================
def get_bsdf(mat):
    if not mat.use_nodes or not mat.node_tree:
        return None
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            return n
    return None

def get_bg(world):
    if not world.use_nodes or not world.node_tree:
        return None
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            return n
    return None

# ===================== 材质 =====================
def make_mat(name, color, rough=0.7, metallic=0.0, emission=None, emit_strength=4.0):
    mat = bpy.data.materials.new(MAT_PREFIX + name)
    mat.use_nodes = True
    bsdf = get_bsdf(mat)
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = rough
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if emission is not None:
            for key in ["Emission Color", "Emission"]:
                if key in bsdf.inputs:
                    try:
                        bsdf.inputs[key].default_value = (*emission, 1.0)
                    except Exception:
                        pass
                    break
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat

mat_wood_dark  = make_mat("WoodDark", (0.22, 0.16, 0.12), 0.92)
mat_wood_light = make_mat("WoodLight", (0.62, 0.55, 0.44), 0.85)
mat_sea_green  = make_mat("SeaGreen", (0.28, 0.48, 0.42), 0.50, 0.35)
mat_rust       = make_mat("Rust", (0.60, 0.26, 0.12), 0.80, 0.10)
mat_iron       = make_mat("Iron", (0.12, 0.12, 0.13), 0.55, 0.65)
mat_glass      = make_mat("StormGlass", (0.20, 0.35, 0.50), 0.15, 0.0)
mat_ivory      = make_mat("Ivory", (0.90, 0.87, 0.78), 0.60)
mat_amber      = make_mat("Amber", (1.0, 0.55, 0.10), 0.50, 0.0, (1.0, 0.55, 0.10), 6.0)
mat_seam       = make_mat("DarkSeam", (0.08, 0.08, 0.08), 0.85)

# ===================== 辅助函数 =====================
def _make_prism(name, verts, faces, mat, collection):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in verts]
    for f in faces:
        try:
            bm.faces.new([bm_verts[i] for i in f])
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    if mat:
        obj.data.materials.append(mat)
    collection.objects.link(obj)
    return obj

def make_box(name, x0, x1, y0, y1, z0, z1, mat, collection):
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (1, 5, 6, 2),
        (2, 6, 7, 3), (3, 7, 4, 0),
    ]
    return _make_prism(name, verts, faces, mat, collection)

def make_bar_between(name, p1, p2, width, mat, collection):
    p1v = mathutils.Vector(p1)
    p2v = mathutils.Vector(p2)
    direction = p2v - p1v
    length = direction.length
    if length < 1e-6:
        return None
    d = direction.normalized()
    up = mathutils.Vector((0, 0, 1))
    if abs(d.dot(up)) > 0.99:
        up = mathutils.Vector((0, 1, 0))
    perp1 = d.cross(up).normalized() * (width / 2)
    perp2 = d.cross(perp1).normalized() * (width / 2)
    verts = [
        p1v - perp1 - perp2, p1v + perp1 - perp2,
        p1v + perp1 + perp2, p1v - perp1 + perp2,
        p2v - perp1 - perp2, p2v + perp1 - perp2,
        p2v + perp1 + perp2, p2v - perp1 + perp2,
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (1, 5, 6, 2),
        (2, 6, 7, 3), (3, 7, 4, 0),
    ]
    return _make_prism(name, verts, faces, mat, collection)

def make_cylinder(name, radius, depth, loc, rot, mat, collection, seg=12):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg,
                          radius1=radius, radius2=radius, depth=depth)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = rot
    if mat:
        obj.data.materials.append(mat)
    collection.objects.link(obj)
    return obj

def make_cone(name, r1, r2, depth, loc, rot, mat, collection, seg=12):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg,
                          radius1=r1, radius2=r2, depth=depth)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = rot
    if mat:
        obj.data.materials.append(mat)
    collection.objects.link(obj)
    return obj

def make_icosphere(name, radius, loc, mat, collection, subdiv=1):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    if mat:
        obj.data.materials.append(mat)
    collection.objects.link(obj)
    return obj

def make_cable(name, p1, p2, radius, mat, collection):
    p1v = mathutils.Vector(p1)
    p2v = mathutils.Vector(p2)
    direction = p2v - p1v
    length = direction.length
    if length < 1e-6:
        return None
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6,
                          radius1=radius, radius2=radius, depth=length)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = (p1v + p2v) / 2
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    if mat:
        obj.data.materials.append(mat)
    collection.objects.link(obj)
    return obj

# ===================== 平台 =====================
# 四条支脚（Z=0 到 0.20）
for i, (lx, ly) in enumerate([(-0.88, -0.88), (0.88, -0.88), (-0.88, 0.88), (0.88, 0.88)]):
    make_box(f"RRC_PlatformLeg_{i}", lx-0.04, lx+0.04, ly-0.04, ly+0.04,
             0.0, 0.20, mat_wood_dark, main_col)

# 底部横梁
make_box("RRC_Beam_F", -0.88, 0.88, -0.90, -0.86, 0.05, 0.10, mat_wood_dark, main_col)
make_box("RRC_Beam_B", -0.88, 0.88, 0.86, 0.90, 0.05, 0.10, mat_wood_dark, main_col)
make_box("RRC_Beam_L", -0.90, -0.86, -0.88, 0.88, 0.05, 0.10, mat_wood_dark, main_col)
make_box("RRC_Beam_R", 0.86, 0.90, -0.88, 0.88, 0.05, 0.10, mat_wood_dark, main_col)

# 前后斜撑
make_bar_between("RRC_Brace_F1", (-0.88, -0.88, 0.02), (0.88, -0.88, 0.10), 0.03, mat_wood_dark, main_col)
make_bar_between("RRC_Brace_F2", (0.88, -0.88, 0.02), (-0.88, -0.88, 0.10), 0.03, mat_wood_dark, main_col)
make_bar_between("RRC_Brace_B1", (-0.88, 0.88, 0.02), (0.88, 0.88, 0.10), 0.03, mat_wood_dark, main_col)
make_bar_between("RRC_Brace_B2", (0.88, 0.88, 0.02), (-0.88, 0.88, 0.10), 0.03, mat_wood_dark, main_col)

# 平台面板
make_box("RRC_PlatformDeck", -1.0, 1.0, -1.0, 1.0, 0.15, 0.20, mat_wood_light, main_col)

# ===================== 操作舱 - 墙体 =====================
WALL_Y0, WALL_Y1 = -0.50, -0.45
Z_BOT, Z_TOP = 0.20, 0.95

# 前墙（-Y 面），预留门洞 X∈[-0.60,-0.20] Z∈[0.20,0.85] 与窗洞 X∈[0.05,0.45] Z∈[0.45,0.72]
make_box("RRC_FrontWall_L", -0.725, -0.60, WALL_Y0, WALL_Y1, Z_BOT, Z_TOP, mat_wood_dark, main_col)
make_box("RRC_FrontWall_DoorTop", -0.60, -0.20, WALL_Y0, WALL_Y1, 0.85, Z_TOP, mat_wood_dark, main_col)
make_box("RRC_FrontWall_Mid", -0.20, 0.05, WALL_Y0, WALL_Y1, Z_BOT, Z_TOP, mat_wood_dark, main_col)
make_box("RRC_FrontWall_WinBot", 0.05, 0.45, WALL_Y0, WALL_Y1, Z_BOT, 0.45, mat_wood_dark, main_col)
make_box("RRC_FrontWall_WinTop", 0.05, 0.45, WALL_Y0, WALL_Y1, 0.72, Z_TOP, mat_wood_dark, main_col)
make_box("RRC_FrontWall_R", 0.45, 0.725, WALL_Y0, WALL_Y1, Z_BOT, Z_TOP, mat_wood_dark, main_col)

# 后墙、左墙、右墙
make_box("RRC_BackWall", -0.725, 0.725, 0.70, 0.75, Z_BOT, Z_TOP, mat_wood_dark, main_col)
make_box("RRC_LeftWall", -0.725, -0.675, -0.50, 0.75, Z_BOT, Z_TOP, mat_wood_dark, main_col)
make_box("RRC_RightWall", 0.675, 0.725, -0.50, 0.75, Z_BOT, Z_TOP, mat_wood_dark, main_col)

# ===================== 门 =====================
make_box("RRC_Door", -0.58, -0.22, -0.505, -0.45, 0.20, 0.83, mat_wood_light, main_col)
make_box("RRC_DoorFrame_L", -0.63, -0.58, -0.52, -0.45, 0.18, 0.87, mat_wood_light, main_col)
make_box("RRC_DoorFrame_R", -0.22, -0.17, -0.52, -0.45, 0.18, 0.87, mat_wood_light, main_col)
make_box("RRC_DoorFrame_T", -0.63, -0.17, -0.52, -0.45, 0.85, 0.90, mat_wood_light, main_col)
make_cylinder("RRC_DoorHandle", 0.015, 0.05, (-0.28, -0.52, 0.52),
              (math.pi/2, 0, 0), mat_iron, main_col, seg=8)

# ===================== 无线电观察窗 =====================
make_box("RRC_WindowGlass", 0.06, 0.44, -0.49, -0.45, 0.46, 0.71, mat_glass, main_col)
make_box("RRC_WindowFrame_T", 0.03, 0.47, -0.505, -0.44, 0.71, 0.74, mat_iron, main_col)
make_box("RRC_WindowFrame_B", 0.03, 0.47, -0.505, -0.44, 0.43, 0.46, mat_iron, main_col)
make_box("RRC_WindowFrame_L", 0.03, 0.06, -0.505, -0.44, 0.43, 0.74, mat_iron, main_col)
make_box("RRC_WindowFrame_R", 0.44, 0.47, -0.505, -0.44, 0.43, 0.74, mat_iron, main_col)
make_box("RRC_WindowBar_H", 0.06, 0.44, -0.49, -0.45, 0.575, 0.595, mat_iron, main_col)
make_box("RRC_WindowBar_V", 0.24, 0.26, -0.49, -0.45, 0.46, 0.71, mat_iron, main_col)

# ===================== 象牙色救援十字 =====================
CX, CZ = 0.585, 0.60
make_box("RRC_CrossH", CX-0.10, CX+0.10, -0.51, -0.50, CZ-0.03, CZ+0.03, mat_ivory, main_col)
make_box("RRC_CrossV", CX-0.03, CX+0.03, -0.51, -0.50, CZ-0.10, CZ+0.10, mat_ivory, main_col)

# ===================== 屋顶 =====================
ROOF_Z0, ROOF_Z1 = 0.95, 1.01
make_box("RRC_Roof", -0.78, 0.78, -0.55, 0.80, ROOF_Z0, ROOF_Z1, mat_sea_green, main_col)

# 边缘包边
make_box("RRC_RoofEdge_F", -0.78, 0.78, -0.55, -0.53, ROOF_Z1, ROOF_Z1+0.015, mat_seam, main_col)
make_box("RRC_RoofEdge_B", -0.78, 0.78, 0.78, 0.80, ROOF_Z1, ROOF_Z1+0.015, mat_seam, main_col)
make_box("RRC_RoofEdge_L", -0.78, -0.76, -0.55, 0.80, ROOF_Z1, ROOF_Z1+0.015, mat_seam, main_col)
make_box("RRC_RoofEdge_R", 0.76, 0.78, -0.55, 0.80, ROOF_Z1, ROOF_Z1+0.015, mat_seam, main_col)

# 沿 Y 方向的深色接缝
for si, sx in enumerate([-0.55, -0.30, 0.0, 0.30, 0.55]):
    make_box(f"RRC_RoofSeam_{si}", sx-0.01, sx+0.01, -0.55, 0.80,
             ROOF_Z1, ROOF_Z1+0.012, mat_seam, main_col)

# 锈橙色修补板
make_box("RRC_RoofPatch1", 0.28, 0.50, -0.30, -0.10, ROOF_Z1, ROOF_Z1+0.008, mat_rust, main_col)
make_box("RRC_RoofPatch2", -0.40, -0.20, 0.35, 0.55, ROOF_Z1, ROOF_Z1+0.008, mat_rust, main_col)

# ===================== 微波碟（左侧屋顶） =====================
make_box("RRC_DishBase", -0.56, -0.44, -0.26, -0.14, ROOF_Z1, ROOF_Z1+0.03, mat_iron, main_col)
make_cylinder("RRC_DishPost", 0.025, 0.40, (-0.50, -0.20, 1.24), (0, 0, 0), mat_iron, main_col, seg=8)
make_box("RRC_DishTilt", -0.53, -0.47, -0.23, -0.17, 1.44, 1.47, mat_iron, main_col)

dish_mesh = bpy.data.meshes.new("RRC_MicrowaveDish")
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=16,
                      radius1=0.10, radius2=0.24, depth=0.08)
bm.to_mesh(dish_mesh)
bm.free()
dish_obj = bpy.data.objects.new("RRC_MicrowaveDish", dish_mesh)
dish_obj.location = (-0.50, -0.20, 1.48)
dish_obj.rotation_euler = (math.radians(75), 0, 0)
dish_obj.data.materials.append(mat_iron)
main_col.objects.link(dish_obj)

make_cone("RRC_DishFeed", 0.03, 0.015, 0.08, (-0.50, -0.345, 1.51),
          (math.radians(75), 0, 0), mat_iron, main_col, seg=8)

# ===================== 加固桅杆（右后屋顶） =====================
MAST_X, MAST_Y = 0.50, 0.50
MAST_Z0, MAST_Z1 = ROOF_Z1, 2.60

make_box("RRC_MastBase", MAST_X-0.07, MAST_X+0.07, MAST_Y-0.07, MAST_Y+0.07,
         ROOF_Z1, ROOF_Z1+0.03, mat_iron, main_col)
make_box("RRC_Mast", MAST_X-0.03, MAST_X+0.03, MAST_Y-0.03, MAST_Y+0.03,
         MAST_Z0, MAST_Z1, mat_iron, main_col)

# ===================== 三单元 Yagi 横向阵列 =====================
def make_yagi(prefix, bx, by, z):
    make_box(prefix + "_Boom", bx-0.01, bx+0.01, by-0.20, by, z-0.015, z+0.015,
             mat_iron, main_col)
    make_box(prefix + "_Reflector", bx-0.12, bx+0.12, by-0.03, by-0.01,
             z-0.008, z+0.008, mat_iron, main_col)
    make_box(prefix + "_Driven", bx-0.11, bx+0.11, by-0.105, by-0.085,
             z-0.008, z+0.008, mat_iron, main_col)
    make_box(prefix + "_Director", bx-0.10, bx+0.10, by-0.195, by-0.175,
             z-0.008, z+0.008, mat_iron, main_col)

for yi, z in enumerate([1.85, 2.15, 2.45]):
    make_yagi(f"RRC_Yagi_{yi}", MAST_X, MAST_Y, z)

# ===================== 四根拉索 + 屋顶锚点 =====================
MAST_TOP = (MAST_X, MAST_Y, 2.50)
ANCHORS = [
    (0.72, 0.75, ROOF_Z1 + 0.03),
    (0.28, 0.75, ROOF_Z1 + 0.03),
    (0.72, 0.28, ROOF_Z1 + 0.03),
    (0.28, 0.28, ROOF_Z1 + 0.03),
]
for ai, anchor in enumerate(ANCHORS):
    make_cable(f"RRC_Guy_{ai}", MAST_TOP, anchor, 0.008, mat_iron, main_col)
    make_box(f"RRC_Anchor_{ai}", anchor[0]-0.02, anchor[0]+0.02,
             anchor[1]-0.02, anchor[1]+0.02, ROOF_Z1, ROOF_Z1+0.03,
             mat_iron, main_col)

# ===================== 应急信标 =====================
make_icosphere("RRC_Beacon", 0.05, (MAST_X, MAST_Y, 2.65), mat_amber, main_col)

# ===================== 背墙特征 =====================
make_box("RRC_CtrlCabinet", -0.45, 0.20, 0.75, 0.83, 0.35, 0.80, mat_iron, main_col)
make_box("RRC_CtrlDoor", -0.42, 0.17, 0.83, 0.85, 0.38, 0.77, mat_sea_green, main_col)
make_cylinder("RRC_CtrlHandle", 0.015, 0.03, (0.05, 0.86, 0.58),
              (math.pi/2, 0, 0), mat_iron, main_col, seg=8)
make_box("RRC_FuseCover", -0.65, -0.50, 0.75, 0.77, 0.45, 0.65, mat_iron, main_col)
make_cylinder("RRC_Conduit", 0.028, 0.75, (0.55, 0.78, 0.575),
              (0, 0, 0), mat_iron, main_col, seg=8)

# ===================== 紧凑线缆盘（左侧平台） =====================
CABLE_REEL_X = -0.86
CABLE_REEL_Y = -0.25

reel_mesh = bpy.data.meshes.new("RRC_CableReel")
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=16,
                      radius1=0.10, radius2=0.10, depth=0.06)
bm.to_mesh(reel_mesh)
bm.free()
reel_obj = bpy.data.objects.new("RRC_CableReel", reel_mesh)
reel_obj.location = (CABLE_REEL_X, CABLE_REEL_Y, 0.30)
reel_obj.rotation_euler = (math.pi/2, 0, 0)
reel_obj.data.materials.append(mat_iron)
main_col.objects.link(reel_obj)

hub_mesh = bpy.data.meshes.new("RRC_CableReelHub")
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=10,
                      radius1=0.03, radius2=0.03, depth=0.08)
bm.to_mesh(hub_mesh)
bm.free()
hub_obj = bpy.data.objects.new("RRC_CableReelHub", hub_mesh)
hub_obj.location = (CABLE_REEL_X, CABLE_REEL_Y, 0.30)
hub_obj.rotation_euler = (math.pi/2, 0, 0)
hub_obj.data.materials.append(mat_wood_dark)
main_col.objects.link(hub_obj)

# ===================== 信号备用电池箱（右侧平台） =====================
make_box("RRC_BatteryBox", 0.77, 0.97, -0.40, -0.10, 0.20, 0.50, mat_wood_dark, main_col)
make_box("RRC_BatteryLid", 0.76, 0.98, -0.41, -0.09, 0.50, 0.53, mat_iron, main_col)
make_box("RRC_BatteryVent", 0.80, 0.94, -0.41, -0.39, 0.30, 0.42, mat_iron, main_col)

# ===================== 相机 =====================
def create_ortho_camera(name, location, look_at, ortho_scale, collection):
    cam_data = bpy.data.cameras.new(name)
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho_scale
    cam_obj = bpy.data.objects.new(name, cam_data)
    collection.objects.link(cam_obj)
    cam_obj.location = location
    direction = mathutils.Vector(look_at) - mathutils.Vector(location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    return cam_obj

TARGET = (0.0, 0.0, 1.20)
ORTHO = 3.4
D = 10.0

cam_front = create_ortho_camera("RRC_Cam_Front", (0, -D, TARGET[2]), TARGET, ORTHO, helper_col)
cam_back  = create_ortho_camera("RRC_Cam_Back",  (0, D, TARGET[2]), TARGET, ORTHO, helper_col)
cam_left  = create_ortho_camera("RRC_Cam_Left",  (-D, 0, TARGET[2]), TARGET, ORTHO, helper_col)
cam_right = create_ortho_camera("RRC_Cam_Right", (D, 0, TARGET[2]), TARGET, ORTHO, helper_col)

cam_top = bpy.data.cameras.new("RRC_Cam_Top")
cam_top.type = 'ORTHO'
cam_top.ortho_scale = ORTHO
cam_top_obj = bpy.data.objects.new("RRC_Cam_Top", cam_top)
helper_col.objects.link(cam_top_obj)
cam_top_obj.location = (0, 0, D)
cam_top_obj.rotation_euler = (0, 0, 0)

cam_bot = bpy.data.cameras.new("RRC_Cam_Bottom")
cam_bot.type = 'ORTHO'
cam_bot.ortho_scale = ORTHO
cam_bot_obj = bpy.data.objects.new("RRC_Cam_Bottom", cam_bot)
helper_col.objects.link(cam_bot_obj)
cam_bot_obj.location = (0, 0, -D)
cam_bot_obj.rotation_euler = (math.pi, 0, 0)

cam_preview = create_ortho_camera("RRC_Cam_Preview", (4.5, -5.5, 4.0),
                                  (0, 0, 1.1), 4.5, helper_col)

# ===================== 灯光与世界 =====================
if not bpy.context.scene.world:
    bpy.context.scene.world = bpy.data.worlds.new("RRC_World")
world = bpy.context.scene.world
world.use_nodes = True
bg = get_bg(world)
if bg:
    if "Color" in bg.inputs:
        bg.inputs["Color"].default_value = (0.58, 0.64, 0.70, 1.0)
    if "Strength" in bg.inputs:
        bg.inputs["Strength"].default_value = 0.6

sun_data = bpy.data.lights.new("RRC_Sun", 'SUN')
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("RRC_Sun", sun_data)
helper_col.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(55), math.radians(12), math.radians(35))

fill_data = bpy.data.lights.new("RRC_Fill", 'AREA')
fill_data.energy = 100.0
fill_data.size = 6.0
fill_obj = bpy.data.objects.new("RRC_Fill", fill_data)
helper_col.objects.link(fill_obj)
fill_obj.location = (-4.0, -4.0, 5.0)
fill_obj.rotation_euler = (math.radians(55), 0, math.radians(-35))

beacon_light_data = bpy.data.lights.new("RRC_BeaconLight", 'POINT')
beacon_light_data.energy = 15.0
beacon_light_data.color = (1.0, 0.55, 0.10)
beacon_light_obj = bpy.data.objects.new("RRC_BeaconLight", beacon_light_data)
helper_col.objects.link(beacon_light_obj)
beacon_light_obj.location = (MAST_X, MAST_Y, 2.65)

# ===================== 渲染设置 =====================
scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except Exception:
        scene.render.engine = 'BLENDER_WORKBENCH'

scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

# ===================== 渲染六视图 + 预览 =====================
views = [
    ("Front", cam_front),
    ("Back", cam_back),
    ("Left", cam_left),
    ("Right", cam_right),
    ("Top", cam_top_obj),
    ("Bottom", cam_bot_obj),
]
for view_name, cam in views:
    scene.camera = cam
    scene.render.filepath = str(OUT_VIEWS / f"RescueRadioCenter_DeepSeek_{view_name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {scene.render.filepath}")

scene.camera = cam_preview
scene.render.filepath = str(OUT_PREVIEW)
bpy.ops.render.render(write_still=True)
print(f"Rendered: {scene.render.filepath}")

# ===================== 保存 .blend =====================
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
print(f"Saved: {OUT_BLEND}")

# ===================== 导出 FBX（只主集合网格） =====================
bpy.ops.object.select_all(action='DESELECT')
mesh_objs = [o for o in main_col.objects if o.type == 'MESH']
for obj in mesh_objs:
    obj.select_set(True)
if mesh_objs:
    bpy.context.view_layer.objects.active = mesh_objs[0]

bpy.ops.export_scene.fbx(
    filepath=str(OUT_FBX),
    use_selection=True,
    object_types={'MESH'},
    use_mesh_modifiers=True,
)
print(f"Exported FBX: {OUT_FBX}")

# ===================== 诊断 =====================
print("\n" + "=" * 62)
print("RescueRadioCenter_DeepSeek — Build Report")
print("=" * 62)

mesh_objs = [o for o in main_col.objects if o.type == 'MESH']
print(f"Mesh objects in model collection: {len(mesh_objs)}")

all_corners = []
for obj in mesh_objs:
    for corner in obj.bound_box:
        wc = obj.matrix_world @ mathutils.Vector(corner)
        all_corners.append(wc)

if all_corners:
    min_x = min(c.x for c in all_corners)
    max_x = max(c.x for c in all_corners)
    min_y = min(c.y for c in all_corners)
    max_y = max(c.y for c in all_corners)
    min_z = min(c.z for c in all_corners)
    max_z = max(c.z for c in all_corners)
    print(f"World bounding box:")
    print(f"  X: [{min_x:.3f}, {max_x:.3f}]  size = {max_x - min_x:.3f} m")
    print(f"  Y: [{min_y:.3f}, {max_y:.3f}]  size = {max_y - min_y:.3f} m")
    print(f"  Z: [{min_z:.3f}, {max_z:.3f}]  size = {max_z - min_z:.3f} m")
    print(f"  Lowest Z = {min_z:.3f} m")

print(f"\nOutput paths:")
print(f"  Script:   Tools/Blender/RescueRadioCenter_DeepSeek.py")
print(f"  Blend:    {OUT_BLEND}")
print(f"  FBX:      {OUT_FBX}")
print(f"  Preview:  {OUT_PREVIEW}")
for name in ["Front", "Back", "Left", "Right", "Top", "Bottom"]:
    print(f"  View:     {OUT_VIEWS / f'RescueRadioCenter_DeepSeek_{name}.png'}")

print(f"\nPer-object mesh diagnostics:")
nm_total = 0
loose_total = 0
issues = 0
for obj in mesh_objs:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    lv = sum(1 for v in bm.verts if not v.link_edges)
    le = sum(1 for e in bm.edges if not e.link_faces)
    bm.free()
    nm_total += nm
    loose_total += lv + le
    if nm > 0 or lv > 0 or le > 0:
        issues += 1
        print(f"  {obj.name}: non-manifold={nm}, loose_verts={lv}, loose_edges={le}")

if issues == 0:
    print(f"  All {len(mesh_objs)} mesh objects: no non-manifold edges, no loose geometry.")
print(f"  Total non-manifold edges: {nm_total}")
print(f"  Total loose geometry items: {loose_total}")

print(f"\nIMPORTANT: The per-object checks above detect non-manifold edges and")
print(f"      loose vertices/edges WITHIN each individual mesh. They CANNOT")
print(f"      detect or evaluate inter-object intersections, overlaps, or")
print(f"      penetrations between different mesh objects (e.g. a support post")
print(f"      embedded in a beam, or two boxes overlapping). No automated")
print(f"      inter-object intersection test is performed by this script.")
print("=" * 62)