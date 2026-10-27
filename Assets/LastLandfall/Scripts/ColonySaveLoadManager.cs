using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace LastLandfall.Prototype
{
    [Serializable]
    public sealed class BuildingSaveEntry
    {
        public string assetName;
        public int anchorX;
        public int anchorY;
        public int rotation;
        public int woodCost;
    }

    [Serializable]
    public sealed class RoadSaveEntry
    {
        public int x;
        public int y;
    }

    [Serializable]
    public sealed class ColonySaveData
    {
        public int saveVersion = 1;
        public string saveTime;
        public float wood;
        public float food;
        public float water;
        public float metal;
        public float fuel;
        public float ore;
        public float medical;
        public int researchLevel;
        public List<string> efficiencyKeys = new List<string>();
        public List<BuildingSaveEntry> buildings = new List<BuildingSaveEntry>();
        public List<RoadSaveEntry> roads = new List<RoadSaveEntry>();
        public List<ColonyCitizen> citizens = new List<ColonyCitizen>();
        public Vector3 boatPos;
        public float boatRotY;
        public float boatFuel;
    }

    /// <summary>
    /// Handles full JSON serialization and deserialization of the Last Landfall colony state.
    /// Provides QuickSave (F5) and QuickLoad (F9) functionalities.
    /// </summary>
    public sealed class ColonySaveLoadManager : MonoBehaviour
    {
        private static ColonySaveLoadManager instance;
        public static ColonySaveLoadManager Instance => instance;

        public const string SaveFileName = "LastLandfall_Save.json";

        public static string SaveFilePath =>
            Path.Combine(Application.persistentDataPath, SaveFileName);

        public event Action<string> SaveLoadNotification;

        private void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(gameObject);
                return;
            }
            instance = this;
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.F5))
            {
                QuickSave();
            }
            else if (Input.GetKeyDown(KeyCode.F9))
            {
                ColonyModalDialog.Show(
                    "读取存档确认",
                    "是否确定读取快速存档？当前未保存的岛屿建设进度将会丢失。",
                    () => QuickLoad(),
                    null,
                    DialogSeverity.Warning,
                    "确认读取",
                    "取消"
                );
            }
        }

        public bool HasExistingSave()
        {
            return File.Exists(SaveFilePath);
        }

        public void QuickSave()
        {
            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            if (prototype == null) return;

            ColonySaveData data = new ColonySaveData
            {
                saveTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            };

            // 1. Resources
            var res = ColonyResourceManager.Instance;
            if (res != null)
            {
                data.wood = res.Wood;
                data.food = res.Food;
                data.water = res.Water;
                data.metal = res.Metal;
                data.fuel = res.Fuel;
                data.ore = res.Ore;
                data.medical = res.Medical;
            }

            // 2. Tech Progression
            data.researchLevel = prototype.ResearchLevel;
            data.efficiencyKeys = new List<string>(prototype.ResearchedEfficiencyKeys);

            // 3. Buildings & Roads
            foreach (var b in prototype.PlacedBuildings)
            {
                data.buildings.Add(new BuildingSaveEntry
                {
                    assetName = b.Definition.AssetName,
                    anchorX = b.Anchor.x,
                    anchorY = b.Anchor.y,
                    rotation = b.Rotation,
                    woodCost = b.WoodCost
                });
            }

            foreach (var r in prototype.RoadCells)
            {
                data.roads.Add(new RoadSaveEntry { x = r.x, y = r.y });
            }

            // 4. Citizens
            var citMgr = ColonyCitizenManager.Instance;
            if (citMgr != null)
            {
                data.citizens = new List<ColonyCitizen>(citMgr.Citizens);
            }

            // 5. Boat
            var boat = RescueBoatController.ActiveVessel;
            if (boat != null)
            {
                data.boatPos = boat.transform.position;
                data.boatRotY = boat.transform.eulerAngles.y;
                data.boatFuel = boat.FuelPercent;
            }

            string json = JsonUtility.ToJson(data, true);
            File.WriteAllText(SaveFilePath, json);
            SaveLoadNotification?.Invoke($"游戏进度已快速保存 (F5) [{data.saveTime}]");
        }

        public void QuickLoad()
        {
            if (!HasExistingSave())
            {
                SaveLoadNotification?.Invoke("未找到已保存的存档文件。");
                return;
            }

            string json = File.ReadAllText(SaveFilePath);
            ColonySaveData data = JsonUtility.FromJson<ColonySaveData>(json);
            if (data == null)
            {
                SaveLoadNotification?.Invoke("存档文件解析失败。");
                return;
            }

            var prototype = FindAnyObjectByType<BuildPlacementPrototype>();
            if (prototype == null) return;

            // 1. Restore resources
            var res = ColonyResourceManager.Instance;
            if (res != null)
            {
                res.LoadStockpiles(data.wood, data.food, data.water, data.metal, data.fuel, data.ore, data.medical);
            }

            // 2. Restore tech
            prototype.RestoreResearchProgress(data.researchLevel, data.efficiencyKeys);

            // 3. Rebuild structures
            prototype.RestoreColonyEntities(data.buildings, data.roads);

            // 4. Restore Citizens
            var citMgr = ColonyCitizenManager.Instance;
            if (citMgr != null)
            {
                citMgr.LoadCitizens(data.citizens);
            }

            // 5. Restore Boat
            var boat = RescueBoatController.ActiveVessel;
            if (boat != null && data.boatPos != Vector3.zero)
            {
                boat.SetBasePosition(data.boatPos, Quaternion.Euler(0f, data.boatRotY, 0f));
            }

            SaveLoadNotification?.Invoke($"已成功读取存档 [{data.saveTime}]！");
        }
    }
}
