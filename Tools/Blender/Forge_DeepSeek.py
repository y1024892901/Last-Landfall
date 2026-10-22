import bpy
import bmesh
import math
import mathutils
from pathlib import Path

# ===================== 路径 =====================
ROOT = Path.cwd()
OUT_BLEND = ROOT / "Assets" / "LastLandfall" / "Art" / "Source" / "Buildings" / "Forge_DeepSeek.blend"
OUT_FBX = ROOT / "Assets" / "LastLandfall" / "Resources" / "Models" / "Buildings" / "Forge_DeepSeek.fbx"
OUT_PREVIEW = ROOT / "Assets" / "LastLandfall" / "Art" / "Previews" / "Buildings" / "Forge_DeepSeek.png"
OUT_VIEWS = ROOT / "Assets" / "LastLandfall" / "Art" / "References" / "ScenarioBuildingViews" / "_renders"

for p in [OUT_BLEND.parent, OUT_FBX.parent, OUT_PREVIEW.parent, OUT_VIEWS]:
    p.mkdir(parents=True, exist_ok=True)

# ===================== 常量 =====================
MAIN_COL = "Forge_DeepSeek"
HELPER_COL = "Helpers_Forge_DeepSeek"
MAT_PREFIX = "FG_"

# ===================== 清理专属集合与材质 =====================
old_mat_names = set()
for col_name in [MAIN_COL, HELPER_COL]:
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
        for obj in list(col.objects):
            if obj.type == 'MESH':
                old_mat_names.update(
                    mat.name for mat in obj.data.materials
                    if mat and mat.name.startswith(MAT_PREFIX)
                )
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

for mat_name in old_mat_names:
    mat = bpy.data.materials.get(mat_name)
    if mat and mat.users == 0:
        bpy.data.materials.remove(mat)

# ===================== 集合 =====================
main_col = bpy.data.collections.new(MAIN_COL)
bpy.context.scene.collection.children.link(main_col)

helper_col = bpy.data.collections.new(HELPER_COL)
bpy.context.scene.collection.children.link(helper_col)

# ===================== 材质 =====================
def make_mat(name, color, rough=0.7, metallic=0.0, emission=None, emit_strength=4.0):
    mat = bpy.data.materials.new(MAT_PREFIX + name)
    mat.use_nodes = True
    bsdf = next((node for node in mat.node_tree.nodes
                 if node.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
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

mat_stone_light = make_mat("StoneLight", (0.68, 0.63, 0.55), 0.92)
mat_stone_forge = make_mat("StoneForge", (0.58, 0.53, 0.46), 0.92)
mat_stone_dark  = make_mat("StoneDark",  (0.30, 0.26, 0.22), 0.95)
mat_iron        = make_mat("Iron",       (0.16, 0.14, 0.13), 0.50, 0.70)
mat_iron_rust   = make_mat("IronRust",   (0.55, 0.28, 0.15), 0.85)
mat_sea_green   = make_mat("SeaGreen",   (0.42, 0.55, 0.50), 0.55, 0.60)
mat_wood_char   = make_mat("WoodChar",   (0.25, 0.17, 0.12), 0.95)
mat_wood_bellows= make_mat("WoodBellows",(0.50, 0.40, 0.28), 0.90)
mat_coal        = make_mat("Coal",       (0.08, 0.07, 0.06), 0.95)
mat_fire        = make_mat("Fire",       (1.00, 0.42, 0.10), 0.60, 0.0, (1.0, 0.42, 0.10), 5.0)
mat_billet      = make_mat("Billet",     (1.00, 0.58, 0.15), 0.55, 0.0, (1.0, 0.58, 0.15), 4.0)
mat_water       = make_mat("Water",      (0.35, 0.45, 0.50), 0.15)
mat_soot        = make_mat("Soot",       (0.05, 0.05, 0.05), 0.98)

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

def make_cone(name, radius1, radius2, depth, loc, rot, mat, collection, seg=12):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg,
                          radius1=radius1, radius2=radius2, depth=depth)
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

# ===================== 尺寸常量 =====================
Z_BASE_TOP = 0.20
FORGE_X0, FORGE_X1 = -0.85, -0.05
FORGE_Y0, FORGE_Y1 = 0.05, 0.85
FORGE_Z1 = 1.55
WALL_T = 0.08

OPEN_X0, OPEN_X1 = -0.65, -0.25
OPEN_Z0, OPEN_Z1 = 0.55, 1.05

# ===================== 石基座（4 块拼合，中间留缝） =====================
SEAM = 0.008
base_blocks = [
    ("SW_Base_BL", -1.0, -SEAM, 0.008, 1.0),
    ("SW_Base_BR",  SEAM, 1.0,  0.008, 1.0),
    ("SW_Base_FL", -1.0, -SEAM, -1.0, -0.008),
    ("SW_Base_FR",  SEAM, 1.0,  -1.0, -0.008),
]
for name, x0, x1, y0, y1 in base_blocks:
    make_box(name, x0, x1, y0, y1, 0.0, Z_BASE_TOP, mat_stone_light, main_col)

# ===================== 石炉体（空心墙 + 前侧火口） =====================
# 左墙
make_box("SW_ForgeWall_L", FORGE_X0, FORGE_X0 + WALL_T, FORGE_Y0, FORGE_Y1,
         Z_BASE_TOP, FORGE_Z1, mat_stone_forge, main_col)
# 右墙
make_box("SW_ForgeWall_R", FORGE_X1 - WALL_T, FORGE_X1, FORGE_Y0, FORGE_Y1,
         Z_BASE_TOP, FORGE_Z1, mat_stone_forge, main_col)
# 后墙
make_box("SW_ForgeWall_B", FORGE_X0, FORGE_X1, FORGE_Y1 - WALL_T, FORGE_Y1,
         Z_BASE_TOP, FORGE_Z1, mat_stone_forge, main_col)
# 前墙下段（火口下方）
make_box("SW_ForgeWall_FB", FORGE_X0, FORGE_X1, FORGE_Y0, FORGE_Y0 + WALL_T,
         Z_BASE_TOP, OPEN_Z0, mat_stone_forge, main_col)
# 前墙上段（火口上方）
make_box("SW_ForgeWall_FT", FORGE_X0, FORGE_X1, FORGE_Y0, FORGE_Y0 + WALL_T,
         OPEN_Z1, FORGE_Z1, mat_stone_forge, main_col)
# 前墙左侧（火口左边）
make_box("SW_ForgeWall_FL", FORGE_X0, OPEN_X0, FORGE_Y0, FORGE_Y0 + WALL_T,
         OPEN_Z0, OPEN_Z1, mat_stone_forge, main_col)
# 前墙右侧（火口右边）
make_box("SW_ForgeWall_FR", OPEN_X1, FORGE_X1, FORGE_Y0, FORGE_Y0 + WALL_T,
         OPEN_Z0, OPEN_Z1, mat_stone_forge, main_col)
# 顶盖
make_box("SW_ForgeTop", FORGE_X0, FORGE_X1, FORGE_Y0, FORGE_Y1,
         FORGE_Z1 - 0.08, FORGE_Z1, mat_stone_forge, main_col)

# 顶部檐口板（略出挑）
make_box("SW_ForgeMantle", FORGE_X0 - 0.05, FORGE_X1 + 0.05,
         FORGE_Y0 - 0.05, FORGE_Y1 + 0.05,
         FORGE_Z1 - 0.02, FORGE_Z1 + 0.04, mat_stone_light, main_col)

# ===================== 炉膛内部：炉台、煤层、烟黑背板 =====================
# 抬高的炉台（底部填充，让火床与火口底部齐平）
make_box("SW_Hearth", -0.70, -0.20, 0.15, 0.65, Z_BASE_TOP, OPEN_Z0,
         mat_stone_dark, main_col)
# 煤床
make_box("SW_CoalBed", -0.64, -0.26, 0.18, 0.58, OPEN_Z0, OPEN_Z0 + 0.08,
         mat_coal, main_col)
# 烟黑背板（贴后墙内侧，透过火口可见）
make_box("SW_SootBack", -0.70, -0.20, FORGE_Y1 - WALL_T - 0.015, FORGE_Y1 - WALL_T,
         OPEN_Z0, OPEN_Z1 + 0.10, mat_soot, main_col)

# 发光煤块（多个小球）
glow_positions = [
    (-0.55, 0.30, OPEN_Z0 + 0.06),
    (-0.45, 0.38, OPEN_Z0 + 0.08),
    (-0.36, 0.28, OPEN_Z0 + 0.06),
    (-0.48, 0.48, OPEN_Z0 + 0.07),
    (-0.38, 0.42, OPEN_Z0 + 0.09),
    (-0.58, 0.42, OPEN_Z0 + 0.07),
]
for gi, (gx, gy, gz) in enumerate(glow_positions):
    make_icosphere(f"SW_GlowCoal_{gi}", 0.045, (gx, gy, gz),
                   mat_fire, main_col, subdiv=1)
# 少量非发光煤块
dark_positions = [
    (-0.62, 0.24, OPEN_Z0 + 0.05),
    (-0.32, 0.50, OPEN_Z0 + 0.05),
    (-0.50, 0.20, OPEN_Z0 + 0.06),
]
for di, (dx, dy, dz) in enumerate(dark_positions):
    make_icosphere(f"SW_DarkCoal_{di}", 0.040, (dx, dy, dz),
                   mat_coal, main_col, subdiv=1)

# ===================== 铁火口框 =====================
FR_Y0, FR_Y1 = -0.01, 0.06
make_box("SW_FireFrame_T", OPEN_X0 - 0.03, OPEN_X1 + 0.03, FR_Y0, FR_Y1,
         OPEN_Z1 - 0.02, OPEN_Z1 + 0.03, mat_iron, main_col)
make_box("SW_FireFrame_B", OPEN_X0 - 0.03, OPEN_X1 + 0.03, FR_Y0, FR_Y1,
         OPEN_Z0 - 0.03, OPEN_Z0 + 0.02, mat_iron, main_col)
make_box("SW_FireFrame_L", OPEN_X0 - 0.03, OPEN_X0 + 0.02, FR_Y0, FR_Y1,
         OPEN_Z0 - 0.03, OPEN_Z1 + 0.03, mat_iron, main_col)
make_box("SW_FireFrame_R", OPEN_X1 - 0.02, OPEN_X1 + 0.03, FR_Y0, FR_Y1,
         OPEN_Z0 - 0.03, OPEN_Z1 + 0.03, mat_iron, main_col)

# 火口上方小金属遮檐
make_box("SW_FireHood", OPEN_X0 - 0.05, OPEN_X1 + 0.05, -0.06, 0.05,
         OPEN_Z1 + 0.03, OPEN_Z1 + 0.06, mat_iron, main_col)

# ===================== 烟道（烟囱）与雨帽 =====================
CH_X0, CH_X1 = -0.65, -0.25
CH_Y0, CH_Y1 = 0.30, 0.70
CH_Z0, CH_Z1 = FORGE_Z1, 2.50

make_box("SW_ChimneyBody", CH_X0, CH_X1, CH_Y0, CH_Y1, CH_Z0, CH_Z1,
         mat_stone_forge, main_col)
# 烟囱壁面接缝（水平两道）
make_box("SW_ChimneySeam1", CH_X0 - 0.005, CH_X1 + 0.005, CH_Y0 - 0.005, CH_Y1 + 0.005,
         1.75, 1.77, mat_stone_dark, main_col)
make_box("SW_ChimneySeam2", CH_X0 - 0.005, CH_X1 + 0.005, CH_Y0 - 0.005, CH_Y1 + 0.005,
         2.10, 2.12, mat_stone_dark, main_col)

# 烟囱加固铁箍（一圈四面）
BAND_Z0, BAND_Z1 = 1.88, 1.94
make_box("SW_ChimBand_F", CH_X0 - 0.005, CH_X1 + 0.005, CH_Y0 - 0.015, CH_Y0 + 0.005,
         BAND_Z0, BAND_Z1, mat_iron, main_col)
make_box("SW_ChimBand_B", CH_X0 - 0.005, CH_X1 + 0.005, CH_Y1 - 0.005, CH_Y1 + 0.015,
         BAND_Z0, BAND_Z1, mat_iron, main_col)
make_box("SW_ChimBand_L", CH_X0 - 0.015, CH_X0 + 0.005, CH_Y0 + 0.005, CH_Y1 - 0.005,
         BAND_Z0, BAND_Z1, mat_iron, main_col)
make_box("SW_ChimBand_R", CH_X1 - 0.005, CH_X1 + 0.015, CH_Y0 + 0.005, CH_Y1 - 0.005,
         BAND_Z0, BAND_Z1, mat_iron, main_col)

# 雨帽：宽出挑板 + 四角短支撑柱
CAP_OVER = 0.08
CAP_Z0, CAP_Z1 = 2.50, 2.62
make_box("SW_ChimCapPlate", CH_X0 - CAP_OVER, CH_X1 + CAP_OVER,
         CH_Y0 - CAP_OVER, CH_Y1 + CAP_OVER, CAP_Z0, CAP_Z1,
         mat_iron, main_col)
# 雨帽下方四角短柱（连接帽与烟囱顶）
for cci, (ccx, ccy) in enumerate([
        (CH_X0 + 0.03, CH_Y0 + 0.03),
        (CH_X1 - 0.03, CH_Y0 + 0.03),
        (CH_X0 + 0.03, CH_Y1 - 0.03),
        (CH_X1 - 0.03, CH_Y1 - 0.03)]):
    make_box(f"SW_ChimCapPost_{cci}", ccx - 0.015, ccx + 0.015,
             ccy - 0.015, ccy + 0.015, CH_Z1 - 0.02, CAP_Z0, mat_iron, main_col)

# ===================== 铁砧与木墩 =====================
STUMP_CX, STUMP_CY = 0.60, -0.34
STUMP_R = 0.13
STUMP_TOP = 0.58
make_cylinder("SW_Stump", STUMP_R, STUMP_TOP - Z_BASE_TOP,
              (STUMP_CX, STUMP_CY, (Z_BASE_TOP + STUMP_TOP) / 2),
              (0, 0, 0), mat_wood_char, main_col, seg=12)

# 铁砧主体
make_box("SW_AnvilBody", 0.48, 0.72, -0.48, -0.20, STUMP_TOP, 0.72, mat_iron, main_col)
# 砧面（略宽）
make_box("SW_AnvilFace", 0.47, 0.73, -0.48, -0.20, 0.72, 0.74, mat_iron, main_col)
# 砧跟（后端台阶）
make_box("SW_AnvilHeel", 0.48, 0.72, -0.20, -0.14, STUMP_TOP, 0.72, mat_iron, main_col)
# 砧角（圆锥，指向 -Y）
make_cone("SW_AnvilHorn", 0.075, 0.005, 0.20,
          (0.60, -0.58, 0.65), (math.pi / 2, 0, 0), mat_iron, main_col, seg=10)

# 热钢坯放在砧面上
make_box("SW_HotBillet", 0.55, 0.65, -0.42, -0.30, 0.74, 0.77, mat_billet, main_col)
# 钢坯侧面小夹钳（示意）
make_bar_between("SW_BilletTongs", (0.67, -0.36, 0.755), (0.73, -0.36, 0.80),
                 0.012, mat_iron, main_col)

# ===================== 风箱 =====================
# 楔形箱体：底部齐平，顶部后高前低
BEL_X0, BEL_X1 = 0.05, 0.30
BEL_Y0, BEL_Y1 = 0.35, 0.68
BEL_Z0 = Z_BASE_TOP
BEL_Z_FRONT_TOP = 0.35
BEL_Z_BACK_TOP = 0.55

bel_v = [
    (BEL_X0, BEL_Y0, BEL_Z0), (BEL_X1, BEL_Y0, BEL_Z0),
    (BEL_X1, BEL_Y1, BEL_Z0), (BEL_X0, BEL_Y1, BEL_Z0),
    (BEL_X0, BEL_Y0, BEL_Z_FRONT_TOP), (BEL_X1, BEL_Y0, BEL_Z_FRONT_TOP),
    (BEL_X1, BEL_Y1, BEL_Z_BACK_TOP), (BEL_X0, BEL_Y1, BEL_Z_BACK_TOP),
]
bel_f = [
    (0, 1, 2, 3), (4, 7, 6, 5),
    (0, 4, 5, 1), (1, 5, 6, 2),
    (2, 6, 7, 3), (3, 7, 4, 0),
]
_make_prism("SW_BellowsBody", bel_v, bel_f, mat_wood_bellows, main_col)

# 风箱前脸皮革（在低矮前壁上）
make_box("SW_BellowsLeather", BEL_X0 + 0.02, BEL_X1 - 0.02, BEL_Y0 - 0.008, BEL_Y0 + 0.005,
         BEL_Z0 + 0.03, BEL_Z_FRONT_TOP - 0.03, mat_iron_rust, main_col)

# 风嘴（水平短管，从风箱前侧连到炉体右壁）
make_cylinder("SW_BellowsNozzle", 0.020, 0.14,
              (-0.01, 0.42, 0.32), (0, math.pi / 2, 0), mat_iron, main_col, seg=10)
make_cylinder("SW_BellowsNozzleTip", 0.028, 0.02,
              (-0.07, 0.42, 0.32), (0, math.pi / 2, 0), mat_iron, main_col, seg=10)

# 风箱手柄（顶部后侧，可握持的横杆）
make_box("SW_BellowsHandlePost_L", 0.11, 0.14, 0.60, 0.63, BEL_Z_BACK_TOP, 0.68,
         mat_wood_bellows, main_col)
make_box("SW_BellowsHandlePost_R", 0.21, 0.24, 0.60, 0.63, BEL_Z_BACK_TOP, 0.68,
         mat_wood_bellows, main_col)
make_box("SW_BellowsHandleBar", 0.10, 0.25, 0.59, 0.64, 0.66, 0.70,
         mat_wood_char, main_col)

# ===================== 煤料篮 =====================
# 篮架：4 立柱 + 3 道横箍
BASK_X0, BASK_X1 = -0.82, -0.53
BASK_Y0, BASK_Y1 = -0.52, -0.23
BASK_Z0, BASK_Z1 = Z_BASE_TOP, 0.38
POST_T = 0.02

for pi, (px, py) in enumerate([
        (BASK_X0 + POST_T / 2, BASK_Y0 + POST_T / 2),
        (BASK_X1 - POST_T / 2, BASK_Y0 + POST_T / 2),
        (BASK_X0 + POST_T / 2, BASK_Y1 - POST_T / 2),
        (BASK_X1 - POST_T / 2, BASK_Y1 - POST_T / 2)]):
    make_box(f"SW_BasketPost_{pi}", px - POST_T / 2, px + POST_T / 2,
             py - POST_T / 2, py + POST_T / 2, BASK_Z0, BASK_Z1, mat_iron, main_col)

for ri, rz in enumerate([BASK_Z0 + 0.01, BASK_Z0 + 0.10, BASK_Z1 - 0.02]):
    make_box(f"SW_BasketRingF_{ri}", BASK_X0, BASK_X1, BASK_Y0, BASK_Y0 + 0.012,
             rz, rz + 0.015, mat_iron, main_col)
    make_box(f"SW_BasketRingB_{ri}", BASK_X0, BASK_X1, BASK_Y1 - 0.012, BASK_Y1,
             rz, rz + 0.015, mat_iron, main_col)
    make_box(f"SW_BasketRingL_{ri}", BASK_X0, BASK_X0 + 0.012, BASK_Y0, BASK_Y1,
             rz, rz + 0.015, mat_iron, main_col)
    make_box(f"SW_BasketRingR_{ri}", BASK_X1 - 0.012, BASK_X1, BASK_Y0, BASK_Y1,
             rz, rz + 0.015, mat_iron, main_col)

# 篮底
make_box("SW_BasketBottom", BASK_X0 + 0.01, BASK_X1 - 0.01,
         BASK_Y0 + 0.01, BASK_Y1 - 0.01, BASK_Z0, BASK_Z0 + 0.02, mat_iron, main_col)

# 篮子里的煤块
basket_coal_positions = [
    (-0.72, -0.40, 0.28, 0.045),
    (-0.63, -0.36, 0.30, 0.040),
    (-0.75, -0.32, 0.29, 0.038),
    (-0.65, -0.45, 0.26, 0.042),
    (-0.58, -0.42, 0.27, 0.036),
]
for bi, (bx, by, bz, br) in enumerate(basket_coal_positions):
    make_icosphere(f"SW_BasketCoal_{bi}", br, (bx, by, bz), mat_coal, main_col, subdiv=1)

# ===================== 淬火水槽 =====================
TROUGH_X0, TROUGH_X1 = -0.40, -0.05
TROUGH_Y0, TROUGH_Y1 = -0.55, -0.25
TROUGH_Z0, TROUGH_Z1 = Z_BASE_TOP, 0.35
TROUGH_T = 0.025

# 四壁
make_box("SW_TroughWall_F", TROUGH_X0, TROUGH_X1, TROUGH_Y0, TROUGH_Y0 + TROUGH_T,
         TROUGH_Z0, TROUGH_Z1, mat_sea_green, main_col)
make_box("SW_TroughWall_B", TROUGH_X0, TROUGH_X1, TROUGH_Y1 - TROUGH_T, TROUGH_Y1,
         TROUGH_Z0, TROUGH_Z1, mat_sea_green, main_col)
make_box("SW_TroughWall_L", TROUGH_X0, TROUGH_X0 + TROUGH_T, TROUGH_Y0 + TROUGH_T, TROUGH_Y1 - TROUGH_T,
         TROUGH_Z0, TROUGH_Z1, mat_sea_green, main_col)
make_box("SW_TroughWall_R", TROUGH_X1 - TROUGH_T, TROUGH_X1, TROUGH_Y0 + TROUGH_T, TROUGH_Y1 - TROUGH_T,
         TROUGH_Z0, TROUGH_Z1, mat_sea_green, main_col)
# 槽底
make_box("SW_TroughBottom", TROUGH_X0 + TROUGH_T, TROUGH_X1 - TROUGH_T,
         TROUGH_Y0 + TROUGH_T, TROUGH_Y1 - TROUGH_T,
         TROUGH_Z0, TROUGH_Z0 + 0.02, mat_sea_green, main_col)
# 水面
make_box("SW_TroughWater", TROUGH_X0 + TROUGH_T + 0.002, TROUGH_X1 - TROUGH_T - 0.002,
         TROUGH_Y0 + TROUGH_T + 0.002, TROUGH_Y1 - TROUGH_T - 0.002,
         TROUGH_Z1 - 0.07, TROUGH_Z1 - 0.06, mat_water, main_col)

# 槽边缘锈色补丁（小片）
make_box("SW_TroughPatch", TROUGH_X0 + 0.03, TROUGH_X0 + 0.08, TROUGH_Y0 - 0.005, TROUGH_Y0,
         TROUGH_Z1 - 0.10, TROUGH_Z1 - 0.05, mat_iron_rust, main_col)

# ===================== 工具架（挂在炉前脸右侧） =====================
RACK_X0, RACK_X1 = -0.22, -0.08
RACK_Y0, RACK_Y1 = -0.04, 0.05
RACK_BAR_Z0, RACK_BAR_Z1 = 1.00, 1.04

# 支架（两个水平连接件，从炉面伸出到横杆）
make_box("SW_RackBracket_L", -0.21, -0.19, RACK_Y0, RACK_Y1, 0.98, 1.06, mat_wood_char, main_col)
make_box("SW_RackBracket_R", -0.11, -0.09, RACK_Y0, RACK_Y1, 0.98, 1.06, mat_wood_char, main_col)
# 横杆
make_box("SW_RackBar", RACK_X0, RACK_X1, RACK_Y0, RACK_Y0 + 0.04, RACK_BAR_Z0, RACK_BAR_Z1,
         mat_wood_char, main_col)

# 挂具 - 铁锤（倒挂，锤头在下）
make_box("SW_ToolHammerHandle", -0.195, -0.175, -0.02, 0.00, 0.75, 1.00, mat_wood_char, main_col)
make_box("SW_ToolHammerHead", -0.22, -0.14, -0.03, 0.01, 0.68, 0.76, mat_iron, main_col)

# 挂具 - 拨火棍（直杆 + 弯钩）
make_bar_between("SW_ToolPoker", (-0.10, -0.01, 1.00), (-0.10, -0.01, 0.60),
                 0.014, mat_iron, main_col)
make_bar_between("SW_ToolPokerHook", (-0.10, -0.01, 0.60), (-0.13, -0.01, 0.56),
                 0.012, mat_iron, main_col)

# 挂具 - 火钳（两条交叉臂）
make_bar_between("SW_ToolTongsA", (-0.15, -0.01, 1.00), (-0.17, -0.01, 0.65),
                 0.012, mat_iron, main_col)
make_bar_between("SW_ToolTongsB", (-0.13, -0.01, 1.00), (-0.15, -0.01, 0.65),
                 0.012, mat_iron, main_col)
# 钳轴销
make_cylinder("SW_ToolTongsPivot", 0.012, 0.02,
              (-0.15, -0.01, 0.82), (math.pi / 2, 0, 0), mat_iron, main_col, seg=8)

# ===================== 锈色修补铁件（基座前右侧的小堆） =====================
make_box("SW_RustPiece_1", 0.50, 0.65, -0.80, -0.66, Z_BASE_TOP, Z_BASE_TOP + 0.025,
         mat_iron_rust, main_col)
make_box("SW_RustPiece_2", 0.53, 0.63, -0.78, -0.68, Z_BASE_TOP + 0.025, Z_BASE_TOP + 0.048,
         mat_iron_rust, main_col)
make_box("SW_RustPiece_3", 0.55, 0.70, -0.75, -0.62, Z_BASE_TOP + 0.048, Z_BASE_TOP + 0.070,
         mat_iron_rust, main_col)
# 一片竖立的废料板靠在砧墩边
make_box("SW_RustLeaner", 0.73, 0.78, -0.55, -0.40, Z_BASE_TOP, 0.42, mat_iron_rust, main_col)

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
ORTHO = 3.3
D = 10.0

cam_front  = create_ortho_camera("FG_Cam_Front",  (0, -D, TARGET[2]), TARGET, ORTHO, helper_col)
cam_back   = create_ortho_camera("FG_Cam_Back",   (0,  D, TARGET[2]), TARGET, ORTHO, helper_col)
cam_left   = create_ortho_camera("FG_Cam_Left",   (-D, 0, TARGET[2]), TARGET, ORTHO, helper_col)
cam_right  = create_ortho_camera("FG_Cam_Right",  ( D, 0, TARGET[2]), TARGET, ORTHO, helper_col)

cam_top = bpy.data.cameras.new("FG_Cam_Top")
cam_top.type = 'ORTHO'
cam_top.ortho_scale = ORTHO
cam_top_obj = bpy.data.objects.new("FG_Cam_Top", cam_top)
helper_col.objects.link(cam_top_obj)
cam_top_obj.location = (0, 0, D)
cam_top_obj.rotation_euler = (0, 0, 0)

cam_bot = bpy.data.cameras.new("FG_Cam_Bottom")
cam_bot.type = 'ORTHO'
cam_bot.ortho_scale = ORTHO
cam_bot_obj = bpy.data.objects.new("FG_Cam_Bottom", cam_bot)
helper_col.objects.link(cam_bot_obj)
cam_bot_obj.location = (0, 0, -D)
cam_bot_obj.rotation_euler = (math.pi, 0, 0)

cam_preview = create_ortho_camera("FG_Cam_Preview",
                                  (4.2, -5.0, 4.0), (0, 0, 1.0), 4.2, helper_col)

# ===================== 灯光与世界 =====================
if not bpy.context.scene.world:
    bpy.context.scene.world = bpy.data.worlds.new("FG_World")
world = bpy.context.scene.world
world.use_nodes = True
bg = next((node for node in world.node_tree.nodes
           if node.bl_idname == "ShaderNodeBackground"), None)
if bg:
    bg.inputs["Color"].default_value = (0.60, 0.64, 0.70, 1.0)
    bg.inputs["Strength"].default_value = 0.60

sun_data = bpy.data.lights.new("FG_Sun", 'SUN')
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("FG_Sun", sun_data)
helper_col.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(55), math.radians(10), math.radians(35))

fill_data = bpy.data.lights.new("FG_Fill", 'AREA')
fill_data.energy = 90.0
fill_data.size = 6.0
fill_obj = bpy.data.objects.new("FG_Fill", fill_data)
helper_col.objects.link(fill_obj)
fill_obj.location = (-4.0, -4.0, 5.0)
fill_obj.rotation_euler = (math.radians(55), 0, math.radians(-35))

# 火口暖光
fire_light_data = bpy.data.lights.new("FG_FireLight", 'POINT')
fire_light_data.energy = 60.0
fire_light_data.color = (1.0, 0.55, 0.20)
fire_light_data.shadow_soft_size = 0.15
fire_light_obj = bpy.data.objects.new("FG_FireLight", fire_light_data)
helper_col.objects.link(fire_light_obj)
fire_light_obj.location = (-0.45, 0.10, 0.75)

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
    ("Front",  cam_front),
    ("Back",   cam_back),
    ("Left",   cam_left),
    ("Right",  cam_right),
    ("Top",    cam_top_obj),
    ("Bottom", cam_bot_obj),
]
for view_name, cam in views:
    scene.camera = cam
    scene.render.filepath = str(OUT_VIEWS / f"Forge_DeepSeek_{view_name}.png")
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
print("Forge_DeepSeek — Build Report")
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
print(f"  Script:   Tools/Blender/Forge_DeepSeek.py")
print(f"  Blend:    {OUT_BLEND}")
print(f"  FBX:      {OUT_FBX}")
print(f"  Preview:  {OUT_PREVIEW}")
for name in ["Front", "Back", "Left", "Right", "Top", "Bottom"]:
    print(f"  View:     {OUT_VIEWS / f'Forge_DeepSeek_{name}.png'}")

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
        print(f"  {obj.name}: non-manifold edges={nm}, loose verts={lv}, loose edges={le}")

if issues == 0:
    print(f"  All {len(mesh_objs)} mesh objects: no non-manifold edges, no loose geometry.")
print(f"  Total non-manifold edges: {nm_total}")
print(f"  Total loose geometry items: {loose_total}")

print(f"\nIMPORTANT NOTE: These per-object checks detect non-manifold edges")
print(f"      and loose vertices/edges WITHIN each individual mesh.")
print(f"      They CANNOT detect or evaluate inter-object intersections,")
print(f"      overlaps, or penetrations between different mesh objects")
print(f"      (e.g. a support post embedded in a beam, or two boxes")
print(f"      overlapping). No automated inter-object intersection test")
print(f"      is performed by this script.")
print("=" * 62)
