"""Cover and charts for the US Montessori School Density dataset.
Input : data/by_state.csv, data/by_county.csv, data/national_summary.csv, scripts/states_albers.geojson,
        scripts/cover_photo.jpg
Output: images/cover.png (1600x800), key_numbers.png, density_map.png, state_ranking.png, count_vs_rate.png, top_counties.png
Montessori School Finder look: ink, blue, green and warm accents on soft backgrounds (see msf_style.py).
Needs pandas, numpy, matplotlib and Pillow.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
import matplotlib.patheffects as pe
import msf_style as S

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
D, IMG = ROOT / "data", ROOT / "images"
IMG.mkdir(exist_ok=True)

s = pd.read_csv(D / "by_state.csv")
c = pd.read_csv(D / "by_county.csv", dtype={"county_fips": str})
nat = pd.read_csv(D / "national_summary.csv").set_index("metric").value
NAT_RATE = float(nat.schools_per_10k_under5)
N_SCHOOLS, KIDS = int(nat.montessori_private_schools), int(nat.children_under_5)
SRC = "Sources: NCES Private School Universe Survey 2023-24, Census Bureau estimates of July 1, 2023."

# ---------- cover
S.cover(IMG / "cover.png", HERE / "cover_photo.jpg", "US Montessori\nSchool Density",
        "Open dataset  ·  2023-24", f"{NAT_RATE:.2f}", "Montessori private schools per\n10,000 children under 5",
        [f"{N_SCHOOLS:,} schools", f"{KIDS / 1e6:.1f} million children under 5", f"{int(nat.counties_with_a_school)} counties"],
        "Photo: Anil Sharma, Pexels", accent=S.GREEN, focus=(0.55, 0.5), title_size=48)

# ---------- key numbers
above = int((s.schools_per_10k_under5 > NAT_RATE).sum())
top_state = s.iloc[0]
S.key_numbers(IMG / "key_numbers.png", "US Montessori Density in Six Numbers",
              "Montessori private schools per 10,000 children under 5, school year 2023-24.", SRC, [
                  (f"{N_SCHOOLS:,}", "Montessori private schools in 50 states and DC", S.GREEN),
                  (f"{KIDS / 1e6:.1f} M", "children under 5, July 1, 2023", S.BLUE),
                  (f"{NAT_RATE:.2f}", f"schools per 10,000 children, or one for every {int(nat.children_under_5_per_school):,}", S.TEAL),
                  (f"{top_state.schools_per_10k_under5:.2f}", f"{top_state.state_name}, the densest state ({top_state.montessori_schools} schools)", S.AMBER),
                  (f"{above} of {len(s)}", "states and DC above the national rate", S.VIOLET),
                  (f"{nat.share_of_children_in_counties_without_a_school_pct}".replace(".0", "") + " %", f"of children under 5 live in a county with no school in the file ({int(nat.counties_without_a_school):,} counties)", S.CORAL),
              ], accent=S.GREEN)

# ---------- map
gj = json.load(open(HERE / "states_albers.geojson", encoding="utf8"))
name2row = s.set_index("state_name")
bins = [0, 0.5, 1.0, 1.5, 2.0, 99]
labels = ["Under 0.5", "0.5 to 0.99", "1.0 to 1.49", "1.5 to 1.99", "2.0 or more"]
pal = [S.mix(S.GREEN, "#ffffff", t) for t in (0.86, 0.62, 0.36)] + [S.GREEN, "#064e3b"]


def shade(v):
    return pal[next(i for i in range(5) if bins[i] <= v < bins[i + 1])]


def centroid(poly):
    x, y = poly[:, 0], poly[:, 1]
    a = x * np.roll(y, -1) - np.roll(x, -1) * y
    A = a.sum() / 2
    return np.array([((x + np.roll(x, -1)) * a).sum() / (6 * A), ((y + np.roll(y, -1)) * a).sum() / (6 * A)])


p = S.Page("Where Montessori Private Schools Are Densest",
           f"Schools per 10,000 children under 5, 2023-24. US rate {NAT_RATE:.2f}. Each label shows the state and its rate.",
           SRC, accent=S.GREEN, size=(1400, 960))
ax = p.axes(40, p.top - 14, 1320, p.bottom - p.top + 4)
patches, cols, cents = [], [], {}
for f in gj["features"]:
    nm = f["properties"]["name"]
    g = f["geometry"]
    parts = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    arr = [np.array(q[0]) for q in parts]
    big = max(arr, key=lambda a: abs(np.ptp(a[:, 0]) * np.ptp(a[:, 1])))
    cents[nm] = centroid(big)
    for a in arr:
        patches.append(Polygon(a, closed=True)); cols.append(shade(name2row.loc[nm].schools_per_10k_under5))
ax.add_collection(PatchCollection(patches, facecolors=cols, edgecolors="white", linewidths=1.1))
allp = np.vstack([q.get_xy() for q in patches])
xmin, xmax, ymin, ymax = allp[:, 0].min(), allp[:, 0].max(), allp[:, 1].min(), allp[:, 1].max()
ax.set_xlim(xmin - 5, xmax + 60); ax.set_ylim(ymax + 5, ymin - 5); ax.set_aspect("equal"); ax.axis("off")
side = ["VT", "NH", "MA", "RI", "CT", "NJ", "DE", "MD", "DC"]
abbr = name2row.state.to_dict()
sy = ymin + (ymax - ymin) * 0.34
for nm, ctr in cents.items():
    r = name2row.loc[nm]
    dark = r.schools_per_10k_under5 >= 1.5
    if r.state in side:
        i = side.index(r.state)
        tx, ty = xmax + 18, sy + i * 17.5
        ax.plot([ctr[0], tx - 3], [ctr[1], ty], color="#94a3b8", lw=0.8, zorder=3)
        ax.text(tx, ty, f"{r.state}  {r.schools_per_10k_under5:.2f}", fontsize=10, va="center", color=S.INK, fontweight="bold", zorder=4)
    else:
        col = "white" if dark else S.INK
        ax.text(ctr[0], ctr[1] - 1.5, r.state, fontsize=10.5, fontweight="bold", ha="center", va="center", color=col, zorder=4)
        ax.text(ctr[0], ctr[1] + 8, f"{r.schools_per_10k_under5:.2f}", fontsize=8.5, ha="center", va="center", color=col, zorder=4)
for i, (lab, col) in enumerate(zip(labels, pal)):
    x = 90 + i * 215
    S.rrect(p.ax, x, p.bottom - 6, 30, 22, r=6, fc=col, z=5)
    p.ax.text(x + 42, p.bottom + 5, lab, fontsize=12, va="center", zorder=5)
p.save(IMG / "density_map.png")

# ---------- ranking lollipop
top = s.head(15)
p = S.Page("The 15 States With the Most Montessori Schools Per Child",
           "Green dots have at least 30 schools. Amber dots rest on fewer, so one school moves the rate.",
           SRC, accent=S.AMBER, size=(1400, 980))
ax = p.axes(330, p.top - 2, 900, p.bottom - p.top - 4)
S.lollipop(ax, list(top.state_name), list(top.schools_per_10k_under5), [S.GREEN if n >= 30 else S.AMBER for n in top.montessori_schools],
           xmax=4.3, size=270, note=lambda v: "")
for y, (v, n) in zip(np.arange(len(top))[::-1], zip(top.schools_per_10k_under5, top.montessori_schools)):
    ax.text(v + 4.3 * 0.04, y, f"{v:.2f}", va="center", fontsize=13.5, fontweight="bold")
    ax.text(v + 4.3 * 0.04 + 0.33, y, f"{n} schools", va="center", fontsize=11.5, color=S.MUTED)
ax.axvline(NAT_RATE, color=S.INK, lw=1.3, ls=(0, (4, 3)), zorder=1)
ax.text(NAT_RATE + 0.03, len(top) - 0.38, f"US rate {NAT_RATE:.2f}", fontsize=11.5, va="center")
p.save(IMG / "state_ranking.png")

# ---------- count against rate
p = S.Page("Many Schools Is Not the Same as Many Per Child",
           "Each bubble is a state or DC. Bubble area follows the number of children under 5.",
           SRC, accent=S.BLUE, size=(1400, 920))
ax = p.axes(120, p.top, 1160, p.bottom - p.top - 40)
for _, r in s.iterrows():
    col = S.GREEN if r.montessori_schools >= 30 else S.AMBER
    ax.scatter(r.montessori_schools, r.schools_per_10k_under5, s=30 + r.children_under_5 / 2000, color=col, alpha=0.6, edgecolor="white", linewidth=1.2, zorder=3)
ax.axhline(NAT_RATE, color=S.INK, lw=1.2, ls=(0, (4, 3)), zorder=2)
ax.text(1000, NAT_RATE + 0.04, f"US rate {NAT_RATE:.2f}", fontsize=11.5, ha="right", va="bottom")
halo = [pe.withStroke(linewidth=3, foreground="white")]
show = set(s.head(4).state) | set(s.sort_values("montessori_schools", ascending=False).head(6).state) | set(s.tail(3).state)
for _, r in s.iterrows():
    if r.state in show:
        ax.annotate(r.state, (r.montessori_schools, r.schools_per_10k_under5), xytext=(0, 14 if r.children_under_5 < 800000 else 0), textcoords="offset points", ha="center", va="center",
                    fontsize=10.5, fontweight="bold", color=S.INK, path_effects=halo, zorder=5)
ax.set_xscale("log"); ax.set_xlim(2.6, 1300); ax.set_ylim(0, 3.3)
ax.set_xticks([3, 5, 10, 25, 50, 100, 250, 500, 1000]); ax.set_xticklabels(["3", "5", "10", "25", "50", "100", "250", "500", "1,000"])
ax.grid(True, color=S.GRID, lw=1.2); ax.tick_params(length=0, labelsize=11.5)
ax.set_xlabel("Montessori private schools in the state (log scale)", fontsize=12.5, color=S.MUTED, labelpad=12)
ax.set_ylabel("Schools per 10,000 children under 5", fontsize=12.5, color=S.MUTED, labelpad=12)
ax.spines["bottom"].set_visible(False)
p.ax.scatter([790], [p.top + 12], s=140, color=S.GREEN, alpha=0.7, zorder=6); p.ax.text(806, p.top + 12, "30 schools or more", fontsize=12, va="center", zorder=6)
p.ax.scatter([1010], [p.top + 12], s=140, color=S.AMBER, alpha=0.7, zorder=6); p.ax.text(1026, p.top + 12, "Fewer than 30", fontsize=12, va="center", zorder=6)
p.save(IMG / "count_vs_rate.png")

# ---------- top counties
t = c[c.rate_shown].sort_values("schools_per_10k_under5", ascending=False).head(15)
lab = [f"{n.replace(' County', '').replace(' city', '')}, {st}" for n, st in zip(t.county_name, t.state)]
p = S.Page("The 15 Densest Counties",
           f"Counties with at least 5,000 children under 5. Dashed line is the US rate, {NAT_RATE:.2f}. Dot size follows the number of schools.",
           SRC, accent=S.TEAL, size=(1400, 980))
ax = p.axes(300, p.top - 2, 940, p.bottom - p.top - 4)
ys = np.arange(len(t))[::-1]
xmax = float(t.schools_per_10k_under5.max()) * 1.55
for y, (_, r) in zip(ys, t.iterrows()):
    ax.plot([0, r.schools_per_10k_under5], [y, y], color=S.mix(S.TEAL, "#ffffff", 0.55), lw=3.2, solid_capstyle="round", zorder=2)
    ax.scatter([r.schools_per_10k_under5], [y], s=90 + 60 * r.montessori_schools, color=S.TEAL, edgecolor="white", linewidth=2, zorder=3)
    ax.text(r.schools_per_10k_under5 + xmax * 0.045, y, f"{r.schools_per_10k_under5:.1f}", va="center", fontsize=13.5, fontweight="bold")
    ax.text(r.schools_per_10k_under5 + xmax * 0.045 + 1.15, y, f"{r.montessori_schools} schools, {r.children_under_5:,} children", va="center", fontsize=11.5, color=S.MUTED)
ax.set_yticks(ys); ax.set_yticklabels(lab, fontsize=13.5)
ax.set_xlim(0, xmax); ax.set_ylim(-0.7, len(t) - 0.3); ax.axvline(NAT_RATE, color=S.INK, lw=1.3, ls=(0, (4, 3)), zorder=1)
ax.xaxis.grid(True, color=S.GRID, lw=1.2); ax.tick_params(axis="y", length=0, pad=10); ax.tick_params(axis="x", length=0, labelsize=11)
ax.spines["bottom"].set_visible(False)
p.save(IMG / "top_counties.png")
print("charts done, font", S.FONT)
