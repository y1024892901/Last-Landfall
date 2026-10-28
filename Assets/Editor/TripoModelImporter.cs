using UnityEditor;
using UnityEngine;

namespace LastLandfall.EditorTools
{
    internal sealed class TripoModelImporter : AssetPostprocessor
    {
        void OnPreprocessModel()
        {
            if (!assetPath.Contains("/Tripo/")) return;
            var importer = (ModelImporter)assetImporter;
            importer.isReadable = true;
            importer.importCameras = false;
            importer.importLights = false;
            importer.importAnimation = false;
            importer.materialImportMode = ModelImporterMaterialImportMode.None;
        }

        void OnPreprocessTexture()
        {
            if (!assetPath.Contains("/Tripo/")) return;
            var importer = (TextureImporter)assetImporter;
            importer.sRGBTexture = true;
            importer.isReadable = assetPath.Contains("/Island/");
            importer.maxTextureSize = 4096;
            importer.mipmapEnabled = true;
            importer.anisoLevel = 4;
            importer.textureCompression = TextureImporterCompression.CompressedHQ;
        }
    }
}
