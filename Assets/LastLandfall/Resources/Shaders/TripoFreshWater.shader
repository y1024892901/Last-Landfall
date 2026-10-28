Shader "LastLandfall/Tripo Fresh Water"
{
    Properties
    {
        _WaterRegion ("Water region reference", 2D) = "black" {}
        _Tint ("Water tint", Color) = (.075,.24,.25,1)
    }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry+5" }
        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            Cull Off
            Offset -1, -1
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            TEXTURE2D(_WaterRegion); SAMPLER(sampler_WaterRegion);
            CBUFFER_START(UnityPerMaterial)
                half4 _Tint;
            CBUFFER_END
            struct Attributes { float4 positionOS:POSITION; float3 normalOS:NORMAL; float2 uv:TEXCOORD0; };
            struct Varyings { float4 positionCS:SV_POSITION; float3 positionWS:TEXCOORD0; float2 uv:TEXCOORD1; float3 normalWS:TEXCOORD2; };
            Varyings Vert(Attributes input)
            {
                Varyings output;
                output.positionWS = TransformObjectToWorld(input.positionOS.xyz);
                output.positionCS = TransformWorldToHClip(output.positionWS);
                output.uv = input.uv;
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
                return output;
            }
            half4 Frag(Varyings input):SV_Target
            {
                half3 reference = SAMPLE_TEXTURE2D(_WaterRegion,sampler_WaterRegion,input.uv).rgb;
                half mask = smoothstep(.015,.075,min(reference.b-reference.r,reference.g-reference.r)) *
                    smoothstep(-.035,.035,reference.b-reference.g);
                clip(mask-.22);
                clip(input.normalWS.y-.45);
                float2 p = input.positionWS.xz;
                // Flow bands move along the island texture's channel direction.
                // Lateral bends keep the streaks from reading as straight stripes.
                float t = _Time.y;
                float bend = sin(input.uv.x*28.0)*.11 + sin(input.uv.x*9.0)*.18;
                float flowPhase = (input.uv.y + bend)*115.0 - t*2.8;
                float flowBand = sin(flowPhase);
                float flowStreak = pow(saturate(sin(flowPhase)*.5+.5), 18.0);
                float fine = sin(flowPhase*2.35 + input.uv.x*41.0)*.5+.5;
                float ripple = sin(p.x*7.0+p.y*3.0-t*.7)*.5+.5;
                float3 normal = normalize(float3(flowBand*.055+ripple*.018,1,fine*.035));
                float fresnel = pow(1-saturate(dot(normal,GetWorldSpaceNormalizeViewDir(input.positionWS))),3);
                Light light = GetMainLight(TransformWorldToShadowCoord(input.positionWS));
                half3 color = _Tint.rgb + flowBand*.022 + fine*.012 + ripple*.008;
                color += flowStreak*half3(.075,.12,.12);
                color += fresnel*half3(.065,.10,.11);
                float specular = pow(saturate(dot(normal,normalize(light.direction+GetWorldSpaceNormalizeViewDir(input.positionWS)))),96);
                color = color*(.4+light.color*.6) + light.color*specular*.22;
                color += (1-smoothstep(.22,.55,mask))*half3(.04,.065,.055);
                return half4(saturate(color),1);
            }
            ENDHLSL
        }
    }
}
