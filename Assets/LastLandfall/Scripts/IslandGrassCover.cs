using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace LastLandfall.Prototype
{
    public sealed class IslandGrassCover : MonoBehaviour
    {
        const int ChunkSize = 8;
        readonly Dictionary<Vector2Int, Chunk> chunks = new Dictionary<Vector2Int, Chunk>();
        IslandConstructionGrid grid;
        HashSet<Vector2Int> occupied, roads;
        Material material;
        Mesh mesh;
        readonly List<Bounds> surfaceBounds = new List<Bounds>();
        readonly List<MeshCollider> freshWater = new List<MeshCollider>();
        bool grassVisible = true;
        static readonly int VisibilityId = Shader.PropertyToID("_GrassVisibility");
        Bounds wreckBounds;
        bool hasWreckBounds;
        struct Tuft { public Matrix4x4 matrix; public Vector4 color; }
        sealed class Chunk
        {
            public readonly Dictionary<Vector2Int, List<Tuft>> cells = new Dictionary<Vector2Int, List<Tuft>>();
            public Matrix4x4[] local;
            public Bounds bounds;
            public GameObject gameObject;
            public Mesh mesh;
            public MeshRenderer renderer;
        }

        public void Initialize(IslandConstructionGrid terrainGrid, HashSet<Vector2Int> occupiedCells, HashSet<Vector2Int> roadCells)
        {
            StopAllCoroutines();
            foreach (Chunk chunk in chunks.Values)
            {
                if (chunk.gameObject != null) Destroy(chunk.gameObject);
                if (chunk.mesh != null) Destroy(chunk.mesh);
            }
            chunks.Clear();
            surfaceBounds.Clear();
            freshWater.Clear();

            grid = terrainGrid;
            occupied = occupiedCells;
            roads = roadCells;

            Shader shader = Resources.Load<Shader>("Shaders/GrassBlades");
            if (shader == null) { Debug.LogWarning("Grass cover requires the grass shader."); return; }
            if (material == null) material = new Material(shader) { name = "Island grass blades" };
            material.SetFloat(VisibilityId, 1f);

            if (mesh == null) mesh = CreateTuft();
            foreach (MeshCollider surface in grid.Surfaces)
                if (surface != null) surfaceBounds.Add(surface.bounds);

            HideLegacyTufts();
            CacheFreshWaterSurfaces();
            CacheWreckFootprint();
            StartCoroutine(Generate());
        }

        void CacheWreckFootprint()
        {
            foreach (Renderer renderer in grid.Root.GetComponentsInChildren<Renderer>(true))
            {
                if (!renderer.enabled) continue;
                string name = renderer.gameObject.name;
                if (!name.StartsWith("Wreck_", System.StringComparison.OrdinalIgnoreCase) &&
                    !name.StartsWith("Debris_", System.StringComparison.OrdinalIgnoreCase)) continue;
                Bounds bounds = renderer.bounds;
                if (!hasWreckBounds) { wreckBounds = bounds; hasWreckBounds = true; }
                else wreckBounds.Encapsulate(bounds);
            }
            if (hasWreckBounds) wreckBounds.Expand(new Vector3(1.7f, 0f, 1.7f));
        }

        void CacheFreshWaterSurfaces()
        {
            foreach (MeshFilter source in grid.Root.GetComponentsInChildren<MeshFilter>(true))
            {
                if (source.sharedMesh == null || !source.gameObject.activeInHierarchy) continue;
                string name = source.name.ToLowerInvariant();
                if (!name.Contains("basin_") || !name.Contains("water")) continue;
                var probe = new GameObject("Grass water exclusion | " + source.name);
                probe.layer = 2; // Ignore ordinary raycasts; we query this collider explicitly.
                probe.transform.SetParent(source.transform, false);
                var collider = probe.AddComponent<MeshCollider>();
                collider.sharedMesh = source.sharedMesh;
                freshWater.Add(collider);
            }
            Physics.SyncTransforms();
        }

        bool IsUnderFreshWater(Vector3 localGround)
        {
            Vector3 worldGround = grid.Root.TransformPoint(localGround);
            Vector3 origin = grid.Root.TransformPoint(new Vector3(localGround.x, grid.LocalBounds.max.y + 8f, localGround.z));
            Ray ray = new Ray(origin, -grid.Root.up);
            foreach (MeshCollider surface in freshWater)
            {
                if (surface == null) continue;
                Bounds bounds = surface.bounds;
                if (worldGround.x < bounds.min.x || worldGround.x > bounds.max.x ||
                    worldGround.z < bounds.min.z || worldGround.z > bounds.max.z) continue;
                if (surface.Raycast(ray, out RaycastHit hit, grid.LocalBounds.size.y + 24f) &&
                    grid.Root.InverseTransformPoint(hit.point).y >= localGround.y - .02f) return true;
            }
            return false;
        }

        public bool IsFreshWater(Vector3 localGround) => grid != null && IsUnderFreshWater(localGround);

        bool IsWithinSurfaceBounds(float x, float z)
        {
            Vector3 world = grid.Root.TransformPoint(new Vector3(x, 0f, z));
            foreach (Bounds bounds in surfaceBounds)
                if (world.x >= bounds.min.x && world.x <= bounds.max.x &&
                    world.z >= bounds.min.z && world.z <= bounds.max.z) return true;
            return false;
        }

        void HideLegacyTufts()
        {
            foreach (Renderer renderer in grid.Root.GetComponentsInChildren<Renderer>(true))
            {
                string name = renderer.gameObject.name.ToLowerInvariant();
                if (name.StartsWith("grounded detail |") || name.StartsWith("tripo_") || name.Contains("tripo")) continue;
                if (name.StartsWith("grass_") || name.Contains("_grass_") || name.EndsWith("_grass"))
                    renderer.enabled = false;
            }
        }

        IEnumerator Generate()
        {
            int minX = Mathf.Max(0, Mathf.FloorToInt(grid.LocalBounds.min.x) - grid.OriginX);
            int maxX = Mathf.Min(grid.Width, Mathf.CeilToInt(grid.LocalBounds.max.x) - grid.OriginX);
            int minZ = Mathf.Max(0, Mathf.FloorToInt(grid.LocalBounds.min.z) - grid.OriginZ);
            int maxZ = Mathf.Min(grid.Depth, Mathf.CeilToInt(grid.LocalBounds.max.z) - grid.OriginZ);

            var pending = new List<Vector2Int>();
            for (int cz = minZ / ChunkSize; cz <= (maxZ - 1) / ChunkSize; cz++)
            for (int cx = minX / ChunkSize; cx <= (maxX - 1) / ChunkSize; cx++)
                pending.Add(new Vector2Int(cx, cz));
            Vector2Int origin = grid.PointToCell(Vector3.zero) / ChunkSize;
            pending.Sort((a, b) => (a - origin).sqrMagnitude.CompareTo((b - origin).sqrMagnitude));

            int totalSpawned = 0;

            foreach (Vector2Int coordinate in pending)
            {
                int cx = coordinate.x, cz = coordinate.y;
                var chunk = new Chunk();
                for (int z = Mathf.Max(minZ, cz * ChunkSize); z < Mathf.Min(maxZ, (cz + 1) * ChunkSize); z++)
                for (int x = Mathf.Max(minX, cx * ChunkSize); x < Mathf.Min(maxX, (cx + 1) * ChunkSize); x++)
                {
                    Vector2Int cell = new Vector2Int(x, z);
                    if (occupied.Contains(cell) || roads.Contains(cell)) continue;
                    float wx = grid.OriginX + x, wz = grid.OriginZ + z;
                    if (!IsWithinSurfaceBounds(wx + .5f, wz + .5f)) continue;

                    // Broad meadow coverage: natural clustering with good breathing room
                    float meadow = Mathf.PerlinNoise(wx * 0.075f + 37f, wz * 0.075f - 19f);
                    float detail = Mathf.PerlinNoise(wx * 0.18f - 11f, wz * 0.18f + 53f);
                    float patchDensity = meadow * 0.70f + detail * 0.30f;
                    if (patchDensity < 0.28f) continue;

                    int count = 2; // Comfortable low-poly clump density
                    var tufts = new List<Tuft>();
                    for (int n = 0; n < count; n++)
                    {
                        float px = wx + 0.20f + Hash(x, z, n * 17 + 2) * 0.60f;
                        float pz = wz + 0.20f + Hash(x, z, n * 17 + 3) * 0.60f;
                        if (!grid.TrySample(px, pz, out Vector3 point, out Vector3 normal) ||
                            point.y < grid.SeaLevel + 0.65f || normal.y < 0.78f || IsUnderFreshWater(point)) continue;

                        Vector3 worldPoint = grid.Root.TransformPoint(point);
                        Vector3 worldNormal = grid.Root.TransformDirection(normal).normalized;
                        float slope = 1f - Mathf.Clamp01(worldNormal.y);

                        // Strict cliff & rock cutoff
                        if (slope > 0.30f) continue;

                        // Precise mud/soil cutoff matching ReferenceIsland.shader
                        Vector3 soilWarp = new Vector3(
                            Noise(worldPoint * 0.06f + Vector3.one * 3.7f),
                            0f,
                            Noise(worldPoint * 0.06f + Vector3.one * 11.3f)
                        ) * 6f;
                        float soilField = Deposits((worldPoint + soilWarp) * 0.045f + Vector3.one * 17.4f);
                        float forestFloor = Smooth(0.50f, 0.72f, soilField + slope * 0.35f);
                        if (forestFloor > 0.25f) continue; // Absolutely NO grass on dirt / mud!

                        // Shore & beach cutoff
                        float shoreHeight = worldPoint.y - grid.SeaLevel;
                        if (shoreHeight < 0.65f) continue; // No grass on beaches

                        // Density check: comfortable, natural grass distribution
                        float chance = (patchDensity - 0.28f) / 0.72f * (1f - Smooth(0.12f, 0.30f, slope));
                        if (Hash(x, z, n * 17 + 13) > chance * 0.85f) continue;

                        if (hasWreckBounds && worldPoint.x >= wreckBounds.min.x && worldPoint.x <= wreckBounds.max.x &&
                            worldPoint.z >= wreckBounds.min.z && worldPoint.z <= wreckBounds.max.z) continue;

                        float height = 0.55f + Hash(x, z, n * 17 + 4) * 0.25f;
                        float width = 0.85f + Hash(x, z, n * 17 + 5) * 0.35f;
                        Color color = Color.Lerp(new Color(0.38f, 0.52f, 0.22f), new Color(0.56f, 0.68f, 0.28f), Hash(x, z, n * 17 + 6));
                        Quaternion align = Quaternion.FromToRotation(Vector3.up, normal);
                        tufts.Add(new Tuft
                        {
                            matrix = Matrix4x4.TRS(point + Vector3.down * 0.01f,
                                align * Quaternion.Euler(0, Hash(x, z, n * 17 + 7) * 360f, 0),
                                new Vector3(width, height, width)),
                            color = color
                        });
                        totalSpawned++;
                    }
                    if (tufts.Count > 0) chunk.cells.Add(cell, tufts);
                }
                if (chunk.cells.Count > 0) { chunks.Add(new Vector2Int(cx, cz), chunk); Rebuild(chunk); }
                yield return null;
            }

            Debug.Log($"[IslandGrassCover] Grass generation complete: {totalSpawned} grass clumps across {chunks.Count} chunks.");
        }

        public void ClearCell(Vector2Int cell)
        {
            if (chunks.TryGetValue(new Vector2Int(cell.x / ChunkSize, cell.y / ChunkSize), out Chunk chunk) && chunk.cells.Remove(cell)) Rebuild(chunk);
        }

        void Rebuild(Chunk chunk)
        {
            var matrices = new List<Matrix4x4>(); var colors = new List<Vector4>();
            bool first = true; Bounds bounds = default;
            foreach (List<Tuft> tufts in chunk.cells.Values)
            foreach (Tuft tuft in tufts)
            {
                matrices.Add(tuft.matrix); colors.Add(tuft.color);
                Vector3 point = tuft.matrix.GetColumn(3);
                if (first) { bounds = new Bounds(point, Vector3.zero); first = false; } else bounds.Encapsulate(point);
            }
            bounds.Expand(1f); chunk.bounds = bounds;
            chunk.local = matrices.ToArray();
            if (chunk.gameObject == null)
            {
                chunk.gameObject = new GameObject("Grass | meadow patch");
                chunk.gameObject.layer = gameObject.layer;
                chunk.gameObject.transform.SetParent(grid.Root, false);
                chunk.mesh = new Mesh { name = "Combined curved grass patch" };
                chunk.mesh.MarkDynamic();
                chunk.gameObject.AddComponent<MeshFilter>().sharedMesh = chunk.mesh;
                chunk.renderer = chunk.gameObject.AddComponent<MeshRenderer>();
                chunk.renderer.sharedMaterial = material;
                chunk.renderer.shadowCastingMode = ShadowCastingMode.Off;
                chunk.renderer.receiveShadows = true;
            }
            chunk.mesh.Clear();
            if (matrices.Count == 0) { chunk.renderer.enabled = false; return; }
            Vector3[] sourceVertices = mesh.vertices, sourceNormals = mesh.normals;
            Color[] sourceColors = mesh.colors;
            int[] sourceTriangles = mesh.triangles;
            int vertexCount = sourceVertices.Length;
            var vertices = new Vector3[matrices.Count * vertexCount];
            var normals = new Vector3[vertices.Length];
            var vertexColors = new Color32[vertices.Length];
            var triangles = new int[matrices.Count * sourceTriangles.Length];
            for (int i = 0; i < matrices.Count; i++)
            {
                Matrix4x4 normalMatrix = matrices[i].inverse.transpose;
                Color tint = colors[i];
                int offset = i * vertexCount;
                for (int v = 0; v < vertexCount; v++)
                {
                    vertices[offset + v] = matrices[i].MultiplyPoint3x4(sourceVertices[v]);
                    normals[offset + v] = normalMatrix.MultiplyVector(sourceNormals[v]).normalized;
                    Color color = sourceColors[v] * tint;
                    color.a = sourceColors[v].a; // Blade height controls wind bend.
                    vertexColors[offset + v] = color;
                }
                for (int t = 0; t < sourceTriangles.Length; t++)
                    triangles[i * sourceTriangles.Length + t] = offset + sourceTriangles[t];
            }
            chunk.mesh.vertices = vertices; chunk.mesh.normals = normals;
            chunk.mesh.colors32 = vertexColors; chunk.mesh.triangles = triangles;
            chunk.mesh.bounds = bounds; chunk.renderer.enabled = grassVisible;
        }

        void LateUpdate()
        {
            if (material == null) return;
            Camera camera = Camera.main;
            if (camera == null) return;
            float size = camera.orthographic ? camera.orthographicSize : 15f;
            float fade = 1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(35f, 85f, size));
            material.SetFloat(VisibilityId, fade);
            bool visible = fade > .001f;
            if (visible == grassVisible) return;
            grassVisible = visible;
            foreach (Chunk chunk in chunks.Values)
                if (chunk.renderer != null) chunk.renderer.enabled = visible && chunk.cells.Count > 0;
        }

        static Mesh CreateTuft()
        {
            // 6 broad curved stylized cartoon blades with spherical normals
            const int blades = 6;
            var vertices = new Vector3[blades * 5];
            var normals = new Vector3[vertices.Length];
            var colors = new Color[vertices.Length];
            var indices = new int[blades * 9];
            Vector3 sphereCenter = new Vector3(0f, -0.2f, 0f);

            for (int i = 0; i < blades; i++)
            {
                float angle = i * (Mathf.PI * 2f / blades) + ((i % 2 == 0) ? 0.28f : -0.22f);
                Vector3 outward = new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle));
                Vector3 side = new Vector3(-outward.z, 0, outward.x);
                float bladeHeight = .38f + (i % 3) * .08f;
                float radius = .04f + (i % 2) * .03f;
                Vector3 root = outward * radius;
                float halfW = .038f + (i % 2) * .008f;

                Vector3 mid = root + Vector3.up * (bladeHeight * 0.52f) + outward * 0.08f;
                Vector3 tip = root + Vector3.up * bladeHeight + outward * 0.16f;

                int v = i * 5;
                vertices[v] = root - side * halfW;
                vertices[v + 1] = root + side * halfW;
                vertices[v + 2] = mid - side * (halfW * 0.7f);
                vertices[v + 3] = mid + side * (halfW * 0.7f);
                vertices[v + 4] = tip;

                colors[v] = colors[v + 1] = new Color(0.38f, 0.50f, 0.22f, 0.0f);
                colors[v + 2] = colors[v + 3] = new Color(0.55f, 0.68f, 0.28f, 0.55f);
                colors[v + 4] = new Color(0.72f, 0.85f, 0.36f, 1.0f);

                for (int k = 0; k < 5; k++)
                    normals[v + k] = (vertices[v + k] - sphereCenter).normalized;

                int t = i * 9;
                indices[t] = v; indices[t + 1] = v + 2; indices[t + 2] = v + 1;
                indices[t + 3] = v + 1; indices[t + 4] = v + 2; indices[t + 5] = v + 3;
                indices[t + 6] = v + 2; indices[t + 7] = v + 4; indices[t + 8] = v + 3;
            }

            var result = new Mesh { name = "Puffed Cartoon Grass Clump" };
            result.vertices = vertices;
            result.normals = normals;
            result.colors = colors;
            result.triangles = indices;
            result.RecalculateBounds();
            return result;
        }

        static float Hash(int x, int z, int seed)
        {
            unchecked { uint v = (uint)(x * 73856093 ^ z * 19349663 ^ seed * 83492791); v ^= v >> 13; v *= 1274126177u; v ^= v >> 16; return (v & 65535) / 65535f; }
        }
        static float Frac(float v) => v - Mathf.Floor(v);
        static float NoiseHash(Vector3 p)
        {
            p = new Vector3(Frac(p.x * .1031f), Frac(p.y * .1031f), Frac(p.z * .1031f));
            float dot = Vector3.Dot(p, new Vector3(p.y + 33.33f, p.z + 33.33f, p.x + 33.33f));
            p += Vector3.one * dot;
            return Frac((p.x + p.y) * p.z);
        }
        static float Smooth(float a, float b, float v) { float t = Mathf.Clamp01((v-a)/(b-a)); return t*t*(3f-2f*t); }
        static float Noise(Vector3 p)
        {
            Vector3 c = new Vector3(Mathf.Floor(p.x), Mathf.Floor(p.y), Mathf.Floor(p.z));
            Vector3 f = p-c;
            f = new Vector3(f.x*f.x*(3-2*f.x), f.y*f.y*(3-2*f.y), f.z*f.z*(3-2*f.z));
            float a = Mathf.Lerp(Mathf.Lerp(NoiseHash(c),NoiseHash(c+Vector3.right),f.x),
                Mathf.Lerp(NoiseHash(c+Vector3.up),NoiseHash(c+Vector3.right+Vector3.up),f.x),f.y);
            float b = Mathf.Lerp(Mathf.Lerp(NoiseHash(c+Vector3.forward),NoiseHash(c+Vector3.right+Vector3.forward),f.x),
                Mathf.Lerp(NoiseHash(c+Vector3.up+Vector3.forward),NoiseHash(c+Vector3.one),f.x),f.y);
            return Mathf.Lerp(a,b,f.z);
        }
        static float Deposits(Vector3 p) => Noise(p)*.58f + Noise(p*2.07f+Vector3.one*12.7f)*.28f + Noise(p*4.19f+Vector3.one*37.1f)*.14f;
        void OnDestroy()
        {
            foreach (MeshCollider water in freshWater) if (water != null) Destroy(water.gameObject);
            foreach (Chunk chunk in chunks.Values)
            {
                if (chunk.gameObject != null) Destroy(chunk.gameObject);
                if (chunk.mesh != null) Destroy(chunk.mesh);
            }
            if (mesh != null) Destroy(mesh);
            if (material != null) Destroy(material);
        }
    }
}
