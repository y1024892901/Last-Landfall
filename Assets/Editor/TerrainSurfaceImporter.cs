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
            importer.anisoLevel = 16;
            importer.mipmapEnabled = true;
            importer.textureCompression = TextureImporterCompression.CompressedHQ;
            importer.maxTextureSize = assetPath.Contains("MeadowGround_") ? 2048 : 1024;
            if (assetPath.Contains("MeadowGround_"))
            {
                importer.textureCompression = TextureImporterCompression.Uncompressed;
                importer.mipMapBias = -.35f;
            }
        }
    }
}
