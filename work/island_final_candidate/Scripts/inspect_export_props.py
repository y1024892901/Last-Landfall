import bpy
p=bpy.ops.export_scene.fbx.get_rna_type().properties
print('embed_textures', 'embed_textures' in p.keys())
print('path_mode', p['path_mode'].enum_items.keys())
print([x.identifier for x in p])
