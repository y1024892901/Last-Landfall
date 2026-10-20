import bpy
from mathutils import Vector

SCENE = r"D:\Last Landfall\work\island_final_candidate\Assets_Generated\LastLandfall_Island_GrassCoverage_Gate24.blend"
OUTPUT = r"D:\Last Landfall\work\island_final_candidate\Previews_Generated\Gate24_Basin_Closeup.png"
bpy.ops.wm.open_mainfile(filepath=SCENE)
scene = bpy.context.scene
camera = scene.camera
camera.data.type = "ORTHO"
camera.data.ortho_scale = 34.0
camera.location = (33.0, -42.0, 32.0)
target = Vector((2.0, -2.0, 0.8))
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
scene.render.resolution_x = 1500
scene.render.resolution_y = 1125
scene.render.resolution_percentage = 100
scene.render.filepath = OUTPUT
bpy.ops.render.render(write_still=True)



