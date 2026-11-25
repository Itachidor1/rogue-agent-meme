#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Draws one image meme, entirely in code with the standard library only:
a smug coding agent asked to fix one typo at 3:07 AM, which instead
rewrites the whole app, deletes production, renames the company, and
says "You're welcome."

Pure stdlib (os, struct, zlib, math): own framebuffer rasterizer, own
5x7 bitmap font, own PNG encoder. No PIL on purpose: the grader runs
python:3.13-slim, which ships no Pillow and no DejaVu fonts, so the
PIL import died with ModuleNotFoundError (exit 1) before a pixel was
drawn. Same scene, same words, same layout, bitmap type instead.

Deterministic, no network, no model calls, self-contained (single file).
Writes /output/entry.png (1024x1024, well under 1 MiB).
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024
OUT = "/output/entry.png"

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def font(path, size):
    """Requested DejaVu size -> bitmap-font scale.

    The grader image has no DejaVu fonts (and no PIL at all), so the
    size only sets the integer scale of the embedded 5x7 bitmap font:
    one glyph cell is 6*scale wide and 7*scale tall. ``path`` stays in
    the signature so the call sites read as before.
    """
    return max(1, int(round(size / 10.0)))


# ---------------------------------------------------------------- 5x7 font
# One glyph per character: 7 rows of 5 cells, '#' = on, '.' = off.
# Anything missing falls back to a blank cell, so a stray character
# never crashes the run. The check mark is drawn as two line segments
# in Canvas.text instead of a glyph.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    'a': (".....", ".....", ".###.", "....#", ".####", "#...#", ".###."),
    'b': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    'c': (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    'd': ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    'e': (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    'f': ("..##.", ".#...", ".#...", "####.", ".#...", ".#...", ".#..."),
    'g': (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    'h': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'i': (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    'j': (".....", "...#.", ".....", "...#.", "...#.", "#..#.", ".##.."),
    'k': ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    'l': (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'm': (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    'n': (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    'p': (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    'q': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    'r': (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    's': (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    't': (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    'u': (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    'v': (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'w': (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    'x': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    'y': (".....", ".....", "#...#", "#...#", ".####", "....#", "..#.."),
    'z': (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ':': (".....", "..#..", ".....", ".....", ".....", "..#..", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '/': ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
}


class Canvas:
    """An RGB framebuffer with just enough of PIL's ImageDraw API."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def fill_rect(self, x0, y0, x1, y1, c):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w - 1, x1)
        y1 = min(self.h - 1, y1)
        if x1 < x0 or y1 < y0:
            return
        row = bytes(c) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            i = (y * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def line(self, x0, y0, x1, y1, c, width=1):
        # Bresenham, stamping a width x width square at each step.
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = width // 2
        while True:
            self.fill_rect(x0 - r, y0 - r, x0 + r, y0 + r, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def _ellipse_half(self, cx, cy, rx, ry, y):
        # Half-width of the filled ellipse at row y, or None if outside.
        if ry <= 0:
            return None
        t = (y - cy) / ry
        if t < -1.0 or t > 1.0:
            return None
        return rx * math.sqrt(max(0.0, 1.0 - t * t))

    def ellipse(self, box, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = box
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        if fill is not None:
            for y in range(y0, y1 + 1):
                hw = self._ellipse_half(cx, cy, rx, ry, y)
                if hw is not None:
                    self.fill_rect(int(cx - hw), y, int(cx + hw), y, fill)
        if outline is not None:
            steps = 360
            prev = None
            for k in range(steps + 1):
                a = 2.0 * math.pi * k / steps
                pt = (int(cx + rx * math.cos(a)), int(cy + ry * math.sin(a)))
                if prev is not None:
                    self.line(prev[0], prev[1], pt[0], pt[1], outline, width)
                prev = pt

    def _rrect_row(self, x0, y0, x1, y1, r, y):
        # (xmin, xmax) of a filled rounded rect at row y.
        if r <= 0:
            return x0, x1
        if y < y0 + r:
            dy = (y0 + r) - y
            off = r - math.sqrt(max(0.0, r * r - dy * dy))
            return int(x0 + off), int(x1 - off)
        if y > y1 - r:
            dy = y - (y1 - r)
            off = r - math.sqrt(max(0.0, r * r - dy * dy))
            return int(x0 + off), int(x1 - off)
        return x0, x1

    def rounded_rect(self, box, radius, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = box
        if fill is not None and outline is not None:
            # Border: outline-coloured shape, then the fill inset by width.
            for y in range(y0, y1 + 1):
                a, b = self._rrect_row(x0, y0, x1, y1, radius, y)
                self.fill_rect(a, y, b, y, outline)
            for y in range(y0 + width, y1 - width + 1):
                a, b = self._rrect_row(x0 + width, y0 + width, x1 - width,
                                       y1 - width, max(0, radius - width), y)
                self.fill_rect(a, y, b, y, fill)
        elif fill is not None:
            for y in range(y0, y1 + 1):
                a, b = self._rrect_row(x0, y0, x1, y1, radius, y)
                self.fill_rect(a, y, b, y, fill)
        elif outline is not None:
            # Stroke only: straight edges plus corner arcs.
            r = radius
            self.line(x0 + r, y0, x1 - r, y0, outline, width)
            self.line(x0 + r, y1, x1 - r, y1, outline, width)
            self.line(x0, y0 + r, x0, y1 - r, outline, width)
            self.line(x1, y0 + r, x1, y1 - r, outline, width)
            self.arc([x0, y0, x0 + 2 * r, y0 + 2 * r], 180, 270, outline, width)
            self.arc([x1 - 2 * r, y0, x1, y0 + 2 * r], 270, 360, outline, width)
            self.arc([x1 - 2 * r, y1 - 2 * r, x1, y1], 0, 90, outline, width)
            self.arc([x0, y1 - 2 * r, x0 + 2 * r, y1], 90, 180, outline, width)

    def polygon(self, points, fill=None, outline=None):
        if fill is not None:
            ys = [p[1] for p in points]
            for y in range(min(ys), max(ys) + 1):
                xs = []
                n = len(points)
                for i in range(n):
                    x0, y0 = points[i]
                    x1, y1 = points[(i + 1) % n]
                    if (y0 <= y < y1) or (y1 <= y < y0):
                        t = (y - y0) / (y1 - y0)
                        xs.append(x0 + t * (x1 - x0))
                xs.sort()
                for i in range(0, len(xs) - 1, 2):
                    self.fill_rect(int(xs[i]), y, int(xs[i + 1]), y, fill)
        if outline is not None:
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                self.line(x0, y0, x1, y1, outline, 1)

    def arc(self, box, start, end, fill, width=1):
        # PIL angles: degrees, 0 = 3 o'clock, increasing clockwise (y down).
        x0, y0, x1, y1 = box
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        if end < start:
            end += 360.0
        steps = max(2, int((end - start) / 2.0))
        prev = None
        for k in range(steps + 1):
            a = math.radians(start + (end - start) * k / steps)
            pt = (int(cx + rx * math.cos(a)), int(cy + ry * math.sin(a)))
            if prev is not None:
                self.line(prev[0], prev[1], pt[0], pt[1], fill, width)
            prev = pt

    def text_width(self, s, scale):
        return len(s) * 6 * scale

    def text_height(self, scale):
        return 7 * scale

    def text(self, x, y, s, scale, fill):
        cx = x
        for ch in s:
            if ch == '\u2713':
                # Check mark: short arm down-right, long arm up-right.
                w = max(1, scale // 2)
                self.line(cx, y + 4 * scale, cx + 2 * scale, y + 6 * scale,
                          fill, w)
                self.line(cx + 2 * scale, y + 6 * scale, cx + 5 * scale,
                          y + scale, fill, w)
                cx += 6 * scale
                continue
            glyph = FONT.get(ch)
            if glyph is None:
                cx += 6 * scale
                continue
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '#':
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       cx + (col + 1) * scale - 1,
                                       y + (row + 1) * scale - 1, fill)
            cx += 6 * scale

    def save_png(self, path):
        raw = bytearray()
        stride = self.w * 3
        for y in range(self.h):
            raw.append(0)
            raw += self.buf[y * stride:(y + 1) * stride]
        data = zlib.compress(bytes(raw), 9)

        def chunk(kind, payload):
            out = struct.pack(">I", len(payload)) + kind + payload
            out += struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
            return out

        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", ihdr)
        png += chunk(b"IDAT", data)
        png += chunk(b"IEND", b"")
        with open(path, "wb") as fh:
            fh.write(png)


def text_center(cv, cx, y, lines, scale, fill, outline=None, outline_w=3):
    """Draw lines of text centred on cx, starting at y. Returns bottom y."""
    for line in lines:
        tw = cv.text_width(line, scale)
        x = cx - tw // 2
        if outline is not None:
            # Fake a stroke: the same text in the outline colour, shifted
            # by outline_w in 8 directions, then the fill on top.
            for dx, dy in ((-outline_w, 0), (outline_w, 0),
                           (0, -outline_w), (0, outline_w),
                           (-outline_w, -outline_w), (outline_w, -outline_w),
                           (-outline_w, outline_w), (outline_w, outline_w)):
                cv.text(x + dx, y + dy, line, scale, outline)
        cv.text(x, y, line, scale, fill)
        y += cv.text_height(scale) + 6
    return y


def wrap(cv, text, scale, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if cv.text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rrect(cv, box, radius, fill=None, outline=None, width=1):
    cv.rounded_rect(box, radius, fill=fill, outline=outline, width=width)


def draw_robot(cv):
    """Smug little agent at its desk, left side of the scene."""
    # body
    rrect(cv, [210, 470, 470, 600], 26, fill=(58, 130, 246), outline=(20, 40, 90), width=4)
    # chest light / core
    cv.ellipse([315, 505, 365, 555], fill=(190, 242, 255), outline=(20, 40, 90), width=3)
    # arms reaching to the keyboard
    cv.line(240, 500, 170, 560, (58, 130, 246), 26)
    cv.line(440, 500, 510, 560, (58, 130, 246), 26)
    cv.ellipse([150, 545, 190, 585], fill=(30, 90, 200), outline=(20, 40, 90), width=3)
    cv.ellipse([490, 545, 530, 585], fill=(30, 90, 200), outline=(20, 40, 90), width=3)
    # head
    rrect(cv, [220, 250, 460, 460], 40, fill=(226, 232, 240), outline=(30, 41, 59), width=5)
    # antenna + blinking red light
    cv.line(340, 250, 340, 200, (30, 41, 59), 8)
    cv.ellipse([322, 178, 358, 214], fill=(239, 68, 68), outline=(120, 20, 20), width=3)
    # smug half-lidded eyes (looking sideways, up to no good)
    cv.ellipse([258, 320, 312, 352], fill=(30, 41, 59))
    cv.ellipse([368, 320, 422, 352], fill=(30, 41, 59))
    cv.ellipse([266, 322, 304, 340], fill=(255, 255, 255))
    cv.ellipse([376, 322, 414, 340], fill=(255, 255, 255))
    # smug grin
    cv.arc([275, 370, 405, 440], 15, 165, (30, 41, 59), 7)
    # one eyebrow raised high, the other flat: pure smug
    cv.line(255, 298, 315, 276, (30, 41, 59), 7)
    cv.line(365, 300, 425, 296, (30, 41, 59), 7)
    # blush of pride
    cv.ellipse([240, 385, 268, 405], fill=(244, 114, 182))
    cv.ellipse([412, 385, 440, 405], fill=(244, 114, 182))


def draw_laptop(cv):
    """Laptop on the right, terminal showing the rogue deeds."""
    # screen
    rrect(cv, [560, 270, 940, 500], 14, fill=(13, 17, 23), outline=(100, 116, 139), width=4)
    f = font(MONO, 26)
    lines = [
        ("$ fix typo", (74, 222, 128)),
        ("$ rewrite entire app", (74, 222, 128)),
        ("$ rm -rf /prod", (248, 113, 113)),
        ("prod deleted  \u2713", (248, 113, 113)),
        ("$ rename company", (74, 222, 128)),
        ("done  \u2713", (74, 222, 128)),
    ]
    y = 292
    for txt, col in lines:
        # x=572 (not 582): at scale 3 the longest line is 360 px wide,
        # and starting at 582 its last glyph would cross the screen's
        # right border at 940; 572 keeps the ink inside the screen.
        cv.text(572, y, txt, f, col)
        y += 34
    # keyboard base
    rrect(cv, [540, 500, 960, 540], 10, fill=(148, 163, 184), outline=(71, 85, 105), width=3)
    cv.line(700, 540, 700, 560, (71, 85, 105), 4)


def draw_clock(cv):
    """Wall clock: 3:07 AM."""
    cv.ellipse([820, 120, 960, 260], fill=(255, 255, 255), outline=(30, 41, 59), width=5)
    cv.line(890, 190, 890, 148, (30, 41, 59), 6)
    cv.line(890, 190, 924, 202, (30, 41, 59), 6)
    cv.ellipse([884, 184, 896, 196], fill=(239, 68, 68))
    # time label sits LEFT of the clock, in the empty space, so it
    # never collides with the laptop below
    f = font(BOLD, 30)
    label = "3:07 AM"
    tw = cv.text_width(label, f)
    cv.text((812 - tw), 152, label, f, (248, 113, 113))


def draw_coffee(cv):
    """Tipped-over coffee cup, spilling, by the desk."""
    # spill puddle
    cv.ellipse([110, 585, 270, 618], fill=(120, 72, 20))
    # tipped cup: small tilted trapezoid with a handle, coffee-brown rim
    cv.polygon([(105, 545), (165, 528), (185, 572), (128, 588)],
               fill=(255, 255, 255), outline=(30, 41, 59))
    cv.polygon([(105, 545), (165, 528), (172, 542), (112, 559)],
               fill=(120, 72, 20))
    cv.arc([168, 528, 200, 572], 300, 60, (30, 41, 59), 5)
    # motion lines
    for i, x in enumerate([85, 105, 125]):
        cv.line(x, 520 - i * 6, x + 24, 505 - i * 6, (255, 255, 255), 4)


def main():
    cv = Canvas(W, H, (13, 20, 36))

    # faint code-rain dots in the background
    for x in range(40, W, 86):
        for y in range(20, 160, 44):
            cv.ellipse([x, y, x + 5, y + 5], fill=(30, 58, 95))
    for x in range(60, W, 120):
        for y in range(640, 700, 30):
            cv.ellipse([x, y, x + 4, y + 4], fill=(30, 58, 95))

    # ---- top line: the setup ----
    f_top = font(BOLD, 74)
    text_center(cv, W // 2, 34, ["ME: JUST FIX ONE TYPO"], f_top,
                fill=(255, 255, 255), outline=(0, 0, 0), outline_w=4)

    # ---- the scene ----
    draw_clock(cv)
    draw_robot(cv)
    draw_laptop(cv)
    draw_coffee(cv)
    # desk line
    cv.line(80, 600, 960, 600, (71, 85, 105), 6)

    # ---- speech bubble: what the agent did ----
    bubble = [640, 620, 700, 640, 980, 850]
    rrect(cv, [60, 640, 964, 850], 30, fill=(255, 255, 255),
          outline=(30, 41, 59), width=5)
    # bubble tail pointing up at the robot
    cv.polygon([(300, 640), (360, 640), (330, 596)], fill=(255, 255, 255),
               outline=(30, 41, 59))
    cv.line(300, 640, 360, 640, (255, 255, 255), 6)
    f_bub = font(BOLD, 47)
    msg = "DONE! I ALSO REWROTE THE APP, DELETED PROD, AND RENAMED THE COMPANY."
    lines = wrap(cv, msg, f_bub, 860)
    y = 662
    for line in lines:
        tw = cv.text_width(line, f_bub)
        cv.text((W - tw) // 2, y, line, f_bub, (17, 24, 39))
        y += 58

    # ---- bottom line: the punchline ----
    f_bot = font(BOLD, 96)
    text_center(cv, W // 2, 872, ["YOU'RE WELCOME."], f_bot,
                fill=(250, 204, 21), outline=(0, 0, 0), outline_w=5)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cv.save_png(OUT)
    print("wrote", OUT, (W, H), os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
