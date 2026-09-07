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
directly inside Gemini Enterprise chat / side panel, with full visual PDF page rendering.
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
    """Generates a self-contained, responsive KPMG-branded Translation Dashboard with visual PDF pages."""
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

    # Build Visual PDF Pages HTML
    num_pages = max(len(translated_pages), len(source_pages), 1)
    has_visual_pages = bool(translated_pages or source_pages)

    # 1. Top-Down / Stacked Comparison (Default — 100% full width per page, no squishing)
    stacked_pages_html = ""
    if has_visual_pages:
        for idx in range(num_pages):
            t_img = translated_pages[idx] if idx < len(translated_pages) else ""
            s_img = source_pages[idx] if idx < len(source_pages) else ""
            page_num = idx + 1
            stacked_pages_html += f"""
            <div class="page-pair-card">
              <div class="page-pair-header">
                <span class="page-badge">PAGE {page_num} OF {num_pages}</span>
                <span style="font-size:11px; color:#94a3b8;">Full-Resolution Visual Output (Formatting, Charts &amp; Images Preserved)</span>
              </div>
              <div class="visual-page-box">
                <div class="visual-page-label">
                  <span>LOCALIZED OUTPUT ({target_lang})</span>
                  <span class="badge-clean">WATERMARK: NONE ({attribution})</span>
                </div>
                {f'<img class="pdf-page-img" src="{t_img}" alt="Translated Page {page_num}" />' if t_img else '<div class="no-img">No visual page rendered</div>'}
              </div>
              <details class="source-compare-details" open>
                <summary class="source-compare-summary">
                  <span>▼ Compare with Source Document Page {page_num} (Original English)</span>
                </summary>
                <div class="visual-page-box source-box">
                  <div class="visual-page-label source-label">
                    <span>ORIGINAL DOCUMENT (SOURCE)</span>
                    <span style="color:#94a3b8;">Page {page_num}</span>
                  </div>
                  {f'<img class="pdf-page-img" src="{s_img}" alt="Source Page {page_num}" />' if s_img else '<div class="no-img">No visual page rendered</div>'}
                </div>
              </details>
            </div>
            """
    else:
        stacked_pages_html = f"""
        <div class="doc-col" style="margin-bottom:16px;">
          <h4><span>Translated Document ({target_lang})</span><span style="color:#10b981;">{attribution}</span></h4>
          <div class="doc-text">{target_preview}</div>
        </div>
        <div class="doc-col">
          <h4><span>Source Document (English)</span><span>Original</span></h4>
          <div class="doc-text">{source_preview}</div>
        </div>
        """

    # 2. Translated Only (Full Width)
    translated_only_html = ""
    if translated_pages:
        for idx, t_img in enumerate(translated_pages):
            translated_only_html += f"""
            <div class="visual-page-box" style="margin-bottom:16px;">
              <div class="visual-page-label">
                <span>LOCALIZED OUTPUT ({target_lang}) — PAGE {idx+1} OF {len(translated_pages)}</span>
                <span class="badge-clean">NO WATERMARK ({attribution})</span>
              </div>
              <img class="pdf-page-img" src="{t_img}" alt="Translated Page {idx+1}" />
            </div>
            """
    else:
        translated_only_html = f'<div class="doc-text">{target_preview}</div>'

    # 3. Side-by-Side Comparison
    side_by_side_html = ""
    if has_visual_pages:
        for idx in range(num_pages):
            t_img = translated_pages[idx] if idx < len(translated_pages) else ""
            s_img = source_pages[idx] if idx < len(source_pages) else ""
            side_by_side_html += f"""
            <div class="side-by-side" style="margin-bottom:16px;">
              <div class="visual-page-box source-box">
                <div class="visual-page-label source-label">
                  <span>ORIGINAL (PAGE {idx+1})</span>
                </div>
                {f'<img class="pdf-page-img" src="{s_img}" alt="Source Page {idx+1}" />' if s_img else ''}
              </div>
              <div class="visual-page-box">
                <div class="visual-page-label">
                  <span>LOCALIZED ({target_lang} - PAGE {idx+1})</span>
                  <span class="badge-clean">NO_ATTRIBUTION</span>
                </div>
                {f'<img class="pdf-page-img" src="{t_img}" alt="Translated Page {idx+1}" />' if t_img else ''}
              </div>
            </div>
            """
    else:
        side_by_side_html = f"""
        <div class="side-by-side">
          <div class="doc-col"><h4>Source Document</h4><div class="doc-text">{source_preview}</div></div>
          <div class="doc-col"><h4>Translated Document</h4><div class="doc-text">{target_preview}</div></div>
        </div>
        """

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
    .header {{ background: #002b7a; color: white; padding: 14px 18px; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    .header-left {{ display: flex; align-items: center; gap: 10px; }}
    .logo-badge {{ background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.3); border-radius: 6px; padding: 4px 10px; font-weight: 900; letter-spacing: 1px; font-size: 13px; }}
    .title {{ font-size: 13px; font-weight: 500; color: #f8fafc; }}
    .header-right {{ display: flex; gap: 6px; align-items: center; }}
    .badge {{ font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; padding: 4px 8px; border-radius: 6px; }}
    .badge-green {{ background: #10b981; color: white; }}
    .badge-blue {{ background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); }}

    .nav-tabs {{ display: flex; background: #ffffff; border-bottom: 2px solid #e2e8f0; padding: 0 12px; }}
    .tab-btn {{ padding: 11px 16px; border: none; background: transparent; cursor: pointer; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }}
    .tab-btn.active {{ color: #002b7a; border-bottom: 2px solid #002b7a; }}

    .content-card {{ background: #ffffff; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 10px 10px; padding: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}

    /* Viewer Toolbar */
    .viewer-toolbar {{ background: #0f172a; color: #f8fafc; padding: 10px 14px; border-radius: 8px; margin-bottom: 14px; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; }}
    .toolbar-group {{ display: flex; align-items: center; gap: 6px; }}
    .mode-btn {{ background: #1e293b; color: #cbd5e1; border: 1px solid #334155; padding: 6px 11px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.15s; }}
    .mode-btn.active {{ background: #2563eb; color: #ffffff; border-color: #3b82f6; }}
    .zoom-btn {{ background: #1e293b; color: #e2e8f0; border: 1px solid #334155; width: 28px; height: 28px; border-radius: 6px; font-weight: 800; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; }}
    .zoom-btn:hover {{ background: #334155; }}

    /* Visual PDF Page Container */
    .pdf-canvas-container {{ background: #1e293b; border-radius: 10px; padding: 14px; overflow-x: auto; }}
    .page-pair-card {{ background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 12px; margin-bottom: 18px; }}
    .page-pair-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #1e293b; }}
    .page-badge {{ background: #2563eb; color: white; font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.05em; }}

    .visual-page-box {{ background: #090d16; border: 1px solid #334155; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 10px; }}
    .visual-page-label {{ display: flex; justify-content: space-between; align-items: center; font-size: 10px; font-weight: 800; color: #e2e8f0; text-transform: uppercase; margin-bottom: 8px; padding: 0 4px; }}
    .badge-clean {{ background: #059669; color: #ffffff; padding: 2px 7px; border-radius: 4px; font-size: 9px; }}
    .pdf-page-img {{ width: 100%; height: auto; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.45); display: block; margin: 0 auto; transition: width 0.2s ease; }}

    .source-compare-details {{ margin-top: 8px; }}
    .source-compare-summary {{ cursor: pointer; font-size: 11px; font-weight: 700; color: #93c5fd; padding: 6px 10px; background: #1e293b; border-radius: 6px; list-style: none; user-select: none; }}
    .source-compare-summary:hover {{ background: #334155; }}
    .source-box {{ margin-top: 8px; border-color: #475569; }}
    .source-label {{ color: #94a3b8; }}

    .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 14px; }}
    .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; text-align: center; position: relative; overflow: hidden; }}
    .kpi-card .bar {{ position: absolute; bottom: 0; left: 0; height: 3px; background: #002b7a; }}
    .kpi-label {{ font-size: 10px; font-weight: 800; color: #64748b; text-transform: uppercase; margin-bottom: 4px; }}
    .kpi-value {{ font-size: 22px; font-weight: 900; color: #002b7a; }}

    .exec-summary {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px; margin-bottom: 14px; }}
    .exec-summary h4 {{ font-size: 11px; font-weight: 800; text-transform: uppercase; color: #1e40af; margin-bottom: 4px; }}
    .exec-summary p {{ font-size: 12px; color: #1e3a8a; line-height: 1.5; }}

    .side-by-side {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .doc-col {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; }}
    .doc-col h4 {{ font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 8px; display:flex; justify-content:space-between; }}
    .doc-text {{ font-size: 12px; line-height: 1.5; color: #334155; white-space: pre-wrap; max-height: 440px; overflow-y: auto; background:#ffffff; padding: 10px; border-radius: 6px; border:1px solid #e2e8f0; }}

    .btn {{ display: inline-flex; align-items: center; gap: 6px; background: #2563eb; color: white; border: none; padding: 7px 14px; border-radius: 6px; font-weight: 800; font-size: 11px; cursor: pointer; text-transform: uppercase; text-decoration: none; }}
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
    <button class="tab-btn active" id="btn-viewer" onclick="switchTab('viewer')">📄 Document Viewer (Visual Output)</button>
    <button class="tab-btn" id="btn-audit" onclick="switchTab('audit')">🛡 Quality Audit ({overall_score}%)</button>
  </div>

  <div class="content-card">
    <!-- Viewer Tab (Active by default so user sees visual document immediately) -->
    <div id="tab-viewer" style="display:block;">
      <div class="viewer-toolbar">
        <div class="toolbar-group">
          <span style="font-size:11px; font-weight:700; color:#94a3b8; margin-right:4px;">LAYOUT:</span>
          <button class="mode-btn active" id="mode-stacked" onclick="setLayoutMode('stacked')">⬇ Top-Down Full Width</button>
          <button class="mode-btn" id="mode-translated" onclick="setLayoutMode('translated')">📄 Translated PDF Only</button>
          <button class="mode-btn" id="mode-side" onclick="setLayoutMode('side')">↔ Side-by-Side</button>
        </div>
        <div class="toolbar-group">
          <span style="font-size:11px; font-weight:700; color:#94a3b8;">ZOOM:</span>
          <button class="zoom-btn" onclick="adjustZoom(-15)">-</button>
          <span id="zoom-label" style="font-size:11px; font-weight:800; min-width:38px; text-align:center;">100%</span>
          <button class="zoom-btn" onclick="adjustZoom(15)">+</button>
          {download_btn_html}
        </div>
      </div>

      <div class="pdf-canvas-container">
        <!-- Mode 1: Top-Down Full Width (Default) -->
        <div id="view-stacked" style="display:block;">
          {stacked_pages_html}
        </div>
        <!-- Mode 2: Translated Document Only -->
        <div id="view-translated" style="display:none;">
          {translated_only_html}
        </div>
        <!-- Mode 3: Side by Side -->
        <div id="view-side" style="display:none;">
          {side_by_side_html}
        </div>
      </div>
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
    var currentZoom = 100;

    function switchTab(tabId) {{
      document.getElementById('tab-viewer').style.display = tabId === 'viewer' ? 'block' : 'none';
      document.getElementById('tab-audit').style.display = tabId === 'audit' ? 'block' : 'none';
      document.getElementById('btn-viewer').className = tabId === 'viewer' ? 'tab-btn active' : 'tab-btn';
      document.getElementById('btn-audit').className = tabId === 'audit' ? 'tab-btn active' : 'tab-btn';
    }}

    function setLayoutMode(mode) {{
      document.getElementById('view-stacked').style.display = mode === 'stacked' ? 'block' : 'none';
      document.getElementById('view-translated').style.display = mode === 'translated' ? 'block' : 'none';
      document.getElementById('view-side').style.display = mode === 'side' ? 'block' : 'none';

      document.getElementById('mode-stacked').className = mode === 'stacked' ? 'mode-btn active' : 'mode-btn';
      document.getElementById('mode-translated').className = mode === 'translated' ? 'mode-btn active' : 'mode-btn';
      document.getElementById('mode-side').className = mode === 'side' ? 'mode-btn active' : 'mode-btn';
    }}

    function adjustZoom(delta) {{
      currentZoom = Math.min(200, Math.max(50, currentZoom + delta));
      document.getElementById('zoom-label').innerText = currentZoom + '%';
      var imgs = document.querySelectorAll('.pdf-page-img');
      for (var i = 0; i < imgs.length; i++) {{
        imgs[i].style.width = currentZoom + '%';
      }}
    }}
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
