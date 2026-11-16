using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>Owns the active world selection and draws its information at the bottom right.</summary>
    public sealed class BuildingInspectorUI : MonoBehaviour
    {
        private enum TargetKind { None, Building, Vessel, People, Lighthouse }

        private static readonly string[] BuildingTabs = { "概况", "运行", "管理" };
        private static readonly string[] PeopleTabs = { "档案", "行动" };
        private static readonly Color PanelFill = new Color32(19, 27, 35, 255);
        private static readonly Color HeaderFill = new Color32(31, 43, 54, 255);
        private static readonly Color PanelEdge = new Color32(76, 91, 103, 255);
        private static readonly Color Divider = new Color32(44, 57, 68, 255);

        private static BuildingInspectorUI instance;
        private BuildPlacementPrototype host;
        private TargetKind kind;
        private BuildPlacementPrototype.PlacedBuildingData building;
        private VesselOrdersUI vessel;
        private LighthouseSite lighthouse;
        private readonly List<SurvivorCharacterController> people = new List<SurvivorCharacterController>();
        private int selectedTab;
        private Vector2 scroll;

        private Font font;
        private readonly List<Texture2D> textures = new List<Texture2D>();
        private GUIStyle titleStyle, subtitleStyle, tabStyle, activeTabStyle, closeStyle;
        private GUIStyle nameStyle, valueStyle, sectionStyle, noteStyle, buttonStyle, dangerStyle;
        private float styleScale;
        private static float Scale => Mathf.Clamp(Mathf.Min(Screen.width / 1100f, Screen.height / 790f), .68f, 1.2f);

        public static Rect GetPanelRect()
        {
            float width = Mathf.Min(Screen.width, Mathf.Round(470f * Scale));
            float height = Mathf.Min(Screen.height, Mathf.Round(344f * Scale));
            return new Rect(Screen.width - width, Screen.height - height, width, height);
        }

        public static bool IsOpen => instance != null && instance.HasTarget;
        public static bool ContainsPoint(Vector2 point) => IsOpen && GetPanelRect().Contains(point);

        private bool HasTarget => kind switch
        {
            TargetKind.Building => building?.GameObject != null && building.GameObject.activeInHierarchy,
            TargetKind.Vessel => vessel != null && vessel.isActiveAndEnabled,
            TargetKind.People => people.Count > 0,
            TargetKind.Lighthouse => lighthouse != null,
            _ => false
        };

        private void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(this);
                return;
            }
            instance = this;
            host = GetComponent<BuildPlacementPrototype>();
        }

        private void OnDestroy()
        {
            if (instance == this) instance = null;
            if (font != null) Destroy(font);
            foreach (Texture2D texture in textures) Destroy(texture);
        }

        public static void Inspect(BuildPlacementPrototype.PlacedBuildingData target)
        {
            if (instance == null || target?.GameObject == null || instance.building == target) return;
            instance.Select(TargetKind.Building);
            instance.building = target;
        }

        internal static void Inspect(VesselOrdersUI target)
        {
            if (instance == null || target == null || instance.vessel == target) return;
            instance.Select(TargetKind.Vessel);
            instance.vessel = target;
        }

        internal static void Inspect(SurvivorCharacterController person, bool extend)
        {
            if (instance == null || person == null || person.IsAboard) return;
            bool keepSelection = instance.kind == TargetKind.People &&
                (extend || (instance.people.Count == 1 && instance.people[0] == person));
            if (!keepSelection) instance.Select(TargetKind.People);
            if (!instance.people.Contains(person)) instance.people.Add(person);
        }

        internal static void Inspect(LighthouseSite target)
        {
            if (instance == null || target == null || instance.lighthouse == target) return;
            instance.Select(TargetKind.Lighthouse);
            instance.lighthouse = target;
        }

        internal static bool IsInspecting(LighthouseSite target) =>
            instance != null && instance.kind == TargetKind.Lighthouse && instance.lighthouse == target;

        public static void Close()
        {
            if (instance != null && instance.kind != TargetKind.None) instance.Select(TargetKind.None);
        }

        private void Select(TargetKind target)
        {
            kind = target;
            building = null;
            vessel = null;
            lighthouse = null;
            people.Clear();
            selectedTab = 0;
            scroll = Vector2.zero;
            if (kind != TargetKind.None && host != null) host.PrepareInspectorSelection();
        }

        internal static bool TryIssueOrder(IslandConstructionGrid grid, Ray ray)
        {
            if (!IsOpen || grid == null) return false;
            if (instance.kind == TargetKind.Vessel)
            {
                instance.vessel.OrderSail(grid, ray);
                return true;
            }
            if (instance.kind != TargetKind.People) return false;

            if (grid.TryRaycast(ray, out RaycastHit hit))
            {
                foreach (var person in instance.people)
                {
                    if (person != null && !person.IsAboard &&
                        VesselGridNavigation.Find(grid, person.transform.position, hit.point, false, out var path))
                        person.RunRoute(path);
                }
            }
            return true;
        }

        internal static bool Hit(Transform target, Ray ray, ref float nearest, float padding = 0f)
        {
            bool hit = false;
            foreach (Renderer renderer in target.GetComponentsInChildren<Renderer>())
            {
                if (!renderer.enabled) continue;
                Bounds bounds = renderer.bounds;
                bounds.Expand(padding);
                if (!bounds.IntersectRay(ray, out float distance) || distance >= nearest) continue;
                nearest = distance;
                hit = true;
            }
            return hit;
        }

        internal static void DrawSelected()
        {
            if (instance == null || ColonyModalDialog.IsDialogOpen) return;
            if (instance.kind == TargetKind.People)
                instance.people.RemoveAll(person => person == null || person.IsAboard);
            if (IsOpen) instance.Draw();
        }

        private void Draw()
        {
            EnsureStyles();
            float s = styleScale;
            Rect panel = GetPanelRect();
            string title, subtitle;
            string[] tabs;
            switch (kind)
            {
                case TargetKind.Building:
                    title = building.Definition.Name;
                    subtitle = CategoryName(building.Definition.Category);
                    tabs = BuildingTabs;
                    break;
                case TargetKind.Vessel:
                    title = vessel.InspectorTitle;
                    subtitle = "救援艇";
                    tabs = VesselOrdersUI.InspectorTabs;
                    break;
                case TargetKind.People:
                    title = people.Count == 1 ? people[0].ResidentName : $"已选岛民 · {people.Count} 人";
                    subtitle = people.Count == 1 ? people[0].Profession : "人员编组";
                    tabs = PeopleTabs;
                    break;
                default:
                    title = "灯塔重建";
                    subtitle = "群岛航标";
                    tabs = LighthouseSite.InspectorTabs;
                    break;
            }

            Fill(panel, PanelFill);
            Fill(new Rect(panel.x, panel.y, panel.width, 59f * s), HeaderFill);
            Fill(new Rect(panel.x, panel.y, panel.width, 1f), PanelEdge);
            Fill(new Rect(panel.x, panel.y, 1f, panel.height), PanelEdge);
            Fill(new Rect(panel.x + 1f, panel.y + 14f * s, 3f * s, 27f * s), HudTheme.BrassMid);
            GUI.Label(new Rect(panel.x + 15f * s, panel.y + 7f * s, panel.width - 58f * s, 27f * s), title, titleStyle);
            GUI.Label(new Rect(panel.x + 15f * s, panel.y + 34f * s, panel.width - 58f * s, 18f * s), subtitle, subtitleStyle);
            if (GUI.Button(new Rect(panel.xMax - 39f * s, panel.y + 11f * s, 28f * s, 28f * s), "×", closeStyle))
            {
                Close();
                return;
            }

            float tabY = panel.y + 60f * s;
            float tabWidth = (panel.width - 2f) / tabs.Length;
            float tabHeight = 29f * s;
            Fill(new Rect(panel.x + 1f, tabY + tabHeight - 1f, panel.width - 1f, 1f), Divider);
            for (int i = 0; i < tabs.Length; i++)
            {
                Rect tab = new Rect(panel.x + 1f + i * tabWidth, tabY, tabWidth, tabHeight);
                bool active = i == selectedTab;
                if (GUI.Button(tab, tabs[i], active ? activeTabStyle : tabStyle) && !active)
                {
                    selectedTab = i;
                    scroll = Vector2.zero;
                    return;
                }
                if (active) Fill(new Rect(tab.x, tab.yMax - 2f * s, tab.width, 2f * s), HudTheme.BrassGold);
            }

            var body = new Rect(panel.x + 14f * s, panel.y + 100f * s, panel.width - 28f * s, panel.height - 110f * s);
            GUILayout.BeginArea(body);
            scroll = GUILayout.BeginScrollView(scroll);
            switch (kind)
            {
                case TargetKind.Building: DrawBuilding(); break;
                case TargetKind.Vessel: vessel.DrawInspectionPage(this, selectedTab); break;
                case TargetKind.People: DrawPeople(); break;
                case TargetKind.Lighthouse: lighthouse.DrawInspectionPage(this, selectedTab); break;
            }
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }

        private void DrawBuilding()
        {
            var construction = building.GameObject.GetComponent<BuildingConstructionController>();
            bool complete = construction == null || construction.IsComplete;
            if (selectedTab == 0)
            {
                if (complete) Row("施工状态", "已完工");
                else Meter("施工进度", construction.CurrentPhaseName + $" · {construction.Progress:P0}", construction.Progress);
                Row("地格位置", $"{building.Anchor.x}, {building.Anchor.y}");
                Row("朝向", $"{building.Rotation}°");
                Vector2Int size = building.Definition.Kind == BuildPlacementPrototype.BuildableKind.Dock
                    ? new Vector2Int(7, 9)
                    : new Vector2Int(building.Definition.Width, building.Definition.Depth);
                Row("占地", $"{size.x} × {size.y} 格");
                Row("建造用料", $"{building.WoodCost} 木材");
                return;
            }

            if (selectedTab == 1)
            {
                Row("运行状态", complete ? "已完工" : "施工中");
                if (!complete) return;
                if (building.Definition.Kind == BuildPlacementPrototype.BuildableKind.Dock)
                {
                    var boat = RescueBoatController.ActiveVessel;
                    var orders = boat != null ? boat.GetComponent<VesselOrdersUI>() : null;
                    Row("救援艇", orders != null && orders.IsMooredAt(building.GameObject.transform) ? "已靠泊" : "未靠泊");
                }
                else if (building.Definition.Category == BuildPlacementPrototype.BuildCategory.Residential)
                {
                    var citizens = ColonyCitizenManager.Instance;
                    if (citizens != null) Row("聚落住房", $"{citizens.TotalPopulation} 人 / {citizens.GetHousingCapacity()} 床位");
                }

                if (host != null)
                {
                    Row("科技效率", $"{host.GetBuildingEfficiencyMultiplier(building.Definition.AssetName):P0}");
                    Row("相邻道路", host.HasAdjacentRoad(building) ? "有" : "无");
                }
                if (ColonyResourceManager.Instance is { } resources)
                    Row("聚落供电余量", $"{resources.PowerSurplus:+0.0;-0.0;0.0}");
                return;
            }

            Section("移动建筑");
            Note("选择新的建造位置。");
            if (ActionButton("移动建筑", host != null))
            {
                var target = building;
                Close();
                if (host != null) host.StartMoveBuilding(target);
                return;
            }

            Section("拆除建筑");
            int refund = Mathf.Max(1, Mathf.RoundToInt(building.WoodCost * .5f));
            Note($"拆除后释放占地并返还 {refund} 木材。");
            if (ActionButton("拆除建筑", host != null, danger: true))
            {
                var target = building;
                ColonyModalDialog.Show("拆除建筑", $"拆除{target.Definition.Name}并返还 {refund} 木材？",
                    () =>
                    {
                        if (building == target) Close();
                        if (host != null && target.GameObject != null) host.DemolishBuilding(target);
                    }, severity: DialogSeverity.Danger, confirmLabel: "确认拆除");
            }
        }

        private void DrawPeople()
        {
            if (selectedTab == 0)
            {
                foreach (var person in people)
                {
                    if (people.Count > 1) Section(person.ResidentName);
                    Row("职业", person.Profession);
                    Row("健康", $"{person.HealthPercent:0}%");
                    Row("士气", $"{person.MoralePercent:0}%");
                    Row("状态", PersonState(person));
                }
                return;
            }

            foreach (var person in people) Row(person.ResidentName, PersonState(person));
            Note("点击陆地安排移动。按住 Shift 点击岛民可加入选中。");
            if (ActionButton("取消移动指令", people.Exists(person => person.IsRunning)))
                foreach (var person in people) person.CancelOrder();
        }

        private static string PersonState(SurvivorCharacterController person) =>
            person.IsRunning ? "正在执行移动指令" : person.IsWalking ? "走动中" : "待命";

        internal void Row(string name, string value)
        {
            GUILayout.BeginHorizontal(GUILayout.Height(25f * styleScale));
            GUILayout.Label(name, nameStyle, GUILayout.Width(104f * styleScale));
            GUILayout.Label(value, valueStyle, GUILayout.ExpandWidth(true));
            GUILayout.EndHorizontal();
            Fill(GUILayoutUtility.GetRect(1f, 1f, GUILayout.ExpandWidth(true)), Divider);
        }

        internal void Section(string text)
        {
            GUILayout.Space(6f * styleScale);
            GUILayout.Label(text, sectionStyle);
        }

        internal void Note(string text)
        {
            GUILayout.Space(3f * styleScale);
            GUILayout.Label(text, noteStyle, GUILayout.ExpandWidth(true));
        }

        internal void Meter(string name, string value, float fraction, Color? color = null)
        {
            Row(name, value);
            Rect track = GUILayoutUtility.GetRect(1f, 4f * styleScale, GUILayout.ExpandWidth(true));
            Fill(track, HeaderFill);
            track.width *= Mathf.Clamp01(fraction);
            Fill(track, color ?? HudTheme.BrassGold);
            GUILayout.Space(4f * styleScale);
        }

        internal bool ActionButton(string text, bool enabled = true, bool danger = false)
        {
            bool previous = GUI.enabled;
            GUI.enabled = previous && enabled;
            bool click = GUILayout.Button(text, danger ? dangerStyle : buttonStyle,
                GUILayout.Height(29f * styleScale), GUILayout.ExpandWidth(true));
            GUI.enabled = previous;
            return click;
        }

        private static string CategoryName(BuildPlacementPrototype.BuildCategory category) => category switch
        {
            BuildPlacementPrototype.BuildCategory.Residential => "居住建筑",
            BuildPlacementPrototype.BuildCategory.Production => "生产设施",
            BuildPlacementPrototype.BuildCategory.Transportation => "交通设施",
            _ => "公共设施"
        };

        private void EnsureStyles()
        {
            float scale = Scale;
            if (titleStyle != null && Mathf.Approximately(styleScale, scale)) return;
            if (titleStyle == null)
            {
                font = Font.CreateDynamicFontFromOSFont(new[] { "Microsoft YaHei", "Noto Sans CJK SC", "Arial" }, 18);
                var idle = Solid(new Color32(34, 47, 59, 255));
                var hover = Solid(new Color32(52, 68, 82, 255));
                var active = Solid(new Color32(57, 65, 68, 255));
                tabStyle = MakeButton(null, hover, active, HudTheme.Muted);
                activeTabStyle = MakeButton(active, active, active, HudTheme.BrassGold);
                closeStyle = MakeButton(null, hover, active, HudTheme.Text);
                buttonStyle = MakeButton(idle, hover, active, HudTheme.Text);
                dangerStyle = MakeButton(Solid(new Color32(76, 40, 42, 255)),
                    Solid(new Color32(107, 51, 53, 255)), idle, new Color32(255, 210, 202, 255));
                titleStyle = TextStyle(HudTheme.Text, TextAnchor.MiddleLeft, bold: true);
                subtitleStyle = TextStyle(HudTheme.FrostCyan, TextAnchor.MiddleLeft);
                nameStyle = TextStyle(HudTheme.Muted, TextAnchor.MiddleLeft);
                valueStyle = TextStyle(HudTheme.Text, TextAnchor.MiddleRight, bold: true);
                sectionStyle = TextStyle(HudTheme.FrostCyan, TextAnchor.MiddleLeft, bold: true);
                noteStyle = TextStyle(HudTheme.Muted, TextAnchor.UpperLeft);
                noteStyle.wordWrap = true;
            }

            styleScale = scale;
            titleStyle.fontSize = Mathf.RoundToInt(20f * scale);
            closeStyle.fontSize = Mathf.RoundToInt(21f * scale);
            int bodySize = Mathf.Max(10, Mathf.RoundToInt(14f * scale));
            subtitleStyle.fontSize = nameStyle.fontSize = valueStyle.fontSize = noteStyle.fontSize = bodySize;
            tabStyle.fontSize = activeTabStyle.fontSize = sectionStyle.fontSize =
                buttonStyle.fontSize = dangerStyle.fontSize = bodySize;
        }

        private GUIStyle TextStyle(Color color, TextAnchor anchor, bool bold = false) => new GUIStyle(GUI.skin.label)
        {
            font = font,
            fontStyle = bold ? FontStyle.Bold : FontStyle.Normal,
            alignment = anchor,
            clipping = TextClipping.Clip,
            padding = new RectOffset(0, 2, 2, 2),
            normal = { textColor = color }
        };

        private GUIStyle MakeButton(Texture2D normal, Texture2D hover, Texture2D active, Color text) =>
            new GUIStyle(GUI.skin.button)
            {
                font = font,
                alignment = TextAnchor.MiddleCenter,
                fontStyle = FontStyle.Bold,
                border = new RectOffset(),
                padding = new RectOffset(6, 6, 2, 2),
                normal = { background = normal, textColor = text },
                hover = { background = hover, textColor = HudTheme.Text },
                focused = { background = normal, textColor = text },
                active = { background = active, textColor = HudTheme.Text }
            };

        private Texture2D Solid(Color color)
        {
            var texture = new Texture2D(1, 1, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave };
            texture.SetPixel(0, 0, color);
            texture.Apply(false, true);
            textures.Add(texture);
            return texture;
        }

        private static void Fill(Rect rect, Color color)
        {
            if (Event.current.type != EventType.Repaint) return;
            Color previous = GUI.color;
            GUI.color = color;
            GUI.DrawTexture(rect, Texture2D.whiteTexture);
            GUI.color = previous;
        }
    }
}
