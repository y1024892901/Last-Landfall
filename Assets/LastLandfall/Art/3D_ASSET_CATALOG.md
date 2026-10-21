# 3D 资产索引

以下资产路径均相对于 `Assets/LastLandfall/`。

## 文件夹用途

- `Art/Source/`：可继续编辑的 Blender `.blend` 源文件，按用途分组。
- `Resources/Models/`：Unity 导入和运行时加载的模型；游戏代码通过 `Resources.Load` 按分类路径加载。
- `Art/Previews/`：模型渲染图，按用途分组。
- `Art/Materials/IslandReference_V2/`：V2 裸地模型的地貌材质；Gate25 运行时地貌由顶点颜色着色。

移动文件时保留同名 `.meta`，以维持 Unity 的资产 GUID 和场景引用。

## 建筑

| 资产 | Blender 源文件 | Unity 模型 | 渲染预览 |
| --- | --- | --- | --- |
| 居民小屋 | `Art/Source/Buildings/ResidentHut.blend` | `Resources/Models/Buildings/ResidentHut.fbx` | `Art/Previews/Buildings/ResidentHut_Final.png` |
| 温室 | `Art/Source/Buildings/Greenhouse.blend` | `Resources/Models/Buildings/Greenhouse.fbx` | `Art/Previews/Buildings/Greenhouse_Final.png` |
| 集水净水站 | `Art/Source/Buildings/WaterPurifier.blend` | `Resources/Models/Buildings/WaterPurifier.fbx` | `Art/Previews/Buildings/WaterPurifier_Final.png` |
| 废料拆解工坊 | `Art/Source/Buildings/SalvageWorkshop.blend` | `Resources/Models/Buildings/SalvageWorkshop.fbx` | `Art/Previews/Buildings/SalvageWorkshop_Final.png` |
| 发电站 | `Art/Source/Buildings/GeneratorStation.blend` | `Resources/Models/Buildings/GeneratorStation.fbx` | `Art/Previews/Buildings/GeneratorStation_Final.png` |
| 仓库 | `Art/Source/Buildings/StorageDepot.blend` | `Resources/Models/Buildings/StorageDepot.fbx` | `Art/Previews/Buildings/StorageDepot_Final.png` |
| 救援指挥站 | `Art/Source/Buildings/RescueRadioCenter.blend` | `Resources/Models/Buildings/RescueRadioCenter.fbx` | `Art/Previews/Buildings/RescueRadioCenter_Final.png` |

## 基础设施

| 资产 | Blender 源文件 | Unity 模型 | 渲染预览 |
| --- | --- | --- | --- |
| 救援码头 | `Art/Source/Infrastructure/RescueDock.blend` | `Resources/Models/Infrastructure/RescueDock.fbx` | `Art/Previews/Infrastructure/RescueDock_Final.png` |
| 单格道路 | `Art/Source/Infrastructure/RoadTiles.blend` | `Resources/Models/Infrastructure/RoadStraight.fbx`、`RoadCorner.fbx`、`RoadTee.fbx`、`RoadCross.fbx`、`RoadEnd.fbx` | `Art/Previews/Infrastructure/RoadTiles_Final.png` |

## 环境和自然资产

| 资产 | 源文件 | Unity 模型 | 预览 |
| --- | --- | --- | --- |
| Gate25 森林溪谷岛屿（当前运行版） | `work/island_final_candidate/Assets_Generated/LastLandfall_Island_GrassCoverage_Gate25.blend` | `Resources/Models/Environment/IslandReference_Gate25.fbx` | `work/island_final_candidate/Previews_Generated/Gate25_Basin_Closeup.png`、`Gate25_GrassCoverage_Zones_TreeClusters.png` |
| Gate25 竹林溪谷版（已加竹丛） | `Art/Source/Environment/IslandReference_Gate25_Bamboo.blend`；生成脚本：`Tools/Blender/add_bamboo_to_gate25.py` | `Resources/Models/Environment/IslandReference_Gate25.fbx` | `Art/Previews/Environment/IslandReference_Gate25_Bamboo.png` |
| Gate26 双子岛（陡峭裸岩峰与全植被版） | `work/island_final_candidate/Gate32_TwinIslands_FullEnvironment/LastLandfall_Gate26_TwinIslands_Foliage.blend` | `Resources/Models/Environment/LastLandfall_Basin_TwinIslands_Gate26.fbx` | `work/island_final_candidate/Gate32_TwinIslands_FullEnvironment/LastLandfall_Gate26_TwinIslands_Foliage_Preview.png` |
| V2 裸地基础地形 | `Art/Source/Environment/IslandReference_V2.blend` | `Resources/Models/Environment/IslandReference_V2.fbx` | `Art/Previews/Environment/IslandReference_V2_Reference.png`、`IslandReference_V2_Top.png`、`IslandReference_V2_Clay.png` |
| 海岸自然资产包 | `Tools/Blender/export_stylized_nature_pack.py` 生成 | `Resources/Models/Nature/` 下 16 个 OBJ/MTL 模型 | `Art/Previews/Nature/StylizedNaturePack.png` |
| 竹丛资源（独立可复用模型） | `Art/Source/Nature/Bamboo_Clump_A.blend`；生成脚本：`Tools/Blender/create_bamboo_clump.py` | `Resources/Models/Nature/Bamboo_Clump_A.fbx` | `Art/Previews/Nature/Bamboo_Clump_A.png` |

海岸自然资产包包含迎风松、阔叶树、耐盐灌木、草丛、蕨类、野花、玄武岩和漂流木；独立竹丛模型另存为 FBX。Gate25 竹林版在溪谷上游岸坡加入 6 丛竹子，未删改原树群；名称和资产包分类详见 `Resources/Models/Nature/asset_manifest.json`。

## 重新生成

- 建筑、码头和道路：在 Blender 所在电脑的项目根目录运行 `Tools/Blender/generate_all_assets.ps1`。
- V2 基础地形：从项目根目录运行 `blender --background --python Tools/Blender/build_island_reference_v2.py`。
- Gate25 森林溪谷岛屿：按 `work/island_final_candidate/Gate25_GrassCoverage_Handoff.md` 使用该候选目录中的 Blender 脚本生成。
- 竹丛资源：运行 `blender --background --python Tools/Blender/create_bamboo_clump.py`，生成独立 `.blend`、FBX、预览图和几何检查报告。
- Gate25 竹林溪谷版：在竹丛 FBX 已生成后运行 `blender --background --python Tools/Blender/add_bamboo_to_gate25.py`；脚本会重建自己的竹丛集合，保留地形、水体和其他植被。
- Gate26 双子岛：从项目根目录运行 `blender --background --python work/island_final_candidate/Scripts/Gate32_Gate26_TwinIslands_FullVegetation.py`；脚本按 Gate26 裸岩基础网格和 Gate25 自然资产包生成完整环境模型。
- 自然资产：运行 `python Tools/Blender/export_stylized_nature_pack.py`。

生成器会写回对应分类目录。`ResidentHut.blend1` 是 Blender 的本地自动备份，不是游戏导入模型。
