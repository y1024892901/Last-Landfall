"""Create an overturned supply-ship wreck on one existing Gate26 island.

Run from the project root with Blender 5.2:
    blender --background --python Tools/Blender/create_capsized_wreck_on_gate26.py

The source Gate26 FBX is imported into a fresh scene and is never modified.
Only the five outputs configured below are written.
"""

import bpy
import json
import math
import os
import random
import re
import bmesh
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree


# -----------------------------------------------------------------------------
# Paths and composition constants
# -----------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

INPUT_FBX = os.path.join(
    PROJECT_ROOT,
    "Assets/LastLandfall/Resources/Models/Environment/LastLandfall_Basin_TwinIslands_Gate26.fbx",
)
SCRIPT_PATH = os.path.join(PROJECT_ROOT, "Tools/Blender/create_capsized_wreck_on_gate26.py")
BLEND_PATH = os.path.join(
    PROJECT_ROOT, "Assets/LastLandfall/Art/Source/Environment/Gate26_CapsizedWreck.blend"
)
FBX_PATH = os.path.join(
    PROJECT_ROOT, "Assets/LastLandfall/Resources/Models/Environment/Gate26_CapsizedWreck.fbx"
)
PREVIEW_PATH = os.path.join(
    PROJECT_ROOT, "Assets/LastLandfall/Art/Previews/Environment/Gate26_CapsizedWreck.png"
)
DETAIL_PREVIEW_PATH = os.path.join(
    PROJECT_ROOT, "Assets/LastLandfall/Art/Previews/Environment/Gate26_CapsizedWreck_Detail.png"
)
QA_PATH = os.path.join(PROJECT_ROOT, "work/shipwreck_islet/Gate26_CapsizedWreck_QA.json")

SELECTED_ISLAND = "East"
CENTER_XY = Vector((10.0, 42.0))
HEADING_DEG = 90.0
HEADING = math.radians(HEADING_DEG)
LENGTH = 20.0
HALF_LENGTH = LENGTH * 0.5
BEAM = 5.5
HALF_BEAM = BEAM * 0.5
LOCAL_HALF_LENGTH = 12.5
LOCAL_HALF_BEAM = 3.0
SCALE_X = LENGTH / 25.0
SCALE_Y = BEAM / 6.0
SCALE_Z = 0.90
CONTACT_OFFSET = 1.22
WATER_Z = -0.15
RANDOM_SEED = 260621

# Expanded terrain has its own rigid, regrounded wreck; the original export remains intact.
if '--expanded' in __import__('sys').argv:
    from pathlib import Path
    metrics = json.loads((Path(PROJECT_ROOT) / 'Art/Reports/IslandExpansion/ExpansionMetrics.json').read_text())
    layout = next(item for item in metrics if item['island'] == 'East')
    CENTER_XY = Vector(tuple(layout['center'][i] + (CENTER_XY[i] - layout['old_center'][i]) * layout['scale'] for i in range(2)))
    INPUT_FBX = os.path.join(PROJECT_ROOT, 'Assets/LastLandfall/Resources/Models/Environment/Island_East_Expanded.fbx')
    WATER_Z = -.92
    BLEND_PATH = BLEND_PATH.replace('Gate26_CapsizedWreck.blend', 'Gate26_CapsizedWreck_Expanded.blend')
    FBX_PATH = FBX_PATH.replace('Gate26_CapsizedWreck.fbx', 'Gate26_CapsizedWreck_Expanded.fbx')
    PREVIEW_PATH = PREVIEW_PATH.replace('.png', '_Expanded.png')
    DETAIL_PREVIEW_PATH = DETAIL_PREVIEW_PATH.replace('.png', '_Expanded.png')
    QA_PATH = QA_PATH.replace('_QA.json', '_Expanded_QA.json')


def ensure_output_dirs():
    for path in (BLEND_PATH, FBX_PATH, PREVIEW_PATH, DETAIL_PREVIEW_PATH, QA_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)


def clear_default_scene():
    # Remove startup camera/cube/lights and any prior in-memory content only.
    for obj in list(bpy.context.scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection.users == 0:
            bpy.data.collections.remove(collection)


def make_collection(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)


def create_material(name, color, roughness=0.82, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    shader = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        shader = nodes.new("ShaderNodeBsdfPrincipled")
    output = next((node for node in nodes if node.type == "OUTPUT_MATERIAL"), None)
    if output is None:
        output = nodes.new("ShaderNodeOutputMaterial")
    if not any(link.from_node == shader and link.to_node == output for link in mat.node_tree.links):
        mat.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return mat


def create_mesh_object(name, verts, faces, collection, materials=(), material_indices=None, parent=None):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    for mat in materials:
        mesh.materials.append(mat)
    if material_indices:
        for poly, index in zip(mesh.polygons, material_indices):
            poly.material_index = min(index, max(0, len(materials) - 1))
    for poly in mesh.polygons:
        poly.use_smooth = False
    if parent:
        obj.parent = parent
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.location = (0.0, 0.0, 0.0)
        obj.rotation_euler = (0.0, 0.0, 0.0)
        obj.scale = (1.0, 1.0, 1.0)
    return obj


def recalc_normals(obj):
    if obj.type != "MESH":
        return
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def bbox_world(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (
        min(p.x for p in points), max(p.x for p in points),
        min(p.y for p in points), max(p.y for p in points),
        min(p.z for p in points), max(p.z for p in points),
    )


def closest_point_segment_2d(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom <= 1.0e-8:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / denom))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def main():
    if not os.path.isfile(INPUT_FBX):
        raise FileNotFoundError("Gate26 source FBX not found: " + INPUT_FBX)
    ensure_output_dirs()
    clear_default_scene()
    random.seed(RANDOM_SEED)

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0

    env_col = make_collection("Gate26_Environment")
    ship_col = make_collection("Capsized_Supply_Ship")
    debris_col = make_collection("Wreck_Debris")
    preview_col = make_collection("PreviewOnly_Water_Camera_Lights")

    # -------------------------------------------------------------------------
    # Import the current two-island asset without editing its mesh data.
    # -------------------------------------------------------------------------
    bpy.ops.import_scene.fbx(filepath=INPUT_FBX)
    imported_objects = list(bpy.context.selected_objects)
    for obj in imported_objects:
        move_to_collection(obj, env_col)

    west = bpy.data.objects.get("Basin_Island_West (terrain source)")
    east = bpy.data.objects.get("Basin_Island_East (terrain source)")
    terrain = east if SELECTED_ISLAND == "East" else west
    if terrain is None:
        terrain = next((o for o in imported_objects if o.type == 'MESH' and
            ('Basin_Island_' + SELECTED_ISLAND + ' (terrain source)') in o.name), None)
    if terrain is None or terrain.type != "MESH":
        raise RuntimeError("Could not find Gate26 {} terrain mesh.".format(SELECTED_ISLAND))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    terrain_eval = terrain.evaluated_get(depsgraph)
    bvh = BVHTree.FromObject(terrain_eval, depsgraph)
    world_to_terrain = terrain.matrix_world.inverted()
    terrain_to_world = terrain.matrix_world
    ray_direction_local = (world_to_terrain.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()

    def sample_terrain_z(world_x, world_y):
        world_origin = Vector((world_x, world_y, 80.0))
        origin_local = world_to_terrain @ world_origin
        hit_local, _normal, _face, _distance = bvh.ray_cast(
            origin_local, ray_direction_local, 200.0
        )
        if hit_local is None:
            return None
        return (terrain_to_world @ hit_local).z

    cos_h = math.cos(HEADING)
    sin_h = math.sin(HEADING)

    def world_xy(local_x, local_y):
        local_x *= SCALE_X
        local_y *= SCALE_Y
        return (
            CENTER_XY.x + cos_h * local_x - sin_h * local_y,
            CENTER_XY.y + sin_h * local_x + cos_h * local_y,
        )

    # Fit a plane to the ship footprint and rotate the whole ship to match
    # the island's broad slope. Keeping the hull rigid avoids the melted look
    # caused by deforming every vertex to the sharp local rock relief.
    plane_rows, plane_heights = [], []
    for local_x in (-LOCAL_HALF_LENGTH, -LOCAL_HALF_LENGTH * 0.5, 0.0,
                    LOCAL_HALF_LENGTH * 0.5, LOCAL_HALF_LENGTH):
        for local_y in (-LOCAL_HALF_BEAM, 0.0, LOCAL_HALF_BEAM):
            wx, wy = world_xy(local_x, local_y)
            ground_z = sample_terrain_z(wx, wy)
            if ground_z is None:
                continue  # The wreck deliberately hangs over the island's shore.
            plane_rows.append((1.0, wx - CENTER_XY.x, wy - CENTER_XY.y))
            plane_heights.append(ground_z)
    if len(plane_rows) < 6:
        raise RuntimeError("Too few terrain contacts to seat the wreck on the island shore.")
    plane_coeff, _, _, _ = np.linalg.lstsq(
        np.asarray(plane_rows), np.asarray(plane_heights), rcond=None
    )
    plane_z, plane_dx, plane_dy = [float(value) for value in plane_coeff]
    center_ground_z = sample_terrain_z(CENTER_XY.x, CENTER_XY.y)
    if center_ground_z is None:
        raise RuntimeError("Chosen {}-island center does not touch terrain.".format(SELECTED_ISLAND))

    local_x_axis = Vector((cos_h, sin_h, plane_dx * cos_h + plane_dy * sin_h)).normalized()
    local_y_axis = Vector((-sin_h, cos_h, -plane_dx * sin_h + plane_dy * cos_h))
    local_y_axis = (local_y_axis - local_x_axis * local_y_axis.dot(local_x_axis)).normalized()
    local_z_axis = local_x_axis.cross(local_y_axis).normalized()
    if local_z_axis.z < 0.0:
        local_z_axis.negate()
    ship_rotation = Matrix((local_x_axis, local_y_axis, local_z_axis)).transposed()

    # Hull vertices stay in ship-local space; only the complete ship tilts with
    # the fitted terrain plane. Terrain-only raycasts allow the stern and bow
    # to overhang the shoreline without pulling the hull into a deformed shape.
    terrain_fallbacks = 0

    def seated_vertex(local_x, local_y, local_z):
        return (local_x, local_y, local_z)

    root = bpy.data.objects.new("Gate26_CapsizedWreck_Root", None)
    ship_col.objects.link(root)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 1.4
    root.location = (0.0, 0.0, 0.0)

    ship_root = bpy.data.objects.new("East_Island_Inverted_Supply_Ship", None)
    ship_col.objects.link(ship_root)
    ship_root.parent = root
    ship_root.matrix_parent_inverse = Matrix.Identity(4)
    ship_root.location = (CENTER_XY.x, CENTER_XY.y, plane_z + CONTACT_OFFSET)
    ship_root.rotation_mode = "QUATERNION"
    ship_root.rotation_quaternion = ship_rotation.to_quaternion()
    ship_root.scale = (SCALE_X, SCALE_Y, SCALE_Z)
    ship_root.empty_display_type = "CUBE"
    ship_root.empty_display_size = 0.65

    # Ship material palette: rusted hull bottom is the dominant upward-facing
    # surface; the dark teal side shell and crushed deck are secondary.
    mat_bottom = create_material("Wreck_Bottom_Oxide", (0.31, 0.115, 0.075, 1.0), 0.91, 0.08)
    mat_bottom_alt = create_material("Wreck_Bottom_Faded_Red", (0.345, 0.155, 0.105, 1.0), 0.96, 0.04)
    mat_bottom_dark = create_material("Wreck_Bottom_Sooted_Rust", (0.24, 0.105, 0.075, 1.0), 0.97, 0.02)
    mat_side = create_material("Wreck_Side_Faded_Teal", (0.105, 0.205, 0.235, 1.0), 0.78, 0.12)
    mat_under = create_material("Wreck_Crushed_Underside", (0.105, 0.12, 0.12, 1.0), 0.96, 0.02)
    mat_keel = create_material("Wreck_Keel_Charcoal_Rust", (0.16, 0.11, 0.085, 1.0), 0.86, 0.16)
    mat_metal = create_material("Wreck_Propeller_Aged_Bronze", (0.55, 0.38, 0.16, 1.0), 0.70, 0.35)
    mat_seam = create_material("Wreck_Seam_Dark", (0.075, 0.065, 0.06, 1.0), 0.95, 0.0)
    mat_wood = create_material("Wreck_Driftwood", (0.28, 0.205, 0.13, 1.0), 0.94, 0.0)
    mat_rescue = create_material("Wreck_Faded_Rescue_Orange", (0.54, 0.235, 0.075, 1.0), 0.82, 0.0)
    mat_deck = create_material("Wreck_Deck_Dark_Wet", (0.18, 0.165, 0.13, 1.0), 0.95, 0.0)
    mat_breach = create_material("Wreck_Breach_Interior_Dark", (0.018, 0.024, 0.024, 1.0), 0.98, 0.0)
    mat_grime = create_material("Wreck_Seaweed_Grime", (0.065, 0.105, 0.09, 1.0), 0.96, 0.0)
    mat_rivet = create_material("Wreck_Exposed_Iron", (0.17, 0.155, 0.13, 1.0), 0.83, 0.22)

    # A sectioned, asymmetrical hull: local +X is stern, -X is the tapered bow.
    # The exposed cross-section is already inverted: broad hull bottom/keel up,
    # deck and wheelhouse down into the island.
    station_data = [
        (-12.50, 0.12, -0.18), (-11.60, 0.95, -0.12), (-10.0, 1.82, -0.04),
        (-7.4, 2.48, 0.02), (-5.8, 2.68, 0.01), (-4.2, 2.82, 0.00),
        (-3.0, 2.89, -0.03), (-1.0, 2.98, -0.10), (0.4, 3.00, -0.16),
        (1.7, 3.00, -0.23), (2.5, 3.00, -0.26), (3.8, 2.98, -0.22),
        (5.4, 2.94, -0.18), (6.7, 2.84, -0.11), (7.9, 2.72, -0.05),
        (9.8, 2.35, 0.02), (11.25, 1.82, -0.02), (12.50, 1.30, 0.02),
    ]

    def hull_width(x):
        if x <= station_data[0][0]:
            return station_data[0][1]
        if x >= station_data[-1][0]:
            return station_data[-1][1]
        for a, b in zip(station_data, station_data[1:]):
            if a[0] <= x <= b[0]:
                t = (x - a[0]) / (b[0] - a[0])
                return a[1] * (1.0 - t) + b[1] * t
        return LOCAL_HALF_BEAM

    def hull_bottom_z(x, y):
        w = max(0.15, hull_width(x))
        across = min(1.0, abs(y) / w)
        bow_taper = max(0.0, (abs(x) - 10.8) / 1.7)
        base = 2.26 - 1.02 * (across ** 1.72) - 0.22 * bow_taper
        # A modest collision buckle toward midship keeps the hull hand-built.
        buckle = -0.16 * math.exp(-((x - 1.8) / 2.6) ** 2) * (0.35 + across)
        return base + buckle

    # Cross section ring starts on the upward-facing centerline and runs around
    # the inverted hull, down each side, then across the crushed deck side.
    cross_profile = [
        (0.00, 2.28), (0.18, 2.25), (0.36, 2.18), (0.54, 2.06),
        (0.71, 1.90), (0.86, 1.68), (0.96, 1.35), (1.00, 0.46),
        (0.88, -0.52), (0.54, -1.08), (0.00, -1.36), (-0.54, -1.08),
        (-0.88, -0.52), (-1.00, 0.46), (-0.96, 1.35), (-0.86, 1.68),
        (-0.71, 1.90), (-0.54, 2.06), (-0.36, 2.18), (-0.18, 2.25),
    ]

    def is_main_breach_face(x_mid, profile_index):
        # The broad torn opening crosses the exposed upper hull and varies by
        # strip, so the silhouette is jagged instead of a clean rectangle.
        limits = {
            0: (-0.2, 1.6), 1: (-1.4, 3.2), 2: (-2.6, 3.8),
            3: (-1.9, 4.1), 4: (-2.9, 3.5), 5: (-2.0, 2.6),
        }
        if profile_index in limits:
            low, high = limits[profile_index]
            return low <= x_mid <= high
        # A second, smaller split on the far upper flank breaks the stern's
        # uninterrupted outline when the island is viewed from the other side.
        if profile_index in (14, 15, 16, 17, 18, 19):
            low, high = {
                14: (7.4, 8.8), 15: (6.8, 9.4), 16: (7.2, 9.8),
                17: (7.8, 9.3), 18: (7.1, 8.9), 19: (7.7, 8.6),
            }[profile_index]
            return low <= x_mid <= high
        return False

    verts = []
    faces = []
    mats = []
    for i, (x, width, station_buckle) in enumerate(station_data):
        row = []
        for lateral_ratio, z in cross_profile:
            y = lateral_ratio * width
            damage = station_buckle * (0.2 + abs(lateral_ratio))
            row.append(seated_vertex(x, y, z + damage))
        verts.extend(row)
    ring_size = len(cross_profile)
    for i in range(len(station_data) - 1):
        x_mid = (station_data[i][0] + station_data[i + 1][0]) * 0.5
        for j in range(ring_size):
            if is_main_breach_face(x_mid, j):
                continue
            j2 = (j + 1) % ring_size
            faces.append((i * ring_size + j, (i + 1) * ring_size + j,
                          (i + 1) * ring_size + j2, i * ring_size + j2))
            profile_height = (cross_profile[j][1] + cross_profile[j2][1]) * 0.5
            if profile_height >= 1.3:
                mats.append(0)
            elif profile_height >= -0.55:
                mats.append(3)
            else:
                mats.append(4)
    faces.append(tuple(range(ring_size)))
    mats.append(3)
    faces.append(tuple((len(station_data) - 1) * ring_size + j for j in reversed(range(ring_size))))
    mats.append(3)
    hull = create_mesh_object(
        "Wreck_Hull_Inverted_Sectioned", verts, faces, ship_col,
        (mat_bottom, mat_bottom_alt, mat_bottom_dark, mat_side, mat_under), mats, ship_root
    )
    recalc_normals(hull)

    def top_z(x, y):
        return hull_bottom_z(x, y) + 0.055

    # Large, readable bottom plating, with small gaps as dark seams. The panels
    # sit on the conforming hull surface and are not a noisy texture overlay.
    plate_materials = (mat_bottom_alt, mat_bottom, mat_bottom_dark)
    x_edges = [-10.7, -7.9, -5.1, -2.3, 0.5, 3.3, 6.1, 8.8, 10.7]
    y_bands = [(-0.82, -0.30), (-0.27, 0.27), (0.30, 0.82)]
    for ix, (xa, xb) in enumerate(zip(x_edges, x_edges[1:])):
        for iy, (ya, yb) in enumerate(y_bands):
            if xa < 4.1 and xb > -2.9 and iy in (1, 2):
                continue
            if xa < 9.8 and xb > 6.8 and iy == 0:
                continue
            x0, x1 = xa + 0.055, xb - 0.055
            w0, w1 = hull_width(x0), hull_width(x1)
            y0a, y0b = ya * w0, yb * w0
            y1a, y1b = ya * w1, yb * w1
            panel_verts = [
                seated_vertex(x0, y0a, top_z(x0, y0a)),
                seated_vertex(x1, y1a, top_z(x1, y1a)),
                seated_vertex(x1, y1b, top_z(x1, y1b)),
                seated_vertex(x0, y0b, top_z(x0, y0b)),
            ]
            panel = create_mesh_object(
                "Wreck_BottomPlate_{:02d}_{:02d}".format(ix, iy), panel_verts,
                [(0, 1, 2, 3)], ship_col,
                (plate_materials[0 if ix in (1, 5) else 1],), parent=ship_root
            )
            recalc_normals(panel)

    # Raised longitudinal keel, visibly sitting on the upward-facing bottom.
    keel_xs = [-10.8, -8.2, -4.0, 0.0, 4.0, 7.8, 10.4]
    keel_verts = []
    for x in keel_xs:
        for y, z in [(-0.24, 2.10), (-0.16, 2.74), (0.16, 2.74), (0.24, 2.10)]:
            keel_verts.append(seated_vertex(x, y, z))
    keel_faces = []
    for i in range(len(keel_xs) - 1):
        x_mid = (keel_xs[i] + keel_xs[i + 1]) * 0.5
        if -0.45 <= x_mid <= 2.75:
            continue
        for j in range(4):
            j2 = (j + 1) % 4
            keel_faces.append((i * 4 + j, (i + 1) * 4 + j, (i + 1) * 4 + j2, i * 4 + j2))
    keel_faces.append((0, 1, 2, 3))
    keel_faces.append(tuple((len(keel_xs) - 1) * 4 + j for j in reversed(range(4))))
    keel_obj = create_mesh_object("Wreck_Raised_Central_Keel", keel_verts, keel_faces,
                                  ship_col, (mat_keel,), parent=ship_root)
    recalc_normals(keel_obj)

    # Plate seams: transverse seams and two long seams, low and broad enough to
    # read in the preview without turning the bottom into high-frequency noise.
    seam_verts, seam_faces = [], []
    seam_half = 0.024
    for x in x_edges[1:-1]:
        if -2.9 <= x <= 4.1 or 6.8 <= x <= 9.8:
            continue
        w = hull_width(x) * 0.82
        y0, y1 = -w, w
        z0, z1 = top_z(x, y0) + 0.035, top_z(x, y1) + 0.035
        base = len(seam_verts)
        seam_verts.extend([
            seated_vertex(x - seam_half, y0, z0), seated_vertex(x + seam_half, y0, z0),
            seated_vertex(x + seam_half, y1, z1), seated_vertex(x - seam_half, y1, z1),
        ])
        seam_faces.append((base, base + 1, base + 2, base + 3))
    seam_xs = (-10.7, -7.5, -4.0, 0.0, 4.0, 7.5, 10.7)
    for ratio in (-0.78, -0.29, 0.29, 0.78):
        for xa, xb in zip(seam_xs, seam_xs[1:]):
            if ratio >= -0.29 and xa < 4.1 and xb > -2.9:
                continue
            if ratio < 0.0 and xa < 9.8 and xb > 6.8:
                continue
            endpoints = []
            for x in (xa, xb):
                y = ratio * hull_width(x)
                z = top_z(x, y) + 0.038
                endpoints.append(Vector(seated_vertex(x, y, z)))
            a, b = endpoints
            tangent = (b - a).normalized()
            side = Vector((-tangent.y, tangent.x, 0.0)).normalized() * 0.022
            base = len(seam_verts)
            seam_verts.extend([tuple(a - side), tuple(b - side), tuple(b + side), tuple(a + side)])
            seam_faces.append((base, base + 1, base + 2, base + 3))
    seams = create_mesh_object("Wreck_Bottom_Plate_Seams", seam_verts, seam_faces,
                               ship_col, (mat_seam,), parent=ship_root)
    recalc_normals(seams)

    # Broad, polygonal rust patches over some panels, kept sparse and varied.
    rust_verts, rust_faces, rust_indices = [], [], []
    for patch_i in range(15):
        x = random.uniform(-9.0, 9.0)
        width = hull_width(x)
        y = random.uniform(-0.72, 0.72) * width
        if -2.9 <= x <= 4.1 and y >= -0.35:
            continue
        if 6.8 <= x <= 9.8 and y <= -0.4:
            continue
        radius_x = random.uniform(0.32, 1.0)
        radius_y = random.uniform(0.16, 0.42)
        count = random.choice((5, 6, 7))
        points = []
        phase = random.uniform(-0.5, 0.5)
        for j in range(count):
            angle = (math.tau * j / count) + phase
            wobble = random.uniform(0.78, 1.12)
            px = max(-10.5, min(10.5, x + math.cos(angle) * radius_x * wobble))
            py = max(-0.82 * hull_width(px), min(0.82 * hull_width(px), y + math.sin(angle) * radius_y * wobble))
            points.append((px, py))
        base = len(rust_verts)
        for px, py in points:
            rust_verts.append(seated_vertex(px, py, top_z(px, py) + 0.07))
        rust_faces.append(tuple(base + i for i in range(len(points))) )
        rust_indices.append(random.randrange(3))
    rust_patches = create_mesh_object("Wreck_Scattered_Rust_Patches", rust_verts, rust_faces,
                                      ship_col, (mat_bottom_dark, mat_bottom_alt, mat_bottom), rust_indices,
                                      ship_root)
    recalc_normals(rust_patches)

    # Shape helpers for local hull fittings and debris.
    def add_box(name, center, size, material, collection, parent=ship_root, z_seated=True):
        cx, cy, cz = center
        sx, sy, sz = size
        points = []
        for xsign, ysign, zsign in [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
        ]:
            x, y, z = cx + xsign * sx * 0.5, cy + ysign * sy * 0.5, cz + zsign * sz * 0.5
            points.append(seated_vertex(x, y, z) if z_seated else (x, y, z))
        faces = [
            (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
            (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
        ]
        obj = create_mesh_object(name, points, faces, collection, (material,), parent=parent)
        recalc_normals(obj)
        return obj

    def add_beam(name, a, b, width, depth, material, collection, parent=ship_root):
        va, vb = Vector(a), Vector(b)
        axis = (vb - va).normalized()
        reference = Vector((0.0, 0.0, 1.0))
        if abs(axis.dot(reference)) > 0.92:
            reference = Vector((0.0, 1.0, 0.0))
        side = axis.cross(reference).normalized() * (width * 0.5)
        up = axis.cross(side).normalized() * (depth * 0.5)
        verts = []
        for point in (va, vb):
            for sgn_s, sgn_u in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                p = point + sgn_s * side + sgn_u * up
                verts.append(seated_vertex(p.x, p.y, p.z))
        faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
                 (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        obj = create_mesh_object(name, verts, faces, collection, (material,), parent=parent)
        recalc_normals(obj)
        return obj

    def add_breach_interior(name, outline, depth):
        # Recessed dark floors sit below the torn shell opening, making the
        # missing hull read as a real cavity from the isometric camera.
        center_x = sum(point[0] for point in outline) / len(outline)
        center_y = sum(point[1] for point in outline) / len(outline)
        points = list(outline) + [(center_x, center_y)]
        verts = [seated_vertex(x, y, top_z(x, y) - depth) for x, y in points]
        center_index = len(outline)
        faces = [(center_index, i, (i + 1) % len(outline)) for i in range(len(outline))]
        floor = create_mesh_object(name, verts, faces, ship_col, (mat_breach,), parent=ship_root)
        recalc_normals(floor)
        return floor

    def add_torn_plate(name, outline, material):
        # Thick, bent fragments turn the cut edge into torn metal rather than
        # a clean panel cutout. The upper vertices are deliberately uneven.
        top = [seated_vertex(x, y, z) for x, y, z in outline]
        bottom = [seated_vertex(x, y, z - 0.10) for x, y, z in outline]
        n = len(outline)
        verts = top + bottom
        faces = [tuple(range(n)), tuple(reversed(range(n, n * 2)))]
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, j, n + j, n + i))
        plate = create_mesh_object(name, verts, faces, debris_col, (material,), parent=ship_root)
        recalc_normals(plate)
        return plate

    main_breach_outline = [
        (-2.65, 0.06), (-2.85, 0.66), (-2.15, 1.45), (-1.55, 2.22),
        (-0.72, 2.56), (0.15, 2.33), (1.05, 2.79), (2.18, 2.52),
        (3.45, 1.98), (3.77, 1.23), (3.08, 0.58), (1.92, 0.12),
        (0.50, -0.04), (-0.85, 0.17),
    ]
    add_breach_interior("Wreck_Breach_Blackened_Interior", main_breach_outline, 0.76)
    for rib_index, x in enumerate((-1.75, -0.35, 1.05, 2.45)):
        y0, y1 = 0.30, 2.32
        z0 = top_z(x, y0) - 0.30
        z1 = top_z(x, y1) - 0.30
        middle = (x + (-0.22 if rib_index % 2 else 0.32), 1.28,
                  top_z(x, 1.28) - 0.52)
        add_beam("Wreck_Exposed_Broken_Rib_{:02d}_A".format(rib_index + 1),
                 (x, y0, z0), middle, 0.24, 0.20, mat_keel, debris_col)
        if rib_index != 2:
            add_beam("Wreck_Exposed_Broken_Rib_{:02d}_B".format(rib_index + 1),
                     (middle[0] + 0.12, middle[1] + 0.22, middle[2] - 0.12),
                     (x + 0.18, y1, z1), 0.23, 0.18, mat_rivet, debris_col)

    # Narrow riveted straps and corrosion runs establish steel construction.
    for index, x in enumerate((-9.5, -7.2, -5.0, -3.6, 4.7, 6.0, 10.0)):
        for side in (-1, 1):
            y = side * hull_width(x) * 0.56
            z = top_z(x, y) + 0.035
            add_box("Wreck_Rivet_{:02d}_{}".format(index, side), (x, y, z),
                    (0.12, 0.12, 0.055), mat_rivet, ship_col)
    for side in (-1, 1):
        streak_verts, streak_faces = [], []
        for index, x in enumerate((-9.3, -7.7, -6.1, -4.6, 4.8, 6.0, 10.1)):
            w = hull_width(x)
            points = [
                (x - 0.11, side * w * 0.61), (x + 0.13, side * w * 0.61),
                (x + 0.045, side * w * 0.92), (x - 0.035, side * w * 0.97),
            ]
            base = len(streak_verts)
            streak_verts.extend((px, py, top_z(px, py) + 0.027) for px, py in points)
            streak_faces.append(tuple(base + j for j in range(4)))
        streaks = create_mesh_object("Wreck_Corrosion_Runs_{}".format(side),
                                    streak_verts, streak_faces, ship_col,
                                    (mat_bottom_dark,), parent=ship_root)
        recalc_normals(streaks)

    # A dark tidal stain remains along both exposed hull flanks.
    for side in (-1, 1):
        stain_verts, stain_faces = [], []
        for xa, xb in zip(station_data, station_data[1:]):
            base = len(stain_verts)
            for station, z in ((xa, 0.56), (xb, 0.56), (xb, 0.84), (xa, 0.84)):
                x, width, buckle = station
                y = side * width * (1.013 - (z - 0.46) * 0.045)
                stain_verts.append((x, y, z + buckle))
            stain_faces.append(tuple(base + j for j in range(4)))
        stain = create_mesh_object("Wreck_Tidal_Stain_{}".format(side), stain_verts,
                                   stain_faces, ship_col, (mat_grime,), parent=ship_root)
        recalc_normals(stain)

    far_breach_outline = [
        (6.95, -0.38), (6.78, -0.98), (7.20, -1.82), (7.82, -2.30),
        (8.60, -2.48), (9.35, -1.91), (9.65, -1.18), (9.20, -0.52),
        (8.24, -0.18), (7.52, -0.24),
    ]
    add_breach_interior("Wreck_Stern_Flank_Breach_Interior", far_breach_outline, 0.58)
    add_torn_plate("Wreck_Torn_Hull_Flap_BowSide", [
        (-2.55, 2.45, top_z(-2.55, 2.45) + 0.14),
        (-1.58, 2.70, top_z(-1.58, 2.70) + 0.20),
        (-1.08, 2.12, top_z(-1.08, 2.12) + 0.78),
        (-2.22, 1.82, top_z(-2.22, 1.82) + 0.30),
    ], mat_bottom_alt)
    add_torn_plate("Wreck_Torn_Hull_Flap_SternSide", [
        (7.22, -1.72, top_z(7.22, -1.72) + 0.13),
        (8.05, -2.48, top_z(8.05, -2.48) + 0.16),
        (8.72, -1.78, top_z(8.72, -1.78) + 0.68),
        (7.75, -1.20, top_z(7.75, -1.20) + 0.26),
    ], mat_bottom_dark)

    # Stern propeller hubs and three broad low-poly blades each; +X is stern.
    def add_propeller(center_x, center_y, center_z, index):
        hub_verts, hub_faces = [], []
        segments = 8
        radius = 0.26
        for x in (center_x - 0.22, center_x + 0.22):
            for j in range(segments):
                ang = math.tau * j / segments
                y = center_y + math.cos(ang) * radius
                z = center_z + math.sin(ang) * radius
                hub_verts.append(seated_vertex(x, y, z))
        for j in range(segments):
            j2 = (j + 1) % segments
            hub_faces.append((j, j2, segments + j2, segments + j))
        hub_faces.extend([tuple(reversed(range(segments))), tuple(segments + j for j in range(segments))])
        hub = create_mesh_object("Wreck_PropellerHub_{}".format(index), hub_verts, hub_faces,
                                  ship_col, (mat_metal,), parent=ship_root)
        recalc_normals(hub)

        for blade_i in range(3):
            if index == "Starboard" and blade_i == 1:
                continue  # One blade was torn away in the grounding.
            ang = math.tau * blade_i / 3.0 + 0.18
            radial_y, radial_z = math.cos(ang), math.sin(ang)
            tangent_y, tangent_z = -radial_z, radial_y
            inner_r, outer_r = 0.20, (0.54 if index == "Port" and blade_i == 2 else 1.02)
            inner_w, outer_w = 0.20, 0.33
            outline = [
                (inner_r, -inner_w), (outer_r * 0.72, -outer_w),
                (outer_r, -outer_w * 0.52), (outer_r * 0.92, outer_w),
                (inner_r, inner_w),
            ]
            blade_verts = []
            for xside in (-0.09, 0.09):
                for r, tangent in outline:
                    y = center_y + radial_y * r + tangent_y * tangent
                    z = center_z + radial_z * r + tangent_z * tangent
                    blade_verts.append(seated_vertex(center_x + xside, y, z))
            n = len(outline)
            blade_faces = [tuple(reversed(range(n))), tuple(n + i for i in range(n))]
            for j in range(n):
                j2 = (j + 1) % n
                blade_faces.append((j, j2, n + j2, n + j))
            blade = create_mesh_object(
                "Wreck_PropellerBlade_{}_{}".format(index, blade_i), blade_verts, blade_faces,
                ship_col, (mat_metal,), parent=ship_root
            )
            recalc_normals(blade)

    # The propeller hubs project beyond the upward-facing hull bottom so the
    # overturned orientation reads clearly in both the render and silhouette.
    add_propeller(12.15, -0.92, 2.58, "Port")
    add_propeller(12.15, 0.92, 2.58, "Starboard")

    # The rudder hangs from the stern assembly and is visible above the wreck.
    rudder_outline = [(10.45, -0.12, 0.55), (11.65, -0.12, 0.62),
                      (11.95, -0.12, 1.60), (11.35, -0.12, 2.05),
                      (10.70, -0.12, 1.35)]
    rudder_verts = [seated_vertex(x, y, z) for x, y, z in rudder_outline]
    rudder_verts += [seated_vertex(x, y + 0.24, z) for x, y, z in rudder_outline]
    n = len(rudder_outline)
    rudder_faces = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
    for i in range(n):
        j = (i + 1) % n
        rudder_faces.append((i, j, n + j, n + i))
    rudder = create_mesh_object("Wreck_Stern_Rudder", rudder_verts, rudder_faces,
                                ship_col, (mat_keel,), parent=ship_root)
    recalc_normals(rudder)

    # Bent snapped deck/wheelhouse frame fragments. Most superstructure is
    # buried beneath the island; only these small edge fragments remain visible.
    add_beam("Wreck_Cabin_Frame_A", (7.2, -2.48, -0.48), (8.0, -2.60, 0.72), 0.20, 0.18,
             mat_deck, debris_col)
    add_beam("Wreck_Cabin_Frame_B", (7.8, -2.58, 0.60), (9.1, -2.43, 0.20), 0.17, 0.16,
             mat_deck, debris_col)
    add_beam("Wreck_Cabin_Frame_C", (7.7, -2.52, 0.34), (8.65, -2.56, 0.95), 0.13, 0.16,
             mat_keel, debris_col)
    add_beam("Wreck_Cabin_Frame_D", (-4.8, 2.55, -0.30), (-5.55, 2.66, 0.46), 0.18, 0.16,
             mat_deck, debris_col)
    add_box("Wreck_Crushed_Cabin_Roof_Fragment", (8.45, 2.34, -0.12), (1.10, 0.82, 0.24),
            mat_deck, debris_col, parent=ship_root)

    # Clear only local clashing vegetation in this composition. The source FBX
    # remains untouched; this hide state belongs to the newly imported scene.
    plant_pattern = re.compile(r"tree|pine|broadleaf|grass|shrub|fern|wildflower|flower|foliage|reed", re.I)
    centerline_a = world_xy(-LOCAL_HALF_LENGTH - 0.2, 0.0)
    centerline_b = world_xy(LOCAL_HALF_LENGTH + 0.2, 0.0)
    hidden_plants = []
    for obj in imported_objects:
        if obj.type != "MESH" or obj is west or (east is not None and obj is east):
            continue
        if not plant_pattern.search(obj.name):
            continue
        p = obj.matrix_world.translation
        if closest_point_segment_2d(p.x, p.y, centerline_a[0], centerline_a[1],
                                    centerline_b[0], centerline_b[1]) <= 5.25:
            obj.hide_render = True
            obj.hide_viewport = True
            obj.hide_set(True)
            hidden_plants.append(obj)

    # A few pieces of driftwood and salvage sit against the surrounding slope.
    # These are placed on the terrain, not scattered randomly over the island.
    ground_contact_errors = []

    def ground_local_z(local_x, local_y, height=0.0):
        # Solve along local Z against a vertical terrain ray, preserving the
        # rigid ship transform while grounding each independent salvage piece.
        bpy.context.view_layer.update()
        matrix = ship_root.matrix_world
        z = -CONTACT_OFFSET
        for _ in range(5):
            world_point = matrix @ Vector((local_x, local_y, z))
            ground = sample_terrain_z(world_point.x, world_point.y)
            target_height = ground + height if ground is not None else WATER_Z + min(height, 0.08)
            z += (target_height - world_point.z) / max(0.1, matrix.col[2].z)
        contact = matrix @ Vector((local_x, local_y, z))
        ground = sample_terrain_z(contact.x, contact.y)
        expected = ground + height if ground is not None else WATER_Z + min(height, 0.08)
        ground_contact_errors.append(abs(contact.z - expected))
        return z

    add_beam("Debris_Driftwood_Log_01", (-7.8, -4.2, ground_local_z(-7.8, -4.2, 0.16)),
             (-5.9, -4.0, ground_local_z(-5.9, -4.0, 0.16)), 0.34, 0.26,
             mat_wood, debris_col)
    add_beam("Debris_Driftwood_Log_02", (4.1, 4.15, ground_local_z(4.1, 4.15, 0.13)),
             (5.8, 4.45, ground_local_z(5.8, 4.45, 0.13)), 0.28, 0.23,
             mat_wood, debris_col)
    add_beam("Debris_Broken_Plank", (-10.1, 3.9, ground_local_z(-10.1, 3.9, 0.10)),
             (-8.4, 4.1, ground_local_z(-8.4, 4.1, 0.10)), 0.13, 0.12,
             mat_wood, debris_col)
    add_box("Debris_Rescue_Canister", (-1.0, -4.35, ground_local_z(-1.0, -4.35, 0.34)),
            (0.82, 0.58, 0.68), mat_rescue, debris_col, parent=ship_root)
    add_box("Debris_Salvage_Crate", (9.8, 3.35, ground_local_z(9.8, 3.35, 0.32)),
            (0.78, 0.72, 0.64), mat_wood, debris_col, parent=ship_root)

    # Terrain-conforming grounding scar: exposed wet shale and compacted dark
    # earth, with an irregular perimeter. No sand or beach is introduced.
    site_materials = (
        create_material("WreckSite_Wet_Shale", (0.095, 0.115, 0.105, 1), 0.94),
        create_material("WreckSite_Crushed_Basalt", (0.125, 0.145, 0.125, 1), 0.98),
        create_material("WreckSite_Weathered_Earth", (0.135, 0.145, 0.105, 1), 1.0),
        create_material("WreckSite_Edge_Earth", (0.145, 0.165, 0.09, 1), 1.0),
    )
    site_verts, site_valid, site_faces, site_indices = [], [], [], []
    segments, rings = 64, 9
    for ring in range(rings):
        radius = 0.025 + ring / (rings - 1) * 0.975
        for segment in range(segments):
            angle = math.tau * segment / segments
            irregular = 1.0 + 0.075 * math.sin(angle * 5 + 0.4) + 0.045 * math.sin(angle * 11)
            lx = math.cos(angle) * 14.5 * radius * irregular
            ly = math.sin(angle) * 4.95 * radius * irregular
            wx, wy = world_xy(lx, ly)
            ground = sample_terrain_z(wx, wy)
            valid = ground is not None and ground > WATER_Z + 0.14
            site_valid.append(valid)
            site_verts.append((wx, wy, (ground if valid else WATER_Z) + 0.035))
    for ring in range(rings - 1):
        for segment in range(segments):
            a = ring * segments + segment
            b = ring * segments + (segment + 1) % segments
            c, d = b + segments, a + segments
            for face in ((a, b, c), (a, c, d)):
                if not all(site_valid[i] for i in face):
                    continue
                va, vb, vc = (Vector(site_verts[i]) for i in face)
                normal = (vb - va).cross(vc - va)
                if normal.length < 0.00001 or abs(normal.normalized().z) < 0.57:
                    continue  # Keep the scar off sheer cliff faces.
                site_faces.append(face)
                site_indices.append(3 if ring >= rings - 3 else random.choice((0, 1, 1, 2)))
    site = create_mesh_object("Debris_Site_Grounding_Scar", site_verts, site_faces,
                              debris_col, site_materials, site_indices, root)
    recalc_normals(site)

    # Rubble is concentrated at the hull sides and impact end, with every
    # boulder sampled independently against the existing island surface.
    grounded_stones = 0
    for index in range(30):
        lx = random.uniform(-12.5, 12.0)
        ly = random.choice((-1, 1)) * random.uniform(3.15, 5.15)
        wx, wy = world_xy(lx, ly)
        ground = sample_terrain_z(wx, wy)
        if ground is None or ground < WATER_Z + 0.18:
            continue
        radius = random.uniform(0.17, 0.46)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1,
                                            location=(wx, wy, ground + radius * 0.27))
        stone = bpy.context.object
        stone.name = "Debris_Site_Basalt_{:02d}".format(index)
        stone.scale = (radius * 1.45, radius, radius * 0.65)
        stone.rotation_euler = (0.08, -0.10, random.uniform(0, math.tau))
        stone.data.materials.append(site_materials[1 if index % 3 else 0])
        move_to_collection(stone, debris_col)
        stone.parent = root
        grounded_stones += 1

    for index, (lx, ly) in enumerate(((-5.6, 3.9), (-2.7, -3.8), (3.6, 4.2), (7.4, -3.7))):
        add_torn_plate("Debris_Grounded_Hull_Panel_{:02d}".format(index), [
            (lx - 0.65, ly - 0.3, ground_local_z(lx - 0.65, ly - 0.3, 0.09)),
            (lx + 0.55, ly - 0.25, ground_local_z(lx + 0.55, ly - 0.25, 0.10)),
            (lx + 0.33, ly + 0.46, ground_local_z(lx + 0.33, ly + 0.46, 0.20)),
            (lx - 0.45, ly + 0.25, ground_local_z(lx - 0.45, ly + 0.25, 0.08)),
        ], mat_bottom_dark if index % 2 else mat_side)

    # Batch repeated detail meshes to avoid one renderer per small rock/rivet.
    for prefix, combined_name in (
        ("Debris_Site_Basalt_", "Debris_Site_Basalt_Rubble"),
        ("Wreck_Rivet_", "Wreck_Riveted_Fasteners"),
    ):
        parts = [o for o in scene.objects if o.type == "MESH" and o.name.startswith(prefix)]
        if len(parts) > 1:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in parts:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = parts[0]
            bpy.ops.object.join()
            combined = bpy.context.object
            combined.name = combined_name
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # Match Unity's crash-site clearing against the complete exported footprint,
    # including the grounded rubble. Crown bounds count as well as plant pivots.
    bpy.context.view_layer.update()
    footprint_bounds = [bbox_world(o) for o in list(ship_col.objects) + list(debris_col.objects)
                        if o.type == "MESH"]
    site_min_x = min(b[0] for b in footprint_bounds) - 0.85
    site_max_x = max(b[1] for b in footprint_bounds) + 0.85
    site_min_y = min(b[2] for b in footprint_bounds) - 0.85
    site_max_y = max(b[3] for b in footprint_bounds) + 0.85
    for obj in imported_objects:
        if obj.type != "MESH" or not plant_pattern.search(obj.name) or obj in hidden_plants:
            continue
        bounds = bbox_world(obj)
        if bounds[1] >= site_min_x and bounds[0] <= site_max_x and \
                bounds[3] >= site_min_y and bounds[2] <= site_max_y:
            obj.hide_render = True
            obj.hide_viewport = True
            obj.hide_set(True)
            hidden_plants.append(obj)

    # The imported Unity-only cliff shader otherwise renders white in Blender.
    # This material is context-only; the original twin-island FBX is untouched.
    preview_basalt = create_material("PreviewOnly_Island_Basalt", (0.235, 0.265, 0.25, 1), 0.96)
    for terrain_object in (east, west):
        if terrain_object is not None and len(terrain_object.data.materials) > 1:
            terrain_object.data.materials[1] = preview_basalt

    # -------------------------------------------------------------------------
    # Preview-only water, camera and lights.
    # -------------------------------------------------------------------------
    water_mat = create_material("Preview_Water_Teal", (0.018, 0.105, 0.145, 1.0), 0.24, 0.12)
    bpy.ops.mesh.primitive_plane_add(size=250.0, location=(0.0, 45.0, WATER_Z))
    water = bpy.context.object
    water.name = "PreviewOnly_Water"
    water.data.materials.append(water_mat)
    move_to_collection(water, preview_col)

    def aim_at(obj, target):
        direction = Vector(target) - obj.location
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    target = Vector((CENTER_XY.x, CENTER_XY.y + 0.8, plane_z + 3.8))
    bpy.ops.object.camera_add(location=(CENTER_XY.x - 8.0, CENTER_XY.y + 34.0,
                                        plane_z + 24.0))
    camera = bpy.context.object
    camera.name = "PreviewOnly_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 78.0
    camera.data.lens = 50.0
    aim_at(camera, target)
    move_to_collection(camera, preview_col)
    scene.camera = camera
    context_camera_location = Vector(camera.location)
    context_camera_scale = camera.data.ortho_scale

    bpy.ops.object.light_add(type="SUN", location=(-10.0, -8.0, 48.0))
    sun = bpy.context.object
    sun.name = "PreviewOnly_Sun"
    sun.data.energy = 2.2
    sun.rotation_euler = (math.radians(28.0), math.radians(-23.0), math.radians(-32.0))
    move_to_collection(sun, preview_col)

    bpy.ops.object.light_add(type="AREA", location=(CENTER_XY.x - 12.0, CENTER_XY.y - 8.0,
                                                     plane_z + 28.0))
    fill = bpy.context.object
    fill.name = "PreviewOnly_Fill"
    fill.data.energy = 900.0
    fill.data.shape = "DISK"
    fill.data.size = 24.0
    aim_at(fill, target)
    move_to_collection(fill, preview_col)

    world = bpy.data.worlds.new("Gate26_Preview_World")
    world.use_nodes = True
    world_nodes = world.node_tree.nodes
    background = next((node for node in world_nodes if node.type == "BACKGROUND"), None)
    world_output = next((node for node in world_nodes if node.type == "OUTPUT_WORLD"), None)
    if background is None:
        background = world_nodes.new("ShaderNodeBackground")
    if world_output is None:
        world_output = world_nodes.new("ShaderNodeOutputWorld")
    if not any(link.from_node == background and link.to_node == world_output
               for link in world.node_tree.links):
        world.node_tree.links.new(background.outputs[0], world_output.inputs[0])
    background.inputs[0].default_value = (0.018, 0.07, 0.095, 1.0)
    background.inputs[1].default_value = 0.48
    scene.world = world

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = PREVIEW_PATH
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"
    scene.camera.data.dof.use_dof = False

    # Keep the composition file viewable in the user's Blender viewport.
    bpy.context.view_layer.objects.active = ship_root
    ship_root.select_set(True)

    # Render before FBX export; only objects in Environment/Ship/Debris can be
    # selected for export, so preview water, camera and lights cannot leak out.
    bpy.ops.render.render(write_still=True)

    # A separate close preview makes the upside-down hull, keel and stern
    # fittings readable while the primary image keeps both islands in frame.
    detail_target = Vector((CENTER_XY.x, CENTER_XY.y, plane_z + 3.8))
    camera.location = (CENTER_XY.x - 5.0, CENTER_XY.y + 11.0, plane_z + 17.0)
    camera.data.ortho_scale = 36.0
    aim_at(camera, detail_target)
    scene.render.filepath = DETAIL_PREVIEW_PATH
    bpy.ops.render.render(write_still=True)

    camera.location = context_camera_location
    camera.data.ortho_scale = context_camera_scale
    aim_at(camera, target)
    scene.render.filepath = PREVIEW_PATH

    # Keep both islands in the Blender source for context, but export only the
    # wreck and salvage. The Unity asset should not carry duplicate island meshes.
    export_objects = list(ship_col.objects) + list(debris_col.objects)
    for obj in export_objects:
        if obj.type == "MESH":
            if not obj.name.startswith(("Wreck_", "Debris_")):
                raise RuntimeError("Unexpected environment mesh in wreck export: " + obj.name)
            if any(not all(math.isfinite(value) for value in vertex.co) for vertex in obj.data.vertices):
                raise RuntimeError("Non-finite wreck vertex: " + obj.name)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in export_objects:
        if obj.name in bpy.context.view_layer.objects:
            obj.select_set(True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in export_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = ship_root
    bpy.ops.export_scene.fbx(
        filepath=FBX_PATH,
        use_selection=True,
        object_types={"EMPTY", "MESH"},
        axis_forward="-Z",
        axis_up="Y",
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=False,
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        path_mode="AUTO",
    )
    bpy.ops.object.select_all(action="DESELECT")

    # Persist the editable Blender scene with environment context after export.
    scene.render.filepath = PREVIEW_PATH
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

    # QA captures the exact terrain sample and what was excluded from export.
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bpy.context.view_layer.update()
    ship_meshes = [o for o in list(ship_col.objects) + list(debris_col.objects) if o.type == "MESH"]
    ship_bounds = [bbox_world(o) for o in ship_meshes]
    ship_world_bounds = {
        "x": [round(min(b[0] for b in ship_bounds), 3), round(max(b[1] for b in ship_bounds), 3)],
        "y": [round(min(b[2] for b in ship_bounds), 3), round(max(b[3] for b in ship_bounds), 3)],
        "z": [round(min(b[4] for b in ship_bounds), 3), round(max(b[5] for b in ship_bounds), 3)],
    }
    qa = {
        "asset": "Gate26_CapsizedWreck",
        "source_fbx": os.path.relpath(INPUT_FBX, PROJECT_ROOT).replace("\\", "/"),
        "selected_island": terrain.name,
        "placement": {
            "center_xy": [CENTER_XY.x, CENTER_XY.y],
            "heading_degrees": HEADING_DEG,
            "terrain_z_at_center": round(center_ground_z, 3),
            "ship_root_z": round(plane_z + CONTACT_OFFSET, 3),
            "fitted_plane_z": round(plane_z, 3),
            "fitted_plane_slope_degrees": round(math.degrees(
                math.atan(math.hypot(plane_dx, plane_dy))), 3),
            "terrain_attachment": "Rigid ship aligned to a terrain-only least-squares plane; hull overhangs shoreline",
            "world_bounds": ship_world_bounds,
        },
        "nominal_ship_dimensions_m": {"length": LENGTH, "beam": BEAM},
        "composition": {
            "imported_environment_objects": len(imported_objects),
            "hidden_conflicting_vegetation": len(hidden_plants),
            "hidden_vegetation_names": [o.name for o in hidden_plants],
            "exported_object_count": len(export_objects),
            "max_salvage_contact_error_m": round(max(ground_contact_errors, default=0.0), 5),
            "grounding_scar_triangle_count": len(site_faces),
            "batched_rubble_and_fasteners": True,
            "damage_features": {
                "terrain_conforming_grounding_scar": True,
                "grounded_basalt_rubble_count": grounded_stones,
                "grounded_torn_hull_panels": 4,
                "individually_terrain_sampled_salvage": True,
                "damaged_propeller_blades": True,
                "tidal_grime_and_corrosion_runs": True,
                "large_jagged_midship_hull_breach": True,
                "secondary_stern_flank_breach": True,
                "recessed_blackened_interior_cavities": 2,
                "exposed_broken_ribs": 4,
                "bent_torn_hull_flaps": 2,
                "broken_central_keel_section": True,
                "vegetation_clearance_in_unity_meters": 0.85,
            },
            "fbx_contains_wreck_and_salvage_only": True,
            "terrain_raycast_fallback_count": terrain_fallbacks,
            "preview_only_objects": [water.name, camera.name, sun.name, fill.name],
            "fbx_excludes_preview_only": True,
            "fbx_excludes_hidden_vegetation": True,
        },
        "outputs": {
            "script": os.path.relpath(SCRIPT_PATH, PROJECT_ROOT).replace("\\", "/"),
            "blend": os.path.relpath(BLEND_PATH, PROJECT_ROOT).replace("\\", "/"),
            "fbx": os.path.relpath(FBX_PATH, PROJECT_ROOT).replace("\\", "/"),
            "preview_png": os.path.relpath(PREVIEW_PATH, PROJECT_ROOT).replace("\\", "/"),
            "detail_preview_png": os.path.relpath(DETAIL_PREVIEW_PATH, PROJECT_ROOT).replace("\\", "/"),
            "qa_json": os.path.relpath(QA_PATH, PROJECT_ROOT).replace("\\", "/"),
        },
    }
    with open(QA_PATH, "w", encoding="utf-8") as handle:
        json.dump(qa, handle, ensure_ascii=False, indent=2)

    print("Gate26 capsized wreck created.")
    print("Island: {} at XY ({:.2f}, {:.2f}), terrain Z {:.2f}".format(
        terrain.name, CENTER_XY.x, CENTER_XY.y, center_ground_z
    ))
    print("Hidden conflicting plants: {}".format(len(hidden_plants)))
    print("Preview: {}".format(PREVIEW_PATH))
    print("Detail preview: {}".format(DETAIL_PREVIEW_PATH))
    print("Blend: {}".format(BLEND_PATH))
    print("FBX: {}".format(FBX_PATH))
    print("QA: {}".format(QA_PATH))


if __name__ == "__main__":
    main()
