using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace LastLandfall.EditorTools
{
    [InitializeOnLoad]
    public static class TripoVegetationValidation
    {
        static TripoVegetationValidation()
        {
            EditorApplication.update -= FinishImport;
            EditorApplication.update += FinishImport;
        }
        static void FinishImport()
        {
            if (!File.Exists("work/TripoImport/Vegetation/apply.request") || EditorApplication.isCompiling || EditorApplication.isUpdating || EditorApplication.isPlayingOrWillChangePlaymode) return;
            File.Delete("work/TripoImport/Vegetation/apply.request");
            ApplyAndValidate();
        }
        [MenuItem("Last Landfall/Apply and Validate Tripo Vegetation")]
        public static void ApplyAndValidate()
        {
            const string path="Assets/LastLandfall/Resources/Models/Environment/Tripo/VegetationRows";
            var models=AssetDatabase.FindAssets("t:Model",new[]{path});
            var diagnostics=new System.Text.StringBuilder();
            if(models.Length!=28) throw new System.Exception("Expected 28 vegetation models, found "+models.Length);
            foreach(string guid in models)
            {
                var importer=(ModelImporter)AssetImporter.GetAtPath(AssetDatabase.GUIDToAssetPath(guid));
                if(importer.materialImportMode!=ModelImporterMaterialImportMode.ImportStandard)
                {
                    importer.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;
                    importer.SaveAndReimport();
                }
                var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(AssetDatabase.GUIDToAssetPath(guid));
                foreach(var filter in prefab.GetComponentsInChildren<MeshFilter>()) diagnostics.AppendLine(prefab.name+" rotation="+filter.transform.localEulerAngles+" mesh="+filter.sharedMesh.bounds.size+" root="+prefab.transform.localEulerAngles);
                if(prefab.GetComponentsInChildren<MeshFilter>().Any(f=>f.sharedMesh==null)) throw new System.Exception("Missing mesh: "+prefab.name);
            }
            AssetDatabase.SaveAssets();
            LastLandfallProjectSetup.ApplyExpandedArchipelago();
            File.WriteAllText("work/TripoImport/Vegetation/orientation.txt",diagnostics.ToString());
            var plants=Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include,FindObjectsSortMode.None)
                .Where(r=>r.name.StartsWith("Tripo_Vegetation_") && r.enabled && r.gameObject.activeInHierarchy).ToArray();
            int missing=plants.Sum(r=>r.sharedMaterials.Count(m=>m==null || m.mainTexture==null));
            File.WriteAllText("work/TripoImport/Vegetation/unity_validation.txt",$"Models: {models.Length}\nPlaced plants: {plants.Length}\nMissing textures: {missing}\n");
            if(plants.Length==0 || missing>0) throw new System.Exception("Tripo vegetation validation failed; inspect unity_validation.txt");
            Debug.Log($"TRIPO_VEGETATION_VALIDATED: {models.Length} models, {plants.Length} plants, all textures assigned.");
        }
    }
}
