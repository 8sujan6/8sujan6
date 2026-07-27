"""
Render a 100% mathematically aligned 2D Pac-Man Maze Contribution Graph SVG:
- Computes exact pixel coordinates for each cell (col * 15 + pad, row * 15 + pad).
- Pac-Man sprite uses <animateMotion> over an exact SVG <path> matching grid cell centers.
- Pellet eating keyframes map 1:1 with Pac-Man's exact arrival timestamp at each cell.
- Ghosts (Blinky & Inky) follow exact path trailing behind Pac-Man.
"""
import datetime
import json
import os

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

    # Define exact 2D serpentine maze path through rows 1, 3, and 5
    # Waypoints: list of (col, row)
    path_cells = []
    # Row 1: left -> right
    for c in range(0, cols_count):
        path_cells.append((c, 1))
    # Row 2: rightmost step down
    path_cells.append((cols_count - 1, 2))
    # Row 3: right -> left
    for c in range(cols_count - 1, -1, -1):
        path_cells.append((c, 3))
    # Row 4: leftmost step down
    path_cells.append((0, 4))
    # Row 5: left -> right
    for c in range(0, cols_count):
        path_cells.append((c, 5))

    total_cells_in_path = len(path_cells)
    total_dur = 18.0  # 18 seconds full loop

    # Construct exact SVG <path d="..."> string passing through center of cells
    path_d_parts = []
    for idx, (c, r) in enumerate(path_cells):
        cx = grid_left + c * STEP + CELL / 2.0
        cy = grid_top + r * STEP + CELL / 2.0
        cmd = "M" if idx == 0 else "L"
        path_d_parts.append(f"{cmd} {cx:.1f} {cy:.1f}")
    
    path_d = " ".join(path_d_parts)

    # Exact time mapping for each cell eating event
    food_events = {}
    for idx, (c, r) in enumerate(path_cells):
        pct = (idx / (total_cells_in_path - 1)) * 100
        cell = grid[c][r]
        if cell and (c, r) not in food_events:
            food_events[(c, r)] = (pct, cell)

    css_rules = []
    for (c, r), (eat_pct, cell) in food_events.items():
        date_s, count, lvl = cell
        target_color = PALETTE[lvl] if count > 0 else "#161b22"
        # If count > 0, it starts yellow (food) and eats into green.
        # If count == 0, it stays dark grid.
        if count > 0:
            anim_name = f"eat_{c}_{r}"
            css_rules.append(f"""
            @keyframes {anim_name} {{
                0%, {eat_pct:.1f}% {{ fill: {PAC_YELLOW}; opacity: 1; }}
                {eat_pct+0.4:.1f}% {{ fill: #ffffff; opacity: 1; }}
                {eat_pct+1.2:.1f}%, 100% {{ fill: {target_color}; opacity: 1; }}
            }}
            .pellet_{c}_{r} {{
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
        # Exact Motion Path
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
        f'text-anchor="middle">8sujan6@arcade: ~/pacman-maze-runner --insert-coin</text>'
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

            if (ci, ri) in food_events and count > 0:
                parts.append(
                    f'<rect class="pellet_{ci}_{ri}" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" '
                    f'fill="{PAC_YELLOW}">'
                    f'<title>{date_s}: {count} contribution{plural} (POWER PELLET)</title></rect>'
                )
            else:
                fill_color = PALETTE[lvl] if count > 0 else "#161b22"
                parts.append(
                    f'<rect x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" fill="{fill_color}">'
                    f'<title>{date_s}: {count} contribution{plural}</title></rect>'
                )

    # 1. PAC-MAN SPRITE using <animateMotion> along exact #pacPath
    parts.append(
        f'<g>'
        f'<path d="M 0 0 L 7 -5 A 7 7 0 1 1 7 5 Z" fill="{PAC_YELLOW}">'
        f'<animate attributeName="d" values="M 0 0 L 7 -5 A 7 7 0 1 1 7 5 Z; M 0 0 L 7 0 A 7 7 0 1 1 7 0.1 Z; M 0 0 L 7 -5 A 7 7 0 1 1 7 5 Z" dur="0.2s" repeatCount="indefinite"/>'
        f'</path>'
        f'<animateMotion dur="{total_dur}s" repeatCount="indefinite" rotate="auto">'
        f'<mpath href="#pacPath"/>'
        f'</animateMotion>'
        f'</g>'
    )

    # 2. BLINKY (RED GHOST) following slightly behind on exact #pacPath
    parts.append(
        f'<g>'
        f'<path d="M -16 -6 A 6 6 0 0 1 -4 -6 L -4 4 L -7 1 L -10 4 L -13 1 L -16 4 Z" fill="#ff0000"/>'
        f'<circle cx="-12" cy="-3" r="1.5" fill="#ffffff"/><circle cx="-12" cy="-3" r="0.7" fill="#0000ff"/>'
        f'<circle cx="-7" cy="-3" r="1.5" fill="#ffffff"/><circle cx="-7" cy="-3" r="0.7" fill="#0000ff"/>'
        f'<animateMotion dur="{total_dur}s" repeatCount="indefinite" rotate="auto" begin="-0.3s">'
        f'<mpath href="#pacPath"/>'
        f'</animateMotion>'
        f'</g>'
    )

    # 3. INKY (CYAN GHOST) following behind Blinky
    parts.append(
        f'<g>'
        f'<path d="M -30 -6 A 6 6 0 0 1 -18 -6 L -18 4 L -21 1 L -24 4 L -27 1 L -30 4 Z" fill="#00ffff"/>'
        f'<circle cx="-26" cy="-3" r="1.5" fill="#ffffff"/><circle cx="-26" cy="-3" r="0.7" fill="#0000ff"/>'
        f'<circle cx="-21" cy="-3" r="1.5" fill="#ffffff"/><circle cx="-21" cy="-3" r="0.7" fill="#0000ff"/>'
        f'<animateMotion dur="{total_dur}s" repeatCount="indefinite" rotate="auto" begin="-0.6s">'
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
    rng = data["range"]

    ly = sep_y + 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{GREEN}">'
                 f'<tspan font-weight="700">{total:,}</tspan>'
                 f'<tspan fill="{MUTED}"> contributions eaten by Pac-Man ᗧ···</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'{rng["start"]} &#8594; {rng["end"]}</text>')
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
    print(f"Wrote mathematically aligned 2D Pac-Man contribution heatmap to {OUT_PATH} ({len(svg)} bytes)")
