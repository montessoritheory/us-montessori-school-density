"""Shared look of the Montessori School Finder open datasets.

One module, copied unchanged into the scripts folder of each dataset package.
Palette: ink, blue, green, plus warm accents. Light backgrounds, rounded cards, a source line on every chart.
Needs matplotlib, numpy and Pillow.
"""
import json
import textwrap
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.collections import PatchCollection
from matplotlib.patches import FancyBboxPatch, Polygon
from PIL import Image

INK, BLUE, GREEN = "#0f172a", "#2563eb", "#059669"
AMBER, CORAL, TEAL, VIOLET = "#d97706", "#e11d48", "#0d9488", "#7c3aed"
SOFT, MINT, LINE, MUTED, GRID = "#f8fafc", "#ecfdf5", "#e2e8f0", "#64748b", "#eef2f7"
LIGHT = {BLUE: "#93c5fd", GREEN: "#6ee7b7", AMBER: "#fcd34d", CORAL: "#fda4af", TEAL: "#5eead4", VIOLET: "#c4b5fd"}
SITE = "montessorischoolfinder.com"
BRAND = "Montessori School Finder"
FOOTER_RIGHT = f"{BRAND}  ·  {SITE}  ·  CC BY 4.0"

_have = {f.name for f in font_manager.fontManager.ttflist}
FONT = next((f for f in ["Segoe UI", "Inter", "Arial", "DejaVu Sans"] if f in _have), "DejaVu Sans")
plt.rcParams.update({"font.family": FONT, "text.color": INK, "axes.edgecolor": LINE, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.spines.left": False, "axes.axisbelow": True, "figure.facecolor": SOFT})


def hexrgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def mix(a, b, t):
    """Blend colour a toward colour b by t (0 to 1)."""
    ca, cb = np.array(hexrgb(a)), np.array(hexrgb(b))
    return tuple(ca + (cb - ca) * t)


def ramp(colors):
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("msf", colors)


# ---------------------------------------------------------------- pixel canvas
def canvas(W, H, bg=SOFT, dpi=100):
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi, facecolor=bg)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    return fig, ax


def rrect(ax, x, y, w, h, r=20, fc="white", ec="none", lw=1.5, alpha=1, z=1):
    r = min(r, w / 2, h / 2)
    p = FancyBboxPatch((x + r, y + r), max(w - 2 * r, 0.01), max(h - 2 * r, 0.01),
                       boxstyle=f"round,pad={r},rounding_size={r}", fc=fc, ec=ec, lw=lw, alpha=alpha, zorder=z)
    ax.add_patch(p)
    return p


def text_w(fig, ax, s, size, weight="normal"):
    t = ax.text(0, 0, s, fontsize=size, fontweight=weight)
    fig.canvas.draw()
    w = t.get_window_extent(fig.canvas.get_renderer()).width
    t.remove()
    return w


def axpx(fig, W, H, x, y, w, h, **kw):
    """Data axes placed with pixel numbers (origin top left)."""
    a = fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H], **kw)
    a.patch.set_alpha(0)
    return a


# ---------------------------------------------------------------- cover
def cover(path, photo, title, kicker, big, big_label, chips, credit, accent=BLUE, flip=False, focus=(0.5, 0.5), zoom=1.0, title_size=45):
    """1600x800 cover. Photo with a dark gradient, title, one key number, stat chips, brand line."""
    W, H = 1600, 800
    fig, ax = canvas(W, H, bg=INK)
    im = Image.open(photo).convert("RGB")
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    iw, ih = im.size
    ch, cw = (int(ih / zoom), int(ih / zoom * 2)) if iw / ih > 2 else (int(iw / zoom / 2), int(iw / zoom))
    left = int(np.clip(focus[0] * iw - cw / 2, 0, iw - cw)); top = int(np.clip(focus[1] * ih - ch / 2, 0, ih - ch))
    im = im.crop((left, top, left + cw, top + ch)).resize((W, H), Image.LANCZOS)
    ax.imshow(np.asarray(im), extent=(0, W, H, 0), zorder=0, aspect="auto")
    x = np.linspace(0, 1, W)[None, :]; y = np.linspace(0, 1, H)[:, None]
    a = 0.16 + 0.80 * np.clip(1 - x / 0.82, 0, 1) ** 1.25 + 0.5 * np.clip((y - 0.78) / 0.22, 0, 1) ** 1.2
    ov = np.zeros((H, W, 4)); ov[..., :3] = hexrgb("#0b1222"); ov[..., 3] = np.clip(a, 0, 0.97)
    ax.imshow(ov, extent=(0, W, H, 0), zorder=1, aspect="auto")
    ax.set_xlim(0, W); ax.set_ylim(H, 0)
    # colour ribbon at the very bottom
    for i, c in enumerate([BLUE, TEAL, GREEN, AMBER, CORAL, VIOLET]):
        ax.add_patch(plt.Rectangle((i * W / 6, H - 9), W / 6 + 1, 9, fc=c, ec="none", zorder=5))
    # kicker pill
    kw_ = text_w(fig, ax, kicker.upper(), 14.5, "bold")
    rrect(ax, 90, 74, kw_ + 44, 46, r=23, fc=accent, z=3)
    ax.text(90 + 22, 97.5, kicker.upper(), fontsize=14.5, color="white", fontweight="bold", va="center", zorder=4)
    ax.text(90, 205, title, fontsize=title_size, color="white", fontweight="bold", va="center", linespacing=1.12, zorder=4)
    # key number
    ax.text(84, 410, big, fontsize=112, color="white", fontweight="bold", va="center", zorder=4)
    bw = text_w(fig, ax, big, 112, "bold")
    ax.add_patch(plt.Rectangle((92, 478), 110, 7, fc=LIGHT[accent], ec="none", zorder=4))
    ax.text(84 + bw + 26, 412, big_label, fontsize=24, color="white", va="center", linespacing=1.3, alpha=0.92, zorder=4)
    # chips
    cx = 90
    for c in chips:
        w = text_w(fig, ax, c, 16.5, "bold") + 44
        rrect(ax, cx, 548, w, 54, r=27, fc="white", ec="white", lw=1.4, alpha=0.16, z=3)
        ax.text(cx + w / 2, 575, c, fontsize=16.5, color="white", fontweight="bold", ha="center", va="center", zorder=4)
        cx += w + 14
    # brand line
    ax.add_patch(plt.Rectangle((90, 672), 4, 52, fc=LIGHT[accent], ec="none", zorder=4))
    ax.text(110, 685, BRAND, fontsize=20, color="white", fontweight="bold", va="center", zorder=4)
    ax.text(110, 713, SITE, fontsize=15, color=LIGHT[accent], va="center", zorder=4)
    ax.text(W - 36, 765, credit, fontsize=10.5, color="white", alpha=0.7, ha="right", va="center", zorder=4)
    fig.savefig(path, dpi=100, facecolor=INK)
    plt.close(fig)


# ---------------------------------------------------------------- chart page
class Page:
    """White rounded card on a soft background, with title, subtitle and a source line.
    Use .ax for pixel drawing and .axes(x, y, w, h) for data axes placed in pixels."""

    def __init__(self, title, subtitle, source, accent=BLUE, size=(1400, 900), subtitle_lines=1):
        self.W, self.H = size
        self.fig, self.ax = canvas(self.W, self.H)
        W, H, ax = self.W, self.H, self.ax
        rrect(ax, 22, 22, W - 44, H - 44, r=30, fc="white", ec=LINE, lw=1.6, z=0)
        rrect(ax, 66, 62, 74, 9, r=4.5, fc=accent, z=2)
        ax.text(66, 94, title, fontsize=29, fontweight="bold", va="top", zorder=3)
        ax.text(66, 146, subtitle, fontsize=14.5, color=MUTED, va="top", linespacing=1.35, zorder=3)
        self.top = 150 + 26 * subtitle_lines + 28
        ax.plot([66, W - 66], [H - 104, H - 104], color=LINE, lw=1.2, zorder=2)
        ax.text(66, H - 80, source, fontsize=10.5, color=MUTED, va="center", zorder=3)
        ax.text(66, H - 52, FOOTER_RIGHT, fontsize=11, color=INK, fontweight="bold", va="center", zorder=3)
        self.bottom = H - 122

    def axes(self, x, y, w, h, **kw):
        return axpx(self.fig, self.W, self.H, x, y, w, h, **kw)

    def save(self, path):
        self.fig.savefig(path, dpi=100, facecolor=SOFT)
        plt.close(self.fig)


def key_numbers(path, title, subtitle, source, tiles, accent=BLUE, cols=3):
    """Infographic card. tiles is a list of (big number, label, colour)."""
    rows = -(-len(tiles) // cols)
    H = 330 + rows * 250
    p = Page(title, subtitle, source, accent=accent, size=(1400, H))
    ax, W = p.ax, p.W
    gap = 26
    tw = (W - 132 - gap * (cols - 1)) / cols
    th = 222
    for i, (big, label, col) in enumerate(tiles):
        r, c = divmod(i, cols)
        x, y = 66 + c * (tw + gap), p.top + 14 + r * (th + gap)
        rrect(ax, x, y, tw, th, r=26, fc=mix(col, "#ffffff", 0.92), ec=mix(col, "#ffffff", 0.7), lw=1.5, z=2)
        rrect(ax, x + 28, y + 30, 46, 8, r=4, fc=col, z=3)
        ax.text(x + 28, y + 108, big, fontsize=46, fontweight="bold", color=col, va="center", zorder=3)
        ax.text(x + 28, y + 172, "\n".join(textwrap.wrap(label, 30)), fontsize=14.5, color=INK, va="center", linespacing=1.3, zorder=3)
    p.save(path)


# ---------------------------------------------------------------- charts
def lollipop(ax, labels, values, colors, fmt=lambda v: f"{v:,}", xmax=None, size=None, note=None):
    """Horizontal lollipop, first item on top."""
    n = len(labels)
    ys = np.arange(n)[::-1]
    xmax = xmax or max(values) * 1.15
    for y, v, c in zip(ys, values, colors):
        ax.plot([0, v], [y, y], color=mix(c, "#ffffff", 0.55), lw=3.2, solid_capstyle="round", zorder=2)
        ax.scatter([v], [y], s=size or 330, color=c, zorder=3, edgecolor="white", linewidth=2)
        ax.text(v + xmax * 0.04, y, fmt(v) if note is None else note(v), va="center", fontsize=13.5, fontweight="bold", color=INK)
    ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=13.5)
    ax.set_xlim(-xmax * 0.01, xmax); ax.set_ylim(-0.7, n - 0.3)
    ax.xaxis.grid(True, color=GRID, lw=1.2); ax.tick_params(axis="y", length=0, pad=10); ax.tick_params(axis="x", length=0, labelsize=11)
    for s in ("bottom",):
        ax.spines[s].set_visible(False)


def donut(ax, values, colors, center_big, center_small, width=0.34, start=90, gap=1.6):
    vals = np.array(values, float)
    ax.pie(vals, colors=colors, startangle=start, counterclock=False,
           wedgeprops=dict(width=width, edgecolor="white", linewidth=gap * 2), radius=1)
    ax.text(0, 0.07, center_big, ha="center", va="center", fontsize=34, fontweight="bold")
    ax.text(0, -0.2, center_small, ha="center", va="center", fontsize=12.5, color=MUTED)
    ax.set_aspect("equal")


# ---------------------------------------------------------------- world geometry (Natural Earth, public domain)
def equal_earth(lon, lat):
    A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
    lam, phi = np.radians(np.asarray(lon, float)), np.radians(np.asarray(lat, float))
    th = np.arcsin(np.sqrt(3) / 2 * np.sin(phi))
    x = 2 * np.sqrt(3) * lam * np.cos(th) / (3 * (A1 + 3 * A2 * th ** 2 + th ** 6 * (7 * A3 + 9 * A4 * th ** 2)))
    y = th * (A1 + A2 * th ** 2 + th ** 6 * (A3 + A4 * th ** 2))
    return x, y


NE_BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"


def natural_earth(raw_dir, name="ne_110m_admin_0_countries.geojson"):
    """Return the Natural Earth countries file, downloading it on first use. Treat it as untrusted data."""
    p = Path(raw_dir) / name
    if not p.exists():
        import urllib.request
        p.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(NE_BASE + name, p)
    return json.loads(p.read_text(encoding="utf8"))


def polygons(feature):
    g = feature["geometry"]
    parts = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    return [np.array(pt[0]) for pt in parts]


def iso2(f):
    pr = f["properties"]
    return pr.get("ISO_A2_EH") if pr.get("ISO_A2") in (None, "-99") else pr["ISO_A2"]


class World:
    """Countries projected with Equal Earth. color_for(iso2, name) returns a colour or None."""

    def __init__(self, geo, skip=("Antarctica",)):
        self.items = []
        for f in geo["features"]:
            if f["properties"]["NAME"] in skip:
                continue
            polys = [np.column_stack(equal_earth(p[:, 0], p[:, 1])) for p in polygons(f)]
            self.items.append((iso2(f), f["properties"]["NAME"], polys))
        allp = np.vstack([p for _, _, ps in self.items for p in ps])
        self.xmin, self.ymin = allp.min(0); self.xmax, self.ymax = allp.max(0)

    def draw(self, ax, color_for, edge="white", lw=0.5):
        patches, cols = [], []
        for code, name, polys in self.items:
            for p in polys:
                patches.append(Polygon(p, closed=True))
                cols.append(color_for(code, name))
        ax.add_collection(PatchCollection(patches, facecolors=cols, edgecolors=edge, linewidths=lw))
        ax.set_xlim(self.xmin - 0.05, self.xmax + 0.05); ax.set_ylim(self.ymin - 0.05, self.ymax + 0.05)
        ax.set_aspect("equal"); ax.axis("off")

    def point(self, lon, lat):
        x, y = equal_earth(lon, lat)
        return float(x), float(y)

    def centroid(self, code, name=None):
        """Centre of the largest polygon of a country, by area."""
        best, area = None, -1
        for c, n, polys in self.items:
            if c == code or n == name:
                for p in polys:
                    x, y = p[:, 0], p[:, 1]
                    a = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
                    if a > area:
                        area, best = a, p.mean(0)
        return best
