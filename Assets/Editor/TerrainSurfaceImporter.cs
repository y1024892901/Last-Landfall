using UnityEditor;
using UnityEngine;

namespace LastLandfall.EditorTools
{
    internal sealed class TerrainSurfaceImporter : AssetPostprocessor
    {
        private void OnPreprocessTexture()
        {
            if (!assetPath.Contains("/Textures/Terrain/")) return;
            var importer = (TextureImporter)assetImporter;
            importer.textureType = TextureImporterType.Default;
            importer.sRGBTexture = assetPath.EndsWith("Albedo.png");
            importer.wrapMode = TextureWrapMode.Repeat;
            importer.filterMode = FilterMode.Trilinear;
            importer.anisoLevel = 8;
            importer.mipmapEnabled = true;
            importer.textureCompression = TextureImporterCompression.CompressedHQ;
            importer.maxTextureSize = 1024;
        }
    }
}
