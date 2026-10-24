import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
h = json.load(open(sys.argv[1])); out = sys.argv[2]
D, B, R = h["deadline"], h["budget"], h["rates"]
panels = [("DCR-v1 Admission", np.array(R["dcr-v1-admission"]), "Blues", (0, 100)),
          ("BDC (ω = 0.5)", np.array(R["bdc"]), "Blues", (0, 100)),
          ("DCR-v1 Admission − BDC (pp)", np.array(R["dcr-v1-admission"]) - np.array(R["bdc"]), "Greens", (0, 50))]
plt.rcParams.update({"font.family": "serif", "font.size": 8.5})
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6), constrained_layout=True)
for ax, (title, M, cmap, (lo, hi)) in zip(axes, panels):
    im = ax.imshow(M, cmap=cmap, vmin=lo, vmax=hi, origin="upper")
    ax.set_xticks(range(len(B)), B); ax.set_yticks(range(len(D)), D)
    ax.set_xlabel("budget fraction β"); ax.set_title(title, fontsize=9)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i,j]:.0f}", ha="center", va="center", fontsize=7,
                    color="white" if (M[i, j] - lo) / (hi - lo) > 0.6 else "black")
axes[0].set_ylabel("deadline fraction α")
fig.colorbar(im, ax=axes[2], shrink=0.8, label="difference (pp)")
fig.savefig(out + ".png", dpi=200); fig.savefig(out + ".pdf")
print("saved", out)
