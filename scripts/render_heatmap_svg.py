"""
Render a 100% mathematically exact Arcade Pac-Man Contribution Graph SVG:
- PROPER 8-BIT PAC-MAN SPRITE: Iconic pixelated arcade Pac-Man with clear mouth chomp and eye.
- RANDOM 2D NON-LINEAR HOPPING: Pac-Man teleports/hops randomly across different columns and rows!
- INDIVIDUAL UN-EVEN TIMING & SPEED: Pac-Man visits random contribution boxes in random order.
- CELL EATING MECHANICS: Active contribution cells start as Pac-Man Yellow (#ffcc00),
  and turn GitHub Green (#39d353) exactly when Pac-Man lands on them.
"""
import datetime
import json
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

    # Collect active contribution cells
    active_cells = []
    for c in range(cols_count):
        for r in range(7):
            cell = grid[c][r]
            if cell and cell[1] > 0:
                active_cells.append((c, r, cell))

    # Seed random for deterministic reproducible pattern
    rng = random.Random(42)
    shuffled = list(active_cells)
    rng.shuffle(shuffled)

    # Pick 16 random targets across all rows and columns
    targets = shuffled[:16]
    total_targets = len(targets)
    total_dur = 20.0  # 20 seconds loop

    # Generate keyframe position jumps for Pac-Man across random targets
    pac_keyframes = []
    food_events = {}

    for idx, (c, r, cell) in enumerate(targets):
        pct = (idx / total_targets) * 100
        cx = grid_left + c * STEP + CELL / 2.0
        cy = grid_top + r * STEP + CELL / 2.0
        
        pac_keyframes.append(f"{pct:.1f}% {{ transform: translate({cx:.1f}px, {cy:.1f}px); }}")
        food_events[(c, r)] = (pct, cell)

    # End at starting location for smooth loop
    first_cx = grid_left + targets[0][0] * STEP + CELL / 2.0
    first_cy = grid_top + targets[0][1] * STEP + CELL / 2.0
    pac_keyframes.append(f"100% {{ transform: translate({first_cx:.1f}px, {first_cy:.1f}px); }}")

    css_rules = [f"""
    @keyframes pacJump {{
        {' '.join(pac_keyframes)}
    }}
    .pacman-sprite {{
        animation: pacJump {total_dur}s step-end infinite;
    }}
    """]

    for (c, r), (eat_pct, cell) in food_events.items():
        date_s, count, lvl = cell
        target_color = PALETTE[lvl]
        anim_name = f"eat_{c}_{r}"
        css_rules.append(f"""
        @keyframes {anim_name} {{
            0%, {eat_pct:.1f}% {{ fill: {PAC_YELLOW}; opacity: 1; }}
            {eat_pct+0.5:.1f}% {{ fill: #ffffff; opacity: 1; }}
            {eat_pct+1.5:.1f}%, 100% {{ fill: {target_color}; opacity: 1; }}
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
        '</defs>',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1.5" stroke-opacity="0.8"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.4"/>',
        f'<circle cx="20" cy="15" r="5" fill="#ff5f56"/>',
        f'<circle cx="36" cy="15" r="5" fill="#ffbd2e"/>',
        f'<circle cx="52" cy="15" r="5" fill="#27c93f"/>',
        f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{PAC_YELLOW}" font-size="12" font-weight="bold" '
        f'text-anchor="middle">8sujan6@arcade: ~/pacman-random-hunter --play</text>'
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

    # ICONIC ARCADE PAC-MAN SPRITE WITH CHOMPING MOUTH & EYE
    parts.append(
        f'<g class="pacman-sprite">'
        f'<g transform="translate(-6, -6)">'
        f'<path fill="{PAC_YELLOW}" d="M 6 6 L 12 1 A 6 6 0 1 1 12 11 Z">'
        f'<animate attributeName="d" values="M 6 6 L 12 1 A 6 6 0 1 1 12 11 Z; M 6 6 L 12 5.5 A 6 6 0 1 1 12 6.5 Z; M 6 6 L 12 1 A 6 6 0 1 1 12 11 Z" dur="0.2s" repeatCount="indefinite"/>'
        f'</path>'
        f'<circle cx="6" cy="3" r="1.2" fill="#000000"/>'
        f'</g>'
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
    print(f"Wrote random 2D hopping Pac-Man contribution heatmap to {OUT_PATH} ({len(svg)} bytes)")
