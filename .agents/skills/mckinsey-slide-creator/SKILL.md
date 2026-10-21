---
name: mckinsey-slide-creator
description: Standardized guidelines, brand voice rules, HTML slide template layouts, and HTML-to-PPTX compilation tools for generating McKinsey & Company executive presentations and consulting decks.
---

# McKinsey & Company Presentation Slide Creator Skill

Use this skill whenever the user asks to generate, design, format, or compile a **McKinsey** presentation, strategy deck, discussion document, digital transformation roadmap, or executive readout (either as a standalone HTML slide deck or as an editable `.pptx` PowerPoint file).

This skill synthesizes:
1. **McKinsey's Visual Identity** (designed with Wolff Olins): Deep McKinsey Navy (`#051C2C` / `#061F32`), Vivid Electric Blue (`#2222F6` / `#1F6FD8`), Bright Cyan (`#22A3DF`), pairing **Bower / Georgia** (serif display & hero figures) with **McKinsey Sans / Arial** (action titles, tables, charts, body).
2. **Slideworks Business & Consulting Toolkit Standards** (`Slideworks_business_consulting_toolkit_SAMPLE`): Fractional grey split layouts (`1/3 grey`, `1/4 grey`, `1/2 grey`), historic & forecast column charts with right-hand key takeaway panels, 3×3 prioritization matrices (`LEVEL OF IMPACT` vs. `TIME TO IMPACT`) with RAG status pills, 4-key-trends tables, and multi-dimension capability assessments.
3. **Real McKinsey Client Discussion Documents** (modeled on the *SAIL Digital Transformation Roadmap | BSL - Discussion Document*): Multi-wave transformation roadmaps, integrated plant/workstream initiative architectures (150+ initiatives), quantified value-realization callouts, and structured governance/capability building slides.

---

## 1. McKinsey Brand Voice, Storyline & Consulting Methodology

Every McKinsey presentation is built as a standalone, self-explanatory **Discussion Document** following strict MBB consulting principles:

- **The Pyramid Principle (Barbara Minto)**:
  - Lead with the governing conclusion first, support it with 3–4 mutually exclusive and collectively exhaustive (**MECE**) arguments, and anchor every argument in quantitative evidence.
- **Full-Sentence Action Titles (Mandatory on Every Content Slide)**:
  - Never use topic titles like *"Market Overview"* or *"Digital Roadmap"*.
  - Every slide must have a complete, active sentence at the top that states the **"So What?"** conclusion (e.g., *"BSL's 3-wave digital transformation roadmap unlocks ~INR 1,300 Cr in annual EBITDA across 150+ prioritized plant and mine initiatives"*).
  - Reading only the Action Titles in sequence ("horizontal flow") must tell the complete story of the deck using the **SCR (Situation – Complication – Resolution)** framework.
- **One Message Per Slide & High Data-to-Ink Ratio**:
  - Every element on the slide (chart, matrix, table, takeaway box) must directly prove the Action Title ("vertical flow").
  - Use **Vivid Electric Blue (`#2222F6` / `#1F6FD8`)** or **Bright Cyan (`#22A3DF`)** sparingly to highlight the focal data series, forecast period, or target state while keeping historical baselines in Deep Navy (`#051C2C`) or Muted Gray (`#A5A5A5`).
- **Mandatory Tracker Header, Source & Footnote Discipline**:
  - Every content slide includes a top-left `[Section]` tracker label above the Action Title.
  - Every content slide includes a bottom-left `Source: ...` and `Footnote: 1. ...` attribution line, and a bottom-right wordmark (`McKinsey & Company`) + slide number.
- **Presenter Notes (`data-notes`)**:
  - **Every `<section class="slide">`** must include a `data-notes="..."` attribute containing a concise 2–4 sentence executive verbal script summarizing the governing insight, key quantitative drivers, and decision implication.
  - Never render presenter notes visually on the slide canvas; `html_to_pptx.py` injects them directly into native PowerPoint Speaker Notes.

---

## 2. Visual System & CSS Design Tokens

### Color Palette (McKinsey & Slideworks 2025 Consulting Palette)
Always define and use these exact CSS variables in HTML slide decks:

```css
:root {
  /* Core McKinsey Blues */
  --mck-navy: #051C2C;           /* Primary Deep McKinsey Navy (Cover, Dividers, Headers, Primary Text) */
  --mck-navy-alt: #061F32;       /* Slideworks Dark Slide / Table Header Navy */
  --mck-electric-blue: #2222F6;  /* Vivid McKinsey Electric Blue (Focal Callouts, Key Accents) */
  --mck-chart-blue: #1F6FD8;     /* Primary Forecast / Highlight Series Blue */
  --mck-cyan: #22A3DF;           /* Secondary Data / Accent Cyan */
  --mck-sky: #5ACBF0;            /* Tertiary Highlight / Dark-Slide Accent Sky Blue */
  --mck-mid-blue: #1877A2;       /* Corporate Mid Blue */
  --mck-ice-blue: #E7F0F9;       /* Light Ice Blue Highlight Fill / Callout Container */
  --mck-ice-border: #A2D5EC;     /* Ice Blue Border / Secondary Fill */

  /* Consulting Neutrals & Fractional Split Greys */
  --mck-white: #FFFFFF;          /* Primary Content Slide Background */
  --mck-bg-grey: #F2F2F2;        /* Fractional Split Panel / Takeaway Box / Alternating Row Grey */
  --mck-header-grey: #D8D8D8;    /* Assessment Parameter Row / Secondary Header Grey */
  --mck-border: #D8D8D8;         /* Hairline Dividers & Table Gridlines */
  --mck-muted: #7F7F7F;          /* Subtitles, Axis Labels, Sources & Footnotes */
  --mck-axis-grey: #A5A5A5;      /* Matrix Headers, Baseline Series, Inactive Harvey Balls */
  --mck-text: #051C2C;           /* Primary Body Copy & Action Title Text */

  /* RAG Status & Prioritization Matrix Accents */
  --mck-green: #00B050;          /* High Readiness / Wave 1 Quick Win / On-Track */
  --mck-amber: #FAD688;          /* Medium Readiness / Wave 2 Scale / In-Progress */
  --mck-amber-dark: #F8BC3B;     /* Amber Accent Border / Text */
  --mck-coral: #E5546C;          /* Critical Bottleneck / High Complexity / Delayed */
}
```

### Typography Rules (PowerPoint-Safe Substitution for Bower & McKinsey Sans)
McKinsey's proprietary typefaces are **Bower** (bold serif named after Marvin Bower) and **McKinsey Sans**. In client PowerPoint presentations, McKinsey substitutes **Georgia** and **Arial** so decks remain 100% editable on any client machine without font breakage:
- **Display & Serif Accent (`font-family: 'Georgia', serif`)**:
  - Used for Cover Slide titles (`36px–42px`, Bold), Section Breaker titles (`32px–36px`, Bold), Matrix background watermarks, and hero KPI callout numbers (`28px–36px`, Bold).
- **Action Titles, Body, Tables & Charts (`font-family: 'Arial', 'Helvetica Neue', sans-serif`)**:
  - **Section Tracker**: `10px`, Uppercase, Bold, Letter-spacing `0.8px`, `--mck-mid-blue` (`#1877A2`).
  - **Action Title**: `20px–22px`, Bold (`700`), `--mck-navy` (`#051C2C`), line-height `1.22`, max 2 lines.
  - **Subtitle / Chart Unit Header**: `12px`, Regular or Italic, `--mck-muted` (`#7F7F7F`), e.g., `INR Crores, FY25–FY28 Forecast`.
  - **Body Copy / Table Cells / Takeaways**: `10.5px–11.5px`, Regular (`400`) with Bold (`700`) lead-ins, `--mck-text`.
  - **Source & Footnotes**: `8.5px–9px`, Regular, `--mck-muted` (`#7F7F7F`).

### Canvas & Structural Geometry
- **Aspect Ratio**: 16:9 Widescreen (`960px × 540px` per `.slide` section in HTML; `13.333" × 7.5"` in PowerPoint).
- **Alternating Dark & White Contrast**:
  - Mix deep navy slides (`slide--cover`, `slide--divider` in `#051C2C` / `#061F32`) with crisp white content slides (`#FFFFFF`) and light grey fractional panels (`#F2F2F2`) to pace the presentation and signal structural transitions.

---

## 3. Standard McKinsey Slide Layout Archetypes

Every HTML deck should be structured as `<section class="slide ...">` blocks inside a single HTML file. Below are the 6 canonical McKinsey & Slideworks layouts supported by our HTML-to-PPTX compiler:

### Layout 1: Dark Navy Cover / Frontpage (`slide--cover`)
- **Background**: Deep McKinsey Navy (`#051C2C`) with subtle right-hand architectural blue line motif (`#2222F6` / `#22A3DF`).
- **Typography**: Top eyebrow tag (`DISCUSSION DOCUMENT | CONFIDENTIAL`), large **Georgia** serif presentation title (`38px`, White), Arial subtitle (`15px`, `#A2D5EC`), and bottom metadata bar with client/engagement details on the left and stacked `McKinsey & Company` wordmark on the right.

```html
<section class="slide slide--cover" data-notes="Welcome to the SAIL Bokaro Steel Plant Digital Transformation Roadmap readout. Over the next 30 minutes we will walk through the 150+ prioritized digital and analytics initiatives that unlock ~INR 1,300 Cr in recurring annual EBITDA.">
  <div class="cover-eyebrow">DISCUSSION DOCUMENT | CLIENT CONFIDENTIAL</div>
  <div class="cover-body">
    <h1 class="cover-title">SAIL Digital Transformation Roadmap | BSL</h1>
    <h2 class="cover-subtitle">End-to-end Industry 4.0 architecture, wave-wise initiative prioritization, and capability building across integrated steel plants and mines</h2>
  </div>
  <div class="cover-footer">
    <div class="cover-meta">Prepared for Steel Authority of India Limited (Bokaro Steel Plant)<br>October 2026</div>
    <div class="cover-brand">McKinsey &amp;<br>Company</div>
  </div>
</section>
```

### Layout 2: Section Breaker / Divider (`slide--divider`)
- **Background**: Deep McKinsey Navy (`#061F32`) with a vivid electric-blue accent rule (`#2222F6`).
- **Content**: Section number / label (`SECTION 01`), **Georgia** serif section headline, and optional 3-bullet executive preview of the section's storyline.

```html
<section class="slide slide--divider" data-notes="Section 1 establishes our baseline diagnostic and quantifies the value creation potential across iron making, steel melting, hot strip mill, and raw material mines.">
  <div class="divider-content">
    <div class="divider-eyebrow">01 | VALUE CREATION &amp; BASELINE DIAGNOSTIC</div>
    <h1 class="divider-title">Capturing ~INR 1,300 Cr in annual value through advanced analytics and plant digitization</h1>
    <p class="divider-sub">Diagnostic synthesis across Blast Furnace, SMS, Hot Strip Mill, Energy &amp; Utilities, and Mining operations</p>
  </div>
  <div class="divider-footer">
    <span class="footer-brand-light">McKinsey &amp; Company</span>
  </div>
</section>
```

### Layout 3: Column Chart (Historic & Forecast) with Right-Hand Key Takeaways (`slide--chart-takeaways`)
- **Structure**: Modeled directly on the Slideworks `1/3 grey` consulting layout (`[Column chart with historic and forecast figures]` + `[Key takeaways/main conclusion]`).
- **Left 2/3 (`chart-panel`)**: Chart unit header (`[Data], [Unit]`), CAGR / delta badge (`+xx% p.a.`), vertical bar/column chart comparing `Actuals` (`#051C2C`) and `Forecast` (`#1F6FD8` / `#22A3DF`), and x-axis category labels.
- **Right 1/3 (`takeaways-sidebar`)**: Shaded `#F2F2F2` vertical panel with top navy header bar (`Key takeaways / main conclusion`) and structured bullet points with bold lead-ins.

```html
<section class="slide" data-notes="Digital and analytics initiatives are projected to expand BSL's cumulative annual EBITDA run-rate impact from INR 180 Cr in FY25 to INR 1,310 Cr by FY28, with Wave 1 quick wins self-funding subsequent capex.">
  <div class="slide-header">
    <div class="slide-tracker">VALUE REALIZATION TRAJECTORY</div>
    <h2 class="slide-title">Phased rollout across three waves scales recurring EBITDA impact to ~INR 1,310 Cr by FY28</h2>
    <div class="slide-subtitle">Cumulative gross annual EBITDA impact from 150+ digital initiatives, INR Crores</div>
  </div>
  <div class="split-2-1">
    <div class="chart-panel">
      <div class="chart-meta">
        <span class="chart-unit">Recurring EBITDA Impact, INR Cr</span>
        <span class="chart-cagr">CAGR +94% (FY25–FY28F)</span>
      </div>
      <div class="bar-chart" data-chart-type="column">
        <div class="bar-group" data-label="FY25 Actuals" data-value="180" data-series="Actuals"></div>
        <div class="bar-group" data-label="FY26 Wave 1" data-value="490" data-series="Forecast"></div>
        <div class="bar-group" data-label="FY27 Wave 2" data-value="920" data-series="Forecast"></div>
        <div class="bar-group" data-label="FY28 Wave 3" data-value="1310" data-series="Forecast"></div>
      </div>
    </div>
    <div class="takeaways-sidebar">
      <div class="sidebar-header">Key takeaways / main conclusion</div>
      <ul class="sidebar-list">
        <li><strong>Self-funding Wave 1 (+INR 490 Cr):</strong> Zero-capex APC and AI yield optimization models in Blast Furnace and SMS generate immediate cash flow within 6–9 months.</li>
        <li><strong>Core plant scaling (+INR 920 Cr):</strong> Predictive maintenance and Computer Vision surface inspection reduce unplanned cobbles and downtime by 22%.</li>
        <li><strong>Integrated mine-to-mill (+INR 1,310 Cr):</strong> End-to-end raw material blend optimization and smart grid energy scheduling lock in structural margin lift.</li>
      </ul>
    </div>
  </div>
  <div class="slide-footer">
    <div class="footer-sources">Source: BSL Operational Diagnostic (FY25); McKinsey Metals &amp; Mining Digital Benchmark | Footnote: 1. Run-rate EBITDA before implementation OpEx.</div>
    <div class="footer-right"><span class="footer-brand">McKinsey &amp; Company</span> <span class="footer-page">3</span></div>
  </div>
</section>
```

### Layout 4: 3×3 Prioritization / Impact vs. Time Matrix (`slide--matrix`)
- **Structure**: Modeled directly on Slideworks `p61` (`LEVEL OF IMPACT`: Low / Medium / High vs. `TIME TO IMPACT`: Short / Medium / Long).
- **Content**: 3×3 matrix grid with `#F2F2F2` cells, axis headers in `#A5A5A5`, initiative badges colored by RAG status (`--mck-green` `#00B050`, `--mck-amber` `#FAD688`, `--mck-coral` `#E5546C`), and a bottom status legend (`= Wave 1 Quick Wins`, `= Wave 2 Core Scale`, `= Wave 3 Foundation`).

```html
<section class="slide" data-notes="We evaluated all 150+ candidate use cases along two dimensions: financial EBITDA impact and time-to-impact. High-impact, short-time initiatives such as Blast Furnace fuel rate AI and SMS ferro-alloy optimization form our immediate Wave 1 priority.">
  <div class="slide-header">
    <div class="slide-tracker">INITIATIVE PRIORITIZATION MATRIX</div>
    <h2 class="slide-title">150+ digital initiatives prioritized by financial impact and time-to-value into three execution cohorts</h2>
    <div class="slide-subtitle">Prioritization matrix across iron making, steel melting, rolling mills, and cross-functional enablers</div>
  </div>
  <div class="matrix-container">
    <!-- 3x3 Grid rendered by HTML & html_to_pptx.py -->
  </div>
</section>
```

### Layout 5: Four Key Trends / Structured Consulting Table (`slide--trends`)
- **Structure**: Modeled on Slideworks `p85` (`[Four key trends slide]` with columns `Trend / Workstream` | `Description & Strategic Levers` | `Selected BSL Examples & Impact`).
- **Visuals**: Deep Navy `#061F32` column headers, 4 structured horizontal bands with bold navy trend cards on the left, 3–4 crisp bullets in the center, and concrete quantified examples in `#E7F0F9` / `#F2F2F2` on the right.

### Layout 6: Multi-Wave Transformation Roadmap & Capability Maturity Assessment (`slide--assessment`)
- **Structure**: Combines Slideworks `p96` (`[Assessment or status overview]` with alternating `#D8D8D8` and `#F2F2F2` dimension rows and RAG status circles) with the *BSL Digital Transformation Roadmap* architecture (Plant/Mine Workstreams, Wave 1–3 timeline milestones, and Digital Academy / CCoE capability readiness indicators).

---

## 4. Converting HTML Presentations to Editable PowerPoint (`.pptx`)

We maintain a dedicated McKinsey HTML-to-PPTX compiler at `mckinsey-slide-deck-demo/scripts/html_to_pptx.py`. It parses any HTML file following the above structure and generates a 100% native, editable 16:9 PowerPoint presentation (`13.333" × 7.5"`) with native shapes, data-driven column charts, 3×3 prioritization matrices, tables, RAG status indicators, and embedded presenter notes.

### Running the Converter
Always use the pre-configured virtual environment in `deloitte-slide-deck-demo/venv/bin/python3` (which includes `python-pptx` and `beautifulsoup4`):

```bash
/Users/upasanapati/shrinkAI\ experiment/Antigravity_Experiments/UP_Demos/deloitte-slide-deck-demo/venv/bin/python3 \
  "/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/scripts/html_to_pptx.py" \
  --input "/path/to/your_mckinsey_deck.html" \
  --output "/path/to/output_presentation.pptx"
```

### Quality Checklist Before Delivering Any McKinsey Deck
1. **Action Titles**: Is every slide title a full sentence stating a quantitative or strategic conclusion?
2. **Visual Restraint**: Are `#051C2C` (Deep Navy) and `#FFFFFF` / `#F2F2F2` dominant, with `#2222F6` / `#1F6FD8` / `#22A3DF` reserved strictly for focal data highlights?
3. **Typography**: Are `Georgia` (display/serif) and `Arial` (body/sans) applied consistently?
4. **Footers & Sources**: Does every content slide carry `Source: ...`, `Footnote: ...`, and the `McKinsey & Company` wordmark?
5. **Speaker Notes**: Does every `<section class="slide">` have a `data-notes="..."` attribute?
