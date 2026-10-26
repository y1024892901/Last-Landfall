import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat

root = Path(__file__).resolve().parents[2]
folder = root / 'Assets/LastLandfall/Art/Previews/Construction/Greenhouse'
manifest = json.loads((folder / 'construction_manifest.json').read_text(encoding='utf-8'))
files = [folder / 'frames' / f'frame_{i:04d}.png' for i in range(1, manifest['frame_count'] + 1)]
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18)
small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 14)
cols, cell_w, cell_h = 4, 304, 296
rows = (len(manifest['phases']) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cell_w, rows * cell_h + 52), '#10272b')
draw = ImageDraw.Draw(sheet)
draw.text((16, 12), '温室建造过程 · 18 个工序 / 180 个施工画面', font=font, fill='#ead9b2')
for i, phase in enumerate(manifest['phases']):
    x, y = (i % cols) * cell_w, 52 + (i // cols) * cell_h
    im = Image.open(files[phase['end_frame'] - 1]).convert('RGB').resize((288, 252), Image.Resampling.LANCZOS)
    sheet.paste(im, (x + 8, y))
    draw.text((x + 10, y + 254), f"{i + 1:02d} {phase['display_name_zh']}", font=font, fill='#ead9b2')
    draw.text((x + 10, y + 277), f"帧 {phase['start_frame']}–{phase['end_frame']} · {phase['parts']} 个零件", font=small, fill='#9ab4b4')
sheet.save(folder / 'Greenhouse_Construction_Stages.png')
strip_w, strip_h = 192, 216
all_frames = Image.new('RGB', (manifest['frames_per_phase'] * strip_w, len(manifest['phases']) * strip_h), '#10272b')
all_draw = ImageDraw.Draw(all_frames)
for row, phase in enumerate(manifest['phases']):
    y = row * strip_h
    all_draw.text((8, y + 2), f"{row + 1:02d} {phase['display_name_zh']}", font=font, fill='#ead9b2')
    for col, number in enumerate(range(phase['start_frame'], phase['end_frame'] + 1)):
        thumb = Image.open(files[number - 1]).convert('RGB').resize((192, 168), Image.Resampling.LANCZOS)
        all_frames.paste(thumb, (col * strip_w, y + 26))
        all_draw.text((col * strip_w + 8, y + 196), f'{number:03d}', font=small, fill='#9ab4b4')
all_frames.save(folder / 'Greenhouse_Construction_All_Frames.jpg', quality=92)
frames = [Image.open(p).convert('RGB').resize((480, 420), Image.Resampling.LANCZOS) for p in files]
palette_sample = Image.new('RGB', (120 * 8, 105 * ((len(frames) + 7) // 8)))
for i, frame in enumerate(frames):
    palette_sample.paste(frame.resize((120, 105), Image.Resampling.LANCZOS), ((i % 8) * 120, (i // 8) * 105))
palette = palette_sample.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
indexed = [frame.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG) for frame in frames]
indexed[0].save(folder / 'Greenhouse_Construction.gif', save_all=True, append_images=indexed[1:], duration=[80 if i % 3 else 90 for i in range(len(indexed))], loop=0, optimize=False, disposal=2)
identical = []
phase_diffs = []
# Exclude the phase caption so a changed label cannot hide a static model.
images = [Image.open(p).convert('RGB').crop((0, 0, 768, 570)) for p in files]
for i in range(1, len(images)):
    if ImageChops.difference(images[i-1], images[i]).getbbox() is None:
        identical.append([i, i + 1])
for phase in manifest['phases']:
    diffs = []
    for i in range(phase['start_frame'], phase['end_frame']):
        diffs.append(sum(ImageStat.Stat(ImageChops.difference(images[i-1], images[i])).mean) / 3)
    phase_diffs.append({'phase': phase['phase'], 'parts': phase['parts'], 'min_pixel_difference': round(min(diffs), 6), 'mean_pixel_difference': round(sum(diffs)/len(diffs), 6)})
report = {'frame_count':len(files), 'identical_adjacent_model_frames':identical, 'phases':phase_diffs}
(folder / 'frame_difference_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
