using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace LastLandfall.EditorTools
{
    [InitializeOnLoad]
    public static class MainIslandShoreValidation
    {
        static MainIslandShoreValidation() { EditorApplication.update += CheckRequest; }
        static void CheckRequest()
        {
            const string request = "work/TripoImport/Shore/apply.request";
            if (!File.Exists(request) || EditorApplication.isCompiling || EditorApplication.isUpdating || EditorApplication.isPlayingOrWillChangePlaymode) return;
            File.Delete(request);
            Apply();
        }
        [MenuItem("Last Landfall/Apply Main Island Shore Height")]
        public static void Apply()
        {
            const string path = "Assets/LastLandfall/Resources/MainIslandShoreSettings.asset";
            var settings = AssetDatabase.LoadAssetAtPath<MainIslandShoreSettings>(path);
            if (settings == null)
            {
                settings = ScriptableObject.CreateInstance<MainIslandShoreSettings>();
                AssetDatabase.CreateAsset(settings,path);
            }
            AssetDatabase.SaveAssets();
            EditorSceneManager.SaveOpenScenes();
            LastLandfallProjectSetup.ApplyExpandedArchipelago();
            var terrain = Object.FindObjectsByType<MeshCollider>(FindObjectsInactive.Exclude,FindObjectsSortMode.None)
                .FirstOrDefault(c=>c.name.Contains("terrain source") && c.enabled && c.GetComponent<Renderer>().enabled && !IsSatellite(c.transform));
            if (terrain == null) throw new System.Exception("Main island preview missing.");
            var b = terrain.bounds;
            Physics.SyncTransforms();
            int beforeLand=0, afterLand=0, shallow=0;
            const float sea = -.92f;
            for (int x=0;x<80;x++) for (int z=0;z<80;z++)
            {
                var origin = new Vector3(Mathf.Lerp(b.min.x,b.max.x,(x+.5f)/80f),b.max.y+10f,
                    Mathf.Lerp(b.min.z,b.max.z,(z+.5f)/80f));
                if (!terrain.Raycast(new Ray(origin,Vector3.down),out var hit,b.size.y+20f)) continue;
                if (hit.point.y+settings.sinkDepth>sea) beforeLand++;
                if (hit.point.y>sea) afterLand++;
                if (hit.point.y>sea && hit.point.y<sea+1.2f) shallow++;
            }
            Directory.CreateDirectory("work/TripoImport/Shore");
            File.WriteAllText("work/TripoImport/Shore/validation.txt",
                $"Main island sink depth: {settings.sinkDepth}\nSea level: {sea}\nDry land sample count before: {beforeLand}\nAfter: {afterLand}\nLow shoreline samples: {shallow}\nMain terrain bounds: {b}\n");
            if (afterLand==0) throw new System.Exception("Main island was submerged completely.");
            Debug.Log($"MAIN_ISLAND_SHORE_VALIDATED: lowered {settings.sinkDepth}m, dry land {afterLand}/{beforeLand}");
        }
        static bool IsSatellite(Transform t)
        {
            for (;t!=null;t=t.parent) if(t.name.Contains("West") || t.name.Contains("East")) return true;
            return false;
        }
    }
}
