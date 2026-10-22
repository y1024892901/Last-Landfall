import bpy
import bmesh
import math
from mathutils import Vector
from pathlib import Path

# ==========================================
# 1. 路径与基础设置
# ==========================================
PROJECT_ROOT = Path.cwd()
SOURCE_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Buildings"
FBX_DIR = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Buildings"
PREVIEW_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Previews/Buildings"
QA_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"

# 确保目录存在
for d in [SOURCE_DIR, FBX_DIR, PREVIEW_DIR, QA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 清理旧场景（仅清理同名集合和物体）
COLLECTION_NAME = "WaterStorageTank"
if COLLECTION_NAME in bpy.data.collections:
    col = bpy.data.collections[COLLECTION_NAME]
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(col)

# 根集合
root_collection = bpy.data.collections.new(COLLECTION_NAME)
bpy.context.scene.collection.children.link(root_collection)

# ==========================================
# 2. 材质定义
# ==========================================
def create_material(name, color, roughness=0.8, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat

mat_wood = create_material("Wood_Cedar", (0.45, 0.3, 0.15, 1.0), roughness=0.9)
mat_tank = create_material("Tank_Teal", (0.2, 0.4, 0.4, 1.0), roughness=0.6, metallic=0.3)
mat_metal = create_material("Metal_Rust", (0.7, 0.3, 0.1, 1.0), roughness=0.5, metallic=0.6)
mat_base = create_material("Concrete_Warm", (0.6, 0.55, 0.5, 1.0), roughness=0.95)
mat_dark_metal = create_material("Dark_Metal", (0.15, 0.2, 0.2, 1.0), roughness=0.4, metallic=0.7)

# ==========================================
# 3. 辅助建模函数
# ==========================================
def add_box(name, size, location, mat, parent_col):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0], size[1], size[2])
    bpy.ops.object.transform_apply(scale=True)
    obj.data.materials.append(mat)
    # 移入根集合
    for c in obj.users_collection:
        c.objects.unlink(obj)
    parent_col.objects.link(obj)
    return obj

def add_cylinder(name, radius, depth, location, mat, parent_col, rotation=(0,0,0), vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    parent_col.objects.link(obj)
    return obj

def add_pipe_segment(name, radius, start, end, mat, parent_col):
    # 基于两点生成圆柱体
    start_v = Vector(start)
    end_v = Vector(end)
    mid = (start_v + end_v) / 2
    length = (end_v - start_v).length
    direction = end_v - start_v
    
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=radius, depth=length, location=mid)
    obj = bpy.context.active_object
    obj.name = name
    
    # 旋转对齐
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = direction.to_track_quat('Z', 'Y')
    
    obj.data.materials.append(mat)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    parent_col.objects.link(obj)
    return obj

# ==========================================
# 4. 构建模型
# ==========================================

# --- 4.1 基座与支柱 ---
base_positions = [(-1.1, -0.6), (1.1, -0.6), (-1.1, 0.6), (1.1, 0.6)]
for i, (x, y) in enumerate(base_positions):
    # 石质基座
    add_box(f"Base_Stone_{i}", (0.4, 0.4, 0.4), (x, y, 0.2), mat_base, root_collection)
    # 木立柱
    add_box(f"Pillar_Wood_{i}", (0.2, 0.2, 0.8), (x, y, 0.6), mat_wood, root_collection)
    # 金属包角
    add_box(f"Base_MetalCap_{i}", (0.22, 0.22, 0.05), (x, y, 0.4), mat_dark_metal, root_collection)

# 斜撑
add_box("Brace_X_Front", (2.2, 0.1, 0.1), (0, -0.6, 0.6), mat_wood, root_collection, )
bpy.context.active_object.rotation_euler = (0, math.radians(45), 0)
add_box("Brace_X_Back", (2.2, 0.1, 0.1), (0, 0.6, 0.6), mat_wood, root_collection)
bpy.context.active_object.rotation_euler = (0, math.radians(-45), 0)
add_box("Brace_Y_Left", (0.1, 1.2, 0.1), (-1.1, 0, 0.6), mat_wood, root_collection)
bpy.context.active_object.rotation_euler = (math.radians(45), 0, 0)
add_box("Brace_Y_Right", (0.1, 1.2, 0.1), (1.1, 0, 0.6), mat_wood, root_collection)
bpy.context.active_object.rotation_euler = (math.radians(-45), 0, 0)

# --- 4.2 高架平台 ---
add_box("Platform_Main", (3.0, 1.8, 0.1), (0, 0, 1.25), mat_wood, root_collection)
# 边缘包边
add_box("Platform_Edge_Front", (3.0, 0.1, 0.12), (0, -0.9, 1.25), mat_wood, root_collection)
add_box("Platform_Edge_Back", (3.0, 0.1, 0.12), (0, 0.9, 1.25), mat_wood, root_collection)
add_box("Platform_Edge_Left", (0.1, 1.8, 0.12), (-1.5, 0, 1.25), mat_wood, root_collection)
add_box("Platform_Edge_Right", (0.1, 1.8, 0.12), (1.5, 0, 1.25), mat_wood, root_collection)

# --- 4.3 储水罐 ---
tank_positions = [(-0.65, 0), (0.65, 0)]
for i, (x, y) in enumerate(tank_positions):
    # 罐体主圆柱
    add_cylinder(f"Tank_Body_{i}", 0.6, 0.9, (x, y, 1.75), mat_tank, root_collection, vertices=16)
    # 顶部圆顶（低模半球效果，用缩放的球体或圆柱）
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.6, location=(x, y, 2.2))
    dome = bpy.context.active_object
    dome.name = f"Tank_Dome_{i}"
    dome.scale = (1, 1, 0.4)
    bpy.ops.object.transform_apply(scale=True)
    dome.data.materials.append(mat_tank)
    for c in dome.users_collection:
        c.objects.unlink(dome)
    root_collection.objects.link(dome)
    
    # 顶部盖板与五金
    add_cylinder(f"Tank_Hatch_{i}", 0.15, 0.1, (x, y, 2.38), mat_dark_metal, root_collection, vertices=8)
    # 罐体加强筋（环向）
    add_cylinder(f"Tank_Ring1_{i}", 0.61, 0.04, (x, y, 1.4), mat_tank, root_collection, vertices=16)
    add_cylinder(f"Tank_Ring2_{i}", 0.61, 0.04, (x, y, 2.1), mat_tank, root_collection, vertices=16)

# --- 4.4 管道与阀门 ---
# 顶部连通横管
add_pipe_segment("Pipe_Top_Connect", 0.08, (-0.6, 0, 1.8), (0.6, 0, 1.8), mat_tank, root_collection)
# 罐体侧面竖管
add_pipe_segment("Pipe_Left_Drop", 0.08, (-1.3, 0, 1.75), (-1.3, 0, 0.8), mat_tank, root_collection)
add_pipe_segment("Pipe_Right_Drop", 0.08, (1.3, 0, 1.75), (1.3, 0, 0.8), mat_tank, root_collection)
# 底部汇流横管
add_pipe_segment("Pipe_Bottom_Main", 0.1, (-1.3, 0, 0.8), (1.3, 0, 0.8), mat_tank, root_collection)
# 伸向营地外的出水管
add_pipe_segment("Pipe_Outflow", 0.1, (0, 0, 0.8), (0, -1.1, 0.8), mat_tank, root_collection)
# 连接罐底与汇流管的短管
add_pipe_segment("Pipe_Tank1_Bottom", 0.08, (-0.65, 0, 0.8), (-0.65, 0, 1.3), mat_tank, root_collection)
add_pipe_segment("Pipe_Tank2_Bottom", 0.08, (0.65, 0, 0.8), (0.65, 0, 1.3), mat_tank, root_collection)

# 阀门（侧边与底部）
def add_valve(name, location, rotation, parent_col):
    # 阀体
    add_cylinder(f"{name}_Body", 0.12, 0.1, location, mat_metal, parent_col, rotation=rotation, vertices=12)
    # 阀轮（用细圆柱交叉）
    bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.02, location=location, rotation=rotation)
    wheel = bpy.context.active_object
    wheel.name = f"{name}_Wheel"
    wheel.data.materials.append(mat_metal)
    for c in wheel.users_collection:
        c.objects.unlink(wheel)
    parent_col.objects.link(wheel)

add_valve("Valve_Left", (-1.3, 0.1, 0.8), (math.radians(90), 0, 0), root_collection)
add_valve("Valve_Right", (1.3, 0.1, 0.8), (math.radians(90), 0, 0), root_collection)

# --- 4.5 检修梯 ---
ladder_x = 0
ladder_y = -0.95
ladder_w = 0.4
ladder_h = 1.3
# 侧边大梁
add_pipe_segment("Ladder_Rail_L", 0.04, (-ladder_w/2, ladder_y, 0), (-ladder_w/2, ladder_y, ladder_h), mat_wood, root_collection)
add_pipe_segment("Ladder_Rail_R", 0.04, (ladder_w/2, ladder_y, 0), (ladder_w/2, ladder_y, ladder_h), mat_wood, root_collection)
# 横档
for i in range(5):
    z = 0.2 + i * 0.25
    add_box(f"Ladder_Rung_{i}", (ladder_w, 0.05, 0.05), (0, ladder_y, z), mat_wood, root_collection)
# 梯子顶部挂钩/固定
add_box("Ladder_Hook", (0.5, 0.1, 0.05), (0, -0.85, 1.3), mat_dark_metal, root_collection)

# ==========================================
# 5. 合并相邻部件并清理网格（基础质量诊断）
# ==========================================
# 这里不进行过度合并，保持物体可读性，仅清理游离几何和法线
for obj in root_collection.objects:
    if obj.type == 'MESH':
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        # 移除松散几何
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        # 重新计算法线
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()

# ==========================================
# 6. 设置相机与渲染
# ==========================================
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT' # 兼容 Blender 4.2+ / 5.0+
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'

# 灯光
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.data.angle = math.radians(30)
sun.rotation_euler = (math.radians(45), 0, math.radians(45))
for c in sun.users_collection:
    c.objects.unlink(sun)
# 不放入根集合，单独管理，输出时排除

bpy.ops.object.light_add(type='AREA', location=(-5, -5, 5))
area = bpy.context.active_object
area.data.energy = 500
area.data.size = 10
area.rotation_euler = (math.radians(60), 0, math.radians(-45))
for c in area.users_collection:
    c.objects.unlink(area)

# 相机
bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 4.0 # 覆盖整个建筑
scene.camera = cam

# 渲染函数
def render_view(cam_loc, cam_rot, output_path):
    cam.location = cam_loc
    cam.rotation_euler = cam_rot
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)

# 视角定义 (位置, 旋转, 文件名)
views = [
    ((0, -10, 1.2), (math.radians(90), 0, 0), "WaterStorageTank_Front.png"),
    ((0, 10, 1.2), (math.radians(90), 0, math.radians(180)), "WaterStorageTank_Back.png"),
    ((-10, 0, 1.2), (math.radians(90), 0, math.radians(-90)), "WaterStorageTank_Left.png"),
    ((10, 0, 1.2), (math.radians(90), 0, math.radians(90)), "WaterStorageTank_Right.png"),
    ((0, 0, 10), (0, 0, 0), "WaterStorageTank_Top.png"),
    ((0, 0, -10), (math.radians(180), 0, 0), "WaterStorageTank_Bottom.png"),
]

# 渲染六视图
for loc, rot, filename in views:
    render_view(loc, rot, QA_DIR / filename)

# 渲染等距预览
render_view((6, -6, 6), (math.radians(60), 0, math.radians(45)), PREVIEW_DIR / "WaterStorageTank.png")

# ==========================================
# 7. 导出与保存
# ==========================================
# 导出 FBX（选中模型，排除相机和灯光）
bpy.ops.object.select_all(action='DESELECT')
for obj in root_collection.objects:
    obj.select_set(True)
    
# 临时取消选择相机和灯光
for obj in bpy.context.selected_objects:
    if obj.type in ['CAMERA', 'LIGHT']:
        obj.select_set(False)

fbx_path = FBX_DIR / "WaterStorageTank.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path),
    use_selection=True,
    apply_scale_options='FBX_SCALE_ALL',
    object_types={'MESH', 'EMPTY'},
    bake_space_transform=True
)

# 保存 .blend
blend_path = SOURCE_DIR / "WaterStorageTank.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# ==========================================
# 8. 诊断信息打印
# ==========================================
# 计算包围盒
min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')

for obj in root_collection.objects:
    if obj.type == 'MESH':
        for v in obj.bound_box:
            world_v = obj.matrix_world @ Vector(v)
            min_x = min(min_x, world_v.x)
            min_y = min(min_y, world_v.y)
            min_z = min(min_z, world_v.z)
            max_x = max(max_x, world_v.x)
            max_y = max(max_y, world_v.y)
            max_z = max(max_z, world_v.z)

bbox_size = (max_x - min_x, max_y - min_y, max_z - min_z)
obj_count = len([o for o in root_collection.objects if o.type == 'MESH'])

print("========== WaterStorageTank 生成完成 ==========")
print(f"对象数量 (Mesh): {obj_count}")
print(f"包围盒尺寸 (X, Y, Z): ({bbox_size[0]:.3f}, {bbox_size[1]:.3f}, {bbox_size[2]:.3f}) 米")
print(f"最小高度 (Z): {min_z:.3f}")
print(f"FBX 输出路径: {fbx_path}")
print(f"Blend 输出路径: {blend_path}")
print(f"预览图路径: {PREVIEW_DIR / 'WaterStorageTank.png'}")
print(f"QA 视图输出目录: {QA_DIR}")
print("=============================================")

# 基础网格质量诊断（非流形边检查）
non_manifold_count = 0
for obj in root_collection.objects:
    if obj.type == 'MESH':
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
        non_manifold_count += len(non_manifold_edges)
        bm.free()

if non_manifold_count > 0:
    print(f"[诊断] 发现 {non_manifold_count} 条非流形边，建议检查管道接口和基座是否穿插。")
else:
    print("[诊断] 未发现非流形边，网格拓扑基本健康。")
print("[注意] 俯视图和仰视图因正交相机视角限制，可能包含少量视觉遮挡。建议逐张查看 QA 渲染图。")