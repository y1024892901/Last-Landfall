import bpy
from mathutils import Vector
path = r'Assets/LastLandfall/Art/Source/Buildings/SolarPowerStation.blend'
bpy.ops.wm.open_mainfile(filepath=path)
mesh = [o for o in bpy.context.scene.objects if o.type=='MESH']
pts=[o.matrix_world @ Vector(c) for o in mesh for c in o.bound_box]
print('OBJECTS', len(mesh))
print('BOUNDS', tuple(round(max(p[i] for p in pts)-min(p[i] for p in pts),3) for i in range(3)))
print('MIN', tuple(round(min(p[i] for p in pts),3) for i in range(3)))
print('MAX', tuple(round(max(p[i] for p in pts),3) for i in range(3)))
print('COLLECTIONS', [c.name for c in bpy.data.collections])
