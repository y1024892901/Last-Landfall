Shader "LastLandfall/Reference Island Terrain"
{
    Properties
    {
        [MainTexture] _BaseMap ("Grass surface albedo", 2D) = "white" {}
        _TextureWeight ("Grass texture blend", Range(0, 1)) = 0.1
        [MainColor] _BaseColor ("Mineral base", Color) = (0.34, 0.32, 0.26, 1)
        _AccentColor ("Weathered mineral variation", Color) = (0.49, 0.45, 0.36, 1)
        _MineralColor ("Exposed flecks", Color) = (0.56, 0.55, 0.50, 1)
        _MacroScale ("Large deposits per world unit", Float) = 0.55
        _DetailScale ("Fractures per world unit", Float) = 6.4
        _MicroScale ("Grain per world unit", Float) = 45
        _LayerScale ("Rock beds per vertical world unit", Float) = 5.2
        _ColorVariation ("Mineral colour variation", Range(0, 1)) = 0.65
        _StrataStrength ("Rock bedding visibility", Range(0, 1)) = 0.38
        _FractureStrength ("Fracture line contrast", Range(0, 0.12)) = 0
        _NormalStrength ("Fractured surface relief", Range(0, 2)) = 0.8
        _Smoothness ("Surface smoothness", Range(0, 1)) = 0.12
        _VertexColorWeight ("Optional mesh colour tint", Range(0, 1)) = 0
        _WeatherWetness ("Weather wetness", Range(0, 1)) = 0
        _WeatherCloudiness ("Weather cloud cover", Range(0, 1)) = 0
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Opaque"
            "Queue" = "Geometry"
            "UniversalMaterialType" = "Lit"
        }
        LOD 300
        Cull Back
        ZWrite On

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

        TEXTURE2D(_BaseMap);
        SAMPLER(sampler_BaseMap);

        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            float4 _BaseMap_TexelSize;
            half _TextureWeight;
            half4 _BaseColor;
            half4 _AccentColor;
            half4 _MineralColor;
            float _MacroScale;
            float _DetailScale;
            float _MicroScale;
            float _LayerScale;
            half _ColorVariation;
            half _StrataStrength;
            half _FractureStrength;
            half _NormalStrength;
            half _Smoothness;
            half _VertexColorWeight;
            half _WeatherWetness;
            half _WeatherCloudiness;
        CBUFFER_END

        struct IslandAttributes
        {
            float4 positionOS : POSITION;
            float3 normalOS : NORMAL;
            half4 color : COLOR;
            float2 uv : TEXCOORD0;
            UNITY_VERTEX_INPUT_INSTANCE_ID
        };

        struct IslandVaryings
        {
            float4 positionCS : SV_POSITION;
            float3 positionWS : TEXCOORD0;
            half3 normalWS : TEXCOORD1;
            half4 color : TEXCOORD2;
            half fogFactor : TEXCOORD3;
            float2 uv : TEXCOORD4;
            UNITY_VERTEX_INPUT_INSTANCE_ID
            UNITY_VERTEX_OUTPUT_STEREO
        };

        IslandVaryings IslandVertex(IslandAttributes input)
        {
            IslandVaryings output = (IslandVaryings)0;
            UNITY_SETUP_INSTANCE_ID(input);
            UNITY_TRANSFER_INSTANCE_ID(input, output);
            UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
            VertexPositionInputs position = GetVertexPositionInputs(input.positionOS.xyz);
            output.positionCS = position.positionCS;
            output.positionWS = position.positionWS;
            output.normalWS = TransformObjectToWorldNormal(input.normalOS);
            output.color = input.color;
            output.uv = TRANSFORM_TEX(input.uv, _BaseMap);
            output.fogFactor = ComputeFogFactor(position.positionCS.z);
            return output;
        }

        // Analytic 3D value noise needs no imported texture, UVs or tangents.
        // All frequencies describe the final 48 metre gameplay world scale.
        float IslandHash(float3 p)
        {
            p = frac(p * 0.1031);
            p += dot(p, p.yzx + 33.33);
            return frac((p.x + p.y) * p.z);
        }

        float IslandNoise(float3 p)
        {
            float3 cell = floor(p);
            float3 f = frac(p);
            f = f * f * (3.0 - 2.0 * f);
            float n000 = IslandHash(cell);
            float n100 = IslandHash(cell + float3(1, 0, 0));
            float n010 = IslandHash(cell + float3(0, 1, 0));
            float n110 = IslandHash(cell + float3(1, 1, 0));
            float n001 = IslandHash(cell + float3(0, 0, 1));
            float n101 = IslandHash(cell + float3(1, 0, 1));
            float n011 = IslandHash(cell + float3(0, 1, 1));
            float n111 = IslandHash(cell + float3(1, 1, 1));
            return lerp(lerp(lerp(n000, n100, f.x), lerp(n010, n110, f.x), f.y),
                        lerp(lerp(n001, n101, f.x), lerp(n011, n111, f.x), f.y), f.z);
        }

        float IslandDeposits(float3 p)
        {
            return IslandNoise(p) * 0.58 +
                   IslandNoise(p * 2.07 + 12.7) * 0.28 +
                   IslandNoise(p * 4.19 + 37.1) * 0.14;
        }

        half3 IslandSurfaceNormal(float3 positionWS, half3 normalWS, float height)
        {
            // Surface-gradient bump mapping follows the mesh's actual normal;
            // cliffs receive the same detail density as gentle valley ground.
            float3 sigmaX = ddx(positionWS);
            float3 sigmaY = ddy(positionWS);
            float3 r1 = cross(sigmaY, normalWS);
            float3 r2 = cross(normalWS, sigmaX);
            float determinant = dot(sigmaX, r1);
            float3 gradient = (ddx(height) * r1 + ddy(height) * r2);
            gradient *= sign(determinant) / max(abs(determinant), 1e-7);
            return normalize(normalWS - gradient);
        }

        half4 IslandFragment(IslandVaryings input) : SV_Target
        {
            UNITY_SETUP_INSTANCE_ID(input);
            UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
            float3 p = input.positionWS;
            half3 geometryNormal = normalize(input.normalWS);
            float macro = IslandDeposits(p * _MacroScale);
            float brokenStone = IslandNoise(p * _DetailScale + 8.4);
            float screenFootprint = max(length(ddx(p)), length(ddy(p)));
            float grainVisibility = saturate(1.35 - screenFootprint * _MicroScale);
            float grain = lerp(0.5, IslandNoise(p * _MicroScale + 43.3), grainVisibility);

            // Warped, discontinuous bedding prevents artificial contour lines.
            float layerPhase = p.y * _LayerScale * 6.2831853 +
                               IslandNoise(p * 1.3 + 19.7) * 6.2 + p.x * 0.24;
            float layers = sin(layerPhase) * 0.5 + 0.5;
            float beddingMask = smoothstep(0.24, 0.66, brokenStone);
            float bedding = (layers - 0.5) * beddingMask * _StrataStrength;
            float fracture = smoothstep(0.43, 0.48, brokenStone) -
                             smoothstep(0.49, 0.57, brokenStone);
            half3 albedo = lerp(_BaseColor.rgb, _AccentColor.rgb,
                                saturate((macro - 0.19) * 1.65) * _ColorVariation);
            // Keep procedural variation subordinate to the imported surface texture;
            // the previous broad value range read as blurry, irregular colour blocks.
            albedo *= 0.96 + 0.06 * brokenStone + 0.03 * (grain - 0.5);
            albedo *= 1.0 + bedding * 0.2 - fracture * _FractureStrength;
            float mineralFlecks = smoothstep(0.72, 0.89, grain) * grainVisibility;
            albedo = lerp(albedo, _MineralColor.rgb, mineralFlecks * 0.13);
            // Default is zero, so meshes without vertex colours remain valid.
            albedo *= lerp(half3(1, 1, 1), max(input.color.rgb, half3(0.15, 0.15, 0.15)),
                           _VertexColorWeight);
            half3 grassTexture = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv).rgb;
            // Fade high-frequency grass detail before it falls below screen pixels.
            // Mipmaps still filter the texture, while the vertex-painted terrain
            // carries a clean, coherent colour at the island overview distance.
            float textureFootprint = max(length(ddx(input.uv)), length(ddy(input.uv))) *
                                     _BaseMap_TexelSize.z;
            float grassDetailFade = 1.0 - smoothstep(16.0, 64.0, textureFootprint);
            albedo = lerp(albedo, grassTexture,
                          saturate(_TextureWeight) * grassDetailFade);

            float cloudTime = _Time.y * 0.003;
            float cloudNoise = IslandNoise(float3(
                p.xz * 0.022 + float2(cloudTime, -cloudTime * 0.72), 0.37));
            float cloudShadow = smoothstep(0.39, 0.69, cloudNoise) * _WeatherCloudiness * 0.32;
            albedo *= 1.0 - cloudShadow;
            half cloudLuminance = dot(albedo, half3(0.299, 0.587, 0.114));
            half3 overcastAlbedo = lerp(albedo, cloudLuminance.xxx, 0.48) *
                                   half3(0.88, 0.92, 0.97);
            albedo = lerp(albedo, overcastAlbedo, _WeatherCloudiness);
            albedo *= 1.0 - saturate(_WeatherWetness) * 0.10;

            float relief = (brokenStone * 0.0035 + grain * 0.0018 +
                            bedding * 0.0022 - fracture * 0.0008) * _NormalStrength;
            half3 normalWS = IslandSurfaceNormal(p, geometryNormal, relief);

            SurfaceData surface = (SurfaceData)0;
            surface.albedo = albedo;
            surface.metallic = 0;
            surface.specular = half3(0.04, 0.04, 0.04);
            surface.smoothness = saturate(_Smoothness + (grain - 0.5) * 0.12 +
                                          saturate(_WeatherWetness) * 0.16);
            surface.normalTS = half3(0, 0, 1);
            surface.occlusion = 0.96 + 0.04 * brokenStone;
            // Keep the exposed waterline readable at grazing angles, where
            // low coastal faces otherwise fall nearly black under the scene light.
            float shorelineLift = 1.0 - smoothstep(0.0, 0.10, p.y);
            surface.emission = albedo * shorelineLift * 0.12;
            surface.alpha = 1;

            InputData lighting = (InputData)0;
            lighting.positionWS = p;
            lighting.positionCS = input.positionCS;
            lighting.normalWS = normalWS;
            lighting.viewDirectionWS = GetWorldSpaceNormalizeViewDir(p);
            #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
                lighting.shadowCoord = ComputeScreenPos(TransformWorldToHClip(p));
            #else
                lighting.shadowCoord = TransformWorldToShadowCoord(p);
            #endif
            lighting.fogCoord = input.fogFactor;
            lighting.vertexLighting = VertexLighting(p, normalWS);
            lighting.bakedGI = SampleSH(normalWS);
            lighting.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(input.positionCS);
            lighting.shadowMask = half4(1, 1, 1, 1);
            half4 color = UniversalFragmentPBR(lighting, surface);
            color.rgb = MixFog(color.rgb, lighting.fogCoord);
            return color;
        }
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForwardOnly" }
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex IslandVertex
            #pragma fragment IslandFragment
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On
            ZTest LEqual
            ColorMask 0
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex IslandShadowVertex
            #pragma fragment IslandDepthFragment
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #pragma multi_compile_instancing
            float3 _LightDirection;
            float3 _LightPosition;

            IslandVaryings IslandShadowVertex(IslandAttributes input)
            {
                IslandVaryings output = (IslandVaryings)0;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_TRANSFER_INSTANCE_ID(input, output);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                float3 positionWS = TransformObjectToWorld(input.positionOS.xyz);
                float3 normalWS = TransformObjectToWorldNormal(input.normalOS);
                #if defined(_CASTING_PUNCTUAL_LIGHT_SHADOW)
                    float3 lightDirection = normalize(_LightPosition - positionWS);
                #else
                    float3 lightDirection = _LightDirection;
                #endif
                output.positionCS = TransformWorldToHClip(ApplyShadowBias(positionWS, normalWS, lightDirection));
                output.positionCS = ApplyShadowClamping(output.positionCS);
                return output;
            }

            half4 IslandDepthFragment(IslandVaryings input) : SV_Target
            {
                return 0;
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ColorMask R
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex IslandVertex
            #pragma fragment IslandDepthOnlyFragment
            #pragma multi_compile_instancing
            half4 IslandDepthOnlyFragment(IslandVaryings input) : SV_Target
            {
                return input.positionCS.z;
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode" = "DepthNormalsOnly" }
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex IslandVertex
            #pragma fragment IslandDepthNormalsFragment
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT
            #pragma multi_compile_instancing
            half4 IslandDepthNormalsFragment(IslandVaryings input) : SV_Target
            {
                half3 normalWS = normalize(input.normalWS);
                #if defined(_GBUFFER_NORMALS_OCT)
                    float2 octNormal = PackNormalOctQuadEncode(normalWS);
                    return half4(PackFloat2To888(saturate(octNormal * 0.5 + 0.5)), 0);
                #else
                    return half4(normalWS, 0);
                #endif
            }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
