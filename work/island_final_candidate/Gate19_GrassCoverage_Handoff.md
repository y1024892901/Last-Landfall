# Gate19 Grass Coverage Handoff

## Files

- Blender scene: `LastLandfall_Island_GrassCoverage_Gate19.blend`
- Unity import candidate: `LastLandfall_Island_GrassCoverage_Gate19.fbx` (grass albedo is embedded in the FBX)
- Overview preview: `Gate19_GrassCoverage_Zones_TreeClusters.png`
- QA and placements: `Gate19_grass_coverage_qa.json`
- Grass albedo source: `Grass_Surface_Albedo_Concept.png`

## What changed

- The terrain uses smoothly blended vertex-painted zones: meadow, dry highland grass, coastal soil, exposed rock, and wet rock. The color attributes travel with the FBX mesh.
- The hand-painted grass image repeats 1.9 times across the island and contributes only 10% surface detail, reducing the previous dense mottling and repetition.
- The old 12 scattered trees were replaced by 24 trees in five irregular groves around the island.
- 250 linked 3D coastal-grass tufts cover suitable dry, gentle ground, including the central build meadow.

## Building footprints

Add each future footprint to `BUILDING_FOOTPRINTS_M` in the build script with `name`, center `x`/`y`, `half_width_m`, `half_depth_m`, and optional `rotation_degrees`; rerunning clears only 3D grass tufts inside the footprint plus a 0.5 m margin. The continuous terrain material remains underneath, so foundations can cover it. The empty interface object is included in the Blender scene for identification.

## Import note

The FBX contains the terrain and environment mesh objects, excludes the preview ocean, camera, sun, and hidden source templates, and embeds the grass albedo image. Blender procedural rock shading may simplify to material color during FBX import; the rock zone still has its own exported material slot.
