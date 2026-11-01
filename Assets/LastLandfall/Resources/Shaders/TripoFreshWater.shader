Shader "LastLandfall/Tripo Fresh Water"
{
    Properties
    {
        _WaterRegion ("Water region reference", 2D) = "black" {}
        _Tint ("Deep water tint", Color) = (0.07, 0.34, 0.38, 1)
        _ShallowColor ("Shallow water tint", Color) = (0.22, 0.58, 0.56, 1)
        _FoamColor ("Foam & rapids tint", Color) = (0.90, 0.96, 0.97, 1)
        _WaterOpacity ("Water translucency / opacity", Range(0.1, 1.0)) = 0.35
        _FlowSpeed ("Stream flow speed", Float) = 1.35
        _NormalStrength ("Wave normal relief", Range(0, 2)) = 0.85
        _CreekLevelOffset ("Creek water level offset (m)", Range(-3.0, 3.0)) = 0.0
        _PondLevelOffset ("Pond water level offset (m)", Range(-3.0, 3.0)) = 0.0
        _CreekWidthScale ("Creek width scale", Range(0.4, 2.5)) = 1.0
    }
    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
            "Queue" = "Transparent-10"
        }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Cull Off
            ZWrite Off
            Offset -2, -2
            Blend SrcAlpha OneMinusSrcAlpha

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fog

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_WaterRegion);
            SAMPLER(sampler_WaterRegion);

            CBUFFER_START(UnityPerMaterial)
                half4 _Tint;
                half4 _ShallowColor;
                half4 _FoamColor;
                half _WaterOpacity;
                float _FlowSpeed;
                half _NormalStrength;
                float _CreekLevelOffset;
                float _PondLevelOffset;
                float _CreekWidthScale;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float2 uv : TEXCOORD0;
                half4 color : COLOR;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float2 uv : TEXCOORD1;
                half3 normalWS : TEXCOORD2;
                half4 color : TEXCOORD3;
                half fogFactor : TEXCOORD4;
            };

            float WaterHash(float2 p)
            {
                float3 p3 = frac(float3(p.xyx) * 0.1031);
                p3 += dot(p3, p3.yzx + 33.33);
                return frac((p3.x + p3.y) * p3.z);
            }

            float WaterNoise(float2 p)
            {
                float2 i = floor(p);
                float2 f = frac(p);
                f = f * f * (3.0 - 2.0 * f);
                float a = WaterHash(i);
                float b = WaterHash(i + float2(1.0, 0.0));
                float c = WaterHash(i + float2(0.0, 1.0));
                float d = WaterHash(i + float2(1.0, 1.0));
                return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
            }

            float WaterFbm(float2 p)
            {
                float v = 0.0;
                v += 0.55 * WaterNoise(p);
                p = float2(p.x * 1.6 - p.y * 1.2, p.x * 1.2 + p.y * 1.6);
                v += 0.30 * WaterNoise(p);
                p = float2(p.x * 1.7 + p.y * 1.1, -p.x * 1.1 + p.y * 1.7);
                v += 0.15 * WaterNoise(p);
                return v;
            }

            half3 PerturbWaterNormal(float3 positionWS, half3 geomNormal, float waveHeight)
            {
                float3 sigmaX = ddx(positionWS);
                float3 sigmaY = ddy(positionWS);
                float3 r1 = cross(sigmaY, geomNormal);
                float3 r2 = cross(geomNormal, sigmaX);
                float det = dot(sigmaX, r1);
                float3 grad = (ddx(waveHeight) * r1 + ddy(waveHeight) * r2);
                grad *= sign(det) / max(abs(det), 1e-7);
                return normalize(geomNormal - grad);
            }

            Varyings Vert(Attributes input)
            {
                Varyings output = (Varyings)0;
                float3 posWS = TransformObjectToWorld(input.positionOS.xyz);
                float t = _Time.y;
                float edgeMask = saturate(sin(saturate(input.uv.x) * 3.14159265));
                float vertexWave = sin(input.uv.y * 1.8 - t * 2.6 + input.uv.x * 4.5) * 0.012 +
                                   cos(posWS.x * 2.3 + posWS.z * 1.9 - t * 1.8) * 0.008;
                posWS.y += vertexWave * edgeMask * saturate(input.color.a);

                output.positionWS = posWS;
                output.positionCS = TransformWorldToHClip(posWS);
                output.uv = input.uv;
                output.normalWS = half3(0, 1, 0);
                output.color = input.color;
                output.fogFactor = ComputeFogFactor(output.positionCS.z);
                return output;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                // Vertex color channels baked by BuildSplineWaterSurface:
                // r = normalized water depth (0 at bank -> 1 in deep channel/pond)
                // g = normalized flow speed (1 in steep creek -> 0.18 in calm pond)
                // b = rapids & cascade turbulence intensity
                // a = bank shoreline soft alpha feathering
                float depthFactor = saturate(input.color.r);
                float flowRate = lerp(0.18, 1.15, saturate(input.color.g));
                float rapidsMask = saturate(input.color.b);

                float u = saturate(input.uv.x);
                float v = input.uv.y;
                float bankDist = min(u, 1.0 - u) * 2.0; // 0 at banks, 1 at channel center
                float centerProfile = smoothstep(0.0, 0.65, bankDist);
                float shoreAlpha = smoothstep(0.0, 0.08, bankDist) * smoothstep(0.0, 0.04, saturate(input.color.a));

                float t = _Time.y * max(0.2, _FlowSpeed);
                // Parabolic cross-channel flow profile: water moves faster mid-stream than along banks
                float advectedV = v - t * flowRate * (0.68 + 0.32 * centerProfile);

                // Dual-layer directional stream ripples + isotropic pond ripples
                float2 streamUV1 = float2(u * 4.2, advectedV * 0.72);
                float2 streamUV2 = float2(u * 7.6 + 3.7, v * 1.25 - t * flowRate * 1.18);
                float2 worldUV = input.positionWS.xz * 0.95;

                float rippleStream = WaterFbm(streamUV1) * 0.58 + WaterFbm(streamUV2) * 0.42;
                float ripplePond = WaterFbm(worldUV + float2(t * 0.16, -t * 0.14)) * 0.52 +
                                   WaterFbm(worldUV * 2.15 + float2(-t * 0.22, t * 0.19)) * 0.48;
                float waveHeight = lerp(ripplePond, rippleStream, saturate(input.color.g * 1.15));

                // Fine capillary wavelets along current streaks
                float streakWave = sin(advectedV * 4.8 + sin(u * 9.5 + rippleStream * 4.0) * 1.6) * 0.5 + 0.5;
                waveHeight = waveHeight * 0.78 + streakWave * 0.22;

                half3 geomNormal = normalize(input.normalWS);
                float reliefScale = (0.045 + 0.035 * rapidsMask) * max(0.1h, _NormalStrength);
                half3 normalWS = PerturbWaterNormal(input.positionWS, geomNormal, waveHeight * reliefScale);

                // Beer-Lambert depth absorption between shallow aqua and deep mountain-basin emerald teal
                half3 shallowTint = _ShallowColor.rgb;
                half3 deepTint = _Tint.rgb;
                float opticalDepth = saturate(depthFactor * 0.82 + bankDist * 0.28);
                half3 waterAlbedo = lerp(shallowTint, deepTint, smoothstep(0.08, 0.88, opticalDepth));

                // Sunlit shallow-water caustics visible over the carved cobble riverbed
                float causticA = WaterNoise(worldUV * 3.2 + normalWS.xz * 1.8 + float2(t * 0.45, -t * 0.32));
                float causticB = WaterNoise(worldUV * 3.6 - normalWS.xz * 1.6 + float2(-t * 0.38, t * 0.41));
                float caustics = smoothstep(0.52, 0.88, causticA * causticB * 2.1);
                float shallowVisibility = (1.0 - smoothstep(0.25, 0.85, opticalDepth)) * smoothstep(0.02, 0.25, bankDist);
                waterAlbedo += half3(0.16, 0.24, 0.21) * caustics * shallowVisibility;

                // Shoreline foam + mountain rapids whitewater streaks
                float foamNoise = WaterFbm(float2(u * 9.0, advectedV * 1.45) + worldUV * 0.6);
                float bankFoamZone = (1.0 - smoothstep(0.02, 0.24 + 0.08 * rapidsMask, bankDist)) *
                                     smoothstep(0.01, 0.06, bankDist);
                float bankFoam = smoothstep(0.46, 0.74, foamNoise + bankFoamZone * 0.42) * bankFoamZone * 0.65;

                float cascadeStreak = smoothstep(0.58, 0.86,
                    WaterFbm(float2(u * 12.5, advectedV * 1.9)) * 0.65 + streakWave * 0.35);
                float rapidsFoam = cascadeStreak * rapidsMask * (0.45 + 0.55 * centerProfile);
                float totalFoam = saturate(bankFoam + rapidsFoam * 0.78);

                half3 viewDirWS = GetWorldSpaceNormalizeViewDir(input.positionWS);
                float ndotv = saturate(dot(normalWS, viewDirWS));
                float fresnel = pow(1.0 - ndotv, 4.0);

                float4 shadowCoord = TransformWorldToShadowCoord(input.positionWS);
                Light mainLight = GetMainLight(shadowCoord);
                half3 lightColor = mainLight.color * lerp(0.55h, 1.0h, mainLight.shadowAttenuation);
                half3 ambient = SampleSH(normalWS);

                // Sky reflection and subsurface scattering in flowing ripples
                half3 skyReflection = lerp(half3(0.32, 0.48, 0.54), half3(0.64, 0.78, 0.84), fresnel) *
                                      (0.45 + 0.55 * saturate(ambient + lightColor * 0.4));
                half3 subsurface = half3(0.06, 0.22, 0.20) * saturate(waveHeight - 0.45) * (0.4 + 0.6 * rapidsMask);

                half ndotl = saturate(dot(normalWS, mainLight.direction)) * 0.65 + 0.35;
                half3 color = (waterAlbedo * (ambient * 0.65 + lightColor * ndotl * 0.75)) + subsurface;
                color = lerp(color, skyReflection, fresnel * 0.48);

                // Dual-lobe sun specular: broad water sheen + crisp sun sparkle
                float3 halfDir = normalize(mainLight.direction + viewDirWS);
                float ndoth = saturate(dot(normalWS, halfDir));
                float specBroad = pow(ndoth, 42.0) * 0.18;
                float specSparkle = pow(ndoth, 180.0) * 0.65;
                color += lightColor * (specBroad + specSparkle) * (1.0 - totalFoam * 0.7);

                // Layer organic whitewater foam on top
                half3 litFoam = _FoamColor.rgb * (ambient * 0.45 + lightColor * 0.68);
                color = lerp(color, litFoam, totalFoam);

                // Depth-based translucency matching the crystal-clear first version:
                // clear over shallow river cobbles (~22% base opacity) and gently deeper in the pond (~44% base opacity)
                float baseOpacity = max(0.05, _WaterOpacity);
                float depthOpacity = lerp(baseOpacity * 0.58, baseOpacity * 1.15, smoothstep(0.0, 0.78, opticalDepth));
                float alpha = saturate(shoreAlpha * depthOpacity +
                                       totalFoam * 0.36 + fresnel * 0.20) * smoothstep(0.0, 0.10, shoreAlpha);

                color = MixFog(color, input.fogFactor);
                return half4(saturate(color), saturate(alpha));
            }
            ENDHLSL
        }
    }
}
