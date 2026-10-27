Shader "LastLandfall/Basin Water"
{
    Properties
    {
        _Tint ("Water tint", Color) = (1, 1, 1, 1)
        [HideInInspector] _TimeOfDayLight ("Time of day light", Color) = (1, 1, 1, 1)
        _FlowSpeed ("Flow speed", Range(0, 1)) = 0.12
        [HideInInspector] _FlowTime ("Accumulated flow time", Float) = 0
        _RippleStrength ("Ripple strength", Range(0, 0.1)) = 0.025
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Opaque"
            "Queue" = "Geometry+1"
        }

        Pass
        {
            Name "UniversalForward"
            Tags { "LightMode" = "UniversalForward" }
            Cull Off
            ZWrite On
            ZTest LEqual

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Tint;
                half4 _TimeOfDayLight;
                float _FlowSpeed;
                float _FlowTime;
                float _RippleStrength;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                half4 color : COLOR;
                float2 uv : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                half4 color : TEXCOORD2;
                float2 uv : TEXCOORD3;
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                VertexPositionInputs position = GetVertexPositionInputs(input.positionOS.xyz);
                output.positionCS = position.positionCS;
                output.positionWS = position.positionWS;
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
                output.color = input.color;
                output.uv = input.uv;
                return output;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                half3 normalWS = normalize(input.normalWS);
                half3 viewDirection = normalize(GetWorldSpaceViewDir(input.positionWS));
                half fresnel = pow(1.0h - saturate(dot(normalWS, viewDirection)), 2.0h);
                float phase = input.uv.x * 6.2831853 - _FlowTime * _FlowSpeed * 6.2831853;
                float ripple = sin(phase + input.uv.y * 2.2) * _RippleStrength;
                // A generated stream can omit vertex colours; Unity then supplies
                // solid white. Give that unpainted surface the pond's water tint.
                half unpainted = smoothstep(.96h, .995h, min(input.color.r, min(input.color.g, input.color.b)));
                half3 authoredWater = lerp(input.color.rgb, half3(.10h,.19h,.20h), unpainted);
                half3 color = authoredWater * _Tint.rgb;
                color += ripple.xxx + fresnel * half3(0.035h, 0.055h, 0.055h);
                color *= _TimeOfDayLight.rgb;
                return half4(saturate(color), 1.0h);
            }
            ENDHLSL
        }
    }
}
