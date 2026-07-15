#!/usr/bin/env python3
"""cn-ex uses a hand-tuned simplified block province map (JapanEx-style topology).

Geometry lives in src/map-block.svg / embedded MAP_SVG in app.js.
This script only re-embeds map-block.svg into app.js after manual edits.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
svg = (ROOT / "src" / "map-block.svg").read_text(encoding="utf-8").strip()
# drop xml decl if present
if svg.startswith("<?xml"):
    svg = svg.split("?>", 1)[-1].strip()
(ROOT / "src" / "map-inner.html").write_text(svg + "\n", encoding="utf-8")

app = ROOT / "app.js"
js = app.read_text(encoding="utf-8")
esc = svg.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
js2, n = re.subn(r"const MAP_SVG = `[\s\S]*?`;", f"const MAP_SVG = `{esc}`;", js, count=1)
if n != 1:
    raise SystemExit(f"MAP_SVG replace failed: {n}")
app.write_text(js2, encoding="utf-8")
print("embedded map-block.svg into app.js, bytes", len(svg.encode()))
