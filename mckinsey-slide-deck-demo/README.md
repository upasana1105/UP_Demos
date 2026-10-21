# McKinsey & Company Presentation Kit (`mckinsey-slide-deck-demo`)

A brand-aligned HTML-to-PowerPoint presentation generator built around **McKinsey & Company's** visual identity (Deep Navy `#051C2C`, Electric Blue `#2222F6`, Bright Cyan `#22A3DF`, `Georgia` + `Arial` typography), **Slideworks Business & Consulting Toolkit** layouts, and the **SAIL Digital Transformation Roadmap | BSL Discussion Document** structure.

## Directory Structure
- `templates/mckinsey_sample_deck.html`: Standalone 16:9 HTML slide deck featuring 6 signature McKinsey & Slideworks consulting archetypes.
- `scripts/html_to_pptx.py`: Python compiler that converts `<section class="slide">` elements into native editable PowerPoint shapes, column charts, 3×3 prioritization matrices, tables, and speaker notes.
- `output/mckinsey_sample_presentation.pptx`: Compiled editable PowerPoint presentation.

## Usage
```bash
../deloitte-slide-deck-demo/venv/bin/python3 scripts/html_to_pptx.py \
  --input templates/mckinsey_sample_deck.html \
  --output output/mckinsey_sample_presentation.pptx
```
