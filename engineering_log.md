# Engineering Log
## Hypothesis

**Theme**

scene is compressed differently png and jpg which reveal different effects when applying DA3 onto it. Question: what is the cause? Supposedly, the scenes are "identical" in the original scene and frame count. Nuance: what are some technical differences in the compression technique that can lead to this, is it just lossy vs lossless?

Consider: shape, distribution of the differences.

Used claude to confirm the frame sets are identical: sandbox over the framesets found 300x300 dist matrix. 

Apparently, mac zipping has unique tendencies that I have to undo with mACOSX. In this same step, I verified that the scenes came from the same scene by checking the size being both 300. 

### Graph Interpretation:
From the curve provided: 
TODO: consider the curves were aligned via a transform onto another, so their practical difference is likely larger, could just be a positional displacement but could also be greater than that. Unsure exactly what to do with this information.

**Interpretation**
This is on camera extrinsics information because it's missing a yth dimension, so it cannot be teh depth map DA3 outputs since this graph would not be useful that way at all.
- the two curves are heavily correlated but differ locally: it's very strange because PNG is lossless and jpg is lossy, but PNG has more variance somehow. So, having more information made the estimation worse which is counterintuitive. This should be something to inspect heavily. 
- jpg is much smoother past 0 on X
- heavy cluster below 0 for both curves

### Test 1: Frame identity and motion profile

| Measure | PNG | JPG | Reading |
|---|---|---|---|
| Frame count | 300 | 300 | Same count |
| Nearest-neighbour matches on diagonal | 300 / 300 | — | Every PNG's closest JPG is its own index |
| Offset histogram | {0: 300} | — | No shifted, dropped, or duplicated frames |
| Mean distance to matched JPG | 0.093 | — | Under a tenth of a gray level |
| Mean distance to runner-up JPG | 7.73 | — | Next-best is ~83× farther; match is unambiguous |
| Motion-profile correlation | 0.99999 | | Identical temporal structure |
| Near-static consecutive pairs | 48 | 45 | JPEG rounding slightly separates near-duplicate frames |

**methodology**

Inspect the components of the frames for being identical through Pillow gray lvl 3 core components:
- gray lvl: checks whether the frames are the same
- minimum lvl: checks the arrays for the smallest difference, identify the frame counts from each of png and jpg to see if it matches. If so, the frame is positioned in the same way
- Progression: check the rate of change in gray lvl to verify the two compressions move in about the same manner

Compile into Json for inspection

**conclusion** frames, arrangement, progression of scenes identical. png vs jpg difference not attributable here.

### Test 2: metadata and general information

| Measure | PNG | JPG | Reading |
|---|---|---|---|
| Unique attribute combinations | 1 (300 files) | 1 (300 files) | Every file within each set is homogeneous; no anomalous frame |
| Format (from file signature) | PNG | JPEG | File contents match extension |
| Dimensions | 1024 × 576 | 1024 × 576 | Same pixel grid; no resize or crop difference |
| Colour mode | RGB | RGB | Three 8-bit channels, no alpha in either set |
| Ancillary metadata keys | none | jfif, jfif_version, jfif_density, jfif_unit | PNG carries nothing; JPG carries only JFIF container boilerplate

My guess was that the metadata would be identical to begin with, but the verification step wasn't too tedious so I thought we'd just run it. 

### Test 3: Internal inspection file conversion 

The objective here is to outline exactly where and the internal logic behind when DA3 converts the frames into values and the subsequent averaging and transformations that may compound any noise present. 

**methodology** 
I applied DA3's method to claude and requested to locate core components that are relevant to inspect logic myself:
- the conversion of frames into array 
- averaging: but I realized after taht averaging would compound noise, the origin and "root cause" which is the intention of this project would not originate from averaging
- claude suggested the chunking logic, but I think it's trivial because the frames have identical dimensions, specifications, etc. which makes chunking likely largely identical, but TODO: inspect chunking logic in case

**decoder inspection**
DA3 processes every scene received through Image.open(path).convert("RGB"), but Pillow internally is what converts the frames to arrays. Pillow differentiates in method:
- jpg is unpack compression, run discrete cos transform, restore half resolution RGB and then turn into RGB proper
- png is just decompress (zlib inflate), then undo the per-row prediction filter. No transform, no rounding; output is bit-identical to what was encoded.

### Test 4: reencoding png into jpg
The objective is to rule out different explanations by turning the png into a jpg to inspect core features of the frames. 

### Test 4: re-encode test

| Measure | Result | Reading |
|---|---|---|
| Recipe read from JPG header | 4:2:0 colour, grid = q95 | Encoder settings recovered from the file itself |
| PNG compressed with that recipe == given JPG | 300/300 bytes | JPGs are exactly the PNGs compressed once; nothing else happened |

While it fulfills partially repetitive functions, the central focus is to narow the explanations to be exclusively driven by the Pillow compression at 95. This means there's only two explanations that remain, it's either caused by the process of lossy compression which permanently alters the pixels, or it's the formatting of the jpg vs png such that the decoder evaluates the two differently.
 

