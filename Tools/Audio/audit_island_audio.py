"""Validate the encoded assets Unity will import, rather than synthesis buffers."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work/audio_tools"))
import numpy as np
import pyloudnorm as pyln
import imageio_ffmpeg

audio = ROOT / "Assets/LastLandfall/Resources/Audio"
manifest = json.loads((audio / "AudioManifest.json").read_text(encoding="utf-8"))
report = []
hashes = set()
for entry in manifest["assets"]:
    path = audio / entry["file"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest not in hashes, "Duplicate asset: " + str(path)
    hashes.add(digest)
    decoded = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", str(path),
                              "-f", "f32le", "-ac", "2", "-ar", "32000", "pipe:1"],
                             check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    samples = np.frombuffer(decoded.stdout, dtype="<f4").reshape(-1, 2)
    assert np.isfinite(samples).all()
    peak = float(np.abs(samples).max())
    assert peak < .86, (entry["file"], "clipping", peak)
    duration = len(samples) / 32000
    assert abs(duration - entry["duration_seconds"]) < .03
    loudness = float(pyln.Meter(32000).integrated_loudness(samples))
    assert abs(loudness - entry["integrated_lufs"]) < .6
    row = dict(file=entry["file"], duration_seconds=round(duration, 3),
               decoded_lufs=round(loudness, 2), decoded_peak=round(peak, 4), sha256=digest)
    if entry["loop"]:
        jump = float(np.abs(samples[0] - samples[-1]).max())
        normal_change = float(np.quantile(np.abs(np.diff(samples, axis=0)), .99))
        assert jump < max(.01, normal_change * 2.0), (entry["file"], "loop seam", jump, normal_change)
        row["loop_boundary_jump"] = round(jump, 6)
    if entry["file"].startswith("Music/"):
        windows = samples[:len(samples) // 32000 * 32000].reshape(-1, 32000, 2)
        quietest = float(np.sqrt(np.mean(windows.astype(np.float64) ** 2, axis=(1, 2))).min())
        assert quietest > .001, (entry["file"], "silent passage")
        row["quietest_second_rms"] = round(quietest, 6)
    report.append(row)

assert len(report) == 14
output = ROOT / "work/audio_previews/Audio_QA.json"
output.write_text(json.dumps(dict(passed=True, checked_assets=len(report), assets=report),
                             ensure_ascii=False, indent=2), encoding="utf-8")
print("ENCODED_AUDIO_AUDIT_OK:", len(report), "assets; decode, loudness, peaks, loops and unique content.")
