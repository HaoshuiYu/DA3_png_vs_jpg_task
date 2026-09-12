"""
02_metadata.py — What is wrapped around the pixels?
inspects frame metadata: format, dimensions, color mode, metadata keys present, EXIF presence.
"""
from PIL import Image
from pathlib import Path
from collections import Counter

for d in ["data/frames_png", "data/frames_jpg"]:
    c = Counter()
    for p in sorted(Path(d).iterdir()):
        im = Image.open(p)
        c[(im.format, im.size, im.mode, tuple(sorted(im.info.keys())), bool(im.getexif()))] += 1
    print(d)
    for key, n in c.items():
        print("  ", n, "files:", key)