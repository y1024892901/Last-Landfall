# DeepSeek Prompt — Resident Hut

Create a complete, runnable Blender Python script for the compact Level-1 resident hut shown in the attached six-view concept sheet. This is a modest early-settlement dwelling in Last Landfall: two responders arrived by fast boat after detecting a shipwreck, then were ordered to establish a permanent island outpost. Build it from salvageable timber and corrugated sheet metal; it must read as practical storm-resistant housing, not a modern or luxurious cabin.

## Model specification

- Blender 5.2.2 LTS. Use `bpy`, `bmesh`, `mathutils`, `pathlib`, and the Python standard library only.
- One self-contained low-poly building asset. Muted weathered cedar/driftwood, subdued blue-gray salvaged roof metal, restrained charcoal iron fittings. Chunky, readable forms appropriate for a stylized survival-colony game; no photoreal texture maps.
- Keep the full asset within about 4.8 m (X) × 4.4 m (Y) × 3.8 m (Z). Center the footprint at X=0, Y=0, use +Z up, front faces -Y, ground at Z=0.
- A compact single-room timber cabin on four stout raised corner piles, with a visibly braced elevated floor frame above wet coastal ground. Use a simple plank floor and horizontal board walls with visible corner framing.
- Follow the concept sheet’s raised hut, small porch, front door, side windows, and simple corrugated-metal roof. Make one continuous single-slope roof with its high edge at +Y and low edge at -Y; modest eaves on all sides. Add one simple gutter along the low/front edge. Do not add a second roof/canopy.
- A narrow, practical front stair at -Y with 3–4 supported steps, a short porch in front of one plain timber door, and simple partial porch rails on the sides. Include one small shuttered window on each long side; keep the back wall plain except for a small vent. Every rail, stair, support, shutter, gutter, and roof piece must connect plausibly.
- Leave the interior unmodeled and opaque. No furniture, tools, residents, vegetation, terrain, water, barrels, extra buildings, solar panels, antennas, signage, text, logos, or background scene. This is residential shelter, not the research station, medical tent, communications center, or high-tech greenhouse.
- Avoid unsupported or floating pieces, negative dimensions, ground penetration below Z=0, unintended geometry intersections, and inconsistent directions between the views. Intentional overlaps at structural joints are acceptable.

## Script and output requirements

- Save script as `Tools/Blender/ResidentHut_DeepSeek.py`; assume it runs from the project root and create parent directories as needed.
- Create a dedicated model collection `ResidentHut_DeepSeek` and a separately named helper collection for camera/lights. Reruns may replace only those exact collections. Reuse only this asset’s namespaced materials; preserve unrelated scene objects, materials, world, and render settings. Restore temporary scene/render changes before saving.
- Name objects by role (`Foundation_Pile_*`, `Floor_Beam_*`, `Wall_Plank_*`, `Door_*`, `Window_*`, `Roof_Panel_*`, `Gutter_*`, `Stair_*`). Keep parts as separate meshes for later Unity use; do not join the whole building.
- Save `.blend` to `Assets/LastLandfall/Art/Source/Buildings/ResidentHut_DeepSeek.blend`, FBX to `Assets/LastLandfall/Resources/Models/Buildings/ResidentHut_DeepSeek.fbx`, and preview to `Assets/LastLandfall/Art/Previews/Buildings/ResidentHut_DeepSeek.png`.
- Render six true orthographic QA views to `Assets/LastLandfall/Art/References/ScenarioBuildingViews/_renders/ResidentHut_DeepSeek_{Front,Back,Left,Right,Top,Bottom}.png`. Center every camera and fit the entire roof, stair, porch, and piles without clipping. Also render one clean three-quarter preview with useful margins.
- Export only mesh objects from the model collection to FBX, excluding cameras and lights, with stable Unity-friendly transforms.
- Print diagnostics for mesh count, world-space bounds, minimum Z, and non-manifold edges. State that this edge check does not detect intersections between separate objects.
- Return one complete runnable Python script in a single fenced `python` block, with no placeholders or omitted sections.
