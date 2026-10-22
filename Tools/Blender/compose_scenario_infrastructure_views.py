"""Compose Blender's six raw inspection renders into labeled image sheets."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
REFERENCES = ROOT / "Assets/LastLandfall/Art/References"
RENDERS = REFERENCES / "ScenarioBuildingViews/_renders"
OUTPUT = REFERENCES / "ScenarioBuildingViews"
MANIFEST = ROOT / "Assets/LastLandfall/Art/Previews/Infrastructure/ScenarioInfrastructure_Manifest.json"

VIEW_ORDER = ("Front", "Back", "Left", "Right", "Top", "Iso")
LABELS = {
    "Front": "正面 / 门面方向 (-Y)",
    "Back": "背面 (+Y)",
    "Left": "左侧面 (-X)",
    "Right": "右侧面 (+X)",
    "Top": "顶视",
    "Iso": "等距检查视角",
}


def load_font(size):
    for path in (
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
    ):
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def make_sheet(asset):
    cell = 512
    label_h = 38
    pad = 16
    header_h = 68
    width = cell * 3 + pad * 4
    height = header_h + (cell + label_h) * 2 + pad * 3
    sheet = Image.new("RGB", (width, height), (230, 229, 222))
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(28)
    label_font = load_font(20)
    draw.text((pad, 12), f"{asset['id']}  |  {asset['name']}  |  L{asset['level']}  |  {asset['footprint']}",
              font=title_font, fill=(34, 44, 43))

    for index, view in enumerate(VIEW_ORDER):
        col = index % 3
        row = index // 3
        x = pad + col * (cell + pad)
        y = header_h + pad + row * (cell + label_h + pad)
        source = RENDERS / f"{asset['id']}_{view}.png"
        if not source.exists():
            raise FileNotFoundError(source)
        with Image.open(source) as image:
            image = image.convert("RGB")
            if image.size != (cell, cell):
                image = image.resize((cell, cell), Image.Resampling.LANCZOS)
            sheet.paste(image, (x, y))
        draw.text((x + 2, y + cell + 4), LABELS[view], font=label_font, fill=(42, 51, 50))

    out = OUTPUT / f"{asset['id']}_SixViews.png"
    sheet.save(out, format="PNG", optimize=True)
    print("Composed:", out)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assets = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for asset in assets:
        make_sheet(asset)
    print("All labeled sheets are in:", OUTPUT)


if __name__ == "__main__":
    main()
