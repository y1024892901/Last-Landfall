"""Generate the remaining Last Landfall scenario infrastructure assets.

Run with Blender 5.2 from any working directory:
    blender --background --python Tools/Blender/create_scenario_infrastructure.py

Each new asset gets its own editable .blend, Unity-ready .fbx, and preview.
Existing output files are preserved: an asset is skipped if any target exists.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
ART_SOURCE = ROOT / "Assets/LastLandfall/Art/Source"
MODELS = ROOT / "Assets/LastLandfall/Resources/Models"
PREVIEWS = ROOT / "Assets/LastLandfall/Art/Previews"
MANIFEST_PATH = ROOT / "Assets/LastLandfall/Art/Previews/Infrastructure/ScenarioInfrastructure_Manifest.json"
OVERVIEW_PATH = ROOT / "Assets/LastLandfall/Art/Previews/Infrastructure/ScenarioInfrastructure_Overview.png"
ARGUMENTS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
REBUILD_ALLOWED_IDS = {
    "DriftwoodCollectionBoom", "FishingDock", "WeatherTideBuoy", "Shipyard",
}
REBUILD_IDS = set(ARGUMENTS) & REBUILD_ALLOWED_IDS
COLLECTION = None
ROOT_OBJECT = None
OBJECTS = []
M = {}


ASSETS = [
    {"id": "DriftwoodCollectionBoom", "name": "漂木收集浮栅", "level": 1, "group": "Infrastructure", "footprint": "6×2", "height": 1.2, "kind": "boom"},
    {"id": "FishingDock", "name": "渔船码头", "level": 1, "group": "Infrastructure", "footprint": "4×2", "height": 2.0, "kind": "fishing_dock"},
    {"id": "WeatherTideBuoy", "name": "气象与潮位浮标", "level": 4, "group": "Infrastructure", "footprint": "1×1", "height": 2.7, "kind": "buoy"},
    {"id": "Shipyard", "name": "船坞", "level": 4, "group": "Infrastructure", "footprint": "5×4", "height": 4.2, "kind": "shipyard"},
]


def material(name, color, metallic=0.0, roughness=0.82):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    output = nodes.new("ShaderNodeOutputMaterial")
    mat.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def make_materials(asset_id):
    prefix = asset_id + " | "
    return {
        "wood": material(prefix + "salt-worn cedar", (0.47, 0.35, 0.23)),
        "wood_light": material(prefix + "sun-bleached boards", (0.66, 0.55, 0.38)),
        "wood_dark": material(prefix + "tarred timber", (0.22, 0.18, 0.13)),
        "teal": material(prefix + "faded sea green", (0.22, 0.39, 0.37), 0.20),
        "teal_light": material(prefix + "patched enamel", (0.43, 0.55, 0.49), 0.18),
        "teal_dark": material(prefix + "deep green metal", (0.12, 0.25, 0.24), 0.22),
        "rust": material(prefix + "rust repair", (0.60, 0.29, 0.16), 0.12),
        "iron": material(prefix + "dark iron", (0.12, 0.17, 0.17), 0.45),
        "stone": material(prefix + "pale rock concrete", (0.48, 0.48, 0.41)),
        "canvas": material(prefix + "weathered cream canvas", (0.78, 0.72, 0.57)),
        "canvas_teal": material(prefix + "patched teal canvas", (0.31, 0.48, 0.43)),
        "glass": material(prefix + "smoky blue glass", (0.12, 0.29, 0.32), 0.08, 0.38),
        "amber": material(prefix + "signal amber", (0.95, 0.55, 0.19), 0.05, 0.36),
        "medical": material(prefix + "medical signal", (0.72, 0.27, 0.19)),
        "panel": material(prefix + "solar slate", (0.08, 0.20, 0.25), 0.28, 0.48),
        "water": material(prefix + "water enamel", (0.20, 0.43, 0.48), 0.14, 0.42),
        "paper": material(prefix + "archive paper", (0.72, 0.64, 0.46)),
    }


def add_mesh(name, vertices, faces, mat, bevel=0.0):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(clean_customdata=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    COLLECTION.objects.link(obj)
    if mat:
        mesh.materials.append(mat)
    for face in mesh.polygons:
        face.use_smooth = False
    if bevel > 0:
        modifier = obj.modifiers.new("Worn edge chamfer", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
    OBJECTS.append(obj)
    return obj


def box(name, location, size, mat, bevel=0.025, rotation=None):
    x, y, z = (float(v) * 0.5 for v in size)
    verts = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
             (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    obj = add_mesh(name, verts, faces, mat, min(bevel, min(size) * 0.18) if bevel else 0.0)
    obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    return obj


def cylinder(name, location, radius, depth, mat, vertices=10, rotation=None, radius_top=None):
    top_r = radius if radius_top is None else radius_top
    verts = []
    for z, r in ((-depth * 0.5, radius), (depth * 0.5, top_r)):
        for i in range(vertices):
            a = math.tau * i / vertices
            verts.append((math.cos(a) * r, math.sin(a) * r, z))
    faces = [tuple(range(vertices - 1, -1, -1)), tuple(range(vertices, vertices * 2))]
    for i in range(vertices):
        j = (i + 1) % vertices
        faces.append((i, j, vertices + j, vertices + i))
    obj = add_mesh(name, verts, faces, mat)
    obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    return obj


def rod(name, start, end, width, mat, width_y=None):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = box(name, (start + end) * 0.5, (width, width if width_y is None else width_y, delta.length), mat, 0.004)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def gable_roof(name, width, depth, wall_top, rise, mat, thickness=0.12):
    half = depth * 0.5
    slope_len = math.sqrt(half * half + rise * rise)
    angle = math.atan2(rise, half)
    box(name + " left roof plane", (0, -half * 0.5, wall_top + rise * 0.5),
        (width + 0.32, slope_len + 0.12, thickness), mat, 0.012, (angle, 0, 0))
    box(name + " right roof plane", (0, half * 0.5, wall_top + rise * 0.5),
        (width + 0.32, slope_len + 0.12, thickness), M["teal_light"] if mat == M["teal"] else mat,
        0.012, (-angle, 0, 0))
    box(name + " ridge cap", (0, 0, wall_top + rise + 0.03), (width + 0.40, 0.13, 0.10), M["wood_dark"], 0.012)
    for index, x in enumerate((-width * 0.38, -width * 0.13, width * 0.13, width * 0.38)):
        box(name + " roof seam %02d" % index, (x, 0, wall_top + rise + 0.07), (0.026, depth * 0.92, 0.025), M["rust"] if index == 3 else M["iron"], 0.003)


def cabin(name, width, depth, wall_h, roof_rise, wall_mat=None, roof_mat=None, foundation=True):
    wall_mat = wall_mat or M["wood"]
    roof_mat = roof_mat or M["teal"]
    if foundation:
        box(name + " stone footing", (0, 0, 0.10), (width + 0.20, depth + 0.18, 0.20), M["stone"], 0.025)
    box(name + " floor", (0, 0, 0.23), (width, depth, 0.12), M["wood_dark"], 0.016)
    box(name + " wall core", (0, 0, 0.23 + wall_h * 0.5), (width * 0.94, depth * 0.94, wall_h), wall_mat, 0.018)
    # The front service wall uses contrasting, readable pieces rather than decals.
    box(name + " front door surround", (-width * 0.22, -depth * 0.485, 0.23 + wall_h * 0.39),
        (width * 0.28, 0.07, wall_h * 0.74), M["wood_dark"], 0.012)
    box(name + " front door", (-width * 0.22, -depth * 0.53, 0.23 + wall_h * 0.39),
        (width * 0.22, 0.035, wall_h * 0.68), M["wood_light"], 0.008)
    box(name + " door patch", (-width * 0.22, -depth * 0.55, 0.37), (width * 0.20, 0.02, 0.18), M["rust"], 0.006)
    box(name + " front window frame", (width * 0.23, -depth * 0.49, 0.23 + wall_h * 0.61),
        (width * 0.28, 0.05, wall_h * 0.27), M["wood_dark"], 0.008)
    box(name + " front window glass", (width * 0.23, -depth * 0.52, 0.23 + wall_h * 0.61),
        (width * 0.22, 0.025, wall_h * 0.20), M["glass"], 0.004)
    box(name + " window mullion", (width * 0.23, -depth * 0.538, 0.23 + wall_h * 0.61),
        (0.025, 0.015, wall_h * 0.22), M["wood_light"], 0.002)
    gable_roof(name + " roof", width, depth, 0.23 + wall_h, roof_rise, roof_mat)
    for x in (-width * 0.45, width * 0.45):
        for y in (-depth * 0.43, depth * 0.43):
            box(name + " corner timber", (x, y, 0.23 + wall_h * 0.5), (0.075, 0.075, wall_h + 0.04), M["wood_dark"], 0.008)


def plank_platform(name, width, depth, z=0.18, count=7, supports=True):
    if supports:
        for x in (-width * 0.42, width * 0.42):
            for y in (-depth * 0.42, depth * 0.42):
                box(name + " pile", (x, y, z * 0.48), (0.13, 0.13, z * 0.96), M["wood_dark"], 0.012)
    for i in range(count):
        x = -width * 0.46 + width * 0.92 * (i + 0.5) / count
        box(name + " deck plank %02d" % i, (x, 0, z), (width * 0.92 / count - 0.025, depth, 0.12), M["wood_light"] if i % 3 == 0 else M["wood"], 0.012)
    for y in (-depth * 0.49, depth * 0.49):
        box(name + " edge beam", (0, y, z - 0.05), (width, 0.075, 0.10), M["wood_dark"], 0.01)


def crate(name, location, size=(0.34, 0.32, 0.32)):
    x, y, z = location
    box(name + " body", (x, y, z + size[2] * 0.5), size, M["wood"], 0.015)
    for side in (-1, 1):
        box(name + " strap", (x + side * size[0] * 0.28, y - size[1] * 0.505, z + size[2] * 0.5),
            (size[0] * 0.08, 0.018, size[2] * 0.9), M["wood_dark"], 0.003)


def add_lamp(name, location):
    cylinder(name + " base", location, 0.11, 0.10, M["iron"], vertices=8)
    cylinder(name + " amber lens", (location[0], location[1], location[2] + 0.10), 0.075, 0.12, M["amber"], vertices=8)
    box(name + " cap", (location[0], location[1], location[2] + 0.19), (0.17, 0.17, 0.045), M["rust"], 0.006)


def add_small_cross(name, center, size=0.34):
    x, y, z = center
    box(name + " vertical", (x, y, z), (size * 0.25, 0.035, size), M["medical"], 0.004)
    box(name + " horizontal", (x, y, z + size * 0.10), (size * 0.82, 0.035, size * 0.23), M["medical"], 0.004)


def build_boom():
    # A shallow U-shaped floating log barrier; separate rope links make its path readable.
    buoy_points = [(-2.50, -0.15), (-1.50, -0.48), (-0.50, -0.62),
                   (0.50, -0.60), (1.50, -0.40), (2.50, -0.10)]
    segments = list(zip(buoy_points[:-1], buoy_points[1:]))
    for index, (a, b) in enumerate(segments):
        rod("Floating driftwood log %02d" % index, (a[0], a[1], 0.46), (b[0], b[1], 0.46), 0.24, M["wood"])
        rod("Log dark end binding %02d" % index, (a[0], a[1], 0.46), (a[0] + (b[0]-a[0])*0.12, a[1] + (b[1]-a[1])*0.12, 0.46), 0.27, M["wood_dark"])
    for index, (x, y) in enumerate(buoy_points):
        cylinder("Boom flotation buoy %02d" % index, (x, y, 0.30), 0.27, 0.36, M["teal"], 10)
        cylinder("Buoy cap %02d" % index, (x, y, 0.51), 0.18, 0.07, M["rust"], 10)
        rod("Mooring anchor line %02d" % index, (x, y, 0.22), (x + (0.42 if index % 2 else -0.42), y - 0.22, 0.04), 0.025, M["iron"])
    for index, (a, b) in enumerate(segments):
        rod("Boom tension line %02d" % index, (a[0], a[1], 0.58), (b[0], b[1], 0.58), 0.035, M["iron"])


def build_fishing_dock():
    plank_platform("Fishing dock", 3.80, 1.65, 1.20, 12)
    # Shore gangway and mooring posts.
    box("Gangway", (0, 1.47, 0.93), (1.35, 1.30, 0.12), M["wood"], 0.012, (math.radians(-25), 0, 0))
    for x in (-0.50, 0.50):
        rod("Gangway landing pile", (x, 1.38, 0.05), (x, 1.38, 1.00), 0.11, M["wood_dark"])
        rod("Gangway outer pile", (x, 1.92, 0.05), (x, 1.92, 0.76), 0.11, M["wood_dark"])
    for x in (-1.62, 1.62):
        for y in (-0.62, 0.62):
            rod("Dock pile", (x, y, 0.05), (x, y, 1.18), 0.14, M["wood_dark"])
        for y in (-0.70, 0.70):
            box("Mooring bollard", (x, y, 1.45), (0.16, 0.16, 0.42), M["iron"], 0.015)
    box("Net winch base", (-1.10, 0.16, 1.48), (0.55, 0.52, 0.30), M["teal_dark"], 0.02)
    cylinder("Winch drum", (-1.10, -0.14, 1.68), 0.20, 0.48, M["wood_dark"], 10, (0, math.pi / 2, 0))
    for x in (-1.38, -0.82):
        cylinder("Winch cheek plate", (x, -0.14, 1.68), 0.27, 0.05, M["rust"], 10, (0, math.pi / 2, 0))
    rod("Winch handle", (-1.52, -0.14, 1.68), (-1.70, -0.14, 1.92), 0.04, M["iron"])
    # Folded net stack and fish basket are props, not a second boat model.
    box("Folded fishing net", (0.40, -0.18, 1.38), (0.72, 0.44, 0.22), M["teal"], 0.025)
    for i in range(4):
        rod("Net mesh strand", (0.08 + i * 0.18, -0.40, 1.50), (0.08 + i * 0.18, 0.05, 1.50), 0.015, M["wood_light"])
    crate("Catch basket", (1.04, -0.26, 1.27), (0.43, 0.35, 0.34))
    add_lamp("Dock lantern", (1.55, 0.48, 1.72))


def build_buoy():
    # Floating lower hull with a capped octagonal mast and exposed sensors.
    cylinder("Tide buoy float", (0, 0, 0.40), 0.72, 0.46, M["teal"], 12, radius_top=0.58)
    cylinder("Lower iron keel", (0, 0, 0.13), 0.30, 0.18, M["iron"], 10)
    for i in range(8):
        a = math.tau * i / 8
        box("Buoy rust belt", (math.cos(a) * 0.62, math.sin(a) * 0.62, 0.40),
            (0.15, 0.055, 0.30), M["rust"], 0.006, (0, 0, a))
    cylinder("Buoy deck", (0, 0, 0.66), 0.56, 0.10, M["teal_light"], 12)
    rod("Sensor mast", (0, 0, 0.70), (0, 0, 2.38), 0.055, M["iron"])
    cylinder("Wind sensor hub", (0, 0, 2.28), 0.12, 0.12, M["rust"], 8)
    rod("Wind vane crossbar", (-0.53, 0, 2.30), (0.53, 0, 2.30), 0.03, M["teal_light"])
    box("Wind vane arrow", (0.50, 0, 2.30), (0.20, 0.09, 0.12), M["amber"], 0.008)
    for side in (-1, 1):
        cylinder("Tide sensor canister", (side * 0.27, 0.0, 1.28), 0.12, 0.36, M["water"], 8)
    box("Solar telemetry plate", (0, -0.35, 0.90), (0.54, 0.42, 0.08), M["panel"], 0.008, (math.radians(20), 0, 0))
    for x in (-0.18, 0.18):
        rod("Telemetry panel front brace", (x, -0.54, 0.70), (x, -0.54, 0.83), 0.035, M["iron"])
        rod("Telemetry panel rear brace", (x, -0.16, 0.70), (x, -0.16, 0.97), 0.035, M["iron"])
    add_lamp("Buoy beacon", (0, 0, 2.36))
    for x in (-0.22, 0.22):
        rod("Mooring bridle", (x, 0, 0.18), (x * 2.3, 0.12, 0.03), 0.025, M["iron"])


def build_shipyard():
    # Slipway rails converge toward the water; gantry surrounds a partly framed hull.
    for y in (-1.05, 1.05):
        box("Slipway timber rail", (0, y, 0.18), (4.80, 0.20, 0.32), M["wood_dark"], 0.02)
        for x in (-1.85, -0.95, 0.0, 0.95, 1.85):
            box("Slipway cross tie", (x, y, 0.35), (0.26, 2.40, 0.16), M["wood"], 0.012)
    for x in (-1.86, 1.86):
        for y in (-1.00, 1.00):
            box("Gantry footing", (x, y, 0.18), (0.70, 0.70, 0.36), M["stone"], 0.035)
        rod("Gantry upright", (x, -0.93, 0.36), (x, -0.93, 3.83), 0.20, M["teal_dark"])
        rod("Gantry rear brace", (x, 0.92, 0.36), (x, -0.93, 2.95), 0.11, M["iron"])
    box("Gantry crossbeam", (0, -0.93, 3.72), (4.10, 0.24, 0.24), M["teal"], 0.03)
    box("Gantry trolley", (0, -0.93, 3.46), (0.62, 0.48, 0.32), M["rust"], 0.025)
    rod("Chain hoist", (0, -0.93, 3.40), (0, -0.93, 2.72), 0.045, M["iron"])
    for side in (-1, 1):
        rod("Hull cradle arm", (0, side * 0.76, 0.70), (0, side * 0.38, 1.03), 0.17, M["wood_light"])
        for x in (-1.0, 0.0, 1.0):
            rod("Cradle cross support", (x, side * 0.84, 0.52), (x, side * 0.38, 1.10), 0.13, M["wood"])
    for x in (-1.0, 0.0, 1.0):
        box("Keel blocking", (x, 0, 0.50), (0.36, 0.42, 0.24), M["wood_light"], 0.012)
    # A clearly recognizable unfinished launch hull ties the gantry to the shipbuilding function.
    stations = [(-1.55, 0.03, 0.84, 0.98), (-1.20, 0.32, 0.62, 1.20),
                (-0.72, 0.55, 0.57, 1.32), (0.0, 0.66, 0.56, 1.36),
                (0.72, 0.60, 0.59, 1.35), (1.20, 0.38, 0.68, 1.23),
                (1.55, 0.03, 0.92, 1.02)]
    hull_vertices = []
    hull_faces = []
    for x, half_width, keel_z, gunwale_z in stations:
        mid_z = (keel_z + gunwale_z) * 0.52
        hull_vertices.extend([
            (x, -half_width, gunwale_z + 0.16),
            (x, -half_width * 0.66, mid_z + 0.16),
            (x, 0.0, keel_z + 0.16),
            (x, half_width * 0.66, mid_z + 0.16),
            (x, half_width, gunwale_z + 0.16),
        ])
    for station_i in range(len(stations) - 1):
        a = station_i * 5
        b = (station_i + 1) * 5
        for point_i in range(4):
            hull_faces.append((a + point_i, a + point_i + 1, b + point_i + 1, b + point_i))
    hull_faces.append(tuple(range(4, -1, -1)))
    hull_faces.append(tuple(range((len(stations) - 1) * 5, len(stations) * 5)))
    add_mesh("Partially framed launch hull", hull_vertices, hull_faces, M["wood_light"], 0.008)
    box("Launch hull keel jig", (0, 0, 0.66), (3.45, 0.26, 0.18), M["wood_dark"], 0.02)
    for x, half_width, keel_z, gunwale_z in stations[1:-1]:
        mid_z = (keel_z + gunwale_z) * 0.52
        for side in (-1, 1):
            rod("Visible hull frame", (x, 0, keel_z + 0.16), (x, side * half_width, gunwale_z + 0.16), 0.055, M["wood_dark"])
            rod("Hull bilge stringer", (x - 0.22, side * half_width * 0.66, mid_z),
                (x + 0.22, side * half_width * 0.66, mid_z + 0.16), 0.045, M["wood"])
    box("Tool shed", (2.72, 0.45, 0.90), (1.12, 1.20, 1.45), M["teal"], 0.02)
    box("Tool shed roof", (2.72, 0.45, 1.67), (1.32, 1.42, 0.16), M["teal_light"], 0.018)
    box("Tool shed door", (2.72, -0.18, 0.76), (0.43, 0.05, 0.96), M["wood"], 0.008)
    add_lamp("Shipyard work light", (2.36, -0.18, 1.62))


BUILDERS = {
    "boom": build_boom,
    "fishing_dock": build_fishing_dock,
    "buoy": build_buoy,
    "shipyard": build_shipyard,
}


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for child in list(bpy.context.scene.collection.children):
        bpy.context.scene.collection.children.unlink(child)
        if child.users == 0:
            bpy.data.collections.remove(child)


def setup_scene():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Last Landfall Preview World")
    scene.world.color = (0.37, 0.39, 0.38)
    return scene


def collection_for(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def add_preview_setup(scene, asset_id, target_z):
    preview_collection = collection_for("Preview Only")
    ground_mat = material(asset_id + " | preview ground", (0.73, 0.73, 0.69))
    mesh = bpy.data.meshes.new("Preview ground Mesh")
    mesh.from_pydata([(-100, -100, -0.04), (100, -100, -0.04), (100, 100, -0.04), (-100, 100, -0.04)], [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new("Preview ground (not exported)", mesh)
    preview_collection.objects.link(ground)
    mesh.materials.append(ground_mat)
    camera_data = bpy.data.cameras.new("Preview camera")
    camera = bpy.data.objects.new("Preview camera", camera_data)
    preview_collection.objects.link(camera)
    camera.location = (7.2, -9.0, 7.2)
    target = Vector((0, 0, target_z))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 7.8
    scene.camera = camera
    light_data = bpy.data.lights.new("Preview softbox", "AREA")
    light = bpy.data.objects.new("Preview softbox", light_data)
    preview_collection.objects.link(light)
    light.location = (0, -4.0, 9.0)
    light.data.energy = 1600
    light.data.shape = "DISK"
    light.data.size = 7.0
    light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = 960
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.camera.data.lens = 52


def create_asset(asset):
    global COLLECTION, ROOT_OBJECT, OBJECTS, M
    group = asset["group"]
    source_dir = ART_SOURCE / group
    model_dir = MODELS / group
    preview_dir = PREVIEWS / group
    blend_path = source_dir / (asset["id"] + ".blend")
    fbx_path = model_dir / (asset["id"] + ".fbx")
    png_path = preview_dir / (asset["id"] + ".png")
    paths = (blend_path, fbx_path, png_path)
    if any(path.exists() for path in paths) and asset["id"] not in REBUILD_IDS:
        print("Preserving existing asset output; skipped:", asset["id"])
        return False
    if asset["id"] in REBUILD_IDS:
        print("Rebuilding current-turn asset after image review:", asset["id"])
    for directory in (source_dir, model_dir, preview_dir):
        directory.mkdir(parents=True, exist_ok=True)

    clear_scene()
    scene = setup_scene()
    COLLECTION = collection_for(asset["id"])
    OBJECTS = []
    M = make_materials(asset["id"])
    ROOT_OBJECT = bpy.data.objects.new(asset["id"] + "_Root", None)
    ROOT_OBJECT.empty_display_type = "PLAIN_AXES"
    ROOT_OBJECT.empty_display_size = 0.18
    COLLECTION.objects.link(ROOT_OBJECT)
    BUILDERS[asset["kind"]]()
    for obj in OBJECTS:
        obj.parent = ROOT_OBJECT
        obj.matrix_parent_inverse = ROOT_OBJECT.matrix_world.inverted()
    add_preview_setup(scene, asset["id"], asset["height"] * 0.44)
    scene.render.filepath = str(png_path)
    bpy.ops.render.render(write_still=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in COLLECTION.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = ROOT_OBJECT
    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path),
        use_selection=True,
        object_types={"EMPTY", "MESH"},
        axis_forward="-Z",
        axis_up="Y",
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="AUTO",
    )
    print("Generated:", asset["id"], blend_path, fbx_path, png_path)
    return True


def create_overview(assets):
    if OVERVIEW_PATH.exists():
        print("Preserving existing overview image:", OVERVIEW_PATH)
        return
    OVERVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Switch away from the last per-asset .blend before appending it as a library.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = setup_scene()
    overview = collection_for("Scenario Infrastructure Overview")
    preview_collection = collection_for("Preview Only")
    cols = 5
    step_x, step_y = 7.8, 7.4
    for i, asset in enumerate(assets):
        blend_path = ART_SOURCE / asset["group"] / (asset["id"] + ".blend")
        if not blend_path.exists():
            continue
        with bpy.data.libraries.load(str(blend_path), link=False) as (data_from, data_to):
            data_to.collections = [asset["id"]] if asset["id"] in data_from.collections else []
        for collection in data_to.collections:
            if collection is None:
                continue
            overview.children.link(collection)
            row, col = divmod(i, cols)
            x = (col - (cols - 1) * 0.5) * step_x
            y = ((len(assets) - 1) // cols * 0.5 - row) * step_y
            root_obj = next((obj for obj in collection.objects if obj.name.endswith("_Root")), None)
            if root_obj:
                root_obj.location = (x, y, 0)
    # A quiet warm-gray floor keeps the asset silhouettes legible.
    floor_mesh = bpy.data.meshes.new("Overview floor Mesh")
    floor_mesh.from_pydata([(-100, -100, -0.05), (100, -100, -0.05), (100, 100, -0.05), (-100, 100, -0.05)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new("Overview floor (not exported)", floor_mesh)
    preview_collection.objects.link(floor)
    floor_mesh.materials.append(material("Overview | neutral gray", (0.73, 0.73, 0.69)))
    camera_data = bpy.data.cameras.new("Overview camera")
    camera = bpy.data.objects.new("Overview camera", camera_data)
    preview_collection.objects.link(camera)
    target = Vector((0, 0, 1.2))
    camera.location = (41, -56, 70)
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 46
    scene.camera = camera
    light_data = bpy.data.lights.new("Overview softbox", "AREA")
    light = bpy.data.objects.new("Overview softbox", light_data)
    preview_collection.objects.link(light)
    light.location = (2, -18, 42)
    light.data.energy = 45000
    light.data.shape = "DISK"
    light.data.size = 24
    light.rotation_euler = (target - light.location).to_track_quat("-Z", "Y").to_euler()
    fill_data = bpy.data.lights.new("Overview fill", "AREA")
    fill = bpy.data.objects.new("Overview fill", fill_data)
    preview_collection.objects.link(fill)
    fill.location = (-28, 20, 34)
    fill.data.energy = 22000
    fill.data.shape = "DISK"
    fill.data.size = 26
    fill.rotation_euler = (target - fill.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = 2200
    scene.render.resolution_y = 1680
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OVERVIEW_PATH)
    bpy.ops.render.render(write_still=True)
    print("Generated overview:", OVERVIEW_PATH)


def main():
    for asset in ASSETS:
        create_asset(asset)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(ASSETS, ensure_ascii=False, indent=2), encoding="utf-8")
    create_overview(ASSETS)
    print("Scenario infrastructure generation finished.")


if __name__ == "__main__":
    main()
