"""Original Last Landfall score and synthesized weather beds (no sampled music).

Python dependencies: numpy scipy pyloudnorm imageio-ffmpeg.
Run from the repository root. Editable MIDI, OGG masters and mix QA are emitted.
"""
from pathlib import Path
import hashlib
import json
import math
import struct
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work/audio_tools"))
import numpy as np
from scipy import signal
from scipy.io import wavfile
import pyloudnorm as pyln
import imageio_ffmpeg

SR = 32000
OUT = ROOT / "Assets/LastLandfall/Resources/Audio"
SOURCE = ROOT / "Assets/LastLandfall/Art/Source/Audio"
PREVIEWS = ROOT / "work/audio_previews"
RNG = np.random.default_rng(481516)
RECORDS = []

def ensure_metadata():
    for path in [OUT, OUT / "Music", OUT / "Weather", SOURCE,
                 OUT / "AudioManifest.json", *SOURCE.glob("*.mid")]:
        target = Path(str(path) + ".meta")
        if target.exists() or not path.exists():
            continue
        guid = uuid.uuid5(uuid.NAMESPACE_URL, "last-landfall-audio/" + path.relative_to(ROOT).as_posix()).hex
        importer = "DefaultImporter" if path.is_dir() or path.suffix == ".mid" else "TextScriptImporter"
        target.write_text("fileFormatVersion: 2\nguid: " + guid + "\n" +
                          ("folderAsset: yes\n" if path.is_dir() else "") +
                          importer + ":\n  externalObjects: {}\n  userData:\n"
                          "  assetBundleName:\n  assetBundleVariant:\n", encoding="utf-8")


def meta(path, music=False, refresh=False):
    target = Path(str(path) + ".meta")
    if target.exists() and not refresh:
        return
    guid = uuid.uuid5(uuid.NAMESPACE_URL, "last-landfall-audio/" + path.relative_to(ROOT).as_posix()).hex
    target.write_text(
        f"fileFormatVersion: 2\nguid: {guid}\nAudioImporter:\n"
        "  externalObjects: {}\n  serializedVersion: 7\n  defaultSettings:\n"
        f"    serializedVersion: 2\n    loadType: {2 if music else 1}\n"
        "    sampleRateSetting: 0\n    sampleRateOverride: 32000\n"
        "    compressionFormat: 1\n    quality: 0.7\n    conversionMode: 0\n    preloadAudioData: 0\n"
        "  platformSettingOverrides: {}\n  forceToMono: 0\n  normalize: 0\n"
        "  loadInBackground: 1\n  ambisonic: 0\n"
        "  3D: 0\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n",
        encoding="utf-8")


def hz(note):
    return 440.0 * 2.0 ** ((note - 69.0) / 12.0)


def mix_at(mix, mono, seconds, gain=1.0, pan=0.0):
    start = int(seconds * SR) % len(mix)
    gains = np.array([math.cos((pan + 1) * math.pi / 4),
                      math.sin((pan + 1) * math.pi / 4)], np.float32) * gain
    data = mono[:, None] * gains[None, :]
    first = min(len(data), len(mix) - start)
    mix[start:start + first] += data[:first]
    remaining = len(data) - first
    if remaining:
        mix[:remaining] += data[first:]


def tone(note, duration, kind):
    t = np.arange(int(duration * SR), dtype=np.float32) / SR
    f = hz(note)
    result = np.zeros(len(t), np.float32)
    if kind == "pad":
        for harmonic, strength in ((1, 1), (2, .19), (3, .075), (4, .035)):
            for detune in (-.0014, .0012):
                phase = 2 * np.pi * f * harmonic * (1 + detune) * t
                phase += .06 * np.sin(2 * np.pi * .27 * t)
                result += np.sin(phase) * strength * .5
        envelope = np.minimum(t / 1.7, 1) * np.minimum((duration - t) / 2.0, 1)
        result *= np.maximum(envelope, 0) * (.94 + .06 * np.sin(t * .77))
    elif kind == "bass":
        result = np.sin(2 * np.pi * f * t) + .12 * np.sin(4 * np.pi * f * t)
        result *= np.minimum(t / .08, 1) * np.exp(-t / 3.6)
    elif kind == "glass":
        for ratio, strength, decay in ((1, 1, 3.5), (2.005, .22, 2.4), (3.992, .08, 1.5)):
            result += np.sin(2 * np.pi * f * ratio * t) * strength * np.exp(-t / decay)
        result *= np.minimum(t / .018, 1)
    else:
        pluck = kind == "pluck"
        for harmonic in range(1, 11 if not pluck else 9):
            stretch = math.sqrt(1 + .000025 * harmonic * harmonic)
            strength = (1.0 / harmonic ** (1.65 if pluck else 1.9))
            if pluck:
                strength *= abs(math.sin(harmonic * math.pi * .24))
            decay = (2.8 if not pluck else 1.65) / (1 + harmonic * .32)
            result += np.sin(2 * np.pi * f * harmonic * stretch * t) * strength * np.exp(-t / decay)
        result *= 1 - np.exp(-t / (.008 if pluck else .017))
        # A subtle resonant body, without a harsh click or bright attack.
        result += .018 * np.sin(2 * np.pi * f * 2.001 * t) * np.exp(-t / 1.2)
    result *= np.minimum(np.maximum((duration - t) / .14, 0), 1)
    return result.astype(np.float32)


def reverb(mix, seed, wet=.26):
    rng = np.random.default_rng(seed)
    length = int(3.8 * SR)
    for channel in range(2):
        impulse = np.zeros(length, np.float32)
        positions = rng.integers(int(.055 * SR), length, 1100)
        impulse[positions] = (rng.uniform(-1, 1, len(positions)) *
                              np.exp(-positions / SR / .75)).astype(np.float32)
        impulse /= max(np.linalg.norm(impulse), 1e-5)
        tail = signal.fftconvolve(mix[:, channel], impulse, mode="full")
        folded = tail[:len(mix)].copy()
        folded[:len(tail) - len(mix)] += tail[len(mix):]
        mix[:, channel] += folded * wet
    return mix


def write_asset(relative, label, mix, target_lufs, looping, extra=None):
    mix = np.nan_to_num(mix).astype(np.float32)
    highpass = signal.butter(2, 32, "highpass", fs=SR, output="sos")
    prefix = min(len(mix), SR)
    mix = signal.sosfilt(highpass, np.concatenate((mix[-prefix:], mix)), axis=0)[prefix:].astype(np.float32)
    # Broad mastering EQ, not a bright or fatiguing high-frequency wash.
    lowpass = signal.butter(2, 10000, "lowpass", fs=SR, output="sos")
    mix = signal.sosfilt(lowpass, np.concatenate((mix[-prefix:], mix)), axis=0)[prefix:].astype(np.float32)
    meter = pyln.Meter(SR)
    before = meter.integrated_loudness(mix)
    mix *= 10 ** ((target_lufs - before) / 20)
    true_peak = float(np.max(np.abs(signal.resample_poly(mix, 4, 1, axis=0))))
    if true_peak > .84:
        mix *= .84 / true_peak
    loudness = float(meter.integrated_loudness(mix))
    peak = float(np.max(np.abs(mix)))
    assert np.isfinite(mix).all() and peak < .85
    path = OUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "pipe:0",
                    "-c:a", "libvorbis", "-q:a", "5", str(path)],
                   input=mix.astype("<f4").tobytes(), check=True, stderr=subprocess.PIPE)
    meta(path, relative.startswith("Music/"))
    record = dict(file=relative, title=label, duration_seconds=round(len(mix) / SR, 3),
                  sample_rate=SR, channels=2, integrated_lufs=round(loudness, 2),
                  sample_peak_dbfs=round(20 * math.log10(max(peak, 1e-8)), 2),
                  loop=looping, provenance="Original composition / procedural synthesis; no external samples")
    record.update(extra or {})
    RECORDS.append(record)
    print(json.dumps(record, ensure_ascii=False), flush=True)
    return mix


def vlq(value):
    result = [value & 127]
    while value >> 7:
        value >>= 7
        result.insert(0, (value & 127) | 128)
    return bytes(result)


def write_midi(name, bpm, events):
    # Type 0 MIDI remains editable in any DAW. Channels map to piano, strings,
    # nylon pluck, vibraphone and soft bass; rendering uses our own synth voices.
    body = b"\x00\xff\x51\x03" + int(60_000_000 / bpm).to_bytes(3, "big")
    for channel, program in enumerate((0, 48, 24, 11, 32)):
        body += b"\x00" + bytes((0xc0 + channel, program))
    sequence = []
    for beat, duration, channel, note, velocity in events:
        sequence += [(int(beat * 480), bytes((0x90 + channel, note, velocity))),
                     (int((beat + duration) * 480), bytes((0x80 + channel, note, 0)))]
    previous = 0
    for tick, data in sorted(sequence, key=lambda item: item[0]):
        body += vlq(tick - previous) + data
        previous = tick
    body += b"\x00\xff\x2f\x00"
    path = SOURCE / (name + ".mid")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480) +
                     b"MTrk" + struct.pack(">I", len(body)) + body)


def compose(name, title, bpm, bars, tonic, scale, progression, seed, palette):
    beat_seconds = 60 / bpm
    beats = bars * 4
    mix = np.zeros((round(beats * beat_seconds * SR), 2), np.float32)
    rng = np.random.default_rng(seed)
    events = []
    cache = {}
    channel_map = dict(piano=0, pad=1, pluck=2, glass=3, bass=4)

    def scale_note(degree, octave=0):
        return tonic + scale[degree % len(scale)] + 12 * (degree // len(scale) + octave)

    def play(kind, note, beat, length, gain, pan=0):
        duration = length * beat_seconds
        key = (kind, note, round(duration, 3))
        if key not in cache:
            cache[key] = tone(note, duration, kind)
        mix_at(mix, cache[key], beat * beat_seconds, gain, pan)
        events.append((beat, length, channel_map[kind], note, max(20, min(105, int(gain * 230)))))

    # Slow two-bar harmonic breathing, with open ninths and no bombastic cadence.
    for block in range(math.ceil(bars / 2)):
        degree = progression[block % len(progression)]
        for voice, offset in enumerate((0, 2, 4, 8)):
            note = scale_note(degree + offset, 1)
            play("pad", note, block * 8, 10, .048 if voice < 3 else .024,
                 (-.52, .24, .50, -.20)[voice])
        play("bass", scale_note(degree, -1), block * 8 + .06, 7.5, .14, 0)

    motif = (0, 2, 4, 5, 4, 2, 1, 0)
    motif_times = (0, 2.5, 5, 8, 11, 15, 19, 24)
    for phrase in range(math.ceil(bars / 8)):
        for i, degree in enumerate(motif):
            beat = phrase * 32 + motif_times[i] + .035
            if beat >= beats - 1:
                continue
            variation = 1 if palette == "horizon" and phrase % 2 else 0
            note = scale_note(degree + variation, 2)
            play("piano" if palette != "ridge" else "glass", note, beat,
                 4.8 if palette != "ridge" else 6, .13 + .035 * rng.random(),
                 -.18 + .36 * rng.random())

    for bar in range(bars):
        degree = progression[(bar // 2) % len(progression)]
        # Sparse introduction, followed by a quiet, humanized broken-chord bed.
        offsets = (0, 2.5) if bar < 4 else (0, 1.5, 3.0)
        for index, offset in enumerate(offsets):
            note = scale_note(degree + (0, 4, 2)[index], 1)
            instrument = "pluck" if palette in ("salvage", "horizon") else "piano"
            play(instrument, note, bar * 4 + offset + rng.uniform(.01, .035),
                 3.4, rng.uniform(.075, .12), -.34 if index % 2 else .32)
        if palette in ("dawn", "horizon") and bar % 2 == 1:
            play("pluck", scale_note(degree + 6, 1), bar * 4 + 2.1, 3,
                 .065, -.45)
        if bar % 8 == 4:
            play("glass", scale_note(degree + 4, 2), bar * 4 + .08, 7,
                 .035, .45)

    mix = reverb(mix, seed + 900, .30 if palette == "menu" else .25)
    write_midi(name, bpm, events)
    relative = "Music/" + name + ".ogg"
    mix = write_asset(relative, title, mix, -22 if palette == "menu" else -23, True,
                      dict(bpm=bpm, bars=bars, midi_source=name + ".mid"))
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    # Listen from the developed passage, not only the sparse intro.
    preview = mix[int(26 * SR):int(56 * SR)].copy()
    fade = np.linspace(0, 1, SR, dtype=np.float32)
    preview[:SR] *= fade[:, None]
    preview[-SR:] *= fade[::-1, None]
    wavfile.write(PREVIEWS / (name + "_Preview.wav"), SR,
                  np.round(np.clip(preview, -1, 1) * 32767).astype(np.int16))
    return relative


def periodic_noise(duration, low, high, rng):
    count = int(duration * SR)
    frequencies = np.fft.rfftfreq(count, 1 / SR)
    spectrum = rng.normal(size=len(frequencies)) + 1j * rng.normal(size=len(frequencies))
    gain = (1 - np.exp(-(frequencies / low) ** 4)) / np.sqrt(1 + (frequencies / high) ** 6)
    spectrum *= gain
    spectrum[0] = 0
    noise = np.fft.irfft(spectrum, n=count).astype(np.float32)
    return noise / max(float(np.std(noise)), 1e-6)


def weather_bed(name, title, duration, kind, seed):
    rng = np.random.default_rng(seed)
    t = np.arange(int(duration * SR), dtype=np.float32) / SR
    mix = np.zeros((len(t), 2), np.float32)
    for channel in range(2):
        broad = periodic_noise(duration, 160, 5200, rng)
        low = periodic_noise(duration, 45, 650, rng)
        swell = (.58 + .26 * np.sin(2 * np.pi * t * 5 / duration + channel * .18) +
                 .13 * np.sin(2 * np.pi * t * 9 / duration))
        gust = .55 + .24 * np.sin(2 * np.pi * t * 2 / duration + .4) + .15 * np.sin(2 * np.pi * t * 5 / duration)
        if kind == "ocean":
            mix[:, channel] = broad * np.maximum(swell, .08) ** 1.8 * .23 + low * swell * .17
        elif kind in ("clear", "overcast", "wind"):
            intensity = dict(clear=.12, overcast=.22, wind=.42)[kind]
            mix[:, channel] = low * gust * intensity + broad * gust * intensity * .23
            if kind == "wind":
                air = periodic_noise(duration, 480, 1900, rng)
                mix[:, channel] += air * np.maximum(gust - .35, 0) * .12
        else:
            hiss = periodic_noise(duration, 900, 8500, rng)
            mix[:, channel] = hiss * (.17 + .025 * np.sin(t * 2 * np.pi * 3 / duration))
            mix[:, channel] += broad * .07 + low * gust * (.15 if kind == "storm" else .04)
    if kind in ("rain", "storm"):
        for index in range(int(duration * 18)):
            length = rng.uniform(.008, .035)
            dt = np.arange(int(length * SR), dtype=np.float32) / SR
            drop = rng.normal(size=len(dt)).astype(np.float32) * np.exp(-dt / .0035)
            mix_at(mix, drop, rng.uniform(0, duration), rng.uniform(.012, .032), rng.uniform(-.9, .9))
    return write_asset("Weather/" + name + ".ogg", title, mix,
                       dict(ocean=-27, clear=-31, overcast=-29, wind=-27,
                            rain=-25, storm=-25)[kind], True)


def thunder(index):
    duration = 7.6 + index * .7
    rng = np.random.default_rng(7000 + index)
    mix = np.zeros((int(duration * SR), 2), np.float32)
    t = np.arange(len(mix), dtype=np.float32) / SR
    for channel in range(2):
        rumble = periodic_noise(duration, 38, 520, rng)
        body = periodic_noise(duration, 180, 1700, rng)
        onset = np.maximum(t - .14, 0)
        envelope = (1 - np.exp(-onset / .20)) * np.exp(-onset / 1.7)
        roll = (1 - np.exp(-onset / .8)) * np.exp(-onset / 2.0) * (
            .75 + .25 * np.sin(t * 5.5 + channel * .2))
        mix[:, channel] = rumble * (envelope + roll) + body * envelope * .22
    mix[-SR:] *= np.linspace(1, 0, SR, dtype=np.float32)[:, None]
    write_asset("Weather/Thunder_%02d.ogg" % index, "远雷回响 %d" % index,
                mix, -23, False)


def main():
    tracks = [
        ("Menu_LastLight", "潮线之外 · 首页主题", 58, 32, 50,
         (0, 2, 3, 5, 7, 9, 10), (0, 5, 3, 4, 0, 2, 5, 4), 101, "menu"),
        ("Game_01_AfterTheFlood", "余陆晨光", 68, 36, 50,
         (0, 2, 3, 5, 7, 9, 10), (0, 3, 5, 4, 0, 5, 2, 4), 201, "dawn"),
        ("Game_02_QuietRidge", "山脊微光", 64, 32, 43,
         (0, 2, 4, 5, 7, 9, 11), (0, 5, 3, 0, 4, 5, 3, 4), 202, "ridge"),
        ("Game_03_SalvageTide", "潮间拾遗", 60, 32, 45,
         (0, 2, 3, 5, 7, 8, 10), (0, 5, 3, 4, 0, 2, 5, 4), 203, "salvage"),
        ("Game_04_NewHorizon", "重建之岸", 70, 40, 41,
         (0, 2, 4, 6, 7, 9, 11), (0, 3, 5, 4, 0, 2, 3, 4), 204, "horizon"),
    ]
    for spec in tracks:
        compose(*spec)
    for spec in [
        ("Ocean_Shore", "远近潮汐 · 常驻海浪", 40, "ocean", 301),
        ("Ambience_Clear", "晴朗岸风", 32, "clear", 302),
        ("Ambience_Overcast", "低云岸风", 36, "overcast", 303),
        ("Ambience_Rain", "连绵雨幕", 40, "rain", 304),
        ("Ambience_Wind", "山脊阵风", 36, "wind", 305),
        ("Ambience_Thunderstorm", "风暴雨幕", 40, "storm", 306),
    ]:
        weather_bed(*spec)
    for index in range(1, 4):
        thunder(index)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "AudioManifest.json").write_text(json.dumps(
        dict(sample_rate=SR, assets=RECORDS, external_samples=False,
             music_and_weather_are_separate=True), ensure_ascii=False, indent=2), encoding="utf-8")
    ensure_metadata()
    print("AUDIO_GENERATION_COMPLETE", len(RECORDS), flush=True)


if __name__ == "__main__":
    main()
