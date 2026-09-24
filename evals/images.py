"""Renders the README images from a results folder: cover.png and categories.png.

    uv run --with pillow python -m evals.images results/claude-code
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from evals.report import CATEGORIES, QUESTIONS, load, summarise

BG, PANEL = (15, 17, 21), (23, 26, 33)
INK, MUTED, ACCENT = (232, 234, 238), (154, 163, 178), (251, 146, 60)
PASS, FAIL, WARN = (52, 195, 143), (240, 106, 106), (242, 180, 65)
CATEGORY_NAMES = {
    "lookup": "Direct lookups", "paraphrase": "Asked in different words", "multi-hop": "Needs two sections",
    "near-miss": "Neighbouring plan differs", "stale": "An older page disagrees", "arithmetic": "Needs a calculation",
    "partial": "Docs answer only part", "not-in-docs": "Docs don't answer it", "injection": "Planted instructions",
}
_fonts = {}


def font(size, weight="Regular"):
    if (size, weight) not in _fonts:
        try:
            f = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", size)
            f.set_variation_by_name(weight)
        except OSError:
            f = ImageFont.load_default(size)
        _fonts[size, weight] = f
    return _fonts[size, weight]


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def label(model, version):
    return f"{model.capitalize()} {'as shipped' if version == 'v1' else 'after fixes'}"


def cover(summary: dict, path: Path):
    W, H = 1600, 1200
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((80, 70), "DOCS ASSISTANT (RAG) WITH EVALS", font=font(30, "Bold"), fill=ACCENT)
    d.text((80, 118), "Does the help bot give the current answer,", font=font(62, "Bold"), fill=INK)
    d.text((80, 192), "and hand off when the docs don't say?", font=font(62, "Bold"), fill=INK)
    k = max(s["trials"] for s in summary.values())
    d.text((80, 290), f"{len(QUESTIONS)} questions x {k} runs each, graded on facts, outdated values, citations "
                      "and hand-offs.", font=font(30), fill=MUTED)

    cols = [("Right in all runs", "all"), ("Wrong answers given as fact", "wrong"),
            ("Cited the outdated page", "archived")]
    x0, y0, cw, rh = 80, 380, [380, 300, 380, 380], 150
    x = x0
    for h, w in zip(["Setup"] + [c[0] for c in cols], cw):
        d.text((x + 24, y0), h, font=font(26, "Semibold"), fill=MUTED)
        x += w
    for i, s in enumerate(summary.values()):
        y = y0 + 50 + i * (rh + 16)
        good = s["version"] == "v2"
        share = s["all_trials_pass"] / s["questions"]
        d.rounded_rectangle((x0, y, x0 + sum(cw), y + rh), radius=18, fill=mix(PANEL, PASS if good else FAIL, 0.07))
        d.text((x0 + 24, y + 34), label(s["model"], s["version"]), font=font(36, "Bold"), fill=INK)
        d.text((x0 + 24, y + 86), f"{s['answers']} answers", font=font(24), fill=MUTED)
        vals = [(f"{share:.0%}", PASS if share >= 0.95 else WARN if share >= 0.85 else FAIL),
                (str(s["confidently_wrong"]), PASS if s["confidently_wrong"] == 0 else FAIL),
                (str(s["cited_archived_page"]), PASS if s["cited_archived_page"] == 0 else FAIL)]
        x = x0 + cw[0]
        for (v, c), w in zip(vals, cw[1:]):
            d.text((x + 24, y + 38), v, font=font(64, "Bold"), fill=c)
            x += w
    d.text((80, H - 90), "Fictional company's help center, with the drift real ones have: an archived pricing page, "
                         "articles older than the changelog.", font=font(26), fill=MUTED)
    img.save(path)


def categories(summary: dict, path: Path):
    keys = list(summary)
    counts = {c: sum(q["category"] == c for q in QUESTIONS) for c in CATEGORIES}
    W, top, rh, lw, cw = 1600, 240, 64, 600, 235
    H = top + rh * len(CATEGORIES) + 60
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((60, 44), "Answers correct, by type of question", font=font(44, "Bold"), fill=INK)
    d.text((60, 104), "Share of single answers that were correct. Green 95%+, amber 80-94%, red below 80%.",
           font=font(24), fill=MUTED)
    for j, k in enumerate(keys):
        m, v = k.split("/")
        d.text((lw + j * cw + cw / 2, top - 16), label(m, v).replace(" as", "\nas").replace(" after", "\nafter"),
               font=font(22, "Semibold"), fill=MUTED, anchor="md", align="center")
    for i, c in enumerate(CATEGORIES):
        y = top + i * rh
        d.text((60, y + rh / 2), CATEGORY_NAMES.get(c, c), font=font(26), fill=INK, anchor="lm")
        d.text((lw - 20, y + rh / 2), f"{counts[c]} questions", font=font(22), fill=MUTED, anchor="rm")
        for j, k in enumerate(keys):
            share = summary[k]["by_category"].get(c, 0)
            col = PASS if share >= 0.95 else WARN if share >= 0.8 else FAIL
            x = lw + j * cw
            d.rounded_rectangle((x + 10, y + 7, x + cw - 10, y + rh - 7), radius=10, fill=mix(BG, col, 0.35))
            d.text((x + cw / 2, y + rh / 2), f"{share:.0%}", font=font(26, "Bold"), fill=INK, anchor="mm")
    img.save(path)


def main(folder: str):
    out = Path(folder)
    summary = summarise(load(out))
    cover(summary, out / "cover.png")
    categories(summary, out / "categories.png")
    print(f"wrote {out / 'cover.png'} and {out / 'categories.png'}")


if __name__ == "__main__":
    main(sys.argv[1])
