Shader "LastLandfall/Construction Reveal"
{
 Properties { _BaseMap("Texture",2D)="white"{} _BaseColor("Color",Color)=(1,1,1,1) _CutHeight("Height",Float)=0 }
 SubShader
 {
 Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" }
 HLSLINCLUDE
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
 TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
 CBUFFER_START(UnityPerMaterial)
 float4 _BaseMap_ST; half4 _BaseColor; float _CutHeight;
 CBUFFER_END
 struct A { float4 p:POSITION; float3 n:NORMAL; float2 uv:TEXCOORD0; };
 struct V { float4 p:SV_POSITION; float3 world:TEXCOORD0; float3 normal:TEXCOORD1; float2 uv:TEXCOORD2; };
 V vert(A i) { V o; o.world=TransformObjectToWorld(i.p.xyz); o.p=TransformWorldToHClip(o.world); o.normal=TransformObjectToWorldNormal(i.n); o.uv=TRANSFORM_TEX(i.uv,_BaseMap); return o; }
 ENDHLSL
 Pass
 {
 Tags { "LightMode"="UniversalForward" }
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
 #pragma multi_compile_fragment _ _SHADOWS_SOFT
 half4 frag(V i):SV_Target {
 clip(_CutHeight-i.world.y);
 half4 c=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,i.uv)*_BaseColor;
 Light l=GetMainLight(TransformWorldToShadowCoord(i.world));
 half3 n=normalize(i.normal);
 return half4(c.rgb*(SampleSH(n)+l.color*saturate(dot(n,l.direction))*l.shadowAttenuation),1);
 }
 ENDHLSL
 }
 Pass
 {
 Tags { "LightMode"="ShadowCaster" }
 ZWrite On ColorMask 0
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment shadow
 half4 shadow(V i):SV_Target { clip(_CutHeight-i.world.y); return 0; }
 ENDHLSL
 }
 Pass
 {
 Tags { "LightMode"="DepthOnly" }
 ZWrite On ColorMask 0
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment depth
 half4 depth(V i):SV_Target { clip(_CutHeight-i.world.y); return 0; }
 ENDHLSL
 }
 }
}
