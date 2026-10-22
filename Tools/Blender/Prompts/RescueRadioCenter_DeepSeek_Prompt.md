# RescueRadioCenter_DeepSeek — Blender 5.2.2 script request

请根据附件六视图概念图和以下规格，输出一份完整、可运行的 Blender 5.2.2 Python 脚本。若无法看到附件，只按文字规格建模，不能声称看过图。最终仅输出一个完整 Python 代码块，不要推理、零散代码或省略号。

## 资产用途

《Last Landfall》4 级区域救援设施：作为区域调度和长距离无线电中继中心，联系多个岛屿并协调救援船队。它应明显比 0 级初始通讯中心更强，但仍是灾后海岸聚落用回收木材、金属和电气部件搭建的低矮、实用工位。保留木平台与小型操作舱的视觉语言，突出更大型的定向通信设备、稳固桅杆和应急调度功能。

## 尺寸与摆位

- 木平台最大占地 2×2 米，最低 Z=0，天线尖端最高约 2.7 米，原点位于平台中心。
- 正面朝 -Y，背面 +Y，左侧 -X，右侧 +X。
- 约 1.45×1.25 米的低矮木质操作舱位于平台中心略偏后；前面朝 -Y，左侧有入口门，右侧有加固的海蓝色无线电观察窗和象牙色救援十字标志。
- 平台架高约 0.2 米，用四根可靠支脚和可见的底部横梁/斜撑承托；平台分为耐候木板，屋顶是海绿色回收金属板，带深色接缝和锈橙色修补板。
- 屋顶新增区域通信设备：左侧有直径约 0.48 米的定向微波碟，带俯仰支架和结构底座；右后侧有加固桅杆、三单元定向 Yagi 横向阵列、四根清楚连接到屋顶锚点的拉索，以及桅杆顶部琥珀色应急信标。
- 背墙有防水控制/电池柜、保险丝检修盖和粗电缆导管，电缆沿墙落到屋顶/平台，不漂浮；平台侧有紧凑线缆盘和信号备用电池箱。
- 材质为焦油深木、盐蚀浅木、褪色海绿色金属、救援橙色补丁、风暴蓝玻璃、暗铁和少量象牙标记。外观低多边形、形体清晰，在游戏视距可辨识。

## 六视图

必须输出统一正交比例的 Front(-Y)、Back(+Y)、Left(-X)、Right(+X)、Top(+Z)、Bottom(-Z) 六图，另外输出等距预览。视图完整包含资产并留边；正面显示门、无线电窗和救援标志；背面清楚显示控制柜和电缆走线；左右侧均看得到微波碟的侧面、桅杆和拉索；俯视清楚呈现碟面、舱体、桅杆、天线阵列在 2×2 平台上的位置；仰视显示平台横梁、斜撑和四根支脚。方向、部件和材质在六张图中必须一致，不能用透视相机代替正交视图。

## 脚本和输出

- 只用 Blender 内置 bpy、bmesh、mathutils 与标准库，可重复运行。
- 仅删除/替换集合 RescueRadioCenter_DeepSeek 与 Helpers_RescueRadioCenter_DeepSeek；保留原版 RescueRadioCenter。
- 关键部件和灯/相机放入独立的主模型/辅助集合。材质使用专属 `RRC_` 前缀，只清理此候选集合实际使用且已无用户的旧材质；不要清空全局孤立网格或其他项目数据。
- Principled BSDF 与世界 Background 节点按 `bl_idname` 查找，避免不同语言界面的名称差异。
- 脚本：Tools/Blender/RescueRadioCenter_DeepSeek.py
- Blend：Assets/LastLandfall/Art/Source/Buildings/RescueRadioCenter_DeepSeek.blend
- FBX：Assets/LastLandfall/Resources/Models/Buildings/RescueRadioCenter_DeepSeek.fbx，只导出主模型集合的网格，不导出相机、灯光、地面或辅助集合。
- 预览：Assets/LastLandfall/Art/Previews/Buildings/RescueRadioCenter_DeepSeek.png
- 六张 QA 图：Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/RescueRadioCenter_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png
- 打印主模型网格数、世界坐标包围盒、最低 Z、每对象非流形边与松散几何数，并写明逐对象检查无法检测不同网格对象之间的穿插/重叠。

最终脚本须完整定义所有函数、变量和路径，不能覆盖 RescueRadioCenter 原版，也不能把灯光和相机导出进 FBX。
