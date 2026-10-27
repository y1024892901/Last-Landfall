using System;
using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>
    /// Resource types in Last Landfall settlement simulation.
    /// Matches the 8 header resource categories.
    /// </summary>
    public enum ResourceType
    {
        Wood,      // 木材
        Food,      // 食物 / 口粮
        Water,     // 淡水
        Metal,     // 金属 / 零件
        Fuel,      // 燃料
        Power,     // 电力 (实时产消平衡)
        Ore,       // 矿石
        Medical    // 医疗物资
    }

    /// <summary>
    /// Manages the colony's economic cycle: resource storage, dynamic production,
    /// power grid balance, facility consumption, and technology efficiency integration.
    /// </summary>
    public sealed class ColonyResourceManager : MonoBehaviour
    {
        private static ColonyResourceManager instance;
        public static ColonyResourceManager Instance => instance;

        [Header("Current Stockpiles")]
        [SerializeField] private float wood = 350f;
        [SerializeField] private float food = 80f;
        [SerializeField] private float water = 120f;
        [SerializeField] private float metal = 45f;
        [SerializeField] private float fuel = 60f;
        [SerializeField] private float powerSurplus = 0f;
        [SerializeField] private float ore = 20f;
        [SerializeField] private float medical = 15f;

        [Header("Capacities")]
        [SerializeField] private float baseGeneralCapacity = 400f;
        [SerializeField] private float baseWaterCapacity = 250f;
        [SerializeField] private float storageDepotBonus = 500f;
        [SerializeField] private float waterTankBonus = 350f;

        // Production rates per second
        private readonly Dictionary<ResourceType, float> netProductionRates = new Dictionary<ResourceType, float>();
        private float totalPowerGeneration;
        private float totalPowerDemand;
        private float tickTimer;
        private const float TickInterval = 1.0f; // 1 simulation second

        public float Wood => wood;
        public float Food => food;
        public float Water => water;
        public float Metal => metal;
        public float Fuel => fuel;
        public float PowerSurplus => powerSurplus;
        public float TotalPowerGeneration => totalPowerGeneration;
        public float TotalPowerDemand => totalPowerDemand;
        public float Ore => ore;
        public float Medical => medical;

        public event Action ResourcesUpdated;

        private void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(gameObject);
                return;
            }
            instance = this;

            foreach (ResourceType type in Enum.GetValues(typeof(ResourceType)))
            {
                netProductionRates[type] = 0f;
            }
        }

        private void Update()
        {
            float simSpeed = 1f;
            var weather = FindAnyObjectByType<IslandWeatherSystem>();
            if (weather != null) simSpeed = weather.SimulationSpeed;

            tickTimer += Time.deltaTime * simSpeed;
            if (tickTimer >= TickInterval)
            {
                tickTimer -= TickInterval;
                RunSimulationTick();
            }
        }

        public float GetAmount(ResourceType type)
        {
            switch (type)
            {
                case ResourceType.Wood: return wood;
                case ResourceType.Food: return food;
                case ResourceType.Water: return water;
                case ResourceType.Metal: return metal;
                case ResourceType.Fuel: return fuel;
                case ResourceType.Power: return powerSurplus;
                case ResourceType.Ore: return ore;
                case ResourceType.Medical: return medical;
                default: return 0f;
            }
        }

        public float GetCapacity(ResourceType type)
        {
            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            int storageCount = prototype != null ? prototype.CountCompletedBuildings("StorageDepot_DeepSeek") : 0;
            int waterTankCount = prototype != null ? prototype.CountCompletedBuildings("WaterStorageTank") : 0;

            if (type == ResourceType.Water)
            {
                return baseWaterCapacity + waterTankCount * waterTankBonus;
            }
            if (type == ResourceType.Power)
            {
                return Mathf.Max(10f, totalPowerGeneration);
            }
            return baseGeneralCapacity + storageCount * storageDepotBonus;
        }

        public bool TrySpend(ResourceType type, float amount)
        {
            if (amount <= 0f) return true;
            if (GetAmount(type) < amount) return false;

            ModifyAmount(type, -amount);
            return true;
        }

        public void Add(ResourceType type, float amount)
        {
            if (amount <= 0f) return;
            float maxCap = GetCapacity(type);
            float current = GetAmount(type);
            float toAdd = Mathf.Min(amount, Mathf.Max(0f, maxCap - current));
            ModifyAmount(type, toAdd);
        }

        private void ModifyAmount(ResourceType type, float delta)
        {
            switch (type)
            {
                case ResourceType.Wood: wood = Mathf.Max(0f, wood + delta); break;
                case ResourceType.Food: food = Mathf.Max(0f, food + delta); break;
                case ResourceType.Water: water = Mathf.Max(0f, water + delta); break;
                case ResourceType.Metal: metal = Mathf.Max(0f, metal + delta); break;
                case ResourceType.Fuel: fuel = Mathf.Max(0f, fuel + delta); break;
                case ResourceType.Power: powerSurplus += delta; break;
                case ResourceType.Ore: ore = Mathf.Max(0f, ore + delta); break;
                case ResourceType.Medical: medical = Mathf.Max(0f, medical + delta); break;
            }
            ResourcesUpdated?.Invoke();
        }

        public float GetNetRate(ResourceType type)
        {
            return netProductionRates.TryGetValue(type, out float rate) ? rate : 0f;
        }

        /// <summary>
        /// Periodic economic evaluation: loops through all operating buildings,
        /// calculates power grid, water production, food farming, salvage, and maintenance.
        /// </summary>
        private void RunSimulationTick()
        {
            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            if (prototype == null) return;

            var weather = FindAnyObjectByType<IslandWeatherSystem>();
            bool isDaytime = weather == null || (weather.TimeOfDayHours >= 6f && weather.TimeOfDayHours <= 18.5f);
            float solarSunEfficiency = isDaytime ? (weather != null && weather.CurrentWeather == IslandWeatherType.Clear ? 1.0f : 0.65f) : 0f;

            // Reset rates
            foreach (ResourceType type in Enum.GetValues(typeof(ResourceType)))
            {
                netProductionRates[type] = 0f;
            }

            // 1. Calculate Power Generation vs Demand
            totalPowerGeneration = 0f;
            totalPowerDemand = 0f;

            int solarCount = prototype.CountCompletedBuildings("SolarPowerStation_DeepSeek");
            float solarMultiplier = BuildPlacementPrototype.GetBuildingEfficiencyMultiplier("SolarPowerStation_DeepSeek");
            totalPowerGeneration += solarCount * 18.0f * solarSunEfficiency * solarMultiplier;

            // Power Demands
            int desalCount = prototype.CountCompletedBuildings("DesalinationPlant_DeepSeek");
            int greenhouseCount = prototype.CountCompletedBuildings("Greenhouse_DeepSeek");
            int commCount = prototype.CountCompletedBuildings("LocalCommunicationsCenter_DeepSeek") +
                            prototype.CountCompletedBuildings("RescueRadioCenter_DeepSeek");
            int researchCount = prototype.CountCompletedBuildings("ResearchStation_DeepSeek");
            int medicalCount = prototype.CountCompletedBuildings("MedicalStation_DeepSeek");

            totalPowerDemand += desalCount * 3.5f;
            totalPowerDemand += greenhouseCount * 2.5f;
            totalPowerDemand += commCount * 1.5f;
            totalPowerDemand += researchCount * 2.0f;
            totalPowerDemand += medicalCount * 2.0f;

            powerSurplus = totalPowerGeneration - totalPowerDemand;
            bool hasSufficientPower = totalPowerGeneration >= totalPowerDemand || totalPowerDemand <= 0f;
            float powerOperationRatio = hasSufficientPower ? 1.0f : Mathf.Clamp01(totalPowerGeneration / Mathf.Max(0.1f, totalPowerDemand));

            // 2. Water Production (Desalination)
            if (desalCount > 0)
            {
                float desalMult = BuildPlacementPrototype.GetBuildingEfficiencyMultiplier("DesalinationPlant_DeepSeek");
                float waterProduced = desalCount * 2.2f * powerOperationRatio * desalMult;
                Add(ResourceType.Water, waterProduced);
                netProductionRates[ResourceType.Water] += waterProduced;
            }

            // 3. Food Production (Greenhouse & Fishing Dock & Kitchen)
            if (greenhouseCount > 0)
            {
                float ghMult = BuildPlacementPrototype.GetBuildingEfficiencyMultiplier("Greenhouse_DeepSeek");
                float rawCropRate = greenhouseCount * 1.6f * powerOperationRatio * ghMult;
                // Greenhouse consumes 0.4 water per tick
                float waterNeeded = greenhouseCount * 0.4f;
                if (water >= waterNeeded)
                {
                    TrySpend(ResourceType.Water, waterNeeded);
                    netProductionRates[ResourceType.Water] -= waterNeeded;
                    Add(ResourceType.Food, rawCropRate);
                    netProductionRates[ResourceType.Food] += rawCropRate;
                }
            }

            int fishingCount = prototype.CountCompletedBuildings("FishingDock_DeepSeek");
            if (fishingCount > 0)
            {
                float fishMult = BuildPlacementPrototype.GetBuildingEfficiencyMultiplier("FishingDock_DeepSeek");
                float fishRate = fishingCount * 1.2f * fishMult;
                Add(ResourceType.Food, fishRate);
                netProductionRates[ResourceType.Food] += fishRate;
            }

            int kitchenCount = prototype.CountCompletedBuildings("PublicKitchen_DeepSeek");
            if (kitchenCount > 0 && food > 0f)
            {
                // Kitchen boosts overall food value by processing raw catch/crops
                float kitchenMult = BuildPlacementPrototype.GetBuildingEfficiencyMultiplier("PublicKitchen_DeepSeek");
                float bonusRations = kitchenCount * 0.5f * kitchenMult;
                Add(ResourceType.Food, bonusRations);
                netProductionRates[ResourceType.Food] += bonusRations;
            }

            // 4. Wood & Salvage (Driftwood Boom & Salvage Workshop)
            int boomCount = prototype.CountCompletedBuildings("DriftwoodCollectionBoom_DeepSeek");
            if (boomCount > 0)
            {
                float boomMult = BuildPlacementPrototype.GetBuildingEfficiencyMultiplier("DriftwoodCollectionBoom_DeepSeek");
                float woodYield = boomCount * 0.9f * boomMult;
                Add(ResourceType.Wood, woodYield);
                netProductionRates[ResourceType.Wood] += woodYield;
            }

            int workshopCount = prototype.CountCompletedBuildings("SalvageWorkshop_DeepSeek");
            if (workshopCount > 0)
            {
                float wsMult = BuildPlacementPrototype.GetBuildingEfficiencyMultiplier("SalvageWorkshop_DeepSeek");
                float metalYield = workshopCount * 0.6f * wsMult;
                Add(ResourceType.Metal, metalYield);
                netProductionRates[ResourceType.Metal] += metalYield;
            }

            int forgeCount = prototype.CountCompletedBuildings("Forge_DeepSeek");
            if (forgeCount > 0 && ore >= 1f)
            {
                TrySpend(ResourceType.Ore, 0.4f);
                float forgeMult = BuildPlacementPrototype.GetBuildingEfficiencyMultiplier("Forge_DeepSeek");
                float metalYield = forgeCount * 0.8f * forgeMult;
                Add(ResourceType.Metal, metalYield);
                netProductionRates[ResourceType.Metal] += metalYield;
                netProductionRates[ResourceType.Ore] -= 0.4f;
            }

            // 5. Medical Supplies (Medical Station)
            if (medicalCount > 0 && powerOperationRatio > 0.5f)
            {
                float medMult = BuildPlacementPrototype.GetBuildingEfficiencyMultiplier("MedicalStation_DeepSeek");
                float medProduced = medicalCount * 0.25f * medMult;
                Add(ResourceType.Medical, medProduced);
                netProductionRates[ResourceType.Medical] += medProduced;
            }

            ResourcesUpdated?.Invoke();
        }

        public void LoadStockpiles(float w, float f, float wt, float m, float fl, float o, float med)
        {
            wood = w;
            food = f;
            water = wt;
            metal = m;
            fuel = fl;
            ore = o;
            medical = med;
            ResourcesUpdated?.Invoke();
        }
    }
}
