"""Author construction timelines and exact part schedules for the 25 detailed assets.
Run: blender -b --python Tools/Blender/build_all_construction_sequences.py
Optional: -- --asset=Greenhouse_DeepSeek --preview
"""
from pathlib import Path
import sys,json,re,math,hashlib
import bpy
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from building_construction_recipes import RECIPES,NAMES,FPS
SOURCE=ROOT/'Assets/LastLandfall/Art/Source'
OUT=ROOT/'Assets/LastLandfall/Art/Source/Construction/Detailed'
REPORT=ROOT/'Assets/LastLandfall/Art/Reports/Construction'
PREVIEW=ROOT/'Assets/LastLandfall/Art/Previews/Construction/Detailed'
DOC=ROOT/'Design/Construction'
for p in (OUT,REPORT,PREVIEW,DOC):p.mkdir(parents=True,exist_ok=True)
helpers={'__file__':str(ROOT/'Tools/Blender/render_building_icon.py')}
exec((ROOT/'Tools/Blender/render_building_icon.py').read_text(encoding='utf-8').split('arguments = argv_after_separator()')[0],helpers)

NOTES={
'Greenhouse_DeepSeek':'种植槽、土壤、滴灌与幼苗必须在玻璃封闭前安装；透明面最后封闭。幼苗生长属于布置表现，不代表实际施工时间。',
'MedicalTent_DeepSeek':'先床架与物资、后帆布；布料以张设动作表现，床脚不得穿过地板。',
'Shipyard_DeepSeek':'完工状态是当前模型中的作业船坞与未封板船体；不将肋骨船体虚构成完整成船。',
'RescueDock_DeepSeek':'救援艇为独立水上单元；码头先完成，船体入水后安装艇上设备，最后连接艏艉缆。',
'WeatherTideBuoy_DeepSeek':'浮体按水面定位，压载环在浮体下方；传感器不得被护栏或太阳能组件遮挡。',
'PublicKitchen_DeepSeek':'水槽开口、炉灶与服务窗口保持原模型轮廓；先室内台柜后屋面封闭，烟道先管身后防雨帽。',
'SolarPowerStation_DeepSeek':'先支架后组件，五金依附外框与承轨；不得在光伏工作面中间新增紧固件。',
'Forge_DeepSeek':'先炉床与炉墙后烟罩烟囱；淬火槽成形后注水，最后表现炉火。',
'DirtRoadTiles_DeepSeek':'五种道路分别建造；起终点与四向接口保持原有标高、宽度，不用额外石块封堵接口。',
}

def curves(action):
    if hasattr(action,'fcurves'):return list(action.fcurves)
    return [c for layer in action.layers for strip in layer.strips for bag in strip.channelbags for c in bag.fcurves]

def normalized(name,asset):return name.removeprefix(asset+'_')

def order(obj):
    n=obj.name.lower()
    rank=0 if re.search('mount|support|foot|base|bracket|bottom|post|jamb',n) else 2 if re.search('cap|handle|glass|label|bolt|screen|light',n) else 1
    return (rank,round(obj.matrix_world.translation.z,3),obj.name)

def assign(asset,objects):
    groups=[dict(p,objects=[]) for p in RECIPES[asset]]
    assignments={};detail=[];missing=[]
    for o in objects:
        if o.get('detail_anchor'):detail.append(o);continue
        i=next((i for i,p in enumerate(groups) if re.search(p['pattern'],normalized(o.name,asset),re.I)),None)
        if i is None:missing.append(o.name)
        else:groups[i]['objects'].append(o);assignments[o.name]=i
    if missing:raise RuntimeError(asset+' unassigned: '+str(missing))
    for o in detail:
        anchor=o['detail_anchor']
        if anchor not in assignments:raise RuntimeError('Missing detail anchor '+o.name+' -> '+anchor)
        groups[assignments[anchor]]['objects'].append(o)
    return [p for p in groups if p['objects']]

def bake(objects,offset):
    deps=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        ev=o.evaluated_get(deps)
        mesh=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=deps)
        world=o.matrix_world.copy();mesh.transform(Matrix.Translation(offset)@world)
        center=sum((Vector(v) for v in [tuple(v.co) for v in mesh.vertices]),Vector())/max(len(mesh.vertices),1)
        mesh.transform(Matrix.Translation(-center))
        o.parent=None;o.constraints.clear();o.modifiers.clear();o.animation_data_clear();o.data=mesh
        o.matrix_world=Matrix.Translation(center);o.hide_render=False;o.hide_viewport=False
    bpy.context.view_layer.update()

def animate(o,start,end,span,mode):
    final=o.location.copy()
    distance=max(.10,min(span*.16,.65))
    delta=Vector((0,0,distance))
    if mode in ('slide','fit'):delta=Vector((distance if final.x>=0 else -distance,0,distance*.28))
    if mode=='raise':delta=Vector((0,0,distance*.5))
    o.hide_render=True;o.hide_viewport=True
    for prop in ('hide_render','hide_viewport'):o.keyframe_insert(prop,frame=start-1)
    o.hide_render=False;o.hide_viewport=False
    for prop in ('hide_render','hide_viewport'):o.keyframe_insert(prop,frame=start)
    o.location=final+delta;o.keyframe_insert('location',frame=start)
    o.location=final;o.keyframe_insert('location',frame=end)
    # Only soft material / soil / growth uses scaling. Rigid assemblies preserve dimensions.
    if mode in ('cloth','earth','grow'):
        o.scale=(1,1,.02);o.keyframe_insert('scale',frame=start)
        o.scale=(1,1,1);o.keyframe_insert('scale',frame=end)
    for curve in curves(o.animation_data.action):
        for key in curve.keyframe_points:key.interpolation='CONSTANT' if curve.data_path.startswith('hide_') else 'LINEAR'
    return dict(object=o.name,start=start,end=end,anchor=o.get('detail_anchor',''),role=o.get('detail_role',''),mode=mode)

def document(record):
    a=record['asset'];lines=[f"# {record['name']}：详细建造过程",'',f"- 当前模型：`{record['source']}`",f"- 动画：`{record['blend']}`",f"- 帧率：{FPS} fps；共 {record['frames']} 帧，{record['seconds']:.1f} 秒。",f"- 构件：{record['objects']} 个；阶段：{len(record['phases'])} 个。",'', '## 编排规则','', '以下时长为动画节奏，不是现实工期。每阶段内部继续逐件安装，画面不是只在阶段末跳变。主件落位后才安装对应紧固件和装饰。数字范围均含首尾帧。','',NOTES.get(a,'先基础、后承重结构与围护；设备支座先于设备，收边和附属件随依附构件安装。'),'', '## 施工准备','', '1. 核对当前模型、朝向、占地和入口，保持最终轮廓与游戏接口。','2. 按下列构件清单分包，确认支承部件已完成再安装上部构件。','3. 首帧为空场；施工动作不改变最终网格和材质。','']
    preview=f"../../Assets/LastLandfall/Art/Previews/Construction/Detailed/{record['clip']}/Overview.jpg"
    lines += ['## 阶段总览','',f'[查看带标签的阶段拼图]({preview})','', ' → '.join(p['title'] for p in record['phases']),'']
    for idx,p in enumerate(record['phases'],1):
        lines += [f"## {idx:02d}．{p['title']}",'',f"**帧 {p['start']}–{p['end']}**（{(p['end']-p['start']+1)/FPS:.1f} 秒；{len(p['parts'])} 件）。",'', '**前置条件：** '+('场地定位完成。' if idx==1 else f"第 {idx-1:02d} 阶段构件已就位；确认当前构件的支承面和连接端。"),'','**操作：** '+p['action'],'','**镜头内动作：** 主件按下表错开起落；细节件在其依附主件完成后进入。安装期间保持已有部件可见。','','| 顺序 | 模型零件 | 入场帧 | 落位帧 | 依附部件 |','| --- | --- | ---: | ---: | --- |']
        for k,part in enumerate(p['parts'],1):lines.append(f"| {k} | `{part['object']}` | {part['start']} | {part['end']} | `{part['anchor']}` |")
        instructions, acceptance = work_instructions(p)
        lines += ['', '**细分工序：**', '']
        lines += [f'{j}. {step}' for j,step in enumerate(instructions,1)]
        lines += ['','**阶段完成要求：** '+acceptance+' 本阶段清单全部就位；不得提前显露下一阶段构件。','']
    lines += ['## 完工状态','', '全部构件到达源模型的位置与比例；源模型未被覆盖。动画是美术施工表现，Unity 接入代码与资源已编写，尚未运行 Unity 验证。完整逐帧 PNG 可通过 Blender 渲染动画导出；附带预览只取关键阶段。','']
    (DOC/(record['clip']+'.md')).write_text('\n'.join(lines),encoding='utf-8')

def work_instructions(phase):
    title=phase['title']
    rules=[
      ('基础|石墩|垫块|支墩|桩基|支桩', ['按最终占地确定各支承点，先处理角点，再补中间点。','构件逐件垂直落位；各顶面以当前模型的承梁标高为准。','逐点核对上层梁的落脚位置，保留桩间水流或通风空间。'], '基础与后续承梁相接，所有支承点保持源模型高差。'),
      ('地梁|横梁|纵梁|框梁|搁栅|承轨|底框', ['先安装主承重方向构件，再装横向连接构件。','每根梁从一端导入，连接两端支座；中间构件按固定间隔补齐。','主体闭合后安装连接片与紧固件，保留与上下层构件的接触关系。'], '梁端有对应支承，框架闭合，未以悬空梁代替支座。'),
      ('斜撑|拉结|梁撑', ['先确认两端柱梁已经完成，再按对角线定位斜撑。','先固定一端，再将另一端旋入或平移到连接点；相邻侧交替安装。','交叉处保持原模型层次，最后锁紧端部连接件。'], '斜撑两端都与既有框架连接，交叉件无新增穿插。'),
      ('立柱|角柱|支柱|支腿|塔柱|门柱|框柱|高侧|低侧', ['先定位柱脚，按后侧到前侧或对称两侧的顺序逐根竖立。','保持柱底与已有基础接触，柱顶对齐下一阶段承梁。','主柱落位后装柱脚板、抱箍或该柱附属细节。'], '柱脚不悬空，柱顶与原有梁架接点一致。'),
      ('地板|甲板|铺板|平台板', ['从远侧或角部开始铺设第一块板，露出尚未铺设的搁栅。','逐块向入口方向延伸，保持原有板缝及边缘收口。','沿开口裁边的板件使用原模型形状，不填平楼梯口、排水口或检修口。'], '板件沿现有梁架铺开，开口和模块接口完整保留。'),
      ('玻璃|光伏面|太阳能面|组件分格', ['确认四周框、承轨及内部设备已经完成。','面板从框外侧缓慢靠近，先贴近下边缘再归位到最终平面。','装框边附属件；透明或发电工作面保持完整，不新增中心螺栓。'], '边缘落在框内，透明面不误变为墙板，工作面无遮挡。'),
      ('屋面|屋顶|棚顶|雨棚|帆布|棚布', ['先确认屋顶支柱、梁椽或雨棚斜撑已经完成。','从低侧或一侧逐片覆盖，给内部安装保留到最后一片封闭前。','盖好后再装压条、补片与沿边紧固件，保持原有排水坡度。'], '顶面覆盖对应支架，屋脊、檐口与排水方向保持源模型形状。'),
      ('墙|围板|挡风板|山墙|踢脚', ['确认墙角立柱与上下横档已在场，先安装背面再安装侧面。','板件由下到上或沿框架逐片固定，前侧开口尽量延后封闭。','洞口四周按原模型收边，不用板件封堵门、窗或设备口。'], '墙面有框架依托，所有门窗与服务窗口保持通畅。'),
      ('门框|窗框|通风框|立框|门楣', ['对照已完成墙洞定位两侧竖框，先下端再上端。','连接上横框与中间分格，保持原模型净开口。','本阶段只安装清单中的框件；玻璃、门扇和百叶按后续清单进入。'], '框件围绕既有洞口闭合，未缩小原有开口。'),
      ('门扇|门板|门五金|百叶|窗玻璃|风挡', ['先核对框、支架或铰接端已经完成。','主体由铰接侧或下支承端进入，归位后再装把手、铰链和锁件。','按源模型保留开合状态，检查相邻墙面与设备间的间隙。'], '主体与支承相连，开口和检修空间不被附属件遮挡。'),
      ('管|阀|滴灌|滴头|龙头|排水|穿线|线盘|电池', ['确认设备接口、管夹或安装面已经在场。','按上游到下游连接各管段；弯头对正后再闭合末端接头。','主体连接完成后装阀轮、刻度、接线端与依附细节，保留操作方向。'], '每段管线有对应接口，阀门与设备检修面可见。'),
      ('梯|台阶|踏步|坡道|栏杆|扶手|防护栏', ['先安装两端支座与侧梁，跨接到已有平台或入口。','踏板从低处向高处逐级安装；栏杆先立柱后横杆。','最后补边缘紧固件，保留入口净宽和原有踏步间距。'], '通行路径连续，栏杆与踏板接点明确，入口未封堵。'),
      ('土|幼苗|注水|炉火|煤料', ['先确认槽、床、容器或炉膛已经成形。','在容器内部逐步填入土、水或物料；植物先茎后叶。','填充到源模型最终高度，最后补小块或叶片，避免溢出边框。'], '填充物位于对应容器内部，最终体积与源模型一致。'),
      ('浮筒|浮体|救援艇入水|压载', ['按源模型水面基准定位浮动主体，不将其当作陆地基础。','先主体后外圈、端盖或束带，逐件固定相应连接点。','上部构件只在浮体就位后进入，系泊绳按其独立阶段连接。'], '浮动主体保持原有水线与位置，未增加虚构海床支脚。'),
      ('龙骨|肋骨|纵材|舷与艏艉', ['先确认船台支架与前序骨架完成，定位本阶段船体基准线。','从中部向艏艉对称补件，先下部后上部，逐条与已有骨架相接。','保持当前未完工船体的开敞轮廓，不补造原模型没有的船板。'], '骨架连续连接，完工状态仍与当前船坞源模型一致。'),
    ]
    steps,acceptance=next(((s,c) for regex,s,c in rules if re.search(regex,title)),(['核对本阶段清单中每个主体的安装面、承架或连接端。','先安装主体和支承连接，再依次补齐其可拆附属部件。','依照逐件帧表错开进入，主体完全落位后才安装所依附的标牌、仪表或紧固细节。'],'主体与已建结构连接，安装位置、朝向和材质与源模型一致。'))
    details=sum(bool(part['anchor']) for part in phase['parts'])
    return steps+[f'本阶段共 {len(phase["parts"])} 件，其中 {details} 件为依附细节；各件严格使用上表的入场帧与落位帧。'],acceptance

def build(path,root_name=None):
    a=path.stem;bpy.ops.wm.open_mainfile(filepath=str(path))
    scene=bpy.context.scene;collection=bpy.data.collections.get(a)
    if root_name:
        root=bpy.data.objects[root_name];objects=[o for o in root.children_recursive if o.type=='MESH'];offset=-root.matrix_world.translation
        clip=root_name+'_DeepSeek'
    else:objects=[o for o in collection.all_objects if o.type=='MESH'];offset=Vector();clip=a
    groups=assign(a,objects)
    keep=set(objects)
    # Bake before deleting parents / nonmodel objects.
    bake(objects,offset)
    for o in list(bpy.data.objects):
        if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
    bounds=helpers['world_bounds'](objects);mins,maxs,_=bounds
    center,sx,sy,sz,tile,corners=helpers['add_stage'](scene,mins,maxs)
    span=max(sx,sy,sz,tile,2.4)
    helpers['add_studio_lighting'](scene,center,span)
    helpers['camera_frame'](scene,corners,center+Vector((0,0,sz*.04)),span)
    scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=480;scene.render.resolution_y=480;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.fps=FPS
    scene.render.film_transparent=False;scene.view_settings.view_transform='Standard'
    if hasattr(scene,'eevee'):scene.eevee.taa_render_samples=24
    scene.timeline_markers.clear();frame=2;phases=[]
    for index,p in enumerate(groups,1):
        main=sorted([o for o in p['objects'] if not o.get('detail_anchor')],key=order)
        details=sorted([o for o in p['objects'] if o.get('detail_anchor')],key=lambda o:(o['detail_anchor'],o.name))
        primary_duration=max(24,12+len(main)*4)
        detail_duration=max(12,8+len(details)*2) if details else 0
        end=frame+primary_duration+detail_duration-1;parts=[]
        for k,o in enumerate(main):
            start=frame+k*4;finish=start+min(20,primary_duration-k*4-1)
            name=o.name.lower();mode=p['mode']
            if re.search('soil|water$|seedling.*leaf',name):mode='grow'
            parts.append(animate(o,start,finish,span,mode))
        for k,o in enumerate(details):
            start=frame+primary_duration+k*2;parts.append(animate(o,start,min(start+10,end),span,'fit'))
        scene.timeline_markers.new(f"{index:02d} {p['title']}",frame=frame)
        phases.append(dict(title=p['title'],action=p['action'],start=frame,end=end,parts=parts));frame=end+1
    scene.frame_start=1;scene.frame_end=frame+11
    scene.timeline_markers.new('完成 / Complete',frame=frame)
    preview_dir=PREVIEW/clip;preview_dir.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(preview_dir/'Frames'/'frame_')
    scene.frame_set(scene.frame_end)
    for o in objects:
        if o.hide_render or o.hide_viewport or (o.scale-Vector((1,1,1))).length>1e-5:raise RuntimeError('Incomplete '+o.name)
    record=dict(asset=a,clip=clip,name=NAMES[a]+(' / '+root_name if root_name else ''),source=path.relative_to(ROOT).as_posix(),blend=(OUT/(clip+'_Construction.blend')).relative_to(ROOT).as_posix(),objects=len(objects),frames=scene.frame_end,seconds=scene.frame_end/FPS,phases=phases)
    scene['construction_catalog']=json.dumps({k:v for k,v in record.items() if k!='phases'},ensure_ascii=False)
    # Open at final frame to keep thumbnail useful; press Shift+Left then Space to play from empty site.
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/record['blend']),compress=True)
    (REPORT/(clip+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');document(record)
    if '--preview' in sys.argv:
        for i,p in enumerate(phases):
            scene.frame_set(p['end']);scene.render.filepath=str(preview_dir/f"{i+1:02d}.png")
            bpy.ops.render.render(write_still=True)
    print('CONSTRUCTION_COMPLETE',clip,len(phases),len(objects),scene.frame_end,flush=True)
    return record

selected=[v.split('=',1)[1] for v in sys.argv if v.startswith('--asset=')]
paths=sorted(SOURCE.glob('*/*_DeepSeek.blend'))+[SOURCE/'Buildings/WaterStorageTank.blend']
records=[]
for path in paths:
    if selected and path.stem not in selected:continue
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    roots=['DirtRoadStraight','DirtRoadCorner','DirtRoadTee','DirtRoadCross','DirtRoadEnd'] if path.stem=='DirtRoadTiles_DeepSeek' else [None]
    for root in roots:records.append(build(path,root))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise RuntimeError('Source changed '+str(path))
all_records=[json.loads(p.read_text(encoding='utf-8')) for p in REPORT.glob('*.json') if p.name!='catalog.json']
(REPORT/'catalog.json').write_text(json.dumps(all_records,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 全建筑详细施工过程','',f"共 {len(set(r['asset'] for r in all_records))} 套资产、{len(all_records)} 条施工序列；{sum(len(r['phases']) for r in all_records)} 个阶段、{sum(r['frames'] for r in all_records)} 个可播放帧。",'', '每份说明列出实际零件名称、进入帧、落位帧、依附主件、阶段操作与完成要求。新增细节跟随主件安装；所有源模型保持原样。','', '## 查看与播放','', '- 点击下表进入逐建筑施工说明。','- 在 Blender 打开对应 Construction.blend，Shift+左方向键回到第 1 帧，空格播放；时间线标记可定位阶段。','- 24 fps；每个构件有连续位移动作，不是几个静态阶段反复显示。','- 关键阶段 PNG 在 `Assets/LastLandfall/Art/Previews/Construction/Detailed/`。','- 动画源文件和逐帧计划已生成；Unity 接入代码与资源已编写，尚未运行 Unity 验证。','', '| 建筑 / 模块 | 阶段 | 构件 | 帧数 | 秒 | 详细说明 |','| --- | ---: | ---: | ---: | ---: | --- |']
for r in sorted(all_records,key=lambda r:r['clip']):lines.append(f"| {r['name']} | {len(r['phases'])} | {r['objects']} | {r['frames']} | {r['seconds']:.1f} | [施工说明](Construction/{r['clip']}.md) |")
lines += ['', '## 施工预览总览','', '[查看全部施工序列总览](../Assets/LastLandfall/Art/Previews/Construction/Detailed/All_Construction_Overview.jpg)','', '各建筑的阶段拼图在对应施工说明的“阶段总览”处。','', '## 重新生成','', '```powershell', r'& "D:\Blender 5.2\blender.exe" --background --python Tools/Blender/build_all_construction_sequences.py', '# 附带阶段预览：在命令尾部添加 -- --preview', '# 单资产： -- --asset=Greenhouse_DeepSeek --preview', '```','', '全帧导出：打开施工 blend，在输出设置选择目录，执行“渲染 → 渲染动画”。各阶段完整构件计划见 `Assets/LastLandfall/Art/Reports/Construction/catalog.json`。','']
(ROOT/'Design/Building_Construction_Sequences.md').write_text('\n'.join(lines),encoding='utf-8')
print('ALL_CONSTRUCTION_COMPLETE',len(all_records),flush=True)
