#!/usr/bin/env python3
"""
01_identity.py — Are the two frame sets the same frames, in the same order?

Method:
  1. Load every frame from both folders with Pillow (DA3's decoder), convert to
     grayscale, downsample (default 8x -> 128x72) 
  2. Build the distance matrix D[i, j] = mean |PNG_i - JPG_j|.
  3. For each PNG i, nearest JPG = argmin_j D[i, j]. Identity means nearest == i.
  4. Motion profile per set: mean |frame_t - frame_{t-1}|; correlate the two.
  5. Report near-static consecutive pairs (motion below --static-thresh).
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

IMG_EXTS = {".png", ".jpg", ".jpeg"}


def list_frames(d: Path): # list arrangement of all images in order sorted via name
    fs = sorted(p for p in d.iterdir() if p.suffix.lower() in IMG_EXTS and not p.name.startswith("._"))
    if not fs:
        sys.exit(f"No image files found in {d}")
    return fs


def load_small(files, scale): # opens file with pillow grayscale
    arrs = []
    w, h = None, None
    for p in files:
        im = Image.open(p).convert("L")
        if w is None:
            w, h = im.size
        im = im.resize((w // scale, h // scale), Image.BOX)
        arrs.append(np.asarray(im, dtype=np.float32))
    return np.stack(arrs), (w, h)


def main(): 
    # paths for folders and scale by 8x
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--png", required=True, type=Path)
    ap.add_argument("--jpg", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--scale", type=int, default=8, help="downsample factor for comparison")
    ap.add_argument("--static-thresh", type=float, default=0.3, help="motion below this = near-static pair")
    ap.add_argument("--no-fig", action="store_true")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    # load downsampled frames in order and record count, size, file names, into report
    png_files = list_frames(args.png)
    jpg_files = list_frames(args.jpg)
    n_p, n_j = len(png_files), len(jpg_files)

    P, size_p = load_small(png_files, args.scale)
    J, size_j = load_small(jpg_files, args.scale)

    report = {
        "n_png": n_p, "n_jpg": n_j,
        "frame_size_png": size_p, "frame_size_jpg": size_j,
        "comparison_scale": args.scale,
        "first_png": png_files[0].name, "last_png": png_files[-1].name,
        "first_jpg": jpg_files[0].name, "last_jpg": jpg_files[-1].name,
    }

    # perform subtraction across png and jpg 300x300, gray lvl diff is applied with abs() to validate frame consistency
    Pf, Jf = P.reshape(n_p, -1), J.reshape(n_j, -1)
    D = np.zeros((n_p, n_j), dtype=np.float32)
    for i in range(n_p):
        D[i] = np.abs(Jf - Pf[i]).mean(axis=1)
    np.save(args.out / "identity_matrix.npy", D)

    # inspect farme alignment, find closest aligned gray lvl and atribute it to the frame count to see if it matches
    nearest = D.argmin(axis=1)
    offsets = nearest - np.arange(n_p)
    identity_matches = int((offsets == 0).sum())
    diag = np.diag(D) if n_p == n_j else np.array([D[i, i] for i in range(min(n_p, n_j))])
    second_best = np.sort(D, axis=1)[:, 1] if n_j > 1 else diag

    report["identity_matches"] = f"{identity_matches}/{n_p}"
    report["offset_histogram"] = {int(k): int(v) for k, v in zip(*np.unique(offsets, return_counts=True))}
    report["mismatched_png_indices"] = [int(i) for i in np.where(offsets != 0)[0][:50]]
    report["mean_distance_to_matched_jpg"] = float(diag.mean())
    report["mean_distance_to_second_best_jpg"] = float(second_best.mean())
    report["separation_ratio"] = float(second_best.mean() / max(diag.mean(), 1e-9))

    # rate of change of gray lvl to see if progression of frames match
    m_p = np.abs(np.diff(P, axis=0)).mean(axis=(1, 2))
    m_j = np.abs(np.diff(J, axis=0)).mean(axis=(1, 2))
    np.save(args.out / "motion_png.npy", m_p)
    np.save(args.out / "motion_jpg.npy", m_j)
    corr = float(np.corrcoef(m_p, m_j)[0, 1]) if n_p == n_j else None
    static_p = np.where(m_p < args.static_thresh)[0]
    static_j = np.where(m_j < args.static_thresh)[0]
    report["motion_profile"] = {
        "correlation_png_jpg": corr,
        "png": {"mean": float(m_p.mean()), "min": float(m_p.min()), "max": float(m_p.max()),
                "near_static_pairs": int(len(static_p)), "near_static_indices": [int(i) for i in static_p]},
        "jpg": {"mean": float(m_j.mean()), "min": float(m_j.min()), "max": float(m_j.max()),
                "near_static_pairs": int(len(static_j)), "near_static_indices": [int(i) for i in static_j]},
    }

    # stores json output ...
    (args.out / "identity_report.json").write_text(json.dumps(report, indent=2))

    if not args.no_fig:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
        ax[0].imshow(D, cmap="viridis")
        ax[0].set_title(f"mean |PNG_i - JPG_j| (identity {identity_matches}/{n_p})")
        ax[0].set_xlabel("JPG index"); ax[0].set_ylabel("PNG index")
        ax[1].plot(m_j, label="JPG", lw=1); ax[1].plot(m_p, "--", label="PNG", lw=1)
        ax[1].axhline(args.static_thresh, c="gray", ls=":", lw=0.8)
        ax[1].set_title(f"frame-to-frame motion (r = {corr:.3f})" if corr is not None else "frame-to-frame motion")
        ax[1].set_xlabel("frame"); ax[1].set_ylabel("mean |diff|"); ax[1].legend()
        plt.tight_layout(); plt.savefig(args.out / "identity_figure.png", dpi=110)

    print(json.dumps({k: report[k] for k in ("n_png", "n_jpg", "identity_matches", "offset_histogram",
                                             "mean_distance_to_matched_jpg", "mean_distance_to_second_best_jpg",
                                             "separation_ratio")}, indent=2))
    mp = report["motion_profile"]
    print(f"motion correlation: {mp['correlation_png_jpg']}")
    print(f"near-static pairs: PNG {mp['png']['near_static_pairs']}, JPG {mp['jpg']['near_static_pairs']}")


if __name__ == "__main__":
    main()