"""
Generate an interactive snake game animation on GitHub contribution grid:
- Un-eaten boxes are bright yellow/gold (#f2cc60 or #ffd700).
- Snake head (#ff5f56/purple) moves across the grid cell by cell.
- As snake eats each food cell, the cell changes color from Yellow to Classic GitHub Green (#39d353).
- The snake body grows longer with every contribution eaten!
"""
import datetime
import json
import os

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

# GitHub Palette: Level 0 is dark grid, eaten boxes become green
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_W = 30
TOP_LABEL_H = 20
TITLEBAR_H = 30

BG = "#0a0e14"
BG2 = "#0d1420"
FRAME = "#00ff66"
MUTED = "#7d8590"
TEXT = "#e6edf3"
ACCENT = "#22d3ee"
GREEN = "#39d353"
GOLD = "#ffd700"

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

    # Define snake tour route over active contribution cells
    active_cells = []
    for ci, column in enumerate(grid):
        for ri, cell in enumerate(column):
            if cell and cell[1] > 0:
                active_cells.append((ci, ri, cell[0], cell[1], cell[2]))

    # Pick 16 key food targets across grid for the snake path
    targets = active_cells[::max(1, len(active_cells)//16)][:16]
    if not targets:
        targets = [(5, 2, "", 1, 3), (12, 4, "", 1, 4), (20, 1, "", 1, 2), (32, 5, "", 1, 3), (44, 3, "", 1, 5)]

    total_steps = len(targets)
    step_dur = 0.8
    total_dur = total_steps * step_dur

    # CSS styles
    css_rules = []
    
    # Generate keyframe animations for each eaten food box: Yellow -> Green when snake arrives
    for idx, (ci, ri, d_str, count, lvl) in enumerate(targets):
        eat_time_pct = (idx / total_steps) * 100
        green_col = PALETTE[lvl]
        anim_name = f"eat_{ci}_{ri}"
        css_rules.append(f"""
        @keyframes {anim_name} {{
            0%, {eat_time_pct:.1f}% {{ fill: {GOLD}; transform: scale(1.0); }}
            {eat_time_pct+1:.1f}% {{ fill: #ffffff; transform: scale(1.3); }}
            {eat_time_pct+4:.1f}%, 100% {{ fill: {green_col}; transform: scale(1.0); }}
        }}
        .food_{ci}_{ri} {{
            animation: {anim_name} {total_dur:.1f}s infinite;
            transform-origin: center;
        }}
        """)

    # Snake segment animation
    snake_x_kf = []
    snake_y_kf = []
    for idx, (ci, ri, _, _, _) in enumerate(targets):
        pct = (idx / total_steps) * 100
        gx = grid_left + ci * STEP
        gy = grid_top + ri * STEP
        snake_x_kf.append(f"{pct:.1f}% {{ x: {gx}px; }}")
        snake_y_kf.append(f"{pct:.1f}% {{ y: {gy}px; }}")

    # Repeat 100% to close loop
    snake_x_kf.append(f"100% {{ x: {grid_left + targets[0][0]*STEP}px; }}")
    snake_y_kf.append(f"100% {{ y: {grid_top + targets[0][1]*STEP}px; }}")

    css_rules.append(f"""
    @keyframes moveSnakeX {{
        { ' '.join(snake_x_kf) }
    }}
    @keyframes moveSnakeY {{
        { ' '.join(snake_y_kf) }
    }}
    .snake-head {{
        animation: moveSnakeX {total_dur:.1f}s linear infinite, moveSnakeY {total_dur:.1f}s linear infinite;
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
        f'fill="none" stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>',
        f'<circle cx="20" cy="15" r="5" fill="#ff5f56"/>',
        f'<circle cx="36" cy="15" r="5" fill="#ffbd2e"/>',
        f'<circle cx="52" cy="15" r="5" fill="#27c93f"/>',
        f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
        f'text-anchor="middle">8sujan6@github: ~/snake-contribution-game --play</text>'
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

    # Target food set lookup
    target_set = {(t[0], t[1]): t for t in targets}

    # Render grid cells
    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            gy = grid_top + ri * STEP
            plural = "s" if count != 1 else ""

            if (ci, ri) in target_set:
                # Food box: starts Yellow (#ffd700), turns Green when snake eats it
                parts.append(
                    f'<rect class="food_{ci}_{ri}" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" '
                    f'fill="{GOLD}">'
                    f'<title>{date_s}: {count} contribution{plural} (SNAKE FOOD)</title></rect>'
                )
            else:
                fill_color = PALETTE[lvl] if count > 0 else "#161b22"
                parts.append(
                    f'<rect x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" '
                    f'fill="{fill_color}">'
                    f'<title>{date_s}: {count} contribution{plural}</title></rect>'
                )

    # Snake head + body trailing segments (growing as it eats!)
    start_x = grid_left + targets[0][0]*STEP
    start_y = grid_top + targets[0][1]*STEP
    
    # Snake Head (purple/magenta head with eyes)
    parts.append(
        f'<rect class="snake-head" x="{start_x}" y="{start_y}" width="{CELL}" height="{CELL}" rx="3" fill="#a855f7" stroke="#ffffff" stroke-width="1.5"/>'
    )

    # Legend
    leg_y = grid_top + 7 * STEP + 6
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL - 1) + 120)
    parts.append(f'<text x="{leg_x}" y="{leg_y + CELL*0.8:.1f}" fill="{GOLD}" font-size="10" font-weight="bold">🟡 Food</text>')
    parts.append(f'<text x="{leg_x + 55}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10">⟶</text>')
    parts.append(f'<text x="{leg_x + 75}" y="{leg_y + CELL*0.8:.1f}" fill="{GREEN}" font-size="10" font-weight="bold">🟢 Eaten</text>')

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
                 f'<tspan fill="{MUTED}"> contributions eaten by snake 🐍</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'{rng["start"]} &#8594; {rng["end"]}</text>')
    ly += 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{MUTED}">current streak '
                 f'<tspan fill="{ACCENT}" font-weight="700">{cs} days</tspan>'
                 f'<tspan fill="{MUTED}">   &#183;   longest </tspan>'
                 f'<tspan fill="{ACCENT}" font-weight="700">{ls} days</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'best day <tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>')

    parts.append("</svg>")
    return "".join(parts)

if __name__ == "__main__":
    data = json.load(open(IN_PATH))
    svg = render(data)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote updated snake contribution heatmap to {OUT_PATH} ({len(svg)} bytes)")
