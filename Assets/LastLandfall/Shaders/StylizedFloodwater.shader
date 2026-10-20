Shader "LastLandfall/Stylized Floodwater"
{
    Properties
    {
        _DeepColor ("Deep ocean", Color) = (0.018, 0.085, 0.23, 1)
        _MidColor ("Continental shelf", Color) = (0.03, 0.20, 0.37, 1)
        _ShallowColor ("Shallow water", Color) = (0.10, 0.43, 0.42, 1)
        _FoamColor ("Shore foam", Color) = (0.92, 0.97, 0.94, 1)
        _ShoreFoamWidth ("Shore foam width", Range(1, 12)) = 9.5
        _ShoreFoamStrength ("Shore foam strength", Range(0, 1)) = 1.0
        _WaveSpeed ("Wave speed", Range(0, 2)) = 0.9
        _WaveTime ("Accumulated wave phase", Float) = 0
        _WaveHeight ("Wave height", Range(0, 1.4)) = 0.4
        _WeatherCloudiness ("Weather overcast", Range(0, 1)) = 0
        _CoastDistanceTex ("Gate25 coast distance", 2D) = "white" {}
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
            "Queue" = "Transparent"
        }

        Pass
        {
            Name "UniversalForward"
            Tags { "LightMode" = "UniversalForward" }

            Blend SrcAlpha OneMinusSrcAlpha
            Cull Back
            ZWrite Off
            ZTest LEqual

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_CoastDistanceTex);
            SAMPLER(sampler_CoastDistanceTex);

            CBUFFER_START(UnityPerMaterial)
                half4 _DeepColor;
                half4 _MidColor;
                half4 _ShallowColor;
                half4 _FoamColor;
                float _ShoreFoamWidth;
                float _ShoreFoamStrength;
                float _WaveSpeed;
                float _WaveTime;
                float _WaveHeight;
                float _WeatherCloudiness;
                float4 _CoastWorldMin;
                float4 _CoastWorldSize;
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
                half3 normalWS : TEXCOORD1;
                half wave : TEXCOORD2;
                float3 coastPositionWS : TEXCOORD3;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                float2 p = input.positionOS.xz;
                float time = _WaveTime;
                float3 basePositionWS = TransformObjectToWorld(input.positionOS.xyz);
                float2 coastUV = (basePositionWS.xz - _CoastWorldMin.xy) /
                                 max(_CoastWorldSize.xy, float2(0.001, 0.001));
                float encodedCoastDistance = 1.0;
                if (all(coastUV >= 0.0) && all(coastUV <= 1.0))
                {
                    encodedCoastDistance = SAMPLE_TEXTURE2D_LOD(
                        _CoastDistanceTex, sampler_CoastDistanceTex, coastUV, 0).r;
                }
                float coastDistance = (encodedCoastDistance * 2.0 - 1.0) * _CoastDistanceRange;
                float effectiveWaveHeight = _WaveHeight * smoothstep(0.0, 6.0, coastDistance);
                float3 displaced = input.positionOS.xyz;
                float slopeX = 0.0;
                float slopeZ = 0.0;
                float wave = 0.0;

                // Four crossing Gerstner waves move the actual water mesh, creating a rolling surface.
                float2 directionA = normalize(float2(0.86, 0.51));
                float amplitudeA = effectiveWaveHeight * 0.42;
                float frequencyA = 6.2831853 / 22.0;
                float phaseA = dot(p, directionA) * frequencyA + time * 0.76;
                float sineA = sin(phaseA);
                float cosineA = cos(phaseA);
                displaced.xz += directionA * amplitudeA * 0.72 * cosineA;
                displaced.y += amplitudeA * sineA;
                slopeX += amplitudeA * frequencyA * directionA.x * cosineA;
                slopeZ += amplitudeA * frequencyA * directionA.y * cosineA;
                wave += amplitudeA * sineA;

                float2 directionB = normalize(float2(-0.47, 0.88));
                float amplitudeB = effectiveWaveHeight * 0.28;
                float frequencyB = 6.2831853 / 14.0;
                float phaseB = dot(p, directionB) * frequencyB - time * 0.59;
                float sineB = sin(phaseB);
                float cosineB = cos(phaseB);
                displaced.xz += directionB * amplitudeB * 0.66 * cosineB;
                displaced.y += amplitudeB * sineB;
                slopeX += amplitudeB * frequencyB * directionB.x * cosineB;
                slopeZ += amplitudeB * frequencyB * directionB.y * cosineB;
                wave += amplitudeB * sineB;

                float2 directionC = normalize(float2(0.32, 0.95));
                float amplitudeC = effectiveWaveHeight * 0.18;
                float frequencyC = 6.2831853 / 9.0;
                float phaseC = dot(p, directionC) * frequencyC + time * 0.91;
                float sineC = sin(phaseC);
                float cosineC = cos(phaseC);
                displaced.xz += directionC * amplitudeC * 0.52 * cosineC;
                displaced.y += amplitudeC * sineC;
                slopeX += amplitudeC * frequencyC * directionC.x * cosineC;
                slopeZ += amplitudeC * frequencyC * directionC.y * cosineC;
                wave += amplitudeC * sineC;

                float2 directionD = normalize(float2(0.91, -0.42));
                float amplitudeD = effectiveWaveHeight * 0.10;
                float frequencyD = 6.2831853 / 6.0;
                float phaseD = dot(p, directionD) * frequencyD - time * 0.82;
                float sineD = sin(phaseD);
                float cosineD = cos(phaseD);
                displaced.xz += directionD * amplitudeD * 0.42 * cosineD;
                displaced.y += amplitudeD * sineD;
                slopeX += amplitudeD * frequencyD * directionD.x * cosineD;
                slopeZ += amplitudeD * frequencyD * directionD.y * cosineD;
                wave += amplitudeD * sineD;

                float3 normalOS = normalize(float3(-slopeX * 14.0, 1.0, -slopeZ * 14.0));
                output.positionWS = TransformObjectToWorld(displaced);
                output.positionCS = TransformWorldToHClip(output.positionWS);
                output.normalWS = TransformObjectToWorldNormal(normalOS);
                output.wave = wave / max(_WaveHeight, 0.001);
                output.coastPositionWS = TransformObjectToWorld(input.positionOS.xyz);
                return output;
            }

            float FloodHash21(float2 coord)
            {
                coord = frac(coord * float2(123.34, 456.21));
                coord += dot(coord, coord + 45.32);
                return frac(coord.x * coord.y);
            }

            float FloodNoise21(float2 coord)
            {
                float2 cell = floor(coord);
                float2 blend = frac(coord);
                blend = blend * blend * (3.0 - 2.0 * blend);
                float bottom = lerp(FloodHash21(cell), FloodHash21(cell + float2(1.0, 0.0)), blend.x);
                float top = lerp(FloodHash21(cell + float2(0.0, 1.0)), FloodHash21(cell + float2(1.0, 1.0)), blend.x);
                return lerp(bottom, top, blend.y);
            }

            float FloodGradientNoise21(float2 coord)
            {
                float2 cell = floor(coord);
                float2 local = frac(coord);
                float2 blend = local * local * (3.0 - 2.0 * local);

                float angle00 = FloodHash21(cell) * 6.2831853;
                float angle10 = FloodHash21(cell + float2(1.0, 0.0)) * 6.2831853;
                float angle01 = FloodHash21(cell + float2(0.0, 1.0)) * 6.2831853;
                float angle11 = FloodHash21(cell + float2(1.0, 1.0)) * 6.2831853;
                float noise00 = dot(float2(cos(angle00), sin(angle00)), local);
                float noise10 = dot(float2(cos(angle10), sin(angle10)), local - float2(1.0, 0.0));
                float noise01 = dot(float2(cos(angle01), sin(angle01)), local - float2(0.0, 1.0));
                float noise11 = dot(float2(cos(angle11), sin(angle11)), local - float2(1.0, 1.0));

                float bottom = lerp(noise00, noise10, blend.x);
                float top = lerp(noise01, noise11, blend.x);
                return saturate(0.5 + lerp(bottom, top, blend.y) * 0.86);
            }

            float SampleCoastDistance(float2 worldPosition)
            {
                float2 uv = (worldPosition - _CoastWorldMin.xy) / max(_CoastWorldSize.xy, float2(0.001, 0.001));
                if (any(uv < 0.0) || any(uv > 1.0)) return _CoastDistanceRange;
                float encoded = SAMPLE_TEXTURE2D(_CoastDistanceTex, sampler_CoastDistanceTex, uv).r;
                return (encoded * 2.0 - 1.0) * _CoastDistanceRange;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                float2 worldPosition = input.positionWS.xz;
                float2 coastPosition = input.coastPositionWS.xz;
                float time = _WaveTime;
                float coastDistance = SampleCoastDistance(coastPosition);
                float2 dominantFlow = normalize(float2(0.82, 0.57));

                // The Gate25 terrain mask defines a broad shelf and a clear, shallow turquoise edge.
                float shelf = 1.0 - smoothstep(9.0, 42.0, coastDistance);
                float shallows = 1.0 - smoothstep(0.0, 15.0, coastDistance);
                half3 waterColor = lerp(_DeepColor.rgb, _MidColor.rgb, shelf * 0.78);
                waterColor = lerp(waterColor, _ShallowColor.rgb, shallows * 0.94);
                half cloudiness = saturate(_WeatherCloudiness);

                // Fine-scale surface motion adds broken reflections without a tiled foam texture.
                half3 normalWS = normalize(input.normalWS);
                float ripplePhaseA = dot(worldPosition, float2(0.82, 0.57)) * 0.64 + time * 1.35;
                float ripplePhaseB = dot(worldPosition, float2(-0.48, 0.88)) * 0.91 - time * 1.12;
                float ripplePhaseC = dot(worldPosition, float2(0.27, 0.96)) * 1.19 + time * 1.48;
                float rippleSlopeX = cos(ripplePhaseA) * 0.64 * 0.82 * 0.42 +
                                     cos(ripplePhaseB) * 0.91 * -0.48 * 0.20 +
                                     cos(ripplePhaseC) * 1.19 * 0.27 * 0.12;
                float rippleSlopeZ = cos(ripplePhaseA) * 0.64 * 0.57 * 0.42 +
                                     cos(ripplePhaseB) * 0.91 * 0.88 * 0.20 +
                                     cos(ripplePhaseC) * 1.19 * 0.96 * 0.12;
                float2 fineDirection = normalize(float2(-0.46, 0.89));
                float ripplePhaseD = dot(worldPosition, fineDirection) * 2.05 - time * 1.83;
                float ripplePhaseE = dot(worldPosition, float2(0.31, 0.95)) * 2.72 + time * 2.21;
                rippleSlopeX += cos(ripplePhaseD) * 2.05 * fineDirection.x * 0.11 +
                                cos(ripplePhaseE) * 2.72 * 0.31 * 0.065;
                rippleSlopeZ += cos(ripplePhaseD) * 2.05 * fineDirection.y * 0.11 +
                                cos(ripplePhaseE) * 2.72 * 0.95 * 0.065;
                normalWS = normalize(normalWS + half3(-rippleSlopeX * 0.15, 0, -rippleSlopeZ * 0.15));

                float crest = smoothstep(0.24, 0.82, input.wave);
                float slope = saturate(length(normalWS.xz) * 1.25);
                half swellLight = saturate(input.wave * 0.5 + 0.5);
                waterColor = lerp(waterColor * 0.64, waterColor * 1.28, swellLight);
                waterColor += input.wave * half3(0.032, 0.078, 0.096);
                waterColor += crest * half3(0.050, 0.12, 0.15);
                waterColor += slope * half3(0.032, 0.078, 0.096);

                half3 viewDirection = normalize(GetWorldSpaceViewDir(input.positionWS));
                Light mainLight = GetMainLight();
                half3 halfDirection = normalize(viewDirection + mainLight.direction);
                half reflection = saturate(dot(normalWS, halfDirection));
                half broadGlint = pow(reflection, 18.0) * 0.38;
                half sharpGlint = pow(reflection, 56.0) * 0.82;
                waterColor += (broadGlint + sharpGlint) * mainLight.color.rgb * half3(0.68, 0.84, 0.92);
                half grazingAngle = 1.0h - saturate(dot(normalWS, viewDirection));
                // Avoid sampling a low-resolution environment cubemap here: its broad
                // texel patches read as a checker/mosaic on the water when viewed close.
                // Keep a smooth, analytic Fresnel tint and let the wave normals and sun
                // highlights provide the visible surface motion instead.
                half reflectionWeight = pow(grazingAngle, 2.2h) * 0.12h;
                waterColor = lerp(waterColor, half3(0.12h, 0.22h, 0.30h), reflectionWeight);
                waterColor += pow(1.0 - saturate(dot(normalWS, viewDirection)), 1.8) * half3(0.015, 0.035, 0.050);

                // Open water needs broad moving tonal shifts and broken wind glints,
                // otherwise the distant ocean reads as one flat painted surface.
                float offshore = smoothstep(3.0, 22.0, coastDistance);
                float broadDrift = FloodNoise21(worldPosition * float2(0.082, 0.068) +
                                                dominantFlow * time * 0.018);
                float fineDrift = FloodNoise21(worldPosition * float2(0.34, 0.29) -
                                               dominantFlow * time * 0.075);
                float swellTone = saturate(0.24 + broadDrift * 0.46 +
                                           (input.wave * 0.5 + 0.5) * 0.30);
                half3 openWaterColor = lerp(_DeepColor.rgb * 0.72, _MidColor.rgb * 0.82, swellTone);
                waterColor = lerp(waterColor, openWaterColor, offshore * 0.68);

                float windRidge = sin(dot(worldPosition, dominantFlow) * 0.38 + time * 0.95 +
                                      (broadDrift - 0.5) * 1.6);
                float brokenGlint = smoothstep(0.70, 0.96, windRidge * 0.5 + 0.5) *
                                    smoothstep(0.34, 0.62, fineDrift) *
                                    smoothstep(0.05, 0.58, input.wave + (fineDrift - 0.5) * 0.24);
                float swellGlint = smoothstep(0.58, 0.90,
                                              input.wave + (fineDrift - 0.5) * 0.38) *
                                   smoothstep(0.48, 0.76, fineDrift);
                waterColor += offshore * brokenGlint * half3(0.045, 0.13, 0.17);
                waterColor += offshore * swellGlint * half3(0.035, 0.095, 0.12);

                // Keep the shoreline foam broad enough to read at normal gameplay zoom,
                // with only a gently irregular outer edge so it stays smooth instead of pixelated.
                float foamDrift = FloodGradientNoise21(coastPosition * float2(0.34, 0.43) +
                                                       float2(time * 0.045, -time * 0.038));
                float foamEdgeOffset = (foamDrift - 0.5) * 1.4;
                float foamBand = 1.0 - smoothstep(0.25 + foamEdgeOffset,
                                                  max(1.0, _ShoreFoamWidth) + foamEdgeOffset,
                                                  coastDistance);
                float innerRim = 1.0 - smoothstep(0.10, 0.95,
                                                  coastDistance + (foamDrift - 0.5) * 0.28);
                float foamCoverage = lerp(0.90, 0.99, saturate(crest * 0.75 + 0.25));
                float shoreFoam = max(innerRim * 0.96, foamBand * foamCoverage) *
                                  saturate(_ShoreFoamStrength);
                float crestNoise = FloodNoise21(worldPosition * 0.24 + float2(time * 0.04, -time * 0.05));
                float brokenCrest = smoothstep(0.55, 0.84, input.wave + (crestNoise - 0.5) * 0.28);
                waterColor = lerp(waterColor, _FoamColor.rgb, brokenCrest * 0.10);
                float nearShelf = 1.0 - smoothstep(1.2, 12.0, coastDistance);
                float crestFoam = crest * nearShelf * 0.045;
                float visibleFoam = saturate(max(shoreFoam, crestFoam));

                // Overcast reduces sun glitter as well as the base water colour.
                half luminance = dot(waterColor, half3(0.299, 0.587, 0.114));
                half3 overcastWater = lerp(waterColor, luminance.xxx, 0.56) *
                                      half3(0.67, 0.75, 0.84);
                overcastWater = lerp(overcastWater, half3(0.07, 0.12, 0.18), 0.18);
                waterColor = lerp(waterColor, overcastWater, cloudiness);

                // Preserve a readable surf line after weather grading so foggy water
                // does not swallow the coastline foam.
                half3 visibleFoamColor = lerp(_FoamColor.rgb,
                                              half3(0.56, 0.66, 0.72), cloudiness * 0.35);
                waterColor = lerp(waterColor, visibleFoamColor, visibleFoam);

                return half4(waterColor, 1.0);
            }
            ENDHLSL
        }
    }
}
