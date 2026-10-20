import bpy

terrain = next(o for o in bpy.data.objects if o.name.startswith("IslandReference_V2"))
scale = 0.02
offset = -0.92
paths = {
    "east_inlet": [(8, 10), (8, 8), (7, 6), (6, 4), (5, 2), (4, 0)],
    "south_outlet": [(4, 0), (5, -2), (6, -4), (6, -6), (6, -8), (6, -10), (6, -12), (6, -14)],
    "west_inlet": [(-5, 9), (-5, 7), (-4, 5), (-3, 3), (-2, 1), (-1, -1)],
    "central_alt": [(0, 7), (1, 5), (1, 3), (0, 1), (0, -1), (1, -3), (2, -5), (2, -7)],
    "pond_outlet_west": [(1, -3), (0, -5), (-1, -7), (-1, -9), (-2, -11), (-3, -13), (-4, -15), (-5, -17)],
    "pond_outlet_east": [(1, -3), (2, -5), (3, -7), (3, -9), (2, -11), (1, -13), (0, -15), (0, -17)],
    "southwest_shore": [(-4, -14), (-4.5, -15.5), (-5, -17), (-5, -18), (-5, -19), (-6, -20), (-6, -21), (-7, -22)],
}
for name, coords in paths.items():
    print(name, end=": ")
    for x, y in coords:
        hit, point, normal, face = terrain.ray_cast((x / scale, y / scale, 900.0), (0, 0, -1))
        if hit:
            z = point.z * scale + offset
            print(f"({x},{y})={z:.2f}/{normal.z:.2f}", end=" ")
        else:
            print(f"({x},{y})=MISS", end=" ")
    print()
