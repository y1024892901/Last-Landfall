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
            if (pipeline == null)
            {
                UniversalRendererData renderer = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(RendererPath);
                if (renderer == null)
                {
                    renderer = ScriptableObject.CreateInstance<UniversalRendererData>();
                    AssetDatabase.CreateAsset(renderer, RendererPath);
                }

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
            if (File.Exists(ScenePath))
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
