using System;
using UnityEngine;

namespace LastLandfall.Prototype
{
    public enum DialogSeverity
    {
        Info,
        Warning,
        Danger
    }

    /// <summary>
    /// Modal confirmation dialog system for dangerous or high-impact actions
    /// (demolition of critical buildings, loading saves, quitting).
    /// </summary>
    public sealed class ColonyModalDialog : MonoBehaviour
    {
        private static ColonyModalDialog instance;
        public static ColonyModalDialog Instance => instance;

        private bool isOpen;
        private string title = string.Empty;
        private string message = string.Empty;
        private string confirmLabel = "确认";
        private string cancelLabel = "取消";
        private DialogSeverity severity = DialogSeverity.Info;
        private Action onConfirmCallback;
        private Action onCancelCallback;

        private GUIStyle windowStyle;
        private GUIStyle titleStyle;
        private GUIStyle messageStyle;
        private GUIStyle confirmButtonStyle;
        private GUIStyle cancelButtonStyle;
        private Texture2D scrimTexture;

        public static bool IsDialogOpen => instance != null && instance.isOpen;

        private void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(gameObject);
                return;
            }
            instance = this;
        }

        public static void Show(string title, string message, Action onConfirm, Action onCancel = null,
                                DialogSeverity severity = DialogSeverity.Info,
                                string confirmLabel = "确认", string cancelLabel = "取消")
        {
            if (instance == null)
            {
                var host = new GameObject("Colony Modal Dialog");
                instance = host.AddComponent<ColonyModalDialog>();
            }

            instance.title = title;
            instance.message = message;
            instance.onConfirmCallback = onConfirm;
            instance.onCancelCallback = onCancel;
            instance.severity = severity;
            instance.confirmLabel = confirmLabel;
            instance.cancelLabel = cancelLabel;
            instance.isOpen = true;
        }

        public static void Close()
        {
            if (instance != null)
            {
                instance.isOpen = false;
            }
        }

        private Texture2D dangerConfirmBg;
        private Texture2D safeConfirmBg;
        private Texture2D dangerConfirmHover;
        private Texture2D safeConfirmHover;

        private void EnsureStyles()
        {
            if (windowStyle != null) return;

            Texture2D boxBg = MakeBeveledGlassTexture(64,
                new Color(0.012f, 0.024f, 0.038f, 0.78f),
                new Color(0.85f, 0.70f, 0.38f, 0.75f),
                1.5f, 8f);
            scrimTexture = MakeSolidTex(new Color(0.02f, 0.04f, 0.06f, 0.65f));

            windowStyle = new GUIStyle(GUI.skin.box)
            {
                normal = { background = boxBg },
                border = new RectOffset(10, 10, 10, 10)
            };

            titleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 17,
                fontStyle = FontStyle.Bold,
                normal = { textColor = new Color(0.96f, 0.90f, 0.76f) },
                alignment = TextAnchor.MiddleCenter
            };

            messageStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 14,
                wordWrap = true,
                normal = { textColor = new Color(0.85f, 0.92f, 0.96f) },
                alignment = TextAnchor.UpperCenter
            };

            Texture2D cancelNormal = MakeBeveledGlassTexture(32,
                new Color(0.04f, 0.08f, 0.12f, 0.50f),
                new Color(0.85f, 0.70f, 0.38f, 0.55f),
                1.2f, 5f);
            Texture2D cancelHover = MakeBeveledGlassTexture(32,
                new Color(0.18f, 0.15f, 0.08f, 0.65f),
                new Color(1.0f, 0.88f, 0.48f, 0.95f),
                1.4f, 5f);

            cancelButtonStyle = new GUIStyle(GUI.skin.button)
            {
                normal = { background = cancelNormal, textColor = new Color(0.88f, 0.85f, 0.78f) },
                hover = { background = cancelHover, textColor = Color.white },
                active = { background = cancelHover, textColor = Color.white },
                fontSize = 14,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter
            };

            dangerConfirmBg = MakeBeveledGlassTexture(32,
                new Color(0.24f, 0.05f, 0.05f, 0.65f),
                new Color(0.95f, 0.40f, 0.32f, 0.85f),
                1.4f, 5f);
            dangerConfirmHover = MakeBeveledGlassTexture(32,
                new Color(0.38f, 0.08f, 0.08f, 0.85f),
                new Color(1.0f, 0.52f, 0.45f, 1.0f),
                1.6f, 5f);

            safeConfirmBg = MakeBeveledGlassTexture(32,
                new Color(0.05f, 0.18f, 0.12f, 0.65f),
                new Color(0.40f, 0.88f, 0.60f, 0.85f),
                1.4f, 5f);
            safeConfirmHover = MakeBeveledGlassTexture(32,
                new Color(0.08f, 0.28f, 0.18f, 0.85f),
                new Color(0.55f, 1.0f, 0.75f, 1.0f),
                1.6f, 5f);

            confirmButtonStyle = new GUIStyle(GUI.skin.button)
            {
                fontSize = 14,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter
            };
        }

        private void OnGUI()
        {
            if (!isOpen) return;
            EnsureStyles();

            // 1. Full-screen scrim overlay to block clicks
            GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), scrimTexture);

            // Handle keyboard confirmation/cancel
            Event evt = Event.current;
            if (evt.type == EventType.KeyDown)
            {
                if (evt.keyCode == KeyCode.Return || evt.keyCode == KeyCode.KeypadEnter)
                {
                    ConfirmAction();
                    evt.Use();
                    return;
                }
                if (evt.keyCode == KeyCode.Escape)
                {
                    CancelAction();
                    evt.Use();
                    return;
                }
            }

            // 2. Centered dialog box
            float width = 420f;
            float height = 210f;
            Rect dialogRect = new Rect((Screen.width - width) * 0.5f, (Screen.height - height) * 0.5f, width, height);
            GUI.Box(dialogRect, GUIContent.none, windowStyle);

            // Dialog Title
            GUI.Label(new Rect(dialogRect.x + 20f, dialogRect.y + 16f, dialogRect.width - 40f, 28f), title, titleStyle);

            // Severity colored line
            Color lineCol = severity == DialogSeverity.Danger ? new Color(0.90f, 0.35f, 0.25f, 0.9f)
                          : severity == DialogSeverity.Warning ? new Color(0.95f, 0.65f, 0.20f, 0.9f)
                          : new Color(0.35f, 0.75f, 0.80f, 0.9f);
            GUI.color = lineCol;
            GUI.DrawTexture(new Rect(dialogRect.x + 30f, dialogRect.y + 46f, dialogRect.width - 60f, 2f), Texture2D.whiteTexture);
            GUI.color = Color.white;

            // Message text
            GUI.Label(new Rect(dialogRect.x + 24f, dialogRect.y + 58f, dialogRect.width - 48f, 75f), message, messageStyle);

            // Buttons
            float bWidth = 110f;
            float bHeight = 34f;
            float bY = dialogRect.yMax - 48f;

            Rect cancelRect = new Rect(dialogRect.center.x - bWidth - 14f, bY, bWidth, bHeight);
            if (GUI.Button(cancelRect, cancelLabel, cancelButtonStyle))
            {
                CancelAction();
            }

            Rect confirmRect = new Rect(dialogRect.center.x + 14f, bY, bWidth, bHeight);
            bool isDanger = severity == DialogSeverity.Danger;
            confirmButtonStyle.normal.background = isDanger ? dangerConfirmBg : safeConfirmBg;
            confirmButtonStyle.normal.textColor = isDanger ? new Color(1.0f, 0.85f, 0.82f) : new Color(0.85f, 1.0f, 0.90f);
            confirmButtonStyle.hover.background = isDanger ? dangerConfirmHover : safeConfirmHover;
            confirmButtonStyle.hover.textColor = Color.white;
            confirmButtonStyle.active.background = confirmButtonStyle.hover.background;
            confirmButtonStyle.active.textColor = Color.white;

            if (GUI.Button(confirmRect, confirmLabel, confirmButtonStyle))
            {
                ConfirmAction();
            }
        }

        private void ConfirmAction()
        {
            isOpen = false;
            onConfirmCallback?.Invoke();
        }

        private void CancelAction()
        {
            isOpen = false;
            onCancelCallback?.Invoke();
        }

        private static Texture2D MakeSolidTex(Color col)
        {
            Texture2D tex = new Texture2D(1, 1);
            tex.SetPixel(0, 0, col);
            tex.Apply();
            return tex;
        }

        private static Texture2D MakeBeveledGlassTexture(int size, Color face, Color border, float borderWidth, float cornerRadius)
        {
            Texture2D texture = new Texture2D(size, size, TextureFormat.RGBA32, false)
            {
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

                    float glassSheen = Mathf.Lerp(0.85f, 1.25f, ny);
                    Color faceCol = new Color(face.r * glassSheen, face.g * glassSheen, face.b * glassSheen, face.a);

                    float topHighlight = ny > 0.85f ? 1.35f : 1.0f;
                    Color borderCol = new Color(border.r * topHighlight, border.g * topHighlight, border.b * topHighlight, border.a);

                    Color c = Color.Lerp(faceCol, borderCol, edge);
                    c.a *= alpha;
                    pixels[y * size + x] = c;
                }
            }

            texture.SetPixels(pixels);
            texture.Apply(false, false);
            return texture;
        }
    }
}
