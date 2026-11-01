using UnityEngine;

namespace LastLandfall
{
    public static class TripoIslandAssets
    {
        const string Root = "Models/Environment/Tripo/";

        // --- 水位与河床调节参数 (也可直接在 TripoDynamicFreshWater.mat 材质面板拖动滑条实时调节) ---
        public const float CreekWaterLevelOffset = 0.0f;  // 上中游溪流水位额外偏移（默认0已齐平岛屿顶部高原）
        public const float PondWaterLevelOffset = 0.0f;   // 南部池塘水位额外偏移（默认0已满至池塘顶部岸沿）
        public const float CreekWidthScale = 1.0f;        // 上中游溪流宽度倍率
        public const float CreekBedDepth = 0.0010f;       // 上中游溪流高河床浅槽深度
        public const float PondBedDepth = 0.0172f;        // 南部池塘保留原始深盆地深度（水位0.0748，池底约0.0576）

        // Catmull-Rom control nodes in island_terrain_3d_model local MeshFilter space:
        // (x, z, halfWidth, baseBankY) tracing the top plateau rim from the northern spring head to the brimming southern pond.
        static readonly Vector4[] StreamSplineNodes =
        {
            new Vector4(-0.196f, -0.102f, 0.0046f, 0.0806f), // 0: Mountain spring head at north plateau top
            new Vector4(-0.208f, -0.084f, 0.0054f, 0.0802f), // 1: Upper spring pool
            new Vector4(-0.207f, -0.062f, 0.0054f, 0.0798f), // 2: Upper rocky rapids
            new Vector4(-0.206f, -0.038f, 0.0052f, 0.0794f), // 3: Upper bend
            new Vector4(-0.208f, -0.014f, 0.0054f, 0.0789f), // 4: Mid-upper bend
            new Vector4(-0.195f,  0.010f, 0.0058f, 0.0783f), // 5: Mid S-curve
            new Vector4(-0.179f,  0.034f, 0.0062f, 0.0777f), // 6: Mid reach
            new Vector4(-0.164f,  0.056f, 0.0060f, 0.0770f), // 7: Lower rapids bend
            new Vector4(-0.138f,  0.075f, 0.0062f, 0.0762f), // 8: Lower reach approaching pond
            new Vector4(-0.098f,  0.092f, 0.0095f, 0.0754f), // 9: Pond inlet mouth
            new Vector4(-0.065f,  0.110f, 0.0450f, 0.0748f), // 10: North pond basin (full to plateau rim)
            new Vector4(-0.061f,  0.134f, 0.0470f, 0.0748f), // 11: Pond center north (brimming full)
            new Vector4(-0.061f,  0.158f, 0.0450f, 0.0748f), // 12: Pond center south (brimming full)
            new Vector4(-0.063f,  0.180f, 0.0360f, 0.0748f), // 13: Pond south basin
            new Vector4(-0.064f,  0.197f, 0.0200f, 0.0748f), // 14: Pond southern shore
        };

        struct SplineSample
        {
            public Vector2 posXZ;
            public Vector2 tangentXZ;
            public Vector2 rightXZ;
            public float halfWidth;
            public float baseBankY;
            public float waterY;
            public float bedDepth;
            public float waterSpanRatio;
            public float pondBlend;
            public float flowSpeed;
            public float rapids;
            public float arcLengthWorld;
            public float normalizedS;
        }

        static Material LoadOrCreateFreshWaterMaterial()
        {
            var shader = Resources.Load<Shader>("Shaders/TripoFreshWater");
            if (shader == null) return null;

            Material material = null;
#if UNITY_EDITOR
            const string assetPath = "Assets/LastLandfall/Resources/Models/Environment/Tripo/TripoDynamicFreshWater.mat";
            material = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>(assetPath);
#endif
            if (material == null)
            {
                material = Resources.Load<Material>(Root + "TripoDynamicFreshWater");
            }

            if (material == null)
            {
                material = new Material(shader) { name = "Tripo Dynamic Fresh Water" };
                material.SetTexture("_WaterRegion", Resources.Load<Texture2D>(
                    Root + "Island/island_terrain_3d_model.fbm/island_terrain_3d_model_basecolor"));
                material.SetColor("_Tint", new Color(0.06f, 0.32f, 0.36f, 1f));
                material.SetColor("_ShallowColor", new Color(0.22f, 0.56f, 0.54f, 1f));
                material.SetColor("_FoamColor", new Color(0.90f, 0.96f, 0.97f, 1f));
                material.SetFloat("_WaterOpacity", 0.35f);
                material.SetFloat("_FlowSpeed", 1.35f);
                material.SetFloat("_NormalStrength", 0.85f);
                material.SetFloat("_CreekLevelOffset", 0f);
                material.SetFloat("_PondLevelOffset", 0f);
                material.SetFloat("_CreekWidthScale", 1f);
#if UNITY_EDITOR
                if (!Application.isPlaying)
                {
                    UnityEditor.AssetDatabase.CreateAsset(material, assetPath);
                }
#endif
            }
            else if (material.shader != shader)
            {
                material.shader = shader;
            }

            return material;
        }

        static SplineSample[] GetSplineSamples(float worldScaleXZ = 240f, Material waterMaterial = null)
        {
            if (waterMaterial == null) waterMaterial = LoadOrCreateFreshWaterMaterial();

            float matCreekOffset = waterMaterial != null && waterMaterial.HasProperty("_CreekLevelOffset")
                ? waterMaterial.GetFloat("_CreekLevelOffset") : 0f;
            float matPondOffset = waterMaterial != null && waterMaterial.HasProperty("_PondLevelOffset")
                ? waterMaterial.GetFloat("_PondLevelOffset") : 0f;
            float matCreekWidth = waterMaterial != null && waterMaterial.HasProperty("_CreekWidthScale")
                ? Mathf.Max(0.25f, waterMaterial.GetFloat("_CreekWidthScale")) : 1f;

            // Convert slider units (-3..+3) into a pronounced local elevation & basin-fill shift.
            float creekOffsetLocal = CreekWaterLevelOffset + matCreekOffset * 0.0024f;
            float pondOffsetLocal = PondWaterLevelOffset + matPondOffset * 0.0024f;
            float effectiveCreekWidth = CreekWidthScale * matCreekWidth;

            const int sampleCount = 140;
            var samples = new SplineSample[sampleCount];
            int segCount = StreamSplineNodes.Length - 1;

            for (int i = 0; i < sampleCount; i++)
            {
                float s = i / (float)(sampleCount - 1);
                float scaled = s * segCount;
                int seg = Mathf.Min(segCount - 1, Mathf.FloorToInt(scaled));
                float t = scaled - seg;

                Vector4 p0 = StreamSplineNodes[Mathf.Max(0, seg - 1)];
                Vector4 p1 = StreamSplineNodes[seg];
                Vector4 p2 = StreamSplineNodes[Mathf.Min(segCount, seg + 1)];
                Vector4 p3 = StreamSplineNodes[Mathf.Min(segCount, seg + 2)];

                Vector4 val = CatmullRom(p0, p1, p2, p3, t);
                float pondBlend = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.62f, 0.74f, s));

                float endCapTaper = 1f;
                if (i < 5) endCapTaper = Mathf.Lerp(0.45f, 1f, i / 5f);
                else if (i > sampleCount - 6) endCapTaper = Mathf.Lerp(0.45f, 1f, (sampleCount - 1 - i) / 5f);

                float widthScale = Mathf.Lerp(effectiveCreekWidth, 1.0f, pondBlend);
                float halfWidth = Mathf.Max(0.0030f, val.z * widthScale * endCapTaper);
                float baseBankY = Mathf.Lerp(val.w, 0.0748f, pondBlend);
                float levelOffset = Mathf.Lerp(creekOffsetLocal, pondOffsetLocal, pondBlend);
                float waterY = baseBankY + levelOffset;
                float bedDepth = Mathf.Lerp(CreekBedDepth, PondBedDepth, pondBlend);

                // As water level rises above 0, water spreads wider across the banks;
                // as water level drops below 0, shoreline contracts inward into the carved basin.
                float normalizedOffset = levelOffset / 0.0036f;
                float waterSpanRatio = Mathf.Clamp(1.12f + normalizedOffset * 0.34f, 0.38f, 1.75f);

                float flowSpeed = Mathf.Lerp(0.95f, 0.18f, pondBlend);
                float upperRapids = Mathf.SmoothStep(1f, 0f, Mathf.InverseLerp(0.04f, 0.34f, s)) * 0.85f;
                float midCascade = Mathf.Sin(Mathf.Clamp01(Mathf.InverseLerp(0.42f, 0.64f, s)) * Mathf.PI) * 0.60f;
                float rapids = Mathf.Clamp01(Mathf.Max(upperRapids, midCascade) * (1f - pondBlend));

                samples[i] = new SplineSample
                {
                    posXZ = new Vector2(val.x, val.y),
                    halfWidth = halfWidth,
                    baseBankY = baseBankY,
                    waterY = waterY,
                    bedDepth = bedDepth,
                    waterSpanRatio = waterSpanRatio,
                    pondBlend = pondBlend,
                    flowSpeed = flowSpeed,
                    rapids = rapids,
                    normalizedS = s
                };
            }

            float arcWorld = 0f;
            for (int i = 0; i < sampleCount; i++)
            {
                if (i > 0)
                {
                    arcWorld += Vector2.Distance(samples[i - 1].posXZ, samples[i].posXZ) * worldScaleXZ;
                }
                samples[i].arcLengthWorld = arcWorld;

                Vector2 prev = samples[Mathf.Max(0, i - 1)].posXZ;
                Vector2 next = samples[Mathf.Min(sampleCount - 1, i + 1)].posXZ;
                Vector2 tangent = next - prev;
                if (tangent.sqrMagnitude < 1e-10f) tangent = new Vector2(0f, 1f);
                else tangent.Normalize();

                Vector2 naturalRight = new Vector2(tangent.y, -tangent.x);
                // Align pond cross-sections cleanly East-West so wide pond rows never twist or self-overlap.
                Vector2 right = Vector2.Lerp(naturalRight, new Vector2(1f, 0f), samples[i].pondBlend);
                if (right.sqrMagnitude < 1e-10f) right = new Vector2(1f, 0f);
                else right.Normalize();

                samples[i].rightXZ = right;
                samples[i].tangentXZ = new Vector2(-right.y, right.x);
            }

            return samples;
        }

        static Vector4 CatmullRom(Vector4 p0, Vector4 p1, Vector4 p2, Vector4 p3, float t)
        {
            float t2 = t * t;
            float t3 = t2 * t;
            return 0.5f * ((2f * p1) +
                           (-p0 + p2) * t +
                           (2f * p0 - 5f * p1 + 4f * p2 - p3) * t2 +
                           (-p0 + 3f * p1 - 3f * p2 + p3) * t3);
        }

        static void QueryClosestSplineSample(Vector2 ptXZ, SplineSample[] samples,
            out float normalizedR, out float halfWidth, out float baseBankY, out float waterY, out float bedDepth, out float waterSpanRatio, out float pondBlend)
        {
            float bestR = float.PositiveInfinity;
            int bestIdx = 0;

            for (int i = 0; i < samples.Length; i++)
            {
                SplineSample s = samples[i];
                Vector2 delta = ptXZ - s.posXZ;
                float carveW = Mathf.Max(0.001f, s.halfWidth * s.waterSpanRatio);
                float lat = Mathf.Abs(Vector2.Dot(delta, s.rightXZ)) / carveW;
                float lon = Mathf.Abs(Vector2.Dot(delta, s.tangentXZ)) / 0.0055f;
                float r = Mathf.Sqrt(lat * lat + lon * lon);
                if (r < bestR)
                {
                    bestR = r;
                    bestIdx = i;
                }
            }

            SplineSample best = samples[bestIdx];
            normalizedR = bestR;
            halfWidth = best.halfWidth;
            baseBankY = best.baseBankY;
            waterY = best.waterY;
            bedDepth = best.bedDepth;
            waterSpanRatio = best.waterSpanRatio;
            pondBlend = best.pondBlend;
        }

        static bool IsNearFreshWaterCorridor(Transform terrainTransform, Vector3 worldPoint, SplineSample[] samples)
        {
            if (terrainTransform == null) return false;
            Vector3 local = terrainTransform.InverseTransformPoint(worldPoint);
            if (local.x < -0.26f || local.x > 0.01f || local.z < -0.12f || local.z > 0.24f)
                return false;
            QueryClosestSplineSample(new Vector2(local.x, local.z), samples,
                out float normalizedR, out _, out _, out _, out _, out _, out _);
            return normalizedR < 1.55f;
        }

        public static GameObject AddShipwreck(Transform satellites)
        {
            var source = Resources.Load<GameObject>(Root + "Shipwreck/Shipwreck");
            if (source == null || satellites == null) return null;
            Transform east = satellites.Find("Expanded East Island");
            if (east == null) return null;
            Bounds land = default;
            bool found = false;
            foreach (var renderer in east.GetComponentsInChildren<Renderer>())
            {
                if (!renderer.enabled || !renderer.name.Contains("terrain source")) continue;
                if (!found) land = renderer.bounds;
                else land.Encapsulate(renderer.bounds);
                found = true;
            }
            if (!found) return null;
            var ship = Object.Instantiate(source, east, false);
            ship.name = "Wreck_Tripo_CargoShip";

            // Measure unrotated local hull dimensions first so yaw/pitch/roll are aligned to the hull keel axis.
            Bounds rawHull = GetBounds(ship);
            bool longX = rawHull.size.x >= rawHull.size.z;
            float rawLength = Mathf.Max(rawHull.size.x, rawHull.size.z);
            float targetLength = Mathf.Max(land.size.x, land.size.z) * 0.44f;
            ship.transform.localScale *= targetLength / Mathf.Max(0.001f, rawLength);
            rawHull = GetBounds(ship);

            float hullHalfLength = Mathf.Max(rawHull.extents.x, rawHull.extents.z);
            float hullHalfWidth = Mathf.Min(rawHull.extents.x, rawHull.extents.z);
            float hullHeight = rawHull.size.y;

            var terrain = east.GetComponentsInChildren<MeshCollider>();
            Vector3 bestCenter = land.center;
            float bestYaw = 20f;
            float bestPitchDeg = 0f;
            float bestRollDeg = 0f;
            float bestSupportY = land.center.y;
            float bestScore = float.PositiveInfinity;

            // Search candidate positions and yaw directions across the central saddle pass between the twin peaks.
            float[] candidateYaws = { 14f, 18f, 22f, 26f, 32f, -18f, 0f, 45f };
            for (int yi = 0; yi < candidateYaws.Length; yi++)
            {
                float testYaw = candidateYaws[yi] - (longX ? 90f : 0f);
                float rad = candidateYaws[yi] * Mathf.Deg2Rad;
                Vector3 fwd = new Vector3(Mathf.Sin(rad), 0f, Mathf.Cos(rad));
                Vector3 right = new Vector3(Mathf.Cos(rad), 0f, -Mathf.Sin(rad));

                for (int ix = -3; ix <= 2; ix++)
                for (int iz = -2; iz <= 3; iz++)
                {
                    Vector3 center = land.center + new Vector3(
                        (ix * 0.032f - 0.02f) * land.size.x,
                        0f,
                        (iz * 0.032f) * land.size.z);

                    // Sample a 7x3 grid across the keel and bilge footprint
                    int validCount = 0;
                    float sumY = 0f, sumV = 0f, sumVY = 0f, sumVV = 0f;
                    float sumU = 0f, sumUY = 0f, sumUU = 0f;
                    float minSampleY = float.PositiveInfinity;
                    float maxSampleY = float.NegativeInfinity;

                    float[] vSteps = { -0.78f, -0.52f, -0.26f, 0f, 0.26f, 0.52f, 0.78f };
                    float[] uSteps = { -0.68f, 0f, 0.68f };
                    float[,] gridY = new float[vSteps.Length, uSteps.Length];

                    for (int iv = 0; iv < vSteps.Length; iv++)
                    {
                        float vDist = vSteps[iv] * hullHalfLength;
                        for (int iu = 0; iu < uSteps.Length; iu++)
                        {
                            float uDist = uSteps[iu] * hullHalfWidth;
                            Vector3 sampleXZ = center + fwd * vDist + right * uDist;
                            var ray = new Ray(new Vector3(sampleXZ.x, land.max.y + 10f, sampleXZ.z), Vector3.down);
                            bool hitLand = false;
                            float y = float.NegativeInfinity;
                            foreach (var collider in terrain)
                            {
                                if (collider.enabled && collider.Raycast(ray, out var hit, land.size.y + 30f))
                                {
                                    y = Mathf.Max(y, hit.point.y);
                                    hitLand = true;
                                }
                            }
                            if (!hitLand) continue;

                            gridY[iv, iu] = y;
                            validCount++;
                            sumY += y;
                            sumV += vDist; sumVY += vDist * y; sumVV += vDist * vDist;
                            sumU += uDist; sumUY += uDist * y; sumUU += uDist * uDist;
                            minSampleY = Mathf.Min(minSampleY, y);
                            maxSampleY = Mathf.Max(maxSampleY, y);
                        }
                    }

                    if (validCount < vSteps.Length * uSteps.Length) continue;

                    // Verify that higher peaks flank the left and right sides (confirming a true mountain saddle pass)
                    float flankLeftY = minSampleY, flankRightY = minSampleY;
                    Vector3 leftProbe = center - right * (hullHalfWidth * 2.6f);
                    Vector3 rightProbe = center + right * (hullHalfWidth * 2.6f);
                    foreach (var collider in terrain)
                    {
                        if (!collider.enabled) continue;
                        if (collider.Raycast(new Ray(new Vector3(leftProbe.x, land.max.y + 10f, leftProbe.z), Vector3.down), out var hitL, land.size.y + 30f))
                            flankLeftY = Mathf.Max(flankLeftY, hitL.point.y);
                        if (collider.Raycast(new Ray(new Vector3(rightProbe.x, land.max.y + 10f, rightProbe.z), Vector3.down), out var hitR, land.size.y + 30f))
                            flankRightY = Mathf.Max(flankRightY, hitR.point.y);
                    }

                    float meanY = sumY / validCount;
                    float pitchSlope = sumVV > 1e-4f ? sumVY / sumVV : 0f;
                    float rollSlope = sumUU > 1e-4f ? sumUY / sumUU : 0f;

                    // Compute max upward terrain protrusion relative to the inclined keel plane
                    float maxProtrusion = 0f;
                    float sumSqResidual = 0f;
                    for (int iv = 0; iv < vSteps.Length; iv++)
                    {
                        float vDist = vSteps[iv] * hullHalfLength;
                        for (int iu = 0; iu < uSteps.Length; iu++)
                        {
                            float uDist = uSteps[iu] * hullHalfWidth;
                            float planeY = meanY + pitchSlope * vDist + rollSlope * uDist;
                            float diff = gridY[iv, iu] - planeY;
                            // Midship deck is lower than bow/stern, so weight midship bumps extra heavily
                            float midWeight = Mathf.Abs(vSteps[iv]) <= 0.3f ? 1.35f : 1.0f;
                            maxProtrusion = Mathf.Max(maxProtrusion, diff * midWeight);
                            sumSqResidual += diff * diff;
                        }
                    }

                    float rmsResidual = Mathf.Sqrt(sumSqResidual / validCount);
                    float saddleFlankBonus = Mathf.Min(flankLeftY - meanY, flankRightY - meanY);
                    // Prefer smooth saddle pass with rising peaks on both flanks and minimal hull slope
                    float score = maxProtrusion * 2.5f + rmsResidual * 1.8f +
                                  (Mathf.Abs(pitchSlope) + Mathf.Abs(rollSlope)) * hullHalfLength * 0.35f -
                                  Mathf.Max(0f, saddleFlankBonus) * 0.30f;

                    if (score < bestScore)
                    {
                        bestScore = score;
                        bestCenter = new Vector3(center.x, meanY, center.z);
                        bestYaw = testYaw;
                        bestPitchDeg = Mathf.Clamp(-Mathf.Atan(pitchSlope) * Mathf.Rad2Deg, -10f, 10f);
                        bestRollDeg = Mathf.Clamp(Mathf.Atan(rollSlope) * Mathf.Rad2Deg + 4.5f, -12f, 12f);
                        // Rest the keel on the upper terrain envelope minus a subtle 2% keel settle so zero rock pokes through the deck
                        bestSupportY = meanY + maxProtrusion - hullHeight * 0.02f;
                    }
                }
            }

            if (float.IsPositiveInfinity(bestScore))
            {
                Object.Destroy(ship);
                Debug.LogWarning("No supported central shipwreck site found on the east island.");
                return null;
            }

            Quaternion pitchRoll = Quaternion.Euler(bestPitchDeg, 0f, bestRollDeg);
            ship.transform.rotation = Quaternion.Euler(0f, bestYaw, 0f) * pitchRoll;
            Bounds hull = GetBounds(ship);
            ship.transform.position += new Vector3(
                bestCenter.x - hull.center.x,
                bestSupportY - hull.min.y,
                bestCenter.z - hull.center.z);
            var material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            material.name = "Tripo Rusted Cargo Ship";
            material.SetTexture("_BaseMap", Resources.Load<Texture2D>(Root + "Shipwreck/Shipwreck_BaseColor"));
            material.SetFloat("_Smoothness", .18f);
            foreach (var mesh in ship.GetComponentsInChildren<MeshFilter>())
            {
                mesh.name = "Wreck_Tripo_Hull";
                SetMaterial(mesh.GetComponent<Renderer>(), material);
                mesh.gameObject.AddComponent<MeshCollider>().sharedMesh = mesh.sharedMesh;
            }
            Debug.Log("Tripo cargo shipwreck placed in east island saddle at " + bestCenter + ", yaw " + bestYaw);
            return ship;
        }

        public static void ApplyRockySatellite(GameObject island, bool lowShore = false)
        {
            var source = Resources.Load<GameObject>(Root + (lowShore ? "LowShore/LowShore" : "Rocky/Rocky"));
            if (source == null) return;
            Bounds target = GetBounds(island);
            foreach (var mesh in island.GetComponentsInChildren<MeshFilter>())
            {
                if (mesh.TryGetComponent<Renderer>(out var renderer)) renderer.enabled = false;
                foreach (var collider in mesh.GetComponents<Collider>()) collider.enabled = false;
                mesh.sharedMesh = null;
            }
            var model = Object.Instantiate(source, island.transform, false);
            Bounds bounds = GetBounds(model);
            model.transform.localScale *= Mathf.Min(target.size.x / bounds.size.x, target.size.z / bounds.size.z);
            bounds = GetBounds(model);
            model.transform.position += new Vector3(target.center.x - bounds.center.x,
                target.min.y - bounds.min.y, target.center.z - bounds.center.z);
            var material = MakeMaterial(null, false);
            foreach (var mesh in model.GetComponentsInChildren<MeshFilter>())
            {
                mesh.name = "Tripo_terrain source";
                SetMaterial(mesh.GetComponent<Renderer>(), material);
                mesh.gameObject.AddComponent<MeshCollider>().sharedMesh = mesh.sharedMesh;
            }
        }

        // Keep the terrain, water and individual trees; hide placed scenery.
        public static void ClearDecorations(GameObject root)
        {
            foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
            {
                string name = renderer.name.ToLowerInvariant();
                bool keep = name.Contains("terrain source") || name.Contains("water") || name.StartsWith("wreck_") ||
                    name.Contains("conifer") || name.Contains("pine") || name.Contains("broadleaf") ||
                    name.Contains("tree") || name.Contains("palm") || name.Contains("grass");
                if (keep) continue;
                renderer.enabled = false;
                foreach (var collider in renderer.GetComponents<Collider>()) collider.enabled = false;
            }
        }

        public static void Apply(GameObject island)
        {
            var source = Resources.Load<GameObject>(Root + "Island/island_terrain_3d_model");
            if (source == null) return;
            Bounds target = default;
            bool found = false;
            foreach (var mesh in island.GetComponentsInChildren<MeshFilter>())
            {
                if (mesh.name.ToLowerInvariant().Contains("terrain source") && mesh.TryGetComponent<Renderer>(out var renderer))
                {
                    if (!found) target = renderer.bounds;
                    else target.Encapsulate(renderer.bounds);
                    found = true;
                }
            }
            if (!found) return;
            foreach (var mesh in island.GetComponentsInChildren<MeshFilter>())
            {
                if (mesh.TryGetComponent<Renderer>(out var renderer)) renderer.enabled = false;
                mesh.sharedMesh = null;
                mesh.name = "Retired original main island mesh";
            }
            var model = Object.Instantiate(source, island.transform, false);
            model.name = "Tripo_MainIsland";
            Bounds bounds = GetBounds(model);
            float scale = Mathf.Min(target.size.x / bounds.size.x, target.size.z / bounds.size.z);
            model.transform.localScale *= scale;
            bounds = GetBounds(model);
            model.transform.position += new Vector3(target.center.x - bounds.center.x,
                target.min.y - bounds.min.y, target.center.z - bounds.center.z);
            // Lower the main terrain before building its river, colliders and vegetation.
            // The ocean and separately created satellites retain their original elevation.
            model.transform.position -= Vector3.up * MainIslandShoreSettings.SinkDepth;
            var landMaterial = MakeMaterial(null);
            var waterMaterial = LoadOrCreateFreshWaterMaterial();
            Transform primaryTerrainTransform = null;
            var splineSamples = GetSplineSamples(scale, waterMaterial);
            foreach (var mesh in model.GetComponentsInChildren<MeshFilter>())
            {
                mesh.name = "Tripo_terrain source";
                primaryTerrainTransform = mesh.transform;
                CarveTerrainRiverbed(mesh, splineSamples);
                SetMaterial(mesh.GetComponent<Renderer>(), landMaterial);
                var collider = mesh.gameObject.AddComponent<MeshCollider>();
                collider.sharedMesh = mesh.sharedMesh;
            }
            AddFreshWater(model, splineSamples, waterMaterial);
            var pine = Resources.Load<GameObject>(Root + "Pine/pine_tree_3d_model");
            if (pine == null) return;
            var treeMaterial = MakeMaterial(Root + "Pine/pine_tree_3d_model.fbm/pine_tree_3d_model_basecolor");
            var random = new System.Random(1028);
            var surfaces = model.GetComponentsInChildren<MeshCollider>();
            bounds = GetBounds(model);
            int placedTrees = 0;
            for (int attempt = 0; attempt < 320 && placedTrees < 150; attempt++)
            {
                Vector3 origin = new Vector3(Mathf.Lerp(bounds.min.x, bounds.max.x, (float)random.NextDouble()), bounds.max.y + 10f,
                    Mathf.Lerp(bounds.min.z, bounds.max.z, (float)random.NextDouble()));
                foreach (var surface in surfaces)
                {
                    if (!surface.Raycast(new Ray(origin, Vector3.down), out var hit, bounds.size.y + 20f)) continue;
                    if (hit.point.y < target.min.y + target.size.y * .3f || hit.normal.y < .8f) break;
                    if (IsNearFreshWaterCorridor(primaryTerrainTransform, hit.point, splineSamples)) break;
                    var tree = Object.Instantiate(pine, model.transform, false);
                    tree.name = "Tripo_Conifer_" + placedTrees;
                    var treeBounds = GetBounds(tree);
                    float height = target.size.x * Mathf.Lerp(.025f, .045f, (float)random.NextDouble());
                    tree.transform.localScale *= height / Mathf.Max(.001f, treeBounds.size.y);
                    tree.transform.Rotate(Vector3.up, (float)random.NextDouble() * 360f);
                    treeBounds = GetBounds(tree);
                    tree.transform.position += hit.point - new Vector3(treeBounds.center.x, treeBounds.min.y, treeBounds.center.z);
                    foreach (var renderer in tree.GetComponentsInChildren<Renderer>())
                    {
                        renderer.name = "Tripo_Conifer";
                        SetMaterial(renderer, treeMaterial);
                    }
                    placedTrees++;
                    break;
                }
            }
        }

        static Mesh GetOriginalUncarvedTerrainMesh()
        {
            var source = Resources.Load<GameObject>(Root + "Island/island_terrain_3d_model");
            if (source == null) return null;
            var filter = source.GetComponentInChildren<MeshFilter>();
            return filter != null ? filter.sharedMesh : null;
        }

        static void CarveTerrainRiverbed(MeshFilter terrainFilter, SplineSample[] samples)
        {
            if (terrainFilter == null) return;
            Mesh baseMesh = GetOriginalUncarvedTerrainMesh() ?? terrainFilter.sharedMesh;
            if (baseMesh == null) return;

            var mesh = Object.Instantiate(baseMesh);
            mesh.name = "Tripo_MainIsland_CarvedTerrain";
            var vertices = mesh.vertices;
            var colors = mesh.colors;
            if (colors == null || colors.Length != vertices.Length)
            {
                colors = new Color[vertices.Length];
                for (int i = 0; i < colors.Length; i++) colors[i] = Color.white;
            }
            else
            {
                for (int i = 0; i < colors.Length; i++) colors[i].a = 1f;
            }

            for (int i = 0; i < vertices.Length; i++)
            {
                Vector3 v = vertices[i];
                // Restrict to the interior creek canyon and pond basin on top of the island plateau.
                float minBasinX = v.z > 0.108f ? -0.132f : -0.247f;
                if (v.y < 0.048f || v.z < -0.114f || v.z > 0.235f || v.x > -0.006f || v.x < minBasinX)
                    continue;

                QueryClosestSplineSample(new Vector2(v.x, v.z), samples,
                    out float r, out _, out float baseBankY, out float waterY, out float bedDepth, out _, out float pondBlend);

                // Bake wet riverbed & narrow riparian bank mask into vertex alpha (0 = wet bed, 1 = dry land).
                if (r < 1.60f)
                {
                    float wetness = r <= 1.04f
                        ? 1.0f
                        : Mathf.SmoothStep(1f, 0f, (r - 1.04f) / 0.56f);
                    colors[i] = new Color(colors[i].r, colors[i].g, colors[i].b, Mathf.Clamp01(1f - wetness));
                }

                float bankRimY = Mathf.Max(baseBankY + 0.00018f, waterY + 0.00015f);
                float lowestBedY = Mathf.Min(baseBankY - bedDepth, waterY - Mathf.Max(bedDepth, 0.0009f));
                float submergedEdgeY = Mathf.Min(baseBankY - bedDepth * 0.28f, waterY - 0.00035f);

                if (r <= 1.02f)
                {
                    float normR = Mathf.Clamp01(r / 1.02f);
                    float troughProfile = Mathf.Cos(normR * Mathf.PI * 0.5f);
                    float targetBedY = Mathf.Lerp(submergedEdgeY, lowestBedY, troughProfile);
                    // In the pond, keep the natural deep floor; in the creek, raise the riverbed high to targetBedY.
                    v.y = (pondBlend > 0.5f && r < 0.85f) ? Mathf.Min(v.y, targetBedY) : targetBedY;
                    vertices[i] = v;
                }
                else if (r < 1.18f)
                {
                    float edgeRamp = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(1.02f, 1.18f, r));
                    v.y = Mathf.Lerp(submergedEdgeY, bankRimY, edgeRamp);
                    vertices[i] = v;
                }
                else
                {
                    // Fill the wide pre-carved FBX canyon outside the narrow creek up to the island plateau height.
                    if (v.y < bankRimY)
                    {
                        v.y = bankRimY;
                        vertices[i] = v;
                    }
                }
            }

            mesh.vertices = vertices;
            mesh.colors = colors;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
#if UNITY_EDITOR
            if (!Application.isPlaying)
            {
                const string carvedPath = "Assets/LastLandfall/Resources/Models/Environment/Tripo/TripoCarvedTerrain.asset";
                var saved = UnityEditor.AssetDatabase.LoadAssetAtPath<Mesh>(carvedPath);
                if (saved == null)
                {
                    UnityEditor.AssetDatabase.CreateAsset(mesh, carvedPath);
                }
                else
                {
                    UnityEditor.EditorUtility.CopySerialized(mesh, saved);
                    UnityEditor.EditorUtility.SetDirty(saved);
                    Object.DestroyImmediate(mesh);
                    mesh = saved;
                }
            }
#endif
            terrainFilter.sharedMesh = mesh;
            if (terrainFilter.TryGetComponent<MeshCollider>(out var collider))
            {
                collider.sharedMesh = mesh;
            }
        }

        static Bounds GetBounds(GameObject model)
        {
            var renderers = model.GetComponentsInChildren<Renderer>();
            Bounds bounds = renderers[0].bounds;
            foreach (var renderer in renderers) bounds.Encapsulate(renderer.bounds);
            return bounds;
        }

        static void AddFreshWater(GameObject model, SplineSample[] samples, Material material)
        {
            if (material == null) material = LoadOrCreateFreshWaterMaterial();
            if (material == null) return;

            foreach (var terrain in model.GetComponentsInChildren<MeshFilter>())
            {
                var water = new GameObject("Basin_Stream_Water_MountainSpring");
                water.transform.SetParent(terrain.transform, false);
                var waterFilter = water.AddComponent<MeshFilter>();
                waterFilter.sharedMesh = BuildWaterSurface(samples);
                var renderer = water.AddComponent<MeshRenderer>();
                renderer.sharedMaterial = material;
                renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }
        }

        static Mesh BuildWaterSurface(SplineSample[] samples)
        {
            var mesh = new Mesh
            {
                name = "Tripo Spline Freshwater Ribbon"
            };

            int rowCount = samples.Length;
            const int colCount = 25;
            var vertices = new Vector3[rowCount * colCount];
            var normals = new Vector3[vertices.Length];
            var uvs = new Vector2[vertices.Length];
            var colors = new Color[vertices.Length];
            var triangles = new int[(rowCount - 1) * (colCount - 1) * 6];

            for (int r = 0; r < rowCount; r++)
            {
                SplineSample sample = samples[r];
                float endFade = Mathf.SmoothStep(0f, 1f,
                    Mathf.Min(r / 5f, (rowCount - 1 - r) / 5f));

                for (int c = 0; c < colCount; c++)
                {
                    int idx = r * colCount + c;
                    float u = c / (float)(colCount - 1);
                    float lateral = (u * 2f - 1f) * sample.halfWidth * sample.waterSpanRatio;
                    Vector2 posXZ = sample.posXZ + sample.rightXZ * lateral;

                    vertices[idx] = new Vector3(posXZ.x, sample.waterY, posXZ.y);
                    normals[idx] = Vector3.up;
                    uvs[idx] = new Vector2(u, sample.arcLengthWorld);

                    float bankProfile = Mathf.Sin(u * Mathf.PI);
                    float actualWaterColumn = Mathf.Max(0.0005f, sample.waterY - (sample.baseBankY - sample.bedDepth));
                    float depthScale = Mathf.Lerp(0.45f, 1.0f, Mathf.InverseLerp(0.0008f, 0.0055f, actualWaterColumn));
                    float normalizedDepth = Mathf.Clamp01(bankProfile * depthScale * endFade);
                    float shoreAlpha = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0f, 0.08f, bankProfile)) * endFade;
                    colors[idx] = new Color(normalizedDepth, sample.flowSpeed, sample.rapids, shoreAlpha);
                }
            }

            int triIdx = 0;
            for (int r = 0; r < rowCount - 1; r++)
            {
                for (int c = 0; c < colCount - 1; c++)
                {
                    int i00 = r * colCount + c;
                    int i10 = (r + 1) * colCount + c;
                    int i01 = i00 + 1;
                    int i11 = i10 + 1;

                    // Upward-facing (+Y) winding order for standard rendering and downward raycast queries.
                    triangles[triIdx++] = i00;
                    triangles[triIdx++] = i10;
                    triangles[triIdx++] = i01;

                    triangles[triIdx++] = i01;
                    triangles[triIdx++] = i10;
                    triangles[triIdx++] = i11;
                }
            }

            mesh.vertices = vertices;
            mesh.normals = normals;
            mesh.uv = uvs;
            mesh.colors = colors;
            mesh.triangles = triangles;
            mesh.RecalculateBounds();
#if UNITY_EDITOR
            if (!Application.isPlaying)
            {
                string path = "Assets/LastLandfall/Resources/Models/Environment/Tripo/TripoFreshwaterSurface.asset";
                var saved = UnityEditor.AssetDatabase.LoadAssetAtPath<Mesh>(path);
                if (saved == null) UnityEditor.AssetDatabase.CreateAsset(mesh, path);
                else
                {
                    UnityEditor.EditorUtility.CopySerialized(mesh, saved);
                    UnityEditor.EditorUtility.SetDirty(saved);
                    Object.DestroyImmediate(mesh);
                    mesh = saved;
                }
            }
#endif
            return mesh;
        }

        public static void RebuildAllSceneWaterSurfaces()
        {
            var material = LoadOrCreateFreshWaterMaterial();
            var filters = Object.FindObjectsByType<MeshFilter>(FindObjectsInactive.Include, FindObjectsSortMode.None);
            foreach (var waterFilter in filters)
            {
                if (waterFilter == null ||
                    (waterFilter.name != "Basin_Stream_Water_MountainSpring" &&
                     waterFilter.name != "Tripo_Water_StreamAndBasin"))
                    continue;
                waterFilter.name = "Basin_Stream_Water_MountainSpring";
                Transform terrainTransform = waterFilter.transform.parent;
                if (terrainTransform == null) continue;
                var terrainFilter = terrainTransform.GetComponent<MeshFilter>();
                if (terrainFilter == null) continue;

                float scale = terrainTransform.lossyScale.x > 1f ? terrainTransform.lossyScale.x : 240f;
                var samples = GetSplineSamples(scale, material);
                CarveTerrainRiverbed(terrainFilter, samples);
                waterFilter.sharedMesh = BuildWaterSurface(samples);
                if (waterFilter.TryGetComponent<MeshRenderer>(out var renderer) && material != null)
                {
                    renderer.sharedMaterial = material;
                }
            }
        }

#if UNITY_EDITOR
        static float lastWatchedCreekOffset = float.NaN;
        static float lastWatchedPondOffset = float.NaN;
        static float lastWatchedCreekWidth = float.NaN;

        [UnityEditor.InitializeOnLoadMethod]
        static void RegisterLiveWaterMaterialWatcher()
        {
            UnityEditor.EditorApplication.update -= PollWaterMaterialChanges;
            UnityEditor.EditorApplication.update += PollWaterMaterialChanges;
        }

        static void PollWaterMaterialChanges()
        {
            var mat = LoadOrCreateFreshWaterMaterial();
            if (mat == null) return;

            float creekOff = mat.HasProperty("_CreekLevelOffset") ? mat.GetFloat("_CreekLevelOffset") : 0f;
            float pondOff = mat.HasProperty("_PondLevelOffset") ? mat.GetFloat("_PondLevelOffset") : 0f;
            float creekWidth = mat.HasProperty("_CreekWidthScale") ? mat.GetFloat("_CreekWidthScale") : 1f;

            if (float.IsNaN(lastWatchedCreekOffset) ||
                Mathf.Abs(creekOff - lastWatchedCreekOffset) > 1e-4f ||
                Mathf.Abs(pondOff - lastWatchedPondOffset) > 1e-4f ||
                Mathf.Abs(creekWidth - lastWatchedCreekWidth) > 1e-4f)
            {
                lastWatchedCreekOffset = creekOff;
                lastWatchedPondOffset = pondOff;
                lastWatchedCreekWidth = creekWidth;
                RebuildAllSceneWaterSurfaces();
                UnityEditor.SceneView.RepaintAll();
            }
        }
#endif

        static Material MakeMaterial(string path, bool riverMask = true)
        {
            bool terrain = path == null;
            var material = terrain
                ? new Material(Resources.Load<Material>("Materials/Gate25Terrain"))
                : new Material(Shader.Find("Universal Render Pipeline/Lit"));
            material.name = terrain ? (riverMask ? "Tripo Clean Terrain" : "Tripo Satellite Terrain") : "Tripo Pine";
            if (terrain)
            {
                Prototype.TerrainSurfaceLibrary.Configure(material);
                material.SetColor("_GrassTint", new Color(.36f, .52f, .30f));
                material.SetColor("_SoilTint", new Color(.40f, .34f, .25f));
                material.SetColor("_RockTint", new Color(.48f, .49f, .47f));
                var meadow = Resources.Load<Texture2D>("Textures/Terrain/MeadowGround_Albedo_v2");
                if (meadow != null) material.SetTexture("_GroundDetail", meadow);
                material.SetTexture("_BaseMap", null);
                material.SetTextureScale("_BaseMap", Vector2.one);
                material.SetTextureOffset("_BaseMap", Vector2.zero);
                material.SetFloat("_TextureWeight", 0f);
                material.SetFloat("_VertexColorWeight", 0f);
                material.SetFloat("_LandscapeBlend", 1f);
                material.SetFloat("_SeaLevel", -.92f);
                material.SetFloat("_GroundTiling", .18f);
                material.SetFloat("_RockTiling", .45f);
                material.SetFloat("_SurfaceDetail", .75f);
                material.SetFloat("_NormalStrength", .5f);
                material.SetTexture("_RiverMaskSource", Resources.Load<Texture2D>(
                    Root + "Island/island_terrain_3d_model.fbm/island_terrain_3d_model_basecolor"));
                material.SetFloat("_RiverMaskStrength", riverMask ? 1f : 0f);
            }
            else material.SetTexture("_BaseMap", Resources.Load<Texture2D>(path));
            material.SetFloat("_Smoothness", .15f);
#if UNITY_EDITOR
            if (!Application.isPlaying)
            {
                string assetPath = "Assets/LastLandfall/Resources/Models/Environment/Tripo/" + material.name + ".mat";
                var saved = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>(assetPath);
                if (saved == null) UnityEditor.AssetDatabase.CreateAsset(material, assetPath);
                else
                {
                    UnityEditor.EditorUtility.CopySerialized(material, saved);
                    UnityEditor.EditorUtility.SetDirty(saved);
                    Object.DestroyImmediate(material);
                    return saved;
                }
            }
#endif
            return material;
        }

        static void SetMaterial(Renderer renderer, Material material)
        {
            var materials = renderer.sharedMaterials;
            if (materials.Length == 0) materials = new Material[1];
            for (int i = 0; i < materials.Length; i++) materials[i] = material;
            renderer.sharedMaterials = materials;
        }
    }
}
