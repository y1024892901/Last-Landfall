# MedicalTent_DeepSeek — Blender 5.2.2 脚本请求

请为《Last Landfall》制作 0 级医疗帐篷 `MedicalTent_DeepSeek` 的完整、可运行 Blender 5.2.2 Python 脚本。随本提示附上的 `MedicalTent_SixViews.png` 是主要造型参考；它展示同一帐篷的正面（-Y）、背面（+Y）、左右侧面（-X/+X）、顶视和等距视图。请按参考保留浅色帐篷、医疗十字、青绿色入口布、木质地台和外露 A 字支撑的轮廓。

## 造型与坐标

- 这是沉船幸存者建立的 0 级野外急救帐篷，使用回收木料、耐候布和有限的医疗用品。采用 Last Landfall 低多边形风格：旧象牙白/暖灰帆布、少量补丁青绿布、风化浅木地台、焦黑木支杆、柔和珊瑚粉医疗十字。保持清楚的色块和厚实简洁的轮廓，不用照片贴图、脏污噪点、人物、血迹、文字、logo、背景建筑、地形或水体。
- 1 BU=1m，+Z 向上，帐篷入口朝 -Y，原点靠近地台中心。整体占地约 2×2m，最高点不超过 2.3m，最低 Z=0。入口门帘、A 架、拉撑、地台脚和附着用品都纳入包围盒。
- 帐篷搭在略高于地面的木质平台上：约 1.9×1.8m，数块可辨木板、周边承梁和四角短垫木。平台结构要落地、稳定，不能让支脚或布面悬空。
- 主要结构是紧凑的 A 字帐篷：两片对称浅色帆布从沿 Y 轴的屋脊斜落至平台两侧，木质或暗色金属框架支撑两端，屋脊短梁连接前后框架。帆布应有真实厚度但保持封闭、连续，不要做成互相穿插的多层大板。两侧可见从屋脊落到平台边缘的支撑脚和简洁横向拉撑；支撑接头必须贴合。
- 正面 -Y 设置清晰的单一入口：青绿色内层门帘位于中央，左右浅色门襟向两侧束起，能看出入口开口；入口上方安装暖白色方形医疗标记板和珊瑚粉十字。不要在门口放大型家具或堵住通道。
- 帐篷内部可从正面看见一张低矮折叠病床/担架和一只小型野外急救包。床面用青绿色布，支架简洁，物件贴合地台且不穿透帐篷外布。用品数量克制，不添加药瓶阵列、器械墙或无关杂物。
- 背面 +Y 以完整、无开口的浅色后帐布为主，呈现边缘固定带和少量木框；两侧保持结构对称。俯视应能辨认帐篷屋脊、双坡帆布和木板平台；底视展示承梁、板底和角垫木。
- 六个方向必须对应同一模型并保持入口方向正确。医疗十字只出现在正面；侧面主要表现 A 架、帆布坡面、拉撑和一只贴近平台的小型补给箱。所有零件都必须附着、支撑或落地，避免悬浮、穿模以及尺寸过大的外伸部件。

## 脚本与输出

- 仅使用 `bpy`、`bmesh`、`mathutils`、`math`、`pathlib` 和 Python 标准库；从项目根目录运行并按需创建目录。
- 模型集合 `MedicalTent_DeepSeek`，辅助集合 `Helpers_MedicalTent_DeepSeek`。重复运行只清理这两个完全匹配的集合和无用户的 `MedicalTent_DeepSeek_` 材质，保留旧版 MedicalTent 及其他场景资产。
- 材质名统一以 `MedicalTent_DeepSeek_` 开头。通过节点 `bl_idname` 查找 Principled BSDF、Material Output、World Background；如果已有同名前缀材质仍由本集合外对象使用，不要替换、删除或修改它。
- 输出：
  - `Assets/LastLandfall/Art/Source/Buildings/MedicalTent_DeepSeek.blend`
  - `Assets/LastLandfall/Resources/Models/Buildings/MedicalTent_DeepSeek.fbx`
  - `Assets/LastLandfall/Art/Previews/Buildings/MedicalTent_DeepSeek.png`
  - `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/MedicalTent_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`
- 六张 QA 图使用正交相机，方向严格为 Front(-Y)、Back(+Y)、Left(-X)、Right(+X)、Top(+Z)、Bottom(-Z)，对齐同一模型中心并留出一致边距；另生成一张居中的三分之四预览。使用中性背景和柔和棚拍光，不要把其他场景物体渲染进图。
- FBX 只导出模型集合中的 Mesh；相机和灯光放在辅助集合。临时渲染前可隔离场景外对象，但保存 Blend 前恢复它们的可见状态以及原相机、世界和渲染设置。不得保存默认启动立方体或场景外模型混入本资产。
- 最后报告 Mesh 对象数、世界空间包围盒、最低 Z、非流形边和松散顶点，并说明逐对象拓扑检查不能检测不同对象之间的穿插。

只返回一个完整 Python 代码块，不要伪代码、占位符、省略号或省略任何必要内容。
