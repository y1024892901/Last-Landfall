"""Make a compact Chinese review sheet and notes for the three island detail layers."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
PREVIEW=ROOT/'Assets/LastLandfall/Art/Previews/Environment/IslandDetail'
REPORT=ROOT/'Assets/LastLandfall/Art/Reports/IslandDetail'
manifest=json.loads((REPORT/'manifest.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
labels={'Main':'主岛 · 溪岸与林下','West':'西侧副岛 · 碎岩与风化岩台','East':'东侧副岛 · 海岸植被与漂流木'}
canvas=Image.new('RGB',(1440,3*400+80),(23,32,35));d=ImageDraw.Draw(canvas)
d.text((18,13),'三个岛屿细节提升 · 原地形与碰撞保持不变',font=font,fill=(233,238,227))
for row,r in enumerate(manifest['islands']):
 y=80+row*400;key=r['island']
 for col,kind in enumerate(('Before','After','Detail')):
  image=Image.open(PREVIEW/f'{key}_{kind}.png').convert('RGB').resize((480,360),Image.Resampling.LANCZOS)
  canvas.paste(image,(col*480,y))
  d.text((col*480+9,y+362),labels[key]+' · '+{'Before':'提升前','After':'提升后','Detail':'局部细节'}[kind],font=small,fill=(216,230,218))
canvas.save(PREVIEW/'Three_Islands_Before_After.jpg',quality=92)
lines=['# 三个岛屿细节提升','', '本轮修改保留本地，未提交或推送。原 Gate25、Gate26 双岛及沉船源文件、游戏模型均未覆盖；仅新增可重复生成的独立细节图层及自动加载入口。','', '[查看三个岛前后对照与近景](../Assets/LastLandfall/Art/Previews/Environment/IslandDetail/Three_Islands_Before_After.jpg)','', '## 完成内容','', '| 岛屿 | 新增可编辑构件 | 游戏导出网格 | 三角面 | 细节方向 |','| --- | ---: | ---: | ---: | --- |']
themes={'Main':'溪岸湿卵石、苔石、林下蕨叶、落叶、枯枝与岸边漂流木','West':'坡脚碎岩、薄层风化岩台、苔石与稀疏林下植被','East':'海岸漂流木、滩石、低矮海岸植被、坡面碎岩与林下枯枝'}
for r in manifest['islands']:lines.append(f"| {labels[r['island']]} | {r['editable_objects']} | {r['export_meshes']} | {r['triangles']} | {themes[r['island']]} |")
lines += ['',f"合计新增 {sum(r['editable_objects'] for r in manifest['islands'])} 个可编辑构件；游戏中按岛屿和材质合并为 {sum(r['export_meshes'] for r in manifest['islands'])} 个网格、{sum(r['triangles'] for r in manifest['islands'])} 个三角面。此统计是资源规模，不代表实际帧率。",'', '## 布置约束','', '- 在实际地形表面采样并随坡面朝向贴合；碎石与枯木端点分别采样，避免统一放在水平平面。','- 主岛中部原有建设留白、池塘 3.5 米缓冲及溪流中心 0.8 米范围留空。','- 东岛沉船与回收通道按 X=4.5～15.5、Y=27～57 米的保守范围避让。','- 平坦空地不做全面散布；林下只在已有树木周围布置，岩石优先落在坡面，海岸装饰优先布置在水线附近。','- 原树木、竹林、草地、河道和地形碰撞不改变。新增装饰不命名为 terrain source，不参与建造地形采样。','- 新增枯木等为视觉装饰，未新增采集产出或可收集资源逻辑。','', '## 资源与接入','', '- `Art/Source/Environment/IslandDetail_Main.blend`、`IslandDetail_West.blend`、`IslandDetail_East.blend`：只保存可编辑细节，没有重复复制整座岛。','- `Resources/Models/Environment/IslandDetail_*.fbx`：用于游戏的材质合并导出。','- `BuildPlacementPrototype.AddIslandDetailLayers()`：主岛与双岛加载后自动加入细节，禁用细节碰撞体；缺少可选图层时原岛仍可加载。','- `Art/Reports/IslandDetail/manifest.json`：逐岛数量、功能分类、落点与法线。','', '## 重新生成','', '```powershell', '& "D:\\Blender 5.2\\blender.exe" --background --python-exit-code 1 --python Tools/Blender/enrich_island_details.py', 'python Tools/Blender/summarize_island_details.py', '```','', '## 当前查看范围','', '已输出三岛各自的提升前、提升后及近景 Blender 预览。副岛预览展示岛屿与细节层，沉船仍使用原有独立资源在游戏中加载。未运行 Unity 编译、Play Mode 或性能测试；Unity 中的材质、坐标对齐和实际显示负担仍待有环境时查看。','']
(ROOT/'Design/Island_Detail_Enhancement.md').write_text('\n'.join(lines),encoding='utf-8')
print('ISLAND_DETAIL_SUMMARY_COMPLETE')
