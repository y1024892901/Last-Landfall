# -*- coding: utf-8 -*-
"""Render an isometric concept preview demonstrating the 'Companion Puff Grass' solution.

- Clean flat open lawn for buildings and paths
- Zero grass on dirt / mud terrain
- Soft, broad-leaf puffed grass clumps & wildflowers clustered naturally around rocks & tree bases
"""
import math
import random
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector, Euler

OUTPUT_PATH = Path(r"C:\Users\10248\.gemini\antigravity\brain\4ad83460-d785-4579-a7a3-3ed6438c0b0b\grass_style_preview.png")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# 1. Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for block in bpy.data.meshes: bpy.data.meshes.remove(block)
for block in bpy.data.materials: bpy.data.materials.remove(block)

# 2. Materials
def make_mat(name, color, roughness=0.85):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
    return mat

mat_lawn = make_mat("Lawn", (0.32, 0.48, 0.22))
mat_dirt = make_mat("DirtPath", (0.35, 0.28, 0.18))
mat_rock = make_mat("Rock", (0.42, 0.44, 0.42))
mat_tree_bark = make_mat("TreeBark", (0.28, 0.20, 0.14))
mat_tree_leaf = make_mat("TreeLeaf", (0.22, 0.40, 0.18))
mat_grass_blade = make_mat("GrassBlade", (0.45, 0.65, 0.25))
mat_grass_tip = make_mat("GrassTip", (0.65, 0.78, 0.32))
mat_flower_petal = make_mat("FlowerPetal", (0.95, 0.95, 0.88))
mat_flower_center = make_mat("FlowerCenter", (0.95, 0.75, 0.15))

# 3. Ground Terrain
# Main grass lawn
bpy.ops.mesh.primitive_cylinder_add(radius=5.5, depth=0.4, vertices=32, location=(0, 0, -0.2))
ground = bpy.context.active_object
ground.name = "GroundLawn"
ground.data.materials.append(mat_lawn)

# Dirt / Mud Patch (zero grass zone)
bpy.ops.mesh.primitive_cylinder_add(radius=2.0, depth=0.41, vertices=16, location=(-2.2, -1.8, -0.19))
dirt = bpy.context.active_object
dirt.name = "DirtPatch"
dirt.scale = (1.5, 0.9, 1.0)
dirt.data.materials.append(mat_dirt)

# 4. Stylized Tree & Rocks
# Stylized Rock
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.1, location=(1.8, 1.2, 0.5))
rock = bpy.context.active_object
rock.name = "StylizedRock"
rock.scale = (1.2, 0.9, 0.7)
rock.rotation_euler = (0.2, 0.4, 0.6)
rock.data.materials.append(mat_rock)

# Smaller accent rock
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.6, location=(2.6, 0.2, 0.25))
rock2 = bpy.context.active_object
rock2.scale = (1.1, 0.8, 0.6)
rock2.data.materials.append(mat_rock)

# Stylized Tree Trunk & Foliage
bpy.ops.mesh.primitive_cylinder_add(radius=0.28, depth=2.4, vertices=8, location=(-1.2, 1.8, 1.2))
trunk = bpy.context.active_object
trunk.data.materials.append(mat_tree_bark)

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.5, location=(-1.2, 1.8, 2.8))
tree_crown = bpy.context.active_object
tree_crown.scale = (1.1, 1.0, 1.2)
tree_crown.data.materials.append(mat_tree_leaf)

# 5. Build Soft, Broad-Leaf Puffed Grass Clump (with Spherical Normals)
def create_puffed_grass_clump(name, loc, scale=1.0, rot_z=0.0):
    bm = bmesh.new()
    blade_count = 6
    for b in range(blade_count):
        ang = (b / blade_count) * math.pi * 2.0 + (0.3 if b % 2 == 0 else -0.2)
        dir_out = Vector((math.cos(ang), math.sin(ang), 0.0))
        dir_side = Vector((-math.sin(ang), math.cos(ang), 0.0))

        h = 0.55 * (0.85 + (b % 3) * 0.15)
        w = 0.08
        r = 0.08

        v0 = bm.verts.new(dir_out * r - dir_side * w * 0.5)
        v1 = bm.verts.new(dir_out * r + dir_side * w * 0.5)

        # Curved outward
        mid_pos = dir_out * (r + 0.14) + Vector((0, 0, h * 0.52))
        v2 = bm.verts.new(mid_pos - dir_side * w * 0.38)
        v3 = bm.verts.new(mid_pos + dir_side * w * 0.38)

        # Soft bending tip
        tip_pos = dir_out * (r + 0.28) + Vector((0, 0, h * 0.88))
        v4 = bm.verts.new(tip_pos)

        bm.faces.new([v0, v1, v3, v2])
        bm.faces.new([v2, v3, v4])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    # Smooth normals
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.scale = (scale, scale, scale)
    obj.rotation_euler = (0, 0, rot_z)
    obj.data.materials.append(mat_grass_blade)
    return obj

# 6. Add Little Daisy / Wildflower Clump
def add_daisy(loc):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.10, depth=0.03, vertices=8, location=loc + Vector((0, 0, 0.42)))
    center = bpy.context.active_object
    center.data.materials.append(mat_flower_center)
    for p in range(5):
        ang = p * (math.pi * 2.0 / 5)
        petal_loc = loc + Vector((math.cos(ang) * 0.13, math.sin(ang) * 0.13, 0.41))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.02, vertices=6, location=petal_loc)
        petal = bpy.context.active_object
        petal.data.materials.append(mat_flower_petal)

# 7. Place Puffed Grass ONLY around Rock & Tree Base (Companion Scattering)
rng = random.Random(42)

# Around Rock (1.8, 1.2)
rock_center = Vector((1.8, 1.2, 0.0))
for i in range(7):
    ang = i * (math.pi * 2.0 / 7) + rng.uniform(-0.2, 0.2)
    dist = rng.uniform(1.0, 1.6)
    pos = rock_center + Vector((math.cos(ang) * dist, math.sin(ang) * dist * 0.85, 0.0))
    create_puffed_grass_clump(f"RockGrass_{i}", pos, scale=rng.uniform(0.9, 1.3), rot_z=rng.uniform(0, 6.28))

add_daisy(rock_center + Vector((-0.7, -0.6, 0.0)))
add_daisy(rock_center + Vector((0.8, -0.8, 0.0)))

# Around Tree Base (-1.2, 1.8)
tree_center = Vector((-1.2, 1.8, 0.0))
for i in range(6):
    ang = i * (math.pi * 2.0 / 6) + rng.uniform(-0.25, 0.25)
    dist = rng.uniform(0.65, 1.3)
    pos = tree_center + Vector((math.cos(ang) * dist, math.sin(ang) * dist, 0.0))
    create_puffed_grass_clump(f"TreeGrass_{i}", pos, scale=rng.uniform(0.85, 1.2), rot_z=rng.uniform(0, 6.28))

add_daisy(tree_center + Vector((0.6, -0.5, 0.0)))

# Notice: THE DIRT PATCH (-2.2, -1.8) HAS ZERO GRASS!
# Notice: THE MAIN CENTRAL LAWN (0, 0) HAS ZERO 3D GRASS (RESERVED FOR BUILDINGS/ROADS)!

# 8. Lighting & Camera (Isometric RTS View)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT" if hasattr(bpy.types, "RenderSettings") and "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_WORKBENCH"
scene.render.resolution_x = 1280
scene.render.resolution_y = 760
scene.render.filepath = str(OUTPUT_PATH)
scene.render.film_transparent = False

# Workbench setup for crisp stylized rendering
if scene.render.engine == "BLENDER_WORKBENCH":
    scene.display.shading.light = "STUDIO"
    scene.display.shading.studio_light = "paint.sl"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.curvature_ridge_factor = 1.2
    scene.display.shading.curvature_valley_factor = 0.9

# Sun Light
light_data = bpy.data.lights.new("Sun", type="SUN")
light_data.energy = 3.5
light = bpy.data.objects.new("Sun", light_data)
bpy.context.collection.objects.link(light)
light.rotation_euler = (math.radians(50), math.radians(25), math.radians(-40))

# Orthographic Isometric Camera
cam_data = bpy.data.cameras.new("IsoCam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 8.5
cam = bpy.data.objects.new("IsoCam", cam_data)
bpy.context.collection.objects.link(cam)

cam.location = Vector((8.5, -8.5, 7.5))
look_at = Vector((0.0, 0.2, 0.4))
cam.rotation_euler = (look_at - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

# 9. Render
bpy.ops.render.render(write_still=True)
print(f"RENDERED PREVIEW TO {OUTPUT_PATH}")
