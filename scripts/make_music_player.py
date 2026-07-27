"""
Generate a sleek, animated Cyberpunk/Vinyl Music Player SVG (Spotify-style)
with pulsing audio visualizer equalizer bars, rotating vinyl record, progress bar,
and track info.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "music-player.svg")

W, H = 860, 140
BG = "#0d1117"
BG2 = "#161b22"
FRAME = "#30363d"
CYAN = "#22d3ee"
GREEN = "#1db954"
MUTED = "#7d8590"
TEXT = "#e6edf3"
SUBTEXT = "#8b949e"

TRACK_TITLE = "Midnight City (Vibe Mix)"
ARTIST_NAME = "8sujan6 · Coding Chill Beats"
ALBUM_ART_BG = "#1f293d"

svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none">
  <style>
    @keyframes spin {{
      from {{ transform: rotate(0deg); }}
      to {{ transform: rotate(360deg); }}
    }}
    @keyframes eqBar1 {{ 0%, 100% {{ height: 8px; y: 26px; }} 50% {{ height: 28px; y: 6px; }} }}
    @keyframes eqBar2 {{ 0%, 100% {{ height: 24px; y: 10px; }} 50% {{ height: 10px; y: 24px; }} }}
    @keyframes eqBar3 {{ 0%, 100% {{ height: 14px; y: 20px; }} 50% {{ height: 32px; y: 2px; }} }}
    @keyframes eqBar4 {{ 0%, 100% {{ height: 30px; y: 4px; }} 50% {{ height: 12px; y: 22px; }} }}
    @keyframes eqBar5 {{ 0%, 100% {{ height: 18px; y: 16px; }} 50% {{ height: 26px; y: 8px; }} }}
    
    @keyframes progress {{
      0% {{ width: 0px; }}
      100% {{ width: 520px; }}
    }}

    .vinyl {{
      transform-origin: 65px 70px;
      animation: spin 4s linear infinite;
    }}
    .eq-1 {{ animation: eqBar1 1.2s ease-in-out infinite; }}
    .eq-2 {{ animation: eqBar2 0.9s ease-in-out infinite; }}
    .eq-3 {{ animation: eqBar3 1.4s ease-in-out infinite; }}
    .eq-4 {{ animation: eqBar4 1.1s ease-in-out infinite; }}
    .eq-5 {{ animation: eqBar5 1.3s ease-in-out infinite; }}
    
    .progress-fill {{
      animation: progress 180s linear infinite;
    }}
  </style>

  <!-- Container Frame -->
  <rect width="{W}" height="{H}" rx="12" fill="{BG}" />
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>

  <!-- Title bar header -->
  <line x1="0" y1="28" x2="{W}" y2="28" stroke="{FRAME}" stroke-opacity="0.5"/>
  <circle cx="20" cy="14" r="4" fill="#ff5f56"/>
  <circle cx="34" cy="14" r="4" fill="#ffbd2e"/>
  <circle cx="48" cy="14" r="4" fill="#27c93f"/>
  <text x="{W/2}" y="18" fill="{MUTED}" font-size="11" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, monospace" text-anchor="middle">
    8sujan6@spotify: ~$ now-playing --stream
  </text>
  <circle cx="{W-25}" cy="14" r="4" fill="{GREEN}">
    <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/>
  </circle>
  <text x="{W-38}" y="17" fill="{GREEN}" font-size="10" font-family="monospace" text-anchor="end" font-weight="bold">LIVE</text>

  <!-- Vinyl Record & Album Art -->
  <g class="vinyl">
    <circle cx="65" cy="70" r="42" fill="#111" stroke="#222" stroke-width="2"/>
    <circle cx="65" cy="70" r="35" fill="none" stroke="#222" stroke-width="1" stroke-dasharray="4 2"/>
    <circle cx="65" cy="70" r="28" fill="none" stroke="#333" stroke-width="1"/>
    <circle cx="65" cy="70" r="18" fill="{GREEN}"/>
    <circle cx="65" cy="70" r="6" fill="{BG}"/>
  </g>

  <!-- Song Details -->
  <text x="125" y="58" fill="{TEXT}" font-size="16" font-weight="bold" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif">
    {TRACK_TITLE}
  </text>
  <text x="125" y="78" fill="{SUBTEXT}" font-size="13" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif">
    {ARTIST_NAME}
  </text>

  <!-- Animated Equalizer Bars -->
  <g transform="translate(670, 48)">
    <rect class="eq-1" x="0" y="10" width="4" height="20" rx="2" fill="{GREEN}"/>
    <rect class="eq-2" x="8" y="10" width="4" height="20" rx="2" fill="{CYAN}"/>
    <rect class="eq-3" x="16" y="10" width="4" height="20" rx="2" fill="{GREEN}"/>
    <rect class="eq-4" x="24" y="10" width="4" height="20" rx="2" fill="{CYAN}"/>
    <rect class="eq-5" x="32" y="10" width="4" height="20" rx="2" fill="{GREEN}"/>
  </g>

  <!-- Progress Bar Track -->
  <rect x="125" y="96" width="520" height="5" rx="2.5" fill="{BG2}" />
  <!-- Progress Bar Fill -->
  <rect class="progress-fill" x="125" y="96" width="220" height="5" rx="2.5" fill="{GREEN}" />
  
  <!-- Time stamps -->
  <text x="125" y="116" fill="{MUTED}" font-size="10" font-family="monospace">1:24</text>
  <text x="645" y="116" fill="{MUTED}" font-size="10" font-family="monospace" text-anchor="end">3:45</text>
  
  <!-- Badge -->
  <rect x="735" y="90" width="105" height="24" rx="12" fill="#1db9541f" stroke="{GREEN}" stroke-width="1"/>
  <text x="787" y="106" fill="{GREEN}" font-size="11" font-weight="bold" font-family="-apple-system, sans-serif" text-anchor="middle">
    ♫ Spotify
  </text>
</svg>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg_content)

print(f"Wrote {OUT}")
