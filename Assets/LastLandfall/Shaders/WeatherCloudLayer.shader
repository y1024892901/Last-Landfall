Shader "LastLandfall/Weather Cloud Layer"
{
    Properties
    {
        _Cloudiness ("Cloudiness", Range(0, 1)) = 0
        _CloudTime ("Cloud Flow", Float) = 0
        _CloudTint ("Cloud Tint", Color) = (1, 1, 1, 1)
        _CloudWindDirection ("Cloud Wind Direction", Vector) = (0.88, 0, 0.47, 0)
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "Queue" = "Transparent"
            "RenderType" = "Transparent"
            "IgnoreProjector" = "True"
        }

        Pass
        {
            Blend SrcAlpha OneMinusSrcAlpha
            Cull Off
            ZWrite Off
            ZTest LEqual

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float _Cloudiness;
                float _CloudTime;
                float4 _CloudTint;
                float4 _CloudWindDirection;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 worldXZ : TEXCOORD0;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                float3 worldPosition = TransformObjectToWorld(input.positionOS.xyz);
                output.positionCS = TransformWorldToHClip(worldPosition);
                output.worldXZ = worldPosition.xz;
                return output;
            }

            float Hash31(float3 p)
            {
                p = frac(p * 0.1031);
                p += dot(p, p.yzx + 33.33);
                return frac((p.x + p.y) * p.z);
            }

            float ValueNoise(float3 p)
            {
                float3 cell = floor(p);
                float3 f = frac(p);
                f = f * f * (3.0 - 2.0 * f);

                float n000 = Hash31(cell + float3(0, 0, 0));
                float n100 = Hash31(cell + float3(1, 0, 0));
                float n010 = Hash31(cell + float3(0, 1, 0));
                float n110 = Hash31(cell + float3(1, 1, 0));
                float n001 = Hash31(cell + float3(0, 0, 1));
                float n101 = Hash31(cell + float3(1, 0, 1));
                float n011 = Hash31(cell + float3(0, 1, 1));
                float n111 = Hash31(cell + float3(1, 1, 1));

                float nx00 = lerp(n000, n100, f.x);
                float nx10 = lerp(n010, n110, f.x);
                float nx01 = lerp(n001, n101, f.x);
                float nx11 = lerp(n011, n111, f.x);
                return lerp(lerp(nx00, nx10, f.y), lerp(nx01, nx11, f.y), f.z);
            }

            float CloudNoise(float3 p)
            {
                return ValueNoise(p) * 0.58 +
                       ValueNoise(p * 2.03 + 11.7) * 0.29 +
                       ValueNoise(p * 4.17 - 6.2) * 0.13;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                float coverage = saturate(_Cloudiness);
                float2 wind = normalize(_CloudWindDirection.xz + float2(0.0001, 0.0001));
                float2 cloudPosition = input.worldXZ * 0.022 + wind * (_CloudTime * 0.22);
                float noise = CloudNoise(float3(cloudPosition, 0.37));
                float threshold = lerp(0.78, 0.43, coverage);
                float cloudShape = smoothstep(threshold - 0.10, threshold + 0.10, noise);
                float detail = smoothstep(0.25, 0.78,
                    CloudNoise(float3(cloudPosition * 2.15 + 7.1, 2.3)));
                float alpha = cloudShape * lerp(0.27, 0.66, detail) * coverage * 0.88;
                return half4(_CloudTint.rgb, saturate(alpha));
            }
            ENDHLSL
        }
    }
}
