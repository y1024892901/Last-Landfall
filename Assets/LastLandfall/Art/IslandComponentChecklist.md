# 岛屿 V2 资产清单

当前岛屿版本为 `IslandReference_V2`。旧版整岛、模块化海岸和地形预览已从工作区清理。

## 当前资源

| 资源 | 用途 |
| --- | --- |
| `Assets/LastLandfall/Resources/Models/Environment/IslandReference_V2.fbx` | 当前裸地岛屿模型 |
| `Assets/LastLandfall/Art/Source/Environment/IslandReference_V2.blend` | 可编辑的 Blender 源文件 |
| `Assets/LastLandfall/Art/Previews/Environment/IslandReference_V2_Reference.png` | 主视角预览 |
| `Assets/LastLandfall/Art/Previews/Environment/IslandReference_V2_Top.png` | 顶视预览 |
| `Assets/LastLandfall/Art/Previews/Environment/IslandReference_V2_Clay.png` | 灰模预览 |
| `Assets/LastLandfall/Art/Materials/IslandReference_V2/` | 裸土、层状岩石和湿岩材质 |
| `Tools/Blender/build_island_reference_v2.py` | V2 地形生成器；依赖同目录的地貌和 Lookdev 模块 |

## 当前范围

V2 是非对称的裸地地貌，包含中央低地、后侧山脊、分离丘陵、南侧岩质半岛和深湾。不包含树木、草地、沙滩、建筑或水面。自然装饰模型单独保存在 `Assets/LastLandfall/Resources/Models/Nature/`，可按需摆放到场景中。其他模型按建筑、基础设施和环境分组；完整清单见 `Assets/LastLandfall/Art/3D_ASSET_CATALOG.md`。

编辑器原型场景和运行时加载流程都使用 V2。自然植被摆放、岸边沙砾和水面效果属于后续场景美术工作，不再混在岛屿地形模型里。
