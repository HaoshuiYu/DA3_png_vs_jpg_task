"""
evaluate.py — Align the five trajectories to png_1 and compare them.

For each run:
  1. Load camera_poses.txt (300 lines x 16 values = 4x4 world-to-camera), get camera centres.
  2. Align to png_1 with Umeyama: Sim(3) (rotation+translation+scale) and SE(3) (scale fixed at 1).
  3. Report: ATE RMSE for both alignments, the fitted scale, and jitter (RMS of second difference).
  4. Per-frame position error after Sim(3) alignment.

Outputs: figures/overlay_aligned.png, figures/per_frame_error.png, runs/metrics.csv, and a
pairwise ATE table printed to the terminal.

Usage: python analysis/evaluate.py
"""
import csv
import numpy as np
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

RUNS = ["png_1", "png_2", "jpg_1", "jpgbar_1", "noise_1", "noise_2"]
REF = "png_1"
ROOT = Path("runs/out")
CHUNK_BOUNDARIES = [60, 120, 180, 240]
STATIC = [(0, 30), (80, 90), (150, 160), (190, 200), (225, 245)]  # from test 1 motion profile


def load_centres(path):
    M = np.loadtxt(path).reshape(-1, 4, 4)
    return M[:, :3, 3]          # C2W: camera position is the translation column


def umeyama(src, dst, with_scale):
    """Find s, R, t minimising ||dst - (s R src + t)||^2.  src, dst: (N,3)."""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    S, D = src - mu_s, dst - mu_d
    H = S.T @ D / len(src)
    U, sig, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(U @ Vt))
    C = np.diag([1, 1, d])
    R = Vt.T @ C @ U.T
    s = (np.trace(np.diag(sig) @ C) / (S ** 2).sum() * len(src)) if with_scale else 1.0
    t = mu_d - s * R @ mu_s
    return s, R, t


def align(src, dst, with_scale):
    s, R, t = umeyama(src, dst, with_scale)
    return (s * (R @ src.T)).T + t, s


def rmse(a, b):
    return float(np.sqrt(((a - b) ** 2).sum(1).mean()))


def jitter(P):
    return float(np.sqrt((np.diff(P, 2, axis=0) ** 2).sum(1).mean()))


# load
C = {r: load_centres(ROOT / r / "camera_poses.txt") for r in RUNS}
ref = C[REF]

# metrics vs reference
rows, aligned, err = [], {}, {}
for r in RUNS:
    A_sim, s = align(C[r], ref, True)
    A_se, _ = align(C[r], ref, False)
    aligned[r] = A_sim
    err[r] = np.linalg.norm(A_sim - ref, axis=1)
    rows.append({"run": r, "ate_sim3": round(rmse(A_sim, ref), 4), "ate_se3": round(rmse(A_se, ref), 4),
                 "scale_vs_ref": round(s, 4), "jitter": round(jitter(C[r]), 4),
                 "max_err": round(float(err[r].max()), 4), "path_len": round(float(np.linalg.norm(np.diff(C[r], axis=0), axis=1).sum()), 3)})

Path("runs").mkdir(exist_ok=True)
with open("runs/metrics.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

print(f"\nmetrics vs {REF} (Sim3-aligned unless noted)")
print(f"{'run':10} {'ATE sim3':>9} {'ATE se3':>9} {'scale':>7} {'jitter':>8} {'max err':>8} {'path':>7}")
for r in rows:
    print(f"{r['run']:10} {r['ate_sim3']:9.4f} {r['ate_se3']:9.4f} {r['scale_vs_ref']:7.4f} {r['jitter']:8.4f} {r['max_err']:8.4f} {r['path_len']:7.3f}")

# pairwise ATE (Sim3)
print("\npairwise ATE (Sim3), row aligned onto column")
print(" " * 10 + "".join(f"{c:>10}" for c in RUNS))
for a in RUNS:
    line = f"{a:10}"
    for b in RUNS:
        A, _ = align(C[a], C[b], True)
        line += f"{rmse(A, C[b]):10.4f}"
    print(line)

# figures
Path("figures").mkdir(exist_ok=True)
colors = {"png_1": "tab:blue", "png_2": "tab:cyan", "jpg_1": "tab:red", "jpgbar_1": "tab:orange", "noise_1": "tab:green", "noise_2": "tab:olive"}

# cosmetic: rotate all aligned runs to match the provided figure's heading, frame 0 at origin
theta = np.arctan2(14, 22) - np.arctan2(ref[-1, 2] - ref[0, 2], ref[-1, 0] - ref[0, 0])
c_, s_ = np.cos(theta), np.sin(theta)
def rot(P):
    Q = P - ref[0]; x, z = Q[:, 0], Q[:, 2]
    return np.stack([c_ * x - s_ * z, Q[:, 1], s_ * x + c_ * z], axis=1)
aligned = {r: rot(P) for r, P in aligned.items()}

fig, ax = plt.subplots(figsize=(9, 7))
for r in RUNS:
    P = aligned[r]
    ax.plot(P[:, 0], P[:, 2], lw=1.2, color=colors[r], label=r, alpha=0.9 if r != REF else 1)
ax.set_xlabel("X (model units)"); ax.set_ylabel("Z (model units)")
ax.set_title(f"top-down trajectories, all Sim(3)-aligned to {REF}"); ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("figures/overlay_aligned.png", dpi=120)

fig, ax = plt.subplots(figsize=(11, 4))
for r in RUNS:
    if r == REF:
        continue
    ax.plot(err[r], lw=1, color=colors[r], label=r)
for b in CHUNK_BOUNDARIES:
    ax.axvline(b, color="k", ls=":", lw=0.8)
for a, b in STATIC:
    ax.axvspan(a, b, color="gray", alpha=0.12)
ax.set_xlabel("frame"); ax.set_ylabel(f"position error vs {REF} (Sim3-aligned)")
ax.set_title("per-frame error — dotted: chunk boundaries, shaded: near-static segments"); ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("figures/per_frame_error.png", dpi=120)

print("\nwrote runs/metrics.csv, figures/overlay_aligned.png, figures/per_frame_error.png")