# Google Antigravity (`agy`) Live Demo Runbook for McKinsey

**Session Context**: McKinsey Spark & Antigravity Demo (Aligned with Julie Polmonari, Al Marsella, Sarah Erdos, and Upasana Pati's Oct 19 Planning Notes)  
**Target Audience**: McKinsey Embedded Consultants (currently heavy **Cursor** power users who build HTML client dashboards and slides) + Consulting Leadership (Scott Wilder, Joe, Mo'Nique's team).  
**Strategic Goal**: Position **Google Antigravity** as the full-stack deliverable & SDLC powerhouse that complements **Gemini Agent (Spark)**—driving **Q4 Antigravity seat sales** while showing how Skills built in Antigravity can be imported into Gemini Agent.

---

## 🛠️ Pre-Built Demo Assets in Your Workspace

Everything is built, tested, and ready to run in `/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/`:

| Asset | File Path | What It Demonstrates |
| :--- | :--- | :--- |
| **1. McKinsey Brand Skill** | [.agents/skills/mckinsey-slide-creator/SKILL.md](file:///Users/upasanapati/shrinkAI%20experiment/Antigravity_Experiments/UP_Demos/.agents/skills/mckinsey-slide-creator/SKILL.md) | Reusable Skill encoding McKinsey's Pyramid Principle, Action Titles, `#051C2C` Navy / `#2222F6` Electric Blue palette, and Slideworks layouts. |
| **2. Interactive Thursday Client HTML Dashboard** | [templates/mckinsey_thursday_dashboard.html](file:///Users/upasanapati/shrinkAI%20experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/templates/mckinsey_thursday_dashboard.html) | Meets embedded consultants in their comfort zone: interactive HTML dashboard with What-If sliders, Partner Memory banner, "Human API" chase button, and `INR Cr` $\leftrightarrow$ `$M` toggle. |
| **3. BYOMCP & In-Place Excel Pipeline** | [scripts/thursday_data_pipeline.py](file:///Users/upasanapati/shrinkAI%20experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/scripts/thursday_data_pipeline.py) | Connects `@bigquery`, `@databricks-genie`, `@snowflake`, and `@sharepoint-excel` to update `McKinsey_Thursday_Value_Tracker.xlsx` **in place**. |
| **4. Generated 3-Tab Excel Model** | [output/McKinsey_Thursday_Value_Tracker.xlsx](file:///Users/upasanapati/shrinkAI%20experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/output/McKinsey_Thursday_Value_Tracker.xlsx) | Formatted McKinsey Excel tracker (*Executive Wave Bridge*, *3×3 Initiative Matrix + Human API Sign-Off*, *BYOMCP Audit Log*). |
| **5. Automated SDLC Test Suite** | [tests/test_thursday_pipeline.py](file:///Users/upasanapati/shrinkAI%20experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/tests/test_thursday_pipeline.py) | 5 automated unit tests verifying zero-variance financial reconciliation across DB, Excel, HTML, and PPTX. |
| **6. HTML Slide Deck Template** | [templates/mckinsey_sample_deck.html](file:///Users/upasanapati/shrinkAI%20experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/templates/mckinsey_sample_deck.html) | 6-slide HTML presentation using McKinsey / Slideworks consulting archetypes. |
| **7. Native PPTX Compiler & Output** | [scripts/html_to_pptx.py](file:///Users/upasanapati/shrinkAI%20experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/scripts/html_to_pptx.py) $\rightarrow$ [output/mckinsey_sample_presentation.pptx](file:///Users/upasanapati/shrinkAI%20experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/output/mckinsey_sample_presentation.pptx) | Compiles HTML slides into 100% native editable PowerPoint shapes, column charts, 3×3 matrices, tables, and speaker notes. |

---

## 🎬 Live Step-by-Step Presenter Script (15 Minutes)

### Opening Hook: Positioning Gemini Agent (Spark) vs. Antigravity (1 Min)
* **Presenter Talking Point**:
  > *"Earlier you saw how **Gemini Agent (Spark)** empowers every consultant with a lightweight assistant for daily planning and quick answers. Now let's look at **Google Antigravity**—purpose-built for your **embedded consultants, analytics translators, and heavy Cursor users** who build interactive HTML client dashboards, financial pipelines, and reusable capabilities that power the entire engagement team."*

---

### Act 1: "Meet Embedded Consultants Where They Live" — The Thursday HTML Client Dashboard (4 Mins)
*(Addresses Sarah's points at `00:02:51`, `00:07:14`, and `00:11:08`)*

1. **Show Workspace & Auto-Discovered McKinsey Skill**:
   In Antigravity chat / CLI:
   ```text
   /skills
   ```
   * **Point out**: `mckinsey-slide-creator`—Antigravity automatically enforces McKinsey's Pyramid Principle, full-sentence Action Titles, Deep Navy (`#051C2C`) + Electric Blue (`#2222F6`), and `Georgia`/`Arial` typography.

2. **Open the Interactive Thursday Dashboard in the Browser**:
   Open [templates/mckinsey_thursday_dashboard.html](file:///Users/upasanapati/shrinkAI%20experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/templates/mckinsey_thursday_dashboard.html).
   * **Walk through 4 highlights on screen**:
     1. **Partner Memory Banner (top right)**: *"Remember how Partners give feedback on Thursday morning—like preferring a 3-Wave Column Chart with a CAGR badge over a line chart? Antigravity persists that preference across every build."*
     2. **Automating the "Human API" (middle right panel)**: Point to the red row (`Hot Strip Mill — A. Kulkarni: Missing Week 42 actuals`). Click **`⚡ Auto-Ping Missing Owner`**—watch it chase the workstream lead via Slack/Teams MCP, ingest the `-22%` cobble reduction actuals, and turn all **8/8 Workstreams Green**.
     3. **Live What-If Sensitivity Sliders (bottom left of chart)**: Drag the **Operator AI Adoption Rate** slider from `85%` to `95%`. Watch the 3-wave column chart, CAGR pill, Action Title, and `1/3 grey` Key Takeaways update instantaneously.
     4. **Customer-Agnostic Toggle (top right)**: Click **`Switch to Global ($M) Mode`** to flip all metrics from `INR 1,310 Cr` to `$158M` (note: use this mode for your **Oct 27 BCG deep-dive**!).

---

### Act 2: Connecting the 90% BYOMCP Fabric & In-Place Excel/SharePoint Updates (4 Mins)
*(Addresses Al's BYOMCP point at `00:05:11` and Sarah's Excel pain point at `00:03:54`)*

1. **Inspect Connected BYOMCP Servers**:
   In Antigravity:
   ```text
   /mcp
   ```
   * **Presenter Talking Point**:
     > *"Al noted that 90% of the firm uses Bring Your Own MCP across BigQuery, Databricks, and Snowflake. In Antigravity, embedded consultants bind those exact MCP servers directly into their data pipeline alongside SharePoint."*

2. **Run the In-Place SharePoint Excel Pipeline**:
   Prompt Antigravity (or run in terminal):
   ```bash
   ../deloitte-slide-deck-demo/venv/bin/python3 scripts/thursday_data_pipeline.py --output-excel output/McKinsey_Thursday_Value_Tracker.xlsx
   ```
   * **Presenter Talking Point**:
     > *"One of the biggest pain points users experienced in Gemini Enterprise was having to download an Excel workbook, edit it locally, and re-upload it to SharePoint. Here, Antigravity updates `McKinsey_Thursday_Value_Tracker.xlsx` **directly in place**—populating the Executive Wave Bridge, the 3×3 Prioritization Matrix, and the Human API sign-off log."*

---

### Act 3: Why Antigravity Beats Cursor — Full-Stack SDLC, `/fork`, Testing & `/schedule` (3 Mins)
*(Addresses Upasana & Julie's positioning at `00:08:09`)*

1. **Safe Branching & Automated Financial Reconciliation Tests (`pytest`)**:
   In Antigravity:
   ```text
   /fork
   ```
   Then run the automated test suite:
   ```bash
   ../deloitte-slide-deck-demo/venv/bin/python3 tests/test_thursday_pipeline.py
   ```
   * **Presenter Talking Point**:
     > *"Why do embedded consultants upgrade from Cursor to Antigravity? Because when a dashboard goes to a client CEO on Thursday afternoon, you can't afford a hallucinated number or a broken formula. Antigravity provides the full SDLC—isolated branching with `/fork`, browser verification via Chrome DevTools MCP, and automated `pytest` suites that verify **zero variance** across BigQuery, the Excel workbook, the HTML dashboard, and the PowerPoint deck."*

2. **Schedule the Thursday Workflow (`/schedule`)**:
   ```text
   /schedule CronExpression="0 9 * * 4" Prompt="Run thursday_data_pipeline.py, chase any missing workstream owners via Teams MCP, update SharePoint Excel in-place, and run pytest verification"
   ```

---

### Act 4: The Coexistence Climax — Build Skills in Antigravity, Run in Gemini Agent (3 Mins)
*(Addresses Upasana's coexistence strategy at `00:12:01` and Q4 seat sales at `00:15:37`)*

1. **Compile the 6-Slide Editable McKinsey PowerPoint Deck**:
   Run in Antigravity:
   ```bash
   ../deloitte-slide-deck-demo/venv/bin/python3 scripts/html_to_pptx.py \
     --input templates/mckinsey_sample_deck.html \
     --output output/mckinsey_sample_presentation.pptx
   ```
   Open [output/mckinsey_sample_presentation.pptx](file:///Users/upasanapati/shrinkAI%20experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/output/mckinsey_sample_presentation.pptx) or preview [templates/mckinsey_sample_deck.html](file:///Users/upasanapati/shrinkAI%20experiment/Antigravity_Experiments/UP_Demos/mckinsey-slide-deck-demo/templates/mckinsey_sample_deck.html).

2. **Deliver the "Better Together" Closing Message for Q4 Seat Sales**:
   > *"Notice how we didn't just build a one-off deck. We packaged McKinsey's visual identity and HTML-to-PPTX compiler as a portable Skill in `.agents/skills/mckinsey-slide-creator/SKILL.md`. Your embedded consultants build, test, and harden these Skills and BYOMCP connectors in **Antigravity**, and then **import them directly into Gemini Agent (Spark)**—so every Partner and Associate across the firm can generate verified, brand-compliant McKinsey deliverables on demand."*
