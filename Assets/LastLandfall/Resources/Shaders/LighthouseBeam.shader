Shader "LastLandfall/Lighthouse Beam"
{
    Properties
    {
        _Visibility("Night visibility",Range(0,1))=1
        _BeamLength("Beam length",Float)=260
        _BeamHalfWidth("Beam half width",Float)=28
    }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "Queue"="Transparent+30" }
        Pass
        {
            Blend SrcAlpha One
            ZWrite Off
            Cull Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            float _Visibility, _BeamLength, _BeamHalfWidth;
            struct V {float4 positionCS:SV_POSITION;float3 local:TEXCOORD0;};
            V vert(float3 p:POSITION){V o;o.positionCS=TransformObjectToHClip(p);o.local=p;return o;}
            half4 frag(V i):SV_Target
            {
                float along=saturate(i.local.z/max(1,_BeamLength));
                float edge=1-saturate(abs(i.local.x)/max(.1,along*_BeamHalfWidth));
                return half4(1,.83,.52,pow(edge,1.6)*pow(1-along,.8)*.12*_Visibility);
            }
            ENDHLSL
        }
    }
}
