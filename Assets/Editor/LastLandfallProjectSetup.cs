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
        private const string GrassTexturePath = "Assets/LastLandfall/Resources/Textures/Environment/Grass_Surface_Albedo_Concept.png";
        private const string Gate25TerrainMaterialPath = "Assets/LastLandfall/Resources/Materials/Gate25Terrain.mat";
        private const string Gate25WetRockMaterialPath = "Assets/LastLandfall/Resources/Materials/Gate25WetRock.mat";
        private const string Gate25BasinWaterMaterialPath = "Assets/LastLandfall/Resources/Materials/Gate25BasinWater.mat";
        private const string IslandRootName = "Playable Island - Gate25";
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
            if (activeScene.path == ScenePath && !SessionState.GetBool("LastLandfall.EnvironmentPreview.V3", false))
            {
                SessionState.SetBool("LastLandfall.EnvironmentPreview.V3", true);
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
            sceneView.rotation = Quaternion.Euler(36f, 350f, 0f);
            sceneView.Focus();
            Camera gameCamera = null;
            foreach (GameObject root in roots)
            {
                gameCamera = root.GetComponentInChildren<Camera>();
                if (gameCamera != null) break;
            }
            if (gameCamera != null)
            {
                Renderer islandRenderer = island.GetComponentInChildren<Renderer>();
                float height = islandRenderer != null ? islandRenderer.bounds.center.y : 0f;
                float directionY = gameCamera.transform.forward.y;
                float distance = Mathf.Abs(directionY) > 0.001f
                    ? Mathf.Max(1f, (height - gameCamera.transform.position.y) / directionY) : 72f;
                sceneView.LookAt(gameCamera.transform.position + gameCamera.transform.forward * distance,
                    gameCamera.transform.rotation, gameCamera.orthographicSize, true, true);
            }
            else sceneView.FrameSelected();
            sceneView.Repaint();
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

            GameObject islandPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(IslandModelPath);
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

            if (prototype == null)
            {
                GameObject host = new GameObject("Last Landfall - Build Prototype");
                SceneManager.MoveGameObjectToScene(host, scene);
                prototype = host.AddComponent<BuildPlacementPrototype>();
            }
            PersistEnvironmentAssets(scene);
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene, ScenePath);

            if (openedForSetup)
            {
                EditorSceneManager.CloseScene(scene, true);
            }
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
