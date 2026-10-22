using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace LastLandfall.Prototype
{
    public enum IslandWeatherType
    {
        Clear,
        Overcast,
        Rain,
        Wind,
        Thunderstorm
    }

    /// <summary>
    /// Runtime weather presets for the generated island scene.
    /// </summary>
    public sealed class IslandWeatherSystem : MonoBehaviour
    {
        private struct WeatherProfile
        {
            public float SunIntensity;
            public float AmbientIntensity;
            public float WaveSpeed;
            public float WaveHeight;
            public float RainRate;
            public float WindStrength;
            public float Wetness;
            public float Cloudiness;
            public float FogAmount;
            public float FogStart;
            public float FogEnd;
            public float BasinFlowMultiplier;
            public float BasinRippleMultiplier;
            public Color SunTint;
            public Color AmbientTint;
            public Color FogColor;
        }

        private sealed class RendererBinding
        {
            public Renderer Renderer;
            public MaterialPropertyBlock OriginalBlock;
            public MaterialPropertyBlock WeatherBlock;
            public bool HasWetness;
            public bool HasCloudiness;
            public bool HasBasinFlowTime;
            public bool HasBasinRipple;
            public bool HasBasinTimeLight;
            public float BasinRipple;
        }

        private sealed class FoliageTarget
        {
            public Transform Transform;
            public Quaternion InitialRotation;
            public float Phase;
            public float MaxAngle;
        }

        private sealed class FoliageMaterialBinding
        {
            public Renderer Renderer;
            public int MaterialIndex;
            public int ColorPropertyId;
            public Color BaseColor;
            public MaterialPropertyBlock OriginalBlock;
            public MaterialPropertyBlock WeatherBlock;
        }

        private struct RainDrop
        {
            public Vector3 Position;
            public Vector3 Velocity;
            public float RemainingLife;
            public float Size;
        }

        private struct SplashDrop
        {
            public Vector3 Position;
            public Vector3 Velocity;
            public float RemainingLife;
            public float Size;
        }

        private static readonly Color NeutralTint = Color.white;
        private static readonly Vector2 WindDirection = new Vector2(0.78f, 0.42f).normalized;
        // Time keys are in local 24-hour clock time. Sunlight values describe
        // normalized light reaching a level island surface, not Light.intensity
        // before compensating for the sun's angle.
        private const float MinimumSunlightFloor = 0.55f;
        private const float MinimumAmbientFloor = 0.52f;
        private const float MinimumOvercastAmbientFloor = 0.38f;
        private static readonly float[] ClockHours = { 0f, 3f, 6f, 9f, 12f, 15f, 18f, 21f, 24f };
        private static readonly float[] DaylightBlendKeys = { 0f, 0f, 0f, 0.70f, 1f, 0.70f, 0f, 0f, 0f };
        // Night light falls to a blue twilight level, then rises toward the
        // full midday values. The minimum prevents the island from going black.
        private static readonly float[] ClearSkySunlightKeys =
            { 0.16f, 0.16f, 0.28f, 0.78f, 1f, 0.78f, 0.28f, 0.16f, 0.16f };
        private static readonly float[] ClearSkyAmbientKeys =
            { 0.40f, 0.42f, 0.56f, 0.84f, 1f, 0.84f, 0.56f, 0.42f, 0.40f };
        private static readonly float[] SunPitchCurveKeys =
            { 10f, 10f, 20f, 48f, 70f, 48f, 20f, 10f, 10f };
        private static readonly int WeatherWetnessId = Shader.PropertyToID("_WeatherWetness");
        private static readonly int WeatherCloudinessId = Shader.PropertyToID("_WeatherCloudiness");
        private static readonly int WaveTimeId = Shader.PropertyToID("_WaveTime");
        private static readonly int BasinFlowTimeId = Shader.PropertyToID("_FlowTime");
        private static readonly int BasinRippleId = Shader.PropertyToID("_RippleStrength");
        private static readonly int BasinTimeLightId = Shader.PropertyToID("_TimeOfDayLight");
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        private static readonly int LegacyColorId = Shader.PropertyToID("_Color");
        private static readonly Vector2[] WeatherViewportCorners =
        {
            new Vector2(0f, 0f),
            new Vector2(0f, 1f),
            new Vector2(1f, 0f),
            new Vector2(1f, 1f)
        };

        private readonly List<RendererBinding> rendererBindings = new List<RendererBinding>();
        private readonly List<FoliageTarget> foliageTargets = new List<FoliageTarget>();
        private readonly List<FoliageMaterialBinding> foliageMaterialBindings = new List<FoliageMaterialBinding>();
        private readonly List<RainDrop> rainDrops = new List<RainDrop>(2600);
        private readonly List<SplashDrop> splashDrops = new List<SplashDrop>(1400);
        private readonly Matrix4x4[] rainMatrices = new Matrix4x4[1023];
        private readonly Matrix4x4[] splashMatrices = new Matrix4x4[1023];

        private Camera weatherCamera;
        private Light sun;
        private Material oceanMaterial;
        private GameObject weatherEffectsRoot;
        private Material weatherParticleMaterial;
        private Material splashParticleMaterial;
        private Mesh weatherParticleQuad;
        private Texture2D screenDropletTexture;
        private Bounds islandBounds;
        private bool hasIslandBounds;
        private float baseSunIntensity;
        private Color baseSunColor;
        private float baseAmbientIntensity;
        private Color baseAmbientLight;
        private Color baseAmbientSky;
        private Color baseAmbientEquator;
        private Color baseAmbientGround;
        private bool baseFogEnabled;
        private FogMode baseFogMode;
        private Color baseFogColor;
        private float baseFogDensity;
        private float baseFogStart;
        private float baseFogEnd;
        private float baseWaveSpeed;
        private float baseWaveHeight;
        private Quaternion baseSunRotation;
        private float baseSunAzimuth;
        private AmbientMode baseAmbientMode;
        private Material baseSkyboxMaterial;
        private Material timeSkyboxMaterial;
        private Light baseRenderSettingsSun;
        private float baseSkyboxExposure = 1f;
        private Color baseSkyboxTint = Color.white;
        private Color baseSkyboxGroundColor = Color.white;
        private float baseSkyboxSunSize = 0.04f;
        private float baseSkyboxAtmosphereThickness = 1f;
        private float timeOfDayHours = 9f;
        private float simulationSpeed = 1f;
        private double waterPhaseTime;
        private double basinFlowPhaseTime;
        private float foliageWindPhase;
        private float lastFoliageCloudiness = -1f;
        private float gustClock;
        private float gustStrength;
        private float rainWindPhase;
        private float rainSpawnRemainder;
        private WeatherProfile currentProfile;
        private WeatherProfile transitionStart;
        private WeatherProfile transitionTarget;
        private float transitionElapsed;
        private float transitionDuration = 4.5f;
        private float currentWetness;
        private float rainVisualRate;
        private float rainTransitionStart;
        private float rainTransitionTarget;
        private float rainTransitionElapsed;
        private float rainTransitionDuration = 6f;
        private float lightningCountdown;
        private float lightningElapsed = -1f;
        private bool initialized;

        public IslandWeatherType CurrentWeather { get; private set; }

        public string CurrentWeatherName => GetWeatherName(CurrentWeather);
        public float TimeOfDayHours => timeOfDayHours;
        public float SimulationSpeed => simulationSpeed;

        public void SetTimeOfDay(float hours)
        {
            timeOfDayHours = Mathf.Repeat(hours, 24f);
        }

        public void SetSimulationSpeed(float multiplier)
        {
            simulationSpeed = Mathf.Clamp(multiplier, 1f, 3f);
        }

        public void Initialize(Camera camera, Light directionalSun, Material floodwaterMaterial,
            Transform island)
        {
            if (initialized)
            {
                return;
            }

            weatherCamera = camera;
            sun = directionalSun;
            oceanMaterial = floodwaterMaterial;

            if (sun != null)
            {
                baseSunIntensity = sun.intensity;
                baseSunColor = sun.color;
                baseSunRotation = sun.transform.rotation;
                baseSunAzimuth = sun.transform.eulerAngles.y;
            }

            baseAmbientMode = RenderSettings.ambientMode;
            baseAmbientIntensity = RenderSettings.ambientIntensity;
            baseAmbientLight = RenderSettings.ambientLight;
            baseAmbientSky = RenderSettings.ambientSkyColor;
            baseAmbientEquator = RenderSettings.ambientEquatorColor;
            baseAmbientGround = RenderSettings.ambientGroundColor;
            baseFogEnabled = RenderSettings.fog;
            baseFogMode = RenderSettings.fogMode;
            baseFogColor = RenderSettings.fogColor;
            baseFogDensity = RenderSettings.fogDensity;
            baseFogStart = RenderSettings.fogStartDistance;
            baseFogEnd = RenderSettings.fogEndDistance;
            baseRenderSettingsSun = RenderSettings.sun;
            baseSkyboxMaterial = RenderSettings.skybox;
            if (baseSkyboxMaterial != null)
            {
                timeSkyboxMaterial = new Material(baseSkyboxMaterial)
                {
                    name = "Runtime Day Night Skybox",
                    hideFlags = HideFlags.HideAndDontSave
                };
                RenderSettings.skybox = timeSkyboxMaterial;
                if (timeSkyboxMaterial.HasProperty("_Exposure"))
                    baseSkyboxExposure = timeSkyboxMaterial.GetFloat("_Exposure");
                if (timeSkyboxMaterial.HasProperty("_SkyTint"))
                    baseSkyboxTint = timeSkyboxMaterial.GetColor("_SkyTint");
                if (timeSkyboxMaterial.HasProperty("_GroundColor"))
                    baseSkyboxGroundColor = timeSkyboxMaterial.GetColor("_GroundColor");
                if (timeSkyboxMaterial.HasProperty("_SunSize"))
                    baseSkyboxSunSize = timeSkyboxMaterial.GetFloat("_SunSize");
                if (timeSkyboxMaterial.HasProperty("_AtmosphereThickness"))
                    baseSkyboxAtmosphereThickness = timeSkyboxMaterial.GetFloat("_AtmosphereThickness");
            }


            if (oceanMaterial != null)
            {
                baseWaveSpeed = oceanMaterial.HasProperty("_WaveSpeed")
                    ? oceanMaterial.GetFloat("_WaveSpeed") : 0.55f;
                baseWaveHeight = oceanMaterial.HasProperty("_WaveHeight")
                    ? oceanMaterial.GetFloat("_WaveHeight") : 0.028f;
            }

            BindIslandRenderers(island);
            FindFoliage(island);
            CaptureIslandBounds(island);
            CreateWeatherEffects();

            CurrentWeather = IslandWeatherType.Clear;
            currentProfile = CreateProfile(CurrentWeather);
            transitionStart = currentProfile;
            transitionTarget = currentProfile;
            rainVisualRate = currentProfile.RainRate;
            rainTransitionStart = rainVisualRate;
            rainTransitionTarget = rainVisualRate;
            lightningCountdown = UnityEngine.Random.Range(14f, 22f);
            initialized = true;
            ApplyProfile(0f);
        }

        public void SetWeather(IslandWeatherType weather, float blendSeconds = 4.5f)
        {
            if (CurrentWeather == weather)
            {
                return;
            }

            CurrentWeather = weather;
            transitionStart = currentProfile;
            transitionTarget = CreateProfile(weather);
            transitionElapsed = 0f;
            transitionDuration = Mathf.Max(0.05f, blendSeconds);
            rainTransitionStart = rainVisualRate;
            rainTransitionTarget = transitionTarget.RainRate;
            rainTransitionElapsed = 0f;
            rainTransitionDuration = rainTransitionTarget < rainVisualRate
                ? Mathf.Max(6f, blendSeconds)
                : Mathf.Max(0.05f, blendSeconds);
            if (weather == IslandWeatherType.Thunderstorm)
            {
                lightningElapsed = -1f;
                lightningCountdown = UnityEngine.Random.Range(14f, 22f);
            }
            else if (weather != IslandWeatherType.Thunderstorm)
            {
                lightningElapsed = -1f;
            }
        }

        private void Update()
        {
            if (!initialized)
            {
                return;
            }

            float deltaTime = Time.unscaledDeltaTime * simulationSpeed;
            // At 1x, one in-game hour passes every two real minutes; the HUD
            // speed buttons accelerate the daylight and weather simulation up to 3x.
            timeOfDayHours = Mathf.Repeat(timeOfDayHours + deltaTime / 120f, 24f);
            if (transitionElapsed < transitionDuration)
            {
                transitionElapsed += deltaTime;
                float blend = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(transitionElapsed / transitionDuration));
                currentProfile = Lerp(transitionStart, transitionTarget, blend);
            }
            else
            {
                currentProfile = transitionTarget;
            }

            if (rainTransitionElapsed < rainTransitionDuration)
            {
                rainTransitionElapsed += deltaTime;
                float rainBlend = Mathf.SmoothStep(0f, 1f,
                    Mathf.Clamp01(rainTransitionElapsed / rainTransitionDuration));
                rainVisualRate = Mathf.Lerp(rainTransitionStart, rainTransitionTarget, rainBlend);
            }
            else
            {
                rainVisualRate = rainTransitionTarget;
            }

            // Integrate wave phase using the current speed. Multiplying absolute _Time by
            // a changing weather speed makes phase jump faster later in a long session.
            UpdateGusts(deltaTime);
            waterPhaseTime += deltaTime * baseWaveSpeed * currentProfile.WaveSpeed *
                              Mathf.Lerp(0.88f, 1.28f, gustStrength);
            basinFlowPhaseTime += deltaTime * currentProfile.BasinFlowMultiplier;
            // Integrate changing wind strength so rain streaks do not jump when
            // the weather or gust level changes during a long-running session.
            rainWindPhase = Mathf.Repeat(rainWindPhase + deltaTime * currentProfile.WindStrength *
                Mathf.Lerp(0.7f, 1.5f, gustStrength) * 0.045f, 1f);

            float wetnessSpeed = transitionTarget.Wetness > currentWetness ? 0.28f : 0.024f;
            currentWetness = Mathf.MoveTowards(currentWetness, transitionTarget.Wetness,
                wetnessSpeed * deltaTime);

            float lightning = UpdateLightning(deltaTime);
            ApplyProfile(lightning);
            UpdateFoliage();
        }

        private void LateUpdate()
        {
            if (!initialized)
                return;

            // Update rain after the camera controller so it follows the final
            // view pose for this frame.
            UpdateRainAndSplashes(Time.deltaTime * simulationSpeed);
            DrawWeatherParticles();
        }

        public void DrawRainOverlay()
        {
            if (!initialized || Event.current == null || Event.current.type != EventType.Repaint)
            {
                return;
            }

            float rainStrength = Mathf.Clamp01(rainVisualRate / 1420f);
            if (rainStrength <= 0.005f || Screen.width <= 0 || Screen.height <= 0)
            {
                return;
            }

            float width = Screen.width;
            float height = Screen.height;
            float resolutionScale = Mathf.Clamp(height / 720f, 0.5f, 2f);
            // Fade rain opacity over time while keeping a small stable set of streaks
            // alive near the end of the transition, rather than deleting them in a burst.
            int streakCount = Mathf.RoundToInt(Mathf.Lerp(70f, 240f, rainStrength));
            float time = Time.unscaledTime;
            float horizontalDrift = rainWindPhase * width;
            float opacity = Mathf.Lerp(0f, 0.10f, Mathf.Sqrt(rainStrength));
            Color previousColor = GUI.color;
            GUI.color = new Color(0.78f, 0.87f, 0.94f, opacity);

            for (int i = 0; i < streakCount; i++)
            {
                float xSeed = Mathf.Repeat((i + 1) * 0.618033989f, 1f);
                float ySeed = Mathf.Repeat((i + 1) * 0.754877666f, 1f);
                float sizeSeed = Mathf.Repeat((i + 1) * 0.569840296f, 1f);
                float fallSpeed = height * Mathf.Lerp(0.36f, 0.58f,
                    Mathf.Repeat((i + 1) * 0.438579021f, 1f));
                float x = Mathf.Repeat(xSeed * width + horizontalDrift, width);
                float y = Mathf.Repeat(ySeed * height + time * fallSpeed, height);
                float streakWidth = Mathf.Lerp(0.8f, 1.3f, sizeSeed) * resolutionScale;
                float streakLength = Mathf.Lerp(12f, 25f, sizeSeed) * resolutionScale;
                GUI.DrawTexture(new Rect(x, y, streakWidth, streakLength), Texture2D.whiteTexture,
                    ScaleMode.StretchToFill, true);
            }

            DrawScreenDroplets(width, height, resolutionScale, rainStrength, time, horizontalDrift);
            GUI.color = previousColor;
        }

        private void DrawScreenDroplets(float width, float height, float resolutionScale,
            float rainStrength, float time, float horizontalDrift)
        {
            if (screenDropletTexture == null)
                return;

            float stormBlend = Mathf.SmoothStep(0f, 1f,
                Mathf.InverseLerp(0.38f, 1f, rainStrength));
            int dropletCount = Mathf.RoundToInt(Mathf.Lerp(4f, 56f, stormBlend));
            Color previousColor = GUI.color;
            GUI.color = new Color(0.88f, 0.95f, 1f, Mathf.Lerp(0.10f, 0.28f, stormBlend));

            for (int i = 0; i < dropletCount; i++)
            {
                float xSeed = Mathf.Repeat((i + 1) * 0.414213562f, 1f);
                float ySeed = Mathf.Repeat((i + 1) * 0.732050808f, 1f);
                float sizeSeed = Mathf.Repeat((i + 1) * 0.569840296f, 1f);
                float widthPixels = Mathf.Lerp(3f, 13f, sizeSeed) * resolutionScale *
                                    Mathf.Lerp(0.82f, 1.3f, stormBlend);
                float heightPixels = widthPixels * Mathf.Lerp(1.2f, 2.0f, sizeSeed);
                float x = Mathf.Repeat(xSeed * width + horizontalDrift * 0.18f, width);
                float y = Mathf.Repeat(ySeed * height + time * Mathf.Lerp(2f, 18f, sizeSeed), height);
                Rect dropletRect = new Rect(x, y, widthPixels, heightPixels);

                GUIUtility.RotateAroundPivot(Mathf.Lerp(-8f, 8f, sizeSeed), dropletRect.center);
                GUI.DrawTexture(dropletRect, screenDropletTexture, ScaleMode.StretchToFill, true);
                GUIUtility.RotateAroundPivot(-Mathf.Lerp(-8f, 8f, sizeSeed), dropletRect.center);
            }

            GUI.color = previousColor;
        }

        private static Texture2D CreateScreenDropletTexture()
        {
            const int textureWidth = 32;
            const int textureHeight = 48;
            Texture2D texture = new Texture2D(textureWidth, textureHeight, TextureFormat.RGBA32,
                false, true)
            {
                name = "Runtime Screen Rain Droplet",
                hideFlags = HideFlags.HideAndDontSave,
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Clamp
            };
            Color[] pixels = new Color[textureWidth * textureHeight];
            for (int y = 0; y < textureHeight; y++)
            {
                float vertical = (y + 0.5f) / textureHeight;
                float normalizedY = (vertical - 0.5f) / 0.5f;
                float ellipseWidth = 0.46f * Mathf.Sqrt(Mathf.Max(0f, 1f - normalizedY * normalizedY));
                float centerX = 0.5f + (vertical - 0.5f) * 0.08f;
                float verticalFade = 1f - Mathf.SmoothStep(0.88f, 1f, Mathf.Abs(normalizedY));
                for (int x = 0; x < textureWidth; x++)
                {
                    float horizontal = (x + 0.5f) / textureWidth;
                    float edgeDistance = Mathf.Abs(horizontal - centerX) / Mathf.Max(0.001f, ellipseWidth);
                    float edgeFade = 1f - Mathf.SmoothStep(0.68f, 1f, edgeDistance);
                    float highlight = 1f - Mathf.SmoothStep(0.02f, 0.35f,
                        Mathf.Abs(horizontal - (centerX - ellipseWidth * 0.3f)) +
                        Mathf.Abs(vertical - 0.36f) * 0.32f);
                    float alpha = edgeFade * verticalFade * 0.58f;
                    Color pixel = new Color(
                        Mathf.Lerp(0.62f, 1f, highlight),
                        Mathf.Lerp(0.76f, 1f, highlight),
                        1f,
                        alpha);
                    pixels[y * textureWidth + x] = pixel;
                }
            }

            texture.SetPixels(pixels);
            texture.Apply(false, true);
            return texture;
        }

        private void BindIslandRenderers(Transform island)
        {
            if (island == null)
            {
                return;
            }

            Renderer[] renderers = island.GetComponentsInChildren<Renderer>(true);
            for (int i = 0; i < renderers.Length; i++)
            {
                Renderer renderer = renderers[i];
                if (renderer == null)
                {
                    continue;
                }

                Material[] materials = renderer.sharedMaterials;
                RendererBinding binding = new RendererBinding();
                for (int materialIndex = 0; materialIndex < materials.Length; materialIndex++)
                {
                    Material material = materials[materialIndex];
                    if (material == null)
                    {
                        continue;
                    }

                    binding.HasWetness |= material.HasProperty(WeatherWetnessId);
                    binding.HasCloudiness |= material.HasProperty(WeatherCloudinessId);
                    binding.HasBasinFlowTime |= material.HasProperty(BasinFlowTimeId);
                    binding.HasBasinTimeLight |= material.HasProperty(BasinTimeLightId);
                    if (material.HasProperty(BasinRippleId))
                    {
                        binding.HasBasinRipple = true;
                        binding.BasinRipple = material.GetFloat(BasinRippleId);
                    }
                }

                if (!binding.HasWetness && !binding.HasCloudiness &&
                    !binding.HasBasinFlowTime && !binding.HasBasinRipple &&
                    !binding.HasBasinTimeLight)
                {
                    continue;
                }

                binding.Renderer = renderer;
                binding.OriginalBlock = new MaterialPropertyBlock();
                binding.WeatherBlock = new MaterialPropertyBlock();
                renderer.GetPropertyBlock(binding.OriginalBlock);
                rendererBindings.Add(binding);
            }
        }

        private void FindFoliage(Transform island)
        {
            if (island == null)
            {
                return;
            }

            Transform[] transforms = island.GetComponentsInChildren<Transform>(true);
            HashSet<Renderer> colorBoundRenderers = new HashSet<Renderer>();
            int foliageIndex = 0;
            for (int i = 0; i < transforms.Length; i++)
            {
                Transform candidate = transforms[i];
                string name = candidate.name;
                bool tree = name.IndexOf("Pine_", StringComparison.OrdinalIgnoreCase) >= 0 ||
                            name.IndexOf("Broadleaf_", StringComparison.OrdinalIgnoreCase) >= 0;
                bool groundCover = name.IndexOf("Grass_", StringComparison.OrdinalIgnoreCase) >= 0 ||
                                   name.IndexOf("Fern", StringComparison.OrdinalIgnoreCase) >= 0 ||
                                   name.IndexOf("Wildflower", StringComparison.OrdinalIgnoreCase) >= 0;
                if (!tree && !groundCover)
                {
                    continue;
                }

                if (tree)
                    BindFoliageMaterialColors(candidate, colorBoundRenderers);

                foliageTargets.Add(new FoliageTarget
                {
                    Transform = candidate,
                    InitialRotation = candidate.localRotation,
                    Phase = Mathf.Repeat((foliageIndex + 1) * 2.39996f, Mathf.PI * 2f),
                    // FBX vegetation is rigid-mesh based, so it needs a visible pivot
                    // angle to read as moving at the camera's gameplay distance.
                    MaxAngle = tree ? 10f : 18f
                });
                foliageIndex++;
            }

            Debug.Log($"天气植被风摆已绑定：{foliageTargets.Count} 个对象（树木、草丛、蕨类和花）。");
            Debug.Log($"阴天天气树木色彩绑定：{foliageMaterialBindings.Count} 个材质槽。");
        }

        private void BindFoliageMaterialColors(Transform treeRoot, HashSet<Renderer> alreadyBound)
        {
            Renderer[] renderers = treeRoot.GetComponentsInChildren<Renderer>(true);
            for (int rendererIndex = 0; rendererIndex < renderers.Length; rendererIndex++)
            {
                Renderer renderer = renderers[rendererIndex];
                if (renderer == null || !alreadyBound.Add(renderer))
                    continue;

                Material[] materials = renderer.sharedMaterials;
                for (int materialIndex = 0; materialIndex < materials.Length; materialIndex++)
                {
                    Material material = materials[materialIndex];
                    if (material == null)
                        continue;

                    int colorPropertyId = material.HasProperty(BaseColorId) ? BaseColorId :
                        material.HasProperty(LegacyColorId) ? LegacyColorId : 0;
                    if (colorPropertyId == 0)
                        continue;

                    FoliageMaterialBinding binding = new FoliageMaterialBinding
                    {
                        Renderer = renderer,
                        MaterialIndex = materialIndex,
                        ColorPropertyId = colorPropertyId,
                        BaseColor = material.GetColor(colorPropertyId),
                        OriginalBlock = new MaterialPropertyBlock(),
                        WeatherBlock = new MaterialPropertyBlock()
                    };
                    renderer.GetPropertyBlock(binding.OriginalBlock, materialIndex);
                    foliageMaterialBindings.Add(binding);
                }
            }
        }

        private void UpdateFoliage()
        {
            if (foliageTargets.Count == 0)
            {
                return;
            }

            float wind = currentProfile.WindStrength * Mathf.Lerp(0.7f, 1.5f, gustStrength);
            // Integrate wind rate instead of scaling absolute elapsed time by the
            // changing weather value. This keeps tree sway phase continuous when
            // the weather blend changes wind speed.
            foliageWindPhase += Time.unscaledDeltaTime * (0.65f + wind * 0.85f);
            float time = foliageWindPhase;
            for (int i = 0; i < foliageTargets.Count; i++)
            {
                FoliageTarget target = foliageTargets[i];
                if (target.Transform == null)
                {
                    continue;
                }

                float phase = time + target.Phase;
                float primary = Mathf.Sin(phase) * wind * target.MaxAngle;
                float crossWind = Mathf.Sin(phase * 0.63f + 1.4f) * wind * target.MaxAngle * 0.32f;
                target.Transform.localRotation = target.InitialRotation * Quaternion.Euler(primary, 0f, crossWind);
            }
        }

        private float UpdateLightning(float deltaTime)
        {
            if (CurrentWeather != IslandWeatherType.Thunderstorm)
            {
                lightningElapsed = -1f;
                return 0f;
            }

            if (lightningElapsed < 0f)
            {
                lightningCountdown -= deltaTime;
                if (lightningCountdown <= 0f)
                {
                    lightningElapsed = 0f;
                    lightningCountdown = UnityEngine.Random.Range(18f, 28f);
                }
                return 0f;
            }

            lightningElapsed += deltaTime;
            float softFlash = Mathf.Clamp01(1f - Mathf.Abs(lightningElapsed - 0.09f) / 0.22f);
            if (lightningElapsed > 0.32f)
            {
                lightningElapsed = -1f;
            }
            return softFlash;
        }

        private void ApplyProfile(float lightning)
        {
            bool overcastSunIsStable = CurrentWeather == IslandWeatherType.Overcast;
            float daylight = EvaluateClockCurve(timeOfDayHours, DaylightBlendKeys);
            float sunlightCurve = EvaluateClockCurve(timeOfDayHours, ClearSkySunlightKeys);
            float ambientCurve = EvaluateClockCurve(timeOfDayHours, ClearSkyAmbientKeys);
            float sunPitch = overcastSunIsStable
                ? 45f
                : EvaluateClockCurve(timeOfDayHours, SunPitchCurveKeys);
            Color daytimeSunColor = baseSunColor * currentProfile.SunTint;
            Color nightSunTint = new Color(
                currentProfile.SunTint.r * 0.68f,
                currentProfile.SunTint.g * 0.76f,
                currentProfile.SunTint.b * 0.92f, 1f);
            Color nightSunColor = baseSunColor * nightSunTint;
            float levelSurfaceSunlight = overcastSunIsStable
                ? currentProfile.SunIntensity
                : Mathf.Max(MinimumSunlightFloor, currentProfile.SunIntensity * sunlightCurve);

            if (sun != null)
            {
                // Keep the sun above the horizon even at night. Compensating for
                // its pitch makes the normalized light landing on the island
                // follow the table instead of becoming dimmer at a low angle.
                sun.transform.rotation = Quaternion.Euler(sunPitch, baseSunAzimuth, 0f);
                float pitchContribution = Mathf.Max(0.70f,
                    Mathf.Sin(sunPitch * Mathf.Deg2Rad));
                sun.intensity = baseSunIntensity * levelSurfaceSunlight / pitchContribution *
                                (1f + lightning * 0.55f);
                sun.color = overcastSunIsStable
                    ? daytimeSunColor
                    : Color.Lerp(nightSunColor, daytimeSunColor, daylight);
            }

            float flashMultiplier = 1f + lightning * 0.75f;
            // Ambient light follows its own curve so nights stay visible while
            // remaining clearly darker than midday.
            float ambientLevel = currentProfile.AmbientIntensity * ambientCurve;
            ambientLevel = overcastSunIsStable
                ? Mathf.Max(MinimumOvercastAmbientFloor, ambientLevel)
                : Mathf.Max(MinimumAmbientFloor, ambientLevel);
            RenderSettings.ambientIntensity = baseAmbientIntensity * ambientLevel * flashMultiplier;
            Color nightAmbientTint = new Color(
                currentProfile.AmbientTint.r * 0.72f,
                currentProfile.AmbientTint.g * 0.80f,
                currentProfile.AmbientTint.b * 0.92f, 1f);
            Color effectiveAmbientTint = Color.Lerp(nightAmbientTint,
                currentProfile.AmbientTint, daylight);
            Color effectiveSunTint = overcastSunIsStable
                ? currentProfile.SunTint
                : Color.Lerp(nightSunTint, currentProfile.SunTint, daylight);
            Color basinTimeTint = Color.Lerp(effectiveAmbientTint, effectiveSunTint, 0.5f);
            float basinTimeBrightness = Mathf.Lerp(ambientLevel, levelSurfaceSunlight, 0.65f);
            Color basinTimeLight = basinTimeTint * (basinTimeBrightness * flashMultiplier);
            RenderSettings.ambientLight = baseAmbientLight * effectiveAmbientTint *
                                          flashMultiplier;
            RenderSettings.ambientSkyColor = baseAmbientSky * effectiveAmbientTint * flashMultiplier;
            RenderSettings.ambientEquatorColor = baseAmbientEquator * effectiveAmbientTint * flashMultiplier;
            RenderSettings.ambientGroundColor = baseAmbientGround * effectiveAmbientTint * flashMultiplier;

            if (timeSkyboxMaterial != null)
            {
                // Script/asset reloads disable this component and restore the
                // original skybox. Reattach the runtime copy when weather resumes.
                RenderSettings.skybox = timeSkyboxMaterial;
                if (timeSkyboxMaterial.HasProperty("_Exposure"))
                    timeSkyboxMaterial.SetFloat("_Exposure", baseSkyboxExposure);
                if (timeSkyboxMaterial.HasProperty("_SkyTint"))
                    timeSkyboxMaterial.SetColor("_SkyTint", Color.Lerp(
                        new Color(baseSkyboxTint.r * 0.98f, baseSkyboxTint.g, baseSkyboxTint.b * 1.04f,
                            baseSkyboxTint.a), baseSkyboxTint, daylight));
                if (timeSkyboxMaterial.HasProperty("_GroundColor"))
                    timeSkyboxMaterial.SetColor("_GroundColor", baseSkyboxGroundColor);
                if (timeSkyboxMaterial.HasProperty("_SunSize"))
                    timeSkyboxMaterial.SetFloat("_SunSize", baseSkyboxSunSize * daylight);
                if (timeSkyboxMaterial.HasProperty("_AtmosphereThickness"))
                    timeSkyboxMaterial.SetFloat("_AtmosphereThickness", baseSkyboxAtmosphereThickness);
            }
            if (sun != null)
                RenderSettings.sun = sun;

            bool activeWeatherFog = currentProfile.FogAmount > 0.005f;
            RenderSettings.fog = baseFogEnabled || activeWeatherFog;
            Color weatherFogColor = Color.Lerp(baseFogColor, currentProfile.FogColor,
                currentProfile.FogAmount);
            Color overcastFogFloor = Color.Lerp(baseFogColor, new Color(0.43f, 0.51f, 0.59f), 0.20f);
            Color nightFogColorFloor = new Color(
                Mathf.Max(weatherFogColor.r, overcastFogFloor.r),
                Mathf.Max(weatherFogColor.g, overcastFogFloor.g),
                Mathf.Max(weatherFogColor.b, overcastFogFloor.b), 1f);
            RenderSettings.fogColor = Color.Lerp(nightFogColorFloor, weatherFogColor, daylight);
            if (activeWeatherFog)
            {
                RenderSettings.fogMode = FogMode.Linear;
                RenderSettings.fogStartDistance = Mathf.Lerp(baseFogStart, currentProfile.FogStart,
                    currentProfile.FogAmount);
                RenderSettings.fogEndDistance = Mathf.Lerp(baseFogEnd, currentProfile.FogEnd,
                    currentProfile.FogAmount);
            }
            else
            {
                RenderSettings.fogMode = baseFogMode;
                RenderSettings.fogDensity = baseFogDensity;
                RenderSettings.fogStartDistance = baseFogStart;
                RenderSettings.fogEndDistance = baseFogEnd;
            }

            if (oceanMaterial != null)
            {
                if (oceanMaterial.HasProperty(WaveTimeId))
                    oceanMaterial.SetFloat(WaveTimeId, (float)waterPhaseTime);
                if (oceanMaterial.HasProperty("_WaveHeight"))
                    oceanMaterial.SetFloat("_WaveHeight", baseWaveHeight * currentProfile.WaveHeight);
                if (oceanMaterial.HasProperty(WeatherCloudinessId))
                    oceanMaterial.SetFloat(WeatherCloudinessId, currentProfile.Cloudiness);
            }

            for (int i = 0; i < rendererBindings.Count; i++)
            {
                RendererBinding binding = rendererBindings[i];
                if (binding.Renderer == null)
                {
                    continue;
                }

                binding.Renderer.GetPropertyBlock(binding.WeatherBlock);
                if (binding.HasWetness)
                    binding.WeatherBlock.SetFloat(WeatherWetnessId, currentWetness);
                // Keep terrain colors authored. Cloudiness is applied to water;
                // tree leaf colors receive a separate, controlled tint below.
                if (binding.HasCloudiness)
                    binding.WeatherBlock.SetFloat(WeatherCloudinessId, 0f);
                if (binding.HasBasinFlowTime)
                    binding.WeatherBlock.SetFloat(BasinFlowTimeId, (float)basinFlowPhaseTime);
                if (binding.HasBasinRipple)
                    binding.WeatherBlock.SetFloat(BasinRippleId,
                        binding.BasinRipple * currentProfile.BasinRippleMultiplier);
                if (binding.HasBasinTimeLight)
                    binding.WeatherBlock.SetColor(BasinTimeLightId, basinTimeLight);
                binding.Renderer.SetPropertyBlock(binding.WeatherBlock);
            }

            ApplyFoliageCloudTint();
        }

        private void ApplyFoliageCloudTint()
        {
            float cloudiness = Mathf.Clamp01(currentProfile.Cloudiness);
            if ((cloudiness <= 0.001f && lastFoliageCloudiness <= 0.001f) ||
                (cloudiness > 0.001f && Mathf.Abs(cloudiness - lastFoliageCloudiness) < 0.02f))
                return;

            Color multiplier = Color.Lerp(Color.white,
                new Color(0.56f, 0.72f, 0.50f, 1f), cloudiness);
            for (int i = 0; i < foliageMaterialBindings.Count; i++)
            {
                FoliageMaterialBinding binding = foliageMaterialBindings[i];
                if (binding.Renderer == null)
                    continue;

                if (cloudiness <= 0.001f)
                {
                    binding.Renderer.SetPropertyBlock(binding.OriginalBlock, binding.MaterialIndex);
                    continue;
                }

                binding.Renderer.GetPropertyBlock(binding.WeatherBlock, binding.MaterialIndex);
                Color color = binding.BaseColor;
                color.r *= multiplier.r;
                color.g *= multiplier.g;
                color.b *= multiplier.b;
                binding.WeatherBlock.SetColor(binding.ColorPropertyId, color);
                binding.Renderer.SetPropertyBlock(binding.WeatherBlock, binding.MaterialIndex);
            }

            lastFoliageCloudiness = cloudiness;
        }

        private static float EvaluateClockCurve(float hour, float[] values)
        {
            float clampedHour = Mathf.Clamp(hour, 0f, 24f);
            for (int i = 0; i < ClockHours.Length - 1; i++)
            {
                if (clampedHour > ClockHours[i + 1])
                    continue;

                float segmentLength = ClockHours[i + 1] - ClockHours[i];
                float segmentTime = segmentLength > 0f
                    ? (clampedHour - ClockHours[i]) / segmentLength
                    : 0f;
                return Mathf.Lerp(values[i], values[i + 1], Mathf.SmoothStep(0f, 1f, segmentTime));
            }

            return values[values.Length - 1];
        }

        private WeatherProfile CreateProfile(IslandWeatherType weather)
        {
            WeatherProfile profile = new WeatherProfile
            {
                SunIntensity = 1f,
                AmbientIntensity = 1f,
                WaveSpeed = 1f,
                WaveHeight = 1f,
                RainRate = 0f,
                // Keep even the calm preset above zero so vegetation never appears frozen.
                WindStrength = 0.24f,
                Wetness = 0f,
                Cloudiness = 0f,
                FogAmount = 0f,
                FogStart = 40f,
                FogEnd = 180f,
                BasinFlowMultiplier = 1f,
                BasinRippleMultiplier = 1f,
                SunTint = NeutralTint,
                AmbientTint = NeutralTint,
                FogColor = baseFogColor
            };

            switch (weather)
            {
                case IslandWeatherType.Overcast:
                    profile.SunIntensity = 0.44f;
                    profile.AmbientIntensity = 0.50f;
                    profile.WindStrength = 0.30f;
                    profile.Cloudiness = 0.82f;
                    profile.FogAmount = 0.05f;
                    profile.FogStart = 48f;
                    profile.FogEnd = 210f;
                    profile.SunTint = NeutralTint;
                    profile.AmbientTint = NeutralTint;
                    profile.FogColor = new Color(0.43f, 0.51f, 0.59f, 1f);
                    break;
                case IslandWeatherType.Rain:
                    profile.SunIntensity = 0.88f;
                    profile.AmbientIntensity = 0.96f;
                    profile.WaveSpeed = 1.45f;
                    profile.WaveHeight = 1.4f;
                    profile.RainRate = 820f;
                    profile.WindStrength = 0.52f;
                    profile.Wetness = 0.38f;
                    profile.Cloudiness = 0.62f;
                    profile.FogAmount = 0.12f;
                    profile.FogStart = 28f;
                    profile.FogEnd = 135f;
                    profile.BasinFlowMultiplier = 1.2f;
                    profile.BasinRippleMultiplier = 1.5f;
                    profile.SunTint = new Color(0.87f, 0.91f, 0.96f, 1f);
                    profile.AmbientTint = new Color(0.92f, 0.96f, 1f, 1f);
                    profile.FogColor = new Color(0.39f, 0.51f, 0.58f, 1f);
                    break;
                case IslandWeatherType.Wind:
                    // Keep wind visually sunny; only wind and water respond to this preset.
                    profile.SunIntensity = 1f;
                    profile.AmbientIntensity = 1f;
                    profile.WaveSpeed = 2.0f;
                    profile.WaveHeight = 1.75f;
                    profile.WindStrength = 0.92f;
                    profile.Cloudiness = 0.28f;
                    profile.FogAmount = 0.05f;
                    profile.FogStart = 48f;
                    profile.FogEnd = 210f;
                    // Wind raises surface ripples, but should not accelerate a spring-fed stream.
                    profile.BasinFlowMultiplier = 1f;
                    profile.BasinRippleMultiplier = 2.1f;
                    profile.SunTint = NeutralTint;
                    profile.AmbientTint = NeutralTint;
                    profile.FogColor = new Color(0.50f, 0.59f, 0.64f, 1f);
                    break;
                case IslandWeatherType.Thunderstorm:
                    profile.SunIntensity = 0.62f;
                    profile.AmbientIntensity = 0.82f;
                    profile.WaveSpeed = 2.25f;
                    profile.WaveHeight = 2.15f;
                    profile.RainRate = 1420f;
                    profile.WindStrength = 0.86f;
                    profile.Wetness = 0.52f;
                    profile.Cloudiness = 0.90f;
                    profile.FogAmount = 0.22f;
                    profile.FogStart = 22f;
                    profile.FogEnd = 110f;
                    profile.BasinFlowMultiplier = 1.35f;
                    profile.BasinRippleMultiplier = 2.4f;
                    profile.SunTint = new Color(0.76f, 0.83f, 0.93f, 1f);
                    profile.AmbientTint = new Color(0.84f, 0.90f, 0.98f, 1f);
                    profile.FogColor = new Color(0.29f, 0.39f, 0.50f, 1f);
                    break;
            }

            return profile;
        }

        private static WeatherProfile Lerp(WeatherProfile from, WeatherProfile to, float blend)
        {
            return new WeatherProfile
            {
                SunIntensity = Mathf.Lerp(from.SunIntensity, to.SunIntensity, blend),
                AmbientIntensity = Mathf.Lerp(from.AmbientIntensity, to.AmbientIntensity, blend),
                WaveSpeed = Mathf.Lerp(from.WaveSpeed, to.WaveSpeed, blend),
                WaveHeight = Mathf.Lerp(from.WaveHeight, to.WaveHeight, blend),
                RainRate = Mathf.Lerp(from.RainRate, to.RainRate, blend),
                WindStrength = Mathf.Lerp(from.WindStrength, to.WindStrength, blend),
                Wetness = Mathf.Lerp(from.Wetness, to.Wetness, blend),
                Cloudiness = Mathf.Lerp(from.Cloudiness, to.Cloudiness, blend),
                FogAmount = Mathf.Lerp(from.FogAmount, to.FogAmount, blend),
                FogStart = Mathf.Lerp(from.FogStart, to.FogStart, blend),
                FogEnd = Mathf.Lerp(from.FogEnd, to.FogEnd, blend),
                BasinFlowMultiplier = Mathf.Lerp(from.BasinFlowMultiplier, to.BasinFlowMultiplier, blend),
                BasinRippleMultiplier = Mathf.Lerp(from.BasinRippleMultiplier, to.BasinRippleMultiplier, blend),
                SunTint = Color.Lerp(from.SunTint, to.SunTint, blend),
                AmbientTint = Color.Lerp(from.AmbientTint, to.AmbientTint, blend),
                FogColor = Color.Lerp(from.FogColor, to.FogColor, blend)
            };
        }

        private static string GetWeatherName(IslandWeatherType weather)
        {
            switch (weather)
            {
                case IslandWeatherType.Overcast: return "阴天";
                case IslandWeatherType.Rain: return "雨天";
                case IslandWeatherType.Wind: return "大风";
                case IslandWeatherType.Thunderstorm: return "雷雨";
                default: return "晴天";
            }
        }

        private void OnDisable()
        {
            RestoreEnvironment();
            if (weatherEffectsRoot != null)
                weatherEffectsRoot.SetActive(false);
        }

        private void OnEnable()
        {
            if (initialized && weatherEffectsRoot != null)
                weatherEffectsRoot.SetActive(true);
        }

        private void OnDestroy()
        {
            RestoreEnvironment();
            if (weatherEffectsRoot != null)
            {
                Destroy(weatherEffectsRoot);
                weatherEffectsRoot = null;
            }
            if (timeSkyboxMaterial != null)
            {
                Destroy(timeSkyboxMaterial);
                timeSkyboxMaterial = null;
            }
            if (weatherParticleMaterial != null)
            {
                Destroy(weatherParticleMaterial);
                weatherParticleMaterial = null;
            }
            if (splashParticleMaterial != null)
            {
                Destroy(splashParticleMaterial);
                splashParticleMaterial = null;
            }
            if (weatherParticleQuad != null)
            {
                Destroy(weatherParticleQuad);
                weatherParticleQuad = null;
            }
            if (screenDropletTexture != null)
            {
                Destroy(screenDropletTexture);
                screenDropletTexture = null;
            }
        }

        private void CaptureIslandBounds(Transform island)
        {
            if (island == null)
                return;

            Renderer[] renderers = island.GetComponentsInChildren<Renderer>(true);
            for (int i = 0; i < renderers.Length; i++)
            {
                if (renderers[i] == null)
                    continue;
                if (!hasIslandBounds)
                {
                    islandBounds = renderers[i].bounds;
                    hasIslandBounds = true;
                }
                else
                {
                    islandBounds.Encapsulate(renderers[i].bounds);
                }
            }
        }

        private void CreateWeatherEffects()
        {
            weatherEffectsRoot = new GameObject("Runtime Weather Effects");
            weatherEffectsRoot.transform.SetParent(transform, false);
            screenDropletTexture = CreateScreenDropletTexture();

            Shader particleShader = Shader.Find("LastLandfall/Weather Particle");
            if (particleShader == null)
                particleShader = Shader.Find("Universal Render Pipeline/Unlit");
            if (particleShader == null)
            {
                Debug.LogWarning("天气粒子没有可用的 Unlit Shader。", this);
                return;
            }

            weatherParticleMaterial = new Material(particleShader)
            {
                name = "Runtime Rain Particle Material",
                hideFlags = HideFlags.HideAndDontSave,
                enableInstancing = true
            };
            weatherParticleMaterial.SetColor("_TintColor", new Color(0.78f, 0.88f, 0.96f, 0.7f));
            splashParticleMaterial = new Material(particleShader)
            {
                name = "Runtime Rain Splash Material",
                hideFlags = HideFlags.HideAndDontSave,
                enableInstancing = true
            };
            splashParticleMaterial.SetColor("_TintColor", new Color(0.9f, 0.97f, 1f, 0.78f));
            weatherParticleQuad = CreateWeatherParticleQuad();
        }

        private void UpdateGusts(float deltaTime)
        {
            gustClock += deltaTime * (0.07f + currentProfile.WindStrength * 0.19f);
            float gustNoise = Mathf.PerlinNoise(gustClock, 0.371f);
            gustStrength = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.28f, 0.76f, gustNoise));
        }

        private bool TryGetViewBoundsAtHeight(float height, out Bounds bounds)
        {
            bounds = default;
            if (weatherCamera == null)
                return false;

            float minX = float.PositiveInfinity;
            float maxX = float.NegativeInfinity;
            float minZ = float.PositiveInfinity;
            float maxZ = float.NegativeInfinity;
            for (int i = 0; i < WeatherViewportCorners.Length; i++)
            {
                Ray ray = weatherCamera.ViewportPointToRay(WeatherViewportCorners[i]);
                if (Mathf.Abs(ray.direction.y) < 0.001f)
                    return false;

                float distance = (height - ray.origin.y) / ray.direction.y;
                if (distance < 0f)
                    return false;

                Vector3 point = ray.origin + ray.direction * distance;
                minX = Mathf.Min(minX, point.x);
                maxX = Mathf.Max(maxX, point.x);
                minZ = Mathf.Min(minZ, point.z);
                maxZ = Mathf.Max(maxZ, point.z);
            }

            bounds = new Bounds(
                new Vector3((minX + maxX) * 0.5f, height, (minZ + maxZ) * 0.5f),
                new Vector3(maxX - minX, 0f, maxZ - minZ));
            return true;
        }

        private void UpdateRainAndSplashes(float deltaTime)
        {
            if (weatherCamera == null || weatherParticleMaterial == null || weatherParticleQuad == null)
                return;

            float viewHeight = weatherCamera.orthographic ? weatherCamera.orthographicSize * 2f : 44f;
            float viewWidth = weatherCamera.orthographic ? viewHeight * weatherCamera.aspect : 58f;
            float spawnWidth = Mathf.Clamp(viewWidth * 1.45f, 36f, 120f);
            float spawnDepth = Mathf.Clamp(viewHeight * 1.45f, 36f, 120f);
            Vector3 cameraPosition = weatherCamera.transform.position;
            float surfaceHeight = hasIslandBounds ? islandBounds.min.y : 0f;
            float visibleSurfaceTop = hasIslandBounds ? islandBounds.max.y : 0f;
            Vector3 spawnCenter = cameraPosition;
            if (TryGetViewBoundsAtHeight(visibleSurfaceTop, out Bounds rainViewBounds))
            {
                spawnCenter = rainViewBounds.center;
                spawnWidth = Mathf.Max(spawnWidth, rainViewBounds.size.x * 1.25f + 8f);
                spawnDepth = Mathf.Max(spawnDepth, rainViewBounds.size.z * 1.25f + 8f);
            }
            float spawnHeight = Mathf.Max(cameraPosition.y + 10f, visibleSurfaceTop + 24f);
            float wind = currentProfile.WindStrength * Mathf.Lerp(0.65f, 1.65f, gustStrength);
            Vector3 dropVelocity = new Vector3(WindDirection.x * wind * 8f, -24f,
                WindDirection.y * wind * 8f);

            for (int i = rainDrops.Count - 1; i >= 0; i--)
            {
                RainDrop drop = rainDrops[i];
                drop.Velocity.x = WindDirection.x * wind * 8f;
                drop.Velocity.z = WindDirection.y * wind * 8f;
                Vector3 previousPosition = drop.Position;
                drop.Position += drop.Velocity * deltaTime;
                drop.RemainingLife -= deltaTime;
                Vector3 segment = drop.Position - previousPosition;
                // Most drops are far above the island; delaying physics tests
                // until the surface band keeps heavy rain inexpensive.
                bool nearSurface = previousPosition.y <= visibleSurfaceTop + 8f;
                if (nearSurface && segment.sqrMagnitude > 0.0001f &&
                    Physics.Raycast(previousPosition, segment.normalized, out RaycastHit hit,
                        segment.magnitude + 0.03f, Physics.AllLayers, QueryTriggerInteraction.Ignore))
                {
                    SpawnSplash(hit.point, hit.normal);
                    RemoveRainDropAt(i);
                    continue;
                }

                if (drop.RemainingLife <= 0f || drop.Position.y < surfaceHeight - 6f)
                {
                    RemoveRainDropAt(i);
                    continue;
                }
                rainDrops[i] = drop;
            }

            for (int i = splashDrops.Count - 1; i >= 0; i--)
            {
                SplashDrop splash = splashDrops[i];
                splash.RemainingLife -= deltaTime;
                splash.Velocity += Vector3.down * 3.2f * deltaTime;
                splash.Position += splash.Velocity * deltaTime;
                if (splash.RemainingLife <= 0f)
                {
                    splashDrops[i] = splashDrops[splashDrops.Count - 1];
                    splashDrops.RemoveAt(splashDrops.Count - 1);
                    continue;
                }
                splashDrops[i] = splash;
            }

            float rainRate = rainVisualRate * 0.42f;
            if (rainRate <= 0.1f)
            {
                rainSpawnRemainder = 0f;
                return;
            }

            rainSpawnRemainder += rainRate * deltaTime;
            int spawnCount = Mathf.Min(Mathf.FloorToInt(rainSpawnRemainder), 80);
            rainSpawnRemainder -= spawnCount;
            float lifetime = Mathf.Clamp((spawnHeight - surfaceHeight) / 24f + 0.35f, 0.8f, 7f);
            for (int i = 0; i < spawnCount && rainDrops.Count < 2600; i++)
            {
                Vector3 position = new Vector3(
                    spawnCenter.x + UnityEngine.Random.Range(-spawnWidth * 0.5f, spawnWidth * 0.5f),
                    spawnHeight,
                    spawnCenter.z + UnityEngine.Random.Range(-spawnDepth * 0.5f, spawnDepth * 0.5f));
                rainDrops.Add(new RainDrop
                {
                    Position = position,
                    Velocity = dropVelocity,
                    RemainingLife = lifetime,
                    Size = UnityEngine.Random.Range(0.22f, 0.38f)
                });
            }
        }

        private void SpawnSplash(Vector3 point, Vector3 surfaceNormal)
        {
            if (splashParticleMaterial == null || splashDrops.Count > 1300)
                return;

            Vector3 normal = surfaceNormal.sqrMagnitude > 0.01f ? surfaceNormal.normalized : Vector3.up;
            for (int i = 0; i < 3 && splashDrops.Count < 1400; i++)
            {
                Vector2 lateral = UnityEngine.Random.insideUnitCircle * 0.45f;
                splashDrops.Add(new SplashDrop
                {
                    Position = point + normal * 0.015f,
                    Velocity = normal * UnityEngine.Random.Range(0.45f, 1.15f) +
                               new Vector3(lateral.x, 0f, lateral.y),
                    RemainingLife = UnityEngine.Random.Range(0.16f, 0.30f),
                    Size = UnityEngine.Random.Range(0.035f, 0.075f)
                });
            }
        }

        private void RemoveRainDropAt(int index)
        {
            rainDrops[index] = rainDrops[rainDrops.Count - 1];
            rainDrops.RemoveAt(rainDrops.Count - 1);
        }

        private void DrawWeatherParticles()
        {
            if (weatherCamera == null || weatherParticleQuad == null)
                return;

            Quaternion facingCamera = weatherCamera.transform.rotation * Quaternion.Euler(0f, 0f, 12f);
            int matrixCount = 0;
            for (int i = 0; i < rainDrops.Count; i++)
            {
                RainDrop drop = rainDrops[i];
                rainMatrices[matrixCount++] = Matrix4x4.TRS(drop.Position, facingCamera,
                    new Vector3(drop.Size * 0.055f, drop.Size, 1f));
                if (matrixCount == rainMatrices.Length)
                {
                    DrawParticleBatch(weatherParticleQuad, weatherParticleMaterial, rainMatrices, matrixCount);
                    matrixCount = 0;
                }
            }
            if (matrixCount > 0)
                DrawParticleBatch(weatherParticleQuad, weatherParticleMaterial, rainMatrices, matrixCount);

            if (splashParticleMaterial == null)
                return;

            matrixCount = 0;
            for (int i = 0; i < splashDrops.Count; i++)
            {
                SplashDrop splash = splashDrops[i];
                float lifeBlend = Mathf.Clamp01(splash.RemainingLife / 0.3f);
                float size = splash.Size * (0.65f + (1f - lifeBlend) * 0.7f);
                splashMatrices[matrixCount++] = Matrix4x4.TRS(splash.Position,
                    weatherCamera.transform.rotation, new Vector3(size, size, 1f));
                if (matrixCount == splashMatrices.Length)
                {
                    DrawParticleBatch(weatherParticleQuad, splashParticleMaterial, splashMatrices, matrixCount);
                    matrixCount = 0;
                }
            }
            if (matrixCount > 0)
                DrawParticleBatch(weatherParticleQuad, splashParticleMaterial, splashMatrices, matrixCount);
        }

        private void DrawParticleBatch(Mesh mesh, Material material, Matrix4x4[] matrices, int count)
        {
            Graphics.DrawMeshInstanced(mesh, 0, material, matrices, count, null,
                ShadowCastingMode.Off, false, 0, weatherCamera, LightProbeUsage.Off, null);
        }

        private static Mesh CreateWeatherParticleQuad()
        {
            Mesh mesh = new Mesh { name = "Weather Particle Quad" };
            mesh.vertices = new[]
            {
                new Vector3(-0.5f, -0.5f, 0f),
                new Vector3(0.5f, -0.5f, 0f),
                new Vector3(0.5f, 0.5f, 0f),
                new Vector3(-0.5f, 0.5f, 0f)
            };
            mesh.triangles = new[] { 0, 1, 2, 0, 2, 3 };
            mesh.uv = new[]
            {
                new Vector2(0f, 0f), new Vector2(1f, 0f),
                new Vector2(1f, 1f), new Vector2(0f, 1f)
            };
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        private void RestoreEnvironment()
        {
            if (!initialized)
            {
                return;
            }

            if (sun != null)
            {
                sun.intensity = baseSunIntensity;
                sun.color = baseSunColor;
            }
            RenderSettings.ambientIntensity = baseAmbientIntensity;
            RenderSettings.ambientMode = baseAmbientMode;
            RenderSettings.ambientLight = baseAmbientLight;
            RenderSettings.ambientSkyColor = baseAmbientSky;
            RenderSettings.ambientEquatorColor = baseAmbientEquator;
            RenderSettings.ambientGroundColor = baseAmbientGround;
            RenderSettings.fog = baseFogEnabled;
            RenderSettings.fogMode = baseFogMode;
            RenderSettings.fogColor = baseFogColor;
            RenderSettings.fogDensity = baseFogDensity;
            RenderSettings.fogStartDistance = baseFogStart;
            RenderSettings.fogEndDistance = baseFogEnd;
            RenderSettings.sun = baseRenderSettingsSun;
            RenderSettings.skybox = baseSkyboxMaterial;

            if (sun != null)
                sun.transform.rotation = baseSunRotation;

            if (oceanMaterial != null)
            {
                if (oceanMaterial.HasProperty("_WaveSpeed")) oceanMaterial.SetFloat("_WaveSpeed", baseWaveSpeed);
                if (oceanMaterial.HasProperty("_WaveHeight")) oceanMaterial.SetFloat("_WaveHeight", baseWaveHeight);
                if (oceanMaterial.HasProperty(WeatherCloudinessId)) oceanMaterial.SetFloat(WeatherCloudinessId, 0f);
            }

            for (int i = 0; i < rendererBindings.Count; i++)
            {
                RendererBinding binding = rendererBindings[i];
                if (binding.Renderer != null)
                    binding.Renderer.SetPropertyBlock(binding.OriginalBlock);
            }

            for (int i = 0; i < foliageMaterialBindings.Count; i++)
            {
                FoliageMaterialBinding binding = foliageMaterialBindings[i];
                if (binding.Renderer != null)
                    binding.Renderer.SetPropertyBlock(binding.OriginalBlock, binding.MaterialIndex);
            }
            lastFoliageCloudiness = -1f;

        }
    }
}
