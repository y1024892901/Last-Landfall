# DeepSeek Prompt — Medical Station

Create a complete, runnable Blender Python script for the Level-2 permanent field medical station in *Last Landfall*. The attached new six-view concept image defines the shape and layout; the existing `MedicalStation.png` is only a low-poly style reference. The starting expedition arrived by fast boat after detecting a shipwreck, carrying two crew, basic food/tools/timber, a water purifier, and communications equipment. After the crew surveyed the island, headquarters ordered them to establish a lasting settlement. The initial medical tent already exists; this building is its weather-resistant upgrade, made possible by the new solar power system. It must feel practical, small, and buildable by a remote expedition, not like a modern urban hospital.

## Model specification

- Target Blender 5.2.2 LTS. Use `bpy`, `bmesh`, `mathutils`, `math`, `pathlib`, and Python standard library only.
- Create one self-contained stylized low-poly game asset. Match the attached style reference: clean geometric forms, soft studio presentation, and a restrained palette of warm off-white insulated panels, pale seafoam/blue-green sheet-metal trim, weathered light timber, concrete gray, dark teal glazing, and a small muted medical red cross. No photoreal textures.
- Use +Z up, front/access side facing -Y, center at X=0/Y=0, and keep the lowest point exactly at Z=0. Keep the overall footprint within about 5.0 m (X) × 4.5 m (Y) × 3.8 m (Z), including the roof, porch, and foundation.
- Build a compact single-room modular clinic with cream insulated wall panels, vertical panel joints, a shallow pitched gable roof, pale teal roof edge, rain gutters/downpipes, and a modest covered patient-entry veranda on the -Y side. Use simple, storm-resistant forms that a small crew could assemble from delivered panels, salvaged timber, and local materials.
- The front must have one clear entry door, a broad medical observation window, a small red cross sign, two or three restrained field supply crates, and a short centered set of porch steps or a low ramp. Add timber porch posts and a simple guard rail only where shown in the concept. The building should read as a clinic at game distance without adding excessive detail.
- Add one compact exterior utility/medical cabinet and a few short, supported pipes or conduits on a side wall, as shown in the concept. Keep the back and both sides mostly plain, with the same roof and foundation. Do not invent extra doors or windows. No interior cutaway.
- Raise the floor on simple concrete footings and cross-braced beams so the true bottom view can show the underside frame and supports. The structure must remain physically supported; no floating roof, porch, steps, fixtures, or braces. Keep all geometry at or above Z=0.
- Produce the same model in six true orthographic views: front (-Y), back (+Y), left (-X), right (+X), top, and true bottom. Follow the attached six-view layout, keep proportions consistent, and frame the whole structure in every view. Add a clean three-quarter preview separately.
- Do not add people, terrain, vegetation, sea, vehicles, extra buildings, beds or interior furniture, text paragraphs, watermarks, weapons, dramatic lighting, or unrelated machinery. The cross may be a simple geometric symbol.
- Avoid unsupported/floating parts, negative dimensions, geometry below Z=0, inconsistent axes between views, and unintended geometry intersections. Contact at structural joints, trim, wall panels, and attached fixtures may overlap intentionally.

## Script and output requirements

- Save the script as `Tools/Blender/MedicalStation_DeepSeek.py`; assume it runs from the project root and create output directories as needed.
- Use a dedicated model collection named `MedicalStation_DeepSeek` and a separate `Helpers_MedicalStation_DeepSeek` collection for cameras/lights. A rerun may replace only those exact collections. Preserve unrelated scene objects, materials, world, and render settings. Namespace newly created materials and restore temporary render changes before saving.
- Keep model parts as separately named Unity-friendly meshes (`Foundation_*`, `Wall_*`, `Roof_*`, `Porch_*`, `Door_*`, `Window_*`, `MedicalSign_*`, `Utility_*`). Do not join the whole building.
- Save the `.blend` to `Assets/LastLandfall/Art/Source/Buildings/MedicalStation_DeepSeek.blend`, the FBX to `Assets/LastLandfall/Resources/Models/Buildings/MedicalStation_DeepSeek.fbx`, and the preview to `Assets/LastLandfall/Art/Previews/Buildings/MedicalStation_DeepSeek.png`.
- Render six true orthographic QA views to `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/MedicalStation_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`.
- Export only meshes from the model collection to FBX, excluding cameras and lights, with stable Unity-friendly transforms and Z-up.
- Print diagnostics for mesh count, world-space bounds, minimum Z, and non-manifold edges. State clearly that edge-manifold checks do not detect intersections between separate objects.
- Return one complete runnable Python script in a single fenced `python` block. Do not omit sections or use placeholders.
