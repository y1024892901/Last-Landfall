using System.Collections.Generic;
using System.Globalization;
using UnityEngine;
using UnityEngine.Rendering;

namespace LastLandfall.Prototype
{
    /// <summary>
    /// Self-contained graybox for the first settlement-building loop.
    /// Add this source to a Unity project, then press Play in any scene.
    /// </summary>
    public sealed class BuildPlacementPrototype : MonoBehaviour
    {
        private const string IslandRootName = "Playable Island - Gate25";
        private const string IslandResourceName = "IslandReference_Gate25";
        private const string SatelliteIslandResourceName = "LastLandfall_Basin_TwinIslands_Gate26";
        private const string LegacyIslandRootName = "Playable Island - Reference V2";
        private const string LegacyIslandModelName = "IslandReference_V2";
        private const string TerrainSourceName = "terrain source";
        private const string PlaySpaceRootName = "Island Play Space - Rotate and Pan";
        private const float CameraRotationSpeed = 28f;
        private const int VisibleHeaderResourceCount = 4;
        private const float RoadModelImportYawCorrectionDegrees = 180f;
        private const int TotalHeaderResourceCount = 8;
        private const float CameraZoomFactor = 1.12f;
        private const float MinimumCameraOrthographicSize = 3f;
        private const float MaximumCameraOrthographicSize = 72f;
        private const float CameraOrbitDegreesPerPixel = 0.35f;
        private const float CameraKeyboardPanSpeed = 0.32f;
        private const float MinimumCameraOrbitPitch = 20f;
        private const float MaximumCameraOrbitPitch = 85f;
        private const float WaterEdgePadding = 24f;
        private const float IslandHorizontalScale = 0.02f;
        private const float IslandValleyReferenceHeight = 54f;
        private const float IslandVerticalOffset = TileTop - IslandValleyReferenceHeight * IslandHorizontalScale;
        private const float DefaultCameraOrthographicSize = 27f;
        private const float WaterPlaneHeight = IslandVerticalOffset;
        private const float WaterPlaneClearance = 4f;
        private const float FloodwaterPlaneSize = 768f;
        private const float TileHeight = 0.32f;
        private const float TileTop = TileHeight * 0.5f;
        private const int SidebarCategoryCount = 3;
        private const float SidebarCategoryButtonSize = 64f;

        private enum SidebarCategory
        {
            Technology,
            Culture,
            Buildings
        }

        private static readonly Vector2Int North = new Vector2Int(0, 1);
        private static readonly Vector2Int South = new Vector2Int(0, -1);
        private static readonly Vector2Int East = new Vector2Int(1, 0);
        private static readonly Vector2Int West = new Vector2Int(-1, 0);
        private static readonly Vector2Int[] CardinalDirections = { North, East, South, West };

        private static readonly BuildableDefinition[] Buildables =
        {
            new BuildableDefinition("居民小屋", "ResidentHut", 1, 1, 20),
            new BuildableDefinition("温室", "Greenhouse", 2, 2, 35),
            new BuildableDefinition("集水净水站", "WaterPurifier", 2, 2, 40),
            new BuildableDefinition("废料拆解工坊", "SalvageWorkshop", 2, 2, 35),
            new BuildableDefinition("发电站", "GeneratorStation", 2, 2, 40),
            new BuildableDefinition("仓库", "StorageDepot", 2, 2, 25),
            new BuildableDefinition("救援指挥站", "RescueRadioCenter", 2, 2, 45),
            new BuildableDefinition("救援码头", "RescueDock", 1, 1, 35, BuildableKind.Dock),
            new BuildableDefinition("道路", "RoadStraight", 1, 1, 4, BuildableKind.Road, "RoadTiles_Final")
        };
        private static readonly string[] HeaderResourceIconNames =
        {
            "Wood", "Food", "Water", "Metal", "Fuel", "Power", "Ore", "Medical"
        };
        private static readonly string[] HeaderResourceDisplayNames =
        {
            "木材", "食物", "淡水", "金属", "燃料", "电力", "矿石", "医疗物资"
        };
        private static readonly string[] SidebarCategoryNames = { "科技", "文化", "建筑" };
        private static readonly string[] TechnologyRouteNames = { "基础供电", "海水淡化", "太阳能微网", "自动化回收" };
        private static readonly string[] TechnologyRouteDetails =
        {
            "建立稳定的基础电力供应。", "解锁更可靠的淡水生产。", "利用太阳能扩展岛屿电网。", "提高废料拆解与回收效率。"
        };
        private static readonly string[] CultureRouteNames = { "生存公约", "灾后档案", "岛屿课堂", "新生聚落" };
        private static readonly string[] CultureRouteDetails =
        {
            "确立聚落成员共同遵守的规则。", "记录灾后经历与重要发现。", "建立知识传承与技能教学。", "形成稳定的岛屿社区认同。"
        };

        private readonly HashSet<Vector2Int> occupiedCells = new HashSet<Vector2Int>();
        private readonly HashSet<Vector2Int> roadCells = new HashSet<Vector2Int>();
        private readonly Dictionary<Vector2Int, GameObject> roadObjects = new Dictionary<Vector2Int, GameObject>();
        private readonly List<Material> ownedMaterials = new List<Material>();
        private readonly List<Texture2D> ownedUiTextures = new List<Texture2D>();

        private Camera gameCamera;
        private Transform mapRoot;
        private Transform islandRoot;
        private Transform satelliteIslandsRoot;
        private Transform waterTransform;
        private Material waterMaterial;
        private Light prototypeSun;
        private IslandWeatherSystem weatherSystem;
        private Material islandBareEarthMaterial;
        private Bounds islandVisibleBounds;
        private bool hasIslandVisibleBounds;
        private MeshCollider[] islandLandColliders;
        private Vector3 cameraOrbitTarget;
        private float cameraOrbitDistance;
        private float defaultCameraOrbitDistance;
        private float cameraOrbitYawDegrees;
        private float cameraOrbitPitchDegrees;
        private GameObject previewObject;
        private Renderer[] previewRenderers;
        private Renderer[] gridOverlayRenderers;
        private MeshFilter[] islandTerrainMeshes;
        private Bounds islandLocalBounds;
        private bool hasIslandLocalBounds;
        private Texture2D coastDistanceTexture;
        private IslandConstructionGrid constructionGrid;
        public IslandConstructionGrid ConstructionGrid => constructionGrid;
        public Renderer[] ConstructionGridRenderers => gridOverlayRenderers;
        private Material foundationMaterial;
        private Material validPreviewMaterial;
        private Material invalidPreviewMaterial;
        private Material houseBodyMaterial;
        private Material houseRoofMaterial;
        private GUIStyle panelStyle;
        private GUIStyle titleStyle;
        private GUIStyle mutedLabelStyle;
        private GUIStyle cardLabelStyle;
        private GUIStyle cardStyle;
        private GUIStyle selectedCardStyle;
        private GUIStyle sidebarCategoryButtonStyle;
        private GUIStyle sidebarCategorySelectedButtonStyle;
        private GUIStyle sidebarCategoryLabelStyle;
        private GUIStyle closeButtonStyle;
        private GUIStyle transparentButtonStyle;
        private GUIStyle headerResourceValueStyle;
        private GUIStyle topHudSmallLabelStyle;
        private GUIStyle topHudClockStyle;
        private GUIStyle topHudSpeedStyle;
        private GUIStyle topHudSpeedSelectedStyle;
        private GUIStyle topHudMoreStyle;
        private GUIStyle topHudTabStyle;
        private GUIStyle topHudTabSelectedStyle;
        private GUIStyle topHudPopupStyle;
        private GUIStyle weatherButtonStyle;
        private GUIStyle weatherOptionStyle;
        private GUIStyle weatherOptionSelectedStyle;
        private GUIStyle weatherOptionLabelStyle;
        private GUIStyle weatherOptionSelectedLabelStyle;
        private GUIStyle weatherMenuTitleStyle;
        private GUIStyle weatherTimeValueStyle;
        private GUIStyle weatherTimeMarksStyle;
        private GUIStyle weatherTimeSliderStyle;
        private GUIStyle weatherTimeSliderThumbStyle;
        private Texture2D weatherToggleOffTrackTexture;
        private Texture2D weatherToggleOnTrackTexture;
        private Texture2D weatherToggleKnobTexture;
        private Texture2D[] weatherIcons;
        private Texture2D[] headerResourceIcons;
        private Texture2D[] topHudUtilityIcons;
        private Texture2D[] sidebarCategoryIcons;
        private readonly float[] headerButtonFlashUntil = new float[4];
        private float nextHeaderAssetRetryTime;
        private string previewAssetName;

        private int wood = 9999;
        private int selectedBuildableIndex = -1;
        private int selectedTechnologyRouteIndex;
        private int selectedCultureRouteIndex;
        private int rotationDegrees;
        private float cameraOrthographicSize = DefaultCameraOrthographicSize;
        private bool hasHoveredCell;
        private bool hasLastRoadCell;
        private bool isBuildMenuOpen;
        private bool isWeatherMenuOpen;
        private bool isResourceMenuOpen;
        private int selectedSimulationSpeedIndex;
        private SidebarCategory activeSidebarCategory = SidebarCategory.Buildings;
        private bool isBuildGridVisible = true;
        private bool isTopDownView;
        private bool isViewDragging;
        private bool viewDragUsesLeftButton;
        private Vector2Int lastRoadCell;
        private Vector2Int hoveredCell;
        private Vector2 buildMenuScroll;
        private Vector3 lastViewDragMousePosition;
        private float cameraPitchBeforeTopDown;
        private string statusMessage = "选择建筑开始建造。";
        private string hoverMessage = string.Empty;
        private Texture2D[] buildIcons;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void CreatePrototypeIfNeeded()
        {
            if (FindAnyObjectByType<BuildPlacementPrototype>() != null)
            {
                return;
            }

            GameObject root = new GameObject("Last Landfall - Build Prototype");
            root.AddComponent<BuildPlacementPrototype>();
        }

        private void Awake()
        {
            mapRoot = new GameObject(PlaySpaceRootName).transform;
            gameCamera = EnsureCamera();
            CreateMaterials();
            CreateLighting();
            CreateWater();
            CreateIslandLandform();
            CreateCoastDistanceField();
            InitializeWeather();
            CreateGridOverlay();
            EnsureHeaderAssetsLoaded();
            LoadBuildIcons();
            PositionCamera();
        }

        private void EnsureHeaderAssetsLoaded()
        {
            bool hasMissingResourceIcon = headerResourceIcons == null ||
                headerResourceIcons.Length != HeaderResourceIconNames.Length;
            if (!hasMissingResourceIcon)
            {
                for (int i = 0; i < headerResourceIcons.Length; i++)
                {
                    hasMissingResourceIcon |= headerResourceIcons[i] == null;
                }
            }

            if (!hasMissingResourceIcon || Time.unscaledTime < nextHeaderAssetRetryTime)
            {
                return;
            }

            nextHeaderAssetRetryTime = Time.unscaledTime + 0.5f;
            if (headerResourceIcons == null || headerResourceIcons.Length != HeaderResourceIconNames.Length)
            {
                headerResourceIcons = new Texture2D[HeaderResourceIconNames.Length];
            }

            for (int i = 0; i < HeaderResourceIconNames.Length; i++)
            {
                if (headerResourceIcons[i] == null)
                {
                    headerResourceIcons[i] = Resources.Load<Texture2D>("UI/ResourceIcons/" + HeaderResourceIconNames[i]);
                }
            }
        }

        private void Update()
        {
            ApplyShoreFoamSettings();

            Vector2 keyboardPan = Vector2.zero;
            if (Input.GetKey(KeyCode.A))
            {
                keyboardPan.x -= 1f;
            }

            if (Input.GetKey(KeyCode.D))
            {
                keyboardPan.x += 1f;
            }

            if (Input.GetKey(KeyCode.S))
            {
                keyboardPan.y -= 1f;
            }

            if (Input.GetKey(KeyCode.W))
            {
                keyboardPan.y += 1f;
            }
            if (keyboardPan.sqrMagnitude > 0.001f)
            {
                keyboardPan.Normalize();
                float panPixelsPerSecond = Screen.height * CameraKeyboardPanSpeed;
                PanCamera(new Vector3(-keyboardPan.x, -keyboardPan.y, 0f) * panPixelsPerSecond * Time.deltaTime);
            }

            bool buildingSelected = selectedBuildableIndex >= 0 &&
                Buildables[selectedBuildableIndex].Kind == BuildableKind.Building;
            if (buildingSelected)
            {
                if (Input.GetKeyDown(KeyCode.Q))
                {
                    RotateSelectedBuilding(-90);
                }

                if (Input.GetKeyDown(KeyCode.E))
                {
                    RotateSelectedBuilding(90);
                }
            }
            else
            {
                float rotationInput = 0f;
                if (Input.GetKey(KeyCode.Q))
                {
                    rotationInput -= 1f;
                }

                if (Input.GetKey(KeyCode.E))
                {
                    rotationInput += 1f;
                }

                if (rotationInput != 0f)
                {
                    cameraOrbitYawDegrees = Mathf.Repeat(
                        cameraOrbitYawDegrees + rotationInput * CameraRotationSpeed * Time.deltaTime,
                        360f);
                    ClampCameraView();
                    UpdateCameraPose();
                }
            }

            Vector3 screenMousePosition = Input.mousePosition;
            Vector2 guiMousePosition = new Vector2(screenMousePosition.x, Screen.height - screenMousePosition.y);
            Rect topBarRect = GetTopBarRect();
            bool pointerOverUi = IsPointerOverUi(guiMousePosition, GetPanelRect(), topBarRect, isBuildMenuOpen);

            float scroll = Input.mouseScrollDelta.y;
            if (Mathf.Abs(scroll) > 0.01f && !pointerOverUi)
            {
                ZoomCamera(scroll);
            }

            bool middlePressed = Input.GetMouseButtonDown(2);
            bool emptyHandLeftPressed = selectedBuildableIndex < 0 && Input.GetMouseButtonDown(0);
            if ((middlePressed || emptyHandLeftPressed) && !pointerOverUi)
            {
                isViewDragging = true;
                viewDragUsesLeftButton = !middlePressed && emptyHandLeftPressed;
                lastViewDragMousePosition = screenMousePosition;
            }

            if (isViewDragging)
            {
                bool dragButtonHeld = viewDragUsesLeftButton ? Input.GetMouseButton(0) : Input.GetMouseButton(2);
                if (!dragButtonHeld)
                {
                    isViewDragging = false;
                }
                else
                {
                    Vector3 mouseDelta = screenMousePosition - lastViewDragMousePosition;
                    if (!pointerOverUi)
                    {
                        if (viewDragUsesLeftButton)
                        {
                            PanCamera(mouseDelta);
                        }
                        else
                        {
                            OrbitCamera(mouseDelta);
                        }
                    }

                    lastViewDragMousePosition = screenMousePosition;
                }
            }
        }

        private void ApplyShoreFoamSettings()
        {
            if (waterMaterial == null || !waterMaterial.HasProperty("_ShoreFoamWidth"))
            {
                return;
            }

            const float visibleFoamWidth = 9.5f;
            const float visibleFoamStrength = 1.0f;
            if (!Mathf.Approximately(waterMaterial.GetFloat("_ShoreFoamWidth"), visibleFoamWidth))
            {
                waterMaterial.SetFloat("_ShoreFoamWidth", visibleFoamWidth);
            }
            if (!Mathf.Approximately(waterMaterial.GetFloat("_ShoreFoamStrength"), visibleFoamStrength))
            {
                waterMaterial.SetFloat("_ShoreFoamStrength", visibleFoamStrength);
            }
        }

        private void OnGUI()
        {
            if (weatherSystem != null)
            {
                weatherSystem.DrawRainOverlay();
            }

            EnsureGuiStyles();
            Event guiEvent = Event.current;
            UpdateHoveredCell(guiEvent.mousePosition);
            Rect panelRect = GetPanelRect();
            Rect topBarRect = GetTopBarRect();
            bool closedHudMenuThisClick = false;
            if (isWeatherMenuOpen && guiEvent.type == EventType.MouseDown && guiEvent.button == 0 &&
                !GetWeatherMenuRect(topBarRect).Contains(guiEvent.mousePosition) &&
                !GetWeatherButtonRect(topBarRect).Contains(guiEvent.mousePosition))
            {
                isWeatherMenuOpen = false;
                closedHudMenuThisClick = true;
            }

            if (isResourceMenuOpen && guiEvent.type == EventType.MouseDown && guiEvent.button == 0 &&
                !GetResourceMenuRect(topBarRect).Contains(guiEvent.mousePosition) &&
                !GetResourceMoreButtonRect(topBarRect).Contains(guiEvent.mousePosition))
            {
                isResourceMenuOpen = false;
                closedHudMenuThisClick = true;
            }

            if (guiEvent.type == EventType.KeyDown)
            {
                if (guiEvent.keyCode == KeyCode.R && selectedBuildableIndex >= 0)
                {
                    BuildableDefinition selected = Buildables[selectedBuildableIndex];
                    if (selected.Kind == BuildableKind.Building)
                    {
                        RotateSelectedBuilding(90);
                        guiEvent.Use();
                    }
                }
            }

            if (guiEvent.type == EventType.MouseDown)
            {
                if (guiEvent.button == 1)
                {
                    selectedBuildableIndex = -1;
                    hoverMessage = string.Empty;
                    hasLastRoadCell = false;
                    statusMessage = "已退出建造模式。";
                    guiEvent.Use();
                }
                else if (guiEvent.button == 0 && selectedBuildableIndex >= 0 && !IsPointerOverUi(
                             guiEvent.mousePosition, panelRect, topBarRect, isBuildMenuOpen) &&
                         !closedHudMenuThisClick && hasHoveredCell)
                {
                    if (Buildables[selectedBuildableIndex].Kind == BuildableKind.Road)
                    {
                        PlaceContinuousRoad(hoveredCell);
                    }
                    else
                    {
                        TryPlaceSelected(hoveredCell);
                    }
                    guiEvent.Use();
                }
            }
            else if (guiEvent.type == EventType.MouseDrag && guiEvent.button == 0 &&
                     selectedBuildableIndex >= 0 && Buildables[selectedBuildableIndex].Kind == BuildableKind.Road &&
                     !IsPointerOverUi(guiEvent.mousePosition, panelRect, topBarRect, isBuildMenuOpen) && hasHoveredCell)
            {
                PlaceContinuousRoad(hoveredCell);
                guiEvent.Use();
            }
            else if (guiEvent.type == EventType.MouseUp && guiEvent.button == 0)
            {
                hasLastRoadCell = false;
            }

            UpdatePreview();
            DrawTopBar(topBarRect);
            DrawSidebarCategories();
            if (isBuildMenuOpen)
            {
                DrawBuildPanel(panelRect);
            }
        }

        private void OnDestroy()
        {
            for (int i = 0; i < ownedMaterials.Count; i++)
            {
                if (ownedMaterials[i] != null)
                {
                    Destroy(ownedMaterials[i]);
                }
            }

            for (int i = 0; i < ownedUiTextures.Count; i++)
            {
                if (ownedUiTextures[i] != null)
                {
                    Destroy(ownedUiTextures[i]);
                }
            }
        }

        private void InitializeWeather()
        {
            weatherSystem = GetComponent<IslandWeatherSystem>();
            if (weatherSystem == null)
            {
                weatherSystem = gameObject.AddComponent<IslandWeatherSystem>();
            }

            weatherSystem.Initialize(gameCamera, prototypeSun, waterMaterial, islandRoot);
        }

        private Camera EnsureCamera()
        {
            Camera existing = Camera.main;
            if (existing == null)
            {
                GameObject cameraObject = new GameObject("Main Camera");
                cameraObject.tag = "MainCamera";
                existing = cameraObject.AddComponent<Camera>();
            }

            existing.orthographic = true;
            existing.orthographicSize = cameraOrthographicSize;
            existing.clearFlags = CameraClearFlags.SolidColor;
            existing.backgroundColor = new Color(0.008f, 0.055f, 0.13f);
            existing.depthTextureMode |= DepthTextureMode.Depth;
            return existing;
        }

        private void PositionCamera()
        {
            cameraOrbitYawDegrees = 350f;
            cameraOrbitPitchDegrees = 36f;
            cameraOrthographicSize = DefaultCameraOrthographicSize;
            cameraOrbitTarget = mapRoot != null ? mapRoot.TransformPoint(new Vector3(0f, 1.15f, 0f)) : Vector3.zero;
            defaultCameraOrbitDistance = 72f;
            if (hasIslandVisibleBounds)
            {
                Quaternion rotation = Quaternion.Euler(cameraOrbitPitchDegrees, cameraOrbitYawDegrees, 0f);
                Vector3 right = rotation * Vector3.right;
                Vector3 up = rotation * Vector3.up;
                Vector3 extent = islandVisibleBounds.extents;
                float halfWidth = Mathf.Abs(right.x) * extent.x + Mathf.Abs(right.y) * extent.y +
                    Mathf.Abs(right.z) * extent.z;
                float halfHeight = Mathf.Abs(up.x) * extent.x + Mathf.Abs(up.y) * extent.y +
                    Mathf.Abs(up.z) * extent.z;
                float screenHeight = Mathf.Max(1f, Screen.height);
                float topReserve = Mathf.Clamp((GetTopBarTop() + GetTopBarHeight() + 16f) / screenHeight, 0.06f, 0.3f);
                const float bottomReserve = 0.055f;
                float visibleHeight = Mathf.Max(0.5f, 1f - topReserve - bottomReserve);
                float sizeForWidth = halfWidth / (Mathf.Max(0.1f, gameCamera.aspect) * 0.93f);
                float sizeForHeight = halfHeight / visibleHeight;
                cameraOrthographicSize = Mathf.Clamp(
                    Mathf.Max(sizeForWidth, sizeForHeight) * 1.06f,
                    MinimumCameraOrthographicSize,
                    MaximumCameraOrthographicSize);
                // Move the frame upwards so the island occupies the clear area below the resource bar.
                cameraOrbitTarget = islandVisibleBounds.center + up *
                    ((topReserve - bottomReserve) * cameraOrthographicSize);
                defaultCameraOrbitDistance = Mathf.Max(72f, islandVisibleBounds.size.magnitude * 1.4f);
            }
            cameraOrbitDistance = defaultCameraOrbitDistance;
            ClampCameraView();
            UpdateCameraPose();
        }

        private void PanCamera(Vector3 mouseDelta)
        {
            float worldUnitsPerPixel = 2f * gameCamera.orthographicSize / Mathf.Max(1, Screen.height);
            Vector3 screenRight = gameCamera.transform.right;
            screenRight.y = 0f;
            screenRight.Normalize();
            Vector3 screenUp = gameCamera.transform.up;
            screenUp.y = 0f;
            screenUp.Normalize();
            Vector3 pan = -screenRight * mouseDelta.x - screenUp * mouseDelta.y;
            cameraOrbitTarget += pan * worldUnitsPerPixel;
            ClampCameraView();
            UpdateCameraPose();
        }

        private void OrbitCamera(Vector3 mouseDelta)
        {
            cameraOrbitYawDegrees = Mathf.Repeat(
                cameraOrbitYawDegrees + mouseDelta.x * CameraOrbitDegreesPerPixel,
                360f);
            cameraOrbitPitchDegrees = Mathf.Clamp(
                cameraOrbitPitchDegrees + mouseDelta.y * CameraOrbitDegreesPerPixel,
                MinimumCameraOrbitPitch,
                MaximumCameraOrbitPitch);
            ClampCameraView();
            UpdateCameraPose();
        }

        private void ClampCameraView()
        {
            if (gameCamera == null)
            {
                return;
            }

            float aspect = Mathf.Max(0.1f, gameCamera.aspect);
            float pitchRadians = cameraOrbitPitchDegrees * Mathf.Deg2Rad;
            float sinePitch = Mathf.Max(Mathf.Sin(pitchRadians), 0.001f);
            float cosinePitch = Mathf.Cos(pitchRadians);
            float waterPlaneOffset = Mathf.Abs(cameraOrbitTarget.y - WaterPlaneHeight) * cosinePitch / sinePitch;
            // Reserve the complete orthographic footprint after projecting it onto the water plane.
            float viewExtentPerSize = aspect + 1f / sinePitch;
            float availableHalfExtent = FloodwaterPlaneSize * 0.5f - WaterEdgePadding - waterPlaneOffset;
            float maximumOrthographicSize = Mathf.Min(
                MaximumCameraOrthographicSize,
                Mathf.Max(MinimumCameraOrthographicSize, availableHalfExtent / viewExtentPerSize));

            cameraOrthographicSize = Mathf.Min(cameraOrthographicSize, maximumOrthographicSize);
            gameCamera.orthographicSize = cameraOrthographicSize;

            // Keep the bottom of the orthographic frustum above the water plane. At
            // large zoom-out values the fixed orbit distance could put that edge
            // below sea level, exposing the camera's solid-color background.
            float requiredOrbitDistance =
                (WaterPlaneHeight + WaterPlaneClearance - cameraOrbitTarget.y +
                 cameraOrthographicSize * cosinePitch) / sinePitch + gameCamera.nearClipPlane;
            cameraOrbitDistance = Mathf.Max(defaultCameraOrbitDistance, requiredOrbitDistance);

            float viewHalfExtent = cameraOrthographicSize * viewExtentPerSize + waterPlaneOffset + WaterEdgePadding;
            float maximumTargetOffset = Mathf.Max(0f, FloodwaterPlaneSize * 0.5f - viewHalfExtent);
            cameraOrbitTarget.x = Mathf.Clamp(cameraOrbitTarget.x, -maximumTargetOffset, maximumTargetOffset);
            cameraOrbitTarget.z = Mathf.Clamp(cameraOrbitTarget.z, -maximumTargetOffset, maximumTargetOffset);
        }

        private void UpdateCameraPose()
        {
            Quaternion cameraRotation = Quaternion.Euler(cameraOrbitPitchDegrees, cameraOrbitYawDegrees, 0f);
            gameCamera.transform.SetPositionAndRotation(
                cameraOrbitTarget + cameraRotation * Vector3.back * cameraOrbitDistance,
                cameraRotation);
        }

        private Rect GetPanelRect()
        {
            float panelTop = GetTopBarTop() + GetTopBarHeight() + 10f;
            float height = Mathf.Max(360f, Mathf.Min(620f, Screen.height - panelTop - 16f));
            return new Rect(16f + SidebarCategoryButtonSize + 10f, panelTop, 430f, height);
        }

        private Rect GetSidebarCategoryButtonRect(int index)
        {
            if (index != (int)SidebarCategory.Buildings)
            {
                return Rect.zero;
            }

            return new Rect(16f, GetTopBarTop() + GetTopBarHeight() + 10f,
                SidebarCategoryButtonSize, SidebarCategoryButtonSize);
        }

        private Rect GetTopBarRect()
        {
            return new Rect(0f, GetTopBarTop(), Screen.width, GetTopBarHeight());
        }

        private static float GetTopBarTop()
        {
            return 0f;
        }

        private static float GetTopBarHeight()
        {
            return Mathf.Clamp(Screen.height * 0.072f, 52f, 76f);
        }

        private bool IsPointerOverUi(Vector2 pointer, Rect panelRect, Rect topBarRect, bool isPanelOpen)
        {
            if (topBarRect.Contains(pointer) || GetResourceStripRect(topBarRect).Contains(pointer) ||
                (isPanelOpen && panelRect.Contains(pointer)))
            {
                return true;
            }

            if (isWeatherMenuOpen && GetWeatherMenuRect(topBarRect).Contains(pointer))
            {
                return true;
            }

            if (isResourceMenuOpen && GetResourceMenuRect(topBarRect).Contains(pointer))
            {
                return true;
            }

            Rect buildingCategoryRect = GetSidebarCategoryButtonRect((int)SidebarCategory.Buildings);
            if (buildingCategoryRect.Contains(pointer))
            {
                return true;
            }

            return false;
        }

        private void EnsureGuiStyles()
        {
            EnsureSidebarCategoryUi();
            EnsureSidebarCategoryStyles();
            if (panelStyle != null)
            {
                return;
            }

            Texture2D panelTexture = MakeUiTexture(new Color(0.035f, 0.08f, 0.083f, 0.94f));
            Texture2D cardTexture = MakeUiTexture(new Color(0.11f, 0.17f, 0.15f, 0.95f));
            Texture2D selectedCardTexture = MakeUiTexture(new Color(0.19f, 0.28f, 0.21f, 0.98f));
            Texture2D hoverTexture = MakeUiTexture(new Color(0.24f, 0.36f, 0.29f, 0.98f));
            Texture2D activeTexture = MakeUiTexture(new Color(0.31f, 0.43f, 0.32f, 1f));
            Texture2D clearTexture = MakeUiTexture(new Color(1f, 1f, 1f, 0f));
            panelStyle = new GUIStyle(GUI.skin.box);
            panelStyle.normal.background = panelTexture;
            panelStyle.border = new RectOffset(12, 12, 12, 12);

            headerResourceValueStyle = CreateHeaderLabelStyle(12, FontStyle.Bold, TextAnchor.MiddleCenter,
                new Color(0.94f, 0.96f, 0.91f));
            headerResourceValueStyle.wordWrap = false;

            topHudSmallLabelStyle = CreateHeaderLabelStyle(10, FontStyle.Normal, TextAnchor.MiddleLeft,
                new Color(0.91f, 0.94f, 0.95f));
            topHudClockStyle = CreateHeaderLabelStyle(18, FontStyle.Normal, TextAnchor.MiddleCenter,
                new Color(0.96f, 0.97f, 0.98f));
            Texture2D speedHoverTexture = MakeRoundedUiTexture(64, 64, 18,
                new Color(0.54f, 0.63f, 0.71f, 0.20f));
            Texture2D speedSelectedTexture = MakeRoundedUiTexture(64, 64, 18,
                new Color(0.58f, 0.66f, 0.75f, 0.48f));
            Texture2D speedSelectedHoverTexture = MakeRoundedUiTexture(64, 64, 18,
                new Color(0.68f, 0.75f, 0.82f, 0.58f));
            topHudSpeedStyle = CreateButtonStyle(
                clearTexture, speedHoverTexture,
                MakeRoundedUiTexture(64, 64, 18, new Color(0.63f, 0.70f, 0.78f, 0.34f)));
            topHudSpeedStyle.alignment = TextAnchor.MiddleCenter;
            topHudSpeedStyle.fontSize = 13;
            topHudSpeedStyle.fontStyle = FontStyle.Bold;
            topHudSpeedStyle.border = new RectOffset(18, 18, 18, 18);
            topHudSpeedStyle.normal.textColor = new Color(0.92f, 0.95f, 0.96f);
            topHudSpeedStyle.hover.textColor = Color.white;
            topHudSpeedSelectedStyle = CreateButtonStyle(
                speedSelectedTexture, speedSelectedHoverTexture,
                MakeRoundedUiTexture(64, 64, 18, new Color(0.66f, 0.73f, 0.81f, 0.60f)));
            topHudSpeedSelectedStyle.alignment = TextAnchor.MiddleCenter;
            topHudSpeedSelectedStyle.fontSize = 13;
            topHudSpeedSelectedStyle.fontStyle = FontStyle.Bold;
            topHudSpeedSelectedStyle.border = new RectOffset(18, 18, 18, 18);
            topHudSpeedSelectedStyle.normal.textColor = Color.white;
            topHudSpeedSelectedStyle.hover.textColor = Color.white;
            topHudMoreStyle = CreateButtonStyle(
                clearTexture, speedHoverTexture, speedSelectedTexture);
            topHudMoreStyle.alignment = TextAnchor.MiddleCenter;
            topHudMoreStyle.fontSize = 12;
            topHudMoreStyle.fontStyle = FontStyle.Bold;
            topHudMoreStyle.border = new RectOffset(18, 18, 18, 18);
            topHudMoreStyle.normal.textColor = new Color(0.93f, 0.96f, 0.97f);
            topHudMoreStyle.hover.textColor = Color.white;
            topHudTabStyle = CreateButtonStyle(clearTexture, clearTexture, clearTexture);
            topHudTabStyle.alignment = TextAnchor.MiddleCenter;
            topHudTabStyle.fontSize = 16;
            topHudTabStyle.fontStyle = FontStyle.Normal;
            topHudTabStyle.normal.textColor = new Color(0.89f, 0.93f, 0.95f);
            topHudTabStyle.hover.textColor = Color.white;
            topHudTabSelectedStyle = CreateButtonStyle(clearTexture, clearTexture, clearTexture);
            topHudTabSelectedStyle.alignment = TextAnchor.MiddleCenter;
            topHudTabSelectedStyle.fontSize = 16;
            topHudTabSelectedStyle.fontStyle = FontStyle.Bold;
            topHudTabSelectedStyle.normal.textColor = Color.white;
            topHudTabSelectedStyle.hover.textColor = Color.white;
            topHudPopupStyle = new GUIStyle(GUI.skin.box);
            topHudPopupStyle.normal.background = MakeRoundedUiTexture(128, 128, 22,
                new Color(0.035f, 0.065f, 0.067f, 0.97f));
            topHudPopupStyle.border = new RectOffset(22, 22, 22, 22);
            topHudPopupStyle.padding = new RectOffset(12, 12, 10, 10);

            weatherButtonStyle = CreateButtonStyle(clearTexture, clearTexture, clearTexture);
            weatherButtonStyle.fontSize = 11;
            weatherButtonStyle.fontStyle = FontStyle.Bold;
            weatherButtonStyle.alignment = TextAnchor.MiddleCenter;
            weatherButtonStyle.padding = new RectOffset(2, 2, 1, 1);
            weatherOptionStyle = CreateButtonStyle(
                MakeUiTexture(new Color(0.075f, 0.13f, 0.13f, 0.98f)),
                MakeUiTexture(new Color(0.14f, 0.22f, 0.19f, 1f)),
                MakeUiTexture(new Color(0.18f, 0.27f, 0.21f, 1f)));
            weatherOptionStyle.fontSize = 12;
            weatherOptionStyle.alignment = TextAnchor.MiddleCenter;
            weatherOptionStyle.padding = new RectOffset(3, 3, 2, 2);
            weatherOptionSelectedStyle = CreateButtonStyle(
                MakeUiTexture(new Color(0.25f, 0.31f, 0.21f, 1f)),
                MakeUiTexture(new Color(0.32f, 0.39f, 0.26f, 1f)),
                MakeUiTexture(new Color(0.36f, 0.43f, 0.28f, 1f)));
            weatherOptionSelectedStyle.fontSize = 12;
            weatherOptionSelectedStyle.fontStyle = FontStyle.Bold;
            weatherOptionSelectedStyle.alignment = TextAnchor.MiddleCenter;
            weatherOptionSelectedStyle.padding = new RectOffset(3, 3, 2, 2);
            weatherOptionStyle.normal.textColor = new Color(0.82f, 0.88f, 0.83f);
            weatherOptionStyle.hover.textColor = Color.white;
            weatherOptionSelectedStyle.normal.textColor = new Color(0.12f, 0.15f, 0.11f);
            weatherOptionSelectedStyle.hover.textColor = new Color(0.12f, 0.15f, 0.11f);
            weatherOptionSelectedStyle.normal.background = MakeUiTexture(new Color(0.78f, 0.65f, 0.34f, 1f));
            weatherOptionSelectedStyle.hover.background = MakeUiTexture(new Color(0.88f, 0.75f, 0.42f, 1f));
            weatherOptionSelectedStyle.onNormal.background = weatherOptionSelectedStyle.normal.background;
            weatherOptionSelectedStyle.onHover.background = weatherOptionSelectedStyle.hover.background;
            weatherOptionSelectedStyle.onActive.background = weatherOptionSelectedStyle.hover.background;
            weatherOptionSelectedStyle.onFocused.background = weatherOptionSelectedStyle.hover.background;
            weatherOptionSelectedStyle.active.background = weatherOptionSelectedStyle.hover.background;
            weatherOptionSelectedStyle.focused.background = weatherOptionSelectedStyle.hover.background;
            weatherOptionLabelStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 12,
                alignment = TextAnchor.MiddleLeft,
                clipping = TextClipping.Clip
            };
            weatherOptionLabelStyle.normal.textColor = new Color(0.85f, 0.90f, 0.86f);
            weatherOptionSelectedLabelStyle = new GUIStyle(weatherOptionLabelStyle)
            {
                fontStyle = FontStyle.Bold
            };
            weatherOptionSelectedLabelStyle.normal.textColor = new Color(0.12f, 0.15f, 0.11f);
            weatherMenuTitleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 14,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleLeft,
                clipping = TextClipping.Clip
            };
            weatherMenuTitleStyle.normal.textColor = new Color(0.9f, 0.93f, 0.82f);
            weatherToggleOffTrackTexture = MakeUiTexture(new Color(0.12f, 0.20f, 0.20f, 1f));
            weatherToggleOnTrackTexture = MakeUiTexture(new Color(0.25f, 0.30f, 0.17f, 1f));
            weatherToggleKnobTexture = MakeUiTexture(new Color(0.98f, 0.91f, 0.70f, 1f));
            weatherTimeValueStyle = new GUIStyle(weatherMenuTitleStyle)
            {
                fontSize = 11,
                alignment = TextAnchor.MiddleRight
            };
            weatherTimeValueStyle.normal.textColor = new Color(0.96f, 0.89f, 0.67f);
            weatherTimeMarksStyle = new GUIStyle(weatherOptionLabelStyle)
            {
                fontSize = 9,
                alignment = TextAnchor.MiddleCenter
            };
            weatherTimeMarksStyle.normal.textColor = new Color(0.67f, 0.76f, 0.68f);
            weatherTimeSliderStyle = new GUIStyle(GUI.skin.horizontalSlider)
            {
                fixedHeight = 6f,
                margin = new RectOffset(0, 0, 6, 6)
            };
            weatherTimeSliderStyle.normal.background = weatherToggleOffTrackTexture;
            weatherTimeSliderThumbStyle = new GUIStyle(GUI.skin.horizontalSliderThumb)
            {
                fixedWidth = 13f,
                fixedHeight = 13f
            };
            weatherTimeSliderThumbStyle.normal.background = weatherToggleKnobTexture;
            weatherTimeSliderThumbStyle.hover.background = weatherToggleKnobTexture;
            weatherTimeSliderThumbStyle.active.background = weatherToggleKnobTexture;

            titleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 17,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleLeft
            };
            titleStyle.normal.textColor = new Color(0.9f, 0.93f, 0.82f);

            mutedLabelStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 12,
                wordWrap = true,
                alignment = TextAnchor.MiddleLeft
            };
            mutedLabelStyle.normal.textColor = new Color(0.67f, 0.76f, 0.68f);

            cardLabelStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 12,
                wordWrap = true,
                alignment = TextAnchor.MiddleLeft
            };
            cardLabelStyle.normal.textColor = new Color(0.91f, 0.92f, 0.82f);

            cardStyle = CreateButtonStyle(cardTexture, hoverTexture, activeTexture);
            cardStyle.border = new RectOffset(9, 9, 9, 9);
            selectedCardStyle = CreateButtonStyle(selectedCardTexture, hoverTexture, activeTexture);
            selectedCardStyle.border = new RectOffset(9, 9, 9, 9);
            transparentButtonStyle = CreateButtonStyle(clearTexture, clearTexture, clearTexture);
            EnsureSidebarCategoryStyles();
        }

        private GUIStyle CreateButtonStyle(Texture2D normal, Texture2D hover, Texture2D active)
        {
            GUIStyle style = new GUIStyle(GUI.skin.button);
            style.normal.background = normal;
            style.hover.background = hover;
            style.active.background = active;
            style.focused.background = hover;
            style.onNormal.background = normal;
            style.onHover.background = hover;
            style.onActive.background = active;
            style.onFocused.background = hover;
            style.border = new RectOffset(8, 8, 8, 8);
            return style;
        }

        private Texture2D MakeUiTexture(Color color)
        {
            Texture2D texture = new Texture2D(2, 2, TextureFormat.RGBA32, false)
            {
                name = "Last Landfall UI tint",
                hideFlags = HideFlags.HideAndDontSave
            };
            texture.SetPixels(new[] { color, color, color, color });
            texture.Apply();
            ownedUiTextures.Add(texture);
            return texture;
        }

        private Texture2D MakeRoundedUiTexture(int width, int height, float radius, Color color)
        {
            Texture2D texture = new Texture2D(width, height, TextureFormat.RGBA32, false)
            {
                name = "Last Landfall rounded HUD texture",
                hideFlags = HideFlags.HideAndDontSave,
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Clamp
            };
            Color[] pixels = new Color[width * height];
            float left = radius;
            float right = width - radius;
            float bottom = radius;
            float top = height - radius;
            float radiusSquared = radius * radius;
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    float nearestX = Mathf.Clamp(x + 0.5f, left, right);
                    float nearestY = Mathf.Clamp(y + 0.5f, bottom, top);
                    float dx = x + 0.5f - nearestX;
                    float dy = y + 0.5f - nearestY;
                    if (dx * dx + dy * dy <= radiusSquared)
                    {
                        pixels[y * width + x] = color;
                    }
                }
            }

            texture.SetPixels(pixels);
            texture.Apply(false, false);
            ownedUiTextures.Add(texture);
            return texture;
        }

        private void EnsureSidebarCategoryUi()
        {
            if (SidebarCategoryArtwork.IsAvailable)
            {
                return;
            }

            if (sidebarCategoryIcons != null && sidebarCategoryIcons.Length == SidebarCategoryCount)
            {
                bool allLoaded = true;
                for (int i = 0; i < sidebarCategoryIcons.Length; i++)
                {
                    allLoaded &= sidebarCategoryIcons[i] != null;
                }

                if (allLoaded)
                {
                    return;
                }
            }

            sidebarCategoryIcons = new Texture2D[SidebarCategoryCount];
            for (int i = 0; i < SidebarCategoryCount; i++)
            {
                sidebarCategoryIcons[i] = CreateSidebarCategoryIcon(i);
            }
        }

        private void EnsureSidebarCategoryStyles()
        {
            if (sidebarCategoryButtonStyle != null && sidebarCategorySelectedButtonStyle != null &&
                sidebarCategoryLabelStyle != null && closeButtonStyle != null)
            {
                return;
            }

            if (cardStyle == null || selectedCardStyle == null)
            {
                return;
            }

            sidebarCategoryButtonStyle = CreateButtonStyle(cardStyle.normal.background,
                cardStyle.hover.background, cardStyle.active.background);
            sidebarCategoryButtonStyle.padding = new RectOffset(2, 2, 2, 2);
            sidebarCategorySelectedButtonStyle = CreateButtonStyle(selectedCardStyle.normal.background,
                selectedCardStyle.hover.background, selectedCardStyle.active.background);
            sidebarCategorySelectedButtonStyle.padding = new RectOffset(2, 2, 2, 2);
            sidebarCategoryLabelStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 12,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter
            };
            sidebarCategoryLabelStyle.normal.textColor = new Color(0.95f, 0.94f, 0.78f);
            closeButtonStyle = CreateButtonStyle(cardStyle.normal.background,
                cardStyle.hover.background, cardStyle.active.background);
            closeButtonStyle.fontSize = 19;
            closeButtonStyle.fontStyle = FontStyle.Bold;
            closeButtonStyle.alignment = TextAnchor.MiddleCenter;
        }

        private Texture2D CreateSidebarCategoryIcon(int categoryIndex)
        {
            Texture2D texture = new Texture2D(64, 64, TextureFormat.RGBA32, false)
            {
                name = "Last Landfall sidebar category " + categoryIndex,
                hideFlags = HideFlags.HideAndDontSave,
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Clamp
            };
            Color color = categoryIndex == (int)SidebarCategory.Technology
                ? new Color(0.49f, 0.85f, 0.78f, 1f)
                : categoryIndex == (int)SidebarCategory.Culture
                    ? new Color(0.91f, 0.76f, 0.46f, 1f)
                    : new Color(0.91f, 0.93f, 0.81f, 1f);

            if (categoryIndex == (int)SidebarCategory.Technology)
            {
                DrawIconLine(texture, new Vector2(32f, 16f), new Vector2(32f, 38f), 3f, color);
                DrawIconLine(texture, new Vector2(16f, 26f), new Vector2(32f, 38f), 3f, color);
                DrawIconLine(texture, new Vector2(48f, 26f), new Vector2(32f, 38f), 3f, color);
                DrawIconLine(texture, new Vector2(22f, 16f), new Vector2(32f, 16f), 3f, color);
                DrawIconLine(texture, new Vector2(42f, 16f), new Vector2(32f, 16f), 3f, color);
                DrawIconCircle(texture, new Vector2(32f, 42f), 5f, 3f, color);
                DrawIconCircle(texture, new Vector2(16f, 24f), 4f, 3f, color);
                DrawIconCircle(texture, new Vector2(48f, 24f), 4f, 3f, color);
                DrawIconCircle(texture, new Vector2(22f, 14f), 3f, 2.5f, color);
                DrawIconCircle(texture, new Vector2(42f, 14f), 3f, 2.5f, color);
            }
            else if (categoryIndex == (int)SidebarCategory.Culture)
            {
                DrawIconLine(texture, new Vector2(11f, 17f), new Vector2(29f, 13f), 3f, color);
                DrawIconLine(texture, new Vector2(29f, 13f), new Vector2(29f, 46f), 3f, color);
                DrawIconLine(texture, new Vector2(29f, 46f), new Vector2(11f, 42f), 3f, color);
                DrawIconLine(texture, new Vector2(11f, 42f), new Vector2(11f, 17f), 3f, color);
                DrawIconLine(texture, new Vector2(35f, 13f), new Vector2(53f, 17f), 3f, color);
                DrawIconLine(texture, new Vector2(53f, 17f), new Vector2(53f, 42f), 3f, color);
                DrawIconLine(texture, new Vector2(53f, 42f), new Vector2(35f, 46f), 3f, color);
                DrawIconLine(texture, new Vector2(35f, 46f), new Vector2(35f, 13f), 3f, color);
                DrawIconLine(texture, new Vector2(16f, 23f), new Vector2(25f, 21f), 2f, color);
                DrawIconLine(texture, new Vector2(16f, 30f), new Vector2(25f, 28f), 2f, color);
                DrawIconLine(texture, new Vector2(39f, 21f), new Vector2(48f, 23f), 2f, color);
                DrawIconLine(texture, new Vector2(39f, 28f), new Vector2(48f, 30f), 2f, color);
            }
            else
            {
                DrawIconLine(texture, new Vector2(10f, 34f), new Vector2(32f, 52f), 4f, color);
                DrawIconLine(texture, new Vector2(32f, 52f), new Vector2(54f, 34f), 4f, color);
                DrawIconLine(texture, new Vector2(16f, 35f), new Vector2(16f, 13f), 3f, color);
                DrawIconLine(texture, new Vector2(48f, 35f), new Vector2(48f, 13f), 3f, color);
                DrawIconLine(texture, new Vector2(16f, 13f), new Vector2(48f, 13f), 3f, color);
                DrawIconLine(texture, new Vector2(27f, 13f), new Vector2(27f, 28f), 2.5f, color);
                DrawIconLine(texture, new Vector2(37f, 13f), new Vector2(37f, 28f), 2.5f, color);
                DrawIconLine(texture, new Vector2(27f, 28f), new Vector2(37f, 28f), 2.5f, color);
            }

            texture.Apply(false, false);
            ownedUiTextures.Add(texture);
            return texture;
        }

        private static void DrawIconLine(Texture2D texture, Vector2 start, Vector2 end, float thickness, Color color)
        {
            Vector2 delta = end - start;
            float lengthSquared = Mathf.Max(0.001f, delta.sqrMagnitude);
            float radius = thickness * 0.5f;
            int minX = Mathf.Max(0, Mathf.FloorToInt(Mathf.Min(start.x, end.x) - radius));
            int maxX = Mathf.Min(texture.width - 1, Mathf.CeilToInt(Mathf.Max(start.x, end.x) + radius));
            int minY = Mathf.Max(0, Mathf.FloorToInt(Mathf.Min(start.y, end.y) - radius));
            int maxY = Mathf.Min(texture.height - 1, Mathf.CeilToInt(Mathf.Max(start.y, end.y) + radius));
            for (int y = minY; y <= maxY; y++)
            {
                for (int x = minX; x <= maxX; x++)
                {
                    Vector2 point = new Vector2(x + 0.5f, y + 0.5f);
                    float progress = Mathf.Clamp01(Vector2.Dot(point - start, delta) / lengthSquared);
                    if ((point - (start + delta * progress)).sqrMagnitude <= radius * radius)
                    {
                        texture.SetPixel(x, y, color);
                    }
                }
            }
        }

        private static void DrawIconCircle(Texture2D texture, Vector2 center, float radius, float thickness, Color color)
        {
            float innerRadius = Mathf.Max(0f, radius - thickness * 0.5f);
            float outerRadius = radius + thickness * 0.5f;
            int minX = Mathf.Max(0, Mathf.FloorToInt(center.x - outerRadius));
            int maxX = Mathf.Min(texture.width - 1, Mathf.CeilToInt(center.x + outerRadius));
            int minY = Mathf.Max(0, Mathf.FloorToInt(center.y - outerRadius));
            int maxY = Mathf.Min(texture.height - 1, Mathf.CeilToInt(center.y + outerRadius));
            for (int y = minY; y <= maxY; y++)
            {
                for (int x = minX; x <= maxX; x++)
                {
                    float distance = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), center);
                    if (distance >= innerRadius && distance <= outerRadius)
                    {
                        texture.SetPixel(x, y, color);
                    }
                }
            }
        }

        private GUIStyle CreateHeaderLabelStyle(int fontSize, FontStyle fontStyle, TextAnchor alignment, Color color)
        {
            GUIStyle style = new GUIStyle(GUI.skin.label)
            {
                fontSize = fontSize,
                fontStyle = fontStyle,
                alignment = alignment,
                clipping = TextClipping.Clip
            };
            style.normal.textColor = color;
            return style;
        }

        private void DrawTopBar(Rect rect)
        {
            EnsureHeaderAssetsLoaded();
            DrawWeatherControl(rect);
            DrawClockAndSpeed(rect);
            DrawKnowledgeTabs(rect);
            DrawHeaderButtons(rect);
            DrawResourceStrip(rect);
            if (isWeatherMenuOpen)
            {
                DrawWeatherMenu(rect);
            }

            if (isResourceMenuOpen)
            {
                DrawResourceMenu(rect);
            }
        }

        private void DrawWeatherControl(Rect topBarRect)
        {
            if (weatherSystem == null || weatherButtonStyle == null)
            {
                return;
            }

            Rect buttonRect = GetWeatherButtonRect(topBarRect);
            bool clicked = GUI.Button(buttonRect,
                new GUIContent(string.Empty, "当前天气：" + weatherSystem.CurrentWeatherName + "。点击切换。"),
                weatherButtonStyle);

            EnsureWeatherIcons();
            int weatherIndex = Mathf.Clamp((int)weatherSystem.CurrentWeather, 0, weatherIcons.Length - 1);
            float scale = GetHudScale();
            float iconSize = 27f * scale;
            Rect iconRect = new Rect(buttonRect.x + 7f * scale,
                buttonRect.center.y - iconSize * 0.5f, iconSize, iconSize);
            GUI.DrawTexture(iconRect, weatherIcons[weatherIndex], ScaleMode.ScaleToFit, true);
            topHudSmallLabelStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(15f * scale), 11, 16);
            topHudSmallLabelStyle.alignment = TextAnchor.MiddleLeft;
            GUI.Label(new Rect(iconRect.xMax + 5f * scale, buttonRect.y,
                    buttonRect.xMax - iconRect.xMax - 8f * scale, buttonRect.height),
                GetShortWeatherName(weatherSystem.CurrentWeather), topHudSmallLabelStyle);

            DrawHudDivider(new Rect(140f * scale, topBarRect.y + 13f * scale,
                Mathf.Max(1f, scale), topBarRect.height - 26f * scale), new Color(0.86f, 0.91f, 0.94f, 0.48f));

            if (clicked)
            {
                isWeatherMenuOpen = !isWeatherMenuOpen;
                if (isWeatherMenuOpen)
                {
                    isResourceMenuOpen = false;
                    isBuildMenuOpen = false;
                }
            }
        }

        private Rect GetWeatherButtonRect(Rect topBarRect)
        {
            float scale = GetHudScale();
            return new Rect(18f * scale, topBarRect.y + 5f * scale,
                116f * scale, topBarRect.height - 10f * scale);
        }

        private void DrawClockAndSpeed(Rect topBarRect)
        {
            if (weatherSystem == null || topHudClockStyle == null || topHudSpeedStyle == null ||
                topHudSpeedSelectedStyle == null)
            {
                return;
            }

            float scale = GetHudScale();
            Rect clockRect = new Rect(151f * scale, topBarRect.y + 4f * scale,
                75f * scale, topBarRect.height - 8f * scale);

            int totalMinutes = Mathf.FloorToInt(weatherSystem.TimeOfDayHours * 60f) % (24 * 60);
            string timeText = string.Format(CultureInfo.InvariantCulture, "{0:00}:{1:00}",
                totalMinutes / 60, totalMinutes % 60);
            topHudClockStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(18f * scale), 13, 20);
            GUI.Label(clockRect, timeText, topHudClockStyle);
            DrawHudDivider(new Rect(235f * scale, topBarRect.y + 13f * scale,
                Mathf.Max(1f, scale), topBarRect.height - 26f * scale), new Color(0.86f, 0.91f, 0.94f, 0.48f));

            float buttonWidth = 38f * scale;
            float buttonHeight = 29f * scale;
            float buttonGap = 4f * scale;
            float buttonsX = 246f * scale;
            float buttonY = topBarRect.center.y - buttonHeight * 0.5f;
            for (int i = 0; i < 3; i++)
            {
                Rect speedRect = new Rect(buttonsX + i * (buttonWidth + buttonGap), buttonY,
                    buttonWidth, buttonHeight);
                bool selected = selectedSimulationSpeedIndex == i;
                if (GUI.Button(speedRect, (i + 1) + "×",
                        selected ? topHudSpeedSelectedStyle : topHudSpeedStyle))
                {
                    selectedSimulationSpeedIndex = i;
                    weatherSystem.SetSimulationSpeed(i + 1);
                    statusMessage = "时间速度设为 " + (i + 1) + "×。";
                }
            }
        }

        private void DrawKnowledgeTabs(Rect topBarRect)
        {
            if (topHudTabStyle == null || topHudTabSelectedStyle == null)
            {
                return;
            }

            float scale = GetHudScale();
            SidebarCategory[] categories = { SidebarCategory.Technology, SidebarCategory.Culture };
            string[] labels = { "科技", "文化" };
            for (int i = 0; i < categories.Length; i++)
            {
                Rect tabRect = GetKnowledgeTabRect(topBarRect, i);
                bool selected = isBuildMenuOpen && activeSidebarCategory == categories[i];
                if (GUI.Button(tabRect, labels[i], selected ? topHudTabSelectedStyle : topHudTabStyle))
                {
                    SelectSidebarCategory(categories[i]);
                }

                if (selected)
                {
                    float underlineWidth = 44f * scale;
                    DrawHudDivider(new Rect(tabRect.center.x - underlineWidth * 0.5f,
                        tabRect.yMax - 2f * scale, underlineWidth, Mathf.Max(1f, 1.5f * scale)),
                        new Color(0.50f, 0.84f, 0.85f, 0.92f));
                }
            }
        }

        private Rect GetKnowledgeTabRect(Rect topBarRect, int index)
        {
            float scale = GetHudScale();
            float tabWidth = 78f * scale;
            float gap = 18f * scale;
            float groupWidth = tabWidth * 2f + gap;
            float x = (Screen.width - groupWidth) * 0.5f + index * (tabWidth + gap);
            float height = 34f * scale;
            return new Rect(x, topBarRect.center.y - height * 0.5f, tabWidth, height);
        }

        private void DrawResourceStrip(Rect topBarRect)
        {
            if (topHudMoreStyle == null)
            {
                return;
            }

            float scale = GetHudScale();
            Rect stripRect = GetResourceStripRect(topBarRect);
            float rowHeight = 39f * scale;
            DrawHudDivider(new Rect(stripRect.x, stripRect.y, Mathf.Max(1f, scale),
                rowHeight * VisibleHeaderResourceCount), new Color(0.69f, 0.84f, 0.87f, 0.62f));

            for (int i = 0; i < VisibleHeaderResourceCount; i++)
            {
                Rect itemRect = GetResourceItemRect(topBarRect, i);
                topHudSmallLabelStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(14f * scale), 10, 15);
                topHudSmallLabelStyle.alignment = TextAnchor.MiddleLeft;
                GUI.Label(new Rect(itemRect.x + 12f * scale, itemRect.y, itemRect.width * 0.58f,
                    itemRect.height), HeaderResourceDisplayNames[i], topHudSmallLabelStyle);
                headerResourceValueStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(14f * scale), 10, 15);
                headerResourceValueStyle.alignment = TextAnchor.MiddleRight;
                GUI.Label(new Rect(itemRect.x + itemRect.width * 0.58f, itemRect.y,
                    itemRect.width * 0.42f - 8f * scale, itemRect.height), GetHeaderResourceAmount(i),
                    headerResourceValueStyle);
                if (i < VisibleHeaderResourceCount - 1)
                {
                    DrawHudDivider(new Rect(itemRect.x + 12f * scale, itemRect.yMax - 1f * scale,
                        itemRect.width - 8f * scale, Mathf.Max(1f, scale)),
                        new Color(0.69f, 0.84f, 0.87f, 0.30f));
                }
            }

            Rect moreRect = GetResourceMoreButtonRect(topBarRect);
            if (GUI.Button(moreRect, "更多   ›", topHudMoreStyle))
            {
                isResourceMenuOpen = !isResourceMenuOpen;
                if (isResourceMenuOpen)
                {
                    isWeatherMenuOpen = false;
                    isBuildMenuOpen = false;
                }
            }
        }

        private Rect GetResourceItemRect(Rect topBarRect, int index)
        {
            float scale = GetHudScale();
            Rect stripRect = GetResourceStripRect(topBarRect);
            float rowHeight = 39f * scale;
            return new Rect(stripRect.x + 1f * scale,
                stripRect.y + index * rowHeight,
                stripRect.width - 2f * scale, rowHeight);
        }

        private Rect GetResourceMoreButtonRect(Rect topBarRect)
        {
            float scale = GetHudScale();
            Rect stripRect = GetResourceStripRect(topBarRect);
            float buttonHeight = 30f * scale;
            return new Rect(stripRect.x + 6f * scale,
                stripRect.y + VisibleHeaderResourceCount * 39f * scale,
                stripRect.width - 12f * scale, buttonHeight);
        }

        private Rect GetResourceStripRect(Rect topBarRect)
        {
            float scale = GetHudScale();
            float width = 154f * scale;
            float height = (VisibleHeaderResourceCount * 39f + 30f) * scale;
            float x = Screen.width - width - 12f * scale;
            float y = Mathf.Max(topBarRect.yMax + 14f * scale, Screen.height * 0.22f);
            return new Rect(x, y, width, height);
        }

        private Rect GetResourceMenuRect(Rect topBarRect)
        {
            float scale = GetHudScale();
            Rect stripRect = GetResourceStripRect(topBarRect);
            float width = 270f * scale;
            float height = 126f * scale;
            return new Rect(Mathf.Max(8f, stripRect.x - width - 8f * scale),
                stripRect.y, width, height);
        }

        private void DrawResourceMenu(Rect topBarRect)
        {
            if (topHudPopupStyle == null || headerResourceIcons == null)
            {
                return;
            }

            Rect menuRect = GetResourceMenuRect(topBarRect);
            GUI.Box(menuRect, GUIContent.none, topHudPopupStyle);
            float scale = GetHudScale();
            topHudSmallLabelStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(13f * scale), 10, 14);
            topHudSmallLabelStyle.fontStyle = FontStyle.Bold;
            GUI.Label(new Rect(menuRect.x + 12f * scale, menuRect.y + 8f * scale,
                    menuRect.width - 24f * scale, 20f * scale), "其他物资", topHudSmallLabelStyle);
            topHudSmallLabelStyle.fontStyle = FontStyle.Normal;
            for (int slot = VisibleHeaderResourceCount; slot < TotalHeaderResourceCount; slot++)
            {
                int localIndex = slot - VisibleHeaderResourceCount;
                int column = localIndex % 2;
                int row = localIndex / 2;
                float columnWidth = (menuRect.width - 28f * scale) * 0.5f;
                Rect itemRect = new Rect(menuRect.x + 14f * scale + column * columnWidth,
                    menuRect.y + 36f * scale + row * 37f * scale, columnWidth, 30f * scale);
                if (slot < headerResourceIcons.Length && headerResourceIcons[slot] != null)
                {
                    Rect iconRect = new Rect(itemRect.x, itemRect.center.y - 11f * scale,
                        22f * scale, 22f * scale);
                    GUI.DrawTexture(iconRect, headerResourceIcons[slot], ScaleMode.ScaleToFit, true);
                }

                topHudSmallLabelStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(10f * scale), 8, 11);
                GUI.Label(new Rect(itemRect.x + 27f * scale, itemRect.y,
                        columnWidth - 60f * scale, itemRect.height), HeaderResourceDisplayNames[slot],
                    topHudSmallLabelStyle);
                headerResourceValueStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(11f * scale), 9, 12);
                headerResourceValueStyle.alignment = TextAnchor.MiddleRight;
                GUI.Label(new Rect(itemRect.xMax - 34f * scale, itemRect.y,
                        31f * scale, itemRect.height), GetHeaderResourceAmount(slot), headerResourceValueStyle);
            }
        }

        private string GetHeaderResourceAmount(int index)
        {
            return index == 0 ? wood.ToString("0", CultureInfo.InvariantCulture) : "0";
        }

        private static float GetHudScale()
        {
            return Mathf.Clamp(Screen.height / 900f, 0.72f, 1.1f);
        }

        private static string GetShortWeatherName(IslandWeatherType weather)
        {
            return weather switch
            {
                IslandWeatherType.Clear => "晴天",
                IslandWeatherType.Overcast => "阴天",
                IslandWeatherType.Rain => "雨天",
                IslandWeatherType.Wind => "大风",
                IslandWeatherType.Thunderstorm => "雷雨",
                _ => "晴天"
            };
        }

        private static void DrawHudDivider(Rect rect, Color color)
        {
            Color previousColor = GUI.color;
            GUI.color = color;
            GUI.DrawTexture(rect, Texture2D.whiteTexture, ScaleMode.StretchToFill, true);
            GUI.color = previousColor;
        }

        private void EnsureWeatherIcons()
        {
            if (weatherIcons == null || weatherIcons.Length != 5)
            {
                weatherIcons = new Texture2D[5];
            }

            for (int i = 0; i < weatherIcons.Length; i++)
            {
                if (weatherIcons[i] == null)
                {
                    weatherIcons[i] = CreateWeatherIcon((IslandWeatherType)i);
                }
            }
        }

        private Texture2D CreateWeatherIcon(IslandWeatherType weather)
        {
            Texture2D texture = new Texture2D(64, 64, TextureFormat.RGBA32, false)
            {
                name = "Last Landfall weather icon " + weather,
                hideFlags = HideFlags.HideAndDontSave,
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Clamp
            };
            Color cloud = new Color(0.82f, 0.90f, 0.87f, 1f);
            Color warm = new Color(1f, 0.77f, 0.34f, 1f);
            Color rain = new Color(0.39f, 0.77f, 0.91f, 1f);
            if (weather == IslandWeatherType.Clear)
            {
                FillIconCircle(texture, new Vector2(32f, 33f), 11f, warm);
                Vector2[] directions =
                {
                    new Vector2(0f, 1f), new Vector2(0.7f, 0.7f), new Vector2(1f, 0f),
                    new Vector2(0.7f, -0.7f), new Vector2(0f, -1f), new Vector2(-0.7f, -0.7f),
                    new Vector2(-1f, 0f), new Vector2(-0.7f, 0.7f)
                };
                for (int i = 0; i < directions.Length; i++)
                {
                    DrawIconLine(texture, new Vector2(32f, 33f) + directions[i] * 16f,
                        new Vector2(32f, 33f) + directions[i] * 22f, 3f, warm);
                }
            }
            else if (weather == IslandWeatherType.Wind)
            {
                Color wind = new Color(0.60f, 0.84f, 0.84f, 1f);
                DrawIconLine(texture, new Vector2(10f, 42f), new Vector2(41f, 42f), 4f, wind);
                DrawIconLine(texture, new Vector2(41f, 42f), new Vector2(52f, 35f), 4f, wind);
                DrawIconLine(texture, new Vector2(8f, 31f), new Vector2(48f, 31f), 4f, wind);
                DrawIconLine(texture, new Vector2(48f, 31f), new Vector2(54f, 25f), 4f, wind);
                DrawIconLine(texture, new Vector2(17f, 20f), new Vector2(38f, 20f), 4f, wind);
                DrawIconLine(texture, new Vector2(38f, 20f), new Vector2(45f, 15f), 4f, wind);
            }
            else
            {
                FillIconCircle(texture, new Vector2(22f, 30f), 10f, cloud);
                FillIconCircle(texture, new Vector2(34f, 35f), 13f, cloud);
                FillIconCircle(texture, new Vector2(46f, 29f), 9f, cloud);
                FillIconRect(texture, 18, 19, 50, 29, cloud);
                if (weather == IslandWeatherType.Rain)
                {
                    DrawIconLine(texture, new Vector2(24f, 15f), new Vector2(20f, 7f), 3f, rain);
                    DrawIconLine(texture, new Vector2(35f, 15f), new Vector2(31f, 7f), 3f, rain);
                    DrawIconLine(texture, new Vector2(46f, 15f), new Vector2(42f, 7f), 3f, rain);
                }
                else if (weather == IslandWeatherType.Thunderstorm)
                {
                    DrawIconLine(texture, new Vector2(36f, 20f), new Vector2(28f, 10f), 5f, warm);
                    DrawIconLine(texture, new Vector2(28f, 10f), new Vector2(37f, 10f), 5f, warm);
                    DrawIconLine(texture, new Vector2(37f, 10f), new Vector2(31f, 1f), 5f, warm);
                }
            }

            texture.Apply(false, false);
            ownedUiTextures.Add(texture);
            return texture;
        }

        private static void FillIconCircle(Texture2D texture, Vector2 center, float radius, Color color)
        {
            int minX = Mathf.Max(0, Mathf.FloorToInt(center.x - radius));
            int maxX = Mathf.Min(texture.width - 1, Mathf.CeilToInt(center.x + radius));
            int minY = Mathf.Max(0, Mathf.FloorToInt(center.y - radius));
            int maxY = Mathf.Min(texture.height - 1, Mathf.CeilToInt(center.y + radius));
            float radiusSquared = radius * radius;
            for (int y = minY; y <= maxY; y++)
            {
                for (int x = minX; x <= maxX; x++)
                {
                    if ((new Vector2(x + 0.5f, y + 0.5f) - center).sqrMagnitude <= radiusSquared)
                    {
                        texture.SetPixel(x, y, color);
                    }
                }
            }
        }

        private static void FillIconRect(Texture2D texture, int minX, int minY, int maxX, int maxY, Color color)
        {
            for (int y = minY; y <= maxY; y++)
            {
                for (int x = minX; x <= maxX; x++)
                {
                    texture.SetPixel(x, y, color);
                }
            }
        }

        private Rect GetWeatherMenuRect(Rect topBarRect)
        {
            float scale = Mathf.Clamp(Mathf.Min(Screen.width / 980f, Screen.height / 480f), 0.72f, 1f);
            float menuWidth = 198f * scale;
            float menuHeight = 260f * scale;
            menuWidth = Mathf.Min(menuWidth, Mathf.Max(150f, Screen.width - 16f));
            menuHeight = Mathf.Min(menuHeight, Mathf.Max(150f, Screen.height - 16f));
            float centerX = GetWeatherButtonRect(topBarRect).center.x;
            float x = Mathf.Clamp(centerX - menuWidth * 0.5f, 8f,
                Mathf.Max(8f, Screen.width - menuWidth - 8f));
            float belowTopBar = topBarRect.yMax + 6f;
            float aboveTopBar = topBarRect.yMin - menuHeight - 6f;
            float y = belowTopBar + menuHeight <= Screen.height - 8f
                ? belowTopBar
                : Mathf.Clamp(aboveTopBar, 8f, Mathf.Max(8f, Screen.height - menuHeight - 8f));
            return new Rect(x, y, menuWidth, menuHeight);
        }

        private void DrawWeatherMenu(Rect topBarRect)
        {
            if (weatherSystem == null || panelStyle == null || weatherOptionStyle == null ||
                weatherOptionSelectedStyle == null || weatherOptionLabelStyle == null ||
                weatherOptionSelectedLabelStyle == null || weatherToggleOffTrackTexture == null ||
                weatherToggleOnTrackTexture == null || weatherToggleKnobTexture == null ||
                weatherMenuTitleStyle == null || weatherTimeValueStyle == null ||
                weatherTimeMarksStyle == null || weatherTimeSliderStyle == null ||
                weatherTimeSliderThumbStyle == null)
            {
                return;
            }

            Rect menuRect = GetWeatherMenuRect(topBarRect);
            GUI.Box(menuRect, GUIContent.none, panelStyle);
            float scale = menuRect.width / 198f;
            weatherMenuTitleStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(14f * scale), 10, 14);
            weatherOptionLabelStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 9, 12);
            weatherOptionSelectedLabelStyle.fontSize = weatherOptionLabelStyle.fontSize;
            weatherTimeValueStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(11f * scale), 8, 11);
            weatherTimeMarksStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(9f * scale), 7, 9);
            GUI.Label(new Rect(menuRect.x + 12f * scale, menuRect.y + 5f * scale,
                    menuRect.width - 24f * scale, 23f * scale),
                "天气模式", weatherMenuTitleStyle);

            string[] names = { "晴天", "阴天", "雨天", "大风", "雷雨" };
            IslandWeatherType[] types =
            {
                IslandWeatherType.Clear, IslandWeatherType.Overcast, IslandWeatherType.Rain,
                IslandWeatherType.Wind, IslandWeatherType.Thunderstorm
            };
            float optionWidth = menuRect.width - 20f * scale;
            float optionHeight = 28f * scale;
            float rowSpacing = 4f * scale;
            for (int i = 0; i < names.Length; i++)
            {
                Rect optionRect = new Rect(menuRect.x + 10f * scale,
                    menuRect.y + 33f * scale + i * (optionHeight + rowSpacing), optionWidth, optionHeight);
                bool selected = weatherSystem.CurrentWeather == types[i];
                GUIStyle style = selected ? weatherOptionSelectedStyle : weatherOptionStyle;
                if (GUI.Button(optionRect, GUIContent.none, style))
                {
                    weatherSystem.SetWeather(types[i]);
                    statusMessage = "天气切换为" + names[i] + "。";
                }

                float toggleWidth = 31f * scale;
                float toggleHeight = 15f * scale;
                Rect toggleRect = new Rect(optionRect.xMax - toggleWidth - 9f * scale,
                    optionRect.center.y - toggleHeight * 0.5f, toggleWidth, toggleHeight);
                GUI.DrawTexture(toggleRect,
                    selected ? weatherToggleOnTrackTexture : weatherToggleOffTrackTexture,
                    ScaleMode.StretchToFill, true);
                float knobSize = 11f * scale;
                float knobX = selected ? toggleRect.xMax - knobSize - 2f * scale : toggleRect.x + 2f * scale;
                Rect knobRect = new Rect(knobX, toggleRect.center.y - knobSize * 0.5f, knobSize, knobSize);
                GUI.DrawTexture(knobRect, weatherToggleKnobTexture, ScaleMode.StretchToFill, true);
                GUIStyle labelStyle = selected ? weatherOptionSelectedLabelStyle : weatherOptionLabelStyle;
                GUI.Label(new Rect(optionRect.x + 10f * scale, optionRect.y,
                    optionRect.width - toggleWidth - 25f * scale, optionRect.height), names[i], labelStyle);
            }

            float timeHeaderY = menuRect.y + 195f * scale;
            GUI.Label(new Rect(menuRect.x + 12f * scale, timeHeaderY,
                    menuRect.width - 90f * scale, 18f * scale),
                "昼夜时间轴", weatherMenuTitleStyle);
            float timeHours = weatherSystem.TimeOfDayHours;
            int totalMinutes = Mathf.RoundToInt(timeHours * 60f);
            string period = timeHours < 6f || timeHours >= 18f ? "夜间" : "白天";
            GUI.Label(new Rect(menuRect.xMax - 78f * scale, timeHeaderY,
                    66f * scale, 18f * scale),
                string.Format(CultureInfo.InvariantCulture, "{0:00}:{1:00} {2}",
                    totalMinutes / 60, totalMinutes % 60, period), weatherTimeValueStyle);

            Rect timeSliderRect = new Rect(menuRect.x + 16f * scale,
                menuRect.y + 214f * scale, menuRect.width - 32f * scale, 17f * scale);
            float selectedTime = GUI.HorizontalSlider(timeSliderRect, timeHours, 0f, 24f,
                weatherTimeSliderStyle, weatherTimeSliderThumbStyle);
            if (Mathf.Abs(selectedTime - timeHours) > 0.001f)
            {
                weatherSystem.SetTimeOfDay(selectedTime);
            }

            string[] timeMarks = { "0", "6", "12", "18", "24" };
            for (int i = 0; i < timeMarks.Length; i++)
            {
                float markerX = timeSliderRect.x + timeSliderRect.width * (i / 4f);
                Rect markerRect = new Rect(markerX - 10f * scale,
                    menuRect.y + 232f * scale, 20f * scale, 14f * scale);
                weatherTimeMarksStyle.alignment = i == 0 ? TextAnchor.MiddleLeft :
                    i == timeMarks.Length - 1 ? TextAnchor.MiddleRight : TextAnchor.MiddleCenter;
                GUI.Label(markerRect, timeMarks[i], weatherTimeMarksStyle);
            }
        }

        private void DrawHeaderButtons(Rect rect)
        {
            string[] tooltips = { "重置视角", "切换俯视", "显示或隐藏网格", "设置" };
            EnsureTopHudUtilityIcons();
            if (topHudUtilityIcons == null)
            {
                return;
            }

            float scale = GetHudScale();
            float buttonSize = 25f * scale;
            float buttonGap = 14f * scale;
            float hitSize = 38f * scale;
            float groupWidth = buttonSize * topHudUtilityIcons.Length + buttonGap * (topHudUtilityIcons.Length - 1);
            float startX = Screen.width - groupWidth - 20f * scale;
            float centerY = rect.center.y;
            Vector2 pointer = Event.current.mousePosition;
            int buttonCount = Mathf.Min(topHudUtilityIcons.Length,
                Mathf.Min(tooltips.Length, headerButtonFlashUntil.Length));
            for (int i = 0; i < buttonCount; i++)
            {
                float centerX = startX + i * (buttonSize + buttonGap) + buttonSize * 0.5f;
                Rect hitRect = new Rect(centerX - hitSize * 0.5f,
                    centerY - hitSize * 0.5f, hitSize, hitSize);
                bool clicked = GUI.Button(hitRect, new GUIContent(string.Empty, tooltips[i]), transparentButtonStyle);
                if (clicked)
                {
                    headerButtonFlashUntil[i] = Time.unscaledTime + 0.16f;
                    ActivateHeaderButton(i);
                }

                Texture2D buttonIcon = topHudUtilityIcons[i];
                if (buttonIcon == null)
                {
                    continue;
                }

                bool hovered = hitRect.Contains(pointer);
                bool pressed = (hovered && Input.GetMouseButton(0)) || Time.unscaledTime < headerButtonFlashUntil[i];
                Rect imageRect = new Rect(centerX - buttonSize * 0.5f,
                    centerY - buttonSize * 0.5f, buttonSize, buttonSize);
                Color previousColor = GUI.color;
                GUI.color = pressed || hovered || (i == 2 && !isBuildGridVisible)
                    ? new Color(1f, 0.84f, 0.53f, 1f)
                    : new Color(0.91f, 0.95f, 0.97f, 0.96f);
                GUI.DrawTexture(imageRect, buttonIcon, ScaleMode.ScaleToFit, true);
                GUI.color = previousColor;
            }
        }

        private void EnsureTopHudUtilityIcons()
        {
            if (topHudUtilityIcons != null && topHudUtilityIcons.Length == 4)
            {
                bool complete = true;
                for (int i = 0; i < topHudUtilityIcons.Length; i++)
                {
                    complete &= topHudUtilityIcons[i] != null;
                }

                if (complete)
                {
                    return;
                }
            }

            topHudUtilityIcons = new Texture2D[4];
            for (int i = 0; i < topHudUtilityIcons.Length; i++)
            {
                topHudUtilityIcons[i] = CreateTopHudUtilityIcon(i);
            }
        }

        private Texture2D CreateTopHudUtilityIcon(int index)
        {
            Texture2D texture = new Texture2D(64, 64, TextureFormat.RGBA32, false)
            {
                name = "Last Landfall HUD utility icon " + index,
                hideFlags = HideFlags.HideAndDontSave,
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Clamp
            };
            Color[] clearPixels = new Color[texture.width * texture.height];
            texture.SetPixels(clearPixels);
            Color line = new Color(0.92f, 0.96f, 0.98f, 1f);

            if (index == 0)
            {
                DrawIconCircle(texture, new Vector2(32f, 32f), 18f, 2.4f, line);
                DrawIconLine(texture, new Vector2(32f, 5f), new Vector2(32f, 15f), 2.4f, line);
                DrawIconLine(texture, new Vector2(32f, 49f), new Vector2(32f, 59f), 2.4f, line);
                DrawIconLine(texture, new Vector2(5f, 32f), new Vector2(15f, 32f), 2.4f, line);
                DrawIconLine(texture, new Vector2(49f, 32f), new Vector2(59f, 32f), 2.4f, line);
                DrawIconCircle(texture, new Vector2(32f, 32f), 3.2f, 2.2f, line);
            }
            else if (index == 1)
            {
                DrawIconLine(texture, new Vector2(8f, 44f), new Vector2(23f, 25f), 2.6f, line);
                DrawIconLine(texture, new Vector2(23f, 25f), new Vector2(33f, 37f), 2.6f, line);
                DrawIconLine(texture, new Vector2(33f, 37f), new Vector2(43f, 22f), 2.6f, line);
                DrawIconLine(texture, new Vector2(43f, 22f), new Vector2(57f, 44f), 2.6f, line);
                DrawIconLine(texture, new Vector2(8f, 49f), new Vector2(57f, 49f), 2f, line);
            }
            else if (index == 2)
            {
                DrawIconLine(texture, new Vector2(11f, 11f), new Vector2(53f, 11f), 2.2f, line);
                DrawIconLine(texture, new Vector2(53f, 11f), new Vector2(53f, 53f), 2.2f, line);
                DrawIconLine(texture, new Vector2(53f, 53f), new Vector2(11f, 53f), 2.2f, line);
                DrawIconLine(texture, new Vector2(11f, 53f), new Vector2(11f, 11f), 2.2f, line);
                DrawIconLine(texture, new Vector2(25f, 11f), new Vector2(25f, 53f), 1.8f, line);
                DrawIconLine(texture, new Vector2(39f, 11f), new Vector2(39f, 53f), 1.8f, line);
                DrawIconLine(texture, new Vector2(11f, 25f), new Vector2(53f, 25f), 1.8f, line);
                DrawIconLine(texture, new Vector2(11f, 39f), new Vector2(53f, 39f), 1.8f, line);
            }
            else
            {
                DrawIconCircle(texture, new Vector2(32f, 32f), 14f, 3f, line);
                DrawIconCircle(texture, new Vector2(32f, 32f), 5f, 2.6f, line);
                for (int tooth = 0; tooth < 8; tooth++)
                {
                    float angle = tooth * Mathf.PI / 4f;
                    Vector2 direction = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
                    DrawIconLine(texture, new Vector2(32f, 32f) + direction * 15f,
                        new Vector2(32f, 32f) + direction * 25f, 3f, line);
                }
            }

            texture.Apply(false, false);
            ownedUiTextures.Add(texture);
            return texture;
        }

        private void ActivateHeaderButton(int index)
        {
            switch (index)
            {
                case 0:
                    cameraOrthographicSize = DefaultCameraOrthographicSize;
                    isTopDownView = false;
                    PositionCamera();
                    statusMessage = "视角已重置。";
                    break;
                case 1:
                    if (isTopDownView)
                    {
                        cameraOrbitPitchDegrees = cameraPitchBeforeTopDown;
                        isTopDownView = false;
                    }
                    else
                    {
                        cameraPitchBeforeTopDown = cameraOrbitPitchDegrees;
                        cameraOrbitPitchDegrees = 78f;
                        isTopDownView = true;
                    }

                    ClampCameraView();
                    UpdateCameraPose();
                    statusMessage = isTopDownView ? "已切换为俯视岛屿。" : "已恢复斜视角度。";
                    break;
                case 2:
                    isBuildGridVisible = !isBuildGridVisible;
                    SetBuildGridVisibility(isBuildGridVisible && selectedBuildableIndex >= 0);
                    statusMessage = isBuildGridVisible ? "建造网格已显示。" : "建造网格已隐藏。";
                    break;
                case 3:
                {
                    MainMenuController menu = FindAnyObjectByType<MainMenuController>();
                    if (menu != null && menu.IsInitialized)
                    {
                        menu.OpenPauseMenu();
                    }
                    else
                    {
                        statusMessage = "设置界面暂不可用。";
                    }
                    break;
                }
            }
        }

        private void DrawSidebarCategories()
        {
            bool hasArtwork = SidebarCategoryArtwork.IsAvailable;
            if ((!hasArtwork && (sidebarCategoryIcons == null || sidebarCategoryIcons.Length != SidebarCategoryCount)) ||
                sidebarCategoryButtonStyle == null || sidebarCategorySelectedButtonStyle == null ||
                sidebarCategoryLabelStyle == null)
            {
                return;
            }

            const int buildingIndex = (int)SidebarCategory.Buildings;
            SidebarCategory category = SidebarCategory.Buildings;
            Rect rect = GetSidebarCategoryButtonRect(buildingIndex);
            if (hasArtwork)
            {
                SidebarCategoryArtwork.DrawRail(new Rect(rect.x - 4f, rect.y - 4f,
                    rect.width + 8f, rect.height + 8f));
            }

            bool selected = isBuildMenuOpen && activeSidebarCategory == category;
            bool hovered = rect.Contains(Event.current.mousePosition);
            GUIStyle buttonStyle = hasArtwork ? transparentButtonStyle
                : selected ? sidebarCategorySelectedButtonStyle : sidebarCategoryButtonStyle;
            if (GUI.Button(rect, GUIContent.none, buttonStyle))
            {
                SelectSidebarCategory(category);
            }

            selected = isBuildMenuOpen && activeSidebarCategory == category;
            if (hasArtwork && SidebarCategoryArtwork.TryDraw(rect, buildingIndex, selected, hovered,
                hovered && Input.GetMouseButton(0)))
            {
                return;
            }

            Texture2D icon = sidebarCategoryIcons[buildingIndex];
            if (icon != null)
            {
                Rect iconRect = new Rect(rect.x + 14f, rect.y + 5f, rect.width - 28f, 28f);
                GUI.DrawTexture(iconRect, icon, ScaleMode.ScaleToFit, true);
            }

            GUI.Label(new Rect(rect.x + 1f, rect.y + 33f, rect.width - 2f, 17f),
                SidebarCategoryNames[buildingIndex], sidebarCategoryLabelStyle);
        }

        private void SelectSidebarCategory(SidebarCategory category)
        {
            isWeatherMenuOpen = false;
            isResourceMenuOpen = false;
            activeSidebarCategory = category;
            isBuildMenuOpen = true;
            selectedBuildableIndex = -1;
            hasLastRoadCell = false;
            hoverMessage = string.Empty;
            SetBuildGridVisibility(false);
        }

        private void DrawBuildPanel(Rect panelRect)
        {
            GUI.Box(panelRect, GUIContent.none, panelStyle);
            string title = activeSidebarCategory == SidebarCategory.Technology
                ? "科技发展路线"
                : activeSidebarCategory == SidebarCategory.Culture
                    ? "文化发展路线"
                    : "海岛建设";
            GUI.Label(new Rect(panelRect.x + 18f, panelRect.y + 13f, panelRect.width - 68f, 27f), title, titleStyle);
            Rect closeRect = new Rect(panelRect.xMax - 38f, panelRect.y + 9f, 28f, 28f);
            if (GUI.Button(closeRect, "×", closeButtonStyle))
            {
                isBuildMenuOpen = false;
            }

            if (activeSidebarCategory == SidebarCategory.Technology)
            {
                DrawKnowledgeRoutePanel(panelRect, TechnologyRouteNames, TechnologyRouteDetails,
                    ref selectedTechnologyRouteIndex);
                return;
            }

            if (activeSidebarCategory == SidebarCategory.Culture)
            {
                DrawKnowledgeRoutePanel(panelRect, CultureRouteNames, CultureRouteDetails,
                    ref selectedCultureRouteIndex);
                return;
            }

            string selectedName = selectedBuildableIndex >= 0 ? Buildables[selectedBuildableIndex].Name + " · 橙色格线标示山地" : "选择设施后显示全岛网格";
            GUI.Label(new Rect(panelRect.x + 19f, panelRect.y + 43f, panelRect.width - 38f, 24f), selectedName, mutedLabelStyle);

            float footerHeight = 88f;
            Rect scrollRect = new Rect(panelRect.x + 12f, panelRect.y + 76f,
                panelRect.width - 24f, panelRect.height - 76f - footerHeight);
            float cardWidth = (scrollRect.width - 28f) * 0.5f;
            float cardHeight = 100f;
            float rowSpacing = 108f;
            float contentHeight = Mathf.Ceil(Buildables.Length / 2f) * rowSpacing;
            Rect viewRect = new Rect(0f, 0f, scrollRect.width - 16f, contentHeight);
            buildMenuScroll = GUI.BeginScrollView(scrollRect, buildMenuScroll, viewRect);

            for (int i = 0; i < Buildables.Length; i++)
            {
                int column = i % 2;
                int row = i / 2;
                Rect cardRect = new Rect(column * (cardWidth + 8f), row * rowSpacing, cardWidth, cardHeight);
                DrawBuildCard(i, cardRect);
            }

            GUI.EndScrollView();

            float footerY = panelRect.yMax - footerHeight + 2f;
            GUI.Label(new Rect(panelRect.x + 18f, footerY, panelRect.width - 36f, 30f), statusMessage, mutedLabelStyle);
            string defaultDetail = selectedBuildableIndex < 0
                ? "左键拖动平移 · 中键拖动转视角"
                : Buildables[selectedBuildableIndex].Kind == BuildableKind.Road
                    ? "按住左键连续铺路 · 中键拖转视角 · 右键取消"
                    : Buildables[selectedBuildableIndex].Kind == BuildableKind.Building
                        ? "左键放置 · Q / E 旋转建筑 · 中键拖转视角 · 右键取消"
                        : "左键放置 · 中键拖转视角 · 右键取消";
            string detail = !string.IsNullOrEmpty(hoverMessage) ? hoverMessage : defaultDetail;
            GUI.Label(new Rect(panelRect.x + 18f, footerY + 31f, panelRect.width - 36f, 43f), detail, mutedLabelStyle);
        }

        private void DrawKnowledgeRoutePanel(Rect panelRect, string[] nodeNames, string[] nodeDetails,
            ref int selectedNodeIndex)
        {
            GUI.Label(new Rect(panelRect.x + 19f, panelRect.y + 43f, panelRect.width - 38f, 22f),
                "路线预览 · 选择节点查看说明", mutedLabelStyle);

            float firstNodeY = panelRect.y + 76f;
            const float nodeSpacing = 69f;
            const float cardHeight = 58f;
            float markerCenterX = panelRect.x + 31f;
            Color previousColor = GUI.color;
            GUI.color = new Color(0.34f, 0.55f, 0.47f, 0.9f);
            for (int i = 0; i < nodeNames.Length - 1; i++)
            {
                float connectorY = firstNodeY + cardHeight * 0.5f + i * nodeSpacing;
                GUI.DrawTexture(new Rect(markerCenterX - 1f, connectorY, 2f, nodeSpacing), Texture2D.whiteTexture);
            }
            GUI.color = previousColor;

            for (int i = 0; i < nodeNames.Length; i++)
            {
                float y = firstNodeY + i * nodeSpacing;
                Rect cardRect = new Rect(panelRect.x + 56f, y, panelRect.width - 72f, cardHeight);
                bool selected = i == selectedNodeIndex;
                GUIStyle nodeCardStyle = selected ? selectedCardStyle : cardStyle;
                if (GUI.Button(cardRect, GUIContent.none, nodeCardStyle))
                {
                    selectedNodeIndex = i;
                }

                GUIStyle markerStyle = selected ? sidebarCategoryLabelStyle : mutedLabelStyle;
                GUI.Label(new Rect(markerCenterX - 11f, y + cardHeight * 0.5f - 12f, 22f, 24f),
                    "●", markerStyle);
                GUI.Label(new Rect(cardRect.x + 12f, cardRect.y + 7f, cardRect.width - 24f, 21f),
                    nodeNames[i], cardLabelStyle);
                GUI.Label(new Rect(cardRect.x + 12f, cardRect.y + 29f, cardRect.width - 24f, 22f),
                    nodeDetails[i], mutedLabelStyle);
            }
        }

        private void DrawBuildCard(int index, Rect cardRect)
        {
            BuildableDefinition definition = Buildables[index];
            GUIStyle style = index == selectedBuildableIndex ? selectedCardStyle : cardStyle;
            GUI.Box(cardRect, GUIContent.none, style);

            Texture2D icon = buildIcons != null && index < buildIcons.Length ? buildIcons[index] : null;
            float iconFrameSize = Mathf.Min(78f, cardRect.height - 14f);
            Rect iconFrameRect = new Rect(cardRect.x + 5f,
                cardRect.y + (cardRect.height - iconFrameSize) * 0.5f,
                iconFrameSize, iconFrameSize);
            DrawBuildIconFrame(iconFrameRect, index == selectedBuildableIndex);

            Rect iconRect = new Rect(iconFrameRect.x + 4f, iconFrameRect.y + 4f,
                iconFrameRect.width - 8f, iconFrameRect.height - 8f);
            if (icon != null)
            {
                if (definition.Kind == BuildableKind.Road)
                {
                    // Crop the straight-road sample out of the wide asset sheet so the icon fills its square frame.
                    GUI.DrawTextureWithTexCoords(iconRect, icon, new Rect(0.214f, 0.269f, 0.208f, 0.34f), true);
                }
                else
                {
                    GUI.DrawTexture(iconRect, icon, ScaleMode.ScaleToFit, true);
                }
            }

            string footprint = definition.Kind == BuildableKind.Dock
                ? "沿岸码头"
                : definition.Kind == BuildableKind.Road
                    ? "可拖动连续铺设"
                    : definition.Width + "×" + definition.Depth + " 格占地";
            GUI.Label(new Rect(cardRect.x + 88f, cardRect.y + 11f, cardRect.width - 96f, 38f), definition.Name, cardLabelStyle);
            GUI.Label(new Rect(cardRect.x + 88f, cardRect.y + 50f, cardRect.width - 96f, 38f),
                footprint + "\n木材 " + definition.WoodCost, mutedLabelStyle);

            if (GUI.Button(cardRect, GUIContent.none, transparentButtonStyle))
            {
                SelectBuildable(index);
            }
        }

        private static void DrawBuildIconFrame(Rect rect, bool selected)
        {
            Color previousColor = GUI.color;
            GUI.color = new Color(0.035f, 0.07f, 0.073f, 1f);
            GUI.DrawTexture(rect, Texture2D.whiteTexture);

            GUI.color = selected
                ? new Color(0.72f, 0.66f, 0.43f, 1f)
                : new Color(0.29f, 0.39f, 0.34f, 1f);
            const float border = 1.5f;
            GUI.DrawTexture(new Rect(rect.x, rect.y, rect.width, border), Texture2D.whiteTexture);
            GUI.DrawTexture(new Rect(rect.x, rect.yMax - border, rect.width, border), Texture2D.whiteTexture);
            GUI.DrawTexture(new Rect(rect.x, rect.y, border, rect.height), Texture2D.whiteTexture);
            GUI.DrawTexture(new Rect(rect.xMax - border, rect.y, border, rect.height), Texture2D.whiteTexture);
            GUI.color = previousColor;
        }

        private void LoadBuildIcons()
        {
            buildIcons = new Texture2D[Buildables.Length];
            for (int i = 0; i < Buildables.Length; i++)
            {
                BuildableDefinition definition = Buildables[i];
                buildIcons[i] = Resources.Load<Texture2D>("UI/BuildIcons/" + definition.IconName);
            }
        }

        private void ZoomCamera(float scroll)
        {
            float zoomMultiplier = Mathf.Pow(CameraZoomFactor, Mathf.Abs(scroll));
            cameraOrthographicSize = scroll > 0f
                ? Mathf.Max(MinimumCameraOrthographicSize, cameraOrthographicSize / zoomMultiplier)
                : cameraOrthographicSize * zoomMultiplier;
            ClampCameraView();
            UpdateCameraPose();
            statusMessage = "视野大小 " + cameraOrthographicSize.ToString("0.0") + "。";
        }

        private void UpdateWaterTransform()
        {
            if (waterTransform != null)
            {
                waterTransform.localRotation = Quaternion.identity;
                waterTransform.localScale = Vector3.one;
                waterTransform.localPosition = new Vector3(0f, WaterPlaneHeight, 0f);
            }

            if (waterMaterial != null && waterMaterial.HasProperty("_MapRotation"))
            {
                waterMaterial.SetFloat("_MapRotation", 0f);
                waterMaterial.SetFloat("_MapScale", 1f);
            }
        }

        private void CreateMaterials()
        {
            houseBodyMaterial = MakeMaterial(new Color(0.76f, 0.66f, 0.48f));
            houseRoofMaterial = MakeMaterial(new Color(0.43f, 0.27f, 0.19f));
            validPreviewMaterial = MakePreviewMaterial(new Color(0.25f, 0.9f, 0.55f, 0.68f));
            invalidPreviewMaterial = MakePreviewMaterial(new Color(0.95f, 0.24f, 0.2f, 0.68f));
        }

        private Material MakePreviewMaterial(Color color)
        {
            Material material = MakeMaterial(color);
            material.SetOverrideTag("RenderType", "Transparent");
            material.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha);
            material.SetInt("_DstBlend", (int)BlendMode.OneMinusSrcAlpha);
            material.SetInt("_ZWrite", 0);
            material.renderQueue = (int)RenderQueue.Transparent;

            if (material.HasProperty("_Surface"))
            {
                material.SetFloat("_Surface", 1f);
                material.SetFloat("_Blend", 0f);
                material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            }
            else if (material.HasProperty("_Mode"))
            {
                material.SetFloat("_Mode", 3f);
                material.EnableKeyword("_ALPHABLEND_ON");
            }

            return material;
        }

        private Material MakeMaterial(Color color)
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                shader = Shader.Find("Standard");
            }

            Material material = new Material(shader);
            material.color = color;
            ownedMaterials.Add(material);
            return material;
        }

        private void CreateLighting()
        {
            Light[] sceneLights = FindObjectsByType<Light>(FindObjectsInactive.Exclude);
            for (int i = 0; i < sceneLights.Length; i++)
            {
                if (sceneLights[i].type == LightType.Directional)
                {
                    prototypeSun = sceneLights[i];
                    break;
                }
            }

            if (prototypeSun == null)
            {
                GameObject lightObject = new GameObject("Prototype Sun");
                prototypeSun = lightObject.AddComponent<Light>();
                prototypeSun.type = LightType.Directional;
                lightObject.transform.rotation = Quaternion.Euler(45f, -35f, 0f);
            }
            prototypeSun.intensity = 0.9f;
            RenderSettings.ambientIntensity = 0.75f;
        }

        private void CreateWater()
        {
            GameObject water = new GameObject("Floodwater | animated teal shallows and foam");
            water.transform.SetParent(mapRoot, false);
            waterTransform = water.transform;
            UpdateWaterTransform();

            // The standard gameplay raycasts ignore layer 2, but the weather
            // particle collision module includes it to create sea splashes.
            water.layer = 2;
            BoxCollider waterWeatherCollider = water.AddComponent<BoxCollider>();
            waterWeatherCollider.center = new Vector3(0f, -0.03f, 0f);
            waterWeatherCollider.size = new Vector3(FloodwaterPlaneSize, 0.06f, FloodwaterPlaneSize);

            MeshFilter meshFilter = water.AddComponent<MeshFilter>();
            MeshRenderer meshRenderer = water.AddComponent<MeshRenderer>();
            meshFilter.sharedMesh = CreateWaterMesh(384, FloodwaterPlaneSize);

            Shader waterShader = Shader.Find("LastLandfall/Stylized Floodwater");
            if (waterShader == null)
            {
                waterShader = Shader.Find("Universal Render Pipeline/Lit");
            }

            waterMaterial = new Material(waterShader);
            waterMaterial.name = "Floodwater - Turquoise Shelf, Currents and Shore Foam";
            if (waterMaterial.HasProperty("_DeepColor"))
            {
                waterMaterial.SetColor("_DeepColor", new Color(0.018f, 0.085f, 0.23f));
                waterMaterial.SetColor("_MidColor", new Color(0.03f, 0.20f, 0.37f));
                waterMaterial.SetColor("_ShallowColor", new Color(0.10f, 0.43f, 0.42f));
                waterMaterial.SetColor("_FoamColor", new Color(0.92f, 0.97f, 0.94f));
                waterMaterial.SetFloat("_ShoreFoamWidth", 9.5f);
                waterMaterial.SetFloat("_ShoreFoamStrength", 1.0f);
                waterMaterial.SetFloat("_WaveSpeed", 0.9f);
                waterMaterial.SetFloat("_WaveHeight", 0.4f);
                waterMaterial.SetFloat("_MapRotation", 0f);
                waterMaterial.SetFloat("_MapScale", 1f);
            }
            else
            {
                waterMaterial.color = new Color(0.06f, 0.31f, 0.34f);
            }
            ownedMaterials.Add(waterMaterial);
            meshRenderer.sharedMaterial = waterMaterial;
            meshRenderer.shadowCastingMode = ShadowCastingMode.Off;
            meshRenderer.receiveShadows = false;
        }

        private void CreateIslandLandform()
        {
            // Scene-authored versions must not remain underneath or alongside the replacement.
            Transform[] sceneTransforms = FindObjectsByType<Transform>(FindObjectsInactive.Include);
            for (int i = 0; i < sceneTransforms.Length; i++)
            {
                string objectName = sceneTransforms[i].name;
                if (objectName == IslandRootName || objectName == LegacyIslandRootName ||
                    objectName == LegacyIslandModelName || objectName == IslandResourceName)
                {
                    sceneTransforms[i].gameObject.SetActive(false);
                }
            }

            GameObject islandPrefab = Resources.Load<GameObject>(GetModelResourcePath(IslandResourceName));
            if (islandPrefab == null)
            {
                Debug.LogError("缺少岛屿模型：Resources/Models/Environment/IslandReference_Gate25.fbx");
                return;
            }

            GameObject island = InstantiateIslandResource(islandPrefab, IslandRootName);
            islandRoot = island.transform;
            EnsureIslandMaterials(island);
            AddBasinTwinIslands();
            Collider[] importedColliders = island.GetComponentsInChildren<Collider>(true);
            for (int i = 0; i < importedColliders.Length; i++)
            {
                importedColliders[i].enabled = false;
            }

            MeshFilter[] importedMeshes = island.GetComponentsInChildren<MeshFilter>(true);
            List<MeshFilter> terrainMeshes = new List<MeshFilter>();
            for (int i = 0; i < importedMeshes.Length; i++)
            {
                MeshFilter filter = importedMeshes[i];
                if (filter.sharedMesh != null && IsIslandTerrainMesh(filter) &&
                    (satelliteIslandsRoot == null || !filter.transform.IsChildOf(satelliteIslandsRoot)))
                {
                    terrainMeshes.Add(filter);
                }
            }

            if (terrainMeshes.Count == 0)
            {
                Debug.LogError("Gate25 FBX 中没有找到地形网格（名称应包含 terrain source）。");
                return;
            }

            islandTerrainMeshes = terrainMeshes.ToArray();
            List<MeshCollider> surfaces = new List<MeshCollider>();
            Bounds localBounds = default;
            bool hasBounds = false;
            foreach (MeshFilter filter in islandTerrainMeshes)
            {
                Renderer terrainRenderer = filter.GetComponent<Renderer>();
                if (terrainRenderer != null)
                {
                    Bounds bounds = terrainRenderer.bounds;
                    if (bounds.max.y > WaterPlaneHeight)
                    {
                        Vector3 minimum = bounds.min;
                        minimum.y = Mathf.Max(minimum.y, WaterPlaneHeight);
                        bounds.SetMinMax(minimum, bounds.max);
                        if (!hasIslandVisibleBounds)
                        {
                            islandVisibleBounds = bounds;
                            hasIslandVisibleBounds = true;
                        }
                        else
                        {
                            islandVisibleBounds.Encapsulate(bounds);
                        }
                    }
                }

                MeshCollider collider = filter.GetComponent<MeshCollider>();
                if (collider == null) collider = filter.gameObject.AddComponent<MeshCollider>();
                collider.sharedMesh = filter.sharedMesh;
                collider.enabled = true;
                surfaces.Add(collider);

                Bounds meshBounds = filter.sharedMesh.bounds;
                for (int corner = 0; corner < 8; corner++)
                {
                    Vector3 point = meshBounds.center + Vector3.Scale(meshBounds.extents, new Vector3(
                        (corner & 1) == 0 ? -1f : 1f,
                        (corner & 2) == 0 ? -1f : 1f,
                        (corner & 4) == 0 ? -1f : 1f));
                    point = mapRoot.InverseTransformPoint(filter.transform.TransformPoint(point));
                    if (!hasBounds) { localBounds = new Bounds(point, Vector3.zero); hasBounds = true; }
                    else localBounds.Encapsulate(point);
                }
            }

            islandLandColliders = surfaces.ToArray();
            islandLocalBounds = localBounds;
            hasIslandLocalBounds = hasBounds;
            Physics.SyncTransforms();
            constructionGrid = new IslandConstructionGrid(mapRoot, islandLandColliders, localBounds, WaterPlaneHeight);
        }

        private void AddBasinTwinIslands()
        {
            GameObject satellitePrefab = Resources.Load<GameObject>(GetModelResourcePath(SatelliteIslandResourceName));
            if (satellitePrefab == null)
            {
                Debug.LogWarning("缺少 Gate26 盆地对岸双岛模型；主岛将继续正常载入。");
                return;
            }

            GameObject satellites = Instantiate(satellitePrefab, islandRoot, false);
            satellites.name = "Basin Twin Islands - Gate26";
            satelliteIslandsRoot = satellites.transform;
            EnsureIslandMaterials(satellites);

            MeshFilter[] meshes = satellites.GetComponentsInChildren<MeshFilter>(true);
            int islandCount = 0;
            for (int i = 0; i < meshes.Length; i++)
            {
                MeshFilter filter = meshes[i];
                if (filter.sharedMesh == null || !IsIslandTerrainMesh(filter))
                {
                    continue;
                }

                Renderer terrainRenderer = filter.GetComponent<Renderer>();
                if (terrainRenderer == null || terrainRenderer.bounds.max.y <= WaterPlaneHeight)
                {
                    continue;
                }

                Bounds bounds = terrainRenderer.bounds;
                Vector3 minimum = bounds.min;
                minimum.y = Mathf.Max(minimum.y, WaterPlaneHeight);
                bounds.SetMinMax(minimum, bounds.max);
                if (!hasIslandVisibleBounds)
                {
                    islandVisibleBounds = bounds;
                    hasIslandVisibleBounds = true;
                }
                else
                {
                    islandVisibleBounds.Encapsulate(bounds);
                }

                islandCount++;
            }

            Debug.Log($"Gate26 basin twin islands loaded ({islandCount} terrain meshes); they remain scenery outside the build grid.");
        }

        private void CreateCoastDistanceField()
        {
            if (waterMaterial == null || !hasIslandLocalBounds || islandLandColliders == null || islandLandColliders.Length == 0)
            {
                return;
            }

            const int resolution = 1024;
            const float margin = 34f;
            const float distanceRange = 40f;
            float minX = islandLocalBounds.min.x - margin;
            float maxX = islandLocalBounds.max.x + margin;
            float minZ = islandLocalBounds.min.z - margin;
            float maxZ = islandLocalBounds.max.z + margin;
            float worldWidth = Mathf.Max(1f, maxX - minX);
            float worldDepth = Mathf.Max(1f, maxZ - minZ);
            float stepX = worldWidth / (resolution - 1);
            float stepZ = worldDepth / (resolution - 1);
            float diagonal = Mathf.Sqrt(stepX * stepX + stepZ * stepZ);
            bool[] land = new bool[resolution * resolution];
            float[] distance = new float[land.Length];
            float rayHeight = islandLocalBounds.max.y + 8f;
            float rayLength = islandLocalBounds.size.y + 24f;
            Vector3 rayDirection = -mapRoot.up;
            int landSampleCount = 0;

            for (int z = 0; z < resolution; z++)
            {
                float localZ = minZ + stepZ * z;
                for (int x = 0; x < resolution; x++)
                {
                    Vector3 localOrigin = new Vector3(minX + stepX * x, rayHeight, localZ);
                    Ray ray = new Ray(mapRoot.TransformPoint(localOrigin), rayDirection);
                    float highestLand = float.NegativeInfinity;
                    for (int colliderIndex = 0; colliderIndex < islandLandColliders.Length; colliderIndex++)
                    {
                        MeshCollider terrain = islandLandColliders[colliderIndex];
                        if (terrain != null && terrain.enabled && terrain.Raycast(ray, out RaycastHit hit, rayLength))
                        {
                            float hitHeight = mapRoot.InverseTransformPoint(hit.point).y;
                            if (hitHeight > highestLand) highestLand = hitHeight;
                        }
                    }

                    bool isLand = highestLand > WaterPlaneHeight + 0.02f;
                    land[z * resolution + x] = isLand;
                    if (isLand) landSampleCount++;
                }
            }

            const float far = 1000000f;
            for (int z = 0; z < resolution; z++)
            {
                for (int x = 0; x < resolution; x++)
                {
                    int index = z * resolution + x;
                    float boundaryDistance = far;
                    for (int dz = -1; dz <= 1; dz++)
                    {
                        for (int dx = -1; dx <= 1; dx++)
                        {
                            if (dx == 0 && dz == 0) continue;
                            int nx = x + dx;
                            int nz = z + dz;
                            if (nx < 0 || nx >= resolution || nz < 0 || nz >= resolution)
                            {
                                continue;
                            }
                            if (land[nz * resolution + nx] != land[index])
                            {
                                float halfStep = 0.5f * Mathf.Sqrt(
                                    dx * dx * stepX * stepX + dz * dz * stepZ * stepZ);
                                boundaryDistance = Mathf.Min(boundaryDistance, halfStep);
                            }
                        }
                    }
                    distance[index] = boundaryDistance;
                }
            }

            for (int z = 0; z < resolution; z++)
            {
                for (int x = 0; x < resolution; x++)
                {
                    int index = z * resolution + x;
                    float value = distance[index];
                    if (x > 0) value = Mathf.Min(value, distance[index - 1] + stepX);
                    if (z > 0) value = Mathf.Min(value, distance[index - resolution] + stepZ);
                    if (x > 0 && z > 0) value = Mathf.Min(value, distance[index - resolution - 1] + diagonal);
                    if (x < resolution - 1 && z > 0) value = Mathf.Min(value, distance[index - resolution + 1] + diagonal);
                    distance[index] = value;
                }
            }

            for (int z = resolution - 1; z >= 0; z--)
            {
                for (int x = resolution - 1; x >= 0; x--)
                {
                    int index = z * resolution + x;
                    float value = distance[index];
                    if (x < resolution - 1) value = Mathf.Min(value, distance[index + 1] + stepX);
                    if (z < resolution - 1) value = Mathf.Min(value, distance[index + resolution] + stepZ);
                    if (x < resolution - 1 && z < resolution - 1) value = Mathf.Min(value, distance[index + resolution + 1] + diagonal);
                    if (x > 0 && z < resolution - 1) value = Mathf.Min(value, distance[index + resolution - 1] + diagonal);
                    distance[index] = value;
                }
            }

            float[] encodedDistance = new float[distance.Length];
            for (int i = 0; i < encodedDistance.Length; i++)
            {
                float signedDistance = land[i] ? -distance[i] : distance[i];
                encodedDistance[i] = 0.5f + Mathf.Clamp(signedDistance, -distanceRange, distanceRange) / (distanceRange * 2f);
            }

            coastDistanceTexture = new Texture2D(resolution, resolution, TextureFormat.RFloat, true, true)
            {
                name = "Gate25 Coast Distance Field",
                filterMode = FilterMode.Trilinear,
                wrapMode = TextureWrapMode.Clamp,
                hideFlags = HideFlags.HideAndDontSave
            };
            coastDistanceTexture.SetPixelData(encodedDistance, 0);
            coastDistanceTexture.Apply(true, true);
            ownedUiTextures.Add(coastDistanceTexture);
            waterMaterial.SetTexture("_CoastDistanceTex", coastDistanceTexture);
            waterMaterial.SetVector("_CoastWorldMin", new Vector4(minX, minZ, 0f, 0f));
            waterMaterial.SetVector("_CoastWorldSize", new Vector4(worldWidth, worldDepth, 0f, 0f));
            waterMaterial.SetFloat("_CoastDistanceRange", distanceRange);
            Debug.Log($"Gate25 coastline field generated ({resolution}x{resolution}, {landSampleCount} land samples, {islandLandColliders.Length} terrain meshes).");
        }

        private static bool IsIslandTerrainMesh(MeshFilter filter)
        {
            return filter != null && filter.name.IndexOf(TerrainSourceName,
                System.StringComparison.OrdinalIgnoreCase) >= 0;
        }

        private GameObject InstantiateIslandResource(GameObject prefab, string objectName)
        {
            // Gate25 already exports metre-scaled mesh transforms and its -0.92 m
            // waterline offset. Keep the wrapper at unit scale so those transforms survive.
            GameObject root = new GameObject(objectName);
            root.transform.SetParent(mapRoot, false);
            root.transform.localPosition = Vector3.zero;
            root.transform.rotation = Quaternion.AngleAxis(180f, Vector3.up) * mapRoot.rotation;
            root.transform.localScale = Vector3.one;
            GameObject imported = Instantiate(prefab, root.transform, false);
            imported.transform.localPosition = prefab.transform.localPosition;
            imported.transform.localRotation = prefab.transform.localRotation;
            imported.transform.localScale = prefab.transform.localScale;
            return root;
        }

        private void EnsureIslandMaterials(GameObject island)
        {
            Material terrainPaint = LoadIslandMaterial("Materials/Gate25Terrain") ??
                MakeTerrainMaterial("Gate25 | Vertex Painted Terrain",
                Color.white, Color.white, Color.white, 0.0f, 0.02f, 0.0f, 0.08f, 1.0f);
            Material wetRock = LoadIslandMaterial("Materials/Gate25WetRock") ??
                MakeTerrainMaterial("Gate25 | Wet Rock",
                new Color(0.12f, 0.17f, 0.18f), new Color(0.23f, 0.27f, 0.28f),
                new Color(0.34f, 0.38f, 0.37f), 0.62f, 0.08f, 0.25f, 0.32f, 0.0f);
            Texture2D grassAlbedo = Resources.Load<Texture2D>(
                "Textures/Environment/Grass_Surface_Albedo_Concept");
            if (grassAlbedo != null && terrainPaint.HasProperty("_BaseMap"))
                terrainPaint.SetTexture("_BaseMap", grassAlbedo);
            if (terrainPaint.HasProperty("_TextureWeight"))
                terrainPaint.SetFloat("_TextureWeight", grassAlbedo != null ? 0.10f : 0.0f);

            Material basinWater = null;
            Dictionary<Material, Material> convertedMaterials = new Dictionary<Material, Material>();
            Material earthFallback = null;
            Material rockFallback = null;
            Renderer[] renderers = island.GetComponentsInChildren<Renderer>(true);
            for (int rendererIndex = 0; rendererIndex < renderers.Length; rendererIndex++)
            {
                Renderer renderer = renderers[rendererIndex];
                if (IsIslandTerrainRenderer(renderer))
                {
                    MeshFilter filter = renderer.GetComponent<MeshFilter>();
                    int materialCount = filter != null && filter.sharedMesh != null
                        ? Mathf.Max(1, filter.sharedMesh.subMeshCount)
                        : Mathf.Max(1, renderer.sharedMaterials.Length);
                    Material[] terrainMaterials = new Material[materialCount];
                    for (int materialIndex = 0; materialIndex < terrainMaterials.Length; materialIndex++)
                    {
                        terrainMaterials[materialIndex] = materialIndex == 1 ? wetRock : terrainPaint;
                    }
                    renderer.sharedMaterials = terrainMaterials;
                    islandBareEarthMaterial = terrainPaint;
                    continue;
                }

                if (IsBasinWaterRenderer(renderer))
                {
                    if (basinWater == null)
                    {
                        basinWater = LoadIslandMaterial("Materials/Gate25BasinWater");
                        if (basinWater == null)
                        {
                            Shader shader = Shader.Find("LastLandfall/Basin Water");
                            if (shader == null) shader = Shader.Find("Universal Render Pipeline/Lit");
                            basinWater = new Material(shader);
                            basinWater.name = "Gate25 | Basin Water";
                            if (basinWater.HasProperty("_Tint")) basinWater.SetColor("_Tint", Color.white);
                            if (basinWater.HasProperty("_FlowSpeed")) basinWater.SetFloat("_FlowSpeed", 0.12f);
                            if (basinWater.HasProperty("_RippleStrength")) basinWater.SetFloat("_RippleStrength", 0.025f);
                            if (basinWater.HasProperty("_Smoothness")) basinWater.SetFloat("_Smoothness", 0.72f);
                            ownedMaterials.Add(basinWater);
                        }
                    }
                    Material[] waterMaterials = renderer.sharedMaterials;
                    if (waterMaterials.Length == 0) waterMaterials = new Material[1];
                    for (int materialIndex = 0; materialIndex < waterMaterials.Length; materialIndex++)
                    {
                        waterMaterials[materialIndex] = basinWater;
                    }
                    renderer.sharedMaterials = waterMaterials;
                    continue;
                }

                Material[] materials = renderer.sharedMaterials;
                bool changed = false;
                for (int materialIndex = 0; materialIndex < materials.Length; materialIndex++)
                {
                    Material material = materials[materialIndex];
                    bool invalid = material == null || material.shader == null || !material.shader.isSupported;
                    if (!invalid)
                    {
                        string shaderName = material.shader.name;
                        invalid = shaderName == "Hidden/InternalErrorShader" ||
                            material.name == "Default-Material" || material.name == "Default Material" ||
                            (GraphicsSettings.currentRenderPipeline != null &&
                             (shaderName == "Standard" || shaderName.StartsWith("Legacy Shaders/")));
                    }
                    if (!invalid)
                    {
                        continue;
                    }
                    if (material != null)
                    {
                        if (!convertedMaterials.TryGetValue(material, out Material compatible))
                        {
                            compatible = MakeUrpCompatibleMaterial(material);
                            convertedMaterials.Add(material, compatible);
                        }
                        materials[materialIndex] = compatible;
                    }
                    else if (materialIndex == 0)
                    {
                        if (earthFallback == null)
                        {
                            earthFallback = MakeMaterial(new Color(0.36f, 0.32f, 0.27f));
                            earthFallback.name = "Island V2 | Bare Earth Fallback";
                            if (earthFallback.HasProperty("_Smoothness"))
                            {
                                earthFallback.SetFloat("_Smoothness", 0.08f);
                            }
                        }
                        materials[materialIndex] = earthFallback;
                    }
                    else
                    {
                        if (rockFallback == null)
                        {
                            rockFallback = MakeMaterial(new Color(0.26f, 0.28f, 0.29f));
                            rockFallback.name = "Island V2 | Rock Fallback";
                            if (rockFallback.HasProperty("_Smoothness"))
                            {
                                rockFallback.SetFloat("_Smoothness", 0.14f);
                            }
                        }
                        materials[materialIndex] = rockFallback;
                    }
                    changed = true;
                }
                if (changed)
                {
                    renderers[rendererIndex].sharedMaterials = materials;
                }
            }
        }

        private static bool IsIslandTerrainRenderer(Renderer renderer)
        {
            return renderer != null && renderer.name.IndexOf(TerrainSourceName,
                System.StringComparison.OrdinalIgnoreCase) >= 0;
        }

        private static bool IsBasinWaterRenderer(Renderer renderer)
        {
            return renderer != null && renderer.name.IndexOf("Basin_", System.StringComparison.OrdinalIgnoreCase) >= 0 &&
                renderer.name.IndexOf("Water", System.StringComparison.OrdinalIgnoreCase) >= 0;
        }

        private Material MakeTerrainMaterial(string materialName, Color baseColor, Color accentColor,
            Color mineralColor, float colorVariation, float strataStrength, float normalStrength,
            float smoothness, float vertexColorWeight)
        {
            Shader shader = Shader.Find("LastLandfall/Reference Island Terrain");
            if (shader == null)
            {
                Material fallback = MakeMaterial(baseColor);
                fallback.name = materialName + " | Fallback";
                return fallback;
            }

            Material material = new Material(shader);
            material.name = materialName;
            material.SetColor("_BaseColor", baseColor);
            material.SetColor("_AccentColor", accentColor);
            material.SetColor("_MineralColor", mineralColor);
            material.SetFloat("_MacroScale", 0.55f);
            material.SetFloat("_DetailScale", 4.6f);
            material.SetFloat("_MicroScale", 32f);
            material.SetFloat("_LayerScale", 2.2f);
            material.SetFloat("_ColorVariation", colorVariation);
            material.SetFloat("_StrataStrength", strataStrength);
            material.SetFloat("_NormalStrength", normalStrength);
            material.SetFloat("_Smoothness", smoothness);
            material.SetFloat("_VertexColorWeight", vertexColorWeight);
            if (material.HasProperty("_TextureWeight")) material.SetFloat("_TextureWeight", 0.0f);
            ownedMaterials.Add(material);
            return material;
        }

        private Material LoadIslandMaterial(string resourcePath)
        {
            Material source = Resources.Load<Material>(resourcePath);
            if (source == null) return null;
            Material material = new Material(source);
            ownedMaterials.Add(material);
            return material;
        }

        private Material MakeUrpCompatibleMaterial(Material source)
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) shader = Shader.Find("Standard");
            Material material = new Material(shader);
            material.name = source.name + " | URP";

            Color baseColor = source.HasProperty("_BaseColor")
                ? source.GetColor("_BaseColor")
                : source.HasProperty("_Color") ? source.GetColor("_Color") : Color.white;
            if (material.HasProperty("_BaseColor")) material.SetColor("_BaseColor", baseColor);
            else if (material.HasProperty("_Color")) material.SetColor("_Color", baseColor);

            Texture baseMap = source.HasProperty("_BaseMap") ? source.GetTexture("_BaseMap") : null;
            if (baseMap == null && source.HasProperty("_MainTex")) baseMap = source.GetTexture("_MainTex");
            if (baseMap != null)
            {
                string property = material.HasProperty("_BaseMap") ? "_BaseMap" : "_MainTex";
                material.SetTexture(property, baseMap);
            }

            if (source.HasProperty("_Metallic") && material.HasProperty("_Metallic"))
                material.SetFloat("_Metallic", source.GetFloat("_Metallic"));
            float smoothness = source.HasProperty("_Glossiness") ? source.GetFloat("_Glossiness")
                : source.HasProperty("_Smoothness") ? source.GetFloat("_Smoothness") : 0.18f;
            if (material.HasProperty("_Smoothness")) material.SetFloat("_Smoothness", smoothness);
            ownedMaterials.Add(material);
            return material;
        }

        private void CreateGridOverlay()
        {
            Shader shader = Shader.Find("LastLandfall/Island Construction Grid");
            if (shader == null || constructionGrid == null)
            {
                Debug.LogError("全岛建造网格缺少地形或网格着色器。");
                return;
            }
            Material material = new Material(shader);
            ownedMaterials.Add(material);
            material.SetMatrix("_WorldToGrid", mapRoot.worldToLocalMatrix);
            material.SetFloat("_SeaLevel", WaterPlaneHeight);
            material.SetFloat("_BuildingElevation", IslandConstructionGrid.BuildingElevationLimit);
            material.SetFloat("_BuildingSlopeCos", Mathf.Cos(IslandConstructionGrid.BuildingSlopeLimit * Mathf.Deg2Rad));
            List<Renderer> overlays = new List<Renderer>();
            foreach (MeshFilter source in islandTerrainMeshes)
            {
                if (source.sharedMesh == null) continue;
                GameObject overlay = new GameObject("Construction Grid | " + source.name);
                overlay.transform.SetParent(source.transform, false);
                overlay.AddComponent<MeshFilter>().sharedMesh = source.sharedMesh;
                MeshRenderer renderer = overlay.AddComponent<MeshRenderer>();
                // One overlay submesh for each source submesh, all sharing the
                // same shader. No terrain triangle is omitted by a slope mask.
                Material[] materials = new Material[source.sharedMesh.subMeshCount];
                for (int i = 0; i < materials.Length; i++) materials[i] = material;
                renderer.sharedMaterials = materials;
                renderer.shadowCastingMode = ShadowCastingMode.Off;
                renderer.receiveShadows = false;
                renderer.enabled = false;
                overlays.Add(renderer);
            }
            gridOverlayRenderers = overlays.ToArray();
        }

        private void SetBuildGridVisibility(bool visible)
        {
            if (gridOverlayRenderers == null) return;
            foreach (Renderer renderer in gridOverlayRenderers)
                if (renderer != null) renderer.enabled = visible;
        }

        public void SetBuildGridPreference(bool visible)
        {
            isBuildGridVisible = visible;
            SetBuildGridVisibility(isBuildGridVisible && selectedBuildableIndex >= 0);
        }

        private static Mesh CreateWaterMesh(int divisions, float size)
        {
            int side = divisions + 1;
            var vertices = new Vector3[side * side];
            var triangles = new int[divisions * divisions * 6];
            float half = size * 0.5f;
            for (int z = 0; z <= divisions; z++)
            {
                for (int x = 0; x <= divisions; x++)
                {
                    float px = Mathf.Lerp(-half, half, x / (float)divisions);
                    float pz = Mathf.Lerp(-half, half, z / (float)divisions);
                    vertices[z * side + x] = new Vector3(px, 0f, pz);
                }
            }

            int index = 0;
            for (int z = 0; z < divisions; z++)
            {
                for (int x = 0; x < divisions; x++)
                {
                    int a = z * side + x;
                    int b = a + 1;
                    int c = a + side + 1;
                    int d = a + side;
                    triangles[index++] = a;
                    triangles[index++] = c;
                    triangles[index++] = b;
                    triangles[index++] = a;
                    triangles[index++] = d;
                    triangles[index++] = c;
                }
            }

            Mesh mesh = new Mesh { name = "Subdivided floodwater surface" };
            mesh.indexFormat = IndexFormat.UInt32;
            mesh.vertices = vertices;
            mesh.triangles = triangles;
            mesh.RecalculateNormals();
            return mesh;
        }

        private void SelectBuildable(int index)
        {
            selectedBuildableIndex = index;
            rotationDegrees = 0;
            hasLastRoadCell = false;
            BuildableDefinition definition = Buildables[index];
            statusMessage = definition.Name + "已选中。";
            hoverMessage = string.Empty;
        }

        private void RotateSelectedBuilding(int direction)
        {
            if (selectedBuildableIndex < 0 ||
                Buildables[selectedBuildableIndex].Kind != BuildableKind.Building)
            {
                return;
            }

            rotationDegrees = (rotationDegrees + direction + 360) % 360;
            statusMessage = "建筑方向已旋转 " + rotationDegrees + "°。";
        }

        private GameObject CreatePlaceableObject(string assetName, string objectName)
        {
            GameObject root = new GameObject(objectName);
            GameObject prefab = Resources.Load<GameObject>(GetModelResourcePath(assetName));
            if (prefab != null)
            {
                GameObject model = Instantiate(prefab, root.transform, false);
                model.name = assetName + " Model";
                if (assetName.StartsWith("Road"))
                {
                    model.transform.localRotation = Quaternion.Euler(0f, RoadModelImportYawCorrectionDegrees, 0f) * model.transform.localRotation;
                }
                return root;
            }

            if (assetName.StartsWith("Road"))
            {
                GameObject road = GameObject.CreatePrimitive(PrimitiveType.Cube);
                road.name = "Road Fallback";
                road.transform.SetParent(root.transform, false);
                road.transform.localPosition = new Vector3(0f, 0.055f, 0f);
                road.transform.localScale = new Vector3(0.5f, 0.11f, 1f);
                road.GetComponent<Renderer>().sharedMaterial = houseRoofMaterial;
                return root;
            }

            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Cube);
            body.name = "Building Body Fallback";
            body.transform.SetParent(root.transform, false);
            body.transform.localPosition = new Vector3(0f, 0.39f, 0f);
            body.transform.localScale = new Vector3(0.68f, 0.68f, 0.68f);
            body.GetComponent<Renderer>().sharedMaterial = houseBodyMaterial;

            GameObject roof = GameObject.CreatePrimitive(PrimitiveType.Cube);
            roof.name = "Building Roof Fallback";
            roof.transform.SetParent(root.transform, false);
            roof.transform.localPosition = new Vector3(0f, 0.79f, 0f);
            roof.transform.localScale = new Vector3(0.82f, 0.18f, 0.82f);
            roof.GetComponent<Renderer>().sharedMaterial = houseRoofMaterial;

            return root;
        }

        private static string GetModelResourcePath(string assetName)
        {
            string category = assetName == "IslandReference_V2" || assetName == "IslandReference_Gate25" ||
                assetName == SatelliteIslandResourceName
                ? "Environment"
                : assetName == "RescueDock" || assetName.StartsWith("Road")
                    ? "Infrastructure"
                    : "Buildings";
            return "Models/" + category + "/" + assetName;
        }

        private void EnsurePreviewObject(string assetName)
        {
            if (previewObject != null && previewAssetName == assetName)
            {
                return;
            }

            if (previewObject != null)
            {
                Destroy(previewObject);
            }

            previewAssetName = assetName;
            previewObject = CreatePlaceableObject(assetName, "Building Preview");
            previewObject.transform.SetParent(mapRoot, false);
            previewRenderers = previewObject.GetComponentsInChildren<Renderer>();
            previewObject.SetActive(false);
        }

        private void UpdateHoveredCell(Vector2 guiPosition)
        {
            hasHoveredCell = false;
            if (gameCamera == null)
            {
                return;
            }

            Vector3 screenPosition = new Vector3(guiPosition.x, Screen.height - guiPosition.y, 0f);
            Ray ray = gameCamera.ScreenPointToRay(screenPosition);
            if (constructionGrid == null) return;
            Vector3 point;
            if (constructionGrid.TryRaycast(ray, out RaycastHit hit))
            {
                point = mapRoot.InverseTransformPoint(hit.point);
            }
            else
            {
                Plane seaPlane = new Plane(mapRoot.up, mapRoot.TransformPoint(new Vector3(0f, WaterPlaneHeight, 0f)));
                if (!seaPlane.Raycast(ray, out float distance)) return;
                point = mapRoot.InverseTransformPoint(ray.GetPoint(distance));
            }
            hoveredCell = constructionGrid.PointToCell(point);
            hasHoveredCell = constructionGrid.Contains(hoveredCell);
        }

        private void UpdatePreview()
        {
            if (selectedBuildableIndex < 0 || !hasHoveredCell)
            {
                SetBuildGridVisibility(isBuildGridVisible && selectedBuildableIndex >= 0);
                if (previewObject != null)
                {
                    previewObject.SetActive(false);
                }

                hoverMessage = string.Empty;
                return;
            }

            BuildableDefinition selected = Buildables[selectedBuildableIndex];
            string assetName = selected.AssetName;
            int previewRotation = rotationDegrees;
            string reason;
            bool canPlace;

            if (selected.Kind == BuildableKind.Road)
            {
                RoadShape shape = GetRoadShape(hoveredCell);
                assetName = shape.AssetName;
                previewRotation = shape.RotationDegrees;
                canPlace = CanPlaceRoad(hoveredCell, selected, out reason);
            }
            else if (selected.Kind == BuildableKind.Dock)
            {
                canPlace = CanPlaceDock(hoveredCell, out Vector2Int shoreDirection, out reason);
                if (canPlace)
                {
                    previewRotation = GetRotationAligning(South, shoreDirection);
                }
            }
            else
            {
                canPlace = CanPlaceBuilding(hoveredCell, selected, out reason);
            }

            EnsurePreviewObject(assetName);
            previewObject.transform.SetLocalPositionAndRotation(
                GetObjectCenter(hoveredCell, selected),
                Quaternion.Euler(0f, previewRotation, 0f));
            previewObject.SetActive(true);
            SetPreviewMaterial(canPlace ? validPreviewMaterial : invalidPreviewMaterial);
            SetBuildGridVisibility(isBuildGridVisible);

            hoverMessage = canPlace ? "地格：" + hoveredCell.x + ", " + hoveredCell.y : reason;
        }

        private void SetPreviewMaterial(Material material)
        {
            if (previewRenderers == null)
            {
                return;
            }

            for (int i = 0; i < previewRenderers.Length; i++)
            {
                Material[] previewMaterials = previewRenderers[i].sharedMaterials;
                for (int materialIndex = 0; materialIndex < previewMaterials.Length; materialIndex++)
                {
                    previewMaterials[materialIndex] = material;
                }

                previewRenderers[i].sharedMaterials = previewMaterials;
            }
        }

        private bool CanPlaceBuilding(Vector2Int anchor, BuildableDefinition definition, out string reason)
        {
            for (int x = 0; x < definition.Width; x++)
            {
                for (int z = 0; z < definition.Depth; z++)
                {
                    Vector2Int cell = anchor + new Vector2Int(x, z);
                    if (!IsBuildingTerrainCell(cell))
                    {
                        reason = "此处是山地、陡坡或岸边，普通建筑需要较平整的完整陆地。";
                        return false;
                    }

                    if (occupiedCells.Contains(cell) || roadCells.Contains(cell))
                    {
                        reason = "占地范围内已有建筑或道路。";
                        return false;
                    }
                }
            }

            if (!constructionGrid.TryBuildingFootprint(anchor, definition.Width, definition.Depth, out _, out _))
            {
                reason = "建筑占地内的高差过大，请选择较平整的陆地。";
                return false;
            }

            if (wood < definition.WoodCost)
            {
                reason = "木材不足，需要 " + definition.WoodCost + "。";
                return false;
            }

            reason = string.Empty;
            return true;
        }

        private bool CanPlaceRoad(Vector2Int cell, BuildableDefinition definition, out string reason)
        {
            if (constructionGrid == null || !constructionGrid.GetTerrain(cell).AllowsRoad)
            {
                reason = "道路需要连续陆地，且坡度不能过陡。";
                return false;
            }

            if (occupiedCells.Contains(cell))
            {
                reason = "建筑占用了这块地。";
                return false;
            }

            if (roadCells.Contains(cell))
            {
                reason = "这里已经有道路。";
                return false;
            }

            if (wood < definition.WoodCost)
            {
                reason = "木材不足，需要 " + definition.WoodCost + "。";
                return false;
            }

            reason = string.Empty;
            return true;
        }

        private bool CanPlaceDock(Vector2Int anchor, out Vector2Int direction, out string reason)
        {
            direction = Vector2Int.zero;
            if (!IsLandCell(anchor))
            {
                reason = "码头的陆侧基座必须放在岛岸上。";
                return false;
            }

            if (occupiedCells.Contains(anchor) || roadCells.Contains(anchor))
            {
                reason = "码头基座位置已被占用。";
                return false;
            }

            if (!TryFindDockDirection(anchor, out direction))
            {
                reason = "这里没有连续水面，或码头两侧没有足够空地。";
                return false;
            }

            if (wood < Buildables[selectedBuildableIndex].WoodCost)
            {
                reason = "木材不足，需要 " + Buildables[selectedBuildableIndex].WoodCost + "。";
                return false;
            }

            reason = string.Empty;
            return true;
        }

        private bool TryFindDockDirection(Vector2Int anchor, out Vector2Int direction)
        {
            for (int i = 0; i < CardinalDirections.Length; i++)
            {
                Vector2Int candidate = CardinalDirections[i];
                Vector2Int firstWaterCell = anchor + candidate;
                Vector2Int secondWaterCell = anchor + candidate * 2;
                if (IsLandCell(firstWaterCell) || IsLandCell(secondWaterCell))
                {
                    continue;
                }

                Vector2Int sideDirection = candidate.x == 0 ? East : North;
                bool sideIsClear = true;
                for (int side = -1; side <= 1; side++)
                {
                    Vector2Int reservedCell = anchor + sideDirection * side;
                    if (IsInsideBoard(reservedCell) &&
                        (occupiedCells.Contains(reservedCell) || roadCells.Contains(reservedCell)))
                    {
                        sideIsClear = false;
                        break;
                    }
                }

                if (sideIsClear)
                {
                    direction = candidate;
                    return true;
                }
            }

            direction = Vector2Int.zero;
            return false;
        }

        private void TryPlaceSelected(Vector2Int anchor)
        {
            BuildableDefinition selected = Buildables[selectedBuildableIndex];
            if (selected.Kind == BuildableKind.Road)
            {
                if (!CanPlaceRoad(anchor, selected, out string roadReason))
                {
                    statusMessage = roadReason;
                    return;
                }

                roadCells.Add(anchor);
                wood -= selected.WoodCost;
                RefreshRoadsAround(anchor);
                statusMessage = "道路铺好了，木材 -" + selected.WoodCost + "。";
                return;
            }

            if (selected.Kind == BuildableKind.Dock)
            {
                if (!CanPlaceDock(anchor, out Vector2Int shoreDirection, out string dockReason))
                {
                    statusMessage = dockReason;
                    return;
                }

                int dockRotation = GetRotationAligning(South, shoreDirection);
                PlaceObject(selected.AssetName, selected.Name, anchor, selected, dockRotation);
                Vector2Int dockSideDirection = shoreDirection.x == 0 ? East : North;
                for (int side = -1; side <= 1; side++)
                {
                    Vector2Int reservedCell = anchor + dockSideDirection * side;
                    if (IsInsideBoard(reservedCell))
                    {
                        occupiedCells.Add(reservedCell);
                    }
                }

                wood -= selected.WoodCost;
                statusMessage = "救援码头建好了，木材 -" + selected.WoodCost + "。";
                return;
            }

            if (!CanPlaceBuilding(anchor, selected, out string reason))
            {
                statusMessage = reason;
                return;
            }

            PlaceObject(selected.AssetName, selected.Name, anchor, selected, rotationDegrees);
            for (int x = 0; x < selected.Width; x++)
            {
                for (int z = 0; z < selected.Depth; z++)
                {
                    occupiedCells.Add(anchor + new Vector2Int(x, z));
                }
            }

            wood -= selected.WoodCost;
            statusMessage = selected.Name + "建好了，木材 -" + selected.WoodCost + "。";
        }

        private void PlaceContinuousRoad(Vector2Int target)
        {
            if (selectedBuildableIndex < 0 || Buildables[selectedBuildableIndex].Kind != BuildableKind.Road)
            {
                return;
            }

            if (!hasLastRoadCell)
            {
                TryPlaceSelected(target);
                lastRoadCell = target;
                hasLastRoadCell = true;
                return;
            }

            Vector2Int cursor = lastRoadCell;
            while (cursor != target)
            {
                int remainingX = target.x - cursor.x;
                int remainingZ = target.y - cursor.y;
                if (Mathf.Abs(remainingX) >= Mathf.Abs(remainingZ) && remainingX != 0)
                {
                    cursor.x += remainingX > 0 ? 1 : -1;
                }
                else if (remainingZ != 0)
                {
                    cursor.y += remainingZ > 0 ? 1 : -1;
                }

                TryPlaceSelected(cursor);
                lastRoadCell = cursor;
            }
        }

        private void PlaceObject(string assetName, string objectName, Vector2Int anchor, BuildableDefinition definition, int rotation)
        {
            GameObject instance = CreatePlaceableObject(assetName, objectName);
            instance.transform.SetParent(mapRoot, false);
            instance.transform.SetLocalPositionAndRotation(
                GetObjectCenter(anchor, definition),
                Quaternion.Euler(0f, rotation, 0f));
            if (definition.Kind == BuildableKind.Building && constructionGrid.TryBuildingFootprint(
                anchor, definition.Width, definition.Depth, out _, out float height))
            {
                GameObject foundation = GameObject.CreatePrimitive(PrimitiveType.Cube);
                foundation.name = "Local terrain foundation";
                foundation.transform.SetParent(instance.transform, false);
                foundation.transform.localPosition = new Vector3(0f, -height * 0.5f, 0f);
                foundation.transform.localScale = new Vector3(definition.Width * 0.96f, height, definition.Depth * 0.96f);
                if (foundationMaterial == null) foundationMaterial = MakeMaterial(new Color(0.29f, 0.30f, 0.28f));
                foundation.GetComponent<Renderer>().sharedMaterial = foundationMaterial;
            }
        }

        private Vector3 GetObjectCenter(Vector2Int anchor, BuildableDefinition definition)
        {
            if (definition.Kind != BuildableKind.Building || constructionGrid == null)
                return CellCenter(anchor);
            constructionGrid.TryBuildingFootprint(anchor, definition.Width, definition.Depth, out Vector3 center, out _);
            return center;
        }

        private void RefreshRoadsAround(Vector2Int cell)
        {
            RefreshRoadAt(cell);
            for (int i = 0; i < CardinalDirections.Length; i++)
            {
                Vector2Int neighbor = cell + CardinalDirections[i];
                if (roadCells.Contains(neighbor))
                {
                    RefreshRoadAt(neighbor);
                }
            }
        }

        private void RefreshRoadAt(Vector2Int cell)
        {
            RoadShape shape = GetRoadShape(cell);
            if (roadObjects.TryGetValue(cell, out GameObject existing) && existing != null)
            {
                Destroy(existing);
            }

            GameObject road = CreatePlaceableObject(shape.AssetName, "Road " + cell.x + "-" + cell.y);
            road.transform.SetParent(mapRoot, false);
            road.transform.SetLocalPositionAndRotation(CellCenter(cell), Quaternion.Euler(0f, shape.RotationDegrees, 0f));
            roadObjects[cell] = road;
        }

        private RoadShape GetRoadShape(Vector2Int cell)
        {
            List<Vector2Int> connections = new List<Vector2Int>(4);
            for (int i = 0; i < CardinalDirections.Length; i++)
            {
                if (roadCells.Contains(cell + CardinalDirections[i]))
                {
                    connections.Add(CardinalDirections[i]);
                }
            }

            if (connections.Count == 4)
            {
                return new RoadShape("RoadCross", 0);
            }

            if (connections.Count == 3)
            {
                Vector2Int[] defaultTee = { West, East, South };
                return new RoadShape("RoadTee", FindRotation(defaultTee, connections));
            }

            if (connections.Count == 2)
            {
                if (connections[0] + connections[1] == Vector2Int.zero)
                {
                    Vector2Int[] defaultStraight = { North, South };
                    return new RoadShape("RoadStraight", FindRotation(defaultStraight, connections));
                }

                Vector2Int[] defaultCorner = { South, East };
                return new RoadShape("RoadCorner", FindRotation(defaultCorner, connections));
            }

            if (connections.Count == 1)
            {
                Vector2Int[] defaultEnd = { South };
                return new RoadShape("RoadEnd", FindRotation(defaultEnd, connections));
            }

            return new RoadShape("RoadStraight", 0);
        }

        private static int FindRotation(Vector2Int[] sourceConnections, IList<Vector2Int> targetConnections)
        {
            for (int rotation = 0; rotation < 360; rotation += 90)
            {
                bool allMatch = sourceConnections.Length == targetConnections.Count;
                for (int i = 0; allMatch && i < sourceConnections.Length; i++)
                {
                    Vector2Int rotated = RotateDirection(sourceConnections[i], rotation);
                    bool found = false;
                    for (int targetIndex = 0; targetIndex < targetConnections.Count; targetIndex++)
                    {
                        if (targetConnections[targetIndex] == rotated)
                        {
                            found = true;
                            break;
                        }
                    }

                    allMatch &= found;
                }

                if (allMatch)
                {
                    return rotation;
                }
            }

            return 0;
        }

        private static int GetRotationAligning(Vector2Int sourceDirection, Vector2Int targetDirection)
        {
            Vector2Int[] source = { sourceDirection };
            Vector2Int[] target = { targetDirection };
            return FindRotation(source, target);
        }

        private static Vector2Int RotateDirection(Vector2Int direction, int degrees)
        {
            switch ((degrees % 360 + 360) % 360)
            {
                case 90:
                    return new Vector2Int(direction.y, -direction.x);
                case 180:
                    return new Vector2Int(-direction.x, -direction.y);
                case 270:
                    return new Vector2Int(-direction.y, direction.x);
                default:
                    return direction;
            }
        }

        private bool IsBuildingTerrainCell(Vector2Int cell)
        {
            return constructionGrid != null && constructionGrid.GetTerrain(cell).AllowsBuilding;
        }

        private bool IsLandCell(Vector2Int cell)
        {
            return constructionGrid != null && constructionGrid.GetTerrain(cell).HasLand;
        }

        private bool IsInsideBoard(Vector2Int cell)
        {
            return constructionGrid != null && constructionGrid.Contains(cell);
        }

        private Vector3 CellCenter(Vector2Int cell)
        {
            return constructionGrid != null ? constructionGrid.CellCenter(cell) : new Vector3(0f, TileTop, 0f);
        }

        private enum BuildableKind
        {
            Building,
            Dock,
            Road
        }

        private sealed class BuildableDefinition
        {
            public readonly string Name;
            public readonly string AssetName;
            public readonly string IconName;
            public readonly int Width;
            public readonly int Depth;
            public readonly int WoodCost;
            public readonly BuildableKind Kind;

            public BuildableDefinition(string name, string assetName, int width, int depth, int woodCost,
                BuildableKind kind = BuildableKind.Building, string iconName = null)
            {
                Name = name;
                AssetName = assetName;
                IconName = string.IsNullOrEmpty(iconName) ? assetName + "_Final" : iconName;
                Width = width;
                Depth = depth;
                WoodCost = woodCost;
                Kind = kind;
            }
        }

        private struct RoadShape
        {
            public readonly string AssetName;
            public readonly int RotationDegrees;

            public RoadShape(string assetName, int rotationDegrees)
            {
                AssetName = assetName;
                RotationDegrees = rotationDegrees;
            }
        }
    }
}
