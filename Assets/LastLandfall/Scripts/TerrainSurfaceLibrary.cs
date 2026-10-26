using UnityEngine;

namespace LastLandfall.Prototype
{
    public static class TerrainSurfaceLibrary
    {
        public static void Configure(Material material)
        {
            if (material == null || !material.HasProperty("_GroundDetail")) return;
            material.SetTexture("_GroundDetail", Resources.Load<Texture2D>("Textures/Terrain/GroundAlbedo"));
            material.SetTexture("_GroundSurface", Resources.Load<Texture2D>("Textures/Terrain/GroundSurface"));
            material.SetTexture("_RockDetail", Resources.Load<Texture2D>("Textures/Terrain/RockAlbedo"));
            material.SetTexture("_RockSurface", Resources.Load<Texture2D>("Textures/Terrain/RockSurface"));
            material.SetFloat("_GroundTiling", .45f);
            material.SetFloat("_RockTiling", .28f);
            material.SetFloat("_SurfaceDetail", .85f);
            material.SetFloat("_TextureWeight", 0f); // Heightfield meshes do not use imported UVs.
            material.SetFloat("_NormalStrength", .6f);
            material.SetColor("_GrassTint", new Color(.235f,.285f,.165f));
            material.SetColor("_SoilTint", new Color(.29f,.255f,.19f));
            material.SetColor("_RockTint", new Color(.35f,.36f,.345f));
        }
    }
}
