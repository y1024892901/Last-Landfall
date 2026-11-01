using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>
    /// Frostpunk-inspired Steampunk / Survival Industrial UI Theme:
    /// Cold dark cast iron, weathered riveted brass frames, warm mechanical amber/gold highlights,
    /// and crisp contrast hierarchy for grim maritime survival.
    /// </summary>
    public static class HudTheme
    {
        // --- Frostpunk Industrial Color Palette ---
        // Deep blackened cold cast iron with subtle vignette/grain
        public static readonly Color IronDark = new Color(0.045f, 0.055f, 0.065f, 0.96f);
        public static readonly Color IronMid  = new Color(0.085f, 0.105f, 0.125f, 0.94f);
        public static readonly Color IronLight = new Color(0.14f, 0.17f, 0.20f, 0.92f);

        // Weathered brass and mechanical gold accents
        public static readonly Color BrassDark = new Color(0.42f, 0.32f, 0.16f, 0.85f);
        public static readonly Color BrassMid  = new Color(0.78f, 0.62f, 0.32f, 0.95f);
        public static readonly Color BrassGold = new Color(0.96f, 0.82f, 0.44f, 1.0f);
        public static readonly Color BrassGlow = new Color(1.0f, 0.88f, 0.55f, 0.65f);

        // Cold survival atmospheric tones
        public static readonly Color FrostCyan = new Color(0.55f, 0.76f, 0.84f, 0.90f);
        public static readonly Color Text = new Color(0.94f, 0.93f, 0.90f, 1.0f);
        public static readonly Color Muted = new Color(0.62f, 0.68f, 0.72f, 1.0f);
        public static readonly Color DangerRed = new Color(0.85f, 0.28f, 0.22f, 1.0f);

        // Aliases for compatibility
        public static readonly Color Ink = IronDark;
        public static readonly Color Accent = BrassGold;
        public static readonly Color AccentSoft = new Color(0.88f, 0.72f, 0.36f, 0.55f);

        static Texture2D panel, card, hover, selected, gradient, stripPanel;
        static Texture2D frostedPanel, brassDivider;

        public static Texture2D Panel => panel != null ? panel : panel = MakeIndustrialPlate(IronDark, BrassDark, 1.6f, 8f, true);
        public static Texture2D Card => card != null ? card : card = MakeIndustrialPlate(IronMid, new Color(0.35f, 0.38f, 0.42f, 0.45f), 1.2f, 6f, false);
        public static Texture2D Hover => hover != null ? hover : hover = MakeIndustrialPlate(IronLight, BrassMid, 1.8f, 6f, false);
        public static Texture2D Selected => selected != null ? selected : selected = MakeIndustrialPlate(new Color(0.16f, 0.15f, 0.10f, 0.96f), BrassGold, 2.2f, 6f, true);
        public static Texture2D StripPanel => stripPanel != null ? stripPanel : stripPanel = MakeIndustrialPlate(new Color(0.035f, 0.045f, 0.055f, 0.88f), BrassDark, 1.2f, 6f, false);

        /// <summary>
        /// Generates a beveled industrial plate texture with mechanical chamfers, metal sheen, and corner rivets.
        /// </summary>
        static Texture2D MakeIndustrialPlate(Color face, Color border, float borderWidth, float cornerRadius, bool addRivets)
        {
            const int size = 64;
            var texture = new Texture2D(size, size, TextureFormat.RGBA32, false)
            {
                hideFlags = HideFlags.HideAndDontSave,
                wrapMode = TextureWrapMode.Clamp,
                filterMode = FilterMode.Bilinear
            };
            var pixels = new Color[size * size];
            float half = size * 0.5f;

            for (int y = 0; y < size; y++)
            {
                float ny = y / (float)(size - 1); // 0 (bottom) to 1 (top)
                for (int x = 0; x < size; x++)
                {
                    float nx = x / (float)(size - 1);
                    // Signed distance to beveled rounded rectangle
                    float qx = Mathf.Abs(x + 0.5f - half) - (half - cornerRadius);
                    float qy = Mathf.Abs(y + 0.5f - half) - (half - cornerRadius);
                    float outside = Mathf.Sqrt(Mathf.Max(qx, 0f) * Mathf.Max(qx, 0f) + Mathf.Max(qy, 0f) * Mathf.Max(qy, 0f));
                    float dist = outside + Mathf.Min(Mathf.Max(qx, qy), 0f) - cornerRadius;

                    float alpha = Mathf.Clamp01(0.5f - dist);
                    float edge = Mathf.Clamp01((dist + borderWidth) / borderWidth);

                    // Vertical subtle metallic lighting gradient (Frostpunk cast iron gradient)
                    float metalSheen = Mathf.Lerp(0.88f, 1.15f, ny);
                    Color baseCol = face * metalSheen;
                    baseCol.a = face.a;

                    // Metallic border with top highlight and bottom shadow
                    Color borderCol = border;
                    if (ny > 0.85f) borderCol = Color.Lerp(borderCol, BrassGold, (ny - 0.85f) / 0.15f * 0.65f);
                    else if (ny < 0.15f) borderCol *= 0.72f;

                    Color value = Color.Lerp(baseCol, borderCol, edge * border.a);
                    value.a = Mathf.Lerp(face.a, Mathf.Max(face.a, border.a), edge) * alpha;

                    // Mechanical corner rivet accents
                    if (addRivets && alpha > 0.7f)
                    {
                        float dRivet1 = Vector2.Distance(new Vector2(x, y), new Vector2(7f, 7f));
                        float dRivet2 = Vector2.Distance(new Vector2(x, y), new Vector2(size - 8f, 7f));
                        float dRivet3 = Vector2.Distance(new Vector2(x, y), new Vector2(7f, size - 8f));
                        float dRivet4 = Vector2.Distance(new Vector2(x, y), new Vector2(size - 8f, size - 8f));
                        float minRivetDist = Mathf.Min(Mathf.Min(dRivet1, dRivet2), Mathf.Min(dRivet3, dRivet4));

                        if (minRivetDist < 2.8f)
                        {
                            float rivetShade = minRivetDist < 1.3f ? 1.4f : 0.45f;
                            value = Color.Lerp(value, BrassGold * rivetShade, 0.75f);
                        }
                    }

                    pixels[y * size + x] = value;
                }
            }
            texture.SetPixels(pixels);
            texture.Apply(false, true);
            return texture;
        }

        public static void StylePanel(GUIStyle style)
        {
            if (style == null) return;
            style.normal.background = Panel;
            style.border = new RectOffset(12, 12, 12, 12);
        }

        public static void StyleButton(GUIStyle style, bool isSelected = false)
        {
            if (style == null) return;
            style.normal.background = isSelected ? Selected : Card;
            style.hover.background = Hover;
            style.active.background = Selected;
            style.focused.background = Hover;
            style.normal.textColor = Text;
            style.hover.textColor = BrassGold;
            style.active.textColor = Color.white;
            style.border = new RectOffset(10, 10, 10, 10);
        }

        public static void TopShade(Rect rect)
        {
            if (gradient == null)
            {
                gradient = new Texture2D(1, 128, TextureFormat.RGBA32, false)
                {
                    hideFlags = HideFlags.HideAndDontSave,
                    wrapMode = TextureWrapMode.Clamp
                };
                for (int y = 0; y < 128; y++)
                {
                    float factor = Mathf.Pow(y / 127f, 1.8f);
                    gradient.SetPixel(0, y, new Color(0.02f, 0.035f, 0.05f, factor * 0.78f));
                }
                gradient.Apply(false, true);
            }
            GUI.DrawTexture(new Rect(0, 0, rect.width, rect.height + 48), gradient);
        }

        /// <summary>
        /// Frostpunk top steel bar with a weathered double brass rule and corner brackets.
        /// </summary>
        public static void TopBar(Rect rect)
        {
            Color previous = GUI.color;
            GUI.color = new Color(0.032f, 0.045f, 0.058f, 0.92f);
            GUI.DrawTexture(rect, Texture2D.whiteTexture);

            // Double brass filament rail
            GUI.color = BrassDark;
            GUI.DrawTexture(new Rect(rect.x, rect.yMax - 3f, rect.width, 1f), Texture2D.whiteTexture);
            GUI.color = BrassGold * 0.9f;
            GUI.DrawTexture(new Rect(rect.x, rect.yMax - 1f, rect.width, 1.5f), Texture2D.whiteTexture);

            GUI.color = previous;
        }

        static GUIStyle plateStyle, cardStyle, hoverCardStyle, selectedCardStyle;
        static GUIStyle MakeBoxStyle(Texture2D background)
        {
            var style = new GUIStyle(GUI.skin.box) { border = new RectOffset(10, 10, 10, 10) };
            style.normal.background = background;
            return style;
        }

        /// <summary>
        /// Industrial cast-iron resource plate with mechanical bevel.
        /// </summary>
        public static void Plate(Rect rect)
        {
            if (plateStyle == null) plateStyle = MakeBoxStyle(StripPanel);
            GUI.Box(rect, GUIContent.none, plateStyle);

            // Subtle top highlight rule
            Color prev = GUI.color;
            GUI.color = new Color(0.85f, 0.70f, 0.38f, 0.28f);
            GUI.DrawTexture(new Rect(rect.x + 8f, rect.y + 1f, rect.width - 16f, 1f), Texture2D.whiteTexture);
            GUI.color = prev;
        }

        /// <summary>
        /// Frostpunk style building card with engraved metal borders, mechanical status bar, and brass corner accents.
        /// </summary>
        public static void DrawCard(Rect rect, bool isSelected, bool isHovered)
        {
            if (cardStyle == null)
            {
                cardStyle = MakeBoxStyle(Card);
                hoverCardStyle = MakeBoxStyle(Hover);
                selectedCardStyle = MakeBoxStyle(Selected);
            }

            GUI.Box(rect, GUIContent.none, isSelected ? selectedCardStyle : isHovered ? hoverCardStyle : cardStyle);

            Color prev = GUI.color;
            if (isSelected)
            {
                // Active golden brass mechanical focus bracket
                GUI.color = BrassGold;
                // Top & Bottom corner ticks
                GUI.DrawTexture(new Rect(rect.x + 4f, rect.y + 2f, 14f, 2f), Texture2D.whiteTexture);
                GUI.DrawTexture(new Rect(rect.xMax - 18f, rect.y + 2f, 14f, 2f), Texture2D.whiteTexture);
                GUI.DrawTexture(new Rect(rect.x + 4f, rect.yMax - 4f, 14f, 2f), Texture2D.whiteTexture);
                GUI.DrawTexture(new Rect(rect.xMax - 18f, rect.yMax - 4f, 14f, 2f), Texture2D.whiteTexture);
                // Center bottom glowing indicator line
                GUI.color = BrassGlow;
                GUI.DrawTexture(new Rect(rect.center.x - 24f, rect.yMax - 2f, 48f, 2f), Texture2D.whiteTexture);
            }
            else if (isHovered)
            {
                // Subtle warm steam-glow line on hover
                GUI.color = new Color(0.88f, 0.72f, 0.38f, 0.45f);
                GUI.DrawTexture(new Rect(rect.x + 10f, rect.y + 1f, rect.width - 20f, 1.5f), Texture2D.whiteTexture);
            }
            GUI.color = prev;
        }

        static GUIStyle trackStyle, goldStyle, segmentHoverStyle;
        static Texture2D track, gold, goldFaint;

        /// <summary>
        /// Speed control segment: vintage steam dial style brass plate when selected.
        /// </summary>
        public static void Segment(Rect rect, bool isSelected, bool isHovered)
        {
            if (goldStyle == null)
            {
                gold = MakeIndustrialPlate(new Color(0.72f, 0.56f, 0.22f, 0.98f), BrassGold, 2.0f, 6f, false);
                goldFaint = MakeIndustrialPlate(new Color(0.24f, 0.22f, 0.16f, 0.65f), BrassMid, 1.2f, 6f, false);
                goldStyle = MakeBoxStyle(gold);
                segmentHoverStyle = MakeBoxStyle(goldFaint);
            }
            if (isSelected)
            {
                GUI.Box(rect, GUIContent.none, goldStyle);
                Color prev = GUI.color;
                GUI.color = BrassGlow;
                GUI.DrawTexture(new Rect(rect.x + 4f, rect.y + 1f, rect.width - 8f, 1.5f), Texture2D.whiteTexture);
                GUI.color = prev;
            }
            else if (isHovered)
            {
                GUI.Box(rect, GUIContent.none, segmentHoverStyle);
            }
        }

        /// <summary>
        /// Recessed iron track housing control toggles and dials.
        /// </summary>
        public static void Track(Rect rect)
        {
            if (trackStyle == null)
            {
                track = MakeIndustrialPlate(new Color(0.02f, 0.028f, 0.038f, 0.85f), new Color(0.45f, 0.36f, 0.20f, 0.40f), 1.2f, 6f, false);
                trackStyle = MakeBoxStyle(track);
            }
            GUI.Box(rect, GUIContent.none, trackStyle);
        }

        public static GUIStyle Label(int size, Color color, bool bold = false)
        {
            var style = new GUIStyle(GUI.skin.label)
            {
                fontSize = size,
                fontStyle = bold ? FontStyle.Bold : FontStyle.Normal,
                wordWrap = true
            };
            style.normal.textColor = color;
            return style;
        }
    }
}
