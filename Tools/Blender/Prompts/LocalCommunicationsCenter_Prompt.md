# LocalCommunicationsCenter_DeepSeek — Blender 5.2.2 脚本请求

请为《Last Landfall》制作 0 级初始通讯中心 `LocalCommunicationsCenter_DeepSeek` 的完整、可运行 Blender 5.2.2 Python 脚本。随本提示附上的 `LocalCommunicationsCenter_SixViews.png` 是主要造型参考；正面朝 -Y，图片包含正面、背面、左右侧、顶视和等距视图。它用于基地本地联络和向总部同步图纸，不是 4 级救援指挥站或高塔式无线电设施。

## 造型与坐标

- 采用 Last Landfall 克制的低多边形风格：盐蚀浅棕木墙、焦油深木框架、褪色海绿色与补丁青灰色金属屋顶、暖浅灰石质基座、烟蓝玻璃、少量锈橙修补片和琥珀色信标。避免照片级纹理、污迹、文字、logo、人物、背景建筑、地形或水面。
- 1 BU=1m，+Z 向上，入口朝 -Y，原点在基座中心附近。占地控制在约 2.75×2.65m 内，最高不超过 3.1m，最低 Z=0。主体是约 2.3×2.0m 的单层小屋，略高出地面的厚实石质基座与木地板清楚可见。
- 正面 -Y 左侧为一扇窄木门，带简单门框和小块锈橙修补板；右侧为一扇小型烟蓝玻璃窗，配木框和清楚的竖向中梃。四角可见焦油深木收边柱。后墙保持简洁，不要复制前门窗。
- 屋顶为低矮、对称的人字双坡金属屋面：屋脊沿 X 轴，坡面分别朝 ±Y，前檐朝 -Y。加入连续的屋脊盖板、少量规则窄接缝和边缘收口；用海绿色、补丁灰青两种相近色区分屋面。屋檐适当外挑但不压住门窗。
- 屋顶后部附近安装一组紧凑的短波无线电设备：牢固底座、短竖桅、两至三根排列清楚的短偶极子/横杆，以及两根短斜撑。整体低矮、清楚、能看出是通讯天线，不要大型塔架、过多天线阵列或科幻造型。总高度不得超过 3.1m。桅杆底座必须压在屋面或屋脊支座上，横杆与桅杆可靠连接。
- 正面屋脊/屋檐附近有一盏小型琥珀色通讯信标，带底座和浅色或锈橙保护帽，与屋顶支撑连接。信标体积克制，不遮挡天线。
- 一侧墙面安装紧凑的备用电池盒和电缆卷盘：墙板固定在墙面，卷盘由两侧金属托架和短支撑板承托，卷轴与两片圆形挡盘清楚可见；一小块无文字几何色条的检修面板贴墙安装。所有组件贴合侧墙且彼此不穿插，不能悬空。另一侧外墙保持较干净。
- 六个方向必须一致：Front(-Y) 显示门、窗与前檐；Back(+Y) 显示简洁后墙和屋顶天线；Left(-X)/Right(+X) 区分两侧，至少一侧能清楚看到电池盒和电缆卷盘；Top(+Z) 展示双坡、屋脊和天线；Bottom(-Z) 展示基座和木地板底部。不要加入人物、桌椅、第二建筑、太阳能板、船只、地形或无关设备。

## 脚本与输出

- 仅使用 `bpy`、`bmesh`、`mathutils`、`math`、`pathlib` 和 Python 标准库；从项目根目录运行并按需创建目录。
- 模型集合 `LocalCommunicationsCenter_DeepSeek`，辅助集合 `Helpers_LocalCommunicationsCenter_DeepSeek`。重复运行只清理这两个完全匹配的集合和无用户的 `LocalCommunicationsCenter_DeepSeek_` 材质；保留旧版通讯中心和其他场景资产。
- 材质名统一使用 `LocalCommunicationsCenter_DeepSeek_` 前缀。通过节点 `bl_idname` 查找 Principled BSDF、Material Output、World Background；任何仍被集合外对象使用的同名前缀材质都不得删除、替换或修改。
- 输出：
  - `Assets/LastLandfall/Art/Source/Buildings/LocalCommunicationsCenter_DeepSeek.blend`
  - `Assets/LastLandfall/Resources/Models/Buildings/LocalCommunicationsCenter_DeepSeek.fbx`
  - `Assets/LastLandfall/Art/Previews/Buildings/LocalCommunicationsCenter_DeepSeek.png`
  - `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/LocalCommunicationsCenter_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`
- 六张 QA 图使用统一中心和留白的正交相机，方向严格为 Front(-Y)、Back(+Y)、Left(-X)、Right(+X)、Top(+Z)、Bottom(-Z)；另渲染一张三分之四预览。使用中性背景和柔和棚拍光，不渲染场景中的其他对象。
- FBX 仅导出模型集合里的 Mesh，相机和灯光放在辅助集合。保存 Blend 前恢复场景中原有相机、世界、渲染参数、选择状态和场景外对象可见性。不要保存默认立方体或把外部场景物件混入资产。
- 最后打印 Mesh 对象数、世界空间包围盒、最低 Z、非流形边和松散顶点，并注明逐对象拓扑检查不能检测不同对象之间的穿插。

只返回一个完整 Python 代码块，不要伪代码、占位符、省略号或省略任何必要内容。
