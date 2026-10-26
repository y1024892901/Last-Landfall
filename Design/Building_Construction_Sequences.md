# 全建筑详细施工过程

共 25 套资产、29 条施工序列；552 个阶段、22807 个可播放帧。

每份说明列出实际零件名称、进入帧、落位帧、依附主件、阶段操作与完成要求。新增细节跟随主件安装；所有源模型保持原样。

## 查看与播放

- 点击下表进入逐建筑施工说明。
- 在 Blender 打开对应 Construction.blend，Shift+左方向键回到第 1 帧，空格播放；时间线标记可定位阶段。
- 24 fps；每个构件有连续位移动作，不是几个静态阶段反复显示。
- 关键阶段 PNG 在 `Assets/LastLandfall/Art/Previews/Construction/Detailed/`。
- 动画源文件和逐帧计划已生成；尚未接入 Unity 游戏建造逻辑。

| 建筑 / 模块 | 阶段 | 构件 | 帧数 | 秒 | 详细说明 |
| --- | ---: | ---: | ---: | ---: | --- |
| 档案馆 | 28 | 179 | 1073 | 44.7 | [施工说明](Construction/Archive_DeepSeek.md) |
| 议事厅 | 32 | 418 | 2053 | 85.5 | [施工说明](Construction/CouncilHall_DeepSeek.md) |
| 海水淡化装置 | 16 | 125 | 699 | 29.1 | [施工说明](Construction/DesalinationPlant_DeepSeek.md) |
| 基础土路套件 / DirtRoadCorner | 5 | 16 | 157 | 6.5 | [施工说明](Construction/DirtRoadCorner_DeepSeek.md) |
| 基础土路套件 / DirtRoadCross | 5 | 20 | 165 | 6.9 | [施工说明](Construction/DirtRoadCross_DeepSeek.md) |
| 基础土路套件 / DirtRoadEnd | 5 | 16 | 161 | 6.7 | [施工说明](Construction/DirtRoadEnd_DeepSeek.md) |
| 基础土路套件 / DirtRoadStraight | 5 | 15 | 157 | 6.5 | [施工说明](Construction/DirtRoadStraight_DeepSeek.md) |
| 基础土路套件 / DirtRoadTee | 5 | 19 | 161 | 6.7 | [施工说明](Construction/DirtRoadTee_DeepSeek.md) |
| 漂木收集浮栅 | 13 | 127 | 641 | 26.7 | [施工说明](Construction/DriftwoodCollectionBoom_DeepSeek.md) |
| 渔船码头 | 15 | 95 | 575 | 24.0 | [施工说明](Construction/FishingDock_DeepSeek.md) |
| 锻造炉 | 25 | 132 | 891 | 37.1 | [施工说明](Construction/Forge_DeepSeek.md) |
| 温室 | 31 | 266 | 1449 | 60.4 | [施工说明](Construction/Greenhouse_DeepSeek.md) |
| 初始通讯中心 | 20 | 101 | 681 | 28.4 | [施工说明](Construction/LocalCommunicationsCenter_DeepSeek.md) |
| 医疗站 | 19 | 151 | 859 | 35.8 | [施工说明](Construction/MedicalStation_DeepSeek.md) |
| 医疗帐篷 | 17 | 85 | 583 | 24.3 | [施工说明](Construction/MedicalTent_DeepSeek.md) |
| 公共厨房 | 27 | 167 | 1037 | 43.2 | [施工说明](Construction/PublicKitchen_DeepSeek.md) |
| 救援码头 | 24 | 129 | 843 | 35.1 | [施工说明](Construction/RescueDock_DeepSeek.md) |
| 救援前哨 | 20 | 145 | 827 | 34.5 | [施工说明](Construction/RescueOutpost_DeepSeek.md) |
| 长距通讯站 | 24 | 122 | 821 | 34.2 | [施工说明](Construction/RescueRadioCenter_DeepSeek.md) |
| 研究站 | 21 | 113 | 751 | 31.3 | [施工说明](Construction/ResearchStation_DeepSeek.md) |
| 居民小屋 | 24 | 192 | 1055 | 44.0 | [施工说明](Construction/ResidentHut_DeepSeek.md) |
| 废料拆解工坊 | 25 | 135 | 879 | 36.6 | [施工说明](Construction/SalvageWorkshop_DeepSeek.md) |
| 学校 | 26 | 236 | 1259 | 52.5 | [施工说明](Construction/School_DeepSeek.md) |
| 船坞 | 20 | 123 | 739 | 30.8 | [施工说明](Construction/Shipyard_DeepSeek.md) |
| 太阳能发电站 | 16 | 234 | 1081 | 45.0 | [施工说明](Construction/SolarPowerStation_DeepSeek.md) |
| 仓库 | 23 | 246 | 1255 | 52.3 | [施工说明](Construction/StorageDepot_DeepSeek.md) |
| 储水设施 | 19 | 96 | 641 | 26.7 | [施工说明](Construction/WaterStorageTank.md) |
| 气象潮位浮标 | 26 | 83 | 767 | 32.0 | [施工说明](Construction/WeatherTideBuoy_DeepSeek.md) |
| 木棚 | 16 | 85 | 547 | 22.8 | [施工说明](Construction/WoodShelter_DeepSeek.md) |

## 施工预览总览

[查看全部施工序列总览](../Assets/LastLandfall/Art/Previews/Construction/Detailed/All_Construction_Overview.jpg)

各建筑的阶段拼图在对应施工说明的“阶段总览”处。

## 重新生成

```powershell
& "D:\Blender 5.2\blender.exe" --background --python Tools/Blender/build_all_construction_sequences.py
# 附带阶段预览：在命令尾部添加 -- --preview
# 单资产： -- --asset=Greenhouse_DeepSeek --preview
```

全帧导出：打开施工 blend，在输出设置选择目录，执行“渲染 → 渲染动画”。各阶段完整构件计划见 `Assets/LastLandfall/Art/Reports/Construction/catalog.json`。
