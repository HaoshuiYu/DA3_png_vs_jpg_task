"""
make a copy of the jpg such that I can turn it into png and inspect the pixels vs decoder confound. Deposite in separate folder
"""
import numpy as np
from pathlib import Path
from PIL import Image

png = sorted(Path("data/frames_png").glob("*.png"))
jpg = sorted(Path("data/frames_jpg").glob("*.jpg"))

out_bar = Path("data/frames_jpgbar"); out_bar.mkdir(exist_ok=True)
out_noise = Path("data/frames_png_noise"); out_noise.mkdir(exist_ok=True)

rng = np.random.default_rng(0)

for p, j in zip(png, jpg):
    Image.open(j).convert("RGB").save(out_bar / p.name)
    arr = np.asarray(Image.open(p).convert("RGB")).astype(np.int16)
    arr = np.clip(arr + rng.integers(-1, 2, arr.shape), 0, 255).astype(np.uint8)
    Image.fromarray(arr).save(out_noise / p.name)

print("jpgbar:", len(list(out_bar.glob("*.png"))), "| noise:", len(list(out_noise.glob("*.png"))))