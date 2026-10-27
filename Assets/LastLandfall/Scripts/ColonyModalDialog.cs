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

        private void EnsureStyles()
        {
            if (windowStyle != null) return;

            Texture2D boxBg = MakeSolidTex(new Color(0.12f, 0.16f, 0.18f, 0.95f));
            scrimTexture = MakeSolidTex(new Color(0.04f, 0.06f, 0.08f, 0.70f));

            windowStyle = new GUIStyle(GUI.skin.box);
            windowStyle.normal.background = boxBg;

            titleStyle = new GUIStyle(GUI.skin.label);
            titleStyle.fontSize = 17;
            titleStyle.fontStyle = FontStyle.Bold;
            titleStyle.normal.textColor = new Color(0.92f, 0.88f, 0.75f);
            titleStyle.alignment = TextAnchor.MiddleCenter;

            messageStyle = new GUIStyle(GUI.skin.label);
            messageStyle.fontSize = 14;
            messageStyle.wordWrap = true;
            messageStyle.normal.textColor = new Color(0.85f, 0.90f, 0.92f);
            messageStyle.alignment = TextAnchor.UpperCenter;

            confirmButtonStyle = new GUIStyle(GUI.skin.button);
            confirmButtonStyle.fontSize = 14;
            confirmButtonStyle.fontStyle = FontStyle.Bold;

            cancelButtonStyle = new GUIStyle(GUI.skin.button);
            cancelButtonStyle.fontSize = 14;
            cancelButtonStyle.normal.textColor = new Color(0.80f, 0.85f, 0.88f);
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
            Color oldBg = GUI.backgroundColor;
            GUI.backgroundColor = severity == DialogSeverity.Danger ? new Color(0.95f, 0.40f, 0.30f) : new Color(0.35f, 0.75f, 0.65f);
            if (GUI.Button(confirmRect, confirmLabel, confirmButtonStyle))
            {
                ConfirmAction();
            }
            GUI.backgroundColor = oldBg;
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
    }
}
