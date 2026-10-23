# Shipyard_DeepSeek — Blender 5.2.2 建模脚本请求

请按以下规格生成一份完整、可运行的 Blender 5.2.2 Python 脚本。项目已有 `Assets/LastLandfall/Art/References/ScenarioBuildingViews/Shipyard_SixViews.png` 作为基础轮廓和方向参考，以及 `Assets/LastLandfall/Art/Previews/Infrastructure/Shipyard.png` 作为旧资产风格参考；本条消息没有附图，不要声称你看到了本地图片，以下文字是完整依据。

## 背景与造型

这是《Last Landfall》4 级船坞，用于在海岛聚落建造、检修并下水区域救援艇。它和普通渔船码头、救援快艇停靠码头不同，重点是滑道、艇体支撑、吊装龙门和修理工位。保留现有概念的开放式木质滑台、未完工救援艇、海绿色龙门吊和侧边设备小屋的结构语言；做成简洁风格化低多边形游戏资产，不用贴图、写实污渍、文字、logo、人物、水体或海岸背景。

- Blender 单位 1 BU = 1 米，+Z 向上，中心靠近原点，正面朝 -Y。整体控制在 5.0 × 4.0 × 4.2 米以内，最低点 Z=0。
- 基础为一组木质滑道：两根长向龙骨/滑轨、分布均匀的横向枕木、少量钢制连接件和四至六个浅灰混凝土垫块。零件要落在一起，支撑关系清晰。
- 滑道上放一艘处于建造/维修中的小型区域救援艇：约 3.2–3.5 米长的未完工低多边形船体，能读出龙骨、舷侧板、几道肋骨和船首/船尾；艇体由木质托架/横向支撑承托，不要做成完整有引擎的成品艇。
- 滑道上方设海绿色两柱龙门架，横梁跨过船体，带简洁锈橙色手拉吊车、短链条和吊钩。立柱有混凝土基脚，后方以深色斜撑连接立柱与滑台，横梁和吊钩不得悬空或穿过船壳。
- 滑道一侧（+X）布置紧凑的有顶检修/工具小屋，含清晰门板、淡青色金属屋顶和少量工具柜；必须把它限制在总占地边界内，不能挡住主要船体或龙门结构。
- 配色采用风化浅木、焦油深木、褪色海绿色金属、暖灰混凝土、暗铁和少量锈橙。大形体优先，六个方向中艇体、龙门、吊链、支撑、侧屋的位置完全一致。
- 连接所有横梁、吊链、船体支架和工具屋部件；避免断链、无支撑横梁、穿模、零长度几何、几何悬空或低于 Z=0。不要复制救援码头的栈桥或添加第二艘船。

## 脚本与交付

- 仅使用 Blender 内置 `bpy`、`bmesh`、`mathutils`、`math` 和 Python 标准库；从项目根目录运行，使用 `pathlib` 并自动创建目录。
- 模型集合 `Shipyard_DeepSeek`，相机/灯光集合 `Helpers_Shipyard_DeepSeek`；可重复运行，只删除/替换这两个精确匹配的集合及无用户的 `Shipyard_DeepSeek_` 材质，保留其他场景内容和基础 `Shipyard` 资产。
- 所有材质名使用 `Shipyard_DeepSeek_` 前缀。通过节点 `bl_idname` 查找 Principled BSDF、Material Output 和 World Background，不依赖本地化节点名称。
- 输出文件：
  - Blend：`Assets/LastLandfall/Art/Source/Infrastructure/Shipyard_DeepSeek.blend`
  - FBX：`Assets/LastLandfall/Resources/Models/Infrastructure/Shipyard_DeepSeek.fbx`
  - 预览：`Assets/LastLandfall/Art/Previews/Infrastructure/Shipyard_DeepSeek.png`
  - 六向 QA：`Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/Shipyard_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`
- 渲染 6 张完整正交视图：Front(-Y)、Back(+Y)、Left(-X)、Right(+X)、Top(+Z)、Bottom(-Z)；统一中心、背景、分辨率和足够大的正交尺度，使整套 5×4×4.2 米模型不裁切。另渲染一张居中留边的等距预览。
- FBX 只导出 `Shipyard_DeepSeek` 集合里的 Mesh，不导出辅助集合。临时改动的相机、世界和渲染设置需在保存前恢复。
- 最后打印模型网格数、世界包围盒、最低 Z、非流形边数、松散几何数，并说明逐对象拓扑检查不能检测不同对象之间的穿插。

请只返回一个完整 Python 代码块，不能使用占位符、伪代码、省略号，也不要生成其他资产。
