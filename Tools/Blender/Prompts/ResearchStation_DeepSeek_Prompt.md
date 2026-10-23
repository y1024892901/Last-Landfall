# ResearchStation_DeepSeek — Blender 5.2.2 脚本请求

请为《Last Landfall》制作 0 级研究站 `ResearchStation_DeepSeek` 的完整、可运行 Blender 5.2.2 Python 脚本。项目已有 `Assets/LastLandfall/Art/References/ScenarioBuildingViews/ResearchStation_SixViews.png` 和 `Assets/LastLandfall/Art/Previews/Buildings/ResearchStation.png`，本条消息没有附图，不要声称看到了本地图片。下面文字已完整整理概念图和旧版模型的主要结构。

## 造型与坐标

- 这是沉船幸存者据点最初的现场研究站，用于检验水样、记录天气和整理总部图纸，不是大型实验室或普通住宅。采用 Last Landfall 低多边形风格：海玻璃青绿色墙体、淡青灰金属屋面、风化浅木门窗框和样品台、暖灰混凝土基座、暗铁紧固件、少量克制的琥珀色标记。不要真实贴图、污渍、文字、logo、人物、背景建筑、地形或水体。
- 1 BU=1m，+Z 向上，正面和入口朝 -Y，原点靠近建筑基座中心。主建筑基座约 2.35×2.05m，完整资产（含正面样品台、屋顶气象仪器和侧面挂板）约 2.75×2.65m，高度不超过 2.8m，最低 Z=0。屋顶檐口、仪器和侧挂件都要纳入包围盒。
- 单层紧凑方形小屋，落在浅暖灰混凝土/石砌基座上，基座和地板略高于地面。四角有木质收边柱；墙体为完整封闭结构。正面 -Y 左侧为浅色单扇门，右侧为带青绿色玻璃和清楚竖向中梃的观察窗。门旁可有小型门牌色块，但不要文字。
- 正面靠窗设置一张短而结实的风化木样品工作台，使用两条支腿或托架可靠支撑，台面放置四只间距一致的小型封盖水样瓶。物件都贴合台面，不能悬浮或穿插；不要添加无关杂物。
- 使用简洁的对称人字双坡金属屋顶：屋脊沿 X 轴，坡面朝 ±Y 两侧落下，屋檐略超出墙体；清楚可见连续屋脊盖板、双侧屋面、少量规则站缝/加强条。顶部后侧（+Y）安装一套简洁且结构连贯的气象采样设备：稳固桅杆、小型雨量收集杯、朝向明确的风向标短横杆和尾翼。器材不超过总高限制，不要做科幻天线阵列。
- 一侧外墙有窄小的现场记录板/样品图板，以支架固定，板面只用少量无文字的几何色条表示记录；另一侧可放由短支臂托住的小型采样/读数盒和短刻度柱，全部固定在墙面上。背面以简洁墙面为主，低处可放一只带绑带的小型样品运输箱。所有侧面设备和箱体须连接到墙或地面，禁止悬空。
- 六方向构造必须一致：正面门窗与工作台；背面简洁并展示运输箱；左右侧可区分外墙设备和人字屋顶；俯视可辨双坡、屋脊、缝条和气象设备；仰视展示基座/地板底部。不要额外加入第二建筑、烟囱、太阳能阵列、睡床、家具或背景道具。

## 脚本与输出

- 仅使用 `bpy`、`bmesh`、`mathutils`、`math`、`pathlib` 和 Python 标准库；从项目根目录运行并按需创建目录。
- 模型集合 `ResearchStation_DeepSeek`，辅助集合 `Helpers_ResearchStation_DeepSeek`。重复运行只清理这两个完全匹配的集合和无用户的 `ResearchStation_DeepSeek_` 材质，保留旧版 ResearchStation 及其他资产。
- 材质名统一以 `ResearchStation_DeepSeek_` 开头。通过节点 `bl_idname` 查找 Principled BSDF、Material Output、World Background；如果已有同名前缀材质仍由本集合外对象使用，不要替换、删除或修改它。
- 输出：
  - `Assets/LastLandfall/Art/Source/Buildings/ResearchStation_DeepSeek.blend`
  - `Assets/LastLandfall/Resources/Models/Buildings/ResearchStation_DeepSeek.fbx`
  - `Assets/LastLandfall/Art/Previews/Buildings/ResearchStation_DeepSeek.png`
  - `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/ResearchStation_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`
- 六张 QA 图用正交相机，方向严格为 Front(-Y)、Back(+Y)、Left(-X)、Right(+X)、Top(+Z)、Bottom(-Z)，对齐同一模型中心并留出一致边距；另生成一张居中的三分之四预览。使用中性背景和柔和棚拍光，不要把其他场景物体渲染进图。
- FBX 只导出模型集合中的 Mesh；相机和灯光放在辅助集合。临时渲染前可隔离场景外对象，但保存 Blend 前恢复它们的可见状态以及原相机、世界和渲染设置。不得保存默认启动立方体或场景外模型混入本资产。
- 最后报告 Mesh 对象数、世界空间包围盒、最低 Z、非流形边和松散顶点，并说明逐对象拓扑检查不能检测不同对象之间的穿插。

只返回一个完整 Python 代码块，不要伪代码、占位符、省略号或省略任何必要内容。
