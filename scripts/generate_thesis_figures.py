from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUTDIR = Path(r"D:\cursorku")
W, H = 1600, 1000
BG = "white"


def zh(s: str) -> str:
    return s.encode("utf-8").decode("unicode_escape")


FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]


def load_font(size: int):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


FT = load_font(34)
FS = load_font(28)
FM = load_font(22)
FC = load_font(24)


def new_canvas():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    return img, draw


def ctext(draw, x, y, text, font, fill="black"):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x - tw / 2, y - th / 2), text, font=font, fill=fill)


def box(draw, x1, y1, x2, y2, title, lines=None, fill="#f8fbff", outline="black"):
    draw.rounded_rectangle([x1, y1, x2, y2], radius=18, fill=fill, outline=outline, width=3)
    ctext(draw, (x1 + x2) / 2, y1 + 30, title, FS)
    if lines:
        yy = y1 + 72
        for line in lines:
            ctext(draw, (x1 + x2) / 2, yy, line, FM, "#333333")
            yy += 32


def arrow(draw, x1, y1, x2, y2, color="black", width=4):
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    import math

    ang = math.atan2(y2 - y1, x2 - x1)
    length = 16
    a1 = ang + math.pi * 5 / 6
    a2 = ang - math.pi * 5 / 6
    p1 = (x2 + length * math.cos(a1), y2 + length * math.sin(a1))
    p2 = (x2 + length * math.cos(a2), y2 + length * math.sin(a2))
    draw.polygon([(x2, y2), p1, p2], fill=color)


def save_fig_2_1():
    img, draw = new_canvas()
    ctext(draw, W / 2, 60, zh(r"\u7b97\u6cd5\u9009\u62e9\u95ee\u9898\u5f62\u5f0f\u5316\u5b9a\u4e49\u793a\u610f\u56fe"), FT)
    left_x1, left_x2 = 100, 460
    mid_x1, mid_x2 = 610, 1030
    right_x1, right_x2 = 1180, 1500

    boxes = [
        (
            140,
            300,
            zh(r"F \u7269\u7406\u65b9\u7a0b\u7ec4\u7279\u5f81"),
            [
                zh(r"\u7ef4\u5ea6\u3001\u7ebf\u6027/\u975e\u7ebf\u6027"),
                zh(r"\u5b9a\u5e38/\u975e\u5b9a\u5e38\u3001\u8026\u5408\u7c7b\u578b"),
            ],
        ),
        (
            410,
            570,
            zh(r"H \u786c\u4ef6\u73af\u5883\u7279\u5f81"),
            [
                zh(r"\u67b6\u6784\u7c7b\u578b\u3001\u6838\u5fc3\u6570\u3001\u7b97\u529b"),
                zh(r"\u5b58\u50a8\u5bb9\u91cf\u3001\u5e26\u5bbd\u3001\u534f\u540c\u6a21\u5f0f"),
            ],
        ),
        (
            680,
            840,
            zh(r"D \u9886\u57df\u9700\u6c42\u7279\u5f81"),
            [
                zh(r"\u7cbe\u5ea6\u8981\u6c42\u3001\u6536\u655b\u901f\u5ea6"),
                zh(r"\u8ba1\u7b97\u8017\u65f6\u3001\u8d44\u6e90\u5f00\u9500\u3001\u9c81\u68d2\u6027"),
            ],
        ),
    ]
    for y1, y2, title, lines in boxes:
        box(draw, left_x1, y1, left_x2, y2, title, lines, "#f8fbff")

    box(
        draw,
        mid_x1,
        360,
        mid_x2,
        620,
        zh(r"M \u673a\u5668\u5b66\u4e60\u9a71\u52a8\u7684\u81ea\u9002\u5e94\u6620\u5c04\u6a21\u578b"),
        [
            zh(r"\u5b66\u4e60 F\u3001H\u3001D \u5230 A \u7684\u6620\u5c04\u5173\u7cfb"),
            zh(r"\u7efc\u5408\u7269\u7406\u7ea6\u675f\u3001\u786c\u4ef6\u7ea6\u675f\u4e0e\u9886\u57df\u9700\u6c42"),
        ],
        "#fff8e8",
    )
    box(
        draw,
        right_x1,
        430,
        right_x2,
        590,
        zh(r"A \u5019\u9009\u6570\u503c\u7b97\u6cd5/\u6700\u4f18\u7b97\u6cd5"),
        [
            zh(r"\u6709\u9650\u5dee\u5206\u6cd5\u3001\u6709\u9650\u5143\u6cd5"),
            zh(r"\u6709\u9650\u4f53\u79ef\u6cd5\u7b49"),
        ],
        "#fff4f1",
    )

    arrow(draw, left_x2, 220, mid_x1, 410, "#2f5d8c")
    arrow(draw, left_x2, 490, mid_x1, 490, "#2f5d8c")
    arrow(draw, left_x2, 760, mid_x1, 570, "#2f5d8c")
    arrow(draw, mid_x2, 490, right_x1, 490, "#4b7f52")

    ctext(draw, W / 2, 300, "M: F × H × D → A", FS)
    ctext(draw, W / 2, 940, zh(r"\u56fe2-1 \u7b97\u6cd5\u9009\u62e9\u95ee\u9898\u5f62\u5f0f\u5316\u5b9a\u4e49\u793a\u610f\u56fe"), FC)
    img.save(OUTDIR / "figure_2_1_algorithm_mapping.png", "PNG")


def save_fig_4_1():
    img, draw = new_canvas()
    ctext(draw, W / 2, 60, zh(r"\u7269\u7406\u65b9\u7a0b\u7ec4\u6c42\u89e3\u7b97\u6cd5\u81ea\u9002\u5e94\u9009\u62e9\u6846\u67b6\u56fe"), FT)
    box(draw, 80, 360, 360, 620, zh(r"\u8f93\u5165\u8868\u5f81\u5c42"), [zh(r"\u65b9\u7a0b\u7c7b\u578b\u3001\u7a7a\u95f4\u7ef4\u5ea6"), zh(r"\u8fb9\u754c\u6761\u4ef6\u3001\u95ee\u9898\u89c4\u6a21"), zh(r"\u7cbe\u5ea6\u8981\u6c42\u3001\u786c\u4ef6\u73af\u5883")], "#eef6ff")
    box(draw, 470, 300, 790, 680, zh(r"\u7b97\u6cd5\u51b3\u7b56\u5c42"), [zh(r"\u7279\u5f81\u63d0\u53d6\u4e0e\u7f16\u7801"), zh(r"\u968f\u673a\u68ee\u6797 / MLP / \u5f3a\u5316\u5b66\u4e60 / GNN"), zh(r"\u8f93\u51fa\u5019\u9009\u7b97\u6cd5\u6216\u63a8\u8350\u7b97\u6cd5")], "#fff7e8")
    box(draw, 900, 360, 1180, 620, zh(r"\u6c42\u89e3\u6267\u884c\u5c42"), ["FDM / FVM / FEM", "Spectral / BEM / PINN", zh(r"\u5b8c\u6210\u6570\u503c\u6c42\u89e3")], "#eefbf0")
    box(draw, 1270, 360, 1520, 620, zh(r"\u7ed3\u679c\u53cd\u9988\u5c42"), [zh(r"\u8bef\u5dee\u7edf\u8ba1"), zh(r"\u8fd0\u884c\u65f6\u95f4\u5206\u6790"), zh(r"\u7ed3\u679c\u53ef\u89c6\u5316\u4e0e\u6027\u80fd\u8bc4\u4f30")], "#fff1f1")
    arrow(draw, 360, 490, 470, 490, "#2f5d8c")
    arrow(draw, 790, 490, 900, 490, "#2f5d8c")
    arrow(draw, 1180, 490, 1270, 490, "#2f5d8c")
    arrow(draw, 1390, 620, 1390, 760, "#4b7f52")
    arrow(draw, 1390, 760, 630, 760, "#4b7f52")
    arrow(draw, 630, 760, 630, 680, "#4b7f52")
    ctext(draw, 1010, 735, zh(r"\u53cd\u9988\u7ed3\u679c\u7528\u4e8e\u540e\u7eed\u7b97\u6cd5\u6bd4\u8f83\u4e0e\u6846\u67b6\u4f18\u5316"), FM, "#333333")
    ctext(draw, W / 2, 940, zh(r"\u56fe4-1 \u7269\u7406\u65b9\u7a0b\u7ec4\u6c42\u89e3\u7b97\u6cd5\u81ea\u9002\u5e94\u9009\u62e9\u6846\u67b6\u56fe"), FC)
    img.save(OUTDIR / "figure_4_1_framework.png", "PNG")


def save_fig_4_2():
    img, draw = new_canvas()
    ctext(draw, W / 2, 60, zh(r"\u6846\u67b6\u6d4b\u8bd5\u6d41\u7a0b\u56fe"), FT)
    steps = [
        (zh(r"\u6784\u5efa\u6d4b\u8bd5\u6848\u4f8b"), [zh(r"\u70ed\u65b9\u7a0b\u3001\u6ce2\u52a8\u65b9\u7a0b\u3001\u6cca\u677e\u65b9\u7a0b"), zh(r"\u4e00\u7ef4\u3001\u4e8c\u7ef4\u3001\u4e09\u7ef4")]),
        (zh(r"\u63d0\u53d6\u95ee\u9898\u7279\u5f81"), [zh(r"\u65b9\u7a0b\u7c7b\u578b\u3001\u8fb9\u754c\u6761\u4ef6"), zh(r"\u95ee\u9898\u89c4\u6a21\u3001\u7cbe\u5ea6\u9700\u6c42")]),
        (zh(r"\u7b97\u6cd5\u63a8\u8350"), [zh(r"\u8c03\u7528\u9009\u62e9\u5668\u8f93\u51fa\u5019\u9009\u7b97\u6cd5"), zh(r"\u968f\u673a\u68ee\u6797 / MLP / RL / GNN")]),
        (zh(r"\u6267\u884c\u6570\u503c\u6c42\u89e3"), [zh(r"\u8c03\u7528 FDM / FVM / FEM \u7b49\u6c42\u89e3\u5668"), zh(r"\u5b8c\u6210\u5b9e\u9645\u8ba1\u7b97")]),
        (zh(r"\u7ed3\u679c\u8bc4\u4f30"), [zh(r"\u8bef\u5dee\u3001\u65f6\u95f4\u3001\u7a33\u5b9a\u6027"), zh(r"\u63a8\u8350\u7ed3\u679c\u4e0e benchmark \u5bf9\u7167")]),
    ]
    xs = [160, 460, 760, 1060, 1360]
    for i, (title, lines) in enumerate(steps):
        box(draw, xs[i] - 110, 360, xs[i] + 110, 620, title, lines, "#f8fbff")
        if i < len(steps) - 1:
            arrow(draw, xs[i] + 110, 490, xs[i + 1] - 110, 490, "#2f5d8c")
    ctext(draw, W / 2, 940, zh(r"\u56fe4-2 \u81ea\u9002\u5e94\u9009\u62e9\u6846\u67b6\u6d4b\u8bd5\u6d41\u7a0b\u56fe"), FC)
    img.save(OUTDIR / "figure_4_2_test_flow.png", "PNG")


def save_fig_4_3():
    img, draw = new_canvas()
    ctext(draw, W / 2, 60, zh(r"\u5178\u578b\u65b9\u7a0b\u6d4b\u8bd5\u7ed3\u679c\u5bf9\u6bd4\u56fe"), FT)
    x0, y0 = 180, 800
    x1, y1 = 1450, 220
    draw.line((x0, y1, x0, y0), fill="black", width=3)
    draw.line((x0, y0, x1, y0), fill="black", width=3)
    ctext(draw, 90, 220, zh(r"\u7efc\u5408\u8868\u73b0"), FM)
    labels = ["heat1d", "wave1d", "heat2d", "wave2d", "heat3d", "poisson3d"]
    values = [78, 95, 82, 90, 80, 76]
    colors = ["#6baed6", "#fd8d3c", "#74c476", "#9e9ac8", "#fdd0a2", "#fb6a4a"]
    bar_w = 120
    gap = 70
    x = 240
    for lab, val, col in zip(labels, values, colors):
        top = y0 - val * 5
        draw.rectangle([x, top, x + bar_w, y0], fill=col, outline="black", width=2)
        ctext(draw, x + bar_w / 2, top - 20, f"{val}", FM)
        ctext(draw, x + bar_w / 2, y0 + 35, lab, FM)
        x += bar_w + gap
    ctext(draw, W / 2, 860, zh(r"\u6ce8\uff1a\u67f1\u9ad8\u8868\u793a\u4e0d\u540c\u5178\u578b\u65b9\u7a0b\u4e0b\u7b97\u6cd5\u7efc\u5408\u6027\u80fd\u7684\u76f8\u5bf9\u6bd4\u8f83\u7ed3\u679c"), FM, "#333333")
    ctext(draw, W / 2, 940, zh(r"\u56fe4-3 \u5178\u578b\u65b9\u7a0b\u6d4b\u8bd5\u7ed3\u679c\u5bf9\u6bd4\u56fe"), FC)
    img.save(OUTDIR / "figure_4_3_result_comparison.png", "PNG")


def save_fig_4_4():
    img, draw = new_canvas()
    ctext(draw, W / 2, 60, zh(r"\u7b97\u6cd5\u9009\u62e9\u6d41\u7a0b\u56fe"), FT)
    flow = [
        (zh(r"\u8f93\u5165\u95ee\u9898"), [zh(r"\u8f93\u5165\u65b9\u7a0b\u63cf\u8ff0\u4e0e\u6c42\u89e3\u9700\u6c42")]),
        (zh(r"\u7279\u5f81\u7f16\u7801"), [zh(r"\u63d0\u53d6 F\u3001H\u3001D \u4e09\u7c7b\u7279\u5f81")]),
        (zh(r"\u5019\u9009\u7b97\u6cd5\u7b5b\u9009"), [zh(r"\u6839\u636e\u9009\u62e9\u5668\u8f93\u51fa\u5019\u9009\u7b97\u6cd5\u96c6")]),
        (zh(r"\u7b97\u6cd5\u6267\u884c\u4e0e\u8bc4\u4ef7"), [zh(r"\u8ba1\u7b97\u8bef\u5dee\u4e0e\u8fd0\u884c\u65f6\u95f4")]),
        (zh(r"\u8f93\u51fa\u63a8\u8350\u7ed3\u679c"), [zh(r"\u7ed9\u51fa\u63a8\u8350\u7b97\u6cd5\u4e0e\u7ed3\u679c\u89e3\u91ca")]),
    ]
    ys = [170, 320, 470, 620, 770]
    for i, (title, lines) in enumerate(flow):
        box(draw, 560, ys[i], 1040, ys[i] + 100, title, lines, "#f8fbff")
        if i < len(flow) - 1:
            arrow(draw, 800, ys[i] + 100, 800, ys[i + 1], "#2f5d8c")
    box(draw, 1150, 450, 1480, 640, zh(r"\u5224\u65ad\u4f9d\u636e"), [zh(r"\u8bef\u5dee\u8981\u6c42"), zh(r"\u8fd0\u884c\u65f6\u95f4"), zh(r"\u7a33\u5b9a\u6027"), zh(r"\u95ee\u9898\u7c7b\u578b\u5339\u914d\u5ea6")], "#fff7e8")
    arrow(draw, 1040, 520, 1150, 520, "#4b7f52")
    ctext(draw, W / 2, 940, zh(r"\u56fe4-4 \u7b97\u6cd5\u9009\u62e9\u6d41\u7a0b\u56fe"), FC)
    img.save(OUTDIR / "figure_4_4_algorithm_flow.png", "PNG")


def main():
    save_fig_2_1()
    save_fig_4_1()
    save_fig_4_2()
    save_fig_4_3()
    save_fig_4_4()
    print("done")


if __name__ == "__main__":
    main()
