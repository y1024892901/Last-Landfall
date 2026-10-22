# Last Landfall 建筑建模清单

按 `LastLandfall_Scenario_Progression.md` 逐栋走六视图概念图 → DeepSeek 脚本 → Blender 生成 → 六向与网格检查 → Blend/FBX/预览归档。基础版资产保留不覆盖；本表只把完成这条新流程的 `_DeepSeek` 成品标为完成。

## 进度

- 已完成：14 / 25
- 本轮停止位置：救援指挥／长距通讯站；按用户要求不推进下一项
- 下一项：气象与潮位浮标
- 每栋输出：六视图概念参考、DeepSeek 提示词、独立 Blender 脚本、`.blend`、`.fbx`、预览、QA 六视图。

## 0级：初始前哨

| 建筑/设施 | DeepSeek 流程 |
| --- | --- |
| 木棚 | 待做 |
| 研究站 | 待做 |
| 医疗帐篷 | 待做 |
| 初始通讯中心 | 待做 |
| 基础土路套件 | 待做 |

## 1级：饮水与近海资源

| 建筑/设施 | DeepSeek 流程 |
| --- | --- |
| 固定海水淡化装置 | 已完成：`DesalinationPlant_DeepSeek` |
| 储水设施 | 已完成：`WaterStorageTank_DeepSeek` |
| 漂木收集浮栅 | 已完成：`DriftwoodCollectionBoom_DeepSeek` |
| 渔船码头 | 已完成：`FishingDock_DeepSeek` |
| 基础仓库 | 已完成：`StorageDepot_DeepSeek` |
| 救援码头 | 已完成：`RescueDock_DeepSeek` |
| 居民小屋 | 已完成：`ResidentHut_DeepSeek` |

## 2级：供电与医疗

| 建筑/设施 | DeepSeek 流程 |
| --- | --- |
| 太阳能发电站 | 已完成：`SolarPowerStation_DeepSeek` |
| 医疗站 | 已完成：`MedicalStation_DeepSeek` |

## 3级：食物与加工

| 建筑/设施 | DeepSeek 流程 |
| --- | --- |
| 高科技温室 | 已完成：`Greenhouse_DeepSeek`；六向检查后补上控制柜混凝土基座并调整入口踏步。213 个网格增至 214 个，最终包围盒 4.490 × 3.960 × 3.413 米，最低 Z=0，非流形边 0。 |
| 公共厨房 | 已完成：`PublicKitchen_DeepSeek`；双盆真实开孔、屋顶封闭拓扑修正后生成。139 个网格，包围盒 2.912 × 2.580 × 3.000 米，最低 Z=0，非流形边 0，松散几何 0；Blend/FBX/预览/六视图齐全。 |
| 废料拆解工坊 | 已完成：`SalvageWorkshop_DeepSeek`；补齐六视图、专属集合和安全清理后生成。90 个网格，包围盒 1.850 × 1.767 × 2.115 米，最低 Z=0，非流形边 0，松散几何 0；Blend/FBX/预览/六视图齐全。逐对象拓扑检查不能判定不同网格之间的穿插。 |
| 锻造炉 | 已完成：`Forge_DeepSeek`；独立石基座、空心火口、烟道、风箱、铁砧、煤篮、淬火槽和工具架。99 个网格，包围盒 2.000 × 2.000 × 2.620 米，最低 Z=0，非流形边 0，松散几何 0；Blend/FBX/预览/六视图齐全，FBX 重导入为 99 个网格、无相机或灯光。逐对象拓扑检查不检测不同网格间的相交。 |

## 4级：区域救援

| 建筑/设施 | DeepSeek 流程 |
| --- | --- |
| 救援指挥／长距通讯站 | 已完成：`RescueRadioCenter_DeepSeek`；86 个网格，包围盒 2.000 × 2.000 × 2.700 米，最低 Z=0；非流形边 0、松散几何 0。Blend/FBX/预览/六视图齐全，FBX 重导入为 86 个网格、无相机或灯光。逐对象拓扑检查不能检测不同网格之间的穿插。 |
| 气象与潮位浮标 | 待做 |
| 船坞 | 待做 |
| 救援前哨 | 待做 |

## 5级：社区与文化

| 建筑/设施 | DeepSeek 流程 |
| --- | --- |
| 学校 | 待做 |
| 档案馆 | 待做 |
| 议事厅 | 待做 |
