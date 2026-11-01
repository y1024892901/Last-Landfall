using UnityEngine;

namespace LastLandfall
{
    [CreateAssetMenu(menuName = "Last Landfall/Main Island Shore Settings")]
    public sealed class MainIslandShoreSettings : ScriptableObject
    {
        [Tooltip("主岛整体下沉量（米）。编辑后刷新岛屿预览或重新开始游戏；海面和附岛保持原高度。")]
        [Range(0f, 4f)] public float sinkDepth = 1.2f;

        public static float SinkDepth
        {
            get
            {
                var settings = Resources.Load<MainIslandShoreSettings>("MainIslandShoreSettings");
                return settings != null ? Mathf.Clamp(settings.sinkDepth, 0f, 4f) : 1.2f;
            }
        }
    }
}
