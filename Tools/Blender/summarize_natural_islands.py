"""Assemble the natural landscape direction review after exporting and reprojecting details."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];BASE=R/'Assets/LastLandfall/Art/Previews/Environment/NaturalIslands';DETAIL=R/'Assets/LastLandfall/Art/Previews/Environment/IslandDetail'
report=json.loads((R/'Assets/LastLandfall/Art/Reports/IslandNatural/manifest.json').read_text(encoding='utf-8'))
details=json.loads((R/'Assets/LastLandfall/Art/Reports/IslandDetail/manifest.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
canvas=Image.new('RGB',(1920,1680),(21,30,29));d=ImageDraw.Draw(canvas)
d.text((18,12),'自然岛屿景观重做 · 参考《纪元1800》的山林与海岸层次',font=font,fill=(237,239,224))
d.text((18,52),'Blender 美术预览；Unity 编译、实机画面与性能尚未验证',font=small,fill=(173,191,172))
for row,key in enumerate(('Main','West','East')):
 for col,(folder,suffix,label) in enumerate(((BASE,'Before','原版'),(DETAIL,'After','新版'),(DETAIL,'Detail','新版近景'))):
  image=Image.open(folder/f'{key}_{suffix}.png').convert('RGB').resize((640,480),Image.Resampling.LANCZOS);x=col*640;y=100+row*520;canvas.paste(image,(x,y));d.text((x+12,y+484),{'Main':'主岛','West':'西侧副岛','East':'东侧副岛'}[key]+' · '+label,font=small,fill=(227,233,218))
canvas.save(BASE/'Natural_Landscape_Review.jpg',quality=93)
lines=['# 自然岛屿景观重做：纪元1800参考方向','', '## 本轮方向','', '此前只增加小石头、枯木和蕨叶，保留了尖峰、简化树冠与硬切的地表材质，整体风格仍显得像灰盒。按照用户指定的《纪元1800》方向，本轮调整山体、树冠、植被疏密与材质过渡，而不是继续单纯增加散布物。','', '[查看三岛原版 / 新版 / 近景对照](../Assets/LastLandfall/Art/Previews/Environment/NaturalIslands/Natural_Landscape_Review.jpg)','', '## 具体改动','', '| 内容 | 本轮处理 |','| --- | --- |','| 山体 | 中高部岩面加入不连续起伏；副岛上部做不对称偏移与高峰压低，减少对称圆锥感。移除会产生梯田条纹的周期高度信号。 |','| 树冠 | 原树木数量、位置和整体体量保留，重建枝干和多簇、非对称树冠，使用更自然的深浅绿。竹林保留原资产。 |','| 草与野花 | 用连续分布场筛出成片区域，减少均匀散点；保留的草花缩短，降低厚重的草刺感。 |','| 地表 | Unity 使用连续坡度、海拔和扰动场混合草地、林下土、岩壁与沙滩，不再以子网格材质边界硬切。 |','| 岩壁 | 添加尺度不同的矿物色差、断裂和微表面凹凸，湿岸按真实水位 -0.92 米处理。 |','| 细节贴地 | 按新地形重新生成上轮独立细节层，避免地形改动后石块、枯木和蕨叶悬空。 |','', '## 生成统计','', '| 资源 | 调整地形顶点 | 重做树木 | 稀疏化草花对象 | 重贴地对象 | 最终导出对象 |','| --- | ---: | ---: | ---: | ---: | ---: |']
for r in report:lines.append(f"| `{r['asset']}` | {r['terrain_vertices_adjusted']} | {r['organic_trees']} | {r['groundcover_hidden']} | {r['reprojected_objects']} | {r['export_objects']} |")
lines += ['',f"三岛合计重做 {sum(r['organic_trees'] for r in report)} 棵树，稀疏化 {sum(r['groundcover_hidden'] for r in report)} 个草花对象。新增独立细节层仍按材质合并，当前共 {sum(r['export_meshes'] for r in details['islands'])} 个网格。这些为资源统计，不代表实际帧率。",'', '## 地形与玩法边界','', '- 海岸低地和主岛中部建设核心区、池塘与河道纳入保护范围；东岛沉船和回收通道沿用保守避让范围。','- 中高部山体采用新版几何；建造网格继续从新版 terrain source 网格生成碰撞，坡地可建造性随新几何计算。','- 岛屿原点、整体尺寸约定、水位及沉船资源保持原有约定；树木与地表装饰按新地形重新贴合。','- 原始 Gate25 / Gate26 模型不覆盖，新的 Natural 资源独立保存。','', '## 游戏接入','', '- 优先加载 `Resources/Models/Environment/IslandReference_Gate25_Natural.fbx`。','- 优先加载 `Resources/Models/Environment/BasinTwinIslands_Natural_v2.fbx`。','- 新资源缺失时回退到原岛屿资源；地表连续混合由 ReferenceIsland.shader 与现有材质加载代码控制。','- 原沉船独立加载；副岛预览只展示岛屿与细节层，没有重复导入沉船。','- 本轮及上轮未提交、未推送，修改保留本地。','', '## 复现','', '```powershell', '& "D:\\Blender 5.2\\blender.exe" --background --python-exit-code 1 --python Tools/Blender/rework_natural_islands.py','& "D:\\Blender 5.2\\blender.exe" --background --python-exit-code 1 --python Tools/Blender/enrich_island_details.py','python Tools/Blender/summarize_island_details.py','python Tools/Blender/summarize_natural_islands.py','```','', '自然版 Blender 源文件保存在 `Art/Source/Environment/`，原始岛屿文件保留。重新做地形后必须重新生成独立细节层。','', '## 当前查看范围','', '已生成 Blender 三岛对照与近景，Unity 着色器和资源加载代码已编写。本机未运行 Unity 编译、Play Mode 或性能测试；Blender 材质仅近似展示 Unity 中的连续地表混合。','', '## 美术参考','', '[Ubisoft《纪元1800》官方页面](https://www.ubisoft.com/en-us/game/anno/1800)。仅参考景观层次方向，未提取或复用该游戏资产。','']
(R/'Design/Island_Natural_Landscape.md').write_text('\n'.join(lines),encoding='utf-8')
p=R/'Design/Island_Detail_Enhancement.md'
s=p.read_text(encoding='utf-8')
if 'Island_Natural_Landscape.md' not in s:s=s.replace('# 三个岛屿细节提升','# 三个岛屿细节提升\n\n后续整体景观已更新为自然版，并重新贴合本页细节层。当前效果与玩法边界见 [自然景观重做](Island_Natural_Landscape.md)。')
p.write_text(s,encoding='utf-8')
print('NATURAL_LANDSCAPE_REVIEW_COMPLETE')
