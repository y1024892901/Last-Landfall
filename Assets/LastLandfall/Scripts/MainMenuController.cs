using System;
using UnityEngine;

namespace LastLandfall.Prototype
{
    // The world panorama belongs to the game as a whole, not to a specific map.
    public sealed class MainMenuController : MonoBehaviour
    {
        private const int MenuLayer = 30;
        private enum Page { Home, Pause, Settings, Quit }
        private Camera sceneCamera;
        private BuildPlacementPrototype gameplay;
        private Action beginSettlement;
        private GameObject backdrop;
        private Material backdropMaterial;
        private Texture2D homeArtwork;
        private int gameplayMask;
        private bool initialized, entering, hasStarted;
        private bool hasPausedTime;
        private float pausedTimeScale = 1f;
        private float entryTime, animationTime;
        private bool motionEnabled;
        private bool fullscreen, confirmReturnToTitle = true, showConstructionGrid = true;
        private int qualityLevel, frameLimitIndex;
        private bool verticalSync;
        private float pushStrength = 1f, oceanStrength = 1f, mistStrength = 1f, masterVolume = 1f;
        private static readonly int[] FrameLimits = { 30, 60, 120, -1 };
        private const string SettingsPrefix = "LastLandfall.Settings.";
        private int selectedItem, selectedSettingsTab, openedFrame;
        private Page page, settingsReturnPage = Page.Home;
        private Font titleFont, interfaceFont;
        private GUIStyle kicker, lastTitle, landfallTitle, subtitle, body, small, buttonText, settingsHeading, pauseTitle;
        private GUIStyle emptyButton;
        private static readonly Color Ivory = new Color(0.91f, 0.92f, 0.88f);
        private static readonly Color Gold = new Color(0.72f, 0.61f, 0.40f);
        private static readonly Color Muted = new Color(0.57f, 0.65f, 0.68f);
        public bool IsBlocking { get; private set; }
        public bool IsInitialized => initialized;
        public bool IsEntering => entering;
        public bool HasStarted => hasStarted;
        public bool IsSettingsOpen => page == Page.Settings;
        public bool MotionEnabled => motionEnabled;
        public Material BackdropMaterial => backdropMaterial;
        public Texture Artwork => backdropMaterial != null ? backdropMaterial.mainTexture : null;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void CreateTitleScreen()
        {
            if (FindAnyObjectByType<MainMenuController>() == null)
                new GameObject("Last Landfall | Main Menu").AddComponent<MainMenuController>();
        }

        private void Start()
        {
            if (!initialized && Camera.main != null) Initialize(Camera.main, null);
        }

        public void Initialize(Camera camera, Action onBegin)
        {
            sceneCamera = camera;
            gameplay = FindAnyObjectByType<BuildPlacementPrototype>();
            beginSettlement = onBegin;
            gameplayMask = camera.cullingMask & ~(1 << MenuLayer);
            motionEnabled = PlayerPrefs.GetInt("LastLandfall.MenuMotion", 1) != 0;
            LoadSettings();
            homeArtwork = Resources.Load<Texture2D>("UI/MainMenuWorld");
            Shader shader = Shader.Find("LastLandfall/Main Menu World");
            if (homeArtwork == null || shader == null)
            {
                Debug.LogError("首页世界主视觉或动态背景着色器缺失。");
                IsBlocking = false;
                return;
            }
            backdropMaterial = new Material(shader) { mainTexture = homeArtwork };
            backdrop = GameObject.CreatePrimitive(PrimitiveType.Quad);
            backdrop.name = "Main Menu | Flooded World Panorama";
            backdrop.layer = MenuLayer;
            Destroy(backdrop.GetComponent<Collider>());
            backdrop.transform.SetParent(camera.transform, false);
            backdrop.GetComponent<Renderer>().sharedMaterial = backdropMaterial;
            initialized = true;
            ShowHome();
            UpdateBackdrop();
        }

        public void ShowHome()
        {
            if (!initialized) return;
            IsBlocking = true;
            entering = false;
            page = Page.Home;
            settingsReturnPage = Page.Home;
            backdropMaterial.mainTexture = homeArtwork;
            selectedItem = 0;
            openedFrame = Time.frameCount;
            backdrop.SetActive(true);
            backdropMaterial.SetFloat("_Opacity", 1f);
            sceneCamera.cullingMask = 1 << MenuLayer;
            if (gameplay != null)
            {
                gameplay.enabled = false;
                if (gameplay.ConstructionGridRenderers != null)
                    foreach (Renderer grid in gameplay.ConstructionGridRenderers) grid.enabled = false;
            }
        }

        public void BeginGame(bool animated = true)
        {
            if (!initialized || entering || !IsBlocking) return;
            if (!hasStarted) beginSettlement?.Invoke();
            hasStarted = true;
            entering = true;
            entryTime = Time.unscaledTime;
            sceneCamera.cullingMask = gameplayMask | (1 << MenuLayer);
            if (!animated) FinishEntry();
        }

        private void FinishEntry()
        {
            entering = false;
            IsBlocking = false;
            backdrop.SetActive(false);
            sceneCamera.cullingMask = gameplayMask;
            if (gameplay != null) gameplay.enabled = true;
            ResumeGameTime();
        }

        public void OpenSettings()
        {
            if (!initialized || entering || page == Page.Settings) return;
            if (!IsBlocking)
            {
                if (!hasStarted) return;
                OpenPauseMenu();
            }
            settingsReturnPage = page;
            selectedSettingsTab = 0;
            openedFrame = Time.frameCount;
            page = Page.Settings;
        }

        public void OpenPauseMenu()
        {
            if (!initialized || entering || IsBlocking || !hasStarted) return;
            IsBlocking = true;
            page = Page.Pause;
            selectedItem = 0;
            openedFrame = Time.frameCount;
            PauseGameTime();
            if (gameplay != null) gameplay.enabled = false;
            backdrop.SetActive(false);
            sceneCamera.cullingMask = gameplayMask;
        }

        private void PauseGameTime()
        {
            if (hasPausedTime) return;
            pausedTimeScale = Time.timeScale;
            Time.timeScale = 0f;
            hasPausedTime = true;
        }

        private void ResumeGameTime()
        {
            if (!hasPausedTime) return;
            Time.timeScale = pausedTimeScale;
            hasPausedTime = false;
        }

        private void ResumeGame()
        {
            if (!initialized || !IsBlocking || !hasStarted || entering) return;
            page = Page.Pause;
            openedFrame = Time.frameCount;
            FinishEntry();
        }

        public void CloseSettings()
        {
            SaveSettings();
            page = settingsReturnPage;
            selectedItem = 0;
            openedFrame = Time.frameCount;
        }

        private void LoadSettings()
        {
            fullscreen = PlayerPrefs.GetInt(SettingsPrefix + "Fullscreen", Screen.fullScreen ? 1 : 0) != 0;
            qualityLevel = Mathf.Clamp(PlayerPrefs.GetInt(SettingsPrefix + "Quality", QualitySettings.GetQualityLevel()),
                0, Mathf.Max(0, QualitySettings.names.Length - 1));
            frameLimitIndex = Mathf.Clamp(PlayerPrefs.GetInt(SettingsPrefix + "FrameLimit", 1), 0, FrameLimits.Length - 1);
            verticalSync = PlayerPrefs.GetInt(SettingsPrefix + "VSync", 1) != 0;
            masterVolume = Mathf.Clamp01(PlayerPrefs.GetFloat(SettingsPrefix + "MasterVolume", UnityEngine.AudioListener.volume));
            confirmReturnToTitle = PlayerPrefs.GetInt(SettingsPrefix + "ConfirmReturn", 1) != 0;
            showConstructionGrid = PlayerPrefs.GetInt(SettingsPrefix + "BuildGrid", 1) != 0;
            pushStrength = Mathf.Clamp01(PlayerPrefs.GetFloat(SettingsPrefix + "Push", 1f));
            oceanStrength = Mathf.Clamp01(PlayerPrefs.GetFloat(SettingsPrefix + "Ocean", 1f));
            mistStrength = Mathf.Clamp01(PlayerPrefs.GetFloat(SettingsPrefix + "Mist", 1f));
            ApplyDisplaySettings();
            if (gameplay != null) gameplay.SetBuildGridPreference(showConstructionGrid);
        }

        private void ApplyDisplaySettings()
        {
            // Editor Game view is controlled by the editor, not the standalone window mode.
#if !UNITY_EDITOR
            Screen.fullScreenMode = fullscreen ? FullScreenMode.FullScreenWindow : FullScreenMode.Windowed;
#endif
            if (QualitySettings.names.Length > 0 && QualitySettings.GetQualityLevel() != qualityLevel)
                QualitySettings.SetQualityLevel(qualityLevel, true);
            QualitySettings.vSyncCount = verticalSync ? 1 : 0;
            Application.targetFrameRate = FrameLimits[frameLimitIndex];
            UnityEngine.AudioListener.volume = masterVolume;
        }

        private void SaveSettings()
        {
            PlayerPrefs.SetInt(SettingsPrefix + "Fullscreen", fullscreen ? 1 : 0);
            PlayerPrefs.SetInt(SettingsPrefix + "Quality", qualityLevel);
            PlayerPrefs.SetInt(SettingsPrefix + "FrameLimit", frameLimitIndex);
            PlayerPrefs.SetInt(SettingsPrefix + "VSync", verticalSync ? 1 : 0);
            PlayerPrefs.SetFloat(SettingsPrefix + "MasterVolume", masterVolume);
            PlayerPrefs.SetInt(SettingsPrefix + "ConfirmReturn", confirmReturnToTitle ? 1 : 0);
            PlayerPrefs.SetInt(SettingsPrefix + "BuildGrid", showConstructionGrid ? 1 : 0);
            PlayerPrefs.SetFloat(SettingsPrefix + "Push", pushStrength);
            PlayerPrefs.SetFloat(SettingsPrefix + "Ocean", oceanStrength);
            PlayerPrefs.SetFloat(SettingsPrefix + "Mist", mistStrength);
            PlayerPrefs.Save();
        }
        public void SetMotionEnabled(bool enabled)
        {
            motionEnabled = enabled;
            PlayerPrefs.SetInt("LastLandfall.MenuMotion", enabled ? 1 : 0);
        }

        private void Update()
        {
            if (!initialized) return;
            if (!IsBlocking)
            {
                if (Input.GetKeyDown(KeyCode.Escape) && hasStarted) OpenPauseMenu();
                return;
            }
            if (motionEnabled) animationTime += Time.unscaledDeltaTime;
            UpdateBackdrop();
            if (entering)
            {
                float progress = Mathf.Clamp01((Time.unscaledTime - entryTime) / 0.9f);
                backdropMaterial.SetFloat("_Opacity", 1f - Mathf.SmoothStep(0f, 1f, progress));
                if (progress >= 1f) FinishEntry();
            }
        }

        private void UpdateBackdrop()
        {
            if (sceneCamera == null || backdrop == null) return;
            float height = sceneCamera.orthographicSize * 2f;
            backdrop.transform.localPosition = new Vector3(0f, 0f, sceneCamera.nearClipPlane + 0.5f);
            backdrop.transform.localRotation = Quaternion.identity;
            backdrop.transform.localScale = new Vector3(height * sceneCamera.aspect, height, 1f);
            backdropMaterial.SetFloat("_ScreenAspect", sceneCamera.aspect);
            backdropMaterial.SetFloat("_AnimationTime", animationTime);
            backdropMaterial.SetFloat("_PushAmount", 0.035f * pushStrength);
            backdropMaterial.SetFloat("_OceanMotion", oceanStrength);
            backdropMaterial.SetFloat("_MistAmount", 0.18f * mistStrength);
        }

        private GUIStyle Label(Font font, int size, Color color)
        {
            return new GUIStyle(GUI.skin.label)
            {
                font = font, fontSize = size, fontStyle = FontStyle.Normal,
                normal = { textColor = color }, padding = new RectOffset(),
                margin = new RectOffset(), wordWrap = false
            };
        }

        private void EnsureStyles()
        {
            if (body != null) return;
            titleFont = Font.CreateDynamicFontFromOSFont(new[] { "Georgia", "Noto Serif", "Times New Roman" }, 128);
            interfaceFont = Font.CreateDynamicFontFromOSFont(new[] { "Microsoft YaHei", "Noto Sans CJK SC", "Arial" }, 48);
            kicker = Label(interfaceFont, 17, Gold);
            lastTitle = Label(titleFont, 68, Ivory);
            landfallTitle = Label(titleFont, 104, Ivory);
            subtitle = Label(interfaceFont, 23, Ivory);
            body = Label(interfaceFont, 19, Ivory);
            small = Label(interfaceFont, 14, Muted);
            buttonText = Label(interfaceFont, 23, Ivory);
            settingsHeading = Label(interfaceFont, 27, Ivory);
            pauseTitle = Label(interfaceFont, 52, Ivory);
            emptyButton = new GUIStyle();

        }

        private static void Fill(Rect rect, Color color)
        {
            Color previous = GUI.color;
            GUI.color *= color;
            GUI.DrawTexture(rect, Texture2D.whiteTexture);
            GUI.color = previous;
        }

        private bool MenuButton(Rect rect, string label, string number, int index, bool primary = false)
        {
            // Handle input first so the transparent IMGUI control cannot cover the custom button art.
            bool clicked = GUI.Button(rect, GUIContent.none, GUIStyle.none);
            bool hover = rect.Contains(Event.current.mousePosition);
            bool active = hover || selectedItem == index;
            if (hover && Event.current.type == EventType.MouseMove) selectedItem = index;
            Fill(rect, new Color(0.025f, 0.075f, 0.09f, active ? 0.75f : 0.34f));
            Fill(new Rect(rect.x, rect.yMax - 1f, rect.width, 1f), new Color(Gold.r, Gold.g, Gold.b, active ? 0.85f : 0.27f));
            if (primary || active)
            {
                Fill(new Rect(rect.x, rect.y, rect.width, 1f), new Color(Gold.r, Gold.g, Gold.b, 0.7f));
                Fill(new Rect(rect.x, rect.y, 2f, rect.height), Gold);
            }
            GUI.Label(new Rect(rect.x + 20, rect.y + (rect.height - 22) * 0.5f, 32, 24), number, small);
            GUI.Label(new Rect(rect.x + 65, rect.y + (rect.height - 32) * 0.5f, rect.width - 100, 36), label, buttonText);
            if (active) GUI.Label(new Rect(rect.xMax - 35, rect.y + (rect.height - 30) * 0.5f, 28, 36), "›", buttonText);
            return clicked;
        }

        private bool Option(Rect rect, string label, bool value)
        {
            GUI.Label(rect, label, body);
            GUI.Label(new Rect(rect.xMax - 50, rect.y, 50, rect.height), value ? "开" : "关", kicker);
            Fill(new Rect(rect.x, rect.yMax - 6, rect.width, 1), new Color(Gold.r, Gold.g, Gold.b, 0.22f));
            return GUI.Button(rect, GUIContent.none, emptyButton) ? !value : value;
        }

        private void ActivateItem()
        {
            if (page == Page.Home)
            {
                if (selectedItem == 0) BeginGame();
                else if (selectedItem == 1) OpenSettings();
                else { page = Page.Quit; selectedItem = 0; }
            }
            else if (page == Page.Pause)
            {
                if (selectedItem == 0) ResumeGame();
                else if (selectedItem == 1) OpenSettings();
                else if (confirmReturnToTitle)
                {
                    page = Page.Quit;
                    selectedItem = 0;
                }
                else ShowHome();
            }
            else if (page == Page.Quit)
            {
                if (selectedItem == 0)
                {
                    if (hasStarted) ShowHome();
                    else
                    {
                        PlayerPrefs.Save();
#if UNITY_EDITOR
                        UnityEditor.EditorApplication.isPlaying = false;
#else
                        Application.Quit();
#endif
                    }
                }
                else page = hasStarted ? Page.Pause : Page.Home;
            }
        }

        private void HandleKeyboard()
        {
            Event current = Event.current;
            if (entering || current.type != EventType.KeyDown || openedFrame == Time.frameCount) return;
            if (current.alt || current.control || current.command || current.shift) return;
            if (current.keyCode == KeyCode.Escape)
            {
                if (page == Page.Settings) CloseSettings();
                else if (page == Page.Pause) ResumeGame();
                else if (page == Page.Quit) page = hasStarted ? Page.Pause : Page.Home;
                else if (page == Page.Home && hasStarted) ResumeGame();
                current.Use();
            }
            else if (page != Page.Settings)
            {
                int itemCount = page == Page.Quit ? 2 : 3;
                if (current.keyCode == KeyCode.DownArrow || current.keyCode == KeyCode.Tab)
                { selectedItem = (selectedItem + 1) % itemCount; current.Use(); }
                else if (current.keyCode == KeyCode.UpArrow)
                { selectedItem = (selectedItem + itemCount - 1) % itemCount; current.Use(); }
                else if (current.keyCode == KeyCode.Return || current.keyCode == KeyCode.Space)
                { ActivateItem(); current.Use(); }
            }
        }

        private void OnGUI()
        {
            if (!initialized || !IsBlocking) return;
            EnsureStyles();
            HandleKeyboard();
            if (!IsBlocking) return;
            Matrix4x4 previousMatrix = GUI.matrix;
            Color previousColor = GUI.color;
            float scale = Mathf.Min(Screen.height / 1080f, Screen.width / 1600f);
            scale = Mathf.Max(0.1f, scale);
            float width = Screen.width / scale, height = Screen.height / scale;
            GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1f));
            if (page == Page.Settings)
            {
                DrawSettings(width, height);
                GUI.matrix = previousMatrix;
                GUI.color = previousColor;
                return;
            }
            if (entering) GUI.color = new Color(1, 1, 1, backdropMaterial.GetFloat("_Opacity"));
            if (page == Page.Pause)
            {
                DrawPauseMenu(width, height);
                GUI.matrix = previousMatrix;
                GUI.color = previousColor;
                return;
            }
            GUI.Label(new Rect(108, 141, 650, 32), "洪 水 之 后   /   A F T E R  T H E  F L O O D", kicker);
            GUI.Label(new Rect(102, 203, 620, 96), "LAST", lastTitle);
            GUI.Label(new Rect(98, 277, 740, 145), "LANDFALL", landfallTitle);
            Fill(new Rect(108, 438, 72, 2), Gold);
            GUI.Label(new Rect(198, 423, 370, 40), "最 后 的 陆 地", subtitle);
            GUI.Label(new Rect(108, 483, 600, 72), "当世界沉入海底，\n文明从下一片陆地重新开始。", body);
            bool wasEnabled = GUI.enabled;
            GUI.enabled = !entering;
            if (page == Page.Home)
            {
                if (MenuButton(new Rect(108, 613, 366, 66), hasStarted ? "继续游戏" : "开始游戏", "01", 0, true)) BeginGame();
                if (MenuButton(new Rect(108, 699, 366, 56), "设置", "02", 1)) OpenSettings();
                if (MenuButton(new Rect(108, 775, 366, 56), "退出游戏", "03", 2))
                {
                    page = Page.Quit;
                    selectedItem = 0;
                }
            }
            else
            {
                GUI.Label(new Rect(108, 606, 580, 48), hasStarted ? "返回标题界面？" : "离开这片海域？", settingsHeading);
                GUI.Label(new Rect(108, 660, 600, 52), hasStarted
                    ? "当前岛屿的建造进度不会自动保存。"
                    : "确定退出游戏吗？", body);
                string confirmLabel = hasStarted ? "确认返回标题" : "确认退出游戏";
                if (MenuButton(new Rect(108, 723, 366, 60), confirmLabel, "01", 0)) ActivateItem();
                if (MenuButton(new Rect(108, 806, 366, 56), "取消", "←", 1))
                    page = hasStarted ? Page.Pause : Page.Home;
            }
            GUI.enabled = wasEnabled;
            GUI.Label(new Rect(108, height - 76, 690, 30), "越过洪水，寻找新的家园。", small);
            GUI.Label(new Rect(width - 300, height - 76, 260, 30), "L A S T  L A N D F A L L", small);
            GUI.matrix = previousMatrix;
            GUI.color = previousColor;
        }

        private void DrawPauseMenu(float width, float height)
        {
            Fill(new Rect(0, 0, width, height), new Color(0.005f, 0.016f, 0.026f, 0.18f));
            float panelWidth = Mathf.Min(650f, width - 96f);
            float panelHeight = Mathf.Min(780f, height - 100f);
            Rect panel = new Rect(Mathf.Max(52f, width * 0.075f), (height - panelHeight) * 0.5f,
                panelWidth, panelHeight);
            Fill(panel, new Color(0.008f, 0.027f, 0.039f, 0.82f));
            Fill(new Rect(panel.x, panel.y, panel.width, 3f), Gold);
            Fill(new Rect(panel.x, panel.y, 2f, panel.height), new Color(Gold.r, Gold.g, Gold.b, 0.45f));

            float x = panel.x + 48f;
            float contentWidth = panel.width - 96f;
            GUI.Label(new Rect(x, panel.y + 44f, contentWidth, 28f), "LAST LANDFALL   /   SYSTEM MENU", kicker);
            GUI.Label(new Rect(x - 2f, panel.y + 88f, contentWidth, 72f), "暂停游戏", pauseTitle);
            Fill(new Rect(x, panel.y + 178f, 9f, 9f), new Color(Gold.r, Gold.g, Gold.b,
                0.55f + 0.35f * Mathf.Sin(animationTime * 1.5f)));
            GUI.Label(new Rect(x + 22f, panel.y + 168f, contentWidth - 22f, 28f), "游戏已暂停", kicker);
            GUI.Label(new Rect(x, panel.y + 207f, contentWidth, 56f),
                "海面暂歇片刻。继续时，岛屿建设将从此刻接续。", body);

            bool previousEnabled = GUI.enabled;
            GUI.enabled = !entering;
            float buttonY = panel.y + 298f;
            const float buttonHeight = 76f;
            const float buttonGap = 18f;
            if (MenuButton(new Rect(x, buttonY, contentWidth, buttonHeight), "继续游戏", "01", 0, true))
                ResumeGame();
            if (MenuButton(new Rect(x, buttonY + buttonHeight + buttonGap, contentWidth, buttonHeight), "设置", "02", 1))
                OpenSettings();
            if (MenuButton(new Rect(x, buttonY + (buttonHeight + buttonGap) * 2f, contentWidth, buttonHeight), "返回标题界面", "03", 2))
            {
                if (confirmReturnToTitle)
                {
                    page = Page.Quit;
                    selectedItem = 0;
                }
                else ShowHome();
            }
            GUI.enabled = previousEnabled;

            Fill(new Rect(x, panel.yMax - 92f, contentWidth, 1f), new Color(Gold.r, Gold.g, Gold.b, 0.25f));
            GUI.Label(new Rect(x, panel.yMax - 68f, contentWidth, 28f), "ESC  继续游戏", small);
            GUI.Label(new Rect(panel.xMax - 170f, panel.yMax - 68f, 122f, 28f), "PAUSED", small);
        }

        private void DrawSettings(float width, float height)
        {
            Fill(new Rect(0, 0, width, height), new Color(0.004f, 0.015f, 0.024f, 0.22f));
            float panelWidth = Mathf.Min(1400f, width - 120f);
            float panelHeight = Mathf.Min(900f, height - 80f);
            Rect panel = new Rect((width - panelWidth) * 0.5f, (height - panelHeight) * 0.5f,
                panelWidth, panelHeight);
            Fill(panel, new Color(0.006f, 0.025f, 0.036f, 0.91f));
            Fill(new Rect(panel.x, panel.y, panel.width, 3f), Gold);
            Fill(new Rect(panel.x + 292f, panel.y + 126f, 1f, panel.height - 222f),
                new Color(Gold.r, Gold.g, Gold.b, 0.28f));

            float left = panel.x + 48f;
            GUI.Label(new Rect(left, panel.y + 28f, 500f, 44f), "设置", settingsHeading);
            GUI.Label(new Rect(left, panel.y + 74f, 670f, 25f), "GAME OPTIONS   /   修改立即生效", kicker);
            GUI.Label(new Rect(panel.xMax - 260f, panel.y + 48f, 210f, 28f),
                settingsReturnPage == Page.Pause ? "暂停菜单" : "标题界面", small);

            bool hasHomeTab = settingsReturnPage == Page.Home;
            int tabCount = hasHomeTab ? 5 : 4;
            selectedSettingsTab = Mathf.Clamp(selectedSettingsTab, 0, tabCount - 1);
            string[] labels = hasHomeTab
                ? new[] { "画面", "音频", "操作", "游戏", "首页氛围" }
                : new[] { "画面", "音频", "操作", "游戏" };
            string[] symbols = { "01", "02", "03", "04", "05" };
            float navX = panel.x + 34f;
            float navY = panel.y + 150f;
            for (int i = 0; i < tabCount; i++)
            {
                Rect tabRect = new Rect(navX, navY + i * 74f, 234f, 60f);
                if (SettingsTabButton(tabRect, symbols[i], labels[i], i)) selectedSettingsTab = i;
            }
            GUI.Label(new Rect(navX + 10f, panel.yMax - 110f, 230f, 48f),
                "设置会自动保存", small);

            Rect content = new Rect(panel.x + 326f, panel.y + 132f, panel.width - 366f, panel.height - 228f);
            Fill(content, new Color(0.012f, 0.039f, 0.052f, 0.56f));
            Fill(new Rect(content.x, content.y, 2f, content.height), new Color(Gold.r, Gold.g, Gold.b, 0.58f));
            DrawSettingsContent(content, hasHomeTab);

            float footerY = panel.yMax - 78f;
            if (MenuButton(new Rect(panel.x + 40f, footerY, 250f, 54f), "恢复默认", "↺", 10))
                RestoreDefaultSettings();
            string returnLabel = settingsReturnPage == Page.Pause ? "返回暂停菜单" : "返回首页";
            if (MenuButton(new Rect(panel.xMax - 330f, footerY, 290f, 54f), returnLabel, "←", 11, true))
                CloseSettings();
        }

        private bool SettingsTabButton(Rect rect, string symbol, string label, int index)
        {
            bool hovered = rect.Contains(Event.current.mousePosition);
            bool active = selectedSettingsTab == index;
            if (hovered && Event.current.type == EventType.MouseMove) selectedSettingsTab = index;
            Fill(rect, new Color(0.02f, 0.066f, 0.08f, active ? 0.96f : hovered ? 0.66f : 0.32f));
            Fill(new Rect(rect.x, rect.yMax - 1f, rect.width, 1f),
                new Color(Gold.r, Gold.g, Gold.b, active ? 0.82f : 0.18f));
            if (active) Fill(new Rect(rect.x, rect.y, 3f, rect.height), Gold);
            GUI.Label(new Rect(rect.x + 18f, rect.y + 10f, 28f, 38f), symbol, kicker);
            GUI.Label(new Rect(rect.x + 58f, rect.y + 12f, rect.width - 74f, 36f), label, body);
            return GUI.Button(rect, GUIContent.none, emptyButton);
        }

        private void DrawSettingsContent(Rect content, bool hasHomeTab)
        {
            float x = content.x + 36f;
            float y = content.y + 30f;
            float rowWidth = content.width - 72f;
            string[] titles = hasHomeTab
                ? new[] { "画面", "音频", "操作", "游戏", "首页氛围" }
                : new[] { "画面", "音频", "操作", "游戏" };
            string[] descriptions = hasHomeTab
                ? new[] { "显示模式与性能", "调整游戏总体音量", "查看镜头与建造快捷键", "管理建造界面选项", "调整标题画面的动态表现" }
                : new[] { "显示模式与性能", "调整游戏总体音量", "查看镜头与建造快捷键", "管理建造界面选项" };
            GUI.Label(new Rect(x, y, rowWidth, 40f), titles[selectedSettingsTab], settingsHeading);
            GUI.Label(new Rect(x, y + 42f, rowWidth, 26f), descriptions[selectedSettingsTab], small);
            y += 100f;

            if (selectedSettingsTab == 0)
            {
                bool oldFullscreen = fullscreen;
                fullscreen = Option(new Rect(x, y, rowWidth, 56f), "无边框全屏", fullscreen);
                if (oldFullscreen != fullscreen) { ApplyDisplaySettings(); SaveSettings(); }
                y += 72f;

                string[] qualityNames = QualitySettings.names;
                string qualityName = qualityNames.Length == 0 ? "默认" : qualityNames[qualityLevel];
                if (Choice(new Rect(x, y, rowWidth, 56f), "画面质量", qualityName) && qualityNames.Length > 0)
                {
                    qualityLevel = (qualityLevel + 1) % qualityNames.Length;
                    ApplyDisplaySettings(); SaveSettings();
                }
                y += 72f;

                bool oldSync = verticalSync;
                verticalSync = Option(new Rect(x, y, rowWidth, 56f), "垂直同步", verticalSync);
                if (oldSync != verticalSync) { ApplyDisplaySettings(); SaveSettings(); }
                y += 72f;

                bool previousEnabled = GUI.enabled;
                GUI.enabled = !verticalSync;
                string frameText = verticalSync ? "跟随显示器" :
                    FrameLimits[frameLimitIndex] < 0 ? "不限" : FrameLimits[frameLimitIndex] + " FPS";
                if (Choice(new Rect(x, y, rowWidth, 56f), "帧率上限", frameText))
                {
                    frameLimitIndex = (frameLimitIndex + 1) % FrameLimits.Length;
                    ApplyDisplaySettings(); SaveSettings();
                }
                GUI.enabled = previousEnabled;
#if UNITY_EDITOR
                GUI.Label(new Rect(x, y + 78f, rowWidth, 28f), "全屏模式会在独立游戏窗口中生效。", small);
#endif
            }
            else if (selectedSettingsTab == 1)
            {
                if (SliderOption(new Rect(x, y, rowWidth, 62f), "总体音量", ref masterVolume))
                {
                    ApplyDisplaySettings();
                    SaveSettings();
                }
                GUI.Label(new Rect(x, y + 96f, rowWidth, 42f), "音量调整会立即生效并自动保存。", small);
            }
            else if (selectedSettingsTab == 2)
            {
                DrawControlHint(new Rect(x, y, rowWidth, 60f), "W  A  S  D", "平移镜头"); y += 68f;
                DrawControlHint(new Rect(x, y, rowWidth, 60f), "滚轮", "缩放镜头"); y += 68f;
                DrawControlHint(new Rect(x, y, rowWidth, 60f), "中键拖动", "旋转镜头"); y += 68f;
                DrawControlHint(new Rect(x, y, rowWidth, 60f), "空手左键拖动", "平移镜头"); y += 68f;
                DrawControlHint(new Rect(x, y, rowWidth, 60f), "Q / E", "旋转镜头或已选建筑"); y += 68f;
                DrawControlHint(new Rect(x, y, rowWidth, 60f), "R", "旋转已选建筑");
            }
            else if (selectedSettingsTab == 3)
            {
                bool oldConfirm = confirmReturnToTitle;
                confirmReturnToTitle = Option(new Rect(x, y, rowWidth, 56f), "返回标题前确认", confirmReturnToTitle);
                if (oldConfirm != confirmReturnToTitle) SaveSettings();
                y += 72f;
                bool oldGrid = showConstructionGrid;
                showConstructionGrid = Option(new Rect(x, y, rowWidth, 56f), "建造时显示网格", showConstructionGrid);
                if (oldGrid != showConstructionGrid)
                {
                    if (gameplay != null) gameplay.SetBuildGridPreference(showConstructionGrid);
                    SaveSettings();
                }
                GUI.Label(new Rect(x, y + 94f, rowWidth, 54f), "打开暂停菜单时，岛屿操作会暂时停止。", small);
            }
            else if (hasHomeTab && selectedSettingsTab == 4)
            {
                bool oldMotion = motionEnabled;
                bool motion = Option(new Rect(x, y, rowWidth, 56f), "启用动态背景", motionEnabled);
                if (motion != oldMotion) { SetMotionEnabled(motion); SaveSettings(); }
                y += 76f;
                bool previousEnabled = GUI.enabled;
                GUI.enabled = motionEnabled;
                bool changed = Strength(new Rect(x, y, rowWidth, 54f), "慢速推镜", ref pushStrength);
                changed |= Strength(new Rect(x, y + 68f, rowWidth, 54f), "海面微动", ref oceanStrength);
                changed |= Strength(new Rect(x, y + 136f, rowWidth, 54f), "漂雾浓度", ref mistStrength);
                GUI.enabled = previousEnabled;
                if (changed) { UpdateBackdrop(); SaveSettings(); }
            }
        }

        private void DrawControlHint(Rect rect, string key, string action)
        {
            Fill(rect, new Color(0.026f, 0.077f, 0.091f, 0.6f));
            Fill(new Rect(rect.x, rect.yMax - 1f, rect.width, 1f),
                new Color(Gold.r, Gold.g, Gold.b, 0.22f));
            GUI.Label(new Rect(rect.x + 16f, rect.y + 12f, 210f, 36f), key, kicker);
            GUI.Label(new Rect(rect.x + 238f, rect.y + 12f, rect.width - 254f, 36f), action, body);
        }

        private void RestoreDefaultSettings()
        {
            fullscreen = true;
            qualityLevel = Mathf.Max(0, QualitySettings.names.Length - 1);
            verticalSync = true;
            frameLimitIndex = 1;
            masterVolume = 1f;
            confirmReturnToTitle = true;
            showConstructionGrid = true;
            pushStrength = oceanStrength = mistStrength = 1f;
            SetMotionEnabled(true);
            if (gameplay != null) gameplay.SetBuildGridPreference(showConstructionGrid);
            ApplyDisplaySettings();
            UpdateBackdrop();
            SaveSettings();
        }

        private bool SliderOption(Rect rect, string label, ref float value)
        {
            GUI.Label(rect, label, body);
            GUI.Label(new Rect(rect.xMax - 68f, rect.y, 68f, 28f),
                Mathf.RoundToInt(value * 100f) + "%", kicker);
            Color previous = GUI.color;
            GUI.color = Gold;
            float next = GUI.HorizontalSlider(new Rect(rect.x + 230f, rect.y + 33f,
                Mathf.Max(120f, rect.width - 320f), 20f), value, 0f, 1f);
            GUI.color = previous;
            Fill(new Rect(rect.x, rect.yMax - 2f, rect.width, 1f), new Color(Gold.r, Gold.g, Gold.b, 0.22f));
            if (Mathf.Approximately(next, value)) return false;
            value = next;
            return true;
        }

        private bool Choice(Rect rect, string label, string value)
        {
            GUI.Label(rect, label, body);
            GUIStyle valueStyle = new GUIStyle(body) { alignment = TextAnchor.UpperRight, normal = { textColor = Gold } };
            GUI.Label(new Rect(rect.xMax - 330, rect.y, 330, rect.height), value + "  ›", valueStyle);
            Fill(new Rect(rect.x, rect.yMax - 6, rect.width, 1), new Color(Gold.r, Gold.g, Gold.b, 0.22f));
            return GUI.Button(rect, GUIContent.none, emptyButton);
        }

        private bool Strength(Rect rect, string label, ref float value)
        {
            GUI.Label(rect, label, body);
            GUI.Label(new Rect(rect.xMax - 55, rect.y, 55, 30), Mathf.RoundToInt(value * 100) + "%", small);
            Color previous = GUI.color;
            GUI.color = Gold;
            float next = GUI.HorizontalSlider(new Rect(rect.x + 210, rect.y + 8, rect.width - 295, 24), value, 0, 1);
            GUI.color = previous;
            if (Mathf.Approximately(next, value)) return false;
            value = next;
            return true;
        }

        private void OnApplicationPause(bool paused) { if (paused && initialized) SaveSettings(); }
        private void OnApplicationQuit() { if (initialized) SaveSettings(); }

        private void OnDestroy()
        {
            ResumeGameTime();
            if (sceneCamera != null && initialized) sceneCamera.cullingMask = gameplayMask;
            if (gameplay != null && initialized) gameplay.enabled = true;
            if (backdrop != null) Destroy(backdrop);
            if (backdropMaterial != null) Destroy(backdropMaterial);
            if (titleFont != null) Destroy(titleFont);
            if (interfaceFont != null) Destroy(interfaceFont);
        }
    }
}
