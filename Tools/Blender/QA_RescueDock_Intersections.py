import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

model_col = bpy.data.collections.get("RescueDock_DeepSeek")
if model_col is None:
    raise RuntimeError("RescueDock_DeepSeek collection not found")

mesh_objects = [obj for obj in model_col.objects if obj.type == "MESH"]
trees = {}
bounds = {}

for obj in mesh_objects:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.transform(bm, matrix=obj.matrix_world, verts=bm.verts)
    trees[obj] = BVHTree.FromBMesh(bm, epsilon=1e-5)
    bm.free()
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    bounds[obj] = (
        tuple(min(v[i] for v in corners) for i in range(3)),
        tuple(max(v[i] for v in corners) for i in range(3)),
    )

intersections = []
for i, obj_a in enumerate(mesh_objects):
    amin, amax = bounds[obj_a]
    for obj_b in mesh_objects[i + 1:]:
        bmin, bmax = bounds[obj_b]
        if any(amax[k] < bmin[k] - 1e-4 or bmax[k] < amin[k] - 1e-4 for k in range(3)):
            continue
        faces = trees[obj_a].overlap(trees[obj_b])
        if faces:
            intersections.append((obj_a.name, obj_b.name, len(faces)))

print(f"Mesh pairs with triangle overlap: {len(intersections)}")
for name_a, name_b, face_count in intersections:
    print(f"{name_a} <-> {name_b}: {face_count} triangle pairs")
