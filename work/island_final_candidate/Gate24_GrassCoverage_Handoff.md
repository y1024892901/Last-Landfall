# Gate24 Basin Woodland and Riparian Handoff

## Files

- Blender scene: `LastLandfall_Island_GrassCoverage_Gate24.blend`
- Unity import candidate: `LastLandfall_Island_GrassCoverage_Gate24.fbx` (grass albedo is embedded in the FBX)
- Overview preview: `Gate24_GrassCoverage_Zones_TreeClusters.png`
- QA and placements: `Gate24_grass_coverage_qa.json`
- Grass albedo source: `Grass_Surface_Albedo_Concept.png`

## What changed

- The terrain uses smoothly blended vertex-painted zones: meadow, dry highland grass, coastal soil, exposed rock, and wet rock. The color attributes travel with the FBX mesh.
- The hand-painted grass image repeats 1.9 times across the island and contributes only 10% surface detail, reducing the previous dense mottling and repetition.
- 52 trees are arranged with the densest broadleaf woodland in the sheltered basin; the ridge and coast groves remain lighter.
- A small spring-fed pond and narrow, gently meandering creek occupy only part of the basin. A broad damp-meadow and silty-bank color transition softens their edges; the pond bowl and creek bed are carved into this exported candidate mesh. Subtle vertex colors shade shallow edges lighter than the deeper centers, so the water gradient travels in the FBX. 2 larger basalt clusters and slabs anchor selected bends, with 6 shade-loving ferns on damp banks. The source terrain remains unchanged.
- 256 linked 3D coastal-grass tufts are grouped into irregular clumps on dry meadow and stream-bank zones.

## Building footprints

A small tree-free meadow remains near `0.0, 0.0` m. Add each future footprint to `BUILDING_FOOTPRINTS_M` in `Gate24_water_depth_gradient.py` with `name`, center `x`/`y`, `half_width_m`, `half_depth_m`, and optional `rotation_degrees`; rerunning clears only 3D grass tufts inside the footprint plus a 0.5 m margin. The continuous terrain material remains underneath, so foundations can cover it.

## Import note

The FBX contains the terrain and environment mesh objects, excludes the preview ocean, camera, sun, and hidden source templates, and embeds the grass albedo image. Blender procedural rock shading may simplify to material color during FBX import; the rock zone still has its own exported material slot.
