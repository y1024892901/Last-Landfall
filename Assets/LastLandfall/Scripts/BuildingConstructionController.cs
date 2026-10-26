using System;
using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>
    /// Progress is authoritative; visuals sample it instead of running independent animations.
    /// Only construction has individual part renderers. Completion releases them and restores
    /// the optimized static model. No occupancy, payment or placement decisions live here.
    /// </summary>
    public sealed class BuildingConstructionController : MonoBehaviour
    {
        private sealed class Binding
        {
            public Transform target;
            public BuildingConstructionCatalog.Part part;
            public Vector3 position;
            public Vector3 scale;
            public Vector3 offset;
            public bool settled;
        }

        private BuildingConstructionCatalog.Entry entry;
        private BuildingConstructionCatalog.Schedule schedule;
        private Binding[] bindings;
        private GameObject constructionVisual;
        private GameObject completedVisual;
        private Func<float> speedProvider;
        private bool automatic = true;
        private bool completionNotified;

        public float Progress { get; private set; }
        public bool IsComplete => Progress >= 1f;
        public float DurationSeconds => schedule != null ? schedule.Duration : 0f;
        public string AssetKey => entry != null ? entry.key : string.Empty;
        public string CurrentPhaseName
        {
            get
            {
                if (schedule == null || schedule.phases == null) return string.Empty;
                float frame = 1f + Progress * (schedule.frames - 1);
                for (int i = schedule.phases.Length - 1; i >= 0; i--)
                    if (frame >= schedule.phases[i].start) return schedule.phases[i].name;
                return string.Empty;
            }
        }
        public event Action<BuildingConstructionController> Completed;
        public event Action<float> ProgressChanged;

        /// <summary>
        /// Spawn any catalog asset for scenario/scripted placement. The caller owns terrain
        /// validation, resource costs and occupancy; this method only creates the visual/job.
        /// </summary>
        public static GameObject Create(string assetName, Transform parent, Vector3 localPosition,
            Quaternion localRotation, Func<float> simulationSpeed = null, float initialProgress = 0f)
        {
            if (!BuildingConstructionCatalog.TryGet(assetName, out BuildingConstructionCatalog.Entry entry)) return null;
            GameObject prefab = Resources.Load<GameObject>(entry.finalResource);
            if (prefab == null) return null;
            GameObject host = new GameObject(entry.key);
            host.transform.SetParent(parent, false);
            host.transform.SetLocalPositionAndRotation(localPosition, localRotation);
            GameObject finalVisual = Instantiate(prefab, host.transform, false);
            finalVisual.name = entry.key + " Model";
            if (entry.key.StartsWith("DirtRoad", StringComparison.Ordinal))
                finalVisual.transform.localRotation = Quaternion.Euler(0f, 180f, 0f) * finalVisual.transform.localRotation;
            TryBegin(host, assetName, finalVisual, simulationSpeed, initialProgress);
            return host;
        }

        public static bool TryBegin(GameObject host, string assetName, GameObject finalVisual,
            Func<float> simulationSpeed = null, float initialProgress = 0f)
        {
            if (host == null || finalVisual == null || float.IsNaN(initialProgress) || float.IsInfinity(initialProgress) ||
                host.GetComponent<BuildingConstructionController>() != null ||
                !BuildingConstructionCatalog.TryGet(assetName, out BuildingConstructionCatalog.Entry entry)) return false;
            BuildingConstructionCatalog.Schedule schedule = BuildingConstructionCatalog.LoadSchedule(entry);
            if (schedule == null) { Debug.LogWarning("Construction schedule unavailable: " + assetName, host); return false; }
            var controller = host.AddComponent<BuildingConstructionController>();
            controller.entry = entry;
            controller.schedule = schedule;
            controller.completedVisual = finalVisual;
            controller.speedProvider = simulationSpeed;
            if (initialProgress < 1f && !controller.CreateConstructionVisual())
            {
                controller.enabled = false;
                Destroy(controller); // Keep the existing static model visible on a bad import.
                return false;
            }
            controller.SetProgress(initialProgress);
            return true;
        }

        private bool CreateConstructionVisual()
        {
            GameObject prefab = Resources.Load<GameObject>(entry.modelResource);
            if (prefab == null) { Debug.LogWarning("Construction model unavailable: " + entry.key, this); return false; }
            constructionVisual = Instantiate(prefab, transform, false);
            constructionVisual.name = entry.key + " Construction";
            // The final and partial FBX use exactly the same export axes and units.
            constructionVisual.transform.localPosition = completedVisual.transform.localPosition;
            constructionVisual.transform.localRotation = completedVisual.transform.localRotation;
            constructionVisual.transform.localScale = completedVisual.transform.localScale;
            var targets = new Dictionary<string, Transform>(StringComparer.Ordinal);
            foreach (Transform child in constructionVisual.GetComponentsInChildren<Transform>(true))
                targets[child.name] = child;
            bindings = new Binding[schedule.parts.Length];
            for (int i = 0; i < schedule.parts.Length; i++)
            {
                BuildingConstructionCatalog.Part part = schedule.parts[i];
                if (!targets.TryGetValue(part.id, out Transform target) || part.start < 1 ||
                    part.end <= part.start || part.end > schedule.frames)
                {
                    Debug.LogWarning("Invalid construction part: " + entry.key + "/" + part.id, this);
                    constructionVisual.SetActive(false);
                    Destroy(constructionVisual);
                    constructionVisual = null;
                    bindings = null;
                    return false;
                }
                Vector3 point = transform.InverseTransformPoint(target.position);
                float distance = schedule.motionDistance;
                Vector3 offset = new Vector3(0f, distance, 0f);
                if (part.mode == "slide" || part.mode == "fit")
                    offset = new Vector3(point.x >= 0f ? distance : -distance, distance * 0.28f, 0f);
                else if (part.mode == "raise") offset.y *= 0.5f;
                bindings[i] = new Binding
                {
                    target = target, part = part, position = target.localPosition,
                    scale = target.localScale,
                    offset = target.parent.InverseTransformVector(transform.TransformVector(offset))
                };
                target.gameObject.SetActive(false);
            }
            completedVisual.SetActive(false);
            return true;
        }

        private void Update()
        {
            if (!automatic || IsComplete || schedule == null) return;
            float speed = speedProvider != null ? speedProvider() : 1f;
            SetProgress(Progress + Time.deltaTime * Mathf.Max(0f, speed) / DurationSeconds);
        }

        public void SetAutomaticProgress(bool value)
        {
            automatic = value;
            enabled = automatic && !IsComplete;
        }

        /// <summary>Allows saved progress or a future worker/job system to drive the same visuals.</summary>
        public void SetProgress(float value)
        {
            if (schedule == null || float.IsNaN(value) || float.IsInfinity(value)) return;
            float next = Mathf.Clamp01(value);
            if (next < 1f && constructionVisual == null && !CreateConstructionVisual()) return;
            bool changed = !Mathf.Approximately(Progress, next);
            Progress = next;
            enabled = automatic && !IsComplete;
            if (IsComplete)
            {
                if (constructionVisual != null)
                {
                    constructionVisual.SetActive(false);
                    Destroy(constructionVisual);
                    constructionVisual = null;
                    bindings = null;
                }
                completedVisual.SetActive(true);
                if (changed) ProgressChanged?.Invoke(Progress);
                if (!completionNotified) { completionNotified = true; Completed?.Invoke(this); }
                return;
            }
            completionNotified = false;
            float frame = 1f + Progress * (schedule.frames - 1);
            foreach (Binding binding in bindings)
            {
                bool visible = frame >= binding.part.start;
                if (binding.target.gameObject.activeSelf != visible) binding.target.gameObject.SetActive(visible);
                if (!visible) { binding.settled = false; continue; }
                float t = Mathf.Clamp01((frame - binding.part.start) / (binding.part.end - binding.part.start));
                if (t >= 1f && binding.settled) continue;
                binding.target.localPosition = binding.position + binding.offset * (1f - t);
                bool soft = binding.part.mode == "cloth" || binding.part.mode == "earth" || binding.part.mode == "grow";
                binding.target.localScale = soft
                    ? Vector3.Scale(binding.scale, new Vector3(1f, Mathf.Lerp(0.02f, 1f, t), 1f)) : binding.scale;
                binding.settled = t >= 1f;
            }
            if (changed) ProgressChanged?.Invoke(Progress);
        }
    }
}
