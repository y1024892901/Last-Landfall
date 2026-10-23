# DirtRoadTiles_DeepSeek — Blender 5.2.2 脚本请求

请为《Last Landfall》制作一套独立的 0 级基础土路模块 `DirtRoadTiles_DeepSeek`，生成完整、可运行的 Blender 5.2.2 Python 脚本。本条消息没有附图或源代码附件，不要声称看到了本地文件；下方文字已包含完整的模块、尺寸、连接、输出和 QA 规格。项目内现有木板路 `RoadTiles` 必须保持不变。本套件使用独立文件名和材质前缀。

## 造型与尺寸

- 这是沉船幸存者在岛屿基地上最初铺设的步行土路。风格为 Last Landfall 的简洁低多边形游戏美术：压实的暖赭色/灰棕色土、浅褐砾石、少量不规则石块和克制的稀疏草芽。颜色层次靠少量独立几何面和材质色块完成，不用照片纹理、噪点贴图、文字、logo、人物、背景地形、海水或额外道具。
- 1 BU = 1 m，+Z 向上。每片是 1 × 1 m 方格，原点在本格中心，拼接路面中心线宽度严格为 0.50 m；道路表面统一位于约 Z=0.10 m，最低几何不低于 Z=0。相邻拼块的路面在格边高度和宽度必须一致，不留缝、不重叠成凸坎。
- 主路由连续压实土面构成，边缘略粗、中央稍平，允许极浅的两道车辙或脚踩压痕，但不要挖出会破坏连接的沟槽。砾石、嵌石和草芽只放在路面范围内或路肩内侧；不得超出 1 × 1 m 格子，不得阻挡路口，不得高到妨碍步行。不同模块的土色和碎石分布轻微变化，整体克制、一致。
- 模块端口方向必须与现有道路代码一致：`DirtRoadStraight` 为 North/South；`DirtRoadCorner` 为 South/East；`DirtRoadTee` 为 West/East/South；`DirtRoadCross` 四向；`DirtRoadEnd` 为 South。正面方向为 -Y。弯道、T 口、十字交叉和封闭端的中间接缝要自然，拼成连续路面。
- 形状边缘定义以真实 Mesh 几何为准，不依赖仅在编辑器中可见的材质或贴图。路面顶面在每个开放边的宽度区间内覆盖完整且同高；封闭边不能被误判成连通端口。

## 文件与实现要求

- 仅使用 `bpy`、`bmesh`、`mathutils`、`math`、`pathlib` 和 Python 标准库。脚本可从项目根目录运行并自动创建输出目录。使用自己的 `DirtRoadTiles_DeepSeek` 集合名及 `DirtRoadTiles_DeepSeek_` 材质前缀，只清理自己精确命名的集合和无用户前缀材质，不改动现有木板道路及场景其他内容。
- 将五个模块排成一个易读的源场景；给每个模块一个以中心为原点的 root，模块内 Mesh 使用稳定、清楚的名称。FBX 必须分别导出五个模块，文件名为 `DirtRoadStraight_DeepSeek.fbx`、`DirtRoadCorner_DeepSeek.fbx`、`DirtRoadTee_DeepSeek.fbx`、`DirtRoadCross_DeepSeek.fbx`、`DirtRoadEnd_DeepSeek.fbx`，只导出相应模块的 Mesh，不包含 root Empty、相机、灯光或地面。
- 输出：
  - `Assets/LastLandfall/Art/Source/Infrastructure/DirtRoadTiles_DeepSeek.blend`
  - `Assets/LastLandfall/Resources/Models/Infrastructure/DirtRoadStraight_DeepSeek.fbx`、`DirtRoadCorner_DeepSeek.fbx`、`DirtRoadTee_DeepSeek.fbx`、`DirtRoadCross_DeepSeek.fbx`、`DirtRoadEnd_DeepSeek.fbx`
  - `Assets/LastLandfall/Art/Previews/Infrastructure/DirtRoadTiles_DeepSeek.png`
  - 六向 QA：`Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/DirtRoadTiles_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`
  - 连接诊断：`Assets/LastLandfall/Art/Previews/Infrastructure/DirtRoadTiles_DeepSeek_Connectivity_QA.json`
- QA 六视图均须以正交相机查看整组五块拼块：Front(-Y)、Back(+Y)、Left(-X)、Right(+X)、Top(+Z)、Bottom(-Z)，中心、背景和比例一致。另渲染居中的三分之四预览。临时渲染环境、相机、世界、分辨率、输出路径和选择状态必须在保存 Blend 前恢复；相机与灯光放在独立辅助集合，Blend 中不应残留默认立方体。
- 实际射线采样五种模块的四条边，逐边核对开放端口；检验 16 种北/东/南/西邻接掩码和四个方向的两格拼接。记录每边覆盖采样数、模块端口和总结果。计算并打印 Mesh 数、世界包围盒、最低 Z、非流形边数、松散顶点数。诊断说明：逐对象拓扑检查无法判断不同对象之间是否互相穿插。

只返回一个完整 Python 代码块，不要占位符、伪代码、省略号或遗漏必需函数。
