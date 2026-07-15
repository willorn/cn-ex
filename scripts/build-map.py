#!/usr/bin/env python3
"""
cn-ex map builder — independent stylized province map.

Goals (not china-ex boxes, not survey-grade geo):
- Keep a recognizable China silhouette and neighbor topology
- Smooth / simplify coastlines for a clean illustration look
- Enlarge tiny provinces (京/津/沪/港/澳/宁/琼/渝 …) so they stay tappable
- Resolve crowded labels in the Beijing–Tianjin–Hebei area
"""
from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUT_SVG = SRC / "map-accurate.svg"
OUT_INNER = SRC / "map-inner.html"
GEO_URL = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"
CACHE = Path("/tmp/china_full.json")

NAME_MAP = {
    "北京市": "北京",
    "天津市": "天津",
    "河北省": "河北",
    "山西省": "山西",
    "内蒙古自治区": "内蒙古",
    "辽宁省": "辽宁",
    "吉林省": "吉林",
    "黑龙江省": "黑龙江",
    "上海市": "上海",
    "江苏省": "江苏",
    "浙江省": "浙江",
    "安徽省": "安徽",
    "福建省": "福建",
    "江西省": "江西",
    "山东省": "山东",
    "河南省": "河南",
    "湖北省": "湖北",
    "湖南省": "湖南",
    "广东省": "广东",
    "广西壮族自治区": "广西",
    "海南省": "海南",
    "重庆市": "重庆",
    "四川省": "四川",
    "贵州省": "贵州",
    "云南省": "云南",
    "西藏自治区": "西藏",
    "陕西省": "陕西",
    "甘肃省": "甘肃",
    "青海省": "青海",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
    "台湾省": "台湾",
    "香港特别行政区": "香港",
    "澳门特别行政区": "澳门",
}

# URL / storage order — never change after publish
PROVINCES = [
    "黑龙江",
    "甘肃",
    "吉林",
    "内蒙古",
    "山东",
    "河北",
    "北京",
    "天津",
    "西藏",
    "新疆",
    "河南",
    "安徽",
    "山西",
    "湖北",
    "青海",
    "辽宁",
    "广东",
    "江苏",
    "江西",
    "浙江",
    "福建",
    "上海",
    "陕西",
    "湖南",
    "广西",
    "香港",
    "澳门",
    "贵州",
    "重庆",
    "四川",
    "云南",
    "宁夏",
    "台湾",
    "海南",
]

# Minimum on-screen footprint after projection (approx half-side in px).
# Tiny admin units get scaled up around their centroid for hit targets.
MIN_HALF = {
    "北京": 24,
    "天津": 22,
    "上海": 20,
    "香港": 16,
    "澳门": 16,
    "宁夏": 22,
    "海南": 24,
    "重庆": 26,
    "台湾": 22,
    "江苏": 0,  # normal
}

# Manual label offsets in px after auto placement (readable, not geo-perfect)
LABEL_TWEAK = {
    "北京": (-2, -18),
    "天津": (22, 14),
    "河北": (28, 28),
    "上海": (20, 4),
    "香港": (22, 12),
    "澳门": (8, 22),
    "宁夏": (0, -4),
    "海南": (0, 6),
    "重庆": (8, 4),
    "江苏": (10, 2),
    "内蒙古": (24, 8),
    "甘肃": (-8, 10),
    "陕西": (4, 8),
    "山西": (-2, 4),
    "山东": (8, 4),
    "河南": (2, 4),
    "安徽": (4, 2),
    "湖北": (2, 2),
    "湖南": (0, 4),
    "江西": (4, 2),
    "浙江": (10, 4),
    "福建": (10, 6),
    "广东": (4, 8),
    "广西": (-2, 6),
    "贵州": (0, 2),
    "云南": (-4, 6),
    "四川": (-6, 0),
    "青海": (-4, 0),
    "西藏": (-10, 8),
    "新疆": (-8, 0),
    "黑龙江": (8, 0),
    "吉林": (6, 0),
    "辽宁": (8, 4),
    "台湾": (14, 0),
}


def load_geo() -> dict:
    if not CACHE.exists():
        print("download", GEO_URL)
        urllib.request.urlretrieve(GEO_URL, CACHE)
    return json.loads(CACHE.read_text(encoding="utf-8"))


def ring_to_pts(ring):
    return [(float(x), float(y)) for x, y in ring]


def simplify_ring(pts, tol):
    if len(pts) <= 3:
        return pts

    def dist(p, a, b):
        ax, ay = a
        bx, by = b
        px, py = p
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

    def rdp(points):
        if len(points) < 3:
            return points
        a, b = points[0], points[-1]
        max_d, idx = -1.0, 0
        for i in range(1, len(points) - 1):
            d = dist(points[i], a, b)
            if d > max_d:
                max_d, idx = d, i
        if max_d > tol:
            left = rdp(points[: idx + 1])
            right = rdp(points[idx:])
            return left[:-1] + right
        return [a, b]

    out = rdp(pts)
    if out[0] != out[-1]:
        out.append(out[0])
    return out


def iter_polygons(geom):
    if geom["type"] == "Polygon":
        yield geom["coordinates"]
    else:
        for poly in geom["coordinates"]:
            yield poly


def poly_area_bbox(outer):
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    return (max(xs) - min(xs)) * (max(ys) - min(ys)), xs, ys


def mean_point(pts):
    return (
        sum(p[0] for p in pts) / len(pts),
        sum(p[1] for p in pts) / len(pts),
    )


def scale_ring_xy(ring_xy, cx, cy, scale):
    if scale <= 1.001:
        return ring_xy
    out = []
    for x, y in ring_xy:
        out.append((cx + (x - cx) * scale, cy + (y - cy) * scale))
    return out


def ring_to_path(ring_xy):
    cmds = []
    for i, (x, y) in enumerate(ring_xy[:-1] if len(ring_xy) > 1 and ring_xy[0] == ring_xy[-1] else ring_xy):
        cmds.append(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}')
    if not cmds:
        return ""
    # ensure closed
    if ring_xy[0] != ring_xy[-1]:
        pass
    cmds.append("Z")
    return "".join(cmds)


def main():
    geo = load_geo()
    features = {}
    for f in geo["features"]:
        name = f["properties"].get("name")
        if name == "100000_JD" or str(f["properties"].get("adcode")) == "100000_JD":
            continue
        short = NAME_MAP.get(name)
        if short:
            features[short] = f

    # bbox for mainland-focused framing (still includes Hainan/Taiwan)
    all_pts = []
    for f in features.values():
        for poly in iter_polygons(f["geometry"]):
            for lon, lat in poly[0]:
                if 17.8 <= lat <= 54.0 and 73.0 <= lon <= 135.5:
                    all_pts.append((float(lon), float(lat)))
    minx = min(p[0] for p in all_pts)
    maxx = max(p[0] for p in all_pts)
    miny = min(p[1] for p in all_pts)
    maxy = max(p[1] for p in all_pts)

    W, H = 1134, 976
    PAD = 40
    LEGEND_W = 148
    MAP_W = W - PAD * 2 - LEGEND_W
    MAP_H = H - PAD * 2 - 48

    def project(lon, lat):
        x = (lon - minx) / (maxx - minx) * MAP_W + PAD
        y = (maxy - lat) / (maxy - miny) * MAP_H + PAD + 34
        return x, y

    def largest_outer(f):
        best, best_area = None, -1.0
        for poly in iter_polygons(f["geometry"]):
            outer = ring_to_pts(poly[0])
            area, _, _ = poly_area_bbox(outer)
            if area > best_area:
                best_area, best = area, outer
        return best, best_area

    def collect_rings(f, name):
        """Return list of lon/lat rings (outer only), simplified, largest first."""
        scored = []
        for poly in iter_polygons(f["geometry"]):
            outer = ring_to_pts(poly[0])
            area, _, _ = poly_area_bbox(outer)
            scored.append((area, outer))
        scored.sort(reverse=True)

        # Stylized simplify: stronger for big provinces, gentler for tiny ones
        if name in MIN_HALF and MIN_HALF[name] >= 12:
            tol, keep_n, min_area = 0.045, 6, 0.0
        elif name in {"新疆", "西藏", "内蒙古", "青海", "黑龙江", "四川", "云南", "甘肃"}:
            tol, keep_n, min_area = 0.16, 6, 0.04
        else:
            tol, keep_n, min_area = 0.11, 8, 0.02

        rings = []
        for area, outer in scored[:keep_n]:
            if area < min_area and len(scored) > 1:
                continue
            simp = simplify_ring(outer, tol)
            if len(simp) >= 4:
                rings.append(simp)
        if not rings and scored:
            rings.append(simplify_ring(scored[0][1], 0.03))
        return rings

    # First pass: project all rings, compute centroid & footprint
    projected = {}  # name -> list of rings in svg px
    centroids = {}
    for name in PROVINCES:
        f = features[name]
        rings_ll = collect_rings(f, name)
        rings_xy = []
        pts_all = []
        for ring in rings_ll:
            xy = [project(lon, lat) for lon, lat in ring]
            # close
            if xy[0] != xy[-1]:
                xy.append(xy[0])
            rings_xy.append(xy)
            pts_all.extend(xy[:-1])
        if not pts_all:
            continue
        cx, cy = mean_point(pts_all)
        centroids[name] = (cx, cy)

        # enlarge tiny footprints
        xs = [p[0] for p in pts_all]
        ys = [p[1] for p in pts_all]
        half_x = max(2.0, (max(xs) - min(xs)) / 2)
        half_y = max(2.0, (max(ys) - min(ys)) / 2)
        half = max(half_x, half_y)
        need = MIN_HALF.get(name, 0)
        scale = max(1.0, need / half) if need else 1.0
        # soft cap so we don't explode into neighbors too hard
        if name in {"北京", "天津"}:
            scale = min(scale, 2.8)
        elif name in {"香港", "澳门"}:
            scale = min(scale, 3.6)
        elif name == "上海":
            scale = min(scale, 2.6)
        else:
            scale = min(scale, 2.2)

        if scale > 1.0:
            rings_xy = [scale_ring_xy(r, cx, cy, scale) for r in rings_xy]
            # recompute centroid of scaled
            pts_all = []
            for r in rings_xy:
                pts_all.extend(r[:-1] if r[0] == r[-1] else r)
            centroids[name] = mean_point(pts_all)
            cx, cy = centroids[name]

        # Ultra-tiny leftovers (e.g. Macau fragments): replace with smooth blob
        pts_all = []
        for r in rings_xy:
            pts_all.extend(r[:-1] if r and r[0] == r[-1] else r)
        if pts_all:
            xs = [p[0] for p in pts_all]
            ys = [p[1] for p in pts_all]
            bw, bh = max(xs) - min(xs), max(ys) - min(ys)
            need = MIN_HALF.get(name, 0)
            if need and (bw < need * 1.2 or bh < need * 1.2):
                rx, ry = need * 1.15, need * 0.95
                # octagon-ish blob — stylized, easy to tap
                blob = []
                for i in range(12):
                    a = (i / 12) * math.tau
                    blob.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
                blob.append(blob[0])
                rings_xy = [blob]

        projected[name] = rings_xy

    # Optional: push 北京 / 天津 slightly apart after enlarge so they don't fully stack
    if "北京" in centroids and "天津" in centroids:
        bx, by = centroids["北京"]
        tx, ty = centroids["天津"]
        # nudge Tianjin SE, Beijing NW a bit
        def translate(rings, dx, dy):
            return [[(x + dx, y + dy) for x, y in ring] for ring in rings]

        projected["北京"] = translate(projected["北京"], -6, -8)
        projected["天津"] = translate(projected["天津"], 14, 12)
        centroids["北京"] = (bx - 6, by - 8)
        centroids["天津"] = (tx + 14, ty + 12)

    # Hong Kong / Macau: pull slightly SE of Guangdong coast if still tiny overlap
    if "香港" in centroids:
        hx, hy = centroids["香港"]
        projected["香港"] = [
            [(x + 6, y + 4) for x, y in ring] for ring in projected["香港"]
        ]
        centroids["香港"] = (hx + 6, hy + 4)
    if "澳门" in centroids:
        mx, my = centroids["澳门"]
        projected["澳门"] = [
            [(x - 2, y + 8) for x, y in ring] for ring in projected["澳门"]
        ]
        centroids["澳门"] = (mx - 2, my + 8)

    # Build paths (draw order: large first under, small on top for click)
    # We'll keep DOM order = PROVINCES for data-level string; SVG paint order can reverse small on top via CSS... 
    # Actually click uses DOM; paint later elements on top. Put small provinces later in PROVINCES already partially.
    # Reorder paint: append small ones last by sorting when writing? Keep id order for getElementById; 
    # use two groups: base + overlay small. Simpler: sort path emission large->small for paint, but 
    # provinceEls order must follow PROVINCES. So keep path id order as PROVINCES; CSS pointer-events ok.
    # For visibility of 京/津, move them to end of SVG group while keeping data order in JS via getElementById.
    paint_order = [n for n in PROVINCES if n not in MIN_HALF or MIN_HALF.get(n, 0) < 12]
    paint_order += [n for n in PROVINCES if n not in paint_order]

    path_nodes = []
    for name in paint_order:
        rings = projected.get(name, [])
        d = " ".join(ring_to_path(r) for r in rings if r)
        path_nodes.append(f'<path id="{name}" d="{d}"/>')

    label_nodes = []
    for name in PROVINCES:
        cx, cy = centroids[name]
        dx, dy = LABEL_TWEAK.get(name, (0, 0))
        x, y = cx + dx, cy + dy
        cls = ' class="fs22"' if MIN_HALF.get(name, 0) >= 12 else ""
        label_nodes.append(
            f'<text x="{x:.1f}" y="{y:.1f}"{cls} text-anchor="middle" dominant-baseline="middle">{name}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="中国省级制霸地图">
  <rect id="map-bg" x="0" y="0" width="{W}" height="{H}" fill="#B4CDEA"/>
  <text id="title" x="48" y="52">中国制霸</text>
  <g id="regions">
{chr(10).join("    " + p for p in path_nodes)}
  </g>
  <g id="labels">
{chr(10).join("    " + t for t in label_nodes)}
  </g>
  <text id="score" x="48" y="{H - 36}">分数: 0</text>
  <g id="legend">
    <path class="legend-swatch" data-level="5" fill="#C0394A" d="M{W - 140} 420h120v48H{W - 140}Z"/>
    <path class="legend-swatch" data-level="4" fill="#D96B42" d="M{W - 140} 468h120v48H{W - 140}Z"/>
    <path class="legend-swatch" data-level="3" fill="#E2B24A" d="M{W - 140} 516h120v48H{W - 140}Z"/>
    <path class="legend-swatch" data-level="2" fill="#5E9E98" d="M{W - 140} 564h120v48H{W - 140}Z"/>
    <path class="legend-swatch" data-level="1" fill="#8FA6C4" d="M{W - 140} 612h120v48H{W - 140}Z"/>
    <path class="legend-swatch" data-level="0" fill="#F3F5F7" d="M{W - 140} 660h120v48H{W - 140}Z"/>
    <path class="legend-border" fill="none" stroke="#2A3544" stroke-width="3" d="M{W - 140} 418h120v292H{W - 140}Z"/>
    <text x="{W - 124}" y="452">居住 5</text>
    <text x="{W - 124}" y="500">短居 4</text>
    <text x="{W - 124}" y="548">游玩 3</text>
    <text x="{W - 124}" y="596">落脚 2</text>
    <text x="{W - 124}" y="644">路过 1</text>
    <text x="{W - 126}" y="692">没去过</text>
  </g>
  <text id="credit" x="48" y="{H - 12}">cn-ex</text>
</svg>
'''
    OUT_SVG.write_text(svg, encoding="utf-8")
    OUT_INNER.write_text(svg, encoding="utf-8")
    empty = [n for n in PROVINCES if n not in projected or not projected[n]]
    print("wrote", OUT_SVG, "bytes", len(svg.encode()), "empty", empty)
    for n in ["北京", "天津", "上海", "香港", "澳门", "宁夏"]:
        rings = projected[n]
        pts = [p for r in rings for p in r]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        print(
            f"  {n}: bbox {max(xs)-min(xs):.1f}x{max(ys)-min(ys):.1f}px center=({centroids[n][0]:.0f},{centroids[n][1]:.0f})"
        )


if __name__ == "__main__":
    main()
