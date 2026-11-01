# WeatherTideBuoy_DeepSeek — Blender 5.2.2 建模脚本请求

请按以下书面规格生成一份完整、可直接运行的 Blender 5.2.2 Python 脚本。项目已有 `Assets/LastLandfall/Art/References/ScenarioBuildingViews/WeatherTideBuoy_SixViews.png` 作为基础轮廓与方向参考，以及 `Assets/LastLandfall/Art/Previews/Infrastructure/WeatherTideBuoy.png` 作为旧资产风格参考；本条消息没有附图，因此不要声称你已看过本地图片，以下文字规格是完整依据。

## 背景和用途

这是《Last Landfall》4 级区域救援设施“气象与潮位浮标”，用于在远离基地的近海连续采集风向、风速、潮位和天气数据，并通过无线电回传给救援指挥中心。它应清楚读作一台可在海上长期工作的无人浮标，而不是岸上气象站、灯塔或大型船舶。整体延续现有低多边形海岛设施的海玻璃青绿、风化木、暗铁和少量锈橙配色，增加紧凑的仪器和太阳能供电部件。

## 尺寸、方向和造型

- Blender 5.2.2 LTS，单位 1 BU = 1 米，+Z 向上，资产中心靠近原点，正面朝 -Y。
- 以 1×1 米占地和 2.7 米总高为目标；全模型含防撞件不得超过 1.10 米 × 1.10 米 × 2.70 米。最低点 Z=0，不包含水面、海床、地形或背景道具。
- 低多边形游戏资产风格，轮廓清楚、零件数量克制；禁用照片级污渍、文字、logo、人物和科幻装饰。
- 下部是 8 至 12 面的紧凑封闭浮体，宽约 0.88–0.96 米，高约 0.42 米；主体用褪色海玻璃青绿，顶部为浅青灰防滑仪器甲板，底部有深色龙骨/压载带。3–4 个锈橙色防撞块沿周缘对称分布，并与浮体贴合。
- 中央有牢固的加厚桅杆基座与竖直桅杆。桅杆连续连接浮体甲板至顶部信标，最高 Z 不超过 2.70 米；使用深青灰金属，设置两道可读的加固环和短斜撑，所有横臂都从桅杆或安装座实际连接。
- 在桅杆上段布置小型三杯风速计和方向风标，风标有清楚箭头/尾翼；在相邻高度布置一体式气象传感器盒。顶端设置琥珀色低多边形航标灯，带海绿色/浅色帽檐。设备层次要明确，不要让仪器互相穿插或被桅杆完全遮住。
- 在甲板上安装一块小型倾斜矩形太阳能板（支架连接到甲板），另有一根细短无线电天线。太阳能板和天线不得越出 1.10 米占地。
- 浮体侧面设置清晰的水位刻度柱/潮位探头接口，探头由有支撑的短安装臂连接；底部设置一只短小受保护的声学潮位换能器和可见的三点系泊耳。它们都必须位于整体尺寸范围内，不得悬空。
- 六个方向保持同一坐标约定和真实部件位置。正面 -Y 主要展示仪器盒、太阳能板和一处防撞块；背面 +Y 展示安装臂和不同的系泊耳；左右侧能区分探头和风标尾翼；俯视能读出浮体、甲板、太阳能板、桅杆、风速计/风标的相对位置；仰视能看到龙骨、潮位换能器保护架和三个系泊点。
- 所有线缆、支架、系泊耳、传感器和仪器盒都须与浮体/桅杆/安装座可靠贴合。避免断开的线、零长度几何、明显穿模和位于 Z<0 的几何体。材质使用清晰的无贴图基础色：海玻璃青绿、浅海沫色、深青灰金属、风化浅木、克制的锈橙、琥珀信标和象牙刻度。

## 集合、脚本和输出

- 仅用 Blender 自带 `bpy`、`bmesh`、`mathutils`、`math` 与 Python 标准库；从项目根目录运行，使用 `pathlib` 并自动创建输出目录。
- 模型集合命名 `WeatherTideBuoy_DeepSeek`，相机/灯光/渲染辅助对象放进 `Helpers_WeatherTideBuoy_DeepSeek`。脚本可重复运行，只能清理这两个完全匹配的集合及本资产前缀且已无用户的材质，保留原版 `WeatherTideBuoy` 和所有其他场景内容。
- 材质统一使用 `WeatherTideBuoy_DeepSeek_` 前缀。通过节点类型/`bl_idname` 查找 Principled BSDF、Material Output 和 World Background，不能依赖本地化节点名称。
- 输出路径：
  - Blend：`Assets/LastLandfall/Art/Source/Infrastructure/WeatherTideBuoy_DeepSeek.blend`
  - FBX：`Assets/LastLandfall/Resources/Models/Infrastructure/WeatherTideBuoy_DeepSeek.fbx`
  - 等距预览：`Assets/LastLandfall/Art/Previews/Infrastructure/WeatherTideBuoy_DeepSeek.png`
  - 六张 QA：`Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/WeatherTideBuoy_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`
- 六张 QA 必须为统一背景、统一目标点和适配完整模型的正交相机：Front 从 -Y、Back 从 +Y、Left 从 -X、Right 从 +X、Top 从 +Z、Bottom 从 -Z；不得镜像、改换朝向或以透视代替正交。另做一张居中、留边充足的三分之四预览。
- FBX 仅导出模型集合内的 Mesh，不导出相机、灯光或辅助物体；采用适合 Unity 的应用变换设置。Blend 保存最终模型和方便编辑的清晰对象命名。
- 保存前恢复脚本临时改动的相机、世界、渲染设置；不要覆盖 `WeatherTideBuoy.blend` 或其余资产。
- 脚本最后打印网格物件数、世界包围盒、最低 Z、非流形边数和松散几何数，并明确说明逐对象拓扑检查不能检测不同对象之间的相交。

请只返回一个完整的 Python 代码块，包含全部导入、路径、函数、建模、渲染、导出和诊断代码；不要返回伪代码、占位符、代码省略号或额外建筑。
