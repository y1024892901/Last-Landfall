"""Generate seamless spectral slope data, not tiled painted wave highlights."""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Assets/LastLandfall/Resources/Textures/Environment"
OUT.mkdir(parents=True, exist_ok=True)
size = 512
kx, ky = np.meshgrid(np.fft.fftfreq(size), np.fft.fftfreq(size))
radius = np.sqrt(kx * kx + ky * ky) * size
angle = np.arctan2(ky, kx)
for name, seed, direction in (("OceanSlopeA", 8192, .31), ("OceanSlopeB", 16384, 2.13)):
    rng = np.random.default_rng(seed)
    spectrum = np.fft.fft2(rng.standard_normal((size, size)))
    band = (1 - np.exp(-(radius / 7) ** 4)) * np.exp(-(radius / 76) ** 3)
    spreading = .30 + .70 * np.cos(angle - direction) ** 4
    spectrum *= band * spreading / np.maximum(radius, 1) ** 1.65
    dx = np.fft.ifft2(spectrum * (2j * np.pi * kx)).real
    dy = np.fft.ifft2(spectrum * (2j * np.pi * ky)).real
    scale = max(np.std(dx), np.std(dy)) / .255
    slopes = np.stack((dx / scale, dy / scale), axis=-1)
    assert np.isfinite(slopes).all()
    encoded = np.zeros((size, size, 3), np.uint8)
    encoded[:, :, :2] = np.round(np.clip(slopes * .5 + .5, 0, 1) * 255).astype(np.uint8)
    encoded[:, :, 2] = 128
    Image.fromarray(encoded).save(OUT / (name + ".png"))
    print(name, "512x512, analytic FFT slopes, independent spectrum/phase")
