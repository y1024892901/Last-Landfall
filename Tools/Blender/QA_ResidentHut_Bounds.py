import bpy
from mathutils import Vector

blend_path = r'Assets/LastLandfall/Art/Source/Buildings/ResidentHut_DeepSeek.blend'
bpy.ops.wm.open_mainfile(filepath=blend_path)
coll = bpy.data.collections.get('ResidentHut_DeepSeek')
rows = []
for obj in coll.all_objects:
    if obj.type != 'MESH':
        continue
    pts = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    mins = [min(p[i] for p in pts) for i in range(3)]
    maxs = [max(p[i] for p in pts) for i in range(3)]
    rows.append((mins[2], maxs[2], obj.name, mins[0], maxs[0], mins[1], maxs[1]))
print('OBJECTS', len(rows))
print('LOWEST 12:')
for row in sorted(rows)[:12]: print(row)
print('HIGHEST 12:')
for row in sorted(rows, key=lambda x:x[1], reverse=True)[:12]: print(row)
