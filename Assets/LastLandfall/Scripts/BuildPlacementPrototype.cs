using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>
    /// Self-contained graybox for the first settlement-building loop.
    /// Add this source to a Unity project, then press Play in any scene.
    /// </summary>
    public sealed class BuildPlacementPrototype : MonoBehaviour
    {
        private const int BoardWidth = 11;
        private const int BoardDepth = 9;
        private const float TileHeight = 0.32f;
        private const float TileTop = TileHeight * 0.5f;
        private const int HutCost = 20;

        private static readonly Rect PanelRect = new Rect(16f, 16f, 310f, 194f);

        private readonly HashSet<Vector2Int> occupiedCells = new HashSet<Vector2Int>();
        private readonly List<Material> ownedMaterials = new List<Material>();

        private Camera gameCamera;
        private GameObject residentHutPrefab;
        private GameObject previewHouse;
        private Renderer[] previewRenderers;
        private Material validPreviewMaterial;
        private Material invalidPreviewMaterial;
        private Material houseBodyMaterial;
        private Material houseRoofMaterial;

        private int wood = 100;
        private bool buildMode;
        private bool hasHoveredCell;
        private Vector2Int hoveredCell;
        private string statusMessage = "点击“小屋”开始建造。";

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void CreatePrototypeIfNeeded()
        {
            if (FindFirstObjectByType<BuildPlacementPrototype>() != null)
            {
                return;
            }

            GameObject root = new GameObject("Last Landfall - Build Prototype");
            root.AddComponent<BuildPlacementPrototype>();
        }

        private void Awake()
        {
            gameCamera = EnsureCamera();
            CreateMaterials();
            residentHutPrefab = Resources.Load<GameObject>("Models/ResidentHut");
            if (residentHutPrefab == null)
            {
                residentHutPrefab = Resources.Load<GameObject>("Models/ResidentHut_OBJ");
            }
            CreateLighting();
            CreateWater();
            CreateHighland();
            CreatePreviewHouse();
            PositionCamera();
        }

        private void OnGUI()
        {
            Event guiEvent = Event.current;
            UpdateHoveredCell(guiEvent.mousePosition);

            if (guiEvent.type == EventType.MouseDown)
            {
                if (guiEvent.button == 1)
                {
                    buildMode = false;
                    statusMessage = "已退出建造模式。";
                    guiEvent.Use();
                }
                else if (guiEvent.button == 0 && buildMode && !PanelRect.Contains(guiEvent.mousePosition) && hasHoveredCell)
                {
                    TryPlaceHut(hoveredCell);
                    guiEvent.Use();
                }
            }

            UpdatePreview();
            GUI.Box(PanelRect, GUIContent.none);
            GUI.Label(new Rect(30f, 28f, 280f, 28f), "LAST LANDFALL  /  高地建设原型");
            GUI.Label(new Rect(30f, 58f, 250f, 26f), "木材：" + wood);

            string buttonLabel = buildMode ? "小屋已选中（木材 20）" : "建造小屋（木材 20）";
            if (GUI.Button(new Rect(30f, 90f, 280f, 34f), buttonLabel))
            {
                buildMode = true;
                statusMessage = "把鼠标移到空地，左键放置；右键取消。";
            }

            GUI.Label(new Rect(30f, 132f, 280f, 30f), statusMessage);

            if (buildMode && hasHoveredCell)
            {
                GUI.Label(new Rect(30f, 164f, 280f, 24f), "地格：" + hoveredCell.x + ", " + hoveredCell.y);
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
            existing.orthographicSize = 7.5f;
            existing.clearFlags = CameraClearFlags.SolidColor;
            existing.backgroundColor = new Color(0.055f, 0.13f, 0.18f);
            return existing;
        }

        private void PositionCamera()
        {
            Vector3 target = new Vector3(0f, 0f, 0f);
            gameCamera.transform.position = target + new Vector3(10f, 13f, -10f);
            gameCamera.transform.LookAt(target);
        }

        private void CreateMaterials()
        {
            houseBodyMaterial = MakeMaterial(new Color(0.76f, 0.66f, 0.48f));
            houseRoofMaterial = MakeMaterial(new Color(0.43f, 0.27f, 0.19f));
            validPreviewMaterial = MakeMaterial(new Color(0.25f, 0.9f, 0.55f, 0.75f));
            invalidPreviewMaterial = MakeMaterial(new Color(0.95f, 0.24f, 0.2f, 0.75f));
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
            Light sun = FindFirstObjectByType<Light>();
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
            GameObject water = GameObject.CreatePrimitive(PrimitiveType.Plane);
            water.name = "Floodwater";
            water.transform.position = new Vector3(0f, -0.22f, 0f);
            water.transform.localScale = new Vector3(5f, 1f, 5f);
            water.GetComponent<Renderer>().sharedMaterial = MakeMaterial(new Color(0.08f, 0.27f, 0.34f));
            water.GetComponent<Collider>().enabled = false;
        }

        private void CreateHighland()
        {
            Material earthA = MakeMaterial(new Color(0.56f, 0.53f, 0.39f));
            Material earthB = MakeMaterial(new Color(0.61f, 0.57f, 0.42f));

            for (int x = 0; x < BoardWidth; x++)
            {
                for (int z = 0; z < BoardDepth; z++)
                {
                    Vector2Int cell = new Vector2Int(x, z);
                    if (!IsHighlandCell(cell))
                    {
                        continue;
                    }

                    GameObject tile = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    tile.name = "Highland Tile " + x + "-" + z;
                    tile.transform.position = CellCenter(cell) - Vector3.up * (TileHeight * 0.5f);
                    tile.transform.localScale = new Vector3(0.96f, TileHeight, 0.96f);
                    tile.GetComponent<Renderer>().sharedMaterial = ((x + z) % 2 == 0) ? earthA : earthB;
                    tile.GetComponent<Collider>().enabled = false;
                }
            }
        }

        private void CreatePreviewHouse()
        {
            previewHouse = CreateHouse("Building Preview", true);
            previewRenderers = previewHouse.GetComponentsInChildren<Renderer>();
            previewHouse.SetActive(false);
        }

        private GameObject CreateHouse(string objectName, bool isPreview)
        {
            GameObject root = new GameObject(objectName);

            if (residentHutPrefab != null)
            {
                GameObject model = Instantiate(residentHutPrefab, root.transform, false);
                model.name = "Resident Hut Model";
                return root;
            }

            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Cube);
            body.name = "House Body";
            body.transform.SetParent(root.transform, false);
            body.transform.localPosition = new Vector3(0f, 0.39f, 0f);
            body.transform.localScale = new Vector3(0.68f, 0.68f, 0.68f);
            body.GetComponent<Renderer>().sharedMaterial = isPreview ? validPreviewMaterial : houseBodyMaterial;
            body.GetComponent<Collider>().enabled = false;

            GameObject roof = GameObject.CreatePrimitive(PrimitiveType.Cube);
            roof.name = "House Roof";
            roof.transform.SetParent(root.transform, false);
            roof.transform.localPosition = new Vector3(0f, 0.79f, 0f);
            roof.transform.localScale = new Vector3(0.82f, 0.18f, 0.82f);
            roof.GetComponent<Renderer>().sharedMaterial = isPreview ? validPreviewMaterial : houseRoofMaterial;
            roof.GetComponent<Collider>().enabled = false;

            return root;
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
            Plane boardPlane = new Plane(Vector3.up, new Vector3(0f, TileTop, 0f));
            if (!boardPlane.Raycast(ray, out float distance))
            {
                return;
            }

            Vector3 point = ray.GetPoint(distance);
            int x = Mathf.FloorToInt(point.x + BoardWidth * 0.5f);
            int z = Mathf.FloorToInt(point.z + BoardDepth * 0.5f);
            if (x < 0 || x >= BoardWidth || z < 0 || z >= BoardDepth)
            {
                return;
            }

            hoveredCell = new Vector2Int(x, z);
            hasHoveredCell = true;
        }

        private void UpdatePreview()
        {
            if (previewHouse == null)
            {
                return;
            }

            bool showPreview = buildMode && hasHoveredCell;
            previewHouse.SetActive(showPreview);
            if (!showPreview)
            {
                return;
            }

            previewHouse.transform.position = CellCenter(hoveredCell);
            bool canBuild = CanPlaceHut(hoveredCell);
            Material previewMaterial = canBuild ? validPreviewMaterial : invalidPreviewMaterial;
            for (int i = 0; i < previewRenderers.Length; i++)
            {
                Material[] previewMaterials = previewRenderers[i].sharedMaterials;
                for (int materialIndex = 0; materialIndex < previewMaterials.Length; materialIndex++)
                {
                    previewMaterials[materialIndex] = previewMaterial;
                }

                previewRenderers[i].sharedMaterials = previewMaterials;
            }
        }

        private bool CanPlaceHut(Vector2Int cell)
        {
            return IsHighlandCell(cell) && !occupiedCells.Contains(cell) && wood >= HutCost;
        }

        private void TryPlaceHut(Vector2Int cell)
        {
            if (!IsHighlandCell(cell))
            {
                statusMessage = "这里是水面，无法建造。";
                return;
            }

            if (occupiedCells.Contains(cell))
            {
                statusMessage = "这块地已经有建筑了。";
                return;
            }

            if (wood < HutCost)
            {
                statusMessage = "木材不足，需要 " + HutCost + "。";
                return;
            }

            GameObject house = CreateHouse("居民小屋", false);
            house.transform.position = CellCenter(cell);
            occupiedCells.Add(cell);
            wood -= HutCost;
            statusMessage = "小屋建好了，木材 -" + HutCost + "。";
        }

        private bool IsHighlandCell(Vector2Int cell)
        {
            if (cell.x < 0 || cell.x >= BoardWidth || cell.y < 0 || cell.y >= BoardDepth)
            {
                return false;
            }

            float normalizedX = (cell.x - (BoardWidth - 1) * 0.5f) / (BoardWidth * 0.5f);
            float normalizedZ = (cell.y - (BoardDepth - 1) * 0.5f) / (BoardDepth * 0.5f);
            return normalizedX * normalizedX + normalizedZ * normalizedZ <= 0.78f;
        }

        private Vector3 CellCenter(Vector2Int cell)
        {
            float x = cell.x - BoardWidth * 0.5f + 0.5f;
            float z = cell.y - BoardDepth * 0.5f + 0.5f;
            return new Vector3(x, TileTop, z);
        }

    }
}
