using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace LastLandfall.Prototype
{
    public sealed class IslandGrassCover : MonoBehaviour
    {
        const int ChunkSize = 8;
        static readonly int ColorId = Shader.PropertyToID("_InstanceColor");
        readonly Dictionary<Vector2Int, Chunk> chunks = new Dictionary<Vector2Int, Chunk>();
        IslandConstructionGrid grid;
        HashSet<Vector2Int> occupied, roads;
        Material material;
        Mesh mesh;
        struct Tuft { public Matrix4x4 matrix; public Vector4 color; }
        sealed class Chunk
        {
            public readonly Dictionary<Vector2Int, List<Tuft>> cells = new Dictionary<Vector2Int, List<Tuft>>();
            public Matrix4x4[] local, world;
            public readonly MaterialPropertyBlock properties = new MaterialPropertyBlock();
            public Bounds bounds;
        }

        public void Initialize(IslandConstructionGrid terrainGrid, HashSet<Vector2Int> occupiedCells, HashSet<Vector2Int> roadCells)
        {
            grid = terrainGrid; occupied = occupiedCells; roads = roadCells;
            Shader shader = Resources.Load<Shader>("Shaders/GrassBlades");
            if (shader == null || !SystemInfo.supportsInstancing) { Debug.LogWarning("Grass cover requires the grass shader and GPU instancing."); return; }
            material = new Material(shader) { name = "Island grass blades", enableInstancing = true };
            mesh = CreateTuft();
            StartCoroutine(Generate());
        }

        IEnumerator Generate()
        {
            int minX = Mathf.Max(0, Mathf.FloorToInt(grid.LocalBounds.min.x) - grid.OriginX);
            int maxX = Mathf.Min(grid.Width, Mathf.CeilToInt(grid.LocalBounds.max.x) - grid.OriginX);
            int minZ = Mathf.Max(0, Mathf.FloorToInt(grid.LocalBounds.min.z) - grid.OriginZ);
            int maxZ = Mathf.Min(grid.Depth, Mathf.CeilToInt(grid.LocalBounds.max.z) - grid.OriginZ);
            for (int cz = minZ / ChunkSize; cz <= (maxZ - 1) / ChunkSize; cz++)
            for (int cx = minX / ChunkSize; cx <= (maxX - 1) / ChunkSize; cx++)
            {
                var chunk = new Chunk();
                for (int z = Mathf.Max(minZ, cz * ChunkSize); z < Mathf.Min(maxZ, (cz + 1) * ChunkSize); z++)
                for (int x = Mathf.Max(minX, cx * ChunkSize); x < Mathf.Min(maxX, (cx + 1) * ChunkSize); x++)
                {
                    Vector2Int cell = new Vector2Int(x, z);
                    if (occupied.Contains(cell) || roads.Contains(cell)) continue;
                    var tufts = new List<Tuft>();
                    for (int n = 0; n < 4; n++)
                    {
                        float px = grid.OriginX + x + (n % 2 + .2f + Hash(x,z,n*7) * .6f) * .5f;
                        float pz = grid.OriginZ + z + (n / 2 + .2f + Hash(x,z,n*7+1) * .6f) * .5f;
                        if (!grid.TrySample(px, pz, out Vector3 point, out Vector3 normal) || point.y < grid.SeaLevel + 1.35f || normal.y < .83f) continue;
                        float height = .16f + Hash(x,z,n*11+2) * .18f;
                        float width = .65f + Hash(x,z,n*11+3) * .55f;
                        Color color = Color.Lerp(new Color(.17f,.25f,.08f), new Color(.40f,.46f,.19f), Hash(x,z,n*11+4));
                        tufts.Add(new Tuft { matrix = Matrix4x4.TRS(point + Vector3.down * .015f,
                            Quaternion.Euler(0, Hash(x,z,n*11+5) * 360f, 0), new Vector3(width,height,width)), color = color });
                    }
                    if (tufts.Count > 0) chunk.cells.Add(cell, tufts);
                }
                if (chunk.cells.Count > 0) { chunks.Add(new Vector2Int(cx,cz), chunk); Rebuild(chunk); }
                yield return null;
            }
        }

        public void ClearCell(Vector2Int cell)
        {
            if (chunks.TryGetValue(new Vector2Int(cell.x / ChunkSize, cell.y / ChunkSize), out Chunk chunk) && chunk.cells.Remove(cell)) Rebuild(chunk);
        }

        static void Rebuild(Chunk chunk)
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
            chunk.local = matrices.ToArray(); chunk.world = new Matrix4x4[matrices.Count];
            if (colors.Count > 0) chunk.properties.SetVectorArray(ColorId, colors);
        }

        void LateUpdate()
        {
            if (material == null || mesh == null || grid == null) return;
            Camera camera = Camera.main;
            if (camera == null) return;
            Plane[] planes = GeometryUtility.CalculateFrustumPlanes(camera);
            Matrix4x4 root = grid.Root.localToWorldMatrix;
            foreach (Chunk chunk in chunks.Values)
            {
                int count = chunk.local.Length; if (count == 0) continue;
                Vector3 e = chunk.bounds.extents;
                Vector3 x = root.MultiplyVector(new Vector3(e.x,0,0)), y = root.MultiplyVector(new Vector3(0,e.y,0)), z = root.MultiplyVector(new Vector3(0,0,e.z));
                Vector3 worldExt = new Vector3(Mathf.Abs(x.x)+Mathf.Abs(y.x)+Mathf.Abs(z.x), Mathf.Abs(x.y)+Mathf.Abs(y.y)+Mathf.Abs(z.y), Mathf.Abs(x.z)+Mathf.Abs(y.z)+Mathf.Abs(z.z));
                if (!GeometryUtility.TestPlanesAABB(planes, new Bounds(root.MultiplyPoint3x4(chunk.bounds.center), worldExt * 2))) continue;
                for (int i = 0; i < count; i++) chunk.world[i] = root * chunk.local[i];
                Graphics.DrawMeshInstanced(mesh, 0, material, chunk.world, count, chunk.properties, ShadowCastingMode.Off, true, gameObject.layer, camera);
            }
        }

        static Mesh CreateTuft()
        {
            var vertices = new Vector3[9]; var indices = new int[9];
            for (int i = 0; i < 3; i++)
            {
                float angle = i * Mathf.PI / 3f;
                Vector3 side = new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * .065f;
                vertices[i*3] = -side; vertices[i*3+1] = side; vertices[i*3+2] = Vector3.up + side * .3f;
                indices[i*3] = i*3; indices[i*3+1] = i*3+2; indices[i*3+2] = i*3+1;
            }
            var result = new Mesh { name = "Shared three-blade tuft" }; result.vertices = vertices; result.triangles = indices; result.RecalculateBounds(); return result;
        }
        static float Hash(int x, int z, int seed)
        {
            unchecked { uint v = (uint)(x * 73856093 ^ z * 19349663 ^ seed * 83492791); v ^= v >> 13; v *= 1274126177u; v ^= v >> 16; return (v & 65535) / 65535f; }
        }
        void OnDestroy() { if (mesh != null) Destroy(mesh); if (material != null) Destroy(material); }
    }
}
