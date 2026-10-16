"""Create reusable highland ground and shoreline modules for Last Landfall.

Run from the Unity project root with:
    blender --background --python Tools/Blender/create_highland_modules.py

The modules are one meter square on top, with the walkable surface at local Z=0.
The cliff edge faces local -Y; the corner module has exposed -X and -Y edges.
Rotate edge modules to match the island outline instead of using one fixed island.
"""

from pathlib import Path

import bpy


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
SOURCE_PATH = PROJECT_ROOT / "Assets/LastLandfall/Art/Source/HighlandModules.blend"
MODEL_DIR = PROJECT_ROOT / "Assets/LastLandfall/Resources/Models"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for group in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                  bpy.data.cameras, bpy.data.lights):
        for block in list(group):
            if block.users == 0:
                group.remove(block)


def make_material(name, color, roughness=0.9):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    return mat


def make_mesh(name, vertices, faces, materials, material_indices):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.clear()
    for mat in materials:
        mesh.materials.append(mat)
    for poly, material_index in zip(mesh.polygons, material_indices):
        poly.material_index = material_index
    mesh.validate(clean_customdata=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def create_module(name, exposed_edges, grass, earth, rock_a, rock_b):
    """Create a 1x1m tile with zero-height top and 1.15m cliffs on exposed edges."""
    half = 0.5
    body_bottom = -0.32
    cliff_bottom = -1.18
    vertices = [
        (-half, -half, 0.0), (half, -half, 0.0),
        (half, half, 0.0), (-half, half, 0.0),
        (-half, -half, body_bottom), (half, -half, body_bottom),
        (half, half, body_bottom), (-half, half, body_bottom),
    ]
    faces = [
        (0, 1, 2, 3),
        (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0),
        (4, 7, 6, 5),
    ]
    face_mats = [0, 1, 1, 1, 1, 1]

    # A cliff is an angular rock skirt that reaches below the compact tile body.
    # Top-edge vertices remain on grid boundaries to keep modules tileable.
    for edge in exposed_edges:
        if edge == "south":  # local -Y
            v0, v1 = 0, 1
            p0, p1 = (-half, -half, cliff_bottom), (half, -half, cliff_bottom)
            mid = (0.0, -half - 0.13, cliff_bottom + 0.13)
        elif edge == "west":  # local -X
            v0, v1 = 3, 0
            p0, p1 = (-half, half, cliff_bottom), (-half, -half, cliff_bottom)
            mid = (-half - 0.13, 0.0, cliff_bottom + 0.13)
        else:
            continue
        first = len(vertices)
        vertices.extend([p0, p1, mid])
        # Irregular broad planes with alternating stone tones create readable strata.
        faces.extend([(v0, v1, first + 1, first + 2),
                      (v0, first + 2, first, 4 if edge == "south" else 7)])
        face_mats.extend([2, 3])
        # A small ledge near the top helps the edge catch light in an isometric view.
        ledge = len(vertices)
        if edge == "south":
            vertices.extend([(-0.5, -0.53, -0.23), (0.5, -0.53, -0.23)])
            faces.append((0, 1, ledge + 1, ledge))
        else:
            vertices.extend([(-0.53, 0.5, -0.23), (-0.53, -0.5, -0.23)])
            faces.append((3, 0, ledge + 1, ledge))
        face_mats.append(3)

    obj = make_mesh(name, vertices, faces, [grass, earth, rock_a, rock_b], face_mats)
    obj["FootprintMeters"] = "1 x 1"
    obj["WalkableTopZ"] = 0.0
    obj["CliffEdges"] = ",".join(exposed_edges) if exposed_edges else "none"
    bevel = obj.modifiers.new("Tiny chipped corners", "BEVEL")
    bevel.width = 0.018
    bevel.segments = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def add_preview(scene, objects):
    bpy.ops.mesh.primitive_plane_add(size=3.4, location=(0.0, 0.0, -1.22))
    plane = bpy.context.object
    plane.name = "Preview background (not exported)"
    plane.data.materials.append(make_material("Preview | deep ocean", (0.045, 0.19, 0.25), 0.4))
    camera_data = bpy.data.cameras.new("Highland modules preview camera")
    camera = bpy.data.objects.new("Highland modules preview camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (3.7, -4.4, 3.2)
    from mathutils import Vector
    camera.rotation_euler = (Vector((0.0, 0.0, -0.2)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 4.0
    scene.camera = camera
    light_data = bpy.data.lights.new("Highland preview softbox", type="AREA")
    light = bpy.data.objects.new("Highland preview softbox", light_data)
    bpy.context.collection.objects.link(light)
    light.location = (1.3, -2.0, 4.4)
    light.data.energy = 500
    light.data.shape = "DISK"
    light.data.size = 4
    light.rotation_euler = (Vector((0.0, 0.0, -0.2)) - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 750
    scene.render.resolution_percentage = 100


def operator_available(operator):
    try:
        operator.get_rna_type()
        return True
    except (AttributeError, RuntimeError):
        return False


def export_selected(path_stem):
    fbx_path = MODEL_DIR / (path_stem + ".fbx")
    obj_path = MODEL_DIR / (path_stem + "_OBJ.obj")
    if operator_available(bpy.ops.export_scene.fbx):
        bpy.ops.export_scene.fbx(filepath=str(fbx_path), use_selection=True,
                                 object_types={"MESH"}, axis_forward="-Z", axis_up="Y",
                                 apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                                 use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False,
                                 path_mode="AUTO")
        print("Exported FBX:", fbx_path)
    elif operator_available(bpy.ops.wm.obj_export):
        bpy.ops.wm.obj_export(filepath=str(obj_path), export_selected_objects=True,
                              forward_axis="NEGATIVE_Z", up_axis="Y", global_scale=1.0,
                              apply_modifiers=True, export_materials=True,
                              export_object_groups=True, export_material_groups=True,
                              path_mode="AUTO")
        print("Exported OBJ fallback:", obj_path)
    else:
        raise RuntimeError("No supported exporter is available; enable Blender's FBX extension.")


def build_and_export():
    clear_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    grass = make_material("Ground | muted salt grass", (0.38, 0.43, 0.29))
    earth = make_material("Ground | dark soil", (0.25, 0.23, 0.19))
    rock_a = make_material("Cliff | slate", (0.30, 0.34, 0.34))
    rock_b = make_material("Cliff | warm stone", (0.43, 0.39, 0.31))

    interior = create_module("HighlandInteriorTile", [], grass, earth, rock_a, rock_b)
    interior.location.x = -1.15
    edge = create_module("HighlandCliffEdge", ["south"], grass, earth, rock_a, rock_b)
    corner = create_module("HighlandCliffCorner", ["south", "west"], grass, earth, rock_a, rock_b)
    corner.location.x = 1.15
    modules = [interior, edge, corner]
    add_preview(scene, modules)

    SOURCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE_PATH))
    # Export each piece separately so Unity can use each shape as a prefab.
    for obj, stem in zip(modules, ("HighlandInteriorTile", "HighlandCliffEdge", "HighlandCliffCorner")):
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        preview_location = obj.location.copy()
        obj.location = (0.0, 0.0, 0.0)
        export_selected(stem)
        obj.location = preview_location
    print("Created Blender source:", SOURCE_PATH)


build_and_export()
