Shader "LastLandfall/Weather Particle"
{
    Properties
    {
        _TintColor ("Tint", Color) = (0.8, 0.9, 1, 0.7)
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
                float4 _TintColor;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                output.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                output.uv = input.uv;
                return output;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                float edge = 1.0 - smoothstep(0.28, 0.5, abs(input.uv.x - 0.5) * 2.0);
                float verticalFade = smoothstep(0.0, 0.12, input.uv.y) *
                                     (1.0 - smoothstep(0.82, 1.0, input.uv.y));
                return half4(_TintColor.rgb, _TintColor.a * edge * verticalFade);
            }
            ENDHLSL
        }
    }
}
