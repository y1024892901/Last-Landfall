using System;
using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    public enum SalvageType
    {
        WoodCrate,       // 漂流木箱 (+木材)
        RationBarrel,    // 补给桶 (+食物, +淡水)
        MetalScrap,      // 废旧机械残骸 (+金属, +零件)
        DistressSurvivor // 遇险幸存者求救浮筏 (+新居民)
    }

    public sealed class SalvageItem : MonoBehaviour
    {
        public SalvageType type;
        public string displayName;
        public float woodReward;
        public float foodReward;
        public float waterReward;
        public float metalReward;
        public float fuelReward;

        private Vector3 initialPos;
        private float floatPhase;

        private void Start()
        {
            initialPos = transform.position;
            floatPhase = UnityEngine.Random.Range(0f, Mathf.PI * 2f);
        }

        private void Update()
        {
            // Floating bobbing on water
            float heave = Mathf.Sin(Time.time * 1.5f + floatPhase) * 0.06f;
            float roll = Mathf.Cos(Time.time * 1.1f + floatPhase) * 4.0f;
            transform.position = new Vector3(initialPos.x, initialPos.y + heave, initialPos.z);
            transform.rotation = Quaternion.Euler(roll, Time.time * 8f, roll * 0.5f);
        }
    }

    /// <summary>
    /// Spawns and manages oceanic salvage items, flotsam crates,
    /// and survivor distress signals around the Last Landfall archipelago.
    /// </summary>
    public sealed class OceanSalvageManager : MonoBehaviour
    {
        private static OceanSalvageManager instance;
        public static OceanSalvageManager Instance => instance;

        [Header("Salvage Configuration")]
        [SerializeField] private int maxActiveSalvage = 12;
        [SerializeField] private float waterLevel = -0.92f;
        [SerializeField] private float collectionRadius = 3.6f;

        private readonly List<SalvageItem> activeItems = new List<SalvageItem>();
        private float nextSpawnTime;
        private float distressSignalCooldown = 60f;
        private float distressTimer;

        public event Action<string> SalvageCollected;

        private void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(gameObject);
                return;
            }
            instance = this;
        }

        private void Start()
        {
            SpawnInitialOceanFlotsam();
        }

        private void Update()
        {
            CheckBoatCollection();

            if (Time.time >= nextSpawnTime && activeItems.Count < maxActiveSalvage)
            {
                SpawnRandomFlotsam();
                nextSpawnTime = Time.time + UnityEngine.Random.Range(20f, 40f);
            }

            distressTimer += Time.deltaTime;
            if (distressTimer >= distressSignalCooldown)
            {
                distressTimer = 0f;
                SpawnDistressSignal();
            }
        }

        private void SpawnInitialOceanFlotsam()
        {
            for (int i = 0; i < 7; i++)
            {
                SpawnRandomFlotsam();
            }
        }

        private void SpawnRandomFlotsam()
        {
            if (!TryFindWater(out Vector3 pos)) return;

            SalvageType st = (SalvageType)UnityEngine.Random.Range(0, 3);
            CreateSalvageVisual(pos, st);
        }

        public void SpawnDistressSignal()
        {
            if (!TryFindWater(out Vector3 pos)) return;

            CreateSalvageVisual(pos, SalvageType.DistressSurvivor);
            SalvageCollected?.Invoke("【无线电求救信号】坐标附近海礁发现幸存者，请驾驶快艇前往救援！(按 B 键出海)");
        }

        private bool TryFindWater(out Vector3 position)
        {
            position = default;
            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            var grid = prototype != null ? prototype.ConstructionGrid : null;
            if (grid == null) return false;
            for (int attempt = 0; attempt < 160; attempt++)
            {
                Vector2 direction = UnityEngine.Random.insideUnitCircle.normalized;
                float distance = UnityEngine.Random.Range(30f, 130f);
                float x = direction.x * distance, z = direction.y * distance;
                bool clear = !grid.TrySample(x, z, out _, out _);
                for (int i = 0; clear && i < 8; i++)
                {
                    float angle = i * Mathf.PI * .25f;
                    clear = !grid.TrySample(x + Mathf.Cos(angle) * 2f, z + Mathf.Sin(angle) * 2f, out _, out _);
                }
                if (!clear) continue;
                position = grid.Root.TransformPoint(new Vector3(x, grid.SeaLevel, z));
                return true;
            }
            return false;
        }

        private void CreateSalvageVisual(Vector3 worldPos, SalvageType type)
        {
            GameObject host = new GameObject("Salvage | " + type);
            host.transform.SetParent(transform, true);
            host.transform.position = worldPos;

            var item = host.AddComponent<SalvageItem>();
            item.type = type;

            GameObject visual;
            switch (type)
            {
                case SalvageType.WoodCrate:
                    visual = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    visual.transform.SetParent(host.transform, false);
                    visual.transform.localScale = new Vector3(1.1f, 0.9f, 1.1f);
                    visual.GetComponent<Renderer>().material.color = new Color(0.48f, 0.35f, 0.22f);
                    item.displayName = "漂流木材箱";
                    item.woodReward = UnityEngine.Random.Range(20f, 40f);
                    break;

                case SalvageType.RationBarrel:
                    visual = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                    visual.transform.SetParent(host.transform, false);
                    visual.transform.localScale = new Vector3(0.9f, 0.7f, 0.9f);
                    visual.GetComponent<Renderer>().material.color = new Color(0.20f, 0.45f, 0.52f);
                    item.displayName = "应急淡水补给桶";
                    item.waterReward = UnityEngine.Random.Range(25f, 45f);
                    item.foodReward = UnityEngine.Random.Range(15f, 30f);
                    break;

                case SalvageType.MetalScrap:
                    visual = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    visual.transform.SetParent(host.transform, false);
                    visual.transform.localScale = new Vector3(1.4f, 0.6f, 0.8f);
                    visual.GetComponent<Renderer>().material.color = new Color(0.35f, 0.38f, 0.40f);
                    item.displayName = "废弃机械构件";
                    item.metalReward = UnityEngine.Random.Range(15f, 30f);
                    item.fuelReward = UnityEngine.Random.Range(10f, 20f);
                    break;

                case SalvageType.DistressSurvivor:
                default:
                    visual = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                    visual.transform.SetParent(host.transform, false);
                    visual.transform.localScale = new Vector3(1.8f, 0.3f, 1.8f);
                    visual.GetComponent<Renderer>().material.color = new Color(0.92f, 0.42f, 0.12f);
                    item.displayName = "遇险幸存者救生筏";
                    break;
            }

            activeItems.Add(item);
        }

        private void CheckBoatCollection()
        {
            var boat = RescueBoatController.ActiveVessel;
            if (boat == null) return;

            Vector3 boatPos = boat.transform.position;
            for (int i = activeItems.Count - 1; i >= 0; i--)
            {
                var item = activeItems[i];
                if (item == null)
                {
                    activeItems.RemoveAt(i);
                    continue;
                }

                float distSqr = (item.transform.position - boatPos).sqrMagnitude;
                if (distSqr <= collectionRadius * collectionRadius)
                {
                    CollectItem(item);
                    activeItems.RemoveAt(i);
                }
            }
        }

        private void CollectItem(SalvageItem item)
        {
            var res = ColonyResourceManager.Instance;
            if (res != null)
            {
                if (item.woodReward > 0f) res.Add(ResourceType.Wood, item.woodReward);
                if (item.foodReward > 0f) res.Add(ResourceType.Food, item.foodReward);
                if (item.waterReward > 0f) res.Add(ResourceType.Water, item.waterReward);
                if (item.metalReward > 0f) res.Add(ResourceType.Metal, item.metalReward);
                if (item.fuelReward > 0f) res.Add(ResourceType.Fuel, item.fuelReward);
            }

            if (item.type == SalvageType.DistressSurvivor)
            {
                string[] survivorNames = { "老林", "苏晴", "阿泽", "晓风", "陈师傅" };
                string[] roles = { "渔民", "技工", "农学家", "护士", "建筑师" };
                string pickedName = survivorNames[UnityEngine.Random.Range(0, survivorNames.Length)];
                string pickedRole = roles[UnityEngine.Random.Range(0, roles.Length)];

                var citizenMgr = ColonyCitizenManager.Instance;
                if (citizenMgr != null)
                {
                    citizenMgr.RescueNewSurvivor(pickedName, pickedRole, new Vector3(0f, 0.2f, -10f));
                }
                SalvageCollected?.Invoke($"【搜救成功】已成功接回幸存者：{pickedName} ({pickedRole})！聚落人口增加。");
            }
            else
            {
                SalvageCollected?.Invoke($"打捞成功：{item.displayName}！已运回物资库。");
            }

            Destroy(item.gameObject);
        }
    }
}
