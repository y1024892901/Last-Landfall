# Gate17 Island Assembly Plan

## Handoff files

- `Assets_Generated/LastLandfall_Island_Foliage_Assembly.blend` — editable Blender assembly, including the preview water plane.
- `Assets_Generated/LastLandfall_Island_Foliage_Assembly.fbx` — consolidated island and foliage export; the preview water plane is excluded.
- `Previews_Generated/Gate17_Island_Foliage_Assembly.png` — overview image.
- `Reports_Generated/Gate17_assembly_qa.json` — placement list, counts, source dimensions, and FBX round-trip results.

Standalone Gate09–16 candidates are also saved as individual `.blend` and `.fbx` files in `Assets_Generated/`, with one preview and QA report per gate.

## Terrain and coordinate frame

The assembly uses the existing `IslandReference_V2` terrain mesh without editing its vertices. The scene applies the Unity prototype's uniform `0.02` scale and `-0.92 m` vertical offset. Placement coordinates and keep-out regions below are in the scaled scene's meter units, with the scene origin at `(0, 0)`.

The central build area is kept clear as an ellipse centered at the origin with 15 m and 12 m radii along X and Y. A southwest landing corridor is also reserved at X `[-24, -8] m` and Y `[-22, -5] m`.

## Placement approach

- Windbent pines frame the higher outer ridges.
- Coastal broadleaf trees and salt-tolerant shrubs fill selected mid-slope pockets.
- Ferns, grass, and wildflowers add smaller-scale cover on sampled dry ledges and gentler slopes.
- Basalt boulders and slabs anchor exposed rocky areas; clusters create larger formations.
- Broken driftwood sits on lower coastal shelves.
- All placements are sampled against the terrain surface. The central build area and landing corridor are excluded.

## Instance counts

| Asset | Instances |
| --- | ---: |
| `Pine_Windbent_Tall_A` | 3 |
| `Pine_Windbent_Short_B` | 3 |
| `Broadleaf_Coastal_A` | 3 |
| `Broadleaf_Coastal_B` | 3 |
| `Shrub_SaltTolerant_A` | 5 |
| `Shrub_SaltTolerant_B` | 5 |
| `Fern_Cliffside` | 10 |
| `Grass_CoastalTuft_A` | 12 |
| `Grass_CoastalTuft_B` | 12 |
| `Wildflower_CoralCream` | 7 |
| `Wildflower_LilacGold` | 7 |
| `Basalt_Boulder_A` | 3 |
| `Basalt_Boulder_B` | 3 |
| `Basalt_TidewornSlab` | 3 |
| `Basalt_RockCluster` | 2 |
| `Driftwood_BrokenSaltLog` | 2 |
| **Total** | **83** |

## Import note

The FBX was exported and re-imported in Blender. The round-trip retained 84 mesh objects (terrain plus 83 placed instances) and 495,820 triangles. Unity was unavailable on the generation computer, so the Unity import itself remains for the destination computer. The FBX contains the terrain and all placed models; it does not include the Blender-only preview water plane.
