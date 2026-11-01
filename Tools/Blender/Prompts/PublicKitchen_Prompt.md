# PublicKitchen：DeepSeek 建模代码生成要求

若本消息带有六视图概念图，请先查看；若附件不可见，则以本文件中的六视图位置表和文字结构说明作为完整参考，不要声称已查看不可见附件。请据此生成一个完整的 Blender Python 脚本。几何以适合游戏运行时的简洁低多边形造型为准，不要照搬概念图中的照片级纹理或小型五金细节。

## 背景和用途

《Last Landfall》是一款海岛灾后生存建造游戏。玩家在解决饮水、供电并启动高科技温室后，开始稳定获得蔬菜和鱼获。公共厨房是 3 级“食物与加工”设施：把温室收成、捕鱼和储备口粮处理成可分发的共享餐食，也承担清洗、备餐、短时储存和聚落用餐的功能。它应像由幸存者用本地木料、石材和总部设备搭建的实用设施，不是民宿、住宅、餐馆或另一座温室。

## 造型和尺寸

- 建筑 ID：`PublicKitchen_DeepSeek`；Blender 单位：1 BU = 1 米；+Z 向上；建筑中心靠近世界原点；最低点严格为 Z=0。
- 游戏网格占地为 3×2 个 1 米格。把墙体、屋檐、前方服务台、座凳、台阶和设备一起控制在约 3.4 m（X）×2.6 m（Y）以内；最高点不超过 3.0 m。
- 正面朝 -Y，背面朝 +Y，左侧为 -X，右侧为 +X。各视图必须保持相同门、窗口、雨棚、烟管、设备和管线位置，不可镜像或调换。
- 采用紧凑的单坡雨棚屋顶，屋顶从正面 -Y 向后方 +Y 升高；正视和后视的檐口水平，左、右侧视都能读出高边在世界坐标 +Y。屋顶用低矮的海绿色/蓝灰色金属板，木结构清楚承托。
- 立面以浅色风化木板和木框架为主，底部用少量暖灰石材或混凝土垫块架高，局部使用海绿色金属连接件和深青色设备。简洁风格化低多边形，形体清楚、无贴图也能识别，避免写实污渍、复杂小零件、标牌和科幻装饰。
- 正面 -Y：一处宽服务窗口，带牢固支架和附着式服务台；旁边一扇清晰可达的门；服务台外放两张简洁固定座凳。雨棚覆盖窗口和等候位置。
- 建筑内部：紧凑的备餐台、双槽洗涤池、置物架、小型食材柜和一台有烟管连接的柴火炉。透过服务窗口能看到主要设备，但不要把室内物件塞入墙体或让物件悬空。
- 背面 +Y：以完整的耐候墙板为主，仅有一处高位通风格栅和简洁检修面板。
- 左右侧：下半部为完整实墙，上半部可设一处小型高位通风窗；仅在一侧布置简洁、贴墙且有支撑的给排水管。
- 烟管应从炉灶连贯地穿出屋顶并有短帽，不要额外添加第二根烟囱或巨大独立烟塔。模型所有部件都须有合理支撑和连接；避免穿过墙/炉体的烟管、断开的管线、无支撑台面、穿模和位于地面以下的几何体。
- 正面为 -Y，参照图单张六视图按如下位置解释：第一行左 Front（从 -Y 看）；第一行中 Back（从 +Y 看）；第一行右 Left（从 -X 看）；第二行左 Right（从 +X 看）；第二行中 Top（从 +Z 看）；第二行右 Bottom（从 -Z 看）。

## 脚本和输出要求

1. 只用 Blender 5.2.2 LTS 自带的 `bpy`、`bmesh`、`mathutils` 及 Python 标准库；不得联网或依赖第三方包。脚本从项目根目录运行，使用 `pathlib` 并自动创建输出目录。
2. 只创建/替换专属 `PublicKitchen_DeepSeek` 模型集合和 `Helpers_PublicKitchen_DeepSeek` 相机灯光集合。保留场景内其他对象、材质、世界和设置；材质应带专属前缀。脚本应能重复运行，只写入该新风格模型的专属输出文件。
3. 保持零件为可在 Unity 中独立选择的命名 Mesh，名称能说明用途；FBX 只导出目标模型集合中的模型网格，排除相机、灯光、地面和 QA 辅助物体。
4. 保存路径：
   - Blender 源文件：`Assets/LastLandfall/Art/Source/Buildings/PublicKitchen_DeepSeek.blend`
   - FBX：`Assets/LastLandfall/Resources/Models/Buildings/PublicKitchen_DeepSeek.fbx`
   - 等距预览：`Assets/LastLandfall/Art/Previews/Buildings/PublicKitchen_DeepSeek.png`
   - 六视图 QA：`Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/PublicKitchen_DeepSeek_Front.png`
   - 同目录另保存 `PublicKitchen_DeepSeek_Back.png`、`PublicKitchen_DeepSeek_Left.png`、`PublicKitchen_DeepSeek_Right.png`、`PublicKitchen_DeepSeek_Top.png`、`PublicKitchen_DeepSeek_Bottom.png`。
5. 六视图必须是真正的正交视图，统一目标点、尺度和背景；分别从正确世界轴向观察并为每张图使用正确的输出路径。渲染后恢复相机和临时渲染设置，再保存最终场景。
6. 脚本末尾打印网格对象数、世界坐标包围盒、最低 Z、输出路径和可执行的网格诊断，例如非流形边。若自动诊断无法检测独立物体之间的交叉，应明确说明限制，不要声称已自动通过相交检查。
7. 代码必须完整、可直接在 Blender 5.2.2 中运行，不得省略函数或用伪代码。不要批量重建其他资产。

请先用几句话说明六视图中读到的房体、服务窗口、门、单坡屋顶、室内灶台和六个方向约定，然后给出完整 Python 脚本，确保它只处理 `PublicKitchen_DeepSeek`。
