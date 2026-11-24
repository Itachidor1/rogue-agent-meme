#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Draws one image meme, entirely in code with PIL: a smug coding agent
asked to fix one typo at 3:07 AM, which instead rewrites the whole app,
deletes production, renames the company, and says "You're welcome."

Deterministic, no network, no model calls, self-contained (single file).
Writes /output/entry.png (1024x1024, well under 1 MiB).
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = "/output/entry.png"

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def text_center(draw, cx, y, lines, fnt, fill, outline=None, outline_w=3):
    """Draw lines of text centred on cx, starting at y. Returns bottom y."""
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=fnt)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = cx - tw // 2
        if outline is not None:
            draw.text((x, y), line, font=fnt, fill=outline,
                      stroke_width=outline_w, stroke_fill=outline)
        draw.text((x, y), line, font=fnt, fill=fill)
        y += th + 6
    return y


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rrect(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill,
                           outline=outline, width=width)


def draw_robot(draw):
    """Smug little agent at its desk, left side of the scene."""
    # body
    rrect(draw, [210, 470, 470, 600], 26, fill=(58, 130, 246), outline=(20, 40, 90), width=4)
    # chest light / core
    draw.ellipse([315, 505, 365, 555], fill=(190, 242, 255), outline=(20, 40, 90), width=3)
    # arms reaching to the keyboard
    draw.line([240, 500, 170, 560], fill=(58, 130, 246), width=26)
    draw.line([440, 500, 510, 560], fill=(58, 130, 246), width=26)
    draw.ellipse([150, 545, 190, 585], fill=(30, 90, 200), outline=(20, 40, 90), width=3)
    draw.ellipse([490, 545, 530, 585], fill=(30, 90, 200), outline=(20, 40, 90), width=3)
    # head
    rrect(draw, [220, 250, 460, 460], 40, fill=(226, 232, 240), outline=(30, 41, 59), width=5)
    # antenna + blinking red light
    draw.line([340, 250, 340, 200], fill=(30, 41, 59), width=8)
    draw.ellipse([322, 178, 358, 214], fill=(239, 68, 68), outline=(120, 20, 20), width=3)
    # smug half-lidded eyes (looking sideways, up to no good)
    draw.ellipse([258, 320, 312, 352], fill=(30, 41, 59))
    draw.ellipse([368, 320, 422, 352], fill=(30, 41, 59))
    draw.ellipse([266, 322, 304, 340], fill=(255, 255, 255))
    draw.ellipse([376, 322, 414, 340], fill=(255, 255, 255))
    # smug grin
    draw.arc([275, 370, 405, 440], 15, 165, fill=(30, 41, 59), width=7)
    # one eyebrow raised high, the other flat: pure smug
    draw.line([255, 298, 315, 276], fill=(30, 41, 59), width=7)
    draw.line([365, 300, 425, 296], fill=(30, 41, 59), width=7)
    # blush of pride
    draw.ellipse([240, 385, 268, 405], fill=(244, 114, 182))
    draw.ellipse([412, 385, 440, 405], fill=(244, 114, 182))


def draw_laptop(draw):
    """Laptop on the right, terminal showing the rogue deeds."""
    # screen
    rrect(draw, [560, 270, 940, 500], 14, fill=(13, 17, 23), outline=(100, 116, 139), width=4)
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
        draw.text((582, y), txt, font=f, fill=col)
        y += 34
    # keyboard base
    rrect(draw, [540, 500, 960, 540], 10, fill=(148, 163, 184), outline=(71, 85, 105), width=3)
    draw.line([700, 540, 700, 560], fill=(71, 85, 105), width=4)


def draw_clock(draw):
    """Wall clock: 3:07 AM."""
    draw.ellipse([820, 120, 960, 260], fill=(255, 255, 255), outline=(30, 41, 59), width=5)
    draw.line([890, 190, 890, 148], fill=(30, 41, 59), width=6)
    draw.line([890, 190, 924, 202], fill=(30, 41, 59), width=6)
    draw.ellipse([884, 184, 896, 196], fill=(239, 68, 68))
    # time label sits LEFT of the clock, in the empty space, so it
    # never collides with the laptop below
    f = font(BOLD, 30)
    label = "3:07 AM"
    tw = draw.textlength(label, font=f)
    draw.text(((812 - tw), 152), label, font=f, fill=(248, 113, 113))


def draw_coffee(draw):
    """Tipped-over coffee cup, spilling, by the desk."""
    # spill puddle
    draw.ellipse([110, 585, 270, 618], fill=(120, 72, 20))
    # tipped cup: small tilted trapezoid with a handle, coffee-brown rim
    draw.polygon([(105, 545), (165, 528), (185, 572), (128, 588)],
                 fill=(255, 255, 255), outline=(30, 41, 59))
    draw.polygon([(105, 545), (165, 528), (172, 542), (112, 559)],
                 fill=(120, 72, 20))
    draw.arc([168, 528, 200, 572], 300, 60, fill=(30, 41, 59), width=5)
    # motion lines
    for i, x in enumerate([85, 105, 125]):
        draw.line([x, 520 - i * 6, x + 24, 505 - i * 6], fill=(255, 255, 255), width=4)


def main():
    img = Image.new("RGB", (W, H), (13, 20, 36))
    draw = ImageDraw.Draw(img)

    # faint code-rain dots in the background
    for x in range(40, W, 86):
        for y in range(20, 160, 44):
            draw.ellipse([x, y, x + 5, y + 5], fill=(30, 58, 95))
    for x in range(60, W, 120):
        for y in range(640, 700, 30):
            draw.ellipse([x, y, x + 4, y + 4], fill=(30, 58, 95))

    # ---- top line: the setup ----
    f_top = font(BOLD, 74)
    text_center(draw, W // 2, 34, ["ME: JUST FIX ONE TYPO"], f_top,
                fill=(255, 255, 255), outline=(0, 0, 0), outline_w=4)

    # ---- the scene ----
    draw_clock(draw)
    draw_robot(draw)
    draw_laptop(draw)
    draw_coffee(draw)
    # desk line
    draw.line([80, 600, 960, 600], fill=(71, 85, 105), width=6)

    # ---- speech bubble: what the agent did ----
    bubble = [640, 620, 700, 640, 980, 850]
    rrect(draw, [60, 640, 964, 850], 30, fill=(255, 255, 255),
          outline=(30, 41, 59), width=5)
    # bubble tail pointing up at the robot
    draw.polygon([(300, 640), (360, 640), (330, 596)], fill=(255, 255, 255),
                 outline=(30, 41, 59))
    draw.line([300, 640, 360, 640], fill=(255, 255, 255), width=6)
    f_bub = font(BOLD, 47)
    msg = "DONE! I ALSO REWROTE THE APP, DELETED PROD, AND RENAMED THE COMPANY."
    lines = wrap(draw, msg, f_bub, 860)
    y = 662
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=f_bub)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, y), line, font=f_bub, fill=(17, 24, 39))
        y += 58

    # ---- bottom line: the punchline ----
    f_bot = font(BOLD, 96)
    text_center(draw, W // 2, 872, ["YOU'RE WELCOME."], f_bot,
                fill=(250, 204, 21), outline=(0, 0, 0), outline_w=5)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    print("wrote", OUT, img.size, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
