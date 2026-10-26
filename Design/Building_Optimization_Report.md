# 25 个建筑模型检查与优化

日期：2026-10-26。范围以 `Building_Modeling_Progress.md` 的 25 项成品为准，储水设施对应 `WaterStorageTank.blend`；道路套件输出 5 个独立 FBX。

## 已完成

- 游戏 FBX 网格对象：原版 2,866 → 优化后 238，减少 91.7%。修复支承后，可编辑源文件共 2,896 个零件；游戏导出按材质合并不透明零件。
- 透明玻璃保持独立对象，以保留透明表面的排序粒度。Blender 源文件保留可逐件编辑的结构。
- 修复档案馆两根薄通风条的 4 个退化面，并限制生成器中薄件的倒角宽度。
- 新增 Unity 建筑材质导入器，按 Blender 材质清单恢复 URP 颜色、透明度、金属度、光滑度及发光参数。
- 统一优化导出的 FBX 轴向；旧生成器在学校、档案馆、议事厅上使用了不同轴向设置。
- 修正若干生成脚本的 Blender 5.2 透明材质 API，以及储水设施的 EEVEE 引擎选择。

## 结构修复

- 温室：为两个种植槽补上 8 个支脚，消除离地板 30 mm 的悬空。
- 议事厅：补上两个门把手安装座，连接把手与门扇。
- 公共厨房：4 个货箱下移到实际层板面；延长排水立管，与弯头接通。
- 医疗站：扩大玻璃及中梃，使它们嵌入窗框，消除周边缝隙。
- 救援前哨：调整 3 根平台承重梁方向，使它们垂直承托所有铺板。
- 渔船码头：延长网绳，使横绳连到立柱、竖绳挂到上横杆。
- 气象浮标：补上风向标尾翼连接臂。
- 废料工坊：补上剪切机底座、后导轨、刀片连接横梁及吊物连接件；将后壁阴影板贴回墙面。
- 居民小屋：补上 4 根窗侧立柱，支承侧墙拼板及窗框。
- 救援码头：补上登船梯安装支架、救援艇挡风板支架及方向盘连接柱。
- 船坞：增加 6 个连接木块，把上层船板与 3 个肋骨站连接。

## 验证结果

- 25 个源模型的非流形边、松散顶点、退化面均为 0；没有完全重叠的重复网格对象，也没有负缩放对象。
- 源模型全部保持原有外包围盒（0.2 mm 容差），最低点均与 Z=0 对齐（2 mm 容差）。
- 29 个 FBX 全部通过重导入检查：网格数、三角面数、三角表面位置、材质面数一致；无相机或灯光混入。表面位置核对容差为 0.2 mm。
- 使用修复后的源模型与优化 FBX，逐一渲染同机位正、反面，共 100 张图。FBX 对照使用源材质，以独立检查几何与法线；Unity 材质由导入清单处理。
- 支承候选检查使用扩大 15 mm 的世界轴对齐包围盒连接图。修复后只剩救援码头的独立水上船体组件；它不应被固定到地面。该检查不能证明任意曲面都物理接触，也不能替代游戏角色通行或完整实体碰撞检查。
- 本机没有 Unity，新增 C# 导入器尚未经过 Unity 编译与实机渲染验证；性能收益尚未用帧率测量。

## 每项导出统计

| 模型 | 源零件（修复后） | 游戏网格 | 三角面 |
| --- | ---: | ---: | ---: |
| Archive_DeepSeek | 139 | 9 | 6,388 |
| CouncilHall_DeepSeek | 378 | 10 | 16,532 |
| DesalinationPlant_DeepSeek | 82 | 7 | 4,368 |
| Forge_DeepSeek | 99 | 13 | 1,420 |
| Greenhouse_DeepSeek | 222 | 24 | 5,144 |
| LocalCommunicationsCenter_DeepSeek | 59 | 10 | 932 |
| MedicalStation_DeepSeek | 130 | 9 | 1,680 |
| MedicalTent_DeepSeek | 54 | 8 | 1,912 |
| PublicKitchen_DeepSeek | 139 | 11 | 1,892 |
| RescueOutpost_DeepSeek | 98 | 11 | 2,492 |
| RescueRadioCenter_DeepSeek | 86 | 9 | 1,272 |
| ResearchStation_DeepSeek | 74 | 14 | 1,088 |
| ResidentHut_DeepSeek | 143 | 4 | 1,764 |
| SalvageWorkshop_DeepSeek | 94 | 9 | 3,944 |
| School_DeepSeek | 199 | 8 | 6,348 |
| SolarPowerStation_DeepSeek | 180 | 7 | 2,560 |
| StorageDepot_DeepSeek | 213 | 7 | 2,924 |
| WoodShelter_DeepSeek | 46 | 6 | 656 |
| DirtRoadTiles_DeepSeek | 46 | 25 | 5,572 |
| DriftwoodCollectionBoom_DeepSeek | 83 | 5 | 2,036 |
| FishingDock_DeepSeek | 68 | 5 | 1,368 |
| RescueDock_DeepSeek | 78 | 7 | 2,372 |
| Shipyard_DeepSeek | 80 | 8 | 2,148 |
| WeatherTideBuoy_DeepSeek | 56 | 7 | 5,988 |
| WaterStorageTank | 50 | 5 | 3,976 |

## 预览与复现

[正面总览](../Assets/LastLandfall/Art/Reports/BuildingAudit/25_Models_Optimized_Front.jpg) · [背面总览](../Assets/LastLandfall/Art/Reports/BuildingAudit/25_Models_Optimized_Rear.jpg)

逐模型正反面对照位于 `Assets/LastLandfall/Art/Reports/BuildingAudit/Visuals/`。原始、最终网格报告、FBX 核对报告和支承候选报告都在同一审查目录。

修改或重新运行单栋建模脚本后，从项目根目录执行以下优化步骤，以免重新产生数百个分散的游戏网格：

```powershell
& 'D:\Blender 5.2\blender.exe' --background --python-exit-code 1 --python Tools/Blender/optimize_building_models.py
```

`repair_building_structure.py` 用于将本轮已审查的结构修复应用到现有源文件；对应单栋生成器也已包含修复。`audit_building_models.py`、`audit_building_supports.py` 与 `render_building_optimization_review.py` 可复查源文件、连接候选和外观。

## 其他已发现的接入差异

- 当前游戏菜单中，救援码头及道路的图标使用新版 DeepSeek 资产，实际加载仍指向旧版 `RescueDock` / `Road*`。这些旧版的玩法和道路旋转约定应单独核对后再切换。
- 此前温室施工样例来自旧版 `Greenhouse.blend`，本次审核的成品为 `Greenhouse_DeepSeek.blend`。制作这批建筑的完整施工动画时，应以成品源文件建立新序列。
