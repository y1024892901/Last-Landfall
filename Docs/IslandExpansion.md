# Expanded archipelago

Multipliers refer to above-water land area, not linear object scale. Source assets are retained for fallback.

| Island | Land area m² | Ratio | New grounded props | Trees before wreck clearance |
| --- | ---: | ---: | ---: | ---: |
| Main | 7312.9 | 4.513× | 2149 | 465 |
| West | 2151.5 | 1.814× | 340 | 74 |
| East | 2097.9 | 1.776× | 313 | 110 |

Each island has an independent FBX and editable Blender source: Island_Main_Expanded, Island_West_Expanded and Island_East_Expanded. All vertices remain registered to the same archipelago origin. Import at position zero, rotation zero and scale one beneath the existing island wrapper; do not add a second manual scale or offset.

The production loader selects the expanded layout only when all three models exist. The editor preview uses the same three assets. Expanded content is grounded in each model; the old independent decoration layers are skipped to avoid duplicate or floating details. The East wreck is a separate, regrounded Gate26_CapsizedWreck_Expanded asset. Its rocky impact shore is kept separate from the three working landing bays.

Coastal terraces use smooth height blends and rounded rocky landing bays. There are no sandy beaches. Trees and rocks retain their original physical sizes; new instances supplement the larger terrain while leaving construction clearings and landing bays open.

One metre construction cells cover all three terrains, including steep cells for future facilities. Standard buildings still require appropriate slope and foundation relief. The grid extends 24 metres beyond the terrain bounds. Water facilities require a fully water-covered footprint within 24 metres of a shore; terrain and water share the same signed coastline field and grid coordinates. Coastal water cells appear only when selecting a dock or water facility, and fade at the outer boundary. Underwater cursor hits are projected onto the water surface to prevent placement offsets. Dock roots use the waterline and reject high cliff anchors.

The initial game camera frames the main island; zooming out can reveal the entire archipelago.

## Regeneration

Run from the Unity project root on a computer with Blender available on `PATH` (or replace `blender` with the path to that computer's Blender executable):

```powershell
blender --background --python Tools/Blender/expand_archipelago.py
blender --background --python Tools/Blender/create_capsized_wreck_on_gate26.py -- --expanded
```

## Verification

ExpansionMetrics.json records projected land area from the generated mesh. UnityConstructionAudit.csv records actual production collider/grid checks, including 3×3 building anchors and valid dock anchors. Anchors are possible starting cells and overlap; they are not a simultaneous building count. UnityConstructionBaseline.csv applies the same construction rules to the original natural models.

The reproducible editor audit source is Tools/QA/ExpansionAudit.cs. Copy it into an isolated Unity project Assets/Editor directory together with the production scripts, models, materials, shaders and settings, then execute ExpansionAudit.Run. It checks exactly three terrain colliders, valid construction on every island, complete 9×3 water footprints, dock waterline placement, and shader compilation, and exports five rendered views. The audit creates an empty scene; do not run it over unsaved editing work.

Rendered views and numerical reports are in Art/Reports/IslandExpansion.
