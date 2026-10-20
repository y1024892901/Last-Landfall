# Island Nature Modeling Progress

Last updated: 2026-10-20

## Workflow

Gates 00–08 were inspected with scripts previously generated through Gemini. At the user's direction, Gates 09 onward are authored locally as new procedural Blender models without Gemini. Existing OBJ/MTL assets remain read-only design references for palette and target dimensions; new geometry is saved separately under `work/island_final_candidate/Assets_Generated/`, with one `.blend`, FBX, preview, and QA report per gate. Do not mark an asset accepted when its QA report has a failure. Unity is not installed on this machine; FBX files are prepared for import on another computer.

## Completed review gates

| Gate | Asset | Status |
| --- | --- | --- |
| 00 | Existing `IslandReference_V2` terrain | Inspected; existing terrain retained. |
| 01 | `Pine_Windbent_Tall_A` | Generated and exported; Blender inspection completed. |
| 02 | `Pine_Windbent_Short_B` | Generated and exported; source geometry retained. QA reports the source mesh extends 4.137 mm below the ground plane (2 mm tolerance), so it is not accepted. |
| 03 | `Broadleaf_Coastal_A` | Generated and exported; geometry/material counts and FBX re-import were verified. Source geometry retained; minimum Z = -4.287 mm (2 mm tolerance), so it is not accepted. |
| 04 | `Broadleaf_Coastal_B` | Generated and exported; 230 vertices, 424 triangles, six material counts, dimensions, and FBX re-import verified. Source geometry retained; minimum Z = -4.218 mm (2 mm tolerance), so it is not accepted. Preview framing was adjusted without changing the mesh. |
| 05 | `Shrub_SaltTolerant_A` | Generated and exported; 260 vertices, 720 edges, 480 triangles, six material slots, dimensions, MTL colors, and FBX re-import verified. Source geometry retained; minimum Z = -102.168 mm (2 mm tolerance), so it is not accepted. |
| 06 | `Shrub_SaltTolerant_B` | Generated and exported; 260 vertices, 720 edges, 480 triangles, five material slots, dimensions, MTL colors, and FBX re-import verified. Source geometry retained; minimum Z = -121.247 mm (2 mm tolerance), so it is not accepted. |
| 07 | `Grass_CoastalTuft_A` | Generated and exported; 168 vertices, 432 edges, 288 triangles, four material slots, dimensions, topology, and FBX re-import verified. Source geometry retained; minimum Z = +10.507 mm (2 mm tolerance), so it is not accepted. |
| 08 | `Grass_CoastalTuft_B` | Generated and exported; 98 vertices, 252 edges, 168 triangles, three material slots, dimensions, topology, and FBX re-import verified. Source geometry retained; minimum Z = +7.313 mm (2 mm tolerance), so it is not accepted. Oblique preview framing was corrected without changing the mesh. |
| 09 | `Fern_Cliffside` | New procedural candidate PASS: 1,940 vertices, 3,312 triangles; 1.352 × 1.604 × 0.644 m; source palette retained; floor aligned; FBX re-import verified. Original-source inspection copy separately reports its +6.464 mm source offset. |
| 10 | `Wildflower_CoralCream` | New procedural candidate PASS: 1,605 vertices, 2,690 triangles; 0.840 × 0.540 × 0.737 m; material colors, floor alignment, and FBX re-import verified. Preview framing and leaf density were adjusted after review. |
| 11 | `Wildflower_LilacGold` | New procedural candidate PASS: 1,605 vertices, 2,690 triangles; 0.380 × 0.264 × 0.610 m; material colors, floor alignment, and FBX re-import verified. |
| 12 | `Basalt_Boulder_A` | New procedural candidate PASS: 162 vertices, 320 triangles; 1.213 × 1.265 × 1.177 m; detail was increased after rejecting the initial 80-triangle draft; floor and FBX checks pass. |
| 13 | `Basalt_Boulder_B` | New procedural candidate PASS: 162 vertices, 320 triangles; 0.979 × 1.403 × 0.874 m; flatter/wider silhouette; floor and FBX checks pass. |
| 14 | `Basalt_TidewornSlab` | New procedural candidate PASS: 162 vertices, 320 triangles; 1.428 × 1.164 × 0.500 m; floor and FBX checks pass. |
| 15 | `Basalt_RockCluster` | New procedural candidate PASS: 210 vertices, 400 triangles; 1.909 × 1.534 × 1.298 m; five-piece cluster; floor and FBX checks pass. |
| 16 | `Driftwood_BrokenSaltLog` | New procedural candidate PASS: 435 vertices, 794 triangles; 1.444 × 0.289 × 0.409 m; forked branches, grain ridges, and splintered ends; floor and FBX checks pass. |
| 17 | `LastLandfall_Island_Foliage_Assembly` | Assembly PASS: 83 instances across all 16 nature asset types around `IslandReference_V2`; central build zone and southwest landing corridor remain clear. Terrain uses the Unity prototype's 0.02 scale and -0.92 m vertical offset. FBX roundtrip preserved all 84 mesh objects and 495,820 triangles. Preview-only water plane is excluded from FBX. |

Gate scripts, reports, previews, and produced Blender/FBX files for these reviews are kept in `work/island_final_candidate/`. Gate03's copied review package is also on the Desktop at `LastLandfall_Gate03_Broadleaf_Coastal_A`.

## Next work

Gate17 assembly is complete and stored separately from the project source. The terrain vertices and original nature assets were not modified. Review the placement counts and coordinates in `work/island_final_candidate/Reports_Generated/Gate17_assembly_qa.json`; the concise zone plan is `work/island_final_candidate/ASSEMBLY_PLAN.md`. Unity was not available on this computer, so the handoff was verified by Blender FBX re-import rather than by opening it in Unity.

## Gate04 source reference

The unprocessed `Broadleaf_Coastal_B` source mesh has 230 vertices and 424 triangles, source Y-up dimensions `(1.465775, 2.590125, 1.104764)` m, and minimum Y = -4.218 mm. Its exact source geometry and origin are preserved; floor-alignment QA is a reported FAIL at the ±2 mm tolerance.

## Gate05 source reference

`Shrub_SaltTolerant_A` has 260 vertices and 480 triangles. Direct OBJ measurements give Y-up bounds `min=(-0.564236, -0.102168, -0.434761)` and `max=(0.521398, 0.539693, 0.451435)` m, dimensions `(1.085634, 0.641861, 0.886196)` m, and six material triangle counts: bark 80, leaf_sun 96, leaf 61, leaf_shadow 165, leaf_deep 53, leaf_salt 25. Preserve the source geometry; report its converted minimum Z (-0.102168 m) accurately rather than snapping it to the floor.

## Gate06 source reference

Shrub_SaltTolerant_B has 260 vertices, 720 unique edges, and 480 triangles. Direct OBJ measurements give Y-up bounds min=(-0.497960, -0.121247, -0.385623) and max=(0.452205, 0.458315, 0.384442) m, dimensions (0.950165, 0.579562, 0.770065) m, and five material triangle counts: bark 80, leaf 40, leaf_deep 63, leaf_shadow 172, leaf_sun 125. Preserve the source geometry; report its converted minimum Z (-0.121247 m) accurately rather than snapping it to the floor.

## Gate07 source reference

`Grass_CoastalTuft_A` has 168 vertices, 432 unique edges, and 288 triangles. Direct OBJ measurements give Y-up bounds min=(-0.187716, 0.010507, -0.309821) and max=(0.366373, 0.757059, 0.341258) m, dimensions (0.554089, 0.746552, 0.651079) m, and four material triangle counts: grass 102, grass_shadow 51, grass_sun 84, leaf_salt 51. Blender verified all mesh counts, bounds, material colors/distribution, topology diagnostics, and FBX re-import. Preserve the source geometry; report its converted minimum Z (+0.010507 m) accurately rather than moving it to the floor. Deliverables: `Assets_Inspected/Grass_CoastalTuft_A.blend`, `.fbx`, `Previews/Gate07_Grass_CoastalTuft_A.png`, and `Reports/Gate07_qa.json`.

## Gate08 source reference

`Grass_CoastalTuft_B` has 98 vertices, 252 unique edges, and 168 triangles. Direct OBJ measurements give Y-up bounds min=(-0.196436, 0.007313, -0.215600) and max=(0.404191, 0.627178, 0.237402) m, dimensions (0.600627, 0.619865, 0.453002) m, and three material triangle counts: grass 85, grass_shadow 34, grass_sun 49. Blender verified counts, bounds, material colors/distribution, topology diagnostics, and FBX re-import. Preserve the source geometry; report converted minimum Z (+0.007313 m) accurately rather than moving it to the floor. Deliverables: `Assets_Inspected/Grass_CoastalTuft_B.blend`, `.fbx`, `Previews/Gate08_Grass_CoastalTuft_B.png`, and `Reports/Gate08_qa.json`.
