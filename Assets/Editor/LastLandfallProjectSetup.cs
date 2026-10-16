using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

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
        private const string RendererPath = "Assets/LastLandfall/Settings/PrototypeRenderer.asset";
        private const string PipelinePath = "Assets/LastLandfall/Settings/PrototypePipeline.asset";
        private const string PostProcessDataPath = "Packages/com.unity.render-pipelines.universal/Runtime/Data/PostProcessData.asset";

        static LastLandfallProjectSetup()
        {
            EditorApplication.delayCall += EnsureProjectIsReady;
        }

        private static void EnsureProjectIsReady()
        {
            EnsureFolders();
            EnsureUniversalRenderPipeline();
            EnsurePrototypeScene();
            EnsureSceneIsInBuildSettings();
            AssetDatabase.SaveAssets();
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
                return;
            }

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            EditorSceneManager.SaveScene(scene, ScenePath);
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
}
