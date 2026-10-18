using System;
using System.IO;
using System.Reflection;
using LastLandfall.Prototype;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace LastLandfall.EditorTools
{
    public static class MainMenuValidation
    {
        private const string RequestKey = "LastLandfall.MainMenu.PreviewRequested";
        private const string Output = "work/main_menu";
        private static double captureAt;

        [Serializable]
        private sealed class Report
        {
            public bool passed, worldArtworkLoaded, shaderCompiled, startsOnHome;
            public bool settingsOpenAndClose, animationCanBeDisabled, startEntersGame;
            public bool returnPreservesIsland, resumeEntersGame, backgroundChangesOverTime;
            public float meanPixelChange;
            public string screenshot;
        }

        [MenuItem("Last Landfall/Preview and Validate Main Menu")]
        public static void PreviewAndValidate()
        {
            if (!EditorApplication.isPlaying)
            {
                SessionState.SetBool(RequestKey, true);
                EditorApplication.EnterPlaymode();
                ResumePreview();
                return;
            }
            Run();
        }

        [InitializeOnLoadMethod]
        private static void ResumePreview()
        {
            if (!SessionState.GetBool(RequestKey, false)) return;
            EditorApplication.update -= WaitForRuntime;
            EditorApplication.update += WaitForRuntime;
        }

        private static void WaitForRuntime()
        {
            if (!EditorApplication.isPlaying || UnityEngine.Object.FindAnyObjectByType<BuildPlacementPrototype>() == null) return;
            EditorApplication.update -= WaitForRuntime;
            SessionState.SetBool(RequestKey, false);
            Run();
        }

        private static void Run()
        {
            BuildPlacementPrototype prototype = UnityEngine.Object.FindAnyObjectByType<BuildPlacementPrototype>();
            if (prototype == null) throw new InvalidOperationException("Play the prototype before previewing the main menu.");
            MainMenuController menu = UnityEngine.Object.FindAnyObjectByType<MainMenuController>();
            if (menu == null) menu = new GameObject("Last Landfall | Main Menu").AddComponent<MainMenuController>();
            if (!menu.IsInitialized) menu.Initialize(Camera.main, null);
            bool originalStarted = menu.HasStarted;
            bool originalMotion = menu.MotionEnabled;
            menu.ShowHome();
            Report report = new Report
            {
                startsOnHome = menu.IsBlocking && !menu.IsEntering,
                worldArtworkLoaded = menu.Artwork == Resources.Load<Texture2D>("UI/MainMenuWorld"),
                screenshot = Path.GetFullPath(Path.Combine(Output, "main-menu.png"))
            };
            Shader shader = menu.BackdropMaterial.shader;
            report.shaderCompiled = shader.isSupported && !ShaderUtil.ShaderHasError(shader);
            menu.OpenSettings();
            bool opened = menu.IsSettingsOpen;
            menu.CloseSettings();
            report.settingsOpenAndClose = opened && !menu.IsSettingsOpen && menu.IsBlocking;
            menu.SetMotionEnabled(false);
            menu.SendMessage("Update");
            float clock = menu.BackdropMaterial.GetFloat("_AnimationTime");
            menu.SendMessage("Update");
            report.animationCanBeDisabled = !menu.MotionEnabled && Mathf.Approximately(clock, menu.BackdropMaterial.GetFloat("_AnimationTime"));
            Color32[] first = CaptureBackdrop(menu, 0f);
            Color32[] second = CaptureBackdrop(menu, 8f);
            double difference = 0;
            for (int i = 0; i < first.Length; i++)
                difference += Math.Abs(first[i].r - second[i].r) + Math.Abs(first[i].g - second[i].g) + Math.Abs(first[i].b - second[i].b);
            report.meanPixelChange = (float)(difference / (first.Length * 3));
            report.backgroundChangesOverTime = report.meanPixelChange > 0.15f;
            IslandConstructionGrid grid = prototype.ConstructionGrid;
            int children = grid.Root.childCount;
            menu.BeginGame(false);
            report.startEntersGame = !menu.IsBlocking && menu.HasStarted;
            menu.ShowHome();
            report.returnPreservesIsland = menu.IsBlocking && prototype.ConstructionGrid == grid && grid.Root.childCount == children;
            menu.BeginGame(false);
            report.resumeEntersGame = !menu.IsBlocking;
            // Restore the initial preview state after exercising entry and resume.
            typeof(MainMenuController).GetField("hasStarted", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(menu, originalStarted);
            menu.SetMotionEnabled(originalMotion);
            menu.ShowHome();
            report.passed = report.worldArtworkLoaded && report.shaderCompiled && report.startsOnHome &&
                report.settingsOpenAndClose && report.animationCanBeDisabled && report.startEntersGame &&
                report.returnPreservesIsland && report.resumeEntersGame && report.backgroundChangesOverTime;
            Directory.CreateDirectory(Output);
            File.WriteAllText(Path.Combine(Output, "validation.json"), JsonUtility.ToJson(report, true));
            Debug.Log("MAIN_MENU_VALIDATION " + JsonUtility.ToJson(report));
            Type gameView = typeof(Editor).Assembly.GetType("UnityEditor.GameView");
            EditorWindow window = EditorWindow.GetWindow(gameView);
            window.Focus();
            window.maximized = true;
            captureAt = EditorApplication.timeSinceStartup + 1.5;
            EditorApplication.update -= CaptureMenuFrame;
            EditorApplication.update += CaptureMenuFrame;
        }

        private static void CaptureMenuFrame()
        {
            if (EditorApplication.timeSinceStartup < captureAt) return;
            EditorApplication.update -= CaptureMenuFrame;
            Type type = typeof(Editor).Assembly.GetType("UnityEditor.GameView");
            EditorWindow window = EditorWindow.GetWindow(type);
            BindingFlags flags = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;
            RenderTexture target = type.GetProperty("targetTexture", flags)?.GetValue(window) as RenderTexture;
            if (target == null) target = type.GetField("m_TargetTexture", flags)?.GetValue(window) as RenderTexture;
            for (Type parent = type; target == null && parent != null; parent = parent.BaseType)
            {
                foreach (FieldInfo field in parent.GetFields(flags | BindingFlags.DeclaredOnly))
                {
                    if (!typeof(RenderTexture).IsAssignableFrom(field.FieldType)) continue;
                    target = field.GetValue(window) as RenderTexture;
                    if (target != null && target.IsCreated()) break;
                    target = null;
                }
            }
            if (target == null) { Debug.LogWarning("Game view render target unavailable for screenshot."); return; }
            RenderTexture previous = RenderTexture.active;
            RenderTexture.active = target;
            Texture2D image = new Texture2D(target.width, target.height, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0, 0, target.width, target.height), 0, 0);
            image.Apply();
            File.WriteAllBytes(Path.Combine(Output, "main-menu.png"), image.EncodeToPNG());
            RenderTexture.active = previous;
            UnityEngine.Object.DestroyImmediate(image);
        }

        private static Color32[] CaptureBackdrop(MainMenuController menu, float time)
        {
            menu.BackdropMaterial.SetFloat("_AnimationTime", time);
            Camera camera = Camera.main;
            RenderTexture target = new RenderTexture(320, 180, 24);
            target.Create();
            RenderPipeline.SubmitRenderRequest(camera, new UniversalRenderPipeline.SingleCameraRequest { destination = target });
            RenderTexture old = RenderTexture.active;
            RenderTexture.active = target;
            Texture2D image = new Texture2D(320, 180, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0, 0, 320, 180), 0, 0);
            image.Apply();
            Color32[] pixels = image.GetPixels32();
            RenderTexture.active = old;
            target.Release();
            UnityEngine.Object.DestroyImmediate(image);
            UnityEngine.Object.DestroyImmediate(target);
            return pixels;
        }
    }
}
