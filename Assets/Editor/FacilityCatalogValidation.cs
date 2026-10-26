using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using LastLandfall.Prototype;
using UnityEditor;
using UnityEngine;

namespace LastLandfall.EditorTools
{
    public static class FacilityCatalogValidation
    {
        private const BindingFlags Private = BindingFlags.NonPublic | BindingFlags.Instance;
        [Serializable] private sealed class Catalog { public BuildingConstructionCatalog.Entry[] entries; }
        [Serializable] private sealed class Report
        {
            public bool passed;
            public int facilities, coveredModules;
            public List<string> failures = new List<string>();
            public List<string> loaded = new List<string>();
        }

        [MenuItem("Last Landfall/Validate All Facilities")]
        public static void Validate()
        {
            Report report = Inspect();
            Directory.CreateDirectory("work/facility_catalog");
            File.WriteAllText("work/facility_catalog/validation.json", JsonUtility.ToJson(report, true));
            if (report.passed) Debug.Log("FACILITY_CATALOG_VALIDATION " + JsonUtility.ToJson(report));
            else Debug.LogError("FACILITY_CATALOG_VALIDATION " + JsonUtility.ToJson(report));
        }

        public static void RunBatch()
        {
            Validate();
            Report report = JsonUtility.FromJson<Report>(File.ReadAllText("work/facility_catalog/validation.json"));
            EditorApplication.Exit(report.passed ? 0 : 1);
        }

        private static Report Inspect()
        {
            Report report = new Report();
            var covered = new HashSet<string>();
            Array definitions = (Array)typeof(BuildPlacementPrototype)
                .GetField("Buildables", BindingFlags.NonPublic | BindingFlags.Static).GetValue(null);
            report.facilities = definitions.Length;
            if (definitions.Length != 25) report.failures.Add("Expected 25 menu facilities.");
            GameObject host = new GameObject("Facility validation");
            Mesh land = null;
            try
            {
                BuildPlacementPrototype prototype = host.AddComponent<BuildPlacementPrototype>();
                land = new Mesh { name = "Validation land" };
                land.vertices = new[] { new Vector3(-2, 1, -2), new Vector3(-2, 1, 2),
                    new Vector3(2, 1, 2), new Vector3(2, 1, -2) };
                land.triangles = new[] { 0, 1, 2, 0, 2, 3 };
                MeshCollider surface = host.AddComponent<MeshCollider>();
                surface.sharedMesh = land;
                Physics.SyncTransforms();
                var grid = new IslandConstructionGrid(host.transform, new[] { surface },
                    new Bounds(Vector3.zero, new Vector3(36, 4, 36)), -0.92f);
                // Synthetic fixture: all water in this small board lies ten metres from shore.
                grid.SetCoastDistanceField(new[] { .625f,.625f,.625f,.625f },2,
                    new Vector2(grid.OriginX,grid.OriginZ),new Vector2(grid.Width,grid.Depth),40f);
                typeof(BuildPlacementPrototype).GetField("constructionGrid", Private).SetValue(prototype, grid);
                typeof(BuildPlacementPrototype).GetField("mapRoot", Private).SetValue(prototype, host.transform);
                typeof(BuildPlacementPrototype).GetField("wood", Private).SetValue(prototype, 99999);

                foreach (object definition in definitions)
                {
                    Type type = definition.GetType();
                    string asset = (string)type.GetField("AssetName").GetValue(definition);
                    string icon = (string)type.GetField("IconName").GetValue(definition);
                    string kind = type.GetField("Kind").GetValue(definition).ToString();
                    if (!BuildingConstructionCatalog.TryGet(asset, out var entry))
                    {
                        report.failures.Add(asset + ": no construction entry");
                        continue;
                    }
                    covered.Add(entry.key);
                    GameObject prefab = Resources.Load<GameObject>(entry.finalResource);
                    if (prefab == null || prefab.GetComponentsInChildren<Renderer>(true).Length == 0)
                        report.failures.Add(asset + ": no renderable final model");
                    if (Resources.Load<Texture2D>("UI/BuildIcons/" + icon) == null)
                        report.failures.Add(asset + ": missing icon " + icon);
                    if (BuildingConstructionCatalog.LoadSchedule(entry) == null ||
                        Resources.Load<GameObject>(entry.modelResource) == null)
                        report.failures.Add(asset + ": missing construction model/schedule");
                    if (kind == "Road")
                        foreach (string road in new[] { "RoadStraight", "RoadCorner", "RoadTee", "RoadCross", "RoadEnd" })
                            if (BuildingConstructionCatalog.TryGet(road, out var module)) covered.Add(module.key);
                    if (kind == "Water") CheckWater(prototype, grid, definition, asset, report);
                    report.loaded.Add(asset);
                }

                Catalog catalog = JsonUtility.FromJson<Catalog>(Resources.Load<TextAsset>("Construction/Catalog").text);
                foreach (var entry in catalog.entries)
                {
                    if (!covered.Contains(entry.key)) report.failures.Add(entry.key + ": not reachable from menu");
                    if (Resources.Load<GameObject>(entry.finalResource) == null ||
                        Resources.Load<GameObject>(entry.modelResource) == null ||
                        BuildingConstructionCatalog.LoadSchedule(entry) == null)
                        report.failures.Add(entry.key + ": incomplete module resources");
                }
            }
            catch (Exception exception) { report.failures.Add(exception.ToString()); }
            finally
            {
                UnityEngine.Object.DestroyImmediate(host);
                if (land != null) UnityEngine.Object.DestroyImmediate(land);
            }
            report.coveredModules = covered.Count;
            report.passed = report.failures.Count == 0 && report.facilities == 25 && covered.Count == 29;
            return report;
        }

        private static void CheckWater(BuildPlacementPrototype prototype, IslandConstructionGrid grid,
            object definition, string asset, Report report)
        {
            MethodInfo canPlace = typeof(BuildPlacementPrototype).GetMethod("CanPlaceWater", Private);
            Vector2Int water = grid.PointToCell(new Vector3(5, 0, 5));
            object[] args = { water, definition, null };
            if (!(bool)canPlace.Invoke(prototype, args)) report.failures.Add(asset + ": rejects open water");
            args[0] = grid.PointToCell(Vector3.zero);
            if ((bool)canPlace.Invoke(prototype, args)) report.failures.Add(asset + ": accepts land");
            var occupied = (HashSet<Vector2Int>)typeof(BuildPlacementPrototype).GetField("occupiedCells", Private).GetValue(prototype);
            occupied.Add(water);
            args[0] = water;
            if ((bool)canPlace.Invoke(prototype, args)) report.failures.Add(asset + ": accepts occupied water");
            occupied.Clear();
        }
    }
}
