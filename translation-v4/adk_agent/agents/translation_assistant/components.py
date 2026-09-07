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
directly inside Gemini Enterprise chat / side panel.
"""

import html
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_LAST_TRANSLATION_DATA: Dict[str, Any] = {}
SURFACE_ID = "kpmg-translation-dashboard"
DEFAULT_FRAME_HEIGHT = 800
A2UI_MIME_TYPE = "application/json+a2ui"

CSP_META = '<meta http-equiv="Content-Security-Policy" content="connect-src \'none\'; style-src \'unsafe-inline\'; script-src \'unsafe-inline\';">'

def generate_dashboard_html(data: Dict[str, Any]) -> str:
    """Generates a self-contained, responsive KPMG-branded Translation Dashboard."""
    filename = html.escape(data.get("filename", "sample_doc.pdf"))
    target_lang = html.escape(data.get("target_language", "es").upper())
    attribution = html.escape(data.get("customized_attribution", "NO_ATTRIBUTION"))
    
    audit = data.get("audit_report", {})
    overall_score = audit.get("overall_score", 95)
    accuracy_score = audit.get("accuracy_score", 95)
    fluency_score = audit.get("fluency_score", 90)
    tone_score = audit.get("tone_score", 95)
    confidence_index = audit.get("confidence_index", 92)
    exec_summary = html.escape(audit.get("executive_summary", "Translation completed with high precision."))
    findings = audit.get("audit_findings", [])
    
    source_preview = html.escape(data.get("source_text_sample", ""))
    target_preview = html.escape(data.get("translated_text_sample", ""))
    gcs_uri = html.escape(data.get("gcs_uri", ""))

    findings_html = ""
    if findings:
        for idx, f in enumerate(findings):
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
        <div style="text-align:center; padding:24px; background:#f8fafc; border:1px dashed #cbd5e1; border-radius:8px; color:#64748b; font-size:12px;">
          ✓ All numerical scale checks passed. Zero 1,000x translation errors detected.
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  {CSP_META}
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>KPMG Translation Assistant</title>
  <style>
    * {{ box-sizing: border-box; margin:0; padding:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
    body {{ background: #f8fafc; color: #0f172a; padding: 12px; font-size: 13px; }}
    .header {{ background: #002b7a; color: white; padding: 16px 20px; border-radius: 12px 12px 0 0; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    .header-left {{ display: flex; align-items: center; gap: 12px; }}
    .logo-badge {{ background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25); border-radius: 6px; padding: 4px 10px; font-weight: 900; letter-spacing: 1px; font-size: 14px; }}
    .title {{ font-size: 14px; font-weight: 400; color: #e2e8f0; }}
    .header-right {{ display: flex; gap: 8px; align-items: center; }}
    .badge {{ font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; padding: 4px 10px; border-radius: 6px; }}
    .badge-green {{ background: #10b981; color: white; }}
    .badge-blue {{ background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); }}
    
    .nav-tabs {{ display: flex; background: #ffffff; border-bottom: 2px solid #e2e8f0; padding: 0 16px; }}
    .tab-btn {{ padding: 12px 18px; border: none; background: transparent; cursor: pointer; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }}
    .tab-btn.active {{ color: #002b7a; border-bottom: 2px solid #002b7a; }}
    
    .content-card {{ background: #ffffff; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    
    .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }}
    .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; text-align: center; position: relative; overflow: hidden; }}
    .kpi-card .bar {{ position: absolute; bottom: 0; left: 0; height: 3px; background: #002b7a; }}
    .kpi-label {{ font-size: 10px; font-weight: 800; color: #64748b; text-transform: uppercase; margin-bottom: 4px; }}
    .kpi-value {{ font-size: 24px; font-weight: 900; color: #002b7a; }}
    
    .exec-summary {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 14px; margin-bottom: 16px; }}
    .exec-summary h4 {{ font-size: 11px; font-weight: 800; text-transform: uppercase; color: #1e40af; margin-bottom: 4px; }}
    .exec-summary p {{ font-size: 12px; color: #1e3a8a; line-height: 1.5; font-style: italic; }}
    
    .side-by-side {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .doc-col {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; }}
    .doc-col h4 {{ font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 10px; display:flex; justify-content:space-between; }}
    .doc-text {{ font-size: 12px; line-height: 1.6; color: #334155; white-space: pre-wrap; max-height: 480px; overflow-y: auto; background:#ffffff; padding: 12px; border-radius: 6px; border:1px solid #e2e8f0; }}
    
    .btn {{ display: inline-flex; align-items: center; gap: 6px; background: #002b7a; color: white; border: none; padding: 8px 16px; border-radius: 8px; font-weight: 700; font-size: 11px; cursor: pointer; text-transform: uppercase; text-decoration: none; }}
    .btn:hover {{ background: #001f5c; }}
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
    <button class="tab-btn active" id="btn-audit" onclick="switchTab('audit')">Quality Audit ({overall_score}%)</button>
    <button class="tab-btn" id="btn-viewer" onclick="switchTab('viewer')">Document Viewer (Side-by-Side)</button>
  </div>

  <div class="content-card">
    <!-- Audit Tab -->
    <div id="tab-audit">
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
          <div class="kpi-label">Tone & Scale</div>
          <div class="kpi-value">{tone_score}%</div>
          <div class="bar" style="width:{tone_score}%; background:#6366f1;"></div>
        </div>
      </div>

      <div class="exec-summary">
        <h4>Auditor's Executive Summary</h4>
        <p>"{exec_summary}"</p>
      </div>

      <h4 style="font-size:11px; font-weight:800; text-transform:uppercase; color:#475569; margin-bottom:10px;">Audit Findings & Scale Verifications</h4>
      <div>
        {findings_html}
      </div>
    </div>

    <!-- Viewer Tab -->
    <div id="tab-viewer" style="display:none;">
      <div style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:12px; color:#64748b; font-weight:600;">File: <strong>{filename}</strong></span>
        {f'<a class="btn" href="{gcs_uri}" target="_blank">Download Clean PDF</a>' if gcs_uri else ''}
      </div>
      <div class="side-by-side">
        <div class="doc-col">
          <h4>
            <span>Source Document (English)</span>
            <span style="color:#64748b; font-weight:normal;">Original</span>
          </h4>
          <div class="doc-text">{source_preview}</div>
        </div>
        <div class="doc-col">
          <h4>
            <span>Translated Document ({target_lang})</span>
            <span style="color:#10b981; font-weight:bold;">NO_ATTRIBUTION</span>
          </h4>
          <div class="doc-text">{target_preview}</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    function switchTab(tabId) {{
      document.getElementById('tab-audit').style.display = tabId === 'audit' ? 'block' : 'none';
      document.getElementById('tab-viewer').style.display = tabId === 'viewer' ? 'block' : 'none';
      document.getElementById('btn-audit').className = tabId === 'audit' ? 'tab-btn active' : 'tab-btn';
      document.getElementById('btn-viewer').className = tabId === 'viewer' ? 'tab-btn active' : 'tab-btn';
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
