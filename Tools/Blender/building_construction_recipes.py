"""Detailed construction recipes bound to the current authored meshes."""
FPS=24
RECIPES={}
NAMES={
'WoodShelter_DeepSeek':'木棚','ResearchStation_DeepSeek':'研究站','MedicalTent_DeepSeek':'医疗帐篷','LocalCommunicationsCenter_DeepSeek':'初始通讯中心','DirtRoadTiles_DeepSeek':'基础土路套件','DesalinationPlant_DeepSeek':'海水淡化装置','WaterStorageTank':'储水设施','DriftwoodCollectionBoom_DeepSeek':'漂木收集浮栅','FishingDock_DeepSeek':'渔船码头','StorageDepot_DeepSeek':'仓库','RescueDock_DeepSeek':'救援码头','ResidentHut_DeepSeek':'居民小屋','SolarPowerStation_DeepSeek':'太阳能发电站','MedicalStation_DeepSeek':'医疗站','Greenhouse_DeepSeek':'温室','PublicKitchen_DeepSeek':'公共厨房','SalvageWorkshop_DeepSeek':'废料拆解工坊','Forge_DeepSeek':'锻造炉','RescueRadioCenter_DeepSeek':'长距通讯站','WeatherTideBuoy_DeepSeek':'气象潮位浮标','Shipyard_DeepSeek':'船坞','RescueOutpost_DeepSeek':'救援前哨','School_DeepSeek':'学校','Archive_DeepSeek':'档案馆','CouncilHall_DeepSeek':'议事厅'}

def add(asset,text):
    phases=[]
    for row in text.strip().splitlines():
        title,pattern,mode,action=[v.strip() for v in row.split(' :: ')]
        phases.append(dict(title=title,pattern=pattern,mode=mode,action=action))
    RECIPES[asset]=phases

add('WoodShelter_DeepSeek','''
四角支墩定位 :: Foundation_Footing :: drop :: 按四角顺序落下支墩并调平顶面。
两侧承重梁 :: Foundation_Beam :: slide :: 将两根主梁落到同侧支墩上。
横向搁栅 :: Foundation_Joist :: slide :: 从前到后插入横梁并闭合底框。
木地板铺设 :: Floor_Plank :: slide :: 由后向前逐块铺板并保留板缝。
高侧立柱 :: Frame_Post_High :: raise :: 先立迎风高侧的两根支柱。
低侧立柱 :: Frame_Post_Low :: raise :: 安装低侧柱并形成棚顶坡度。
顶部框梁 :: Frame_(Beam|Cross) :: slide :: 先长梁再短梁，连接四根立柱。
斜撑与拉结 :: Brace_ :: swing :: 交替固定两侧斜撑和水平拉结。
挡风横档 :: Back_Windbreak_Rail :: slide :: 先固定后侧上下横档。
后侧挡风板 :: Back_Windbreak_ :: slide :: 从底部向上逐片安装挡风板。
物资箱体 :: Crate_Base :: drop :: 将箱体放到有支承的地板位置。
合盖与捆扎 :: Crate_ :: fit :: 合上箱盖，再扣紧交叉绑带和绳卷。
防雨帆布 :: Roof_Canvas :: cloth :: 从高侧向低侧张开帆布并固定缝线。
帆布补片 :: Roof_Patch :: fit :: 将补片压到帆布磨损处并固定边缘。
灯钩与挂绳 :: Lantern_(Mount|String) :: fit :: 先灯钩，再连接灯具挂绳。
营地灯装配 :: Lantern_ :: drop :: 挂好灯体并合上灯帽。
''')
add('ResearchStation_DeepSeek','''
基础台座 :: Foundation_Base :: drop :: 放平基座并确认建筑外轮廓。
四角框柱 :: Wall_CornerPost :: raise :: 先后侧再前侧，逐根竖立角柱。
后侧墙板 :: Wall_Back :: raise :: 固定后墙并建立室内设备的背景支承。
样品台支腿 :: SampleTable_Leg :: raise :: 就位工作台两侧支腿并校平。
样品台与采样瓶 :: SampleTable_Top|SampleBottle :: drop :: 先落台面，再摆样品瓶、瓶盖和托盘。
侧盒安装支臂 :: SideBox_Arm :: fit :: 固定侧壁采样盒的承重支臂。
侧墙与山墙 :: Wall_(Left|Right|Gable) :: raise :: 左右侧墙从下至上围合。
前墙开口 :: Wall_Front :: raise :: 围绕门窗洞口补齐前墙。
入口门装配 :: Door_ :: swing :: 挂门扇，再装把手、标牌与铰链。
窗框和中梃 :: Window_(Frame|Mullion) :: fit :: 先外框再分格，形成玻璃支承。
观察窗玻璃 :: Window_Glass :: fit :: 沿框面法线将玻璃嵌入槽口。
前坡屋面 :: Roof_Panel_Front :: swing :: 从一端吊入前坡屋面。
后坡屋面 :: Roof_Panel_Back :: swing :: 补齐后坡并在屋脊对接。
屋脊与屋面接缝 :: Roof_(Ridge|Seam) :: fit :: 逐条压紧屋面接缝并盖住屋脊。
记录板和图表 :: SideBoard :: fit :: 固定板框、板面与采样记录。
侧壁采样仪 :: SideBox_(Main|Screen)|SideScale :: fit :: 安装采样盒、屏幕与刻度标尺。
气象杆底座 :: Weather_Mast_Foot :: fit :: 将气象底座锁在屋顶。
气象桅杆 :: Weather_Mast$ :: raise :: 抬升主杆并插入底座。
雨量采集器 :: Weather_RainGauge :: fit :: 安装支臂，再放雨量杯。
风向测量件 :: Weather_Vane :: fit :: 连接转轴、指示杆、箭头和尾翼。
运输箱封装 :: TransportBox :: drop :: 摆放样品运输箱并压紧盖板和绑带。
''')
add('MedicalTent_DeepSeek','''
平台基础墩 :: Platform_Footing :: drop :: 依次落下四角支墩。
平台周边梁 :: Platform_Beam :: slide :: 连接左右长梁和前后短梁。
木平台铺设 :: Platform_Plank :: slide :: 逐板铺设平台并保持前缘平齐。
前侧三角架 :: Frame_Leg_F :: raise :: 先竖起入口侧两根斜腿。
后侧三角架 :: Frame_Leg_B :: raise :: 装后侧斜腿，与前架对齐。
屋脊主梁 :: Frame_RidgeBeam :: slide :: 将主梁插入两片三角架顶部。
侧向撑架 :: Frame_(SidePost|Rail|Brace) :: swing :: 先侧杆，再横档及斜撑。
诊疗床脚 :: Bed_Leg :: raise :: 在平台内安装四只床脚。
床架和床垫 :: Bed_(Frame|Mattress) :: drop :: 先锁床架，再放床垫。
医疗补给箱 :: SideCrate :: drop :: 放箱、合盖、捆扎并摆急救用品。
随身医疗包 :: MedicalBag :: drop :: 就位医疗包和提手。
背侧帆布 :: Canvas_Back :: cloth :: 先张设背侧帆布并固定下缘。
左侧屋面帆布 :: Canvas_Roof_L :: cloth :: 从屋脊向左张紧帆布，固定包边缝线。
右侧屋面帆布 :: Canvas_Roof_R :: cloth :: 向右张紧帆布并固定加固带。
隐私内帘 :: Canvas_InnerCurtain :: cloth :: 在床位一侧安装内帘。
入口门帘 :: Canvas_(Flap|FlapTie) :: cloth :: 连接左右门帘并系好开启侧绑带。
医疗标牌 :: Frame_SignSupport|MedicalSign :: fit :: 固定标牌支撑，再安装医疗十字。
''')
add('LocalCommunicationsCenter_DeepSeek','''
石质基础 :: Base_Stone :: drop :: 放平基座并确认入口朝向。
室内地板 :: Floor_Wood :: slide :: 固定地板并保持门口标高。
后侧与两侧墙 :: Wall_(Back|Left|Right) :: raise :: 先背墙，再左右围护墙。
前墙门窗开口 :: Wall_Front :: raise :: 围绕门窗开口补齐前墙。
入口门及五金 :: Door_ :: swing :: 挂门、压修补板、固定门把和铰链。
观察窗框 :: Window_(Frame|Mullion) :: fit :: 安装窗框四边与中梃。
观察玻璃 :: Window_Glass :: fit :: 将玻璃压入框槽。
蓄电箱与箍带 :: Battery_ :: drop :: 就位蓄电箱，再收紧金属带。
线盘墙架 :: Reel_(WallPlate|SupportShelf|Bracket) :: fit :: 固定墙板、托架及托架斜撑。
线盘主轴 :: Reel_Axle :: slide :: 将主轴插入支架。
线盘与电缆 :: Reel_(Flange|Cable) :: fit :: 安装法兰盘并放入缆线卷。
通讯记录板 :: Panel_ :: fit :: 固定记录板和数据纸。
前坡屋面 :: Roof_Panel_Front :: swing :: 吊装前坡屋面。
后坡屋面 :: Roof_Panel_Back :: swing :: 装后坡并对齐屋脊。
屋脊盖条 :: Roof_Ridge :: fit :: 压紧屋脊盖条。
天线安装座 :: Antenna_Base :: fit :: 固定底座及紧固件。
天线桅杆 :: Antenna_Mast :: raise :: 将主杆插入底座。
天线振子 :: Antenna_(Element|Cross|Rod)|Antenna_[0-9] :: slide :: 逐条安装水平振子。
桅杆斜撑 :: Antenna_Brace :: fit :: 左右斜撑依次锁定。
信号灯 :: Beacon_ :: fit :: 装灯座、发光罩和帽盖。
''')
add('DirtRoadTiles_DeepSeek','''
道路基层 :: _Base$ :: earth :: 从中心向四边整平基层，保持一米边界。
主路面铺筑 :: _Road$ :: earth :: 铺出模块对应的道路轮廓并保持接口。
路肩护边石 :: _Stone_ :: drop :: 将较大石块压入路肩。
压实碎石层 :: _Gravel_ :: drop :: 分批补入细碎石并压实。
路肩植被 :: _Grass_ :: grow :: 在边缘放草簇，避开道路连接口。
''')
add('DesalinationPlant_DeepSeek','''
设备基础支脚 :: Foot|Pier|Foundation|Base_Concrete :: drop :: 布置设备支脚并调平顶面。
滑橇纵梁 :: Skid_Long :: slide :: 先就位左右两根长向滑橇。
滑橇横梁 :: Skid_Cross :: slide :: 从前到后连接横梁。
设备底板 :: Skid_Deck :: slide :: 将底板落到横梁并固定四周。
棚架立柱 :: Frame_Post :: raise :: 竖起四角立柱。
棚顶框梁 :: Frame_Top|Canopy_Beam :: slide :: 连接周边梁和中部棚顶梁。
过滤筒安装座 :: PreFilter_Mount :: fit :: 先安装预过滤筒支承。
预过滤筒体 :: PreFilter_(Body|Top|Bottom) :: drop :: 安筒体，再合上上下端盖并装仪表。
水泵底座 :: Pump_Base :: fit :: 固定泵座至底板。
电机与泵头 :: Pump_(Motor|Head) :: slide :: 就位电机和泵头并补散热罩。
膜组支架 :: Membrane_(Mount|Support)|MembraneRack :: fit :: 将膜组支架固定在框架内。
膜处理单元 :: Membrane_ :: slide :: 逐筒送入膜组并固定端部。
海水进水管路 :: Pipe_Intake|Pipe_Filter_Out|Pipe_Pump_In :: fit :: 从入口向过滤器和水泵逐段接管。
高压处理管路 :: Pipe_Pump_Out|Pipe_Membrane_In|Pipe_Membrane_Bridge :: fit :: 将泵后管线接到膜组并闭合跨接段。
净水出水管路 :: Pipe_Outlet|Pipe_Membrane_Out :: fit :: 连接净水立管、弯头和出口。
阀门与压力表 :: Valve|Gauge :: fit :: 先阀体，再手轮和压力读数件。
遮雨棚板 :: Canopy_|Roof_ :: swing :: 从一侧到另一侧逐条铺装棚板。
''')
add('WaterStorageTank','''
四角基础石墩 :: Base_Stone :: drop :: 按四角顺序放平石墩。
木支柱与柱帽 :: Pillar_Wood|Base_MetalCap :: raise :: 先竖木柱，再装金属柱帽。
纵横交叉撑 :: Brace_ :: swing :: 交替安装两方向斜撑。
承重平台 :: Platform_Main :: drop :: 将台面放在柱帽上。
平台封边梁 :: Platform_Edge :: slide :: 固定前后左右边梁。
左侧储水筒 :: Tank_Body_0 :: drop :: 吊放左筒并装仪表。
右侧储水筒 :: Tank_Body_1 :: drop :: 就位右筒并保留检修间隙。
储水罐顶 :: Tank_Dome :: drop :: 对齐罐口并扣上罐顶。
罐顶检修盖 :: Tank_Hatch :: fit :: 合盖并固定螺栓。
罐体加强箍带 :: Tank_Ring :: fit :: 从下到上扣紧箍带。
顶部均衡管 :: Pipe_Top_Connect :: slide :: 闭合两罐顶部连通管。
左右落水立管 :: Pipe_(Left_Drop|Right_Drop) :: fit :: 从罐口向下接入两侧立管。
罐底支管 :: Pipe_Tank :: fit :: 连接两只罐底出水口。
底部总管 :: Pipe_Bottom_Main :: slide :: 闭合平台下方总管。
外部取水口 :: Pipe_Outflow :: fit :: 将取水支管接到总管。
左右阀体 :: Valve_.*Body :: fit :: 将阀体装入管线。
阀门手轮 :: Valve_.*Wheel :: fit :: 对齐阀杆并装手轮。
检修梯侧梁 :: Ladder_Rail :: raise :: 将两根梯梁挂到平台边缘。
梯级与挂钩 :: Ladder_(Rung|Hook) :: fit :: 从下到上装梯级，最后固定挂钩。
''')

# Each ordered pair is an assembly, expanded to individual part arrivals by the builder.
EXTRA = {
'DriftwoodCollectionBoom_DeepSeek': [('锚块','Mooring_Weight'),('系泊绳','Mooring_Rope'),('浮筒主体','Float_Pod_[0-9]+$'),('浮筒端盖','Float_Pod_.*Cap'),('浮筒鞍座','Float_Saddle'),('前后拦木','Log_'),('绑带与端部束带','Strap_|End_Binding'),('收集兜支架','Pocket_Mount'),('收集兜底板','Pocket_Base'),('收集兜格栅','Pocket_Slat'),('收集兜上框','Pocket_Top'),('护栏立柱','Rail_Post'),('护栏绳','Rail_Rope')],
'FishingDock_DeepSeek': [('码头桩基','Pile|Foundation'),('主梁与搁栅','Beam|Joist'),('逐块铺板','Deck_Plank'),('系泊柱','Mooring|Bollard|Post_Cap'),('踏步底座','Ramp_Base'),('踏步','Ramp_Tread'),('晾网架立柱','Rack_Post'),('晾网横梁','Rack_TopBar'),('横向网绳','Net_String_H'),('纵向网绳','Net_String_V'),('鱼箱底部','Crate_Base'),('鱼箱盖板','Crate_'),('绳卷','Rope_Coil'),('附属五金','Cleat|Ring|Ladder|Life')],
'StorageDepot_DeepSeek': [('支墩','Foundation_Pier|Loading_Platform_Pier'),('柱帽','Foundation_Cap|Loading_Platform_Post'),('地梁','Floor_Joist|Loading_Platform_Joist'),('室内地板','Floor_Board'),('装卸平台','Loading_Platform_Board'),('墙框','Wall_(CornerPost|SideStud)'),('后墙','Wall_Back'),('左墙','Wall_Left'),('右墙','Wall_Right'),('前墙','Wall_Front'),('门框','Door_(Frame|Header)'),('门板斜撑','Door_(Panel|Leaf|DiagonalBrace)'),('门五金','Door_(Hinge|Latch)'),('通风框','Vent_Frame'),('通风百叶','Vent_Louver'),('主屋面','Roof_MainPanel'),('屋面收边','Roof_'),('雨棚支架','Awning_(Post|Brace)'),('装卸雨棚','Loading_Awning|Awning_Corrugation'),('坡道','Access_Ramp'),('排水槽','Gutter_'),('集雨桶','RainBarrel'),('物资堆放','Cargo_')],
'RescueDock_DeepSeek': [('桩基','Dock_Pile'),('横梁','Dock_CrossBeam'),('纵梁','Dock_LongBeam'),('甲板','Deck_Plank'),('系泊柱','MooringPost_[0-9]+$'),('柱帽系缆件','MooringPost_(Cap|Cleat)|Dock_TieRing'),('梯支座','Ladder_Mount'),('梯侧梁','Ladder_Rail'),('梯级','Ladder_Rung'),('救生圈立柱','LifeRing_Post'),('救生圈','LifeRing_'),('救援艇入水','Boat_Hull'),('艇舷','Boat_Gunwale'),('座舱','Boat_Cockpit_Well'),('座椅','Boat_Seat'),('操纵台','Boat_Console'),('风挡支架','Boat_Windshield_Bracket'),('风挡','Boat_Windshield'),('舵轮','Boat_Steering'),('发动机挂架','Boat_Motor_Mount'),('发动机','Boat_Motor'),('船上系缆件','Boat_Cleat'),('艏缆','MooringLine_Bow'),('艉缆','MooringLine_Stern')],
'ResidentHut_DeepSeek': [('基础','Foundation_Base'),('支桩','Foundation_Pile'),('主梁','Floor_Beam'),('搁栅','Floor_Joist'),('斜撑','Foundation_Brace'),('室内地板','Floor_Plank_Main'),('门廊地板','Floor_Plank_Porch'),('角柱','Wall_CornerPost'),('窗侧立框','Side_Window_Stud'),('后墙','Wall_Plank_Back'),('左墙','Wall_Plank_Side_-1'),('右墙','Wall_Plank_Side_1'),('前墙','Wall_Plank_Front'),('门框','Door_(Jamb|Lintel)'),('门板','Door_Main'),('门五金','Door_(Handle|Hinge)'),('窗框','Window_Frame'),('窗玻璃与百叶','Window_(Glass|Shutter)'),('屋面','Roof_Panel'),('屋脊压条','Roof_Rib'),('通风口','Vent_Frame'),('排水','Gutter_'),('台阶','Stair_(Step|Riser)'),('栏杆','Porch_Rail|Stair_Rail')],
'SolarPowerStation_DeepSeek': [('基础支脚','Foundation_(PlinthFoot|Underside_FootPlate)'),('底部承轨','Foundation_Underside_Rail'),('混凝土基座','Foundation_Pad'),('锚固与接缝','Foundation_(Anchor|Seam)'),('支架底板','Rack_BasePlate'),('支柱','Rack_Post'),('斜撑','Rack_Brace'),('承载横轨','Rack_Rail'),('组件外框','Panel_Frame'),('光伏面板','Panel_Glass'),('组件分格','Panel_Div'),('电柜','Cabinet_Main'),('电柜门','Cabinet_(Door|Hinge|Handle)'),('隔离开关','Cabinet_(Disconnect|Light)'),('穿线口','Pad_CableEntry|Conduit_Pad_Penetration'),('线管','Conduit_')],
'MedicalStation_DeepSeek': [('基础','Foundation_(Pad|Pier|Base)'),('承重底框','Foundation_|Floor_(Beam|Joist)|Base_'),('地板','Floor_|Porch_Deck'),('墙框','Frame_|Wall_Corner'),('后墙','Wall_Back'),('侧墙','Wall_(Left|Right|Gable)'),('前墙','Wall_Front'),('门框','Door_(Frame|Threshold)'),('门扇','Door_(Panel|Glass|Handle)'),('窗框','Window_Frame'),('玻璃','Window_(Glass|Mullion)'),('医疗标识','MedicalSign'),('门廊柱栏','Porch_(Post|Rail|Baluster)'),('雨棚','Porch_Roof'),('屋面','Roof_Panel'),('屋面收边','Roof_'),('入口踏步','Access|Step|Stair'),('设备柜','Utility_Cabinet'),('设备管线','Utility_Conduit'),('医疗物资','MedicalSupply')],
'Greenhouse_DeepSeek': [('基础垫块','Foundation_Pad'),('短柱','Foundation_ShortPost'),('承重梁','Foundation_Bearer'),('搁栅','Foundation_Joist'),('底部斜撑','Foundation_(CrossBrace|Underside)'),('地板','Floor_Deck'),('角柱','Frame_CornerPost'),('侧墙框','Frame_(SideStud|SideMidRail|SideRoofRail)'),('端墙门楣','Frame_(EndHeader|Front_Mullion|Back_Mullion)'),('屋顶椽','Roof_Rafter'),('踢脚围板','KickPanel'),('种植槽支脚','PlantBed_.*Foot'),('种植槽体','PlantBed_.*Body'),('种植土','PlantBed_.*Soil'),('滴灌管','DripLine'),('滴头','Dripper'),('幼苗茎','Seedling_.*Stem'),('幼苗叶','Seedling_.*Leaf'),('水箱支脚','WaterTank_Foot'),('水箱','WaterTank_'),('控制柜基础','ControlCabinet_Footing'),('控制柜','ControlCabinet_'),('门框门板','Door_Frame|Door_(Leaf|Lower_Panel|Handle)'),('侧玻璃','Glazing_Side'),('后玻璃','Glazing_Back'),('前玻璃','Glazing_Front|Door_Glass'),('屋顶玻璃','Roof_Glazing'),('屋面收边','Roof_Edge'),('高位通风窗','Roof_HighVent'),('雨水管线','Gutter_|RainPipe_|Tank_'),('入口台阶','AccessStep')],
'PublicKitchen_DeepSeek': [('基础支墩','PK_(Pier|Foundation|Footing)'),('地梁','PK_Beam'),('地板','PK_Floor'),('后墙','PK_RearWall|PK_RearVentBacking'),('备餐台腿','PK_PrepLeg'),('备餐台面','PK_Prep(Slab|Top)'),('水槽','PK_(Sink|Basin)'),('龙头','PK_Faucet'),('层架','PK_Shelf'),('储物柜物资','PK_FoodCabinet|PK_ProvisionCrate'),('炉体','PK_Stove(Body|Foot)'),('炉门灶头','PK_Stove(Door|Top)|PK_Burner'),('炉烟管','PK_StoveFlue'),('侧墙','PK_(LeftWall|RightWall)'),('前墙','PK_FrontWall'),('通风窗','PK_(RearVent|Vent|Window)'),('门','PK_Door'),('服务台','PK_(ServiceCounter|CounterBrace|HatchSill)'),('雨棚撑','PK_CanopyBrace'),('屋顶','PK_(Roof|FrontFascia|RearFascia)'),('烟管防雨帽','PK_(FlueRoofCollar|FlueCap)'),('排水','PK_(SideDrainPipe|DrainElbow|PipeBracket)'),('服务面板','PK_ServicePanel'),('踏步','PK_EntryStep'),('餐桌凳','PK_(Stool|Chair|Table)')],
'SalvageWorkshop_DeepSeek': [('木桩基础','Piled timber footing'),('地板','Deck plank'),('剪切机底座','Scrap shear mounting plinth'),('剪切机立座','Scrap shear pedestal'),('导轨','Shear rear guide'),('下颚与压头','Shear lower jaw|Shear upper ram'),('横梁刀片','Shear blade crosshead|Shear blade'),('液压系统','Hydraulic'),('后墙','Rear wall|Interior rear shadow'),('侧墙','Workshop side wall|Side corner post'),('开口门柱','Bay timber jamb'),('门楣','Bay lintel|Bay header repair plate'),('墙补片','Side cladding patch'),('警戒涂装','Bay warning stripe|Jamb dark stripe'),('龙门底板','Gantry foot plate'),('龙门柱','Gantry upright'),('龙门梁撑','Gantry (crossbeam|brace)'),('小车','Trolley'),('葫芦吊钩','Hoist|Hook'),('吊装板材','Lifted scrap plate|Load suspension link'),('分拣箱','Sorting bin|Bin corner brace'),('废管','Pipe bundle|Salvaged pipe|Scrap pipe'),('屋面','Main patched roof'),('屋面补片','Roof (rust|wood) patch'),('工坊标识灯','Workshop (name board|marker)|Work lamp')],
'Forge_DeepSeek': [('炉基础','SW_Base'),('炉床','SW_Hearth|SW_CoalBed'),('侧后炉墙','SW_ForgeWall_[LRB]$'),('前炉墙','SW_ForgeWall_F'),('炉顶','SW_ForgeTop|SW_ForgeMantle'),('耐火背板','SW_SootBack'),('炉口框','SW_FireFrame'),('集烟罩','SW_FireHood'),('烟囱','SW_ChimneyBody'),('烟囱接箍','SW_ChimneySeam|SW_ChimBand'),('帽支柱','SW_ChimCapPost'),('防雨帽','SW_ChimCapPlate'),('砧座木墩','SW_Stump'),('铁砧','SW_Anvil'),('风箱','SW_BellowsBody'),('风箱皮囊手柄','SW_Bellows(Leather|Handle)'),('风嘴','SW_BellowsNozzle'),('煤篮框','SW_Basket(Post|Ring|Bottom)'),('煤料','SW_BasketCoal'),('淬火槽','SW_Trough(Wall|Bottom|Patch)'),('注水','SW_TroughWater'),('工具架','SW_Rack'),('工具','SW_Tool'),('工件与夹具','SW_Rust|SW_HotBillet|SW_BilletTongs'),('炉火','SW_(GlowCoal|DarkCoal)')],
'RescueRadioCenter_DeepSeek': [('高架支腿','RRC_PlatformLeg'),('地梁','RRC_Beam'),('斜撑','RRC_Brace'),('平台','RRC_PlatformDeck'),('侧后墙','RRC_(BackWall|LeftWall|RightWall)'),('前墙','RRC_FrontWall'),('门框','RRC_DoorFrame'),('门','RRC_Door'),('窗框','RRC_Window(Frame|Bar)'),('玻璃','RRC_WindowGlass'),('救援标记','RRC_Cross'),('主屋顶','RRC_Roof$'),('屋顶收边','RRC_Roof'),('碟形天线支架','RRC_Dish(Base|Post|Tilt)'),('碟面馈源','RRC_MicrowaveDish|RRC_DishFeed'),('桅杆底座','RRC_MastBase'),('桅杆','RRC_Mast$'),('八木天线','RRC_Yagi'),('地锚拉索','RRC_(Anchor|Guy)'),('控制设备','RRC_Ctrl|RRC_FuseCover'),('线管','RRC_Conduit'),('线盘','RRC_CableReel'),('电池','RRC_Battery'),('信标','RRC_Beacon')],
'WeatherTideBuoy_DeepSeek': [('浮体','Float_Body'),('顶甲板','Float_Deck'),('桅杆底座','Mast_Base'),('主桅','Mast_Main'),('抱箍','Mast_Ring'),('传感盒支座','Sensor_Box_Mount'),('传感盒','Sensor_Box$'),('风速轴毂','Anemo_Hub'),('风杯支臂','Anemo_Arm'),('风杯','Anemo_Cup'),('风向标轴','Vane_(Arm|Arrow|Pivot)'),('尾翼','Vane_Tail'),('太阳能支柱','Solar_Post'),('组件框','Solar_Frame'),('太阳能面','Solar_Glass'),('无线电座','Radio_Base'),('天线','Radio_Whip'),('潮位支臂','Tide_Arm'),('潮位刻度','Tide_Scale|Tide_Tick'),('潮位探头','Tide_Probe|Transducer'),('航灯底座','NavLight_Base'),('航灯','NavLight_')],
'Shipyard_DeepSeek': [('支墩','Foundation|Base_Pad|Footing|Pier'),('作业平台','Platform|Deck'),('滑道轨','Slipway_Rail'),('船台支架','Hull_Support|Cradle|Slipway_(Support|Cross|Sleeper)'),('龙骨','Hull_Keel'),('底肋','Hull_Rib_Bot'),('左右肋骨','Hull_Rib_[LR]'),('下纵材','Hull_Stringer_.*Low'),('连接块','Hull_Stringer_Cleat'),('上纵材','Hull_Stringer_.*High'),('舷与艏艉','Hull_(Gunwale|Transom|Bow)'),('龙门底座','Gantry_(Foot|Base)'),('龙门柱','Gantry_(Post|Leg|Upright)'),('龙门横梁','Gantry_'),('吊车小车','Crane_(Trolley|Wheel)'),('吊链钩','Crane_(Chain|Hook)'),('工具棚底','Shed_Base'),('工具棚墙','Shed_Wall'),('棚门','Shed_Door'),('工具柜','Shed_Exterior_Tool|Shed_Tool_Cabinet'),('棚顶','Shed_Roof'),('棚灯','Shed_Light')],
'RescueOutpost_DeepSeek': [('基础','Foundation_|Base_|Footing'),('塔柱','Tower_|Main_Post|Pillar_|Frame_Post|Post_Main'),('交叉斜撑','Brace_X'),('平台搁栅','Platform_Joist'),('平台板','Platform_Plank'),('栏杆柱','Rail_Post'),('栏杆','Rail_'),('楼梯梁','Stair_Stringer'),('楼梯踏步','Stair_(Tread|Step)'),('梯扶手','Stair_Rail|Stair_Hand|Stair_Post'),('岗亭地板','Cabin_Floor'),('岗亭侧后墙','Cabin_Wall_(Back|Left|Right)'),('岗亭前墙','Cabin_Wall_Front'),('岗亭门','Cabin_Door'),('岗亭窗','Cabin_Window'),('屋面','Roof_Main'),('屋面收边','Roof_Trim'),('信号杆','Mast_Pole'),('信号灯','Signal_Light'),('天线','Antenna_'),('救生圈','LifeRing')],
'School_DeepSeek': [('石墩','StonePier'),('主地梁','Beam_Main'),('门廊地梁','Beam_Porch'),('室内地板','Floor_Main'),('门廊地板','Floor_Porch'),('角柱','Post_Corner'),('后墙','Wall_Back'),('侧墙','Wall_Side'),('前墙','Wall_Front'),('顶梁','Beam_Top'),('山墙','Gable_'),('门框','Door_Frame'),('门扇','Door_(Left|Right|Handle)'),('窗框','Win_'),('玻璃','Glass_'),('门廊柱','Porch_Post'),('门廊梁','Porch_Beam'),('栏杆','Railing_'),('台阶','Step_'),('雨棚椽','Porch_Roof_Beam'),('前屋面','Roof_Front'),('后屋面','Roof_Back'),('脊盖补片','Roof_(Ridge|Patch)'),('排水','Gutter_|Downspout_'),('教学公告板','Board_'),('灯具','Light_')],
'Archive_DeepSeek': [('石墩','Base_StonePier|Porch_Pier'),('地梁','Base_FloorBeam'),('地板','Base_Floor$'),('门廊梁','Porch_Beam'),('门廊板','Porch_Deck'),('角柱','Post_Corner'),('底框','Beam_Bottom'),('后墙','Wall_Back'),('侧墙','Wall_Side'),('前墙','Wall_Front'),('顶框','Beam_Top'),('墙面板','Siding_'),('门框','Door_Frame'),('门','Door_'),('窗框','Window_.*Frame'),('玻璃','Window_.*Glass'),('百叶','Window_.*Shutter'),('通风框','Back_Vent_Frame'),('通风件','Back_Vent_'),('门廊支架','Porch_(Post|Header|Brace)'),('门廊雨棚','Porch_Canopy'),('主屋面','Roof_Main'),('屋面压条','Roof_'),('檐沟','Gutter_(Back|Front|Left|Right)'),('排水管','Gutter_'),('踏步','Step_'),('公告板','NoticeBoard'),('入口灯','Entrance_Light')],
'CouncilHall_DeepSeek': [('基础墩','Foundation_Pier'),('横地梁','Foundation_Beam_X'),('纵地梁','Foundation_Beam_Y'),('主楼板','Floor_Main'),('地板铺板','Floor_Plank'),('门廊基础','Porch_StonePier|Porch_Beam'),('门廊甲板','Porch_Deck'),('主体框架','^(Post_|Frame_|Beam_|Column_)'),('后墙','Wall_Back'),('左墙','Wall_Side_-1'),('右墙','Wall_Side_1'),('前墙','Wall_Front'),('门框','DoorFrame'),('门洞衬板','Door_Recess'),('门扇','Door_Leaf'),('门把手','Door_Handle'),('高窗框','Back_Clerestory_.*Frame'),('高窗玻璃','Back_Clerestory_.*Glass'),('侧窗框','Side-?1_Window.*(Frame|Mullion)'),('侧玻璃','Side-?1_Window.*Glass'),('百叶通风','Side-?1_Window.*(Shutter|Louver)|Back_Vent'),('门廊柱','Porch_Post'),('门廊梁撑','Porch_(FrontHeader|Header|Brace|Rafter)'),('门廊棚','Porch_Canopy'),('四坡屋顶','Roof_HipShell'),('压棱接缝','Roof_(Corrugation|HipSeam)'),('屋脊补片','Roof_(Ridge|RepairPatch)'),('排水','Roof_(Gutter|Down)|Gutter_|Downspout'),('入口踏步','Step_|Stair_|Ramp_'),('栏杆','Rail_|Railing_|Porch_Rail'),('公共公告板','Community_Noticeboard'),('入口灯','EntryLamp')]
}
for asset, groups in EXTRA.items():
    RECIPES[asset] = [dict(title=title, pattern=pattern, mode='fit', action=f'按支承端到自由端的顺序安装{title}；先定位主体，再锁紧连接件，保留现有开口与检修空间。') for title,pattern in groups]

def insert(asset, before, title, pattern, action):
    phases=RECIPES[asset]
    index=next((i for i,p in enumerate(phases) if p['title']==before),len(phases))
    phases.insert(index,dict(title=title,pattern=pattern,mode='fit',action=action))

def extend(asset,title,pattern):
    next(p for p in RECIPES[asset] if p['title']==title)['pattern']+='|'+pattern

extend('CouncilHall_DeepSeek','主体框架','^Structure_')
extend('CouncilHall_DeepSeek','侧窗框','SideWindowJamb|FrontWindow.*(Frame|Mullion)')
extend('CouncilHall_DeepSeek','侧玻璃','FrontWindow.*Glass')
extend('CouncilHall_DeepSeek','前墙','Front_Siding')
extend('CouncilHall_DeepSeek','门廊梁撑','Porch_KneeBrace')
extend('CouncilHall_DeepSeek','排水','Downpipe')
insert('DesalinationPlant_DeepSeek','', '顶棚支柱','^Post_','先固定立柱底端，再连接顶棚承梁。')
insert('LocalCommunicationsCenter_DeepSeek','', '墙角立柱','Frame_CornerPost','竖立四角柱并锁紧柱脚。')
# Move corner posts before walls and canopy posts before equipment enclosure.
for asset,title,index in [('LocalCommunicationsCenter_DeepSeek','墙角立柱',2),('DesalinationPlant_DeepSeek','顶棚支柱',5)]:
    p=next(p for p in RECIPES[asset] if p['title']==title); RECIPES[asset].remove(p); RECIPES[asset].insert(index,p)
insert('LocalCommunicationsCenter_DeepSeek','', '屋面接缝压条','Roof_Seam','屋面就位后逐条压紧板缝。')
insert('LocalCommunicationsCenter_DeepSeek','', '天线振子','Antenna_Dipole','将振子对称固定到桅杆横臂。')
insert('MedicalStation_DeepSeek','', '雨水排放系统','Gutter_|Downpipe','先固定檐沟和出口，再装落水管。')
insert('PublicKitchen_DeepSeek','基础支墩','垫块与支腿','PK_Pad|PK_Leg','先落垫块，再竖起平台支腿。')
insert('PublicKitchen_DeepSeek','地板','底部交叉斜撑','PK_XBrace','对称安装平台下方交叉斜撑。')
insert('PublicKitchen_DeepSeek','屋顶','服务雨棚','PK_ServiceCanopy','将服务口雨棚固定在已有斜撑上。')
extend('PublicKitchen_DeepSeek','通风窗','PK_(Left|Right)Vent')
extend('RescueOutpost_DeepSeek','交叉斜撑','Brace_H')
extend('SalvageWorkshop_DeepSeek','屋面补片','Roof corrugation')
extend('SolarPowerStation_DeepSeek','电柜门','Cabinet_Louver')
insert('FishingDock_DeepSeek','码头桩基','浮筒','Float_Drum','逐只将浮筒放入水面定位。')
insert('FishingDock_DeepSeek','码头桩基','浮筒束带','Float_Strap','逐条绕过浮筒固定到承重结构。')
insert('FishingDock_DeepSeek','踏步','坡道侧梁','Ramp_Rail','连接岸侧和码头侧坡道梁。')
insert('WeatherTideBuoy_DeepSeek','顶甲板','压载防撞圈','Float_Ballast|Float_Bumper','浮体完成后安装下部压载圈和周边防撞块。')
insert('WeatherTideBuoy_DeepSeek','主桅','系泊环','Mooring_','先焊系泊垫板，再安装系泊环。')
insert('WeatherTideBuoy_DeepSeek','抱箍','桅杆斜撑','Mast_Brace','对称锁紧桅杆四侧斜撑。')
insert('WeatherTideBuoy_DeepSeek','航灯','防护栏','Guard_','先立护栏柱，再闭合上圈。')
