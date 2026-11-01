Shader "LastLandfall/Stylized Floodwater"
{
    Properties
    {
        _DeepColor ("Deep ocean", Color) = (0.024, 0.14, 0.24, 1)
        _MidColor ("Open coastal water", Color) = (0.055, 0.31, 0.39, 1)
        _ShallowColor ("Rocky shallows", Color) = (0.14, 0.52, 0.50, 1)
        _SubsurfaceColor ("Wave crest subsurface tint", Color) = (0.10, 0.54, 0.48, 1)
        _FoamColor ("Broken rock surf", Color) = (0.90, 0.95, 0.96, 1)
        _ShoreFoamWidth ("Surf reach", Range(0.4, 6)) = 2.4
        _ShoreFoamStrength ("Surf strength", Range(0, 1)) = 0.85
        _WaveSpeed ("Wave clock speed", Range(0, 2)) = 0.65
        _WaveTime ("Accumulated wave phase", Float) = 0
        _WaveHeight ("Swell height", Range(0, 1.4)) = 0.32
        _RippleStrength ("Fine ripple normals", Range(0, 0.5)) = 0.30
        _ReflectionStrength ("Broken reflections", Range(0, 1)) = 0.78
        _OceanSlopeA ("Spectral wave slopes A", 2D) = "gray" {}
        _OceanSlopeB ("Spectral wave slopes B", 2D) = "gray" {}
        _WeatherCloudiness ("Cloud cover", Range(0, 1)) = 0
        _WeatherRain ("Rain disturbance", Range(0, 1)) = 0
        _TimeOfDayLight ("Day/night light", Color) = (1, 1, 1, 1)
        _CoastDistanceTex ("Signed rock coast distance", 2D) = "white" {}
        _CoastWorldMin ("Coast field world minimum", Vector) = (0, 0, 0, 0)
        _CoastWorldSize ("Coast field world size", Vector) = (1, 1, 0, 0)
        _CoastDistanceRange ("Coast distance range", Float) = 40
    }
    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
            "Queue" = "Transparent-20"
        }
        Pass
        {
            Name "UniversalForward"
            Tags { "LightMode" = "UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            ZTest LEqual
            Cull Back

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fog

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            TEXTURE2D(_CoastDistanceTex);
            SAMPLER(sampler_CoastDistanceTex);
            TEXTURE2D(_OceanSlopeA);
            SAMPLER(sampler_OceanSlopeA);
            TEXTURE2D(_OceanSlopeB);
            SAMPLER(sampler_OceanSlopeB);

            CBUFFER_START(UnityPerMaterial)
                half4 _DeepColor, _MidColor, _ShallowColor, _SubsurfaceColor, _FoamColor, _TimeOfDayLight;
                float _ShoreFoamWidth, _ShoreFoamStrength, _WaveSpeed, _WaveTime, _WaveHeight;
                float _RippleStrength, _ReflectionStrength, _WeatherCloudiness, _WeatherRain;
                float4 _CoastWorldMin, _CoastWorldSize;
                float _CoastDistanceRange;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float2 coastPosition : TEXCOORD1;
                half fogFactor : TEXCOORD2;
                float4 screenPos : TEXCOORD3;
                float crestFactor : TEXCOORD4;
            };

            float Hash(float2 p)
            {
                float3 q = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
                q += dot(q, q.yzx + 33.33);
                return frac((q.x + q.y) * q.z);
            }

            float3 NoiseGradient(float2 p)
            {
                float2 cell = floor(p), f = frac(p);
                float2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
                float2 du = 30.0 * f * f * (f - 1.0) * (f - 1.0);
                float a = Hash(cell), b = Hash(cell + float2(1, 0));
                float c = Hash(cell + float2(0, 1)), d = Hash(cell + 1.0);
                float k = a - b - c + d;
                return float3(
                    a + (b - a) * u.x + (c - a) * u.y + k * u.x * u.y,
                    ((b - a) + k * u.y) * du.x,
                    ((c - a) + k * u.x) * du.y);
            }

            float2 Rotate(float2 p)
            {
                return float2(0.80 * p.x - 0.60 * p.y, 0.60 * p.x + 0.80 * p.y);
            }

            float Fractal(float2 p)
            {
                float value = NoiseGradient(p).x * 0.57;
                p = Rotate(p) * 2.03 + float2(11.7, 5.2);
                value += NoiseGradient(p).x * 0.29;
                p = Rotate(p) * 2.11 + float2(-7.4, 19.6);
                return value + NoiseGradient(p).x * 0.14;
            }

            float GetWaveTime()
            {
                return (_WaveTime > 0.001) ? _WaveTime : (_Time.y * max(0.25, _WaveSpeed));
            }

            float CoastDistance(float2 p)
            {
                if (_CoastWorldSize.x <= 1.5 || _CoastWorldSize.y <= 1.5)
                    return _CoastDistanceRange;
                float2 uv = (p - _CoastWorldMin.xy) / max(_CoastWorldSize.xy, 0.001);
                if (any(uv < 0.0) || any(uv > 1.0))
                    return _CoastDistanceRange;
                float value = SAMPLE_TEXTURE2D_LOD(_CoastDistanceTex, sampler_CoastDistanceTex, uv, 0).r;
                return (value * 2.0 - 1.0) * _CoastDistanceRange;
            }

            // 4-component Gerstner / Trochoidal ocean swell with crest steepening
            void GerstnerSwell(float2 p, float t, out float3 displacement, out float2 gradient, out float crest)
            {
                float2 d0 = float2(0.81, 0.59);
                float2 d1 = float2(-0.57, 0.82);
                float2 d2 = float2(0.25, -0.968);
                float2 d3 = float2(-0.912, -0.410);

                float4 freqs = float4(0.1698, 0.2768, 0.4520, 0.6905);
                float4 phases = float4(
                    dot(p, d0) * freqs.x - t * 0.52,
                    dot(p, d1) * freqs.y - t * 0.68 + 1.7,
                    dot(p, d2) * freqs.z - t * 0.89 + 3.1,
                    dot(p, d3) * freqs.w - t * 1.12 + 0.8);

                float4 amps = _WaveHeight * float4(0.42, 0.27, 0.19, 0.12);
                float4 s = sin(phases);
                float4 c = cos(phases);

                // Trochoidal crest sharpening: horizontal pinch toward wave crests
                float4 steepness = float4(0.32, 0.28, 0.22, 0.18);
                float2 horiz = d0 * (c.x * amps.x * steepness.x) +
                               d1 * (c.y * amps.y * steepness.y) +
                               d2 * (c.z * amps.z * steepness.z) +
                               d3 * (c.w * amps.w * steepness.w);

                // Asymmetric crest lift (sharper peaks, flatter troughs)
                float4 sharpS = s + 0.22 * (s * s - 0.5);
                float height = dot(sharpS, amps);

                displacement = float3(-horiz.x, height, -horiz.y);

                float4 dSharp = (1.0 + 0.44 * s) * c * amps * freqs;
                gradient = float2(
                    dot(dSharp, float4(d0.x, d1.x, d2.x, d3.x)),
                    dot(dSharp, float4(d0.y, d1.y, d2.y, d3.y)));

                crest = saturate(dot(max(0.0, s), float4(0.45, 0.28, 0.17, 0.10)));
            }

            Varyings Vert(Attributes input)
            {
                Varyings output = (Varyings)0;
                float3 world = TransformObjectToWorld(input.positionOS.xyz);
                output.coastPosition = world.xz;

                float t = GetWaveTime();
                float distance = CoastDistance(world.xz);
                float coastDamp = smoothstep(0.15, 6.5, distance);

                float3 disp;
                float2 gradient;
                float crest;
                GerstnerSwell(world.xz, t, disp, gradient, crest);

                world.xz += disp.xz * coastDamp;
                world.y += disp.y * coastDamp;

                output.positionWS = world;
                output.positionCS = TransformWorldToHClip(world);
                output.fogFactor = ComputeFogFactor(output.positionCS.z);
                output.screenPos = ComputeScreenPos(output.positionCS);
                output.crestFactor = crest * coastDamp;
                return output;
            }

            float2 RainGradient(float2 p, float time)
            {
                float2 cell = floor(p), local = frac(p);
                float seed = Hash(cell + 17.2);
                float2 center = float2(seed, Hash(cell - 5.3)) * 0.62 + 0.19;
                float2 delta = local - center;
                float distance = length(delta);
                float age = frac(time * 0.46 + seed * 7.13);
                float ring = distance - age * 0.53;
                float profile = exp(-abs(ring) * 34.0) * sin(ring * 57.0);
                float cellFade = smoothstep(0.0, 0.13, min(min(local.x, local.y), min(1.0 - local.x, 1.0 - local.y)));
                return delta / max(distance, 0.01) * profile * (1.0 - age) * cellFade;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                float2 p = input.coastPosition;
                float t = GetWaveTime();
                float sdfDistance = CoastDistance(p);
                bool hasValidSdf = (_CoastWorldSize.x > 1.5 && _CoastWorldSize.y > 1.5 && sdfDistance < _CoastDistanceRange - 0.5);

                // 1. Reconstruct true 3D underwater depth from _CameraDepthTexture (works for both Ortho and Perspective)
                float2 screenUV = input.screenPos.xy / max(1e-5, input.screenPos.w);
                float rawDepth = SampleSceneDepth(screenUV);
                #if UNITY_REVERSED_Z
                    bool isFarClip = rawDepth < 1e-4;
                #else
                    bool isFarClip = rawDepth > 0.9999;
                #endif
                float3 sceneWorldPos = ComputeWorldSpacePosition(screenUV, rawDepth, UNITY_MATRIX_I_VP);
                float verticalDepth = isFarClip ? 45.0 : max(0.0, input.positionWS.y - sceneWorldPos.y);

                // Combine 3D scene depth (for exact rock/cliff shoreline & shallow reefs) with 2D coastal SDF shelf
                float coastDist = hasValidSdf ? max(0.0, sdfDistance) : verticalDepth * 3.8;
                float effectiveDepth = hasValidSdf
                    ? lerp(verticalDepth, min(verticalDepth, coastDist * 0.32 + 0.05), 0.65)
                    : verticalDepth;

                float clouds = saturate(_WeatherCloudiness);
                float roughWeather = saturate((_WaveHeight - 0.30) / 0.55);
                float2 drift = float2(t * 0.026, -t * 0.019);
                float2 warp = float2(
                    NoiseGradient(p * 0.083 + drift).x,
                    NoiseGradient(Rotate(p) * 0.071 - drift + 19.0).x) - 0.5;
                float broadVariation = Fractal(p * 0.024 + warp * 0.42 + drift * 0.18);
                float nearVariation = NoiseGradient(p * 0.19 + warp + drift).x;

                // 2. Evaluate Gerstner swell and dual spectral normal maps
                float3 swellDisp;
                float2 swellGradient;
                float swellCrest;
                GerstnerSwell(p, t, swellDisp, swellGradient, swellCrest);
                float coastDamp = smoothstep(0.15, 6.5, coastDist);
                swellGradient *= coastDamp;

                float phaseA = dot(p, float2(0.93, 0.37)) * 2.17 + warp.x * 5.7 - t * 0.88;
                float phaseB = dot(p, float2(-0.42, 0.907)) * 3.81 + warp.y * 6.3 - t * 1.24;
                float attenuationA = rcp(1.0 + fwidth(phaseA) * 1.7);
                float attenuationB = rcp(1.0 + fwidth(phaseB) * 1.7);
                float3 fineNoise = NoiseGradient(Rotate(p) * 1.73 + warp * 2.7 + drift * 3.0);
                float2 ripples = float2(0.93, 0.37) * cos(phaseA) * attenuationA * 0.56 +
                                 float2(-0.42, 0.907) * cos(phaseB) * attenuationB * 0.33;
                ripples += fineNoise.yz * 0.22 / (1.0 + length(fwidth(p * 1.73)));

                float2 slopeA = SAMPLE_TEXTURE2D(_OceanSlopeA, sampler_OceanSlopeA,
                    p / 68.0 + warp * 0.034 + float2(t * 0.0022, -t * 0.0015)).rg * 2.0 - 1.0;
                float2 slopeB = SAMPLE_TEXTURE2D(_OceanSlopeB, sampler_OceanSlopeB,
                    Rotate(p) / 102.0 - warp * 0.027 + float2(-t * 0.0016, t * 0.0020)).rg * 2.0 - 1.0;
                slopeB = float2(0.80 * slopeB.x + 0.60 * slopeB.y, -0.60 * slopeB.x + 0.80 * slopeB.y);
                ripples = ripples * 0.32 + slopeA * 0.85 + slopeB * 0.65;

                float2 rainRipples = RainGradient(p * 0.73 + 3.2, t) +
                                     RainGradient(Rotate(p) * 1.11 - 9.7, t * 1.19) * 0.55;
                float2 gradient = swellGradient + ripples * _RippleStrength *
                                  lerp(0.92, 1.65, roughWeather) + rainRipples * _WeatherRain * 0.045;
                half3 normal = normalize(half3(-gradient.x, 1.0, -gradient.y));
                half3 view = GetWorldSpaceNormalizeViewDir(input.positionWS);
                Light light = GetMainLight();

                // 3. Beer-Lambert Water Depth Absorption (Shallow Aquamarine -> Coastal Teal -> Deep Marine Blue)
                float organicOffset = (nearVariation - 0.5) * 0.85;
                float shelfFactor = 1.0 - smoothstep(2.5, 26.0, max(0.0, coastDist + organicOffset * 2.2));
                float shallowFactor = max(
                    1.0 - smoothstep(0.15, 2.35, verticalDepth + organicOffset * 0.25),
                    (1.0 - smoothstep(0.25, 5.8, coastDist + organicOffset)) * 0.75);

                half3 water = lerp(_DeepColor.rgb, _MidColor.rgb, saturate(shelfFactor * 0.90));
                water = lerp(water, _ShallowColor.rgb, saturate(shallowFactor * 0.88));
                water *= 0.94 + broadVariation * 0.12;

                // 4. Sunlit Underwater Caustics in Translucent Shallows
                float shallowCausticMask = (1.0 - smoothstep(0.20, 2.40, verticalDepth)) *
                                           smoothstep(0.02, 0.18, verticalDepth);
                if (shallowCausticMask > 0.001)
                {
                    float2 causticUV = sceneWorldPos.xz * 1.45 + normal.xz * 0.65;
                    float cA = NoiseGradient(causticUV + float2(t * 0.34, -t * 0.26)).x;
                    float cB = NoiseGradient(Rotate(causticUV * 1.28) - float2(t * 0.29, t * 0.31)).x;
                    float causticNet = smoothstep(0.46, 0.84, cA * cB * 2.25);
                    water += _ShallowColor.rgb * (0.42 * causticNet * shallowCausticMask * (1.0 - clouds * 0.65));
                }

                // 5. Wave Crest Subsurface Scattering (SSS) + Sky Reflection + Sun Glints
                float backLit = saturate(dot(view, -light.direction) * 0.5 + 0.5);
                float waveSlopeScatter = saturate(dot(normal, float3(0, 1, 0)) < 0.98 ? length(gradient) * 1.8 : 0.0);
                float sssStrength = saturate((swellCrest * 0.75 + waveSlopeScatter * 0.45 + shallowFactor * 0.30) *
                                             (0.45 + 0.55 * backLit)) * (1.0 - clouds * 0.55);
                half3 sssColor = _SubsurfaceColor.rgb * light.color.rgb * 0.42;
                water += sssColor * sssStrength;

                half fresnel = 0.05h + 0.68h * pow(1.0h - saturate(dot(normal, view)), 3.2h);
                half3 reflected = reflect(-view, normal);
                half skyGradient = saturate(reflected.y * 0.65h + 0.35h);
                half3 clearSky = lerp(half3(0.18, 0.32, 0.40), half3(0.32, 0.48, 0.58), skyGradient);
                half3 cloudSky = half3(0.18, 0.23, 0.27);
                half3 sky = lerp(clearSky, cloudSky, clouds * 0.72);
                water = lerp(water, sky, saturate(fresnel * _ReflectionStrength * 0.78));

                // Dual-lobe sun specular: warm broad sheen + crisp spectral wave sparkles
                half3 halfDir = normalize(view + light.direction);
                half ndh = saturate(dot(normal, halfDir));
                half broadSpec = pow(ndh, 38.0h) * 0.14h;
                half gloss = lerp(210.0h, 72.0h, roughWeather);
                float sparkle = smoothstep(0.50, 0.85, fineNoise.x);
                half sharpSpec = pow(ndh, gloss) * sparkle * 0.72h;
                water += (broadSpec + sharpSpec) * light.color.rgb * _ReflectionStrength * (1.0 - clouds * 0.75);

                half skyFacing = dot(normal, normalize(half3(-0.35, 0.85, 0.40)));
                water *= 0.92h + 0.14h * skyFacing;
                half rippleFacing = saturate(0.5h + dot(gradient, float2(-0.71, 0.70)) * 1.65h);
                water *= lerp(0.82h, 1.18h, rippleFacing);

                float skyGlints = smoothstep(0.54, 0.90, 0.5 + dot(gradient, float2(0.80, 0.60)) * 2.1) *
                                  smoothstep(0.38, 0.70, slopeA.y * 0.5 + 0.5);
                water += skyGlints * half3(0.13, 0.21, 0.24) * _ReflectionStrength * (1.0 - clouds * 0.60);

                // 6. Shore-Directed Rolling Breakers + 3D Rock-Contact Surf Foam
                float foamNoise = Fractal(p * 1.25 + warp * 2.2 - float2(t * 0.08, t * 0.06));
                float bubbleCell = NoiseGradient(p * 3.8 + warp * 3.5 + float2(-t * 0.15, t * 0.12)).x;
                float lacyMask = smoothstep(0.28, 0.68, foamNoise * 0.65 + bubbleCell * 0.35);

                float alongCoast = NoiseGradient(p * 0.12 + 7.7).x;
                float surfDist = min(verticalDepth * 1.65, coastDist);
                float maxReach = max(0.6, _ShoreFoamWidth);

                // Rolling wave train advancing inward toward the shoreline (surfDist -> 0)
                float wavePhase1 = surfDist * 3.4 + t * 1.35 + alongCoast * 6.2 + foamNoise * 1.8;
                float waveTrain1 = pow(saturate(0.5 + 0.5 * sin(wavePhase1)), 4.5) *
                                   (1.0 - smoothstep(0.15, maxReach, surfDist)) *
                                   smoothstep(0.02, 0.18, surfDist);

                float wavePhase2 = surfDist * 2.1 + t * 0.92 - alongCoast * 5.1 + bubbleCell * 1.5 + 2.4;
                float waveTrain2 = pow(saturate(0.5 + 0.5 * sin(wavePhase2)), 5.0) *
                                   (1.0 - smoothstep(0.25, maxReach * 1.25, surfDist)) *
                                   smoothstep(0.05, 0.25, surfDist) * 0.65;

                // Crisp 3D rock-contact surf rim hugging every cliff and boulder at the waterline
                float rockContact = (1.0 - smoothstep(0.02, 0.28, verticalDepth)) *
                                    smoothstep(0.25, 0.64, foamNoise * 0.6 + bubbleCell * 0.4) * 0.88;
                float sdfContact = hasValidSdf
                    ? (1.0 - smoothstep(0.03, 0.32, coastDist)) * smoothstep(0.35, 0.66, foamNoise) * 0.62
                    : 0.0;

                float shoreFoam = saturate(max(max(rockContact, sdfContact), (waveTrain1 + waveTrain2) * lacyMask * 0.92)) *
                                  _ShoreFoamStrength;

                // Open-ocean whitecaps on steep swell crests
                float whitecaps = smoothstep(0.40, 0.68, length(gradient)) *
                                  smoothstep(0.46, 0.74, foamNoise) *
                                  lerp(0.12, 0.55, roughWeather) *
                                  smoothstep(3.5, 12.0, coastDist);

                float totalFoam = saturate(shoreFoam + whitecaps);

                // 7. Weather & Time-of-Day Grading + Soft Depth-Based Shoreline Feathering
                half waterLuma = dot(water, half3(0.2126, 0.7152, 0.0722));
                water = lerp(water, lerp(water, waterLuma.xxx, 0.30) * half3(0.85, 0.91, 0.97), clouds);
                half timeLight = saturate(dot(_TimeOfDayLight.rgb, half3(0.2126, 0.7152, 0.0722)));
                water *= lerp(0.68, 1.0, timeLight);

                half3 foamTint = lerp(_FoamColor.rgb, half3(0.52, 0.62, 0.66), clouds * 0.40) * lerp(0.70, 1.0, timeLight);
                water = lerp(water, foamTint, totalFoam);
                water = MixFog(water, input.fogFactor);

                // Depth-based shoreline translucency:
                // Feather out the razor-sharp 0..8cm intersection, stay translucent (42%..88%) over shallow submerged rocks,
                // and become 100% opaque in deeper coastal & open water (> 1.8m).
                float waterBodyAlpha = smoothstep(0.0, 0.07, verticalDepth) *
                                       lerp(0.42, 1.0, smoothstep(0.06, 1.85, verticalDepth));
                float finalAlpha = saturate(max(waterBodyAlpha, totalFoam * smoothstep(0.0, 0.025, verticalDepth)));

                return half4(max(water, 0.002h), finalAlpha);
            }
            ENDHLSL
        }
    }
}
