"""Render stage endpoints from saved construction timelines without changing them."""
from pathlib import Path
import bpy,json,sys
ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'Assets/LastLandfall/Art/Reports/Construction'
PREVIEW=ROOT/'Assets/LastLandfall/Art/Previews/Construction/Detailed'
records=json.loads((REPORT/'catalog.json').read_text(encoding='utf-8'))
start=next((int(v.split('=',1)[1]) for v in sys.argv if v.startswith('--start-index=')),0)
end=next((int(v.split('=',1)[1]) for v in sys.argv if v.startswith('--end-index=')),len(records))
records=records[start:end]
for record in records:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/record['blend']))
    scene=bpy.context.scene;scene.render.resolution_x=384;scene.render.resolution_y=384
    if hasattr(scene,'eevee'):scene.eevee.taa_render_samples=16
    out=PREVIEW/record['clip'];out.mkdir(parents=True,exist_ok=True)
    for i,phase in enumerate(record['phases'],1):
        target=out/f'{i:02d}.png'
        if target.exists():continue
        scene.frame_set(phase['end']);scene.render.filepath=str(target)
        bpy.ops.render.render(write_still=True)
    print('CONSTRUCTION_PREVIEW_COMPLETE',record['clip'],flush=True)
