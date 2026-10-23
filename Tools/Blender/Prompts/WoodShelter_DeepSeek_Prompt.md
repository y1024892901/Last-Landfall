# WoodShelter_DeepSeek — Blender 5.2.2 脚本请求

请为《Last Landfall》制作 0 级木棚 `WoodShelter_DeepSeek` 的完整、可运行 Blender 5.2.2 Python 脚本。项目内已有 `Assets/LastLandfall/Art/References/ScenarioBuildingViews/WoodShelter_SixViews.png` 和 `Assets/LastLandfall/Art/Previews/Buildings/WoodShelter.png`；本消息没有附图，不要声称看到了本地图片。以下文字为完整建模依据。

## 造型

- 这是沉船幸存者在岛上最早搭建的简易遮雨休息点：实用、粗粝但结构可靠，不是封闭住宅。采用 Last Landfall 的低多边形风格，风化浅木、焦油深木、粗帆布米白、少量海玻璃青绿补片、暗铁和克制的琥珀灯色。不要写实纹理、污渍、文字、logo、人物、背景、海水或地形。
- 单位 1 BU=1m，+Z 向上，正面朝 -Y，原点靠近地板中心；整个资产控制在约 1.9×1.7×1.7m，最低 Z=0。
- 底部是落地的木质短底梁和略抬高的条板地板，有清楚的横梁承托，四角加小型落脚块。
- 上方为两端三角支撑的简易单坡帆布棚：高侧梁和低侧梁沿 Y 方向延伸，坡面由高侧朝 +X 向低侧倾斜；两端各有牢固的斜木撑和横向连接。浅帆布主篷面有一块克制的补丁，必须固定在梁上，不要悬空或穿过支撑。保持一个面向正面 -Y 的开放入口。
- 背侧（+Y）设三块或少量竖向挡风板，提供遮挡但保留开放感；棚下放一只小型捆带应急物资箱。前侧或低檐下挂一盏小型琥珀灯，带底座和遮帽，连接到梁上。
- 所有横梁、端部三角支撑、帆布、挡风板、地板、物资箱和灯的位置在六个方向中保持一致。不要添加第二顶棚、睡床、人物、额外房间或背景道具。

## 脚本与输出

- 仅使用 `bpy`、`bmesh`、`mathutils`、`math`、`pathlib` 和 Python 标准库；从项目根目录运行并创建需要的目录。
- 模型集合 `WoodShelter_DeepSeek`，辅助集合 `Helpers_WoodShelter_DeepSeek`。重复运行只删除这两个精确名称的集合及无用户的 `WoodShelter_DeepSeek_` 材质，保留旧版 WoodShelter 和场景内其他资产。
- 所有材质使用 `WoodShelter_DeepSeek_` 前缀；通过节点 `bl_idname` 查找 Principled BSDF、Material Output 和 World Background。不要替换或修改仍由集合外对象使用的同名前缀材质。
- 输出：
  - `Assets/LastLandfall/Art/Source/Buildings/WoodShelter_DeepSeek.blend`
  - `Assets/LastLandfall/Resources/Models/Buildings/WoodShelter_DeepSeek.fbx`
  - `Assets/LastLandfall/Art/Previews/Buildings/WoodShelter_DeepSeek.png`
  - `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/WoodShelter_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`
- 六张 QA 图采用正交视图 Front(-Y)、Back(+Y)、Left(-X)、Right(+X)、Top(+Z)、Bottom(-Z)，统一中心、中性背景和足够留边；另生成一张居中的三分之四预览。
- FBX 只导出模型集合内 Mesh。相机和灯光放在辅助集合；保存 Blend 前恢复原相机、世界和渲染设置。
- 最后打印网格对象数、世界空间包围盒、最低 Z、非流形边数和松散顶点数，并注明逐对象拓扑检查不能检测不同对象之间的穿插。

只返回一个完整 Python 代码块，不要伪代码、占位符、省略号或缺失任何必要部分。
