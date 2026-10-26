"""Build and render a detailed, frame-by-frame greenhouse construction sequence.

Run from the repository root with:
    blender --background Assets/LastLandfall/Art/Source/Buildings/Greenhouse.blend \
        --python Tools/Blender/create_greenhouse_construction_sequence.py

The source greenhouse remains unchanged. The script saves an animated Blender
source file and a PNG for every rendered frame under Art/Previews/Construction.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
FRAMES_PER_PHASE = 12
FPS = 12
RESOLUTION = (768, 672)
BUILD_DURATION = 4
SETTLE_DURATION = 4

PHASES = [
    "01_foundation",
    "02_frame",
    "03_door_and_wood_panels",
    "04_glazing",
    "05_ventilation_and_trim",
    "06_rainwater_and_irrigation",
    "07_growing_beds_and_soil",
    "08_seedling_stems",
    "09_leaf_growth",
]
PHASE_LABELS_ZH = [
    "地基与底座",
    "主体框架",
    "门与木围板",
    "透明面板",
    "通风与收边",
    "集水和灌溉",
    "种植槽与土壤",
    "幼苗茎部",
    "叶片生长",
]


def parse_args():
    if "--" not in sys.argv:
        return {}
    raw = sys.argv[sys.argv.index("--") + 1 :]
    result = {}
    index = 0
    while index < len(raw):
        token = raw[index]
        if token.startswith("--") and index + 1 < len(raw):
            result[token[2:].replace("-", "_")] = raw[index + 1]
            index += 2
        else:
            index += 1
    return result


def root_name(obj):
    return obj.get("construction_source", obj.name)


def component_count(mesh):
    parent = list(range(len(mesh.vertices)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for edge in mesh.edges:
        left, right = edge.vertices
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[left_root] = right_root
    return len({find(index) for index in range(len(parent))})


def separate_loose_parts():
    """Turn disconnected frame, cladding, glass, and metal pieces into objects."""
    candidates = [
        obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH"
        and obj.name.startswith(
            (
                "Greenhouse_Glass_",
                "Greenhouse_Metal_",
                "Greenhouse_Wood_",
            )
        )
    ]
    for obj in candidates:
        source_name = obj.name
        obj["construction_source"] = source_name
        if component_count(obj.data) <= 1:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.separate(type="LOOSE")
        bpy.ops.object.mode_set(mode="OBJECT")
        for part in bpy.context.selected_objects:
            part["construction_source"] = source_name

    # Center each separate part's origin on its own geometry so its small
    # assembly motion expands from the component rather than the old group origin.
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or "construction_source" not in obj:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    bpy.ops.object.select_all(action="DESELECT")


def world_bounds_z(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return min(point.z for point in points), max(point.z for point in points)


def phase_for(obj):
    source = root_name(obj)

    if source.startswith("Preview ground"):
        return None
    if source == "Greenhouse_Wood_salt-worn_cedar":
        return 0
    if source == "Greenhouse_Wood_tarred_frame":
        low, high = world_bounds_z(obj)
        return 0 if (low + high) * 0.5 < 0.29 else 1
    if source in {"Greenhouse_Wood_sun-bleached_boards", "Greenhouse_Metal_rust_repair"}:
        return 2
    if source.startswith("Greenhouse_Glass_"):
        return 3
    if source == "Greenhouse_Metal_faded_sea_green" or source.startswith("Ridge vent"):
        return 4
    if source in {
        "Downspout to rain barrel",
        "Greenhouse downspout elbow",
        "Greenhouse irrigation header",
        "Greenhouse rain barrel",
        "Rain barrel lid",
        "Rain barrel reinforcing band",
        "Rain barrel reinforcing band.001",
        "Irrigation drip emitter",
        "Irrigation drip emitter.001",
        "Irrigation drip emitter.002",
        "Irrigation drip emitter.003",
        "Irrigation drop tube",
        "Irrigation drop tube.001",
        "Irrigation drop tube.002",
        "Irrigation drop tube.003",
    }:
        return 5
    if source.startswith(("Raised growing bed", "Dark soil bed")):
        return 6
    if source.startswith("Crop stem"):
        return 7
    if source.startswith("Crop leaf"):
        return 8

    # Any newly added decorative object joins the final fit-and-finish stage.
    return 4


def set_smooth_interpolation(obj):
    animation = obj.animation_data
    if animation is None or animation.action is None:
        return
    # Blender 5.0+ stores curves in layered actions and creates Bezier handles
    # by default. Keep the explicit handle adjustment for older action data.
    for fcurve in getattr(animation.action, "fcurves", []):
        for key in fcurve.keyframe_points:
            key.interpolation = "BEZIER"
            key.handle_left_type = "AUTO_CLAMPED"
            key.handle_right_type = "AUTO_CLAMPED"


def animate_part(obj, arrival_frame, first_build_frame):
    # Discard any presentation-only animation embedded in the source model.
    # For example, its preview ground is animated for an unrelated render.
    obj.animation_data_clear()
    base_location = obj.location.copy()
    base_scale = obj.scale.copy()
    start_frame = first_build_frame
    grow_frame = arrival_frame
    settle_frame = min(arrival_frame + BUILD_DURATION, first_build_frame + len(PHASES) * FRAMES_PER_PHASE - 1)

    # Hold the part out of view until its place in the build sequence.
    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=start_frame)
    if grow_frame > start_frame:
        obj.keyframe_insert(data_path="hide_render", frame=grow_frame - 1)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=grow_frame)

    obj.location = base_location + Vector((0.0, 0.0, 0.08))
    obj.scale = base_scale * 0.3
    obj.keyframe_insert(data_path="location", frame=grow_frame)
    obj.keyframe_insert(data_path="scale", frame=grow_frame)

    obj.location = base_location
    obj.scale = base_scale
    obj.keyframe_insert(data_path="location", frame=settle_frame)
    obj.keyframe_insert(data_path="scale", frame=settle_frame)
    set_smooth_interpolation(obj)


def add_build_phase_labels(scene, phase_start_frames, phase_end_frame):
    """Create unobtrusive English phase labels for the timeline and renders."""
    labels = [
        "FOUNDATION",
        "FRAME",
        "DOOR AND WALLS",
        "GLAZING",
        "VENTS AND TRIM",
        "WATER SYSTEM",
        "GROWING BEDS",
        "SEEDLINGS",
        "LEAF GROWTH",
    ]
    camera = scene.camera
    if camera is None:
        return
    camera_rotation = camera.rotation_euler.to_matrix()
    camera_right = camera_rotation @ Vector((1, 0, 0))
    camera_up = camera_rotation @ Vector((0, 1, 0))
    camera_forward = camera_rotation @ Vector((0, 0, -1))
    label_position = camera.location + camera_forward * 3.0 - camera_up * 1.65 - camera_right * 1.55

    material = bpy.data.materials.new("Construction Label | warm ivory")
    material.diffuse_color = (0.94, 0.86, 0.68, 1.0)
    material.use_nodes = True
    shader = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader:
        shader.inputs["Base Color"].default_value = material.diffuse_color
        shader.inputs["Emission Color"].default_value = (0.94, 0.86, 0.68, 1.0)
        shader.inputs["Emission Strength"].default_value = 0.8

    label_collection = bpy.data.collections.new("Construction_Sequence_Labels")
    scene.collection.children.link(label_collection)
    for phase_index, (label, frame_start) in enumerate(zip(labels, phase_start_frames)):
        curve = bpy.data.curves.new(f"ConstructionPhase_{phase_index + 1:02d}", "FONT")
        curve.body = f"{phase_index + 1:02d}  {label}"
        curve.size = 0.12
        curve.extrude = 0.0005
        text_obj = bpy.data.objects.new(curve.name, curve)
        label_collection.objects.link(text_obj)
        text_obj.location = label_position
        text_obj.rotation_euler = camera.rotation_euler
        text_obj.data.materials.append(material)
        text_obj.hide_render = True
        text_obj.keyframe_insert(data_path="hide_render", frame=1)
        if frame_start > 1:
            text_obj.keyframe_insert(data_path="hide_render", frame=frame_start - 1)
        text_obj.hide_render = False
        text_obj.keyframe_insert(data_path="hide_render", frame=frame_start)
        phase_end = phase_start_frames[phase_index + 1] - 1 if phase_index + 1 < len(phase_start_frames) else phase_end_frame
        text_obj.keyframe_insert(data_path="hide_render", frame=phase_end)
        text_obj.hide_render = True
        text_obj.keyframe_insert(data_path="hide_render", frame=phase_end + 1)


def build_sequence(frames_per_phase, output_dir, save_blend):
    scene = bpy.context.scene
    separate_loose_parts()

    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 24
    scene.render.resolution_x, scene.render.resolution_y = RESOLUTION
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.render.filepath = str(output_dir / "frames" / "frame_")

    phases = [[] for _ in PHASES]
    static_objects = []
    for obj in scene.objects:
        if obj.type == "MESH":
            phase_index = phase_for(obj)
            if phase_index is None:
                obj.animation_data_clear()
                obj.hide_render = False
                static_objects.append(obj)
            else:
                phases[phase_index].append(obj)

    # Deterministic spatial ordering gives beams, panes, and crops a readable
    # assembly order while keeping each asset's sub-parts independent.
    for parts in phases:
        parts.sort(
            key=lambda obj: (
                round(obj.location.z, 3),
                round(obj.location.y, 3),
                round(obj.location.x, 3),
                obj.name,
            )
        )

    frames_per_phase = max(6, int(frames_per_phase))
    first_build_frame = 1
    phase_start_frames = [1 + index * frames_per_phase for index in range(len(PHASES))]
    for phase_index, parts in enumerate(phases):
        phase_start = phase_start_frames[phase_index]
        phase_end = phase_start + frames_per_phase - 1
        if not parts:
            continue
        span = max(1, phase_end - phase_start - BUILD_DURATION + 1)
        for part_index, obj in enumerate(parts):
            arrival = phase_start + round(part_index * span / max(1, len(parts) - 1))
            animate_part(obj, arrival, first_build_frame)

    final_frame = len(PHASES) * frames_per_phase + SETTLE_DURATION
    scene.frame_end = final_frame
    add_build_phase_labels(scene, phase_start_frames, final_frame)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "frames").mkdir(parents=True, exist_ok=True)

    # Save an editable animation source as a separate file, never over the
    # finished greenhouse model used by the game.
    bpy.ops.wm.save_as_mainfile(filepath=str(save_blend))

    # Render every frame as a standalone image so the game can use individual
    # progress states, and other buildings can use shorter sequences.
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        scene.render.filepath = str(output_dir / "frames" / f"frame_{frame:04d}.png")
        bpy.ops.render.render(write_still=True)

    # Leave the saved animation at the completed greenhouse frame.
    scene.frame_set(scene.frame_end)
    bpy.ops.wm.save_as_mainfile(filepath=str(save_blend))

    phase_manifest = [
        {
            "index": index + 1,
            "phase": PHASES[index],
            "display_name_zh": PHASE_LABELS_ZH[index],
            "start_frame": phase_start_frames[index],
            "end_frame": phase_start_frames[index] + frames_per_phase - 1,
            "parts": len(phases[index]),
        }
        for index in range(len(PHASES))
    ]
    manifest_path = output_dir / "construction_manifest.json"
    manifest_path.write_text(
        __import__("json").dumps(
            {
                "building": "Greenhouse",
                "frames_per_phase": frames_per_phase,
                "frame_count": final_frame,
                "fps": FPS,
                "phases": phase_manifest,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"CONSTRUCTION_SEQUENCE_FRAMES={final_frame}")
    print(f"CONSTRUCTION_SEQUENCE_OUTPUT={output_dir}")
    print(f"CONSTRUCTION_SEQUENCE_BLEND={save_blend}")
    for phase in phase_manifest:
        print(
            "PHASE",
            phase["index"],
            phase["phase"],
            f"frames={phase['start_frame']}-{phase['end_frame']}",
            f"parts={phase['parts']}",
        )


def main():
    args = parse_args()
    frames_per_phase = int(args.get("frames_per_phase", FRAMES_PER_PHASE))
    output_dir = Path(args.get("output", ROOT / "Assets/LastLandfall/Art/Previews/Construction/Greenhouse"))
    save_blend = Path(
        args.get(
            "blend",
            ROOT / "Assets/LastLandfall/Art/Source/Construction/Greenhouse_Construction.blend",
        )
    )
    save_blend.parent.mkdir(parents=True, exist_ok=True)
    build_sequence(frames_per_phase, output_dir, save_blend)


if __name__ == "__main__":
    main()
