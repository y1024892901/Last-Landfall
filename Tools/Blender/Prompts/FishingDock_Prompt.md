# DeepSeek Prompt — Fishing Dock

Create a complete, runnable Blender Python script for the compact Level-1 fishing dock shown in the attached six-view concept image. This is for the stylized survival-colony game Last Landfall. The crew has found a shipwreck, established a small island outpost, and now needs a modest near-shore fishing pier built from salvaged timber, rope, simple iron fittings, and sealed flotation drums. It supports early hand fishing while the research station prepares the greenhouse supply chain.

Image roles:

1. `FishingDock_Concept_SixViews_DeepSeek.png` defines the structure and six orthographic directions.
2. `WaterStorageTank.png` is only a low-poly palette and finish reference. Do not copy its silhouette or combine it with the dock.

## Model specification

- Blender 5.2.2 LTS; use `bpy`, `bmesh`, `mathutils`, `pathlib`, and the Python standard library only.
- Style: stylized low-poly game asset, chunky readable construction, muted cedar/driftwood browns, sea-glass teal flotation drums, rope natural tan, restrained charcoal iron. No photoreal textures.
- Asset: one compact rectangular floating timber pier, main deck roughly 5.2 m long on X by 2.6 m wide on Y, with its full assembly within approximately 5.8 m (X) × 4.6 m (Y) × 2.2 m (Z). Origin centered on the deck footprint; +Z up; front faces -Y; ground/waterline reference at Z=0.
- Follow Image 1: open plank deck with visible cross-joists, four teal flotation drums protected by simple dark straps and mounted below the deck, four practical corner piles/bollards with dark iron caps, one narrow sloped timber access gangway at the front (-Y) centered on X, a simple net-drying rack on one long side, one closed bait/fish crate on deck, and a compact rope bollard or coil. No roof and no enclosed room.
- Keep the dock clearly distinct from the separate RescueDock: this one is for hand fishing, net handling, and bringing in a small catch, not rescue boat dispatch.
- Every plank, support, drum, rack, rope, and fitting must attach plausibly. Keep the four floats evenly spaced and fully supported. Avoid loose or floating parts, zero-length geometry, obvious gaps, and unintended intersections. Intentional join overlap is acceptable where parts visibly connect.
- Do not include water, terrain, shoreline, buildings, people, a boat, fish, loose gear piles, logos, labels, text, or background scenery. Export only the dock asset.

## Script and output requirements

- Use Blender 5.2.2 compatible API.
- Create a dedicated model collection named `FishingDock_DeepSeek` and a dedicated helper collection. On rerun, remove only those exact script-owned collections. Preserve all unrelated objects, collections, and materials. Use uniquely prefixed material names (`FishingDock_DeepSeek_*`); never delete or replace generic project materials.
- Create Principled BSDF and Material Output links explicitly. Keep camera, lights, groundless studio setup, and other render helpers outside the model export collection.
- Assume the script runs from the project root. Create parent folders as needed and write:
  - `Assets/LastLandfall/Art/Source/Infrastructure/FishingDock_DeepSeek.blend`
  - `Assets/LastLandfall/Resources/Models/Infrastructure/FishingDock_DeepSeek.fbx`
  - `Assets/LastLandfall/Art/Previews/Infrastructure/FishingDock_DeepSeek.png`
  - Six orthographic QA images in `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/` named `FishingDock_DeepSeek_Front.png`, `_Back.png`, `_Left.png`, `_Right.png`, `_Top.png`, `_Bottom.png`.
- Center all QA cameras on the asset. Make the front and back views fit the complete long deck; use a tighter orthographic scale for left and right so the short profile is legible. Render a neutral-background three-quarter preview with useful margins.
- Export only mesh objects in `FishingDock_DeepSeek` to FBX; exclude helpers. Apply/export transforms safely for Unity.
- Print a concise report with mesh-object count, world bounds, minimum Z, and non-manifold-edge count. State that non-manifold checking does not detect intersections between separate objects.
- Return only the complete, runnable Python script in one fenced `python` code block. Include all helpers and sections; no placeholders or ellipses.
