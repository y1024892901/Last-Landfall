# Grass and survivor models

The old imported coastal tuft meshes are hidden at runtime after the replacement grass shader has loaded. Smaller seven-blade, curved tufts are distributed in irregular meadow patches on suitable terrain. The starting island is generated first. Tufts are combined into small terrain chunks, allowing Unity to cull whole chunks without depending on GPU-instanced draws. Wind bends only the blade tips.

Grass is excluded from the pond, the mountain stream, the wreck impact footprint, occupied building cells and roads. Placing or moving a building updates its affected chunks. The land texture remains visible between clusters.

Two independent articulated models are in `Resources/Models/Characters`: `Survivor_Rescuer_v2` and `Survivor_Technician_v2`. Their Blender sources and preview renders are in the corresponding `Art/Source/Characters` and `Art/Previews/Characters` directories. `Tools/Blender/create_survivor_variants.py` regenerates both. Named hip, shoulder and head pivots carry the full limbs and equipment through the walk and idle motions. Characters sample the terrain during movement and avoid water and steep slopes. The earlier `Survivor_Worker` asset remains a loading fallback.

`Tools/QA/GrassCharacterReview.cs` is an editor validation script for an isolated copy of the Unity project. It checks the two crew models, URP materials, human scale, articulated movement, terrain contact, visible grass chunks and the clearing of grass when a building is placed. It also checks that construction, demolition refunds and lighthouse stages use the same visible wood stockpile.
