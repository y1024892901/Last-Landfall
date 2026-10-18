Shader "LastLandfall/Island Construction Grid"
{
    Properties
    {
        _Color ("Lowland Grid", Color) = (0.82, 0.95, 0.85, 0.82)
        _MountainColor ("Mountain Grid", Color) = (1, 0.72, 0.34, 0.82)
        _LineWidth ("Line Width", Float) = 0.018
        _SeaLevel ("Sea Level", Float) = -0.92
        _BuildingElevation ("Building Elevation Limit", Float) = 2.76
        _BuildingSlopeCos ("Building Slope Cosine", Float) = 0.9703
    }
    SubShader
    {
        Tags { "Queue"="Transparent+10" "RenderType"="Transparent" }
        Pass
        {
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            ZTest LEqual
            Cull Off
            Offset -2, -2
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            struct Input { float4 vertex : POSITION; float3 normal : NORMAL; };
            struct Output { float4 clip : SV_POSITION; float3 grid : TEXCOORD0; float3 normal : TEXCOORD1; };
            float4x4 _WorldToGrid;
            float4 _Color, _MountainColor;
            float _LineWidth, _SeaLevel, _BuildingElevation, _BuildingSlopeCos;
            Output vert(Input v)
            {
                Output o;
                o.clip = UnityObjectToClipPos(v.vertex);
                o.grid = mul(_WorldToGrid, mul(unity_ObjectToWorld, v.vertex)).xyz;
                o.normal = mul((float3x3)_WorldToGrid, UnityObjectToWorldNormal(v.normal));
                return o;
            }
            float4 frag(Output i) : SV_Target
            {
                clip(i.grid.y - _SeaLevel - 0.002);
                float2 p = i.grid.xz;
                float2 distanceToLine = abs(frac(p + 0.5) - 0.5);
                float2 aa = max(fwidth(p), 0.0001);
                float2 lines = 1 - smoothstep(_LineWidth * 0.5, _LineWidth * 0.5 + aa, distanceToLine);
                float2 dash = step(frac(p.yx * 4), 0.72);
                float alpha = max(lines.x * dash.x, lines.y * dash.y);
                clip(alpha - 0.005);
                float mountain = max(step(normalize(i.normal).y, _BuildingSlopeCos), step(_BuildingElevation, i.grid.y));
                float4 color = lerp(_Color, _MountainColor, mountain);
                color.a *= alpha;
                return color;
            }
            ENDHLSL
        }
    }
}
