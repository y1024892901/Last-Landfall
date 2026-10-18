"""Materials and honest geometry previews for the reference island rebuild.

The module adds no vegetation, scenery rocks, structures or other decorations.
Material order returned by ``create_materials`` is stable:
    0: bare_earth    -- compact, mineral earth on gentle land
    1: layered_rock -- exposed, fractured grey rock
    2: wet_rock     -- dark waterline/submerged rock

``render_previews(terrain_obj, output_dir, prefix)`` temporarily creates a
render-only sea, a camera and lighting.  It renders the actual supplied mesh,
then removes its preview objects and restores the scene's render settings.
Only terrain_obj should be selected when exporting the deliverable FBX.
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


MATERIAL_BARE_EARTH = 0
MATERIAL_LAYERED_ROCK = 1
MATERIAL_WET_ROCK = 2


def _material(name, base_color, roughness):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*base_color, 1.0)
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (860, 100)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (570, 100)
    shader.inputs["Base Color"].default_value = (*base_color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.28
    mat.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    geometry = nodes.new("ShaderNodeNewGeometry")
    geometry.location = (-1060, 100)
    geometry.label = "World position in metres: no UV stretching"
    return mat, nodes, mat.node_tree.links, shader, geometry.outputs["Position"]


def _noise(nodes, links, position, scale, detail, location, name):
    tex = nodes.new("ShaderNodeTexNoise")
    tex.location = location
    tex.label = name
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = detail
    tex.inputs["Roughness"].default_value = 0.68
    links.new(position, tex.inputs["Vector"])
    return tex


def _ramp(nodes, links, factor, stops, location, name):
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = location
    ramp.label = name
    ramp.color_ramp.interpolation = "EASE"
    elements = ramp.color_ramp.elements
    while len(elements) > 2:
        elements.remove(elements[-1])
    elements[0].position = stops[0][0]
    elements[0].color = (*stops[0][1], 1.0)
    elements[1].position = stops[-1][0]
    elements[1].color = (*stops[-1][1], 1.0)
    for position, color in stops[1:-1]:
        elem = elements.new(position)
        elem.color = (*color, 1.0)
    links.new(factor, ramp.inputs["Fac"])
    return ramp


def _mix(nodes, links, color_a, color_b, factor, location, blend="MIX"):
    node = nodes.new("ShaderNodeMixRGB")
    node.blend_type = blend
    node.location = location
    node.inputs["Fac"].default_value = factor
    links.new(color_a, node.inputs["Color1"])
    links.new(color_b, node.inputs["Color2"])
    return node


def _roughness(nodes, links, factor, low, high, shader, location):
    ramp = _ramp(nodes, links, factor,
                 [(0.0, (low, low, low)), (1.0, (high, high, high))],
                 location, "Broken mineral roughness")
    links.new(ramp.outputs["Color"], shader.inputs["Roughness"])


def _bump(nodes, links, height, shader, distance, strength, location, previous=None):
    node = nodes.new("ShaderNodeBump")
    node.location = location
    node.inputs["Distance"].default_value = distance
    node.inputs["Strength"].default_value = strength
    links.new(height, node.inputs["Height"])
    if previous:
        links.new(previous, node.inputs["Normal"])
    links.new(node.outputs["Normal"], shader.inputs["Normal"])
    return node.outputs["Normal"]


def create_materials():
    """Return [bare_earth, layered_rock, wet_rock], ready for mesh slots.

    Physical rock detail is carried by procedural nodes. diffuse_color is set
    as an FBX/Unity fallback; FBX cannot carry Blender procedural shader graphs.
    """
    earth, nodes, links, shader, pos = _material(
        "bare_earth", (0.185, 0.172, 0.14), 0.94)
    broad = _noise(nodes, links, pos, 0.011, 4.0, (-830, 350),
                   "Exposed mineral deposits, 90 metre scale")
    earth_colors = _ramp(nodes, links, broad.outputs["Fac"], [
        (0.13, (0.075, 0.081, 0.075)),
        (0.43, (0.145, 0.141, 0.116)),
        (0.66, (0.225, 0.206, 0.164)),
        (0.89, (0.285, 0.263, 0.218)),
    ], (-550, 380), "Compacted grey-brown earth; no grass")
    aggregate = _noise(nodes, links, pos, 0.07, 3.0, (-830, 40),
                       "Irregular gravel and exposed stone")
    aggregate_colors = _ramp(nodes, links, aggregate.outputs["Fac"], [
        (0.2, (0.29, 0.28, 0.25)),
        (0.8, (0.83, 0.79, 0.68)),
    ], (-550, 80), "Earth aggregate")
    mixed = _mix(nodes, links, earth_colors.outputs["Color"],
                 aggregate_colors.outputs["Color"], 0.26, (-220, 360), "MULTIPLY")
    links.new(mixed.outputs["Color"], shader.inputs["Base Color"])
    fine = _noise(nodes, links, pos, 0.18, 2.2, (-820, -280),
                  "Fine compacted gravel")
    normal = _bump(nodes, links, aggregate.outputs["Fac"], shader,
                   0.2, 0.26, (-130, -110))
    _bump(nodes, links, fine.outputs["Fac"], shader,
          0.04, 0.18, (150, -110), normal)
    _roughness(nodes, links, aggregate.outputs["Fac"], 0.84, 0.98,
               shader, (-220, -390))

    rock, nodes, links, shader, pos = _material(
        "layered_rock", (0.135, 0.151, 0.16), 0.89)
    macro = _noise(nodes, links, pos, 0.009, 4.2, (-830, 390),
                   "Large slate mineral variation")
    rock_colors = _ramp(nodes, links, macro.outputs["Fac"], [
        (0.12, (0.045, 0.055, 0.064)),
        (0.40, (0.105, 0.122, 0.134)),
        (0.67, (0.215, 0.225, 0.222)),
        (0.89, (0.305, 0.301, 0.277)),
    ], (-550, 420), "Cool grey slate with mineral weathering")
    bed_mapping = nodes.new("ShaderNodeVectorMath")
    bed_mapping.operation = "MULTIPLY"
    bed_mapping.location = (-1060, -100)
    bed_mapping.inputs[1].default_value = (0.6, 0.6, 2.1)
    links.new(pos, bed_mapping.inputs[0])
    strata = _noise(nodes, links, bed_mapping.outputs["Vector"], 0.035, 3.8,
                    (-830, 95), "Weak irregular foliation; no repeating wave bands")
    strata_colors = _ramp(nodes, links, strata.outputs["Fac"], [
        (0.15, (0.35, 0.39, 0.42)),
        (0.85, (0.85, 0.85, 0.81)),
    ], (-550, 100), "Weathered bedding contrast")
    mixed = _mix(nodes, links, rock_colors.outputs["Color"],
                 strata_colors.outputs["Color"], 0.16, (-205, 390), "MULTIPLY")
    links.new(mixed.outputs["Color"], shader.inputs["Base Color"])
    cracks = nodes.new("ShaderNodeTexVoronoi")
    cracks.location = (-830, -220)
    cracks.feature = "DISTANCE_TO_EDGE"
    cracks.inputs["Scale"].default_value = 0.045
    links.new(pos, cracks.inputs["Vector"])
    crack_height = _ramp(nodes, links, cracks.outputs["Distance"], [
        (0.008, (0.12, 0.12, 0.12)),
        (0.07, (0.55, 0.55, 0.55)),
        (0.28, (0.64, 0.64, 0.64)),
    ], (-530, -235), "Broken slate joints")
    normal = _bump(nodes, links, crack_height.outputs["Color"], shader,
                   0.35, 0.3, (-120, -60))
    grain = _noise(nodes, links, pos, 0.14, 3.0, (-820, -545), "Mineral grain")
    _bump(nodes, links, grain.outputs["Fac"], shader,
          0.06, 0.24, (160, -60), normal)
    _roughness(nodes, links, grain.outputs["Fac"], 0.72, 0.94,
               shader, (-220, -395))

    wet, nodes, links, shader, pos = _material(
        "wet_rock", (0.058, 0.072, 0.079), 0.48)
    wet_noise = _noise(nodes, links, pos, 0.037, 4.0, (-830, 260),
                       "Flood-darkened exposed minerals")
    wet_colors = _ramp(nodes, links, wet_noise.outputs["Fac"], [
        (0.12, (0.019, 0.029, 0.035)),
        (0.48, (0.054, 0.073, 0.08)),
        (0.85, (0.13, 0.15, 0.155)),
    ], (-530, 285), "Wet slate darkened at the waterline")
    links.new(wet_colors.outputs["Color"], shader.inputs["Base Color"])
    wet_grain = _noise(nodes, links, pos, 0.18, 3.2, (-820, -80),
                       "Wet fracture grain")
    _bump(nodes, links, wet_grain.outputs["Fac"], shader,
          0.16, 0.34, (130, -110))
    _roughness(nodes, links, wet_grain.outputs["Fac"], 0.34, 0.65,
               shader, (-230, -320))
    return [earth, rock, wet]


def _preview_water_material(name):
    mat, nodes, links, shader, pos = _material(
        name, (0.022, 0.065, 0.086), 0.29)
    shader.inputs["Metallic"].default_value = 0.09
    variation = _noise(nodes, links, pos, 0.0025, 2.0, (-820, 300),
                       "Deep, floodwater colour")
    colors = _ramp(nodes, links, variation.outputs["Fac"], [
        (0.0, (0.018, 0.047, 0.062)),
        (1.0, (0.032, 0.068, 0.086)),
    ], (-510, 320), "Open sea grey-blue")
    links.new(colors.outputs["Color"], shader.inputs["Base Color"])
    swell = _noise(nodes, links, pos, 0.12, 2.5, (-820, -40),
                   "Small wind ripples, preview only")
    _bump(nodes, links, swell.outputs["Fac"], shader,
          0.11, 0.18, (100, -80))
    return mat


def _aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_previews(terrain_obj, output_dir, prefix="IslandReference_V2"):
    """Render mesh-only reference, top view and clay geometry previews.

    Returns a dictionary whose keys are ``reference``, ``top`` and ``clay``.
    These images are geometry renders, never AI concept images.  The sea plane
    is at z=0 and is removed along with the isolated preview rig afterwards.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    state = {
        "camera": scene.camera,
        "world": scene.world,
        "engine": scene.render.engine,
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y,
        "resolution_percentage": scene.render.resolution_percentage,
        "filepath": scene.render.filepath,
        "film_transparent": scene.render.film_transparent,
        "file_format": scene.render.image_settings.file_format,
        "view_transform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "exposure": scene.view_settings.exposure,
        "gamma": scene.view_settings.gamma,
        "override": bpy.context.view_layer.material_override,
    }
    prior_hidden = {obj: obj.hide_render for obj in scene.objects if obj != terrain_obj}
    terrain_hidden = terrain_obj.hide_render
    original_materials = list(terrain_obj.data.materials)
    collection = bpy.data.collections.new("__ReferencePreviewRig")
    scene.collection.children.link(collection)
    created_materials = []
    created_world = None
    paths = {
        "reference": output_dir / (prefix + "_Reference.png"),
        "top": output_dir / (prefix + "_Top.png"),
        "clay": output_dir / (prefix + "_Clay.png"),
    }
    try:
        # Preview exactly this terrain mesh; project props cannot accidentally
        # appear in the beauty render.
        for obj in prior_hidden:
            obj.hide_render = True
        terrain_obj.hide_render = False
        surface_points = []
        for vertex in terrain_obj.data.vertices:
            point = terrain_obj.matrix_world @ vertex.co
            if point.z >= -0.1:
                surface_points.append(point)
        if not surface_points:
            surface_points = [terrain_obj.matrix_world @ Vector(p) for p in terrain_obj.bound_box]
        min_x, max_x = min(v.x for v in surface_points), max(v.x for v in surface_points)
        min_y, max_y = min(v.y for v in surface_points), max(v.y for v in surface_points)
        max_z = max(v.z for v in surface_points)
        width, length = max_x - min_x, max_y - min_y
        span = max(width, length, 1.0)
        cx, cy = (min_x + max_x) * 0.5, (min_y + max_y) * 0.5

        # Blender 4.2/5.0 calls the modern engine BLENDER_EEVEE; 4.0 used NEXT.
        try:
            scene.render.engine = "BLENDER_EEVEE"
        except TypeError:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        if hasattr(scene, "eevee"):
            for prop in ("taa_render_samples", "taa_samples"):
                if hasattr(scene.eevee, prop):
                    setattr(scene.eevee, prop, 64)
        scene.render.resolution_x = 1600
        scene.render.resolution_y = 1100
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = False
        scene.render.image_settings.file_format = "PNG"
        try:
            scene.view_settings.view_transform = "AgX"
            scene.view_settings.look = "AgX - Medium High Contrast"
        except (TypeError, ValueError):
            pass
        scene.view_settings.exposure = 0.05
        scene.view_settings.gamma = 1.0

        created_world = bpy.data.worlds.new("__ReferencePreviewSky")
        created_world.use_nodes = True
        world_nodes = created_world.node_tree.nodes
        world_nodes.clear()
        background = world_nodes.new("ShaderNodeBackground")
        background.inputs["Color"].default_value = (0.37, 0.45, 0.53, 1.0)
        background.inputs["Strength"].default_value = 0.22
        world_out = world_nodes.new("ShaderNodeOutputWorld")
        created_world.node_tree.links.new(background.outputs[0], world_out.inputs[0])
        scene.world = created_world

        camera_data = bpy.data.cameras.new("__ReferencePreviewCamera")
        camera = bpy.data.objects.new("__ReferencePreviewCamera", camera_data)
        collection.objects.link(camera)
        camera_data.type = "PERSP"
        camera_data.clip_start = 1.0
        camera_data.clip_end = span * 20.0
        camera_data.lens = 44
        camera_data.sensor_width = 36
        camera_data.sensor_fit = "HORIZONTAL"
        scene.camera = camera
        target = Vector((cx, cy + length * 0.05, max_z * 0.25))
        camera.location = target + Vector((span * 0.05, -span * 1.383333, span * 0.666667))
        _aim(camera, target)
        aspect = 1600.0 / 1100.0
        # Fit the actual visible land to a 44 mm perspective camera. The
        # submerged base never changes the framing. A pinhole fit avoids both
        # cropping the near peninsula and shrinking it into an orthographic map.
        inverse_rotation = camera.rotation_euler.to_quaternion().inverted()
        tan_x = camera_data.sensor_width / (2.0 * camera_data.lens)
        tan_y = tan_x / aspect
        stride = max(1, len(surface_points) // 6000)
        framing_points = surface_points[::stride]
        for axis in range(3):
            framing_points += [min(surface_points, key=lambda p: p[axis]),
                               max(surface_points, key=lambda p: p[axis])]
        required_distance = 1.0
        for point in framing_points:
            q = inverse_rotation @ (point - target)
            required_distance = max(required_distance,
                                    q.z + abs(q.x) / (tan_x * 0.89),
                                    q.z + abs(q.y) / (tan_y * 0.87))
        view_backward = camera.rotation_euler.to_quaternion() @ Vector((0, 0, 1))
        camera.location = target + view_backward * required_distance

        sun_data = bpy.data.lights.new("__ReferencePreviewSun", "SUN")
        sun_data.energy = 2.65
        sun_data.angle = math.radians(3)
        sun_data.use_shadow = True
        sun_data.color = (1.0, 0.88, 0.72)
        sun = bpy.data.objects.new("__ReferencePreviewSun", sun_data)
        collection.objects.link(sun)
        sun.location = (cx + span, cy + span * 0.45, span)
        _aim(sun, (cx, cy, 0))

        fill_data = bpy.data.lights.new("__ReferencePreviewFill", "AREA")
        fill_data.energy = 120.0 * (span / 10.0) ** 2
        fill_data.shape = "DISK"
        fill_data.size = span * 1.4
        fill_data.color = (0.73, 0.82, 1.0)
        fill = bpy.data.objects.new("__ReferencePreviewFill", fill_data)
        collection.objects.link(fill)
        fill.location = (cx - span * 0.55, cy - span * 0.5, span * 1.1)
        _aim(fill, (cx, cy, 0))

        water_mesh = bpy.data.meshes.new("__ReferencePreviewSea")
        half = span * 8
        water_mesh.from_pydata([
            (cx - half, cy - half, 0), (cx + half, cy - half, 0),
            (cx + half, cy + half, 0), (cx - half, cy + half, 0),
        ], [], [(0, 1, 2, 3)])
        water = bpy.data.objects.new("__ReferencePreviewSea", water_mesh)
        collection.objects.link(water)
        water_material = _preview_water_material("__ReferencePreviewWater")
        water.data.materials.append(water_material)
        created_materials.append(water_material)

        scene.render.filepath = str(paths["reference"])
        bpy.ops.render.render(write_still=True)

        reference_location = camera.location.copy()
        reference_rotation = camera.rotation_euler.copy()
        camera_data.type = "ORTHO"
        camera.location = (cx, cy, span * 2.0 + max_z)
        camera.rotation_euler = (0.0, 0.0, 0.0)
        camera_data.ortho_scale = max(width * 1.13, length * 1.13 * aspect)
        scene.render.filepath = str(paths["top"])
        bpy.ops.render.render(write_still=True)

        camera.location = reference_location
        camera.rotation_euler = reference_rotation
        camera_data.type = "PERSP"
        clay, _, _, _, _ = _material("__ReferencePreviewClay", (0.58, 0.59, 0.60), 0.86)
        created_materials.append(clay)
        # Only the terrain is clay. Keeping the sea's blue-grey material makes
        # shore recesses, the flooded base and isolated skerries readable.
        bpy.context.view_layer.material_override = None
        if original_materials:
            for index in range(len(original_materials)):
                terrain_obj.data.materials[index] = clay
        else:
            terrain_obj.data.materials.append(clay)
        scene.render.filepath = str(paths["clay"])
        bpy.ops.render.render(write_still=True)
    finally:
        if original_materials:
            for index, material in enumerate(original_materials):
                terrain_obj.data.materials[index] = material
        else:
            terrain_obj.data.materials.clear()
        bpy.context.view_layer.material_override = state["override"]
        for obj, was_hidden in prior_hidden.items():
            obj.hide_render = was_hidden
        terrain_obj.hide_render = terrain_hidden
        scene.camera = state["camera"]
        scene.world = state["world"]
        scene.render.engine = state["engine"]
        for prop in ("resolution_x", "resolution_y", "resolution_percentage", "filepath", "film_transparent"):
            setattr(scene.render, prop, state[prop])
        scene.render.image_settings.file_format = state["file_format"]
        scene.view_settings.view_transform = state["view_transform"]
        scene.view_settings.look = state["look"]
        scene.view_settings.exposure = state["exposure"]
        scene.view_settings.gamma = state["gamma"]
        for obj in list(collection.objects):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Light):
                    bpy.data.lights.remove(data)
                elif isinstance(data, bpy.types.Camera):
                    bpy.data.cameras.remove(data)
        bpy.data.collections.remove(collection)
        if created_world and created_world.users == 0:
            bpy.data.worlds.remove(created_world)
        for mat in created_materials:
            if mat.users == 0:
                bpy.data.materials.remove(mat)
    return {key: str(path) for key, path in paths.items()}
