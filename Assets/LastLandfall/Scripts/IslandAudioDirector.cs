using System;
using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>Independent score, coastal ambience and weather layers.</summary>
    public sealed class IslandAudioDirector : MonoBehaviour
    {
        public const float DefaultMusicVolume = 0.65f;
        public const float DefaultEnvironmentVolume = 0.70f;
        public const string MusicVolumeKey = "LastLandfall.Settings.MusicVolume";
        public const string EnvironmentVolumeKey = "LastLandfall.Settings.EnvironmentVolume";
        private const float MusicFadeSeconds = 4f;
        private const float WeatherFadeSeconds = 5f;
        private static IslandAudioDirector instance;
        private readonly System.Random random = new System.Random();
        private readonly List<int> shuffleBag = new List<int>();
        private readonly AudioClip[] gameplayMusic = new AudioClip[4];
        private readonly AudioClip[] weatherClips = new AudioClip[5];
        private readonly AudioClip[] thunderClips = new AudioClip[3];
        private AudioClip menuMusic;
        private CrossfadePair music, ambience;
        private AudioSource ocean, thunder;
        private IslandWeatherSystem observedWeather;
        private int bagCursor, lastTrack = -1;
        private bool contextInitialized, gameplay, paused;
        private double nextTrackAt;
        private float nextBindingCheck, pendingThunderAt = -1f;
        private float weatherStrength = 0.35f, gameplayAmbienceGain, oceanLevel;
        public static IslandAudioDirector Existing => instance;

        public static IslandAudioDirector Instance
        {
            get
            {
                if (instance == null)
                    instance = FindAnyObjectByType<IslandAudioDirector>();
                if (instance == null)
                    instance = new GameObject("Last Landfall | Audio Director").AddComponent<IslandAudioDirector>();
                return instance;
            }
        }

        public float MusicVolume { get; private set; }
        public float EnvironmentVolume { get; private set; }
        public bool IsGameplay => gameplay;
        public IslandWeatherType Weather { get; private set; }
        public AudioClip CurrentMusic => music != null ? music.CurrentClip : null;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap() { _ = Instance; }

        private void Awake()
        {
            if (instance != null && instance != this) { Destroy(gameObject); return; }
            instance = this;
            DontDestroyOnLoad(gameObject);
            MusicVolume = Mathf.Clamp01(PlayerPrefs.GetFloat(MusicVolumeKey, DefaultMusicVolume));
            EnvironmentVolume = Mathf.Clamp01(PlayerPrefs.GetFloat(EnvironmentVolumeKey, DefaultEnvironmentVolume));
            music = new CrossfadePair(CreateSource("Music A", 64), CreateSource("Music B", 64));
            ambience = new CrossfadePair(CreateSource("Weather A", 144), CreateSource("Weather B", 144));
            ocean = CreateSource("Coastal surf", 160);
            thunder = CreateSource("Distant thunder", 96);
            menuMusic = Load("Music/Menu_LastLight");
            string[] tracks = { "Game_01_AfterTheFlood", "Game_02_QuietRidge",
                "Game_03_SalvageTide", "Game_04_NewHorizon" };
            for (int i = 0; i < tracks.Length; i++) gameplayMusic[i] = Load("Music/" + tracks[i]);
            string[] beds = { "Clear", "Overcast", "Rain", "Wind", "Thunderstorm" };
            for (int i = 0; i < beds.Length; i++) weatherClips[i] = Load("Weather/Ambience_" + beds[i]);
            for (int i = 0; i < thunderClips.Length; i++)
                thunderClips[i] = Load("Weather/Thunder_" + (i + 1).ToString("00"));
            ocean.clip = Load("Weather/Ocean_Shore");
            ocean.loop = true;
            ocean.volume = 0;
            if (ocean.clip != null) ocean.Play();
            SetWeather(IslandWeatherType.Clear, 0.5f);
            SetGameplay(false);
            EnsureListener();
        }

        private static AudioClip Load(string path)
        {
            AudioClip clip = Resources.Load<AudioClip>("Audio/" + path);
            if (clip == null) Debug.LogWarning("Missing Last Landfall audio: Resources/Audio/" + path);
            return clip;
        }

        private AudioSource CreateSource(string name, int priority)
        {
            var child = new GameObject("Audio | " + name);
            child.transform.SetParent(transform, false);
            AudioSource source = child.AddComponent<AudioSource>();
            source.playOnAwake = false;
            source.spatialBlend = 0f;
            source.dopplerLevel = 0f;
            source.priority = priority;
            source.ignoreListenerPause = true;
            source.volume = 0f;
            return source;
        }

        public void SetGameplay(bool inGameplay)
        {
            if (contextInitialized && gameplay == inGameplay) return;
            contextInitialized = true;
            gameplay = inGameplay;
            paused = false;
            pendingThunderAt = -1f;
            if (gameplay) PlayNextGameplayTrack();
            else
            {
                thunder.Stop();
                music.Play(menuMusic, true, MusicFadeSeconds);
            }
        }

        public void SetPaused(bool value) { paused = value; }

        public void SetMixVolumes(float score, float environment)
        {
            MusicVolume = Mathf.Clamp01(score);
            EnvironmentVolume = Mathf.Clamp01(environment);
            PlayerPrefs.SetFloat(MusicVolumeKey, MusicVolume);
            PlayerPrefs.SetFloat(EnvironmentVolumeKey, EnvironmentVolume);
        }

        private void PlayNextGameplayTrack()
        {
            if (bagCursor >= shuffleBag.Count)
            {
                shuffleBag.Clear();
                for (int i = 0; i < gameplayMusic.Length; i++)
                    if (gameplayMusic[i] != null) shuffleBag.Add(i);
                for (int i = shuffleBag.Count - 1; i > 0; i--)
                {
                    int j = random.Next(i + 1);
                    int value = shuffleBag[i]; shuffleBag[i] = shuffleBag[j]; shuffleBag[j] = value;
                }
                if (shuffleBag.Count > 1 && shuffleBag[0] == lastTrack)
                { int value = shuffleBag[0]; shuffleBag[0] = shuffleBag[1]; shuffleBag[1] = value; }
                bagCursor = 0;
            }
            if (shuffleBag.Count == 0) return;
            lastTrack = shuffleBag[bagCursor++];
            AudioClip clip = gameplayMusic[lastTrack];
            music.Play(clip, false, MusicFadeSeconds);
            nextTrackAt = AudioSettings.dspTime + Mathf.Max(1f, clip.length - MusicFadeSeconds);
        }

        private void Update()
        {
            float delta = Time.unscaledDeltaTime;
            if (Time.unscaledTime >= nextBindingCheck)
            {
                nextBindingCheck = Time.unscaledTime + 1f;
                EnsureListener();
                if (observedWeather == null)
                {
                    var candidate = FindAnyObjectByType<IslandWeatherSystem>();
                    if (candidate != null) AttachWeather(candidate);
                }
            }
            if (gameplay && !music.IsFading && AudioSettings.dspTime >= nextTrackAt)
                PlayNextGameplayTrack();
            float pauseScore = paused ? 0.72f : 1f;
            float pauseEnvironment = paused ? 0.45f : 1f;
            music.Tick(delta, MusicVolume * 0.75f * pauseScore);
            weatherStrength = Mathf.MoveTowards(weatherStrength, WeatherGain(Weather), delta * 0.12f);
            gameplayAmbienceGain = Mathf.MoveTowards(gameplayAmbienceGain, gameplay ? 1f : 0f, delta * 0.35f);
            float weatherGain = EnvironmentVolume * weatherStrength * gameplayAmbienceGain * pauseEnvironment;
            ambience.Tick(delta, weatherGain);
            float oceanTarget = gameplay ? 0.45f * pauseEnvironment : 0.16f;
            oceanLevel = Mathf.MoveTowards(oceanLevel, oceanTarget, delta * 0.18f);
            ocean.volume = EnvironmentVolume * oceanLevel;
            thunder.volume = EnvironmentVolume * (paused ? 0.30f : 0.62f) * (gameplay ? 1f : 0f);
            if (pendingThunderAt >= 0f && Time.unscaledTime >= pendingThunderAt)
            {
                pendingThunderAt = -1f;
                if (gameplay && Weather == IslandWeatherType.Thunderstorm)
                {
                    AudioClip clip = thunderClips[random.Next(thunderClips.Length)];
                    if (clip != null)
                    {
                        thunder.PlayOneShot(clip);
                    }
                }
            }
        }

        private static float WeatherGain(IslandWeatherType type)
        {
            switch (type)
            {
                case IslandWeatherType.Overcast: return 0.55f;
                case IslandWeatherType.Rain: return 0.75f;
                case IslandWeatherType.Wind: return 0.78f;
                case IslandWeatherType.Thunderstorm: return 0.85f;
                default: return 0.35f;
            }
        }

        public void AttachWeather(IslandWeatherSystem system)
        {
            if (observedWeather == system) return;
            if (observedWeather != null)
            {
                observedWeather.WeatherChanged -= SetWeather;
                observedWeather.LightningStarted -= ScheduleThunder;
            }
            observedWeather = system;
            if (observedWeather == null) return;
            observedWeather.WeatherChanged += SetWeather;
            observedWeather.LightningStarted += ScheduleThunder;
            SetWeather(observedWeather.CurrentWeather, WeatherFadeSeconds);
        }

        private void SetWeather(IslandWeatherType type, float blendSeconds)
        {
            Weather = type;
            pendingThunderAt = -1f;
            ambience.Play(weatherClips[Mathf.Clamp((int)type, 0, weatherClips.Length - 1)],
                true, Mathf.Max(WeatherFadeSeconds, blendSeconds));
        }

        private void ScheduleThunder()
        {
            if (gameplay && Weather == IslandWeatherType.Thunderstorm)
                pendingThunderAt = Time.unscaledTime + 2.1f + (float)random.NextDouble() * 2.3f;
        }

        private static void EnsureListener()
        {
            foreach (AudioListener listener in FindObjectsByType<AudioListener>(FindObjectsInactive.Exclude))
                if (listener.enabled) return;
            Camera camera = Camera.main;
            if (camera == null) return;
            AudioListener existing = camera.GetComponent<AudioListener>();
            if (existing != null) existing.enabled = true;
            else camera.gameObject.AddComponent<AudioListener>();
        }

        private void OnDestroy()
        {
            if (instance != this) return;
            if (observedWeather != null)
            {
                observedWeather.WeatherChanged -= SetWeather;
                observedWeather.LightningStarted -= ScheduleThunder;
            }
            instance = null;
        }

        private sealed class CrossfadePair
        {
            private readonly AudioSource[] sources;
            private readonly float[] weights = new float[2];
            private int current, previous;
            private float elapsed, duration, previousWeight;
            public bool IsFading { get; private set; }
            public AudioClip CurrentClip => sources[current].clip;
            public CrossfadePair(AudioSource a, AudioSource b) { sources = new[] { a, b }; }

            public void Play(AudioClip clip, bool loop, float seconds)
            {
                if (clip == null || (CurrentClip == clip && sources[current].isPlaying)) return;
                previous = weights[0] >= weights[1] ? 0 : 1;
                current = 1 - previous;
                previousWeight = weights[previous];
                sources[current].Stop();
                sources[current].clip = clip;
                sources[current].loop = loop;
                sources[current].volume = 0;
                sources[current].Play();
                weights[current] = 0;
                elapsed = 0;
                duration = Mathf.Max(.05f, seconds);
                IsFading = true;
            }

            public void Tick(float delta, float volume)
            {
                if (IsFading)
                {
                    elapsed += delta;
                    float blend = Mathf.Clamp01(elapsed / duration);
                    weights[previous] = previousWeight * Mathf.Cos(blend * Mathf.PI * .5f);
                    weights[current] = Mathf.Sin(blend * Mathf.PI * .5f);
                    if (blend >= 1f)
                    {
                        sources[previous].Stop();
                        weights[previous] = 0f;
                        weights[current] = 1f;
                        IsFading = false;
                    }
                }
                sources[0].volume = weights[0] * volume;
                sources[1].volume = weights[1] * volume;
            }
        }
    }
}
