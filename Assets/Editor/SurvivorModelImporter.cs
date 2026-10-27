using System;
using UnityEditor;
using UnityEngine;

namespace LastLandfall.EditorTools
{
    // FBX contains simple authored material colours and the named joint pivots.
    public sealed class SurvivorModelImporter : AssetPostprocessor
    {
        bool Applies => assetPath.StartsWith("Assets/LastLandfall/Resources/Models/Characters/Survivor_",StringComparison.Ordinal)
                        && assetPath.EndsWith("_v2.fbx",StringComparison.Ordinal);
        void OnPreprocessModel()
        {
            if(!Applies)return;
            var importer=(ModelImporter)assetImporter;
            importer.preserveHierarchy=true;importer.importAnimation=false;importer.addCollider=false;
            importer.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;
            importer.materialLocation=ModelImporterMaterialLocation.InPrefab;
        }
        void OnPostprocessMaterial(Material material)
        {
            if(!Applies)return;
            Color color=material.HasProperty("_BaseColor")?material.GetColor("_BaseColor"):material.color;
            Shader shader=Shader.Find("Universal Render Pipeline/Lit");if(shader==null)return;
            material.shader=shader;material.SetColor("_BaseColor",color);material.SetFloat("_Smoothness",.18f);
        }
    }
}
