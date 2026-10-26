Shader "LastLandfall/Coastal Construction Grid"
{
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "Queue"="Transparent+20" "RenderType"="Transparent" }
        Pass
        {
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            Cull Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            TEXTURE2D(_CoastDistanceTex); SAMPLER(sampler_CoastDistanceTex);
            float4 _CoastWorldMin, _CoastWorldSize;
            float _CoastDistanceRange;
            float4x4 _WorldToGrid;
            struct Varyings { float4 positionCS:SV_POSITION; float2 local:TEXCOORD0; };
            Varyings vert(float3 positionOS:POSITION)
            {
                Varyings o; float3 world=TransformObjectToWorld(positionOS);
                o.positionCS=TransformWorldToHClip(world);
                o.local=mul(_WorldToGrid,float4(world,1)).xz; return o;
            }
            half4 frag(Varyings i):SV_Target
            {
                float2 uv=(i.local-_CoastWorldMin.xy)/_CoastWorldSize.xy;
                float distance=(SAMPLE_TEXTURE2D(_CoastDistanceTex,sampler_CoastDistanceTex,uv).r-.5)*2*_CoastDistanceRange;
                clip(distance-.12); clip(24-distance);
                float2 edge=abs(frac(i.local+.5)-.5);
                float2 aa=max(fwidth(i.local),.008);
                float2 lines=1-smoothstep(.012,.012+aa,edge);
                float coverage=max(lines.x,lines.y);
                float dash=step(.3,frac((i.local.x+i.local.y)*3));
                float fade=(1-smoothstep(21,24,distance))*smoothstep(.12,.6,distance);
                return half4(.34,.77,.84,(.025+coverage*.38*dash)*fade);
            }
            ENDHLSL
        }
    }
}
