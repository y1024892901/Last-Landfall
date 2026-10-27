# 3D 资产索引

除明确标注为项目根目录的 `Tools/`、`work/` 和 `Art/Reports/` 路径外，以下资产路径相对于 `Assets/LastLandfall/`。同一单元格中简写的文件名位于前一个完整路径的目录内。

## 文件夹用途

- `Art/Source/`：可继续编辑的 Blender `.blend` 源文件，按用途分组。
- `Resources/Models/`：Unity 导入和运行时加载的模型；游戏代码通过 `Resources.Load` 按分类路径加载。
- `Art/Previews/`：模型渲染图，按用途分组。
- `Art/Materials/IslandReference_V2/`：V2 裸地模型的地貌材质；Gate25 运行时地貌由顶点颜色着色。

移动文件时保留同名 `.meta`，以维持 Unity 的资产 GUID 和场景引用。

## 建筑

| 资产 | Blender 源文件 | Unity 模型 | 渲染预览 |
| --- | --- | --- | --- |
| 居民小屋 | `Art/Source/Buildings/ResidentHut_DeepSeek.blend` | `Resources/Models/Buildings/ResidentHut_DeepSeek.fbx` | `Art/Previews/Buildings/ResidentHut_DeepSeek.png` |
| 温室 | `Art/Source/Buildings/Greenhouse_DeepSeek.blend` | `Resources/Models/Buildings/Greenhouse_DeepSeek.fbx` | `Art/Previews/Buildings/Greenhouse_DeepSeek.png` |
| 废料拆解工坊 | `Art/Source/Buildings/SalvageWorkshop_DeepSeek.blend` | `Resources/Models/Buildings/SalvageWorkshop_DeepSeek.fbx` | `Art/Previews/Buildings/SalvageWorkshop_DeepSeek.png` |
| 仓库 | `Art/Source/Buildings/StorageDepot_DeepSeek.blend` | `Resources/Models/Buildings/StorageDepot_DeepSeek.fbx` | `Art/Previews/Buildings/StorageDepot_DeepSeek.png` |
| 救援指挥站 | `Art/Source/Buildings/RescueRadioCenter_DeepSeek.blend` | `Resources/Models/Buildings/RescueRadioCenter_DeepSeek.fbx` | `Art/Previews/Buildings/RescueRadioCenter_DeepSeek.png` |
| 固定海水淡化装置 | `Art/Source/Buildings/DesalinationPlant_DeepSeek.blend` | `Resources/Models/Buildings/DesalinationPlant_DeepSeek.fbx` | `Art/Previews/Buildings/DesalinationPlant_DeepSeek.png` |
| 医疗站 | `Art/Source/Buildings/MedicalStation_DeepSeek.blend` | `Resources/Models/Buildings/MedicalStation_DeepSeek.fbx` | `Art/Previews/Buildings/MedicalStation_DeepSeek.png` |
| 太阳能发电站 | `Art/Source/Buildings/SolarPowerStation_DeepSeek.blend` | `Resources/Models/Buildings/SolarPowerStation_DeepSeek.fbx` | `Art/Previews/Buildings/SolarPowerStation_DeepSeek.png` |
| 公共厨房 | `Art/Source/Buildings/PublicKitchen_DeepSeek.blend` | `Resources/Models/Buildings/PublicKitchen_DeepSeek.fbx` | `Art/Previews/Buildings/PublicKitchen_DeepSeek.png` |
| 锻造炉 | `Art/Source/Buildings/Forge_DeepSeek.blend` | `Resources/Models/Buildings/Forge_DeepSeek.fbx` | `Art/Previews/Buildings/Forge_DeepSeek.png` |
| 淡水储水罐 | `Art/Source/Buildings/WaterStorageTank.blend` | `Resources/Models/Buildings/WaterStorageTank.fbx` | `Art/Previews/Buildings/WaterStorageTank.png` |
| 木棚 | `Art/Source/Buildings/WoodShelter_DeepSeek.blend` | `Resources/Models/Buildings/WoodShelter_DeepSeek.fbx` | `Art/Previews/Buildings/WoodShelter_DeepSeek.png` |
| 研究站 | `Art/Source/Buildings/ResearchStation_DeepSeek.blend` | `Resources/Models/Buildings/ResearchStation_DeepSeek.fbx` | `Art/Previews/Buildings/ResearchStation_DeepSeek.png` |
| 医疗帐篷 | `Art/Source/Buildings/MedicalTent_DeepSeek.blend` | `Resources/Models/Buildings/MedicalTent_DeepSeek.fbx` | `Art/Previews/Buildings/MedicalTent_DeepSeek.png` |
| 初始通讯中心 | `Art/Source/Buildings/LocalCommunicationsCenter_DeepSeek.blend` | `Resources/Models/Buildings/LocalCommunicationsCenter_DeepSeek.fbx` | `Art/Previews/Buildings/LocalCommunicationsCenter_DeepSeek.png` |
| 学校 | `Art/Source/Buildings/School_DeepSeek.blend` | `Resources/Models/Buildings/School_DeepSeek.fbx` | `Art/Previews/Buildings/School_DeepSeek.png` |
| 档案馆 | `Art/Source/Buildings/Archive_DeepSeek.blend` | `Resources/Models/Buildings/Archive_DeepSeek.fbx` | `Art/Previews/Buildings/Archive_DeepSeek.png` |
| 议事厅 | `Art/Source/Buildings/CouncilHall_DeepSeek.blend` | `Resources/Models/Buildings/CouncilHall_DeepSeek.fbx` | `Art/Previews/Buildings/CouncilHall_DeepSeek.png` |
| 救援前哨 | `Art/Source/Buildings/RescueOutpost_DeepSeek.blend` | `Resources/Models/Buildings/RescueOutpost_DeepSeek.fbx` | `Art/Previews/Buildings/RescueOutpost_DeepSeek.png` |

## 基础设施

| 资产 | Blender 源文件 | Unity 模型 | 渲染预览 |
| --- | --- | --- | --- |
| 救援码头 | `Art/Source/Infrastructure/RescueDock.blend` | `Resources/Models/Infrastructure/RescueDock.fbx` | `Art/Previews/Infrastructure/RescueDock_Final.png` |
| 气象与潮位浮标（DeepSeek 变体） | `Art/Source/Infrastructure/WeatherTideBuoy_DeepSeek.blend` | `Resources/Models/Infrastructure/WeatherTideBuoy_DeepSeek.fbx` | `Art/Previews/Infrastructure/WeatherTideBuoy_DeepSeek.png` |
| 船坞（DeepSeek 变体） | `Art/Source/Infrastructure/Shipyard_DeepSeek.blend` | `Resources/Models/Infrastructure/Shipyard_DeepSeek.fbx` | `Art/Previews/Infrastructure/Shipyard_DeepSeek.png` |
| 单格道路 | `Art/Source/Infrastructure/RoadTiles.blend` | `Resources/Models/Infrastructure/RoadStraight.fbx`、`RoadCorner.fbx`、`RoadTee.fbx`、`RoadCross.fbx`、`RoadEnd.fbx` | `Art/Previews/Infrastructure/RoadTiles_Final.png` |
| 土路模块（DeepSeek 变体） | `Art/Source/Infrastructure/DirtRoadTiles_DeepSeek.blend` | `Resources/Models/Infrastructure/DirtRoadStraight_DeepSeek.fbx`、`DirtRoadCorner_DeepSeek.fbx`、`DirtRoadTee_DeepSeek.fbx`、`DirtRoadCross_DeepSeek.fbx`、`DirtRoadEnd_DeepSeek.fbx` | `Art/Previews/Infrastructure/DirtRoadTiles_DeepSeek.png` |
| 漂木收集浮栅 | `Art/Source/Infrastructure/DriftwoodCollectionBoom.blend` | `Resources/Models/Infrastructure/DriftwoodCollectionBoom.fbx` | `Art/Previews/Infrastructure/DriftwoodCollectionBoom.png` |
| 渔船码头 | `Art/Source/Infrastructure/FishingDock.blend` | `Resources/Models/Infrastructure/FishingDock.fbx` | `Art/Previews/Infrastructure/FishingDock.png` |
| 气象与潮位浮标 | `Art/Source/Infrastructure/WeatherTideBuoy.blend` | `Resources/Models/Infrastructure/WeatherTideBuoy.fbx` | `Art/Previews/Infrastructure/WeatherTideBuoy.png` |
| 船坞 | `Art/Source/Infrastructure/Shipyard.blend` | `Resources/Models/Infrastructure/Shipyard.fbx` | `Art/Previews/Infrastructure/Shipyard.png` |

## 环境和自然资产

| 资产 | 源文件 | Unity 模型 | 预览 |
| --- | --- | --- | --- |
| 扩展版主岛 | `Art/Source/Environment/Island_Main_Expanded.blend` | `Resources/Models/Environment/Island_Main_Expanded.fbx` | 项目根目录 `Art/Reports/IslandExpansion/Expanded_Main.png` |
| 扩展版西岛 | `Art/Source/Environment/Island_West_Expanded.blend` | `Resources/Models/Environment/Island_West_Expanded.fbx` | 项目根目录 `Art/Reports/IslandExpansion/Expanded_West.png` |
| 扩展版东岛 | `Art/Source/Environment/Island_East_Expanded.blend` | `Resources/Models/Environment/Island_East_Expanded.fbx` | 项目根目录 `Art/Reports/IslandExpansion/Expanded_East.png` |
| 扩展版沉船 | `Art/Source/Environment/Gate26_CapsizedWreck_Expanded.blend` | `Resources/Models/Environment/Gate26_CapsizedWreck_Expanded.fbx` | `Art/Previews/Environment/Gate26_CapsizedWreck_Expanded.png` |
| 灯塔阶段 | `Art/Source/Environment/Lighthouse_Stages.blend` | `Resources/Models/Lighthouse/Lighthouse_Reef.fbx` 和 `Lighthouse_Stage_0.fbx` 至 `Lighthouse_Stage_4.fbx` | 发布复核预览位于项目根目录 `Art/Reports/ReleaseReview/` |
| Gate25 森林溪谷岛屿（历史／回退版） | `work/island_final_candidate/Assets_Generated/LastLandfall_Island_GrassCoverage_Gate25.blend` | `Resources/Models/Environment/IslandReference_Gate25.fbx` | `work/island_final_candidate/Previews_Generated/Gate25_Basin_Closeup.png`、`Gate25_GrassCoverage_Zones_TreeClusters.png` |
| Gate25 竹林溪谷版（已加竹丛） | `Art/Source/Environment/IslandReference_Gate25_Bamboo.blend`；生成脚本：`Tools/Blender/add_bamboo_to_gate25.py` | `Resources/Models/Environment/IslandReference_Gate25.fbx` | `Art/Previews/Environment/IslandReference_Gate25_Bamboo.png` |
| Gate26 双子岛（陡峭裸岩峰与全植被版） | `work/island_final_candidate/Gate32_TwinIslands_FullEnvironment/LastLandfall_Gate26_TwinIslands_Foliage.blend` | `Resources/Models/Environment/LastLandfall_Basin_TwinIslands_Gate26.fbx` | `work/island_final_candidate/Gate32_TwinIslands_FullEnvironment/LastLandfall_Gate26_TwinIslands_Foliage_Preview.png` |
| Gate26 倾覆废弃补给船与搁浅区 | `Art/Source/Environment/Gate26_CapsizedWreck.blend` | `Resources/Models/Environment/Gate26_CapsizedWreck.fbx` | `Art/Previews/Environment/Gate26_CapsizedWreck.png`、`Gate26_CapsizedWreck_Detail.png` |
| V2 裸地基础地形 | `Art/Source/Environment/IslandReference_V2.blend` | `Resources/Models/Environment/IslandReference_V2.fbx` | `Art/Previews/Environment/IslandReference_V2_Reference.png`、`IslandReference_V2_Top.png`、`IslandReference_V2_Clay.png` |
| 海岸自然资产包 | `Tools/Blender/export_stylized_nature_pack.py` 生成 | `Resources/Models/Nature/` 下 16 个 OBJ/MTL 模型 | `Art/Previews/Nature/StylizedNaturePack.png` |
| 竹丛资源（独立可复用模型） | `Art/Source/Nature/Bamboo_Clump_A.blend`；生成脚本：`Tools/Blender/create_bamboo_clump.py` | `Resources/Models/Nature/Bamboo_Clump_A.fbx` | `Art/Previews/Nature/Bamboo_Clump_A.png` |

海岸自然资产包包含迎风松、阔叶树、耐盐灌木、草丛、蕨类、野花、玄武岩和漂流木；独立竹丛模型另存为 FBX。Gate25 竹林版在溪谷上游岸坡加入 6 丛竹子，未删改原树群；名称和资产包分类详见 `Resources/Models/Nature/asset_manifest.json`。

## 重新生成

- 扩展版三岛：参见项目根目录 [Docs/IslandExpansion.md](../../../Docs/IslandExpansion.md)，含面积、加载顺序与生成命令。
- 新风格建筑：从项目根目录分别运行对应的 `Tools/Blender/*_DeepSeek.py` 脚本。
- 基础设施和道路：在 Blender 所在电脑的项目根目录运行 `Tools/Blender/generate_all_assets.ps1`；基础设施子集脚本为 `Tools/Blender/create_scenario_infrastructure.py`。
- V2 基础地形：从项目根目录运行 `blender --background --python Tools/Blender/build_island_reference_v2.py`。
- Gate25 森林溪谷岛屿：按 `work/island_final_candidate/Gate25_GrassCoverage_Handoff.md` 使用该候选目录中的 Blender 脚本生成。
- 竹丛资源：运行 `blender --background --python Tools/Blender/create_bamboo_clump.py`，生成独立 `.blend`、FBX、预览图和几何检查报告。
- Gate25 竹林溪谷版：在竹丛 FBX 已生成后运行 `blender --background --python Tools/Blender/add_bamboo_to_gate25.py`；脚本会重建自己的竹丛集合，保留地形、水体和其他植被。
- Gate26 双子岛：从项目根目录运行 `blender --background --python work/island_final_candidate/Scripts/Gate32_Gate26_TwinIslands_FullVegetation.py`；脚本按 Gate26 裸岩基础网格和 Gate25 自然资产包生成完整环境模型。
- 自然资产：运行 `python Tools/Blender/export_stylized_nature_pack.py`。
- Gate26 废弃船与搁浅区：运行 `blender --background --python Tools/Blender/create_capsized_wreck_on_gate26.py`。包含破损船壳、弯折断肋、损坏推进器、锈蚀流挂、潮水污痕、贴地冲刷痕、碎岩和脱落钢板，不含沙滩。散落物分别采样地形，岸外浮木降至海面；碎岩与铆钉合并网格。Unity 沿用 `Wreck_` / `Debris_` 加载与植被避让。

生成器会写回对应分类目录。旧风格建筑的 Blender 源文件、Unity 模型、预览图和建造图标已移除。
