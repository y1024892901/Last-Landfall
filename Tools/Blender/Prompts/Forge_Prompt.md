# Forge_DeepSeek — Blender 5.2.2 script request

请根据附件六视图概念图和以下规格，输出一份完整、可运行的 Blender 5.2.2 Python 脚本。若无法看到附件，只按文字规格建模，不能声称看过图。最终仅输出一个完整 Python 代码块，不要推理、零散代码或省略号。

## 资产用途

《Last Landfall》3 级锻造炉：把废料拆解工坊整理出的金属加工成工具、修补件和建筑构件。它是户外小型锻造工位，必须有清晰的石炉火口、烟囱、铁砧、风箱和煤料区；不能像住宅、厨房或废料剪切工坊。

## 尺寸与摆位

- 2×2 米占地，最高约 2.7 米，最低 Z=0，原点在方形石基座中心。
- 正面朝 -Y、背面 +Y、左侧 -X、右侧 +X。
- 厚石基座上布置后部偏左的石砌炉体，正面开黑铁框火口并可见橙色煤火；直立烟道从炉体接出，顶部有雨帽。
- 前右方有铁砧和木墩，砧角朝外；砧面上放一块小型热钢坯。加可操作的风箱/鼓风口、带水的浅淬火槽、煤篮、锤/钳/拨火棍工具架、少量锈色修补铁件。所有物件都要落在基座或可靠连接到炉体，不能漂浮。
- 石料为海盐风化灰米色，金属为暗色氧化铁与褪色海绿修补件，木墩为焦褐色；火口和热钢坯使用克制的发光橙色。

## 六视图

正交相机方向必须是 Front(-Y)、Back(+Y)、Left(-X)、Right(+X)、Top(+Z)、Bottom(-Z)，另有一张等距预览。六个视图保持统一比例、摆位和材质，完整包含资产并留边；侧视显示烟道高度和工位进深，俯视显示 2×2 平台的火炉/工具/砧台/煤篮/淬火槽布局，仰视显示石基座底面和支撑结构。

## 脚本和输出

- 只用 Blender 内置 bpy、bmesh、mathutils 与标准库，可重复运行。
- 只创建或替换集合 Forge_DeepSeek 与 Helpers_Forge_DeepSeek；不要生成旧风格 Forge。
- 脚本：Tools/Blender/Forge_DeepSeek.py
- Blend：Assets/LastLandfall/Art/Source/Buildings/Forge_DeepSeek.blend
- FBX：Assets/LastLandfall/Resources/Models/Buildings/Forge_DeepSeek.fbx，只导出主模型网格。
- 预览：Assets/LastLandfall/Art/Previews/Buildings/Forge_DeepSeek.png
- 六张 QA 图：Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/Forge_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png
- 打印网格数、世界坐标包围盒、最低 Z、每对象非流形边和松散几何数。
- 明确说明逐对象非流形检查无法检测不同网格对象之间的穿插/重叠。

最终脚本须完整定义所有函数、变量与路径，不能把灯光和相机导出进 FBX。
