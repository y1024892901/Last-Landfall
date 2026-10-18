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
        private const string IslandRootName = "Playable Island - Reference V2";
        private const string PlaySpaceRootName = "Island Play Space - Rotate and Pan";
        private const float CameraRotationSpeed = 28f;
        private const float TopBarImageAspect = 2172f / 160f;
        private const float TopBarTextureTopInset = 6f / 160f;
        private const int HeaderResourceSlotCount = 8;
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
        private const float SidebarCategorySpacing = SidebarCategoryButtonSize + 8f;

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
        private static readonly string[] HeaderButtonResourceNames =
        {
            "CameraReset", "IslandView", "GridToggle", "ControlsHelp"
        };
        private static readonly string[] HeaderResourceIconNames =
        {
            "Wood", "Food", "Water", "Metal", "Fuel", "Power", "Ore", "Medical"
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
        private Transform waterTransform;
        private Material waterMaterial;
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
        private GUIStyle headerTitleStyle;
        private GUIStyle headerSubtitleStyle;
        private GUIStyle headerResourceValueStyle;
        private Texture2D lastLandfallHeaderImage;
        private Texture2D[] headerResourceIcons;
        private Texture2D[] headerButtonImages;
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
            CreateGridOverlay();
            EnsureHeaderAssetsLoaded();
            LoadBuildIcons();
            PositionCamera();
        }

        private void EnsureHeaderAssetsLoaded()
        {
            bool hasMissingAsset = lastLandfallHeaderImage == null ||
                headerButtonImages == null || headerButtonImages.Length != HeaderButtonResourceNames.Length ||
                headerResourceIcons == null || headerResourceIcons.Length != HeaderResourceIconNames.Length;
            if (!hasMissingAsset)
            {
                for (int i = 0; i < headerButtonImages.Length; i++)
                {
                    hasMissingAsset |= headerButtonImages[i] == null;
                }

                for (int i = 0; i < headerResourceIcons.Length; i++)
                {
                    hasMissingAsset |= headerResourceIcons[i] == null;
                }
            }

            if (!hasMissingAsset || Time.unscaledTime < nextHeaderAssetRetryTime)
            {
                return;
            }

            nextHeaderAssetRetryTime = Time.unscaledTime + 0.5f;
            if (lastLandfallHeaderImage == null)
            {
                lastLandfallHeaderImage = Resources.Load<Texture2D>("UI/LastLandfallHeader");
            }

            if (headerButtonImages == null || headerButtonImages.Length != HeaderButtonResourceNames.Length)
            {
                headerButtonImages = new Texture2D[HeaderButtonResourceNames.Length];
            }

            for (int i = 0; i < HeaderButtonResourceNames.Length; i++)
            {
                if (headerButtonImages[i] == null)
                {
                    headerButtonImages[i] = Resources.Load<Texture2D>("UI/HeaderButtons/" + HeaderButtonResourceNames[i]);
                }
            }

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

        private void OnGUI()
        {
            EnsureGuiStyles();
            Event guiEvent = Event.current;
            UpdateHoveredCell(guiEvent.mousePosition);
            Rect panelRect = GetPanelRect();
            Rect topBarRect = GetTopBarRect();
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
                             guiEvent.mousePosition, panelRect, topBarRect, isBuildMenuOpen) && hasHoveredCell)
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
            return new Rect(16f, GetTopBarTop() + GetTopBarHeight() + 10f + index * SidebarCategorySpacing,
                SidebarCategoryButtonSize, SidebarCategoryButtonSize);
        }

        private Rect GetTopBarRect()
        {
            return new Rect(0f, GetTopBarTop(), Screen.width, GetTopBarHeight());
        }

        private static float GetTopBarTop()
        {
            return -GetTopBarHeight() * TopBarTextureTopInset;
        }

        private static float GetTopBarHeight()
        {
            return Mathf.Max(1f, Screen.width / TopBarImageAspect);
        }

        private bool IsPointerOverUi(Vector2 pointer, Rect panelRect, Rect topBarRect, bool isPanelOpen)
        {
            if (topBarRect.Contains(pointer) || (isPanelOpen && panelRect.Contains(pointer)))
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

            headerTitleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 16,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleLeft,
                clipping = TextClipping.Clip
            };
            headerTitleStyle.normal.textColor = new Color(0.11f, 0.16f, 0.12f);
            headerSubtitleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 11,
                alignment = TextAnchor.MiddleLeft,
                clipping = TextClipping.Clip
            };
            headerSubtitleStyle.normal.textColor = new Color(0.23f, 0.25f, 0.18f);

            headerResourceValueStyle = CreateHeaderLabelStyle(12, FontStyle.Bold, TextAnchor.MiddleCenter,
                new Color(0.96f, 0.89f, 0.67f));
            headerResourceValueStyle.wordWrap = false;

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
            if (lastLandfallHeaderImage == null)
            {
                return;
            }

            GUI.DrawTexture(rect, lastLandfallHeaderImage, ScaleMode.StretchToFill, true);

            Rect titleRect = new Rect(rect.x + rect.width * 0.067f, rect.y + rect.height * 0.22f,
                rect.width * 0.155f, rect.height * 0.28f);
            headerTitleStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(rect.height * 0.20f), 13, 27);
            headerTitleStyle.alignment = TextAnchor.MiddleCenter;
            GUI.Label(titleRect, "LAST LANDFALL", headerTitleStyle);
            headerSubtitleStyle.fontSize = Mathf.Clamp(Mathf.RoundToInt(rect.height * 0.12f), 9, 16);
            headerSubtitleStyle.alignment = TextAnchor.MiddleCenter;
            GUI.Label(new Rect(titleRect.x, rect.y + rect.height * 0.51f, titleRect.width, rect.height * 0.20f),
                "据点物资", headerSubtitleStyle);

            const float slotStep = 0.068f;
            float slotCenterY = rect.y + rect.height * 0.495f;
            float iconSize = rect.height * 0.27f;
            for (int i = 0; i < HeaderResourceSlotCount; i++)
            {
                float iconCenterX = rect.x + rect.width * (0.257f + i * slotStep);
                float amountCenterX = iconCenterX + rect.width * 0.021f;
                Rect iconRect = new Rect(iconCenterX - iconSize * 0.5f,
                    slotCenterY - iconSize * 0.5f, iconSize, iconSize);
                Rect amountRect = new Rect(amountCenterX - rect.width * 0.017f,
                    slotCenterY - rect.height * 0.18f, rect.width * 0.034f, rect.height * 0.36f);
                if (headerResourceIcons != null && i < headerResourceIcons.Length && headerResourceIcons[i] != null)
                {
                    GUI.DrawTexture(iconRect, headerResourceIcons[i], ScaleMode.ScaleToFit, true);
                }
                string amount = i == 0 ? wood.ToString("0", CultureInfo.InvariantCulture) : "0";
                int designFontSize = Mathf.RoundToInt(rect.height * 0.19f);
                int fittingFontSize = Mathf.FloorToInt(amountRect.width / Mathf.Max(1f, amount.Length * 0.62f));
                headerResourceValueStyle.fontSize = Mathf.Clamp(Mathf.Min(designFontSize, fittingFontSize), 8, 20);
                GUI.Label(amountRect, amount, headerResourceValueStyle);
            }

            DrawHeaderButtons(rect);
        }

        private void DrawHeaderButtons(Rect rect)
        {
            if (headerButtonImages == null)
            {
                return;
            }

            string[] tooltips = { "重置视角", "切换俯视", "显示或隐藏网格", "设置" };
            float[] buttonCenters = { 0.8275f, 0.8745f, 0.9215f, 0.968f };
            float buttonSize = rect.height * 0.52f;
            float hitSize = rect.height * 0.52f;
            Vector2 pointer = Event.current.mousePosition;
            int buttonCount = Mathf.Min(headerButtonImages.Length,
                Mathf.Min(tooltips.Length, Mathf.Min(buttonCenters.Length, headerButtonFlashUntil.Length)));
            for (int i = 0; i < buttonCount; i++)
            {
                float centerX = rect.x + rect.width * buttonCenters[i];
                Rect hitRect = new Rect(centerX - hitSize * 0.5f,
                    rect.y + (rect.height - hitSize) * 0.5f, hitSize, hitSize);
                bool clicked = GUI.Button(hitRect, new GUIContent(string.Empty, tooltips[i]), transparentButtonStyle);
                if (clicked)
                {
                    headerButtonFlashUntil[i] = Time.unscaledTime + 0.16f;
                    ActivateHeaderButton(i);
                }

                Texture2D buttonImage = headerButtonImages[i];
                if (buttonImage == null)
                {
                    continue;
                }

                bool hovered = hitRect.Contains(pointer);
                bool pressed = (hovered && Input.GetMouseButton(0)) || Time.unscaledTime < headerButtonFlashUntil[i];
                float drawSize = buttonSize;
                Rect imageRect = new Rect(centerX - drawSize * 0.5f,
                    rect.y + (rect.height - drawSize) * 0.5f, drawSize, drawSize);
                Color previousColor = GUI.color;
                if (pressed)
                {
                    GUI.color = new Color(0.76f, 0.76f, 0.76f, 1f);
                }
                else if (i == 2 && !isBuildGridVisible)
                {
                    GUI.color = new Color(0.58f, 0.58f, 0.58f, 0.86f);
                }
                else if (hovered)
                {
                    GUI.color = new Color(1.08f, 1.06f, 0.96f, 1f);
                }

                GUI.DrawTexture(imageRect, buttonImage, ScaleMode.ScaleToFit, true);
                GUI.color = previousColor;
            }
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

            if (hasArtwork)
            {
                Rect first = GetSidebarCategoryButtonRect(0);
                SidebarCategoryArtwork.DrawRail(new Rect(first.x - 4f, first.y - 4f,
                    first.width + 8f, (SidebarCategoryCount - 1) * SidebarCategorySpacing + first.height + 8f));
            }

            for (int i = 0; i < SidebarCategoryCount; i++)
            {
                Rect rect = GetSidebarCategoryButtonRect(i);
                SidebarCategory category = (SidebarCategory)i;
                bool selected = isBuildMenuOpen && activeSidebarCategory == category;
                GUIStyle buttonStyle = hasArtwork ? transparentButtonStyle
                    : selected ? sidebarCategorySelectedButtonStyle : sidebarCategoryButtonStyle;
                bool hovered = rect.Contains(Event.current.mousePosition);
                if (GUI.Button(rect, GUIContent.none, buttonStyle))
                {
                    activeSidebarCategory = category;
                    isBuildMenuOpen = true;
                    selectedBuildableIndex = -1;
                    hasLastRoadCell = false;
                    hoverMessage = string.Empty;
                    SetBuildGridVisibility(false);
                }

                selected = isBuildMenuOpen && activeSidebarCategory == category;
                if (hasArtwork && SidebarCategoryArtwork.TryDraw(rect, i, selected, hovered,
                    hovered && Input.GetMouseButton(0)))
                {
                    continue;
                }

                Texture2D icon = sidebarCategoryIcons[i];
                if (icon != null)
                {
                    Rect iconRect = new Rect(rect.x + 14f, rect.y + 5f, rect.width - 28f, 28f);
                    GUI.DrawTexture(iconRect, icon, ScaleMode.ScaleToFit, true);
                }

                GUI.Label(new Rect(rect.x + 1f, rect.y + 33f, rect.width - 2f, 17f),
                    SidebarCategoryNames[i], sidebarCategoryLabelStyle);
            }
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
            Light sun = FindAnyObjectByType<Light>();
            if (sun == null)
            {
                GameObject lightObject = new GameObject("Prototype Sun");
                sun = lightObject.AddComponent<Light>();
                sun.type = LightType.Directional;
                sun.intensity = 1.2f;
                lightObject.transform.rotation = Quaternion.Euler(45f, -35f, 0f);
            }
        }

        private void CreateWater()
        {
            GameObject water = new GameObject("Floodwater | animated teal shallows and foam");
            water.transform.SetParent(mapRoot, false);
            waterTransform = water.transform;
            UpdateWaterTransform();

            MeshFilter meshFilter = water.AddComponent<MeshFilter>();
            MeshRenderer meshRenderer = water.AddComponent<MeshRenderer>();
            meshFilter.sharedMesh = CreateWaterMesh(160, FloodwaterPlaneSize);

            Shader waterShader = Shader.Find("LastLandfall/Stylized Floodwater");
            if (waterShader == null)
            {
                waterShader = Shader.Find("Universal Render Pipeline/Lit");
            }

            waterMaterial = new Material(waterShader);
            waterMaterial.name = "Floodwater - Turquoise Shelf, Currents and Shore Foam";
            if (waterMaterial.HasProperty("_DeepColor"))
            {
                waterMaterial.SetColor("_DeepColor", new Color(0.018f, 0.09f, 0.20f));
                waterMaterial.SetColor("_MidColor", new Color(0.035f, 0.25f, 0.36f));
                waterMaterial.SetColor("_ShallowColor", new Color(0.15f, 0.47f, 0.44f));
                waterMaterial.SetColor("_FoamColor", new Color(0.90f, 0.93f, 0.81f));
                waterMaterial.SetFloat("_FoamPixelRadius", 6f);
                waterMaterial.SetFloat("_FoamDepthRange", 2.1f);
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
                if (objectName == IslandRootName || objectName == "IslandReference_V2")
                {
                    sceneTransforms[i].gameObject.SetActive(false);
                }
            }

            GameObject islandPrefab = Resources.Load<GameObject>("Models/IslandReference_V2");
            if (islandPrefab == null)
            {
                Debug.LogError("缺少岛屿模型：Resources/Models/IslandReference_V2.fbx");
                return;
            }

            GameObject island = InstantiateIslandResource(islandPrefab, IslandRootName);
            EnsureIslandMaterials(island);
            Collider[] importedColliders = island.GetComponentsInChildren<Collider>(true);
            for (int i = 0; i < importedColliders.Length; i++)
            {
                importedColliders[i].enabled = false;
            }

            Renderer[] islandRenderers = island.GetComponentsInChildren<Renderer>(true);
            for (int i = 0; i < islandRenderers.Length; i++)
            {
                Material[] islandMaterials = islandRenderers[i].sharedMaterials;
                for (int materialIndex = 0; materialIndex < islandMaterials.Length; materialIndex++)
                {
                    Material material = islandMaterials[materialIndex];
                    if (material != null && material.shader != null &&
                        material.shader.name == "LastLandfall/Reference Island Terrain" &&
                        material.name.IndexOf("earth", System.StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        islandBareEarthMaterial = material;
                        break;
                    }
                }

                Bounds bounds = islandRenderers[i].bounds;
                if (bounds.max.y <= WaterPlaneHeight)
                {
                    continue;
                }
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

            // Sample the exact visible V2 mesh, including every mountain and reef.
            // The coarser closed collision export is unsuitable for a surface overlay.
            islandTerrainMeshes = island.GetComponentsInChildren<MeshFilter>(true);
            List<MeshCollider> surfaces = new List<MeshCollider>();
            Bounds localBounds = default;
            bool hasBounds = false;
            foreach (MeshFilter filter in islandTerrainMeshes)
            {
                if (filter.sharedMesh == null) continue;
                MeshCollider collider = filter.GetComponent<MeshCollider>();
                if (collider == null) collider = filter.gameObject.AddComponent<MeshCollider>();
                collider.sharedMesh = filter.sharedMesh;
                collider.enabled = true;
                surfaces.Add(collider);
                Bounds bounds = filter.sharedMesh.bounds;
                for (int corner = 0; corner < 8; corner++)
                {
                    Vector3 point = bounds.center + Vector3.Scale(bounds.extents, new Vector3(
                        (corner & 1) == 0 ? -1f : 1f,
                        (corner & 2) == 0 ? -1f : 1f,
                        (corner & 4) == 0 ? -1f : 1f));
                    point = mapRoot.InverseTransformPoint(filter.transform.TransformPoint(point));
                    if (!hasBounds) { localBounds = new Bounds(point, Vector3.zero); hasBounds = true; }
                    else localBounds.Encapsulate(point);
                }
            }
            islandLandColliders = surfaces.ToArray();
            Physics.SyncTransforms();
            constructionGrid = new IslandConstructionGrid(mapRoot, islandLandColliders, localBounds, WaterPlaneHeight);
        }

        private GameObject InstantiateIslandResource(GameObject prefab, string objectName)
        {
            // The wrapper applies game units and world heading. Its child retains the FBX
            // importer's own axis conversion, which can differ between the two resources.
            GameObject root = new GameObject(objectName);
            root.transform.SetParent(mapRoot, false);
            root.transform.localPosition = new Vector3(0f, IslandVerticalOffset, 0f);
            root.transform.rotation = Quaternion.AngleAxis(180f, Vector3.up) * mapRoot.rotation;
            root.transform.localScale = Vector3.one * IslandHorizontalScale;
            GameObject imported = Instantiate(prefab, root.transform, false);
            imported.transform.localPosition = prefab.transform.localPosition;
            imported.transform.localRotation = prefab.transform.localRotation;
            imported.transform.localScale = prefab.transform.localScale;
            return root;
        }

        private void EnsureIslandMaterials(GameObject island)
        {
            Material earthFallback = null;
            Material rockFallback = null;
            Renderer[] renderers = island.GetComponentsInChildren<Renderer>(true);
            for (int rendererIndex = 0; rendererIndex < renderers.Length; rendererIndex++)
            {
                Material[] materials = renderers[rendererIndex].sharedMaterials;
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
                    if (materialIndex == 0)
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
            GameObject prefab = Resources.Load<GameObject>("Models/" + assetName);
            if (prefab != null)
            {
                GameObject model = Instantiate(prefab, root.transform, false);
                model.name = assetName + " Model";
                if (assetName.StartsWith("Road"))
                {
                    CenterRoadModelOnCell(root.transform, model.transform);
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

        private static void CenterRoadModelOnCell(Transform root, Transform model)
        {
            Renderer[] renderers = model.GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0)
            {
                return;
            }

            Bounds modelBounds = renderers[0].bounds;
            for (int i = 1; i < renderers.Length; i++)
            {
                modelBounds.Encapsulate(renderers[i].bounds);
            }

            Vector3 localCenter = root.InverseTransformPoint(modelBounds.center);
            model.localPosition -= new Vector3(localCenter.x, 0f, localCenter.z);
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
