using System;
using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    [Serializable]
    public sealed class ColonyCitizen
    {
        public string id;
        public string name;
        public string profession;
        public float health = 100f;
        public float morale = 80f;
        public float hunger = 0f;  // 0 = full, 100 = starving
        public float thirst = 0f;  // 0 = quenched, 100 = dehydrated
        public string assignedBuilding = string.Empty;
        public bool isIll;

        [NonSerialized]
        public SurvivorCharacterController characterController;
    }

    /// <summary>
    /// Manages settlement population, workforce allocation, housing capacity,
    /// and survivor physiological needs (water, food, medical health, morale).
    /// </summary>
    public sealed class ColonyCitizenManager : MonoBehaviour
    {
        private static ColonyCitizenManager instance;
        public static ColonyCitizenManager Instance => instance;

        [SerializeField] private List<ColonyCitizen> citizens = new List<ColonyCitizen>();
        private float metabolicTimer;
        private const float MetabolicTickInterval = 2.5f;

        public IReadOnlyList<ColonyCitizen> Citizens => citizens;
        public int TotalPopulation => citizens.Count;

        public event Action PopulationChanged;

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
            // Initial crew from lore
            if (citizens.Count == 0)
            {
                RegisterInitialCrew();
            }
        }

        private void Update()
        {
            float simSpeed = 1f;
            var weather = FindAnyObjectByType<IslandWeatherSystem>();
            if (weather != null) simSpeed = weather.SimulationSpeed;

            metabolicTimer += Time.deltaTime * simSpeed;
            if (metabolicTimer >= MetabolicTickInterval)
            {
                metabolicTimer -= MetabolicTickInterval;
                RunMetabolicTick();
            }
        }

        public int GetHousingCapacity()
        {
            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            if (prototype == null) return 2;

            int woodShelters = prototype.CountCompletedBuildings("WoodShelter_DeepSeek");
            int residentHuts = prototype.CountCompletedBuildings("ResidentHut_DeepSeek");

            // Base 2 (crew raft), +2 per wood shelter, +4 per resident hut
            return 2 + woodShelters * 2 + residentHuts * 4;
        }

        public int GetEmployedCount()
        {
            int count = 0;
            for (int i = 0; i < citizens.Count; i++)
            {
                if (!string.IsNullOrEmpty(citizens[i].assignedBuilding)) count++;
            }
            return count;
        }

        public int GetIdleCount()
        {
            return Mathf.Max(0, TotalPopulation - GetEmployedCount());
        }

        private void RegisterInitialCrew()
        {
            AddCitizenInternal("阿岩", "搜救驾驶员", 100f, 90f);
            AddCitizenInternal("小海", "技术维修员", 100f, 85f);
        }

        private ColonyCitizen AddCitizenInternal(string name, string role, float health = 100f, float morale = 80f)
        {
            ColonyCitizen citizen = new ColonyCitizen
            {
                id = Guid.NewGuid().ToString().Substring(0, 8),
                name = name,
                profession = role,
                health = health,
                morale = morale
            };
            citizens.Add(citizen);
            PopulationChanged?.Invoke();
            return citizen;
        }

        /// <summary>
        /// Recruits a newly rescued survivor into the settlement.
        /// </summary>
        public bool RescueNewSurvivor(string name, string role, Vector3 spawnPosition)
        {
            var citizen = AddCitizenInternal(name, role, UnityEngine.Random.Range(70f, 95f), UnityEngine.Random.Range(65f, 90f));

            // Spawn visual character model
            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            Transform mapRoot = prototype != null ? prototype.transform.Find("Island Play Space - Rotate and Pan") : null;
            var charController = SurvivorCharacterController.Spawn(spawnPosition, name, role, mapRoot);
            citizen.characterController = charController;

            PopulationChanged?.Invoke();
            return true;
        }

        private void RunMetabolicTick()
        {
            if (citizens.Count == 0) return;
            var resourceMgr = ColonyResourceManager.Instance;
            if (resourceMgr == null) return;

            float perCitizenWater = 0.22f;
            float perCitizenFood = 0.16f;

            float totalWaterNeeded = citizens.Count * perCitizenWater;
            float totalFoodNeeded = citizens.Count * perCitizenFood;

            bool hadWater = resourceMgr.TrySpend(ResourceType.Water, totalWaterNeeded);
            bool hadFood = resourceMgr.TrySpend(ResourceType.Food, totalFoodNeeded);

            for (int i = 0; i < citizens.Count; i++)
            {
                var c = citizens[i];

                // Thirst & Hunger adjustments
                if (!hadWater)
                {
                    c.thirst = Mathf.Min(100f, c.thirst + 4.5f);
                    c.morale = Mathf.Max(10f, c.morale - 2.5f);
                }
                else
                {
                    c.thirst = Mathf.Max(0f, c.thirst - 3.0f);
                }

                if (!hadFood)
                {
                    c.hunger = Mathf.Min(100f, c.hunger + 3.0f);
                    c.morale = Mathf.Max(10f, c.morale - 1.5f);
                }
                else
                {
                    c.hunger = Mathf.Max(0f, c.hunger - 2.5f);
                }

                // Severe dehydration or starvation causes health decline
                if (c.thirst > 70f || c.hunger > 80f)
                {
                    c.health = Mathf.Max(5f, c.health - 2.0f);
                }
                else if (hadWater && hadFood && c.health < 100f)
                {
                    c.health = Mathf.Min(100f, c.health + 1.0f);
                }
            }

            PopulationChanged?.Invoke();
        }

        public void LoadCitizens(List<ColonyCitizen> loadedCitizens)
        {
            citizens.Clear();
            if (loadedCitizens != null)
            {
                citizens.AddRange(loadedCitizens);
            }
            PopulationChanged?.Invoke();
        }
    }
}
