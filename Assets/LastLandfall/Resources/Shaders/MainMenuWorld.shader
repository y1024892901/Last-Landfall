Shader "LastLandfall/Main Menu World"
{
    Properties
    {
        _MainTex ("Flooded World", 2D) = "black" {}
        _AnimationTime ("Animation Time", Float) = 0
        _ScreenAspect ("Screen Aspect", Float) = 1.7778
        _Opacity ("Opacity", Range(0, 1)) = 1
        _PushAmount ("Camera Push Amount", Range(0, 0.1)) = 0.035
        _OceanMotion ("Ocean Motion", Range(0, 2)) = 1
        _MistAmount ("Drifting Mist", Range(0, 1)) = 0.18
    }
    SubShader
    {
        Tags { "Queue"="Overlay+100" "RenderType"="Transparent" }
        Pass
        {
            Cull Off
            ZWrite Off
            ZTest Always
            Blend SrcAlpha OneMinusSrcAlpha
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            sampler2D _MainTex;
            float4 _MainTex_TexelSize;
            float _AnimationTime, _ScreenAspect, _Opacity;
            float _PushAmount, _OceanMotion, _MistAmount;
            struct Varyings { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; };
            Varyings vert(appdata_img input)
            {
                Varyings output;
                output.pos = UnityObjectToClipPos(input.vertex);
                output.uv = input.texcoord;
                return output;
            }
            float hash(float2 p) { return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453); }
            float noise(float2 p)
            {
                float2 a = floor(p), f = frac(p);
                f = f * f * (3 - 2 * f);
                return lerp(lerp(hash(a), hash(a + float2(1,0)), f.x),
                    lerp(hash(a + float2(0,1)), hash(a + 1), f.x), f.y);
            }
            float4 frag(Varyings input) : SV_Target
            {
                float t = _AnimationTime;
                float2 uv = input.uv;
                float imageAspect = _MainTex_TexelSize.z / _MainTex_TexelSize.w;
                if (_ScreenAspect < imageAspect) uv.x = (uv.x - 0.5) * _ScreenAspect / imageAspect + 0.5;
                else uv.y = (uv.y - 0.5) * imageAspect / _ScreenAspect + 0.5;
                // A two-minute out-and-back cycle; starts pushing in and eases at both ends.
                // The overscan keeps texture edges outside the visible frame.
                float push = 0.5 - 0.5 * cos(t * 0.05235988);
                float zoom = 1.025 + _PushAmount * push;
                uv = (uv - 0.5) / zoom + 0.5;
                uv += float2(sin(t * 0.018) * 0.003, sin(t * 0.013) * 0.0015);
                float3 source = tex2D(_MainTex, uv).rgb;
                // Teal water moves gently; neutral rock silhouettes remain stable.
                float sea = smoothstep(0.02, 0.12, min(source.g - source.r, source.b - source.r));
                // Suppress sky/cloud highlights and avoid pulling mountain edges into waves.
                sea *= 1 - smoothstep(0.70, 0.86, uv.y);
                float2 ripple = float2(sin(uv.y * 130 + t * 0.8), cos(uv.x * 110 - t * 0.55));
                ripple += 0.35 * float2(sin(uv.y * 270 - t * 0.43), cos(uv.x * 195 + t * 0.37));
                float3 color = tex2D(_MainTex, uv + ripple * sea * 0.00065 * _OceanMotion).rgb;
                float shimmer = pow(saturate(sin(uv.y * 210 + sin(uv.x * 38) * 1.8 + t * 0.7)), 18);
                color += shimmer * sea * _OceanMotion * float3(0.012, 0.022, 0.026);
                float cloud = noise(uv * float2(7, 12) + float2(t * 0.007, -t * 0.002));
                cloud += 0.45 * noise(uv * 26 + float2(t * 0.011, 0));
                float fogBand = exp(-pow((uv.y - 0.54) * 5, 2));
                float distantMist = smoothstep(0.68, 1.25, cloud) * fogBand;
                float nearCloud = noise(uv * float2(11, 19) + float2(-t * 0.004, t * 0.001));
                float nearBand = exp(-pow((uv.y - 0.32) * 8, 2));
                float nearMist = smoothstep(0.58, 0.90, nearCloud) * nearBand;
                float fog = saturate((distantMist * 0.75 + nearMist * 0.3) * _MistAmount);
                color = lerp(color, float3(0.58, 0.68, 0.72), fog);
                float leftShade = 1 - smoothstep(0.03, 0.60, input.uv.x);
                color *= 1 - 0.34 * leftShade;
                float2 v = (input.uv - 0.5) * float2(1, 0.8);
                color *= 1 - 0.30 * dot(v, v);
                return float4(color, _Opacity);
            }
            ENDHLSL
        }
    }
}
