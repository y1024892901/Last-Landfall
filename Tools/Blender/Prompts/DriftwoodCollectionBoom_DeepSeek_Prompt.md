# DeepSeek Prompt — Driftwood Collection Boom

Create a complete, runnable Blender Python script for the floating driftwood collection system shown in the attached six-view concept sheet. This is a Level 1 infrastructure asset in Last Landfall: after establishing a reliable water supply, the island crew builds a salvageable coastal device from supplied rope, simple hardware and recovered timber to gather driftwood from the tidal current.

Image roles: Image 1 (`DriftwoodCollectionBoom_Concept_SixViews_DeepSeek.png`) defines the structure, silhouette and six orthographic directions. Image 2 (`WaterStorageTank.png`) is only a low-poly palette/style reference. Do not copy its tank form or combine it with this asset.

## Modeling target

- Blender 5.2.2 LTS; use `bpy`, `mathutils`, and the Python standard library only.
- Create a stylized low-poly game prop that matches Last Landfall: muted sea-glass teal floats, weathered cedar/driftwood brown, subdued iron fittings and natural rope. Use faceted forms and restrained bevels; no photoreal textures.
- One self-contained floating infrastructure asset, centered at the origin, +Z up, front facing -Y. Its long axis is X. Keep the complete assembly, ropes and mooring weights within 8.2 m wide × 2.8 m deep × 1.4 m high. The lowest geometry should be Z=0; there is no seabed or ground plane in the exported asset.
- Follow Image 1: a shallow symmetrical crescent built from six evenly spaced sealed teal float pods; two weathered wooden barrier logs follow the same arc and are joined with practical metal straps and hinges. Add rope rails/lashings and two mooring lines running from the outer end pods to compact flat mooring weights. Integrate the small open timber collection pocket at the inward middle of the crescent, with simple slats and a clear opening where driftwood would gather. Keep it compact and readable.
- Make each rope, log, float, strap, hinge, collection-pocket slat and mooring weight attach plausibly. Join log segments cleanly around the curve; avoid gaps, zero-length cylinders, floating details and obvious object intersections. The six floats must remain distinct and evenly distributed.
- Do not add water, terrain, a dock, people, loose driftwood, scenery, logos, labels or text. The result is a single reusable gameplay prop.

## Required script behavior

- Be safe and idempotent: create a dedicated model collection named `DriftwoodCollectionBoom_DeepSeek`; on rerun remove only that named model collection and the script's own helper collection. Never clear or delete unrelated scene content. Keep camera/light/render helpers outside the FBX export collection.
- Build materials explicitly with Principled BSDF and Material Output links; do not depend on localized default node names or pre-existing materials.
- Assume the script is launched with the project root as the working directory. Save to these exact paths, relative to that root:
  - `Assets/LastLandfall/Art/Source/Infrastructure/DriftwoodCollectionBoom_DeepSeek.blend`
  - `Assets/LastLandfall/Resources/Models/Infrastructure/DriftwoodCollectionBoom_DeepSeek.fbx`
  - `Assets/LastLandfall/Art/Previews/Infrastructure/DriftwoodCollectionBoom_DeepSeek.png`
- Render six separate, labeled QA PNGs using orthographic cameras: Front (-Y), Back (+Y), Left (-X), Right (+X), Top (+Z), Bottom (-Z). Save them under `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/` as `DriftwoodCollectionBoom_DeepSeek_Front.png`, `_Back.png`, `_Left.png`, `_Right.png`, `_Top.png`, and `_Bottom.png`. Ensure the whole elongated prop fits each frame; use a larger orthographic scale for front/back/top/bottom as needed.
- Also render a clear three-quarter preview with a neutral pale background, soft studio lighting and visible margins. Use a Blender render engine enum supported by Blender 5.2.2 on Windows; if uncertain, keep the current default.
- Export only model mesh geometry to FBX, excluding cameras, lights and render helpers. Apply transforms as needed for Unity without changing the `.blend` model geometry.
- Print a concise diagnostic report: mesh-object count, world-space bounding dimensions, minimum Z, and non-manifold edge count. State clearly in comments or report that the non-manifold diagnostic does not detect object-to-object intersections.
- Return only the complete Python script in one fenced `python` code block. Include comments for major model sections and export settings; do not omit required sections with placeholders or ellipses.
