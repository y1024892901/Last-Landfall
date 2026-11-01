# RescueDock Level-1 Blender Script Request

Create a complete, runnable Blender 5.2.2 Python script for a distinct `_DeepSeek` variant of the Level-1 Rescue Dock. Use the attached `RescueDock_Concept_SixViews_DeepSeek.png` for the revised silhouette and six directions; use `RescueDock_Final.png` only as a visual-style reference for the established low-poly Last Landfall asset family. Do not overwrite or modify the baseline RescueDock asset. The outpost crew brought one small fast rescue boat after detecting a shipwreck; this fixed dock secures that boat and makes shoreline launch/recovery safe. This is a simple timber facility, not the later rescue command center.

## Target design and coordinate plan

- Fixed timber pier, approximately 6.2 m wide on X by 4.2 m deep on Y; front is -Y, rear is +Y, +Z is up. Keep the complete assembly including boat within about 6.5 m X × 5.8 m Y × 3.1 m Z.
- Raised open timber deck on six dark timber pilings, with visible cross-beams and separated deck planks. Deck surface around Z=1.6 m; piles start at Z=0.
- Four robust corner mooring posts with iron caps/cleats, plus a few restrained iron tie rings.
- One practical vertical boarding ladder fixed to the front (-Y) edge.
- One orange life ring on a simple low post/rack at an outer corner.
- One compact, open 4.6 m rescue runabout moored parallel to the long edge along +Y. The boat is a separate named mesh assembly, points its bow toward +X, and has a simple tapered low-poly hull, open cockpit, low windshield, two restrained seats, steering wheel, and small outboard at the -X transom. Rescue orange hull and muted teal-gray upper trim.
- Include two or four taut mooring ropes from boat cleats to dock cleats. Keep the boat clearly separate from the dock and leave safe clearance between hull and piles/platform.
- No roof, water, terrain, people, buildings, rescue tower, crane, powered machinery, solar panels, signs, text, or extra vessels. Do not merge the boat with the pier.
- Low-poly, readable, weathered timber construction in sun-bleached warm cedar, charcoal-brown piles, restrained charcoal iron, rescue-orange boat accents, and muted teal-gray trim. Avoid photoreal textures.

## Script and output requirements

1. Save as `Tools/Blender/RescueDock_DeepSeek.py`, rooted at `Path.cwd()`, with these outputs:
   - `.blend`: `Assets/LastLandfall/Art/Source/Infrastructure/RescueDock_DeepSeek.blend`
   - FBX: `Assets/LastLandfall/Resources/Models/Infrastructure/RescueDock_DeepSeek.fbx`
   - preview: `Assets/LastLandfall/Art/Previews/Infrastructure/RescueDock_DeepSeek.png`
   - six orthographic QA images: `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/RescueDock_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`
2. Use a dedicated `RescueDock_DeepSeek` model collection and `Helpers_RescueDock_DeepSeek` helper collection. On rerun, remove only those exact collections. Preserve unrelated scene objects and settings. Use namespaced materials `RescueDock_DeepSeek_*`; reuse existing named materials without deleting or changing unrelated materials.
3. Name the dock and boat parts clearly (`Dock_Pile_*`, `Deck_Plank_*`, `MooringPost_*`, `Ladder_*`, `LifeRing_*`, `Boat_Hull_*`, `Boat_Seat_*`, `Boat_Motor_*`, `MooringLine_*`). Keep boat meshes distinct from pier meshes for later Unity use.
4. Render six centered, full-asset orthographic QA views and a clean three-quarter preview. Fit the boat, ladder, pilings and tie lines in frame; do not crop any component. Top/bottom must be true orthographic.
5. Export only model-collection mesh geometry to FBX (no cameras/lights/helpers). Apply transforms safely for Unity.
6. Print mesh count, world bounds, minimum Z, and non-manifold edge count; state that this does not detect intersections between separate objects.
7. Self-contained standard-library script compatible with Blender 5.2.2. Handle sloped/tapered boat geometry cleanly; avoid zero-length geometry and negative dimensions. Save all outputs and return one complete Python code block, followed by a short dimensions/object-groups note.
