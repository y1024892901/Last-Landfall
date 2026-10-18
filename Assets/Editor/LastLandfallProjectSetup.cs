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
        private const string IslandModelPath = "Assets/LastLandfall/Resources/Models/IslandReference_V2.fbx";
        private const string IslandRootName = "IslandReference_V2";
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
                    if (child.name == "Playable Island - Reference V2" || child.name == IslandRootName)
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
            GameObject currentIsland = null;
            BuildPlacementPrototype prototype = null;
            for (int i = 0; i < roots.Length; i++)
            {
                foreach (Transform child in roots[i].GetComponentsInChildren<Transform>(true))
                    if (child.name == IslandRootName || child.name == "Playable Island - Reference V2")
                        currentIsland = child.gameObject;
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

            if (currentIsland == null)
            {
                GameObject island = (GameObject)PrefabUtility.InstantiatePrefab(islandPrefab, scene);
                island.name = IslandRootName;
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
        private const string IslandModelPath = "Assets/LastLandfall/Resources/Models/IslandReference_V2.fbx";

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
