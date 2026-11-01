# RescueOutpost_DeepSeek — Blender 5.2.2 脚本请求

请生成一份完整、可运行的 Blender 5.2.2 Python 脚本，用于《Last Landfall》的 4 级海上救援前哨。项目内已有 `Assets/LastLandfall/Art/References/ScenarioBuildingViews/RescueOutpost_SixViews.png` 和 `Assets/LastLandfall/Art/Previews/Buildings/RescueOutpost.png`；本条消息没有附图，不要声称你看到了本地图片。以下规格和文字是建模依据。

## 造型和尺寸

- 这是供救援队值守、观察海面并发出信号的高脚救援前哨，不是住宅或普通瞭望塔。低多边形、色彩克制，沿用海岛建筑的风化浅木、焦油深木、海玻璃青绿、淡青灰金属、暖灰混凝土、深铁和少量救援橙/琥珀色。无写实贴图、文字、logo、人物、背景地形或水体。
- 单位 1 BU = 1 m，+Z 向上，正面朝 -Y，原点靠近支撑平台中心。平台约 1.9×1.7 m；完整模型含正面楼梯宽度不超过 2.2×3.4 m，总高不超过 4.2 m，最低点 Z=0。
- 高脚木平台：四根牢固的深色方木支柱落地，位于平台四角；加横向连接和适量斜撑。平台高度约 2.2 m，木板甲板有清晰厚度；平台周边设置结实的护栏，正面楼梯开口处留通道。
- 前方（-Y）设置一座居中的木楼梯，从地面稳固接到平台，使用两根斜梁和均匀分布的独立踏板；踏板不能悬空、穿模或低于 Z=0。
- 平台上是一间紧凑的救援值班舱，墙体为海绿色/青灰色，屋顶为略微悬挑的浅青灰金属平屋顶。正面和侧面有清楚的观察窗；舱门面向平台并可从楼梯进入。窗框、门和护栏保持清晰且不互相遮挡。
- 平台前护栏上挂一个小型救生圈；舱顶中央或偏后有短桅杆、琥珀色救援信号灯及浅色帽檐，可配简洁短无线电天线。灯具和天线必须与屋顶或桅杆实体连接。
- 六向中四根立柱、舱体、护栏、楼梯、救生圈和屋顶灯位置一致；所有构件受力和连接关系可信。不要添加第二座建筑、船只、海水或地形。

## 脚本和文件

- 仅使用 `bpy`、`bmesh`、`mathutils`、`math`、`pathlib` 和 Python 标准库；从项目根目录运行，自动创建目录。
- 模型集合 `RescueOutpost_DeepSeek`，相机灯光辅助集合 `Helpers_RescueOutpost_DeepSeek`。重复运行只清理这两个精确匹配的集合和无用户的 `RescueOutpost_DeepSeek_` 材质；保留场景其他内容及旧版 RescueOutpost。
- 所有材质以 `RescueOutpost_DeepSeek_` 开头；通过节点 `bl_idname` 查找 Principled BSDF、Material Output、World Background。材质重用时不得破坏集合以外对象正在使用的材质。
- 输出：
  - `Assets/LastLandfall/Art/Source/Buildings/RescueOutpost_DeepSeek.blend`
  - `Assets/LastLandfall/Resources/Models/Buildings/RescueOutpost_DeepSeek.fbx`
  - `Assets/LastLandfall/Art/Previews/Buildings/RescueOutpost_DeepSeek.png`
  - `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/RescueOutpost_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`
- 六张正交 QA 图视向依次为 Front(-Y)、Back(+Y)、Left(-X)、Right(+X)、Top(+Z)、Bottom(-Z)，共享模型中心和中性背景，尺寸留边充足；另渲染居中的三分之四预览。
- FBX 只导出模型集合内的 Mesh。临时改动的活动相机、世界和渲染设置在保存 Blend 前恢复；渲染灯光与相机放入辅助集合。
- 最后打印 Mesh 数、世界包围盒、最低 Z、逐对象非流形边数和松散顶点数，并说明逐对象拓扑检查无法检测对象之间的穿插。

只返回一个完整 Python 代码块，不得使用占位符、伪代码、省略号或省略任何必要部分。
