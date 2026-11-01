Shader "LastLandfall/Island Construction Grid"
{
    Properties
    {
        _Color ("Lowland Grid", Color) = (0.82, 0.95, 0.85, 0.82)
        _MountainColor ("Mountain Grid", Color) = (1, 0.72, 0.34, 0.82)
        _LineWidth ("Line Width", Float) = 0.018
        _SeaLevel ("Sea Level", Float) = -0.92
        _BuildingSlopeCos ("Building Slope Cosine", Float) = 0.9272
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
            sampler2D _CoastDistanceTex;
            float4 _CoastWorldMin, _CoastWorldSize;
            float _CoastDistanceRange, _CoastalOnly, _PlacementHeight, _HeightBandEnabled;
            float4x4 _WorldToGrid;
            float4 _Color, _MountainColor;
            float _LineWidth, _SeaLevel, _BuildingSlopeCos;
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
                if (_HeightBandEnabled > .5)
                {
                    clip(.55 - abs(i.grid.y - _PlacementHeight));
                    clip(normalize(i.normal).y - .45);
                }
                float2 p = i.grid.xz;
                if (_CoastalOnly > .5)
                {
                    float2 uv = (p - _CoastWorldMin.xy) / _CoastWorldSize.xy;
                    float coast = (tex2D(_CoastDistanceTex, uv).r - .5) * 2 * _CoastDistanceRange;
                    clip(coast + 2.0);
                    clip(i.grid.y - _SeaLevel);
                    clip(_SeaLevel + 3.0 - i.grid.y);
                }
                float2 distanceToLine = abs(frac(p + 0.5) - 0.5);
                float2 aa = max(fwidth(p), 0.0001);
                float2 lines = 1 - smoothstep(_LineWidth * 0.5, _LineWidth * 0.5 + aa, distanceToLine);
                float2 dash = step(frac(p.yx * 4), 0.72);
                float alpha = max(lines.x * dash.x, lines.y * dash.y);
                clip(alpha - 0.005);
                float restrictedSlope = step(normalize(i.normal).y, _BuildingSlopeCos);
                float4 color = lerp(_Color, _MountainColor, restrictedSlope);
                if (_CoastalOnly > .5) color.rgb = float3(.34, .77, .84);
                color.a *= alpha;
                return color;
            }
            ENDHLSL
        }
    }
}
