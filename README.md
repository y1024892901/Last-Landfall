# 潮线之上（Last Landfall）

这是可直接由 Unity 打开的项目源码。使用 Unity Hub 安装并打开 Unity 6.6（6000.6），选择本项目根目录。

## 打开项目

Unity 会恢复 URP 17.6，并由 `Assets/Editor/LastLandfallProjectSetup.cs` 自动创建 URP 配置、原型场景和岛屿实例。打开 `Prototype` 场景，等待 FBX 导入和脚本编译完成后按 Play。若 Unity 窗口没有显示磁盘上的最新场景或脚本，先用 `Assets > Refresh` 刷新项目；仍未放置时，使用 `Last Landfall > Place Island in Prototype Scene`。

## 当前原型

- 斜俯视正交相机；运行时加载 `IslandReference_V2.fbx` 裸地岛屿，并用可见地形网格采样建造位置
- 42×36 米的 1 米格原型范围；椭圆建造区避开丘陵脚印，中央谷地和西南登陆通道保持开阔
- 建造菜单接入居民小屋、温室、集水净水站、废料拆解工坊、发电站、仓库、救援指挥站、救援码头和道路模型
- 2×2 建筑检查完整占地；道路只能铺在空闲高地格，并随相邻道路自动切换直线、转角、T 字、十字和端头模块
- 码头只能从高地边缘向连续水面延伸；建筑、道路、地形和木材不足都会阻止放置
- 放置成功扣除对应木材，初始木材为 100；物资数量固定显示在界面顶栏
- 岛屿可用顶栏按钮或 Q/E 旋转，鼠标滚轮缩放；正交相机视野 size 范围为 1–72，运行时自动对准岛屿
- 海面使用项目内置的动态蓝绿潮汐着色器，包含浅水渐变、流纹和断续岸边白沫；海平面与岛屿模型的零高度基准一致
- 建造卡片带对应设施美术；选中设施并移动鼠标到高地时才显示格网与放置预览
- 道路支持按住鼠标拖动连续铺设，并自动补齐格子、接驳道路模块

操作：点击左侧建筑图标展开或收起菜单，再选择设施；按 R 旋转普通建筑，左键放置，右键退出建造。按住左键拖动道路可连续铺设。顶栏按钮可旋转、缩放岛屿；Q/E 旋转，+/- 缩放。

当前界面仍是早期原型，项目目标版本为 Unity 6.6。海水插件调研建议：如果后续需要船只尾流、浮力、浪花预制体等交互效果，可评估 [Stylized Water 3](https://assetstore.unity.com/packages/vfx/shaders/stylized-water-3-287769)；当前原型暂用项目内的轻量着色器，未引入付费依赖。

## 故事背景与开场

### 核心设定

一颗巨大的富冰天体掠过太阳系，在太阳潮汐作用下解体，留下与地球轨道相交的碎片流。人类起初只观测到零散的先导碎片，并成功将其拦截。各国因此相信防御系统有效，社会士气高涨。

不久后，密集的主碎片云突然到来。先前的拦截成功让人类低估了后续威胁；碎片从难以观测的方向逼近，拦截和预警都来不及应对。大量碎片进入大气并撞击海洋，引发连续冲击、海啸和沿海城市崩塌。卫星、电网和海底通信线路遭到破坏，全球互联网长期不稳定。

灾难并非一次海啸后就结束。残余碎片仍会不定期经过地球，任何一天、任何区域都可能遇袭；富冰碎片持续进入地球环境，带来新的水量和极端降雨，海平面因此逐年上涨。海上航行与高地生存成为日常，安全的高地也成为人类重建聚落的基础。持续补水和多年上涨属于本作的科幻前提。

### 人类社会与玩家

集中式救援逐渐演变为区域救援联盟和高地自治据点。卫星网络或电力中断时，人们靠短波无线电、船只和信使传递附近的求救任务。救援站以公共互助为目的，依靠居民生产、打捞和物资交换维持运作。

玩家从一艘救援船开始，亲自出海救援、探索和打捞；随后在一座可以旋转、四面扩建的高地上建立救援站。居民生产食物和物资，新来的幸存者带来技能与需求。随着船队和聚落发展，玩家逐步从亲自驾驶扩展到任务调度，同时仍能亲自出航。

故事模式围绕救援、招募、探索和聚落建设展开：玩家连接周边幸存者据点，寻找资源与新航路，并在不断上涨的海面上把一座高地建设成区域救援网络的中心。故事的目标不是恢复灾前世界，而是让更多人能在新环境中生活下去。

横版漫画风格开场概念图：`Assets/LastLandfall/Art/Concepts/OpeningComicIntro.png`。

## 第一批 Blender 资产

`Tools/Blender/` 中的脚本会生成可继续编辑的 `.blend` 源文件，并导出 Unity 可导入的 FBX；Blender 没有 FBX 导出器时会使用内置 OBJ 导出器。批量生成时，在装有 Blender 的电脑上从项目根目录运行：

```powershell
.\Tools\Blender\generate_all_assets.ps1
```

如果 Blender 不在 `PATH`，传入 Blender 可执行文件路径：

```powershell
.\Tools\Blender\generate_all_assets.ps1 -BlenderExe "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
```

当前首批资产包括：居民小屋、温室、集水净水站、废料拆解工坊、发电站、仓库、救援指挥站、码头和单格道路模块。模型以米为单位，地面原点为 `(0, 0, 0)`；建筑正面朝局部 `-Y`。建筑按材质合并网格以减少 Unity 渲染器数量。道路模块占地严格为 1×1 格，包含直线、转角、T 字、十字和端头形状。

3D 文件按用途分组：Blender 源文件位于 `Assets/LastLandfall/Art/Source/Buildings/`、`Infrastructure/`、`Environment/`；Unity 模型位于 `Assets/LastLandfall/Resources/Models/` 下同名分类目录。自然资产单独位于 `Resources/Models/Nature/`。可查看 `Assets/LastLandfall/Art/3D_ASSET_CATALOG.md`，按资产名称找到源文件、导入模型和预览图。

## 海岸低模自然资产

`Assets/LastLandfall/Resources/Models/Nature/` 包含一套原创、Unity 可导入的 OBJ/MTL 模型：迎风松树、阔叶树、耐盐灌木、草丛、蕨类、野花、玄武岩和漂流木，共 16 个模型；另有独立的 `Bamboo_Clump_A.fbx` 竹丛资源，含带竹节的成竹和新笋。竹丛由 `Tools/Blender/create_bamboo_clump.py` 建模，源文件位于 `Assets/LastLandfall/Art/Source/Nature/`。Gate25 主岛溪谷上游布置了 6 丛竹子；用 `Tools/Blender/add_bamboo_to_gate25.py` 可重建竹丛布置。岛屿 FBX 可直接导入，该环境版本的 Blender 源文件和预览位于 `Art/Source/Environment/`、`Art/Previews/Environment/`。海岸 OBJ/MTL 资产包预览图为 `Assets/LastLandfall/Art/Previews/Nature/StylizedNaturePack.png`。

从项目根目录运行 `python Tools/Blender/export_stylized_nature_pack.py` 可重新生成模型、材质、清单和预览图。

统一美术方向参考图保存在 `Assets/LastLandfall/Art/References/`。批量生成器会先运行基础建模脚本，再运行 `Tools/Blender/refine_asset_models.py` 添加海盐侵蚀材质细节、生活设施和功能道具，并重新导出 FBX。精修渲染图按类别保存在 `Assets/LastLandfall/Art/Previews/` 对应子目录，使用 `*_Final.png` 命名；重复运行不会累加几何细节。

当前岛屿资产为 `IslandReference_V2`：Blender 5.2.2 LTS 生成的非对称裸地地貌，包含中央低地、后侧主脊、分离丘陵、岩质半岛和深湾。建造格网直接采样可见地形网格，避免独立粗碰撞网格造成表面位置偏差。这个版本不包含树木、草地、沙滩、建筑或水面；自然植被作为独立资源放在 `Resources/Models/Nature/`。场景与编辑器自动放置流程均指向 V2；FBX、可编辑 `.blend` 源文件、三张预览图和地貌材质分别位于 `Resources/Models/Environment/`、`Art/Source/Environment/`、`Art/Previews/Environment/` 和 `Art/Materials/IslandReference_V2/`。

## 项目结构

- `Assets/LastLandfall/Art/Source/`：按类别整理的 Blender 源文件
- `Assets/LastLandfall/Art/Previews/`：按类别整理的 3D 渲染预览
- `Assets/LastLandfall/Art/References/`：美术方向和总览参考图
- `Assets/LastLandfall/Art/3D_ASSET_CATALOG.md`：源文件、Unity 模型与预览图索引
- `Assets/LastLandfall/Resources/Models/`：按类别整理的 Unity 模型；`Nature/` 保存 OBJ/MTL 自然资产
- `Assets/LastLandfall/Scripts/`：运行时原型代码
- `Assets/Editor/`：首次打开时自动配置 URP 和原型场景
- `Tools/Blender/`：用 Blender 程序化生成的游戏资产脚本
- `Packages/manifest.json`：Unity 包依赖
- `ProjectSettings/ProjectVersion.txt`：目标 Unity 版本
