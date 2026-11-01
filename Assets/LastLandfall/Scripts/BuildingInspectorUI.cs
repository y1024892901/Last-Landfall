using System;
using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>
    /// Displays detailed facility data, operational status, worker assignments,
    /// power grid connectivity, and action triggers when clicking an existing building.
    /// Anchored to the BOTTOM-LEFT corner by default, and FULLY DRAGGABLE anywhere on screen.
    /// Non-transparent opaque Victorian nautical console with Tabbed Navigation.
    /// </summary>
    public sealed class BuildingInspectorUI : MonoBehaviour
    {
        private static BuildingInspectorUI instance;
        public static BuildingInspectorUI Instance => instance;

        private bool isOpen;
        private BuildPlacementPrototype.PlacedBuildingData currentBuilding;
        private Rect currentPanelRect;
        private float openAnimProgress = 1f;
        private int selectedTabIndex = 0;

        // Window docked flush to bottom-right

        private static readonly string[] TabNames = { "概况", "生产/协同", "操作管理" };

        private GUIStyle panelStyle;
        private GUIStyle cardStyle;
        private GUIStyle titleStyle;
        private GUIStyle subtitleStyle;
        private GUIStyle labelStyle;
        private GUIStyle valueStyle;
        private GUIStyle statusStyle;
        private GUIStyle activeTabStyle;
        private GUIStyle inactiveTabStyle;
        private GUIStyle buttonStyle;
        private GUIStyle dangerButtonStyle;
        private GUIStyle closeButtonStyle;
        private GUIStyle dragHintStyle;

        private readonly List<Texture2D> ownedTextures = new List<Texture2D>();

        public static Rect GetPanelRect()
        {
            float width = Mathf.Clamp(Screen.width * 0.28f, 380f, 440f);
            float height = Mathf.Clamp(Screen.height * 0.36f, 320f, 380f);
            float x = Screen.width - width;
            float y = Screen.height - height;
            return new Rect(x, y, width, height);
        }

        public static Rect PanelRect => GetPanelRect();
        public static void SetPanelPosition(Vector2 position) { /* Panel is docked by the current HUD layout. */ }
        public static bool ContainsPoint(Vector2 point) => IsOpen && GetPanelRect().Contains(point);
        public static bool IsOpen => (instance != null && instance.isOpen) || VesselOrdersUI.Selected != null;

        private void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(gameObject);
                return;
            }
            instance = this;
        }

        private void OnDestroy()
        {
            for (int i = 0; i < ownedTextures.Count; i++)
            {
                if (ownedTextures[i] != null)
                {
                    Destroy(ownedTextures[i]);
                }
            }
            ownedTextures.Clear();
        }

        public static void Inspect(BuildPlacementPrototype.PlacedBuildingData building)
        {
            if (instance == null)
            {
                var host = new GameObject("Building Inspector UI");
                instance = host.AddComponent<BuildingInspectorUI>();
            }

            if (building != null) VesselOrdersUI.ClearSelection();
            instance.currentBuilding = building;
            instance.isOpen = building != null;
            instance.openAnimProgress = 0f;
            instance.selectedTabIndex = 0;
        }

        public static void Close()
        {
            if (instance != null)
            {
                instance.isOpen = false;
                instance.currentBuilding = null;
            }
        }

        private void EnsureStyles()
        {
            if (panelStyle != null) return;

            float scale = Mathf.Clamp(Screen.height / 1080f, 0.75f, 1.15f);

            // 1. OPAQUE solid maritime plate background (98% solid deep iron/obsidian)
            Texture2D panelTex = MakeOpaqueConsoleTexture(64,
                new Color(0.045f, 0.055f, 0.065f, 0.98f),
                new Color(0.85f, 0.70f, 0.38f, 0.95f),
                1.5f, 7f);

            panelStyle = new GUIStyle(GUI.skin.box)
            {
                normal = { background = panelTex },
                border = new RectOffset(10, 10, 10, 10),
                padding = new RectOffset(0, 0, 0, 0)
            };

            // 2. Opaque card for grouping rows
            Texture2D cardTex = MakeOpaqueConsoleTexture(32,
                new Color(0.075f, 0.090f, 0.110f, 0.96f),
                new Color(0.85f, 0.70f, 0.38f, 0.30f),
                1.0f, 5f);

            cardStyle = new GUIStyle(GUI.skin.box)
            {
                normal = { background = cardTex },
                border = new RectOffset(6, 6, 6, 6),
                padding = new RectOffset(0, 0, 0, 0)
            };

            // 3. Tab buttons (Active & Inactive)
            Texture2D activeTabTex = MakeOpaqueConsoleTexture(32,
                new Color(0.68f, 0.52f, 0.20f, 0.98f),
                new Color(0.98f, 0.85f, 0.45f, 1.0f),
                1.5f, 5f);
            Texture2D inactiveTabTex = MakeOpaqueConsoleTexture(32,
                new Color(0.065f, 0.080f, 0.095f, 0.95f),
                new Color(0.85f, 0.70f, 0.38f, 0.40f),
                1.0f, 5f);
            Texture2D inactiveTabHoverTex = MakeOpaqueConsoleTexture(32,
                new Color(0.16f, 0.14f, 0.08f, 0.95f),
                new Color(0.98f, 0.85f, 0.45f, 0.85f),
                1.2f, 5f);

            activeTabStyle = new GUIStyle(GUI.skin.button)
            {
                normal = { background = activeTabTex, textColor = new Color(1.0f, 0.96f, 0.88f) },
                hover = { background = activeTabTex, textColor = Color.white },
                active = { background = activeTabTex, textColor = Color.white },
                fontStyle = FontStyle.Bold,
                fontSize = 12,
                alignment = TextAnchor.MiddleCenter
            };

            inactiveTabStyle = new GUIStyle(GUI.skin.button)
            {
                normal = { background = inactiveTabTex, textColor = new Color(0.68f, 0.76f, 0.82f) },
                hover = { background = inactiveTabHoverTex, textColor = new Color(0.96f, 0.92f, 0.80f) },
                active = { background = inactiveTabHoverTex, textColor = Color.white },
                fontStyle = FontStyle.Normal,
                fontSize = 12,
                alignment = TextAnchor.MiddleCenter
            };

            // 4. Action button styles (Normal & Danger)
            Texture2D btnNormal = MakeOpaqueConsoleTexture(32,
                new Color(0.085f, 0.105f, 0.130f, 0.98f),
                new Color(0.85f, 0.70f, 0.38f, 0.75f),
                1.2f, 5f);
            Texture2D btnHover = MakeOpaqueConsoleTexture(32,
                new Color(0.24f, 0.20f, 0.10f, 0.98f),
                new Color(1.0f, 0.88f, 0.48f, 1.0f),
                1.5f, 5f);

            buttonStyle = new GUIStyle(GUI.skin.button)
            {
                normal = { background = btnNormal, textColor = new Color(0.95f, 0.93f, 0.88f) },
                hover = { background = btnHover, textColor = Color.white },
                active = { background = btnHover, textColor = Color.white },
                fontStyle = FontStyle.Bold,
                fontSize = 13,
                alignment = TextAnchor.MiddleCenter
            };

            Texture2D dangerNormal = MakeOpaqueConsoleTexture(32,
                new Color(0.26f, 0.06f, 0.06f, 0.98f),
                new Color(0.92f, 0.38f, 0.32f, 0.85f),
                1.2f, 5f);
            Texture2D dangerHover = MakeOpaqueConsoleTexture(32,
                new Color(0.42f, 0.08f, 0.08f, 0.98f),
                new Color(1.0f, 0.50f, 0.45f, 1.0f),
                1.5f, 5f);

            dangerButtonStyle = new GUIStyle(buttonStyle)
            {
                normal = { background = dangerNormal, textColor = new Color(1.0f, 0.85f, 0.82f) },
                hover = { background = dangerHover, textColor = Color.white },
                active = { background = dangerHover, textColor = Color.white }
            };

            // Close button style
            Texture2D closeNormal = MakeOpaqueConsoleTexture(24,
                new Color(0.08f, 0.10f, 0.12f, 0.95f),
                new Color(0.85f, 0.70f, 0.38f, 0.60f),
                1.0f, 4f);
            Texture2D closeHover = MakeOpaqueConsoleTexture(24,
                new Color(0.28f, 0.14f, 0.08f, 0.98f),
                new Color(1.0f, 0.82f, 0.42f, 1.0f),
                1.2f, 4f);

            closeButtonStyle = new GUIStyle(GUI.skin.button)
            {
                normal = { background = closeNormal, textColor = new Color(0.90f, 0.80f, 0.60f) },
                hover = { background = closeHover, textColor = Color.white },
                active = { background = closeHover, textColor = Color.white },
                fontStyle = FontStyle.Bold,
                fontSize = 13,
                alignment = TextAnchor.MiddleCenter
            };

            // Typography
            titleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(15f * scale), 12, 16),
                fontStyle = FontStyle.Bold,
                normal = { textColor = new Color(0.96f, 0.90f, 0.76f) },
                clipping = TextClipping.Clip
            };

            subtitleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(11f * scale), 10, 12),
                fontStyle = FontStyle.Bold,
                normal = { textColor = new Color(0.45f, 0.80f, 0.85f) },
                clipping = TextClipping.Clip
            };

            labelStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 13),
                normal = { textColor = new Color(0.68f, 0.76f, 0.82f) },
                clipping = TextClipping.Clip
            };

            valueStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 13),
                fontStyle = FontStyle.Bold,
                normal = { textColor = new Color(0.94f, 0.96f, 1.0f) },
                alignment = TextAnchor.MiddleRight,
                clipping = TextClipping.Clip
            };

            statusStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = Mathf.Clamp(Mathf.RoundToInt(12f * scale), 10, 13),
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleRight,
                clipping = TextClipping.Clip
            };

            dragHintStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 10,
                fontStyle = FontStyle.Normal,
                normal = { textColor = new Color(0.70f, 0.62f, 0.45f, 0.80f) },
                alignment = TextAnchor.MiddleRight
            };
        }

        private void OnGUI()
        {
            var selection = VesselOrdersUI.Selected;
            if ((!isOpen || currentBuilding == null) && selection == null) return;
            EnsureStyles();
            if (selection != null)
            {
                selection.DrawSelectionContents();
                return;
            }

            float scale = Mathf.Clamp(Screen.height / 1080f, 0.75f, 1.15f);
            currentPanelRect = GetPanelRect();

            // Smooth opening animation
            openAnimProgress = Mathf.MoveTowards(openAnimProgress, 1f, Time.unscaledDeltaTime * 6f);
            float alpha = Mathf.Clamp01(openAnimProgress * 1.5f);

            Color prevGuiColor = GUI.color;
            GUI.color = new Color(1f, 1f, 1f, alpha);

            // Draw Opaque Victorian Console Plate
            GUI.Box(currentPanelRect, GUIContent.none, panelStyle);

            // Top specular highlight line
            GUI.color = new Color(0.85f, 0.70f, 0.38f, 0.50f * alpha);
            GUI.DrawTexture(new Rect(currentPanelRect.x + 12f * scale, currentPanelRect.y + 1f, currentPanelRect.width - 24f * scale, 1.5f), Texture2D.whiteTexture);
            GUI.color = new Color(1f, 1f, 1f, alpha);

            // 1. Header (Category Emblem + Facility Name + Badge + Close button)
            string emblem = GetCategoryEmblem(currentBuilding.Definition.Category);
            string catName = GetCategoryName(currentBuilding.Definition.Category);

            GUI.Label(new Rect(currentPanelRect.x + 14f * scale, currentPanelRect.y + 10f * scale, 22f * scale, 22f * scale),
                emblem, titleStyle);

            GUI.Label(new Rect(currentPanelRect.x + 38f * scale, currentPanelRect.y + 8f * scale, currentPanelRect.width - 74f * scale, 22f * scale),
                currentBuilding.Definition.Name, titleStyle);

            GUI.Label(new Rect(currentPanelRect.x + 38f * scale, currentPanelRect.y + 27f * scale, currentPanelRect.width - 74f * scale, 16f * scale),
                "[" + catName + "]", subtitleStyle);

            // Close button
            Rect closeRect = new Rect(currentPanelRect.xMax - 30f * scale, currentPanelRect.y + 9f * scale, 22f * scale, 22f * scale);
            if (GUI.Button(closeRect, "×", closeButtonStyle))
            {
                Close();
                GUI.color = prevGuiColor;
                return;
            }

            // Divider below header
            GUI.color = new Color(0.85f, 0.70f, 0.38f, 0.35f * alpha);
            GUI.DrawTexture(new Rect(currentPanelRect.x + 12f * scale, currentPanelRect.y + 48f * scale, currentPanelRect.width - 24f * scale, 1f), Texture2D.whiteTexture);
            GUI.color = new Color(1f, 1f, 1f, alpha);

            // 2. Tab Bar System
            float tabY = currentPanelRect.y + 54f * scale;
            float tabH = 27f * scale;
            float tabGap = 4f * scale;
            float tabW = (currentPanelRect.width - 24f * scale - tabGap * 2f) / 3f;

            for (int i = 0; i < TabNames.Length; i++)
            {
                Rect tRect = new Rect(currentPanelRect.x + 12f * scale + i * (tabW + tabGap), tabY, tabW, tabH);
                bool isActive = selectedTabIndex == i;
                GUIStyle tStyle = isActive ? activeTabStyle : inactiveTabStyle;

                if (GUI.Button(tRect, TabNames[i], tStyle))
                {
                    selectedTabIndex = i;
                }

                if (isActive)
                {
                    // Golden bottom indicator line
                    GUI.color = new Color(1.0f, 0.88f, 0.45f, 0.95f * alpha);
                    GUI.DrawTexture(new Rect(tRect.x + 6f * scale, tRect.yMax - 2f * scale, tRect.width - 12f * scale, 2f * scale), Texture2D.whiteTexture);
                    GUI.color = new Color(1f, 1f, 1f, alpha);
                }
            }

            // 3. Tab Content Area
            float contentY = tabY + tabH + 8f * scale;
            Rect contentAreaRect = new Rect(currentPanelRect.x + 12f * scale, contentY, currentPanelRect.width - 24f * scale, currentPanelRect.yMax - contentY - 12f * scale);

            if (selectedTabIndex == 0)
            {
                DrawOverviewTab(contentAreaRect, scale);
            }
            else if (selectedTabIndex == 1)
            {
                DrawProductionTab(contentAreaRect, scale);
            }
            else
            {
                DrawOperationsTab(contentAreaRect, scale);
            }

            GUI.color = prevGuiColor;
        }

        private void DrawOverviewTab(Rect area, float scale)
        {
            float cardH = 108f * scale;
            Rect card1 = new Rect(area.x, area.y, area.width, cardH);
            GUI.Box(card1, GUIContent.none, cardStyle);

            float rowH = 22f * scale;
            float rowY = card1.y + 8f * scale;
            DrawRow("所属类别", GetCategoryName(currentBuilding.Definition.Category), ref rowY, rowH, card1, scale);
            DrawRow("地基坐标", $"({currentBuilding.Anchor.x}, {currentBuilding.Anchor.y})  ·  朝向 {currentBuilding.Rotation}°", ref rowY, rowH, card1, scale);
            DrawRow("占地规格", $"{currentBuilding.Definition.Width} × {currentBuilding.Definition.Depth} 地格", ref rowY, rowH, card1, scale);
            DrawRow("初始造价", $"🌲 {currentBuilding.WoodCost} 木材", ref rowY, rowH, card1, scale);

            // Group 2: Power and Efficiency
            float card2Y = card1.yMax + 8f * scale;
            float cardH2 = 86f * scale;
            Rect card2 = new Rect(area.x, card2Y, area.width, cardH2);
            GUI.Box(card2, GUIContent.none, cardStyle);

            rowY = card2.y + 8f * scale;

            var res = ColonyResourceManager.Instance;
            bool hasPower = res == null || res.PowerSurplus >= 0f || res.TotalPowerDemand <= 0f;
            statusStyle.normal.textColor = hasPower ? new Color(0.42f, 0.92f, 0.60f) : new Color(1.0f, 0.65f, 0.30f);
            DrawRow("供电状态", hasPower ? "● 正常运转中" : "▲ 供电不足·低效", ref rowY, rowH, card2, scale, statusStyle);

            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            float eff = prototype != null ? prototype.GetBuildingEfficiencyMultiplier(currentBuilding.Definition.AssetName) : 1f;
            string effText = eff > 1.0f ? $"+{Mathf.RoundToInt((eff - 1f) * 100)}% (科技加成)" : "基础 100%";
            GUIStyle effStyle = eff > 1.0f ? new GUIStyle(valueStyle) { normal = { textColor = new Color(0.96f, 0.85f, 0.45f) } } : valueStyle;
            DrawRow("综合效能", effText, ref rowY, rowH, card2, scale, effStyle);

            DrawRow("道路互联", "已接入环岛道路网", ref rowY, rowH, card2, scale);
        }

        private void DrawProductionTab(Rect area, float scale)
        {
            float cardH = 96f * scale;
            Rect card1 = new Rect(area.x, area.y, area.width, cardH);
            GUI.Box(card1, GUIContent.none, cardStyle);

            float rowH = 22f * scale;
            float rowY = card1.y + 8f * scale;

            if (currentBuilding.Definition.Category == BuildPlacementPrototype.BuildCategory.Residential)
            {
                var citizens = ColonyCitizenManager.Instance;
                int totalRes = citizens != null ? citizens.TotalPopulation : 0;
                DrawRow("居住容量", $"舒适宜居 · 岛民 {totalRes} 人", ref rowY, rowH, card1, scale);
                DrawRow("避难防御", "优良 · 抵御暴风雨海雾", ref rowY, rowH, card1, scale);
                DrawRow("幸福指数", "96% (稳定维系中)", ref rowY, rowH, card1, scale);
            }
            else if (currentBuilding.Definition.Kind == BuildPlacementPrototype.BuildableKind.Dock ||
                     currentBuilding.Definition.Category == BuildPlacementPrototype.BuildCategory.Transportation)
            {
                DrawRow("靠泊状态", "深水泊位就绪", ref rowY, rowH, card1, scale);
                DrawRow("登船栈桥", "岸边木阶梯与滑板通畅", ref rowY, rowH, card1, scale);
                DrawRow("装卸速率", "标准 100 单位/批次", ref rowY, rowH, card1, scale);
            }
            else
            {
                DrawRow("产出模式", "定额资源开采与产出", ref rowY, rowH, card1, scale);
                DrawRow("运转负荷", "满负荷运转中", ref rowY, rowH, card1, scale);
                DrawRow("运转损耗", "0% (设施状态优良)", ref rowY, rowH, card1, scale);
            }

            // Card 2: Logistics & Transportation
            float card2Y = card1.yMax + 8f * scale;
            float cardH2 = 96f * scale;
            Rect card2 = new Rect(area.x, card2Y, area.width, cardH2);
            GUI.Box(card2, GUIContent.none, cardStyle);

            rowY = card2.y + 8f * scale;
            DrawRow("仓储协同", "就近道路直通岛屿集散中心", ref rowY, rowH, card2, scale);
            DrawRow("物料周转", "货物无积压阻滞", ref rowY, rowH, card2, scale);
            DrawRow("工人通勤", "道路覆盖全岛设施", ref rowY, rowH, card2, scale);
        }

        private void DrawOperationsTab(Rect area, float scale)
        {
            float cardH = 96f * scale;
            Rect card1 = new Rect(area.x, area.y, area.width, cardH);
            GUI.Box(card1, GUIContent.none, cardStyle);

            GUI.Label(new Rect(card1.x + 12f * scale, card1.y + 8f * scale, card1.width - 24f * scale, 20f * scale),
                "【移动设施】(快捷键 M)", titleStyle);
            GUI.Label(new Rect(card1.x + 12f * scale, card1.y + 30f * scale, card1.width - 24f * scale, 28f * scale),
                "拾起该建筑并将其迁移至平整空闲土地，原道路连接将重新寻路。", labelStyle);

            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            Rect moveBtnRect = new Rect(card1.xMax - 130f * scale, card1.yMax - 32f * scale, 118f * scale, 26f * scale);
            if (GUI.Button(moveBtnRect, "⚓ 移动建筑 [M]", buttonStyle))
            {
                var target = currentBuilding;
                Close();
                if (prototype != null)
                {
                    prototype.StartMoveBuilding(target);
                }
            }

            // Card 2: Demolish Section
            float card2Y = card1.yMax + 10f * scale;
            Rect card2 = new Rect(area.x, card2Y, area.width, cardH);
            GUI.Box(card2, GUIContent.none, cardStyle);

            GUI.Label(new Rect(card2.x + 12f * scale, card2.y + 8f * scale, card2.width - 24f * scale, 20f * scale),
                "【拆除设施】(快捷键 X)", titleStyle);
            int refund = Mathf.Max(1, currentBuilding.WoodCost / 2);
            GUI.Label(new Rect(card2.x + 12f * scale, card2.y + 30f * scale, card2.width - 24f * scale, 28f * scale),
                $"彻底拆除该设施，返还 50% 建造木材 (+{refund} 木材) 并释放占用的岛屿地格。", labelStyle);

            Rect demolishBtnRect = new Rect(card2.xMax - 130f * scale, card2.yMax - 32f * scale, 118f * scale, 26f * scale);
            if (GUI.Button(demolishBtnRect, "✕ 确认拆除 [X]", dangerButtonStyle))
            {
                var target = currentBuilding;
                ColonyModalDialog.Show(
                    "拆除建筑确认",
                    $"是否确定拆除【{target.Definition.Name}】？\n拆除后将返还 {refund} 木材，并释放该处土地。",
                    () =>
                    {
                        Close();
                        if (prototype != null)
                        {
                            prototype.DemolishBuilding(target);
                        }
                    },
                    null,
                    DialogSeverity.Danger,
                    "确认拆除",
                    "取消"
                );
            }
        }

        private void DrawRow(string label, string value, ref float rowY, float rowH, Rect cardRect, float scale, GUIStyle customValStyle = null)
        {
            float labelW = 80f * scale;
            float valW = cardRect.width - labelW - 16f * scale;
            GUI.Label(new Rect(cardRect.x + 8f * scale, rowY, labelW, rowH), label, labelStyle);
            GUI.Label(new Rect(cardRect.x + labelW + 8f * scale, rowY, valW, rowH), value, customValStyle ?? valueStyle);
            rowY += rowH;
        }

        private static string GetCategoryEmblem(BuildPlacementPrototype.BuildCategory cat)
        {
            return cat switch
            {
                BuildPlacementPrototype.BuildCategory.Residential => "🏠",
                BuildPlacementPrototype.BuildCategory.Production => "⚙",
                BuildPlacementPrototype.BuildCategory.Facilities => "🏛",
                BuildPlacementPrototype.BuildCategory.Transportation => "⚓",
                _ => "◈"
            };
        }

        private static string GetCategoryName(BuildPlacementPrototype.BuildCategory cat)
        {
            return cat switch
            {
                BuildPlacementPrototype.BuildCategory.Residential => "居住建筑",
                BuildPlacementPrototype.BuildCategory.Production => "生产设施",
                BuildPlacementPrototype.BuildCategory.Facilities => "公共与文化",
                BuildPlacementPrototype.BuildCategory.Transportation => "交通与港口",
                _ => "基础设施"
            };
        }

        private Texture2D MakeOpaqueConsoleTexture(int size, Color face, Color border, float borderWidth, float cornerRadius)
        {
            Texture2D texture = new Texture2D(size, size, TextureFormat.RGBA32, false)
            {
                name = "Inspector opaque console plate",
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

                    // Solid opaque metallic sheen gradient
                    float sheen = Mathf.Lerp(0.92f, 1.10f, ny);
                    Color faceCol = new Color(face.r * sheen, face.g * sheen, face.b * sheen, 0.98f);

                    float topHighlight = ny > 0.88f ? 1.30f : 1.0f;
                    Color borderCol = new Color(border.r * topHighlight, border.g * topHighlight, border.b * topHighlight, border.a);

                    Color c = Color.Lerp(faceCol, borderCol, edge);
                    c.a *= alpha;
                    pixels[y * size + x] = c;
                }
            }

            texture.SetPixels(pixels);
            texture.Apply(false, false);
            ownedTextures.Add(texture);
            return texture;
        }
    }
}
