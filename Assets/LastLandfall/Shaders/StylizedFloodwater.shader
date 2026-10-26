Shader "LastLandfall/Stylized Floodwater"
{
    Properties
    {
        _DeepColor ("Deep ocean", Color) = (0.045, 0.18, 0.25, 1)
        _MidColor ("Open coastal water", Color) = (0.075, 0.28, 0.34, 1)
        _ShallowColor ("Rocky shallows", Color) = (0.13, 0.40, 0.40, 1)
        _FoamColor ("Broken rock surf", Color) = (0.80, 0.89, 0.87, 1)
        _ShoreFoamWidth ("Surf reach", Range(0.4, 6)) = 1.8
        _ShoreFoamStrength ("Surf strength", Range(0, 1)) = 0.72
        _WaveSpeed ("Wave clock speed", Range(0, 2)) = 0.6
        _WaveTime ("Accumulated wave phase", Float) = 0
        _WaveHeight ("Swell height", Range(0, 1.4)) = 0.30
        _RippleStrength ("Fine ripple normals", Range(0, 0.5)) = 0.28
        _ReflectionStrength ("Broken reflections", Range(0, 1)) = 0.72
        _OceanSlopeA ("Spectral wave slopes A", 2D) = "gray" {}
        _OceanSlopeB ("Spectral wave slopes B", 2D) = "gray" {}
        _WeatherCloudiness ("Cloud cover", Range(0, 1)) = 0
        _WeatherRain ("Rain disturbance", Range(0, 1)) = 0
        _TimeOfDayLight ("Day/night light", Color) = (1, 1, 1, 1)
        _CoastDistanceTex ("Signed rock coast distance", 2D) = "white" {}
        _CoastWorldMin ("Coast field world minimum", Vector) = (0, 0, 0, 0)
        _CoastWorldSize ("Coast field world size", Vector) = (1, 1, 0, 0)
        _CoastDistanceRange ("Coast distance range", Float) = 40
    }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Transparent" "Queue"="Transparent" }
        Pass
        {
            Name "UniversalForward"
            Tags { "LightMode"="UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            ZTest LEqual
            Cull Back
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_CoastDistanceTex);
            SAMPLER(sampler_CoastDistanceTex);
            TEXTURE2D(_OceanSlopeA);
            SAMPLER(sampler_OceanSlopeA);
            TEXTURE2D(_OceanSlopeB);
            SAMPLER(sampler_OceanSlopeB);
            CBUFFER_START(UnityPerMaterial)
                half4 _DeepColor, _MidColor, _ShallowColor, _FoamColor, _TimeOfDayLight;
                float _ShoreFoamWidth, _ShoreFoamStrength, _WaveSpeed, _WaveTime, _WaveHeight;
                float _RippleStrength, _ReflectionStrength, _WeatherCloudiness, _WeatherRain;
                float4 _CoastWorldMin, _CoastWorldSize;
                float _CoastDistanceRange;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float2 coastPosition : TEXCOORD1;
                half fogFactor : TEXCOORD2;
            };

            float Hash(float2 p)
            {
                float3 q = frac(float3(p.xyx) * float3(0.1031, 0.1030, 0.0973));
                q += dot(q, q.yzx + 33.33);
                return frac((q.x + q.y) * q.z);
            }

            // Continuous analytic derivatives avoid mesh-facet lighting and
            // eliminate the former fourteen-fold exaggeration of swell slopes.
            float3 NoiseGradient(float2 p)
            {
                float2 cell = floor(p), f = frac(p);
                float2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
                float2 du = 30.0 * f * f * (f - 1.0) * (f - 1.0);
                float a = Hash(cell), b = Hash(cell + float2(1, 0));
                float c = Hash(cell + float2(0, 1)), d = Hash(cell + 1.0);
                float k = a - b - c + d;
                return float3(a + (b - a) * u.x + (c - a) * u.y + k * u.x * u.y,
                    ((b - a) + k * u.y) * du.x, ((c - a) + k * u.x) * du.y);
            }

            float2 Rotate(float2 p) { return float2(.80*p.x-.60*p.y, .60*p.x+.80*p.y); }
            float Fractal(float2 p)
            {
                float value = NoiseGradient(p).x * .57;
                p = Rotate(p) * 2.03 + float2(11.7, 5.2);
                value += NoiseGradient(p).x * .29;
                p = Rotate(p) * 2.11 + float2(-7.4, 19.6);
                return value + NoiseGradient(p).x * .14;
            }

            float CoastDistance(float2 p)
            {
                float2 uv = (p - _CoastWorldMin.xy) / max(_CoastWorldSize.xy, .001);
                if (any(uv < 0.0) || any(uv > 1.0)) return _CoastDistanceRange;
                float value = SAMPLE_TEXTURE2D_LOD(_CoastDistanceTex, sampler_CoastDistanceTex, uv, 0).r;
                return (value * 2.0 - 1.0) * _CoastDistanceRange;
            }

            void Swell(float2 p, float t, out float height, out float2 gradient)
            {
                float4 phases = float4(dot(p, float2(.81, .59)) * .1698 - t * .43,
                    dot(p, float2(-.57, .82)) * .2768 - t * .57 + 1.7,
                    dot(p, float2(.25, -.968)) * .4520 - t * .79 + 3.1,
                    dot(p, float2(-.912, -.410)) * .6905 - t * .94 + .8);
                float4 amplitudes = _WaveHeight * float4(.43, .27, .18, .12);
                height = dot(sin(phases), amplitudes);
                float4 slopes = cos(phases) * amplitudes * float4(.1698, .2768, .4520, .6905);
                gradient = float2(dot(slopes, float4(.81, -.57, .25, -.912)),
                                  dot(slopes, float4(.59, .82, -.968, -.410)));
            }

            Varyings Vert(Attributes input)
            {
                Varyings output;
                float3 world = TransformObjectToWorld(input.positionOS.xyz);
                output.coastPosition = world.xz;
                float distance = CoastDistance(world.xz);
                float height; float2 gradient;
                Swell(world.xz, _WaveTime, height, gradient);
                world.y += height * smoothstep(.1, 7.0, distance);
                output.positionWS = world;
                output.positionCS = TransformWorldToHClip(world);
                output.fogFactor = ComputeFogFactor(output.positionCS.z);
                return output;
            }

            float2 RainGradient(float2 p, float time)
            {
                float2 cell = floor(p), local = frac(p);
                float seed = Hash(cell + 17.2);
                float2 center = float2(seed, Hash(cell - 5.3)) * .62 + .19;
                float2 delta = local - center;
                float distance = length(delta);
                float age = frac(time * .46 + seed * 7.13);
                float ring = distance - age * .53;
                float profile = exp(-abs(ring) * 34.0) * sin(ring * 57.0);
                float cellFade = smoothstep(0.0, .13, min(min(local.x, local.y), min(1-local.x, 1-local.y)));
                return delta / max(distance, .01) * profile * (1.0-age) * cellFade;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                float2 p = input.coastPosition;
                float t = _WaveTime;
                float distance = CoastDistance(p);
                float clouds = saturate(_WeatherCloudiness);
                float roughWeather = saturate((_WaveHeight - .30) / .55);
                float2 drift = float2(t * .024, -t * .017);
                float2 warp = float2(NoiseGradient(p * .083 + drift).x,
                    NoiseGradient(Rotate(p) * .071 - drift + 19.0).x) - .5;
                float broadVariation = Fractal(p * .024 + warp * .42 + drift * .18);
                float nearVariation = NoiseGradient(p * .19 + warp + drift).x;

                // A narrow irregular rocky shelf replaces the broad cyan belt.
                float coloredDistance = max(0.0, distance + (nearVariation - .5) * 1.35);
                float shelf = 1.0 - smoothstep(3.0, 25.0, coloredDistance);
                float shallows = 1.0 - smoothstep(.3, 6.5, coloredDistance);
                half3 water = lerp(_DeepColor.rgb, _MidColor.rgb, shelf * .82);
                water = lerp(water, _ShallowColor.rgb, shallows * .68);
                water *= .93 + broadVariation * .14;

                float swellHeight; float2 swellGradient;
                Swell(p, t, swellHeight, swellGradient);
                swellGradient *= smoothstep(.1, 7.0, distance);
                float phaseA = dot(p, float2(.93, .37)) * 2.17 + warp.x * 5.7 - t * .82;
                float phaseB = dot(p, float2(-.42, .907)) * 3.81 + warp.y * 6.3 - t * 1.17;
                float attenuationA = rcp(1.0 + fwidth(phaseA) * 1.7);
                float attenuationB = rcp(1.0 + fwidth(phaseB) * 1.7);
                float3 fineNoise = NoiseGradient(Rotate(p) * 1.73 + warp * 2.7 + drift * 3.0);
                float2 ripples = float2(.93, .37) * cos(phaseA) * attenuationA * .56 +
                    float2(-.42, .907) * cos(phaseB) * attenuationB * .33;
                ripples += fineNoise.yz * .22 / (1.0 + length(fwidth(p * 1.73)));
                float2 slopeA = SAMPLE_TEXTURE2D(_OceanSlopeA, sampler_OceanSlopeA,
                    p / 73.0 + warp * .034 + float2(t*.0019,-t*.0012)).rg * 2.0 - 1.0;
                float2 slopeB = SAMPLE_TEXTURE2D(_OceanSlopeB, sampler_OceanSlopeB,
                    Rotate(p) / 109.0 - warp * .027 + float2(-t*.0013,t*.0017)).rg * 2.0 - 1.0;
                // Rotate the second gradient back into world axes. The two
                // spectra have different directions, scales, drift and phase.
                slopeB = float2(.80*slopeB.x+.60*slopeB.y, -.60*slopeB.x+.80*slopeB.y);
                ripples = ripples * .30 + slopeA * .85 + slopeB * .65;
                float2 rainRipples = RainGradient(p * .73 + 3.2, t) +
                    RainGradient(Rotate(p) * 1.11 - 9.7, t * 1.19) * .55;
                float2 gradient = swellGradient + ripples * _RippleStrength *
                    lerp(.90, 1.60, roughWeather) + rainRipples * _WeatherRain * .045;
                half3 normal = normalize(half3(-gradient.x, 1, -gradient.y));
                half3 view = GetWorldSpaceNormalizeViewDir(input.positionWS);
                Light light = GetMainLight();

                half fresnel = .07h + .65h * pow(1.0h-saturate(dot(normal, view)), 3.0h);
                half3 reflected = reflect(-view, normal);
                half skyGradient = saturate(reflected.y * .65h + .35h);
                half3 sky = lerp(half3(.105,.17,.22), half3(.21,.31,.37), skyGradient);
                sky = lerp(sky, half3(.15,.19,.22), clouds * .7);
                water = lerp(water, sky, fresnel * _ReflectionStrength);
                half ndh = saturate(dot(normal, normalize(view + light.direction)));
                half gloss = lerp(190.0h, 68.0h, roughWeather);
                float sparkle = smoothstep(.52, .86, fineNoise.x);
                water += pow(ndh, gloss) * sparkle * light.color.rgb *
                    _ReflectionStrength * (1.0-clouds*.78) * .55;
                // Sky response reveals small normal motion away from sun glare.
                half skyFacing = dot(normal, normalize(half3(-.35,.85,.40)));
                water *= .90h + .16h * skyFacing;
                half rippleFacing = saturate(.5h + dot(gradient, float2(-.71,.70)) * 1.7h);
                water *= lerp(.78h, 1.22h, rippleFacing);
                // Broken bright-sky facets remain visible when the sun itself
                // is behind the camera. Their shape comes from spectral slope
                // data, never from a repeated sine ridge or square noise cell.
                float skyGlints = smoothstep(.54,.90,.5+dot(gradient,float2(.80,.60))*2.1) *
                    smoothstep(.38,.70,slopeA.y*.5+.5);
                water += skyGlints * half3(.12,.18,.20) * _ReflectionStrength *
                    (1.0-clouds*.60);
                water += fineNoise.x * .005h * half3(.4,.8,1);

                // Independent surge phases break up the shore; never draw an
                // uninterrupted white rim or multiple concentric foam rings.
                float foamNoise = Fractal(p * 1.21 + warp * 2.3 - float2(t*.09,t*.06));
                float alongCoast = NoiseGradient(p * .13 + 7.7).x;
                float surge = .5 + .5 * sin(t * .76 + alongCoast * 7.0);
                float reach = max(.4, _ShoreFoamWidth) * (.28 + .52 * surge);
                float frontDistance = distance - reach * (.40 + .60 * surge);
                float front = exp(-frontDistance*frontDistance / (.035 + surge*.055));
                float wash = (1.0-smoothstep(.10,max(.35,reach),distance)) * (.07+.18*surge);
                float broken = smoothstep(.36,.70,foamNoise);
                float contact = (1.0-smoothstep(.025,.24,distance)) *
                    smoothstep(.43,.66,foamNoise) * .32;
                float shore = max(contact, (front*.55+wash)*broken) *
                    _ShoreFoamStrength * step(-.25,distance);
                float caps = smoothstep(.42,.68,length(gradient)) *
                    smoothstep(.50,.74,slopeA.x*.5+.5) * roughWeather *
                    smoothstep(5.0,14.0,distance) * .07;

                half waterLuma = dot(water, half3(.2126,.7152,.0722));
                water = lerp(water, lerp(water, waterLuma.xxx, .30) * half3(.85,.91,.97), clouds);
                half timeLight = saturate(dot(_TimeOfDayLight.rgb, half3(.2126,.7152,.0722)));
                water *= lerp(.68,1.0,timeLight);
                half3 foam = lerp(_FoamColor.rgb, half3(.48,.59,.63), clouds*.40);
                water = lerp(water, foam, saturate(shore+caps));
                water = MixFog(water, input.fogFactor);
                return half4(max(water,.002h),1);
            }
            ENDHLSL
        }
    }
}
