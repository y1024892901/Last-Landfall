using System;
using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>
    /// Displays detailed facility data, operational status, worker assignments,
    /// power grid connectivity, and action triggers when clicking an existing building.
    /// </summary>
    public sealed class BuildingInspectorUI : MonoBehaviour
    {
        private static BuildingInspectorUI instance;
        public static BuildingInspectorUI Instance => instance;

        private bool isOpen;
        private BuildPlacementPrototype.PlacedBuildingData currentBuilding;

        private GUIStyle panelStyle;
        private GUIStyle titleStyle;
        private GUIStyle labelStyle;
        private GUIStyle valueStyle;
        private GUIStyle statusStyle;
        private GUIStyle buttonStyle;
        private Texture2D panelBg;

        public static bool IsOpen => instance != null && instance.isOpen;

        private void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(gameObject);
                return;
            }
            instance = this;
        }

        public static void Inspect(BuildPlacementPrototype.PlacedBuildingData building)
        {
            if (instance == null)
            {
                var host = new GameObject("Building Inspector UI");
                instance = host.AddComponent<BuildingInspectorUI>();
            }

            instance.currentBuilding = building;
            instance.isOpen = building != null;
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

            panelBg = MakeSolidTex(new Color(0.10f, 0.14f, 0.17f, 0.94f));

            panelStyle = new GUIStyle(GUI.skin.box);
            panelStyle.normal.background = panelBg;

            titleStyle = new GUIStyle(GUI.skin.label);
            titleStyle.fontSize = 16;
            titleStyle.fontStyle = FontStyle.Bold;
            titleStyle.normal.textColor = new Color(0.92f, 0.88f, 0.72f);

            labelStyle = new GUIStyle(GUI.skin.label);
            labelStyle.fontSize = 13;
            labelStyle.normal.textColor = new Color(0.68f, 0.76f, 0.80f);

            valueStyle = new GUIStyle(GUI.skin.label);
            valueStyle.fontSize = 13;
            valueStyle.fontStyle = FontStyle.Bold;
            valueStyle.normal.textColor = new Color(0.88f, 0.92f, 0.95f);
            valueStyle.alignment = TextAnchor.MiddleRight;

            statusStyle = new GUIStyle(GUI.skin.label);
            statusStyle.fontSize = 13;
            statusStyle.fontStyle = FontStyle.Bold;

            buttonStyle = new GUIStyle(GUI.skin.button);
            buttonStyle.fontSize = 13;
        }

        private void OnGUI()
        {
            if (!isOpen || currentBuilding == null) return;
            EnsureStyles();

            float scale = Mathf.Clamp(Screen.height / 1080f, 0.8f, 1.4f);
            float width = 310f * scale;
            float height = 290f * scale;

            // Anchor to bottom-right corner, above HUD bottom
            float x = Screen.width - width - 18f * scale;
            float y = Screen.height - height - 32f * scale;
            Rect panelRect = new Rect(x, y, width, height);

            GUI.Box(panelRect, GUIContent.none, panelStyle);

            // 1. Header with Close button
            GUI.Label(new Rect(panelRect.x + 14f * scale, panelRect.y + 12f * scale, panelRect.width - 60f * scale, 24f * scale),
                currentBuilding.Definition.Name, titleStyle);

            if (GUI.Button(new Rect(panelRect.xMax - 32f * scale, panelRect.y + 10f * scale, 22f * scale, 22f * scale), "×", buttonStyle))
            {
                Close();
                return;
            }

            GUI.color = new Color(0.40f, 0.75f, 0.70f, 0.6f);
            GUI.DrawTexture(new Rect(panelRect.x + 14f * scale, panelRect.y + 38f * scale, panelRect.width - 28f * scale, 1.5f), Texture2D.whiteTexture);
            GUI.color = Color.white;

            // 2. Info details
            float rowY = panelRect.y + 46f * scale;
            float rowH = 22f * scale;

            DrawRow("所属类别", GetCategoryName(currentBuilding.Definition.Category), ref rowY, rowH, panelRect, scale);
            DrawRow("地基坐标", $"({currentBuilding.Anchor.x}, {currentBuilding.Anchor.y})", ref rowY, rowH, panelRect, scale);
            DrawRow("初始造价", $"{currentBuilding.WoodCost} 木材", ref rowY, rowH, panelRect, scale);

            // Operation & Power state
            var res = ColonyResourceManager.Instance;
            bool hasPower = res == null || res.PowerSurplus >= 0f || res.TotalPowerDemand <= 0f;
            statusStyle.normal.textColor = hasPower ? new Color(0.40f, 0.88f, 0.50f) : new Color(0.95f, 0.40f, 0.30f);
            DrawRow("运转状态", hasPower ? "● 正常运转中" : "▲ 供电不足·低效", ref rowY, rowH, panelRect, scale, statusStyle);

            // Efficiency
            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            float eff = prototype != null ? prototype.GetBuildingEfficiencyMultiplier(currentBuilding.Definition.AssetName) : 1f;
            string effText = eff > 1.0f ? $"+{Mathf.RoundToInt((eff - 1f) * 100)}% (科技加成)" : "基础 100%";
            DrawRow("综合效能", effText, ref rowY, rowH, panelRect, scale);

            // 3. Action Buttons (Move & Demolish)
            float bWidth = (panelRect.width - 36f * scale) * 0.5f;
            float bHeight = 32f * scale;
            float bY = panelRect.yMax - bHeight - 14f * scale;

            // Move Button
            if (GUI.Button(new Rect(panelRect.x + 14f * scale, bY, bWidth, bHeight), "移动建筑 (M)", buttonStyle))
            {
                var target = currentBuilding;
                Close();
                if (prototype != null)
                {
                    prototype.StartMoveBuilding(target);
                }
            }

            // Demolish Button with Modal Confirmation
            Color oldBg = GUI.backgroundColor;
            GUI.backgroundColor = new Color(0.95f, 0.40f, 0.35f);
            if (GUI.Button(new Rect(panelRect.x + 18f * scale + bWidth, bY, bWidth, bHeight), "拆除建筑 (X)", buttonStyle))
            {
                var target = currentBuilding;
                int refund = Mathf.Max(1, target.WoodCost / 2);
                ColonyModalDialog.Show(
                    "拆除建筑确认",
                    $"是否确定拆除【{target.Definition.Name}】？\n拆除后将返还 {refund} 木材，并释放土地。",
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
            GUI.backgroundColor = oldBg;
        }

        private void DrawRow(string label, string value, ref float rowY, float rowH, Rect panelRect, float scale, GUIStyle customValStyle = null)
        {
            GUI.Label(new Rect(panelRect.x + 14f * scale, rowY, 100f * scale, rowH), label, labelStyle);
            GUI.Label(new Rect(panelRect.x + 110f * scale, rowY, panelRect.width - 124f * scale, rowH), value, customValStyle ?? valueStyle);
            rowY += rowH;
        }

        private string GetCategoryName(BuildPlacementPrototype.BuildCategory cat)
        {
            switch (cat)
            {
                case BuildPlacementPrototype.BuildCategory.Residential: return "居住建筑";
                case BuildPlacementPrototype.BuildCategory.Production: return "生产设施";
                case BuildPlacementPrototype.BuildCategory.Facilities: return "公共与文化";
                case BuildPlacementPrototype.BuildCategory.Transportation: return "交通与港口";
                default: return "基础设施";
            }
        }

        private static Texture2D MakeSolidTex(Color col)
        {
            Texture2D tex = new Texture2D(1, 1);
            tex.SetPixel(0, 0, col);
            tex.Apply();
            return tex;
        }
    }
}
