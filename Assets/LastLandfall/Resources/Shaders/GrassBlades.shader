Shader "LastLandfall/Grass Blades"
{
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        Cull Off
        Pass
        {
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            UNITY_INSTANCING_BUFFER_START(GrassProperties)
                UNITY_DEFINE_INSTANCED_PROP(float4, _InstanceColor)
            UNITY_INSTANCING_BUFFER_END(GrassProperties)
            float _IslandGrassWind;
            float _IslandGrassWindPhase;
            struct Attributes { float4 positionOS : POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; half4 color : COLOR; };
            Varyings Vert(Attributes input)
            {
                Varyings output;
                UNITY_SETUP_INSTANCE_ID(input);
                float3 root = TransformObjectToWorld(float3(0, 0, 0));
                float3 world = TransformObjectToWorld(input.positionOS.xyz);
                float phase = _IslandGrassWindPhase + dot(root.xz, float2(.37, .23));
                float sway = sin(phase) * .7 + sin(phase * 1.73 + root.x * .6) * .3;
                world.xz += normalize(float2(.78, .42)) * sway * (.025 + _IslandGrassWind * .11) * saturate(input.positionOS.y);
                output.positionCS = TransformWorldToHClip(world);
                output.color = UNITY_ACCESS_INSTANCED_PROP(GrassProperties, _InstanceColor);
                output.color.rgb *= lerp(.72, 1.0, saturate(input.positionOS.y));
                return output;
            }
            half4 Frag(Varyings input) : SV_Target
            {
                Light sun = GetMainLight();
                return half4(input.color.rgb * (half3(.48,.48,.48) + sun.color * .52), 1);
            }
            ENDHLSL
        }
    }
}
