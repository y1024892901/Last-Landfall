import bpy,numpy as np
p=r'D:\Last Landfall\work\island_final_candidate\Assets_Generated\LastLandfall_Island_Foliage_Assembly.blend'
bpy.ops.wm.open_mainfile(filepath=p)
o=next(o for o in bpy.data.objects if o.name.startswith('IslandReference_V2'))
arr=np.empty(len(o.data.vertices)*3,dtype='float32')
try:
 o.data.vertices.foreach_get('normal',arr)
 print('vertex_normal_ok',arr[:6].tolist())
except Exception as e: print('vertex_normal_fail',repr(e))
cent=np.empty(len(o.data.polygons)*3,dtype='float32')
try:
 o.data.polygons.foreach_get('center',cent); print('center_ok',cent[:6].tolist())
except Exception as e: print('center_fail',repr(e))
