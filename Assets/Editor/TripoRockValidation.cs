using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace LastLandfall.EditorTools
{
    [InitializeOnLoad]
    public static class TripoRockValidation
    {
        static TripoRockValidation() { EditorApplication.update += CheckRequest; }
        static void CheckRequest()
        {
            const string request = "work/TripoImport/Rocks/apply.request";
            if (!File.Exists(request) || EditorApplication.isCompiling || EditorApplication.isUpdating || EditorApplication.isPlayingOrWillChangePlaymode) return;
            File.Delete(request);
            Apply();
        }
        [MenuItem("Last Landfall/Apply and Validate Tripo Rocks")]
        public static void Apply()
        {
            const string path = "Assets/LastLandfall/Resources/Models/Environment/Tripo/Rocks";
            var models = AssetDatabase.FindAssets("t:Model",new[]{path});
            if (models.Length != 4) throw new System.Exception("Expected four Tripo rock models.");
            foreach (var guid in models)
            {
                string file = AssetDatabase.GUIDToAssetPath(guid);
                var importer = (ModelImporter)AssetImporter.GetAtPath(file);
                if (importer.materialImportMode != ModelImporterMaterialImportMode.ImportStandard)
                {
                    importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
                    importer.SaveAndReimport();
                }
            }
            LastLandfallProjectSetup.ApplyExpandedArchipelago();
            foreach (var tr in Object.FindObjectsByType<Transform>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                if (tr.name == "Tripo Vegetation Collection" && tr.parent != null)
                {
                    TripoVegetationAssets.Apply(tr.parent.gameObject);
                    TripoRockAssets.Apply(tr.parent.gameObject);
                }
            var rocks = Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include,FindObjectsSortMode.None)
                .Where(r=>r.name.StartsWith("Tripo_Rock_") && r.enabled && r.gameObject.activeInHierarchy).ToArray();
            int missing = rocks.Sum(r=>r.sharedMaterials.Count(m=>m==null || m.mainTexture==null));
            int main = rocks.Count(r=>r.name.StartsWith("Tripo_Rock_Main_"));
            int mainLarge = rocks.Count(r=>r.name.StartsWith("Tripo_Rock_Main_WeatheredBoulder_"));
            int west = rocks.Count(r=>r.name.StartsWith("Tripo_Rock_West_"));
            AssetDatabase.SaveAssets();
            EditorSceneManager.SaveOpenScenes();
            File.WriteAllText("work/TripoImport/Rocks/unity_validation.txt",$"Models: {models.Length}\nPlaced rocks: {rocks.Length}\nMain island: {main} (large boulders: {mainLarge})\nWest island: {west}\nMissing textures: {missing}\n");
            if (main < 40 || mainLarge != 1 || west < 50 || missing > 0) throw new System.Exception("Tripo rock validation failed.");
            Debug.Log("TRIPO_ROCKS_VALIDATED: " + rocks.Length);
        }
    }
}
