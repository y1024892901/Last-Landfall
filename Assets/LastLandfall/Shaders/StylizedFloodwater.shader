Shader "LastLandfall/Stylized Floodwater"
{
    Properties
    {
        _DeepColor ("Deep ocean", Color) = (0.018, 0.09, 0.20, 1)
        _MidColor ("Mid-depth water", Color) = (0.035, 0.25, 0.36, 1)
        _ShallowColor ("Shallow water", Color) = (0.15, 0.47, 0.44, 1)
        _FoamColor ("Shore foam", Color) = (0.90, 0.93, 0.81, 1)
        _WaveSpeed ("Current speed", Range(0, 2)) = 0.55
        _WaveHeight ("Wave height", Range(0, 0.12)) = 0.028
        _FoamPixelRadius ("Shore foam width", Range(1, 12)) = 6
        _FoamDepthRange ("Shore foam depth", Range(0.1, 5)) = 2.1
        _MapRotation ("Island rotation", Float) = 0
        _MapScale ("Island scale", Float) = 1
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
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _DeepColor;
                half4 _MidColor;
                half4 _ShallowColor;
                half4 _FoamColor;
                float _WaveSpeed;
                float _WaveHeight;
                float _FoamPixelRadius;
                float _FoamDepthRange;
                float _MapRotation;
                float _MapScale;
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
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                float2 p = input.positionOS.xz;
                float time = _Time.y * _WaveSpeed;

                float phaseA = dot(p, float2(0.105, 0.074)) + time;
                float phaseB = dot(p, float2(-0.052, 0.139)) - time * 0.72;
                float phaseC = dot(p, float2(0.19, -0.115)) + time * 0.48;
                float waveA = sin(phaseA) * 0.58;
                float waveB = sin(phaseB) * 0.30;
                float waveC = sin(phaseC) * 0.12;
                float wave = waveA + waveB + waveC;

                float derivativeX = cos(phaseA) * 0.105 * 0.58 +
                                    cos(phaseB) * -0.052 * 0.30 +
                                    cos(phaseC) * 0.19 * 0.12;
                float derivativeZ = cos(phaseA) * 0.074 * 0.58 +
                                    cos(phaseB) * 0.139 * 0.30 +
                                    cos(phaseC) * -0.115 * 0.12;

                float3 displaced = input.positionOS.xyz;
                displaced.y += wave * _WaveHeight;
                float3 normalOS = normalize(float3(-derivativeX * _WaveHeight, 1.0, -derivativeZ * _WaveHeight));

                output.positionWS = TransformObjectToWorld(displaced);
                output.positionCS = TransformWorldToHClip(output.positionWS);
                output.normalWS = TransformObjectToWorldNormal(normalOS);
                output.wave = wave;
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

            float GetShoreFoam(float2 screenUV, float waterEyeDepth)
            {
                float foam = 0.0;
                float2 pixelSize = (1.0 / _ScaledScreenParams.xy) * _FoamPixelRadius;

                [unroll]
                for (int sampleIndex = 0; sampleIndex < 8; sampleIndex++)
                {
                    float angle = 6.2831853 * (sampleIndex / 8.0);
                    float2 sampleUV = screenUV + float2(cos(angle), sin(angle)) * pixelSize;
                    sampleUV = saturate(sampleUV);

                    float rawDepth = SampleSceneDepth(sampleUV);
                    float sceneEyeDepth = LinearEyeDepth(rawDepth, _ZBufferParams);
                    float depthDifference = waterEyeDepth - sceneEyeDepth;
                    float isLandInFront = step(0.01, depthDifference);
                    float closeToShore = 1.0 - smoothstep(0.12, _FoamDepthRange, depthDifference);
                    foam = max(foam, isLandInFront * closeToShore);
                }

                return foam;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                float2 worldPosition = input.positionWS.xz;
                float2 islandPosition = worldPosition / max(_MapScale, 0.001);
                float angleRadians = radians(_MapRotation);
                float sineRotation = sin(angleRadians);
                float cosineRotation = cos(angleRadians);
                islandPosition = float2(
                    cosineRotation * islandPosition.x - sineRotation * islandPosition.y,
                    sineRotation * islandPosition.x + cosineRotation * islandPosition.y);

                float2 normalizedIslandPosition = islandPosition / float2(19.0, 16.0);
                float islandRadius = length(normalizedIslandPosition);
                float coastAngle = atan2(normalizedIslandPosition.y, normalizedIslandPosition.x);
                float coveAngle = atan2(sin(coastAngle - radians(220.0)), cos(coastAngle - radians(220.0)));
                float coveInset = 0.08 * exp(-0.5 * pow(coveAngle / radians(27.0), 2.0));
                float coastShape = 1.34
                    + 0.035 * sin(coastAngle * 3.0 + 0.35)
                    + 0.020 * sin(coastAngle * 7.0 - 0.8)
                    + 0.013 * cos(coastAngle * 11.0 + 1.2)
                    - coveInset;

                // Distance from the island lets the water transition from bright shallows to deep floodwater.
                float shoreDistance = (islandRadius - coastShape) * 17.0;
                float shallowBlend = 1.0 - smoothstep(0.15, 8.0, shoreDistance);
                float midBlend = 1.0 - smoothstep(7.0, 33.0, shoreDistance);
                half3 waterColor = lerp(_DeepColor.rgb, _MidColor.rgb, midBlend);
                waterColor = lerp(waterColor, _ShallowColor.rgb, shallowBlend);

                float time = _Time.y * _WaveSpeed;
                float2 broadFlowUV = worldPosition * 0.055;
                float warpX = FloodNoise21(broadFlowUV + float2(time * 0.028, 1.7));
                float warpY = FloodNoise21(broadFlowUV + float2(-3.1, -time * 0.024));
                float2 warpedFlowUV = worldPosition * 0.11 + (float2(warpX, warpY) - 0.5) * 1.25;
                warpedFlowUV += float2(time * 0.018, -time * 0.013);
                float broadCurrent = FloodNoise21(warpedFlowUV);
                float fineCurrent = FloodNoise21(worldPosition * 0.31 + float2(time * 0.035, time * 0.022));
                float currentPattern = (broadCurrent - 0.5) * 0.82 + (fineCurrent - 0.5) * 0.22;
                waterColor += currentPattern * half3(0.085, 0.105, 0.085);

                float brokenGlint = sin(dot(worldPosition, float2(0.38, 0.16)) + time * 0.34 +
                    (broadCurrent - 0.5) * 4.0 + (fineCurrent - 0.5) * 1.7);
                float glimmer = pow(saturate(0.5 + brokenGlint * 0.5), 18.0);
                waterColor += glimmer * half3(0.032, 0.052, 0.046);

                half3 normalWS = normalize(input.normalWS);
                half3 viewDirection = normalize(GetWorldSpaceViewDir(input.positionWS));
                Light mainLight = GetMainLight();
                half3 halfDirection = normalize(viewDirection + mainLight.direction);
                half sunGlint = pow(saturate(dot(normalWS, halfDirection)), 72.0) * 0.18;
                waterColor += sunGlint * mainLight.color.rgb;

                half fresnel = pow(1.0 - saturate(dot(normalWS, viewDirection)), 3.0);
                waterColor += fresnel * half3(0.08, 0.13, 0.13);

                float2 screenUV = GetNormalizedScreenSpaceUV(input.positionCS);
                float waterEyeDepth = -TransformWorldToView(input.positionWS).z;
                float screenFoam = GetShoreFoam(screenUV, waterEyeDepth);
                float coastNoise = FloodNoise21(islandPosition * 0.72 + float2(time * 0.018, -time * 0.012));
                float foamLineDistance = abs(shoreDistance - 0.24 + (coastNoise - 0.5) * 0.62);
                float shorelineFoam = 1.0 - smoothstep(0.12, 0.82, foamLineDistance);
                float foamPatches = smoothstep(0.28, 0.62,
                    FloodNoise21(islandPosition * 1.35 + float2(time * 0.028, 0.0)));
                shorelineFoam *= foamPatches;
                float shoreFoam = max(screenFoam, shorelineFoam * 0.92);
                shoreFoam *= 0.86 + 0.14 * saturate(input.wave * 1.2 + 0.5);
                waterColor = lerp(waterColor, _FoamColor.rgb, saturate(shoreFoam));

                return half4(waterColor, 0.98);
            }
            ENDHLSL
        }
    }
}
