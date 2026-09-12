# Engineering Log
## Hypothesis

**Theme**

scene is compressed differently png and jpg which reveal different effects when applying DA3 onto it. Question: what is the cause? Supposedly, the scenes are "identical" in the original scene and frame count. Nuance: what are some technical differences in the compression technique that can lead to this, is it just lossy vs lossless?

Consider: shape, distribution of the differences.

Used claude to confirm the frame sets are identical: sandbox over the framesets found 300x300 dist matrix. 

Apparently, mac zipping has unique tendencies that I have to undo with mACOSX. In this same step, I verified that the scenes came from the same scene by checking the size being both 300. 

**Test 1**

Inspect the components of the frames for being identical through Pillow gray lvl 3 core components:
- gray lvl: checks whether the frames are the same
- minimum lvl: checks the arrays for the smallest difference, identify the frame counts from each of png and jpg to see if it matches. If so, the frame is positioned in the same way
- Progression: check the rate of change in gray lvl to verify the two compressions move in about the same manner

Compile into Json for inspection

### Test 1 — Frame identity and motion profile

| Measure | PNG | JPG | Reading |
|---|---|---|---|
| Frame count | 300 | 300 | Same count |
| Nearest-neighbour matches on diagonal | 300 / 300 | — | Every PNG's closest JPG is its own index |
| Offset histogram | {0: 300} | — | No shifted, dropped, or duplicated frames |
| Mean distance to matched JPG | 0.093 | — | Under a tenth of a gray level |
| Mean distance to runner-up JPG | 7.73 | — | Next-best is ~83× farther; match is unambiguous |
| Motion-profile correlation | 0.99999 | | Identical temporal structure |
| Near-static consecutive pairs | 48 | 45 | JPEG rounding slightly separates near-duplicate frames |

Conclusion: same frames, same order. Ordering is ruled out as a cause.


