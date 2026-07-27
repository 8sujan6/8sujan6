"""
Render smooth, continuous non-teleporting 2D Pac-Man maze runner across contribution boxes:
- CONTINUOUS GLIDING MOVEMENT (No teleporting! Smooth SVG animateMotion path).
- ICONIC NAMCO PAC-MAN SPRITE: Classic yellow circle with wedge mouth that chomps open and shut.
- RANDOM MANHATTAN PATH: Pac-Man glides continuously along row and column lines between random active contribution cells!
- DYNAMIC ROTATION: Pac-Man automatically faces the direction he is running (Right, Down, Left, Up).
- PERFECT 1:1 EATING MATCH: Each contribution box turns Green (#39d353) exactly when Pac-Man glides over it.
"""
import datetime
import json
import math
import os
import random

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_W = 30
TOP_LABEL_H = 20
TITLEBAR_H = 30

BG = "#0d1117"
BG2 = "#050c18"
FRAME = "#ffcc00"
MUTED = "#7d8590"
TEXT = "#e6edf3"
ACCENT = "#00ffff"
GREEN = "#00ff66"
PAC_YELLOW = "#ffcc00"

def level_for(count):
    if count == 0:
        return 0
    if count <= 5:
        return 1
    if count <= 15:
        return 2
    if count <= 30:
        return 3
    if count <= 50:
        return 4
    return 5

def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7
    grid = []
    col = [None] * lead_pad
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
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

def render(data):
    days = data["days"]
    grid = build_grid(days)

    cols_count = len(grid)
    grid_w = cols_count * STEP - GAP
    grid_h = 7 * STEP - GAP

    canvas_w = PAD + LEFT_LABEL_W + grid_w + PAD
    canvas_h = TITLEBAR_H + TOP_LABEL_H + grid_h + 85

    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    active_cells = []
    for c in range(cols_count):
        for r in range(7):
            cell = grid[c][r]
            if cell and cell[1] > 0:
                active_cells.append((c, r, cell))

    rng = random.Random(77)
    shuffled = list(active_cells)
    rng.shuffle(shuffled)
    key_targets = shuffled[:12]

    # Generate continuous Manhattan path (moving horizontally then vertically between random targets)
    path_nodes = []
    curr_c, curr_r, _ = key_targets[0]
    path_nodes.append((curr_c, curr_r))

    for target in key_targets[1:]:
        tc, tr, _ = target
        # Move horizontally first to tc, then vertically to tr
        if tc != curr_c:
            step_c = 1 if tc > curr_c else -1
            for c in range(curr_c + step_c, tc + step_c, step_c):
                path_nodes.append((c, curr_r))
            curr_c = tc
        if tr != curr_r:
            step_r = 1 if tr > curr_r else -1
            for r in range(curr_r + step_r, tr + step_r, step_r):
                path_nodes.append((curr_c, r))
            curr_r = tr

    total_nodes = len(path_nodes)
    total_dur = 22.0  # Smooth continuous 22-second run

    # Build continuous SVG path d="..." string
    path_d_parts = []
    food_events = {}

    for idx, (c, r) in enumerate(path_nodes):
        cx = grid_left + c * STEP + CELL / 2.0
        cy = grid_top + r * STEP + CELL / 2.0
        cmd = "M" if idx == 0 else "L"
        path_d_parts.append(f"{cmd} {cx:.1f} {cy:.1f}")

        cell = grid[c][r]
        if cell and cell[1] > 0 and (c, r) not in food_events:
            pct = (idx / (total_nodes - 1)) * 100
            food_events[(c, r)] = (pct, cell)

    path_d = " ".join(path_d_parts)

    css_rules = []
    for (c, r), (eat_pct, cell) in food_events.items():
        date_s, count, lvl = cell
        target_color = PALETTE[lvl]
        anim_name = f"eat_{c}_{r}"
        css_rules.append(f"""
        @keyframes {anim_name} {{
            0%, {eat_pct:.1f}% {{ fill: {PAC_YELLOW}; opacity: 1; }}
            {eat_pct+0.4:.1f}% {{ fill: #ffffff; opacity: 1; }}
            {eat_pct+1.2:.1f}%, 100% {{ fill: {target_color}; opacity: 1; }}
        }}
        .active_box_{c}_{r} {{
            animation: {anim_name} {total_dur}s linear infinite;
        }}
        """)

    css = "\n".join(css_rules)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs>',
        f'<linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        # Continuous Motion Path
        f'<path id="pacPath" d="{path_d}" fill="none"/>',
        '</defs>',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1.5" stroke-opacity="0.8"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.4"/>',
        f'<circle cx="20" cy="15" r="5" fill="#ff5f56"/>',
        f'<circle cx="36" cy="15" r="5" fill="#ffbd2e"/>',
        f'<circle cx="52" cy="15" r="5" fill="#27c93f"/>',
        f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{PAC_YELLOW}" font-size="12" font-weight="bold" '
        f'text-anchor="middle">8sujan6@arcade: ~/pacman-maze-runner --smooth-glider</text>'
    ]

    # Month labels
    month_labels = []
    curr_m = None
    for ci, column in enumerate(grid):
        for cell in column:
            if cell:
                m = datetime.date.fromisoformat(cell[0]).strftime("%b")
                if m != curr_m:
                    curr_m = m
                    month_labels.append((ci, m))
                break

    for ci, label in month_labels:
        x = grid_left + ci * STEP
        parts.append(f'<text x="{x}" y="{TITLEBAR_H + 14}" fill="{MUTED}" font-size="10">{label}</text>')

    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + wi * STEP + CELL * 0.78
        parts.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="9">{wname}</text>')

    # Render grid cells
    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            gy = grid_top + ri * STEP
            plural = "s" if count != 1 else ""

            if (ci, ri) in food_events:
                # Active target box: starts Yellow (#ffcc00), turns Green when Pac-Man lands on it
                parts.append(
                    f'<rect class="active_box_{ci}_{ri}" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" '
                    f'fill="{PAC_YELLOW}">'
                    f'<title>{date_s}: {count} contribution{plural} (PAC-MAN TARGET)</title></rect>'
                )
            else:
                fill_color = PALETTE[lvl] if count > 0 else "#161b22"
                parts.append(
                    f'<rect x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" fill="{fill_color}">'
                    f'<title>{date_s}: {count} contribution{plural}</title></rect>'
                )

    # ICONIC NAMCO PAC-MAN VECTOR SPRITE WITH ROTATING CONTINUOUS GLIDE AND WEDGE CHOMP
    parts.append(
        f'<g>'
        f'<path fill="{PAC_YELLOW}" d="M 0 0 L 7 -5.5 A 7.5 7.5 0 1 1 7 5.5 Z">'
        f'<animate attributeName="d" values="M 0 0 L 7.5 -5.5 A 7.5 7.5 0 1 1 7.5 5.5 Z; M 0 0 L 7.5 -0.5 A 7.5 7.5 0 1 1 7.5 0.5 Z; M 0 0 L 7.5 -5.5 A 7.5 7.5 0 1 1 7.5 5.5 Z" dur="0.2s" repeatCount="indefinite"/>'
        f'</path>'
        f'<animateMotion dur="{total_dur}s" repeatCount="indefinite" rotate="auto">'
        f'<mpath href="#pacPath"/>'
        f'</animateMotion>'
        f'</g>'
    )

    # Legend
    leg_y = grid_top + 7 * STEP + 6
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL - 1) + 140)
    parts.append(f'<text x="{leg_x}" y="{leg_y + CELL*0.8:.1f}" fill="{PAC_YELLOW}" font-size="10" font-weight="bold">🟡 Power Pellet</text>')
    parts.append(f'<text x="{leg_x + 85}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10">⟶</text>')
    parts.append(f'<text x="{leg_x + 105}" y="{leg_y + CELL*0.8:.1f}" fill="{GREEN}" font-size="10" font-weight="bold">🟢 Eaten</text>')

    sep_y = leg_y + CELL + 14
    parts.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity="0.3"/>')

    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    total = data["total_contributions"]
    best = data["best_day"]
    rng_data = data["range"]

    ly = sep_y + 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{GREEN}">'
                 f'<tspan font-weight="700">{total:,}</tspan>'
                 f'<tspan fill="{MUTED}"> contributions eaten by Pac-Man ᗧ···</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'{rng_data["start"]} &#8594; {rng_data["end"]}</text>')
    ly += 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{MUTED}">current streak '
                 f'<tspan fill="{ACCENT}" font-weight="700">{cs} days</tspan>'
                 f'<tspan fill="{MUTED}">   &#183;   longest </tspan>'
                 f'<tspan fill="{ACCENT}" font-weight="700">{ls} days</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'best day <tspan fill="{PAC_YELLOW}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>')

    parts.append("</svg>")
    return "".join(parts)

if __name__ == "__main__":
    data = json.load(open(IN_PATH))
    svg = render(data)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote smooth continuous 2D Pac-Man maze runner heatmap to {OUT_PATH} ({len(svg)} bytes)")
