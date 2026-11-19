"""Render the GTA 6 "WANTED" meme poster (1080x1080) with Pillow.

Deterministic: no randomness, no network, no wall clock. The only input
is the official make.fun ghost at repo/assets/mark-1024.png; the output
is repo/meme.png. Run:  python3 meme.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SIZE = 1080
GHOST_PATH = HERE / "assets" / "mark-1024.png"
OUT_PATH = HERE / "meme.png"

# Vice City sunset: magenta -> orange -> teal, top to bottom.
STOPS = [
    (0.00, (214, 22, 110)),
    (0.38, (255, 94, 44)),
    (0.62, (255, 158, 44)),
    (1.00, (0, 128, 128)),
]

BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
REGULAR = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

GOLD = (255, 205, 0)
BLACK = (12, 10, 16)
WHITE = (255, 255, 255)
CREAM = (255, 244, 214)


def lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def gradient(size: int) -> Image.Image:
    """Vertical multi-stop gradient, filled one horizontal line per row."""
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)
    for y in range(size):
        pos = y / (size - 1)
        colour = STOPS[-1][1]
        for i in range(len(STOPS) - 1):
            p0, c0 = STOPS[i]
            p1, c1 = STOPS[i + 1]
            if p0 <= pos <= p1:
                t = 0.0 if p1 == p0 else (pos - p0) / (p1 - p0)
                colour = tuple(lerp(c0[k], c1[k], t) for k in range(3))
                break
        draw.line([(0, y), (size - 1, y)], fill=colour)
    return img


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def text_centred(
    draw: ImageDraw.ImageDraw,
    cx: int,
    y: int,
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    stroke: int = 0,
    stroke_fill: tuple[int, int, int] = BLACK,
) -> int:
    box = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    w = box[2] - box[0]
    h = box[3] - box[1]
    draw.text(
        (cx - w / 2 - box[0], y - box[1]),
        text,
        font=fnt,
        fill=fill,
        stroke_width=stroke,
        stroke_fill=stroke_fill,
    )
    return h


def star_points(cx: float, cy: float, outer: float, inner: float) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = outer if i % 2 == 0 else inner
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def _bezier(p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float], n: int = 16) -> list[tuple[float, float]]:
    """Points along a quadratic Bezier curve."""
    pts: list[tuple[float, float]] = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append(
            (
                u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1],
            )
        )
    return pts


def _frond(
    draw: ImageDraw.ImageDraw,
    crown: tuple[float, float],
    angle_deg: float,
    length: float,
    droop: float,
    lift: float,
) -> None:
    """One curved, tapered palm frond: it arches up from the crown, then
    droops down to a point, so it reads as a blade, not a stick."""
    a = math.radians(angle_deg)
    dx, dy = math.cos(a), math.sin(a)
    spine = _bezier(
        crown,
        (crown[0] + dx * length * 0.55, crown[1] + dy * length * 0.55 - lift),
        (crown[0] + dx * length, crown[1] + dy * length + droop),
    )
    left: list[tuple[float, float]] = []
    right: list[tuple[float, float]] = []
    n = len(spine) - 1
    for i, (x, y) in enumerate(spine):
        j = min(i + 1, n)
        k = max(i - 1, 0)
        tx, ty = spine[j][0] - spine[k][0], spine[j][1] - spine[k][1]
        m = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / m, tx / m
        w = 7.0 * (1 - i / n) + 0.5
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    draw.polygon(left + right[::-1], fill=BLACK)


def palm(draw: ImageDraw.ImageDraw, base_x: int, base_y: int, height: int, lean: int) -> None:
    """One black palm-tree silhouette, trunk curving inward to the crown.

    The crown is a fan of six arching, drooping blades plus a pair of
    coconuts, kept in the corner below the reward band so no frond
    touches any text.
    """
    crown = (base_x + lean, base_y - height)
    trunk = _bezier(
        (base_x, base_y),
        (base_x + lean * 0.3, base_y - height * 0.5),
        crown,
    )
    for i in range(len(trunk) - 1):
        w = round(13 - 5 * i / (len(trunk) - 1))
        draw.line([trunk[i], trunk[i + 1]], fill=BLACK, width=w)
    # Fronds fan over the top of the crown: (angle, length, droop, lift).
    # Angles use screen coords (0 = right, -90 = up); the set is
    # symmetric about straight up, so it suits both corners as-is.
    for angle, length, droop, lift in [
        (-168, 62, 20, 10),
        (-140, 58, 24, 14),
        (-108, 50, 26, 12),
        (-72, 50, 26, 12),
        (-40, 58, 24, 14),
        (-12, 62, 20, 10),
    ]:
        _frond(draw, crown, angle, length, droop, lift)
    # Two coconuts tucked under the crown on the inward side.
    s = 1 if lean >= 0 else -1
    draw.ellipse(
        [crown[0] + s * 2 - 6, crown[1] + 4, crown[0] + s * 2 + 6, crown[1] + 16],
        fill=BLACK,
    )
    draw.ellipse(
        [crown[0] + s * 13 - 5, crown[1] + 8, crown[0] + s * 13 + 5, crown[1] + 18],
        fill=BLACK,
    )


def main() -> None:
    img = gradient(SIZE)
    draw = ImageDraw.Draw(img, "RGBA")

    # Sun glow behind the ghost: a soft pale disc, low in the sky.
    draw.ellipse([340, 300, 740, 700], fill=(255, 214, 140, 90))

    # Five gold wanted stars across the top.
    for i in range(5):
        cx = 190 + i * 175
        draw.polygon(star_points(cx, 78, 52, 22), fill=GOLD, outline=BLACK)
        draw.line(star_points(cx, 78, 52, 22) + [star_points(cx, 78, 52, 22)[0]], fill=BLACK, width=4)

    # Huge WANTED headline.
    wanted = font(BOLD, 168)
    text_centred(draw, SIZE // 2, 132, "WANTED", wanted, WHITE, stroke=6)

    # The official ghost, large in the centre, on a white ring so the
    # magenta disc reads against the sunset.
    ghost = Image.open(GHOST_PATH).convert("RGBA").resize((500, 500), Image.LANCZOS)
    ring = Image.new("RGBA", (540, 540), (0, 0, 0, 0))
    ring_draw = ImageDraw.Draw(ring)
    ring_draw.ellipse([0, 0, 539, 539], fill=WHITE, outline=BLACK, width=10)
    img.paste(ring, (270, 300), ring)
    img.paste(ghost, (290, 320), ghost)
    draw = ImageDraw.Draw(img, "RGBA")

    # Dark band behind the reward lines so they stay readable.
    draw.rectangle([0, 838, SIZE, 962], fill=(12, 10, 16, 178))

    reward = font(BOLD, 54)
    text_centred(draw, SIZE // 2, 852, "REWARD: $500 IN BOUNTIES", reward, GOLD, stroke=2)
    seen = font(BOLD, 30)
    text_centred(
        draw,
        SIZE // 2,
        918,
        "LAST SEEN EARNING REAL MONEY ON make.fun",
        seen,
        CREAM,
        stroke=1,
    )

    # Palm silhouettes framing the bottom corners, kept below the dark
    # reward band so they never touch any text.
    palm(draw, 60, SIZE, 90, 30)
    palm(draw, SIZE - 60, SIZE, 90, -30)

    # make.fun name, large, at the bottom.
    name = font(BOLD, 96)
    text_centred(draw, SIZE // 2, 972, "make.fun", name, WHITE, stroke=4)

    img.save(OUT_PATH, format="PNG")
    print(f"wrote {OUT_PATH} ({SIZE}x{SIZE})")


if __name__ == "__main__":
    main()
