"""Short listening reels; these files are not used by the runtime playlist."""
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work/audio_tools"))
import numpy as np
from scipy.io import wavfile
import pyloudnorm as pyln
import imageio_ffmpeg
SR = 32000
OUT = ROOT / "work/audio_previews"
ASSETS = ROOT / "Assets/LastLandfall/Resources/Audio"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def decode(path):
    result = subprocess.run([FFMPEG, "-v", "error", "-i", str(path), "-f", "f32le",
                             "-ar", str(SR), "-ac", "2", "pipe:1"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return np.frombuffer(result.stdout, "<f4").reshape(-1, 2).copy()

def join(parts, fade):
    result = parts[0]
    count = int(fade * SR)
    phase = np.linspace(0, np.pi / 2, count)[:, None]
    for part in parts[1:]:
        seam = result[-count:] * np.cos(phase) + part[:count] * np.sin(phase)
        result = np.concatenate((result[:-count], seam, part[count:]))
    return result

def write(name, data, loudness=-23):
    data *= 10 ** ((loudness - pyln.Meter(SR).integrated_loudness(data)) / 20)
    data *= min(1, .82 / max(float(np.abs(data).max()), 1e-6))
    fade = np.linspace(0, 1, SR)[:, None]
    data[:SR] *= fade
    data[-SR:] *= fade[::-1]
    wav = OUT / (name + ".wav")
    wavfile.write(wav, SR, np.round(data * 32767).astype(np.int16))
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(wav),
                    "-c:a", "libmp3lame", "-b:a", "160k", str(OUT / (name + ".mp3"))],
                   check=True, stderr=subprocess.PIPE)

OUT.mkdir(parents=True, exist_ok=True)
tracks = ["Game_01_AfterTheFlood", "Game_02_QuietRidge", "Game_03_SalvageTide", "Game_04_NewHorizon"]
music_parts = [decode(ASSETS / "Music" / (name + ".ogg"))[30*SR:45*SR] for name in tracks]
write("Gameplay_Rotation_Preview", join(music_parts, 1.5))
sea = decode(ASSETS / "Weather/Ocean_Shore.ogg")
beds = []
for weather, duration, gain in [("Clear", 5, .35), ("Overcast", 5, .55), ("Rain", 7, .75),
                                ("Wind", 6, .78), ("Thunderstorm", 11, .85)]:
    data = decode(ASSETS / "Weather" / ("Ambience_" + weather + ".ogg"))[:duration*SR] * gain
    data += sea[:len(data)] * .45
    if weather == "Thunderstorm":
        thunder = decode(ASSETS / "Weather/Thunder_01.ogg")
        start = int(2.2 * SR)
        data[start:start+len(thunder)] += thunder[:len(data)-start] * .62
    beds.append(data)
write("Weather_Transitions_Preview", join(beds, 1), -25)
for wav in OUT.glob("*_Preview.wav"):
    target = wav.with_suffix(".mp3")
    if not target.exists() or target.stat().st_mtime < wav.stat().st_mtime:
        subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(wav),
                        "-c:a", "libmp3lame", "-b:a", "160k", str(target)],
                       check=True, stderr=subprocess.PIPE)
print("LISTENING_PREVIEWS_READY", OUT)
