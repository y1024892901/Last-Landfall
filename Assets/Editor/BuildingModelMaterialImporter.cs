using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace LastLandfall.EditorTools
{
    // Generated building materials use explicit source values instead of relying
    // on the lossy Standard-to-URP conversion performed by an FBX importer.
    public sealed class BuildingModelMaterialImporter : AssetPostprocessor
    {
        private const string ManifestPath = "Assets/LastLandfall/Art/Reports/BuildingAudit/material_manifest.json";
        private Dictionary<string, MaterialSettings> settings;

        [Serializable]
        private sealed class MaterialManifest { public MaterialSettings[] materials; }

        [Serializable]
        private sealed class MaterialSettings
        {
            public string name;
            public float[] color;
            public float metallic;
            public float smoothness;
            public float[] emission;
        }

        public override uint GetVersion() { return 1; }

        private bool IsBuildingModel()
        {
            return (assetPath.StartsWith("Assets/LastLandfall/Resources/Models/Buildings/", StringComparison.Ordinal) ||
                    assetPath.StartsWith("Assets/LastLandfall/Resources/Models/Infrastructure/", StringComparison.Ordinal)) &&
                   (assetPath.EndsWith("_DeepSeek.fbx", StringComparison.Ordinal) ||
                    assetPath.EndsWith("/WaterStorageTank.fbx", StringComparison.Ordinal));
        }

        private void OnPreprocessModel()
        {
            if (!IsBuildingModel()) return;
            ModelImporter importer = (ModelImporter)assetImporter;
            importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
            if (File.Exists(ManifestPath)) context.DependsOnSourceAsset(ManifestPath);
        }

        private void OnPostprocessMaterial(Material material)
        {
            if (!IsBuildingModel() || !File.Exists(ManifestPath)) return;
            if (settings == null)
            {
                settings = new Dictionary<string, MaterialSettings>();
                MaterialManifest manifest = JsonUtility.FromJson<MaterialManifest>(File.ReadAllText(ManifestPath));
                if (manifest == null || manifest.materials == null) return;
                foreach (MaterialSettings entry in manifest.materials) settings[entry.name] = entry;
            }
            if (!settings.TryGetValue(material.name, out MaterialSettings source)) return;
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) return;
            material.shader = shader;
            material.SetColor("_BaseColor", new Color(source.color[0], source.color[1], source.color[2], source.color[3]));
            material.SetFloat("_Metallic", source.metallic);
            material.SetFloat("_Smoothness", source.smoothness);
            Color emission = new Color(source.emission[0], source.emission[1], source.emission[2]);
            material.SetColor("_EmissionColor", emission);
            if (emission.maxColorComponent > 0f) material.EnableKeyword("_EMISSION");
            else material.DisableKeyword("_EMISSION");

            bool transparent = source.color[3] < 0.999f;
            material.SetFloat("_Surface", transparent ? 1f : 0f);
            material.SetFloat("_Blend", 0f);
            material.SetFloat("_AlphaClip", 0f);
            material.SetFloat("_SrcBlend", (float)(transparent ? BlendMode.SrcAlpha : BlendMode.One));
            material.SetFloat("_DstBlend", (float)(transparent ? BlendMode.OneMinusSrcAlpha : BlendMode.Zero));
            material.SetFloat("_ZWrite", transparent ? 0f : 1f);
            material.SetOverrideTag("RenderType", transparent ? "Transparent" : "Opaque");
            material.DisableKeyword("_ALPHATEST_ON");
            material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            if (transparent) material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            else material.DisableKeyword("_SURFACE_TYPE_TRANSPARENT");
            material.SetShaderPassEnabled("ShadowCaster", !transparent);
            material.renderQueue = (int)(transparent ? RenderQueue.Transparent : RenderQueue.Geometry);
        }
    }
}
