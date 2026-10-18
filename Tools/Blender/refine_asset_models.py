"""Apply the shared Last Landfall art direction to generated Blender assets.

Run after the individual create_*.py scripts. The refinement is deliberately
additive: it preserves the existing footprints, pivots, tile interfaces, and
Unity model names while adding surface breakup and functional set dressing.
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
SOURCE_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Source"
MODEL_DIR = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models"
PREVIEW_DIR = PROJECT_ROOT / "Assets/LastLandfall/Art/Previews"

SINGLE_ASSETS = (
    "ResidentHut",
    "Greenhouse",
    "WaterPurifier",
    "StorageDepot",
    "SalvageWorkshop",
    "GeneratorStation",
    "RescueRadioCenter",
    "RescueDock",
)


def material(name, color, roughness=0.78, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = next((node for node in mat.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if shader is None:
        shader = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return mat


CEDAR = CEDAR_LIGHT = TEAL = IRON = RUST = CREAM = GLASS = SOIL = None
LEAF = LEAF_LIGHT = STONE_A = STONE_B = WATER = RUBBER = None


def initialize_detail_materials():
    """Refresh material references after Blender opens each source .blend."""
    global CEDAR, CEDAR_LIGHT, TEAL, IRON, RUST, CREAM, GLASS, SOIL
    global LEAF, LEAF_LIGHT, STONE_A, STONE_B, WATER, RUBBER
    CEDAR = material("ArtRefine | weathered cedar", (0.38, 0.28, 0.19), 0.88)
    CEDAR_LIGHT = material("ArtRefine | sun-bleached cedar", (0.59, 0.46, 0.30), 0.9)
    TEAL = material("ArtRefine | faded sea-glass metal", (0.18, 0.34, 0.34), 0.58, 0.28)
    IRON = material("ArtRefine | corroded iron", (0.12, 0.17, 0.17), 0.62, 0.42)
    RUST = material("ArtRefine | rescue rust orange", (0.72, 0.25, 0.11), 0.68, 0.18)
    CREAM = material("ArtRefine | aged canvas", (0.77, 0.68, 0.50), 0.93)
    GLASS = material("ArtRefine | storm glass", (0.16, 0.38, 0.43), 0.3, 0.08)
    SOIL = material("ArtRefine | greenhouse soil", (0.19, 0.14, 0.095), 0.96)
    LEAF = material("ArtRefine | coastal leaf", (0.25, 0.39, 0.23), 0.9)
    LEAF_LIGHT = material("ArtRefine | new leaf", (0.43, 0.54, 0.28), 0.88)
    STONE_A = material("ArtRefine | slate strata", (0.27, 0.32, 0.33), 0.95)
    STONE_B = material("ArtRefine | warm strata", (0.42, 0.39, 0.32), 0.96)
    WATER = material("ArtRefine | rescue skiff enamel", (0.92, 0.31, 0.12), 0.42, 0.12)
    RUBBER = material("ArtRefine | black rubber", (0.075, 0.09, 0.09), 0.85)


def add_detail_tag(obj):
    obj["ArtRefinement"] = "coastal-survival-v1"
    return obj


def parent_to(obj, parent):
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    add_detail_tag(obj)
    return obj


def box(name, location, dimensions, mat, parent, bevel=0.012, rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rotation is not None:
        obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    if bevel > 0:
        modifier = obj.modifiers.new("Soft worn edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return parent_to(obj, parent)


def cylinder(name, location, radius, depth, mat, parent, vertices=12, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    if rotation is not None:
        obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    return parent_to(obj, parent)


def rod(name, start, end, radius, mat, parent, vertices=10):
    a = Vector(start)
    b = Vector(end)
    direction = b - a
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=direction.length,
        location=(a + b) * 0.5,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    return parent_to(obj, parent)


def torus(name, location, major_radius, minor_radius, mat, parent, rotation=None):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=20,
        minor_segments=6,
        location=location,
        rotation=rotation or (0.0, 0.0, 0.0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return parent_to(obj, parent)


def ellipsoid(name, location, scale, mat, parent, subdivisions=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return parent_to(obj, parent)


def mesh_object(name, vertices, faces, mat, parent):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    mesh.validate(clean_customdata=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return parent_to(obj, parent)


def remove_previous_refinements():
    for obj in list(bpy.data.objects):
        if obj.get("ArtRefinement") == "coastal-survival-v1":
            bpy.data.objects.remove(obj, do_unlink=True)


def add_surface_detail():
    for mat in bpy.data.materials:
        if mat.name.startswith("Preview"):
            continue
        if not mat.use_nodes:
            continue
        shader = next((node for node in mat.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled"), None)
        if shader is None:
            continue

        name = mat.name.lower()
        if "glass" in name or "lamp" in name:
            continue
        if any(word in name for word in ("wood", "timber", "cedar", "canvas", "cloth")):
            scale, strength, distance, wave = 11.0, 0.09, 0.009, True
        elif any(word in name for word in ("stone", "cliff", "rock", "concrete", "soil")):
            scale, strength, distance, wave = 9.0, 0.13, 0.018, False
        else:
            scale, strength, distance, wave = 32.0, 0.07, 0.005, False

        if mat.get("ArtDirectionV1"):
            bump = next((node for node in mat.node_tree.nodes if node.label == "Subtle salt-worn surface"), None)
            if bump is not None:
                bump.inputs["Strength"].default_value = strength
                bump.inputs["Distance"].default_value = distance
            continue
        normal_input = shader.inputs.get("Normal")
        if normal_input is None or normal_input.is_linked:
            continue

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        texcoord = nodes.new("ShaderNodeTexCoord")
        texcoord.label = "Generated surface coordinates"
        bump = nodes.new("ShaderNodeBump")
        bump.label = "Subtle salt-worn surface"
        bump.inputs["Strength"].default_value = strength
        bump.inputs["Distance"].default_value = distance
        if wave:
            texture = nodes.new("ShaderNodeTexWave")
            texture.label = "Long weathered grain"
            texture.inputs["Scale"].default_value = scale
            texture.inputs["Distortion"].default_value = 3.0
            texture.inputs["Detail"].default_value = 2.0
            links.new(texcoord.outputs["Generated"], texture.inputs["Vector"])
            links.new(texture.outputs["Fac"], bump.inputs["Height"])
        else:
            texture = nodes.new("ShaderNodeTexNoise")
            texture.label = "Fine coastal material wear"
            texture.inputs["Scale"].default_value = scale
            texture.inputs["Detail"].default_value = 3.0
            texture.inputs["Roughness"].default_value = 0.7
            links.new(texcoord.outputs["Generated"], texture.inputs["Vector"])
            links.new(texture.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
        mat["ArtDirectionV1"] = True


def soften_greenhouse_glazing():
    """Make greenhouse panes translucent so crop silhouettes read in the render."""
    for mat in bpy.data.materials:
        if not mat.name.lower().startswith("glass |") or not mat.use_nodes:
            continue
        shader = next((node for node in mat.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled"), None)
        if shader is None or shader.inputs.get("Alpha") is None:
            continue
        shader.inputs["Alpha"].default_value = 0.34
        shader.inputs["Roughness"].default_value = 0.22
        mat.diffuse_color = (*mat.diffuse_color[:3], 0.34)
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"


def refine_resident_hut(root):
    # Small rope rails define a real porch while leaving the front step clear.
    for side in (-1.0, 1.0):
        x = side * 0.37
        for y in (-0.42, -0.22):
            box("Porch rail post", (x, y, 0.39), (0.045, 0.045, 0.22), CEDAR_LIGHT, root, 0.006)
        rod("Porch top rail", (x, -0.42, 0.49), (x, -0.22, 0.49), 0.018, CEDAR_LIGHT, root)
        rod("Porch rope rail", (x, -0.42, 0.40), (x, -0.22, 0.40), 0.008, CREAM, root, 8)
        rod("Under-deck diagonal brace", (side * 0.31, -0.28, 0.12), (side * 0.31, -0.07, 0.27), 0.022, CEDAR, root)

    # The stove flue and rain-chain make the small home read as inhabited.
    cylinder("Stove flue", (-0.22, 0.22, 0.98), 0.035, 0.32, IRON, root, 10)
    cylinder("Flue collar", (-0.22, 0.22, 0.88), 0.052, 0.035, RUST, root, 10)
    box("Flue rain hood", (-0.22, 0.22, 1.15), (0.13, 0.13, 0.035), IRON, root, 0.008)

    # A little window planter breaks up the blank side wall.
    box("Window planter", (0.37, 0.08, 0.40), (0.11, 0.31, 0.13), CEDAR, root, 0.012)
    for index, y in enumerate((-0.02, 0.08, 0.18)):
        ellipsoid("Planter leaf %02d" % index, (0.40, y, 0.50), (0.045, 0.06, 0.07), LEAF_LIGHT if index == 1 else LEAF, root)

    # A compact striped rain awning and timber braces echo the weatherproof
    # porch in the art sheet while staying within the hut's one-cell footprint.
    for side in (-1.0, 1.0):
        rod("Awning side stay", (side * 0.31, -0.31, 0.67), (side * 0.31, -0.51, 0.55), 0.018, IRON, root)
        rod("Stilt diagonal brace", (side * 0.30, 0.28, 0.08), (side * 0.30, 0.28, 0.26), 0.022, CEDAR_LIGHT, root)
    for index in range(4):
        x0 = -0.32 + index * 0.16
        x1 = x0 + 0.16
        panel = CREAM if index % 2 == 0 else RUST
        mesh_object(
            "Porch canvas panel %02d" % index,
            [(x0, -0.33, 0.68), (x1, -0.33, 0.68), (x1, -0.51, 0.55), (x0, -0.51, 0.55)],
            [(3, 2, 1, 0)],
            panel,
            root,
        )
    rod("Awning front hem", (-0.33, -0.51, 0.55), (0.33, -0.51, 0.55), 0.014, CEDAR, root)


def refine_greenhouse(root):
    # Three raised beds and repeated crop clusters add the greenhouse's purpose.
    bed_centers = ((-0.47, 0.10, 0.30, 1.12), (0.47, 0.10, 0.30, 1.12), (0.0, 0.59, 0.58, 0.30))
    for bed_index, (x, y, width, length) in enumerate(bed_centers):
        box("Raised growing bed %02d" % bed_index, (x, y, 0.255), (width, length, 0.16), CEDAR, root, 0.016)
        box("Dark soil bed %02d" % bed_index, (x, y, 0.342), (width - 0.04, length - 0.04, 0.025), SOIL, root, 0.004)
        if bed_index < 2:
            crop_positions = [(x + dx, py) for dx in (-0.07, 0.07) for py in (-0.29, -0.04, 0.21, 0.46)]
        else:
            crop_positions = [(px, y) for px in (-0.20, 0.0, 0.20)]
        for plant_index, (px, py) in enumerate(crop_positions):
            top = 0.44 + (plant_index % 3) * 0.025
            rod("Crop stem", (px, py, 0.35), (px, py, top), 0.012, LEAF, root, 6)
            ellipsoid("Crop leaf left", (px - 0.035, py, top - 0.025), (0.05, 0.027, 0.018), LEAF_LIGHT if plant_index % 2 else LEAF, root)
            ellipsoid("Crop leaf right", (px + 0.035, py + 0.015, top), (0.05, 0.027, 0.018), LEAF, root)

    # Ridge vent opens above the glass roof without widening the footprint.
    box("Ridge vent housing", (0.0, 0.0, 1.64), (0.20, 0.58, 0.075), TEAL, root, 0.012)
    for y in (-0.20, -0.08, 0.04, 0.16):
        box("Ridge vent louver", (0.0, y, 1.685), (0.17, 0.035, 0.018), IRON, root, 0.003)

    # A simple drip line and rain barrel show how this greenhouse reuses water.
    rod("Greenhouse irrigation header", (0.0, -0.60, 0.88), (0.0, 0.60, 0.88), 0.018, TEAL, root)
    for y in (-0.48, -0.16, 0.16, 0.48):
        rod("Irrigation drop tube", (0.0, y, 0.88), (0.0, y, 0.73), 0.009, IRON, root, 6)
        ellipsoid("Irrigation drip emitter", (0.0, y, 0.70), (0.018, 0.018, 0.025), RUST, root, 1)
    cylinder("Greenhouse rain barrel", (0.86, 0.55, 0.37), 0.105, 0.40, TEAL, root, 12)
    for z in (0.23, 0.49):
        torus("Rain barrel reinforcing band", (0.86, 0.55, z), 0.108, 0.012, IRON, root)
    cylinder("Rain barrel lid", (0.86, 0.55, 0.58), 0.11, 0.025, CEDAR_LIGHT, root, 12)
    rod("Greenhouse downspout elbow", (0.76, 0.72, 0.95), (0.86, 0.72, 0.76), 0.025, TEAL, root)
    rod("Downspout to rain barrel", (0.86, 0.72, 0.76), (0.86, 0.63, 0.58), 0.025, TEAL, root)


def refine_water_purifier(root):
    # A short service ladder and a handwheel make the cistern maintainable.
    for x in (0.42, 0.70):
        rod("Cistern ladder rail", (x, -0.115, 0.23), (x, -0.115, 0.97), 0.018, IRON, root)
    for z in (0.29, 0.44, 0.59, 0.74, 0.89):
        rod("Cistern ladder rung", (0.42, -0.115, z), (0.70, -0.115, z), 0.014, TEAL, root)
    torus("Filter handwheel rim", (0.13, -0.60, 0.50), 0.066, 0.009, RUST, root, (math.radians(90.0), 0.0, 0.0))
    rod("Filter handwheel hub", (0.13, -0.61, 0.44), (0.13, -0.61, 0.56), 0.009, IRON, root)
    rod("Filter handwheel crossbar", (0.07, -0.61, 0.50), (0.19, -0.61, 0.50), 0.009, IRON, root)
    box("Cistern service hatch", (0.56, 0.20, 0.956), (0.20, 0.20, 0.025), TEAL, root, 0.008)
    for x in (0.49, 0.63):
        for y in (0.13, 0.27):
            cylinder("Hatch bolt", (x, y, 0.973), 0.012, 0.012, IRON, root, 8)

    # A readable analog pressure gauge makes the purifier feel serviceable.
    gauge_center = (-0.08, -0.535, 0.42)
    cylinder("Pressure gauge casing", gauge_center, 0.105, 0.045, IRON, root, 16, (math.radians(90.0), 0.0, 0.0))
    torus("Pressure gauge bezel", (-0.08, -0.563, 0.42), 0.088, 0.012, CEDAR_LIGHT, root, (math.radians(90.0), 0.0, 0.0))
    cylinder("Pressure gauge face", (-0.08, -0.565, 0.42), 0.075, 0.012, CREAM, root, 16, (math.radians(90.0), 0.0, 0.0))
    rod("Pressure gauge needle", (-0.08, -0.578, 0.42), (-0.045, -0.578, 0.465), 0.006, RUST, root, 6)
    rod("Gauge feed pipe", (-0.08, -0.53, 0.36), (-0.08, -0.46, 0.30), 0.014, TEAL, root, 8)


def refine_storage_depot(root):
    # A striped canvas loading awning adds depth to the large paired doors.
    for side in (-1.0, 1.0):
        rod("Awning support arm", (side * 0.56, -0.67, 1.18), (side * 0.56, -1.02, 0.98), 0.022, IRON, root)
    for index, x in enumerate((-0.48, -0.16, 0.16, 0.48)):
        color = CREAM if index % 2 == 0 else RUST
        vertices = [
            (x - 0.15, -0.69, 1.16), (x + 0.15, -0.69, 1.16),
            (x + 0.15, -1.02, 0.97), (x - 0.15, -1.02, 0.97),
        ]
        mesh_object("Canvas awning panel %02d" % index, vertices, [(3, 2, 1, 0)], color, root)
    rod("Awning front hem", (-0.62, -1.02, 0.97), (0.62, -1.02, 0.97), 0.018, CEDAR, root)
    for x in (-0.50, -0.18, 0.18, 0.50):
        cylinder("Awning tie eye", (x, -0.69, 1.18), 0.018, 0.026, IRON, root, 8, (math.radians(90.0), 0.0, 0.0))


def refine_salvage_workshop(root):
    # A wheeled scrap trolley gives the open bay a readable work-in-progress story.
    box("Scrap trolley tray", (0.0, -0.42, 0.40), (0.42, 0.36, 0.10), IRON, root, 0.018)
    box("Trolley front lip", (0.0, -0.61, 0.46), (0.42, 0.035, 0.12), TEAL, root, 0.008)
    for x in (-0.17, 0.17):
        cylinder("Trolley wheel", (x, -0.43, 0.30), 0.075, 0.045, RUBBER, root, 12, (0.0, math.radians(90.0), 0.0))
        cylinder("Trolley axle cap", (x * 1.08, -0.43, 0.30), 0.025, 0.012, RUST, root, 8, (0.0, math.radians(90.0), 0.0))
    for index, (x, y, z, angle) in enumerate(((-0.11, -0.43, 0.50, -12), (0.02, -0.40, 0.53, 17), (0.12, -0.45, 0.49, 6))):
        box("Trolley scrap plate %02d" % index, (x, y, z), (0.16, 0.12, 0.035), RUST if index == 0 else TEAL, root, 0.008, (0.0, 0.0, math.radians(angle)))
    # A hanging work lamp sits below the gantry beam and lights the active bay.
    rod("Work lamp cord", (0.48, -0.70, 2.00), (0.48, -0.70, 1.69), 0.009, IRON, root, 6)
    cylinder("Gantry work lamp", (0.48, -0.70, 1.64), 0.07, 0.10, CREAM, root, 10)
    cylinder("Gantry lamp lens", (0.48, -0.70, 1.58), 0.045, 0.025, RUST, root, 10)


def refine_generator_station(root):
    # Insulated feeder cables and a larger service junction emphasize power distribution.
    box("Cable junction box", (-0.39, -0.62, 0.39), (0.22, 0.24, 0.23), TEAL, root, 0.018)
    for z in (0.33, 0.39, 0.45):
        rod("Insulated feeder cable", (-0.31, -0.64, z), (0.30, -0.64, z), 0.014, RUST if z == 0.39 else IRON, root, 8)
    for x in (-0.47, -0.31):
        cylinder("Junction gland", (x, -0.64, 0.39), 0.033, 0.045, CEDAR_LIGHT, root, 10, (math.radians(90.0), 0.0, 0.0))
    # Four fasteners on the front service panel catch light at isometric scale.
    for x in (-0.25, 0.25):
        for z in (0.38, 0.93):
            cylinder("Service panel fastener", (x, -0.54, z), 0.014, 0.012, CEDAR_LIGHT, root, 8, (math.radians(90.0), 0.0, 0.0))


def refine_rescue_radio_center(root):
    # A small parabolic dish complements the shortwave mast and makes the comms role obvious.
    cx, cy, cz = -0.47, 0.10, 1.69
    radius = 0.22
    rings = 4
    segments = 20
    vertices = [(cx, cy + 0.13, cz)]
    for ring in range(1, rings + 1):
        r = radius * ring / rings
        depth = 0.13 * (1.0 - (r / radius) ** 2)
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            vertices.append((cx + r * math.cos(angle), cy + depth, cz + r * math.sin(angle)))
    faces = []
    for index in range(segments):
        faces.append((0, 1 + index, 1 + (index + 1) % segments))
    for ring in range(1, rings):
        inner = 1 + (ring - 1) * segments
        outer = 1 + ring * segments
        for index in range(segments):
            nxt = (index + 1) % segments
            faces.append((inner + index, outer + index, outer + nxt, inner + nxt))
    mesh_object("Shortwave parabolic dish", vertices, faces, TEAL, root)
    torus("Dish rim", (cx, cy, cz), radius, 0.012, IRON, root, (math.radians(90.0), 0.0, 0.0))
    rod("Dish mounting yoke", (cx, cy + 0.12, cz), (cx, cy + 0.37, 1.31), 0.018, IRON, root)
    rod("Dish feed arm", (cx, cy + 0.14, cz), (cx, cy - 0.08, cz), 0.012, RUST, root)
    ellipsoid("Dish feed element", (cx, cy - 0.09, cz), (0.035, 0.04, 0.035), CREAM, root)


def refine_dock(root):
    # A compact rescue skiff and a hanging life ring establish scale and purpose.
    boat_x, boat_y = 1.12, -1.30
    stations = [
        (-0.78, 0.045, 0.43), (-0.56, 0.17, 0.43), (-0.20, 0.25, 0.43),
        (0.34, 0.25, 0.43), (0.62, 0.16, 0.43), (0.78, 0.045, 0.43),
    ]
    verts = []
    for y, half_width, z in stations:
        bottom_width = half_width * 0.62
        verts.extend((
            (boat_x - half_width, boat_y + y, z),
            (boat_x + half_width, boat_y + y, z),
            (boat_x + bottom_width, boat_y + y, z - 0.19),
            (boat_x - bottom_width, boat_y + y, z - 0.19),
        ))
    faces = []
    for index in range(len(stations) - 1):
        a = index * 4
        b = a + 4
        # The fourth edge is the open gunwale; the cream deck sits inside it.
        for side in (1, 2, 3):
            nxt = (side + 1) % 4
            faces.append((a + side, b + side, b + nxt, a + nxt))
    faces.append((0, 1, 2, 3))
    last = (len(stations) - 1) * 4
    faces.append((last + 3, last + 2, last + 1, last))
    mesh_object("Rescue skiff orange hull", verts, faces, WATER, root)
    box("Skiff deck", (boat_x, boat_y, 0.395), (0.38, 1.08, 0.035), CREAM, root, 0.018)
    for y in (-0.35, -0.02, 0.30):
        box("Skiff bench", (boat_x, boat_y + y, 0.425), (0.36, 0.10, 0.045), CEDAR, root, 0.012)
    box("Skiff console", (boat_x, boat_y + 0.35, 0.51), (0.20, 0.18, 0.20), TEAL, root, 0.02)
    box("Skiff windscreen", (boat_x, boat_y + 0.27, 0.64), (0.20, 0.025, 0.12), GLASS, root, 0.006)
    for side in (-1.0, 1.0):
        rod("Skiff gunwale rub rail", (boat_x + side * 0.20, boat_y - 0.52, 0.42), (boat_x + side * 0.20, boat_y + 0.48, 0.42), 0.018, CREAM, root)
        cylinder("Skiff bow cleat", (boat_x + side * 0.10, boat_y - 0.60, 0.45), 0.022, 0.035, IRON, root, 8)
    rod("Skiff keel", (boat_x, boat_y - 0.58, 0.24), (boat_x, boat_y + 0.58, 0.24), 0.025, IRON, root, 8)
    cylinder("Skiff outboard housing", (boat_x, boat_y + 0.70, 0.40), 0.075, 0.24, IRON, root, 10)
    rod("Skiff mooring line", (0.67, -0.70, 0.40), (boat_x - 0.16, boat_y + 0.56, 0.42), 0.009, CREAM, root, 6)
    torus("Dock life ring", (-0.67, -0.18, 0.68), 0.13, 0.035, RUST, root, (math.radians(90.0), 0.0, 0.0))
    for z in (0.56, 0.80):
        rod("Life ring rack arm", (-0.67, -0.18, z), (-0.67, -0.18, z + 0.04), 0.012, IRON, root, 8)


def refine_single_asset(asset_name):
    blend_path = SOURCE_DIR / (asset_name + ".blend")
    if not blend_path.exists():
        raise FileNotFoundError("Missing Blender source: %s" % blend_path)
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    initialize_detail_materials()
    root = bpy.data.objects.get(asset_name + "_Root")
    if root is None:
        raise RuntimeError("Missing root object %s_Root in %s" % (asset_name, blend_path))

    remove_previous_refinements()
    add_surface_detail()
    if asset_name == "Greenhouse":
        soften_greenhouse_glazing()
    {
        "ResidentHut": refine_resident_hut,
        "Greenhouse": refine_greenhouse,
        "WaterPurifier": refine_water_purifier,
        "StorageDepot": refine_storage_depot,
        "SalvageWorkshop": refine_salvage_workshop,
        "GeneratorStation": refine_generator_station,
        "RescueRadioCenter": refine_rescue_radio_center,
        "RescueDock": refine_dock,
    }[asset_name](root)

    for scene in bpy.data.scenes:
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 1120
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.film_transparent = False
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    preview_path = PREVIEW_DIR / (asset_name + "_Final.png")
    bpy.context.scene.render.filepath = str(preview_path)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for child in root.children_recursive:
        if child.type == "MESH":
            child.select_set(True)
    bpy.context.view_layer.objects.active = root
    fbx_path = MODEL_DIR / (asset_name + ".fbx")
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
    print("Refined:", asset_name, "->", fbx_path)


def refine_roads():
    blend_path = SOURCE_DIR / "RoadTiles.blend"
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    initialize_detail_materials()
    remove_previous_refinements()
    add_surface_detail()
    mat = material("ArtRefine | road rivet steel", (0.34, 0.39, 0.38), 0.55, 0.55)
    patterns = {
        "RoadStraight": [(x, y) for y in (-0.40, -0.20, 0.0, 0.20, 0.40) for x in (-0.205, 0.205)],
        "RoadCorner": [(x, y) for y in (-0.40, -0.30) for x in (-0.205, 0.205)] + [(x, y) for x in (0.30, 0.40) for y in (-0.205, 0.205)],
        "RoadTee": [(x, y) for x in (-0.40, -0.20, 0.0, 0.20, 0.40) for y in (-0.205, 0.205)] + [(x, y) for y in (-0.40, -0.30) for x in (-0.205, 0.205)],
        "RoadCross": [(x, y) for x in (-0.40, -0.20, 0.0, 0.20, 0.40) for y in (-0.205, 0.205)] + [(x, y) for y in (-0.40, -0.20, 0.20, 0.40) for x in (-0.205, 0.205)],
        "RoadEnd": [(x, y) for y in (-0.40, -0.20) for x in (-0.205, 0.205)],
    }
    roots = {}
    for tile_name, points in patterns.items():
        root = bpy.data.objects.get(tile_name + "_Root")
        if root is None:
            raise RuntimeError("Missing road tile root: " + tile_name)
        saved_location = root.location.copy()
        root.location = (0.0, 0.0, 0.0)
        for index, (x, y) in enumerate(points):
            cylinder("Road plank countersunk rivet %02d" % index, (x, y, 0.108), 0.012, 0.009, mat, root, 8)
        root.location = saved_location
        roots[tile_name] = (root, saved_location)

    bpy.context.preferences.filepaths.save_version = 0
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(PREVIEW_DIR / "RoadTiles_Final.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    for tile_name, (root, saved_location) in roots.items():
        root.location = (0.0, 0.0, 0.0)
        bpy.ops.object.select_all(action="DESELECT")
        root.select_set(True)
        for child in root.children_recursive:
            if child.type == "MESH":
                child.select_set(True)
        bpy.context.view_layer.objects.active = root
        bpy.ops.export_scene.fbx(
            filepath=str(MODEL_DIR / (tile_name + ".fbx")),
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
        root.location = saved_location
        print("Refined road tile:", tile_name)


def main():
    bpy.context.preferences.filepaths.save_version = 0
    for asset_name in SINGLE_ASSETS:
        refine_single_asset(asset_name)
    refine_roads()
    print("All asset refinements completed.")


if __name__ == "__main__":
    main()
