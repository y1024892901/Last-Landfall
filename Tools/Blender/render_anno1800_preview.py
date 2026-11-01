# -*- coding: utf-8 -*-
"""Render an Anno 1800 Style Environment Vegetation Showcase.

Key characteristics:
1. Open flat meadow for building / farming / roads (Zero protruding spikes or needle fuzz).
2. Clean dirt road with zero weeds.
3. Natural Dense Foliage Clusters along forest borders & rock bases:
   - Tall slender seed grass & reeds
   - Dense leafy grass tufts
   - Low-lying broadleaf ferns
   - Tiny white clover & wild flower patches
   All clustered tightly together in organic, rich, layered mounds.
"""
import math
import random
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector, Euler

OUTPUT_PATH = Path(r"C:\Users\10248\.gemini\antigravity\brain\4ad83460-d785-4579-a7a3-3ed6438c0b0b\anno1800_style_preview.png")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# 1. Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for block in bpy.data.meshes: bpy.data.meshes.remove(block)
for block in bpy.data.materials: bpy.data.materials.remove(block)

# 2. Materials (Anno 1800 European Temperate Palette)
def make_mat(name, color, roughness=0.88):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
    return mat

mat_lawn = make_mat("Anno_Lawn", (0.28, 0.42, 0.18))
mat_dirt = make_mat("Anno_DirtPath", (0.36, 0.30, 0.20))
mat_rock = make_mat("Anno_Rock", (0.42, 0.43, 0.40))
mat_tree_bark = make_mat("Anno_Bark", (0.24, 0.18, 0.14))
mat_tree_canopy = make_mat("Anno_Canopy", (0.20, 0.35, 0.16))

# Foliage cluster elements
mat_tall_grass = make_mat("Anno_TallGrass", (0.42, 0.54, 0.22))
mat_seed_head = make_mat("Anno_SeedHead", (0.62, 0.58, 0.36))
mat_low_grass = make_mat("Anno_LowGrass", (0.32, 0.48, 0.19))
mat_fern = make_mat("Anno_Fern", (0.22, 0.38, 0.16))
mat_clover = make_mat("Anno_Clover", (0.36, 0.52, 0.20))
mat_white_flower = make_mat("Anno_Flower", (0.94, 0.94, 0.90))

# 3. Ground Base
bpy.ops.mesh.primitive_cylinder_add(radius=7.0, depth=0.4, vertices=48, location=(0, 0, -0.2))
ground = bpy.context.active_object
ground.name = "Anno_Ground"
ground.data.materials.append(mat_lawn)

# Dirt Road Cutting through (Anno 1800 cart path)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-1.2, -0.8, -0.19))
road = bpy.context.active_object
road.name = "Anno_CartRoad"
road.scale = (1.4, 12.0, 0.41)
road.rotation_euler = (0, 0, math.radians(28))
road.data.materials.append(mat_dirt)

# 4. Forest & Rocky Hill on the Right / Rear
# Rocky outcrops
rock_positions = [(2.8, 1.4, 0.6), (3.6, 0.2, 0.4), (2.1, 2.5, 0.8), (4.2, 1.8, 0.9)]
for idx, (rx, ry, rz) in enumerate(rock_positions):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(rx, ry, rz))
    r_obj = bpy.context.active_object
    r_obj.scale = (1.1, 0.9, 0.7)
    r_obj.rotation_euler = (0.2 * idx, 0.4 * idx, 0.6 * idx)
    r_obj.data.materials.append(mat_rock)

# Temperate Trees (Pine & Broadleaf mix)
tree_positions = [(3.2, 3.2), (4.5, 2.6), (1.5, 4.2), (4.0, 4.5)]
for idx, (tx, ty) in enumerate(tree_positions):
    # Trunk
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=3.2, vertices=8, location=(tx, ty, 1.6))
    trunk = bpy.context.active_object
    trunk.data.materials.append(mat_tree_bark)
    # Dense Canopy
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.6, location=(tx, ty, 3.8))
    canopy = bpy.context.active_object
    canopy.scale = (1.1, 1.0, 1.3)
    canopy.data.materials.append(mat_tree_canopy)

# 5. Build Anno 1800 Style Foliage Elements
# A) Tall Seed Grass (Slender stems with golden wheat-like seed heads)
def add_seed_grass(loc, scale=1.0, count=7):
    rng = random.Random(int(loc.x * 100 + loc.y))
    for i in range(count):
        ang = rng.uniform(0, 6.28)
        lean = rng.uniform(0.15, 0.35)
        h = 1.1 * scale * rng.uniform(0.85, 1.25)
        stem_loc = loc + Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0.0))
        # Stem
        bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=h, vertices=5, location=stem_loc + Vector((0, 0, h*0.5)))
        stem = bpy.context.active_object
        stem.rotation_euler = (math.sin(ang) * lean, math.cos(ang) * lean, ang)
        stem.data.materials.append(mat_tall_grass)
        # Golden Seed Head at top
        head_loc = stem_loc + Vector((math.sin(ang)*lean*h, math.cos(ang)*lean*h, h * 0.95))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.038, depth=0.28 * scale, vertices=6, location=head_loc)
        head = bpy.context.active_object
        head.rotation_euler = stem.rotation_euler
        head.data.materials.append(mat_seed_head)

# B) Broadleaf Fern (Curving fronds spreading outwards)
def add_fern(loc, scale=1.0):
    frond_count = 5
    for f in range(frond_count):
        ang = f * (math.pi * 2.0 / frond_count) + 0.2
        dir_out = Vector((math.cos(ang), math.sin(ang), 0.0))
        frond_len = 0.65 * scale
        frond_loc = loc + dir_out * (frond_len * 0.45) + Vector((0, 0, 0.18))
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=frond_loc)
        leaf = bpy.context.active_object
        leaf.scale = (frond_len * 0.5, 0.14 * scale, 0.02)
        leaf.rotation_euler = (0.25 * math.sin(ang), -0.25 * math.cos(ang), ang)
        leaf.data.materials.append(mat_fern)

# C) Low-lying dense green grass patch (Soft organic clump)
def add_dense_low_grass(loc, scale=1.0):
    for i in range(8):
        ang = i * (math.pi * 2.0 / 8) + 0.15
        dir_out = Vector((math.cos(ang), math.sin(ang), 0.0))
        blade_len = 0.42 * scale
        blade_loc = loc + dir_out * 0.12 + Vector((0, 0, blade_len * 0.45))
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=blade_loc)
        blade = bpy.context.active_object
        blade.scale = (0.04, 0.10 * scale, blade_len * 0.5)
        blade.rotation_euler = (0.35 * math.sin(ang), -0.35 * math.cos(ang), ang)
        blade.data.materials.append(mat_low_grass)

# D) Little White Clover / Wildflower tuft
def add_clover_flowers(loc, count=4):
    for c in range(count):
        cl_loc = loc + Vector((random.uniform(-0.35, 0.35), random.uniform(-0.35, 0.35), 0.08))
        bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.03, vertices=5, location=cl_loc)
        flower = bpy.context.active_object
        flower.data.materials.append(mat_white_flower)

# E) COMPOSITE ANNO 1800 CLUSTER (All species packed tightly in a 1.5m organic clump)
def spawn_anno_cluster(center_pos, scale=1.0):
    # Tall seed grass at core
    add_seed_grass(center_pos + Vector((0.0, 0.1, 0.0)), scale=scale, count=9)
    # Ferns spreading on flanks
    add_fern(center_pos + Vector((-0.45, -0.2, 0.0)), scale=scale * 1.1)
    add_fern(center_pos + Vector((0.40, -0.15, 0.0)), scale=scale * 0.95)
    # Dense low grass bedding
    add_dense_low_grass(center_pos + Vector((0.15, -0.35, 0.0)), scale=scale)
    add_dense_low_grass(center_pos + Vector((-0.25, 0.30, 0.0)), scale=scale * 0.85)
    # Ground clovers & white wildflowers weaving through
    add_clover_flowers(center_pos, count=6)

# 6. Scatter Foliage ONLY in Forest Borders & Rock Edges (The Anno 1800 Way!)
# Cluster 1: Hugging the main rock base
spawn_anno_cluster(Vector((2.0, 0.9, 0.0)), scale=1.1)
# Cluster 2: Tucked between rock and tree
spawn_anno_cluster(Vector((2.6, 2.2, 0.0)), scale=1.2)
# Cluster 3: Forest line fringe
spawn_anno_cluster(Vector((1.1, 3.2, 0.0)), scale=0.95)
# Cluster 4: Wild rock corner
spawn_anno_cluster(Vector((3.8, 0.8, 0.0)), scale=1.05)
# Cluster 5: Background woodland understory
spawn_anno_cluster(Vector((3.4, 4.0, 0.0)), scale=1.25)

# Notice: THE CART ROAD (-1.2, -0.8) HAS ZERO WEEDS / CLEAN DIRT!
# Notice: THE MAIN BUILDING MEADOW (Left side: -3.5 to -0.5) IS CLEAN, FLAT, BEAUTIFUL TURF!

# 7. Cinematic RTS Camera (Anno 1800 Ortho Perspective)
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.filepath = str(OUTPUT_PATH)
scene.render.film_transparent = False

scene.display.shading.light = "STUDIO"
scene.display.shading.studio_light = "paint.sl"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.curvature_ridge_factor = 1.3
scene.display.shading.curvature_valley_factor = 0.85

# Lighting
light_data = bpy.data.lights.new("Sun", type="SUN")
light_data.energy = 3.8
light = bpy.data.objects.new("Sun", light_data)
bpy.context.collection.objects.link(light)
light.rotation_euler = (math.radians(52), math.radians(20), math.radians(-42))

# Isometric RTS Camera (Matching Anno 1800 classic overview)
cam_data = bpy.data.cameras.new("AnnoCamera")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 9.8
cam = bpy.data.objects.new("AnnoCamera", cam_data)
bpy.context.collection.objects.link(cam)

cam.location = Vector((9.8, -10.2, 8.8))
look_at = Vector((0.4, 0.8, 0.5))
cam.rotation_euler = (look_at - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

# 8. Render
bpy.ops.render.render(write_still=True)
print(f"ANNO 1800 SHOWCASE RENDERED TO: {OUTPUT_PATH}")
