"""Generate the Survivor / Resident character low-poly 3D model for Last Landfall.

Run with Blender 5.2 from the project root:
    & "D:\\Blender 5.2\\blender.exe" --background --python Tools/Blender/create_survivor_character.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
ART_SOURCE = ROOT / "Assets/LastLandfall/Art/Source/Characters"
MODELS = ROOT / "Assets/LastLandfall/Resources/Models/Characters"
PREVIEWS = ROOT / "Assets/LastLandfall/Art/Previews/Characters"

ASSET_ID = "Survivor_Worker"
BLEND_PATH = ART_SOURCE / f"{ASSET_ID}.blend"
FBX_PATH = MODELS / f"{ASSET_ID}.fbx"
PREVIEW_PATH = PREVIEWS / f"{ASSET_ID}.png"

COLLECTION = None
OBJECTS = []
MATERIALS = {}


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block_group in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(block_group):
            if block.users == 0:
                block_group.remove(block)


def make_material(name, color, metallic=0.0, roughness=0.85):
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


def setup_materials():
    prefix = f"{ASSET_ID} | "
    return {
        "skin": make_material(prefix + "weathered skin", (0.82, 0.64, 0.50), roughness=0.7),
        "jacket": make_material(prefix + "teal rain jacket", (0.16, 0.38, 0.36), roughness=0.75),
        "vest": make_material(prefix + "orange rescue harness", (0.92, 0.40, 0.12), roughness=0.65),
        "pants": make_material(prefix + "durable work pants", (0.28, 0.25, 0.22), roughness=0.9),
        "boots": make_material(prefix + "rubber boots", (0.10, 0.11, 0.12), roughness=0.5),
        "beanie": make_material(prefix + "knit beanie cap", (0.75, 0.58, 0.28), roughness=0.95),
        "gear": make_material(prefix + "salvage belt & pouches", (0.42, 0.31, 0.19), roughness=0.8),
        "metal": make_material(prefix + "carabiners & buckle", (0.55, 0.58, 0.60), metallic=0.7, roughness=0.35),
    }


def add_mesh(name, vertices, faces, mat):
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
    OBJECTS.append(obj)
    return obj


def box(name, location, size, mat, rotation=None):
    x, y, z = (float(v) * 0.5 for v in size)
    verts = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
             (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    obj = add_mesh(name, verts, faces, mat)
    obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    return obj


def cylinder(name, location, radius, depth, mat, vertices=8, rotation=None, radius_top=None):
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


def build_survivor():
    # Overall height: ~1.75m. Stylized low-poly aesthetic.
    # Ground at Z=0. Character faces -Y (standard project orientation).
    
    # --- Boots & Legs (Z: 0.0 -> 0.82) ---
    for side, x in (("Left", -0.16), ("Right", 0.16)):
        # Heavy work/rubber boot
        box(f"Boot_{side}", (x, -0.04, 0.10), (0.17, 0.28, 0.20), MATERIALS["boots"])
        # Boot toe cap
        box(f"BootToe_{side}", (x, -0.16, 0.07), (0.16, 0.12, 0.14), MATERIALS["boots"])
        # Boot collar
        box(f"BootCollar_{side}", (x, -0.04, 0.22), (0.19, 0.22, 0.08), MATERIALS["boots"])
        # Lower leg pants
        box(f"LowerLeg_{side}", (x, -0.03, 0.40), (0.18, 0.20, 0.32), MATERIALS["pants"])
        # Upper leg pants / thigh
        box(f"UpperLeg_{side}", (x, -0.02, 0.66), (0.20, 0.22, 0.28), MATERIALS["pants"])

    # Pelvis / Hips (Z: 0.78 -> 0.90)
    box("Hips", (0.0, -0.02, 0.84), (0.44, 0.25, 0.16), MATERIALS["pants"])
    
    # Utility tool belt & pouch (Z: 0.88 -> 0.95)
    box("Belt", (0.0, -0.02, 0.92), (0.47, 0.28, 0.08), MATERIALS["gear"])
    box("BeltBuckle", (0.0, -0.16, 0.92), (0.10, 0.03, 0.07), MATERIALS["metal"])
    # Tool pouches
    box("Pouch_Right", (0.24, -0.02, 0.90), (0.10, 0.16, 0.14), MATERIALS["gear"])
    box("Canteen_Left", (-0.24, -0.01, 0.91), (0.09, 0.12, 0.16), MATERIALS["metal"])

    # --- Torso / Rain Jacket (Z: 0.94 -> 1.38) ---
    # Abdomen / Lower Torso
    box("TorsoLower", (0.0, -0.01, 1.05), (0.42, 0.26, 0.22), MATERIALS["jacket"])
    # Chest / Upper Torso
    box("TorsoUpper", (0.0, -0.01, 1.25), (0.48, 0.28, 0.24), MATERIALS["jacket"])

    # --- Rescue / High-Vis Life Harness Vest (layered over jacket) ---
    # Front vest panels
    box("VestFront_Left", (-0.12, -0.15, 1.18), (0.18, 0.05, 0.36), MATERIALS["vest"])
    box("VestFront_Right", (0.12, -0.15, 1.18), (0.18, 0.05, 0.36), MATERIALS["vest"])
    # Back vest panel
    box("VestBack", (0.0, 0.13, 1.18), (0.42, 0.05, 0.36), MATERIALS["vest"])
    # Shoulder harness straps
    box("VestShoulder_Left", (-0.16, -0.01, 1.37), (0.11, 0.26, 0.05), MATERIALS["vest"])
    box("VestShoulder_Right", (0.16, -0.01, 1.37), (0.11, 0.26, 0.05), MATERIALS["vest"])
    # High-vis reflective stripes
    box("ReflectiveStripe_Left", (-0.12, -0.178, 1.12), (0.16, 0.01, 0.04), MATERIALS["metal"])
    box("ReflectiveStripe_Right", (0.12, -0.178, 1.12), (0.16, 0.01, 0.04), MATERIALS["metal"])

    # --- Neck & Head (Z: 1.38 -> 1.76) ---
    cylinder("Neck", (0.0, -0.01, 1.41), 0.09, 0.10, MATERIALS["skin"], vertices=8)
    # Jacket high waterproof collar
    box("Collar", (0.0, -0.01, 1.40), (0.28, 0.22, 0.09), MATERIALS["jacket"])
    # Stylized faceted head
    box("Head", (0.0, -0.02, 1.54), (0.22, 0.22, 0.20), MATERIALS["skin"])
    # Facial plane / nose feature
    box("Nose", (0.0, -0.14, 1.53), (0.04, 0.04, 0.05), MATERIALS["skin"])
    
    # Knit beanie / winter cap covering upper head
    cylinder("BeanieDome", (0.0, -0.01, 1.67), 0.135, 0.12, MATERIALS["beanie"], vertices=10, radius_top=0.10)
    box("BeanieFold", (0.0, -0.01, 1.62), (0.25, 0.25, 0.06), MATERIALS["beanie"])
    # Beanie pompom on top
    box("BeanieTip", (0.0, -0.01, 1.74), (0.06, 0.06, 0.06), MATERIALS["beanie"])

    # --- Arms & Hands ---
    for side, sign in (("Left", -1), ("Right", 1)):
        x_shoulder = sign * 0.28
        # Shoulder pad
        box(f"Shoulder_{side}", (x_shoulder, -0.01, 1.32), (0.16, 0.20, 0.16), MATERIALS["jacket"])
        # Upper Arm
        box(f"UpperArm_{side}", (x_shoulder + sign * 0.04, -0.01, 1.16), (0.14, 0.16, 0.22), MATERIALS["jacket"])
        # Elbow / Forearm
        box(f"Forearm_{side}", (x_shoulder + sign * 0.05, -0.03, 0.94), (0.13, 0.15, 0.24), MATERIALS["jacket"])
        # Heavy work gloves
        box(f"Hand_{side}", (x_shoulder + sign * 0.05, -0.05, 0.77), (0.12, 0.13, 0.14), MATERIALS["gear"])
        box(f"Thumb_{side}", (x_shoulder + sign * 0.01, -0.10, 0.77), (0.04, 0.06, 0.07), MATERIALS["gear"])

    # --- Small Salvage Radio attached to left chest ---
    box("ChestRadio", (-0.16, -0.18, 1.28), (0.07, 0.05, 0.10), MATERIALS["boots"])
    box("RadioAntenna", (-0.18, -0.18, 1.39), (0.015, 0.015, 0.14), MATERIALS["metal"])


def setup_lighting_and_camera():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    
    # Ground plane for preview
    floor_mesh = bpy.data.meshes.new("PreviewFloorMesh")
    floor_mesh.from_pydata([(-2, -2, 0), (2, -2, 0), (2, 2, 0), (-2, 2, 0)], [], [(0, 1, 2, 3)])
    floor_mesh.update()
    floor_obj = bpy.data.objects.new("PreviewFloor", floor_mesh)
    COLLECTION.objects.link(floor_obj)
    floor_obj.data.materials.append(make_material("NeutralFloor", (0.20, 0.24, 0.26), roughness=0.9))

    # Camera - isometric style view looking at character
    cam_data = bpy.data.cameras.new("PreviewCamera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2.4
    cam_obj = bpy.data.objects.new("PreviewCamera", cam_data)
    COLLECTION.objects.link(cam_obj)
    cam_obj.location = (2.2, -3.2, 2.5)
    target = Vector((0.0, 0.0, 0.9))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam_obj

    # Key light
    key_data = bpy.data.lights.new("KeyLight", "SUN")
    key_data.energy = 3.5
    key_data.color = (1.0, 0.96, 0.90)
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    COLLECTION.objects.link(key_obj)
    key_obj.rotation_euler = (math.radians(50), math.radians(20), math.radians(-35))

    # Fill light
    fill_data = bpy.data.lights.new("FillLight", "SUN")
    fill_data.energy = 1.2
    fill_data.color = (0.75, 0.85, 0.95)
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    COLLECTION.objects.link(fill_obj)
    fill_obj.rotation_euler = (math.radians(30), math.radians(-40), math.radians(130))

    return floor_obj, cam_obj, [key_obj, fill_obj]


def main():
    global COLLECTION, MATERIALS
    ART_SOURCE.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    PREVIEWS.mkdir(parents=True, exist_ok=True)

    clear_scene()
    COLLECTION = bpy.context.collection
    MATERIALS = setup_materials()
    build_survivor()

    # Create root empty object
    root = bpy.data.objects.new(f"{ASSET_ID}_Root", None)
    COLLECTION.objects.link(root)
    for obj in list(OBJECTS):
        obj.parent = root

    # Render Preview
    floor_obj, cam_obj, lights = setup_lighting_and_camera()
    bpy.context.scene.render.resolution_x = 800
    bpy.context.scene.render.resolution_y = 800
    bpy.context.scene.render.filepath = str(PREVIEW_PATH)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered character preview to {PREVIEW_PATH}")

    # Remove preview-only items before export
    bpy.data.objects.remove(floor_obj, do_unlink=True)
    bpy.data.objects.remove(cam_obj, do_unlink=True)
    for l in lights:
        bpy.data.objects.remove(l, do_unlink=True)

    # Save .blend
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print(f"Saved .blend to {BLEND_PATH}")

    # Export FBX
    bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH),
        use_selection=False,
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
    print(f"Exported FBX to {FBX_PATH}")


if __name__ == "__main__":
    main()
