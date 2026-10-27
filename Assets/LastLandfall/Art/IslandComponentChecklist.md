# 岛屿资产清单

当前运行时优先使用完整的扩展版主岛、西岛和东岛；三岛模型不齐时回退到自然版，再在相应资源缺失时使用 Gate25／Gate26。扩展版已有地面细节，不重复加载旧版 `IslandDetail_*` 细节层。详细说明见 [岛屿扩展说明](../../../Docs/IslandExpansion.md)。

## 当前资源

| 资源 | 用途 |
| --- | --- |
| `Assets/LastLandfall/Resources/Models/Environment/Island_Main_Expanded.fbx` | 扩展版主岛 |
| `Assets/LastLandfall/Resources/Models/Environment/Island_West_Expanded.fbx` | 扩展版西岛 |
| `Assets/LastLandfall/Resources/Models/Environment/Island_East_Expanded.fbx` | 扩展版东岛 |
| `Assets/LastLandfall/Art/Source/Environment/Island_Main_Expanded.blend`、`Island_West_Expanded.blend`、`Island_East_Expanded.blend` | 三岛可编辑源文件 |
| `Assets/LastLandfall/Resources/Models/Environment/Gate26_CapsizedWreck_Expanded.fbx` | 独立扩展版沉船 |
| `Art/Reports/IslandExpansion/Expanded_Archipelago.png` | 三岛总览预览，路径相对于项目根目录 |

## Gate25 历史与回退资源

| 资源 | 用途 |
| --- | --- |
| `Assets/LastLandfall/Resources/Models/Environment/IslandReference_Gate25.fbx` | Gate25 主岛回退模型 |
| `work/island_final_candidate/Assets_Generated/LastLandfall_Island_GrassCoverage_Gate25.blend` | Gate25 可编辑的 Blender 源文件 |
| `work/island_final_candidate/Assets_Generated/LastLandfall_Island_GrassCoverage_Gate25.fbx` | Gate25 原始 Unity 导出文件 |
| `Assets/LastLandfall/Art/Source/Environment/IslandReference_V2.blend` | Gate25 使用的基础地形源文件 |
| `Assets/LastLandfall/Resources/Models/Environment/IslandReference_V2.fbx` | 旧版裸地模型，保留作回退 |
| `Assets/LastLandfall/Art/Previews/Environment/IslandReference_V2_Reference.png` | 主视角预览 |
| `Assets/LastLandfall/Art/Previews/Environment/IslandReference_V2_Top.png` | 顶视预览 |
| `Assets/LastLandfall/Art/Previews/Environment/IslandReference_V2_Clay.png` | 灰模预览 |
| `Assets/LastLandfall/Art/Materials/IslandReference_V2/` | V2 裸地模型材质 |
| `work/island_final_candidate/Gate25_GrassCoverage_Handoff.md` | Gate25 的地形、植被、溪流和导入说明 |
| `work/island_final_candidate/Scripts/Gate25_harvest_forest_and_flow_uv.py` | Gate25 岛屿候选生成器 |

## Gate25 范围

Gate25 在基础地形上加入顶点绘制地貌、树木、草丛、蕨类、溪流和池塘。它的场景导出包含数百个独立网格；建造网格和碰撞只使用主地形网格，装饰网格不作为建造表面。自然资产目录仍保存可单独摆放的 OBJ 模型。

Gate25 的溪流和池塘使用 FBX 内的水面网格与顶点颜色。外海使用项目内的动态水面；当前扩展版的水体和环境请参阅岛屿扩展及发布复核记录。
