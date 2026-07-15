#!/usr/bin/env python3
"""Build accurate simplified province SVG from Aliyun DataV GeoJSON."""
import json, math, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
OUT_SVG = SRC / 'map-accurate.svg'
OUT_INNER = SRC / 'map-inner.html'
GEO_URL = 'https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json'
CACHE = Path('/tmp/china_full.json')

NAME_MAP = {
    '北京市': '北京', '天津市': '天津', '河北省': '河北', '山西省': '山西',
    '内蒙古自治区': '内蒙古', '辽宁省': '辽宁', '吉林省': '吉林', '黑龙江省': '黑龙江',
    '上海市': '上海', '江苏省': '江苏', '浙江省': '浙江', '安徽省': '安徽',
    '福建省': '福建', '江西省': '江西', '山东省': '山东', '河南省': '河南',
    '湖北省': '湖北', '湖南省': '湖南', '广东省': '广东', '广西壮族自治区': '广西',
    '海南省': '海南', '重庆市': '重庆', '四川省': '四川', '贵州省': '贵州',
    '云南省': '云南', '西藏自治区': '西藏', '陕西省': '陕西', '甘肃省': '甘肃',
    '青海省': '青海', '宁夏回族自治区': '宁夏', '新疆维吾尔自治区': '新疆',
    '台湾省': '台湾', '香港特别行政区': '香港', '澳门特别行政区': '澳门',
}
# URL order — do not change
PROVINCES = [
  '黑龙江', '甘肃', '吉林', '内蒙古', '山东', '河北', '北京', '天津',
  '西藏', '新疆', '河南', '安徽', '山西', '湖北', '青海', '辽宁',
  '广东', '江苏', '江西', '浙江', '福建', '上海', '陕西', '湖南',
  '广西', '香港', '澳门', '贵州', '重庆', '四川', '云南', '宁夏',
  '台湾', '海南',
]
SMALL = {'北京','天津','上海','香港','澳门','宁夏','海南','重庆','台湾'}
LABEL_TWEAK = {
    '北京': (0, -8), '天津': (10, 12), '上海': (14, 2), '香港': (16, 10),
    '澳门': (-2, 16), '海南': (0, 6), '重庆': (6, 2),
    '河北': (12, 18), '江苏': (8, 2), '内蒙古': (20, 10),
}

def load_geo():
    if not CACHE.exists():
        print('download', GEO_URL)
        urllib.request.urlretrieve(GEO_URL, CACHE)
    return json.loads(CACHE.read_text())

def ring_to_pts(ring):
    return [(float(x), float(y)) for x, y in ring]

def simplify_ring(pts, tol):
    if len(pts) <= 3:
        return pts
    def dist(p, a, b):
        ax, ay = a; bx, by = b; px, py = p
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
    def rdp(points):
        if len(points) < 3:
            return points
        a, b = points[0], points[-1]
        max_d, idx = -1, 0
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
    if geom['type'] == 'Polygon':
        yield geom['coordinates']
    else:
        for poly in geom['coordinates']:
            yield poly

def main():
    geo = load_geo()
    features = {}
    for f in geo['features']:
        name = f['properties'].get('name')
        if name == '100000_JD' or str(f['properties'].get('adcode')) == '100000_JD':
            continue
        short = NAME_MAP.get(name)
        if short:
            features[short] = f

    all_pts = []
    for f in features.values():
        for poly in iter_polygons(f['geometry']):
            for ring in poly:
                for x, y in ring:
                    if 17.5 <= y <= 54.5 and 73 <= x <= 136:
                        all_pts.append((x, y))
    minx = min(p[0] for p in all_pts)
    maxx = max(p[0] for p in all_pts)
    miny = min(p[1] for p in all_pts)
    maxy = max(p[1] for p in all_pts)

    W, H, PAD, LEGEND_W = 1134, 976, 36, 150
    MAP_W = W - PAD * 2 - LEGEND_W
    MAP_H = H - PAD * 2 - 40

    def project(lon, lat):
        x = (lon - minx) / (maxx - minx) * MAP_W + PAD
        y = (maxy - lat) / (maxy - miny) * MAP_H + PAD + 30
        return x, y

    def path_from_geom(geom, tol_deg, min_area=0.00001, keep_all=False):
        scored = []
        for poly in iter_polygons(geom):
            outer = ring_to_pts(poly[0])
            xs = [p[0] for p in outer]
            ys = [p[1] for p in outer]
            area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            scored.append((area, poly))
        scored.sort(reverse=True)
        keep_n = 40 if keep_all else 12
        parts = []
        for area, poly in scored[:keep_n]:
            if area < min_area and len(scored) > 1:
                continue
            simp = simplify_ring(ring_to_pts(poly[0]), tol_deg)
            if len(simp) < 3:
                continue
            cmds = []
            for i, (lon, lat) in enumerate(simp[:-1]):
                x, y = project(lon, lat)
                cmds.append(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}')
            cmds.append('Z')
            parts.append(''.join(cmds))
        return ' '.join(parts)

    def centroid(f):
        best, best_area = None, -1
        for poly in iter_polygons(f['geometry']):
            outer = ring_to_pts(poly[0])
            xs = [p[0] for p in outer]
            ys = [p[1] for p in outer]
            area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            if area > best_area:
                best_area, best = area, outer
        lon = sum(p[0] for p in best) / len(best)
        lat = sum(p[1] for p in best) / len(best)
        return project(lon, lat)

    paths, labels = {}, {}
    for name in PROVINCES:
        f = features[name]
        if name in SMALL:
            tol, min_area, keep_all = 0.02, 0.0, True
        elif name in {'新疆', '西藏', '内蒙古', '青海', '黑龙江', '四川', '云南', '甘肃'}:
            tol, min_area, keep_all = 0.11, 0.02, False
        else:
            tol, min_area, keep_all = 0.07, 0.008, False
        d = path_from_geom(f['geometry'], tol, min_area, keep_all)
        if not d:
            d = path_from_geom(f['geometry'], 0.01, 0.0, True)
        paths[name] = d
        lx, ly = centroid(f)
        dx, dy = LABEL_TWEAK.get(name, (0, 0))
        labels[name] = (lx + dx, ly + dy)

    region_paths = [f'<path id="{n}" d="{paths[n]}"/>' for n in PROVINCES]
    label_texts = []
    for name in PROVINCES:
        x, y = labels[name]
        cls = ' class="fs22"' if name in SMALL else ''
        label_texts.append(
            f'<text x="{x:.1f}" y="{y:.1f}"{cls} text-anchor="middle" dominant-baseline="middle">{name}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="中国省级制霸地图">
  <rect id="map-bg" x="0" y="0" width="{W}" height="{H}" fill="#B4CDEA"/>
  <text id="title" x="48" y="52">中国制霸</text>
  <g id="regions">
{chr(10).join('    ' + p for p in region_paths)}
  </g>
  <g id="labels">
{chr(10).join('    ' + t for t in label_texts)}
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
    OUT_SVG.write_text(svg, encoding='utf-8')
    OUT_INNER.write_text(svg, encoding='utf-8')
    empty = [n for n, p in paths.items() if not p]
    print('wrote', OUT_SVG, 'bytes', len(svg.encode()), 'empty', empty)

if __name__ == '__main__':
    main()
