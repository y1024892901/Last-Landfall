Shader "LastLandfall/Grass Blades"
{
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        Cull Off
        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            float _IslandGrassWind;
            float _IslandGrassWindPhase;
            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; half4 color : COLOR; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; half4 color : COLOR; half3 normalWS : TEXCOORD0; half fog : TEXCOORD1; };
            Varyings Vert(Attributes input)
            {
                Varyings output;
                UNITY_SETUP_INSTANCE_ID(input);
                float3 world = TransformObjectToWorld(input.positionOS.xyz);
                float phase = _IslandGrassWindPhase + dot(world.xz, float2(.37, .23));
                float sway = sin(phase) * .7 + sin(phase * 1.73 + world.x * .6) * .3;
                world.xz += normalize(float2(.78, .42)) * sway * (.012 + _IslandGrassWind * .07) * input.color.a * input.color.a;
                output.positionCS = TransformWorldToHClip(world);
                output.color = input.color;
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
                output.fog = ComputeFogFactor(output.positionCS.z);
                return output;
            }
            half4 Frag(Varyings input, FRONT_FACE_TYPE face : FRONT_FACE_SEMANTIC) : SV_Target
            {
                Light sun = GetMainLight();
                half3 normalWS = normalize(input.normalWS) * IS_FRONT_VFACE(face, 1.0h, -1.0h);
                half daylight = saturate(dot(normalWS, sun.direction) * .5h + .5h);
                half3 ambient = max(SampleSH(normalWS), half3(.28,.28,.28));
                half3 color = input.color.rgb * (ambient + sun.color * daylight * .55h);
                return half4(MixFog(color, input.fog), 1);
            }
            ENDHLSL
        }
    }
}
