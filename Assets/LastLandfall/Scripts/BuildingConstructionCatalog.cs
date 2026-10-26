using System;
using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>Resource paths for all 25 authored assets (29 independent modules).</summary>
    public static class BuildingConstructionCatalog
    {
        [Serializable] private sealed class Catalog { public int schemaVersion; public Entry[] entries; }
        [Serializable] public sealed class Entry
        {
            public string key;
            public string[] aliases;
            public string modelResource;
            public string finalResource;
            public string scheduleResource;
        }
        [Serializable] public sealed class Schedule
        {
            public int schemaVersion;
            public string key;
            public int fps;
            public int frames;
            public float motionDistance;
            public Part[] parts;
            public Phase[] phases;
            public float Duration => (frames - 1f) / fps;
        }
        [Serializable] public sealed class Part
        {
            public string id;
            public string sourceName;
            public int start;
            public int end;
            public string mode;
        }
        [Serializable] public sealed class Phase { public string name; public int start; public int end; }

        private static Dictionary<string, Entry> entries;
        private static readonly Dictionary<string, Schedule> Schedules = new Dictionary<string, Schedule>();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetCache() { entries = null; Schedules.Clear(); }

        public static bool TryGet(string assetName, out Entry entry)
        {
            if (entries == null)
            {
                entries = new Dictionary<string, Entry>(StringComparer.Ordinal);
                TextAsset data = Resources.Load<TextAsset>("Construction/Catalog");
                Catalog catalog = data != null ? JsonUtility.FromJson<Catalog>(data.text) : null;
                if (catalog != null && catalog.schemaVersion == 1 && catalog.entries != null)
                    foreach (Entry item in catalog.entries)
                    {
                        entries[item.key] = item;
                        if (item.aliases != null)
                            foreach (string alias in item.aliases) entries[alias] = item;
                    }
            }
            return entries.TryGetValue(assetName, out entry);
        }

        public static Schedule LoadSchedule(Entry entry)
        {
            if (Schedules.TryGetValue(entry.key, out Schedule cached)) return cached;
            TextAsset data = Resources.Load<TextAsset>(entry.scheduleResource);
            if (data == null) return null;
            Schedule schedule = JsonUtility.FromJson<Schedule>(data.text);
            if (schedule == null || schedule.schemaVersion != 1 || schedule.key != entry.key ||
                schedule.fps <= 0 || schedule.frames < 2 || schedule.parts == null || schedule.parts.Length == 0)
                return null;
            Schedules[entry.key] = schedule;
            return schedule;
        }
    }
}
