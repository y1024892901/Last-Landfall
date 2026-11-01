# DeepSeek Prompt — Fixed Seawater Desalination Plant

Create a complete, runnable Blender Python script for the compact fixed seawater desalination plant shown in the attached six-view concept sheet. This is the next building in Last Landfall's survival progression: headquarters has sent the equipment by helicopter after the island research station completed its first stable data sync. It must read as a robust field unit adapted for a remote island, not a full industrial factory.

Image roles: Image 1 (`DesalinationPlant_Concept_SixViews_DeepSeek.png`) defines this asset's structure and its six orthographic directions. Image 2 (`WaterStorageTank.png`) is only a palette and low-poly style reference; do not copy its tank form or combine it with this machine.

## Modeling target

- Blender 5.2.2 LTS; Python code must use `bpy`, `mathutils`, and the standard library only.
- Stylized low-poly game asset matching the attached water-storage-tank preview: subdued sea-green enamel, sun-bleached cedar, dark iron, a few rust/copper repair bands, and pale concrete footings. Use flat/faceted forms and restrained edge bevels; no photoreal textures.
- One self-contained asset, centered at the origin, ground at Z=0, +Z up, front facing -Y. Overall bounding box must stay within 3.0 m wide × 2.0 m deep × 2.4 m high. Keep all intended geometry inside those bounds.
- The visual silhouette should follow the reference: low timber-and-concrete mounting skid with four concrete feet; open service frame and small sloping canopy; two horizontal pressure-membrane cylinders stacked vertically; vertical seawater pre-filter; clearly readable pump/motor housing; pressure gauges and hand valves; compact, continuous intake and freshwater pipes with elbows and unions. Mark the seawater intake and treated-water outlet by their routing and fittings, not by text. The freshwater outlet should visibly point toward a separate storage tank, but do not include or intersect another tank.
- Keep the unit practical and readable from every direction. Pipes must join their fittings; gauges, valves, membrane housings, supports, and canopy must attach to the frame or skid. Avoid floating parts and obvious geometry clashes. Do not add people, crates, scenery, logos, or text.

## Required script behavior

- Build a clean model collection named `DesalinationPlant_DeepSeek` and keep camera/light/render helpers outside the export collection. On re-run, remove only that model/helper collection so the script is idempotent and does not delete unrelated scene content.
- Create all materials and their Principled BSDF-to-output node links explicitly; do not depend on localized default node names or materials.
- Save a `.blend`, a Unity-ready FBX, and a transparent-free PNG preview to these exact paths relative to the project root:
  - `Assets/LastLandfall/Art/Source/Buildings/DesalinationPlant_DeepSeek.blend`
  - `Assets/LastLandfall/Resources/Models/Buildings/DesalinationPlant_DeepSeek.fbx`
  - `Assets/LastLandfall/Art/Previews/Buildings/DesalinationPlant_DeepSeek.png`
- Render the preview with a neutral pale background, orthographic three-quarter camera, soft studio lighting, and the model centered with margins. Keep render helpers out of the FBX.
- Use a render engine enum supported by Blender 5.2.2 on Windows; if uncertain, leave the scene default rather than assigning an unsupported enum.
- Print a concise report with mesh-object count, world-space bounding dimensions and min Z, plus a basic non-manifold-edge diagnostic. Do not claim that this diagnostic detects intersections.
- Return only the complete Python script in one fenced `python` code block. Include comments for major components and export settings. Do not omit required sections with placeholders or ellipses.
