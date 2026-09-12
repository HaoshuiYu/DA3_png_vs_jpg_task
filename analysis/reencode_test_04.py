"""
rTests whether the only diff between jpg and png is the compression, would narrow possibilities of explanation into:
lossy compression or pixel level differences. 
Method: turn png into jpg then compare, rules out diff explanations
"""

import io, sys
from pathlib import Path
from PIL import Image, JpegImagePlugin

png = sorted(Path("data/frames_png").glob("*.png"))
jpg = sorted(Path("data/frames_jpg").glob("*.jpg"))

# read the recipe off the first JPG: grid, colour resolution
ref = Image.open(jpg[0]); ref.load()
qtables = ref.quantization
subsampling = JpegImagePlugin.get_sampling(ref)
print("recipe: subsampling", subsampling, "| luma grid starts", qtables[0][:8])

# compress each PNG with that recipe, compare bytes to the real JPG
matches = 0
for p, j in zip(png, jpg):
    buf = io.BytesIO()
    Image.open(p).convert("RGB").save(buf, "JPEG", qtables=qtables, subsampling=subsampling)
    matches += buf.getvalue() == j.read_bytes()

print(f"byte-identical after re-encoding: {matches}/{len(png)}")