import bpy

BASE = r"D:\Last Landfall\work\island_final_candidate\Assets_Generated\LastLandfall_Island_Foliage_Assembly.blend"
bpy.ops.wm.open_mainfile(filepath=BASE)
terrain = next(o for o in bpy.data.objects if o.name.startswith("IslandReference_V2"))
scale = 0.02
offset = -0.92

print("TERRAIN_BOUNDS", tuple(round(v * scale + (offset if i == 2 else 0), 2) for i, v in enumerate(terrain.bound_box[0])))
for y in range(22, -25, -2):
    cells = []
    for x in range(-26, 29, 2):
        hit, point, normal, face = terrain.ray_cast((x / scale, y / scale, 900.0), (0, 0, -1))
        if not hit:
            cells.append("   ")
            continue
        z = point.z * scale + offset
        cells.append(f"{z:4.1f}")
    print(f"GRID {y:>3}:" + " ".join(cells))

print("FINE_BASIN x=-12..12 y=12..-16; .=low flat, :=low slope, +=slope, ^=high, ~ below sea-level")
for y in range(12, -17, 1):
    cells = []
    for x in range(-12, 13, 1):
        hit, point, normal, face = terrain.ray_cast((x / scale, y / scale, 900.0), (0, 0, -1))
        if not hit:
            cells.append(" ")
            continue
        z = point.z * scale + offset
        cells.append("~" if z < 0 else "." if z < 0.35 else ":" if z < 0.7 else "+" if z < 1.5 else "^")
    print(f"FINE {y:>3}:" + "".join(cells))
