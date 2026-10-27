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
        private const string CapsizedWreckResourceName = "Gate26_CapsizedWreck";
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
        private const int DockWaterwardCells = 4;
        private const int TotalHeaderResourceCount = 8;
        private const float CameraZoomFactor = 1.12f;
        private const float MinimumCameraOrthographicSize = 3f;
        private const float MaximumCameraOrthographicSize = 160f;
        private bool usingExpandedArchipelago;
        private Bounds mainIslandFramingBounds;
        private Renderer coastalGridRenderer;
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

        private enum BuildCategory
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
            new BuildableDefinition("居民小屋", "ResidentHut_DeepSeek", 1, 1, 20, BuildableKind.Building, "ResidentHut_DeepSeek", 1, BuildCategory.Residential),
            new BuildableDefinition("温室", "Greenhouse_DeepSeek", 2, 2, 35, BuildableKind.Building, "Greenhouse_DeepSeek", 3, BuildCategory.Production),
            new BuildableDefinition("废料拆解工坊", "SalvageWorkshop_DeepSeek", 2, 2, 35, BuildableKind.Building, "SalvageWorkshop_DeepSeek", 3, BuildCategory.Production),
            new BuildableDefinition("仓库", "StorageDepot_DeepSeek", 2, 2, 25, BuildableKind.Building, "StorageDepot_DeepSeek", 1, BuildCategory.Facilities),
            new BuildableDefinition("救援指挥站", "RescueRadioCenter_DeepSeek", 2, 2, 45, BuildableKind.Building, "RescueRadioCenter_DeepSeek", 4, BuildCategory.Facilities),
            new BuildableDefinition("救援码头", "RescueDock", 1, 1, 35, BuildableKind.Dock, "RescueDock_DeepSeek", 1, BuildCategory.Transportation),
            new BuildableDefinition("道路", "RoadStraight", 1, 1, 4, BuildableKind.Road, "RoadTiles_DeepSeek", 0, BuildCategory.Transportation),
            new BuildableDefinition("固定海水淡化装置", "DesalinationPlant_DeepSeek", 3, 2, 35, BuildableKind.Building, "DesalinationPlant_DeepSeek", 1, BuildCategory.Production),
            new BuildableDefinition("医疗站", "MedicalStation_DeepSeek", 3, 2, 35, BuildableKind.Building, "MedicalStation_DeepSeek", 2, BuildCategory.Facilities),
            new BuildableDefinition("太阳能发电站", "SolarPowerStation_DeepSeek", 4, 3, 45, BuildableKind.Building, "SolarPowerStation_DeepSeek", 2, BuildCategory.Production),
            new BuildableDefinition("公共厨房", "PublicKitchen_DeepSeek", 3, 2, 35, BuildableKind.Building, "PublicKitchen_DeepSeek", 3, BuildCategory.Production),
            new BuildableDefinition("锻造炉", "Forge_DeepSeek", 2, 2, 40, BuildableKind.Building, "Forge_DeepSeek", 3, BuildCategory.Production),
            new BuildableDefinition("木棚", "WoodShelter_DeepSeek", 2, 2, 15, BuildableKind.Building, "WoodShelter_DeepSeek", 0, BuildCategory.Residential),
            new BuildableDefinition("研究站", "ResearchStation_DeepSeek", 3, 3, 40, BuildableKind.Building, "ResearchStation_DeepSeek", 0, BuildCategory.Facilities),
            new BuildableDefinition("医疗帐篷", "MedicalTent_DeepSeek", 3, 3, 20, BuildableKind.Building, "MedicalTent_DeepSeek", 0, BuildCategory.Facilities),
            new BuildableDefinition("初始通讯中心", "LocalCommunicationsCenter_DeepSeek", 3, 3, 30, BuildableKind.Building, "LocalCommunicationsCenter_DeepSeek", 0, BuildCategory.Facilities),
            new BuildableDefinition("淡水储水罐", "WaterStorageTank", 4, 3, 25, BuildableKind.Building, "WaterStorageTank_DeepSeek", 1, BuildCategory.Production),
            new BuildableDefinition("漂木收集浮栅", "DriftwoodCollectionBoom_DeepSeek", 9, 3, 30, BuildableKind.Water, "DriftwoodCollectionBoom_DeepSeek", 1, BuildCategory.Production),
            new BuildableDefinition("渔船码头", "FishingDock_DeepSeek", 1, 1, 35, BuildableKind.Dock, "FishingDock_DeepSeek", 1, BuildCategory.Production),
            new BuildableDefinition("气象潮位浮标", "WeatherTideBuoy_DeepSeek", 2, 2, 25, BuildableKind.Water, "WeatherTideBuoy_DeepSeek", 4, BuildCategory.Facilities),
            new BuildableDefinition("船坞", "Shipyard_DeepSeek", 1, 1, 50, BuildableKind.Dock, "Shipyard_DeepSeek", 4, BuildCategory.Transportation),
            new BuildableDefinition("救援前哨", "RescueOutpost_DeepSeek", 2, 4, 35, BuildableKind.Building, "RescueOutpost_DeepSeek", 4, BuildCategory.Facilities),
            new BuildableDefinition("学校", "School_DeepSeek", 8, 7, 45, BuildableKind.Building, "School_DeepSeek", 5, BuildCategory.Facilities),
            new BuildableDefinition("档案馆", "Archive_DeepSeek", 5, 5, 40, BuildableKind.Building, "Archive_DeepSeek", 5, BuildCategory.Facilities),
            new BuildableDefinition("议事厅", "CouncilHall_DeepSeek", 10, 12, 60, BuildableKind.Building, "CouncilHall_DeepSeek", 5, BuildCategory.Facilities)
        };
        private static readonly TechnologyResearchDefinition[] MainlineResearch =
        {
            new TechnologyResearchDefinition(1, "岛屿水文与饮水保障", "掌握淡水循环与漂木流向，建立稳定的近海补给。", 48f,
                "ResearchStation_DeepSeek", "LocalCommunicationsCenter_DeepSeek"),
            new TechnologyResearchDefinition(2, "稳定供水与太阳能", "完成储水和供电验证，为常驻医疗设施提供基础保障。", 60f,
                "DesalinationPlant_DeepSeek", "WaterStorageTank"),
            new TechnologyResearchDefinition(3, "温室种植与食物加工", "建立可持续种植、食品加工与资源回收流程。", 72f,
                "SolarPowerStation_DeepSeek", "MedicalStation_DeepSeek"),
            new TechnologyResearchDefinition(4, "区域救援与海况观测", "联网观测潮汐天气，并建立救援调度能力。", 84f,
                "Greenhouse_DeepSeek", "PublicKitchen_DeepSeek"),
            new TechnologyResearchDefinition(5, "社区教育与共同治理", "将教育、共同记忆和自治制度纳入聚落建设。", 96f,
                "RescueRadioCenter_DeepSeek", "RescueOutpost_DeepSeek"),
            new TechnologyResearchDefinition(6, "回收自动化与生产维护", "改进材料回收、锻造和设施维护流程。", 108f,
                "SalvageWorkshop_DeepSeek", "Forge_DeepSeek"),
            new TechnologyResearchDefinition(7, "高效农业与区域协作", "共享农业、加工和社区运行数据，提升聚落协作效率。", 120f,
                "Greenhouse_DeepSeek", "PublicKitchen_DeepSeek", "School_DeepSeek", "Archive_DeepSeek"),
            new TechnologyResearchDefinition(8, "区域海运与环境联动", "将船坞、海况观测和救援网络联成区域物流体系。", 132f,
                "Shipyard_DeepSeek", "WeatherTideBuoy_DeepSeek", "RescueRadioCenter_DeepSeek"),
            new TechnologyResearchDefinition(9, "自治知识网络", "整合档案、教育和社区治理，完成区域知识网络。", 144f,
                "School_DeepSeek", "Archive_DeepSeek", "CouncilHall_DeepSeek")
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
                    if (selected.Kind == BuildableKind.Building || selected.Kind == BuildableKind.Water)
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
            if (wood < amount) return false;
            wood -= amount;
            return true;
        }

        public void CloseTransientHudMenus()
        {
            isWeatherMenuOpen = false;
            isResourceMenuOpen = false;
        }

        private void FocusLighthouse(Vector3 point)
        {
            cameraOrbitTarget = point;
            cameraOrthographicSize = 18f;
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
            if (lighthouseSite != null && lighthouseSite.ContainsPointer(pointer)) return true;
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
            Texture2D buildPanelTexture = MakeRoundedUiTexture(128, 128, 16,
                new Color(0.035f, 0.08f, 0.083f, 0.82f));
            Texture2D buildCardTexture = MakeRoundedUiTexture(64, 64, 10,
                new Color(0.11f, 0.17f, 0.15f, 0.68f));
            Texture2D selectedBuildCardTexture = MakeRoundedUiTexture(64, 64, 10,
                new Color(0.28f, 0.38f, 0.27f, 0.82f));
            Texture2D buildHoverTexture = MakeRoundedUiTexture(64, 64, 10,
                new Color(0.24f, 0.36f, 0.29f, 0.78f));
            Texture2D buildActiveTexture = MakeRoundedUiTexture(64, 64, 10,
                new Color(0.31f, 0.43f, 0.32f, 0.84f));
            Texture2D buildCategoryTexture = MakeRoundedUiTexture(64, 64, 12,
                new Color(0.08f, 0.15f, 0.15f, 0.58f));
            Texture2D selectedBuildCategoryTexture = MakeRoundedUiTexture(64, 64, 12,
                new Color(0.34f, 0.42f, 0.27f, 0.80f));
            Texture2D buildCategoryHoverTexture = MakeRoundedUiTexture(64, 64, 12,
                new Color(0.18f, 0.29f, 0.24f, 0.72f));
            Texture2D buildCategoryActiveTexture = MakeRoundedUiTexture(64, 64, 12,
                new Color(0.31f, 0.43f, 0.32f, 0.82f));
            panelStyle = new GUIStyle(GUI.skin.box);
            panelStyle.normal.background = panelTexture;
            panelStyle.border = new RectOffset(12, 12, 12, 12);
            buildPanelStyle = new GUIStyle(GUI.skin.box);
            buildPanelStyle.normal.background = buildPanelTexture;
            buildPanelStyle.border = new RectOffset(18, 18, 18, 18);

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

        private void EnsureSidebarCategoryUi()
        {

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
            HudTheme.TopShade(rect);
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

            if (index == 5)
            {
                return val >= 0 ? "+" + Mathf.RoundToInt(val) : Mathf.RoundToInt(val).ToString(CultureInfo.InvariantCulture);
            }
            return Mathf.RoundToInt(val).ToString(CultureInfo.InvariantCulture);
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
            bool hasArtwork = false; // Use the restrained line-icon navigation.
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
            GUIStyle activePanelStyle = activeSidebarCategory == SidebarCategory.Buildings ? buildPanelStyle : panelStyle;
            GUI.Box(panelRect, GUIContent.none, activePanelStyle);
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
                DrawTechnologyPanel(panelRect);
                return;
            }

            if (activeSidebarCategory == SidebarCategory.Culture)
            {
                DrawKnowledgeRoutePanel(panelRect, CultureRouteNames, CultureRouteDetails,
                    ref selectedCultureRouteIndex);
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
            return definition.ScenarioLevel <= researchLevel;
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

            if (!completedBuildableAssets.Contains("ResearchStation_DeepSeek"))
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
            GUI.Box(cardRect, GUIContent.none, style);

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
                    objectName == LegacyIslandModelName || objectName == IslandResourceName)
                {
                    sceneTransforms[i].gameObject.SetActive(false);
                }
            }

            GameObject expandedMain = Resources.Load<GameObject>("Models/Environment/Island_Main_Expanded");
            usingExpandedArchipelago = expandedMain != null &&
                Resources.Load<GameObject>("Models/Environment/Island_West_Expanded") != null &&
                Resources.Load<GameObject>("Models/Environment/Island_East_Expanded") != null;
            GameObject islandPrefab = (usingExpandedArchipelago ? expandedMain : null) ??
                Resources.Load<GameObject>("Models/Environment/IslandReference_Gate25_Natural") ??
                Resources.Load<GameObject>(GetModelResourcePath(IslandResourceName));
            if (islandPrefab == null)
            {
                Debug.LogError("缺少岛屿模型：Resources/Models/Environment/IslandReference_Gate25.fbx");
                return;
            }

            GameObject island = InstantiateIslandResource(islandPrefab, IslandRootName);
            islandRoot = island.transform;
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
            AddIslandDetailLayers();
            AddCapsizedWreck();
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
            grassCover = gameObject.AddComponent<IslandGrassCover>();
            grassCover.Initialize(constructionGrid, occupiedCells, roadCells);
            Debug.Log($"Construction grid covers all {islandLandColliders.Length} island terrain surfaces " +
                      $"({constructionGrid.Width} × {constructionGrid.Depth} map cells).");
        }

        private void AddBasinTwinIslands()
        {
            if (usingExpandedArchipelago)
            {
                satelliteIslandsRoot = new GameObject("Expanded satellite islands | separate models").transform;
                satelliteIslandsRoot.SetParent(islandRoot, false);
                foreach (string side in new[] { "West", "East" })
                {
                    GameObject prefab = Resources.Load<GameObject>("Models/Environment/Island_" + side + "_Expanded");
                    GameObject model = Instantiate(prefab, satelliteIslandsRoot, false);
                    model.name = "Expanded " + side + " Island";
                    EnsureIslandMaterials(model);
                }
                return;
            }
            GameObject satellitePrefab = Resources.Load<GameObject>("Models/Environment/BasinTwinIslands_Natural_v2") ??
                Resources.Load<GameObject>(GetModelResourcePath(SatelliteIslandResourceName));
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

            Debug.Log($"Gate26 basin twin islands loaded ({islandCount} terrain meshes); they are included in the construction grid.");
        }

        private void AddIslandDetailLayers()
        {
            if (usingExpandedArchipelago) return; // Grounded details are included in each new model.
            // These optional meshes contain decoration only; terrain-source naming and
            // collision surfaces stay in the original three island models.
            string[] names = { "IslandDetail_Main", "IslandDetail_West", "IslandDetail_East" };
            foreach (string name in names)
            {
                GameObject prefab = Resources.Load<GameObject>("Models/Environment/" + name);
                if (prefab == null) continue;
                GameObject details = Instantiate(prefab, islandRoot, false);
                details.name = name;
                EnsureIslandMaterials(details);
                foreach (Collider collider in details.GetComponentsInChildren<Collider>(true))
                    collider.enabled = false;
            }
        }

        private void AddCapsizedWreck()
        {
            GameObject wreckPrefab = Resources.Load<GameObject>(usingExpandedArchipelago
                ? "Models/Environment/Gate26_CapsizedWreck_Expanded"
                : GetModelResourcePath(CapsizedWreckResourceName));
            if (wreckPrefab == null)
            {
                Debug.LogWarning("缺少 Gate26 废弃船模型；两座副岛仍会正常载入。路径：Resources/Models/Environment/Gate26_CapsizedWreck.fbx");
                return;
            }

            GameObject wreckComposite = Instantiate(wreckPrefab, islandRoot, false);
            wreckComposite.name = "Capsized Wreck - Gate26 East Shore";

            // Guard against older composite exports: only ship and salvage
            // renderers belong in the playable scene.
            Renderer[] renderers = wreckComposite.GetComponentsInChildren<Renderer>(true);
            int wreckRendererCount = 0;
            for (int i = 0; i < renderers.Length; i++)
            {
                Renderer renderer = renderers[i];
                string objectName = renderer.gameObject.name;
                bool isWreckPiece = objectName.StartsWith("Wreck_", System.StringComparison.OrdinalIgnoreCase) ||
                    objectName.StartsWith("Debris_", System.StringComparison.OrdinalIgnoreCase);
                renderer.enabled = isWreckPiece;
                if (isWreckPiece) wreckRendererCount++;
            }

            if (wreckRendererCount == 0)
            {
                wreckComposite.SetActive(false);
                Debug.LogWarning("Gate26 废弃船 FBX 已载入，但没有找到 Wreck_ 或 Debris_ 网格；为避免显示重复岛屿，已隐藏组合模型。请检查 FBX 子物体名称。");
                return;
            }

            int hiddenVegetationCount = ClearVegetationFromWreckFootprint(renderers);
            Debug.Log($"Gate26 capsized wreck loaded ({wreckRendererCount} ship and salvage meshes); " +
                      $"cleared {hiddenVegetationCount} overlapping vegetation renderers from its impact site.");
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
                    renderer.enabled = visible && (renderer != coastalGridRenderer || waterSelection);
                }
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
            if (index < 0 || index >= Buildables.Length || !IsBuildableUnlocked(Buildables[index]))
            {
                return;
            }

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
                (Buildables[selectedBuildableIndex].Kind != BuildableKind.Building &&
                 Buildables[selectedBuildableIndex].Kind != BuildableKind.Water))
            {
                return;
            }

            rotationDegrees = (rotationDegrees + direction + 360) % 360;
            statusMessage = "建筑方向已旋转 " + rotationDegrees + "°。";
        }

        private GameObject CreatePlaceableObject(string assetName, string objectName)
        {
            GameObject root = new GameObject(objectName);
            string resourcePath = BuildingConstructionCatalog.TryGet(assetName, out BuildingConstructionCatalog.Entry entry)
                ? entry.finalResource : GetModelResourcePath(assetName);
            GameObject prefab = Resources.Load<GameObject>(resourcePath);
            if (prefab != null)
            {
                GameObject model = Instantiate(prefab, root.transform, false);
                model.name = assetName + " Model";
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
            string category = assetName == "IslandReference_V2" || assetName == "IslandReference_Gate25" ||
                assetName == SatelliteIslandResourceName || assetName == CapsizedWreckResourceName
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
            direction = Vector2Int.zero;
            if (constructionGrid == null || !constructionGrid.GetTerrain(anchor).HasLand ||
                constructionGrid.CellCenter(anchor).y > WaterPlaneHeight + 2f) return false;
            for (int i = 0; i < CardinalDirections.Length; i++)
            {
                Vector2Int candidate = CardinalDirections[i];
                Vector2Int sideDirection = candidate.x == 0 ? East : North;
                bool sideIsClear = true;
                for (int forward = -DockInlandCells; forward <= DockWaterwardCells && sideIsClear; forward++)
                {
                    for (int side = -DockHalfWidthCells; side <= DockHalfWidthCells; side++)
                    {
                        Vector2Int reservedCell = anchor + candidate * forward + sideDirection * side;
                        if (!constructionGrid.Contains(reservedCell) ||
                            (forward > 0 && !constructionGrid.IsCoastalWaterCell(reservedCell)) ||
                            (forward < 0 && !constructionGrid.GetTerrain(reservedCell).AllowsRoad) ||
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
                wood -= selected.WoodCost;
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

                wood -= selected.WoodCost;
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

                wood -= selected.WoodCost;
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

            wood -= selected.WoodCost;
            statusMessage = selected.Name + "开始施工，木材 -" + selected.WoodCost + "。";
        }

        private void OccupyCell(Vector2Int cell)
        {
            occupiedCells.Add(cell);
            if (grassCover != null) grassCover.ClearCell(cell);
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

        private enum BuildableKind
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
                    if (string.Equals(RequiredAssets[i], "ResearchStation_DeepSeek", System.StringComparison.Ordinal))
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

        private sealed class BuildableDefinition
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
                wood += refund;

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
                wood += roadRefund;
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

        private void StartMoveBuilding(PlacedBuildingData data)
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

            // Southwest landing bay water area for the rescue speedboat
            Vector3 boatPos = new Vector3(-8.5f, WaterPlaneHeight, -14.5f);
            if (constructionGrid.TrySample(-8, -14, out Vector3 sampleWater, out _))
            {
                boatPos = new Vector3(sampleWater.x, WaterPlaneHeight, sampleWater.z);
            }
            RescueBoatController.Spawn(boatPos, Quaternion.Euler(0f, -35f, 0f), mapRoot);

            // Initial crew members from the game lore ("玩家带着两名船员出发")
            Vector3 crew1Pos = new Vector3(2f, TileTop, 2f);
            if (constructionGrid.TrySample(2, 2, out Vector3 s1, out _)) crew1Pos = s1;
            SurvivorCharacterController.Spawn(crew1Pos, "阿岩", "搜救驾驶员", mapRoot);

            Vector3 crew2Pos = new Vector3(-2f, TileTop, 1f);
            if (constructionGrid.TrySample(-2, 1, out Vector3 s2, out _)) crew2Pos = s2;
            SurvivorCharacterController.Spawn(crew2Pos, "小海", "技术维修员", mapRoot);
        }


        private void InitializeColonySystems()
        {
            if (GetComponent<ColonyResourceManager>() == null) gameObject.AddComponent<ColonyResourceManager>();
            if (GetComponent<ColonyCitizenManager>() == null) gameObject.AddComponent<ColonyCitizenManager>();
            if (GetComponent<OceanSalvageManager>() == null) gameObject.AddComponent<OceanSalvageManager>();
            if (GetComponent<ColonySaveLoadManager>() == null) gameObject.AddComponent<ColonySaveLoadManager>();
            if (GetComponent<BuildingInspectorUI>() == null) gameObject.AddComponent<BuildingInspectorUI>();
            if (GetComponent<ColonyModalDialog>() == null) gameObject.AddComponent<ColonyModalDialog>();

            // Sync initial wood
            var res = ColonyResourceManager.Instance;
            if (res != null)
            {
                res.Add(ResourceType.Wood, wood);
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
            wood += refund;
            var res = ColonyResourceManager.Instance;
            if (res != null) res.Add(ResourceType.Wood, refund);

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
