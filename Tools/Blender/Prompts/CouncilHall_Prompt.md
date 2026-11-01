# CouncilHall_DeepSeek — Blender 5.2.2 建模脚本请求

请依据随本提示上传的 `CouncilHall_Concept_SixViews_DeepSeek.png` 和以下约束，为《Last Landfall》制作 5 级社区议事厅 `CouncilHall_DeepSeek` 的完整、可运行 Blender 5.2.2 Python 脚本。它是沉船后岛屿聚落共同讨论、制定规则和接待居民的公共建筑，应当稳固、亲切、便于维修；不能像奢华市政厅或军事设施。概念图仅作造型参考，尺寸和交付规范以下文为准。不要声称参考图外的本地文件已上传。

## 建筑造型

- 一栋独立的一层议事厅，低多边形游戏美术；项目清单为 4×5 占地、最高约 4.1 米。主体约 8.4 m 宽 × 9.4 m 深，含屋檐、门廊、踏步和坡道后总体不得超过 X=9.6 m、Y=12.0 m、Z=4.1 m；最低 Z=0。1 BU=1 m，+Z 向上，主入口朝 -Y，原点位于主体平面中心附近。
- 主体采用架高木地板，暖灰石墩间距合理，承托深色回收木梁、立柱和地板。前面设置宽约 2.8–3.2 m 的公共门廊和双开门，门廊有坚固立柱、斜撑、扶手及宽阔踏步。可在门廊右侧设置一段简洁防滑坡道；坡道必须有地面落点、侧梁、扶手并保持在总尺寸包络内。
- 外墙为盐蚀暖棕木板，深色回收木角柱、横梁和清晰可见的结构支撑。正立面中央设置宽双开木门，门两侧适度留出空间，可有一两组窗。门旁设空白社区公告板，不得包含文字、徽标、牌号或旗帜。
- 左右长墙均匀布置三组较宽的烟蓝玻璃会堂窗，配厚实木框和简洁暴雨百叶；后立面简洁，带少量高窗或通风口。窗门必须有明确分层和厚度，墙体封闭完整。
- 使用宽矮对称的四坡或折坡海绿色波纹金属屋顶，明确覆盖主体和门廊；只设窄屋脊盖板、少量青灰维修补片、檐沟和可见落水管。屋顶不得加钟楼、塔、天线、太阳能板或高烟囱。
- 材质为盐蚀浅棕木、深色回收结构木、褪色海绿/青灰金属、暖灰石墩和烟蓝玻璃。低多边形块面清楚，有适量小倒角；不用照片纹理、噪声污迹或文字贴图。入口可挂小巧暖色防水壁灯。不要加入人物、家具、室内切面、其他建筑、地形、植被、海水或船。
- 六向方向和结构保持一致：Front(-Y) 看到门廊、双开门、踏步、公告板与坡道；Back(+Y) 为简洁后墙；Left(-X)/Right(+X) 各看到三组会堂窗；Top(+Z) 读出完整对称屋顶；Bottom(-Z) 读出木梁、石墩、门廊和坡道支撑。

## 脚本与输出

- 仅使用 `bpy`、`bmesh`、`mathutils`、`math`、`pathlib` 和 Python 标准库。自动创建目录；从脚本路径定位项目根目录，避免依赖工作目录。
- 模型集合 `CouncilHall_DeepSeek`，辅助集合 `Helpers_CouncilHall_DeepSeek`；材质统一使用 `CouncilHall_DeepSeek_` 前缀。重复运行只清理自有集合和无用户的前缀材质，不触碰其他对象、资产或仍在使用的材质。
- 输出：
  - `Assets/LastLandfall/Art/Source/Buildings/CouncilHall_DeepSeek.blend`
  - `Assets/LastLandfall/Resources/Models/Buildings/CouncilHall_DeepSeek.fbx`
  - `Assets/LastLandfall/Art/Previews/Buildings/CouncilHall_DeepSeek.png`
  - `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/CouncilHall_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`
- 在独立辅助集合中创建相机和柔和灯光，只渲染本资产；输出六张留白均匀的严格正交 QA 图和一张居中三分之四预览，中性棚拍背景。
- FBX 只导出模型集合中的 Mesh，应用缩放、中心对齐到平面原点，轴向 `axis_forward='-Y'`、`axis_up='Z'`；不导出相机、灯光、Empty 或外部对象。
- 保存 Blend 前恢复原有相机、世界、渲染引擎、分辨率、输出路径、图像格式、透明设置、选择状态和外部对象的渲染可见性；不得将渲染辅助对象或临时世界保存成活动相机/世界。
- 最后打印 Mesh 数、世界包围盒、最低 Z、非流形边数、松散顶点数，并注明逐对象拓扑检查不能检测不同对象之间的穿插。

只返回一个完整、可运行的 Python 代码块，不要省略、伪代码、占位符或额外说明。
