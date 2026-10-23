import bpy
import bmesh
import math
import random
import json
from mathutils import Vector
from pathlib import Path

# ==========================================
# 1. Setup and Path Management
# ==========================================
scene = bpy.context.scene
initial_selection = list(bpy.context.selected_objects)
initial_active = bpy.context.view_layer.objects.active
initial_object_render_visibility = {obj: obj.hide_render for obj in scene.objects}

PROJECT_ROOT = Path.cwd()
BLEND_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/Infrastructure"
FBX_DIR = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models/Infrastructure"
PREVIEW_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Previews/Infrastructure"
QA_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders"

for d in [BLEND_DIR, FBX_DIR, PREVIEW_DIR, QA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MODEL_COLLECTION_NAME = "DirtRoadTiles_DeepSeek"
HELPER_COLLECTION_NAME = "Helpers_DirtRoadTiles_DeepSeek"
MATERIAL_PREFIX = "DirtRoadTiles_DeepSeek_"

# Clean up previous runs (idempotent)
for col_name in [MODEL_COLLECTION_NAME, HELPER_COLLECTION_NAME]:
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

# Clean up specific materials with prefix that have no users
for mat in list(bpy.data.materials):
    if mat.name.startswith(MATERIAL_PREFIX) and mat.users == 0:
        bpy.data.materials.remove(mat)

# Create new collections
model_col = bpy.data.collections.new(MODEL_COLLECTION_NAME)
bpy.context.scene.collection.children.link(model_col)

helper_col = bpy.data.collections.new(HELPER_COLLECTION_NAME)
bpy.context.scene.collection.children.link(helper_col)

# ==========================================
# 2. Material Creation
# ==========================================
def create_material(name, base_color, roughness=0.9, metallic=0.0):
    mat_name = f"{MATERIAL_PREFIX}{name}"
    mat = bpy.data.materials.get(mat_name)
    # The previous run's own collection has already been removed. Reuse an
    # exact-name material only if it is still safe to replace; never alter one
    # that an unrelated collection may still use.
    if mat and mat.users == 0:
        bpy.data.materials.remove(mat)
    # An exact-name material that still has users belongs to existing scene
    # content. Leave it untouched; Blender will suffix the new material.
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default nodes to avoid localization issues
    for node in list(nodes):
        nodes.remove(node)
        
    # Find by bl_idname to avoid localized node names
    out_node = next((n for n in nodes if n.bl_idname == 'ShaderNodeOutputMaterial'), None)
    if not out_node:
        out_node = nodes.new('ShaderNodeOutputMaterial')
        
    bsdf_node = next((n for n in nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'), None)
    if not bsdf_node:
        bsdf_node = nodes.new('ShaderNodeBsdfPrincipled')
    
    bsdf_node.inputs['Base Color'].default_value = base_color
    bsdf_node.inputs['Roughness'].default_value = roughness
    bsdf_node.inputs['Metallic'].default_value = metallic
    
    links.new(bsdf_node.outputs['BSDF'], out_node.inputs['Surface'])
    return mat

mat_base_dirt = create_material("BaseDirt", (0.25, 0.2, 0.15, 1.0), roughness=0.95)
mat_road_dirt = create_material("RoadDirt", (0.45, 0.35, 0.25, 1.0), roughness=0.9)
mat_gravel = create_material("Gravel", (0.5, 0.45, 0.4, 1.0), roughness=0.8)
mat_stone = create_material("Stone", (0.4, 0.4, 0.4, 1.0), roughness=0.8)
mat_grass = create_material("Grass", (0.3, 0.5, 0.2, 1.0), roughness=0.9)

# ==========================================
# 3. Helper Functions
# ==========================================
def apply_flat_shading(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = False

def add_box(name, size, location, mat, parent_col, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    obj.data.materials.append(mat)
    for c in obj.users_collection:
        c.objects.unlink(obj)
    parent_col.objects.link(obj)
    apply_flat_shading(obj)
    return obj

# ==========================================
# 4. Tile Generation Logic
# ==========================================
# Grid resolution: 0.05m
RES = 0.05
STEPS = int(1.0 / RES)

def is_road_cell(cx, cy, mask):
    # mask: [N, E, S, W]
    # cx, cy are the center of the cell, between -0.5 and 0.5
    N, E, S, W = mask
    
    # Core road width is 0.5m, so from -0.25 to 0.25
    # Check straight segments
    if N and not S and not E and not W:
        return abs(cx) <= 0.25 and cy >= -0.25
    if S and not N and not E and not W:
        return abs(cx) <= 0.25 and cy <= 0.25
    if E and not W and not N and not S:
        return abs(cy) <= 0.25 and cx >= -0.25
    if W and not E and not N and not S:
        return abs(cy) <= 0.25 and cx <= 0.25
        
    # Straight N/S
    if N and S and not E and not W:
        return abs(cx) <= 0.25
        
    # Corner S/E
    if S and E and not N and not W:
        if abs(cx) <= 0.25 and cy <= 0.25: return True
        if abs(cy) <= 0.25 and cx >= -0.25: return True
        return False
        
    # Tee W/E/S
    if W and E and S and not N:
        if abs(cx) <= 0.25 and cy <= 0.25: return True
        if abs(cy) <= 0.25 and -0.5 <= cx <= 0.5: return True
        return False
        
    # Cross N/E/S/W
    if N and E and S and W:
        if abs(cx) <= 0.25 and -0.5 <= cy <= 0.5: return True
        if abs(cy) <= 0.25 and -0.5 <= cx <= 0.5: return True
        return False
        
    return False

def create_tile(name, mask, location):
    # 1. Create Root Empty
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    root = bpy.context.active_object
    root.name = name
    for c in root.users_collection:
        c.objects.unlink(root)
    model_col.objects.link(root)

    # 2. Create Base Mesh (1x1x0.08)
    # Child geometry is in tile-local coordinates; the root supplies the tile
    # staging offset in the source scene.
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.04))
    base_obj = bpy.context.active_object
    base_obj.name = f"{name}_Base"
    base_obj.scale = (1.0, 1.0, 0.08)
    bpy.ops.object.transform_apply(scale=True)
    base_obj.data.materials.append(mat_base_dirt)
    for c in base_obj.users_collection:
        c.objects.unlink(base_obj)
    model_col.objects.link(base_obj)
    base_obj.parent = root
    apply_flat_shading(base_obj)
    
    # Slightly perturb top vertices for organic look, keeping edges at Z=0.08
    bm = bmesh.new()
    bm.from_mesh(base_obj.data)
    for v in bm.verts:
        if v.co.z > 0.07 and abs(v.co.x) < 0.49 and abs(v.co.y) < 0.49:
            v.co.z += random.uniform(-0.005, 0.005)
    bm.to_mesh(base_obj.data)
    bm.free()

    # 3. Create Road Mesh
    bm = bmesh.new()
    verts = {}
    
    # Create grid of vertices
    for i in range(STEPS + 1):
        for j in range(STEPS + 1):
            x = -0.5 + i * RES
            y = -0.5 + j * RES
            # Snap to edges to prevent gaps
            if abs(x) < 0.001: x = 0.0
            if abs(y) < 0.001: y = 0.0
            if abs(x - 0.5) < 0.001: x = 0.5
            if abs(x + 0.5) < 0.001: x = -0.5
            if abs(y - 0.5) < 0.001: y = 0.5
            if abs(y + 0.5) < 0.001: y = -0.5
            
            # Bottom vertex (Z=0.08)
            v_bot = bm.verts.new((x, y, 0.08))
            # Top vertex (Z=0.10)
            v_top = bm.verts.new((x, y, 0.10))
            verts[(i, j)] = (v_bot, v_top)
            
    # Build a closed, watertight raised road strip. Shared grid vertices are
    # welded after all cells are emitted; side walls are created only along the
    # perimeter, so adjacent road cells remain manifold.
    for i in range(STEPS):
        for j in range(STEPS):
            # Cell center
            cx = -0.5 + (i + 0.5) * RES
            cy = -0.5 + (j + 0.5) * RES
            
            if is_road_cell(cx, cy, mask):
                v00_bot, v00_top = verts[(i, j)]
                v10_bot, v10_top = verts[(i+1, j)]
                v11_bot, v11_top = verts[(i+1, j+1)]
                v01_bot, v01_top = verts[(i, j+1)]

                bm.faces.new((v00_top, v10_top, v11_top, v01_top))
                bm.faces.new((v01_bot, v11_bot, v10_bot, v00_bot))

                south_road = j > 0 and is_road_cell(cx, cy - RES, mask)
                east_road = i < STEPS - 1 and is_road_cell(cx + RES, cy, mask)
                north_road = j < STEPS - 1 and is_road_cell(cx, cy + RES, mask)
                west_road = i > 0 and is_road_cell(cx - RES, cy, mask)
                if not south_road:
                    bm.faces.new((v00_top, v00_bot, v10_bot, v10_top))
                if not east_road:
                    bm.faces.new((v10_top, v10_bot, v11_bot, v11_top))
                if not north_road:
                    bm.faces.new((v11_top, v11_bot, v01_bot, v01_top))
                if not west_road:
                    bm.faces.new((v01_top, v01_bot, v00_bot, v00_top))

    # Clean up doubles to connect adjacent faces
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    loose_verts = [v for v in bm.verts if not v.link_faces]
    if loose_verts:
        bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')
    
    # Create the mesh object
    road_mesh = bpy.data.meshes.new(f"{name}_RoadMesh")
    bm.to_mesh(road_mesh)
    bm.free()
    
    road_obj = bpy.data.objects.new(f"{name}_Road", road_mesh)
    model_col.objects.link(road_obj)
    road_obj.parent = root
    road_obj.data.materials.append(mat_road_dirt)
    apply_flat_shading(road_obj)

    # 4. Add Decorations
    random.seed(name)
    
    # Stones
    for _ in range(3):
        sx = random.uniform(-0.4, 0.4)
        sy = random.uniform(-0.4, 0.4)
        if is_road_cell(sx, sy, mask):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.02, 0.04), location=(sx, sy, 0.10 + random.uniform(0, 0.02)))
            stone = bpy.context.active_object
            stone.name = f"{name}_Stone_{_}"
            stone.scale.z = 0.5
            bpy.ops.object.transform_apply(scale=True)
            stone.data.materials.append(mat_stone)
            for c in stone.users_collection:
                c.objects.unlink(stone)
            model_col.objects.link(stone)
            stone.parent = root
            apply_flat_shading(stone)

    # Gravel
    for _ in range(5):
        gx = random.uniform(-0.4, 0.4)
        gy = random.uniform(-0.4, 0.4)
        if is_road_cell(gx, gy, mask):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(gx, gy, 0.10 + random.uniform(0, 0.01)))
            gravel = bpy.context.active_object
            gravel.name = f"{name}_Gravel_{_}"
            gravel.scale = (random.uniform(0.02, 0.05), random.uniform(0.02, 0.05), 0.01)
            bpy.ops.object.transform_apply(scale=True)
            gravel.data.materials.append(mat_gravel)
            for c in gravel.users_collection:
                c.objects.unlink(gravel)
            model_col.objects.link(gravel)
            gravel.parent = root
            apply_flat_shading(gravel)

    # Grass
    for _ in range(2):
        gx = random.uniform(-0.45, 0.45)
        gy = random.uniform(-0.45, 0.45)
        if not is_road_cell(gx, gy, mask) or random.random() > 0.5:
            # Place on edge
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.03, radius2=0.0, depth=0.1, location=(gx, gy, 0.08 + 0.05))
            grass = bpy.context.active_object
            grass.name = f"{name}_Grass_{_}"
            grass.rotation_euler = (random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), random.uniform(0, 3.14))
            grass.data.materials.append(mat_grass)
            for c in grass.users_collection:
                c.objects.unlink(grass)
            model_col.objects.link(grass)
            grass.parent = root
            apply_flat_shading(grass)

    return root

# ==========================================
# 5. Generate the 5 Modules
# ==========================================
# Placement in source scene: spread out along X
modules = [
    ("DirtRoadStraight", [True, False, True, False], Vector((-3.0, 0, 0))), # N, S
    ("DirtRoadCorner",   [False, True, True, False], Vector((-1.0, 0, 0))), # E, S
    ("DirtRoadTee",      [False, True, True, True],  Vector((1.0, 0, 0))),  # E, S, W
    ("DirtRoadCross",    [True, True, True, True],   Vector((3.0, 0, 0))),  # N, E, S, W
    ("DirtRoadEnd",      [False, False, True, False],Vector((0.0, -2.0, 0))) # S
]

tile_roots = {}
for name, mask, loc in modules:
    tile_roots[name] = create_tile(name, mask, loc)

# ==========================================
# 6. Quality Diagnostic Setup (Connectivity QA)
# ==========================================
def check_port_hits(tile_name, edge, tile_obj):
    # Sample in world cardinal directions so rotated mask instances are checked
    # just inside each edge; an exact polygon boundary is half-open in ray casts.
    bpy.context.view_layer.update()
    return edge_samples_on_world_edge(tile_obj.matrix_world.translation, edge, edge_distance=0.499)

CARDINALS = ("N", "E", "S", "W")
CANONICAL_MODULES = {
    "DirtRoadStraight": (True, False, True, False),
    "DirtRoadCorner": (False, True, True, False),
    "DirtRoadTee": (False, True, True, True),
    "DirtRoadCross": (True, True, True, True),
    "DirtRoadEnd": (False, False, True, False),
}

def rotate_mask_ccw(mask):
    # New N/E/S/W values after a positive 90-degree Z rotation.
    return (mask[1], mask[2], mask[3], mask[0])

def module_for_mask(mask):
    for module_name, canonical in CANONICAL_MODULES.items():
        rotated = canonical
        for quarter_turns in range(4):
            if rotated == tuple(mask):
                return module_name, quarter_turns
            rotated = rotate_mask_ccw(rotated)
    return None, 0

def edge_samples_on_world_edge(origin, edge, edge_distance=0.5):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    hits = 0
    for k in range(25):
        offset = -0.24 + k * 0.02
        if edge in ("N", "S"):
            ray_origin = origin + Vector((offset, edge_distance if edge == "N" else -edge_distance, 1.0))
        else:
            ray_origin = origin + Vector((edge_distance if edge == "E" else -edge_distance, offset, 1.0))
        hit, loc, norm, idx, obj, mat = bpy.context.scene.ray_cast(
            depsgraph, ray_origin, Vector((0, 0, -1))
        )
        if hit and loc.z > 0.09:
            hits += 1
    return hits

def remove_tile_tree(root):
    for child in list(root.children):
        bpy.data.objects.remove(child, do_unlink=True)
    bpy.data.objects.remove(root, do_unlink=True)

def run_connectivity_qa():
    qa_data = {"samples_per_port": 25, "minimum_open_hits": 23,
               "modules": {}, "masks": {}, "stitching": {}}
    
    # 1. Check the 5 generated modules
    for name, mask, loc in modules:
        root = tile_roots[name]
        qa_data["modules"][name] = {}
        for e in ['N', 'E', 'S', 'W']:
            hits = check_port_hits(name, e, root)
            expected_open = bool(mask["NESW".index(e)])
            qa_data["modules"][name][e] = {
                "expected_open": expected_open,
                "hits": hits,
                "is_open": hits >= 23,
                "passed": (hits >= 23) == expected_open
            }

    # Exercise all 16 neighbor masks against actual rotated meshes. The zero
    # mask is an empty cell; all other masks map to one of the five modules.
    temporary_roots = []
    try:
        for value in range(16):
            mask = tuple(bool((value >> shift) & 1) for shift in (3, 2, 1, 0))
            mask_name = "".join("1" if bit else "0" for bit in mask)
            module_name, turns = module_for_mask(mask)
            row = {"expected_ports": dict(zip(CARDINALS, mask))}
            if module_name is None:
                row.update({"module": "EmptyCell", "actual_ports": dict(zip(CARDINALS, (False,) * 4)), "passed": not any(mask)})
            else:
                qa_index = len(temporary_roots)
                qa_root = create_tile(
                    f"QA_Mask_{mask_name}", CANONICAL_MODULES[module_name],
                    Vector((20.0 + qa_index * 2.0, 20.0, 0.0))
                )
                qa_root.rotation_euler.z = turns * math.pi / 2.0
                temporary_roots.append(qa_root)
                actual = {}
                port_rows = {}
                for edge in CARDINALS:
                    edge_hits = check_port_hits(qa_root.name, edge, qa_root)
                    actual[edge] = edge_hits >= 23
                    port_rows[edge] = {"hits": edge_hits, "passed": actual[edge] == mask[CARDINALS.index(edge)]}
                row.update({"module": module_name, "quarter_turns_ccw": turns,
                            "actual_ports": actual, "port_samples": port_rows,
                            "passed": actual == dict(zip(CARDINALS, mask))})
            qa_data["masks"][mask_name] = row

        # Test all four cardinal seam directions with full-width surface rays.
        stitch_cases = [
            ("North", "DirtRoadStraight", "DirtRoadStraight", (60.0, 60.0), (0.0, 1.0), "N"),
            ("South", "DirtRoadStraight", "DirtRoadStraight", (70.0, 60.0), (0.0, -1.0), "S"),
            ("East", "DirtRoadTee", "DirtRoadTee", (80.0, 60.0), (1.0, 0.0), "E"),
            ("West", "DirtRoadTee", "DirtRoadTee", (90.0, 60.0), (-1.0, 0.0), "W"),
        ]
        for label, first_name, second_name, start, delta, edge in stitch_cases:
            first = create_tile(f"QA_Stitch_{label}_A", CANONICAL_MODULES[first_name], Vector((start[0], start[1], 0.0)))
            second = create_tile(f"QA_Stitch_{label}_B", CANONICAL_MODULES[second_name],
                                 Vector((start[0] + delta[0], start[1] + delta[1], 0.0)))
            temporary_roots.extend((first, second))
            if edge in ("N", "S"):
                seam_origin = Vector((start[0], start[1] + (0.5 if edge == "N" else -0.5), 0.0))
            else:
                seam_origin = Vector((start[0] + (0.5 if edge == "E" else -0.5), start[1], 0.0))
            hits = edge_samples_on_world_edge(seam_origin, edge)
            qa_data["stitching"][label] = {"hits": hits, "total_samples": 25,
                                            "continuous": hits >= 23, "passed": hits >= 23}
    finally:
        for root in reversed(temporary_roots):
            if root.name in bpy.data.objects:
                remove_tile_tree(root)

    qa_data["passed"] = (
        all(item["passed"] for module in qa_data["modules"].values() for item in module.values())
        and all(row["passed"] for row in qa_data["masks"].values())
        and all(row["passed"] for row in qa_data["stitching"].values())
    )

    return qa_data

# ==========================================
# 7. Render Setup & QA Renders
# ==========================================
scene = bpy.context.scene

old_camera = scene.camera
old_world = scene.world
old_render_state = {
    "engine": scene.render.engine,
    "resolution_x": scene.render.resolution_x,
    "resolution_y": scene.render.resolution_y,
    "resolution_percentage": scene.render.resolution_percentage,
    "filepath": scene.render.filepath,
    "file_format": scene.render.image_settings.file_format,
    "film_transparent": scene.render.film_transparent,
    "view_transform": scene.view_settings.view_transform,
    "look": scene.view_settings.look,
    "exposure": scene.view_settings.exposure,
    "gamma": scene.view_settings.gamma,
}

# Render with a private world so a pre-existing project world stays untouched.
render_world = bpy.data.worlds.new(f"{MATERIAL_PREFIX}RenderWorld")
render_world.use_nodes = True
bg_node = next((n for n in render_world.node_tree.nodes if n.bl_idname == 'ShaderNodeBackground'), None)
if bg_node:
    bg_node.inputs[0].default_value = (0.85, 0.85, 0.85, 1.0)
scene.world = render_world

# Keep unrelated scene objects out of the asset renders, restoring their flags
# before saving the source scene.
managed_objects = set(model_col.objects) | set(helper_col.objects)
for obj in scene.objects:
    if obj not in managed_objects:
        obj.hide_render = True

try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        pass

scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'

# Lighting
bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), math.radians(20), math.radians(30))
for c in sun.users_collection:
    c.objects.unlink(sun)
helper_col.objects.link(sun)

bpy.ops.object.light_add(type='AREA', location=(-5, -6, 6))
area = bpy.context.active_object
area.data.energy = 500
area.data.size = 10
area.rotation_euler = (math.radians(60), 0, math.radians(-45))
for c in area.users_collection:
    c.objects.unlink(area)
helper_col.objects.link(area)

# Camera
bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.data.type = 'ORTHO'
for c in cam.users_collection:
    c.objects.unlink(cam)
helper_col.objects.link(cam)
scene.camera = cam

def render_view(loc, rot, ortho_scale, filename):
    cam.location = loc
    cam.rotation_euler = rot
    cam.data.ortho_scale = ortho_scale
    scene.render.filepath = str(QA_DIR / filename)
    bpy.ops.render.render(write_still=True)

center_z = 0.1
center_y = -1.0
# Fit the 5 modules. They span X from -3.5 to 3.5, Y from -2.5 to 0.5
scale_factor = 8.0

# True Orthographic Views
render_view((0, -15, center_z), (math.radians(90), 0, 0), scale_factor, "DirtRoadTiles_DeepSeek_Front.png")
render_view((0, 15, center_z), (math.radians(90), 0, math.radians(180)), scale_factor, "DirtRoadTiles_DeepSeek_Back.png")
render_view((-15, center_y, center_z), (math.radians(90), 0, math.radians(-90)), scale_factor, "DirtRoadTiles_DeepSeek_Left.png")
render_view((15, center_y, center_z), (math.radians(90), 0, math.radians(90)), scale_factor, "DirtRoadTiles_DeepSeek_Right.png")
render_view((0, center_y, 15), (0, 0, 0), scale_factor, "DirtRoadTiles_DeepSeek_Top.png")
render_view((0, center_y, -15), (math.radians(180), 0, 0), scale_factor, "DirtRoadTiles_DeepSeek_Bottom.png")

# 3/4 Preview
cam.location = (8, center_y - 10, 8)
look_target = Vector((0, center_y, 0.05))
direction = look_target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = 9.0
scene.render.filepath = str(PREVIEW_DIR / "DirtRoadTiles_DeepSeek.png")
bpy.ops.render.render(write_still=True)

# ==========================================
# 8. Export FBX & Save Blend
# ==========================================
# Run QA before export (it creates temporary tiles)
qa_results = run_connectivity_qa()
qa_json_path = PREVIEW_DIR / "DirtRoadTiles_DeepSeek_Connectivity_QA.json"
with open(qa_json_path, 'w') as f:
    json.dump(qa_results, f, indent=4)
if not qa_results["passed"]:
    raise RuntimeError(f"Dirt-road connectivity QA failed; see {qa_json_path}")

# Export each module
for name, _, _ in modules:
    root = tile_roots[name]
    display_location = root.location.copy()
    root.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for child in root.children:
        child.select_set(True)
        
    fbx_path = FBX_DIR / f"{name}_DeepSeek.fbx"
    try:
        bpy.ops.export_scene.fbx(
            filepath=str(fbx_path),
            use_selection=True,
            apply_scale_options='FBX_SCALE_ALL',
            object_types={'MESH'},
            bake_space_transform=True,
            axis_forward='-Z',
            axis_up='Y'
        )
    finally:
        root.location = display_location
        bpy.context.view_layer.update()

# Restore the caller's scene state before saving the standalone source asset.
scene.camera = old_camera
scene.world = old_world
scene.render.engine = old_render_state["engine"]
scene.render.resolution_x = old_render_state["resolution_x"]
scene.render.resolution_y = old_render_state["resolution_y"]
scene.render.resolution_percentage = old_render_state["resolution_percentage"]
scene.render.filepath = old_render_state["filepath"]
scene.render.image_settings.file_format = old_render_state["file_format"]
scene.render.film_transparent = old_render_state["film_transparent"]
scene.view_settings.view_transform = old_render_state["view_transform"]
scene.view_settings.look = old_render_state["look"]
scene.view_settings.exposure = old_render_state["exposure"]
scene.view_settings.gamma = old_render_state["gamma"]
for obj, hide_render in initial_object_render_visibility.items():
    if bpy.data.objects.get(obj.name) == obj:
        obj.hide_render = hide_render
bpy.ops.object.select_all(action='DESELECT')
for obj in initial_selection:
    if bpy.data.objects.get(obj.name) == obj:
        obj.select_set(True)
bpy.context.view_layer.objects.active = (
    initial_active if initial_active and bpy.data.objects.get(initial_active.name) == initial_active else None
)
if render_world.users == 0:
    bpy.data.worlds.remove(render_world)

blend_path = BLEND_DIR / "DirtRoadTiles_DeepSeek.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# ==========================================
# 9. Diagnostics
# ==========================================
def calculate_bounds_and_diagnostics():
    min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
    max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
    
    mesh_objects = [obj for obj in model_col.objects if obj.type == 'MESH']
    non_manifold_count = 0
    loose_verts = 0
    
    for obj in mesh_objects:
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ Vector(corner)
            min_x = min(min_x, world_corner.x)
            min_y = min(min_y, world_corner.y)
            min_z = min(min_z, world_corner.z)
            max_x = max(max_x, world_corner.x)
            max_y = max(max_y, world_corner.y)
            max_z = max(max_z, world_corner.z)
            
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
        non_manifold_count += len(non_manifold_edges)
        
        loose_verts += len([v for v in bm.verts if not v.link_edges])
        bm.free()

    print("\n--- Diagnostic Report ---")
    print(f"Mesh Object Count: {len(mesh_objects)}")
    print(f"World Bounds (W, D, H): {max_x - min_x:.3f} m, {max_y - min_y:.3f} m, {max_z - min_z:.3f} m")
    print(f"Minimum Z: {min_z:.3f} m")
    print(f"Non-Manifold Edges: {non_manifold_count}")
    print(f"Loose Vertices: {loose_verts}")
    print("Note: Per-object topological checks cannot detect intersections between separate objects.")
    print("-------------------------\n")

calculate_bounds_and_diagnostics()
print(f"Saved Blender file to: {blend_path}")
print(f"Saved FBX modules to: {FBX_DIR}")
print(f"Saved Connectivity QA to: {qa_json_path}")
