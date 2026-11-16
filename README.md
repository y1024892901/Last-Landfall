# 潮线之上（Last Landfall）

这是可由 Unity 打开的项目源码。项目记录的编辑器版本为 Unity 6.6（`6000.6.6f1`），在装有对应版本 Unity 的电脑上选择本项目根目录打开。

## 打开项目

项目使用 Git LFS 管理部分大型资源。换电脑克隆后，请先安装并启用 Git LFS，在项目根目录执行 `git lfs pull`，确保模型等资源下载完成，再用 Unity 打开项目。

Unity 会恢复 URP 17.6，并由 `Assets/Editor/LastLandfallProjectSetup.cs` 自动创建 URP 配置、原型场景和岛屿实例。打开 `Prototype` 场景，等待 FBX 导入和脚本编译完成后按 Play。若 Unity 窗口没有显示磁盘上的最新场景或脚本，先用 `Assets > Refresh` 刷新项目；仍未放置时，使用 `Last Landfall > Place Island in Prototype Scene`。

## 当前原型

- 三座岛屿共用建造格网。放置根据水位、坡度和占用判断，低岸码头可生成接岸台阶。主岛有溪流与池塘，东副岛有沉船，海上另有灯塔遗址。
- 左侧建造菜单有 25 类设施，对应 29 个施工模块。普通设施分四阶段施工；道路可拖铺，并按相邻格切换直线、转角、T 字、十字和端头。
- 科技菜单包含 R1–R9 主线研究和效率研究。淡化、捕鱼和温室等已接入产出，居民消耗食水。开局库存和基础发电仍采用测试数值。
- 可指挥船员登船，在码头装卸货物，选择海面目标航行。灯塔从废墟开始，经八道工序点亮，面板保留阶段跳转用于查看模型。
- 动态首页和游戏内设置已接入。游戏支持天气切换、时钟、暂停与 1×/2×/3×，以及首页音乐、游戏内轮播和天气声。
- F5/F9 提供单槽快速存读档。普通施工与在研课题的进度仍待补齐，F9 当前还会触发测试用的库存补满。

从左侧建筑菜单选设施，按 R 旋转，左键放置，右键退出。铺路可按住左键拖动。滚轮缩放；未选中普通或水面设施时可用 Q/E 转动镜头。按 L 定位灯塔并打开重建面板。

最近一次 Unity 复核及待办见[项目进度与待办](Docs/ProjectProgress.md)。

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

建筑菜单提供完整的 25 类设施，按居住、生产、设施、交通分类，包含 19 类建筑和 6 类基础设施；土路的 5 个连接模块自动切换，共对应施工目录中的 29 个模块。浮标和漂木浮栅放在连续水面，码头与船坞放在岸边，各设施使用对应图标、成品模型和施工动画。模型以米为单位，地面原点为 `(0, 0, 0)`；建筑正面朝局部 `-Y`。在 Unity 菜单 `Last Landfall/Validate All Facilities` 可检查菜单覆盖率和资源完整性。

3D 文件按用途分组：Blender 源文件位于 `Assets/LastLandfall/Art/Source/Buildings/`、`Infrastructure/`、`Environment/`；Unity 模型位于 `Assets/LastLandfall/Resources/Models/` 下同名分类目录。自然资产单独位于 `Resources/Models/Nature/`。可查看 `Assets/LastLandfall/Art/3D_ASSET_CATALOG.md`，按资产名称找到源文件、导入模型和预览图。

## 海岸低模自然资产

`Assets/LastLandfall/Resources/Models/Nature/` 包含一套原创、Unity 可导入的 OBJ/MTL 模型：迎风松树、阔叶树、耐盐灌木、草丛、蕨类、野花、玄武岩和漂流木，共 16 个模型；另有独立的 `Bamboo_Clump_A.fbx` 竹丛资源，含带竹节的成竹和新笋。竹丛由 `Tools/Blender/create_bamboo_clump.py` 建模，源文件位于 `Assets/LastLandfall/Art/Source/Nature/`。Gate25 主岛溪谷上游布置了 6 丛竹子；用 `Tools/Blender/add_bamboo_to_gate25.py` 可重建竹丛布置。岛屿 FBX 可直接导入，该环境版本的 Blender 源文件和预览位于 `Art/Source/Environment/`、`Art/Previews/Environment/`。海岸 OBJ/MTL 资产包预览图为 `Assets/LastLandfall/Art/Previews/Nature/StylizedNaturePack.png`。

从项目根目录运行 `python Tools/Blender/export_stylized_nature_pack.py` 可重新生成模型、材质、清单和预览图。

建筑生成脚本位于 `Tools/Blender/`，例如 `WoodShelter.py`。场景基础设施的生成脚本见 `Tools/Blender/create_scenario_infrastructure.py`。

当前运行时以 `Island_Main_Expanded.fbx`、`Island_West_Expanded.fbx` 和 `Island_East_Expanded.fbx` 为群岛基底，再加载新版地形、植被、岩石及东岛沉船。三座扩展岛屿的 FBX 都需要到位。[岛屿扩展说明](Docs/IslandExpansion.md)记录原扩展版的测量数据和生成方法。

`IslandReference_V2` 裸地地形保留为建模参考。

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

## 主要文档与验证记录

- [项目进度与待办](Docs/ProjectProgress.md)：当前试玩范围、实测结果和待办优先级。
- [游戏优化清单](Docs/GamePolishBacklog.md)：实机问题、画面与操作优化、验收用例。
- [岛屿扩展说明](Docs/IslandExpansion.md)：三岛规模、模型加载和重建方法。
- [岛屿资产清单](Assets/LastLandfall/Art/IslandComponentChecklist.md)和 [3D 资产索引](Assets/LastLandfall/Art/3D_ASSET_CATALOG.md)：当前模型、回退资源与 Blender 源文件。
- [岛屿建模进度](ISLAND_MODELING_PROGRESS.md)：当前交付状态及历史 Gate 检查记录。
- [剧情与阶段进度](Design/LastLandfall_Scenario_Progression.md)：研究、设施与游戏阶段设计。
- [音频](Docs/AudioDirection.md)、[海面](Docs/OceanRendering.md)、[天气与光照](Docs/WeatherLighting.md)：各系统设计和专项验证。
- [历史发布复核记录](Art/Reports/ReleaseReview/Validation.txt)：保留旧版地形、设施、设置、灯塔和着色器的检查结果。
