"""Assemble Chinese-labelled construction phase overview sheets from rendered PNGs."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'Assets/LastLandfall/Art/Reports/Construction'
OUT=ROOT/'Assets/LastLandfall/Art/Previews/Construction/Detailed'
font_path='C:/Windows/Fonts/msyh.ttc'
font=ImageFont.truetype(font_path,16);small=ImageFont.truetype(font_path,13);heading=ImageFont.truetype(font_path,23)
records=json.loads((REPORT/'catalog.json').read_text(encoding='utf-8'))
ROAD_NAMES={'DirtRoadStraight_DeepSeek':'土路 · 直路','DirtRoadCorner_DeepSeek':'土路 · 弯道','DirtRoadTee_DeepSeek':'土路 · T形路口','DirtRoadCross_DeepSeek':'土路 · 十字路口','DirtRoadEnd_DeepSeek':'土路 · 封闭端'}
complete=[]
for record in records:
    folder=OUT/record['clip'];phases=record['phases']
    if not all((folder/f'{i:02d}.png').exists() for i in range(1,len(phases)+1)):continue
    w=256;h=300;cols=4;rows=math.ceil(len(phases)/cols)
    sheet=Image.new('RGB',(w*cols,70+h*rows),(22,29,33));draw=ImageDraw.Draw(sheet)
    draw.text((18,12),ROAD_NAMES.get(record['clip'],record['name']),font=heading,fill=(237,240,233))
    draw.text((18,43),f"{len(phases)} 个阶段 / {record['objects']} 件 / {record['frames']} 帧 @ 24 fps",font=small,fill=(153,189,185))
    for idx,phase in enumerate(phases):
        x=(idx%cols)*w;y=70+(idx//cols)*h
        pic=Image.open(folder/f'{idx+1:02d}.png').convert('RGB').resize((256,256),Image.Resampling.LANCZOS)
        sheet.paste(pic,(x,y));draw.text((x+8,y+257),f"{idx+1:02d}  {phase['title']}",font=font,fill=(235,240,233))
        draw.text((x+8,y+279),f"帧 {phase['start']}–{phase['end']}  ·  {len(phase['parts'])} 件",font=small,fill=(153,189,185))
    sheet.save(folder/'Overview.jpg',quality=90)
    complete.append(record)
if len(complete)==len(records):
    w=256;h=304;cols=5
    master=Image.new('RGB',(w*cols,80+h*math.ceil(len(records)/cols)),(22,29,33));d=ImageDraw.Draw(master)
    d.text((18,14),'全建筑施工序列 · 25 套资产 / 29 条序列',font=heading,fill=(237,240,233))
    d.text((18,49),f"共 {sum(len(r['phases']) for r in records)} 阶段 / {sum(r['frames'] for r in records):,} 可播放帧",font=font,fill=(153,189,185))
    for idx,r in enumerate(records):
        x=(idx%cols)*w;y=80+(idx//cols)*h
        # Mid-construction view makes structural differences readable.
        n=len(r['phases']) if r['clip'] in ROAD_NAMES else max(1,len(r['phases'])//2)
        pic=Image.open(OUT/r['clip']/f'{n:02d}.png').convert('RGB').resize((256,256),Image.Resampling.LANCZOS)
        master.paste(pic,(x,y));d.text((x+7,y+257),ROAD_NAMES.get(r['clip'],r['name'])[:15],font=font,fill=(235,240,233))
        d.text((x+7,y+281),f"{len(r['phases'])} 阶段 · {r['frames']} 帧",font=small,fill=(153,189,185))
    master.save(OUT/'All_Construction_Overview.jpg',quality=92)
print('OVERVIEWS_COMPLETE',len(complete),'/',len(records))
