"""Assemble out/slide-*.png into a 16:9 .pptx, one full-bleed picture per slide, with speaker notes."""
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Emu

HERE = Path(__file__).parent
OUT = HERE / "out"
W, H = Emu(12192000), Emu(6858000)  # 13.333 x 7.5 in

prs = Presentation()
prs.slide_width, prs.slide_height = W, H
blank = prs.slide_layouts[6]
notes = json.loads((OUT / "notes.json").read_text(encoding="utf-8"))
for img, note in zip(sorted(OUT.glob("slide-*.png")), notes):
    slide = prs.slides.add_slide(blank)
    slide.shapes.add_picture(str(img), 0, 0, W, H)
    slide.notes_slide.notes_text_frame.text = note or ""
dest = HERE / "Who to Call First - Q3 2026 call list.pptx"
prs.save(dest)
print(dest.name, f"{dest.stat().st_size / 1e6:.1f} MB", len(prs.slides), "slides")
