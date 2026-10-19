# 3D 资产索引

以下资产路径均相对于 `Assets/LastLandfall/`。

## 文件夹用途

- `Art/Source/`：可继续编辑的 Blender `.blend` 源文件，按用途分组。
- `Resources/Models/`：Unity 导入和运行时加载的模型；游戏代码通过 `Resources.Load` 按分类路径加载。
- `Art/Previews/`：模型渲染图，按用途分组。
- `Art/Materials/IslandReference_V2/`：岛屿地貌材质。

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
| V2 裸地岛屿 | `Art/Source/Environment/IslandReference_V2.blend` | `Resources/Models/Environment/IslandReference_V2.fbx` | `Art/Previews/Environment/IslandReference_V2_Reference.png`、`IslandReference_V2_Top.png`、`IslandReference_V2_Clay.png` |
| 海岸自然资产包 | `Tools/Blender/export_stylized_nature_pack.py` 生成 | `Resources/Models/Nature/` 下 16 个 OBJ/MTL 模型 | `Art/Previews/Nature/StylizedNaturePack.png` |

自然资产包含迎风松、阔叶树、耐盐灌木、草丛、蕨类、野花、玄武岩和漂流木；名称和分类详见 `Resources/Models/Nature/asset_manifest.json`。

## 重新生成

- 建筑、码头和道路：在 Blender 所在电脑的项目根目录运行 `Tools/Blender/generate_all_assets.ps1`。
- 岛屿：从项目根目录运行 `blender --background --python Tools/Blender/build_island_reference_v2.py`。
- 自然资产：运行 `python Tools/Blender/export_stylized_nature_pack.py`。

生成器会写回对应分类目录。`ResidentHut.blend1` 是 Blender 的本地自动备份，不是游戏导入模型。
