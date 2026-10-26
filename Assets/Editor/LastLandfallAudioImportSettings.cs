using UnityEditor;
using UnityEngine;

namespace LastLandfall.EditorTools
{
    internal sealed class LastLandfallAudioImportSettings : AssetPostprocessor
    {
        private void OnPreprocessAudio()
        {
            if (!assetPath.StartsWith("Assets/LastLandfall/Resources/Audio/")) return;
            var importer = (AudioImporter)assetImporter;
            bool music = assetPath.Contains("/Music/");
            AudioImporterSampleSettings settings = importer.defaultSampleSettings;
            settings.loadType = music ? AudioClipLoadType.Streaming : AudioClipLoadType.CompressedInMemory;
            settings.compressionFormat = AudioCompressionFormat.Vorbis;
            settings.sampleRateSetting = AudioSampleRateSetting.PreserveSampleRate;
            settings.quality = 0.7f;
            settings.preloadAudioData = false;
            importer.defaultSampleSettings = settings;
            importer.forceToMono = false;
            importer.loadInBackground = true;
        }
    }
}
