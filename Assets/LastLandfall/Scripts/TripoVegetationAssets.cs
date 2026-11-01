using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEngine;
using LastLandfall.Prototype;

namespace LastLandfall
{
    // Shared by the saved editor preview and the playable archipelago.
    public static class TripoVegetationAssets
    {
        const string Path = "Models/Environment/Tripo/VegetationRows/";
        const string CollectionName = "Tripo Vegetation Collection";
        const string VersionTagName = "Layout_v5_LushGrass";
        static readonly List<Transform> ActiveVegetation = new List<Transform>();

        static readonly string[] Names = {
            "Spruce", "Oak", "Sapling", "YoungPine", "Birch", "Willow", "Cypress", "CoastalJuniper", "Bamboo",
            "RoundShrub", "LowShrub", "Hazel", "WildRose", "BerryBush",
            "WoodFern", "BroadleafHerb", "GreenGrass", "SeedGrass",
            "Daisy", "YellowFlowers", "Cattail", "Sedge", "UprightFern", "Bracken",
            "Violet", "Cornflower", "WhiteClover", "YellowGroundcover"
        };
        static readonly float[] Heights = {
            10f, 9f, 6f, 6.5f, 9f, 8f, 10f, 6f, 4.5f,
            1.6f, 1f, 1.8f, 1.4f, 1.4f,
            1f, .65f, .55f, .85f,
            .5f, .45f, 1.35f, .8f, 1f, .8f,
            .35f, .5f, .3f, .25f
        };
        static readonly Dictionary<string, Material> Materials = new Dictionary<string, Material>();

        public static void Apply(GameObject island)
        {
            if (island == null) return;
            Materials.Clear();
            var prefabs = new GameObject[Names.Length];
            for (int i = 0; i < Names.Length; i++)
            {
                prefabs[i] = Resources.Load<GameObject>(Path + Names[i]);
                if (prefabs[i] == null) return; // Keep the existing trees if an import is incomplete.
            }

            Transform existing = island.transform.Find(CollectionName);
            if (existing != null)
            {
                ReplaceYoungPines(existing);
                if (existing.Find(VersionTagName) != null) return;
                if (Application.isPlaying) Object.Destroy(existing.gameObject);
                else Object.DestroyImmediate(existing.gameObject);
            }

            var surfaces = new List<MeshCollider>();
            var waterCells = new HashSet<Vector2Int>();
            var waterPoints = new List<Vector3>();
            var wrecks = new List<Bounds>();

            foreach (var filter in island.GetComponentsInChildren<MeshFilter>())
            {
                if (filter.sharedMesh == null) continue;
                string n = filter.name.ToLowerInvariant();
                if (n.Contains("terrain source") && filter.TryGetComponent<MeshCollider>(out var surface))
                    surfaces.Add(surface);
                if (n.Contains("water"))
                {
                    var verts = filter.sharedMesh.vertices;
                    for (int i = 0; i < verts.Length; i++)
                    {
                        Vector3 p = filter.transform.TransformPoint(verts[i]);
                        waterCells.Add(Cell(p));
                        if (i % 6 == 0) waterPoints.Add(p);
                    }
                }
            }

            foreach (var r in island.GetComponentsInChildren<Renderer>())
            {
                string n = r.name.ToLowerInvariant();
                if (n.StartsWith("wreck_")) wrecks.Add(r.bounds);
                if (n.Contains("conifer") || n.Contains("pine") || n.Contains("broadleaf") || n.Contains("tree") || n.Contains("palm"))
                    r.enabled = false;
            }

            Physics.SyncTransforms();
            var root = new GameObject(CollectionName);
            root.transform.SetParent(island.transform, false);
            var versionMarker = new GameObject(VersionTagName);
            versionMarker.transform.SetParent(root.transform, false);
            ActiveVegetation.Clear();

            var random = new System.Random(281035);
            var occupiedTrees = new List<Vector3>();
            var occupiedUnderstory = new List<Vector3>();
            int placed = 0;
            int treeCount = 0;
            int largeTreeCount = 0;
            int shrubCount = 0;
            int herbCount = 0;
            int surfaceIndex = 0;

            foreach (var surface in surfaces)
            {
                if (!surface.enabled || !surface.TryGetComponent<Renderer>(out var land) || !land.enabled) continue;
                Bounds b = land.bounds;
                bool isMainIsland = surfaceIndex == 0;

                // Main island gets 9 lush woodland groves framing the northern peaks, slopes and coast;
                // satellite islands get 3 groves scaled to their landmass.
                Vector2[] anchors = isMainIsland
                    ? new[]
                    {
                        new Vector2(0.22f, 0.78f), // NW alpine conifer ridge
                        new Vector2(0.48f, 0.82f), // North mountain crown forest
                        new Vector2(0.75f, 0.76f), // NE mixed highland grove
                        new Vector2(0.82f, 0.54f), // Upper East slope woodland
                        new Vector2(0.78f, 0.32f), // Lower East broadleaf woodland
                        new Vector2(0.18f, 0.56f), // Upper West creekside forest
                        new Vector2(0.20f, 0.34f), // Lower West valley woodland
                        new Vector2(0.30f, 0.18f), // SW coastal headland grove
                        new Vector2(0.68f, 0.18f)  // SE pondside headland grove
                    }
                    : new[]
                    {
                        new Vector2(0.26f, 0.70f),
                        new Vector2(0.72f, 0.64f),
                        new Vector2(0.68f, 0.30f)
                    };

                for (int grove = 0; grove < anchors.Length; grove++)
                {
                    Vector3 center = new Vector3(
                        Mathf.Lerp(b.min.x, b.max.x, anchors[grove].x),
                        0f,
                        Mathf.Lerp(b.min.z, b.max.z, anchors[grove].y));

                    if (!FindGround(surface, b, center, waterCells, wrecks, out var groveHit))
                    {
                        bool found = false;
                        for (int probe = 0; probe < 65 && !found; probe++)
                        {
                            Vector3 candidate = center + new Vector3(
                                (Next(random) - 0.5f) * b.size.x * 0.28f,
                                0f,
                                (Next(random) - 0.5f) * b.size.z * 0.28f);
                            found = FindGround(surface, b, candidate, waterCells, wrecks, out groveHit);
                        }
                        if (!found) continue;
                    }

                    center = groveHit.point;
                    float radius = isMainIsland
                        ? Mathf.Clamp(Mathf.Min(b.size.x, b.size.z) * 0.165f, 12.0f, 20.0f)
                        : Mathf.Clamp(Mathf.Min(b.size.x, b.size.z) * 0.155f, 6.0f, 10.0f);

                    int targetTrees = isMainIsland ? 15 : 8;
                    int focalBudget = isMainIsland ? 4 : 2;
                    int trees = 0;

                    for (int attempt = 0; attempt < 240 && trees < targetTrees; attempt++)
                    {
                        Vector3 candidate = PatchPoint(center, radius, random);
                        if (!FindGround(surface, b, candidate, waterCells, wrecks, out var hit)) continue;
                        if (isMainIsland && InClearing(hit.point, b)) continue;

                        float minTreeSpacing = trees < focalBudget ? 3.1f : 2.3f;
                        bool crowded = false;
                        for (int i = 0; i < occupiedTrees.Count; i++)
                        {
                            if (FlatDistance(occupiedTrees[i], hit.point) < minTreeSpacing)
                            {
                                crowded = true;
                                break;
                            }
                        }
                        if (crowded) continue;

                        bool isFocal = trees < focalBudget;
                        int kind = PickGroveTreeKind(surfaceIndex, grove, trees, isFocal, random);
                        float height = isFocal
                            ? Mathf.Lerp(7.4f, 9.4f, Next(random))
                            : kind == 7 ? Mathf.Lerp(3.5f, 4.8f, Next(random))
                            : kind == 8 ? Mathf.Lerp(4.2f, 5.6f, Next(random))
                            : Mathf.Lerp(5.0f, 6.8f, Next(random));

                        Place(kind, hit.point, height);
                        occupiedTrees.Add(hit.point);
                        trees++;
                        treeCount++;
                        if (isFocal) largeTreeCount++;
                    }

                    // Understory shrubs & shade ferns: kept subordinate to the lush tree canopy
                    int targetShrubs = isMainIsland ? 9 : 5;
                    int[] shrubPalette = grove % 2 == 0
                        ? new[] { 9, 10, 11, 14, 23 }
                        : new[] { 10, 12, 13, 14, 22 };

                    for (int attempt = 0, count = 0; attempt < 110 && count < targetShrubs; attempt++)
                    {
                        float ringRadius = radius * Mathf.Lerp(0.45f, 1.15f, Next(random));
                        float angle = Next(random) * Mathf.PI * 2f;
                        Vector3 candidate = center + new Vector3(Mathf.Cos(angle) * ringRadius, 0f, Mathf.Sin(angle) * ringRadius * 0.78f);
                        if (!FindGround(surface, b, candidate, waterCells, wrecks, out var hit)) continue;
                        if (isMainIsland && InClearing(hit.point, b)) continue;

                        bool tooClose = false;
                        for (int i = 0; i < occupiedTrees.Count; i++)
                            if (FlatDistance(occupiedTrees[i], hit.point) < 1.35f) { tooClose = true; break; }
                        for (int i = 0; i < occupiedUnderstory.Count && !tooClose; i++)
                            if (FlatDistance(occupiedUnderstory[i], hit.point) < 1.65f) { tooClose = true; break; }
                        if (tooClose) continue;

                        int kind = shrubPalette[count % shrubPalette.Length];
                        Place(kind, hit.point, Heights[kind] * Mathf.Lerp(0.68f, 0.92f, Next(random)));
                        occupiedUnderstory.Add(hit.point);
                        count++;
                        shrubCount++;
                    }
                }

                // Woodland connector trees across slopes & ridges so groves blend into a continuous lush forest belt
                int targetConnectorTrees = isMainIsland ? 32 : 8;
                int[] connectorKinds = isMainIsland
                    ? new[] { 0, 1, 3, 4, 6, 2, 3, 4 }
                    : new[] { 3, 4, 6, 7, 2 };
                for (int attempt = 0, count = 0; attempt < 260 && count < targetConnectorTrees; attempt++)
                {
                    Vector3 candidate = new Vector3(
                        Mathf.Lerp(b.min.x, b.max.x, Mathf.Lerp(0.12f, 0.88f, Next(random))),
                        0f,
                        Mathf.Lerp(b.min.z, b.max.z, Mathf.Lerp(0.12f, 0.88f, Next(random))));
                    if (!FindGround(surface, b, candidate, waterCells, wrecks, out var hit)) continue;
                    if (isMainIsland && InClearing(hit.point, b)) continue;

                    bool crowded = false;
                    for (int i = 0; i < occupiedTrees.Count; i++)
                        if (FlatDistance(occupiedTrees[i], hit.point) < 2.6f) { crowded = true; break; }
                    if (crowded) continue;

                    int kind = connectorKinds[count % connectorKinds.Length];
                    bool tall = count % 4 == 0;
                    float height = tall
                        ? Mathf.Lerp(7.2f, 8.8f, Next(random))
                        : kind == 7 ? Mathf.Lerp(3.5f, 4.6f, Next(random))
                        : Mathf.Lerp(5.0f, 6.7f, Next(random));
                    Place(kind, hit.point, height);
                    occupiedTrees.Add(hit.point);
                    count++;
                    treeCount++;
                    if (tall) largeTreeCount++;
                }

                // Riparian corridor on the main island: graceful Willows, Bamboo, Birch and Pines along the creek & pond banks.
                if (isMainIsland && waterPoints.Count > 0)
                {
                    int riparianTrees = 0;
                    for (int attempt = 0; attempt < 160 && riparianTrees < 16; attempt++)
                    {
                        Vector3 wp = waterPoints[random.Next(waterPoints.Count)];
                        float angle = Next(random) * Mathf.PI * 2f;
                        float bankDist = Mathf.Lerp(2.2f, 5.8f, Next(random));
                        Vector3 candidate = wp + new Vector3(Mathf.Cos(angle) * bankDist, 0f, Mathf.Sin(angle) * bankDist);
                        if (!FindGround(surface, b, candidate, waterCells, wrecks, out var hit)) continue;

                        bool crowded = false;
                        for (int i = 0; i < occupiedTrees.Count; i++)
                            if (FlatDistance(occupiedTrees[i], hit.point) < 2.6f) { crowded = true; break; }
                        if (crowded) continue;

                        // Only 1-2 accent Willows (5) near the pond; mostly Birch (4), YoungPine (3), Bamboo (8) and Sapling (2)
                        int kind = riparianTrees == 0 ? 5 : riparianTrees % 4 == 1 ? 8 : riparianTrees % 2 == 0 ? 4 : 3;
                        float height = kind == 5 ? Mathf.Lerp(6.4f, 8.0f, Next(random))
                                     : kind == 8 ? Mathf.Lerp(4.4f, 5.8f, Next(random))
                                     : Mathf.Lerp(5.4f, 6.9f, Next(random));
                        Place(kind, hit.point, height);
                        occupiedTrees.Add(hit.point);
                        riparianTrees++;
                        treeCount++;
                    }

                    int riparianReeds = 0;
                    int[] reedPalette = { 20, 21, 22, 14, 15 }; // Cattail, Sedge, UprightFern, WoodFern, BroadleafHerb
                    for (int attempt = 0; attempt < 120 && riparianReeds < 22; attempt++)
                    {
                        Vector3 wp = waterPoints[random.Next(waterPoints.Count)];
                        float angle = Next(random) * Mathf.PI * 2f;
                        float bankDist = Mathf.Lerp(1.5f, 3.6f, Next(random));
                        Vector3 candidate = wp + new Vector3(Mathf.Cos(angle) * bankDist, 0f, Mathf.Sin(angle) * bankDist);
                        if (!FindGround(surface, b, candidate, waterCells, wrecks, out var hit)) continue;

                        bool crowded = false;
                        for (int i = 0; i < occupiedUnderstory.Count; i++)
                            if (FlatDistance(occupiedUnderstory[i], hit.point) < 1.35f) { crowded = true; break; }
                        if (crowded) continue;

                        int kind = reedPalette[riparianReeds % reedPalette.Length];
                        Place(kind, hit.point, Heights[kind] * Mathf.Lerp(0.70f, 1.0f, Next(random)));
                        occupiedUnderstory.Add(hit.point);
                        riparianReeds++;
                        herbCount++;
                    }
                }

                // Anno 1800 Style: Tight, composite wild foliage clusters along woodland edges & rock bases.
                // Open settlement plains stay 100% clean and flat for construction; no lone grass spikes scattered about!
                int clusterCount = isMainIsland ? 22 : 9;
                int itemsPerCluster = isMainIsland ? 14 : 10;
                // Palette: SeedGrass (17), GreenGrass (16), WoodFern (14), UprightFern (22), WhiteClover (26), YellowGroundcover (27), Daisy (18), Violet (24)
                int[] annoFoliagePalette = { 17, 16, 17, 14, 26, 16, 22, 27, 18, 17, 16, 24 };

                for (int c = 0; c < clusterCount; c++)
                {
                    Vector3 clusterCenter = Vector3.zero;
                    bool centerFound = false;

                    // Anchor clusters near tree bases or woodland fringes
                    if (occupiedTrees.Count > 0 && Next(random) < 0.85f)
                    {
                        Vector3 treePos = occupiedTrees[random.Next(occupiedTrees.Count)];
                        float angle = Next(random) * Mathf.PI * 2f;
                        float offsetDist = Mathf.Lerp(1.2f, 2.8f, Next(random));
                        Vector3 candidate = treePos + new Vector3(Mathf.Cos(angle) * offsetDist, 0f, Mathf.Sin(angle) * offsetDist);
                        if (FindGround(surface, b, candidate, waterCells, wrecks, out var tHit))
                        {
                            if (!isMainIsland || !InClearing(tHit.point, b))
                            {
                                clusterCenter = tHit.point;
                                centerFound = true;
                            }
                        }
                    }

                    // Fallback to peripheral slope / ridge if tree anchor wasn't found
                    if (!centerFound)
                    {
                        for (int attempt = 0; attempt < 20 && !centerFound; attempt++)
                        {
                            Vector3 candidate = new Vector3(
                                Mathf.Lerp(b.min.x, b.max.x, Mathf.Lerp(0.12f, 0.88f, Next(random))),
                                0f,
                                Mathf.Lerp(b.min.z, b.max.z, Mathf.Lerp(0.12f, 0.88f, Next(random))));
                            if (FindGround(surface, b, candidate, waterCells, wrecks, out var sHit))
                            {
                                if (!isMainIsland || !InClearing(sHit.point, b))
                                {
                                    clusterCenter = sHit.point;
                                    centerFound = true;
                                }
                            }
                        }
                    }

                    if (!centerFound) continue;

                    // Dense, tight cluster radius (1.2m ~ 2.0m) so all plants pack into a cohesive wild mound
                    float clusterRadius = Mathf.Lerp(1.2f, 2.0f, Next(random));
                    int placedInCluster = 0;

                    for (int attempt = 0; attempt < 45 && placedInCluster < itemsPerCluster; attempt++)
                    {
                        Vector3 itemCandidate = PatchPoint(clusterCenter, clusterRadius, random);
                        if (!FindGround(surface, b, itemCandidate, waterCells, wrecks, out var hit)) continue;
                        if (isMainIsland && InClearing(hit.point, b)) continue;

                        int kind = annoFoliagePalette[placedInCluster % annoFoliagePalette.Length];
                        float scaleFactor = Heights[kind] * Mathf.Lerp(0.60f, 0.95f, Next(random));
                        Place(kind, hit.point, scaleFactor);
                        placedInCluster++;
                        herbCount++;
                    }
                }

                surfaceIndex++;
            }

            Debug.Log($"Tripo vegetation balanced: {placed} total ({treeCount} trees [{largeTreeCount} canopy], {shrubCount} shrubs, {herbCount} riparian/meadow herbs) across {surfaces.Count} islands.");

            void Place(int kind, Vector3 ground, float height)
            {
                if (kind == 3) kind = 0;
                var plant = Object.Instantiate(prefabs[kind], root.transform, false);
                plant.name = "Tripo_Vegetation_" + Names[kind] + "_" + placed;
                var renderers = plant.GetComponentsInChildren<Renderer>();
                Bounds pb = renderers[0].bounds;
                foreach (var r in renderers) pb.Encapsulate(r.bounds);
                plant.transform.localScale *= height / Mathf.Max(.001f, pb.size.y);
                plant.transform.Rotate(Vector3.up, Next(random) * 360f, Space.World);
                pb = renderers[0].bounds;
                foreach (var r in renderers) pb.Encapsulate(r.bounds);
                plant.transform.position += ground - new Vector3(pb.center.x, pb.min.y + .035f, pb.center.z);
                foreach (var r in renderers)
                {
                    r.name = plant.name;
                    var slots = r.sharedMaterials;
                    for (int m = 0; m < slots.Length; m++)
                    {
                        var match = Regex.Match(slots[m] == null ? "" : slots[m].name, @"Row\d{2}");
                        if (match.Success) slots[m] = MaterialFor(match.Value);
                    }
                    r.sharedMaterials = slots;
                    r.shadowCastingMode = kind < 9
                        ? UnityEngine.Rendering.ShadowCastingMode.On
                        : UnityEngine.Rendering.ShadowCastingMode.Off;
                }
                ActiveVegetation.Add(plant.transform);
                placed++;
            }
        }

        static void ReplaceYoungPines(Transform collection)
        {
            foreach (var filter in collection.GetComponentsInChildren<MeshFilter>(true))
            {
                if (!filter.name.StartsWith("Tripo_Vegetation_YoungPine_") || !filter.TryGetComponent<Renderer>(out var renderer)) continue;
                var source = Resources.Load<GameObject>(Path + "Spruce");
                var replacement = source != null ? source.GetComponentInChildren<MeshFilter>() : null;
                if (replacement == null || replacement.sharedMesh == null) return;
                Bounds before = renderer.bounds;
                filter.sharedMesh = replacement.sharedMesh;
                float height = renderer.bounds.size.y;
                filter.transform.localScale *= before.size.y / Mathf.Max(.001f, height);
                Bounds after = renderer.bounds;
                filter.transform.position += new Vector3(before.center.x-after.center.x,
                    before.min.y-after.min.y, before.center.z-after.center.z);
                renderer.sharedMaterial = MaterialFor("Row01");
                filter.name = filter.name.Replace("Tripo_Vegetation_YoungPine_", "Tripo_Vegetation_Spruce_");
            }
        }

        public static void ClearVegetationAt(Vector3 center, float radius = 1.35f)
        {
            float rSq = radius * radius;
            if (ActiveVegetation.Count == 0)
            {
                var col = GameObject.Find(CollectionName);
                if (col != null)
                {
                    for (int i = 0; i < col.transform.childCount; i++)
                    {
                        var child = col.transform.GetChild(i);
                        if (child != null && child.name.StartsWith("Tripo_Vegetation_"))
                            ActiveVegetation.Add(child);
                    }
                }
            }

            for (int i = ActiveVegetation.Count - 1; i >= 0; i--)
            {
                var tr = ActiveVegetation[i];
                if (tr == null)
                {
                    ActiveVegetation.RemoveAt(i);
                    continue;
                }
                Vector3 p = tr.position;
                float dx = p.x - center.x;
                float dz = p.z - center.z;
                if (dx * dx + dz * dz <= rSq)
                {
                    if (Application.isPlaying) Object.Destroy(tr.gameObject);
                    else Object.DestroyImmediate(tr.gameObject);
                    ActiveVegetation.RemoveAt(i);
                }
            }
        }

        static int PickGroveTreeKind(int surfaceIndex, int grove, int treeIndex, bool isFocal, System.Random random)
        {
            if (surfaceIndex == 0)
            {
                // Main island biome-specific tree mix:
                // 0:Spruce, 1:Oak, 2:Sapling, 3:YoungPine, 4:Birch, 5:Willow, 6:Cypress, 7:CoastalJuniper, 8:Bamboo
                switch (grove)
                {
                    case 0: // NW alpine conifer ridge
                    case 1: // North mountain crown forest
                        return isFocal ? (treeIndex % 2 == 0 ? 0 : 6) : (treeIndex % 3 == 0 ? 6 : 3);
                    case 2: // NE mixed highland grove
                        return isFocal ? 0 : (treeIndex % 2 == 0 ? 3 : 4);
                    case 3: // Upper East slope woodland
                    case 4: // Lower East broadleaf woodland
                        return isFocal ? 1 : (treeIndex % 3 == 0 ? 4 : 2);
                    case 5: // Upper West creekside forest
                    case 6: // Lower West valley woodland
                        return isFocal ? (treeIndex % 2 == 0 ? 1 : 0) : (treeIndex % 3 == 0 ? 4 : treeIndex % 2 == 0 ? 3 : 2);
                    case 7: // SW coastal headland grove
                        return isFocal ? 6 : (treeIndex % 2 == 0 ? 7 : 3);
                    default: // SE pondside headland grove
                        return isFocal ? (treeIndex == 0 ? 5 : 1) : (treeIndex % 4 == 0 ? 8 : treeIndex % 2 == 0 ? 4 : 3);
                }
            }
            if (surfaceIndex == 1)
            {
                // West rocky satellite: wind-hardy pines, cypress & coastal juniper
                return isFocal ? 0 : (grove == 0 ? (treeIndex % 2 == 0 ? 3 : 6) : 7);
            }
            // East shipwreck satellite: birch, coastal juniper & young pine
            return isFocal ? 4 : (treeIndex % 2 == 0 ? 7 : 2);
        }

        static Vector3 PatchPoint(Vector3 center, float radius, System.Random random)
        {
            float angle = Next(random) * Mathf.PI * 2f, r = Mathf.Sqrt(Next(random)) * radius;
            return center + new Vector3(Mathf.Cos(angle) * r, 0f, Mathf.Sin(angle) * r * .75f);
        }

        static float FlatDistance(Vector3 a, Vector3 b) => new Vector2(a.x - b.x, a.z - b.z).magnitude;

        static bool InClearing(Vector3 p, Bounds b)
        {
            // Keep a central settlement meadow clear on the main plateau while allowing peripheral groves.
            float u = (p.x - b.center.x) / (b.size.x * .14f);
            float v = (p.z - b.center.z) / (b.size.z * .15f);
            return u * u + v * v < 1f;
        }

        static bool FindGround(MeshCollider surface, Bounds bounds, Vector3 candidate, HashSet<Vector2Int> water, List<Bounds> wrecks, out RaycastHit hit)
        {
            candidate.y = bounds.max.y + 10f;
            if (!surface.Raycast(new Ray(candidate, Vector3.down), out hit, bounds.size.y + 20f) ||
                hit.point.y < .15f || hit.normal.y < .84f)
                return false;
            Vector2Int cell = Cell(hit.point);
            for (int x = -1; x <= 1; x++)
                for (int z = -1; z <= 1; z++)
                    if (water.Contains(cell + new Vector2Int(x, z))) return false;
            foreach (var w in wrecks)
                if (hit.point.x > w.min.x - 3.5f && hit.point.x < w.max.x + 3.5f &&
                    hit.point.z > w.min.z - 3.5f && hit.point.z < w.max.z + 3.5f)
                    return false;
            return true;
        }

        static float Next(System.Random r) => (float)r.NextDouble();
        static Vector2Int Cell(Vector3 p) => new Vector2Int(Mathf.FloorToInt(p.x / 1.2f), Mathf.FloorToInt(p.z / 1.2f));

        static Material MaterialFor(string part)
        {
            if (Materials.TryGetValue(part, out var m) && m != null) return m;
            m = Resources.Load<Material>(Path + part + "_Material");
            if (m != null) { Materials[part] = m; return m; }
            if (m == null)
            {
                m = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = "Tripo Vegetation " + part, enableInstancing = true };
#if UNITY_EDITOR
                if (!Application.isPlaying) UnityEditor.AssetDatabase.CreateAsset(m, "Assets/LastLandfall/Resources/" + Path + part + "_Material.mat");
#endif
            }
            m.shader = Shader.Find("Universal Render Pipeline/Lit");
            m.SetTexture("_BaseMap", Resources.Load<Texture2D>(Path + part + "_BaseColor"));
            m.SetFloat("_Smoothness", .12f);
            m.SetFloat("_Cull", 0);
            Materials[part] = m;
            return m;
        }

#if UNITY_EDITOR
        [UnityEditor.InitializeOnLoadMethod]
        static void RefreshScenePreviewVegetation()
        {
            UnityEditor.EditorApplication.delayCall += () =>
            {
                if (Application.isPlaying) return;
                foreach (var tr in Object.FindObjectsByType<Transform>(FindObjectsInactive.Include))
                {
                    if (tr != null && tr.name == CollectionName && tr.Find(VersionTagName) == null && tr.parent != null)
                    {
                        Apply(tr.parent.gameObject);
                        break;
                    }
                }
            };
        }
#endif
    }
}
