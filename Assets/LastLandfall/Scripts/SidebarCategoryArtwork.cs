using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>Small category buttons with restrained frames and the existing painted symbols.</summary>
    internal static class SidebarCategoryArtwork
    {
        private const float AtlasWidth = 1024f;
        private const float AtlasHeight = 1536f;
        private const int FrameResolution = 128;
        // Sample only symbols; the baked ornate borders and lettering are outside these UVs.
        private static readonly Rect[] SymbolSources =
        {
            new Rect(346f, 164f, 324f, 236f),
            new Rect(362f, 613f, 300f, 211f),
            new Rect(366f, 1028f, 290f, 238f)
        };
        private static readonly string[] Labels = { "科技", "文化", "建筑" };
        private static readonly Texture2D[] Frames = new Texture2D[4];
        private static Texture2D atlas;
        private static GUIStyle labelStyle;

        private static Texture2D Atlas
        {
            get
            {
                if (atlas == null)
                    atlas = Resources.Load<Texture2D>("UI/Sidebar/CategoryButtonsAtlas");
                return atlas;
            }
        }

        internal static bool IsAvailable => Atlas != null;

        internal static void DrawRail(Rect rect)
        {
            Color previous = GUI.color;
            Fill(rect, new Color(0.015f, 0.035f, 0.045f, 0.42f));
            GUI.color = previous;
        }

        internal static bool TryDraw(Rect rect, int category, bool selected, bool hovered, bool pressed)
        {
            if (category < 0 || category >= SymbolSources.Length || Atlas == null)
                return false;

            Color previous = GUI.color;
            int state = pressed ? 3 : selected ? 2 : hovered ? 1 : 0;
            if (Frames[state] == null)
                Frames[state] = CreateFrame(state);
            GUI.DrawTexture(rect, Frames[state], ScaleMode.StretchToFill, true);

            Rect source = SymbolSources[category];
            Rect symbolArea = new Rect(rect.x + rect.width * 0.12f, rect.y + rect.height * 0.10f,
                rect.width * 0.76f, rect.height * 0.55f);
            float scale = Mathf.Min(symbolArea.width / source.width, symbolArea.height / source.height);
            Rect symbolRect = new Rect(symbolArea.center.x - source.width * scale * 0.5f,
                symbolArea.center.y - source.height * scale * 0.5f, source.width * scale, source.height * scale);
            Rect uv = new Rect(source.x / AtlasWidth, 1f - source.yMax / AtlasHeight,
                source.width / AtlasWidth, source.height / AtlasHeight);
            float brightness = pressed ? 0.72f : selected || hovered ? 1f : 0.88f;
            GUI.color = new Color(previous.r * brightness, previous.g * brightness,
                previous.b * brightness, previous.a);
            GUI.DrawTextureWithTexCoords(symbolRect, Atlas, uv, true);

            float separatorY = rect.y + rect.height * 0.72f;
            Fill(new Rect(rect.x + rect.width * 0.18f, separatorY, rect.width * 0.64f, 1f),
                selected ? new Color(0.62f, 0.49f, 0.28f, 0.7f) : new Color(0.30f, 0.39f, 0.39f, 0.38f));

            if (labelStyle == null)
            {
                labelStyle = new GUIStyle(GUI.skin.label)
                {
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter,
                    wordWrap = false,
                    clipping = TextClipping.Clip,
                    padding = new RectOffset(),
                    margin = new RectOffset()
                };
            }
            labelStyle.fontSize = Mathf.Max(10, Mathf.RoundToInt(rect.height * 0.172f));
            labelStyle.normal.textColor = selected
                ? new Color(1f, 0.87f, 0.60f) : new Color(0.80f, 0.83f, 0.78f);
            GUI.color = previous;
            GUI.Label(new Rect(rect.x + 4f, separatorY + 1f, rect.width - 8f,
                rect.yMax - separatorY - 5f), Labels[category], labelStyle);
            GUI.color = previous;
            return true;
        }

        private static Texture2D CreateFrame(int state)
        {
            var texture = new Texture2D(FrameResolution, FrameResolution, TextureFormat.RGBA32, false)
            {
                name = "Sidebar fine frame " + state,
                hideFlags = HideFlags.HideAndDontSave,
                wrapMode = TextureWrapMode.Clamp,
                filterMode = FilterMode.Bilinear
            };
            var pixels = new Color[FrameResolution * FrameResolution];
            Color rim = state == 2 ? new Color(0.78f, 0.62f, 0.35f)
                : state == 1 ? new Color(0.55f, 0.51f, 0.36f)
                : new Color(0.31f, 0.37f, 0.35f);
            for (int y = 0; y < FrameResolution; y++)
            {
                for (int x = 0; x < FrameResolution; x++)
                {
                    float dx = Mathf.Abs(x - (FrameResolution - 1f) * 0.5f);
                    float dy = Mathf.Abs(y - (FrameResolution - 1f) * 0.5f);
                    float half = FrameResolution * 0.5f - 1.5f;
                    float distance = Mathf.Max(Mathf.Max(dx - half, dy - half),
                        (dx + dy - 2f * half + 7f) * 0.70710678f);
                    float alpha = Mathf.Clamp01(0.5f - distance);
                    float depth = -distance;
                    float vertical = y / (FrameResolution - 1f);
                    Color color = Color.Lerp(new Color(0.022f, 0.046f, 0.056f),
                        new Color(0.042f, 0.086f, 0.095f), vertical);
                    if (state == 2)
                        color = Color.Lerp(color, new Color(0.055f, 0.14f, 0.15f), 0.35f);
                    if (depth < 2f)
                        color = Color.Lerp(rim * 0.8f, rim, vertical);
                    else if (depth < 4f)
                        color = new Color(0.010f, 0.026f, 0.032f);
                    if (state == 3)
                        color *= 0.78f;
                    color.a = alpha;
                    pixels[y * FrameResolution + x] = color;
                }
            }
            texture.SetPixels(pixels);
            texture.Apply(false, true);
            return texture;
        }

        private static void Fill(Rect rect, Color color)
        {
            GUI.color = color;
            GUI.DrawTexture(rect, Texture2D.whiteTexture);
        }
    }
}
