using System.IO;
using LastLandfall.Prototype;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace LastLandfall.EditorTools
{
    /// <summary>
    /// Creates the small amount of Unity editor data needed to open and run this source-only project.
    /// This runs on the computer that has Unity installed; it does not add a setup dependency here.
    /// </summary>
    [InitializeOnLoad]
    internal static class LastLandfallProjectSetup
    {
        private const string ScenePath = "Assets/LastLandfall/Scenes/Prototype.unity";
        private const string IslandModelPath = "Assets/LastLandfall/Resources/Models/Environment/IslandReference_Gate25.fbx";
        private const string SatelliteIslandModelPath = "Assets/LastLandfall/Resources/Models/Environment/LastLandfall_Basin_TwinIslands_Gate26.fbx";
        private const string CapsizedWreckModelPath = "Assets/LastLandfall/Resources/Models/Environment/Gate26_CapsizedWreck.fbx";
        private const string GrassTexturePath = "Assets/LastLandfall/Resources/Textures/Environment/Grass_Surface_Albedo_Concept.png";
        private const string Gate25TerrainMaterialPath = "Assets/LastLandfall/Resources/Materials/Gate25Terrain.mat";
        private const string Gate25WetRockMaterialPath = "Assets/LastLandfall/Resources/Materials/Gate25WetRock.mat";
        private const string Gate25BasinWaterMaterialPath = "Assets/LastLandfall/Resources/Materials/Gate25BasinWater.mat";
        private const string IslandRootName = "Playable Island - Gate25";
        private const string SatelliteIslandRootName = "Basin Twin Islands - Gate26";
        private const string LegacyIslandRootName = "Playable Island - Reference V2";
        private const string LegacyIslandModelName = "IslandReference_V2";
        private const string IslandPrefabRootName = "IslandReference_Gate25";
        private const string PlaySpaceRootName = "Island Play Space - Rotate and Pan";
        private const string RendererPath = "Assets/LastLandfall/Settings/PrototypeRenderer.asset";
        private const string PipelinePath = "Assets/LastLandfall/Settings/PrototypePipeline.asset";
        private const string PostProcessDataPath = "Packages/com.unity.render-pipelines.universal/Runtime/Data/PostProcessData.asset";

        static LastLandfallProjectSetup()
        {
            EditorApplication.delayCall += EnsureProjectIsReady;
            EditorSceneManager.sceneOpened += OnSceneOpened;
        }

        private static void EnsureProjectIsReady()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                return;
            }

            EnsureFolders();
            EnsureUniversalRenderPipeline();
            EnsureGate25MaterialAssets();
            EnsurePrototypeScene();
            EnsureSceneIsInBuildSettings();
            AssetDatabase.SaveAssets();
            Scene activeScene = SceneManager.GetActiveScene();
            if (activeScene.path == ScenePath && !SessionState.GetBool("LastLandfall.EnvironmentPreview.V4", false))
            {
                SessionState.SetBool("LastLandfall.EnvironmentPreview.V4", true);
                EditorApplication.delayCall += () => FramePrototypeIsland(activeScene);
            }
        }

        private static void EnsureFolders()
        {
            CreateFolderIfMissing("Assets/LastLandfall", "Scenes");
            CreateFolderIfMissing("Assets/LastLandfall", "Settings");
            CreateFolderIfMissing("Assets/LastLandfall/Resources", "Materials");
            CreateFolderIfMissing("Assets/LastLandfall/Resources", "Textures");
            CreateFolderIfMissing("Assets/LastLandfall/Resources/Textures", "Environment");
        }

        private static void CreateFolderIfMissing(string parent, string folderName)
        {
            string path = parent + "/" + folderName;
            if (!AssetDatabase.IsValidFolder(path))
            {
                AssetDatabase.CreateFolder(parent, folderName);
            }
        }

        private static void EnsureUniversalRenderPipeline()
        {
            UniversalRenderPipelineAsset pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(PipelinePath);
            UniversalRendererData renderer = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(RendererPath);
            PostProcessData postProcessData = AssetDatabase.LoadAssetAtPath<PostProcessData>(PostProcessDataPath);

            if (postProcessData == null)
            {
                Debug.LogError("URP 默认 PostProcessData 资源缺失：" + PostProcessDataPath);
                return;
            }

            if (renderer == null)
            {
                renderer = ScriptableObject.CreateInstance<UniversalRendererData>();
                renderer.postProcessData = postProcessData;
                AssetDatabase.CreateAsset(renderer, RendererPath);
            }
            else if (renderer.postProcessData != postProcessData)
            {
                renderer.postProcessData = postProcessData;
                EditorUtility.SetDirty(renderer);
            }

            if (pipeline == null)
            {
                pipeline = UniversalRenderPipelineAsset.Create(renderer);
                AssetDatabase.CreateAsset(pipeline, PipelinePath);
            }

            if (GraphicsSettings.defaultRenderPipeline != pipeline)
            {
                GraphicsSettings.defaultRenderPipeline = pipeline;
            }
        }

        private static void EnsurePrototypeScene()
        {
            string sceneFilePath = Path.Combine(Application.dataPath, "LastLandfall", "Scenes", "Prototype.unity");
            if (File.Exists(sceneFilePath))
            {
                EnsureIslandInPrototypeScene();
                return;
            }

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            EditorSceneManager.SaveScene(scene, ScenePath);
            EnsureIslandInPrototypeScene();
        }

        [MenuItem("Last Landfall/Place Island in Prototype Scene")]
        private static void PlaceIslandInPrototypeSceneFromMenu()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogWarning("请先退出 Play 模式，再放置原型岛屿。");
                return;
            }

            EnsurePrototypeScene();
            AssetDatabase.SaveAssets();
        }

        [MenuItem("Last Landfall/Apply Expanded Archipelago")]
        public static void ApplyExpandedArchipelago()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogWarning("请先退出 Play 模式，再更新岛屿场景预览。");
                return;
            }
            foreach (string side in new[] { "Main", "West", "East" })
            {
                string path = "Assets/LastLandfall/Resources/Models/Environment/Island_" + side + "_Expanded.fbx";
                if (AssetDatabase.LoadAssetAtPath<GameObject>(path) == null)
                    throw new System.InvalidOperationException("扩容岛屿尚未导入：" + path);
            }
            EnsureIslandInPrototypeScene();
            AssetDatabase.SaveAssets();
            Debug.Log("EXPANDED_ARCHIPELAGO_APPLIED: main, west and east independent models saved in Prototype scene.");
        }

        [MenuItem("Last Landfall/Reload Playable Workspace")]
        public static void OpenPlayableWorkspace()
        {
            ApplyExpandedArchipelago();
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            EditorApplication.ExecuteMenuItem("Window/General/Project");
            UnityEngine.Object folder = AssetDatabase.LoadAssetAtPath<UnityEngine.Object>("Assets/LastLandfall/Resources");
            Selection.activeObject = folder;
            EditorGUIUtility.PingObject(folder);
            // A stale search filter can make an intact resource folder appear empty.
            System.Type browser = typeof(UnityEditor.Editor).Assembly.GetType("UnityEditor.ProjectBrowser");
            if (browser != null)
            {
                var window = EditorWindow.GetWindow(browser);
                var clear = browser.GetMethod("SetSearch", System.Reflection.BindingFlags.Instance |
                    System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic,
                    null, new[] { typeof(string) }, null);
                clear?.Invoke(window, new object[] { string.Empty });
                window.Repaint();
            }
            SceneView view = SceneView.lastActiveSceneView;
            if (view != null) view.LookAt(new Vector3(0f, 3f, -8f), Quaternion.Euler(45f,350f,0f), 90f);
            Debug.Log("PLAYABLE_WORKSPACE_READY: Prototype scene and Resources folder are loaded.");
        }

        [MenuItem("Last Landfall/Show Prototype Island in Scene View")]
        private static void ShowPrototypeIslandInSceneView()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogWarning("请先退出 Play 模式，再在 Scene 视图中查看原型岛屿。\n");
                return;
            }

            EnsurePrototypeScene();

            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
            {
                return;
            }

            Scene scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            FramePrototypeIsland(scene);
        }

        private static void OnSceneOpened(Scene scene, OpenSceneMode mode)
        {
            if (scene.path == ScenePath)
            {
                EditorApplication.delayCall += () => FramePrototypeIsland(scene);
            }
        }

        private static void FramePrototypeIsland(Scene scene)
        {
            if (!scene.IsValid() || !scene.isLoaded || EditorApplication.isPlayingOrWillChangePlaymode)
            {
                return;
            }

            GameObject island = null;
            GameObject[] roots = scene.GetRootGameObjects();
            for (int i = 0; i < roots.Length; i++)
            {
                foreach (Transform child in roots[i].GetComponentsInChildren<Transform>(true))
                    if (child.name == IslandRootName || child.name == LegacyIslandRootName)
                    { island = child.gameObject; break; }
                if (island != null) break;
            }

            if (island == null)
            {
                Debug.LogWarning("Prototype 场景已打开，但没有找到岛屿根对象。请使用 Last Landfall/Place Island in Prototype Scene。\n");
                return;
            }

            Selection.activeGameObject = island;
            SceneView sceneView = SceneView.lastActiveSceneView;
            if (sceneView == null)
            {
                sceneView = EditorWindow.GetWindow<SceneView>();
            }

            sceneView.cameraMode = SceneView.GetBuiltinCameraMode(DrawCameraMode.Textured);
            sceneView.showGrid = false;
            sceneView.sceneLighting = true;
            Quaternion islandViewRotation = Quaternion.Euler(36f, 350f, 0f);
            sceneView.rotation = islandViewRotation;
            sceneView.Focus();
            if (TryGetIslandVisualBounds(island, out Bounds islandBounds))
            {
                Vector3 right = islandViewRotation * Vector3.right;
                Vector3 up = islandViewRotation * Vector3.up;
                Vector3 extent = islandBounds.extents;
                float halfWidth = Mathf.Abs(right.x) * extent.x + Mathf.Abs(right.y) * extent.y +
                    Mathf.Abs(right.z) * extent.z;
                float halfHeight = Mathf.Abs(up.x) * extent.x + Mathf.Abs(up.y) * extent.y +
                    Mathf.Abs(up.z) * extent.z;
                float aspect = sceneView.camera != null
                    ? Mathf.Max(0.1f, sceneView.camera.aspect)
                    : 1.6f;
                float frameSize = Mathf.Max(halfHeight, halfWidth / aspect) * 1.18f;
                sceneView.LookAt(islandBounds.center, islandViewRotation, frameSize, true, true);
            }
            else sceneView.FrameSelected();
            sceneView.Repaint();
        }

        private static bool TryGetIslandVisualBounds(GameObject islandRoot, out Bounds bounds)
        {
            bounds = default;
            bool hasBounds = false;
            if (islandRoot == null) return false;

            foreach (Renderer renderer in islandRoot.GetComponentsInChildren<Renderer>(true))
            {
                if (renderer == null || !renderer.enabled) continue;
                if (!hasBounds)
                {
                    bounds = renderer.bounds;
                    hasBounds = true;
                }
                else
                {
                    bounds.Encapsulate(renderer.bounds);
                }
            }

            return hasBounds;
        }

        private static void FrameGameCameraToIslandGroup(Scene scene, GameObject islandRoot)
        {
            if (!TryGetIslandVisualBounds(islandRoot, out Bounds islandBounds)) return;

            Camera gameCamera = null;
            foreach (GameObject root in scene.GetRootGameObjects())
            {
                gameCamera = root.GetComponentInChildren<Camera>(true);
                if (gameCamera != null) break;
            }
            if (gameCamera == null) return;

            Quaternion rotation = Quaternion.Euler(36f, 350f, 0f);
            Vector3 right = rotation * Vector3.right;
            Vector3 up = rotation * Vector3.up;
            Vector3 extent = islandBounds.extents;
            float halfWidth = Mathf.Abs(right.x) * extent.x + Mathf.Abs(right.y) * extent.y +
                Mathf.Abs(right.z) * extent.z;
            float halfHeight = Mathf.Abs(up.x) * extent.x + Mathf.Abs(up.y) * extent.y +
                Mathf.Abs(up.z) * extent.z;
            float aspect = Mathf.Max(0.1f, gameCamera.aspect);
            gameCamera.orthographic = true;
            gameCamera.orthographicSize = Mathf.Max(halfHeight, halfWidth / aspect) * 1.18f;

            float distance = Mathf.Max(72f, islandBounds.size.magnitude * 1.4f);
            gameCamera.transform.SetPositionAndRotation(
                islandBounds.center - rotation * Vector3.forward * distance,
                rotation);
            EditorUtility.SetDirty(gameCamera);
            EditorUtility.SetDirty(gameCamera.transform);
        }

        internal static void EnsureIslandInPrototypeScene()
        {
            if (EditorApplication.isPlaying || EditorApplication.isPlayingOrWillChangePlaymode) return;
            Scene scene = SceneManager.GetSceneByPath(ScenePath);
            bool openedForSetup = !scene.IsValid() || !scene.isLoaded;
            if (openedForSetup)
            {
                scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Additive);
            }

            GameObject[] roots = scene.GetRootGameObjects();
            GameObject previewRoot = null;
            GameObject legacyModel = null;
            Transform playSpace = null;
            BuildPlacementPrototype prototype = null;
            for (int i = 0; i < roots.Length; i++)
            {
                foreach (Transform child in roots[i].GetComponentsInChildren<Transform>(true))
                {
                    if (child.name == IslandRootName || child.name == LegacyIslandRootName)
                        previewRoot = child.gameObject;
                    else if (child.name == LegacyIslandModelName)
                        legacyModel = child.gameObject;
                    else if (child.name == PlaySpaceRootName)
                        playSpace = child;
                }
                if (prototype == null) prototype = roots[i].GetComponentInChildren<BuildPlacementPrototype>(true);
            }

            const string expandedDirectory = "Assets/LastLandfall/Resources/Models/Environment/";
            GameObject expandedMain = AssetDatabase.LoadAssetAtPath<GameObject>(expandedDirectory + "Island_Main_Expanded.fbx");
            GameObject expandedWest = AssetDatabase.LoadAssetAtPath<GameObject>(expandedDirectory + "Island_West_Expanded.fbx");
            GameObject expandedEast = AssetDatabase.LoadAssetAtPath<GameObject>(expandedDirectory + "Island_East_Expanded.fbx");
            bool expanded = expandedMain != null && expandedWest != null && expandedEast != null;
            GameObject islandPrefab = expanded ? expandedMain : AssetDatabase.LoadAssetAtPath<GameObject>(IslandModelPath);
            if (islandPrefab == null)
            {
                Debug.LogWarning("岛屿 FBX 尚未导入，稍后打开项目时会重试：" + IslandModelPath);
                if (openedForSetup)
                {
                    EditorSceneManager.CloseScene(scene, true);
                }
                return;
            }

            EnsureGate25MaterialAssets();

            if (previewRoot == null)
            {
                previewRoot = new GameObject(IslandRootName);
                SceneManager.MoveGameObjectToScene(previewRoot, scene);
                if (playSpace != null)
                    previewRoot.transform.SetParent(playSpace, false);
                previewRoot.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);
            }
            else
            {
                previewRoot.name = IslandRootName;
            }

            if (legacyModel != null && legacyModel.transform.parent != previewRoot.transform)
                UnityEngine.Object.DestroyImmediate(legacyModel);

            previewRoot.transform.localPosition = Vector3.zero;
            previewRoot.transform.localScale = Vector3.one;
            for (int childIndex = previewRoot.transform.childCount - 1; childIndex >= 0; childIndex--)
                UnityEngine.Object.DestroyImmediate(previewRoot.transform.GetChild(childIndex).gameObject);

            GameObject island = (GameObject)PrefabUtility.InstantiatePrefab(islandPrefab, previewRoot.transform);
            if (island != null)
            {
                island.name = IslandPrefabRootName;
                ApplyGate25PreviewMaterials(island);
            }

            GameObject satelliteIslands = null;
            GameObject satelliteIslandPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(SatelliteIslandModelPath);
            if (expanded)
            {
                satelliteIslands = new GameObject(SatelliteIslandRootName);
                satelliteIslands.transform.SetParent(previewRoot.transform, false);
                foreach (GameObject prefab in new[] { expandedWest, expandedEast })
                {
                    GameObject child = (GameObject)PrefabUtility.InstantiatePrefab(prefab, satelliteIslands.transform);
                    ApplyGate25PreviewMaterials(child);
                }
            }
            else if (satelliteIslandPrefab != null)
            {
                satelliteIslands = (GameObject)PrefabUtility.InstantiatePrefab(
                    satelliteIslandPrefab, previewRoot.transform);
                if (satelliteIslands != null)
                {
                    satelliteIslands.name = SatelliteIslandRootName;
                    ApplyGate25PreviewMaterials(satelliteIslands);
                }
            }
            else
            {
                Debug.LogWarning("Gate26 双子岛 FBX 尚未导入，稍后打开项目时会重试：" + SatelliteIslandModelPath);
            }

            GameObject capsizedWreckPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(expanded
                ? expandedDirectory + "Gate26_CapsizedWreck_Expanded.fbx" : CapsizedWreckModelPath);
            if (capsizedWreckPrefab != null)
            {
                GameObject wreckComposite = (GameObject)PrefabUtility.InstantiatePrefab(
                    capsizedWreckPrefab, previewRoot.transform);
                if (wreckComposite != null)
                {
                    wreckComposite.name = "Capsized Wreck - Gate26 East Shore";
                    int wreckRendererCount = IsolateCapsizedWreckRenderers(wreckComposite);
                    if (wreckRendererCount == 0)
                    {
                        wreckComposite.SetActive(false);
                        Debug.LogWarning("Gate26 废弃船 FBX 未找到 Wreck_ 或 Debris_ 网格，已在编辑器预览中隐藏组合模型，避免重复显示副岛。");
                    }
                    else
                    {
                        int hiddenVegetationCount = ClearVegetationFromWreckFootprint(
                            satelliteIslands, wreckComposite);
                        Debug.Log($"Gate26 wreck preview cleared {hiddenVegetationCount} overlapping vegetation renderers.");
                    }
                }
            }
            else
            {
                Debug.LogWarning("Gate26 废弃船 FBX 尚未导入，稍后打开项目时会重试：" + CapsizedWreckModelPath);
            }

            if (prototype == null)
            {
                GameObject host = new GameObject("Last Landfall - Build Prototype");
                SceneManager.MoveGameObjectToScene(host, scene);
                prototype = host.AddComponent<BuildPlacementPrototype>();
            }
            EnsureLighthousePreview(scene);
            PersistEnvironmentAssets(scene);
            FrameGameCameraToIslandGroup(scene, previewRoot);
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene, ScenePath);

            if (openedForSetup)
            {
                EditorSceneManager.CloseScene(scene, true);
            }
        }

        private static void EnsureLighthousePreview(Scene scene)
        {
            foreach (GameObject root in scene.GetRootGameObjects())
                if (root.name == "Lighthouse | Scene Preview") UnityEngine.Object.DestroyImmediate(root);
            var reef = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/LastLandfall/Resources/Models/Lighthouse/Lighthouse_Reef.fbx");
            var stage = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/LastLandfall/Resources/Models/Lighthouse/Lighthouse_Stage_0.fbx");
            if (reef == null || stage == null) return;
            var site = new GameObject("Lighthouse | Scene Preview");
            SceneManager.MoveGameObjectToScene(site, scene);
            site.transform.position = LastLandfall.Prototype.LighthouseSite.SitePosition;
            foreach (var prefab in new[] { reef, stage })
            {
                var model = (GameObject)PrefabUtility.InstantiatePrefab(prefab, site.transform);
                LastLandfall.Prototype.LighthouseSite.ConvertMaterials(model);
                foreach (var renderer in model.GetComponentsInChildren<Renderer>())
                    PrefabUtility.RecordPrefabInstancePropertyModifications(renderer);
            }
        }

        private static int IsolateCapsizedWreckRenderers(GameObject wreckComposite)
        {
            int wreckRendererCount = 0;
            foreach (Renderer renderer in wreckComposite.GetComponentsInChildren<Renderer>(true))
            {
                string objectName = renderer.gameObject.name;
                bool isWreckPiece = objectName.StartsWith("Wreck_", System.StringComparison.OrdinalIgnoreCase) ||
                    objectName.StartsWith("Debris_", System.StringComparison.OrdinalIgnoreCase);
                renderer.enabled = isWreckPiece;
                if (isWreckPiece) wreckRendererCount++;
                PrefabUtility.RecordPrefabInstancePropertyModifications(renderer);
            }

            return wreckRendererCount;
        }

        private static int ClearVegetationFromWreckFootprint(GameObject satelliteIslands, GameObject wreckComposite)
        {
            if (satelliteIslands == null || wreckComposite == null) return 0;

            Bounds footprint = default;
            bool hasFootprint = false;
            Renderer[] wreckRenderers = wreckComposite.GetComponentsInChildren<Renderer>(true);
            for (int i = 0; i < wreckRenderers.Length; i++)
            {
                Renderer renderer = wreckRenderers[i];
                if (renderer == null || !renderer.enabled) continue;
                string name = renderer.gameObject.name;
                if (!name.StartsWith("Wreck_", System.StringComparison.OrdinalIgnoreCase) &&
                    !name.StartsWith("Debris_", System.StringComparison.OrdinalIgnoreCase)) continue;

                if (!hasFootprint)
                {
                    footprint = renderer.bounds;
                    hasFootprint = true;
                }
                else
                {
                    footprint.Encapsulate(renderer.bounds);
                }
            }

            if (!hasFootprint) return 0;

            const float clearance = 0.85f;
            footprint.Expand(new Vector3(clearance * 2f, 0f, clearance * 2f));
            Renderer[] environmentRenderers = satelliteIslands.GetComponentsInChildren<Renderer>(true);
            int hiddenCount = 0;
            for (int i = 0; i < environmentRenderers.Length; i++)
            {
                Renderer vegetation = environmentRenderers[i];
                if (vegetation == null || !vegetation.enabled ||
                    !IsWreckSiteVegetation(vegetation.gameObject.name)) continue;

                Bounds bounds = vegetation.bounds;
                bool overlaps = bounds.max.x >= footprint.min.x && bounds.min.x <= footprint.max.x &&
                    bounds.max.z >= footprint.min.z && bounds.min.z <= footprint.max.z;
                if (!overlaps) continue;

                vegetation.enabled = false;
                PrefabUtility.RecordPrefabInstancePropertyModifications(vegetation);
                hiddenCount++;
            }

            return hiddenCount;
        }

        private static bool IsWreckSiteVegetation(string objectName)
        {
            if (string.IsNullOrEmpty(objectName)) return false;
            string name = objectName.ToLowerInvariant();
            if (name.StartsWith("grounded detail |")) return false;
            return name.Contains("tree") || name.Contains("pine") || name.Contains("broadleaf") ||
                name.Contains("grass") || name.Contains("shrub") || name.Contains("fern") ||
                name.Contains("wildflower") || name.Contains("flower") || name.Contains("foliage") ||
                name.Contains("reed");
        }

        private static void EnsureGate25MaterialAssets()
        {
            if (!AssetDatabase.IsValidFolder("Assets/LastLandfall/Resources/Materials"))
                CreateFolderIfMissing("Assets/LastLandfall/Resources", "Materials");

            Texture2D grassAlbedo = AssetDatabase.LoadAssetAtPath<Texture2D>(GrassTexturePath);
            Material terrain = GetOrCreateMaterial(Gate25TerrainMaterialPath,
                "Gate25 Terrain", Shader.Find("LastLandfall/Reference Island Terrain"));
            if (terrain != null)
            {
                terrain.SetColor("_BaseColor", Color.white);
                terrain.SetColor("_AccentColor", Color.white);
                terrain.SetColor("_MineralColor", Color.white);
                terrain.SetFloat("_MacroScale", 0.55f);
                terrain.SetFloat("_DetailScale", 4.6f);
                terrain.SetFloat("_MicroScale", 32f);
                terrain.SetFloat("_LayerScale", 2.2f);
                terrain.SetFloat("_ColorVariation", 0.0f);
                terrain.SetFloat("_StrataStrength", 0.02f);
                terrain.SetFloat("_NormalStrength", 0.0f);
                terrain.SetFloat("_Smoothness", 0.08f);
                terrain.SetFloat("_VertexColorWeight", 1.0f);
                if (terrain.HasProperty("_BaseMap") && grassAlbedo != null)
                    terrain.SetTexture("_BaseMap", grassAlbedo);
                if (terrain.HasProperty("_TextureWeight"))
                    terrain.SetFloat("_TextureWeight", grassAlbedo != null ? 0.10f : 0.0f);
                EditorUtility.SetDirty(terrain);
                LastLandfall.Prototype.TerrainSurfaceLibrary.Configure(terrain);
                terrain.SetFloat("_LandscapeBlend", 1f);
            }

            Material wetRock = GetOrCreateMaterial(Gate25WetRockMaterialPath,
                "Gate25 Wet Rock", Shader.Find("LastLandfall/Reference Island Terrain"));
            if (wetRock != null)
            {
                wetRock.SetColor("_BaseColor", new Color(0.12f, 0.17f, 0.18f));
                wetRock.SetColor("_AccentColor", new Color(0.23f, 0.27f, 0.28f));
                wetRock.SetColor("_MineralColor", new Color(0.34f, 0.38f, 0.37f));
                wetRock.SetFloat("_MacroScale", 0.55f);
                wetRock.SetFloat("_DetailScale", 4.6f);
                wetRock.SetFloat("_MicroScale", 32f);
                wetRock.SetFloat("_LayerScale", 2.2f);
                wetRock.SetFloat("_ColorVariation", 0.62f);
                wetRock.SetFloat("_StrataStrength", 0.08f);
                wetRock.SetFloat("_NormalStrength", 0.25f);
                wetRock.SetFloat("_Smoothness", 0.32f);
                wetRock.SetFloat("_VertexColorWeight", 0.0f);
                if (wetRock.HasProperty("_TextureWeight")) wetRock.SetFloat("_TextureWeight", 0.0f);
                EditorUtility.SetDirty(wetRock);
            }

            Material water = GetOrCreateMaterial(Gate25BasinWaterMaterialPath,
                "Gate25 Basin Water", Shader.Find("LastLandfall/Basin Water"));
            if (water != null)
            {
                if (water.HasProperty("_Tint")) water.SetColor("_Tint", Color.white);
                if (water.HasProperty("_FlowSpeed")) water.SetFloat("_FlowSpeed", 0.12f);
                if (water.HasProperty("_RippleStrength")) water.SetFloat("_RippleStrength", 0.025f);
                EditorUtility.SetDirty(water);
            }
        }

        private static Material GetOrCreateMaterial(string path, string materialName, Shader shader)
        {
            if (shader == null) return null;
            Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                material = new Material(shader) { name = materialName };
                AssetDatabase.CreateAsset(material, path);
            }
            else if (material.shader != shader)
            {
                material.shader = shader;
            }
            return material;
        }

        private static void ApplyGate25PreviewMaterials(GameObject island)
        {
            Material terrain = AssetDatabase.LoadAssetAtPath<Material>(Gate25TerrainMaterialPath);
            Material wetRock = AssetDatabase.LoadAssetAtPath<Material>(Gate25WetRockMaterialPath);
            Material water = AssetDatabase.LoadAssetAtPath<Material>(Gate25BasinWaterMaterialPath);
            foreach (Renderer renderer in island.GetComponentsInChildren<Renderer>(true))
            {
                string objectName = renderer.gameObject.name;
                if (objectName.IndexOf("terrain source", System.StringComparison.OrdinalIgnoreCase) >= 0 &&
                    terrain != null)
                {
                    MeshFilter filter = renderer.GetComponent<MeshFilter>();
                    int count = filter != null && filter.sharedMesh != null
                        ? Mathf.Max(1, filter.sharedMesh.subMeshCount)
                        : Mathf.Max(1, renderer.sharedMaterials.Length);
                    Material[] materials = new Material[count];
                    for (int i = 0; i < materials.Length; i++)
                        materials[i] = i == 1 && wetRock != null ? wetRock : terrain;
                    renderer.sharedMaterials = materials;
                    PrefabUtility.RecordPrefabInstancePropertyModifications(renderer);
                }
                else if (water != null && objectName.IndexOf("Basin_", System.StringComparison.OrdinalIgnoreCase) >= 0 &&
                         objectName.IndexOf("Water", System.StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    Material[] materials = renderer.sharedMaterials;
                    if (materials.Length == 0) materials = new Material[1];
                    for (int i = 0; i < materials.Length; i++) materials[i] = water;
                    renderer.sharedMaterials = materials;
                    PrefabUtility.RecordPrefabInstancePropertyModifications(renderer);
                }
            }
        }

        private static void PersistEnvironmentAssets(Scene scene)
        {
            const string folder = "Assets/LastLandfall/Settings/SceneEnvironment";
            CreateFolderIfMissing("Assets/LastLandfall/Settings", "SceneEnvironment");
            foreach (GameObject root in scene.GetRootGameObjects())
            {
                if (root.name != "Island Play Space - Rotate and Pan") continue;
                foreach (MeshFilter filter in root.GetComponentsInChildren<MeshFilter>(true))
                {
                    Mesh mesh = filter.sharedMesh;
                    if (mesh != null && !AssetDatabase.Contains(mesh))
                    {
                        string path = folder + "/FloodwaterMesh.asset";
                        Mesh saved = AssetDatabase.LoadAssetAtPath<Mesh>(path);
                        if (saved == null) AssetDatabase.CreateAsset(mesh, path);
                        else
                        {
                            EditorUtility.CopySerialized(mesh, saved);
                            EditorUtility.SetDirty(saved);
                            filter.sharedMesh = saved;
                            UnityEngine.Object.DestroyImmediate(mesh);
                        }
                    }
                    MeshRenderer renderer = filter.GetComponent<MeshRenderer>();
                    if (renderer == null) continue;
                    Material[] materials = renderer.sharedMaterials;
                    for (int i = 0; i < materials.Length; i++)
                    {
                        Material material = materials[i];
                        if (material == null || AssetDatabase.Contains(material)) continue;
                        string path = folder + "/" + material.name.Replace("|", "-") + ".mat";
                        Material saved = AssetDatabase.LoadAssetAtPath<Material>(path);
                        if (saved == null) AssetDatabase.CreateAsset(material, path);
                        else
                        {
                            EditorUtility.CopySerialized(material, saved);
                            EditorUtility.SetDirty(saved);
                            materials[i] = saved;
                            UnityEngine.Object.DestroyImmediate(material);
                        }
                    }
                    renderer.sharedMaterials = materials;
                }
            }
        }

        private static void EnsureSceneIsInBuildSettings()
        {
            EditorBuildSettingsScene[] currentScenes = EditorBuildSettings.scenes;
            for (int i = 0; i < currentScenes.Length; i++)
            {
                if (currentScenes[i].path == ScenePath)
                {
                    return;
                }
            }

            var updatedScenes = new EditorBuildSettingsScene[currentScenes.Length + 1];
            for (int i = 0; i < currentScenes.Length; i++)
            {
                updatedScenes[i] = currentScenes[i];
            }

            updatedScenes[currentScenes.Length] = new EditorBuildSettingsScene(ScenePath, true);
            EditorBuildSettings.scenes = updatedScenes;
        }
    }

    /// <summary>
    /// Asset import order is not guaranteed on first project open. Retry scene placement
    /// after Unity has finished importing the island FBX.
    /// </summary>
    internal sealed class IslandSceneModelPostprocessor : AssetPostprocessor
    {
        private const string IslandModelPath = "Assets/LastLandfall/Resources/Models/Environment/IslandReference_Gate25.fbx";

        private static void OnPostprocessAllAssets(string[] importedAssets, string[] deletedAssets,
            string[] movedAssets, string[] movedFromAssetPaths)
        {
            for (int i = 0; i < importedAssets.Length; i++)
            {
                if (importedAssets[i] == IslandModelPath)
                {
                    EditorApplication.delayCall += LastLandfallProjectSetup.EnsureIslandInPrototypeScene;
                    return;
                }
            }
        }
    }
}
// Trigger Unity asset refresh.
