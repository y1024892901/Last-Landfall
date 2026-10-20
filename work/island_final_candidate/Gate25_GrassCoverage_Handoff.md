# Gate25 Basin Woodland and Riparian Handoff

## Files

- Blender scene: `LastLandfall_Island_GrassCoverage_Gate25.blend`
- Unity import candidate: `LastLandfall_Island_GrassCoverage_Gate25.fbx` (grass albedo is embedded in the FBX)
- Overview preview: `Gate25_GrassCoverage_Zones_TreeClusters.png`
- QA and placements: `Gate25_grass_coverage_qa.json`
- Grass albedo source: `Grass_Surface_Albedo_Concept.png`

## What changed

- The terrain uses smoothly blended vertex-painted zones: meadow, dry highland grass, coastal soil, exposed rock, and wet rock. The color attributes travel with the FBX mesh.
- The terrain vertex colors use a 62% brightness multiplier; the hand-painted grass image repeats 1.9 times across the island and contributes only 10% surface detail, reducing the previous dense mottling and repetition.
- 94 trees are arranged around the island, including a dense 32-tree `Main_Forest` patch on the northwestern slope.
- A small spring-fed pond and a single upper stream occupy only part of the basin. The stream ends inside the pond; its final 3.2 m smoothly blends to the pond water level, with no downstream outlet. A broad damp-meadow and silty-bank color transition softens their edges; the pond bowl and creek bed are carved into this exported candidate mesh. Subtle vertex colors shade shallow edges lighter than the deeper centers, so the water gradient travels in the FBX. 0 larger basalt clusters and slabs anchor selected banks, with 5 shade-loving ferns on damp banks. The source terrain remains unchanged.
- Grass coverage was increased to 646 terrain-aligned tufts in wider irregular meadow and stream-bank clumps.

- 480 smaller wildflower groundcover clumps were added around tree, shrub, fern, and rock bases to soften the transition into the ground.

## River movement in Unity

The Blender/FBX water is static. The upper stream mesh carries a `Flow_UV` layer whose U coordinate follows water from the spring into the pond, and the pond carries `Pond_UV` for slow ripples. In URP Shader Graph, use a Time node and Tiling And Offset node; use an offset of `U = -Time * FlowSpeed` so sampled texture detail travels toward increasing U (flip the sign if it appears to move upstream). Sample a tiling normal map and start around 0.08–0.15 UV units per second, then tune by eye. Use two subtle normal samples at different speeds for less repetitive motion. Keep the pond flow speed near zero and use gentle crossed ripples. A water shader/material is still required in Unity; the FBX alone does not animate.

Tree meshes are exported as individual objects with a `wood` resource hint. Add Unity colliders and harvesting health/drop logic on the game side; this modeling pass does not implement those mechanics.

## Building footprints

A small tree-free meadow remains near `0.0, 0.0` m. Add each future footprint to `BUILDING_FOOTPRINTS_M` in `Gate25_harvest_forest_and_flow_uv.py` with `name`, center `x`/`y`, `half_width_m`, `half_depth_m`, and optional `rotation_degrees`; rerunning clears only 3D grass tufts inside the footprint plus a 0.5 m margin. The continuous terrain material remains underneath, so foundations can cover it.

## Import note

The FBX contains the terrain and environment mesh objects, excludes the preview ocean, camera, sun, and hidden source templates, and embeds the grass albedo image. Blender procedural rock shading may simplify to material color during FBX import; the rock zone still has its own exported material slot.
