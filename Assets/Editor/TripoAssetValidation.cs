using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace LastLandfall.EditorTools
{
    public static class TripoAssetValidation
    {
        [MenuItem("Last Landfall/Validate Tripo Assets")]
        public static void Run()
        {
            var report = new StringBuilder();
            foreach (string model in new[] { "Characters/Adventurer/Adventurer", "Characters/Survival/Survival", "Rocky/Rocky" })
            {
                string path = "Assets/LastLandfall/Resources/Models/Environment/Tripo/" + model + ".fbx";
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (prefab == null) throw new System.Exception("Missing model: " + path);
                report.AppendLine(model + ": skinned meshes=" + prefab.GetComponentsInChildren<SkinnedMeshRenderer>(true).Length);
                int clipCount = 0;
                foreach (var asset in AssetDatabase.LoadAllAssetsAtPath(path))
                    if (asset is AnimationClip clip && !clip.name.StartsWith("__preview__"))
                    {
                        clipCount++;
                        report.AppendLine("  clip=" + clip.name + ", length=" + clip.length + ", legacy=" + clip.legacy);
                    }
                if (model.StartsWith("Characters/") && (clipCount == 0 || prefab.GetComponentInChildren<Animation>(true) == null))
                    throw new System.Exception("Missing character animation: " + model);
            }
            Directory.CreateDirectory("work/TripoImport");
            File.WriteAllText("work/TripoImport/validation.txt", report.ToString());
            Debug.Log(report.ToString());
        }
    }
}
