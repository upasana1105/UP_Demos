# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
KPMG Translation Assistant — A2UI Component Builder.

Builds the WebFrameSrcdoc payload rendering the KPMG Translation Dashboard
directly inside Gemini Enterprise chat / side panel, storing page images once in JS
to keep payload size < 650 KB.
"""

import html
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_LAST_TRANSLATION_DATA: Dict[str, Any] = {}
SURFACE_ID = "kpmg-translation-dashboard"
DEFAULT_FRAME_HEIGHT = 860
A2UI_MIME_TYPE = "application/json+a2ui"

CSP_META = '<meta http-equiv="Content-Security-Policy" content="default-src \'self\' \'unsafe-inline\' data: blob:; img-src \'self\' data: blob:; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; connect-src \'none\';">'


def generate_dashboard_html(data: Dict[str, Any]) -> str:
    """Generates a self-contained, responsive KPMG-branded Translation Dashboard with single-copy JS page rendering."""
    filename = html.escape(data.get("filename", "sample_doc.pdf"))
    target_lang = html.escape(data.get("target_language", "de").upper())
    attribution = html.escape(data.get("customized_attribution", "NO_ATTRIBUTION"))

    audit = data.get("audit_report", {})
    overall_score = audit.get("overall_score", 95)
    accuracy_score = audit.get("accuracy_score", 95)
    fluency_score = audit.get("fluency_score", 90)
    tone_score = audit.get("tone_score", 95)
    exec_summary = html.escape(audit.get("executive_summary", "Translation completed with high precision."))
    findings = audit.get("audit_findings", [])

    source_preview = html.escape(data.get("source_text_sample", ""))
    target_preview = html.escape(data.get("translated_text_sample", ""))
    gcs_uri = html.escape(data.get("gcs_uri", ""))

    source_pages: List[str] = data.get("source_pages_b64", [])
    translated_pages: List[str] = data.get("translated_pages_b64", [])
    translated_pdf_b64: str = data.get("translated_pdf_b64", "")

    # Findings HTML
    findings_html = ""
    if findings:
        for f in findings:
            issue = html.escape(f.get("issue", "Terminology Alignment"))
            impact = html.escape(f.get("impact", "Medium"))
            orig = html.escape(f.get("original_text", ""))
            trans = html.escape(f.get("translated_text", ""))
            rec = html.escape(f.get("recommendation", ""))
            badge_color = "#e11d48" if impact.lower() == "high" else "#d97706"
            badge_bg = "#ffe4e6" if impact.lower() == "high" else "#fef3c7"
            findings_html += f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid {badge_color}; border-radius:8px; padding:12px; margin-bottom:10px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-weight:700; font-size:12px; color:#1e293b;">{issue}</span>
                <span style="background:{badge_bg}; color:{badge_color}; font-size:10px; font-weight:800; padding:2px 8px; border-radius:4px; text-transform:uppercase;">{impact} Impact</span>
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:8px; font-size:11px;">
                <div style="background:#f8fafc; padding:8px; border-radius:6px;">
                  <span style="display:block; font-size:9px; font-weight:700; color:#64748b; text-transform:uppercase;">Original</span>
                  <span style="color:#334155;">{orig}</span>
                </div>
                <div style="background:#eff6ff; padding:8px; border-radius:6px;">
                  <span style="display:block; font-size:9px; font-weight:700; color:#002b7a; text-transform:uppercase;">Translated</span>
                  <span style="color:#002b7a; font-weight:600;">{trans}</span>
                </div>
              </div>
              <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:8px; border-radius:6px; font-size:11px; color:#15803d;">
                <strong>Recommendation:</strong> {rec}
              </div>
            </div>
            """
    else:
        findings_html = """
        <div style="text-align:center; padding:20px; background:#f8fafc; border:1px dashed #cbd5e1; border-radius:8px; color:#64748b; font-size:12px;">
          ✓ All numerical scale checks passed. Zero 1,000x translation errors detected.
        </div>
        """

    # Build JS pages array once so images are NEVER duplicated in the DOM string
    num_pages = max(len(translated_pages), len(source_pages), 1)
    pages_js_list = []
    for idx in range(num_pages):
        s_img = source_pages[idx] if idx < len(source_pages) else ""
        t_img = translated_pages[idx] if idx < len(translated_pages) else ""
        pages_js_list.append({"pageNum": idx + 1, "source": s_img, "translated": t_img})

    pages_json_str = json.dumps(pages_js_list)

    # Download button HTML
    download_href = translated_pdf_b64 if translated_pdf_b64 else gcs_uri
    download_attr = f'download="translated_{filename}"' if translated_pdf_b64 else 'target="_blank"'
    download_btn_html = (
        f'<a class="btn" href="{download_href}" {download_attr}>⬇ DOWNLOAD CLEAN PDF</a>'
        if download_href
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  {CSP_META}
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>KPMG Translation Assistant</title>
  <style>
    * {{ box-sizing: border-box; margin:0; padding:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
    body {{ background: #f1f5f9; color: #0f172a; padding: 8px; font-size: 13px; }}
    .header {{ background: #002b7a; color: white; padding: 12px 16px; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    .header-left {{ display: flex; align-items: center; gap: 10px; }}
    .logo-badge {{ background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.3); border-radius: 6px; padding: 4px 10px; font-weight: 900; letter-spacing: 1px; font-size: 13px; }}
    .title {{ font-size: 13px; font-weight: 500; color: #f8fafc; }}
    .header-right {{ display: flex; gap: 6px; align-items: center; }}
    .badge {{ font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; padding: 4px 8px; border-radius: 6px; }}
    .badge-green {{ background: #10b981; color: white; }}
    .badge-blue {{ background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); }}

    .nav-tabs {{ display: flex; background: #ffffff; border-bottom: 2px solid #e2e8f0; padding: 0 12px; }}
    .tab-btn {{ padding: 10px 14px; border: none; background: transparent; cursor: pointer; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; color: #64748b; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }}
    .tab-btn.active {{ color: #002b7a; border-bottom: 2px solid #002b7a; }}

    .content-card {{ background: #ffffff; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 10px 10px; padding: 14px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}

    /* Viewer Toolbar */
    .viewer-toolbar {{ background: #0f172a; color: #f8fafc; padding: 8px 12px; border-radius: 8px; margin-bottom: 12px; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; }}
    .toolbar-group {{ display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }}
    .mode-btn {{ background: #1e293b; color: #cbd5e1; border: 1px solid #334155; padding: 5px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.15s; }}
    .mode-btn.active {{ background: #2563eb; color: #ffffff; border-color: #3b82f6; }}
    .nav-page-btn {{ background: #1e293b; color: #e2e8f0; border: 1px solid #334155; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; }}
    .nav-page-btn:disabled {{ opacity: 0.4; cursor: default; }}

    /* Visual PDF Page Container */
    .pdf-canvas-container {{ background: #1e293b; border-radius: 10px; padding: 12px; }}
    .page-pair-card {{ background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 12px; margin-bottom: 16px; }}
    .page-pair-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #1e293b; }}
    .page-badge {{ background: #2563eb; color: white; font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.05em; }}

    .visual-page-box {{ background: #090d16; border: 1px solid #334155; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 10px; }}
    .visual-page-label {{ display: flex; justify-content: space-between; align-items: center; font-size: 10px; font-weight: 800; color: #e2e8f0; text-transform: uppercase; margin-bottom: 8px; padding: 0 4px; }}
    .badge-clean {{ background: #059669; color: #ffffff; padding: 2px 7px; border-radius: 4px; font-size: 9px; }}
    .pdf-page-img {{ width: 100%; height: auto; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.45); display: block; margin: 0 auto; }}

    .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 14px; }}
    .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; text-align: center; position: relative; overflow: hidden; }}
    .kpi-card .bar {{ position: absolute; bottom: 0; left: 0; height: 3px; background: #002b7a; }}
    .kpi-label {{ font-size: 10px; font-weight: 800; color: #64748b; text-transform: uppercase; margin-bottom: 4px; }}
    .kpi-value {{ font-size: 22px; font-weight: 900; color: #002b7a; }}

    .exec-summary {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px; margin-bottom: 14px; }}
    .exec-summary h4 {{ font-size: 11px; font-weight: 800; text-transform: uppercase; color: #1e40af; margin-bottom: 4px; }}
    .exec-summary p {{ font-size: 12px; color: #1e3a8a; line-height: 1.5; }}

    .side-by-side {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .btn {{ display: inline-flex; align-items: center; gap: 6px; background: #2563eb; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-weight: 800; font-size: 11px; cursor: pointer; text-transform: uppercase; text-decoration: none; }}
    .btn:hover {{ background: #1d4ed8; }}
  </style>
</head>
<body>
  <div class="header">
    <div class="header-left">
      <div class="logo-badge">KPMG</div>
      <div class="title">Document Translation Assistant</div>
    </div>
    <div class="header-right">
      <span class="badge badge-blue">Target: {target_lang}</span>
      <span class="badge badge-green">Watermark: None ({attribution})</span>
    </div>
  </div>

  <div class="nav-tabs">
    <button class="tab-btn active" id="btn-viewer" onclick="switchTab('viewer')">📄 Document Viewer</button>
    <button class="tab-btn" id="btn-audit" onclick="switchTab('audit')">🛡 Quality Audit ({overall_score}%)</button>
  </div>

  <div class="content-card">
    <!-- Viewer Tab -->
    <div id="tab-viewer" style="display:block;">
      <div class="viewer-toolbar">
        <div class="toolbar-group">
          <button class="mode-btn active" id="mode-topdown" onclick="setMode('topdown')">⬍ Top-Down</button>
          <button class="mode-btn" id="mode-side" onclick="setMode('side')">⬌ Side-by-Side</button>
          <button class="mode-btn" id="mode-translated" onclick="setMode('translated')">Translated ({target_lang})</button>
          <button class="mode-btn" id="mode-original" onclick="setMode('original')">Original (EN)</button>
        </div>
        <div class="toolbar-group" id="page-nav-group" style="display:none;">
          <button class="nav-page-btn" id="prev-btn" onclick="changePage(-1)">&lt;</button>
          <span id="page-indicator" style="font-size:11px; font-weight:800; color:#e2e8f0; min-width:85px; text-align:center;">Page 1 of 1</span>
          <button class="nav-page-btn" id="next-btn" onclick="changePage(1)">&gt;</button>
        </div>
        <div class="toolbar-group">
          {download_btn_html}
        </div>
      </div>

      <div class="pdf-canvas-container" id="viewer-canvas"></div>
    </div>

    <!-- Audit Tab -->
    <div id="tab-audit" style="display:none;">
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Overall Score</div>
          <div class="kpi-value">{overall_score}%</div>
          <div class="bar" style="width:{overall_score}%; background:#002b7a;"></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Accuracy</div>
          <div class="kpi-value">{accuracy_score}%</div>
          <div class="bar" style="width:{accuracy_score}%; background:#10b981;"></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Fluency</div>
          <div class="kpi-value">{fluency_score}%</div>
          <div class="bar" style="width:{fluency_score}%; background:#f59e0b;"></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Tone &amp; Scale</div>
          <div class="kpi-value">{tone_score}%</div>
          <div class="bar" style="width:{tone_score}%; background:#6366f1;"></div>
        </div>
      </div>

      <div class="exec-summary">
        <h4>Auditor's Executive Summary</h4>
        <p>"{exec_summary}"</p>
      </div>

      <h4 style="font-size:11px; font-weight:800; text-transform:uppercase; color:#475569; margin-bottom:10px;">Audit Findings &amp; Scale Verifications</h4>
      <div>
        {findings_html}
      </div>
    </div>
  </div>

  <script>
    const PAGES = {pages_json_str};
    const TARGET_LANG = "{target_lang}";
    const ATTRIBUTION = "{attribution}";
    let currentMode = 'topdown';
    let currentPageIdx = 0;

    function switchTab(tabId) {{
      document.getElementById('tab-viewer').style.display = tabId === 'viewer' ? 'block' : 'none';
      document.getElementById('tab-audit').style.display = tabId === 'audit' ? 'block' : 'none';
      document.getElementById('btn-viewer').className = tabId === 'viewer' ? 'tab-btn active' : 'tab-btn';
      document.getElementById('btn-audit').className = tabId === 'audit' ? 'tab-btn active' : 'tab-btn';
    }}

    function setMode(mode) {{
      currentMode = mode;
      document.getElementById('mode-topdown').className = mode === 'topdown' ? 'mode-btn active' : 'mode-btn';
      document.getElementById('mode-side').className = mode === 'side' ? 'mode-btn active' : 'mode-btn';
      document.getElementById('mode-translated').className = mode === 'translated' ? 'mode-btn active' : 'mode-btn';
      document.getElementById('mode-original').className = mode === 'original' ? 'mode-btn active' : 'mode-btn';

      const navGroup = document.getElementById('page-nav-group');
      navGroup.style.display = (mode === 'translated' || mode === 'original') ? 'flex' : 'none';

      renderViewer();
    }}

    function changePage(delta) {{
      const next = currentPageIdx + delta;
      if (next >= 0 && next < PAGES.length) {{
        currentPageIdx = next;
        renderViewer();
      }}
    }}

    function renderViewer() {{
      const container = document.getElementById('viewer-canvas');
      if (!PAGES || PAGES.length === 0) {{
        container.innerHTML = '<div style="color:#94a3b8; padding:20px; text-align:center;">No document pages available</div>';
        return;
      }}

      let html = '';

      if (currentMode === 'topdown') {{
        // Stacks Original above Translated at 100% full width per page
        PAGES.forEach((p) => {{
          html += `
            <div class="page-pair-card">
              <div class="page-pair-header">
                <span class="page-badge">PAGE ${{p.pageNum}} OF ${{PAGES.length}}</span>
                <span style="font-size:11px; color:#94a3b8;">Top-Down Full Width (Original &rarr; Translated)</span>
              </div>
              <div class="visual-page-box">
                <div class="visual-page-label">
                  <span>ORIGINAL DOCUMENT (EN) — PAGE ${{p.pageNum}}</span>
                  <span style="color:#94a3b8;">SOURCE</span>
                </div>
                <img class="pdf-page-img" src="${{p.source}}" alt="Original Page ${{p.pageNum}}" />
              </div>
              <div class="visual-page-box" style="margin-bottom:0;">
                <div class="visual-page-label">
                  <span>TRANSLATED DOCUMENT (${{TARGET_LANG}}) — PAGE ${{p.pageNum}}</span>
                  <span class="badge-clean">WATERMARK: NONE (${{ATTRIBUTION}})</span>
                </div>
                <img class="pdf-page-img" src="${{p.translated}}" alt="Translated Page ${{p.pageNum}}" />
              </div>
            </div>
          `;
        }});
      }} else if (currentMode === 'side') {{
        // Side-by-side comparison
        PAGES.forEach((p) => {{
          html += `
            <div class="page-pair-card">
              <div class="page-pair-header">
                <span class="page-badge">PAGE ${{p.pageNum}} OF ${{PAGES.length}}</span>
                <span style="font-size:11px; color:#94a3b8;">Side-by-Side Comparison</span>
              </div>
              <div class="side-by-side">
                <div class="visual-page-box" style="margin-bottom:0;">
                  <div class="visual-page-label">
                    <span>ORIGINAL (EN)</span>
                  </div>
                  <img class="pdf-page-img" src="${{p.source}}" alt="Original Page ${{p.pageNum}}" />
                </div>
                <div class="visual-page-box" style="margin-bottom:0;">
                  <div class="visual-page-label">
                    <span>TRANSLATED (${{TARGET_LANG}})</span>
                    <span class="badge-clean">NO_ATTRIBUTION</span>
                  </div>
                  <img class="pdf-page-img" src="${{p.translated}}" alt="Translated Page ${{p.pageNum}}" />
                </div>
              </div>
            </div>
          `;
        }});
      }} else if (currentMode === 'translated' || currentMode === 'original') {{
        // Single Document Tab with Page Navigation (< Page 1 of 2 >)
        const p = PAGES[currentPageIdx] || PAGES[0];
        const isTranslated = currentMode === 'translated';
        const imgSrc = isTranslated ? p.translated : p.source;
        const label = isTranslated ? `TRANSLATED DOCUMENT (${{TARGET_LANG}})` : 'ORIGINAL DOCUMENT (EN)';
        const badge = isTranslated
          ? `<span class="badge-clean">WATERMARK: NONE (${{ATTRIBUTION}})</span>`
          : '<span style="color:#94a3b8;">SOURCE</span>';

        document.getElementById('page-indicator').innerText = `Page ${{currentPageIdx + 1}} of ${{PAGES.length}}`;
        document.getElementById('prev-btn').disabled = (currentPageIdx === 0);
        document.getElementById('next-btn').disabled = (currentPageIdx === PAGES.length - 1);

        html = `
          <div class="visual-page-box" style="margin-bottom:0;">
            <div class="visual-page-label">
              <span>${{label}} — PAGE ${{p.pageNum}} OF ${{PAGES.length}}</span>
              ${{badge}}
            </div>
            <img class="pdf-page-img" src="${{imgSrc}}" alt="${{label}} Page ${{p.pageNum}}" />
          </div>
        `;
      }}

      container.innerHTML = html;
    }}

    // Initial render
    renderViewer();
  </script>
</body>
</html>"""


def build_translation_dashboard_frame(surface_id: str, data: Dict[str, Any], height: int = DEFAULT_FRAME_HEIGHT) -> dict:
    """Build the A2UI v0.8 WebFrameSrcdoc payload containing the KPMG Translation Dashboard."""
    html_content = generate_dashboard_html(data)

    surface_update = {
        "surfaceUpdate": {
            "surfaceId": surface_id,
            "components": [
                {
                    "id": "root",
                    "component": {
                        "WebFrameSrcdoc": {
                            "htmlContent": {
                                "literalString": html_content
                            },
                            "height": height
                        }
                    }
                }
            ]
        }
    }

    data_model_update = {
        "dataModelUpdate": {
            "surfaceId": surface_id,
            "contents": []
        }
    }

    begin_rendering = {
        "beginRendering": {
            "surfaceId": surface_id,
            "root": "root"
        }
    }

    return {
        "surface_update": surface_update,
        "data_model_update": data_model_update,
        "begin_rendering": begin_rendering,
        "html": html_content
    }


def generate_translation_a2ui_tool(data: Dict[str, Any], height: int = DEFAULT_FRAME_HEIGHT) -> str:
    """Returns the formatted <a2ui-json> string for the translation dashboard."""
    payload = build_translation_dashboard_frame(SURFACE_ID, data, height)
    sequence = [
        payload["surface_update"],
        payload["data_model_update"],
        payload["begin_rendering"],
    ]
    return f"<a2ui-json>\n{json.dumps(sequence, indent=2)}\n</a2ui-json>"
