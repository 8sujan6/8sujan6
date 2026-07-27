"""
Render a retro Pac-Man Arcade Contribution Graph SVG for GitHub Profile README:
- Pac-Man (#ffcc00) moves across active contribution rows eating pellets.
- Un-eaten contribution cells start as glowing Pac-Man Power Pellets (Yellow dots #ffcc00 / #ffbd2e).
- As Pac-Man arrives at each cell:
  - Pac-Man's mouth chitter-chaps open/close using SVG path animations.
  - The pellet is eaten (flashes white) and transforms into a GitHub Green contribution block (#39d353).
- Ghosts (Blinky #ff0000, Inky #00ffff, Pinky #ffb8ff, Clyde #ffb852) chase Pac-Man along the maze row!
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
FRAME = "#1f6feb"
MUTED = "#7d8590"
TEXT = "#e6edf3"
ACCENT = "#22d3ee"
GREEN = "#39d353"
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

    # Define exact Pac-Man path traversing grid rows
    pac_row = 3  # Wednesday row across the calendar
    total_cols = len(grid)
    total_dur = 14.0  # 14 seconds sweep across screen

    css_rules = ["""
    @keyframes chomp {
        0%, 100% { d: path('M 0 0 L 7 -5 A 7 7 0 1 1 7 5 Z'); }
        50% { d: path('M 0 0 L 7 0 A 7 7 0 1 1 7 0.1 Z'); }
    }
    @keyframes movePacman {
        0% { transform: translate(var(--start-x), var(--pac-y)); }
        100% { transform: translate(var(--end-x), var(--pac-y)); }
    }
    .pacman {
        animation: movePacman 14s linear infinite;
        fill: #ffcc00;
    }
    .ghost-red {
        animation: movePacman 14s linear infinite;
        animation-delay: -0.4s;
    }
    .ghost-pink {
        animation: movePacman 14s linear infinite;
        animation-delay: -0.8s;
    }
    .ghost-cyan {
        animation: movePacman 14s linear infinite;
        animation-delay: -1.2s;
    }
    """]

    # Generate keyframe animations for each pellet in row `pac_row`
    for ci in range(total_cols):
        cell = grid[ci][pac_row]
        if not cell:
            continue
        date_s, count, lvl = cell
        eat_pct = (ci / total_cols) * 100
        green_col = PALETTE[lvl] if count > 0 else "#161b22"
        anim_name = f"pellet_{ci}"
        css_rules.append(f"""
        @keyframes {anim_name} {{
            0%, {eat_pct:.1f}% {{ opacity: 1; fill: {PAC_YELLOW}; rx: 6px; }}
            {eat_pct+0.5:.1f}% {{ opacity: 1; fill: #ffffff; rx: 2px; }}
            {eat_pct+1.5:.1f}%, 100% {{ opacity: 1; fill: {green_col}; rx: 2.5px; }}
        }}
        .pellet-cell-{ci} {{
            animation: {anim_name} {total_dur}s linear infinite;
        }}
        """)

    css = "\n".join(css_rules)

    start_x = grid_left - 20
    end_x = grid_left + grid_w + 30
    pac_y = grid_top + pac_row * STEP + 6

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>'
        f':root {{ --start-x: {start_x}px; --end-x: {end_x}px; --pac-y: {pac_y}px; }}'
        f'{css}'
        f'</style>',
        '<defs>',
        f'<linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        '</defs>',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>',
        f'<circle cx="20" cy="15" r="5" fill="#ff5f56"/>',
        f'<circle cx="36" cy="15" r="5" fill="#ffbd2e"/>',
        f'<circle cx="52" cy="15" r="5" fill="#27c93f"/>',
        f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
        f'text-anchor="middle">8sujan6@arcade: ~/pacman-contributions --insert-coin</text>'
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

            if ri == pac_row:
                # Pac-Man path pellet cell
                parts.append(
                    f'<rect class="pellet-cell-{ci}" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" '
                    f'fill="{PAC_YELLOW}">'
                    f'<title>{date_s}: {count} contribution{plural} (PAC-PELLET)</title></rect>'
                )
            else:
                fill_color = PALETTE[lvl] if count > 0 else "#161b22"
                parts.append(
                    f'<rect x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" fill="{fill_color}">'
                    f'<title>{date_s}: {count} contribution{plural}</title></rect>'
                )

    # Pac-Man Element (Chomping Mouth)
    parts.append(
        f'<g class="pacman">'
        f'<path d="M 0 0 L 6 -4 A 6 6 0 1 1 6 4 Z" fill="{PAC_YELLOW}">'
        f'<animate attributeName="d" values="M 0 0 L 7 -5 A 7 7 0 1 1 7 5 Z; M 0 0 L 7 0 A 7 7 0 1 1 7 0.1 Z; M 0 0 L 7 -5 A 7 7 0 1 1 7 5 Z" dur="0.25s" repeatCount="indefinite"/>'
        f'</path>'
        f'</g>'
    )

    # Ghost 1: Blinky (Red) chasing behind
    parts.append(
        f'<g class="ghost-red">'
        f'<path d="M -18 -6 A 6 6 0 0 1 -6 -6 L -6 4 L -9 1 L -12 4 L -15 1 L -18 4 Z" fill="#ff0000"/>'
        f'<circle cx="-14" cy="-3" r="1.5" fill="#ffffff"/><circle cx="-14" cy="-3" r="0.7" fill="#0000ff"/>'
        f'<circle cx="-9" cy="-3" r="1.5" fill="#ffffff"/><circle cx="-9" cy="-3" r="0.7" fill="#0000ff"/>'
        f'</g>'
    )

    # Ghost 2: Inky (Cyan) chasing behind
    parts.append(
        f'<g class="ghost-cyan">'
        f'<path d="M -32 -6 A 6 6 0 0 1 -20 -6 L -20 4 L -23 1 L -26 4 L -29 1 L -32 4 Z" fill="#00ffff"/>'
        f'<circle cx="-28" cy="-3" r="1.5" fill="#ffffff"/><circle cx="-28" cy="-3" r="0.7" fill="#0000ff"/>'
        f'<circle cx="-23" cy="-3" r="1.5" fill="#ffffff"/><circle cx="-23" cy="-3" r="0.7" fill="#0000ff"/>'
        f'</g>'
    )

    # Legend
    leg_y = grid_top + 7 * STEP + 6
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL - 1) + 140)
    parts.append(f'<text x="{leg_x}" y="{leg_y + CELL*0.8:.1f}" fill="{PAC_YELLOW}" font-size="10" font-weight="bold">🟡 Power Pellet</text>')
    parts.append(f'<text x="{leg_x + 85}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10">⟶</text>')
    parts.append(f'<text x="{leg_x + 105}" y="{leg_y + CELL*0.8:.1f}" fill="{GREEN}" font-size="10" font-weight="bold">🟢 Eaten</text>')

    sep_y = leg_y + CELL + 14
    parts.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity="0.25"/>')

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
    print(f"Wrote Pac-Man Arcade contribution heatmap to {OUT_PATH} ({len(svg)} bytes)")
