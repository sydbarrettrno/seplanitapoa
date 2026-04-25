from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import fitz


DIM_TEXT_RE = re.compile(r"^\s*[0-9]+(?:[\.,][0-9]+)?\s*(?:m|cm|mm)?\s*$", re.IGNORECASE)


def parse_csv(v, n):
    p = [float(x.strip()) for x in v.split(",")]
    if len(p) != n:
        raise ValueError("CSV invalido")
    return p


def avg(c):
    return None if c is None else sum(c) / 3.0


def orange(c):
    if c is None:
        return False
    r, g, b = c
    return r > 0.75 and 0.25 < g < 0.60 and b < 0.25


def tx(x, ox):
    return x - ox


def ty(y, oy):
    return oy - y


def dev(x1, y1, x2, y2):
    a = abs(math.degrees(math.atan2(y2 - y1, x2 - x1))) % 180
    return min(min(abs(a), abs(180 - a)), abs(90 - a))


def add(out, x1, y1, x2, y2, layer):
    if math.hypot(x2 - x1, y2 - y1) >= 0.01:
        out.append((float(x1), float(y1), float(x2), float(y2), layer))


def oline(ln):
    x1, y1, x2, y2, layer = ln
    if abs(y1 - y2) <= abs(x1 - x2):
        return "h", (y1 + y2) / 2, min(x1, x2), max(x1, x2), layer
    return "v", (x1 + x2) / 2, min(y1, y2), max(y1, y2), layer


def mk(axis, coord, a, b, layer):
    if b - a < 0.01:
        return None
    return (a, coord, b, coord, layer) if axis == "h" else (coord, a, coord, b, layer)


def key(ln):
    x1, y1, x2, y2, layer = ln
    a = (round(x1, 3), round(y1, 3))
    b = (round(x2, 3), round(y2, 3))
    if b < a:
        a, b = b, a
    return a, b, layer


def clean(lines, coord_tol=0.25, gap_tol=0.15):
    unique = {key(ln): ln for ln in lines}
    groups = {}
    free = []
    for ln in unique.values():
        x1, y1, x2, y2, layer = ln
        if dev(x1, y1, x2, y2) > 3:
            free.append(ln)
            continue
        axis, coord, a, b, layer = oline(ln)
        bucket = round(coord / coord_tol) * coord_tol
        groups.setdefault((layer, axis, bucket), []).append((a, b, coord))
    out = []
    for (layer, axis, bucket), spans in groups.items():
        spans = sorted(spans)
        ca, cb, coords = spans[0][0], spans[0][1], [spans[0][2]]
        for a, b, coord in spans[1:]:
            if a <= cb + gap_tol:
                cb = max(cb, b)
                coords.append(coord)
            else:
                ln = mk(axis, sum(coords) / len(coords), ca, cb, layer)
                if ln:
                    out.append(ln)
                ca, cb, coords = a, b, [coord]
        ln = mk(axis, sum(coords) / len(coords), ca, cb, layer)
        if ln:
            out.append(ln)
    return list({key(ln): ln for ln in out + free}.values()), len(unique)


def is_dimension_text(text):
    t = " ".join((text or "").split())
    return bool(t) and bool(DIM_TEXT_RE.match(t))


def line_rect_distance(x1, y1, x2, y2, rect):
    rx1, ry1, rx2, ry2 = rect
    lx1, lx2 = min(x1, x2), max(x1, x2)
    ly1, ly2 = min(y1, y2), max(y1, y2)
    dx = max(rx1 - lx2, lx1 - rx2, 0.0)
    dy = max(ry1 - ly2, ly1 - ry2, 0.0)
    return math.hypot(dx, dy)


def extract_texts(page, clip, origin):
    texts = []
    tdict = page.get_text("dict", clip=clip)
    for block in tdict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                txt = (span.get("text") or "").strip()
                if not txt:
                    continue
                x0, y0, x1, y1 = span.get("bbox", (0.0, 0.0, 0.0, 0.0))
                cad_x = tx(x0, origin[0])
                cad_y = ty(y1, origin[1])
                bbox_cad = (tx(x0, origin[0]), ty(y1, origin[1]), tx(x1, origin[0]), ty(y0, origin[1]))
                texts.append(
                    {
                        "text": txt,
                        "x": cad_x,
                        "y": cad_y,
                        "height": max(1.0, float(span.get("size") or 2.5) * 0.35),
                        "layer": "A-TEXT",
                        "is_dim_text": is_dimension_text(txt),
                        "bbox": bbox_cad,
                    }
                )
    return texts


def classify_layer(base_layer, x1, y1, x2, y2, width, is_orange, dim_text_bboxes):
    if base_layer != "A-REF":
        return base_layer

    if is_orange:
        return "A-DIM"

    length = math.hypot(x2 - x1, y2 - y1)
    if length < 1.0 or length > 80.0:
        return base_layer

    if not (is_orange or width <= 0.35):
        return base_layer

    near_dim = any(line_rect_distance(x1, y1, x2, y2, rect) <= 45.0 for rect in dim_text_bboxes)
    if near_dim:
        return "A-DIM"

    return base_layer


def extract(pdf, page_i, view, origin):
    doc = fitz.open(pdf)
    page = doc[page_i]
    clip = fitz.Rect(*view)

    texts = extract_texts(page, clip, origin)
    dim_text_bboxes = [t["bbox"] for t in texts if t["is_dim_text"]]

    lines = []
    for d in page.get_drawings():
        if not clip.intersects(d["rect"]):
            continue
        color = d.get("color")
        bright = avg(color)
        is_orange = orange(color)
        width = float(d.get("width") or 0)
        for it in d.get("items", []):
            if it[0] == "l":
                _, p1, p2 = it
                x1, y1 = tx(p1.x, origin[0]), ty(p1.y, origin[1])
                x2, y2 = tx(p2.x, origin[0]), ty(p2.y, origin[1])
                length = math.hypot(x2 - x1, y2 - y1)
                wall = (
                    not is_orange
                    and dev(x1, y1, x2, y2) <= 6
                    and length >= 2
                    and not (bright is not None and bright > 0.72 and width < 0.15)
                )
                base_layer = "A-WALL" if wall else "A-REF"
                layer = classify_layer(base_layer, x1, y1, x2, y2, width, is_orange, dim_text_bboxes)
                add(lines, x1, y1, x2, y2, layer)
            elif it[0] == "re":
                _, r, _ = it
                x = tx(r.x0, origin[0])
                y = ty(r.y1, origin[1])
                w, h = r.width, r.height
                base_layer = "A-REF" if is_orange else "A-WALL"
                layer = classify_layer(base_layer, x, y, x + w, y, width, is_orange, dim_text_bboxes)
                add(lines, x, y, x + w, y, layer)
                add(lines, x + w, y, x + w, y + h, layer)
                add(lines, x + w, y + h, x, y + h, layer)
                add(lines, x, y + h, x, y, layer)

    doc.close()
    return lines, texts


def write_dxf(path, lines, texts):
    xs = [v for x1, y1, x2, y2, l in lines for v in (x1, x2)] + [t["x"] for t in texts]
    ys = [v for x1, y1, x2, y2, l in lines for v in (y1, y2)] + [t["y"] for t in texts]
    xs = xs or [0, 1]
    ys = ys or [0, 1]

    layers = sorted(set([l for *_, l in lines] + [t["layer"] for t in texts])) or ["A-WALL"]
    rows = []

    def add(c, v):
        rows.extend([str(c), f"{v:.6f}" if isinstance(v, float) else str(v)])

    add(0, "SECTION")
    add(2, "HEADER")
    add(9, "$ACADVER")
    add(1, "AC1009")
    add(9, "$EXTMIN")
    add(10, min(xs))
    add(20, min(ys))
    add(30, 0.0)
    add(9, "$EXTMAX")
    add(10, max(xs))
    add(20, max(ys))
    add(30, 0.0)
    add(0, "ENDSEC")

    add(0, "SECTION")
    add(2, "TABLES")
    add(0, "TABLE")
    add(2, "LTYPE")
    add(70, 1)
    add(0, "LTYPE")
    add(2, "CONTINUOUS")
    add(70, 64)
    add(3, "Solid line")
    add(72, 65)
    add(73, 0)
    add(40, 0.0)
    add(0, "ENDTAB")

    add(0, "TABLE")
    add(2, "LAYER")
    add(70, len(layers))
    colors = {"A-WALL": 7, "A-REF": 8, "A-DIM": 6, "A-TEXT": 3}
    for layer in layers:
        add(0, "LAYER")
        add(2, layer)
        add(70, 0)
        add(62, colors.get(layer, 7))
        add(6, "CONTINUOUS")
    add(0, "ENDTAB")
    add(0, "ENDSEC")

    add(0, "SECTION")
    add(2, "ENTITIES")
    for x1, y1, x2, y2, layer in lines:
        add(0, "LINE")
        add(8, layer)
        add(10, x1)
        add(20, y1)
        add(30, 0.0)
        add(11, x2)
        add(21, y2)
        add(31, 0.0)
    for t in texts:
        add(0, "TEXT")
        add(8, t["layer"])
        add(10, float(t["x"]))
        add(20, float(t["y"]))
        add(30, 0.0)
        add(40, float(t["height"]))
        add(1, t["text"])
        add(50, 0.0)
    add(0, "ENDSEC")
    add(0, "EOF")

    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_svg(path, lines, texts):
    xs = [v for x1, y1, x2, y2, l in lines for v in (x1, x2)] + [t["x"] for t in texts]
    ys = [v for x1, y1, x2, y2, l in lines for v in (y1, y2)] + [t["y"] for t in texts]
    xs = xs or [0, 1]
    ys = ys or [0, 1]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w = max(50, maxx - minx + 40)
    h = max(50, maxy - miny + 40)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(w)}" height="{int(h)}" viewBox="0 0 {w:.2f} {h:.2f}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<g transform="translate({20 - minx:.2f},{20 - miny:.2f})">',
    ]
    for x1, y1, x2, y2, l in lines:
        if l == "A-WALL":
            col = "#111"
            sw = "0.9"
        elif l == "A-DIM":
            col = "#f39c12"
            sw = "0.55"
        else:
            col = "#999"
            sw = "0.45"
        out.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="{sw}"/>'
        )
    for t in texts:
        out.append(
            f'<text x="{t["x"]:.2f}" y="{t["y"]:.2f}" fill="#2c7" font-size="{max(6.0, t["height"] * 2.4):.2f}" font-family="Arial">{t["text"]}</text>'
        )
    out += ["</g></svg>"]
    path.write_text("\n".join(out), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Motor V07.3 conservative DIM/TEXT layer split")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--page", type=int, default=0)
    ap.add_argument("--view", default="240,450,1160,1640")
    ap.add_argument("--origin", default="280,1600")
    ap.add_argument("--outdir", default="output")
    ap.add_argument("--name", default="Mallmann06_1Pavimento_V073")
    args = ap.parse_args()

    view = parse_csv(args.view, 4)
    origin = parse_csv(args.origin, 2)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    raw, texts = extract(args.pdf, args.page, view, origin)
    cleaned, unique_count = clean(raw)

    dxf = out / f"{args.name}.dxf"
    svg = out / f"{args.name}.svg"
    write_dxf(dxf, cleaned, texts)
    write_svg(svg, cleaned, texts)

    layer_counts = {
        "A-WALL": sum(1 for *_, l in cleaned if l == "A-WALL"),
        "A-REF": sum(1 for *_, l in cleaned if l == "A-REF"),
        "A-DIM": sum(1 for *_, l in cleaned if l == "A-DIM"),
    }
    text_counts = {
        "A-TEXT": len(texts),
        "dimension_like_texts": sum(1 for t in texts if t["is_dim_text"]),
        "non_dimension_texts": sum(1 for t in texts if not t["is_dim_text"]),
    }

    report = {
        "motor": "V07.3 Conservative DIM/TEXT Split",
        "base": "V07.2 Clean Native Export",
        "rules": "Conservative promotion: uncertain entities remain A-REF",
        "raw_lines": len(raw),
        "unique_input_lines": unique_count,
        "final_lines": len(cleaned),
        "removed_or_merged_before_export": len(raw) - len(cleaned),
        "line_layers": layer_counts,
        "text_layers": text_counts,
        "dxf": str(dxf),
        "svg": str(svg),
        "dxf_format": "R12 / AC1009",
        "target": "AutoCAD 2026",
    }
    (out / f"{args.name}_relatorio.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / f"{args.name}_relatorio.txt").write_text(
        "\n".join(
            [
                "Motor V07.3 Conservative DIM/TEXT Split",
                "Base: V07.2 Clean Native Export",
                f"Linhas brutas: {len(raw)}",
                f"Linhas únicas: {unique_count}",
                f"Linhas finais: {len(cleaned)}",
                f"Removidas/fundidas antes do DXF: {len(raw)-len(cleaned)}",
                f"A-WALL: {layer_counts['A-WALL']}",
                f"A-REF: {layer_counts['A-REF']}",
                f"A-DIM: {layer_counts['A-DIM']}",
                f"A-TEXT: {text_counts['A-TEXT']}",
                f"Textos com padrão de cota: {text_counts['dimension_like_texts']}",
                f"Textos não-cota: {text_counts['non_dimension_texts']}",
                f"DXF: {dxf}",
                f"SVG: {svg}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("Concluído.")
    print("DXF:", dxf)
    print("Relatório:", out / f"{args.name}_relatorio.json")


if __name__ == "__main__":
    main()
