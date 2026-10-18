using System;
using System.IO;
using System.Reflection;
using LastLandfall.Prototype;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace LastLandfall.EditorTools
{
    public static class IslandConstructionGridValidation
    {
        private const string BatchKey = "LastLandfall.GridValidation.Batch";
        private const string Output = "work/island_construction_grid";
        private static int frames;
        private static bool running;

        [Serializable]
        private sealed class Report
        {
            public bool passed;
            public string model = "IslandReference_V2";
            public int width, depth, landCells, ordinaryBuildingCells, reservedTerrainCells;
            public int buildingCellsOutsideOldEllipse, overlayMeshes, sourceTriangles, overlayTriangles;
            public int aboveWaterVertices, verticesOutsideGrid;
            public bool overlaysReuseExactSourceMeshes, sourceResourceMatches, shaderCompiled;
            public bool mountainPickingPassed, mountainBuildingRejected, outerLowlandPlacementPassed;
            public bool selectionShowsWholeGrid, cancellationHidesWholeGrid, noFlatHelper;
            public Vector3 minimum, maximum, mountainSample, outerLowlandSample;
            public string error;
        }

        public static void RunBatch()
        {
            SessionState.SetBool(BatchKey, true);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            ResumeBatch();
            EditorApplication.EnterPlaymode();
        }

        [InitializeOnLoadMethod]
        private static void ResumeBatch()
        {
            if (!SessionState.GetBool(BatchKey, false)) return;
            frames = 0;
            EditorApplication.update -= WaitForPrototype;
            EditorApplication.update += WaitForPrototype;
        }

        private static void WaitForPrototype()
        {
            if (!EditorApplication.isPlaying || running) return;
            BuildPlacementPrototype prototype = UnityEngine.Object.FindAnyObjectByType<BuildPlacementPrototype>();
            if (prototype == null || prototype.ConstructionGrid == null || ++frames < 12) return;
            running = true;
            EditorApplication.update -= WaitForPrototype;
            int exitCode = 1;
            try
            {
                Report report = Validate(prototype);
                Directory.CreateDirectory(Output);
                File.WriteAllText(Path.Combine(Output, "validation.json"), JsonUtility.ToJson(report, true));
                Debug.Log("ISLAND_GRID_VALIDATION " + JsonUtility.ToJson(report));
                exitCode = report.passed ? 0 : 1;
            }
            catch (Exception exception)
            {
                Directory.CreateDirectory(Output);
                File.WriteAllText(Path.Combine(Output, "validation.json"), JsonUtility.ToJson(new Report { error = exception.ToString() }, true));
                Debug.LogException(exception);
            }
            finally
            {
                SessionState.SetBool(BatchKey, false);
                EditorApplication.Exit(exitCode);
            }
        }

        private static Report Validate(BuildPlacementPrototype prototype)
        {
            MainMenuController menu = UnityEngine.Object.FindAnyObjectByType<MainMenuController>();
            if (menu != null) menu.BeginGame(false);
            IslandConstructionGrid grid = prototype.ConstructionGrid;
            Report report = new Report
            {
                width = grid.Width, depth = grid.Depth,
                minimum = grid.LocalBounds.min, maximum = grid.LocalBounds.max,
                overlaysReuseExactSourceMeshes = true,
                overlayMeshes = prototype.ConstructionGridRenderers.Length,
                noFlatHelper = GameObject.Find("Highland | seamless buildable ground") == null
            };
            Shader shader = Shader.Find("LastLandfall/Island Construction Grid");
            report.shaderCompiled = shader != null && shader.isSupported && !ShaderUtil.ShaderHasError(shader);
            GameObject resource = Resources.Load<GameObject>("Models/IslandReference_V2");
            MeshFilter[] assetMeshes = resource.GetComponentsInChildren<MeshFilter>(true);
            report.sourceResourceMatches = assetMeshes.Length == grid.Surfaces.Length;
            foreach (MeshCollider surface in grid.Surfaces)
            {
                Mesh mesh = surface.sharedMesh;
                bool inResource = false;
                foreach (MeshFilter asset in assetMeshes) inResource |= asset.sharedMesh == mesh;
                report.sourceResourceMatches &= inResource;
                report.sourceTriangles += mesh.triangles.Length / 3;
                foreach (Vector3 vertex in mesh.vertices)
                {
                    Vector3 point = grid.Root.InverseTransformPoint(surface.transform.TransformPoint(vertex));
                    if (point.y <= grid.SeaLevel + 0.002f) continue;
                    report.aboveWaterVertices++;
                    if (!grid.Contains(grid.PointToCell(point))) report.verticesOutsideGrid++;
                }
            }
            foreach (Renderer overlay in prototype.ConstructionGridRenderers)
            {
                MeshFilter filter = overlay.GetComponent<MeshFilter>();
                MeshFilter source = overlay.transform.parent.GetComponent<MeshFilter>();
                report.overlaysReuseExactSourceMeshes &= source != null && filter.sharedMesh == source.sharedMesh &&
                    overlay.transform.localPosition == Vector3.zero && overlay.transform.localRotation == Quaternion.identity &&
                    overlay.transform.localScale == Vector3.one && overlay.sharedMaterials.Length == source.sharedMesh.subMeshCount;
                report.overlayTriangles += filter.sharedMesh.triangles.Length / 3;
            }

            Vector2Int outer = default, mountain = default;
            float highest = float.NegativeInfinity;
            for (int x = 0; x < grid.Width; x++)
            for (int z = 0; z < grid.Depth; z++)
            {
                Vector2Int cell = new Vector2Int(x, z);
                IslandConstructionGrid.CellTerrain terrain = grid.GetTerrain(cell);
                if (!terrain.HasLand) continue;
                report.landCells++;
                if (terrain.AllowsBuilding)
                {
                    report.ordinaryBuildingCells++;
                    Vector3 center = grid.CellCenter(cell);
                    float nx = center.x / 9f, nz = (center.z + 1.6f) / 6.3f;
                    if (nx * nx + nz * nz > 1.2f)
                    {
                        outer = cell;
                        report.buildingCellsOutsideOldEllipse++;
                    }
                }
                else report.reservedTerrainCells++;
                Vector3 ground = grid.CellCenter(cell);
                if (ground.y > highest) { mountain = cell; highest = ground.y; }
            }
            report.mountainSample = grid.CellCenter(mountain);
            report.outerLowlandSample = grid.CellCenter(outer);
            BindingFlags flags = BindingFlags.Instance | BindingFlags.NonPublic;
            Type type = typeof(BuildPlacementPrototype);
            MethodInfo select = type.GetMethod("SelectBuildable", flags);
            MethodInfo preview = type.GetMethod("UpdatePreview", flags);
            select.Invoke(prototype, new object[] { 0 });
            preview.Invoke(prototype, null);
            report.selectionShowsWholeGrid = Array.TrueForAll(prototype.ConstructionGridRenderers, r => r.enabled);

            Camera camera = Camera.main;
            camera.transform.SetPositionAndRotation(grid.Root.TransformPoint(new Vector3(
                report.mountainSample.x, grid.LocalBounds.max.y + 40f, report.mountainSample.z)), Quaternion.Euler(90f, 0f, 0f));
            Vector3 screen = camera.WorldToScreenPoint(grid.Root.TransformPoint(report.mountainSample));
            type.GetMethod("UpdateHoveredCell", flags).Invoke(prototype,
                new object[] { new Vector2(screen.x, Screen.height - screen.y) });
            report.mountainPickingPassed = (bool)type.GetField("hasHoveredCell", flags).GetValue(prototype) &&
                (Vector2Int)type.GetField("hoveredCell", flags).GetValue(prototype) == mountain;

            MethodInfo place = type.GetMethod("TryPlaceSelected", flags);
            int woodBefore = (int)type.GetField("wood", flags).GetValue(prototype);
            place.Invoke(prototype, new object[] { mountain });
            report.mountainBuildingRejected = (int)type.GetField("wood", flags).GetValue(prototype) == woodBefore &&
                !grid.GetTerrain(mountain).AllowsBuilding;
            place.Invoke(prototype, new object[] { outer });
            Transform placed = grid.Root.Find("居民小屋");
            grid.TryBuildingFootprint(outer, 1, 1, out Vector3 expected, out _);
            report.outerLowlandPlacementPassed = placed != null && Vector3.Distance(placed.localPosition, expected) < 0.001f &&
                (int)type.GetField("wood", flags).GetValue(prototype) == woodBefore - 20;
            if (placed != null) placed.gameObject.SetActive(false);

            Directory.CreateDirectory(Output);
            Vector3 centerOfIsland = grid.Root.TransformPoint(grid.LocalBounds.center);
            Vector3 groundCenter = new Vector3(centerOfIsland.x, 0f, centerOfIsland.z);
            float radius = Mathf.Max(grid.LocalBounds.size.x * 0.5f, grid.LocalBounds.size.z * 0.5f);
            Capture(camera, groundCenter + new Vector3(0f, 90f, -0.001f), groundCenter,
                radius * 1.12f, Path.Combine(Output, "island-grid-top.png"));
            Capture(camera, groundCenter + new Vector3(0f, 62f, -72f), groundCenter,
                radius * 0.88f, Path.Combine(Output, "island-grid-oblique.png"));
            Vector3 mountainWorld = grid.Root.TransformPoint(report.mountainSample);
            Capture(camera, mountainWorld + new Vector3(10f, 20f, -24f), mountainWorld,
                10f, Path.Combine(Output, "island-grid-mountain.png"));
            type.GetField("selectedBuildableIndex", flags).SetValue(prototype, -1);
            preview.Invoke(prototype, null);
            report.cancellationHidesWholeGrid = Array.TrueForAll(prototype.ConstructionGridRenderers, r => !r.enabled);

            report.passed = report.shaderCompiled && report.sourceResourceMatches && report.overlaysReuseExactSourceMeshes &&
                report.sourceTriangles == report.overlayTriangles && report.verticesOutsideGrid == 0 &&
                report.overlayMeshes > 0 && report.ordinaryBuildingCells > 0 && report.reservedTerrainCells > 0 &&
                report.buildingCellsOutsideOldEllipse > 0 && report.mountainPickingPassed && report.mountainBuildingRejected &&
                report.outerLowlandPlacementPassed && report.selectionShowsWholeGrid && report.cancellationHidesWholeGrid && report.noFlatHelper;
            return report;
        }

        private static void Capture(Camera camera, Vector3 position, Vector3 target, float size, string path)
        {
            camera.transform.SetPositionAndRotation(position, Quaternion.LookRotation(target - position));
            camera.orthographic = true;
            camera.orthographicSize = size;
            camera.aspect = 1600f / 1200f;
            RenderTexture texture = new RenderTexture(1600, 1200, 24, RenderTextureFormat.ARGB32);
            texture.Create();
            RenderPipeline.SubmitRenderRequest(camera, new UniversalRenderPipeline.SingleCameraRequest { destination = texture });
            RenderTexture previous = RenderTexture.active;
            RenderTexture.active = texture;
            Texture2D image = new Texture2D(texture.width, texture.height, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0, 0, texture.width, texture.height), 0, 0);
            image.Apply();
            File.WriteAllBytes(path, image.EncodeToPNG());
            RenderTexture.active = previous;
            texture.Release();
            UnityEngine.Object.Destroy(image);
            UnityEngine.Object.Destroy(texture);
        }
    }
}
