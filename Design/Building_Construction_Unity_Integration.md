# 建筑施工接入 Unity

## 当前状态

已完成代码接线与资源导出，覆盖 25 套资产、29 个独立模块、3,871 个施工构件。当前电脑未运行 Unity；没有进行编译、Play Mode、画面或性能验证。

25 套场景资产现已接入分类建造菜单和场景科技等级筛选。建筑解锁及研究前置条件见 [`LastLandfall_Scenario_Progression.md`](LastLandfall_Scenario_Progression.md)；施工控制器完工事件也会通知科技系统。资源价格仍由建造菜单各条目配置，研究本身目前不消耗资源。

## 放置到完工

1. 放置预览继续显示成品；预览不创建施工任务。
2. 玩家确认后沿用原有地形判定、扣费和占地保留；地形找平基础立即存在。
3. 控制器隐藏成品，实例化逐件 FBX，从源时间线第 1 帧开始。
4. 按每个零件的 start/end 帧错开安装，软质填充采用比例变化，其他构件保持尺寸并平移落位。
5. 完工时关闭并销毁逐件模型，显示原有按材质合并的静态成品。施工构件不会常驻到完工后的绘制负担中。
6. 道路邻接刷新时保留归一化进度，已经完成的道路保持完成，不重复扣费。

### 道路和码头

- Road*、RescueDock 旧名称由目录映射到对应 DeepSeek 成品与施工文件，两者使用同一资产版本。
- 道路保留现有 180° 导入修正；施工体继承成品局部变换，直路、弯道、T口、十字与封闭端分别绑定。实际连通朝向待 Unity 中查看。
- 新救援码头宽 6.30 米，向陆侧 2.255 米、向水侧 3.64 米；岸线判定和占地保留改为横向 7 格、纵向 -2～4 格的保守范围，避免继续使用旧的三格占地。

## 资源与代码

- `Resources/Construction/Catalog.json`：静态成品、施工 FBX、逐件时间表和旧名称别名。
- `Resources/Construction/<资产>.json`：24 fps 时间表、阶段标签、零件 ID、入场与落位帧。
- `Resources/Models/Construction/<资产>.fbx`：LLC_0000 格式稳定节点 ID，无 FBX 动画剪辑、相机、灯光或展示底台。
- `BuildingConstructionCatalog.cs`：目录与时间表加载缓存。
- `BuildingConstructionController.cs`：进度、逐件显示、完成切换和公共调用接口。
- `BuildPlacementPrototype.cs`：现有建筑放置与道路邻接刷新入口。
- `BuildingModelMaterialImporter.cs`：施工资源沿用源材质清单并保留节点层级。

## 公共接口

所有目录资产均可通过以下方式由剧情、编辑工具或后续玩法创建。调用方负责地形、成本与占地；本接口只处理模型和施工进度。

```csharp
GameObject building = BuildingConstructionController.Create(
    "School_DeepSeek", mapRoot, localPosition, localRotation,
    () => weatherSystem.SimulationSpeed);
var job = building != null ? building.GetComponent<BuildingConstructionController>() : null;
if (job != null)
{
    job.Completed += completed => { /* 此处接后续设施启用逻辑 */ };
    float progressForSave = job.Progress;
    string stage = job.CurrentPhaseName;
}
```

已有成品对象可调用 `TryBegin(host, assetName, finalVisual, speedProvider, initialProgress)`；finalVisual 必须是 host 下的独立成品子对象，不应包含地形基础。

### 工人驱动、暂停与恢复

```csharp
job.SetAutomaticProgress(false); // 由外部任务系统接管，或暂停这一个施工任务
job.SetProgress(savedProgress);  // 0～1；支持恢复和回退到未完工状态
job.SetAutomaticProgress(true);  // 恢复自动推进
```

默认按 `Time.deltaTime × SimulationSpeed` 推进；现有 1×/2×/3×按钮同步影响施工，全局 Time.timeScale=0 时停止。源时间线时长为临时美术节奏，不代表已平衡的施工工期。没有新增存档系统，Progress 提供后续存取入口。

## 故障回退

施工资源、时间表或节点绑定缺失时输出警告并保留成品可见；不吞掉原有占地或重复扣费。成品资源缺失时，现有放置入口沿用原灰盒占位。公共 Create 在找不到成品时返回 null。

## 模块明细

| 模块 | 构件 | 阶段 | 默认时长（秒） |
| --- | ---: | ---: | ---: |
| `Archive_DeepSeek` | 179 | 28 | 44.67 |
| `CouncilHall_DeepSeek` | 418 | 32 | 85.50 |
| `DesalinationPlant_DeepSeek` | 125 | 16 | 29.08 |
| `DirtRoadCorner_DeepSeek` | 16 | 5 | 6.50 |
| `DirtRoadCross_DeepSeek` | 20 | 5 | 6.83 |
| `DirtRoadEnd_DeepSeek` | 16 | 5 | 6.67 |
| `DirtRoadStraight_DeepSeek` | 15 | 5 | 6.50 |
| `DirtRoadTee_DeepSeek` | 19 | 5 | 6.67 |
| `DriftwoodCollectionBoom_DeepSeek` | 127 | 13 | 26.67 |
| `FishingDock_DeepSeek` | 95 | 15 | 23.92 |
| `Forge_DeepSeek` | 132 | 25 | 37.08 |
| `Greenhouse_DeepSeek` | 266 | 31 | 60.33 |
| `LocalCommunicationsCenter_DeepSeek` | 101 | 20 | 28.33 |
| `MedicalStation_DeepSeek` | 151 | 19 | 35.75 |
| `MedicalTent_DeepSeek` | 85 | 17 | 24.25 |
| `PublicKitchen_DeepSeek` | 167 | 27 | 43.17 |
| `RescueDock_DeepSeek` | 129 | 24 | 35.08 |
| `RescueOutpost_DeepSeek` | 145 | 20 | 34.42 |
| `RescueRadioCenter_DeepSeek` | 122 | 24 | 34.17 |
| `ResearchStation_DeepSeek` | 113 | 21 | 31.25 |
| `ResidentHut_DeepSeek` | 192 | 24 | 43.92 |
| `SalvageWorkshop_DeepSeek` | 135 | 25 | 36.58 |
| `School_DeepSeek` | 236 | 26 | 52.42 |
| `Shipyard_DeepSeek` | 123 | 20 | 30.75 |
| `SolarPowerStation_DeepSeek` | 234 | 16 | 45.00 |
| `StorageDepot_DeepSeek` | 246 | 23 | 52.25 |
| `WaterStorageTank` | 96 | 19 | 26.67 |
| `WeatherTideBuoy_DeepSeek` | 83 | 26 | 31.92 |
| `WoodShelter_DeepSeek` | 85 | 16 | 22.75 |

## 再次导出

修改源施工时间线后，先重新生成时间线与报告，再从项目根目录执行：

```powershell
& "D:\Blender 5.2\blender.exe" --background --python-exit-code 1 --python Tools/Blender/export_unity_construction.py
```

导出器同步更新 FBX、时间表、目录及首次生成的 Unity 元数据；已有 GUID 保留。无需在 Unity 中手动拖入 3,871 个节点或绑定 Animator。

## 待 Unity 环境查看

- C# 编译与资源自动导入；材质、透明面与稳定节点名是否保持。
- 首帧空场、阶段中间动作、最后一帧与静态成品切换是否对齐。
- 四向道路拼接、连续拖铺时进度保留、码头岸线与完整占地。
- 1×/2×/3×、Time.timeScale=0、外部进度恢复与回退。
- 多处同时施工时的首载开销、绘制负担和完工释放。

上述项目尚未在本机运行，不将代码完成等同于画面或性能已验证。
