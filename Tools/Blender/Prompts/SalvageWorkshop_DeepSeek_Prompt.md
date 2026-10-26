# SalvageWorkshop_DeepSeek — Blender 5.2.2 script request

请根据已附的《Last Landfall》废料拆解工坊六视图概念图和以下约束，直接输出一份完整、可运行的 Blender 5.2.2 Python 脚本。不要输出推理过程、零散代码、伪代码或省略号；最终回复只包含一个完整的 ```python``` 代码块。

## 资产定位

3 级食物与加工阶段的废料拆解工坊。幸存者在此拆解沉船和海岸打捞物，分类、压剪金属，再把可用材料送往锻造炉。风格为《Last Landfall》的低多边形、海盐侵蚀、漂木与再利用金属，适配游戏内第三人称视角。它必须一眼读作废料加工工位，不能像住宅或厨房。

## 体量和坐标

- 总占地控制在约 2 m × 2 m，最高约 2.15 m；最低 Z 必须为 0。
- 原点在平台中心；正面入口朝 -Y，背面为 +Y，左侧为 -X，右侧为 +X。
- 正面是敞开的装卸工位；棚屋主体在平台后半部。浅单坡瓦楞金属屋顶从前侧较低、向背侧较高。正面与背面视图里的屋顶边缘必须水平，坡向只在左右侧视图中出现。
- 龙门吊横跨 X 轴：两根立柱固定到平台前沿两侧，上方横梁连接两柱；小车位于横梁上，链条和吊钩下垂到开口内。正面看到门架全宽，左右侧面看到它沿深度对齐的侧影。
- 工作位内有液压剪/压床：底座、下砧、活动压头、液压缸/铰点和护罩都要有结构连接。加入小型滚轮废料车、两个分拣箱、少量管料/金属板和工作灯。
- 平台下方使用支撑块、横梁和交叉撑，所有立柱与构件要落地或相接，不能有漂浮件。后墙可有补丁板、斜撑与维修件；正面立柱可有少量琥珀色警示条。

## 材质和表现

海盐侵蚀的棕色木板、暗色氧化钢、褪色海绿色金属、少量锈橙补丁及克制的琥珀警示色。避免文字、商标、人物和场景背景。低多边形、干净平涂，能从正面和等距预览清楚读出龙门吊、压床和分拣功能。

## 脚本要求

- 只用 Blender 自带 `bpy`、`bmesh`、`mathutils` 和 Python 标准库；可重复运行。
- 只创建/替换集合 `SalvageWorkshop_DeepSeek` 与 `Helpers_SalvageWorkshop_DeepSeek`；不要生成旧风格拆解工坊。
- 脚本路径：`Tools/Blender/SalvageWorkshop_DeepSeek.py`。
- Blend：`Assets/LastLandfall/Art/Source/Buildings/SalvageWorkshop_DeepSeek.blend`。
- FBX：`Assets/LastLandfall/Resources/Models/Buildings/SalvageWorkshop_DeepSeek.fbx`，只导出主模型集合的网格，不导出相机/灯光。
- 等距预览：`Assets/LastLandfall/Art/Previews/Buildings/SalvageWorkshop_DeepSeek.png`。
- 正交 QA 六视图：`Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/SalvageWorkshop_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`。
- 相机方向严格为 Front(-Y)、Back(+Y)、Left(-X)、Right(+X)、Top(+Z)、Bottom(-Z)。各视图须包含完整资产且留边，不使用透视相机。
- 输出诊断：网格数、世界坐标包围盒、最低 Z、每对象非流形边和松散几何计数。
- 必须在代码注释或诊断中注明：逐对象非流形检查不能检测不同网格物体之间的穿插/重叠。

如果看不到附件，不要声称已查看图像；请严格按以上方向表和文字规格建模。最终只给完整 Python 代码块。
