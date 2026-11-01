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
        private const string LegacyIslandRootName = "Playable Island - Reference V2";
        private const string LegacyIslandModelName = "IslandReference_V2";
        private const string TerrainSourceName = "terrain source";
        private IslandGrassCover grassCover;
        private const string PlaySpaceRootName = "Island Play Space - Rotate and Pan";
        private const float CameraRotationSpeed = 28f;
        private const int VisibleHeaderResourceCount = 4;
        private const float RoadModelImportYawCorrectionDegrees = 180f;
        // Detailed rescue dock: 6.30 m wide, 2.255 m inland and 3.64 m waterward.
        private const int DockHalfWidthCells = 3;
        private const int DockInlandCells = 2;
        private const int DockWaterwardCells = 6;
        private const int TotalHeaderResourceCount = 8;
        private const float CameraZoomFactor = 1.12f;
        private const float MinimumCameraOrthographicSize = 3f;
        private const float MaximumCameraOrthographicSize = 160f;
        private bool usingExpandedArchipelago;
        private Bounds mainIslandFramingBounds;
        private Renderer coastalGridRenderer;
        private Material dockAccessMaterial;
        private Material dockValidPreviewMaterial;
        private Material dockInvalidPreviewMaterial;
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
        private const int SidebarCategoryCount = 5;
        private const float SidebarCategoryButtonSize = 64f;
        private const bool IgnoreBuildingTechnologyForTesting = true;

        private enum SidebarCategory
        {
            Technology,
            Culture,
            Buildings,
            Tasks,
            Warehouse
        }

        public enum BuildCategory
        {
            Residential,
            Production,
            Facilities,
            Transportation
        }

        private static readonly Vector2Int North = new Vector2Int(0, 1);
        private static readonly Vector2Int South = new Vector2Int(0, -1);
        private static readonly Vector2Int East = new Vector2Int(1, 0);
        private static readonly Vector2Int West = new Vector2Int(-1, 0);
        private static readonly Vector2Int[] CardinalDirections = { North, East, South, West };

        private static readonly string[] BuildCategoryNames = { "居住", "生产", "设施", "交通" };
        private static readonly string[] BuildCategoryHeaderNames = { "居住建筑", "生产设施", "公共设施", "交通设施" };

        private static readonly BuildableDefinition[] Buildables =
        {
            new BuildableDefinition("居民小屋", "ResidentHut", 1, 1, 20, BuildableKind.Building, "ResidentHut", 1, BuildCategory.Residential),
            new BuildableDefinition("温室", "Greenhouse", 2, 2, 35, BuildableKind.Building, "Greenhouse", 3, BuildCategory.Production),
            new BuildableDefinition("废料拆解工坊", "SalvageWorkshop", 2, 2, 35, BuildableKind.Building, "SalvageWorkshop", 3, BuildCategory.Production),
            new BuildableDefinition("仓库", "StorageDepot", 2, 2, 25, BuildableKind.Building, "StorageDepot", 1, BuildCategory.Facilities),
            new BuildableDefinition("救援指挥站", "RescueRadioCenter", 2, 2, 45, BuildableKind.Building, "RescueRadioCenter", 4, BuildCategory.Facilities),
            new BuildableDefinition("救援码头", "RescueDock", 1, 1, 35, BuildableKind.Dock, "RescueDock", 1, BuildCategory.Transportation),
            new BuildableDefinition("道路", "RoadStraight", 1, 1, 4, BuildableKind.Road, "RoadTiles", 0, BuildCategory.Transportation),
            new BuildableDefinition("固定海水淡化装置", "DesalinationPlant", 3, 2, 35, BuildableKind.Building, "DesalinationPlant", 1, BuildCategory.Production),
            new BuildableDefinition("医疗站", "MedicalStation", 3, 2, 35, BuildableKind.Building, "MedicalStation", 2, BuildCategory.Facilities),
            new BuildableDefinition("太阳能发电站", "SolarPowerStation", 4, 3, 45, BuildableKind.Building, "SolarPowerStation", 2, BuildCategory.Production),
            new BuildableDefinition("公共厨房", "PublicKitchen", 3, 2, 35, BuildableKind.Building, "PublicKitchen", 3, BuildCategory.Production),
            new BuildableDefinition("锻造炉", "Forge", 2, 2, 40, BuildableKind.Building, "Forge", 3, BuildCategory.Production),
            new BuildableDefinition("木棚", "WoodShelter", 2, 2, 15, BuildableKind.Building, "WoodShelter", 0, BuildCategory.Residential),
            new BuildableDefinition("研究站", "ResearchStation", 3, 3, 40, BuildableKind.Building, "ResearchStation", 0, BuildCategory.Facilities),
            new BuildableDefinition("医疗帐篷", "MedicalTent", 3, 3, 20, BuildableKind.Building, "MedicalTent", 0, BuildCategory.Facilities),
            new BuildableDefinition("初始通讯中心", "LocalCommunicationsCenter", 3, 3, 30, BuildableKind.Building, "LocalCommunicationsCenter", 0, BuildCategory.Facilities),
            new BuildableDefinition("淡水储水罐", "WaterStorageTank", 4, 3, 25, BuildableKind.Building, "WaterStorageTank", 1, BuildCategory.Production),
            new BuildableDefinition("漂木收集浮栅", "DriftwoodCollectionBoom", 9, 3, 30, BuildableKind.Water, "DriftwoodCollectionBoom", 1, BuildCategory.Production),
            new BuildableDefinition("渔船码头", "FishingDock", 1, 1, 35, BuildableKind.Dock, "FishingDock", 1, BuildCategory.Production),
            new BuildableDefinition("气象潮位浮标", "WeatherTideBuoy", 2, 2, 25, BuildableKind.Water, "WeatherTideBuoy", 4, BuildCategory.Facilities),
            new BuildableDefinition("船坞", "Shipyard", 1, 1, 50, BuildableKind.Dock, "Shipyard", 4, BuildCategory.Transportation),
            new BuildableDefinition("救援前哨", "RescueOutpost", 2, 4, 35, BuildableKind.Building, "RescueOutpost", 4, BuildCategory.Facilities),
            new BuildableDefinition("学校", "School", 8, 7, 45, BuildableKind.Building, "School", 5, BuildCategory.Facilities),
            new BuildableDefinition("档案馆", "Archive", 5, 5, 40, BuildableKind.Building, "Archive", 5, BuildCategory.Facilities),
            new BuildableDefinition("议事厅", "CouncilHall", 10, 12, 60, BuildableKind.Building, "CouncilHall", 5, BuildCategory.Facilities)
        };
        private static readonly TechnologyResearchDefinition[] MainlineResearch =
        {
            new TechnologyResearchDefinition(1, "岛屿水文与饮水保障", "掌握淡水循环与漂木流向，建立稳定的近海补给。", 48f,
                "ResearchStation", "LocalCommunicationsCenter"),
            new TechnologyResearchDefinition(2, "稳定供水与太阳能", "完成储水和供电验证，为常驻医疗设施提供基础保障。", 60f,
                "DesalinationPlant", "WaterStorageTank"),
            new TechnologyResearchDefinition(3, "温室种植与食物加工", "建立可持续种植、食品加工与资源回收流程。", 72f,
                "SolarPowerStation", "MedicalStation"),
            new TechnologyResearchDefinition(4, "区域救援与海况观测", "联网观测潮汐天气，并建立救援调度能力。", 84f,
                "Greenhouse", "PublicKitchen"),
            new TechnologyResearchDefinition(5, "社区教育与共同治理", "将教育、共同记忆和自治制度纳入聚落建设。", 96f,
                "RescueRadioCenter", "RescueOutpost"),
            new TechnologyResearchDefinition(6, "回收自动化与生产维护", "改进材料回收、锻造和设施维护流程。", 108f,
                "SalvageWorkshop", "Forge"),
            new TechnologyResearchDefinition(7, "高效农业与区域协作", "共享农业、加工和社区运行数据，提升聚落协作效率。", 120f,
                "Greenhouse", "PublicKitchen", "School", "Archive"),
            new TechnologyResearchDefinition(8, "区域海运与环境联动", "将船坞、海况观测和救援网络联成区域物流体系。", 132f,
                "Shipyard", "WeatherTideBuoy", "RescueRadioCenter"),
            new TechnologyResearchDefinition(9, "自治知识网络", "整合档案、教育和社区治理，完成区域知识网络。", 144f,
                "School", "Archive", "CouncilHall")
        };
        private static readonly string[] HeaderResourceIconNames =
        {
            "Wood", "Food", "Water", "Metal", "Fuel", "Power", "Ore", "Medical"
        };
        private static readonly string[] HeaderResourceDisplayNames =
        {
            "木材", "食物", "淡水", "金属", "燃料", "电力", "矿石", "医疗物资"
        };
        private static readonly string[] SidebarCategoryNames = { "科技", "文化", "建筑", "任务", "仓库" };
        private static readonly string[] CultureRouteNames = { "生存公约", "灾后档案", "岛屿课堂", "新生聚落" };
        private static readonly string[] CultureRouteDetails =
        {
            "确立聚落成员共同遵守的规则。", "记录灾后经历与重要发现。", "建立知识传承与技能教学。", "形成稳定的岛屿社区认同。"
        };

        public sealed class PlacedBuildingData
        {
            public GameObject GameObject;
            public GameObject Foundation;
            public BuildableDefinition Definition;
            public Vector2Int Anchor;
            public int Rotation;
            public List<Vector2Int> OccupiedCells = new List<Vector2Int>();
            public int WoodCost;
        }

        private enum BuildToolMode
        {
            Place,
            Move,
            Demolish
        }

        private BuildToolMode currentToolMode = BuildToolMode.Place;
        private PlacedBuildingData movingBuilding;
        private bool isMovingBuilding;
        private readonly List<PlacedBuildingData> placedBuildingList = new List<PlacedBuildingData>();
        private readonly Dictionary<Vector2Int, PlacedBuildingData> cellToPlacedBuilding = new Dictionary<Vector2Int, PlacedBuildingData>();

        private readonly HashSet<Vector2Int> occupiedCells = new HashSet<Vector2Int>();
        private readonly HashSet<Vector2Int> roadCells = new HashSet<Vector2Int>();
        private readonly HashSet<string> completedBuildableAssets = new HashSet<string>();
        private readonly HashSet<string> researchedEfficiencyKeys = new HashSet<string>();
        private readonly Dictionary<Vector2Int, GameObject> roadObjects = new Dictionary<Vector2Int, GameObject>();
        private readonly List<Material> ownedMaterials = new List<Material>();
        private readonly List<Texture2D> ownedUiTextures = new List<Texture2D>();

        private Camera gameCamera;
        private Transform mapRoot;
        private Transform islandRoot;
        private Transform satelliteIslandsRoot;
        private Transform waterTransform;
        private Material waterMaterial;
        private Transform cameraFollowTarget;

        public IReadOnlyList<PlacedBuildingData> PlacedBuildings => placedBuildingList;
        public IEnumerable<Vector2Int> RoadCells => roadCells;
        public int ResearchLevel => researchLevel;
        public HashSet<string> ResearchedEfficiencyKeys => researchedEfficiencyKeys;
        private Light prototypeSun;
        private IslandWeatherSystem weatherSystem;
        private LighthouseSite lighthouseSite;
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
        private GUIStyle buildPanelStyle;
        private GUIStyle titleStyle;
        private GUIStyle mutedLabelStyle;
        private GUIStyle cardLabelStyle;
        private GUIStyle cardStyle;
        private GUIStyle selectedCardStyle;
        private GUIStyle buildCardStyle;
        private GUIStyle selectedBuildCardStyle;
        private GUIStyle buildCategoryButtonStyle;
        private GUIStyle selectedBuildCategoryButtonStyle;
        private GUIStyle buildCategoryLabelStyle;
        private GUIStyle selectedBuildCategoryLabelStyle;
        private GUIStyle buildCategoryCountStyle;
        private GUIStyle buildCategoryHeadingStyle;
        private GUIStyle sidebarCategoryButtonStyle;
        private GUIStyle sidebarCategorySelectedButtonStyle;
        private GUIStyle sidebarCategoryLabelStyle;
        private GUIStyle closeButtonStyle;
        private GUIStyle transparentButtonStyle;
        private GUIStyle headerResourceValueStyle;
        private GUIStyle resourceNameStyle;
        private GUIStyle resourceValueStyle;
        private GUIStyle topHudSmallLabelStyle;
        private GUIStyle glassPlateStyle;
        private Texture2D glassPlateTexture;
        private IslandWeatherType lastTrackedWeather;
        private IslandWeatherType previousWeather;
        private float weatherTransitionTimer;
        private const float WeatherTransitionDuration = 2.0f; // Stately 2.0s transition

        private int lastTrackedWatchPhase = -1;
        private int previousWatchPhase = -1;
        private float watchPhaseTransitionTimer;
        private const float WatchPhaseTransitionDuration = 1.8f;

        private int lastTrackedSurvivalDay = -1;
        private float dayTransitionTimer;
        private const float DayTransitionDuration = 1.5f;

        private GUIStyle transparentSpeedStyle;
        private GUIStyle transparentSpeedSelectedStyle;
        private GUIStyle speedSegmentStyle;
        private GUIStyle speedSegmentSelectedStyle;
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
        private BuildCategory selectedBuildCategory = BuildCategory.Facilities;
        private int selectedTechnologyTab;
        private int selectedMainlineResearchIndex;
        private string selectedEfficiencyResearchKey = string.Empty;
        private Vector2 mainlineResearchScroll;
        private Vector2 efficiencyResearchScroll;
        private int researchLevel;
        private ResearchType activeResearchType;
        private int activeMainlineResearchIndex = -1;
        private string activeEfficiencyResearchKey = string.Empty;
        private string activeEfficiencyAssetName = string.Empty;
        private int activeEfficiencyTier;
        private float activeResearchProgressSeconds;
        private float activeResearchDurationSeconds;
        private int selectedCultureRouteIndex;
        private int selectedTaskTab;
        private Vector2 taskMenuScroll;
        private Vector2 warehouseMenuScroll;
        private int[] pinnedHeaderResourceIndices = new int[] { 0, 2, 1, 3 }; // 0: Wood, 2: Water, 1: Food, 3: Metal (user specified: 木材淡水食物金属)
        private int activePinnedResourceSlotPicker = -1;
        private int rotationDegrees;
        private bool dockManualRotation;
        private float cameraOrthographicSize = DefaultCameraOrthographicSize;
        private bool hasHoveredCell;
        private bool hasLastRoadCell;
        private bool isBuildMenuOpen;
        private bool isWeatherMenuOpen;
        private bool isResourceMenuOpen;
        private int selectedSimulationSpeedIndex = 1;
        private int lastActiveSpeedIndex = 1;
        private SidebarCategory activeSidebarCategory = SidebarCategory.Buildings;
        private bool isBuildGridVisible = true;
        private bool IsBuildingContextActive =>
            selectedBuildableIndex >= 0 ||
            currentToolMode != BuildToolMode.Place ||
            (isBuildMenuOpen && activeSidebarCategory == SidebarCategory.Buildings);
        private bool isTopDownView;
        private bool isViewDragging;
        private bool viewDragUsesLeftButton;
        private Vector2Int lastRoadCell;
        private Vector2Int hoveredCell;
        private Vector2 buildMenuScroll;
        private Vector3 lastViewDragMousePosition;
        private float cameraPitchBeforeTopDown;
        private string statusMessage = "选择建筑开始建造。";

        public void SetStatusMessage(string message)
        {
            statusMessage = message;
        }
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
            lighthouseSite = GetComponent<LighthouseSite>();
            if (lighthouseSite == null) lighthouseSite = gameObject.AddComponent<LighthouseSite>();
            lighthouseSite.Initialize(mapRoot, FocusLighthouse, () => researchLevel, SpendLighthouseWood);
            CreateCoastDistanceField();
            InitializeWeather();
            CreateGridOverlay();
            EnsureHeaderAssetsLoaded();
            LoadBuildIcons();
            PositionCamera();
            InitializeScenarioCrewAndVessel();
            InitializeColonySystems();
            TripoIslandAssets.ClearDecorations(islandRoot.gameObject);
            TripoVegetationAssets.Apply(islandRoot.gameObject);
            TripoRockAssets.Apply(islandRoot.gameObject);
            if (weatherSystem != null && islandRoot != null)
            {
                weatherSystem.FindFoliage(islandRoot);
            }
            foreach (var renderer in lighthouseSite.GetComponentsInChildren<Renderer>()) renderer.enabled = false;
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
            UpdateTechnologyResearch();

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
                (Buildables[selectedBuildableIndex].Kind == BuildableKind.Building ||
                 Buildables[selectedBuildableIndex].Kind == BuildableKind.Water);
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

            const float visibleFoamWidth = FloodwaterAppearance.FoamWidth;
            const float visibleFoamStrength = FloodwaterAppearance.FoamStrength;
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
                    if (selected.Kind == BuildableKind.Building || selected.Kind == BuildableKind.Water || selected.Kind == BuildableKind.Dock)
                    {
                        RotateSelectedBuilding(90);
                        guiEvent.Use();
                    }
                }
                else if (guiEvent.keyCode == KeyCode.X || guiEvent.keyCode == KeyCode.Delete)
                {
                    if (isMovingBuilding) CancelMove();
                    currentToolMode = (currentToolMode == BuildToolMode.Demolish) ? BuildToolMode.Place : BuildToolMode.Demolish;
                    selectedBuildableIndex = -1;
                    SetBuildGridVisibility(currentToolMode != BuildToolMode.Place);
                    statusMessage = currentToolMode == BuildToolMode.Demolish
                        ? "已进入【拆除模式】(X)：点击建筑或道路拆除并返还50%木材，右键退出。"
                        : "已退出拆除模式。";
                    guiEvent.Use();
                }
                else if (guiEvent.keyCode == KeyCode.M)
                {
                    if (isMovingBuilding) CancelMove();
                    currentToolMode = (currentToolMode == BuildToolMode.Move) ? BuildToolMode.Place : BuildToolMode.Move;
                    selectedBuildableIndex = -1;
                    SetBuildGridVisibility(currentToolMode != BuildToolMode.Place);
                    statusMessage = currentToolMode == BuildToolMode.Move
                        ? "已进入【移动模式】(M)：点击想要移动的建筑进行拾起，右键退出。"
                        : "已退出移动模式。";
                    guiEvent.Use();
                }
                else if (guiEvent.keyCode == KeyCode.G)
                {
                    ActivateHeaderButton(2);
                    guiEvent.Use();
                }
                else if (guiEvent.keyCode == KeyCode.Space)
                {
                    TogglePauseSimulation();
                    guiEvent.Use();
                }
                else if (guiEvent.keyCode == KeyCode.Escape)
                {
                    if (isMovingBuilding)
                    {
                        CancelMove();
                    }
                    else
                    {
                        currentToolMode = BuildToolMode.Place;
                        selectedBuildableIndex = -1;
                        statusMessage = "已取消当前操作。";
                    }
                    guiEvent.Use();
                }
            }

            if (guiEvent.type == EventType.MouseDown)
            {
                if (guiEvent.button == 1)
                {
                    if (isMovingBuilding)
                    {
                        CancelMove();
                    }
                    else if (currentToolMode != BuildToolMode.Place)
                    {
                        currentToolMode = BuildToolMode.Place;
                        statusMessage = "已退出操作模式。";
                    }
                    else
                    {
                        selectedBuildableIndex = -1;
                        hoverMessage = string.Empty;
                        hasLastRoadCell = false;
                        statusMessage = "已退出建造模式。";
                    }
                    guiEvent.Use();
                }
                else if (guiEvent.button == 0 && !IsPointerOverUi(
                             guiEvent.mousePosition, panelRect, topBarRect, isBuildMenuOpen) &&
                         !closedHudMenuThisClick && hasHoveredCell && !ColonyModalDialog.IsDialogOpen)
                {
                    if (currentToolMode == BuildToolMode.Demolish)
                    {
                        DemolishAt(hoveredCell);
                        guiEvent.Use();
                    }
                    else if (currentToolMode == BuildToolMode.Move)
                    {
                        if (!isMovingBuilding)
                        {
                            if (cellToPlacedBuilding.TryGetValue(hoveredCell, out PlacedBuildingData target))
                            {
                                StartMoveBuilding(target);
                            }
                            else
                            {
                                statusMessage = "该地格没有可移动的建筑。";
                            }
                        }
                        else
                        {
                            TryCommitMove(hoveredCell);
                        }
                        guiEvent.Use();
                    }
                    else if (selectedBuildableIndex >= 0)
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
                    else if (currentToolMode == BuildToolMode.Place)
                    {
                        if (cellToPlacedBuilding.TryGetValue(hoveredCell, out PlacedBuildingData inspected))
                        {
                            BuildingInspectorUI.Inspect(inspected);
                        }
                        else
                        {
                            BuildingInspectorUI.Close();
                        }
                        guiEvent.Use();
                    }
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

            if (isKnowledgeFullscreenOpen)
            {
                DrawSteamAgeKnowledgeFullscreen();
            }
        }


        // =========================================================================
        // STEAM AGE FULLSCREEN KNOWLEDGE & CULTURE DECK (蒸汽时代全屏科技文化工坊)
        // Reference: Frostpunk / Age of Steam layout covering entire viewport
        // =========================================================================
        private bool isKnowledgeFullscreenOpen = false;
        private int knowledgeFullscreenTab = 0; // 0 = 科技 (Technology), 1 = 文化 (Culture)
        private Vector2 steamTechScrollPos = Vector2.zero;
        private Vector2 steamCultureScrollPos = Vector2.zero;
        private int steamSelectedMainlineIndex = 1;
        private string steamSelectedEfficiencyKey = null;
        private int steamSelectedCultureIndex = 0;

        // Culture policies state
        private readonly HashSet<string> enactedCulturePolicies = new HashSet<string>();

        private struct SteamCulturePolicy
        {
            public string Id;
            public int Branch; // 0: 存续纪律, 1: 共同记忆, 2: 聚落自治
            public string BranchName;
            public string Title;
            public string Subtitle;
            public string Lore;
            public string Effects;
            public int RequiredLevel; // R level
            public int WoodCost;
        }

        private static readonly SteamCulturePolicy[] CulturePolicies = new[]
        {
            new SteamCulturePolicy
            {
                Id = "InitialCompact",
                Branch = 0,
                BranchName = "存续纪律",
                Title = "初抵配给公约",
                Subtitle = "随队应急口粮配额制与净水严格供给准则",
                Lore = "小队初抵沉船海域，前哨物资极其有限。确立聚落生活配给公约，定员定额统筹应急净水器与干粮分配，严禁擅自挥霍。",
                Effects = "• 食物与淡水日消耗 -15%\n• 岛民抗病耐力显著提升",
                RequiredLevel = 0,
                WoodCost = 15
            },
            new SteamCulturePolicy
            {
                Id = "WorkShifts",
                Branch = 0,
                BranchName = "存续纪律",
                Title = "昼夜巡守与工时轮换",
                Subtitle = "规范白班与夜间巡守，建立连续轮班作息",
                Lore = "随着海水淡化设备与太阳能电网落地，工时安排从杂乱无章转向标准化轮班。保障设备全天候运转与夜间值守安全。",
                Effects = "• 所有生产设施效率 +10%\n• 设备意外故障率降低",
                RequiredLevel = 1,
                WoodCost = 25
            },
            new SteamCulturePolicy
            {
                Id = "DisasterArchive",
                Branch = 1,
                BranchName = "共同记忆",
                Title = "海难勘察与灾后档案",
                Subtitle = "整理沉船遗留物资与群岛失联航海日志",
                Lore = "通讯中心与档案馆联动，细致勘察沉船撞击痕迹，搜集遇难船员日志并建立海难档案，将悲痛转化为重建航标的集体决心。",
                Effects = "• 灯塔重建木材消耗 -10%\n• 搜救声望累计速率 +20%",
                RequiredLevel = 1,
                WoodCost = 20
            },
            new SteamCulturePolicy
            {
                Id = "KnowledgeLineage",
                Branch = 1,
                BranchName = "共同记忆",
                Title = "群岛知识谱系与工匠传承",
                Subtitle = "在学校与档案馆建立完整的工程技艺传授体系",
                Lore = "图纸不能永远依赖总部远程传输。通过老船员带教新学徒，将岛屿水文、种植与机械维护经验编纂成册，代代相传。",
                Effects = "• 所有主线科技研究耗时 -20%\n• 建筑效率校准速度 +25%",
                RequiredLevel = 3,
                WoodCost = 35
            },
            new SteamCulturePolicy
            {
                Id = "IslandCouncil",
                Branch = 2,
                BranchName = "聚落自治",
                Title = "长桌议事与聚落自治会",
                Subtitle = "设立岛民议事制度，实现共同商议与自主治理",
                Lore = "基地吸纳多方获救者后，单纯的指令式管理已无法满足社区需求。在议事厅设立长桌议事会，推动平权协作与聚落自治。",
                Effects = "• 岛民士气大幅提振 (工作积极性 +20%)\n• 建筑施工速度 +15%",
                RequiredLevel = 4,
                WoodCost = 45
            },
            new SteamCulturePolicy
            {
                Id = "EcologicalStewardship",
                Branch = 2,
                BranchName = "聚落自治",
                Title = "近海休渔与生态共生准则",
                Subtitle = "规范漂木浮栅循环利用，严禁近海过度捕捞",
                Lore = "海岛空间脆弱封闭。设定捕鱼休养季，并强制推行废料浮栅循环利用，避免近海渔业与林木资源枯竭，确保聚落永续生存。",
                Effects = "• 漂木浮栅木材捕获量 +20%\n• 渔船码头鱼类持续丰产度 +15%",
                RequiredLevel = 2,
                WoodCost = 30
            }
        };

        public void OpenKnowledgeFullscreen(int tabIndex)
        {
            isKnowledgeFullscreenOpen = true;
            knowledgeFullscreenTab = Mathf.Clamp(tabIndex, 0, 1);
            isBuildMenuOpen = false;
            isWeatherMenuOpen = false;
            isResourceMenuOpen = false;

            if (activeResearchType == ResearchType.Mainline && activeMainlineResearchIndex >= 0)
            {
                steamSelectedMainlineIndex = activeMainlineResearchIndex;
                steamSelectedEfficiencyKey = null;
            }
            else if (steamSelectedEfficiencyKey == null)
            {
                steamSelectedMainlineIndex = Mathf.Clamp(researchLevel + 1, 1, MainlineResearch.Length - 1);
            }
        }

        private void DrawSteamAgeKnowledgeFullscreen()
        {
            float scale = GetHudScale();
            Rect screenRect = new Rect(0f, 0f, Screen.width, Screen.height);

            // 1. Deep Atmospheric Steampunk Slate-Iron Background
            DrawHudDivider(screenRect, new Color(0.05f, 0.07f, 0.09f, 0.98f));

            // Blueprint grid lines
            Color gridColor = new Color(0.18f, 0.25f, 0.32f, 0.09f);
            float gridSize = 40f * scale;
            for (float x = 0; x < Screen.width; x += gridSize)
            {
                DrawHudDivider(new Rect(x, 0, 1f, Screen.height), gridColor);
            }
            for (float y = 0; y < Screen.height; y += gridSize)
            {
                DrawHudDivider(new Rect(0, y, Screen.width, 1f), gridColor);
            }

            // Outer Brass Riveted Framing
            Color outerBorderColor = new Color(0.85f, 0.70f, 0.38f, 0.65f);
            DrawHudDivider(new Rect(0, 0, Screen.width, 3f), outerBorderColor);
            DrawHudDivider(new Rect(0, Screen.height - 3f, Screen.width, 3f), outerBorderColor);
            DrawHudDivider(new Rect(0, 0, 3f, Screen.height), outerBorderColor);
            DrawHudDivider(new Rect(Screen.width - 3f, 0, 3f, Screen.height), outerBorderColor);

            // 2. Steampunk Header Deck
            float headerH = 62f * scale;
            Rect headerRect = new Rect(0f, 0f, Screen.width, headerH);
            DrawHudDivider(headerRect, new Color(0.08f, 0.11f, 0.15f, 0.95f));
            DrawHudDivider(new Rect(0, headerH - 2f, Screen.width, 2f), new Color(0.85f, 0.70f, 0.38f, 0.75f));

            // Left Logo & Era Badge
            GUIStyle logoStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(19f * scale), 16, 23),
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleLeft
            };
            logoStyle.normal.textColor = new Color(0.95f, 0.82f, 0.50f);
            GUI.Label(new Rect(24f * scale, 8f * scale, 340f * scale, 28f * scale), "⚙ 蒸汽时代 · 聚落知识工坊", logoStyle);

            GUIStyle eraBadgeStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 14),
                fontStyle = FontStyle.Normal,
                alignment = TextAnchor.MiddleLeft
            };
            eraBadgeStyle.normal.textColor = new Color(0.70f, 0.78f, 0.85f);
            string activeResearchStr = activeResearchType != ResearchType.None
                ? " | 正在研发: " + GetActiveResearchName() + " (" + Mathf.CeilToInt(Mathf.Max(0f, activeResearchDurationSeconds - activeResearchProgressSeconds)) + "s)"
                : " | 科研队列就绪";
            GUI.Label(new Rect(24f * scale, 34f * scale, 420f * scale, 20f * scale),
                "主线科研等级：时代 R" + researchLevel + " / 9" + activeResearchStr, eraBadgeStyle);

            // Center Dual Mode Switcher: [ ⚙ 科学与工程技术 (Technology) ] vs [ ⚖ 聚落法令与文化 (Culture) ]
            float tabBtnW = 190f * scale;
            float tabBtnH = 34f * scale;
            float tabGap = 10f * scale;
            float totalTabW = tabBtnW * 2f + tabGap;
            float tabStartX = (Screen.width - totalTabW) * 0.5f;
            float tabY = (headerH - tabBtnH) * 0.5f;

            string[] tabNames = { "⚙ 科学与工程 (Technology)", "⚖ 聚落法令与文化 (Culture)" };
            for (int t = 0; t < 2; t++)
            {
                Rect tRect = new Rect(tabStartX + t * (tabBtnW + tabGap), tabY, tabBtnW, tabBtnH);
                bool isSelected = knowledgeFullscreenTab == t;
                bool isHov = tRect.Contains(Event.current.mousePosition);

                // Tab button plate
                Color bg = isSelected ? new Color(0.85f, 0.68f, 0.28f, 0.35f) : (isHov ? new Color(1f, 1f, 1f, 0.10f) : new Color(0.04f, 0.06f, 0.08f, 0.6f));
                DrawHudDivider(tRect, bg);
                Color border = isSelected ? new Color(1f, 0.88f, 0.45f, 0.90f) : (isHov ? new Color(0.85f, 0.70f, 0.38f, 0.50f) : new Color(0.40f, 0.45f, 0.50f, 0.30f));
                DrawHudDivider(new Rect(tRect.x, tRect.y, tRect.width, 1.5f), border);
                DrawHudDivider(new Rect(tRect.x, tRect.yMax - 1.5f, tRect.width, 1.5f), border);
                DrawHudDivider(new Rect(tRect.x, tRect.y, 1.5f, tRect.height), border);
                DrawHudDivider(new Rect(tRect.xMax - 1.5f, tRect.y, 1.5f, tRect.height), border);

                if (isSelected)
                {
                    DrawHudDivider(new Rect(tRect.x + 12f * scale, tRect.yMax - 3f, tRect.width - 24f * scale, 3f), new Color(1f, 0.88f, 0.45f, 1f));
                }

                GUIStyle tabStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = Mathf.Clamp(Mathf.RoundToInt(13f * scale), 11, 16),
                    fontStyle = isSelected ? FontStyle.Bold : FontStyle.Normal,
                    alignment = TextAnchor.MiddleCenter
                };
                tabStyle.normal.textColor = isSelected ? Color.white : (isHov ? new Color(1f, 0.92f, 0.60f) : new Color(0.78f, 0.82f, 0.86f));

                if (GUI.Button(tRect, tabNames[t], tabStyle))
                {
                    knowledgeFullscreenTab = t;
                }
            }

            // Right Close / Esc Button
            float closeBtnW = 140f * scale;
            float closeBtnH = 34f * scale;
            Rect closeBtnRect = new Rect(Screen.width - closeBtnW - 20f * scale, (headerH - closeBtnH) * 0.5f, closeBtnW, closeBtnH);
            bool closeHov = closeBtnRect.Contains(Event.current.mousePosition);
            DrawHudDivider(closeBtnRect, closeHov ? new Color(0.6f, 0.15f, 0.15f, 0.65f) : new Color(0.12f, 0.15f, 0.18f, 0.70f));
            DrawHudDivider(new Rect(closeBtnRect.x, closeBtnRect.y, closeBtnRect.width, 1f), closeHov ? Color.red : new Color(0.85f, 0.70f, 0.38f, 0.50f));
            DrawHudDivider(new Rect(closeBtnRect.x, closeBtnRect.yMax - 1f, closeBtnRect.width, 1f), closeHov ? Color.red : new Color(0.85f, 0.70f, 0.38f, 0.50f));
            DrawHudDivider(new Rect(closeBtnRect.x, closeBtnRect.y, 1f, closeBtnRect.height), closeHov ? Color.red : new Color(0.85f, 0.70f, 0.38f, 0.50f));
            DrawHudDivider(new Rect(closeBtnRect.xMax - 1f, closeBtnRect.y, 1f, closeBtnRect.height), closeHov ? Color.red : new Color(0.85f, 0.70f, 0.38f, 0.50f));

            GUIStyle closeStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(13f * scale), 11, 15),
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter
            };
            closeStyle.normal.textColor = closeHov ? Color.white : new Color(0.90f, 0.92f, 0.94f);
            if (GUI.Button(closeBtnRect, "✕ 返回海岛 (ESC)", closeStyle))
            {
                isKnowledgeFullscreenOpen = false;
            }

            // 3. Main Body Split: Left Tree Canvas (72% width) & Right Blueprint Inspector (28% width)
            float inspectorW = Mathf.Clamp(420f * scale, 340f, 500f);
            float bodyY = headerH;
            float bodyH = Screen.height - bodyY;
            Rect canvasRect = new Rect(0f, bodyY, Screen.width - inspectorW, bodyH);
            Rect inspectorRect = new Rect(Screen.width - inspectorW, bodyY, inspectorW, bodyH);

            if (knowledgeFullscreenTab == 0)
            {
                DrawSteamAgeTechTree(canvasRect, scale);
                DrawSteamAgeTechInspector(inspectorRect, scale);
            }
            else
            {
                DrawSteamAgeCultureTree(canvasRect, scale);
                DrawSteamAgeCultureInspector(inspectorRect, scale);
            }

            // Eat all mouse events in fullscreen so nothing clicks through to 3D world
            if (Event.current.type == EventType.MouseDown || Event.current.type == EventType.MouseUp || Event.current.type == EventType.ScrollWheel)
            {
                Event.current.Use();
            }
        }

        // =========================================================================
        // 1. TECHNOLOGY TREE (科学与工程 - 时代分栏与蒸汽管道布局)
        // =========================================================================
        private void DrawSteamAgeTechTree(Rect canvasRect, float scale)
        {
            // Era information
            string[] eraTitles =
            {
                "时代 0 · 初始前哨",
                "时代 I · 饮水保障",
                "时代 II · 能源医疗",
                "时代 III · 农业加工",
                "时代 IV · 远洋观测",
                "时代 V · 社区自治",
                "时代 VI · 回收自动化",
                "时代 VII · 高效农业",
                "时代 VIII · 海运联动",
                "时代 IX · 自治知识网"
            };

            float colW = 210f * scale;
            float colGap = 42f * scale;
            float totalColsW = 10 * colW + 9 * colGap + 60f * scale;
            float contentH = canvasRect.height - 20f * scale;

            Rect viewRect = new Rect(0f, 0f, totalColsW, Mathf.Max(contentH, 680f * scale));
            steamTechScrollPos = GUI.BeginScrollView(canvasRect, steamTechScrollPos, viewRect, true, false);

            float startX = 30f * scale;
            float mainlineY = 80f * scale;
            float nodeW = colW;
            float nodeH = 118f * scale;

            // Draw horizontal conduit steam pipes connecting all 10 mainline nodes
            for (int e = 0; e < 9; e++)
            {
                float x1 = startX + e * (colW + colGap) + nodeW;
                float x2 = startX + (e + 1) * (colW + colGap);
                float py = mainlineY + nodeH * 0.5f;
                bool isConduitActive = e < researchLevel;
                DrawSteamConduit(new Vector2(x1, py), new Vector2(x2, py), isConduitActive, scale);
            }

            // Loop each Era Column
            for (int e = 0; e < 10; e++)
            {
                float cx = startX + e * (colW + colGap);

                // Era Column Header Plate
                Rect eraPlateRect = new Rect(cx, 16f * scale, colW, 36f * scale);
                bool isCurrentEra = e == researchLevel;
                bool isPastEra = e < researchLevel;
                Color eraPlateCol = isPastEra ? new Color(0.20f, 0.28f, 0.22f, 0.85f)
                    : (isCurrentEra ? new Color(0.45f, 0.35f, 0.12f, 0.90f) : new Color(0.10f, 0.12f, 0.15f, 0.70f));
                DrawHudDivider(eraPlateRect, eraPlateCol);
                DrawHudDivider(new Rect(eraPlateRect.x, eraPlateRect.y, eraPlateRect.width, 1.5f),
                    isCurrentEra ? new Color(1f, 0.85f, 0.40f, 0.90f) : new Color(0.70f, 0.60f, 0.40f, 0.45f));
                DrawHudDivider(new Rect(eraPlateRect.x, eraPlateRect.yMax - 1f, eraPlateRect.width, 1f),
                    isCurrentEra ? new Color(1f, 0.85f, 0.40f, 0.90f) : new Color(0.70f, 0.60f, 0.40f, 0.45f));

                GUIStyle eraTitleStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = Mathf.Clamp(Mathf.RoundToInt(13f * scale), 11, 15),
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter
                };
                eraTitleStyle.normal.textColor = isCurrentEra ? new Color(1f, 0.95f, 0.70f) : (isPastEra ? new Color(0.85f, 0.95f, 0.88f) : new Color(0.65f, 0.70f, 0.75f));
                GUI.Label(eraPlateRect, eraTitles[e], eraTitleStyle);

                // Mainline Node Card
                Rect nodeRect = new Rect(cx, mainlineY, nodeW, nodeH);
                bool isMainlineSelected = steamSelectedEfficiencyKey == null && steamSelectedMainlineIndex == e;

                // State determination: 0=Completed, 1=Researching, 2=Available, 3=Locked
                int nodeState;
                string statePill;
                Color pillColor;
                if (e == 0)
                {
                    nodeState = 0;
                    statePill = "✔ 初始落脚点";
                    pillColor = new Color(0.40f, 0.85f, 0.50f);
                }
                else
                {
                    TechnologyResearchDefinition def = MainlineResearch[e];
                    if (def.Level <= researchLevel)
                    {
                        nodeState = 0;
                        statePill = "✔ 核心已掌握";
                        pillColor = new Color(0.40f, 0.85f, 0.50f);
                    }
                    else if (activeResearchType == ResearchType.Mainline && activeMainlineResearchIndex == e)
                    {
                        nodeState = 1;
                        statePill = "⚙ 研发推进中 (" + Mathf.FloorToInt((activeResearchProgressSeconds / Mathf.Max(0.1f, activeResearchDurationSeconds)) * 100f) + "%)";
                        pillColor = new Color(1f, 0.75f, 0.25f);
                    }
                    else if (CanStartMainlineResearch(e, out _))
                    {
                        nodeState = 2;
                        statePill = "◈ 可启动研究";
                        pillColor = new Color(1f, 0.88f, 0.45f);
                    }
                    else
                    {
                        nodeState = 3;
                        statePill = e == researchLevel + 1 ? "🔒 待建成前置" : "🔒 待解锁上一代";
                        pillColor = new Color(0.65f, 0.68f, 0.72f);
                    }
                }

                string nodeTitle = e == 0 ? "R0 初始前哨建立" : "R" + e + " " + MainlineResearch[e].Name;
                string nodeSub = e == 0 ? "随队装备与前哨基础采集" : MainlineResearch[e].Description;

                DrawSteamNodeCard(nodeRect, nodeTitle, nodeSub, statePill, pillColor, nodeState, isMainlineSelected, scale);

                if (GUI.Button(nodeRect, GUIContent.none, GUIStyle.none))
                {
                    steamSelectedMainlineIndex = e;
                    steamSelectedEfficiencyKey = null;
                }

                // Vertical conduit down to Efficiency Upgrades
                float effStartY = mainlineY + nodeH + 35f * scale;
                DrawSteamConduit(new Vector2(cx + nodeW * 0.5f, mainlineY + nodeH),
                    new Vector2(cx + nodeW * 0.5f, effStartY - 10f * scale), e <= researchLevel, scale);

                // Section header for Efficiency Upgrades
                GUIStyle effHeaderStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = Mathf.Clamp(Mathf.RoundToInt(11f * scale), 9, 13),
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter
                };
                effHeaderStyle.normal.textColor = new Color(0.85f, 0.75f, 0.55f);
                GUI.Label(new Rect(cx, effStartY - 14f * scale, nodeW, 18f * scale), "── 设施效率研究 ──", effHeaderStyle);

                // List matching efficiency options for this era
                List<EfficiencyResearchOption> effList = GetEfficiencyOptionsForEra(e);
                float curEffY = effStartY + 10f * scale;
                float effCardH = 68f * scale;

                if (effList.Count == 0)
                {
                    Rect emptyCard = new Rect(cx, curEffY, nodeW, 46f * scale);
                    DrawHudDivider(emptyCard, new Color(0.06f, 0.08f, 0.10f, 0.40f));
                    GUIStyle emptyStyle = new GUIStyle(GUI.skin.label)
                    {
                        fontSize = Mathf.Clamp(Mathf.RoundToInt(10f * scale), 8, 12),
                        alignment = TextAnchor.MiddleCenter
                    };
                    emptyStyle.normal.textColor = new Color(0.50f, 0.55f, 0.60f);
                    GUI.Label(emptyCard, "该时代无额外效率课题", emptyStyle);
                }
                else
                {
                    for (int k = 0; k < effList.Count; k++)
                    {
                        EfficiencyResearchOption opt = effList[k];
                        string effKey = GetEfficiencyResearchKey(opt.AssetName, opt.Tier);
                        bool isCompleted = researchedEfficiencyKeys.Contains(effKey);
                        bool isResearching = activeResearchType == ResearchType.Efficiency && activeEfficiencyResearchKey == effKey;
                        bool canStart = !isCompleted && !isResearching && CanResearchEfficiency(FindBuildable(opt.AssetName), opt.Tier);

                        int effState = isCompleted ? 0 : (isResearching ? 1 : (canStart ? 2 : 3));
                        string effPill = isCompleted ? "✔ 已强化" : (isResearching ? "⚙ 校准中" : (canStart ? "◈ 可校准" : "🔒 未达成"));
                        Color effPillCol = isCompleted ? new Color(0.40f, 0.85f, 0.50f) : (isResearching ? new Color(1f, 0.75f, 0.25f) : (canStart ? new Color(1f, 0.88f, 0.45f) : new Color(0.60f, 0.65f, 0.70f)));

                        Rect effCardRect = new Rect(cx, curEffY, nodeW, effCardH);
                        bool isEffSelected = steamSelectedEfficiencyKey == effKey;

                        string effTitle = opt.BuildingName + " 效率 " + (opt.Tier == 1 ? "I (+10%)" : "II (+15%)");
                        string effSub = "门槛: R" + opt.RequiredResearchLevel + " · 需岛上建成";

                        DrawSteamNodeCard(effCardRect, effTitle, effSub, effPill, effPillCol, effState, isEffSelected, scale);

                        if (GUI.Button(effCardRect, GUIContent.none, GUIStyle.none))
                        {
                            steamSelectedEfficiencyKey = effKey;
                        }

                        curEffY += effCardH + 12f * scale;
                    }
                }
            }

            GUI.EndScrollView();
        }

        private List<EfficiencyResearchOption> GetEfficiencyOptionsForEra(int era)
        {
            List<EfficiencyResearchOption> list = new List<EfficiencyResearchOption>();
            for (int i = 0; i < Buildables.Length; i++)
            {
                BuildableDefinition b = Buildables[i];
                if (b.Kind == BuildableKind.Road) continue;

                // Tier 1 efficiency opens at R = L + 2
                if (b.ScenarioLevel + 2 == era)
                {
                    list.Add(new EfficiencyResearchOption(b.AssetName, b.Name, 1, b.ScenarioLevel + 2));
                }
                // Tier 2 efficiency opens at R = L + 4
                if (b.ScenarioLevel + 4 == era)
                {
                    list.Add(new EfficiencyResearchOption(b.AssetName, b.Name, 2, b.ScenarioLevel + 4));
                }
            }
            return list;
        }

        // =========================================================================
        // 2. TECHNOLOGY INSPECTOR (右侧科技蓝图规格面板)
        // =========================================================================
        private void DrawSteamAgeTechInspector(Rect panelRect, float scale)
        {
            // Background plate with brass rivet frame
            DrawHudDivider(panelRect, new Color(0.08f, 0.10f, 0.13f, 0.96f));
            DrawHudDivider(new Rect(panelRect.x, panelRect.y, 2f, panelRect.height), new Color(0.85f, 0.70f, 0.38f, 0.65f));

            float pad = 18f * scale;
            float contentW = panelRect.width - pad * 2f;
            float curY = panelRect.y + 16f * scale;

            // Efficiency research inspect mode
            if (!string.IsNullOrEmpty(steamSelectedEfficiencyKey))
            {
                DrawEfficiencyInspectorContent(panelRect, pad, contentW, ref curY, scale);
                return;
            }

            // Mainline tech inspect mode
            int idx = Mathf.Clamp(steamSelectedMainlineIndex, 0, MainlineResearch.Length - 1);
            TechnologyResearchDefinition def = MainlineResearch[idx];

            string title = idx == 0 ? "R0 初始前哨建立" : "R" + def.Level + " " + def.Name;
            float duration = idx == 0 ? 0f : def.DurationSeconds;

            // Header Cog & Title
            GUIStyle headTitleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(17f * scale), 14, 21),
                fontStyle = FontStyle.Bold,
                wordWrap = true
            };
            headTitleStyle.normal.textColor = new Color(0.96f, 0.85f, 0.52f);
            float titleH = headTitleStyle.CalcHeight(new GUIContent(title), contentW);
            GUI.Label(new Rect(panelRect.x + pad, curY, contentW, titleH), title, headTitleStyle);
            curY += titleH + 4f * scale;

            // Badge row: Level & Duration
            string tierStr = idx == 0 ? "【基础前哨 · 时代 0】" : "【核心时代推进 · R" + def.Level + "】";
            string timeStr = idx == 0 ? "自带掌握" : "标准耗时: " + Mathf.RoundToInt(duration) + " 模拟秒";
            GUIStyle badgeStyle = new GUIStyle(GUI.skin.label) { fontSize = Mathf.Clamp(Mathf.RoundToInt(11f * scale), 9, 13) };
            badgeStyle.normal.textColor = new Color(0.68f, 0.75f, 0.82f);
            GUI.Label(new Rect(panelRect.x + pad, curY, contentW, 20f * scale), tierStr + "   " + timeStr, badgeStyle);
            curY += 26f * scale;

            DrawHudDivider(new Rect(panelRect.x + pad, curY, contentW, 1f), new Color(0.85f, 0.70f, 0.38f, 0.35f));
            curY += 10f * scale;

            // Section 1: 课题背景与战略目标 (from progression doc)
            DrawSectionHeader("【 📜 课题档案与战略背景 】", panelRect.x + pad, ref curY, contentW, scale);
            string loreText = GetTechLore(idx);
            GUIStyle bodyStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 14),
                wordWrap = true
            };
            bodyStyle.normal.textColor = new Color(0.82f, 0.86f, 0.90f);
            float loreH = bodyStyle.CalcHeight(new GUIContent(loreText), contentW);
            GUI.Label(new Rect(panelRect.x + pad, curY, contentW, loreH), loreText, bodyStyle);
            curY += loreH + 16f * scale;

            // Section 2: 前置设施与科研准则
            DrawSectionHeader("【 ⚙ 前置建筑与科研准则 】", panelRect.x + pad, ref curY, contentW, scale);
            if (idx == 0)
            {
                GUI.Label(new Rect(panelRect.x + pad, curY, contentW, 20f * scale), "✔ 无需额外前置，抵达即可着手建设", bodyStyle);
                curY += 24f * scale;
            }
            else
            {
                // Research Station check
                bool hasStation = completedBuildableAssets.Contains("ResearchStation");
                DrawPrereqItem("研究站 (科研队列核心)", hasStation, panelRect.x + pad, ref curY, contentW, scale);

                for (int r = 0; r < def.RequiredAssets.Length; r++)
                {
                    string reqAsset = def.RequiredAssets[r];
                    bool hasBuilt = completedBuildableAssets.Contains(reqAsset);
                    DrawPrereqItem(GetBuildableDisplayName(reqAsset), hasBuilt, panelRect.x + pad, ref curY, contentW, scale);
                }
            }
            curY += 8f * scale;

            // Section 3: 解锁设施与技术加成
            DrawSectionHeader("【 🔨 对应解锁设施与功能 】", panelRect.x + pad, ref curY, contentW, scale);
            string unlocksText = GetTechUnlocks(idx);
            float unlockH = bodyStyle.CalcHeight(new GUIContent(unlocksText), contentW);
            GUI.Label(new Rect(panelRect.x + pad, curY, contentW, unlockH), unlocksText, bodyStyle);
            curY += unlockH + 20f * scale;

            // Section 4: 研发指令中枢
            DrawHudDivider(new Rect(panelRect.x + pad, curY, contentW, 1f), new Color(0.85f, 0.70f, 0.38f, 0.35f));
            curY += 12f * scale;

            if (idx == 0 || def.Level <= researchLevel)
            {
                Rect doneBox = new Rect(panelRect.x + pad, curY, contentW, 44f * scale);
                DrawHudDivider(doneBox, new Color(0.18f, 0.35f, 0.22f, 0.50f));
                GUIStyle doneStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = Mathf.Clamp(Mathf.RoundToInt(13f * scale), 11, 16),
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter
                };
                doneStyle.normal.textColor = new Color(0.45f, 0.90f, 0.55f);
                GUI.Label(doneBox, "✔ 该时代技术已在全岛推广生效", doneStyle);
            }
            else if (activeResearchType == ResearchType.Mainline && activeMainlineResearchIndex == idx)
            {
                float prog = Mathf.Clamp01(activeResearchProgressSeconds / Mathf.Max(0.1f, activeResearchDurationSeconds));
                float rem = Mathf.CeilToInt(Mathf.Max(0f, activeResearchDurationSeconds - activeResearchProgressSeconds));

                Rect progBox = new Rect(panelRect.x + pad, curY, contentW, 50f * scale);
                DrawHudDivider(progBox, new Color(0.15f, 0.12f, 0.05f, 0.70f));
                DrawHudDivider(new Rect(progBox.x, progBox.y, progBox.width * prog, progBox.height), new Color(0.85f, 0.65f, 0.20f, 0.55f));

                GUIStyle progStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = Mathf.Clamp(Mathf.RoundToInt(13f * scale), 11, 15),
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter
                };
                progStyle.normal.textColor = Color.white;
                GUI.Label(progBox, "⚙ 正在研发中... " + Mathf.FloorToInt(prog * 100f) + "% (" + rem + "s 剩余)", progStyle);
            }
            else if (CanStartMainlineResearch(idx, out string reason))
            {
                Rect actionBtn = new Rect(panelRect.x + pad, curY, contentW, 46f * scale);
                bool btnHov = actionBtn.Contains(Event.current.mousePosition);

                DrawHudDivider(actionBtn, btnHov ? new Color(0.95f, 0.72f, 0.25f, 0.85f) : new Color(0.85f, 0.60f, 0.18f, 0.65f));
                DrawHudDivider(new Rect(actionBtn.x, actionBtn.y, actionBtn.width, 2f), new Color(1f, 0.92f, 0.55f, 1f));
                DrawHudDivider(new Rect(actionBtn.x, actionBtn.yMax - 2f, actionBtn.width, 2f), new Color(1f, 0.92f, 0.55f, 1f));

                GUIStyle actionStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = Mathf.Clamp(Mathf.RoundToInt(14f * scale), 12, 17),
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter
                };
                actionStyle.normal.textColor = btnHov ? Color.black : Color.white;

                if (GUI.Button(actionBtn, "⚙ 启动该课题研发 (耗时 " + Mathf.RoundToInt(duration) + "s)", actionStyle))
                {
                    StartMainlineResearch(idx);
                }
            }
            else
            {
                Rect lockBox = new Rect(panelRect.x + pad, curY, contentW, 44f * scale);
                DrawHudDivider(lockBox, new Color(0.18f, 0.12f, 0.12f, 0.60f));
                GUIStyle lockStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 14),
                    alignment = TextAnchor.MiddleCenter
                };
                lockStyle.normal.textColor = new Color(0.95f, 0.55f, 0.45f);
                GUI.Label(lockBox, "🔒 未达成: " + reason, lockStyle);
            }
        }

        private void DrawEfficiencyInspectorContent(Rect panelRect, float pad, float contentW, ref float curY, float scale)
        {
            string[] parts = steamSelectedEfficiencyKey.Split('|');
            string assetName = parts[0];
            int tier = int.Parse(parts[2]);
            BuildableDefinition b = FindBuildable(assetName);
            string bName = b != null ? b.Name : assetName;

            string title = bName + " 效率校准 (阶级 " + tier + ")";
            GUIStyle headTitleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(17f * scale), 14, 21),
                fontStyle = FontStyle.Bold
            };
            headTitleStyle.normal.textColor = new Color(0.96f, 0.85f, 0.52f);
            GUI.Label(new Rect(panelRect.x + pad, curY, contentW, 28f * scale), title, headTitleStyle);
            curY += 32f * scale;

            DrawHudDivider(new Rect(panelRect.x + pad, curY, contentW, 1f), new Color(0.85f, 0.70f, 0.38f, 0.35f));
            curY += 12f * scale;

            DrawSectionHeader("【 📜 效率校准规范 】", panelRect.x + pad, ref curY, contentW, scale);
            string effDesc = "依据《剧本科技方案》：建筑效率研究在 R = L + " + (tier == 1 ? "2" : "4") +
                " 开放。对应建筑必须已经在岛上建成并投入运行，研究站才能依据现场数据完成校准优化。\n\n本次校准提升该设施基础运行效率 +" +
                (tier == 1 ? "10%" : "15%") + "，两次完成后累计提升 +25%（不复利计算）。";
            GUIStyle bodyStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 14),
                wordWrap = true
            };
            bodyStyle.normal.textColor = new Color(0.82f, 0.86f, 0.90f);
            float h = bodyStyle.CalcHeight(new GUIContent(effDesc), contentW);
            GUI.Label(new Rect(panelRect.x + pad, curY, contentW, h), effDesc, bodyStyle);
            curY += h + 16f * scale;

            DrawSectionHeader("【 ⚙ 门槛条件检测 】", panelRect.x + pad, ref curY, contentW, scale);
            bool isBuilt = completedBuildableAssets.Contains(assetName);
            int reqR = b != null ? b.ScenarioLevel + (tier == 1 ? 2 : 4) : 99;
            bool hasLevel = researchLevel >= reqR;

            DrawPrereqItem(bName + " (已在岛上建成运行)", isBuilt, panelRect.x + pad, ref curY, contentW, scale);
            DrawPrereqItem("主线科研等级达到时代 R" + reqR, hasLevel, panelRect.x + pad, ref curY, contentW, scale);
            curY += 16f * scale;

            // Action
            bool isCompleted = researchedEfficiencyKeys.Contains(steamSelectedEfficiencyKey);
            bool isRunning = activeResearchType == ResearchType.Efficiency && activeEfficiencyResearchKey == steamSelectedEfficiencyKey;

            if (isCompleted)
            {
                Rect doneBox = new Rect(panelRect.x + pad, curY, contentW, 44f * scale);
                DrawHudDivider(doneBox, new Color(0.18f, 0.35f, 0.22f, 0.50f));
                GUIStyle doneStyle = new GUIStyle(GUI.skin.label) { fontSize = 13, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
                doneStyle.normal.textColor = new Color(0.45f, 0.90f, 0.55f);
                GUI.Label(doneBox, "✔ 该设施效率加成已生效", doneStyle);
            }
            else if (isRunning)
            {
                float prog = Mathf.Clamp01(activeResearchProgressSeconds / Mathf.Max(0.1f, activeResearchDurationSeconds));
                Rect progBox = new Rect(panelRect.x + pad, curY, contentW, 46f * scale);
                DrawHudDivider(progBox, new Color(0.15f, 0.12f, 0.05f, 0.70f));
                DrawHudDivider(new Rect(progBox.x, progBox.y, progBox.width * prog, progBox.height), new Color(0.85f, 0.65f, 0.20f, 0.55f));
                GUIStyle progStyle = new GUIStyle(GUI.skin.label) { fontSize = 13, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
                progStyle.normal.textColor = Color.white;
                GUI.Label(progBox, "⚙ 效率校准中... " + Mathf.FloorToInt(prog * 100f) + "%", progStyle);
            }
            else if (CanResearchEfficiency(b, tier) && activeResearchType == ResearchType.None)
            {
                Rect actionBtn = new Rect(panelRect.x + pad, curY, contentW, 46f * scale);
                bool btnHov = actionBtn.Contains(Event.current.mousePosition);
                DrawHudDivider(actionBtn, btnHov ? new Color(0.95f, 0.72f, 0.25f, 0.85f) : new Color(0.85f, 0.60f, 0.18f, 0.65f));

                GUIStyle actionStyle = new GUIStyle(GUI.skin.label) { fontSize = 14, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
                actionStyle.normal.textColor = btnHov ? Color.black : Color.white;

                if (GUI.Button(actionBtn, "⚙ 启动效率校准 (耗时 36s)", actionStyle))
                {
                    StartEfficiencyResearch(assetName, tier);
                }
            }
            else
            {
                Rect lockBox = new Rect(panelRect.x + pad, curY, contentW, 44f * scale);
                DrawHudDivider(lockBox, new Color(0.18f, 0.12f, 0.12f, 0.60f));
                GUIStyle lockStyle = new GUIStyle(GUI.skin.label) { fontSize = 12, alignment = TextAnchor.MiddleCenter };
                lockStyle.normal.textColor = new Color(0.95f, 0.55f, 0.45f);
                GUI.Label(lockBox, "🔒 前置未达成或科研站忙碌", lockStyle);
            }
        }

        // =========================================================================
        // 3. CULTURE TREE & INSPECTOR (聚落法令与文化政策 - 蒸汽时代治理风格)
        // =========================================================================
        private void DrawSteamAgeCultureTree(Rect canvasRect, float scale)
        {
            string[] branchNames = { "分支 I · 存续纪律", "分支 II · 共同记忆", "分支 III · 聚落自治" };
            float colW = 270f * scale;
            float colGap = 50f * scale;
            float totalW = 3 * colW + 2 * colGap + 60f * scale;

            Rect viewRect = new Rect(0f, 0f, totalW, canvasRect.height - 20f * scale);
            steamCultureScrollPos = GUI.BeginScrollView(canvasRect, steamCultureScrollPos, viewRect, true, false);

            float startX = 40f * scale;

            for (int b = 0; b < 3; b++)
            {
                float cx = startX + b * (colW + colGap);

                // Branch Header
                Rect bHeader = new Rect(cx, 16f * scale, colW, 36f * scale);
                DrawHudDivider(bHeader, new Color(0.15f, 0.18f, 0.22f, 0.90f));
                DrawHudDivider(new Rect(bHeader.x, bHeader.y, bHeader.width, 1.5f), new Color(0.85f, 0.70f, 0.38f, 0.60f));
                DrawHudDivider(new Rect(bHeader.x, bHeader.yMax - 1f, bHeader.width, 1f), new Color(0.85f, 0.70f, 0.38f, 0.60f));

                GUIStyle bhStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = Mathf.Clamp(Mathf.RoundToInt(14f * scale), 12, 16),
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter
                };
                bhStyle.normal.textColor = new Color(0.95f, 0.88f, 0.65f);
                GUI.Label(bHeader, branchNames[b], bhStyle);

                // Filter policies for this branch
                List<int> pIndices = new List<int>();
                for (int p = 0; p < CulturePolicies.Length; p++)
                {
                    if (CulturePolicies[p].Branch == b) pIndices.Add(p);
                }

                float cardY = 75f * scale;
                float cardH = 110f * scale;

                for (int k = 0; k < pIndices.Count; k++)
                {
                    int pIdx = pIndices[k];
                    SteamCulturePolicy pol = CulturePolicies[pIdx];
                    bool isEnacted = enactedCulturePolicies.Contains(pol.Id);
                    bool canEnact = !isEnacted && researchLevel >= pol.RequiredLevel;
                    bool isSelected = steamSelectedCultureIndex == pIdx;

                    int cState = isEnacted ? 0 : (canEnact ? 2 : 3);
                    string cPill = isEnacted ? "✔ 已签署生效" : (canEnact ? "◈ 可颁布法案" : "🔒 时代未达 (需R" + pol.RequiredLevel + ")");
                    Color cPillCol = isEnacted ? new Color(0.40f, 0.85f, 0.50f) : (canEnact ? new Color(1f, 0.88f, 0.45f) : new Color(0.60f, 0.65f, 0.70f));

                    Rect cardRect = new Rect(cx, cardY, colW, cardH);
                    DrawSteamNodeCard(cardRect, pol.Title, pol.Subtitle, cPill, cPillCol, cState, isSelected, scale);

                    if (GUI.Button(cardRect, GUIContent.none, GUIStyle.none))
                    {
                        steamSelectedCultureIndex = pIdx;
                    }

                    // Vertical connecting pipe between doctrines
                    if (k < pIndices.Count - 1)
                    {
                        float pipeStartY = cardY + cardH;
                        float pipeEndY = cardY + cardH + 28f * scale;
                        DrawSteamConduit(new Vector2(cx + colW * 0.5f, pipeStartY),
                            new Vector2(cx + colW * 0.5f, pipeEndY), isEnacted, scale);
                    }

                    cardY += cardH + 28f * scale;
                }
            }

            GUI.EndScrollView();
        }

        private void DrawSteamAgeCultureInspector(Rect panelRect, float scale)
        {
            DrawHudDivider(panelRect, new Color(0.08f, 0.10f, 0.13f, 0.96f));
            DrawHudDivider(new Rect(panelRect.x, panelRect.y, 2f, panelRect.height), new Color(0.85f, 0.70f, 0.38f, 0.65f));

            float pad = 18f * scale;
            float contentW = panelRect.width - pad * 2f;
            float curY = panelRect.y + 16f * scale;

            int pIdx = Mathf.Clamp(steamSelectedCultureIndex, 0, CulturePolicies.Length - 1);
            SteamCulturePolicy pol = CulturePolicies[pIdx];

            // Header
            GUIStyle headTitleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(17f * scale), 14, 21),
                fontStyle = FontStyle.Bold
            };
            headTitleStyle.normal.textColor = new Color(0.96f, 0.85f, 0.52f);
            GUI.Label(new Rect(panelRect.x + pad, curY, contentW, 28f * scale), pol.Title, headTitleStyle);
            curY += 32f * scale;

            GUIStyle badgeStyle = new GUIStyle(GUI.skin.label) { fontSize = Mathf.Clamp(Mathf.RoundToInt(11f * scale), 9, 13) };
            badgeStyle.normal.textColor = new Color(0.68f, 0.75f, 0.82f);
            GUI.Label(new Rect(panelRect.x + pad, curY, contentW, 20f * scale),
                "【" + pol.BranchName + "】   门槛要求: 时代 R" + pol.RequiredLevel + "   消耗木材: " + pol.WoodCost, badgeStyle);
            curY += 26f * scale;

            DrawHudDivider(new Rect(panelRect.x + pad, curY, contentW, 1f), new Color(0.85f, 0.70f, 0.38f, 0.35f));
            curY += 12f * scale;

            DrawSectionHeader("【 📜 法令渊源与聚落记忆 】", panelRect.x + pad, ref curY, contentW, scale);
            GUIStyle bodyStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 14),
                wordWrap = true
            };
            bodyStyle.normal.textColor = new Color(0.82f, 0.86f, 0.90f);
            float h1 = bodyStyle.CalcHeight(new GUIContent(pol.Lore), contentW);
            GUI.Label(new Rect(panelRect.x + pad, curY, contentW, h1), pol.Lore, bodyStyle);
            curY += h1 + 16f * scale;

            DrawSectionHeader("【 ⚖ 颁布法令实际效力 】", panelRect.x + pad, ref curY, contentW, scale);
            float h2 = bodyStyle.CalcHeight(new GUIContent(pol.Effects), contentW);
            GUI.Label(new Rect(panelRect.x + pad, curY, contentW, h2), pol.Effects, bodyStyle);
            curY += h2 + 24f * scale;

            // Enact Action
            bool isEnacted = enactedCulturePolicies.Contains(pol.Id);
            bool canEnact = !isEnacted && researchLevel >= pol.RequiredLevel && AvailableWood >= pol.WoodCost;

            if (isEnacted)
            {
                Rect doneBox = new Rect(panelRect.x + pad, curY, contentW, 44f * scale);
                DrawHudDivider(doneBox, new Color(0.18f, 0.35f, 0.22f, 0.50f));
                GUIStyle doneStyle = new GUIStyle(GUI.skin.label) { fontSize = 13, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
                doneStyle.normal.textColor = new Color(0.45f, 0.90f, 0.55f);
                GUI.Label(doneBox, "✔ 该聚落法令已在全岛推行", doneStyle);
            }
            else if (canEnact)
            {
                Rect enactBtn = new Rect(panelRect.x + pad, curY, contentW, 46f * scale);
                bool btnHov = enactBtn.Contains(Event.current.mousePosition);
                DrawHudDivider(enactBtn, btnHov ? new Color(0.95f, 0.72f, 0.25f, 0.85f) : new Color(0.85f, 0.60f, 0.18f, 0.65f));

                GUIStyle actionStyle = new GUIStyle(GUI.skin.label) { fontSize = 14, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
                actionStyle.normal.textColor = btnHov ? Color.black : Color.white;

                if (GUI.Button(enactBtn, "⚖ 签署并颁布该项法令 (木材 -" + pol.WoodCost + ")", actionStyle))
                {
                    SpendWood(pol.WoodCost);
                    enactedCulturePolicies.Add(pol.Id);
                    statusMessage = "【法令颁布】" + pol.Title + "已生效！";
                }
            }
            else
            {
                Rect lockBox = new Rect(panelRect.x + pad, curY, contentW, 44f * scale);
                DrawHudDivider(lockBox, new Color(0.18f, 0.12f, 0.12f, 0.60f));
                GUIStyle lockStyle = new GUIStyle(GUI.skin.label) { fontSize = 12, alignment = TextAnchor.MiddleCenter };
                lockStyle.normal.textColor = new Color(0.95f, 0.55f, 0.45f);
                string rReason = researchLevel < pol.RequiredLevel ? ("需达到时代 R" + pol.RequiredLevel) : "木材不足 (需 " + pol.WoodCost + ")";
                GUI.Label(lockBox, "🔒 无法签署: " + rReason, lockStyle);
            }
        }

        // =========================================================================
        // 4. STEAM CONDUIT & NODE CARD DRAWING HELPERS
        // =========================================================================
        private void DrawSteamConduit(Vector2 start, Vector2 end, bool isActive, float scale)
        {
            Vector2 dir = end - start;
            float length = dir.magnitude;
            if (length < 1f) return;

            // Outer dark pipe sheath
            Color pipeSheath = new Color(0.12f, 0.14f, 0.16f, 0.95f);
            // Core pressurized steam glow
            Color steamCore = isActive ? new Color(1.0f, 0.78f, 0.35f, 0.90f) : new Color(0.24f, 0.28f, 0.32f, 0.50f);

            bool isHorizontal = Mathf.Abs(dir.x) >= Mathf.Abs(dir.y);
            float thickness = 6f * scale;

            if (isHorizontal)
            {
                float rx = Mathf.Min(start.x, end.x);
                float ry = start.y - thickness * 0.5f;
                DrawHudDivider(new Rect(rx, ry, length, thickness), pipeSheath);
                DrawHudDivider(new Rect(rx, ry + 1.5f * scale, length, thickness - 3f * scale), steamCore);

                // Flange joint rings
                DrawHudDivider(new Rect(rx, ry - 2f * scale, 4f * scale, thickness + 4f * scale), new Color(0.85f, 0.70f, 0.38f, 0.85f));
                DrawHudDivider(new Rect(rx + length - 4f * scale, ry - 2f * scale, 4f * scale, thickness + 4f * scale), new Color(0.85f, 0.70f, 0.38f, 0.85f));
            }
            else
            {
                float rx = start.x - thickness * 0.5f;
                float ry = Mathf.Min(start.y, end.y);
                DrawHudDivider(new Rect(rx, ry, thickness, length), pipeSheath);
                DrawHudDivider(new Rect(rx + 1.5f * scale, ry, thickness - 3f * scale, length), steamCore);

                // Flange joint rings
                DrawHudDivider(new Rect(rx - 2f * scale, ry, thickness + 4f * scale, 4f * scale), new Color(0.85f, 0.70f, 0.38f, 0.85f));
                DrawHudDivider(new Rect(rx - 2f * scale, ry + length - 4f * scale, thickness + 4f * scale, 4f * scale), new Color(0.85f, 0.70f, 0.38f, 0.85f));
            }
        }

        private void DrawSteamNodeCard(Rect rect, string title, string subtitle, string pillText, Color pillColor,
            int state, bool isSelected, float scale)
        {
            bool isHovered = rect.Contains(Event.current.mousePosition);

            // Card background: Completed, Active, Available, Locked
            Color cardBg;
            switch (state)
            {
                case 0: // Completed
                    cardBg = isSelected ? new Color(0.18f, 0.32f, 0.22f, 0.95f) : (isHovered ? new Color(0.14f, 0.24f, 0.18f, 0.90f) : new Color(0.10f, 0.16f, 0.12f, 0.85f));
                    break;
                case 1: // Researching
                    cardBg = isSelected ? new Color(0.35f, 0.25f, 0.08f, 0.95f) : (isHovered ? new Color(0.28f, 0.20f, 0.06f, 0.90f) : new Color(0.20f, 0.14f, 0.04f, 0.85f));
                    break;
                case 2: // Available
                    cardBg = isSelected ? new Color(0.25f, 0.22f, 0.14f, 0.95f) : (isHovered ? new Color(0.18f, 0.16f, 0.10f, 0.90f) : new Color(0.12f, 0.14f, 0.16f, 0.85f));
                    break;
                default: // Locked
                    cardBg = isSelected ? new Color(0.14f, 0.16f, 0.18f, 0.90f) : (isHovered ? new Color(0.10f, 0.12f, 0.14f, 0.80f) : new Color(0.07f, 0.08f, 0.10f, 0.70f));
                    break;
            }

            DrawHudDivider(rect, cardBg);

            // Brass Filigree Borders
            Color borderCol;
            if (isSelected) borderCol = new Color(1f, 0.90f, 0.45f, 1f);
            else if (state == 1) borderCol = new Color(1f, 0.75f, 0.25f, 0.85f);
            else if (isHovered) borderCol = new Color(0.85f, 0.70f, 0.38f, 0.85f);
            else borderCol = state == 3 ? new Color(0.35f, 0.40f, 0.45f, 0.35f) : new Color(0.70f, 0.58f, 0.32f, 0.55f);

            float bThick = isSelected ? 2f : 1.5f;
            DrawHudDivider(new Rect(rect.x, rect.y, rect.width, bThick), borderCol);
            DrawHudDivider(new Rect(rect.x, rect.yMax - bThick, rect.width, bThick), borderCol);
            DrawHudDivider(new Rect(rect.x, rect.y, bThick, rect.height), borderCol);
            DrawHudDivider(new Rect(rect.xMax - bThick, rect.y, bThick, rect.height), borderCol);

            // Steampunk Corner Rivets
            float rivet = 4f * scale;
            Color rivetCol = new Color(0.85f, 0.70f, 0.38f, 0.75f);
            DrawHudDivider(new Rect(rect.x + 2f, rect.y + 2f, rivet, rivet), rivetCol);
            DrawHudDivider(new Rect(rect.xMax - 2f - rivet, rect.y + 2f, rivet, rivet), rivetCol);
            DrawHudDivider(new Rect(rect.x + 2f, rect.yMax - 2f - rivet, rivet, rivet), rivetCol);
            DrawHudDivider(new Rect(rect.xMax - 2f - rivet, rect.yMax - 2f - rivet, rivet, rivet), rivetCol);

            // Status Pill
            float pillW = rect.width - 24f * scale;
            float pillH = 20f * scale;
            Rect pillRect = new Rect(rect.x + 12f * scale, rect.y + 8f * scale, pillW, pillH);
            DrawHudDivider(pillRect, new Color(pillColor.r * 0.25f, pillColor.g * 0.25f, pillColor.b * 0.25f, 0.65f));
            DrawHudDivider(new Rect(pillRect.x, pillRect.yMax - 1f, pillRect.width, 1f), new Color(pillColor.r, pillColor.g, pillColor.b, 0.5f));

            GUIStyle pillStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(10f * scale), 9, 12),
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter
            };
            pillStyle.normal.textColor = pillColor;
            GUI.Label(pillRect, pillText, pillStyle);

            // Card Title
            GUIStyle cardTitleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(13f * scale), 11, 15),
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleLeft,
                wordWrap = true
            };
            cardTitleStyle.normal.textColor = state == 3 ? new Color(0.70f, 0.72f, 0.75f) : (isSelected ? Color.white : new Color(0.95f, 0.88f, 0.65f));
            float titleY = rect.y + 32f * scale;
            GUI.Label(new Rect(rect.x + 12f * scale, titleY, rect.width - 24f * scale, 42f * scale), title, cardTitleStyle);

            // Card Subtitle / effect
            GUIStyle subStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(10f * scale), 8, 12),
                alignment = TextAnchor.MiddleLeft,
                wordWrap = true
            };
            subStyle.normal.textColor = new Color(0.65f, 0.70f, 0.75f);
            GUI.Label(new Rect(rect.x + 12f * scale, rect.yMax - 32f * scale, rect.width - 24f * scale, 28f * scale), subtitle, subStyle);
        }

        private void DrawSectionHeader(string text, float x, ref float y, float width, float scale)
        {
            GUIStyle sStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(13f * scale), 11, 15),
                fontStyle = FontStyle.Bold
            };
            sStyle.normal.textColor = new Color(0.85f, 0.72f, 0.42f);
            GUI.Label(new Rect(x, y, width, 22f * scale), text, sStyle);
            y += 24f * scale;
        }

        private void DrawPrereqItem(string name, bool isCompleted, float x, ref float y, float width, float scale)
        {
            GUIStyle pStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 14),
                alignment = TextAnchor.MiddleLeft
            };
            pStyle.normal.textColor = isCompleted ? new Color(0.45f, 0.90f, 0.55f) : new Color(0.95f, 0.50f, 0.40f);
            string icon = isCompleted ? "✔ [已建成] " : "✖ [尚未建成] ";
            GUI.Label(new Rect(x, y, width, 20f * scale), icon + name, pStyle);
            y += 22f * scale;
        }

        private string GetTechLore(int level)
        {
            switch (level)
            {
                case 0:
                    return "玩家带着两名船员、一艘快艇、通信设备、基础口粮、初始木材和应急净水器抵达岛屿。小队勘察周边海域后向总部汇报，总部确认建立前哨，开启海岛扎根生存。";
                case 1:
                    return "研究站依据总部图纸开展本地验证。首要任务是查明海域水文与漂木流向，通过海水淡化设备与储水罐确保生命之源，并依托漂木浮栅与渔业维持初期补给。";
                case 2:
                    return "临时电源即将耗尽，聚落亟需建立本地稳定供电。利用太阳能电网驱动固定淡化设备与专业医疗站，改善初期恶劣卫生条件，防范热带疾病与意外创伤。";
                case 3:
                    return "随队口粮告急，组装总部送达的温室设备并按本地水质气候校准。高科技温室承担稳定种植任务，结合公共厨房与金属锻造工坊，形成食物生产与资源再生闭环。";
                case 4:
                    return "基地物资充裕后，将通讯能力扩展到远距离联网与区域搜救调度。设置气象与潮位浮标预警风暴，建造大型船坞维护快艇，建立前哨站向周边海域辐射救援。";
                case 5:
                    return "接纳各方获救幸存者后，前哨正式转型为成熟群岛文明聚落。建造学校、档案馆与议事厅，推动知识代际传承、灾后记忆归档与社群自治。";
                case 6:
                    return "升级废料拆解工坊与锻造炉的自动化联动，大幅度提高深海打捞残骸的拆解效率与金属纯度，减轻全岛设施的磨损与维护压力。";
                case 7:
                    return "统筹温室水肥、厨房热食与学校管理数据，构建高效农业闭环，实现全天候稳定产出与食品储备，支持更大规模的人口承载。";
                case 8:
                    return "将船坞、海况观测浮标与长距救援指挥站联为一体化海运中枢，快艇续航与搜救半径全面突破，形成高效的区域物流与避险走廊。";
                default:
                    return "整合历史档案、教育传承和议事厅自治制度，实现海岛避难所向永久自给自足文明共同体的终极蜕变，让文明在风暴之后永续闪耀。";
            }
        }

        private string GetTechUnlocks(int level)
        {
            switch (level)
            {
                case 0:
                    return "• 木棚 (居住类 2×2)\n• 研究站 (设施类 3×3)\n• 医疗帐篷 (设施类 3×3)\n• 初始通讯中心 (设施类 3×3)\n• 基础土路 (交通类 1×1)";
                case 1:
                    return "• 固定海水淡化装置 (生产类 3×2)\n• 淡水储水罐 (生产类 4×3)\n• 漂木收集浮栅 (近海生产 9×3)\n• 渔船码头 (码头类 1×1)\n• 基础仓库 (设施类 2×2)\n• 救援码头 (码头类 1×1)\n• 居民小屋 (居住类 1×1)";
                case 2:
                    return "• 太阳能发电站 (生产类 4×3)\n• 医疗站 (设施类 3×2)\n• 本地清洁电网系统";
                case 3:
                    return "• 高科技温室 (生产类 2×2)\n• 公共厨房 (生产类 3×2)\n• 废料拆解工坊 (生产类 2×2)\n• 锻造炉 (生产类 2×2)";
                case 4:
                    return "• 救援指挥／长距通讯站 (设施类 2×2)\n• 气象与潮位浮标 (近海水体 2×2)\n• 船坞 (码头类 1×1)\n• 救援前哨 (设施类 2×4)";
                case 5:
                    return "• 学校 (设施类 8×7)\n• 档案馆 (设施类 5×5)\n• 议事厅 (设施类 10×12)";
                default:
                    return "• 对应全岛生产设施深度自动化与效率加成\n• 主线全部阶段核心成就";
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
                Bounds framingBounds = usingExpandedArchipelago ? mainIslandFramingBounds : islandVisibleBounds;
                Vector3 extent = framingBounds.extents;
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
                cameraOrbitTarget = framingBounds.center + up *
                    ((topReserve - bottomReserve) * cameraOrthographicSize);
                defaultCameraOrbitDistance = Mathf.Max(72f, islandVisibleBounds.size.magnitude * 1.4f);
            }
            cameraOrbitDistance = defaultCameraOrbitDistance;
            ClampCameraView();
            UpdateCameraPose();
        }

        private bool SpendLighthouseWood(int amount)
        {
            return SpendWood(amount);
        }

        private int AvailableWood => ColonyResourceManager.Instance != null
            ? Mathf.FloorToInt(ColonyResourceManager.Instance.Wood) : wood;

        private bool SpendWood(int amount)
        {
            var resources = ColonyResourceManager.Instance;
            if (resources != null)
            {
                if (!resources.TrySpend(ResourceType.Wood, amount)) return false;
                wood = Mathf.FloorToInt(resources.Wood);
                return true;
            }
            if (wood < amount) return false;
            wood -= amount;
            return true;
        }

        private void RefundWood(int amount)
        {
            var resources = ColonyResourceManager.Instance;
            if (resources == null) { wood += amount; return; }
            resources.Add(ResourceType.Wood, amount);
            wood = Mathf.FloorToInt(resources.Wood);
        }

        public void CloseTransientHudMenus()
        {
            isWeatherMenuOpen = false;
            isResourceMenuOpen = false;
        }

        private void FocusLighthouse(Vector3 point)
        {
            cameraOrbitTarget = point;
            cameraOrthographicSize = 38f;
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
            if (cameraFollowTarget != null)
            {
                cameraOrbitTarget = cameraFollowTarget.position;
            }
            Quaternion cameraRotation = Quaternion.Euler(cameraOrbitPitchDegrees, cameraOrbitYawDegrees, 0f);
            gameCamera.transform.SetPositionAndRotation(
                cameraOrbitTarget + cameraRotation * Vector3.back * cameraOrbitDistance,
                cameraRotation);
        }

        private static readonly SidebarCategory[] SidebarDisplayOrder = {
            SidebarCategory.Buildings,
            SidebarCategory.Technology,
            SidebarCategory.Culture,
            SidebarCategory.Tasks,
            SidebarCategory.Warehouse
        };

        private bool hasCustomBuildPanelPos = false;
        private Vector2 customBuildPanelPos;
        private bool isDraggingBuildPanel = false;
        private Vector2 dragBuildPanelMouseStartPos;
        private Vector2 dragBuildPanelStartPos;

        private Rect GetPanelRect()
        {
            float scale = GetHudScale();
            float panelTop = GetTopBarTop() + GetTopBarHeight() + 8f * scale;
            float height = Mathf.Max(360f, Mathf.Min(620f, Screen.height - panelTop - 16f));
            float panelWidth = 430f * scale;
            if (hasCustomBuildPanelPos)
            {
                float clampedX = Mathf.Clamp(customBuildPanelPos.x, 8f, Mathf.Max(8f, Screen.width - panelWidth - 8f));
                float clampedY = Mathf.Clamp(customBuildPanelPos.y, 8f, Mathf.Max(8f, Screen.height - height - 8f));
                return new Rect(clampedX, clampedY, panelWidth, height);
            }
            float x = Mathf.Max(16f, Screen.width - 160f * scale - 26f * scale - panelWidth);
            return new Rect(x, panelTop, panelWidth, height);
        }

        private Rect GetSidebarCategoryButtonRect(int displayIndex)
        {
            float scale = GetHudScale();
            float buttonWidth = 58f * scale;
            float buttonHeight = 62f * scale;
            float gap = 12f * scale;
            float x = 16f * scale;
            float y = GetTopBarTop() + GetTopBarHeight() + 22f * scale + displayIndex * (buttonHeight + gap);
            return new Rect(x, y, buttonWidth, buttonHeight);
        }

        public void CollapseResourceDetails() { isResourceMenuOpen = false; }
        public bool BlocksWorldOrders(Vector2 point) => selectedBuildableIndex >= 0 || isMovingBuilding || IsPointerOverUi(point, GetPanelRect(), GetTopBarRect(), isBuildMenuOpen);
        public bool IsNavigationCellOccupied(Vector2Int cell) => occupiedCells.Contains(cell);

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
            return Mathf.Clamp(Screen.height * 0.095f, 74f, 102f);
        }

        private bool IsPointerOverUi(Vector2 pointer, Rect panelRect, Rect topBarRect, bool isPanelOpen)
        {
            if (isKnowledgeFullscreenOpen) return true;
            if (BuildingInspectorUI.ContainsPoint(pointer)) return true;
            if (VesselOrdersUI.ContainsPoint(pointer)) return true;
            if (lighthouseSite != null && lighthouseSite.ContainsPointer(pointer)) return true;
            if (activePinnedResourceSlotPicker >= 0)
            {
                float s = GetHudScale();
                float pickerX = 468f * s + activePinnedResourceSlotPicker * (98f + 5f) * s;
                float pickerY = topBarRect.yMax + 4f * s;
                float pickerW = 145f * s;
                float pickerH = TotalHeaderResourceCount * 28f * s + 26f * s;
                if (new Rect(pickerX, pickerY, pickerW, pickerH).Contains(pointer)) return true;
            }
            float slotScale = GetHudScale();
            if (new Rect(468f * slotScale, topBarRect.y, (4f * 103f) * slotScale, topBarRect.height).Contains(pointer))
            {
                return true;
            }
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

            for (int i = 0; i < SidebarCategoryCount; i++)
            {
                if (GetSidebarCategoryButtonRect(i).Contains(pointer))
                {
                    return true;
                }
            }

            return false;
        }

        private void EnsureGuiStyles()
        {
            EnsureSidebarCategoryUi();
            EnsureSidebarCategoryStyles();
            EnsureGlassPlateStyle();
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
            Texture2D buildPanelTexture = MakeRoundedUiTexture(128, 128, 16,
                new Color(0.035f, 0.08f, 0.083f, 0.82f));
            Texture2D buildCardTexture = MakeRoundedUiTexture(64, 64, 10,
                new Color(0.12f, 0.15f, 0.17f, 0.80f));
            Texture2D selectedBuildCardTexture = MakeRoundedUiTexture(64, 64, 10,
                new Color(0.30f, 0.27f, 0.17f, 0.92f));
            Texture2D buildHoverTexture = MakeRoundedUiTexture(64, 64, 10,
                new Color(0.20f, 0.25f, 0.28f, 0.90f));
            Texture2D buildActiveTexture = MakeRoundedUiTexture(64, 64, 10,
                new Color(0.36f, 0.31f, 0.19f, 0.95f));
            Texture2D buildCategoryTexture = MakeRoundedUiTexture(64, 64, 12,
                new Color(0.09f, 0.12f, 0.14f, 0.70f));
            Texture2D selectedBuildCategoryTexture = MakeRoundedUiTexture(64, 64, 12,
                new Color(0.45f, 0.38f, 0.21f, 0.92f));
            Texture2D buildCategoryHoverTexture = MakeRoundedUiTexture(64, 64, 12,
                new Color(0.20f, 0.25f, 0.28f, 0.85f));
            Texture2D buildCategoryActiveTexture = MakeRoundedUiTexture(64, 64, 12,
                new Color(0.52f, 0.44f, 0.25f, 0.95f));
            panelStyle = new GUIStyle(GUI.skin.box);
            panelStyle.normal.background = HudTheme.Panel;
            panelStyle.border = new RectOffset(12, 12, 12, 12);
            buildPanelStyle = new GUIStyle(GUI.skin.box);
            buildPanelStyle.normal.background = HudTheme.Panel;
            buildPanelStyle.border = new RectOffset(12, 12, 12, 12);

            headerResourceValueStyle = CreateHeaderLabelStyle(12, FontStyle.Bold, TextAnchor.MiddleCenter,
                new Color(0.96f, 0.84f, 0.48f));
            headerResourceValueStyle.wordWrap = false;

            topHudSmallLabelStyle = CreateHeaderLabelStyle(10, FontStyle.Normal, TextAnchor.MiddleLeft,
                new Color(0.91f, 0.94f, 0.95f));
            topHudClockStyle = CreateHeaderLabelStyle(22, FontStyle.Normal, TextAnchor.MiddleCenter,
                new Color(0.96f, 0.97f, 0.98f));
            Texture2D speedHoverTexture = MakeRoundedUiTexture(64, 64, 18,
                new Color(0.86f, 0.73f, 0.44f, 0.16f));
            Texture2D speedSelectedTexture = MakeRoundedUiTexture(64, 64, 18,
                new Color(0.86f, 0.73f, 0.44f, 0.38f));
            Texture2D speedSelectedHoverTexture = MakeRoundedUiTexture(64, 64, 18,
                new Color(0.90f, 0.78f, 0.48f, 0.52f));
            topHudSpeedStyle = CreateButtonStyle(
                clearTexture, speedHoverTexture,
                MakeRoundedUiTexture(64, 64, 18, new Color(0.86f, 0.73f, 0.44f, 0.28f)));
            topHudSpeedStyle.alignment = TextAnchor.MiddleCenter;
            topHudSpeedStyle.fontSize = 13;
            topHudSpeedStyle.fontStyle = FontStyle.Bold;
            topHudSpeedStyle.border = new RectOffset(18, 18, 18, 18);
            topHudSpeedStyle.normal.textColor = new Color(0.92f, 0.95f, 0.96f);
            topHudSpeedStyle.hover.textColor = Color.white;
            topHudSpeedSelectedStyle = CreateButtonStyle(
                speedSelectedTexture, speedSelectedHoverTexture,
                MakeRoundedUiTexture(64, 64, 18, new Color(0.86f, 0.73f, 0.44f, 0.60f)));
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
            topHudTabStyle.fontSize = 19;
            topHudTabStyle.fontStyle = FontStyle.Normal;
            topHudTabStyle.normal.textColor = new Color(0.89f, 0.93f, 0.95f);
            topHudTabStyle.hover.textColor = Color.white;
            topHudTabSelectedStyle = CreateButtonStyle(clearTexture, clearTexture, clearTexture);
            topHudTabSelectedStyle.alignment = TextAnchor.MiddleCenter;
            topHudTabSelectedStyle.fontSize = 19;
            topHudTabSelectedStyle.fontStyle = FontStyle.Bold;
            topHudTabSelectedStyle.normal.textColor = HudTheme.Accent;
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
            titleStyle.normal.textColor = new Color(0.96f, 0.84f, 0.48f);

            mutedLabelStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 12,
                wordWrap = true,
                alignment = TextAnchor.MiddleLeft
            };
            mutedLabelStyle.normal.textColor = new Color(0.62f, 0.68f, 0.72f);

            cardLabelStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 12,
                wordWrap = true,
                alignment = TextAnchor.MiddleLeft
            };
            cardLabelStyle.normal.textColor = new Color(0.94f, 0.93f, 0.90f);

            cardStyle = CreateButtonStyle(cardTexture, hoverTexture, activeTexture);
            cardStyle.border = new RectOffset(9, 9, 9, 9);
            selectedCardStyle = CreateButtonStyle(selectedCardTexture, hoverTexture, activeTexture);
            selectedCardStyle.border = new RectOffset(9, 9, 9, 9);
            buildCardStyle = CreateButtonStyle(buildCardTexture, buildHoverTexture, buildActiveTexture);
            buildCardStyle.border = new RectOffset(12, 12, 12, 12);
            selectedBuildCardStyle = CreateButtonStyle(selectedBuildCardTexture, buildHoverTexture, buildActiveTexture);
            selectedBuildCardStyle.border = new RectOffset(12, 12, 12, 12);
            buildCategoryButtonStyle = CreateButtonStyle(buildCategoryTexture,
                buildCategoryHoverTexture, buildCategoryActiveTexture);
            buildCategoryButtonStyle.border = new RectOffset(12, 12, 12, 12);
            selectedBuildCategoryButtonStyle = CreateButtonStyle(selectedBuildCategoryTexture,
                buildCategoryHoverTexture, buildCategoryActiveTexture);
            selectedBuildCategoryButtonStyle.border = new RectOffset(12, 12, 12, 12);
            buildCategoryHeadingStyle = new GUIStyle(titleStyle)
            {
                fontSize = 14,
                alignment = TextAnchor.MiddleLeft
            };
            buildCategoryHeadingStyle.normal.textColor = new Color(0.87f, 0.92f, 0.84f);
            buildCategoryLabelStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 11,
                alignment = TextAnchor.MiddleLeft,
                wordWrap = false,
                clipping = TextClipping.Clip
            };
            buildCategoryLabelStyle.normal.textColor = new Color(0.79f, 0.86f, 0.81f);
            selectedBuildCategoryLabelStyle = new GUIStyle(buildCategoryLabelStyle)
            {
                fontStyle = FontStyle.Bold
            };
            selectedBuildCategoryLabelStyle.normal.textColor = new Color(0.96f, 0.91f, 0.72f);
            buildCategoryCountStyle = new GUIStyle(buildCategoryLabelStyle)
            {
                fontSize = 10,
                alignment = TextAnchor.MiddleCenter
            };
            transparentButtonStyle = CreateButtonStyle(clearTexture, clearTexture, clearTexture);
            EnsureSidebarCategoryStyles();
            ApplyNavigationTheme();
        }

        private void ApplyNavigationTheme()
        {
            HudTheme.StylePanel(panelStyle);
            HudTheme.StylePanel(buildPanelStyle);
            HudTheme.StylePanel(topHudPopupStyle);
            foreach (GUIStyle style in new[] { cardStyle, buildCardStyle, buildCategoryButtonStyle, weatherOptionStyle, closeButtonStyle })
                HudTheme.StyleButton(style);
            foreach (GUIStyle style in new[] { selectedCardStyle, selectedBuildCardStyle, selectedBuildCategoryButtonStyle, weatherOptionSelectedStyle })
                HudTheme.StyleButton(style, true);
            foreach (GUIStyle style in new[] { mutedLabelStyle, buildCategoryCountStyle, topHudSmallLabelStyle, weatherTimeMarksStyle })
                if (style != null) style.normal.textColor = HudTheme.Muted;
            if (titleStyle != null) titleStyle.normal.textColor = HudTheme.Text;
            selectedBuildCategoryLabelStyle.normal.textColor = HudTheme.Accent;
            weatherOptionSelectedLabelStyle.normal.textColor = HudTheme.Text;
            HudTheme.StyleButton(sidebarCategoryButtonStyle);
            HudTheme.StyleButton(sidebarCategorySelectedButtonStyle, true);
            sidebarCategoryLabelStyle.normal.textColor = HudTheme.Text;
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

        private void EnsureGlassPlateStyle()
        {
            if (glassPlateStyle != null)
            {
                return;
            }

            glassPlateTexture = MakeBeveledGlassTexture(64,
                new Color(0.015f, 0.030f, 0.045f, 0.22f),
                new Color(0.85f, 0.70f, 0.38f, 0.65f),
                1.4f, 7f);
            glassPlateStyle = new GUIStyle(GUI.skin.box)
            {
                normal = { background = glassPlateTexture },
                border = new RectOffset(10, 10, 10, 10),
                padding = new RectOffset(0, 0, 0, 0)
            };
        }

        private Texture2D MakeBeveledGlassTexture(int size, Color face, Color border, float borderWidth, float cornerRadius)
        {
            Texture2D texture = new Texture2D(size, size, TextureFormat.RGBA32, false)
            {
                name = "Last Landfall glass plate texture",
                hideFlags = HideFlags.HideAndDontSave,
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Clamp
            };
            Color[] pixels = new Color[size * size];
            float half = size * 0.5f;

            for (int y = 0; y < size; y++)
            {
                float ny = y / (float)(size - 1);
                for (int x = 0; x < size; x++)
                {
                    float qx = Mathf.Abs(x + 0.5f - half) - (half - cornerRadius);
                    float qy = Mathf.Abs(y + 0.5f - half) - (half - cornerRadius);
                    float outside = Mathf.Sqrt(Mathf.Max(qx, 0f) * Mathf.Max(qx, 0f) + Mathf.Max(qy, 0f) * Mathf.Max(qy, 0f));
                    float dist = outside + Mathf.Min(Mathf.Max(qx, qy), 0f) - cornerRadius;

                    float alpha = Mathf.Clamp01(0.5f - dist);
                    float edge = Mathf.Clamp01((dist + borderWidth) / borderWidth);

                    // Specular rim gradient at top for glass reflection
                    float glassSheen = Mathf.Lerp(0.85f, 1.25f, ny);
                    Color faceCol = new Color(face.r * glassSheen, face.g * glassSheen, face.b * glassSheen, face.a);

                    float topHighlight = ny > 0.82f ? 1.35f : 1.0f;
                    Color borderCol = new Color(border.r * topHighlight, border.g * topHighlight, border.b * topHighlight, border.a);

                    Color c = Color.Lerp(faceCol, borderCol, edge);
                    c.a *= alpha;
                    pixels[y * size + x] = c;
                }
            }

            texture.SetPixels(pixels);
            texture.Apply(false, false);
            ownedUiTextures.Add(texture);
            return texture;
        }

        private void EnsureSidebarCategoryUi()
        {
            if (sidebarCategoryIcons == null || sidebarCategoryIcons.Length != SidebarCategoryCount)
            {
                sidebarCategoryIcons = new Texture2D[SidebarCategoryCount];
            }

            // Category order: Technology (0), Culture (1), Buildings (2), Tasks (3), Warehouse (4)
            string[] iconResourcePaths = {
                "UI/Sidebar/Technology",
                "UI/Sidebar/Culture",
                "UI/Sidebar/Buildings",
                "UI/Sidebar/Tasks",
                "UI/Sidebar/Warehouse"
            };

            for (int i = 0; i < SidebarCategoryCount; i++)
            {
                if (sidebarCategoryIcons[i] == null)
                {
                    // 1. Try loading custom generated icon from Resources/UI/Sidebar/
                    sidebarCategoryIcons[i] = Resources.Load<Texture2D>(iconResourcePaths[i]);

                    // 2. If not generated yet, fall back to procedural clean icon
                    if (sidebarCategoryIcons[i] == null)
                    {
                        sidebarCategoryIcons[i] = CreateSidebarCategoryIcon(i);
                    }
                }
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
            sidebarCategoryLabelStyle.normal.textColor = HudTheme.Accent;
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
            texture.SetPixels(new Color[64 * 64]);
            Color color = Color.white;

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
            else if (categoryIndex == (int)SidebarCategory.Tasks)
            {
                // Clipboard / task checklist icon
                DrawIconLine(texture, new Vector2(25f, 52f), new Vector2(25f, 58f), 2.5f, color);
                DrawIconLine(texture, new Vector2(25f, 58f), new Vector2(39f, 58f), 2.5f, color);
                DrawIconLine(texture, new Vector2(39f, 58f), new Vector2(39f, 52f), 2.5f, color);
                DrawIconLine(texture, new Vector2(22f, 52f), new Vector2(42f, 52f), 3f, color);

                DrawIconLine(texture, new Vector2(16f, 10f), new Vector2(48f, 10f), 3f, color);
                DrawIconLine(texture, new Vector2(48f, 10f), new Vector2(48f, 52f), 3f, color);
                DrawIconLine(texture, new Vector2(48f, 52f), new Vector2(42f, 52f), 3f, color);
                DrawIconLine(texture, new Vector2(16f, 52f), new Vector2(22f, 52f), 3f, color);
                DrawIconLine(texture, new Vector2(16f, 52f), new Vector2(16f, 10f), 3f, color);

                DrawIconLine(texture, new Vector2(21f, 41f), new Vector2(24f, 38f), 2f, color);
                DrawIconLine(texture, new Vector2(24f, 38f), new Vector2(29f, 44f), 2f, color);
                DrawIconLine(texture, new Vector2(33f, 40f), new Vector2(43f, 40f), 2.5f, color);

                DrawIconLine(texture, new Vector2(21f, 29f), new Vector2(24f, 26f), 2f, color);
                DrawIconLine(texture, new Vector2(24f, 26f), new Vector2(29f, 32f), 2f, color);
                DrawIconLine(texture, new Vector2(33f, 28f), new Vector2(43f, 28f), 2.5f, color);

                DrawIconLine(texture, new Vector2(21f, 18f), new Vector2(28f, 18f), 2f, color);
                DrawIconLine(texture, new Vector2(33f, 18f), new Vector2(43f, 18f), 2.5f, color);
            }
            else if (categoryIndex == (int)SidebarCategory.Warehouse)
            {
                // Warehouse / Storage Crate icon
                DrawIconLine(texture, new Vector2(14f, 14f), new Vector2(50f, 14f), 3.5f, color);
                DrawIconLine(texture, new Vector2(50f, 14f), new Vector2(50f, 48f), 3.5f, color);
                DrawIconLine(texture, new Vector2(50f, 48f), new Vector2(14f, 48f), 3.5f, color);
                DrawIconLine(texture, new Vector2(14f, 48f), new Vector2(14f, 14f), 3.5f, color);

                DrawIconLine(texture, new Vector2(14f, 38f), new Vector2(50f, 38f), 2.5f, color);
                DrawIconLine(texture, new Vector2(17f, 17f), new Vector2(47f, 35f), 2f, color);
                DrawIconLine(texture, new Vector2(47f, 17f), new Vector2(17f, 35f), 2f, color);
                DrawIconCircle(texture, new Vector2(32f, 38f), 3.5f, 2f, color);
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
            // Solid backdrop removed to preserve transparent floating glass nautical HUD over 3D scene
            DrawTopPlates(rect);
            EnsureHeaderAssetsLoaded();
            DrawSurvivalDay(rect);
            DrawWeatherControl(rect);
            DrawPinnedResourceSlots(rect);
            DrawClockAndSpeed(rect);
            DrawHeaderButtons(rect);
            // DrawResourceStrip is retired in favor of Anno 1800 4 pinned slots and full Warehouse panel
            if (isWeatherMenuOpen)
            {
                DrawWeatherMenu(rect);
            }

            if (isResourceMenuOpen)
            {
                DrawResourceMenu(rect);
            }
        }

        private static int GetWatchPhaseIndex(float hour)
        {
            if (hour >= 5.0f && hour < 8.5f) return 0; // Dawn (破晓)
            if (hour >= 8.5f && hour < 15.5f) return 1; // Noon (顺风/正阳)
            if (hour >= 15.5f && hour < 19.0f) return 2; // Dusk (暮色)
            return 3; // Night (星海)
        }

        private static string GetWatchPhaseName(int phaseIndex)
        {
            return phaseIndex switch
            {
                0 => "⚓ 破晓微光",
                1 => "⚓ 顺风扬帆",
                2 => "⚓ 暮色沉霞",
                _ => "⚓ 星海守望"
            };
        }

        private static Color GetWatchPhaseColor(int phaseIndex)
        {
            return phaseIndex switch
            {
                0 => new Color(1f, 0.72f, 0.35f), // Sunrise apricot gold
                1 => new Color(1f, 0.92f, 0.45f), // Solar zenith gold
                2 => new Color(1f, 0.50f, 0.32f), // Dusk crimson amber
                _ => new Color(0.68f, 0.85f, 1.0f)  // Night starry cyan
            };
        }

        private static string GetCelestialEmblem(int phaseIndex)
        {
            return phaseIndex switch
            {
                0 => "🌅",
                1 => "☀️",
                2 => "🌇",
                _ => "🌙"
            };
        }

        private static string GetWeatherSeaState(IslandWeatherType weather)
        {
            return weather switch
            {
                IslandWeatherType.Clear => "海况平稳",
                IslandWeatherType.Overcast => "浮云蔽日",
                IslandWeatherType.Rain => "细雨汇流",
                IslandWeatherType.Wind => "大风起浪",
                IslandWeatherType.Thunderstorm => "狂澜惊雷",
                IslandWeatherType.Fog => "浓雾迷航",
                IslandWeatherType.StormSurge => "怒涛狂澜",
                IslandWeatherType.DebrisShower => "浮木碎屑",
                IslandWeatherType.FreezingRain => "极寒封冻",
                IslandWeatherType.Blizzard => "狂雪封海",
                IslandWeatherType.Aurora => "星海流光",
                _ => "海况平稳"
            };
        }

        /// <summary>Three floating transparent glass nautical instrument modules (Day plaque, chronometer & speed regulator, weather dial).</summary>
        private void DrawTopPlates(Rect rect)
        {
            EnsureGlassPlateStyle();
            if (glassPlateStyle == null) return;

            float scale = GetHudScale();
            float y = rect.y + 6f * scale;
            float height = rect.height - 12f * scale;

            // Victorian Marine Chronometer Suite: 4 discrete transparent glass plates
            // Module 1: Day Plaque
            GUI.Box(new Rect(12f * scale, y, 114f * scale, height), GUIContent.none, glassPlateStyle);

            // Module 2: Astronomical Marine Chronometer & Integrated Speed Regulator
            GUI.Box(new Rect(132f * scale, y, 206f * scale, height), GUIContent.none, glassPlateStyle);

            // Module 3: Lighthouse Reconstruction Plaque (right of *3)
            GUI.Box(new Rect(344f * scale, y, 128f * scale, height), GUIContent.none, glassPlateStyle);

            // Module 4: Barometric Weather Dial (compact 118px width, right of lighthouse)
            GUI.Box(new Rect(478f * scale, y, 118f * scale, height), GUIContent.none, glassPlateStyle);

            // Module 4: Anno 1800 Pinned 4 Resource Slots (right of weather dial)
            for (int s = 0; s < 4; s++)
            {
                float slotX = 468f * scale + s * (98f + 5f) * scale;
                GUI.Box(new Rect(slotX, y, 98f * scale, height), GUIContent.none, glassPlateStyle);
            }
        }

        private GUIStyle dayLabelStyle;
        private GUIStyle daySubtitleStyle;

        private void DrawSurvivalDay(Rect topBarRect)
        {
            float scale = GetHudScale();
            float y = topBarRect.y + 6f * scale;
            float height = topBarRect.height - 12f * scale;
            Rect plaqueRect = new Rect(12f * scale, y, 114f * scale, height);
            int day = weatherSystem != null ? weatherSystem.SurvivalDay : 1;

            // Day rollover switch detection
            if (lastTrackedSurvivalDay == -1)
            {
                lastTrackedSurvivalDay = day;
            }
            else if (day != lastTrackedSurvivalDay)
            {
                lastTrackedSurvivalDay = day;
                dayTransitionTimer = DayTransitionDuration;
            }
            if (dayTransitionTimer > 0f)
            {
                dayTransitionTimer -= Time.deltaTime;
            }

            if (dayLabelStyle == null)
            {
                dayLabelStyle = new GUIStyle(GUI.skin.label)
                {
                    alignment = TextAnchor.MiddleCenter,
                    fontSize = 17,
                    fontStyle = FontStyle.Bold
                };
                dayLabelStyle.normal.textColor = HudTheme.Accent;
            }
            dayLabelStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(17f * scale), 14, 22);

            if (daySubtitleStyle == null)
            {
                daySubtitleStyle = new GUIStyle(GUI.skin.label)
                {
                    alignment = TextAnchor.MiddleCenter,
                    fontSize = 12,
                    fontStyle = FontStyle.Normal
                };
            }
            daySubtitleStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 14);

            // --- Day Number (with transition flip when day rolls over) ---
            Rect dayNumRect = new Rect(plaqueRect.x, plaqueRect.y + 6f * scale, plaqueRect.width, 26f * scale);
            if (dayTransitionTimer > 0f)
            {
                float dt = 1f - Mathf.Clamp01(dayTransitionTimer / DayTransitionDuration);
                if (dt < 0.5f)
                {
                    float exitP = dt * 2f;
                    dayLabelStyle.normal.textColor = new Color(HudTheme.Accent.r, HudTheme.Accent.g, HudTheme.Accent.b, 1f - exitP);
                    GUI.Label(new Rect(dayNumRect.x, dayNumRect.y - exitP * 14f * scale, dayNumRect.width, dayNumRect.height),
                        "第 " + (day - 1) + " 天", dayLabelStyle);
                }
                else
                {
                    float enterP = (dt - 0.5f) * 2f;
                    float ease = Mathf.Sin(enterP * Mathf.PI * 0.5f);
                    dayLabelStyle.normal.textColor = new Color(HudTheme.Accent.r, HudTheme.Accent.g, HudTheme.Accent.b, enterP);
                    GUI.Label(new Rect(dayNumRect.x, dayNumRect.y + (1f - ease) * 14f * scale, dayNumRect.width, dayNumRect.height),
                        "第 " + day + " 天", dayLabelStyle);
                }

                // Golden celebration flash across day plaque
                float flashAlpha = Mathf.Sin(dt * Mathf.PI) * 0.45f;
                DrawHudDivider(new Rect(plaqueRect.x + 4f * scale, plaqueRect.y + 2f * scale,
                    plaqueRect.width - 8f * scale, plaqueRect.height - 4f * scale),
                    new Color(1f, 0.88f, 0.45f, flashAlpha));
            }
            else
            {
                dayLabelStyle.normal.textColor = HudTheme.Accent;
                GUI.Label(dayNumRect, "第 " + day + " 天", dayLabelStyle);
            }

            // Subtle nautical brass divider line
            DrawHudDivider(new Rect(plaqueRect.x + 16f * scale, plaqueRect.y + 34f * scale,
                plaqueRect.width - 32f * scale, 1f),
                new Color(0.85f, 0.70f, 0.38f, 0.30f));

            // --- Maritime Watch Phase Subtitle (Switching transition on morning/noon/evening change) ---
            float hour = weatherSystem != null ? weatherSystem.TimeOfDayHours : 8f;
            int currentPhase = GetWatchPhaseIndex(hour);

            Rect subRect = new Rect(plaqueRect.x, plaqueRect.y + 38f * scale, plaqueRect.width, 20f * scale);

            if (watchPhaseTransitionTimer > 0f)
            {
                float pt = 1f - Mathf.Clamp01(watchPhaseTransitionTimer / WatchPhaseTransitionDuration);
                if (pt < 0.5f)
                {
                    float exitP = pt * 2f;
                    Color col = GetWatchPhaseColor(previousWatchPhase);
                    col.a = 1f - exitP;
                    daySubtitleStyle.normal.textColor = col;
                    GUI.Label(new Rect(subRect.x, subRect.y - exitP * 12f * scale, subRect.width, subRect.height),
                        GetWatchPhaseName(previousWatchPhase), daySubtitleStyle);
                }
                else
                {
                    float enterP = (pt - 0.5f) * 2f;
                    float ease = Mathf.Sin(enterP * Mathf.PI * 0.5f);
                    Color col = GetWatchPhaseColor(currentPhase);
                    col.a = enterP;
                    daySubtitleStyle.normal.textColor = col;
                    GUI.Label(new Rect(subRect.x, subRect.y + (1f - ease) * 12f * scale, subRect.width, subRect.height),
                        GetWatchPhaseName(currentPhase), daySubtitleStyle);
                }
            }
            else
            {
                // Completely static, solid color, no idle breathing
                daySubtitleStyle.normal.textColor = GetWatchPhaseColor(currentPhase);
                GUI.Label(subRect, GetWatchPhaseName(currentPhase), daySubtitleStyle);
            }
        }

        private GUIStyle weatherStatusSubStyle;

        private void DrawWeatherControl(Rect topBarRect)
        {
            if (weatherSystem == null)
            {
                return;
            }

            float scale = GetHudScale();
            Rect buttonRect = GetWeatherButtonRect(topBarRect);
            bool isHovered = buttonRect.Contains(Event.current.mousePosition);

            // Weather change detection & trigger transition animation
            if (weatherSystem.CurrentWeather != lastTrackedWeather)
            {
                previousWeather = lastTrackedWeather;
                lastTrackedWeather = weatherSystem.CurrentWeather;
                weatherTransitionTimer = WeatherTransitionDuration;
            }
            if (weatherTransitionTimer > 0f)
            {
                weatherTransitionTimer -= Time.deltaTime;
            }

            if (isHovered || isWeatherMenuOpen)
            {
                HudTheme.Segment(buttonRect, isWeatherMenuOpen, isHovered);
            }

            bool clicked = GUI.Button(buttonRect,
                new GUIContent(string.Empty, "当前天气：" + weatherSystem.CurrentWeatherName + "。点击展开天气罗盘。"),
                transparentButtonStyle != null ? transparentButtonStyle : GUIStyle.none);

            EnsureWeatherIcons();

            // Styles & Text measurement for perfect horizontal and vertical centering
            GUIStyle weatherTitleStyle = new GUIStyle(GUI.skin.label)
            {
                alignment = TextAnchor.MiddleLeft,
                fontStyle = FontStyle.Bold
            };
            weatherTitleStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(18f * scale), 14, 23);
            weatherTitleStyle.normal.textColor = isWeatherMenuOpen ? new Color(0.12f, 0.10f, 0.05f) : Color.white;

            GUIStyle arrowStyle = new GUIStyle(GUI.skin.label)
            {
                alignment = TextAnchor.MiddleCenter,
                fontSize = Mathf.Clamp(Mathf.RoundToInt(11f * scale), 9, 13)
            };
            arrowStyle.normal.textColor = isWeatherMenuOpen ? new Color(0.20f, 0.16f, 0.08f) : new Color(0.85f, 0.70f, 0.38f, 0.75f);

            if (weatherStatusSubStyle == null)
            {
                weatherStatusSubStyle = new GUIStyle(GUI.skin.label)
                {
                    alignment = TextAnchor.MiddleLeft,
                    fontStyle = FontStyle.Normal
                };
            }
            weatherStatusSubStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 16);
            weatherStatusSubStyle.normal.textColor = isWeatherMenuOpen
                ? new Color(0.20f, 0.16f, 0.08f)
                : new Color(0.58f, 0.80f, 0.88f, 0.95f);

            string weatherName = GetShortWeatherName(weatherSystem.CurrentWeather);
            string seaState = GetWeatherSeaState(weatherSystem.CurrentWeather);

            // Compute exact centered layout
            float iconSize = 34f * scale;
            float iconGap = 7f * scale;
            float titleWidth = weatherTitleStyle.CalcSize(new GUIContent(weatherName)).x;
            float subWidth = weatherStatusSubStyle.CalcSize(new GUIContent(seaState)).x;
            float caretWidth = 10f * scale;
            float caretGap = 3f * scale;
            float textBlockWidth = Mathf.Max(titleWidth + caretGap + caretWidth, subWidth);

            float totalGroupWidth = iconSize + iconGap + textBlockWidth;
            float groupStartX = buttonRect.center.x - totalGroupWidth * 0.5f;

            float titleHeight = 22f * scale;
            float subtitleHeight = 18f * scale;
            float textGap = 2f * scale;
            float totalTextHeight = titleHeight + textGap + subtitleHeight;

            float contentCenterY = buttonRect.center.y;
            float iconY = contentCenterY - iconSize * 0.5f;
            float titleY = contentCenterY - totalTextHeight * 0.5f;
            float subtitleY = titleY + titleHeight + textGap;
            float textX = groupStartX + iconSize + iconGap;

            Rect iconRect = new Rect(groupStartX, iconY, iconSize, iconSize);
            Rect nameRect = new Rect(textX, titleY, titleWidth + 2f * scale, titleHeight);
            Rect arrowRect = new Rect(textX + titleWidth + caretGap, titleY + 1f * scale, caretWidth, 20f * scale);
            Rect subRect = new Rect(textX, subtitleY, subWidth + 4f * scale, subtitleHeight);

            int currentIconIndex = Mathf.Clamp((int)weatherSystem.CurrentWeather, 0, weatherIcons.Length - 1);
            int prevIconIndex = Mathf.Clamp((int)previousWeather, 0, weatherIcons.Length - 1);

            // --- Weather Transition Animation vs Steady Display ---
            if (weatherTransitionTimer > 0f)
            {
                float wt = 1f - Mathf.Clamp01(weatherTransitionTimer / WeatherTransitionDuration);

                // Stately sweeping brass/cyan luminous wave across the weather dial
                float sweepW = 34f * scale;
                float sweepX = Mathf.Lerp(buttonRect.x - sweepW, buttonRect.xMax, wt);
                Rect sweepRect = new Rect(sweepX, buttonRect.y + 2f * scale, sweepW, buttonRect.height - 4f * scale);
                float sweepAlpha = Mathf.Sin(wt * Mathf.PI) * 0.45f;
                DrawHudDivider(sweepRect, new Color(1f, 0.88f, 0.45f, sweepAlpha));

                // Border pulse highlight during transition
                Color rimFlash = new Color(0.96f, 0.82f, 0.44f, sweepAlpha * 0.7f);
                DrawHudDivider(new Rect(buttonRect.x, buttonRect.y, buttonRect.width, 1.5f), rimFlash);
                DrawHudDivider(new Rect(buttonRect.x, buttonRect.yMax - 1.5f, buttonRect.width, 1.5f), rimFlash);

                Color prevGuiColor = GUI.color;

                if (wt < 0.5f)
                {
                    // Phase 1: Outgoing weather slides up and fades out
                    float exitP = wt * 2f;
                    float offsetY = -exitP * 18f * scale;
                    float alpha = 1f - exitP;

                    GUI.color = new Color(1f, 1f, 1f, alpha);
                    if (weatherIcons != null && prevIconIndex < weatherIcons.Length && weatherIcons[prevIconIndex] != null)
                    {
                        GUI.DrawTexture(new Rect(iconRect.x, iconRect.y + offsetY, iconRect.width, iconRect.height),
                            weatherIcons[prevIconIndex], ScaleMode.ScaleToFit, true);
                    }

                    weatherTitleStyle.normal.textColor = new Color(weatherTitleStyle.normal.textColor.r,
                        weatherTitleStyle.normal.textColor.g, weatherTitleStyle.normal.textColor.b, alpha);
                    GUI.Label(new Rect(nameRect.x, nameRect.y + offsetY, nameRect.width, nameRect.height),
                        GetShortWeatherName(previousWeather), weatherTitleStyle);

                    arrowStyle.normal.textColor = new Color(arrowStyle.normal.textColor.r,
                        arrowStyle.normal.textColor.g, arrowStyle.normal.textColor.b, alpha);
                    GUI.Label(new Rect(arrowRect.x, arrowRect.y + offsetY, arrowRect.width, arrowRect.height),
                        "▾", arrowStyle);

                    weatherStatusSubStyle.normal.textColor = new Color(weatherStatusSubStyle.normal.textColor.r,
                        weatherStatusSubStyle.normal.textColor.g, weatherStatusSubStyle.normal.textColor.b, alpha);
                    GUI.Label(new Rect(subRect.x, subRect.y + offsetY, subRect.width, subRect.height),
                        GetWeatherSeaState(previousWeather), weatherStatusSubStyle);
                }
                else
                {
                    // Phase 2: Incoming weather enters from below with elastic settle
                    float enterP = (wt - 0.5f) * 2f;
                    float ease = Mathf.Sin(enterP * Mathf.PI * 0.5f);
                    float offsetY = (1f - ease) * 18f * scale;
                    float alpha = enterP;

                    GUI.color = new Color(1f, 1f, 1f, alpha);
                    if (weatherIcons != null && currentIconIndex < weatherIcons.Length && weatherIcons[currentIconIndex] != null)
                    {
                        GUI.DrawTexture(new Rect(iconRect.x, iconRect.y + offsetY, iconRect.width, iconRect.height),
                            weatherIcons[currentIconIndex], ScaleMode.ScaleToFit, true);
                    }

                    weatherTitleStyle.normal.textColor = new Color(weatherTitleStyle.normal.textColor.r,
                        weatherTitleStyle.normal.textColor.g, weatherTitleStyle.normal.textColor.b, alpha);
                    GUI.Label(new Rect(nameRect.x, nameRect.y + offsetY, nameRect.width, nameRect.height),
                        weatherName, weatherTitleStyle);

                    arrowStyle.normal.textColor = new Color(arrowStyle.normal.textColor.r,
                        arrowStyle.normal.textColor.g, arrowStyle.normal.textColor.b, alpha);
                    GUI.Label(new Rect(arrowRect.x, arrowRect.y + offsetY, arrowRect.width, arrowRect.height),
                        "▾", arrowStyle);

                    weatherStatusSubStyle.normal.textColor = new Color(weatherStatusSubStyle.normal.textColor.r,
                        weatherStatusSubStyle.normal.textColor.g, weatherStatusSubStyle.normal.textColor.b, alpha);
                    GUI.Label(new Rect(subRect.x, subRect.y + offsetY, subRect.width, subRect.height),
                        seaState, weatherStatusSubStyle);
                }

                GUI.color = prevGuiColor;
            }
            else
            {
                // Steady display: Completely static, crisp, perfectly centered in box
                if (weatherIcons != null && currentIconIndex < weatherIcons.Length && weatherIcons[currentIconIndex] != null)
                {
                    GUI.DrawTexture(iconRect, weatherIcons[currentIconIndex], ScaleMode.ScaleToFit, true);
                }
                GUI.Label(nameRect, weatherName, weatherTitleStyle);
                GUI.Label(arrowRect, "▾", arrowStyle);
                GUI.Label(subRect, seaState, weatherStatusSubStyle);
            }

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
            return new Rect(478f * scale, topBarRect.y + 6f * scale,
                118f * scale, topBarRect.height - 12f * scale);
        }

        private void TogglePauseSimulation()
        {
            if (weatherSystem == null) return;
            if (selectedSimulationSpeedIndex == 0)
            {
                int resumeSpeed = Mathf.Clamp(lastActiveSpeedIndex, 1, 3);
                selectedSimulationSpeedIndex = resumeSpeed;
                weatherSystem.SetSimulationSpeed(resumeSpeed);
                statusMessage = "时间已恢复运行：" + resumeSpeed + "×。";
            }
            else
            {
                lastActiveSpeedIndex = Mathf.Clamp(selectedSimulationSpeedIndex, 1, 3);
                selectedSimulationSpeedIndex = 0;
                weatherSystem.SetSimulationSpeed(0f);
                statusMessage = "游戏已暂停 (按空格或点击速度继续)。";
            }
        }

        private void DrawClockAndSpeed(Rect topBarRect)
        {
            if (weatherSystem == null || topHudClockStyle == null)
            {
                return;
            }

            float scale = GetHudScale();
            float y = topBarRect.y + 6f * scale;
            float height = topBarRect.height - 12f * scale;
            Rect clockModuleRect = new Rect(132f * scale, y, 206f * scale, height);

            float hour = weatherSystem.TimeOfDayHours;
            int currentPhase = GetWatchPhaseIndex(hour);

            // Watch phase transition detection (早中晚切换)
            if (lastTrackedWatchPhase == -1)
            {
                lastTrackedWatchPhase = currentPhase;
                previousWatchPhase = currentPhase;
            }
            else if (currentPhase != lastTrackedWatchPhase)
            {
                previousWatchPhase = lastTrackedWatchPhase;
                lastTrackedWatchPhase = currentPhase;
                watchPhaseTransitionTimer = WatchPhaseTransitionDuration;
            }
            if (watchPhaseTransitionTimer > 0f)
            {
                watchPhaseTransitionTimer -= Time.deltaTime;
            }

            // Lower regulator section dimensions
            float buttonWidth = 44f * scale;
            float buttonHeight = 21f * scale;
            float buttonGap = 4f * scale;
            int segmentCount = 4; // 0 = Pause (||), 1 = 1x, 2 = 2x, 3 = 3x
            float totalButtonsWidth = buttonWidth * segmentCount + buttonGap * (segmentCount - 1);
            float buttonsX = clockModuleRect.center.x - totalButtonsWidth * 0.5f;
            float buttonY = clockModuleRect.yMax - buttonHeight - 7f * scale;

            // Upper blank area (above speed buttons track)
            float upperAreaHeight = (buttonY - 2f * scale) - clockModuleRect.y;
            float upperCenterY = clockModuleRect.y + upperAreaHeight * 0.5f;

            // Digital Time text
            int totalMinutes = Mathf.FloorToInt(weatherSystem.TimeOfDayHours * 60f) % (24 * 60);
            string timeText = string.Format(CultureInfo.InvariantCulture, "{0:00}:{1:00}",
                totalMinutes / 60, totalMinutes % 60);

            topHudClockStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(24f * scale), 19, 28);
            topHudClockStyle.fontStyle = FontStyle.Bold;
            topHudClockStyle.alignment = TextAnchor.MiddleCenter;

            float timeWidth = topHudClockStyle.CalcSize(new GUIContent(timeText)).x;
            float timeHeight = 26f * scale;
            float iconSize = 24f * scale;
            float clusterGap = 7f * scale;
            float totalClusterWidth = iconSize + clusterGap + timeWidth;
            float clusterStartX = clockModuleRect.center.x - totalClusterWidth * 0.5f;

            // Perfectly centered in the upper blank area both horizontally and vertically
            Rect celestialRect = new Rect(clusterStartX, upperCenterY - iconSize * 0.5f, iconSize, iconSize);
            Rect clockTextRect = new Rect(clusterStartX + iconSize + clusterGap, upperCenterY - timeHeight * 0.5f - 1f * scale,
                timeWidth + 2f * scale, timeHeight);

            GUIStyle celestialStyle = new GUIStyle(GUI.skin.label)
            {
                alignment = TextAnchor.MiddleCenter,
                fontSize = Mathf.Clamp(Mathf.RoundToInt(17f * scale), 14, 21)
            };

            GUI.Label(clockTextRect, timeText, topHudClockStyle);

            // Celestial Emblem: Transition Flip Action on phase change vs Steady placement
            if (watchPhaseTransitionTimer > 0f)
            {
                float pt = 1f - Mathf.Clamp01(watchPhaseTransitionTimer / WatchPhaseTransitionDuration);

                // Subtle phase switch shimmer across chronometer plate
                float sweepW = 34f * scale;
                float sweepX = Mathf.Lerp(clockModuleRect.x - sweepW, clockModuleRect.xMax, pt);
                Rect sweepRect = new Rect(sweepX, clockModuleRect.y + 2f * scale, sweepW, clockModuleRect.height - 4f * scale);
                float sweepAlpha = Mathf.Sin(pt * Mathf.PI) * 0.35f;
                DrawHudDivider(sweepRect, new Color(1f, 0.88f, 0.45f, sweepAlpha));

                Matrix4x4 oldMat = GUI.matrix;

                if (pt < 0.5f)
                {
                    // Phase 1: Old celestial icon rotates and slides up
                    float exitP = pt * 2f;
                    float offsetY = -exitP * 18f * scale;
                    Color col = GetWatchPhaseColor(previousWatchPhase);
                    col.a = 1f - exitP;
                    celestialStyle.normal.textColor = col;

                    GUIUtility.RotateAroundPivot(exitP * 45f, celestialRect.center);
                    GUI.Label(new Rect(celestialRect.x, celestialRect.y + offsetY, celestialRect.width, celestialRect.height),
                        GetCelestialEmblem(previousWatchPhase), celestialStyle);
                }
                else
                {
                    // Phase 2: New celestial icon rises from below with rotation snap
                    float enterP = (pt - 0.5f) * 2f;
                    float ease = Mathf.Sin(enterP * Mathf.PI * 0.5f);
                    float offsetY = (1f - ease) * 18f * scale;
                    Color col = GetWatchPhaseColor(currentPhase);
                    col.a = enterP;
                    celestialStyle.normal.textColor = col;

                    GUIUtility.RotateAroundPivot((1f - ease) * -45f, celestialRect.center);
                    GUI.Label(new Rect(celestialRect.x, celestialRect.y + offsetY, celestialRect.width, celestialRect.height),
                        GetCelestialEmblem(currentPhase), celestialStyle);
                }

                GUI.matrix = oldMat;
            }
            else
            {
                // Steady display: completely static, solid color, no idle movement
                celestialStyle.normal.textColor = GetWatchPhaseColor(currentPhase);
                GUI.Label(celestialRect, GetCelestialEmblem(currentPhase), celestialStyle);
            }

            // Horizontal divider line below time is removed

            // Lower regulator section: Fully transparent speed buttons [ || ] [ 1× ] [ 2× ] [ 3× ]
            if (transparentSpeedStyle == null)
            {
                transparentSpeedStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = 12,
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter
                };
                transparentSpeedStyle.normal.textColor = new Color(0.82f, 0.86f, 0.88f);
                transparentSpeedStyle.hover.textColor = Color.white;

                transparentSpeedSelectedStyle = new GUIStyle(transparentSpeedStyle);
                transparentSpeedSelectedStyle.normal.textColor = new Color(1f, 0.94f, 0.70f);
                transparentSpeedSelectedStyle.hover.textColor = new Color(1f, 0.94f, 0.70f);
            }
            transparentSpeedStyle.fontSize = transparentSpeedSelectedStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 15);

            // Transparent recessed track: fine brass wireframe outline, NO opaque solid fill
            Rect trackRect = new Rect(buttonsX - 2f * scale, buttonY - 2f * scale,
                totalButtonsWidth + 4f * scale, buttonHeight + 4f * scale);
            DrawHudDivider(trackRect, new Color(0.01f, 0.02f, 0.03f, 0.18f)); // 18% smokey glass recess
            Color trackBorderColor = new Color(0.85f, 0.70f, 0.38f, 0.35f);
            DrawHudDivider(new Rect(trackRect.x, trackRect.y, trackRect.width, 1f), trackBorderColor);
            DrawHudDivider(new Rect(trackRect.x, trackRect.yMax - 1f, trackRect.width, 1f), trackBorderColor);
            DrawHudDivider(new Rect(trackRect.x, trackRect.y, 1f, trackRect.height), trackBorderColor);
            DrawHudDivider(new Rect(trackRect.xMax - 1f, trackRect.y, 1f, trackRect.height), trackBorderColor);

            for (int i = 0; i < segmentCount; i++)
            {
                Rect speedRect = new Rect(buttonsX + i * (buttonWidth + buttonGap), buttonY,
                    buttonWidth, buttonHeight);
                bool selected = selectedSimulationSpeedIndex == i;
                bool hovered = speedRect.Contains(Event.current.mousePosition);

                // Transparent segment styling (no opaque backing)
                if (selected)
                {
                    // Semi-transparent warm gold fill (38% alpha) with bright brass top rim
                    DrawHudDivider(speedRect, new Color(0.85f, 0.68f, 0.28f, 0.38f));
                    DrawHudDivider(new Rect(speedRect.x, speedRect.y, speedRect.width, 1.5f), new Color(1f, 0.88f, 0.45f, 0.90f));
                    DrawHudDivider(new Rect(speedRect.x, speedRect.yMax - 1f, speedRect.width, 1f), new Color(0.85f, 0.68f, 0.28f, 0.50f));
                }
                else if (hovered)
                {
                    // Subtle hover glow
                    DrawHudDivider(speedRect, new Color(1f, 1f, 1f, 0.10f));
                    DrawHudDivider(new Rect(speedRect.x, speedRect.y, speedRect.width, 1f), new Color(0.85f, 0.70f, 0.38f, 0.50f));
                }

                // Inner divider between segments (except first)
                if (i > 0)
                {
                    DrawHudDivider(new Rect(speedRect.x - buttonGap * 0.5f, speedRect.y + 2f * scale, 1f, speedRect.height - 4f * scale),
                        new Color(0.85f, 0.70f, 0.38f, 0.20f));
                }

                string label = i == 0 ? string.Empty : i + "×";
                string tooltip = i == 0 ? "暂停游戏 (空格键)" : ("设置时间速度为 " + i + "×");
                GUIStyle btnStyle = selected ? transparentSpeedSelectedStyle : transparentSpeedStyle;
                if (GUI.Button(speedRect, new GUIContent(label, tooltip), btnStyle))
                {
                    if (i == 0)
                    {
                        TogglePauseSimulation();
                    }
                    else
                    {
                        selectedSimulationSpeedIndex = i;
                        lastActiveSpeedIndex = i;
                        weatherSystem.SetSimulationSpeed(i);
                        statusMessage = "时间速度设为 " + i + "×。";
                    }
                }

                // Double bar pause emblem
                if (i == 0)
                {
                    float barW = 2.5f * scale;
                    float barH = 10f * scale;
                    float barGap = 3.5f * scale;
                    float bx = speedRect.center.x - barW - barGap * 0.5f;
                    float by = speedRect.center.y - barH * 0.5f;
                    Color barCol = selected ? new Color(1f, 0.94f, 0.70f) : (hovered ? Color.white : new Color(0.82f, 0.86f, 0.88f));
                    DrawHudDivider(new Rect(bx, by, barW, barH), barCol);
                    DrawHudDivider(new Rect(bx + barW + barGap, by, barW, barH), barCol);
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
            string[] labels = { "科技", "文化" };
            for (int i = 0; i < labels.Length; i++)
            {
                Rect tabRect = GetKnowledgeTabRect(topBarRect, i);
                bool selected = isKnowledgeFullscreenOpen && knowledgeFullscreenTab == i;
                if (GUI.Button(tabRect, labels[i], selected ? topHudTabSelectedStyle : topHudTabStyle))
                {
                    if (isKnowledgeFullscreenOpen && knowledgeFullscreenTab == i)
                    {
                        isKnowledgeFullscreenOpen = false;
                    }
                    else
                    {
                        OpenKnowledgeFullscreen(i);
                    }
                }

                if (selected)
                {
                    float underlineWidth = 44f * scale;
                    DrawHudDivider(new Rect(tabRect.center.x - underlineWidth * 0.5f,
                        tabRect.yMax - 2f * scale, underlineWidth, Mathf.Max(1f, 1.5f * scale)),
                        HudTheme.Accent);
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
            float rowHeight = 44f * scale;

            // Background plate removed: clean single-layer floating HUD with solid crisp typography (no ghosting on hover)

            if (resourceNameStyle == null)
            {
                resourceNameStyle = new GUIStyle(GUI.skin.label)
                {
                    alignment = TextAnchor.MiddleLeft,
                    fontStyle = FontStyle.Normal,
                    clipping = TextClipping.Clip
                };
            }
            resourceNameStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(15f * scale), 12, 17);
            resourceNameStyle.normal.textColor = Color.white;
            resourceNameStyle.hover.textColor = Color.white;
            resourceNameStyle.active.textColor = Color.white;
            resourceNameStyle.focused.textColor = Color.white;

            if (resourceValueStyle == null)
            {
                resourceValueStyle = new GUIStyle(GUI.skin.label)
                {
                    alignment = TextAnchor.MiddleRight,
                    fontStyle = FontStyle.Bold,
                    clipping = TextClipping.Clip,
                    wordWrap = false
                };
            }
            resourceValueStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(16f * scale), 13, 18);
            Color goldColor = new Color(1.0f, 0.86f, 0.42f, 1f); // Warm golden amber highlight
            resourceValueStyle.normal.textColor = goldColor;
            resourceValueStyle.hover.textColor = goldColor;
            resourceValueStyle.active.textColor = goldColor;
            resourceValueStyle.focused.textColor = goldColor;

            int displayedCount = isResourceMenuOpen ? TotalHeaderResourceCount : VisibleHeaderResourceCount;
            for (int i = 0; i < displayedCount; i++)
            {
                Rect itemRect = GetResourceItemRect(topBarRect, i);
                if (headerResourceIcons != null && i < headerResourceIcons.Length && headerResourceIcons[i] != null)
                {
                    float resourceIconSize = 24f * scale;
                    GUI.DrawTexture(new Rect(itemRect.x + 8f * scale, itemRect.center.y - resourceIconSize * 0.5f,
                        resourceIconSize, resourceIconSize), headerResourceIcons[i], ScaleMode.ScaleToFit, true);
                }

                // Crisp single-layer white label (no offset ghosting on hover)
                GUI.Label(new Rect(itemRect.x + 36f * scale, itemRect.y, itemRect.width * 0.46f - 10f * scale,
                    itemRect.height), HeaderResourceDisplayNames[i], resourceNameStyle);

                // Crisp single-layer warm gold value (no offset ghosting on hover)
                GUI.Label(new Rect(itemRect.x + itemRect.width * 0.52f, itemRect.y,
                    itemRect.width * 0.48f - 10f * scale, itemRect.height), GetHeaderResourceAmount(i),
                    resourceValueStyle);
            }

            // Down/Up toggle button styled identically to the speed control segments
            Rect moreRect = GetResourceMoreButtonRect(topBarRect);
            bool isMoreHovered = moreRect.Contains(Event.current.mousePosition);

            if (speedSegmentStyle == null)
            {
                speedSegmentStyle = new GUIStyle(topHudTabStyle != null ? topHudTabStyle : GUI.skin.button)
                {
                    fontSize = 14,
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter
                };
                speedSegmentStyle.normal.textColor = new Color(0.78f, 0.83f, 0.85f);
                speedSegmentStyle.hover.textColor = Color.white;
                speedSegmentSelectedStyle = new GUIStyle(speedSegmentStyle);
                speedSegmentSelectedStyle.normal.textColor = new Color(0.10f, 0.08f, 0.04f);
                speedSegmentSelectedStyle.hover.textColor = new Color(0.10f, 0.08f, 0.04f);
            }

            // Recessed track + speed segment effect (golden plate with highlight when expanded, soft amber glow on hover)
            HudTheme.Track(new Rect(moreRect.x - 2f * scale, moreRect.y - 2f * scale,
                moreRect.width + 4f * scale, moreRect.height + 4f * scale));
            HudTheme.Segment(moreRect, isResourceMenuOpen, isMoreHovered);

            string toggleText = isResourceMenuOpen ? "▲ 收起" : "▼ 展开";
            GUIStyle buttonStyle = isResourceMenuOpen ? speedSegmentSelectedStyle : speedSegmentStyle;
            buttonStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(13f * scale), 11, 16);

            if (GUI.Button(moreRect, toggleText, buttonStyle))
            {
                isResourceMenuOpen = !isResourceMenuOpen;
                if (isResourceMenuOpen)
                {
                    if (lighthouseSite != null) lighthouseSite.IsPanelOpen = false;
                    isWeatherMenuOpen = false;
                    isBuildMenuOpen = false;
                }
            }
        }

        private Rect GetResourceItemRect(Rect topBarRect, int index)
        {
            float scale = GetHudScale();
            Rect stripRect = GetResourceStripRect(topBarRect);
            float rowHeight = 44f * scale;
            return new Rect(stripRect.x + 2f * scale,
                stripRect.y + 6f * scale + index * rowHeight,
                stripRect.width - 4f * scale, rowHeight);
        }

        private Rect GetResourceMoreButtonRect(Rect topBarRect)
        {
            float scale = GetHudScale();
            Rect stripRect = GetResourceStripRect(topBarRect);
            float buttonHeight = 28f * scale;
            int count = isResourceMenuOpen ? TotalHeaderResourceCount : VisibleHeaderResourceCount;
            return new Rect(stripRect.x + 8f * scale,
                stripRect.y + 8f * scale + count * 44f * scale,
                stripRect.width - 16f * scale, buttonHeight);
        }

        private Rect GetResourceStripRect(Rect topBarRect)
        {
            float scale = GetHudScale();
            float width = 160f * scale;
            int count = isResourceMenuOpen ? TotalHeaderResourceCount : VisibleHeaderResourceCount;
            float height = (count * 44f + 44f) * scale;
            float x = Screen.width - width - 14f * scale;
            float buttonsHeight = 46f * scale;
            float y = topBarRect.yMax + 6f * scale;
            return new Rect(x, y, width, height);
        }

        private Rect GetResourceMenuRect(Rect topBarRect)
        {
            return GetResourceStripRect(topBarRect);
        }

        private void DrawResourceMenu(Rect topBarRect)
        {
            // Fully integrated inline inside DrawResourceStrip!
        }

        private string GetHeaderResourceAmount(int index)
        {
            var res = ColonyResourceManager.Instance;
            if (res == null) return index == 0 ? wood.ToString("0", CultureInfo.InvariantCulture) : "0";

            float val = index switch
            {
                0 => res.Wood,
                1 => res.Food,
                2 => res.Water,
                3 => res.Metal,
                4 => res.Fuel,
                5 => res.PowerSurplus,
                6 => res.Ore,
                7 => res.Medical,
                _ => 0f
            };
            if (index == 0) return Mathf.FloorToInt(val).ToString(CultureInfo.InvariantCulture);

            if (index == 5)
            {
                return val >= 0 ? "+" + Mathf.RoundToInt(val) : Mathf.RoundToInt(val).ToString(CultureInfo.InvariantCulture);
            }
            return Mathf.RoundToInt(val).ToString(CultureInfo.InvariantCulture);
        }

        private static float GetHudScale()
        {
            return Mathf.Clamp(Screen.height / 900f, 0.92f, 1.15f);
        }

        public static Rect GetLighthouseLauncherRect()
        {
            float scale = GetHudScale();
            return new Rect(344f * scale, GetTopBarTop() + GetTopBarHeight() * .5f - 14.5f * scale,
                128f * scale, 29f * scale);
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
                IslandWeatherType.Fog => "海雾",
                IslandWeatherType.StormSurge => "暴潮",
                IslandWeatherType.DebrisShower => "碎屑",
                IslandWeatherType.FreezingRain => "冻雨",
                IslandWeatherType.Blizzard => "暴雪",
                IslandWeatherType.Aurora => "极光",
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
            int weatherCount = System.Enum.GetValues(typeof(IslandWeatherType)).Length;
            if (weatherIcons == null || weatherIcons.Length != weatherCount)
            {
                weatherIcons = new Texture2D[weatherCount];
            }

            for (int i = 0; i < weatherIcons.Length; i++)
            {
                IslandWeatherType weatherType = (IslandWeatherType)i;
                Texture2D loaded = Resources.Load<Texture2D>("UI/Weather/" + weatherType);
                if (loaded != null)
                {
                    weatherIcons[i] = loaded;
                }
                else if (weatherIcons[i] == null)
                {
                    weatherIcons[i] = CreateWeatherIcon(weatherType);
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
            else if (weather == IslandWeatherType.Fog)
            {
                Color mist = new Color(0.72f, 0.85f, 0.92f, 0.9f);
                DrawIconLine(texture, new Vector2(12f, 46f), new Vector2(52f, 46f), 4f, mist);
                DrawIconLine(texture, new Vector2(8f, 34f), new Vector2(56f, 34f), 5f, mist);
                DrawIconLine(texture, new Vector2(14f, 22f), new Vector2(50f, 22f), 4f, mist);
                DrawIconLine(texture, new Vector2(18f, 12f), new Vector2(46f, 12f), 3f, mist * 0.85f);
            }
            else if (weather == IslandWeatherType.StormSurge)
            {
                Color ocean = new Color(0.28f, 0.72f, 0.92f, 1f);
                Color foam = new Color(0.88f, 0.96f, 1.0f, 1f);
                DrawIconLine(texture, new Vector2(8f, 16f), new Vector2(26f, 30f), 5f, ocean);
                DrawIconLine(texture, new Vector2(26f, 30f), new Vector2(44f, 48f), 6f, ocean);
                DrawIconLine(texture, new Vector2(44f, 48f), new Vector2(54f, 38f), 5f, ocean);
                DrawIconLine(texture, new Vector2(54f, 38f), new Vector2(42f, 34f), 4f, foam);
                FillIconCircle(texture, new Vector2(44f, 48f), 4f, foam);
                DrawIconLine(texture, new Vector2(8f, 12f), new Vector2(56f, 12f), 3f, ocean);
            }
            else if (weather == IslandWeatherType.DebrisShower)
            {
                Color ember = new Color(1.0f, 0.52f, 0.18f, 1f);
                Color gold = new Color(1.0f, 0.88f, 0.38f, 1f);
                DrawIconLine(texture, new Vector2(50f, 54f), new Vector2(32f, 36f), 4f, ember);
                FillIconCircle(texture, new Vector2(50f, 54f), 4f, gold);
                DrawIconLine(texture, new Vector2(34f, 46f), new Vector2(18f, 30f), 3f, ember);
                FillIconCircle(texture, new Vector2(34f, 46f), 3.5f, gold);
                DrawIconLine(texture, new Vector2(54f, 32f), new Vector2(40f, 18f), 3f, ember);
                FillIconCircle(texture, new Vector2(54f, 32f), 3.5f, gold);
            }
            else if (weather == IslandWeatherType.FreezingRain)
            {
                Color iceCloud = new Color(0.68f, 0.84f, 0.98f, 1f);
                Color icicle = new Color(0.38f, 0.92f, 1.0f, 1f);
                FillIconCircle(texture, new Vector2(22f, 35f), 10f, iceCloud);
                FillIconCircle(texture, new Vector2(34f, 40f), 13f, iceCloud);
                FillIconCircle(texture, new Vector2(46f, 34f), 9f, iceCloud);
                FillIconRect(texture, 18, 24, 50, 34, iceCloud);
                DrawIconLine(texture, new Vector2(24f, 21f), new Vector2(21f, 7f), 3.5f, icicle);
                DrawIconLine(texture, new Vector2(34f, 21f), new Vector2(31f, 5f), 4f, icicle);
                DrawIconLine(texture, new Vector2(44f, 21f), new Vector2(41f, 8f), 3.5f, icicle);
            }
            else if (weather == IslandWeatherType.Blizzard)
            {
                Color snow = new Color(0.92f, 0.97f, 1.0f, 1f);
                Vector2 center = new Vector2(32f, 32f);
                for (int a = 0; a < 3; a++)
                {
                    float rad = a * Mathf.PI / 3f;
                    Vector2 dir = new Vector2(Mathf.Cos(rad), Mathf.Sin(rad));
                    DrawIconLine(texture, center - dir * 21f, center + dir * 21f, 3.5f, snow);
                    Vector2 p1 = center + dir * 14f;
                    Vector2 p2 = center - dir * 14f;
                    Vector2 perp = new Vector2(-dir.y, dir.x) * 5.5f;
                    DrawIconLine(texture, p1, p1 + perp + dir * 3.5f, 2.5f, snow);
                    DrawIconLine(texture, p1, p1 - perp + dir * 3.5f, 2.5f, snow);
                    DrawIconLine(texture, p2, p2 + perp - dir * 3.5f, 2.5f, snow);
                    DrawIconLine(texture, p2, p2 - perp - dir * 3.5f, 2.5f, snow);
                }
                FillIconCircle(texture, center, 4f, snow);
            }
            else if (weather == IslandWeatherType.Aurora)
            {
                Color aGreen = new Color(0.25f, 0.95f, 0.65f, 0.95f);
                Color aCyan = new Color(0.20f, 0.85f, 0.95f, 0.85f);
                Color aPurple = new Color(0.68f, 0.38f, 0.98f, 0.75f);
                DrawIconLine(texture, new Vector2(8f, 46f), new Vector2(24f, 54f), 4f, aGreen);
                DrawIconLine(texture, new Vector2(24f, 54f), new Vector2(40f, 44f), 4f, aGreen);
                DrawIconLine(texture, new Vector2(40f, 44f), new Vector2(56f, 52f), 4f, aGreen);

                DrawIconLine(texture, new Vector2(10f, 32f), new Vector2(26f, 38f), 4f, aCyan);
                DrawIconLine(texture, new Vector2(26f, 38f), new Vector2(42f, 28f), 4f, aCyan);
                DrawIconLine(texture, new Vector2(42f, 28f), new Vector2(54f, 34f), 4f, aCyan);

                DrawIconLine(texture, new Vector2(12f, 18f), new Vector2(28f, 22f), 3.5f, aPurple);
                DrawIconLine(texture, new Vector2(28f, 22f), new Vector2(44f, 15f), 3.5f, aPurple);
                DrawIconLine(texture, new Vector2(44f, 15f), new Vector2(52f, 20f), 3.5f, aPurple);
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
            float menuWidth = 215f * scale;
            float menuHeight = Mathf.Min(430f * scale, Screen.height - 16f);
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
            float scale = menuRect.width / 210f;
            weatherMenuTitleStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(14f * scale), 10, 14);
            weatherOptionLabelStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 9, 12);
            weatherOptionSelectedLabelStyle.fontSize = weatherOptionLabelStyle.fontSize;
            weatherTimeValueStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(11f * scale), 8, 11);
            weatherTimeMarksStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(9f * scale), 7, 9);
            GUI.Label(new Rect(menuRect.x + 12f * scale, menuRect.y + 5f * scale,
                    menuRect.width - 24f * scale, 23f * scale),
                "天气模式", weatherMenuTitleStyle);

            string[] names = { "晴天", "阴天", "雨天", "大风", "雷雨", "海雾", "暴风潮", "天体碎屑", "极寒冻雨", "极寒暴雪", "极光之夜" };
            IslandWeatherType[] types =
            {
                IslandWeatherType.Clear, IslandWeatherType.Overcast, IslandWeatherType.Rain,
                IslandWeatherType.Wind, IslandWeatherType.Thunderstorm, IslandWeatherType.Fog,
                IslandWeatherType.StormSurge, IslandWeatherType.DebrisShower, IslandWeatherType.FreezingRain,
                IslandWeatherType.Blizzard, IslandWeatherType.Aurora
            };
            float optionWidth = menuRect.width - 20f * scale;
            float optionHeight = 25f * scale;
            float rowSpacing = 3f * scale;
            float startY = menuRect.y + 32f * scale;
            for (int i = 0; i < names.Length; i++)
            {
                Rect optionRect = new Rect(menuRect.x + 10f * scale,
                    startY + i * (optionHeight + rowSpacing), optionWidth, optionHeight);
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
                float itemIconSize = 20f * scale;
                Rect itemIconRect = new Rect(optionRect.x + 6f * scale, optionRect.center.y - itemIconSize * 0.5f, itemIconSize, itemIconSize);
                int typeIdx = (int)types[i];
                if (weatherIcons != null && typeIdx >= 0 && typeIdx < weatherIcons.Length && weatherIcons[typeIdx] != null)
                {
                    GUI.DrawTexture(itemIconRect, weatherIcons[typeIdx], ScaleMode.ScaleToFit, true);
                }
                GUIStyle labelStyle = selected ? weatherOptionSelectedLabelStyle : weatherOptionLabelStyle;
                GUI.Label(new Rect(itemIconRect.xMax + 6f * scale, optionRect.y,
                    optionRect.width - toggleWidth - itemIconSize - 18f * scale, optionRect.height), names[i], labelStyle);
            }

            // Divider between weather list and daylight timeline
            float lastOptionBottom = startY + names.Length * (optionHeight + rowSpacing);
            DrawHudDivider(new Rect(menuRect.x + 12f * scale, lastOptionBottom + 2f * scale,
                menuRect.width - 24f * scale, Mathf.Max(1f, scale)), new Color(0.86f, 0.73f, 0.44f, 0.25f));

            float timeHeaderY = lastOptionBottom + 6f * scale;
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
                timeHeaderY + 20f * scale, menuRect.width - 32f * scale, 17f * scale);
            float selectedTime = GUI.HorizontalSlider(timeSliderRect, timeHours, 0f, 24f,
                weatherTimeSliderStyle, weatherTimeSliderThumbStyle);
            if (Mathf.Abs(selectedTime - timeHours) > 0.001f)
            {
                weatherSystem.SetTimeOfDay(selectedTime);
            }

            string[] timeMarks = { "0", "6", "12", "18", "24" };
            float marksY = timeSliderRect.yMax + 3f * scale;
            for (int i = 0; i < timeMarks.Length; i++)
            {
                float markerX = timeSliderRect.x + timeSliderRect.width * (i / 4f);
                Rect markerRect = new Rect(markerX - 10f * scale,
                    marksY, 20f * scale, 14f * scale);
                weatherTimeMarksStyle.alignment = i == 0 ? TextAnchor.MiddleLeft :
                    i == timeMarks.Length - 1 ? TextAnchor.MiddleRight : TextAnchor.MiddleCenter;
                GUI.Label(markerRect, timeMarks[i], weatherTimeMarksStyle);
            }
        }

        private void DrawHeaderButtons(Rect rect)
        {
            string gridTooltip = IsBuildingContextActive
                ? (isBuildGridVisible ? "隐藏建造网格 (G)" : "显示建造网格 (G)")
                : "进入建设并显示网格 (G)";
            string[] tooltips = { "重置视角", "切换俯视 (Tab)", gridTooltip, "设置 (Esc)" };
            EnsureTopHudUtilityIcons();
            if (topHudUtilityIcons == null)
            {
                return;
            }

            float scale = GetHudScale();
            float buttonSize = 34f * scale;
            float buttonGap = 8f * scale;
            float hitSize = 48f * scale;
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
                // Brass emblems: slightly dimmed at rest, full brightness on hover, faded when the grid is hidden.
                GUI.color = pressed ? new Color(0.72f, 0.72f, 0.72f, 1f)
                    : hovered ? Color.white
                    : (i == 2 && !isBuildGridVisible) ? new Color(0.78f, 0.78f, 0.78f, 0.5f)
                    : new Color(0.86f, 0.86f, 0.86f, 1f);
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
            // Prefer the hand-painted brass emblems: compass, island, map layers, gear.
            string[] emblemNames = { "CameraReset", "IslandView", "GridToggle", "ControlsHelp" };
            Texture2D emblem = Resources.Load<Texture2D>("UI/HeaderButtons/" + emblemNames[Mathf.Clamp(index, 0, 3)]);
            if (emblem != null) return emblem;

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
                    SetBuildGridVisibility(isBuildGridVisible && IsBuildingContextActive);
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
            EnsureSidebarCategoryUi();
            EnsureSidebarCategoryStyles();

            float scale = GetHudScale();
            for (int displayIndex = 0; displayIndex < SidebarDisplayOrder.Length; displayIndex++)
            {
                SidebarCategory category = SidebarDisplayOrder[displayIndex];
                int catIndex = (int)category;
                Rect rect = GetSidebarCategoryButtonRect(displayIndex);

                bool selected = isBuildMenuOpen && activeSidebarCategory == category;
                bool hovered = rect.Contains(Event.current.mousePosition);

                // Speed-button style segment effect (warm plate when active, soft glow when hovered)
                // Transparent emblem buttons follow the HUD utility icon treatment.

                if (GUI.Button(rect, new GUIContent(string.Empty, SidebarCategoryNames[catIndex] + "菜单"), transparentButtonStyle != null ? transparentButtonStyle : GUIStyle.none))
                {
                    if (isBuildMenuOpen && activeSidebarCategory == category)
                    {
                        isBuildMenuOpen = false;
                    }
                    else
                    {
                        SelectSidebarCategory(category);
                    }
                }

                // Draw Icon
                Texture2D icon = sidebarCategoryIcons != null && catIndex < sidebarCategoryIcons.Length
                    ? sidebarCategoryIcons[catIndex] : null;
                if (icon != null)
                {
                    float iconSize = 34f * scale;
                    Rect iconRect = new Rect(rect.center.x - iconSize * 0.5f, rect.y + 4f * scale, iconSize, iconSize);
                    Color prevColor = GUI.color;
                    GUI.color = selected ? new Color(1f, .88f, .48f) : hovered ? new Color(1f, .96f, .80f) : new Color(.86f, .69f, .36f);
                    GUI.DrawTexture(iconRect, icon, ScaleMode.ScaleToFit, true);
                    GUI.color = prevColor;
                }

                // Draw Label
                GUIStyle labelStyle = new GUIStyle(speedSegmentStyle ?? GUI.skin.label);
                labelStyle.alignment = TextAnchor.MiddleCenter;
                labelStyle.normal.textColor = selected ? new Color(1f, .88f, .48f) : Color.white;
                if (labelStyle != null)
                {
                    labelStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 14);
                    GUI.Label(new Rect(rect.x, rect.y + 40f * scale, rect.width, 18f * scale),
                        SidebarCategoryNames[catIndex], labelStyle);
                }
            }
        }

        private void SelectSidebarCategory(SidebarCategory category)
        {
            if (category == SidebarCategory.Technology)
            {
                OpenKnowledgeFullscreen(0);
                return;
            }
            if (category == SidebarCategory.Culture)
            {
                OpenKnowledgeFullscreen(1);
                return;
            }
            isWeatherMenuOpen = false;
            isResourceMenuOpen = false;
            isKnowledgeFullscreenOpen = false;
            activeSidebarCategory = category;
            isBuildMenuOpen = true;
            selectedBuildableIndex = -1;
            hasLastRoadCell = false;
            hoverMessage = string.Empty;
            SetBuildGridVisibility(false);
        }

        private void DrawBuildPanel(Rect panelRect)
        {
            // Drag handling on the header bar
            Rect headerDragRect = new Rect(panelRect.x, panelRect.y, panelRect.width - 45f, 40f);
            Event evt = Event.current;
            if (evt.type == EventType.MouseDown && evt.button == 0 && headerDragRect.Contains(evt.mousePosition))
            {
                isDraggingBuildPanel = true;
                dragBuildPanelMouseStartPos = evt.mousePosition;
                dragBuildPanelStartPos = new Vector2(panelRect.x, panelRect.y);
                evt.Use();
            }
            else if (evt.type == EventType.MouseDrag && isDraggingBuildPanel)
            {
                Vector2 delta = evt.mousePosition - dragBuildPanelMouseStartPos;
                Vector2 newPos = dragBuildPanelStartPos + delta;
                float clampedX = Mathf.Clamp(newPos.x, 8f, Mathf.Max(8f, Screen.width - panelRect.width - 8f));
                float clampedY = Mathf.Clamp(newPos.y, 8f, Mathf.Max(8f, Screen.height - panelRect.height - 8f));
                customBuildPanelPos = new Vector2(clampedX, clampedY);
                hasCustomBuildPanelPos = true;
                evt.Use();
            }
            else if (evt.type == EventType.MouseUp && isDraggingBuildPanel)
            {
                isDraggingBuildPanel = false;
                evt.Use();
            }

            GUIStyle activePanelStyle = activeSidebarCategory == SidebarCategory.Buildings ? buildPanelStyle : panelStyle;
            GUI.Box(panelRect, GUIContent.none, activePanelStyle);
            string title = activeSidebarCategory == SidebarCategory.Technology
                ? "科技发展路线"
                : activeSidebarCategory == SidebarCategory.Culture
                    ? "文化发展路线"
                    : activeSidebarCategory == SidebarCategory.Tasks
                        ? "海岛生存目标与任务"
                        : activeSidebarCategory == SidebarCategory.Warehouse
                            ? "群岛中央储备物资库"
                            : "海岛建设";
            GUI.Label(new Rect(panelRect.x + 18f, panelRect.y + 13f, panelRect.width - 110f, 27f), title, titleStyle);
            GUI.Label(new Rect(panelRect.xMax - 90f, panelRect.y + 16f, 48f, 20f), "⋮⋮ 拖拽", mutedLabelStyle);
            Rect closeRect = new Rect(panelRect.xMax - 38f, panelRect.y + 9f, 28f, 28f);
            if (GUI.Button(closeRect, "×", closeButtonStyle))
            {
                isBuildMenuOpen = false;
            }

            if (activeSidebarCategory == SidebarCategory.Technology)
            {
                DrawTechnologyPanel(panelRect);
                return;
            }

            if (activeSidebarCategory == SidebarCategory.Culture)
            {
                DrawKnowledgeRoutePanel(panelRect, CultureRouteNames, CultureRouteDetails,
                    ref selectedCultureRouteIndex);
                return;
            }

            if (activeSidebarCategory == SidebarCategory.Tasks)
            {
                DrawTasksPanel(panelRect);
                return;
            }

            if (activeSidebarCategory == SidebarCategory.Warehouse)
            {
                DrawWarehousePanel(panelRect);
                return;
            }

            DrawToolModeButtons(panelRect);
            GUI.Label(new Rect(panelRect.x + 19f, panelRect.y + 43f, panelRect.width - 38f, 22f),
                "按类别浏览设施", mutedLabelStyle);
            DrawBuildCategoryTabs(panelRect);

            int categoryIndex = (int)selectedBuildCategory;
            int categoryItemCount = CountBuildablesInCategory(selectedBuildCategory);
            GUI.Label(new Rect(panelRect.x + 19f, panelRect.y + 108f, panelRect.width - 38f, 22f),
                BuildCategoryHeaderNames[categoryIndex] + " · " + categoryItemCount + " 项", buildCategoryHeadingStyle);
            Color previousColor = GUI.color;
            GUI.color = new Color(0.55f, 0.68f, 0.59f, 0.42f);
            GUI.DrawTexture(new Rect(panelRect.x + 145f, panelRect.y + 119f, panelRect.width - 164f, 1f),
                Texture2D.whiteTexture);
            GUI.color = previousColor;

            float footerHeight = 88f;
            const float scrollTop = 136f;
            Rect scrollRect = new Rect(panelRect.x + 12f, panelRect.y + scrollTop,
                panelRect.width - 24f, panelRect.height - scrollTop - footerHeight);
            float cardWidth = (scrollRect.width - 28f) * 0.5f;
            float cardHeight = 164f;
            float rowSpacing = 174f;
            float contentHeight = Mathf.Ceil(categoryItemCount / 2f) * rowSpacing;
            Rect viewRect = new Rect(0f, 0f, scrollRect.width - 16f, contentHeight);
            if (categoryItemCount == 0)
            {
                string unlockText = GetNextBuildUnlockText(selectedBuildCategory);
                GUI.Label(new Rect(scrollRect.x + 20f, scrollRect.y + 28f, scrollRect.width - 40f,
                    scrollRect.height - 30f),
                    unlockText, mutedLabelStyle);
                return;
            }
            buildMenuScroll = GUI.BeginScrollView(scrollRect, buildMenuScroll, viewRect);

            int visibleIndex = 0;
            for (int i = 0; i < Buildables.Length; i++)
            {
                if (Buildables[i].Category != selectedBuildCategory || !IsBuildableUnlocked(Buildables[i]))
                {
                    continue;
                }

                int column = visibleIndex % 2;
                int row = visibleIndex / 2;
                Rect cardRect = new Rect(column * (cardWidth + 8f), row * rowSpacing, cardWidth, cardHeight);
                DrawBuildCard(i, cardRect);
                visibleIndex++;
            }

            GUI.EndScrollView();

            float footerY = panelRect.yMax - footerHeight + 2f;
            GUI.Label(new Rect(panelRect.x + 18f, footerY, panelRect.width - 36f, 30f), statusMessage, mutedLabelStyle);
            string defaultDetail = selectedBuildableIndex < 0
                ? "选择设施后显示全岛网格 · 左键拖动平移 · 中键拖转视角"
                : Buildables[selectedBuildableIndex].Kind == BuildableKind.Road
                    ? "按住左键连续铺路 · 中键拖转视角 · 右键取消"
                    : Buildables[selectedBuildableIndex].Kind == BuildableKind.Building
                        ? "左键放置 · Q / E 旋转 · 橙色格线标示山地 · 右键取消"
                        : "左键放置 · 中键拖转视角 · 右键取消";
            string detail = !string.IsNullOrEmpty(hoverMessage) ? hoverMessage : defaultDetail;
            GUI.Label(new Rect(panelRect.x + 18f, footerY + 31f, panelRect.width - 36f, 43f), detail, mutedLabelStyle);
        }

        private void DrawBuildCategoryTabs(Rect panelRect)
        {
            const float topOffset = 70f;
            const float height = 34f;
            const float gap = 4f;
            float width = (panelRect.width - 24f - gap * (BuildCategoryNames.Length - 1)) /
                BuildCategoryNames.Length;

            for (int i = 0; i < BuildCategoryNames.Length; i++)
            {
                BuildCategory category = (BuildCategory)i;
                bool selected = category == selectedBuildCategory;
                Rect tabRect = new Rect(panelRect.x + 12f + i * (width + gap), panelRect.y + topOffset, width, height);
                GUIStyle buttonStyle = selected ? selectedBuildCategoryButtonStyle : buildCategoryButtonStyle;
                if (GUI.Button(tabRect, GUIContent.none, buttonStyle))
                {
                    SelectBuildCategory(category);
                }

                selected = category == selectedBuildCategory;
                Color iconColor = selected
                    ? new Color(0.94f, 0.86f, 0.62f, 1f)
                    : new Color(0.73f, 0.82f, 0.75f, 1f);
                Rect iconRect = new Rect(tabRect.x + 7f, tabRect.y + 9f, 16f, 16f);
                DrawBuildCategoryIcon(iconRect, category, iconColor);
                GUIStyle labelStyle = selected ? selectedBuildCategoryLabelStyle : buildCategoryLabelStyle;
                GUI.Label(new Rect(tabRect.x + 26f, tabRect.y + 2f, width - 45f, height - 4f),
                    BuildCategoryNames[i], labelStyle);
                GUI.Label(new Rect(tabRect.xMax - 19f, tabRect.y + 2f, 15f, height - 4f),
                    CountBuildablesInCategory(category).ToString(), buildCategoryCountStyle);

                if (selected)
                {
                    Color previousColor = GUI.color;
                    GUI.color = new Color(0.84f, 0.72f, 0.39f, 0.95f);
                    GUI.DrawTexture(new Rect(tabRect.x + 9f, tabRect.yMax - 2f, tabRect.width - 18f, 2f),
                        Texture2D.whiteTexture);
                    GUI.color = previousColor;
                }
            }
        }

        private void SelectBuildCategory(BuildCategory category)
        {
            if (selectedBuildCategory == category)
            {
                return;
            }

            selectedBuildCategory = category;
            buildMenuScroll = Vector2.zero;
            selectedBuildableIndex = -1;
            hasLastRoadCell = false;
            hoverMessage = string.Empty;
            statusMessage = "已切换至" + BuildCategoryNames[(int)category] + "分类。";
            SetBuildGridVisibility(false);
        }

        private int CountBuildablesInCategory(BuildCategory category)
        {
            int count = 0;
            for (int i = 0; i < Buildables.Length; i++)
            {
                if (Buildables[i].Category == category && IsBuildableUnlocked(Buildables[i]))
                {
                    count++;
                }
            }

            return count;
        }

        private bool IsBuildableUnlocked(BuildableDefinition definition)
        {
            return IgnoreBuildingTechnologyForTesting || definition.ScenarioLevel <= researchLevel;
        }

        private string GetNextBuildUnlockText(BuildCategory category)
        {
            int nextLevel = int.MaxValue;
            for (int i = 0; i < Buildables.Length; i++)
            {
                if (Buildables[i].Category == category && Buildables[i].ScenarioLevel > researchLevel)
                {
                    nextLevel = Mathf.Min(nextLevel, Buildables[i].ScenarioLevel);
                }
            }

            return nextLevel == int.MaxValue
                ? "当前分类没有更多设施。"
                : "当前阶段尚无可建造设施。\n完成主线研究 R" + nextLevel + " 后解锁本类首批设施。";
        }

        private static void DrawBuildCategoryIcon(Rect rect, BuildCategory category, Color color)
        {
            Vector2 center = rect.center;
            switch (category)
            {
                case BuildCategory.Residential:
                    DrawBuildCategoryLine(new Vector2(rect.x + 1f, rect.y + 8f), new Vector2(center.x, rect.y + 2f), 1.7f, color);
                    DrawBuildCategoryLine(new Vector2(center.x, rect.y + 2f), new Vector2(rect.xMax - 1f, rect.y + 8f), 1.7f, color);
                    DrawBuildCategoryLine(new Vector2(rect.x + 3f, rect.y + 7f), new Vector2(rect.x + 3f, rect.yMax - 1f), 1.7f, color);
                    DrawBuildCategoryLine(new Vector2(rect.xMax - 3f, rect.y + 7f), new Vector2(rect.xMax - 3f, rect.yMax - 1f), 1.7f, color);
                    DrawBuildCategoryLine(new Vector2(rect.x + 3f, rect.yMax - 1f), new Vector2(rect.xMax - 3f, rect.yMax - 1f), 1.7f, color);
                    DrawBuildCategoryLine(new Vector2(center.x, rect.y + 10f), new Vector2(center.x, rect.yMax - 1f), 1.5f, color);
                    break;
                case BuildCategory.Production:
                    DrawBuildCategoryLine(new Vector2(rect.x + 3f, rect.yMax - 2f), new Vector2(rect.xMax - 4f, rect.y + 4f), 2f, color);
                    DrawBuildCategoryLine(new Vector2(rect.xMax - 7f, rect.y + 2f), new Vector2(rect.xMax - 2f, rect.y + 7f), 2.6f, color);
                    DrawBuildCategoryLine(new Vector2(rect.x + 2f, rect.y + 4f), new Vector2(rect.xMax - 3f, rect.yMax - 3f), 1.7f, color);
                    DrawBuildCategoryLine(new Vector2(rect.x + 1f, rect.y + 2f), new Vector2(rect.x + 6f, rect.y + 7f), 2.4f, color);
                    break;
                case BuildCategory.Facilities:
                    DrawBuildCategoryCircle(center, 4f, 1.6f, color);
                    for (int i = 0; i < 8; i++)
                    {
                        float angle = i * 45f * Mathf.Deg2Rad;
                        Vector2 direction = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
                        DrawBuildCategoryLine(center + direction * 5.5f, center + direction * 7.5f, 1.7f, color);
                    }
                    break;
                case BuildCategory.Transportation:
                    DrawBuildCategoryCircle(new Vector2(center.x, rect.y + 3.5f), 2.2f, 1.5f, color);
                    DrawBuildCategoryLine(new Vector2(center.x, rect.y + 5.5f), new Vector2(center.x, rect.yMax - 4f), 1.7f, color);
                    DrawBuildCategoryLine(new Vector2(rect.x + 3f, rect.y + 7f), new Vector2(rect.xMax - 3f, rect.y + 7f), 1.7f, color);
                    DrawBuildCategoryLine(new Vector2(rect.x + 2f, rect.y + 11f), new Vector2(rect.x + 5f, rect.yMax - 2f), 1.7f, color);
                    DrawBuildCategoryLine(new Vector2(rect.x + 5f, rect.yMax - 2f), new Vector2(rect.xMax - 5f, rect.yMax - 2f), 1.7f, color);
                    DrawBuildCategoryLine(new Vector2(rect.xMax - 5f, rect.yMax - 2f), new Vector2(rect.xMax - 2f, rect.y + 11f), 1.7f, color);
                    break;
            }
        }

        private static void DrawBuildCategoryCircle(Vector2 center, float radius, float thickness, Color color)
        {
            const int segmentCount = 12;
            for (int i = 0; i < segmentCount; i++)
            {
                float firstAngle = (i / (float)segmentCount) * Mathf.PI * 2f;
                float secondAngle = ((i + 1) / (float)segmentCount) * Mathf.PI * 2f;
                Vector2 first = center + new Vector2(Mathf.Cos(firstAngle), Mathf.Sin(firstAngle)) * radius;
                Vector2 second = center + new Vector2(Mathf.Cos(secondAngle), Mathf.Sin(secondAngle)) * radius;
                DrawBuildCategoryLine(first, second, thickness, color);
            }
        }

        private static void DrawBuildCategoryLine(Vector2 start, Vector2 end, float thickness, Color color)
        {
            Vector2 delta = end - start;
            float length = delta.magnitude;
            if (length <= 0.01f)
            {
                return;
            }

            Vector2 center = (start + end) * 0.5f;
            Matrix4x4 previousMatrix = GUI.matrix;
            Color previousColor = GUI.color;
            GUIUtility.RotateAroundPivot(Mathf.Atan2(delta.y, delta.x) * Mathf.Rad2Deg, center);
            GUI.color = color;
            GUI.DrawTexture(new Rect(center.x - length * 0.5f, center.y - thickness * 0.5f, length, thickness),
                Texture2D.whiteTexture);
            GUI.matrix = previousMatrix;
            GUI.color = previousColor;
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

        private void DrawTasksPanel(Rect panelRect)
        {
            const float horizontalPadding = 14f;
            string[] tabs = { "主线航标", "聚落生存", "海洋搜救" };
            float tabWidth = (panelRect.width - horizontalPadding * 2f - 8f) / 3f;

            for (int i = 0; i < tabs.Length; i++)
            {
                Rect tabRect = new Rect(panelRect.x + horizontalPadding + i * (tabWidth + 4f), panelRect.y + 44f, tabWidth, 30f);
                bool selected = selectedTaskTab == i;
                if (GUI.Button(tabRect, tabs[i], selected ? selectedBuildCategoryButtonStyle : buildCategoryButtonStyle))
                {
                    selectedTaskTab = i;
                    taskMenuScroll = Vector2.zero;
                }
            }

            const float contentTop = 84f;
            float footerHeight = 44f;
            Rect scrollRect = new Rect(panelRect.x + 12f, panelRect.y + contentTop,
                panelRect.width - 24f, panelRect.height - contentTop - footerHeight);

            switch (selectedTaskTab)
            {
                case 0:
                    DrawLighthouseTaskContent(scrollRect);
                    break;
                case 1:
                    DrawColonySurvivalTaskContent(scrollRect);
                    break;
                case 2:
                    DrawOceanRescueTaskContent(scrollRect);
                    break;
            }

            float footerY = panelRect.yMax - footerHeight + 4f;
            string tip = selectedTaskTab == 0
                ? "提示：按下快捷键 [L] 可快速将镜头平移至灯塔遗址。"
                : selectedTaskTab == 1
                    ? "提示：合理调配居所与仓储，防范潮汐暴风来袭。"
                    : "提示：落脚码头可为船只提供补给与船员登乘。";
            GUI.Label(new Rect(panelRect.x + 18f, footerY, panelRect.width - 36f, 32f), tip, mutedLabelStyle);
        }

        private void DrawLighthouseTaskContent(Rect scrollRect)
        {
            int completed = lighthouseSite != null ? lighthouseSite.CompletedStage : 0;
            int working = lighthouseSite != null ? lighthouseSite.WorkingStage : -1;
            float progress = lighthouseSite != null ? lighthouseSite.ConstructionProgress : 0f;
            int nextStage = completed + 1;

            float contentHeight = 520f;
            Rect viewRect = new Rect(0f, 0f, scrollRect.width - 16f, contentHeight);
            taskMenuScroll = GUI.BeginScrollView(scrollRect, taskMenuScroll, viewRect);

            // Overview Card
            Rect cardRect = new Rect(4f, 4f, viewRect.width - 8f, 130f);
            GUI.Box(cardRect, GUIContent.none, cardStyle);

            GUI.Label(new Rect(cardRect.x + 12f, cardRect.y + 8f, cardRect.width - 24f, 22f),
                "【主线工程】群岛航标灯塔修复", cardLabelStyle);

            string currentStageName = completed < LighthouseSite.StageNames.Length
                ? LighthouseSite.StageNames[completed]
                : "全面竣工";
            string statusStr = working >= 0
                ? "施工建造中 (" + Mathf.FloorToInt(progress * 100f) + "%)"
                : completed >= 8
                    ? "★ 航标已点亮，群岛生还！"
                    : "阶段 " + nextStage + "/8：待开启工程";

            GUI.Label(new Rect(cardRect.x + 12f, cardRect.y + 32f, cardRect.width - 24f, 20f),
                "当前已达成：" + currentStageName + "  (" + statusStr + ")", mutedLabelStyle);

            // Progress bar
            Rect barBg = new Rect(cardRect.x + 12f, cardRect.y + 56f, cardRect.width - 24f, 12f);
            Color prevColor = GUI.color;
            GUI.color = new Color(0.12f, 0.16f, 0.18f, 0.95f);
            GUI.DrawTexture(barBg, Texture2D.whiteTexture);
            float overallFraction = Mathf.Clamp01((completed + (working >= 0 ? progress : 0f)) / 8f);
            GUI.color = new Color(0.85f, 0.70f, 0.38f, 1f);
            GUI.DrawTexture(new Rect(barBg.x, barBg.y, barBg.width * overallFraction, barBg.height), Texture2D.whiteTexture);
            GUI.color = prevColor;

            // Buttons
            Rect focusBtnRect = new Rect(cardRect.x + 12f, cardRect.y + 80f, (cardRect.width - 32f) * 0.5f, 32f);
            Rect openSiteBtnRect = new Rect(focusBtnRect.xMax + 8f, cardRect.y + 80f, (cardRect.width - 32f) * 0.5f, 32f);

            if (GUI.Button(focusBtnRect, "定位灯塔 [L]", buildCategoryButtonStyle))
            {
                FocusLighthouse(LighthouseSite.SitePosition);
            }
            if (GUI.Button(openSiteBtnRect, "施工管理面板", selectedBuildCategoryButtonStyle))
            {
                if (lighthouseSite != null) lighthouseSite.IsPanelOpen = true;
            }

            // Milestone stages list
            float listY = cardRect.yMax + 12f;
            GUI.Label(new Rect(4f, listY, viewRect.width, 22f), "航标建造阶段蓝图：", buildCategoryHeadingStyle);
            listY += 26f;

            for (int i = 0; i < LighthouseSite.StageNames.Length; i++)
            {
                Rect stageCard = new Rect(4f, listY, viewRect.width - 8f, 38f);
                bool isDone = i <= completed;
                bool isCurr = i == working || (working < 0 && i == nextStage);

                GUI.Box(stageCard, GUIContent.none, isCurr ? selectedCardStyle : cardStyle);

                string badge = isDone ? "✓ 已完工" : isCurr ? (working >= 0 ? "⚡ 施工中" : "▶ 当前待建") : "○ 待解锁";
                Color badgeColor = isDone ? new Color(0.4f, 0.9f, 0.5f) : isCurr ? new Color(1f, 0.85f, 0.45f) : new Color(0.6f, 0.65f, 0.65f);

                GUI.Label(new Rect(stageCard.x + 10f, stageCard.y + 8f, 240f, 22f),
                    (i + 1).ToString("00") + ". " + LighthouseSite.StageNames[i], cardLabelStyle);

                GUIStyle badgeStyle = new GUIStyle(mutedLabelStyle) { alignment = TextAnchor.MiddleRight };
                badgeStyle.normal.textColor = badgeColor;
                GUI.Label(new Rect(stageCard.xMax - 110f, stageCard.y + 8f, 100f, 22f), badge, badgeStyle);

                listY += 44f;
            }

            GUI.EndScrollView();
        }

        private void DrawColonySurvivalTaskContent(Rect scrollRect)
        {
            var res = ColonyResourceManager.Instance;
            var citizens = ColonyCitizenManager.Instance;

            int woodCount = res != null ? Mathf.FloorToInt(res.Wood) : wood;
            int foodCount = res != null ? Mathf.FloorToInt(res.Food) : 0;
            int waterCount = res != null ? Mathf.FloorToInt(res.Water) : 0;
            int popCount = citizens != null ? citizens.TotalPopulation : 0;
            int housedCount = citizens != null ? Mathf.Min(citizens.TotalPopulation, citizens.GetHousingCapacity()) : 0;

            float contentHeight = 380f;
            Rect viewRect = new Rect(0f, 0f, scrollRect.width - 16f, contentHeight);
            taskMenuScroll = GUI.BeginScrollView(scrollRect, taskMenuScroll, viewRect);

            float cardY = 4f;

            // Objective 1: Stockpiling
            DrawObjectiveCard(ref cardY, viewRect.width - 8f,
                "防灾物资储备",
                "在库房与露天堆场中储备充足的基础生存物资，以备不时之需。",
                "原木: " + woodCount + "/100    食物: " + foodCount + "/50    淡水: " + waterCount + "/50",
                woodCount >= 100 && foodCount >= 50 && waterCount >= 50,
                Mathf.Clamp01((Mathf.Clamp01(woodCount / 100f) + Mathf.Clamp01(foodCount / 50f) + Mathf.Clamp01(waterCount / 50f)) / 3f));

            // Objective 2: Population & Housing
            DrawObjectiveCard(ref cardY, viewRect.width - 8f,
                "聚落人口与庇护所",
                "建造庇护棚与简易木屋，为所有上岸的落难流民提供遮风避雨之处。",
                "人口: " + popCount + " 人    已安置居所: " + housedCount + " 人",
                popCount > 0 && housedCount >= popCount,
                popCount > 0 ? Mathf.Clamp01((float)housedCount / popCount) : 0f);

            // Objective 3: Storm Defense
            string weatherName = weatherSystem != null ? weatherSystem.CurrentWeatherName : "晴天";
            string seaState = weatherSystem != null ? GetWeatherSeaState(weatherSystem.CurrentWeather) : "平静";
            DrawObjectiveCard(ref cardY, viewRect.width - 8f,
                "风暴防潮与基础护岸",
                "当前气候：" + weatherName + "，海况：" + seaState + "。密切观察天候并防范潮位上升。",
                "建造防潮堤坝或加固近海设施以应对暴风潮",
                true,
                1f);

            GUI.EndScrollView();
        }

        private void DrawOceanRescueTaskContent(Rect scrollRect)
        {
            bool hasDock = false;
            foreach (var b in cellToPlacedBuilding.Values)
            {
                if (b.Definition.Kind == BuildableKind.Dock)
                {
                    hasDock = true;
                    break;
                }
            }

            int boatCount = FindObjectsByType<RescueBoatController>(FindObjectsSortMode.None)?.Length ?? 0;

            float contentHeight = 360f;
            Rect viewRect = new Rect(0f, 0f, scrollRect.width - 16f, contentHeight);
            taskMenuScroll = GUI.BeginScrollView(scrollRect, taskMenuScroll, viewRect);

            float cardY = 4f;

            // Objective 1: Dock
            DrawObjectiveCard(ref cardY, viewRect.width - 8f,
                "落脚码头运转",
                "在平缓海岸铺设延伸木栈桥与码头泊位，作为海上救援与货物集散枢纽。",
                hasDock ? "码头已成功落成运转" : "尚未建造码头设施（设施分类中选择【码头】）",
                hasDock,
                hasDock ? 1f : 0f);

            // Objective 2: Boat Fleet
            DrawObjectiveCard(ref cardY, viewRect.width - 8f,
                "巡航搜救艇队伍",
                "调配搜救艇与船员巡视近海海域，搜救落水生还者并打捞漂流货箱。",
                "现存搜救船只：" + boatCount + " 艘",
                boatCount > 0,
                boatCount > 0 ? 1f : 0f);

            // Objective 3: Maritime Salvage
            DrawObjectiveCard(ref cardY, viewRect.width - 8f,
                "近海生还者搜救",
                "当海上出现求救信号时，派遣救援艇前往定位并接载登船，返航后移交居所安置。",
                "选中船只后右键海面指派航路，靠近生还者自动搜救",
                false,
                0.5f);

            GUI.EndScrollView();
        }

        private void DrawObjectiveCard(ref float y, float width, string title, string description, string progressText, bool isComplete, float progressFraction)
        {
            float height = 98f;
            Rect card = new Rect(4f, y, width, height);
            GUI.Box(card, GUIContent.none, isComplete ? selectedCardStyle : cardStyle);

            GUI.Label(new Rect(card.x + 12f, card.y + 7f, card.width - 110f, 22f), title, cardLabelStyle);

            string badge = isComplete ? "✓ 已达成" : "▶ 进行中";
            Color badgeColor = isComplete ? new Color(0.4f, 0.9f, 0.5f) : new Color(1f, 0.85f, 0.45f);
            GUIStyle badgeStyle = new GUIStyle(mutedLabelStyle) { alignment = TextAnchor.MiddleRight };
            badgeStyle.normal.textColor = badgeColor;
            GUI.Label(new Rect(card.xMax - 100f, card.y + 7f, 90f, 22f), badge, badgeStyle);

            GUI.Label(new Rect(card.x + 12f, card.y + 29f, card.width - 24f, 20f), description, mutedLabelStyle);
            GUI.Label(new Rect(card.x + 12f, card.y + 50f, card.width - 24f, 20f), progressText, cardLabelStyle);

            // Progress bar
            Rect barBg = new Rect(card.x + 12f, card.y + 74f, card.width - 24f, 8f);
            Color prevColor = GUI.color;
            GUI.color = new Color(0.12f, 0.16f, 0.18f, 0.95f);
            GUI.DrawTexture(barBg, Texture2D.whiteTexture);
            GUI.color = isComplete ? new Color(0.4f, 0.85f, 0.5f, 1f) : new Color(0.85f, 0.70f, 0.38f, 1f);
            GUI.DrawTexture(new Rect(barBg.x, barBg.y, barBg.width * Mathf.Clamp01(progressFraction), barBg.height), Texture2D.whiteTexture);
            GUI.color = prevColor;

            y += height + 10f;
        }

        private void DrawPinnedResourceSlots(Rect topBarRect)
        {
            float scale = GetHudScale();
            float y = topBarRect.y + 6f * scale;
            float height = topBarRect.height - 12f * scale;

            for (int s = 0; s < 4; s++)
            {
                float slotX = 468f * scale + s * (98f + 5f) * scale;
                Rect slotRect = new Rect(slotX, y, 98f * scale, height);
                int resIndex = pinnedHeaderResourceIndices != null && s < pinnedHeaderResourceIndices.Length
                    ? pinnedHeaderResourceIndices[s] : s;
                if (resIndex < 0 || resIndex >= TotalHeaderResourceCount) resIndex = 0;

                string resName = HeaderResourceDisplayNames[resIndex];
                string resAmount = GetHeaderResourceAmount(resIndex);

                // Resource Icon
                if (headerResourceIcons != null && resIndex < headerResourceIcons.Length && headerResourceIcons[resIndex] != null)
                {
                    float iconSize = 22f * scale;
                    GUI.DrawTexture(new Rect(slotRect.x + 6f * scale, slotRect.center.y - iconSize * 0.5f,
                        iconSize, iconSize), headerResourceIcons[resIndex], ScaleMode.ScaleToFit, true);
                }

                // Name & Value
                GUIStyle nameStyle = topHudSmallLabelStyle ?? GUI.skin.label;
                nameStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(11f * scale), 9, 13);
                nameStyle.normal.textColor = new Color(0.75f, 0.82f, 0.88f);
                GUI.Label(new Rect(slotRect.x + 30f * scale, slotRect.y + 3f * scale, slotRect.width - 34f * scale, 14f * scale),
                    resName, nameStyle);

                GUIStyle valStyle = headerResourceValueStyle ?? GUI.skin.label;
                valStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(14f * scale), 11, 16);
                GUI.Label(new Rect(slotRect.x + 30f * scale, slotRect.y + 17f * scale, slotRect.width - 34f * scale, 18f * scale),
                    resAmount, valStyle);

                // Dropdown indicator
                GUIStyle chevronStyle = new GUIStyle(mutedLabelStyle ?? GUI.skin.label)
                {
                    fontSize = Mathf.Clamp(Mathf.RoundToInt(10f * scale), 8, 12),
                    alignment = TextAnchor.MiddleRight
                };
                chevronStyle.normal.textColor = new Color(0.85f, 0.70f, 0.38f, 0.8f);
                GUI.Label(new Rect(slotRect.xMax - 14f * scale, slotRect.y + 2f * scale, 11f * scale, 12f * scale), "▾", chevronStyle);

                // Click to toggle dropdown picker
                if (GUI.Button(slotRect, new GUIContent(string.Empty, "点击更换展示物资 (当前: " + resName + ")"), transparentButtonStyle ?? GUIStyle.none))
                {
                    activePinnedResourceSlotPicker = activePinnedResourceSlotPicker == s ? -1 : s;
                }
            }

            // Draw Dropdown Picker if active
            if (activePinnedResourceSlotPicker >= 0 && activePinnedResourceSlotPicker < 4)
            {
                float pickerX = 468f * scale + activePinnedResourceSlotPicker * (98f + 5f) * scale;
                float pickerY = topBarRect.yMax + 4f * scale;
                float itemH = 28f * scale;
                float pickerW = 145f * scale;
                float pickerH = TotalHeaderResourceCount * itemH + 26f * scale;
                Rect pickerRect = new Rect(pickerX, pickerY, pickerW, pickerH);

                GUI.Box(pickerRect, GUIContent.none, cardStyle ?? GUI.skin.box);
                GUI.Label(new Rect(pickerRect.x + 8f * scale, pickerRect.y + 4f * scale, pickerRect.width - 16f * scale, 18f * scale),
                    "选择第 " + (activePinnedResourceSlotPicker + 1) + " 格展示物资", cardLabelStyle ?? GUI.skin.label);

                for (int i = 0; i < TotalHeaderResourceCount; i++)
                {
                    Rect rowRect = new Rect(pickerRect.x + 4f * scale, pickerRect.y + 22f * scale + i * itemH, pickerRect.width - 8f * scale, itemH - 2f * scale);
                    bool isSelected = pinnedHeaderResourceIndices[activePinnedResourceSlotPicker] == i;
                    GUIStyle btnStyle = isSelected ? selectedBuildCategoryButtonStyle : buildCategoryButtonStyle;

                    if (GUI.Button(rowRect, string.Empty, btnStyle))
                    {
                        pinnedHeaderResourceIndices[activePinnedResourceSlotPicker] = i;
                        activePinnedResourceSlotPicker = -1;
                    }

                    if (headerResourceIcons != null && i < headerResourceIcons.Length && headerResourceIcons[i] != null)
                    {
                        float icSize = 18f * scale;
                        GUI.DrawTexture(new Rect(rowRect.x + 4f * scale, rowRect.center.y - icSize * 0.5f, icSize, icSize),
                            headerResourceIcons[i], ScaleMode.ScaleToFit, true);
                    }

                    GUI.Label(new Rect(rowRect.x + 24f * scale, rowRect.y + 2f * scale, 60f * scale, rowRect.height),
                        HeaderResourceDisplayNames[i], isSelected ? cardLabelStyle : mutedLabelStyle);
                    GUI.Label(new Rect(rowRect.x + 84f * scale, rowRect.y + 2f * scale, rowRect.width - 88f * scale, rowRect.height),
                        GetHeaderResourceAmount(i), resourceValueStyle ?? GUI.skin.label);
                }

                // Close picker when clicking outside
                Event e = Event.current;
                if (e.type == EventType.MouseDown && !pickerRect.Contains(e.mousePosition))
                {
                    activePinnedResourceSlotPicker = -1;
                }
            }
        }

        private void DrawWarehousePanel(Rect panelRect)
        {
            var res = ColonyResourceManager.Instance;
            float scale = GetHudScale();

            // 1. Header Overview Card
            float headerCardH = 72f;
            Rect headerCard = new Rect(panelRect.x + 12f, panelRect.y + 44f, panelRect.width - 24f, headerCardH);
            GUI.Box(headerCard, GUIContent.none, cardStyle);

            float totalStorageCap = res != null ? res.GetCapacity(ResourceType.Wood) : 300f;
            float totalWaterCap = res != null ? res.GetCapacity(ResourceType.Water) : 200f;
            int storageCount = CountCompletedBuildings("StorageDepot");
            int waterTankCount = CountCompletedBuildings("WaterStorageTank");

            GUI.Label(new Rect(headerCard.x + 10f, headerCard.y + 7f, headerCard.width - 20f, 20f),
                "【全岛仓储容量总览】", cardLabelStyle);
            GUI.Label(new Rect(headerCard.x + 10f, headerCard.y + 27f, (headerCard.width - 20f) * 0.5f, 18f),
                "干货储量上限: " + Mathf.FloorToInt(totalStorageCap) + " (" + storageCount + " 处堆场)", mutedLabelStyle);
            GUI.Label(new Rect(headerCard.x + headerCard.width * 0.5f, headerCard.y + 27f, (headerCard.width - 20f) * 0.5f, 18f),
                "蓄水储量上限: " + Mathf.FloorToInt(totalWaterCap) + " (" + waterTankCount + " 座水罐)", mutedLabelStyle);
            GUI.Label(new Rect(headerCard.x + 10f, headerCard.y + 47f, headerCard.width - 20f, 18f),
                "点击任意物资右侧 [1]~[4] 可直接将其快捷钉选至顶部栏相应槽位。", mutedLabelStyle);

            // 2. Resource Items List
            float contentTop = 124f;
            float footerHeight = 40f;
            Rect scrollRect = new Rect(panelRect.x + 12f, panelRect.y + contentTop,
                panelRect.width - 24f, panelRect.height - contentTop - footerHeight);

            float itemHeight = 62f;
            float viewHeight = TotalHeaderResourceCount * (itemHeight + 6f);
            Rect viewRect = new Rect(0f, 0f, scrollRect.width - 16f, viewHeight);

            warehouseMenuScroll = GUI.BeginScrollView(scrollRect, warehouseMenuScroll, viewRect);

            ResourceType[] allTypes = {
                ResourceType.Wood,
                ResourceType.Food,
                ResourceType.Water,
                ResourceType.Metal,
                ResourceType.Fuel,
                ResourceType.Power,
                ResourceType.Ore,
                ResourceType.Medical
            };

            string[] categoryBadges = {
                "基础建材", "生活物资", "生活饮水", "工业精炼",
                "机械燃料", "电力能源", "地下采矿", "医疗卫勤"
            };

            for (int i = 0; i < TotalHeaderResourceCount; i++)
            {
                float rowY = i * (itemHeight + 6f);
                Rect rowRect = new Rect(0f, rowY, viewRect.width, itemHeight);

                int pinnedSlot = -1;
                for (int s = 0; s < 4; s++)
                {
                    if (pinnedHeaderResourceIndices[s] == i) { pinnedSlot = s + 1; break; }
                }

                GUI.Box(rowRect, GUIContent.none, pinnedSlot > 0 ? selectedCardStyle : cardStyle);

                // Resource Icon
                if (headerResourceIcons != null && i < headerResourceIcons.Length && headerResourceIcons[i] != null)
                {
                    GUI.DrawTexture(new Rect(rowRect.x + 8f, rowRect.y + 12f, 36f, 36f),
                        headerResourceIcons[i], ScaleMode.ScaleToFit, true);
                }

                // Name & Category Badge
                GUI.Label(new Rect(rowRect.x + 52f, rowRect.y + 6f, 70f, 20f),
                    HeaderResourceDisplayNames[i], cardLabelStyle);
                GUI.Label(new Rect(rowRect.x + 122f, rowRect.y + 7f, 65f, 18f),
                    "[" + categoryBadges[i] + "]", mutedLabelStyle);

                // Quantity / Capacity
                string amountStr = GetHeaderResourceAmount(i);
                float cap = res != null ? res.GetCapacity(allTypes[i]) : 300f;
                string capStr = allTypes[i] == ResourceType.Power ? " kW (盈余)" : " / " + Mathf.FloorToInt(cap);
                GUI.Label(new Rect(rowRect.x + 52f, rowRect.y + 26f, 150f, 18f),
                    amountStr + capStr, resourceValueStyle);

                // Net Production Rate
                float netRate = res != null ? res.GetNetRate(allTypes[i]) : 0f;
                string rateStr = netRate > 0.05f ? "+" + netRate.ToString("F1") + "/秒"
                    : (netRate < -0.05f ? netRate.ToString("F1") + "/秒" : "±0.0/秒");
                Color rateColor = netRate > 0.05f ? new Color(0.4f, 0.9f, 0.5f)
                    : (netRate < -0.05f ? new Color(1.0f, 0.45f, 0.4f) : new Color(0.7f, 0.75f, 0.75f));
                GUIStyle rateStyle = new GUIStyle(mutedLabelStyle);
                rateStyle.normal.textColor = rateColor;
                GUI.Label(new Rect(rowRect.x + 52f, rowRect.y + 42f, 120f, 16f),
                    "产耗: " + rateStr, rateStyle);

                // Quick Pin Buttons to Top Bar: [1] [2] [3] [4]
                float pinBtnW = 26f;
                float pinBtnH = 24f;
                float pinStartX = rowRect.xMax - (pinBtnW + 4f) * 4f - 6f;
                float pinY = rowRect.y + 18f;

                for (int s = 0; s < 4; s++)
                {
                    Rect pinRect = new Rect(pinStartX + s * (pinBtnW + 4f), pinY, pinBtnW, pinBtnH);
                    bool isThisSlot = pinnedHeaderResourceIndices[s] == i;
                    GUIStyle pStyle = isThisSlot ? selectedBuildCategoryButtonStyle : buildCategoryButtonStyle;
                    string btnLabel = (s + 1).ToString();

                    if (GUI.Button(pinRect, new GUIContent(btnLabel, "将【" + HeaderResourceDisplayNames[i] + "】钉选到顶部第 " + (s + 1) + " 栏"), pStyle))
                    {
                        pinnedHeaderResourceIndices[s] = i;
                    }
                }
            }

            GUI.EndScrollView();

            // Footer
            float footerY = panelRect.yMax - footerHeight + 4f;
            GUI.Label(new Rect(panelRect.x + 18f, footerY, panelRect.width - 36f, 32f),
                "提示：顶部栏 4 个物资框亦可直接点击切换展示任意品类。", mutedLabelStyle);
        }

        private void DrawTechnologyPanel(Rect panelRect)
        {
            const float horizontalPadding = 14f;
            float tabWidth = (panelRect.width - horizontalPadding * 2f - 6f) * 0.5f;
            Rect mainlineTab = new Rect(panelRect.x + horizontalPadding, panelRect.y + 44f, tabWidth, 30f);
            Rect efficiencyTab = new Rect(mainlineTab.xMax + 6f, mainlineTab.y, tabWidth, 30f);
            if (GUI.Button(mainlineTab, "主线研究", selectedTechnologyTab == 0 ? selectedBuildCategoryButtonStyle : buildCategoryButtonStyle))
            {
                selectedTechnologyTab = 0;
            }
            if (GUI.Button(efficiencyTab, "效率研究", selectedTechnologyTab == 1 ? selectedBuildCategoryButtonStyle : buildCategoryButtonStyle))
            {
                selectedTechnologyTab = 1;
            }

            GUI.Label(new Rect(panelRect.x + 18f, panelRect.y + 79f, panelRect.width - 36f, 22f),
                "研究等级 R" + researchLevel + "  ·  建筑开放至 L" + Mathf.Min(researchLevel, 5),
                buildCategoryHeadingStyle);
            DrawResearchProgressBar(new Rect(panelRect.x + 18f, panelRect.y + 104f, panelRect.width - 36f, 8f));

            const float footerHeight = 78f;
            const float contentTop = 128f;
            Rect listRect = new Rect(panelRect.x + 12f, panelRect.y + contentTop,
                panelRect.width - 24f, panelRect.height - contentTop - footerHeight);
            if (selectedTechnologyTab == 0)
            {
                DrawMainlineResearchList(listRect);
                DrawMainlineResearchFooter(panelRect, footerHeight);
            }
            else
            {
                List<EfficiencyResearchOption> options = GetAvailableEfficiencyResearchOptions();
                DrawEfficiencyResearchList(listRect, options);
                DrawEfficiencyResearchFooter(panelRect, footerHeight, options);
            }
        }

        private void DrawResearchProgressBar(Rect rect)
        {
            Color previousColor = GUI.color;
            GUI.color = new Color(0.08f, 0.14f, 0.14f, 0.95f);
            GUI.DrawTexture(rect, Texture2D.whiteTexture);
            if (activeResearchType != ResearchType.None && activeResearchDurationSeconds > 0f)
            {
                float progress = Mathf.Clamp01(activeResearchProgressSeconds / activeResearchDurationSeconds);
                GUI.color = new Color(0.53f, 0.76f, 0.59f, 1f);
                GUI.DrawTexture(new Rect(rect.x, rect.y, rect.width * progress, rect.height), Texture2D.whiteTexture);
            }
            GUI.color = previousColor;

            string label = activeResearchType == ResearchType.None
                ? "研究队列空闲"
                : GetActiveResearchName() + " · " + Mathf.RoundToInt(
                    Mathf.Clamp01(activeResearchProgressSeconds / Mathf.Max(0.01f, activeResearchDurationSeconds)) * 100f) + "%";
            GUI.Label(new Rect(rect.x, rect.y - 1f, rect.width, 20f), label, mutedLabelStyle);
        }

        private void DrawMainlineResearchList(Rect listRect)
        {
            const float rowHeight = 75f;
            const float rowSpacing = 81f;
            Rect viewRect = new Rect(0f, 0f, listRect.width - 16f, MainlineResearch.Length * rowSpacing);
            mainlineResearchScroll = GUI.BeginScrollView(listRect, mainlineResearchScroll, viewRect);
            for (int i = 0; i < MainlineResearch.Length; i++)
            {
                TechnologyResearchDefinition definition = MainlineResearch[i];
                Rect rowRect = new Rect(0f, i * rowSpacing, viewRect.width, rowHeight);
                bool selected = i == selectedMainlineResearchIndex;
                if (GUI.Button(rowRect, GUIContent.none, selected ? selectedCardStyle : cardStyle))
                {
                    selectedMainlineResearchIndex = i;
                }

                string state = GetMainlineResearchState(i);
                GUI.Label(new Rect(rowRect.x + 12f, rowRect.y + 5f, rowRect.width - 125f, 20f),
                    "R" + definition.Level + " · " + definition.Name, cardLabelStyle);
                GUI.Label(new Rect(rowRect.xMax - 112f, rowRect.y + 5f, 100f, 20f), state, mutedLabelStyle);
                GUI.Label(new Rect(rowRect.x + 12f, rowRect.y + 27f, rowRect.width - 24f, 19f),
                    definition.Description, mutedLabelStyle);
                GUI.Label(new Rect(rowRect.x + 12f, rowRect.y + 48f, rowRect.width - 24f, 19f),
                    "前置：" + definition.RequirementsSummary, mutedLabelStyle);
            }
            GUI.EndScrollView();
        }

        private void DrawMainlineResearchFooter(Rect panelRect, float footerHeight)
        {
            float footerY = panelRect.yMax - footerHeight + 2f;
            int index = Mathf.Clamp(selectedMainlineResearchIndex, 0, MainlineResearch.Length - 1);
            TechnologyResearchDefinition definition = MainlineResearch[index];
            string detail = GetMainlineResearchDetail(index);
            GUI.Label(new Rect(panelRect.x + 18f, footerY, panelRect.width - 36f, 25f), detail, mutedLabelStyle);

            bool canStart = CanStartMainlineResearch(index, out _);
            bool isThisResearchRunning = activeResearchType == ResearchType.Mainline && activeMainlineResearchIndex == index;
            bool guiWasEnabled = GUI.enabled;
            GUI.enabled = guiWasEnabled && canStart;
            if (GUI.Button(new Rect(panelRect.xMax - 142f, footerY + 29f, 124f, 32f),
                isThisResearchRunning ? "研究中" : "开始主线研究", selectedBuildCategoryButtonStyle))
            {
                StartMainlineResearch(index);
            }
            GUI.enabled = guiWasEnabled;
            GUI.Label(new Rect(panelRect.x + 18f, footerY + 31f, panelRect.width - 176f, 30f),
                "预计 " + Mathf.CeilToInt(definition.DurationSeconds) + " 秒 · 随游戏速度推进", mutedLabelStyle);
        }

        private void DrawEfficiencyResearchList(Rect listRect, List<EfficiencyResearchOption> options)
        {
            if (options.Count == 0)
            {
                GUI.Label(new Rect(listRect.x + 18f, listRect.y + 24f, listRect.width - 36f, 100f),
                    "暂无可研究的效率项目。\n先建成设施并推进研究等级：首次校准需 R=L+2，二次校准需 R=L+4。",
                    mutedLabelStyle);
                return;
            }

            const float rowHeight = 62f;
            const float rowSpacing = 68f;
            Rect viewRect = new Rect(0f, 0f, listRect.width - 16f, options.Count * rowSpacing);
            efficiencyResearchScroll = GUI.BeginScrollView(listRect, efficiencyResearchScroll, viewRect);
            for (int i = 0; i < options.Count; i++)
            {
                EfficiencyResearchOption option = options[i];
                Rect rowRect = new Rect(0f, i * rowSpacing, viewRect.width, rowHeight);
                bool selected = string.Equals(option.Key, selectedEfficiencyResearchKey, System.StringComparison.Ordinal);
                if (GUI.Button(rowRect, GUIContent.none, selected ? selectedCardStyle : cardStyle))
                {
                    selectedEfficiencyResearchKey = option.Key;
                }

                string tier = option.Tier == 1 ? "I · +10%" : "II · +15%";
                GUI.Label(new Rect(rowRect.x + 12f, rowRect.y + 5f, rowRect.width - 24f, 21f),
                    option.BuildingName + "效率校准 " + tier, cardLabelStyle);
                GUI.Label(new Rect(rowRect.x + 12f, rowRect.y + 29f, rowRect.width - 24f, 20f),
                    "需研究等级 R" + option.RequiredResearchLevel + " · 对同类型设施生效", mutedLabelStyle);
            }
            GUI.EndScrollView();
        }

        private void DrawEfficiencyResearchFooter(Rect panelRect, float footerHeight,
            List<EfficiencyResearchOption> options)
        {
            float footerY = panelRect.yMax - footerHeight + 2f;
            EfficiencyResearchOption selected = default;
            bool hasSelection = false;
            for (int i = 0; i < options.Count; i++)
            {
                if (string.Equals(options[i].Key, selectedEfficiencyResearchKey, System.StringComparison.Ordinal))
                {
                    selected = options[i];
                    hasSelection = true;
                    break;
                }
            }
            if (!hasSelection && options.Count > 0)
            {
                selected = options[0];
                selectedEfficiencyResearchKey = selected.Key;
                hasSelection = true;
            }

            string detail = hasSelection
                ? selected.BuildingName + " · 校准 " + (selected.Tier == 1 ? "I (+10%)" : "II (+15%)")
                : "设施必须建成，且研究等级达到对应门槛。";
            GUI.Label(new Rect(panelRect.x + 18f, footerY, panelRect.width - 36f, 25f), detail, mutedLabelStyle);
            bool canStart = hasSelection && activeResearchType == ResearchType.None;
            bool selectedIsRunning = hasSelection && activeResearchType == ResearchType.Efficiency &&
                string.Equals(activeEfficiencyResearchKey, selected.Key, System.StringComparison.Ordinal);
            bool guiWasEnabled = GUI.enabled;
            GUI.enabled = guiWasEnabled && canStart;
            if (GUI.Button(new Rect(panelRect.xMax - 142f, footerY + 29f, 124f, 32f),
                selectedIsRunning ? "研究中" : "开始效率研究", selectedBuildCategoryButtonStyle))
            {
                StartEfficiencyResearch(selected.AssetName, selected.Tier);
            }
            GUI.enabled = guiWasEnabled;
            GUI.Label(new Rect(panelRect.x + 18f, footerY + 31f, panelRect.width - 176f, 30f),
                "完成后效率加成按基础值累加", mutedLabelStyle);
        }

        private bool CanStartMainlineResearch(int index, out string reason)
        {
            if (index < 0 || index >= MainlineResearch.Length)
            {
                reason = "研究课题不存在。";
                return false;
            }
            if (activeResearchType != ResearchType.None)
            {
                reason = "研究站正在进行其他课题。";
                return false;
            }

            TechnologyResearchDefinition definition = MainlineResearch[index];
            if (definition.Level <= researchLevel)
            {
                reason = "该课题已经完成。";
                return false;
            }
            if (definition.Level != researchLevel + 1)
            {
                reason = "请先完成 R" + (researchLevel + 1) + " 主线研究。";
                return false;
            }

            if (!completedBuildableAssets.Contains("ResearchStation"))
            {
                reason = "尚未建成：研究站";
                return false;
            }
            for (int i = 0; i < definition.RequiredAssets.Length; i++)
            {
                string requiredAsset = definition.RequiredAssets[i];
                if (!completedBuildableAssets.Contains(requiredAsset))
                {
                    reason = "尚未建成：" + GetBuildableDisplayName(requiredAsset);
                    return false;
                }
            }

            reason = string.Empty;
            return true;
        }

        private string GetMainlineResearchState(int index)
        {
            TechnologyResearchDefinition definition = MainlineResearch[index];
            if (definition.Level <= researchLevel) return "已完成";
            if (activeResearchType == ResearchType.Mainline && activeMainlineResearchIndex == index) return "研究中";
            if (definition.Level != researchLevel + 1) return "未开放";
            return CanStartMainlineResearch(index, out _) ? "可研究" : "待建成";
        }

        private string GetMainlineResearchDetail(int index)
        {
            if (activeResearchType == ResearchType.Mainline && activeMainlineResearchIndex == index)
            {
                return "研究进行中：" + Mathf.CeilToInt(Mathf.Max(0f,
                    activeResearchDurationSeconds - activeResearchProgressSeconds)) + " 秒剩余";
            }

            if (!CanStartMainlineResearch(index, out string reason)) return reason;
            return "完成后开放 L" + MainlineResearch[index].Level + " 建筑";
        }

        private static string GetBuildableDisplayName(string assetName)
        {
            for (int i = 0; i < Buildables.Length; i++)
            {
                if (string.Equals(Buildables[i].AssetName, assetName, System.StringComparison.Ordinal))
                {
                    return Buildables[i].Name;
                }
            }
            return assetName;
        }

        private void StartMainlineResearch(int index)
        {
            if (!CanStartMainlineResearch(index, out string reason))
            {
                statusMessage = reason;
                return;
            }
            activeResearchType = ResearchType.Mainline;
            activeMainlineResearchIndex = index;
            activeResearchDurationSeconds = MainlineResearch[index].DurationSeconds;
            activeResearchProgressSeconds = 0f;
            statusMessage = "开始研究 R" + MainlineResearch[index].Level + "：" + MainlineResearch[index].Name + "。";
        }

        private List<EfficiencyResearchOption> GetAvailableEfficiencyResearchOptions()
        {
            List<EfficiencyResearchOption> options = new List<EfficiencyResearchOption>();
            for (int i = 0; i < Buildables.Length; i++)
            {
                BuildableDefinition definition = Buildables[i];
                if (definition.Kind == BuildableKind.Road ||
                    !completedBuildableAssets.Contains(definition.AssetName))
                {
                    continue;
                }

                if (CanResearchEfficiency(definition, 1))
                {
                    options.Add(new EfficiencyResearchOption(definition.AssetName, definition.Name, 1,
                        definition.ScenarioLevel + 2));
                }
                else if (CanResearchEfficiency(definition, 2))
                {
                    options.Add(new EfficiencyResearchOption(definition.AssetName, definition.Name, 2,
                        definition.ScenarioLevel + 4));
                }
            }
            return options;
        }

        private bool CanResearchEfficiency(BuildableDefinition definition, int tier)
        {
            if (definition == null || tier < 1 || tier > 2 ||
                !completedBuildableAssets.Contains(definition.AssetName)) return false;
            string key = GetEfficiencyResearchKey(definition.AssetName, tier);
            if (researchedEfficiencyKeys.Contains(key)) return false;
            if (tier == 2 && !researchedEfficiencyKeys.Contains(GetEfficiencyResearchKey(definition.AssetName, 1)))
                return false;
            int requiredLevel = definition.ScenarioLevel + (tier == 1 ? 2 : 4);
            return researchLevel >= requiredLevel;
        }

        private void StartEfficiencyResearch(string assetName, int tier)
        {
            BuildableDefinition definition = FindBuildable(assetName);
            if (activeResearchType != ResearchType.None || !CanResearchEfficiency(definition, tier))
            {
                statusMessage = "该效率课题尚未满足研究条件。";
                return;
            }
            activeResearchType = ResearchType.Efficiency;
            activeEfficiencyResearchKey = GetEfficiencyResearchKey(assetName, tier);
            activeEfficiencyAssetName = assetName;
            activeEfficiencyTier = tier;
            activeMainlineResearchIndex = -1;
            activeResearchDurationSeconds = 36f;
            activeResearchProgressSeconds = 0f;
            statusMessage = "开始研究" + definition.Name + "的效率校准。";
        }

        private void UpdateTechnologyResearch()
        {
            if (activeResearchType == ResearchType.None) return;
            float speed = weatherSystem != null ? Mathf.Max(0f, weatherSystem.SimulationSpeed) : 1f;
            activeResearchProgressSeconds += Time.deltaTime * speed;
            if (activeResearchProgressSeconds >= activeResearchDurationSeconds)
            {
                CompleteActiveResearch();
            }
        }

        private void CompleteActiveResearch()
        {
            if (activeResearchType == ResearchType.Mainline && activeMainlineResearchIndex >= 0)
            {
                TechnologyResearchDefinition definition = MainlineResearch[activeMainlineResearchIndex];
                researchLevel = Mathf.Max(researchLevel, definition.Level);
                selectedMainlineResearchIndex = Mathf.Min(activeMainlineResearchIndex + 1, MainlineResearch.Length - 1);
                statusMessage = "R" + definition.Level + "研究完成，已开放 L" + Mathf.Min(researchLevel, 5) + " 建筑。";
            }
            else if (activeResearchType == ResearchType.Efficiency && !string.IsNullOrEmpty(activeEfficiencyResearchKey))
            {
                researchedEfficiencyKeys.Add(activeEfficiencyResearchKey);
                BuildableDefinition definition = FindBuildable(activeEfficiencyAssetName);
                statusMessage = (definition != null ? definition.Name : activeEfficiencyAssetName) +
                    "效率校准完成，效率提升 " + (activeEfficiencyTier == 1 ? "10%" : "15%") + "。";
            }

            activeResearchType = ResearchType.None;
            activeMainlineResearchIndex = -1;
            activeEfficiencyResearchKey = string.Empty;
            activeEfficiencyAssetName = string.Empty;
            activeEfficiencyTier = 0;
            activeResearchProgressSeconds = 0f;
            activeResearchDurationSeconds = 0f;
        }

        private string GetActiveResearchName()
        {
            if (activeResearchType == ResearchType.Mainline && activeMainlineResearchIndex >= 0)
            {
                TechnologyResearchDefinition definition = MainlineResearch[activeMainlineResearchIndex];
                return "R" + definition.Level + " " + definition.Name;
            }
            if (activeResearchType == ResearchType.Efficiency)
            {
                BuildableDefinition definition = FindBuildable(activeEfficiencyAssetName);
                return (definition != null ? definition.Name : activeEfficiencyAssetName) + "效率校准";
            }
            return string.Empty;
        }

        private BuildableDefinition FindBuildable(string assetName)
        {
            for (int i = 0; i < Buildables.Length; i++)
            {
                if (string.Equals(Buildables[i].AssetName, assetName, System.StringComparison.Ordinal))
                    return Buildables[i];
            }
            return null;
        }

        private static string GetEfficiencyResearchKey(string assetName, int tier)
        {
            return assetName + "|Efficiency|" + tier;
        }

        public float GetBuildingEfficiencyMultiplier(string assetName)
        {
            for (int i = 0; i < Buildables.Length; i++)
            {
                bool matches = string.Equals(Buildables[i].AssetName, assetName, System.StringComparison.Ordinal);
                if (!matches && BuildingConstructionCatalog.TryGet(assetName,
                    out BuildingConstructionCatalog.Entry requested) &&
                    BuildingConstructionCatalog.TryGet(Buildables[i].AssetName,
                        out BuildingConstructionCatalog.Entry candidate))
                {
                    matches = string.Equals(requested.key, candidate.key, System.StringComparison.Ordinal);
                }
                if (matches)
                {
                    assetName = Buildables[i].AssetName;
                    break;
                }
            }

            float multiplier = 1f;
            if (researchedEfficiencyKeys.Contains(GetEfficiencyResearchKey(assetName, 1))) multiplier += 0.10f;
            if (researchedEfficiencyKeys.Contains(GetEfficiencyResearchKey(assetName, 2))) multiplier += 0.15f;
            return multiplier;
        }

        private void DrawBuildCard(int index, Rect cardRect)
        {
            BuildableDefinition definition = Buildables[index];
            GUIStyle style = index == selectedBuildableIndex ? selectedBuildCardStyle : buildCardStyle;
            HudTheme.DrawCard(cardRect, index == selectedBuildableIndex, cardRect.Contains(Event.current.mousePosition));

            Texture2D icon = buildIcons != null && index < buildIcons.Length ? buildIcons[index] : null;
            float iconFrameSize = 90f;
            Rect iconFrameRect = new Rect(cardRect.center.x - iconFrameSize*.5f,
                cardRect.y + 8f,
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
                    : definition.Width + "×" + definition.Depth +
                      (definition.Kind == BuildableKind.Water ? " 格水面" : " 格占地");
            GUI.Label(new Rect(cardRect.x + 12f, cardRect.y + 103f, cardRect.width - 24f, 22f), definition.Name, cardLabelStyle);
            string stage = definition.ScenarioLevel >= 0 ? " · 阶段 " + definition.ScenarioLevel : string.Empty;
            GUI.Label(new Rect(cardRect.x + 12f, cardRect.y + 128f, cardRect.width - 24f, 30f),
                footprint + "  ·  木材 " + definition.WoodCost, mutedLabelStyle);

            if (GUI.Button(cardRect, GUIContent.none, transparentButtonStyle))
            {
                SelectBuildable(index);
            }
        }

        private static void DrawBuildIconFrame(Rect rect, bool selected)
        {
            Color previousColor = GUI.color;
            GUI.color = Color.white;
            GUI.DrawTexture(rect, selected ? HudTheme.Selected : HudTheme.Card);
            if (selected)
            {
                GUI.color = HudTheme.Accent;
                GUI.DrawTexture(new Rect(rect.x+8,rect.yMax-2,rect.width-16,2),Texture2D.whiteTexture);
            }
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
            // A small emissive contribution keeps valid/invalid placement
            // colors legible in night shadows without brightening the map.
            if (material.HasProperty("_EmissionColor"))
            {
                material.EnableKeyword("_EMISSION");
                material.SetColor("_EmissionColor", new Color(color.r, color.g, color.b, 1f) * 0.18f);
            }
            material.SetOverrideTag("RenderType", "Transparent");
            material.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha);
            material.SetInt("_DstBlend", (int)BlendMode.OneMinusSrcAlpha);
            material.SetInt("_ZWrite", 1);
            material.SetInt("_ZTest", (int)CompareFunction.LessEqual);
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
            FloodwaterAppearance.DisableSceneOceans(mapRoot);
            GameObject water = new GameObject("Floodwater | irregular swells and rocky surf");
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
            waterMaterial.name = "Floodwater - Irregular Swells, Sky Glints and Rocky Surf";
            if (waterMaterial.HasProperty("_DeepColor"))
            {
                FloodwaterAppearance.Configure(waterMaterial);
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
                    objectName == LegacyIslandModelName || objectName == IslandResourceName ||
                    objectName == "Capsized Wreck - Gate26 East Shore")
                {
                    sceneTransforms[i].gameObject.SetActive(false);
                }
            }

            GameObject expandedMain = Resources.Load<GameObject>("Models/Environment/Island_Main_Expanded");
            GameObject expandedWest = Resources.Load<GameObject>("Models/Environment/Island_West_Expanded");
            GameObject expandedEast = Resources.Load<GameObject>("Models/Environment/Island_East_Expanded");
            usingExpandedArchipelago = expandedMain != null && expandedWest != null && expandedEast != null;
            if (!usingExpandedArchipelago)
            {
                Debug.LogError("扩展群岛资源不完整。请确认 Resources/Models/Environment/Island_Main_Expanded、Island_West_Expanded 和 Island_East_Expanded 均已导入。");
                return;
            }

            GameObject island = InstantiateIslandResource(expandedMain, IslandRootName);
            islandRoot = island.transform;
            TripoIslandAssets.Apply(island);
            EnsureIslandMaterials(island);
            bool mainBoundsFound = false;
            foreach (MeshFilter mesh in island.GetComponentsInChildren<MeshFilter>())
            {
                if (!IsIslandTerrainMesh(mesh)) continue;
                Bounds bounds = mesh.GetComponent<Renderer>().bounds;
                if (!mainBoundsFound) { mainIslandFramingBounds = bounds; mainBoundsFound = true; }
                else mainIslandFramingBounds.Encapsulate(bounds);
            }
            AddBasinTwinIslands();
            MixIslandTreeTypes(islandRoot);
            RefreshIslandVisibleBounds();
            Collider[] importedColliders = island.GetComponentsInChildren<Collider>(true);
            for (int i = 0; i < importedColliders.Length; i++)
            {
                importedColliders[i].enabled = false;
            }

            // The playable surface includes the main island and both Gate26
            // satellites. They share one map-space grid and placement raycast.
            MeshFilter[] importedMeshes = islandRoot.GetComponentsInChildren<MeshFilter>(true);
            List<MeshFilter> terrainMeshes = new List<MeshFilter>();
            for (int i = 0; i < importedMeshes.Length; i++)
            {
                MeshFilter filter = importedMeshes[i];
                if (filter.sharedMesh != null && IsIslandTerrainMesh(filter))
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
            List<MeshCollider> satelliteSurfaces = new List<MeshCollider>();
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
                if (satelliteIslandsRoot != null && filter.transform.IsChildOf(satelliteIslandsRoot))
                {
                    satelliteSurfaces.Add(collider);
                }

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
            constructionGrid = new IslandConstructionGrid(mapRoot, islandLandColliders, localBounds, WaterPlaneHeight,
                satelliteSurfaces.ToArray());
            AddCapsizedWreck();
            // In Anno 1800 style, open plains stay clean and flat; dense foliage clusters are placed by TripoVegetationAssets.
            if (grassCover != null) Destroy(grassCover);
            Debug.Log($"Construction grid covers all {islandLandColliders.Length} island terrain surfaces " +
                      $"({constructionGrid.Width} × {constructionGrid.Depth} map cells).");
        }

        private static void MixIslandTreeTypes(Transform root)
        {
            // Use the original tree assets rather than the later reconstructed crowns.
            string[] names = { "Broadleaf_Coastal_A", "Broadleaf_Coastal_B", "Pine_Windbent_Tall_A", "Pine_Windbent_Short_B" };
            var prefabs = new GameObject[names.Length];
            for (int i = 0; i < names.Length; i++) prefabs[i] = Resources.Load<GameObject>("Models/Nature/" + names[i]);
            MeshRenderer[] originals = root.GetComponentsInChildren<MeshRenderer>(true);
            int index = 0;
            foreach (MeshRenderer original in originals)
            {
                string name = original.name.ToLowerInvariant();
                if (!original.enabled || (!name.Contains("broadleaf") && !name.Contains("pine_"))) continue;
                int current = index++;
                int kind = name.Contains("pine_") || current % 3 == 0 ? 2 + current % 2 : current % 2;
                if (prefabs[kind] == null) continue;
                Bounds target = original.bounds;
                GameObject tree = Instantiate(prefabs[kind], root, false);
                tree.name = (kind >= 2 ? "Pine_Variety_" : "Broadleaf_Variety_") + current;
                Renderer[] parts = tree.GetComponentsInChildren<Renderer>();
                if (parts.Length == 0) { Destroy(tree); continue; }
                foreach (Renderer part in parts)
                    if (part.gameObject != tree) part.name = tree.name + "_" + part.name;
                Bounds bounds = parts[0].bounds;
                foreach (Renderer part in parts) bounds.Encapsulate(part.bounds);
                if (bounds.size.y < .001f) { Destroy(tree); continue; }
                tree.transform.localScale *= target.size.y / bounds.size.y;
                bounds = parts[0].bounds;
                foreach (Renderer part in parts) bounds.Encapsulate(part.bounds);
                tree.transform.position += new Vector3(target.center.x - bounds.center.x,
                    target.min.y - bounds.min.y, target.center.z - bounds.center.z);
                original.enabled = false;
            }
        }

        private void AddBasinTwinIslands()
        {
            if (!usingExpandedArchipelago)
            {
                Debug.LogError("无法载入副岛：扩展群岛模型未完整载入。");
                return;
            }

            satelliteIslandsRoot = new GameObject("Expanded satellite islands | separate models").transform;
            satelliteIslandsRoot.SetParent(islandRoot, false);
            foreach (string side in new[] { "West", "East" })
            {
                GameObject prefab = Resources.Load<GameObject>("Models/Environment/Island_" + side + "_Expanded");
                if (prefab == null)
                {
                    Debug.LogError("缺少扩展副岛模型：Island_" + side + "_Expanded。");
                    continue;
                }
                GameObject model = Instantiate(prefab, satelliteIslandsRoot, false);
                model.name = "Expanded " + side + " Island";
                TripoIslandAssets.ApplyRockySatellite(model, side == "East");
                EnsureIslandMaterials(model);
            }
        }

        private void AddCapsizedWreck()
        {
            var tripoWreck = TripoIslandAssets.AddShipwreck(satelliteIslandsRoot);
            if (tripoWreck != null)
            {
                ClearVegetationFromWreckFootprint(tripoWreck.GetComponentsInChildren<Renderer>());
                return;
            }
            Debug.LogWarning("Tripo 沉船资源缺失；副岛仍正常载入。请确认 Resources/Models/Environment/Tripo/Shipwreck/Shipwreck 已导入。");
        }

        private int ClearVegetationFromWreckFootprint(Renderer[] wreckRenderers)
        {
            if (satelliteIslandsRoot == null || wreckRenderers == null)
            {
                return 0;
            }

            Bounds footprint = default;
            bool hasFootprint = false;
            for (int i = 0; i < wreckRenderers.Length; i++)
            {
                Renderer renderer = wreckRenderers[i];
                if (renderer == null || !renderer.enabled)
                {
                    continue;
                }

                string objectName = renderer.gameObject.name;
                if (!objectName.StartsWith("Wreck_", System.StringComparison.OrdinalIgnoreCase) &&
                    !objectName.StartsWith("Debris_", System.StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

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

            if (!hasFootprint)
            {
                return 0;
            }

            // Keep nearby leaves and grass tufts off the hull and impact debris.
            const float clearance = 0.85f;
            footprint.Expand(new Vector3(clearance * 2f, 0f, clearance * 2f));
            Renderer[] environmentRenderers = satelliteIslandsRoot.GetComponentsInChildren<Renderer>(true);
            int hiddenCount = 0;
            for (int i = 0; i < environmentRenderers.Length; i++)
            {
                Renderer vegetation = environmentRenderers[i];
                if (vegetation == null || !vegetation.enabled || !IsWreckSiteVegetation(vegetation.gameObject.name))
                {
                    continue;
                }

                Bounds bounds = vegetation.bounds;
                bool intersectsFootprint = bounds.max.x >= footprint.min.x && bounds.min.x <= footprint.max.x &&
                    bounds.max.z >= footprint.min.z && bounds.min.z <= footprint.max.z;
                if (!intersectsFootprint)
                {
                    continue;
                }

                vegetation.enabled = false;
                hiddenCount++;
            }

            return hiddenCount;
        }

        private static bool IsWreckSiteVegetation(string objectName)
        {
            if (string.IsNullOrEmpty(objectName)) return false;
            string name = objectName.ToLowerInvariant();
            // These material batches were cleared component by component during export.
            if (name.StartsWith("grounded detail |")) return false;
            return name.Contains("tree") || name.Contains("pine") || name.Contains("broadleaf") ||
                name.Contains("grass") || name.Contains("shrub") || name.Contains("fern") ||
                name.Contains("wildflower") || name.Contains("flower") || name.Contains("foliage") ||
                name.Contains("reed");
        }

        private void RefreshIslandVisibleBounds()
        {
            hasIslandVisibleBounds = false;
            if (islandRoot == null) return;

            Renderer[] renderers = islandRoot.GetComponentsInChildren<Renderer>(true);
            for (int i = 0; i < renderers.Length; i++)
            {
                Renderer renderer = renderers[i];
                if (renderer == null || !renderer.enabled || renderer.bounds.max.y <= WaterPlaneHeight)
                {
                    continue;
                }

                Bounds bounds = renderer.bounds;
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
            constructionGrid?.SetCoastDistanceField(encodedDistance, resolution,
                new Vector2(minX, minZ), new Vector2(worldWidth, worldDepth), distanceRange);

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
            Texture2D grassAlbedo = Resources.Load<Texture2D>(
                "Textures/Environment/Grass_Surface_Albedo_Concept");
            if (grassAlbedo != null && terrainPaint.HasProperty("_BaseMap"))
                terrainPaint.SetTexture("_BaseMap", grassAlbedo);
            if (terrainPaint.HasProperty("_TextureWeight"))
                terrainPaint.SetFloat("_TextureWeight", grassAlbedo != null ? 0.10f : 0.0f);
            terrainPaint.SetFloat("_LandscapeBlend", 1f);
            terrainPaint.SetFloat("_SeaLevel", WaterPlaneHeight);
            terrainPaint.SetColor("_GrassTint", new Color(0.19f, 0.28f, 0.10f));
            terrainPaint.SetColor("_SoilTint", new Color(0.25f, 0.21f, 0.12f));
            terrainPaint.SetColor("_RockTint", new Color(0.33f, 0.34f, 0.30f));
            terrainPaint.SetColor("_SandTint", new Color(0.49f, 0.43f, 0.29f));
            TerrainSurfaceLibrary.Configure(terrainPaint);

            Material basinWater = null;
            Dictionary<Material, Material> convertedMaterials = new Dictionary<Material, Material>();
            Material earthFallback = null;
            Material rockFallback = null;
            Material springRock = null;
            Renderer[] renderers = island.GetComponentsInChildren<Renderer>(true);
            for (int rendererIndex = 0; rendererIndex < renderers.Length; rendererIndex++)
            {
                Renderer renderer = renderers[rendererIndex];
                if (renderer.name.StartsWith("Tripo_", System.StringComparison.Ordinal)) continue;
                if (renderer.name.IndexOf("Mountain spring weathered rock", System.StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    if (springRock == null)
                    {
                        springRock = MakeMaterial(new Color(.15f, .18f, .16f));
                        springRock.name = "Mountain spring | dark weathered rock";
                        if (springRock.HasProperty("_Smoothness")) springRock.SetFloat("_Smoothness", .08f);
                    }
                    Material[] rocks = renderer.sharedMaterials;
                    if (rocks.Length == 0) rocks = new Material[1];
                    for (int j = 0; j < rocks.Length; j++) rocks[j] = springRock;
                    renderer.sharedMaterials = rocks;
                    continue;
                }
                if (IsIslandTerrainRenderer(renderer))
                {
                    MeshFilter filter = renderer.GetComponent<MeshFilter>();
                    int materialCount = filter != null && filter.sharedMesh != null
                        ? Mathf.Max(1, filter.sharedMesh.subMeshCount)
                        : Mathf.Max(1, renderer.sharedMaterials.Length);
                    Material[] terrainMaterials = new Material[materialCount];
                    for (int materialIndex = 0; materialIndex < terrainMaterials.Length; materialIndex++)
                    {
                        terrainMaterials[materialIndex] = terrainPaint;
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
            if (renderer == null) return false;
            if (renderer.sharedMaterial != null && renderer.sharedMaterial.shader != null &&
                renderer.sharedMaterial.shader.name == "LastLandfall/Tripo Fresh Water")
                return false;
            return renderer.name.IndexOf("Basin_", System.StringComparison.OrdinalIgnoreCase) >= 0 &&
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
            Material mainIslandMaterial = CreateConstructionGridMaterial(shader,
                IslandConstructionGrid.BuildingSlopeLimit);
            Material satelliteIslandMaterial = CreateConstructionGridMaterial(shader,
                IslandConstructionGrid.SatelliteBuildingSlopeLimit);
            List<Renderer> overlays = new List<Renderer>();
            foreach (MeshFilter source in islandTerrainMeshes)
            {
                if (source.sharedMesh == null) continue;
                bool isSatellite = satelliteIslandsRoot != null && source.transform.IsChildOf(satelliteIslandsRoot);
                Material material = isSatellite ? satelliteIslandMaterial : mainIslandMaterial;
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
            Shader coastalShader = Shader.Find("LastLandfall/Coastal Construction Grid");
            if (coastalShader != null && coastDistanceTexture != null)
            {
                Material coastal = new Material(coastalShader);
                ownedMaterials.Add(coastal);
                coastal.SetTexture("_CoastDistanceTex", coastDistanceTexture);
                coastal.SetVector("_CoastWorldMin", waterMaterial.GetVector("_CoastWorldMin"));
                coastal.SetVector("_CoastWorldSize", waterMaterial.GetVector("_CoastWorldSize"));
                coastal.SetFloat("_CoastDistanceRange", waterMaterial.GetFloat("_CoastDistanceRange"));
                coastal.SetMatrix("_WorldToGrid", mapRoot.worldToLocalMatrix);
                GameObject oceanGrid = GameObject.CreatePrimitive(PrimitiveType.Quad);
                oceanGrid.name = "Construction Grid | continuous coastal water";
                oceanGrid.transform.SetParent(mapRoot, false);
                oceanGrid.transform.localPosition = new Vector3(constructionGrid.OriginX + constructionGrid.Width * .5f,
                    WaterPlaneHeight + .04f, constructionGrid.OriginZ + constructionGrid.Depth * .5f);
                oceanGrid.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
                oceanGrid.transform.localScale = new Vector3(constructionGrid.Width, constructionGrid.Depth, 1f);
                Collider gridCollider = oceanGrid.GetComponent<Collider>();
                gridCollider.enabled = false;
                if (Application.isPlaying) Destroy(gridCollider);
                else DestroyImmediate(gridCollider);
                coastalGridRenderer = oceanGrid.GetComponent<Renderer>();
                coastalGridRenderer.sharedMaterial = coastal;
                coastalGridRenderer.shadowCastingMode = ShadowCastingMode.Off;
                coastalGridRenderer.receiveShadows = false;
                coastalGridRenderer.enabled = false;
                overlays.Add(coastalGridRenderer);
            }
            gridOverlayRenderers = overlays.ToArray();
        }

        private Material CreateConstructionGridMaterial(Shader shader, float slopeLimit)
        {
            Material material = new Material(shader);
            material.name = "Island Construction Grid | " + slopeLimit.ToString("F0") + "°";
            ownedMaterials.Add(material);
            material.SetMatrix("_WorldToGrid", mapRoot.worldToLocalMatrix);
            material.SetFloat("_SeaLevel", WaterPlaneHeight);
            if (coastDistanceTexture != null && waterMaterial != null)
            {
                material.SetTexture("_CoastDistanceTex", coastDistanceTexture);
                material.SetVector("_CoastWorldMin", waterMaterial.GetVector("_CoastWorldMin"));
                material.SetVector("_CoastWorldSize", waterMaterial.GetVector("_CoastWorldSize"));
                material.SetFloat("_CoastDistanceRange", waterMaterial.GetFloat("_CoastDistanceRange"));
            }
            material.SetFloat("_BuildingSlopeCos", Mathf.Cos(slopeLimit * Mathf.Deg2Rad));
            return material;
        }

        private void SetBuildGridVisibility(bool visible)
        {
            if (gridOverlayRenderers == null) return;
            foreach (Renderer renderer in gridOverlayRenderers)
                if (renderer != null)
                {
                    bool waterSelection = selectedBuildableIndex >= 0 &&
                        (Buildables[selectedBuildableIndex].Kind == BuildableKind.Water ||
                         Buildables[selectedBuildableIndex].Kind == BuildableKind.Dock);
                    if (renderer != coastalGridRenderer)
                        foreach (Material gridMaterial in renderer.sharedMaterials)
                        {
                            gridMaterial.SetFloat("_CoastalOnly", waterSelection ? 1f : 0f);
                            gridMaterial.SetFloat("_HeightBandEnabled", hasHoveredCell && selectedBuildableIndex >= 0 ? 1f : 0f);
                            gridMaterial.SetFloat("_PlacementHeight", hasHoveredCell ? constructionGrid.GetTerrain(hoveredCell).MaximumHeight : WaterPlaneHeight);
                        }
                    renderer.enabled = visible && (renderer != coastalGridRenderer || waterSelection);
                }
        }

        public void SetBuildGridPreference(bool visible)
        {
            isBuildGridVisible = visible;
            SetBuildGridVisibility(isBuildGridVisible && IsBuildingContextActive);
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
            if (index < 0 || index >= Buildables.Length || !IsBuildableUnlocked(Buildables[index]))
            {
                return;
            }

            selectedBuildableIndex = index;
            rotationDegrees = 0;
            dockManualRotation = false;
            hasLastRoadCell = false;
            BuildableDefinition definition = Buildables[index];
            statusMessage = definition.Name + "已选中。";
            hoverMessage = string.Empty;
        }

        private void RotateSelectedBuilding(int direction)
        {
            if (selectedBuildableIndex < 0 ||
                (Buildables[selectedBuildableIndex].Kind != BuildableKind.Building &&
                 Buildables[selectedBuildableIndex].Kind != BuildableKind.Water &&
                 Buildables[selectedBuildableIndex].Kind != BuildableKind.Dock))
            {
                return;
            }

            if (Buildables[selectedBuildableIndex].Kind == BuildableKind.Dock && !dockManualRotation &&
                TryFindDockDirection(hoveredCell, out Vector2Int currentDockDirection))
                rotationDegrees = GetRotationAligning(South, currentDockDirection);
            dockManualRotation = true;
            rotationDegrees = (rotationDegrees + direction + 360) % 360;
            statusMessage = "建筑方向已旋转 " + rotationDegrees + "°。";
        }

        private GameObject CreatePlaceableObject(string assetName, string objectName)
        {
            GameObject root = new GameObject(objectName);
            string resourcePath = BuildingConstructionCatalog.TryGet(assetName, out BuildingConstructionCatalog.Entry entry)
                ? entry.finalResource : GetModelResourcePath(assetName);
            bool tripoDock = assetName == "RescueDock" || assetName == "RescueDock";
            GameObject prefab = tripoDock ? Resources.Load<GameObject>("Models/Infrastructure/Tripo/RescueDock/TripoRescueDock") : null;
            bool hasTripoDock = prefab != null;
            if (prefab == null) prefab = Resources.Load<GameObject>(resourcePath);
            if (prefab != null)
            {
                GameObject model = Instantiate(prefab, root.transform, false);
                model.name = assetName + " Model";
                if (hasTripoDock)
                {
                    model.transform.localRotation = Quaternion.Euler(0f, 180f, 0f) * model.transform.localRotation;
                    Material dockMaterial = MakeMaterial(Color.white);
                    dockMaterial.mainTexture = Resources.Load<Texture2D>("Models/Infrastructure/Tripo/RescueDock/TripoRescueDock_BaseColor");
                    foreach (Renderer part in model.GetComponentsInChildren<Renderer>()) part.sharedMaterial = dockMaterial;
                }
                if (assetName.StartsWith("Road") || assetName.StartsWith("DirtRoad"))
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
            string category = assetName == "IslandReference_V2" || assetName == IslandResourceName
                ? "Environment"
                : assetName.StartsWith("RescueDock") || assetName.StartsWith("Road") ||
                  assetName.StartsWith("DirtRoad") || assetName.StartsWith("FishingDock") ||
                  assetName.StartsWith("DriftwoodCollectionBoom") || assetName.StartsWith("WeatherTideBuoy") ||
                  assetName.StartsWith("Shipyard")
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
            if (constructionGrid.TryRaycast(ray, out RaycastHit hit) &&
                mapRoot.InverseTransformPoint(hit.point).y > WaterPlaneHeight + 0.002f)
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
            if (hasHoveredCell && selectedBuildableIndex >= 0 &&
                Buildables[selectedBuildableIndex].Kind == BuildableKind.Dock && currentToolMode == BuildToolMode.Place)
            {
                Vector2Int raw = hoveredCell;
                bool snapped = false;
                for (int radius = 0; radius <= 4 && !snapped; radius++)
                    for (int dx = -radius; dx <= radius && !snapped; dx++)
                        for (int dz = -radius; dz <= radius && !snapped; dz++)
                        {
                            if (Mathf.Max(Mathf.Abs(dx), Mathf.Abs(dz)) != radius) continue;
                            Vector2Int candidate = raw + new Vector2Int(dx, dz);
                            if (TryFindDockDirection(candidate, out _)) { hoveredCell = candidate; snapped = true; }
                        }
            }
        }

        private void UpdatePreview()
        {
            if (currentToolMode == BuildToolMode.Demolish)
            {
                SetBuildGridVisibility(true);
                if (previewObject != null) previewObject.SetActive(false);
                if (hasHoveredCell)
                {
                    if (cellToPlacedBuilding.TryGetValue(hoveredCell, out PlacedBuildingData target) && target != null)
                    {
                        hoverMessage = "【拆除】" + target.Definition.Name + " · 点击拆除并返还 " + Mathf.Max(1, target.WoodCost / 2) + " 木材";
                    }
                    else if (roadCells.Contains(hoveredCell))
                    {
                        hoverMessage = "【拆除】道路 · 点击拆除并返还 2 木材";
                    }
                    else
                    {
                        hoverMessage = "【拆除模式】点击建筑或道路拆除 (返还50%木材)，右键退出";
                    }
                }
                else
                {
                    hoverMessage = "【拆除模式】移动鼠标至地格上选择目标";
                }
                return;
            }

            if (currentToolMode == BuildToolMode.Move && !isMovingBuilding)
            {
                SetBuildGridVisibility(true);
                if (previewObject != null) previewObject.SetActive(false);
                if (hasHoveredCell)
                {
                    if (cellToPlacedBuilding.TryGetValue(hoveredCell, out PlacedBuildingData target) && target != null)
                    {
                        hoverMessage = "【移动】点击拾起 " + target.Definition.Name + " 进行重新布局";
                    }
                    else
                    {
                        hoverMessage = "【移动模式】点击想要移动的建筑，右键退出";
                    }
                }
                else
                {
                    hoverMessage = "【移动模式】移动鼠标至建筑上方";
                }
                return;
            }

            if (selectedBuildableIndex < 0 || !IsBuildableUnlocked(Buildables[selectedBuildableIndex]) || !hasHoveredCell)
            {
                SetBuildGridVisibility(isBuildGridVisible && IsBuildingContextActive);
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
            else if (selected.Kind == BuildableKind.Water)
            {
                canPlace = CanPlaceWater(hoveredCell, selected, out reason);
            }
            else
            {
                canPlace = CanPlaceBuilding(hoveredCell, selected, out reason);
            }

            EnsurePreviewObject(assetName);
            previewObject.transform.SetLocalPositionAndRotation(
                GetObjectCenter(hoveredCell, selected),
                Quaternion.Euler(0f, previewRotation, 0f));
            if (selected.Kind == BuildableKind.Dock)
            {
                UpdateDockAccess(previewObject, hoveredCell);
                previewRenderers = previewObject.GetComponentsInChildren<Renderer>();
            }
            previewObject.SetActive(true);
            if (selected.Kind == BuildableKind.Dock)
            {
                if (dockValidPreviewMaterial == null) dockValidPreviewMaterial = MakeMaterial(new Color(.25f, .9f, .55f, 1f));
                if (dockInvalidPreviewMaterial == null) dockInvalidPreviewMaterial = MakeMaterial(new Color(.95f, .24f, .2f, 1f));
                SetPreviewMaterial(canPlace ? dockValidPreviewMaterial : dockInvalidPreviewMaterial);
            }
            else SetPreviewMaterial(canPlace ? validPreviewMaterial : invalidPreviewMaterial);
            SetBuildGridVisibility(isBuildGridVisible && IsBuildingContextActive);

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

            if (AvailableWood < definition.WoodCost)
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

            if (AvailableWood < definition.WoodCost)
            {
                reason = "木材不足，需要 " + definition.WoodCost + "。";
                return false;
            }

            reason = string.Empty;
            return true;
        }

        private void GetWaterFootprint(BuildableDefinition definition, out int width, out int depth)
        {
            bool turned = rotationDegrees % 180 != 0;
            width = turned ? definition.Depth : definition.Width;
            depth = turned ? definition.Width : definition.Depth;
        }

        private bool CanPlaceWater(Vector2Int anchor, BuildableDefinition definition, out string reason)
        {
            if (constructionGrid == null)
            {
                reason = "水面建造区域尚未载入。";
                return false;
            }

            GetWaterFootprint(definition, out int width, out int depth);
            for (int x = 0; x < width; x++)
            for (int z = 0; z < depth; z++)
            {
                Vector2Int cell = anchor + new Vector2Int(x, z);
                if (!constructionGrid.IsCoastalWaterCell(cell))
                {
                    reason = definition.Name + "需要距岸 24 米内完整、连续的水面。";
                    return false;
                }
                if (occupiedCells.Contains(cell) || roadCells.Contains(cell))
                {
                    reason = "这片水面已被设施占用。";
                    return false;
                }
            }

            if (AvailableWood < definition.WoodCost)
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

            if (AvailableWood < Buildables[selectedBuildableIndex].WoodCost)
            {
                reason = "木材不足，需要 " + Buildables[selectedBuildableIndex].WoodCost + "。";
                return false;
            }

            reason = string.Empty;
            return true;
        }

        private bool TryFindDockDirection(Vector2Int anchor, out Vector2Int direction)
        {
            direction = Vector2Int.zero;
            if (constructionGrid == null || !constructionGrid.GetTerrain(anchor).HasLand ||
                constructionGrid.CellCenter(anchor).y > WaterPlaneHeight + 3f) return false;
            for (int i = 0; i < CardinalDirections.Length; i++)
            {
                Vector2Int candidate = CardinalDirections[i];
                if (dockManualRotation && candidate != RotateDirection(South, rotationDegrees)) continue;
                Vector2Int sideDirection = candidate.x == 0 ? East : North;
                bool sideIsClear = true;
                for (int forward = -DockInlandCells; forward <= DockWaterwardCells && sideIsClear; forward++)
                {
                    for (int side = -DockHalfWidthCells; side <= DockHalfWidthCells; side++)
                    {
                        Vector2Int reservedCell = anchor + candidate * forward + sideDirection * side;
                        if (!constructionGrid.Contains(reservedCell) ||
                            (forward >= 2 && constructionGrid.GetTerrain(reservedCell).HasLand &&
                                constructionGrid.GetTerrain(reservedCell).MaximumHeight > WaterPlaneHeight + .35f) ||
                            (forward == 1 && side == 0 && constructionGrid.GetTerrain(reservedCell).HasLand &&
                                constructionGrid.GetTerrain(reservedCell).MaximumHeight > constructionGrid.GetTerrain(anchor).MaximumHeight + .2f) ||
                            (forward == -DockInlandCells && side == 0 &&
                                (!constructionGrid.GetTerrain(reservedCell).HasLand ||
                                 constructionGrid.GetTerrain(reservedCell).MaximumSlope > 45f ||
                                 constructionGrid.GetTerrain(reservedCell).MaximumHeight > WaterPlaneHeight + 3f)) ||
                            occupiedCells.Contains(reservedCell) || roadCells.Contains(reservedCell))
                        {
                            sideIsClear = false;
                            break;
                        }
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
            if (selectedBuildableIndex < 0 || !IsBuildableUnlocked(Buildables[selectedBuildableIndex]))
            {
                selectedBuildableIndex = -1;
                statusMessage = "该设施尚未解锁。请先完成对应研究。";
                return;
            }

            BuildableDefinition selected = Buildables[selectedBuildableIndex];
            if (selected.Kind == BuildableKind.Road)
            {
                if (!CanPlaceRoad(anchor, selected, out string roadReason))
                {
                    statusMessage = roadReason;
                    return;
                }

                roadCells.Add(anchor);
                if (grassCover != null) grassCover.ClearCell(anchor);
                if (constructionGrid != null) TripoVegetationAssets.ClearVegetationAt(constructionGrid.Root.TransformPoint(constructionGrid.CellCenter(anchor)));
                SpendWood(selected.WoodCost);
                RefreshRoadsAround(anchor);
                statusMessage = "道路开始铺设，木材 -" + selected.WoodCost + "。";
                return;
            }

            if (selected.Kind == BuildableKind.Water)
            {
                if (!CanPlaceWater(anchor, selected, out string waterReason))
                {
                    statusMessage = waterReason;
                    return;
                }

                GameObject inst = PlaceObject(selected.AssetName, selected.Name, anchor, selected, rotationDegrees, out GameObject foundation);
                GetWaterFootprint(selected, out int width, out int depth);
                PlacedBuildingData data = new PlacedBuildingData
                {
                    GameObject = inst,
                    Foundation = foundation,
                    Definition = selected,
                    Anchor = anchor,
                    Rotation = rotationDegrees,
                    WoodCost = selected.WoodCost
                };
                for (int x = 0; x < width; x++)
                for (int z = 0; z < depth; z++)
                {
                    Vector2Int c = anchor + new Vector2Int(x, z);
                    OccupyCell(c);
                    data.OccupiedCells.Add(c);
                    cellToPlacedBuilding[c] = data;
                }
                placedBuildingList.Add(data);

                SpendWood(selected.WoodCost);
                statusMessage = selected.Name + "开始施工，木材 -" + selected.WoodCost + "。";
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
                GameObject inst = PlaceObject(selected.AssetName, selected.Name, anchor, selected, dockRotation, out GameObject foundation);
                PlacedBuildingData data = new PlacedBuildingData
                {
                    GameObject = inst,
                    Foundation = foundation,
                    Definition = selected,
                    Anchor = anchor,
                    Rotation = dockRotation,
                    WoodCost = selected.WoodCost
                };
                Vector2Int dockSideDirection = shoreDirection.x == 0 ? East : North;
                for (int forward = -DockInlandCells; forward <= DockWaterwardCells; forward++)
                {
                    for (int side = -DockHalfWidthCells; side <= DockHalfWidthCells; side++)
                    {
                        Vector2Int reservedCell = anchor + shoreDirection * forward + dockSideDirection * side;
                        OccupyCell(reservedCell);
                        data.OccupiedCells.Add(reservedCell);
                        cellToPlacedBuilding[reservedCell] = data;
                    }
                }
                placedBuildingList.Add(data);

                SpendWood(selected.WoodCost);
                statusMessage = selected.Name + "开始施工，木材 -" + selected.WoodCost + "。";
                return;
            }

            if (!CanPlaceBuilding(anchor, selected, out string reason))
            {
                statusMessage = reason;
                return;
            }

            GameObject instBuilding = PlaceObject(selected.AssetName, selected.Name, anchor, selected, rotationDegrees, out GameObject bFoundation);
            PlacedBuildingData bData = new PlacedBuildingData
            {
                GameObject = instBuilding,
                Foundation = bFoundation,
                Definition = selected,
                Anchor = anchor,
                Rotation = rotationDegrees,
                WoodCost = selected.WoodCost
            };
            for (int x = 0; x < selected.Width; x++)
            {
                for (int z = 0; z < selected.Depth; z++)
                {
                    Vector2Int c = anchor + new Vector2Int(x, z);
                    OccupyCell(c);
                    bData.OccupiedCells.Add(c);
                    cellToPlacedBuilding[c] = bData;
                }
            }
            placedBuildingList.Add(bData);

            SpendWood(selected.WoodCost);
            statusMessage = selected.Name + "开始施工，木材 -" + selected.WoodCost + "。";
        }

        private void OccupyCell(Vector2Int cell)
        {
            occupiedCells.Add(cell);
            if (grassCover != null) grassCover.ClearCell(cell);
            if (constructionGrid != null) TripoVegetationAssets.ClearVegetationAt(constructionGrid.Root.TransformPoint(constructionGrid.CellCenter(cell)));
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

        private GameObject PlaceObject(string assetName, string objectName, Vector2Int anchor, BuildableDefinition definition, int rotation, out GameObject foundation)
        {
            GameObject instance = CreatePlaceableObject(assetName, objectName);
            instance.transform.SetParent(mapRoot, false);
            instance.transform.SetLocalPositionAndRotation(
                GetObjectCenter(anchor, definition),
                Quaternion.Euler(0f, rotation, 0f));
            foundation = null;
            if (definition.Kind == BuildableKind.Building && constructionGrid.TryBuildingFootprint(
                anchor, definition.Width, definition.Depth, out _, out float height))
            {
                foundation = GameObject.CreatePrimitive(PrimitiveType.Cube);
                foundation.name = "Local terrain foundation";
                foundation.transform.SetParent(instance.transform, false);
                foundation.transform.localPosition = new Vector3(0f, -height * 0.5f, 0f);
                foundation.transform.localScale = new Vector3(definition.Width * 0.96f, height, definition.Depth * 0.96f);
                if (foundationMaterial == null) foundationMaterial = MakeMaterial(new Color(0.29f, 0.30f, 0.28f));
                foundation.GetComponent<Renderer>().sharedMaterial = foundationMaterial;
            }
            if (definition.Kind == BuildableKind.Dock) UpdateDockAccess(instance, anchor);
            BeginConstruction(instance, assetName);
            BuildingConstructionController construction = instance.GetComponent<BuildingConstructionController>();
            if (construction == null || construction.IsComplete)
            {
                RegisterCompletedBuildable(assetName);
            }
            else
            {
                construction.Completed += HandleBuildableConstructionCompleted;
            }
            return instance;
        }

        private void UpdateDockAccess(GameObject instance, Vector2Int anchor)
        {
            if (dockAccessMaterial == null) dockAccessMaterial = MakeMaterial(new Color(.34f, .24f, .14f));
            Transform old = instance.transform.Find("Adaptive shore stairs");
            Vector3 inland = instance.transform.localRotation * Vector3.forward;
            Vector2Int landing = anchor + new Vector2Int(Mathf.RoundToInt(inland.x), Mathf.RoundToInt(inland.z)) * DockInlandCells;
            var terrain = constructionGrid.GetTerrain(landing);
            float deck = WaterPlaneHeight + 0.65f;
            float top = Mathf.Max(deck, Mathf.Max(terrain.MaximumHeight, constructionGrid.GetTerrain(anchor).MaximumHeight) + 0.08f);
            float rise = top - deck;
            int expectedCount = Mathf.Max(1, Mathf.CeilToInt(rise / 0.18f));
            if (old != null && old.childCount == expectedCount + 1 &&
                Mathf.Abs(old.GetChild(0).localPosition.y - (top - rise / expectedCount - WaterPlaneHeight - .09f)) < .001f) return;
            if (old != null)
            {
                old.gameObject.SetActive(false);
                old.SetParent(null, false);
                Destroy(old.gameObject);
            }
            GameObject access = new GameObject("Adaptive shore stairs");
            access.transform.SetParent(instance.transform, false);
            int count = Mathf.Max(1, Mathf.CeilToInt(rise / 0.18f));
            float run = 2.5f / count;
            for (int i = 0; i < count; i++)
            {
                GameObject step = GameObject.CreatePrimitive(PrimitiveType.Cube);
                step.name = "Shore stair " + (i + 1);
                step.transform.SetParent(access.transform, false);
                float y = Mathf.Lerp(top, deck, (i + 1f) / count);
                step.transform.localPosition = new Vector3(0f, y - WaterPlaneHeight - 0.09f, .5f - (i + .5f) * run);
                step.transform.localScale = new Vector3(1.4f, .18f, run + .03f);
                step.GetComponent<Renderer>().sharedMaterial = dockAccessMaterial;
            }
            GameObject landingPlatform = GameObject.CreatePrimitive(PrimitiveType.Cube);
            landingPlatform.name = "Shore landing";
            landingPlatform.transform.SetParent(access.transform, false);
            landingPlatform.transform.localPosition = new Vector3(0f, top - WaterPlaneHeight - .09f, 1.25f);
            landingPlatform.transform.localScale = new Vector3(1.4f, .18f, 1.5f);
            landingPlatform.GetComponent<Renderer>().sharedMaterial = dockAccessMaterial;
        }

        private void HandleBuildableConstructionCompleted(BuildingConstructionController construction)
        {
            if (construction != null)
            {
                RegisterCompletedBuildable(construction.AssetKey);
            }
        }

        private void RegisterCompletedBuildable(string assetName)
        {
            if (string.IsNullOrEmpty(assetName)) return;

            string canonicalKey = assetName;
            bool newlyCompleted = false;
            if (BuildingConstructionCatalog.TryGet(assetName, out BuildingConstructionCatalog.Entry entry))
            {
                canonicalKey = entry.key;
                newlyCompleted |= completedBuildableAssets.Add(entry.key);
            }

            string displayName = assetName;
            newlyCompleted |= completedBuildableAssets.Add(assetName);
            for (int i = 0; i < Buildables.Length; i++)
            {
                if (BuildingConstructionCatalog.TryGet(Buildables[i].AssetName,
                    out BuildingConstructionCatalog.Entry buildableEntry) &&
                    string.Equals(buildableEntry.key, canonicalKey, System.StringComparison.Ordinal))
                {
                    newlyCompleted |= completedBuildableAssets.Add(Buildables[i].AssetName);
                    displayName = Buildables[i].Name;
                    break;
                }
            }

            if (newlyCompleted)
            {
                statusMessage = displayName + "已建成，研究条件已更新。";
            }
        }

        private void BeginConstruction(GameObject instance, string assetName, float progress = 0f)
        {
            Transform finalVisual = instance.transform.Find(assetName + " Model");
            if (finalVisual == null) return; // Missing model: retain the existing graybox fallback.
            BuildingConstructionController.TryBegin(instance, assetName, finalVisual.gameObject,
                () => weatherSystem != null ? weatherSystem.SimulationSpeed : 1f, progress);
        }

        private Vector3 GetObjectCenter(Vector2Int anchor, BuildableDefinition definition)
        {
            if (definition.Kind == BuildableKind.Dock)
            {
                Vector3 dockCenter = CellCenter(anchor);
                dockCenter.y = WaterPlaneHeight; // Dock FBXs are authored relative to their waterline.
                return dockCenter;
            }
            if (definition.Kind == BuildableKind.Water)
            {
                GetWaterFootprint(definition, out int width, out int depth);
                Vector3 waterCenter = CellCenter(anchor) + new Vector3((width - 1) * 0.5f, 0f, (depth - 1) * 0.5f);
                waterCenter.y = WaterPlaneHeight;
                return waterCenter;
            }
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
            float progress = 0f;
            if (roadObjects.TryGetValue(cell, out GameObject existing) && existing != null)
            {
                BuildingConstructionController construction = existing.GetComponent<BuildingConstructionController>();
                // Joining another road changes topology, not work already completed.
                progress = construction != null ? construction.Progress : 1f;
                existing.SetActive(false);
                Destroy(existing);
            }

            GameObject road = CreatePlaceableObject(shape.AssetName, "Road " + cell.x + "-" + cell.y);
            road.transform.SetParent(mapRoot, false);
            road.transform.SetLocalPositionAndRotation(CellCenter(cell), Quaternion.Euler(0f, shape.RotationDegrees, 0f));
            BeginConstruction(road, shape.AssetName, progress);
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

        private Vector3 CellCenter(Vector2Int cell)
        {
            return constructionGrid != null ? constructionGrid.CellCenter(cell) : new Vector3(0f, TileTop, 0f);
        }

        public enum BuildableKind
        {
            Building,
            Dock,
            Road,
            Water
        }

        private enum ResearchType
        {
            None,
            Mainline,
            Efficiency
        }

        private sealed class TechnologyResearchDefinition
        {
            public readonly int Level;
            public readonly string Name;
            public readonly string Description;
            public readonly float DurationSeconds;
            public readonly string[] RequiredAssets;
            public readonly string RequirementsSummary;

            public TechnologyResearchDefinition(int level, string name, string description, float durationSeconds,
                params string[] requiredAssets)
            {
                Level = level;
                Name = name;
                Description = description;
                DurationSeconds = durationSeconds;
                RequiredAssets = requiredAssets ?? new string[0];
                List<string> requirements = new List<string> { "研究站" };
                for (int i = 0; i < RequiredAssets.Length; i++)
                {
                    if (string.Equals(RequiredAssets[i], "ResearchStation", System.StringComparison.Ordinal))
                        continue;
                    string displayName = GetBuildableDisplayName(RequiredAssets[i]);
                    if (!requirements.Contains(displayName)) requirements.Add(displayName);
                }
                RequirementsSummary = string.Join("、", requirements.ToArray());
            }
        }

        private struct EfficiencyResearchOption
        {
            public readonly string AssetName;
            public readonly string BuildingName;
            public readonly string Key;
            public readonly int Tier;
            public readonly int RequiredResearchLevel;

            public EfficiencyResearchOption(string assetName, string buildingName, int tier,
                int requiredResearchLevel)
            {
                AssetName = assetName;
                BuildingName = buildingName;
                Key = GetEfficiencyResearchKey(assetName, tier);
                Tier = tier;
                RequiredResearchLevel = requiredResearchLevel;
            }
        }

        public sealed class BuildableDefinition
        {
            public readonly string Name;
            public readonly string AssetName;
            public readonly string IconName;
            public readonly int Width;
            public readonly int Depth;
            public readonly int WoodCost;
            public readonly BuildableKind Kind;
            public readonly int ScenarioLevel;
            public readonly BuildCategory Category;

            public BuildableDefinition(string name, string assetName, int width, int depth, int woodCost,
                BuildableKind kind = BuildableKind.Building, string iconName = null, int scenarioLevel = -1,
                BuildCategory category = BuildCategory.Production)
            {
                Name = name;
                AssetName = assetName;
                IconName = string.IsNullOrEmpty(iconName) ? assetName + "_Final" : iconName;
                Width = width;
                Depth = depth;
                WoodCost = woodCost;
                Kind = kind;
                ScenarioLevel = scenarioLevel;
                Category = category;
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
        private void DrawToolModeButtons(Rect panelRect)
        {
            float buttonWidth = 72f;
            float buttonHeight = 22f;
            float startX = panelRect.xMax - (buttonWidth * 3f + 14f) - 38f;
            float y = panelRect.y + 14f;

            string[] modeNames = { "建造", "移动 (M)", "拆除 (X)" };
            BuildToolMode[] modes = { BuildToolMode.Place, BuildToolMode.Move, BuildToolMode.Demolish };

            for (int i = 0; i < modes.Length; i++)
            {
                Rect bRect = new Rect(startX + i * (buttonWidth + 6f), y, buttonWidth, buttonHeight);
                bool isActive = currentToolMode == modes[i];
                Color oldBg = GUI.backgroundColor;
                if (isActive)
                {
                    GUI.backgroundColor = (modes[i] == BuildToolMode.Demolish)
                        ? new Color(0.92f, 0.40f, 0.35f, 1f)
                        : new Color(0.40f, 0.78f, 0.75f, 1f);
                }

                if (GUI.Button(bRect, modeNames[i]))
                {
                    if (isMovingBuilding) CancelMove();
                    currentToolMode = modes[i];
                    selectedBuildableIndex = -1;
                    SetBuildGridVisibility(currentToolMode != BuildToolMode.Place);
                    if (currentToolMode == BuildToolMode.Demolish)
                        statusMessage = "【拆除模式】：点击已放置的建筑或道路拆除，返还50%木材。";
                    else if (currentToolMode == BuildToolMode.Move)
                        statusMessage = "【移动模式】：点击想要移动的建筑进行拾起。";
                    else
                        statusMessage = "【建造模式】：在下方选择建筑进行建造。";
                }
                GUI.backgroundColor = oldBg;
            }
        }

        private void DemolishAt(Vector2Int cell)
        {
            if (cellToPlacedBuilding.TryGetValue(cell, out PlacedBuildingData data) && data != null)
            {
                int refund = Mathf.Max(1, Mathf.RoundToInt(data.WoodCost * 0.5f));
                RefundWood(refund);

                foreach (Vector2Int c in data.OccupiedCells)
                {
                    occupiedCells.Remove(c);
                    cellToPlacedBuilding.Remove(c);
                }
                placedBuildingList.Remove(data);

                bool stillHasType = false;
                for (int i = 0; i < placedBuildingList.Count; i++)
                {
                    if (placedBuildingList[i].Definition.AssetName == data.Definition.AssetName)
                    {
                        stillHasType = true;
                        break;
                    }
                }
                if (!stillHasType)
                {
                    completedBuildableAssets.Remove(data.Definition.AssetName);
                    if (BuildingConstructionCatalog.TryGet(data.Definition.AssetName, out var entry))
                    {
                        completedBuildableAssets.Remove(entry.key);
                    }
                }

                if (data.GameObject != null)
                {
                    Destroy(data.GameObject);
                }

                statusMessage = "已拆除 " + data.Definition.Name + "，返还木材 +" + refund + "。";
                return;
            }

            if (roadCells.Contains(cell))
            {
                const int roadRefund = 2;
                RefundWood(roadRefund);
                roadCells.Remove(cell);
                if (roadObjects.TryGetValue(cell, out GameObject roadObj) && roadObj != null)
                {
                    Destroy(roadObj);
                    roadObjects.Remove(cell);
                }
                RefreshRoadsAround(cell);
                statusMessage = "已拆除道路，返还木材 +" + roadRefund + "。";
            }
        }

        public void StartMoveBuilding(PlacedBuildingData data)
        {
            if (data == null) return;
            movingBuilding = data;
            isMovingBuilding = true;

            foreach (Vector2Int c in data.OccupiedCells)
            {
                occupiedCells.Remove(c);
                cellToPlacedBuilding.Remove(c);
            }

            if (data.GameObject != null)
            {
                data.GameObject.SetActive(false);
            }

            selectedBuildableIndex = -1;
            for (int i = 0; i < Buildables.Length; i++)
            {
                if (Buildables[i].AssetName == data.Definition.AssetName)
                {
                    selectedBuildableIndex = i;
                    break;
                }
            }

            rotationDegrees = data.Rotation;
            statusMessage = "正在移动 " + data.Definition.Name + "：移动鼠标寻找新位置并点击放置，右键取消。";
        }

        private void TryCommitMove(Vector2Int newAnchor)
        {
            if (movingBuilding == null) return;

            int newRot = rotationDegrees;
            List<Vector2Int> newCells = new List<Vector2Int>();

            if (movingBuilding.Definition.Kind == BuildableKind.Dock)
            {
                if (!CanPlaceDock(newAnchor, out Vector2Int shoreDir, out string dockReason))
                {
                    statusMessage = dockReason;
                    return;
                }
                newRot = GetRotationAligning(South, shoreDir);
                Vector2Int dockSideDir = shoreDir.x == 0 ? East : North;
                for (int forward = -DockInlandCells; forward <= DockWaterwardCells; forward++)
                for (int side = -DockHalfWidthCells; side <= DockHalfWidthCells; side++)
                    newCells.Add(newAnchor + shoreDir * forward + dockSideDir * side);
            }
            else if (movingBuilding.Definition.Kind == BuildableKind.Water)
            {
                if (!CanPlaceWater(newAnchor, movingBuilding.Definition, out string waterReason))
                {
                    statusMessage = waterReason;
                    return;
                }
                GetWaterFootprint(movingBuilding.Definition, out int w, out int d);
                for (int x = 0; x < w; x++)
                for (int z = 0; z < d; z++)
                    newCells.Add(newAnchor + new Vector2Int(x, z));
            }
            else
            {
                if (!CanPlaceBuilding(newAnchor, movingBuilding.Definition, out string bReason))
                {
                    statusMessage = bReason;
                    return;
                }
                for (int x = 0; x < movingBuilding.Definition.Width; x++)
                for (int z = 0; z < movingBuilding.Definition.Depth; z++)
                    newCells.Add(newAnchor + new Vector2Int(x, z));
            }

            if (movingBuilding.GameObject != null)
            {
                movingBuilding.GameObject.transform.SetLocalPositionAndRotation(
                    GetObjectCenter(newAnchor, movingBuilding.Definition),
                    Quaternion.Euler(0f, newRot, 0f));

                if (movingBuilding.Foundation != null && movingBuilding.Definition.Kind == BuildableKind.Building &&
                    constructionGrid.TryBuildingFootprint(newAnchor, movingBuilding.Definition.Width, movingBuilding.Definition.Depth, out _, out float h))
                {
                    movingBuilding.Foundation.transform.localPosition = new Vector3(0f, -h * 0.5f, 0f);
                    movingBuilding.Foundation.transform.localScale = new Vector3(movingBuilding.Definition.Width * 0.96f, h, movingBuilding.Definition.Depth * 0.96f);
                }

                if (movingBuilding.Definition.Kind == BuildableKind.Dock)
                    UpdateDockAccess(movingBuilding.GameObject, newAnchor);
                movingBuilding.GameObject.SetActive(true);
            }

            movingBuilding.Anchor = newAnchor;
            movingBuilding.Rotation = newRot;
            movingBuilding.OccupiedCells.Clear();

            foreach (Vector2Int c in newCells)
            {
                OccupyCell(c);
                movingBuilding.OccupiedCells.Add(c);
                cellToPlacedBuilding[c] = movingBuilding;
            }

            statusMessage = "已将 " + movingBuilding.Definition.Name + " 移动至新位置。";
            movingBuilding = null;
            isMovingBuilding = false;
            selectedBuildableIndex = -1;
            currentToolMode = BuildToolMode.Place;
        }

        private void CancelMove()
        {
            if (movingBuilding != null)
            {
                foreach (Vector2Int c in movingBuilding.OccupiedCells)
                {
                    OccupyCell(c);
                    cellToPlacedBuilding[c] = movingBuilding;
                }

                if (movingBuilding.GameObject != null)
                {
                    if (movingBuilding.Definition.Kind == BuildableKind.Dock)
                    UpdateDockAccess(movingBuilding.GameObject, movingBuilding.Anchor);
                movingBuilding.GameObject.SetActive(true);
                }

                statusMessage = "已取消移动 " + movingBuilding.Definition.Name + "。";
                movingBuilding = null;
                isMovingBuilding = false;
                selectedBuildableIndex = -1;
                currentToolMode = BuildToolMode.Place;
            }
        }

        private void InitializeScenarioCrewAndVessel()
        {
            if (constructionGrid == null) return;

            // Search outside the enlarged shoreline rather than using old land coordinates.
            Vector3 preferred = new Vector3(-8.5f, WaterPlaneHeight, -14.5f);
            if (!TryFindClearWater(preferred, 5f, out Vector3 boatLocal)) boatLocal = preferred;
            Vector3 boatPos = mapRoot.TransformPoint(boatLocal);
            RescueBoatController.Spawn(boatPos, Quaternion.Euler(0f, -35f, 0f), mapRoot);

            // Initial crew members from the game lore ("玩家带着两名船员出发")
            Vector3 crew1Pos = new Vector3(2f, TileTop, 2f);
            if (constructionGrid.TrySample(2, 2, out Vector3 s1, out _)) crew1Pos = s1;
            SurvivorCharacterController.Spawn(crew1Pos, "阿岩", "搜救驾驶员", mapRoot);

            Vector3 crew2Pos = new Vector3(-2f, TileTop, 1f);
            if (constructionGrid.TrySample(-2, 1, out Vector3 s2, out _)) crew2Pos = s2;
            SurvivorCharacterController.Spawn(crew2Pos, "小海", "技术维修员", mapRoot);
        }

        private bool TryFindClearWater(Vector3 preferred, float radius, out Vector3 result)
        {
            result = preferred;
            if (constructionGrid == null) return false;
            for (float distance = 0f; distance <= 180f; distance += 2f)
            for (int direction = 0; direction < (distance == 0f ? 1 : 32); direction++)
            {
                float angle = direction * Mathf.PI * 2f / 32f;
                float x = preferred.x + Mathf.Cos(angle) * distance;
                float z = preferred.z + Mathf.Sin(angle) * distance;
                bool clear = !constructionGrid.TrySample(x, z, out _, out _);
                for (int i = 0; clear && i < 32; i++)
                {
                    float a = (i % 16) * Mathf.PI * 2f / 16f;
                    float r = radius * (i < 16 ? .5f : 1f);
                    clear = !constructionGrid.TrySample(x + Mathf.Cos(a) * r,
                        z + Mathf.Sin(a) * r, out _, out _);
                }
                if (!clear) continue;
                result = new Vector3(x, WaterPlaneHeight, z);
                return true;
            }
            return false;
        }


        private void InitializeColonySystems()
        {
            if (GetComponent<ColonyResourceManager>() == null) gameObject.AddComponent<ColonyResourceManager>();
            if (GetComponent<ColonyCitizenManager>() == null) gameObject.AddComponent<ColonyCitizenManager>();
            // if (GetComponent<OceanSalvageManager>() == null) gameObject.AddComponent<OceanSalvageManager>();
            if (GetComponent<ColonySaveLoadManager>() == null) gameObject.AddComponent<ColonySaveLoadManager>();
            if (GetComponent<BuildingInspectorUI>() == null) gameObject.AddComponent<BuildingInspectorUI>();
            if (GetComponent<ColonyModalDialog>() == null) gameObject.AddComponent<ColonyModalDialog>();

            // The resource manager owns the visible stockpile and save data.
            var res = ColonyResourceManager.Instance;
            if (res != null)
            {
                res.SetAllResources(999f);
                wood = Mathf.FloorToInt(res.Wood);
            }
        }

        public void SetCameraFollowTarget(Transform target)
        {
            cameraFollowTarget = target;
            if (target != null)
            {
                cameraOrbitTarget = target.position;
                statusMessage = "【快艇驾驶模式】WASD 控制航行，按 Esc 退出驾驶。";
            }
            else
            {
                statusMessage = "已退出快艇驾驶模式。";
            }
        }

        public int CountCompletedBuildings(string assetName)
        {
            int count = 0;
            string key = assetName;
            if (BuildingConstructionCatalog.TryGet(assetName, out var entry)) key = entry.key;

            for (int i = 0; i < placedBuildingList.Count; i++)
            {
                var b = placedBuildingList[i];
                if (b != null)
                {
                    string bKey = b.Definition.AssetName;
                    if (BuildingConstructionCatalog.TryGet(bKey, out var bEntry)) bKey = bEntry.key;
                    if (bKey == key || b.Definition.AssetName == assetName)
                    {
                        var c = b.GameObject != null ? b.GameObject.GetComponent<BuildingConstructionController>() : null;
                        if (c == null || c.IsComplete) count++;
                    }
                }
            }
            return count;
        }

        public void DemolishBuilding(PlacedBuildingData data)
        {
            if (data == null) return;
            int refund = Mathf.Max(1, Mathf.RoundToInt(data.WoodCost * 0.5f));
            RefundWood(refund);

            foreach (Vector2Int c in data.OccupiedCells)
            {
                occupiedCells.Remove(c);
                cellToPlacedBuilding.Remove(c);
            }
            placedBuildingList.Remove(data);

            if (data.GameObject != null)
            {
                Destroy(data.GameObject);
            }

            statusMessage = "已成功拆除 " + data.Definition.Name + "，返还木材 +" + refund + "。";
        }

        public void RestoreResearchProgress(int level, List<string> efficiency)
        {
            researchLevel = level;
            researchedEfficiencyKeys.Clear();
            if (efficiency != null)
            {
                foreach (var k in efficiency) researchedEfficiencyKeys.Add(k);
            }
        }

        public void RestoreColonyEntities(List<BuildingSaveEntry> savedBuildings, List<RoadSaveEntry> savedRoads)
        {
            // Clear existing buildings
            for (int i = 0; i < placedBuildingList.Count; i++)
            {
                if (placedBuildingList[i].GameObject != null)
                {
                    Destroy(placedBuildingList[i].GameObject);
                }
            }
            placedBuildingList.Clear();
            cellToPlacedBuilding.Clear();
            occupiedCells.Clear();

            // Clear existing roads
            foreach (var kvp in roadObjects)
            {
                if (kvp.Value != null) Destroy(kvp.Value);
            }
            roadObjects.Clear();
            roadCells.Clear();

            // Restore roads
            if (savedRoads != null)
            {
                foreach (var r in savedRoads)
                {
                    Vector2Int c = new Vector2Int(r.x, r.y);
                    roadCells.Add(c);
                    RefreshRoadsAround(c);
                }
            }

            // Restore buildings
            if (savedBuildings != null)
            {
                foreach (var b in savedBuildings)
                {
                    for (int i = 0; i < Buildables.Length; i++)
                    {
                        if (Buildables[i].AssetName == b.assetName)
                        {
                            Vector2Int anchor = new Vector2Int(b.anchorX, b.anchorY);
                            rotationDegrees = b.rotation;
                            selectedBuildableIndex = i;

                            GameObject inst = PlaceObject(b.assetName, Buildables[i].Name, anchor, Buildables[i], b.rotation, out GameObject foundation);
                            PlacedBuildingData bData = new PlacedBuildingData
                            {
                                GameObject = inst,
                                Foundation = foundation,
                                Definition = Buildables[i],
                                Anchor = anchor,
                                Rotation = b.rotation,
                                WoodCost = b.woodCost
                            };

                            if (Buildables[i].Kind == BuildableKind.Water)
                            {
                                GetWaterFootprint(Buildables[i], out int w, out int d);
                                for (int x = 0; x < w; x++)
                                for (int z = 0; z < d; z++)
                                {
                                    Vector2Int cell = anchor + new Vector2Int(x, z);
                                    OccupyCell(cell);
                                    bData.OccupiedCells.Add(cell);
                                    cellToPlacedBuilding[cell] = bData;
                                }
                            }
                            else if (Buildables[i].Kind == BuildableKind.Dock)
                            {
                                Vector2Int shoreDir = North;
                                Vector2Int dockSideDir = East;
                                for (int forward = -DockInlandCells; forward <= DockWaterwardCells; forward++)
                                for (int side = -DockHalfWidthCells; side <= DockHalfWidthCells; side++)
                                {
                                    Vector2Int cell = anchor + shoreDir * forward + dockSideDir * side;
                                    OccupyCell(cell);
                                    bData.OccupiedCells.Add(cell);
                                    cellToPlacedBuilding[cell] = bData;
                                }
                            }
                            else
                            {
                                for (int x = 0; x < Buildables[i].Width; x++)
                                for (int z = 0; z < Buildables[i].Depth; z++)
                                {
                                    Vector2Int cell = anchor + new Vector2Int(x, z);
                                    OccupyCell(cell);
                                    bData.OccupiedCells.Add(cell);
                                    cellToPlacedBuilding[cell] = bData;
                                }
                            }

                            placedBuildingList.Add(bData);
                            break;
                        }
                    }
                }
                selectedBuildableIndex = -1;
            }
        }

    }
}
