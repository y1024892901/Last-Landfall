"""Package the 25-model detail pass into visual comparisons and a report."""
from pathlib import Path
import json,ast
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'Assets/LastLandfall/Art/Reports/BuildingDetail'
read=lambda name:json.loads((R/name).read_text(encoding='utf-8'))
manifest=read('detail_manifest.json');audit=read('source_audit.json');exports=read('optimization_report.json');supports=read('support_candidates.json')
baseline=json.loads((ROOT/'Assets/LastLandfall/Art/Reports/BuildingAudit/source_audit.json').read_text(encoding='utf-8'))
order=[x['asset'] for x in baseline];index={m['asset']:m for m in manifest};manifest=[index[a] for a in order]
assert len(manifest)==25 and exports['all_passed'] and len(exports['exports'])==29
assert not any(a['mesh_issues'] for a in audit)
assert all(not s['disconnected_bounds_groups'] for s in supports if s['asset']!='RescueDock_DeepSeek')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
names={
'Archive_DeepSeek':'档案馆','CouncilHall_DeepSeek':'议事厅','DesalinationPlant_DeepSeek':'海水淡化装置','Forge_DeepSeek':'锻造炉','Greenhouse_DeepSeek':'温室',
'LocalCommunicationsCenter_DeepSeek':'初始通讯中心','MedicalStation_DeepSeek':'医疗站','MedicalTent_DeepSeek':'医疗帐篷','PublicKitchen_DeepSeek':'公共厨房',
'RescueOutpost_DeepSeek':'救援前哨','RescueRadioCenter_DeepSeek':'长距通讯站','ResearchStation_DeepSeek':'研究站','ResidentHut_DeepSeek':'居民小屋',
'SalvageWorkshop_DeepSeek':'废料拆解工坊','School_DeepSeek':'学校','SolarPowerStation_DeepSeek':'太阳能发电站','StorageDepot_DeepSeek':'仓库','WoodShelter_DeepSeek':'木棚',
'DirtRoadTiles_DeepSeek':'五种土路模块','DriftwoodCollectionBoom_DeepSeek':'漂木收集浮栅','FishingDock_DeepSeek':'渔船码头','RescueDock_DeepSeek':'救援码头',
'Shipyard_DeepSeek':'船坞','WeatherTideBuoy_DeepSeek':'气象潮位浮标','WaterStorageTank':'储水设施'}
for view in ['Front','Rear']:
    sheet=Image.new('RGB',(1600,1800),'#20282b');draw=ImageDraw.Draw(sheet)
    for i,m in enumerate(manifest):
        thumb=Image.open(R/'Visuals'/m['asset']/f'After_{view}.png').convert('RGB').resize((320,320),Image.Resampling.LANCZOS)
        x,y=(i%5)*320,(i//5)*360;sheet.paste(thumb,(x,y));draw.text((x+8,y+324),names[m['asset']],font=font,fill='#ead9b2')
        draw.text((x+8,y+345),f"新增 {m['added_objects']} 个细节零件",font=small,fill='#acbfc1')
    sheet.save(R/f'25_Models_Detail_{view}.jpg',quality=93)
comparison=Image.new('RGB',(2560,1500),'#20282b');draw=ImageDraw.Draw(comparison)
for i,m in enumerate(manifest):
    folder=R/'Visuals'/m['asset'];x,y=(i%5)*512,(i//5)*300
    pair=Image.new('RGB',(1280,728),'#20282b');pd=ImageDraw.Draw(pair)
    for col,variant in enumerate(['Before','After']):
        image=Image.open(folder/f'{variant}_Front.png').convert('RGB')
        comparison.paste(image.resize((256,256),Image.Resampling.LANCZOS),(x+col*256,y+22))
        pair.paste(image,(col*640,30));pd.text((col*640+12,6),'细节提升前' if col==0 else '细节提升后',font=font,fill='#ead9b2')
    draw.text((x+8,y+2),names[m['asset']]+'   原版 → 细节版',font=small,fill='#ead9b2')
    draw.text((x+8,y+280),' / '.join(m['features_zh'])[:34],font=small,fill='#acbfc1')
    pd.text((12,678),names[m['asset']]+'：'+' / '.join(m['features_zh']),font=font,fill='#ead9b2')
    pair.save(folder/'Before_After_Comparison.jpg',quality=93)
comparison.save(R/'25_Models_Before_After.jpg',quality=93)
old_tri=sum(x['evaluated_triangles'] for x in baseline);new_tri=sum(x['after']['triangles'] for x in exports['exports']);new_mesh=sum(x['after']['meshes'] for x in exports['exports']);added=sum(m['added_objects'] for m in manifest)
lines=['# 25 个建筑模型细节提升','', '本轮在结构优化后的成品上补充与用途相符的可编辑几何细节。原有模型保持完整，新增部分分组于每栋模型的 `<资产名>_DetailPass` 子集合，零件带用途和依附对象标记。','',
'## 结果','',f'- 完成 25 / 25 项资产，共增加 {added} 个可编辑细节零件。',
f'- 游戏导出仍为 {new_mesh} 个网格对象；不透明细节复用原材质并合并，透明窗格保留原有排序粒度。',
f'- 全套三角面：{old_tri:,} → {new_tri:,}，增加 {(new_tri/old_tri-1)*100:.1f}%。',
'- 已更新全部 25 张建筑图标，以及 29 个 FBX（道路套件对应 5 个独立模块）。','',
'## 逐项内容','', '| 模型 | 新增零件 | 细节内容 |','| --- | ---: | --- |']
for m in manifest:lines.append(f"| {names[m['asset']]} | {m['added_objects']} | {'；'.join(m['features_zh'])} |")
lines += ['', '## 检查','',
'- 25 个源模型均无非流形边、松散顶点及退化面；29 个 FBX 的几何、材质面数与重导入核对全部通过。',
'- 新物件依附于现有地板、墙面、柜体和支架。修正了学校书本托盘的边缘位置；道路碎石位于模块内部路肩，保留拼接口。',
'- 支承候选检查使用 15 mm 包围盒邻接容差，最终只剩原有救援艇水上独立组件；该检查不能代替完整实体碰撞或角色通行测试。',
'- 已渲染 100 张正反面对照图，新增细节可按模型逐一对照。Unity 实机效果和帧率尚未验证。','',
'## 查看','',
'[正面总览](../Assets/LastLandfall/Art/Reports/BuildingDetail/25_Models_Detail_Front.jpg) · [背面总览](../Assets/LastLandfall/Art/Reports/BuildingDetail/25_Models_Detail_Rear.jpg) · [25 项前后对照](../Assets/LastLandfall/Art/Reports/BuildingDetail/25_Models_Before_After.jpg)','',
'逐模型原图、前后对照及 JSON 报告位于 `Assets/LastLandfall/Art/Reports/BuildingDetail/`。','',
'## 重新生成','',
'从项目根目录依次运行细节生成、优化导出与渲染。细节脚本会替换自己的子集合，重复运行不会叠加同一批细节。原版源文件在本机 `work/BuildingDetail_Before/Source/` 备份，也可从上一提交恢复。','',
'```powershell',
"& 'D:\\Blender 5.2\\blender.exe' --background --python-exit-code 1 --python Tools/Blender/enrich_building_details.py",
"& 'D:\\Blender 5.2\\blender.exe' --background --python-exit-code 1 --python Tools/Blender/optimize_building_models.py -- --report-dir Assets/LastLandfall/Art/Reports/BuildingDetail",
"& 'D:\\Blender 5.2\\blender.exe' --background --python-exit-code 1 --python Tools/Blender/render_building_detail_review.py -- --update-icons",'```','',
'修改单栋源模型或重新运行其原始生成器后，需重新应用细节生成步骤。此轮没有切换游戏里仍在使用的旧版码头、道路及温室施工样例。']
(ROOT/'Design/Building_Detail_Enhancement_Report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
for p in (ROOT/'Tools/Blender').glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
print('DETAIL_SUMMARY',len(manifest),'assets',added,'new_parts',new_mesh,'game_meshes',old_tri,'->',new_tri,'triangles')
