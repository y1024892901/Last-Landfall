using UnityEngine;

namespace LastLandfall
{
    public static class TripoIslandAssets
    {
        const string Root = "Models/Environment/Tripo/";

        // Keep the terrain, water and individual trees; hide placed scenery.
        public static void ClearDecorations(GameObject root)
        {
            foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
            {
                string name = renderer.name.ToLowerInvariant();
                bool keep = name.Contains("terrain source") || name.Contains("water") ||
                    name.Contains("conifer") || name.Contains("pine") || name.Contains("broadleaf") ||
                    name.Contains("tree") || name.Contains("palm");
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
            var landMaterial = MakeMaterial(null);
            foreach (var mesh in model.GetComponentsInChildren<MeshFilter>())
            {
                mesh.name = "Tripo_terrain source";
                SetMaterial(mesh.GetComponent<Renderer>(), landMaterial);
                var collider = mesh.gameObject.AddComponent<MeshCollider>();
                collider.sharedMesh = mesh.sharedMesh;
            }
            AddFreshWater(model);
            var pine = Resources.Load<GameObject>(Root + "Pine/pine_tree_3d_model");
            if (pine == null) return;
            var treeMaterial = MakeMaterial(Root + "Pine/pine_tree_3d_model.fbm/pine_tree_3d_model_basecolor");
            var random = new System.Random(1028);
            var surfaces = model.GetComponentsInChildren<MeshCollider>();
            bounds = GetBounds(model);
            for (int i = 0; i < 150; i++)
            {
                Vector3 origin = new Vector3(Mathf.Lerp(bounds.min.x, bounds.max.x, (float)random.NextDouble()), bounds.max.y + 10f,
                    Mathf.Lerp(bounds.min.z, bounds.max.z, (float)random.NextDouble()));
                foreach (var surface in surfaces)
                {
                    if (!surface.Raycast(new Ray(origin, Vector3.down), out var hit, bounds.size.y + 20f)) continue;
                    if (hit.point.y < target.min.y + target.size.y * .3f || hit.normal.y < .8f) break;
                    var tree = Object.Instantiate(pine, model.transform, false);
                    tree.name = "Tripo_Conifer_" + i;
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
                    break;
                }
            }
        }

        static Bounds GetBounds(GameObject model)
        {
            var renderers = model.GetComponentsInChildren<Renderer>();
            Bounds bounds = renderers[0].bounds;
            foreach (var renderer in renderers) bounds.Encapsulate(renderer.bounds);
            return bounds;
        }

        static void AddFreshWater(GameObject model)
        {
            var shader = Resources.Load<Shader>("Shaders/TripoFreshWater");
            if (shader == null) return;
            var material = new Material(shader) { name = "Tripo Dynamic Fresh Water" };
            material.SetTexture("_WaterRegion", Resources.Load<Texture2D>(
                Root + "Island/island_terrain_3d_model.fbm/island_terrain_3d_model_basecolor"));
#if UNITY_EDITOR
            if (!Application.isPlaying)
            {
                string path = "Assets/LastLandfall/Resources/Models/Environment/Tripo/Tripo Dynamic Fresh Water.mat";
                var saved = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>(path);
                if (saved == null) UnityEditor.AssetDatabase.CreateAsset(material, path);
                else
                {
                    UnityEditor.EditorUtility.CopySerialized(material, saved);
                    UnityEditor.EditorUtility.SetDirty(saved);
                    Object.DestroyImmediate(material);
                    material = saved;
                }
            }
#endif
            foreach (var terrain in model.GetComponentsInChildren<MeshFilter>())
            {
                var water = new GameObject("Tripo_Water_StreamAndBasin");
                water.transform.SetParent(terrain.transform, false);
                water.AddComponent<MeshFilter>().sharedMesh = BuildWaterSurface(terrain);
                var renderer = water.AddComponent<MeshRenderer>();
                int count = Mathf.Max(1, terrain.sharedMesh.subMeshCount);
                var materials = new Material[count];
                for (int i = 0; i < count; i++) materials[i] = material;
                renderer.sharedMaterials = materials;
                renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }
        }

        static Mesh BuildWaterSurface(MeshFilter terrain)
        {
            var mesh = Object.Instantiate(terrain.sharedMesh);
            mesh.name = "Tripo independent freshwater surface";
            var texture = Resources.Load<Texture2D>(Root +
                "Island/island_terrain_3d_model.fbm/island_terrain_3d_model_basecolor");
            if (texture == null || !texture.isReadable)
            {
                Debug.LogWarning("Freshwater surface requires the readable island reference texture.");
                return mesh;
            }
            var vertices = mesh.vertices;
            var uv = mesh.uv;
            var selected = new bool[vertices.Length];
            var world = new Vector3[vertices.Length];
            for (int i = 0; i < vertices.Length; i++)
            {
                world[i] = terrain.transform.TransformPoint(vertices[i]);
                Color color = texture.GetPixelBilinear(uv[i].x, uv[i].y);
                selected[i] = color.b > color.r + .035f && color.g > color.r + .035f && color.b > color.g - .04f;
            }
            bool hasWater = false;
            for (int i = 0; i < selected.Length; i++) hasWater |= selected[i];
            if (!hasWater) return mesh;
            var neighbors = new System.Collections.Generic.List<int>[vertices.Length];
            for (int i = 0; i < neighbors.Length; i++) neighbors[i] = new System.Collections.Generic.List<int>();
            var triangles = mesh.triangles;
            for (int i = 0; i < triangles.Length; i += 3)
                for (int edge = 0; edge < 3; edge++)
                {
                    int a = triangles[i + edge], b = triangles[i + (edge + 1) % 3];
                    neighbors[a].Add(b); neighbors[b].Add(a);
                }
            var levels = new float[vertices.Length];
            const float waterLift = .85f;
            for (int i = 0; i < levels.Length; i++)
                levels[i] = selected[i] ? world[i].y + waterLift : world[i].y;
            // Smooth only the marked channel, keeping the surface above its local bed.
            for (int pass = 0; pass < 5; pass++)
            {
                var next = (float[])levels.Clone();
                for (int i = 0; i < levels.Length; i++)
                {
                    if (!selected[i]) continue;
                    float total = levels[i]; int count = 1;
                    foreach (int neighbor in neighbors[i])
                        if (selected[neighbor]) { total += levels[neighbor]; count++; }
                    next[i] = Mathf.Max(world[i].y + .70f, Mathf.Lerp(levels[i], total / count, .42f));
                }
                levels = next;
            }
            for (int i = 0; i < vertices.Length; i++)
            {
                if (!selected[i]) continue;
                world[i].y = levels[i];
                vertices[i] = terrain.transform.InverseTransformPoint(world[i]);
            }
            mesh.vertices = vertices;
            mesh.RecalculateNormals(); mesh.RecalculateBounds();
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
                    Object.DestroyImmediate(mesh); mesh = saved;
                }
            }
#endif
            return mesh;
        }

        static Material MakeMaterial(string path)
        {
            bool terrain = path == null;
            var material = terrain
                ? new Material(Resources.Load<Material>("Materials/Gate25Terrain"))
                : new Material(Shader.Find("Universal Render Pipeline/Lit"));
            material.name = terrain ? "Tripo Clean Terrain" : "Tripo Pine";
            if (terrain)
            {
                Prototype.TerrainSurfaceLibrary.Configure(material);
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
                material.SetFloat("_SurfaceDetail", .9f);
                material.SetFloat("_NormalStrength", .5f);
                material.SetTexture("_RiverMaskSource", Resources.Load<Texture2D>(
                    Root + "Island/island_terrain_3d_model.fbm/island_terrain_3d_model_basecolor"));
                material.SetFloat("_RiverMaskStrength", 1f);
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
