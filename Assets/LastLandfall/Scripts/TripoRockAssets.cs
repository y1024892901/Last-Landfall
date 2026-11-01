using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall
{
    // Uses the same placement for the editor preview and the playable island.
    public static class TripoRockAssets
    {
        const string Path = "Models/Environment/Tripo/Rocks/";
        const string Collection = "Tripo Rock Collection";
        const string Layout = "Layout_v3_MainPebbles";
        static readonly string[] Names = { "WeatheredBoulder", "AngularRock", "LayeredRock", "PebbleCluster" };

        public static void Apply(GameObject island)
        {
            if (island == null) return;
            var existing = island.transform.Find(Collection);
            if (existing != null && existing.Find(Layout) != null)
            {
                foreach (var r in existing.GetComponentsInChildren<Renderer>()) r.enabled = true;
                return;
            }
            var models = new GameObject[4];
            for (int i = 0; i < models.Length; i++)
                if ((models[i] = Resources.Load<GameObject>(Path + Names[i])) == null) return;
            if (existing != null)
            {
                existing.gameObject.SetActive(false);
                if (Application.isPlaying) Object.Destroy(existing.gameObject);
                else Object.DestroyImmediate(existing.gameObject);
            }
            var texture = Resources.Load<Texture2D>(Path + "Rocks_BaseColor");
            if (texture == null) return;
            var material = Resources.Load<Material>(Path + "Rocks_Material");
            if (material == null)
            {
                material = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = "Tripo Rocks", enableInstancing = true };
                material.SetTexture("_BaseMap", texture);
                material.SetFloat("_Smoothness", .08f);
#if UNITY_EDITOR
                if (!Application.isPlaying) UnityEditor.AssetDatabase.CreateAsset(material,
                    "Assets/LastLandfall/Resources/" + Path + "Rocks_Material.mat");
#endif
            }
            var surfaces = new List<MeshCollider>();
            var water = new List<Bounds>();
            var obstacles = new List<Bounds>();
            foreach (var f in island.GetComponentsInChildren<MeshFilter>())
            {
                if (!f.TryGetComponent<Renderer>(out var r) || !r.enabled) continue;
                string n = f.name.ToLowerInvariant();
                if (n.Contains("terrain source") && f.TryGetComponent<MeshCollider>(out var c) && c.enabled) surfaces.Add(c);
                if (n.Contains("water") && f.sharedMesh != null)
                {
                    // Small local bounds avoid treating the entire winding river's bounding box as water.
                    var vertices = f.sharedMesh.vertices;
                    for (int v = 0; v < vertices.Length; v += 3)
                        water.Add(new Bounds(f.transform.TransformPoint(vertices[v]), new Vector3(2.8f, 1000f, 2.8f)));
                }
                if (n.StartsWith("wreck_") || n.StartsWith("tripo_vegetation_") && r.bounds.size.y > 3f)
                    obstacles.Add(r.bounds);
            }
            Physics.SyncTransforms();
            var root = new GameObject(Collection);
            root.transform.SetParent(island.transform, false);
            new GameObject(Layout).transform.SetParent(root.transform, false);
            var random = new System.Random(281101);
            var occupied = new List<Vector3>();
            int count = 0;
            foreach (var surface in surfaces)
            {
                Bounds b = surface.bounds;
                bool west = false, east = false;
                for (var parent = surface.transform; parent != null; parent = parent.parent)
                {
                    west |= parent.name.Contains("West");
                    east |= parent.name.Contains("East");
                }
                // Satellite names are retained on their containing objects in both saved and runtime layouts.
                bool main = !west && !east;
                string islandName = main ? "Main" : west ? "West" : "East";
                int islandCount = 0, largeCount = 0;
                var anchors = west
                    ? new[] { new Vector2(.22f,.76f), new Vector2(.47f,.80f), new Vector2(.72f,.73f),
                        new Vector2(.19f,.52f), new Vector2(.48f,.57f), new Vector2(.77f,.49f),
                        new Vector2(.22f,.29f), new Vector2(.48f,.28f), new Vector2(.73f,.25f) }
                    : new[] { new Vector2(.24f,.73f), new Vector2(.76f,.68f), new Vector2(.21f,.32f), new Vector2(.75f,.24f) };
                for (int group = 0; group < anchors.Length; group++)
                {
                    Vector3 center = new Vector3(Mathf.Lerp(b.min.x,b.max.x,anchors[group].x), 0f,
                        Mathf.Lerp(b.min.z,b.max.z,anchors[group].y));
                    int target = main ? 26 : west ? 15 : 4;
                    for (int attempt = 0, placed = 0; attempt < 600 && placed < target; attempt++)
                    {
                        float radius = Mathf.Min(b.size.x,b.size.z) * (main ? .13f : west ? .115f : .075f);
                        Vector3 p = center + new Vector3(Next()-.5f,0f,Next()-.5f) * radius * 2f;
                        p.y = b.max.y + 8f;
                        if (!surface.Raycast(new Ray(p,Vector3.down),out var hit,b.size.y+16f) || hit.normal.y < (west ? .65f : .78f) || hit.point.y < .3f) continue;
                        p = hit.point;
                        bool blocked = false;
                        foreach (var w in water) if (w.Contains(p)) { blocked = true; break; }
                        foreach (var o in obstacles)
                            if (p.x > o.min.x-1f && p.x < o.max.x+1f && p.z > o.min.z-1f && p.z < o.max.z+1f) { blocked = true; break; }
                        float spacing = main ? .8f : west ? 1.45f : 2.25f;
                        foreach (var o in occupied) if (new Vector2(p.x-o.x,p.z-o.z).sqrMagnitude < spacing*spacing) { blocked = true; break; }
                        if (blocked) continue;
                        int kind = main ? (largeCount == 0 ? 0 : placed % 5 == 0 ? 2 : 3)
                            : west ? (placed % 7 == 0 ? 0 : placed % 3 == 0 ? 1 : placed % 3 == 1 ? 2 : 3)
                            : placed == 0 ? group % 3 : placed == 1 ? 2 : 3;
                        float height = kind == 0 ? 2.3f+Next()*.8f : kind == 1 ? 1.2f+Next()*.65f
                            : kind == 2 ? (main ? .22f+Next()*.18f : .55f+Next()*.45f)
                            : main ? .16f+Next()*.22f : .28f+Next()*.3f;
                        var rock = Object.Instantiate(models[kind],root.transform,false);
                        rock.name = "Tripo_Rock_" + islandName + "_" + Names[kind] + "_" + count;
                        var renderers = rock.GetComponentsInChildren<Renderer>();
                        Bounds rb = renderers[0].bounds;
                        foreach (var r in renderers) rb.Encapsulate(r.bounds);
                        rock.transform.localScale *= height / Mathf.Max(.001f,rb.size.y);
                        rock.transform.Rotate(Vector3.up,Next()*360f,Space.World);
                        rb = renderers[0].bounds;
                        foreach (var r in renderers) rb.Encapsulate(r.bounds);
                        rock.transform.position += p - new Vector3(rb.center.x,rb.min.y+height*.12f,rb.center.z);
                        foreach (var r in renderers)
                        {
                            r.name = rock.name;
                            var slots = r.sharedMaterials;
                            for (int m=0;m<slots.Length;m++) slots[m]=material;
                            r.sharedMaterials=slots;
                        }
                        occupied.Add(p); placed++; count++;
                        islandCount++;
                        if (kind == 0) largeCount++;
                    }
                }
                Debug.Log($"TRIPO_ROCK_LAYOUT: {islandName}: {islandCount} rocks, {largeCount} large boulders");
            }
            Debug.Log("TRIPO_ROCKS_PLACED: " + count);
            float Next() => (float)random.NextDouble();
        }
    }
}
