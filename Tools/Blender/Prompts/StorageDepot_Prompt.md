# StorageDepot Level-1 Blender Script Request

Create a complete, rerunnable Blender Python script for a stylized low-poly game asset named `StorageDepot_DeepSeek`, using the attached six-view concept sheet and `ResidentHut_DeepSeek.png` as a style reference. The concept sheet defines the silhouette and material direction. This is an early settlement building assembled by two survivors from local timber and salvaged materials after finding the shipwreck. It is a basic dry-goods store, not a powered/industrial warehouse.

## Target design and scale

- Overall footprint about 5.4 m wide (X) × 4.6 m deep (Y), standing on short raised stone/timber piers; keep the base near Z=0 and total roof height under about 4.2 m.
- Compact timber-frame shed: visible corner posts, horizontal plank walls, raised floor joists and floorboards.
- Broad single-slope roof with salvaged corrugated blue-gray sheet metal, slight rust accents, and enough overhang to protect the wall. High side at the rear (Y positive), low side toward the front entrance (Y negative), matching the concept views.
- Front-facing wide double cargo doors, clearly readable as separate panels, with diagonal timber braces, hinges and a simple latch. Leave the door opening visually legible; do not cover it with stored goods.
- Small high rear ventilation opening with a simple slatted cover.
- A modest loading awning over the front threshold; short non-slip step/ramp from ground to raised platform.
- Simple gutter and downpipe draining into one sealed rain barrel beside the building.
- Three restrained cargo props near, but not blocking, the entry: two low wooden crates and one sealed weatherproof drum. Keep props as separately named mesh objects.
- No solar panels, electrical equipment, modern machinery, signage/text, people, landscape, water, or extra buildings.
- Cohesive stylized low-poly shapes, warm aged cedar, muted blue-gray salvaged metal, restrained teal/rust details; crisp readable geometry and practical proportions.

## Script requirements

1. Save the script as `Tools/Blender/StorageDepot_DeepSeek.py` and use project-relative paths rooted at `Path.cwd()`:
   - `.blend`: `Assets/LastLandfall/Art/Source/Buildings/StorageDepot_DeepSeek.blend`
   - FBX: `Assets/LastLandfall/Resources/Models/Buildings/StorageDepot_DeepSeek.fbx`
   - preview: `Assets/LastLandfall/Art/Previews/Buildings/StorageDepot_DeepSeek.png`
   - six orthographic QA renders: `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/StorageDepot_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`
2. Create a dedicated `StorageDepot_DeepSeek` model collection and a separately named helper collection for cameras/lights. Make reruns idempotent by replacing only those exact collections and reusing only this asset's namespaced materials. Preserve unrelated scene objects and scene/render settings; restore temporary camera, world, and render-state changes before saving the editable scene.
3. Name objects clearly by construction role (`Foundation_Pier_*`, `Wall_Plank_*`, `Door_*`, `Roof_Panel_*`, `Gutter_*`, `Crate_*`, etc.). Keep the structure separable for later Unity use. Use mesh objects, not text labels.
4. Render a clean three-quarter preview plus six full-asset orthographic QA views with neutral background. Center and scale cameras so every appendage, support and roof edge is visible in all directions, with no clipping. The top and bottom views must be true orthographic views.
5. Export FBX containing only the model collection's mesh objects, with applied scales and stable orientation. Do not export camera/light helpers.
6. Print diagnostics: model mesh count, world-space bounds, minimum Z, and count of non-manifold edges. Mention that this does not prove absence of intersections between separate objects.
7. Add concise comments for intentional joints/contacts, and keep the script self-contained and compatible with Blender 5.2.

Return the full Python script in one code block, followed by a short note on dimensions and the key object groups. Do not omit any part of the runnable script.
