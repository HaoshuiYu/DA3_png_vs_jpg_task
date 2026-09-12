"""plot_pair.py — PNG vs JPG only, JPG Sim(3)-aligned onto PNG, matching the assessor's figure."""
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

def load_centres(path):
    M = np.loadtxt(path).reshape(-1, 4, 4)
    return M[:, :3, 3]          # C2W: camera position is the translation column

def align(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0); S, D = src - mu_s, dst - mu_d
    U, sig, Vt = np.linalg.svd(S.T @ D / len(src)); d = np.sign(np.linalg.det(U @ Vt))
    C = np.diag([1, 1, d]); R = Vt.T @ C @ U.T
    s = np.trace(np.diag(sig) @ C) / (S ** 2).sum() * len(src)
    return (s * (R @ src.T)).T + (mu_d - s * R @ mu_s), s

png = load_centres("runs/out/png_1/camera_poses.txt")
jpg = load_centres("runs/out/jpg_1/camera_poses.txt")
jpg_al, s = align(jpg, png)

fig, ax = plt.subplots(figsize=(8, 7))
ax.plot(png[:, 0], png[:, 2], c="blue", lw=1.5, label="PNG")
ax.plot(jpg_al[:, 0], jpg_al[:, 2], c="red", lw=1.5, label=f"JPG (aligned, scale {s:.3f})")
ax.set_xlabel("X (model units)"); ax.set_ylabel("Z (model units)"); ax.set_aspect("equal")
ax.grid(alpha=0.3); ax.legend(); ax.set_title("Our reproduction: PNG vs JPG, top-down")
plt.tight_layout(); plt.savefig("figures/pair_png_jpg.png", dpi=120); print("wrote figures/pair_png_jpg.png")