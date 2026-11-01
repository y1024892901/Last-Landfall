# DeepSeek Prompt — Solar Power Station

Create a complete, runnable Blender Python script for the Level-2 off-grid solar power station in Last Landfall. The attached six-view concept sheet is the main shape and layout reference. This station is built after the first water systems so the expedition can power communications, research equipment, and the later medical station without relying on a fuel supply.

## Model specification

- Blender 5.2.2 LTS. Use `bpy`, `bmesh`, `mathutils`, `math`, `pathlib`, and Python standard library only.
- One self-contained low-poly game asset. Use a restrained muted gray-teal palette: blue-black photovoltaic glass with fine silver cell dividers, galvanized dark gray steel supports, a teal-gray weatherproof electrical cabinet, pale concrete pad, and restrained amber electrical markers. No photoreal texture maps.
- Use +Z up, front faces -Y, center the footprint around X=0/Y=0, and place the lowest point exactly at Z=0. Keep the complete model within about 4.8 m (X) × 3.8 m (Y) × 2.6 m (Z), including the base pad.
- Build a low rectangular concrete equipment pad with visible corner anchors and expansion seams. The concept shows eight photovoltaic modules in two rows of four on fixed, salt-resistant steel racks tilted upward toward +Y by about 18 degrees. Keep the panel spacing even and support every module along its rails. Add believable posts, cross-braces, rear rails, and base plates; nothing may float.
- Place one compact weatherproof inverter/battery cabinet within the array footprint, beneath the central raised panels, with access facing -Y. It must sit on the pad, clear the panel frames, and have a hinged door, shallow ventilation louvers, small status lights, and an electrical disconnect box. Route a few simple conduits from the panels down the rack posts to the cabinet, then along the pad to a central cable entry. Keep the cable runs short, supported, and visible enough to read.
- Include four clear views of the same array and cabinet from the front, back, left, and right, plus a top view that clearly shows all eight panels and a true bottom view that shows the pad underside, anchors, rack feet, and cable entry. Use the concept image's layout and silhouette, but keep the model physically plausible and easy to read at game camera distance.
- This is a small island microgrid, not a large utility farm. Do not add turbines, poles, transformers, extra buildings, vehicles, people, terrain, vegetation, water, smoke, signage, text, logos, or invented machinery.
- Avoid unsupported/floating parts, negative dimensions, geometry below Z=0, inconsistent axis directions between views, and unintended geometry intersections. Structural joints and panel/rail contacts may overlap intentionally.

## Script and output requirements

- Save the script as `Tools/Blender/SolarPowerStation_DeepSeek.py`; assume it runs from the project root and create output directories as needed.
- Create model collection `SolarPowerStation_DeepSeek` and separately named helper collection `Helpers_SolarPowerStation_DeepSeek` for cameras/lights. A rerun may replace only these exact collections. Preserve unrelated scene objects, materials, world, and render settings. Use namespaced materials, and restore temporary scene/render changes before saving.
- Keep model parts as separate Unity-friendly meshes; name them by role (`Foundation_*`, `Panel_*`, `Rack_*`, `Cabinet_*`, `Conduit_*`, `Electrical_*`). Do not join the whole station.
- Save the `.blend` to `Assets/LastLandfall/Art/Source/Buildings/SolarPowerStation_DeepSeek.blend`, the FBX to `Assets/LastLandfall/Resources/Models/Buildings/SolarPowerStation_DeepSeek.fbx`, and the preview to `Assets/LastLandfall/Art/Previews/Buildings/SolarPowerStation_DeepSeek.png`.
- Render six true orthographic QA views to `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/SolarPowerStation_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`. Fit the whole pad, array, and cabinet in every view. Also render one clean three-quarter preview with useful margins.
- Export only meshes from the model collection to FBX, excluding cameras/lights, with stable Unity-friendly transforms and Z-up.
- Print diagnostics for mesh count, world-space bounds, minimum Z, and non-manifold edges. State clearly that edge manifold checks do not detect intersections between separate objects.
- Return one complete runnable Python script in a single fenced `python` block. Do not omit sections or use placeholders.
