using UnityEditor;
using UnityEngine;

namespace LastLandfall.EditorTools
{
    internal sealed class OceanTextureImportSettings : AssetPostprocessor
    {
        private void OnPreprocessTexture()
        {
            if (!assetPath.EndsWith("/OceanSlopeA.png") && !assetPath.EndsWith("/OceanSlopeB.png")) return;
            var importer = (TextureImporter)assetImporter;
            importer.textureType = TextureImporterType.Default;
            importer.sRGBTexture = false;
            importer.mipmapEnabled = true;
            importer.wrapMode = TextureWrapMode.Repeat;
            importer.filterMode = FilterMode.Trilinear;
            importer.anisoLevel = 2;
            importer.alphaSource = TextureImporterAlphaSource.None;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.maxTextureSize = 512;
        }
    }
}
