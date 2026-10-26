# 议事厅：详细建造过程

- 当前模型：`Assets/LastLandfall/Art/Source/Buildings/CouncilHall_DeepSeek.blend`
- 动画：`Assets/LastLandfall/Art/Source/Construction/Detailed/CouncilHall_DeepSeek_Construction.blend`
- 帧率：24 fps；共 2053 帧，85.5 秒。
- 构件：418 个；阶段：32 个。

## 编排规则

以下时长为动画节奏，不是现实工期。每阶段内部继续逐件安装，画面不是只在阶段末跳变。主件落位后才安装对应紧固件和装饰。数字范围均含首尾帧。

先基础、后承重结构与围护；设备支座先于设备，收边和附属件随依附构件安装。

## 施工准备

1. 核对当前模型、朝向、占地和入口，保持最终轮廓与游戏接口。
2. 按下列构件清单分包，确认支承部件已完成再安装上部构件。
3. 首帧为空场；施工动作不改变最终网格和材质。

## 阶段总览

[查看带标签的阶段拼图](../../Assets/LastLandfall/Art/Previews/Construction/Detailed/CouncilHall_DeepSeek/Overview.jpg)

基础墩 → 横地梁 → 纵地梁 → 主楼板 → 地板铺板 → 门廊基础 → 门廊甲板 → 主体框架 → 后墙 → 左墙 → 右墙 → 前墙 → 门框 → 门洞衬板 → 门扇 → 门把手 → 高窗框 → 高窗玻璃 → 侧窗框 → 侧玻璃 → 百叶通风 → 门廊柱 → 门廊梁撑 → 门廊棚 → 四坡屋顶 → 压棱接缝 → 屋脊补片 → 排水 → 入口踏步 → 栏杆 → 公共公告板 → 入口灯

## 01．基础墩

**帧 2–61**（2.5 秒；12 件）。

**前置条件：** 场地定位完成。

**操作：** 按支承端到自由端的顺序安装基础墩；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Foundation_Pier_0_0` | 2 | 22 | `` |
| 2 | `CouncilHall_DeepSeek_Foundation_Pier_0_1` | 6 | 26 | `` |
| 3 | `CouncilHall_DeepSeek_Foundation_Pier_0_2` | 10 | 30 | `` |
| 4 | `CouncilHall_DeepSeek_Foundation_Pier_1_0` | 14 | 34 | `` |
| 5 | `CouncilHall_DeepSeek_Foundation_Pier_1_1` | 18 | 38 | `` |
| 6 | `CouncilHall_DeepSeek_Foundation_Pier_1_2` | 22 | 42 | `` |
| 7 | `CouncilHall_DeepSeek_Foundation_Pier_2_0` | 26 | 46 | `` |
| 8 | `CouncilHall_DeepSeek_Foundation_Pier_2_1` | 30 | 50 | `` |
| 9 | `CouncilHall_DeepSeek_Foundation_Pier_2_2` | 34 | 54 | `` |
| 10 | `CouncilHall_DeepSeek_Foundation_Pier_3_0` | 38 | 58 | `` |
| 11 | `CouncilHall_DeepSeek_Foundation_Pier_3_1` | 42 | 61 | `` |
| 12 | `CouncilHall_DeepSeek_Foundation_Pier_3_2` | 46 | 61 | `` |

**细分工序：**

1. 按最终占地确定各支承点，先处理角点，再补中间点。
2. 构件逐件垂直落位；各顶面以当前模型的承梁标高为准。
3. 逐点核对上层梁的落脚位置，保留桩间水流或通风空间。
4. 本阶段共 12 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 基础与后续承梁相接，所有支承点保持源模型高差。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 02．横地梁

**帧 62–85**（1.0 秒；3 件）。

**前置条件：** 第 01 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装横地梁；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Foundation_Beam_X_-4.12` | 62 | 82 | `` |
| 2 | `CouncilHall_DeepSeek_Foundation_Beam_X_0.0` | 66 | 85 | `` |
| 3 | `CouncilHall_DeepSeek_Foundation_Beam_X_4.12` | 70 | 85 | `` |

**细分工序：**

1. 先安装主承重方向构件，再装横向连接构件。
2. 每根梁从一端导入，连接两端支座；中间构件按固定间隔补齐。
3. 主体闭合后安装连接片与紧固件，保留与上下层构件的接触关系。
4. 本阶段共 3 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 梁端有对应支承，框架闭合，未以悬空梁代替支座。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 03．纵地梁

**帧 86–109**（1.0 秒；3 件）。

**前置条件：** 第 02 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装纵地梁；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Foundation_Beam_Y_-4.08` | 86 | 106 | `` |
| 2 | `CouncilHall_DeepSeek_Foundation_Beam_Y_0.0` | 90 | 109 | `` |
| 3 | `CouncilHall_DeepSeek_Foundation_Beam_Y_4.08` | 94 | 109 | `` |

**细分工序：**

1. 先安装主承重方向构件，再装横向连接构件。
2. 每根梁从一端导入，连接两端支座；中间构件按固定间隔补齐。
3. 主体闭合后安装连接片与紧固件，保留与上下层构件的接触关系。
4. 本阶段共 3 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 梁端有对应支承，框架闭合，未以悬空梁代替支座。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 04．主楼板

**帧 110–133**（1.0 秒；1 件）。

**前置条件：** 第 03 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装主楼板；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Floor_Main` | 110 | 130 | `` |

**细分工序：**

1. 核对本阶段清单中每个主体的安装面、承架或连接端。
2. 先安装主体和支承连接，再依次补齐其可拆附属部件。
3. 依照逐件帧表错开进入，主体完全落位后才安装所依附的标牌、仪表或紧固细节。
4. 本阶段共 1 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与已建结构连接，安装位置、朝向和材质与源模型一致。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 05．地板铺板

**帧 134–217**（3.5 秒；18 件）。

**前置条件：** 第 04 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装地板铺板；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Floor_Plank_00` | 134 | 154 | `` |
| 2 | `CouncilHall_DeepSeek_Floor_Plank_01` | 138 | 158 | `` |
| 3 | `CouncilHall_DeepSeek_Floor_Plank_02` | 142 | 162 | `` |
| 4 | `CouncilHall_DeepSeek_Floor_Plank_03` | 146 | 166 | `` |
| 5 | `CouncilHall_DeepSeek_Floor_Plank_04` | 150 | 170 | `` |
| 6 | `CouncilHall_DeepSeek_Floor_Plank_05` | 154 | 174 | `` |
| 7 | `CouncilHall_DeepSeek_Floor_Plank_06` | 158 | 178 | `` |
| 8 | `CouncilHall_DeepSeek_Floor_Plank_07` | 162 | 182 | `` |
| 9 | `CouncilHall_DeepSeek_Floor_Plank_08` | 166 | 186 | `` |
| 10 | `CouncilHall_DeepSeek_Floor_Plank_09` | 170 | 190 | `` |
| 11 | `CouncilHall_DeepSeek_Floor_Plank_10` | 174 | 194 | `` |
| 12 | `CouncilHall_DeepSeek_Floor_Plank_11` | 178 | 198 | `` |
| 13 | `CouncilHall_DeepSeek_Floor_Plank_12` | 182 | 202 | `` |
| 14 | `CouncilHall_DeepSeek_Floor_Plank_13` | 186 | 206 | `` |
| 15 | `CouncilHall_DeepSeek_Floor_Plank_14` | 190 | 210 | `` |
| 16 | `CouncilHall_DeepSeek_Floor_Plank_15` | 194 | 214 | `` |
| 17 | `CouncilHall_DeepSeek_Floor_Plank_16` | 198 | 217 | `` |
| 18 | `CouncilHall_DeepSeek_Floor_Plank_17` | 202 | 217 | `` |

**细分工序：**

1. 从远侧或角部开始铺设第一块板，露出尚未铺设的搁栅。
2. 逐块向入口方向延伸，保持原有板缝及边缘收口。
3. 沿开口裁边的板件使用原模型形状，不填平楼梯口、排水口或检修口。
4. 本阶段共 18 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 板件沿现有梁架铺开，开口和模块接口完整保留。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 06．门廊基础

**帧 218–249**（1.3 秒；5 件）。

**前置条件：** 第 05 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装门廊基础；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Porch_StonePier_-1` | 218 | 238 | `` |
| 2 | `CouncilHall_DeepSeek_Porch_StonePier_1` | 222 | 242 | `` |
| 3 | `CouncilHall_DeepSeek_Porch_Beam_Front` | 226 | 246 | `` |
| 4 | `CouncilHall_DeepSeek_Porch_Beam_Side_-1` | 230 | 249 | `` |
| 5 | `CouncilHall_DeepSeek_Porch_Beam_Side_1` | 234 | 249 | `` |

**细分工序：**

1. 按最终占地确定各支承点，先处理角点，再补中间点。
2. 构件逐件垂直落位；各顶面以当前模型的承梁标高为准。
3. 逐点核对上层梁的落脚位置，保留桩间水流或通风空间。
4. 本阶段共 5 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 基础与后续承梁相接，所有支承点保持源模型高差。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 07．门廊甲板

**帧 250–313**（2.7 秒；13 件）。

**前置条件：** 第 06 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装门廊甲板；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Porch_Deck` | 250 | 270 | `` |
| 2 | `CouncilHall_DeepSeek_Porch_DeckBoard_00` | 254 | 274 | `` |
| 3 | `CouncilHall_DeepSeek_Porch_DeckBoard_01` | 258 | 278 | `` |
| 4 | `CouncilHall_DeepSeek_Porch_DeckBoard_02` | 262 | 282 | `` |
| 5 | `CouncilHall_DeepSeek_Porch_DeckBoard_03` | 266 | 286 | `` |
| 6 | `CouncilHall_DeepSeek_Porch_DeckBoard_04` | 270 | 290 | `` |
| 7 | `CouncilHall_DeepSeek_Porch_DeckBoard_05` | 274 | 294 | `` |
| 8 | `CouncilHall_DeepSeek_Porch_DeckBoard_06` | 278 | 298 | `` |
| 9 | `CouncilHall_DeepSeek_Porch_DeckBoard_07` | 282 | 302 | `` |
| 10 | `CouncilHall_DeepSeek_Porch_DeckBoard_08` | 286 | 306 | `` |
| 11 | `CouncilHall_DeepSeek_Porch_DeckBoard_09` | 290 | 310 | `` |
| 12 | `CouncilHall_DeepSeek_Porch_DeckBoard_10` | 294 | 313 | `` |
| 13 | `CouncilHall_DeepSeek_Porch_DeckBoard_11` | 298 | 313 | `` |

**细分工序：**

1. 从远侧或角部开始铺设第一块板，露出尚未铺设的搁栅。
2. 逐块向入口方向延伸，保持原有板缝及边缘收口。
3. 沿开口裁边的板件使用原模型形状，不填平楼梯口、排水口或检修口。
4. 本阶段共 13 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 板件沿现有梁架铺开，开口和模块接口完整保留。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 08．主体框架

**帧 314–373**（2.5 秒；12 件）。

**前置条件：** 第 07 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装主体框架；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Structure_CornerPost_0_0` | 314 | 334 | `` |
| 2 | `CouncilHall_DeepSeek_Structure_CornerPost_0_1` | 318 | 338 | `` |
| 3 | `CouncilHall_DeepSeek_Structure_CornerPost_1_0` | 322 | 342 | `` |
| 4 | `CouncilHall_DeepSeek_Structure_CornerPost_1_1` | 326 | 346 | `` |
| 5 | `CouncilHall_DeepSeek_Structure_FrontBack_Belt_0.98_0` | 330 | 350 | `` |
| 6 | `CouncilHall_DeepSeek_Structure_FrontBack_Belt_0.98_1` | 334 | 354 | `` |
| 7 | `CouncilHall_DeepSeek_Structure_Side_Belt_0.98_0` | 338 | 358 | `` |
| 8 | `CouncilHall_DeepSeek_Structure_Side_Belt_0.98_1` | 342 | 362 | `` |
| 9 | `CouncilHall_DeepSeek_Structure_FrontBack_Belt_2.83_0` | 346 | 366 | `` |
| 10 | `CouncilHall_DeepSeek_Structure_FrontBack_Belt_2.83_1` | 350 | 370 | `` |
| 11 | `CouncilHall_DeepSeek_Structure_Side_Belt_2.83_0` | 354 | 373 | `` |
| 12 | `CouncilHall_DeepSeek_Structure_Side_Belt_2.83_1` | 358 | 373 | `` |

**细分工序：**

1. 核对本阶段清单中每个主体的安装面、承架或连接端。
2. 先安装主体和支承连接，再依次补齐其可拆附属部件。
3. 依照逐件帧表错开进入，主体完全落位后才安装所依附的标牌、仪表或紧固细节。
4. 本阶段共 12 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与已建结构连接，安装位置、朝向和材质与源模型一致。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 09．后墙

**帧 374–425**（2.2 秒；10 件）。

**前置条件：** 第 08 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装后墙；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Wall_Back_Lower_0` | 374 | 394 | `` |
| 2 | `CouncilHall_DeepSeek_Wall_Back_Lower_1` | 378 | 398 | `` |
| 3 | `CouncilHall_DeepSeek_Wall_Back_Lower_2` | 382 | 402 | `` |
| 4 | `CouncilHall_DeepSeek_Wall_Back_Segment_0` | 386 | 406 | `` |
| 5 | `CouncilHall_DeepSeek_Wall_Back_Segment_1` | 390 | 410 | `` |
| 6 | `CouncilHall_DeepSeek_Wall_Back_Segment_2` | 394 | 414 | `` |
| 7 | `CouncilHall_DeepSeek_Wall_Back_Segment_End` | 398 | 418 | `` |
| 8 | `CouncilHall_DeepSeek_Wall_Back_Upper_0` | 402 | 422 | `` |
| 9 | `CouncilHall_DeepSeek_Wall_Back_Upper_1` | 406 | 425 | `` |
| 10 | `CouncilHall_DeepSeek_Wall_Back_Upper_2` | 410 | 425 | `` |

**细分工序：**

1. 确认墙角立柱与上下横档已在场，先安装背面再安装侧面。
2. 板件由下到上或沿框架逐片固定，前侧开口尽量延后封闭。
3. 洞口四周按原模型收边，不用板件封堵门、窗或设备口。
4. 本阶段共 10 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 墙面有框架依托，所有门窗与服务窗口保持通畅。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 10．左墙

**帧 426–477**（2.2 秒；10 件）。

**前置条件：** 第 09 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装左墙；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Wall_Side_-1_Sill_0` | 426 | 446 | `` |
| 2 | `CouncilHall_DeepSeek_Wall_Side_-1_Sill_1` | 430 | 450 | `` |
| 3 | `CouncilHall_DeepSeek_Wall_Side_-1_Sill_2` | 434 | 454 | `` |
| 4 | `CouncilHall_DeepSeek_Wall_Side_-1_PierceSpan_0` | 438 | 458 | `` |
| 5 | `CouncilHall_DeepSeek_Wall_Side_-1_PierceSpan_1` | 442 | 462 | `` |
| 6 | `CouncilHall_DeepSeek_Wall_Side_-1_PierceSpan_2` | 446 | 466 | `` |
| 7 | `CouncilHall_DeepSeek_Wall_Side_-1_PierceSpan_End` | 450 | 470 | `` |
| 8 | `CouncilHall_DeepSeek_Wall_Side_-1_Head_0` | 454 | 474 | `` |
| 9 | `CouncilHall_DeepSeek_Wall_Side_-1_Head_1` | 458 | 477 | `` |
| 10 | `CouncilHall_DeepSeek_Wall_Side_-1_Head_2` | 462 | 477 | `` |

**细分工序：**

1. 确认墙角立柱与上下横档已在场，先安装背面再安装侧面。
2. 板件由下到上或沿框架逐片固定，前侧开口尽量延后封闭。
3. 洞口四周按原模型收边，不用板件封堵门、窗或设备口。
4. 本阶段共 10 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 墙面有框架依托，所有门窗与服务窗口保持通畅。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 11．右墙

**帧 478–529**（2.2 秒；10 件）。

**前置条件：** 第 10 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装右墙；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Wall_Side_1_Sill_0` | 478 | 498 | `` |
| 2 | `CouncilHall_DeepSeek_Wall_Side_1_Sill_1` | 482 | 502 | `` |
| 3 | `CouncilHall_DeepSeek_Wall_Side_1_Sill_2` | 486 | 506 | `` |
| 4 | `CouncilHall_DeepSeek_Wall_Side_1_PierceSpan_0` | 490 | 510 | `` |
| 5 | `CouncilHall_DeepSeek_Wall_Side_1_PierceSpan_1` | 494 | 514 | `` |
| 6 | `CouncilHall_DeepSeek_Wall_Side_1_PierceSpan_2` | 498 | 518 | `` |
| 7 | `CouncilHall_DeepSeek_Wall_Side_1_PierceSpan_End` | 502 | 522 | `` |
| 8 | `CouncilHall_DeepSeek_Wall_Side_1_Head_0` | 506 | 526 | `` |
| 9 | `CouncilHall_DeepSeek_Wall_Side_1_Head_1` | 510 | 529 | `` |
| 10 | `CouncilHall_DeepSeek_Wall_Side_1_Head_2` | 514 | 529 | `` |

**细分工序：**

1. 确认墙角立柱与上下横档已在场，先安装背面再安装侧面。
2. 板件由下到上或沿框架逐片固定，前侧开口尽量延后封闭。
3. 洞口四周按原模型收边，不用板件封堵门、窗或设备口。
4. 本阶段共 10 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 墙面有框架依托，所有门窗与服务窗口保持通畅。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 12．前墙

**帧 530–585**（2.3 秒；11 件）。

**前置条件：** 第 11 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装前墙；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Wall_Front_Lower_0` | 530 | 550 | `` |
| 2 | `CouncilHall_DeepSeek_Wall_Front_Lower_1` | 534 | 554 | `` |
| 3 | `CouncilHall_DeepSeek_Front_Siding_Board_0` | 538 | 558 | `` |
| 4 | `CouncilHall_DeepSeek_Front_Siding_Board_1` | 542 | 562 | `` |
| 5 | `CouncilHall_DeepSeek_Front_Siding_Board_2` | 546 | 566 | `` |
| 6 | `CouncilHall_DeepSeek_Front_Siding_Board_3` | 550 | 570 | `` |
| 7 | `CouncilHall_DeepSeek_Wall_Front_WindowZone_0` | 554 | 574 | `` |
| 8 | `CouncilHall_DeepSeek_Wall_Front_WindowZone_1` | 558 | 578 | `` |
| 9 | `CouncilHall_DeepSeek_Wall_Front_WindowZone_2` | 562 | 582 | `` |
| 10 | `CouncilHall_DeepSeek_Wall_Front_WindowZone_3` | 566 | 585 | `` |
| 11 | `CouncilHall_DeepSeek_Wall_Front_Header` | 570 | 585 | `` |

**细分工序：**

1. 确认墙角立柱与上下横档已在场，先安装背面再安装侧面。
2. 板件由下到上或沿框架逐片固定，前侧开口尽量延后封闭。
3. 洞口四周按原模型收边，不用板件封堵门、窗或设备口。
4. 本阶段共 11 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 墙面有框架依托，所有门窗与服务窗口保持通畅。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 13．门框

**帧 586–609**（1.0 秒；3 件）。

**前置条件：** 第 12 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装门框；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_DoorFrame_Jamb_-1` | 586 | 606 | `` |
| 2 | `CouncilHall_DeepSeek_DoorFrame_Jamb_1` | 590 | 609 | `` |
| 3 | `CouncilHall_DeepSeek_DoorFrame_Head` | 594 | 609 | `` |

**细分工序：**

1. 对照已完成墙洞定位两侧竖框，先下端再上端。
2. 连接上横框与中间分格，保持原模型净开口。
3. 本阶段只安装清单中的框件；玻璃、门扇和百叶按后续清单进入。
4. 本阶段共 3 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 框件围绕既有洞口闭合，未缩小原有开口。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 14．门洞衬板

**帧 610–633**（1.0 秒；1 件）。

**前置条件：** 第 13 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装门洞衬板；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Door_Recess_Shadow` | 610 | 630 | `` |

**细分工序：**

1. 核对本阶段清单中每个主体的安装面、承架或连接端。
2. 先安装主体和支承连接，再依次补齐其可拆附属部件。
3. 依照逐件帧表错开进入，主体完全落位后才安装所依附的标牌、仪表或紧固细节。
4. 本阶段共 1 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与已建结构连接，安装位置、朝向和材质与源模型一致。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 15．门扇

**帧 634–709**（3.2 秒；18 件）。

**前置条件：** 第 14 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装门扇；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Door_Leaf_-1_Panel_1.15` | 634 | 654 | `` |
| 2 | `CouncilHall_DeepSeek_Door_Leaf_1_Panel_1.15` | 638 | 658 | `` |
| 3 | `CouncilHall_DeepSeek_Door_Leaf_-1` | 642 | 662 | `` |
| 4 | `CouncilHall_DeepSeek_Door_Leaf_-1_Stile_-1` | 646 | 666 | `` |
| 5 | `CouncilHall_DeepSeek_Door_Leaf_-1_Stile_1` | 650 | 670 | `` |
| 6 | `CouncilHall_DeepSeek_Door_Leaf_1` | 654 | 674 | `` |
| 7 | `CouncilHall_DeepSeek_Door_Leaf_1_Stile_-1` | 658 | 678 | `` |
| 8 | `CouncilHall_DeepSeek_Door_Leaf_1_Stile_1` | 662 | 682 | `` |
| 9 | `CouncilHall_DeepSeek_Door_Leaf_-1_Panel_2.13` | 666 | 685 | `` |
| 10 | `CouncilHall_DeepSeek_Door_Leaf_1_Panel_2.13` | 670 | 685 | `` |
| 11 | `DetailPass__015_Hinge_leaf` | 686 | 696 | `CouncilHall_DeepSeek_Door_Leaf_-1` |
| 12 | `DetailPass__016_Hinge_pin` | 688 | 698 | `CouncilHall_DeepSeek_Door_Leaf_-1` |
| 13 | `DetailPass__017_Hinge_leaf` | 690 | 700 | `CouncilHall_DeepSeek_Door_Leaf_-1` |
| 14 | `DetailPass__018_Hinge_pin` | 692 | 702 | `CouncilHall_DeepSeek_Door_Leaf_-1` |
| 15 | `DetailPass__019_Hinge_leaf` | 694 | 704 | `CouncilHall_DeepSeek_Door_Leaf_1` |
| 16 | `DetailPass__020_Hinge_pin` | 696 | 706 | `CouncilHall_DeepSeek_Door_Leaf_1` |
| 17 | `DetailPass__021_Hinge_leaf` | 698 | 708 | `CouncilHall_DeepSeek_Door_Leaf_1` |
| 18 | `DetailPass__022_Hinge_pin` | 700 | 709 | `CouncilHall_DeepSeek_Door_Leaf_1` |

**细分工序：**

1. 先核对框、支架或铰接端已经完成。
2. 主体由铰接侧或下支承端进入，归位后再装把手、铰链和锁件。
3. 按源模型保留开合状态，检查相邻墙面与设备间的间隙。
4. 本阶段共 18 件，其中 8 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与支承相连，开口和检修空间不被附属件遮挡。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 16．门把手

**帧 710–737**（1.2 秒；4 件）。

**前置条件：** 第 15 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装门把手；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Door_Handle_Mount_-1` | 710 | 730 | `` |
| 2 | `CouncilHall_DeepSeek_Door_Handle_Mount_1` | 714 | 734 | `` |
| 3 | `CouncilHall_DeepSeek_Door_Handle_-1` | 718 | 737 | `` |
| 4 | `CouncilHall_DeepSeek_Door_Handle_1` | 722 | 737 | `` |

**细分工序：**

1. 核对本阶段清单中每个主体的安装面、承架或连接端。
2. 先安装主体和支承连接，再依次补齐其可拆附属部件。
3. 依照逐件帧表错开进入，主体完全落位后才安装所依附的标牌、仪表或紧固细节。
4. 本阶段共 4 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与已建结构连接，安装位置、朝向和材质与源模型一致。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 17．高窗框

**帧 738–797**（2.5 秒；12 件）。

**前置条件：** 第 16 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装高窗框；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Back_Clerestory_0_FrameH_2.35` | 738 | 758 | `` |
| 2 | `CouncilHall_DeepSeek_Back_Clerestory_1_FrameH_2.35` | 742 | 762 | `` |
| 3 | `CouncilHall_DeepSeek_Back_Clerestory_2_FrameH_2.35` | 746 | 766 | `` |
| 4 | `CouncilHall_DeepSeek_Back_Clerestory_0_FrameV_-1` | 750 | 770 | `` |
| 5 | `CouncilHall_DeepSeek_Back_Clerestory_0_FrameV_1` | 754 | 774 | `` |
| 6 | `CouncilHall_DeepSeek_Back_Clerestory_1_FrameV_-1` | 758 | 778 | `` |
| 7 | `CouncilHall_DeepSeek_Back_Clerestory_1_FrameV_1` | 762 | 782 | `` |
| 8 | `CouncilHall_DeepSeek_Back_Clerestory_2_FrameV_-1` | 766 | 786 | `` |
| 9 | `CouncilHall_DeepSeek_Back_Clerestory_2_FrameV_1` | 770 | 790 | `` |
| 10 | `CouncilHall_DeepSeek_Back_Clerestory_0_FrameH_2.72` | 774 | 794 | `` |
| 11 | `CouncilHall_DeepSeek_Back_Clerestory_1_FrameH_2.72` | 778 | 797 | `` |
| 12 | `CouncilHall_DeepSeek_Back_Clerestory_2_FrameH_2.72` | 782 | 797 | `` |

**细分工序：**

1. 对照已完成墙洞定位两侧竖框，先下端再上端。
2. 连接上横框与中间分格，保持原模型净开口。
3. 本阶段只安装清单中的框件；玻璃、门扇和百叶按后续清单进入。
4. 本阶段共 12 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 框件围绕既有洞口闭合，未缩小原有开口。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 18．高窗玻璃

**帧 798–821**（1.0 秒；3 件）。

**前置条件：** 第 17 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装高窗玻璃；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Back_Clerestory_0_Glass` | 798 | 818 | `` |
| 2 | `CouncilHall_DeepSeek_Back_Clerestory_1_Glass` | 802 | 821 | `` |
| 3 | `CouncilHall_DeepSeek_Back_Clerestory_2_Glass` | 806 | 821 | `` |

**细分工序：**

1. 确认四周框、承轨及内部设备已经完成。
2. 面板从框外侧缓慢靠近，先贴近下边缘再归位到最终平面。
3. 装框边附属件；透明或发电工作面保持完整，不新增中心螺栓。
4. 本阶段共 3 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 边缘落在框内，透明面不误变为墙板，工作面无遮挡。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 19．侧窗框

**帧 822–1065**（10.2 秒；58 件）。

**前置条件：** 第 18 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装侧窗框；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_SideWindowJamb_-1_0_-1` | 822 | 842 | `` |
| 2 | `CouncilHall_DeepSeek_SideWindowJamb_-1_0_1` | 826 | 846 | `` |
| 3 | `CouncilHall_DeepSeek_SideWindowJamb_-1_1_-1` | 830 | 850 | `` |
| 4 | `CouncilHall_DeepSeek_SideWindowJamb_-1_1_1` | 834 | 854 | `` |
| 5 | `CouncilHall_DeepSeek_SideWindowJamb_-1_2_-1` | 838 | 858 | `` |
| 6 | `CouncilHall_DeepSeek_SideWindowJamb_-1_2_1` | 842 | 862 | `` |
| 7 | `CouncilHall_DeepSeek_SideWindowJamb_1_0_-1` | 846 | 866 | `` |
| 8 | `CouncilHall_DeepSeek_SideWindowJamb_1_0_1` | 850 | 870 | `` |
| 9 | `CouncilHall_DeepSeek_SideWindowJamb_1_1_-1` | 854 | 874 | `` |
| 10 | `CouncilHall_DeepSeek_SideWindowJamb_1_1_1` | 858 | 878 | `` |
| 11 | `CouncilHall_DeepSeek_SideWindowJamb_1_2_-1` | 862 | 882 | `` |
| 12 | `CouncilHall_DeepSeek_SideWindowJamb_1_2_1` | 866 | 886 | `` |
| 13 | `CouncilHall_DeepSeek_Side-1_Window0_FrameH_0` | 870 | 890 | `` |
| 14 | `CouncilHall_DeepSeek_Side-1_Window1_FrameH_0` | 874 | 894 | `` |
| 15 | `CouncilHall_DeepSeek_Side-1_Window2_FrameH_0` | 878 | 898 | `` |
| 16 | `CouncilHall_DeepSeek_Side1_Window0_FrameH_0` | 882 | 902 | `` |
| 17 | `CouncilHall_DeepSeek_Side1_Window1_FrameH_0` | 886 | 906 | `` |
| 18 | `CouncilHall_DeepSeek_Side1_Window2_FrameH_0` | 890 | 910 | `` |
| 19 | `CouncilHall_DeepSeek_FrontWindow0_FrameH_-1` | 894 | 914 | `` |
| 20 | `CouncilHall_DeepSeek_FrontWindow1_FrameH_-1` | 898 | 918 | `` |
| 21 | `CouncilHall_DeepSeek_Side-1_Window0_Mullion_-1` | 902 | 922 | `` |
| 22 | `CouncilHall_DeepSeek_Side-1_Window1_Mullion_-1` | 906 | 926 | `` |
| 23 | `CouncilHall_DeepSeek_Side-1_Window2_Mullion_-1` | 910 | 930 | `` |
| 24 | `CouncilHall_DeepSeek_Side1_Window0_Mullion_-1` | 914 | 934 | `` |
| 25 | `CouncilHall_DeepSeek_Side1_Window1_Mullion_-1` | 918 | 938 | `` |
| 26 | `CouncilHall_DeepSeek_Side1_Window2_Mullion_-1` | 922 | 942 | `` |
| 27 | `CouncilHall_DeepSeek_Side-1_Window0_FrameV_-1` | 926 | 946 | `` |
| 28 | `CouncilHall_DeepSeek_Side-1_Window0_FrameV_1` | 930 | 950 | `` |
| 29 | `CouncilHall_DeepSeek_Side-1_Window1_FrameV_-1` | 934 | 954 | `` |
| 30 | `CouncilHall_DeepSeek_Side-1_Window1_FrameV_1` | 938 | 958 | `` |
| 31 | `CouncilHall_DeepSeek_Side-1_Window2_FrameV_-1` | 942 | 962 | `` |
| 32 | `CouncilHall_DeepSeek_Side-1_Window2_FrameV_1` | 946 | 966 | `` |
| 33 | `CouncilHall_DeepSeek_Side1_Window0_FrameV_-1` | 950 | 970 | `` |
| 34 | `CouncilHall_DeepSeek_Side1_Window0_FrameV_1` | 954 | 974 | `` |
| 35 | `CouncilHall_DeepSeek_Side1_Window1_FrameV_-1` | 958 | 978 | `` |
| 36 | `CouncilHall_DeepSeek_Side1_Window1_FrameV_1` | 962 | 982 | `` |
| 37 | `CouncilHall_DeepSeek_Side1_Window2_FrameV_-1` | 966 | 986 | `` |
| 38 | `CouncilHall_DeepSeek_Side1_Window2_FrameV_1` | 970 | 990 | `` |
| 39 | `CouncilHall_DeepSeek_FrontWindow0_FrameV_-1` | 974 | 994 | `` |
| 40 | `CouncilHall_DeepSeek_FrontWindow0_FrameV_1` | 978 | 998 | `` |
| 41 | `CouncilHall_DeepSeek_FrontWindow0_Mullion` | 982 | 1002 | `` |
| 42 | `CouncilHall_DeepSeek_FrontWindow1_FrameV_-1` | 986 | 1006 | `` |
| 43 | `CouncilHall_DeepSeek_FrontWindow1_FrameV_1` | 990 | 1010 | `` |
| 44 | `CouncilHall_DeepSeek_FrontWindow1_Mullion` | 994 | 1014 | `` |
| 45 | `CouncilHall_DeepSeek_Side-1_Window0_Mullion_1` | 998 | 1018 | `` |
| 46 | `CouncilHall_DeepSeek_Side-1_Window1_Mullion_1` | 1002 | 1022 | `` |
| 47 | `CouncilHall_DeepSeek_Side-1_Window2_Mullion_1` | 1006 | 1026 | `` |
| 48 | `CouncilHall_DeepSeek_Side1_Window0_Mullion_1` | 1010 | 1030 | `` |
| 49 | `CouncilHall_DeepSeek_Side1_Window1_Mullion_1` | 1014 | 1034 | `` |
| 50 | `CouncilHall_DeepSeek_Side1_Window2_Mullion_1` | 1018 | 1038 | `` |
| 51 | `CouncilHall_DeepSeek_FrontWindow0_FrameH_1` | 1022 | 1042 | `` |
| 52 | `CouncilHall_DeepSeek_FrontWindow1_FrameH_1` | 1026 | 1046 | `` |
| 53 | `CouncilHall_DeepSeek_Side-1_Window0_FrameH_1` | 1030 | 1050 | `` |
| 54 | `CouncilHall_DeepSeek_Side-1_Window1_FrameH_1` | 1034 | 1054 | `` |
| 55 | `CouncilHall_DeepSeek_Side-1_Window2_FrameH_1` | 1038 | 1058 | `` |
| 56 | `CouncilHall_DeepSeek_Side1_Window0_FrameH_1` | 1042 | 1062 | `` |
| 57 | `CouncilHall_DeepSeek_Side1_Window1_FrameH_1` | 1046 | 1065 | `` |
| 58 | `CouncilHall_DeepSeek_Side1_Window2_FrameH_1` | 1050 | 1065 | `` |

**细分工序：**

1. 对照已完成墙洞定位两侧竖框，先下端再上端。
2. 连接上横框与中间分格，保持原模型净开口。
3. 本阶段只安装清单中的框件；玻璃、门扇和百叶按后续清单进入。
4. 本阶段共 58 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 框件围绕既有洞口闭合，未缩小原有开口。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 20．侧玻璃

**帧 1066–1109**（1.8 秒；8 件）。

**前置条件：** 第 19 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装侧玻璃；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Side-1_Window0_Glass` | 1066 | 1086 | `` |
| 2 | `CouncilHall_DeepSeek_Side-1_Window1_Glass` | 1070 | 1090 | `` |
| 3 | `CouncilHall_DeepSeek_Side-1_Window2_Glass` | 1074 | 1094 | `` |
| 4 | `CouncilHall_DeepSeek_Side1_Window0_Glass` | 1078 | 1098 | `` |
| 5 | `CouncilHall_DeepSeek_Side1_Window1_Glass` | 1082 | 1102 | `` |
| 6 | `CouncilHall_DeepSeek_Side1_Window2_Glass` | 1086 | 1106 | `` |
| 7 | `CouncilHall_DeepSeek_FrontWindow0_Glass` | 1090 | 1109 | `` |
| 8 | `CouncilHall_DeepSeek_FrontWindow1_Glass` | 1094 | 1109 | `` |

**细分工序：**

1. 确认四周框、承轨及内部设备已经完成。
2. 面板从框外侧缓慢靠近，先贴近下边缘再归位到最终平面。
3. 装框边附属件；透明或发电工作面保持完整，不新增中心螺栓。
4. 本阶段共 8 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 边缘落在框内，透明面不误变为墙板，工作面无遮挡。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 21．百叶通风

**帧 1110–1377**（11.2 秒；64 件）。

**前置条件：** 第 20 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装百叶通风；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Side-1_Window0_Louver_-1_0` | 1110 | 1130 | `` |
| 2 | `CouncilHall_DeepSeek_Side-1_Window0_Louver_1_0` | 1114 | 1134 | `` |
| 3 | `CouncilHall_DeepSeek_Side-1_Window1_Louver_-1_0` | 1118 | 1138 | `` |
| 4 | `CouncilHall_DeepSeek_Side-1_Window1_Louver_1_0` | 1122 | 1142 | `` |
| 5 | `CouncilHall_DeepSeek_Side-1_Window2_Louver_-1_0` | 1126 | 1146 | `` |
| 6 | `CouncilHall_DeepSeek_Side-1_Window2_Louver_1_0` | 1130 | 1150 | `` |
| 7 | `CouncilHall_DeepSeek_Side1_Window0_Louver_-1_0` | 1134 | 1154 | `` |
| 8 | `CouncilHall_DeepSeek_Side1_Window0_Louver_1_0` | 1138 | 1158 | `` |
| 9 | `CouncilHall_DeepSeek_Side1_Window1_Louver_-1_0` | 1142 | 1162 | `` |
| 10 | `CouncilHall_DeepSeek_Side1_Window1_Louver_1_0` | 1146 | 1166 | `` |
| 11 | `CouncilHall_DeepSeek_Side1_Window2_Louver_-1_0` | 1150 | 1170 | `` |
| 12 | `CouncilHall_DeepSeek_Side1_Window2_Louver_1_0` | 1154 | 1174 | `` |
| 13 | `CouncilHall_DeepSeek_Side-1_Window0_Louver_-1_1` | 1158 | 1178 | `` |
| 14 | `CouncilHall_DeepSeek_Side-1_Window0_Louver_1_1` | 1162 | 1182 | `` |
| 15 | `CouncilHall_DeepSeek_Side-1_Window1_Louver_-1_1` | 1166 | 1186 | `` |
| 16 | `CouncilHall_DeepSeek_Side-1_Window1_Louver_1_1` | 1170 | 1190 | `` |
| 17 | `CouncilHall_DeepSeek_Side-1_Window2_Louver_-1_1` | 1174 | 1194 | `` |
| 18 | `CouncilHall_DeepSeek_Side-1_Window2_Louver_1_1` | 1178 | 1198 | `` |
| 19 | `CouncilHall_DeepSeek_Side1_Window0_Louver_-1_1` | 1182 | 1202 | `` |
| 20 | `CouncilHall_DeepSeek_Side1_Window0_Louver_1_1` | 1186 | 1206 | `` |
| 21 | `CouncilHall_DeepSeek_Side1_Window1_Louver_-1_1` | 1190 | 1210 | `` |
| 22 | `CouncilHall_DeepSeek_Side1_Window1_Louver_1_1` | 1194 | 1214 | `` |
| 23 | `CouncilHall_DeepSeek_Side1_Window2_Louver_-1_1` | 1198 | 1218 | `` |
| 24 | `CouncilHall_DeepSeek_Side1_Window2_Louver_1_1` | 1202 | 1222 | `` |
| 25 | `CouncilHall_DeepSeek_Side-1_Window0_Shutter_-1` | 1206 | 1226 | `` |
| 26 | `CouncilHall_DeepSeek_Side-1_Window0_Shutter_1` | 1210 | 1230 | `` |
| 27 | `CouncilHall_DeepSeek_Side-1_Window1_Shutter_-1` | 1214 | 1234 | `` |
| 28 | `CouncilHall_DeepSeek_Side-1_Window1_Shutter_1` | 1218 | 1238 | `` |
| 29 | `CouncilHall_DeepSeek_Side-1_Window2_Shutter_-1` | 1222 | 1242 | `` |
| 30 | `CouncilHall_DeepSeek_Side-1_Window2_Shutter_1` | 1226 | 1246 | `` |
| 31 | `CouncilHall_DeepSeek_Side1_Window0_Shutter_-1` | 1230 | 1250 | `` |
| 32 | `CouncilHall_DeepSeek_Side1_Window0_Shutter_1` | 1234 | 1254 | `` |
| 33 | `CouncilHall_DeepSeek_Side1_Window1_Shutter_-1` | 1238 | 1258 | `` |
| 34 | `CouncilHall_DeepSeek_Side1_Window1_Shutter_1` | 1242 | 1262 | `` |
| 35 | `CouncilHall_DeepSeek_Side1_Window2_Shutter_-1` | 1246 | 1266 | `` |
| 36 | `CouncilHall_DeepSeek_Side1_Window2_Shutter_1` | 1250 | 1270 | `` |
| 37 | `CouncilHall_DeepSeek_Side-1_Window0_Louver_-1_2` | 1254 | 1274 | `` |
| 38 | `CouncilHall_DeepSeek_Side-1_Window0_Louver_1_2` | 1258 | 1278 | `` |
| 39 | `CouncilHall_DeepSeek_Side-1_Window1_Louver_-1_2` | 1262 | 1282 | `` |
| 40 | `CouncilHall_DeepSeek_Side-1_Window1_Louver_1_2` | 1266 | 1286 | `` |
| 41 | `CouncilHall_DeepSeek_Side-1_Window2_Louver_-1_2` | 1270 | 1290 | `` |
| 42 | `CouncilHall_DeepSeek_Side-1_Window2_Louver_1_2` | 1274 | 1294 | `` |
| 43 | `CouncilHall_DeepSeek_Side1_Window0_Louver_-1_2` | 1278 | 1298 | `` |
| 44 | `CouncilHall_DeepSeek_Side1_Window0_Louver_1_2` | 1282 | 1302 | `` |
| 45 | `CouncilHall_DeepSeek_Side1_Window1_Louver_-1_2` | 1286 | 1306 | `` |
| 46 | `CouncilHall_DeepSeek_Side1_Window1_Louver_1_2` | 1290 | 1310 | `` |
| 47 | `CouncilHall_DeepSeek_Side1_Window2_Louver_-1_2` | 1294 | 1314 | `` |
| 48 | `CouncilHall_DeepSeek_Side1_Window2_Louver_1_2` | 1298 | 1318 | `` |
| 49 | `CouncilHall_DeepSeek_Back_Vent_Slat_0` | 1302 | 1322 | `` |
| 50 | `CouncilHall_DeepSeek_Side-1_Window0_Louver_-1_3` | 1306 | 1326 | `` |
| 51 | `CouncilHall_DeepSeek_Side-1_Window0_Louver_1_3` | 1310 | 1330 | `` |
| 52 | `CouncilHall_DeepSeek_Side-1_Window1_Louver_-1_3` | 1314 | 1334 | `` |
| 53 | `CouncilHall_DeepSeek_Side-1_Window1_Louver_1_3` | 1318 | 1338 | `` |
| 54 | `CouncilHall_DeepSeek_Side-1_Window2_Louver_-1_3` | 1322 | 1342 | `` |
| 55 | `CouncilHall_DeepSeek_Side-1_Window2_Louver_1_3` | 1326 | 1346 | `` |
| 56 | `CouncilHall_DeepSeek_Side1_Window0_Louver_-1_3` | 1330 | 1350 | `` |
| 57 | `CouncilHall_DeepSeek_Side1_Window0_Louver_1_3` | 1334 | 1354 | `` |
| 58 | `CouncilHall_DeepSeek_Side1_Window1_Louver_-1_3` | 1338 | 1358 | `` |
| 59 | `CouncilHall_DeepSeek_Side1_Window1_Louver_1_3` | 1342 | 1362 | `` |
| 60 | `CouncilHall_DeepSeek_Side1_Window2_Louver_-1_3` | 1346 | 1366 | `` |
| 61 | `CouncilHall_DeepSeek_Side1_Window2_Louver_1_3` | 1350 | 1370 | `` |
| 62 | `CouncilHall_DeepSeek_Back_Vent_Slat_1` | 1354 | 1374 | `` |
| 63 | `CouncilHall_DeepSeek_Back_Vent_Slat_2` | 1358 | 1377 | `` |
| 64 | `CouncilHall_DeepSeek_Back_Vent_Slat_3` | 1362 | 1377 | `` |

**细分工序：**

1. 先核对框、支架或铰接端已经完成。
2. 主体由铰接侧或下支承端进入，归位后再装把手、铰链和锁件。
3. 按源模型保留开合状态，检查相邻墙面与设备间的间隙。
4. 本阶段共 64 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与支承相连，开口和检修空间不被附属件遮挡。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 22．门廊柱

**帧 1378–1429**（2.2 秒；12 件）。

**前置条件：** 第 21 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装门廊柱；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Porch_Post_-1` | 1378 | 1398 | `` |
| 2 | `CouncilHall_DeepSeek_Porch_Post_1` | 1382 | 1401 | `` |
| 3 | `DetailPass__031_Structural_joint_plate` | 1402 | 1412 | `CouncilHall_DeepSeek_Porch_Post_-1` |
| 4 | `DetailPass__032_Hex_fastener` | 1404 | 1414 | `CouncilHall_DeepSeek_Porch_Post_-1` |
| 5 | `DetailPass__033_Hex_fastener` | 1406 | 1416 | `CouncilHall_DeepSeek_Porch_Post_-1` |
| 6 | `DetailPass__034_Hex_fastener` | 1408 | 1418 | `CouncilHall_DeepSeek_Porch_Post_-1` |
| 7 | `DetailPass__035_Hex_fastener` | 1410 | 1420 | `CouncilHall_DeepSeek_Porch_Post_-1` |
| 8 | `DetailPass__036_Structural_joint_plate` | 1412 | 1422 | `CouncilHall_DeepSeek_Porch_Post_1` |
| 9 | `DetailPass__037_Hex_fastener` | 1414 | 1424 | `CouncilHall_DeepSeek_Porch_Post_1` |
| 10 | `DetailPass__038_Hex_fastener` | 1416 | 1426 | `CouncilHall_DeepSeek_Porch_Post_1` |
| 11 | `DetailPass__039_Hex_fastener` | 1418 | 1428 | `CouncilHall_DeepSeek_Porch_Post_1` |
| 12 | `DetailPass__040_Hex_fastener` | 1420 | 1429 | `CouncilHall_DeepSeek_Porch_Post_1` |

**细分工序：**

1. 核对本阶段清单中每个主体的安装面、承架或连接端。
2. 先安装主体和支承连接，再依次补齐其可拆附属部件。
3. 依照逐件帧表错开进入，主体完全落位后才安装所依附的标牌、仪表或紧固细节。
4. 本阶段共 12 件，其中 10 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与已建结构连接，安装位置、朝向和材质与源模型一致。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 23．门廊梁撑

**帧 1430–1453**（1.0 秒；3 件）。

**前置条件：** 第 22 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装门廊梁撑；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Porch_KneeBrace_-1` | 1430 | 1450 | `` |
| 2 | `CouncilHall_DeepSeek_Porch_KneeBrace_1` | 1434 | 1453 | `` |
| 3 | `CouncilHall_DeepSeek_Porch_FrontHeader` | 1438 | 1453 | `` |

**细分工序：**

1. 先确认两端柱梁已经完成，再按对角线定位斜撑。
2. 先固定一端，再将另一端旋入或平移到连接点；相邻侧交替安装。
3. 交叉处保持原模型层次，最后锁紧端部连接件。
4. 本阶段共 3 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 斜撑两端都与既有框架连接，交叉件无新增穿插。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 24．门廊棚

**帧 1454–1509**（2.3 秒；11 件）。

**前置条件：** 第 23 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装门廊棚；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Porch_Canopy` | 1454 | 1474 | `` |
| 2 | `CouncilHall_DeepSeek_Porch_Canopy_Rib_0` | 1458 | 1478 | `` |
| 3 | `CouncilHall_DeepSeek_Porch_Canopy_Rib_1` | 1462 | 1482 | `` |
| 4 | `CouncilHall_DeepSeek_Porch_Canopy_Rib_2` | 1466 | 1486 | `` |
| 5 | `CouncilHall_DeepSeek_Porch_Canopy_Rib_3` | 1470 | 1490 | `` |
| 6 | `CouncilHall_DeepSeek_Porch_Canopy_Rib_4` | 1474 | 1494 | `` |
| 7 | `CouncilHall_DeepSeek_Porch_Canopy_Rib_5` | 1478 | 1498 | `` |
| 8 | `CouncilHall_DeepSeek_Porch_Canopy_Rib_6` | 1482 | 1502 | `` |
| 9 | `CouncilHall_DeepSeek_Porch_Canopy_Rib_7` | 1486 | 1506 | `` |
| 10 | `CouncilHall_DeepSeek_Porch_Canopy_Rib_8` | 1490 | 1509 | `` |
| 11 | `CouncilHall_DeepSeek_Porch_Canopy_Rib_9` | 1494 | 1509 | `` |

**细分工序：**

1. 核对本阶段清单中每个主体的安装面、承架或连接端。
2. 先安装主体和支承连接，再依次补齐其可拆附属部件。
3. 依照逐件帧表错开进入，主体完全落位后才安装所依附的标牌、仪表或紧固细节。
4. 本阶段共 11 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与已建结构连接，安装位置、朝向和材质与源模型一致。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 25．四坡屋顶

**帧 1510–1533**（1.0 秒；1 件）。

**前置条件：** 第 24 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装四坡屋顶；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Roof_HipShell` | 1510 | 1530 | `` |

**细分工序：**

1. 先确认屋顶支柱、梁椽或雨棚斜撑已经完成。
2. 从低侧或一侧逐片覆盖，给内部安装保留到最后一片封闭前。
3. 盖好后再装压条、补片与沿边紧固件，保持原有排水坡度。
4. 本阶段共 1 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 顶面覆盖对应支架，屋脊、檐口与排水方向保持源模型形状。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 26．压棱接缝

**帧 1534–1689**（6.5 秒；36 件）。

**前置条件：** 第 25 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装压棱接缝；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Roof_HipSeam_-1_0` | 1534 | 1554 | `` |
| 2 | `CouncilHall_DeepSeek_Roof_HipSeam_-1_1` | 1538 | 1558 | `` |
| 3 | `CouncilHall_DeepSeek_Roof_HipSeam_-1_2` | 1542 | 1562 | `` |
| 4 | `CouncilHall_DeepSeek_Roof_HipSeam_-1_3` | 1546 | 1566 | `` |
| 5 | `CouncilHall_DeepSeek_Roof_HipSeam_-1_4` | 1550 | 1570 | `` |
| 6 | `CouncilHall_DeepSeek_Roof_HipSeam_-1_5` | 1554 | 1574 | `` |
| 7 | `CouncilHall_DeepSeek_Roof_HipSeam_-1_6` | 1558 | 1578 | `` |
| 8 | `CouncilHall_DeepSeek_Roof_HipSeam_-1_7` | 1562 | 1582 | `` |
| 9 | `CouncilHall_DeepSeek_Roof_HipSeam_-1_8` | 1566 | 1586 | `` |
| 10 | `CouncilHall_DeepSeek_Roof_HipSeam_1_0` | 1570 | 1590 | `` |
| 11 | `CouncilHall_DeepSeek_Roof_HipSeam_1_1` | 1574 | 1594 | `` |
| 12 | `CouncilHall_DeepSeek_Roof_HipSeam_1_2` | 1578 | 1598 | `` |
| 13 | `CouncilHall_DeepSeek_Roof_HipSeam_1_3` | 1582 | 1602 | `` |
| 14 | `CouncilHall_DeepSeek_Roof_HipSeam_1_4` | 1586 | 1606 | `` |
| 15 | `CouncilHall_DeepSeek_Roof_HipSeam_1_5` | 1590 | 1610 | `` |
| 16 | `CouncilHall_DeepSeek_Roof_HipSeam_1_6` | 1594 | 1614 | `` |
| 17 | `CouncilHall_DeepSeek_Roof_HipSeam_1_7` | 1598 | 1618 | `` |
| 18 | `CouncilHall_DeepSeek_Roof_HipSeam_1_8` | 1602 | 1622 | `` |
| 19 | `CouncilHall_DeepSeek_Roof_Corrugation_-1_0` | 1606 | 1626 | `` |
| 20 | `CouncilHall_DeepSeek_Roof_Corrugation_-1_1` | 1610 | 1630 | `` |
| 21 | `CouncilHall_DeepSeek_Roof_Corrugation_-1_2` | 1614 | 1634 | `` |
| 22 | `CouncilHall_DeepSeek_Roof_Corrugation_-1_3` | 1618 | 1638 | `` |
| 23 | `CouncilHall_DeepSeek_Roof_Corrugation_-1_4` | 1622 | 1642 | `` |
| 24 | `CouncilHall_DeepSeek_Roof_Corrugation_-1_5` | 1626 | 1646 | `` |
| 25 | `CouncilHall_DeepSeek_Roof_Corrugation_-1_6` | 1630 | 1650 | `` |
| 26 | `CouncilHall_DeepSeek_Roof_Corrugation_-1_7` | 1634 | 1654 | `` |
| 27 | `CouncilHall_DeepSeek_Roof_Corrugation_-1_8` | 1638 | 1658 | `` |
| 28 | `CouncilHall_DeepSeek_Roof_Corrugation_1_0` | 1642 | 1662 | `` |
| 29 | `CouncilHall_DeepSeek_Roof_Corrugation_1_1` | 1646 | 1666 | `` |
| 30 | `CouncilHall_DeepSeek_Roof_Corrugation_1_2` | 1650 | 1670 | `` |
| 31 | `CouncilHall_DeepSeek_Roof_Corrugation_1_3` | 1654 | 1674 | `` |
| 32 | `CouncilHall_DeepSeek_Roof_Corrugation_1_4` | 1658 | 1678 | `` |
| 33 | `CouncilHall_DeepSeek_Roof_Corrugation_1_5` | 1662 | 1682 | `` |
| 34 | `CouncilHall_DeepSeek_Roof_Corrugation_1_6` | 1666 | 1686 | `` |
| 35 | `CouncilHall_DeepSeek_Roof_Corrugation_1_7` | 1670 | 1689 | `` |
| 36 | `CouncilHall_DeepSeek_Roof_Corrugation_1_8` | 1674 | 1689 | `` |

**细分工序：**

1. 核对本阶段清单中每个主体的安装面、承架或连接端。
2. 先安装主体和支承连接，再依次补齐其可拆附属部件。
3. 依照逐件帧表错开进入，主体完全落位后才安装所依附的标牌、仪表或紧固细节。
4. 本阶段共 36 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与已建结构连接，安装位置、朝向和材质与源模型一致。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 27．屋脊补片

**帧 1690–1737**（2.0 秒；11 件）。

**前置条件：** 第 26 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装屋脊补片；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Roof_RepairPatch_Front` | 1690 | 1710 | `` |
| 2 | `CouncilHall_DeepSeek_Roof_RepairPatch_Back` | 1694 | 1713 | `` |
| 3 | `CouncilHall_DeepSeek_Roof_RidgeCap` | 1698 | 1713 | `` |
| 4 | `DetailPass__023_Weathered_repair_plate` | 1714 | 1724 | `CouncilHall_DeepSeek_Roof_RepairPatch_Front` |
| 5 | `DetailPass__024_Hex_fastener` | 1716 | 1726 | `CouncilHall_DeepSeek_Roof_RepairPatch_Front` |
| 6 | `DetailPass__025_Hex_fastener` | 1718 | 1728 | `CouncilHall_DeepSeek_Roof_RepairPatch_Front` |
| 7 | `DetailPass__026_Hex_fastener` | 1720 | 1730 | `CouncilHall_DeepSeek_Roof_RepairPatch_Front` |
| 8 | `DetailPass__027_Hex_fastener` | 1722 | 1732 | `CouncilHall_DeepSeek_Roof_RepairPatch_Front` |
| 9 | `DetailPass__028_Repair_surface_scuff` | 1724 | 1734 | `CouncilHall_DeepSeek_Roof_RepairPatch_Front` |
| 10 | `DetailPass__029_Repair_surface_scuff` | 1726 | 1736 | `CouncilHall_DeepSeek_Roof_RepairPatch_Front` |
| 11 | `DetailPass__030_Repair_surface_scuff` | 1728 | 1737 | `CouncilHall_DeepSeek_Roof_RepairPatch_Front` |

**细分工序：**

1. 核对本阶段清单中每个主体的安装面、承架或连接端。
2. 先安装主体和支承连接，再依次补齐其可拆附属部件。
3. 依照逐件帧表错开进入，主体完全落位后才安装所依附的标牌、仪表或紧固细节。
4. 本阶段共 11 件，其中 8 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与已建结构连接，安装位置、朝向和材质与源模型一致。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 28．排水

**帧 1738–1813**（3.2 秒；16 件）。

**前置条件：** 第 27 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装排水；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Downpipe_Shoe_-1_-1` | 1738 | 1758 | `` |
| 2 | `CouncilHall_DeepSeek_Downpipe_Shoe_-1_1` | 1742 | 1762 | `` |
| 3 | `CouncilHall_DeepSeek_Downpipe_Shoe_1_-1` | 1746 | 1766 | `` |
| 4 | `CouncilHall_DeepSeek_Downpipe_Shoe_1_1` | 1750 | 1770 | `` |
| 5 | `CouncilHall_DeepSeek_Downpipe_Vertical_-1_-1` | 1754 | 1774 | `` |
| 6 | `CouncilHall_DeepSeek_Downpipe_Vertical_-1_1` | 1758 | 1778 | `` |
| 7 | `CouncilHall_DeepSeek_Downpipe_Vertical_1_-1` | 1762 | 1782 | `` |
| 8 | `CouncilHall_DeepSeek_Downpipe_Vertical_1_1` | 1766 | 1786 | `` |
| 9 | `CouncilHall_DeepSeek_Roof_Gutter_X_-4.82` | 1770 | 1790 | `` |
| 10 | `CouncilHall_DeepSeek_Roof_Gutter_X_4.82` | 1774 | 1794 | `` |
| 11 | `CouncilHall_DeepSeek_Roof_Gutter_Y_-4.7` | 1778 | 1798 | `` |
| 12 | `CouncilHall_DeepSeek_Roof_Gutter_Y_4.7` | 1782 | 1802 | `` |
| 13 | `CouncilHall_DeepSeek_Downpipe_Elbow_-1_-1` | 1786 | 1806 | `` |
| 14 | `CouncilHall_DeepSeek_Downpipe_Elbow_-1_1` | 1790 | 1810 | `` |
| 15 | `CouncilHall_DeepSeek_Downpipe_Elbow_1_-1` | 1794 | 1813 | `` |
| 16 | `CouncilHall_DeepSeek_Downpipe_Elbow_1_1` | 1798 | 1813 | `` |

**细分工序：**

1. 确认设备接口、管夹或安装面已经在场。
2. 按上游到下游连接各管段；弯头对正后再闭合末端接头。
3. 主体连接完成后装阀轮、刻度、接线端与依附细节，保留操作方向。
4. 本阶段共 16 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 每段管线有对应接口，阀门与设备检修面可见。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 29．入口踏步

**帧 1814–1917**（4.3 秒；23 件）。

**前置条件：** 第 28 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装入口踏步；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Ramp_StoneFoot_0` | 1814 | 1834 | `` |
| 2 | `CouncilHall_DeepSeek_Ramp_StoneFoot_1` | 1818 | 1838 | `` |
| 3 | `CouncilHall_DeepSeek_Ramp_StoneFoot_2` | 1822 | 1842 | `` |
| 4 | `CouncilHall_DeepSeek_Ramp_RailPost_-1_0` | 1826 | 1846 | `` |
| 5 | `CouncilHall_DeepSeek_Ramp_RailPost_1_0` | 1830 | 1850 | `` |
| 6 | `CouncilHall_DeepSeek_Ramp_RailPost_-1_1` | 1834 | 1854 | `` |
| 7 | `CouncilHall_DeepSeek_Ramp_RailPost_1_1` | 1838 | 1858 | `` |
| 8 | `CouncilHall_DeepSeek_Ramp_RailPost_-1_2` | 1842 | 1862 | `` |
| 9 | `CouncilHall_DeepSeek_Ramp_RailPost_1_2` | 1846 | 1866 | `` |
| 10 | `CouncilHall_DeepSeek_Ramp_RailPost_-1_3` | 1850 | 1870 | `` |
| 11 | `CouncilHall_DeepSeek_Ramp_RailPost_1_3` | 1854 | 1874 | `` |
| 12 | `CouncilHall_DeepSeek_Entry_Step_1` | 1858 | 1878 | `` |
| 13 | `CouncilHall_DeepSeek_Ramp_UndersideCrossTie_0.25` | 1862 | 1882 | `` |
| 14 | `CouncilHall_DeepSeek_Entry_Step_Nosing_1` | 1866 | 1886 | `` |
| 15 | `CouncilHall_DeepSeek_Entry_Step_2` | 1870 | 1890 | `` |
| 16 | `CouncilHall_DeepSeek_Ramp_UndersideCrossTie_0.5` | 1874 | 1894 | `` |
| 17 | `CouncilHall_DeepSeek_Entry_Step_3` | 1878 | 1898 | `` |
| 18 | `CouncilHall_DeepSeek_Ramp_Deck` | 1882 | 1902 | `` |
| 19 | `CouncilHall_DeepSeek_Entry_Step_Nosing_2` | 1886 | 1906 | `` |
| 20 | `CouncilHall_DeepSeek_Ramp_UndersideCrossTie_0.75` | 1890 | 1910 | `` |
| 21 | `CouncilHall_DeepSeek_Entry_Step_Nosing_3` | 1894 | 1914 | `` |
| 22 | `CouncilHall_DeepSeek_Ramp_Handrail_-1` | 1898 | 1917 | `` |
| 23 | `CouncilHall_DeepSeek_Ramp_Handrail_1` | 1902 | 1917 | `` |

**细分工序：**

1. 先安装两端支座与侧梁，跨接到已有平台或入口。
2. 踏板从低处向高处逐级安装；栏杆先立柱后横杆。
3. 最后补边缘紧固件，保留入口净宽和原有踏步间距。
4. 本阶段共 23 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 通行路径连续，栏杆与踏板接点明确，入口未封堵。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 30．栏杆

**帧 1918–1953**（1.5 秒；6 件）。

**前置条件：** 第 29 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装栏杆；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Porch_Railing_Post_-1` | 1918 | 1938 | `` |
| 2 | `CouncilHall_DeepSeek_Porch_Railing_Post_1` | 1922 | 1942 | `` |
| 3 | `CouncilHall_DeepSeek_Porch_SideLowerRail_-1` | 1926 | 1946 | `` |
| 4 | `CouncilHall_DeepSeek_Porch_SideLowerRail_1` | 1930 | 1950 | `` |
| 5 | `CouncilHall_DeepSeek_Porch_SideHandrail_-1` | 1934 | 1953 | `` |
| 6 | `CouncilHall_DeepSeek_Porch_SideHandrail_1` | 1938 | 1953 | `` |

**细分工序：**

1. 先安装两端支座与侧梁，跨接到已有平台或入口。
2. 踏板从低处向高处逐级安装；栏杆先立柱后横杆。
3. 最后补边缘紧固件，保留入口净宽和原有踏步间距。
4. 本阶段共 6 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 通行路径连续，栏杆与踏板接点明确，入口未封堵。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 31．公共公告板

**帧 1954–2013**（2.5 秒；16 件）。

**前置条件：** 第 30 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装公共公告板；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_Community_Noticeboard_Back` | 1954 | 1974 | `` |
| 2 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` | 1958 | 1977 | `` |
| 3 | `DetailPass__001_Notice_backboard` | 1978 | 1988 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 4 | `DetailPass__002_Pinned_paper` | 1980 | 1990 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 5 | `DetailPass__003_Notice_marks` | 1982 | 1992 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 6 | `DetailPass__004_Notice_marks` | 1984 | 1994 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 7 | `DetailPass__005_Notice_marks` | 1986 | 1996 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 8 | `DetailPass__006_Notice_pin` | 1988 | 1998 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 9 | `DetailPass__007_Pinned_paper` | 1990 | 2000 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 10 | `DetailPass__008_Notice_marks` | 1992 | 2002 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 11 | `DetailPass__009_Notice_marks` | 1994 | 2004 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 12 | `DetailPass__010_Notice_marks` | 1996 | 2006 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 13 | `DetailPass__011_Notice_pin` | 1998 | 2008 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 14 | `DetailPass__012_Pinned_paper` | 2000 | 2010 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 15 | `DetailPass__013_Notice_marks` | 2002 | 2012 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |
| 16 | `DetailPass__014_Notice_pin` | 2004 | 2013 | `CouncilHall_DeepSeek_Community_Noticeboard_Blank` |

**细分工序：**

1. 核对本阶段清单中每个主体的安装面、承架或连接端。
2. 先安装主体和支承连接，再依次补齐其可拆附属部件。
3. 依照逐件帧表错开进入，主体完全落位后才安装所依附的标牌、仪表或紧固细节。
4. 本阶段共 16 件，其中 14 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与已建结构连接，安装位置、朝向和材质与源模型一致。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 32．入口灯

**帧 2014–2041**（1.2 秒；4 件）。

**前置条件：** 第 31 阶段构件已就位；确认当前构件的支承面和连接端。

**操作：** 按支承端到自由端的顺序安装入口灯；先定位主体，再锁紧连接件，保留现有开口与检修空间。

**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。

| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |
| --- | --- | ---: | ---: | --- |
| 1 | `CouncilHall_DeepSeek_EntryLamp_Housing` | 2014 | 2034 | `` |
| 2 | `CouncilHall_DeepSeek_EntryLamp_Housing_R` | 2018 | 2038 | `` |
| 3 | `CouncilHall_DeepSeek_EntryLamp_Glass` | 2022 | 2041 | `` |
| 4 | `CouncilHall_DeepSeek_EntryLamp_Glass_R` | 2026 | 2041 | `` |

**细分工序：**

1. 核对本阶段清单中每个主体的安装面、承架或连接端。
2. 先安装主体和支承连接，再依次补齐其可拆附属部件。
3. 依照逐件帧表错开进入，主体完全落位后才安装所依附的标牌、仪表或紧固细节。
4. 本阶段共 4 件，其中 0 件为依附细节；各件严格使用上表的入场帧与落位帧。

**阶段完成要求：** 主体与已建结构连接，安装位置、朝向和材质与源模型一致。 本阶段清单全部就位；不得提前显露下一阶段构件。

## 完工状态

全部构件到达源模型的位置与比例；源模型未被覆盖。动画是美术施工表现，Unity 接入代码与资源已编写，尚未运行 Unity 验证。完整逐帧 PNG 可通过 Blender 渲染动画导出；附带预览只取关键阶段。
