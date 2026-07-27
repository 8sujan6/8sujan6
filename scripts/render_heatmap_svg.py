"""
Pac-Man Contribution Heatmap — Correct ground-up implementation.

DESIGN PRINCIPLES:
1. animateMotion calcMode="linear" + <mpath> → smooth continuous glide (ZERO teleportation)
2. Arc-length-proportional food timing → pellet color changes EXACTLY when Pac-Man arrives
3. Correct Namco Pac-Man SVG: wedge mouth using cos/sin trig, black eye, chomp animation
4. All active contribution cells are waypoints; Manhattan path connects them in random order
5. rotate="auto" in animateMotion → Pac-Man automatically faces direction of travel
"""
import datetime
import json
import math
import os
import random

HERE   = os.path.dirname(os.path.abspath(__file__))
IN_PATH  = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

# GitHub contribution color palette (levels 0–5)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

# Grid geometry
CELL = 12      # cell size px
GAP  = 3       # gap between cells px
STEP = CELL + GAP   # 15 px per cell

PAD          = 22
LEFT_LABEL_W = 30
TOP_LABEL_H  = 20
TITLEBAR_H   = 30

# Colors
BG         = "#0d1117"
BG2        = "#050c18"
FRAME      = "#ffcc00"
MUTED      = "#7d8590"
ACCENT     = "#00ffff"
GREEN      = "#00ff66"
PAC_YELLOW = "#ffcc00"
WHITE      = "#ffffff"

# Pac-Man sprite geometry
PAC_R   = 7     # body radius in px
MOUTH_A = 25    # half-angle of mouth opening, degrees


# ─── Pac-Man path math ────────────────────────────────────────────────────────

def pac_open() -> str:
    """SVG path data: Pac-Man mouth open, facing right (+x direction), centered at 0,0."""
    a  = math.radians(MOUTH_A)
    lx = PAC_R * math.cos(a)
    ly = PAC_R * math.sin(a)
    # Arc sweeps the body (large arc flag=1, sweep=1 = counter-clockwise body)
    return f"M 0 0 L {lx:.4f} {-ly:.4f} A {PAC_R} {PAC_R} 0 1 1 {lx:.4f} {ly:.4f} Z"


def pac_closed() -> str:
    """SVG path data: Pac-Man mouth nearly closed, facing right, centered at 0,0."""
    a  = math.radians(2)          # 2° — nearly closed
    lx = PAC_R * math.cos(a)
    ly = PAC_R * math.sin(a)
    return f"M 0 0 L {lx:.4f} {-ly:.4f} A {PAC_R} {PAC_R} 0 1 1 {lx:.4f} {ly:.4f} Z"


# ─── Grid builder ─────────────────────────────────────────────────────────────

def level_for(count: int) -> int:
    if count == 0:  return 0
    if count <= 5:  return 1
    if count <= 15: return 2
    if count <= 30: return 3
    if count <= 50: return 4
    return 5


def build_grid(days: list) -> list:
    """
    Arrange flat day list into a 53-col × 7-row grid.
    Columns = weeks (left=oldest). Rows = weekdays, row 0 = Sunday.
    Each cell is (date_str, count, level) or None.
    """
    first    = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7   # Sun=0 offset
    grid     = []
    col      = [None] * lead_pad
    for d in days:
        date    = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"])))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        while len(col) < 7:
            col.append(None)
        grid.append(col)
    return grid[-53:]


# ─── Path builder ─────────────────────────────────────────────────────────────

def cell_center(c: int, r: int, grid_left: float, grid_top: float):
    """Return pixel center (px, py) of grid cell at column c, row r."""
    return (
        grid_left + c * STEP + CELL / 2.0,
        grid_top  + r * STEP + CELL / 2.0,
    )


def build_manhattan_path(waypoint_coords: list, grid_left: float, grid_top: float) -> list:
    """
    Build an ordered list of (col, row, px, py) nodes connecting waypoints
    via Manhattan (L-shaped) routing: alternates horizontal-first and vertical-first
    between consecutive waypoints for a natural maze-like feel.
    Returns a list of (c, r, px, py) tuples.
    """
    nodes = []
    alt   = False

    def push(c, r):
        px, py = cell_center(c, r, grid_left, grid_top)
        nodes.append((c, r, px, py))

    curr_c, curr_r = waypoint_coords[0]
    push(curr_c, curr_r)

    for tc, tr in waypoint_coords[1:]:
        if alt:
            # Vertical first, then horizontal
            if tr != curr_r:
                s = 1 if tr > curr_r else -1
                for r in range(curr_r + s, tr + s, s):
                    push(curr_c, r)
                curr_r = tr
            if tc != curr_c:
                s = 1 if tc > curr_c else -1
                for c in range(curr_c + s, tc + s, s):
                    push(c, curr_r)
                curr_c = tc
        else:
            # Horizontal first, then vertical
            if tc != curr_c:
                s = 1 if tc > curr_c else -1
                for c in range(curr_c + s, tc + s, s):
                    push(c, curr_r)
                curr_c = tc
            if tr != curr_r:
                s = 1 if tr > curr_r else -1
                for r in range(curr_r + s, tr + s, s):
                    push(curr_c, r)
                curr_r = tr
        alt = not alt

    return nodes


def compute_arc_lengths(nodes: list) -> list:
    """
    Return cumulative Euclidean arc length at each node.
    nodes is a list of (c, r, px, py).
    Returns list of floats, same length as nodes, starting at 0.0.
    """
    lengths = [0.0]
    for i in range(1, len(nodes)):
        dx = nodes[i][2] - nodes[i - 1][2]
        dy = nodes[i][3] - nodes[i - 1][3]
        lengths.append(lengths[-1] + math.hypot(dx, dy))
    return lengths


# ─── Main renderer ────────────────────────────────────────────────────────────

def render(data: dict) -> str:
    days = data["days"]
    grid = build_grid(days)

    cols_count = len(grid)
    canvas_w   = PAD + LEFT_LABEL_W + (cols_count * STEP - GAP) + PAD
    canvas_h   = TITLEBAR_H + TOP_LABEL_H + (7 * STEP - GAP) + 90

    grid_top  = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    # ── Collect active cells ──────────────────────────────────────────────────
    active_cells = []
    for c in range(cols_count):
        for r in range(7):
            cell = grid[c][r]
            if cell and cell[1] > 0:
                active_cells.append((c, r, cell))

    # ── Shuffle for random traversal (seeded = reproducible) ─────────────────
    rng = random.Random(42)
    rng.shuffle(active_cells)
    waypoint_coords = [(c, r) for c, r, _ in active_cells]

    # ── Build Manhattan path ──────────────────────────────────────────────────
    path_nodes  = build_manhattan_path(waypoint_coords, grid_left, grid_top)
    cum_lengths = compute_arc_lengths(path_nodes)
    total_len   = cum_lengths[-1]

    # ── Build SVG path d= string ──────────────────────────────────────────────
    path_d = " ".join(
        ("M" if i == 0 else "L") + f" {px:.2f} {py:.2f}"
        for i, (_, _, px, py) in enumerate(path_nodes)
    )

    # ── Compute food-event timing per active cell ─────────────────────────────
    # Find the first node index where Pac-Man arrives at each (c, r)
    first_visit = {}
    for i, (c, r, px, py) in enumerate(path_nodes):
        if (c, r) not in first_visit:
            first_visit[(c, r)] = i

    # food_events: (c, r) → (eat_pct, cell_data)
    # eat_pct is the % of total arc length where Pac-Man arrives at that cell
    food_events = {}
    for c, r, cell_data in active_cells:
        if (c, r) in first_visit:
            idx     = first_visit[(c, r)]
            eat_pct = (cum_lengths[idx] / total_len) * 100.0
            food_events[(c, r)] = (eat_pct, cell_data)

    # ── Animation duration: target ~55 px/sec, clamp 14–25s ──────────────────
    total_dur = round(max(14.0, min(25.0, total_len / 55.0)), 2)

    # ── CSS: per-pellet eat animation ─────────────────────────────────────────
    css_rules = []
    for (c, r), (ep, cell_data) in food_events.items():
        _, count, lvl   = cell_data
        target_color    = PALETTE[lvl]
        anim            = f"eat_{c}_{r}"
        flash_pct       = min(ep + 0.3, 99.5)
        settle_pct      = min(ep + 0.8, 99.9)
        css_rules.append(
            f"@keyframes {anim}{{"
            f"0%,{ep:.3f}%{{fill:{PAC_YELLOW}}}"
            f"{flash_pct:.3f}%{{fill:{WHITE}}}"
            f"{settle_pct:.3f}%,100%{{fill:{target_color}}}"
            f"}}"
            f".ab_{c}_{r}{{animation:{anim} {total_dur}s linear infinite}}"
        )

    css = "\n".join(css_rules)

    # ── SVG assembly ──────────────────────────────────────────────────────────
    p = []

    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink"'
        f' width="{canvas_w}" height="{canvas_h}"'
        f' viewBox="0 0 {canvas_w} {canvas_h}"'
        f' font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">'
    )

    p.append(f"<style>\n{css}\n</style>")

    # Defs: background gradient + motion path
    p.append(
        f'<defs>'
        f'<linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/>'
        f'<stop offset="1" stop-color="{BG}"/>'
        f'</linearGradient>'
        f'<path id="pacPath" d="{path_d}" fill="none"/>'
        f'</defs>'
    )

    # Background + border
    p.append(f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>')
    p.append(
        f'<rect x="0.5" y="0.5" width="{canvas_w - 1}" height="{canvas_h - 1}"'
        f' rx="12" fill="none" stroke="{FRAME}" stroke-width="1.5" stroke-opacity="0.7"/>'
    )

    # Title bar
    p.append(
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}"'
        f' stroke="{FRAME}" stroke-opacity="0.3"/>'
    )
    for cx, fc in [(18, "#ff5f56"), (32, "#ffbd2e"), (46, "#27c93f")]:
        p.append(f'<circle cx="{cx}" cy="15" r="4.5" fill="{fc}"/>')
    p.append(
        f'<text x="{canvas_w / 2:.1f}" y="{TITLEBAR_H / 2 + 4:.1f}"'
        f' fill="{PAC_YELLOW}" font-size="11" font-weight="bold" text-anchor="middle">'
        f'8sujan6@arcade: ~/contributions  ᗧ···ᗣ</text>'
    )

    # Month labels
    curr_m = None
    for ci, column in enumerate(grid):
        for cell in column:
            if cell:
                m = datetime.date.fromisoformat(cell[0]).strftime("%b")
                if m != curr_m:
                    curr_m = m
                    x = grid_left + ci * STEP
                    p.append(
                        f'<text x="{x:.1f}" y="{TITLEBAR_H + 14}"'
                        f' fill="{MUTED}" font-size="10">{m}</text>'
                    )
                break

    # Weekday labels
    for wi, wn in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + wi * STEP + CELL * 0.78
        p.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="9">{wn}</text>')

    # Grid cells
    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            gy     = grid_top + ri * STEP
            plural = "s" if count != 1 else ""
            title  = f"{date_s}: {count} contribution{plural}"

            if (ci, ri) in food_events:
                # Power pellet — yellow, gets eaten (CSS animation changes fill)
                p.append(
                    f'<rect class="ab_{ci}_{ri}"'
                    f' x="{gx}" y="{gy}" width="{CELL}" height="{CELL}"'
                    f' rx="2.5" fill="{PAC_YELLOW}">'
                    f'<title>{title} 🍒</title></rect>'
                )
            else:
                fill = PALETTE[lvl] if count > 0 else "#161b22"
                p.append(
                    f'<rect x="{gx}" y="{gy}" width="{CELL}" height="{CELL}"'
                    f' rx="2.5" fill="{fill}">'
                    f'<title>{title}</title></rect>'
                )

    # ── PAC-MAN SPRITE ────────────────────────────────────────────────────────
    # The <g> element contains the body path + eye circle.
    # animateMotion moves the WHOLE <g> along pacPath smoothly (no teleportation).
    # rotate="auto" rotates the group so +x axis points in direction of travel.
    # Since Pac-Man faces +x (right) by default, he always faces where he's going.
    # The mouth animate switches between open_d and closed_d at 0.25s intervals.
    open_d   = pac_open()
    closed_d = pac_closed()

    # Eye sits at top-right of center: offset (2.5, -2.8) relative to body center
    eye_cx = 2.5
    eye_cy = -2.8
    eye_r  = 1.4

    p.append(
        f'<g>'
        f'<path fill="{PAC_YELLOW}" d="{open_d}">'
        f'<animate attributeName="d"'
        f' values="{open_d};{closed_d};{open_d}"'
        f' dur="0.25s" repeatCount="indefinite"/>'
        f'</path>'
        f'<circle cx="{eye_cx}" cy="{eye_cy}" r="{eye_r}" fill="#000000"/>'
        f'<animateMotion dur="{total_dur}s" repeatCount="indefinite"'
        f' calcMode="linear" rotate="auto">'
        f'<mpath xlink:href="#pacPath"/>'
        f'</animateMotion>'
        f'</g>'
    )

    # Legend
    leg_y = grid_top + 7 * STEP + 10
    p.append(
        f'<text x="{PAD}" y="{leg_y + 9:.1f}"'
        f' fill="{PAC_YELLOW}" font-size="10" font-weight="bold">◉ Power Pellet</text>'
    )
    p.append(
        f'<text x="{PAD + 98}" y="{leg_y + 9:.1f}" fill="{MUTED}" font-size="10">→</text>'
    )
    p.append(
        f'<text x="{PAD + 112}" y="{leg_y + 9:.1f}"'
        f' fill="{GREEN}" font-size="10" font-weight="bold">▪ Eaten</text>'
    )

    # Stats separator
    sep_y = leg_y + CELL + 20
    p.append(
        f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}"'
        f' stroke="{FRAME}" stroke-opacity="0.2"/>'
    )

    # Stats text
    cs       = data["current_streak"]["length"]
    ls       = data["longest_streak"]["length"]
    total_c  = data["total_contributions"]
    best     = data["best_day"]
    rng_data = data["range"]

    ly = sep_y + 22
    p.append(
        f'<text x="{PAD}" y="{ly}" font-size="13" fill="{GREEN}">'
        f'<tspan font-weight="700">{total_c:,}</tspan>'
        f'<tspan fill="{MUTED}"> contributions eaten  ᗧ·· nom nom</tspan>'
        f'</text>'
        f'<text x="{canvas_w - PAD}" y="{ly}" font-size="11"'
        f' fill="{MUTED}" text-anchor="end">'
        f'{rng_data["start"]} → {rng_data["end"]}</text>'
    )

    ly += 22
    p.append(
        f'<text x="{PAD}" y="{ly}" font-size="12" fill="{MUTED}">'
        f'streak <tspan fill="{ACCENT}" font-weight="700">{cs}d</tspan>'
        f'  ·  longest <tspan fill="{ACCENT}" font-weight="700">{ls}d</tspan>'
        f'  ·  best <tspan fill="{PAC_YELLOW}" font-weight="700">{best["count"]}</tspan>'
        f' on {best["date"]}'
        f'</text>'
    )

    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    with open(IN_PATH, encoding="utf-8") as f:
        data = json.load(f)
    svg  = render(data)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    n_active = sum(1 for d in data["days"] if d["count"] > 0)
    print(f"[OK] Pac-Man heatmap written -> {OUT_PATH}")
    print(f"  Active pellets : {n_active}")
    print(f"  SVG size       : {len(svg):,} bytes")
