"""Compose review sheets and a readable report from Blender audit outputs."""
import json,ast
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops,ImageStat
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'Assets/LastLandfall/Art/Reports/BuildingAudit'
report=json.loads((R/'optimization_report.json').read_text(encoding='utf-8'))
before=json.loads((R/'source_audit_before.json').read_text(encoding='utf-8'))
after=json.loads((R/'source_audit.json').read_text(encoding='utf-8'))
fixes=json.loads((R/'structural_repairs.json').read_text(encoding='utf-8'))
assets=list(dict.fromkeys(x['asset'] for x in report['exports']))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
comparisons=[]
for asset in assets:
    for view in ['Front','Rear']:
        folder=R/'Visuals'/asset
        source=Image.open(folder/f'Source_{view}.png').convert('RGB')
        optimized=Image.open(folder/f'Optimized_{view}.png').convert('RGB')
        delta=sum(ImageStat.Stat(ImageChops.difference(source,optimized)).mean)/3
        comparisons.append({'asset':asset,'view':view,'mean_rgb_difference_0_255':delta})
for view in ['Front','Rear']:
    sheet=Image.new('RGB',(1600,1800),'#20282b');draw=ImageDraw.Draw(sheet)
    for i,asset in enumerate(assets):
        thumb=Image.open(R/'Visuals'/asset/f'Optimized_{view}.png').convert('RGB').resize((320,320),Image.Resampling.LANCZOS)
        sheet.paste(thumb,((i%5)*320,(i//5)*360))
        draw.text(((i%5)*320+5,(i//5)*360+326),asset.replace('_DeepSeek',''),font=font,fill='white')
    sheet.save(R/f'25_Models_Optimized_{view}.jpg',quality=92)
(R/'visual_comparison.json').write_text(json.dumps(comparisons,indent=2),encoding='utf-8')
old_meshes=sum(x['meshes'] for x in before);new_meshes=sum(x['after']['meshes'] for x in report['exports']);new_source=sum(x['meshes'] for x in after)
translations={
'Greenhouse_DeepSeek':'温室：为两个种植槽补上 8 个支脚，消除离地板 30 mm 的悬空。',
'CouncilHall_DeepSeek':'议事厅：补上两个门把手安装座，连接把手与门扇。',
'PublicKitchen_DeepSeek':'公共厨房：4 个货箱下移到实际层板面；延长排水立管，与弯头接通。',
'MedicalStation_DeepSeek':'医疗站：扩大玻璃及中梃，使它们嵌入窗框，消除周边缝隙。',
'RescueOutpost_DeepSeek':'救援前哨：调整 3 根平台承重梁方向，使它们垂直承托所有铺板。',
'FishingDock_DeepSeek':'渔船码头：延长网绳，使横绳连到立柱、竖绳挂到上横杆。',
'WeatherTideBuoy_DeepSeek':'气象浮标：补上风向标尾翼连接臂。',
'SalvageWorkshop_DeepSeek':'废料工坊：补上剪切机底座、后导轨、刀片连接横梁及吊物连接件；将后壁阴影板贴回墙面。',
'ResidentHut_DeepSeek':'居民小屋：补上 4 根窗侧立柱，支承侧墙拼板及窗框。',
'RescueDock_DeepSeek':'救援码头：补上登船梯安装支架、救援艇挡风板支架及方向盘连接柱。',
'Shipyard_DeepSeek':'船坞：增加 6 个连接木块，把上层船板与 3 个肋骨站连接。'}
lines=['# 25 个建筑模型检查与优化','', '日期：2026-10-26。范围以 `Building_Modeling_Progress.md` 的 25 项成品为准，储水设施对应 `WaterStorageTank.blend`；道路套件输出 5 个独立 FBX。','',
'## 已完成','',f'- 游戏 FBX 网格对象：原版 {old_meshes:,} → 优化后 {new_meshes:,}，减少 {(1-new_meshes/old_meshes)*100:.1f}%。修复支承后，可编辑源文件共 {new_source:,} 个零件；游戏导出按材质合并不透明零件。',
'- 透明玻璃保持独立对象，以保留透明表面的排序粒度。Blender 源文件保留可逐件编辑的结构。',
'- 修复档案馆两根薄通风条的 4 个退化面，并限制生成器中薄件的倒角宽度。',
'- 新增 Unity 建筑材质导入器，按 Blender 材质清单恢复 URP 颜色、透明度、金属度、光滑度及发光参数。',
'- 统一优化导出的 FBX 轴向；旧生成器在学校、档案馆、议事厅上使用了不同轴向设置。',
'- 修正若干生成脚本的 Blender 5.2 透明材质 API，以及储水设施的 EEVEE 引擎选择。','', '## 结构修复','']
lines += ['- '+translations[k] for k in fixes]
lines += ['', '## 验证结果','',
'- 25 个源模型的非流形边、松散顶点、退化面均为 0；没有完全重叠的重复网格对象，也没有负缩放对象。',
'- 源模型全部保持原有外包围盒（0.2 mm 容差），最低点均与 Z=0 对齐（2 mm 容差）。',
'- 29 个 FBX 全部通过重导入检查：网格数、三角面数、三角表面位置、材质面数一致；无相机或灯光混入。表面位置核对容差为 0.2 mm。',
'- 使用修复后的源模型与优化 FBX，逐一渲染同机位正、反面，共 100 张图。FBX 对照使用源材质，以独立检查几何与法线；Unity 材质由导入清单处理。',
'- 支承候选检查使用扩大 15 mm 的世界轴对齐包围盒连接图。修复后只剩救援码头的独立水上船体组件；它不应被固定到地面。该检查不能证明任意曲面都物理接触，也不能替代游戏角色通行或完整实体碰撞检查。',
'- 本机没有 Unity，新增 C# 导入器尚未经过 Unity 编译与实机渲染验证；性能收益尚未用帧率测量。', '', '## 每项导出统计','', '| 模型 | 源零件（修复后） | 游戏网格 | 三角面 |', '| --- | ---: | ---: | ---: |']
for asset in assets:
    entries=[x for x in report['exports'] if x['asset']==asset]
    lines.append(f"| {asset} | {sum(x['before']['meshes'] for x in entries)} | {sum(x['after']['meshes'] for x in entries)} | {sum(x['after']['triangles'] for x in entries):,} |")
lines += ['', '## 预览与复现','',
'[正面总览](../Assets/LastLandfall/Art/Reports/BuildingAudit/25_Models_Optimized_Front.jpg) · [背面总览](../Assets/LastLandfall/Art/Reports/BuildingAudit/25_Models_Optimized_Rear.jpg)', '',
'逐模型正反面对照位于 `Assets/LastLandfall/Art/Reports/BuildingAudit/Visuals/`。原始、最终网格报告、FBX 核对报告和支承候选报告都在同一审查目录。', '',
'修改或重新运行单栋建模脚本后，从项目根目录执行以下优化步骤，以免重新产生数百个分散的游戏网格：','',
'```powershell',"& 'D:\\Blender 5.2\\blender.exe' --background --python-exit-code 1 --python Tools/Blender/optimize_building_models.py",'```','',
'`repair_building_structure.py` 用于将本轮已审查的结构修复应用到现有源文件；对应单栋生成器也已包含修复。`audit_building_models.py`、`audit_building_supports.py` 与 `render_building_optimization_review.py` 可复查源文件、连接候选和外观。', '',
'## 其他已发现的接入差异','',
'- 当前游戏菜单中，救援码头及道路的图标使用新版 DeepSeek 资产，实际加载仍指向旧版 `RescueDock` / `Road*`。这些旧版的玩法和道路旋转约定应单独核对后再切换。',
'- 此前温室施工样例来自旧版 `Greenhouse.blend`，本次审核的成品为 `Greenhouse_DeepSeek.blend`。制作这批建筑的完整施工动画时，应以成品源文件建立新序列。']
(ROOT/'Design/Building_Optimization_Report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
for path in (ROOT/'Tools/Blender').glob('*.py'):ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
print('AUDIT_SUMMARY',old_meshes,new_meshes,'ALL_FBX_PASS',report['all_passed'],'MAX_VISUAL_DELTA',max(x['mean_rgb_difference_0_255'] for x in comparisons))
