using UnityEngine;

namespace LastLandfall.Prototype
{
    // Shared by gameplay and the water preview to keep the displayed result
    // identical to runtime Material.SetColor / linear color-space settings.
    public static class FloodwaterAppearance
    {
        public const float FoamWidth = 2.4f;
        public const float FoamStrength = 0.85f;
        public static void Configure(Material material)
        {
            material.SetColor("_DeepColor", new Color(.032f, .165f, .245f));
            material.SetColor("_MidColor", new Color(.058f, .295f, .375f));
            material.SetColor("_ShallowColor", new Color(.125f, .475f, .465f));
            material.SetColor("_SubsurfaceColor", new Color(.14f, .56f, .49f));
            material.SetColor("_FoamColor", new Color(.92f, .96f, .95f));
            material.SetFloat("_ShoreFoamWidth", FoamWidth);
            material.SetFloat("_ShoreFoamStrength", FoamStrength);
            material.SetFloat("_WaveSpeed", .65f);
            material.SetFloat("_WaveHeight", .32f);
            material.SetFloat("_RippleStrength", .30f);
            material.SetFloat("_ReflectionStrength", .78f);
            Texture2D slopeA = Resources.Load<Texture2D>("Textures/Environment/OceanSlopeA");
            Texture2D slopeB = Resources.Load<Texture2D>("Textures/Environment/OceanSlopeB");
            if (slopeA != null && slopeB != null)
            {
                material.SetTexture("_OceanSlopeA", slopeA);
                material.SetTexture("_OceanSlopeB", slopeB);
            }
            else Debug.LogWarning("Ocean slope data is missing; water will use its procedural fallback.");
        }

        public static int DisableSceneOceans(Transform currentMapRoot)
        {
            if (currentMapRoot == null) return 0;
            int disabled = 0;
            foreach (Renderer renderer in Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include))
            {
                if (!renderer.name.StartsWith("Floodwater |", System.StringComparison.Ordinal) ||
                    renderer.transform.IsChildOf(currentMapRoot) || !renderer.gameObject.activeSelf) continue;
                // Saved editor previews otherwise overlap the new runtime sea.
                // Basin/stream water has a different name and remains active.
                renderer.gameObject.SetActive(false);
                disabled++;
            }
            return disabled;
        }
    }
}
