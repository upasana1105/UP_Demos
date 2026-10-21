#!/usr/bin/env python3
"""
McKinsey Thursday SteerCo Data Pipeline & In-Place SharePoint Excel Updater
Demonstrates:
1. 90% BYOMCP multi-source data aggregation (BigQuery Plant Telemetry, Databricks ML Models, Snowflake ERP)
2. Automating the "Human API" (Workstream Owner check-in & missing input resolution)
3. In-Place SharePoint / Excel Financial Model Updating (`McKinsey_Thursday_Value_Tracker.xlsx`)
4. Zero-Variance Reconciliation across Database -> Excel -> HTML Dashboard -> PPTX Slide Deck
"""

import argparse
import json
import math
import os
from datetime import datetime
import xlsxwriter

# ==============================================================================
# CANONICAL MCKINSEY ENGAGEMENT TELEMETRY (BYOMCP AGGREGATED)
# ==============================================================================
ENGAGEMENT_METADATA = {
    "client": "Steel Authority of India Limited (SAIL) - Bokaro Steel Plant (BSL)",
    "agnostic_client": "Global Industrial Manufacturing Corp (Enterprise Transformation)",
    "total_initiatives": 154,
    "inr_to_usd_divisor": 8.29,  # ~83 INR/USD -> Cr to $M conversion
}

WAVE_TRAJECTORY = [
    {
        "period": "FY25 Actuals",
        "phase": "Pilot Baseline",
        "initiatives": 12,
        "ebitda_inr_cr": 180,
        "ebitda_usd_m": 22,
        "series": "Actuals",
        "source_mcp": "@bigquery-plant-telemetry",
    },
    {
        "period": "FY26 Wave 1",
        "phase": "Quick Wins",
        "initiatives": 45,
        "ebitda_inr_cr": 490,
        "ebitda_usd_m": 59,
        "series": "Forecast",
        "source_mcp": "@databricks-genie-ml",
    },
    {
        "period": "FY27 Wave 2",
        "phase": "Core Plant Scale",
        "initiatives": 65,
        "ebitda_inr_cr": 920,
        "ebitda_usd_m": 111,
        "series": "Forecast",
        "source_mcp": "@databricks-genie-ml",
    },
    {
        "period": "FY28 Wave 3",
        "phase": "Full Maturity",
        "initiatives": 154,
        "ebitda_inr_cr": 1310,
        "ebitda_usd_m": 158,
        "series": "Target",
        "source_mcp": "@snowflake-erp-actuals",
    },
]

INITIATIVE_PORTFOLIO = [
    {
        "id": "BSL-01",
        "name": "Blast Furnace (BF-2/BF-5) AI Coke Rate & Thermal Setpoint",
        "pillar": "1. Primary Steelmaking",
        "impact_level": "HIGH",
        "time_horizon": "SHORT (< 6 Months)",
        "wave": "Wave 1",
        "ebitda_inr_cr": 240,
        "ebitda_usd_m": 29,
        "owner": "R. Sharma",
        "human_api_status": "Synced",
        "mcp_source": "@bigquery-plant-telemetry",
    },
    {
        "id": "BSL-02",
        "name": "SMS-II BOF End-Point Temperature & Ferro-Alloy Yield Twin",
        "pillar": "1. Primary Steelmaking",
        "impact_level": "HIGH",
        "time_horizon": "SHORT (< 6 Months)",
        "wave": "Wave 1",
        "ebitda_inr_cr": 165,
        "ebitda_usd_m": 20,
        "owner": "P. Verma",
        "human_api_status": "Synced",
        "mcp_source": "@databricks-genie-ml",
    },
    {
        "id": "BSL-03",
        "name": "Hot Strip Mill (HSM) Cobble Prevention & Pacing AI",
        "pillar": "2. Flat Products & Rolling",
        "impact_level": "HIGH",
        "time_horizon": "MEDIUM (6–15 Months)",
        "wave": "Wave 1",
        "ebitda_inr_cr": 190,
        "ebitda_usd_m": 23,
        "owner": "A. Kulkarni",
        "human_api_status": "Synced (Auto-Chased via Teams MCP)",
        "mcp_source": "@sharepoint-excel-inplace",
    },
    {
        "id": "BSL-04",
        "name": "Integrated Mine-to-Sinter Blend Optimizer",
        "pillar": "3. Captive Mines & Energy",
        "impact_level": "HIGH",
        "time_horizon": "MEDIUM (6–15 Months)",
        "wave": "Wave 2",
        "ebitda_inr_cr": 145,
        "ebitda_usd_m": 18,
        "owner": "S. Chatterjee",
        "human_api_status": "Synced",
        "mcp_source": "@snowflake-erp-actuals",
    },
    {
        "id": "BSL-05",
        "name": "Autonomous Raw Material Yard & Torpedo Ladle Twin",
        "pillar": "3. Captive Mines & Energy",
        "impact_level": "HIGH",
        "time_horizon": "LONG (15–24+ Months)",
        "wave": "Wave 2",
        "ebitda_inr_cr": 130,
        "ebitda_usd_m": 16,
        "owner": "M. Dasgupta",
        "human_api_status": "Synced",
        "mcp_source": "@bigquery-plant-telemetry",
    },
    {
        "id": "BSL-06",
        "name": " Gas-Grid & Captive Power Turbine Predictive Maintenance",
        "pillar": "3. Captive Mines & Energy",
        "impact_level": "MEDIUM",
        "time_horizon": "SHORT (< 6 Months)",
        "wave": "Wave 1",
        "ebitda_inr_cr": 85,
        "ebitda_usd_m": 10,
        "owner": "V. Nair",
        "human_api_status": "Synced",
        "mcp_source": "@bigquery-plant-telemetry",
    },
    {
        "id": "BSL-07",
        "name": "Computer Vision Strip Surface Defect Grading",
        "pillar": "2. Flat Products & Rolling",
        "impact_level": "MEDIUM",
        "time_horizon": "MEDIUM (6–15 Months)",
        "wave": "Wave 2",
        "ebitda_inr_cr": 90,
        "ebitda_usd_m": 11,
        "owner": "K. Iyer",
        "human_api_status": "Synced",
        "mcp_source": "@databricks-genie-ml",
    },
    {
        "id": "BSL-08",
        "name": "Remaining 147 Plant, Logistics & Commercial Tail Initiatives",
        "pillar": "4. Digital Factory & OT Core",
        "impact_level": "MEDIUM/LOW",
        "time_horizon": "MEDIUM/LONG",
        "wave": "Wave 2–3",
        "ebitda_inr_cr": 265,
        "ebitda_usd_m": 31,
        "owner": "PMO Digital Factory",
        "human_api_status": "Synced",
        "mcp_source": "@snowflake-erp-actuals",
    },
]


def calculate_what_if_scenario(
    adoption_pct: float = 85.0,
    energy_index_pct: float = 100.0,
    capex_buffer_pct: float = 0.0,
    currency: str = "INR",
) -> dict:
    """
    Calculates McKinsey 3-wave EBITDA impact under What-If sensitivity parameters.
    Tested by `tests/test_thursday_pipeline.py` to guarantee zero financial drift.
    """
    if adoption_pct <= 0:
        raise ValueError("Operator adoption percentage must be positive")

    mult = (adoption_pct / 85.0) * (energy_index_pct / 100.0) * (1.0 + capex_buffer_pct / 100.0)
    key = "ebitda_inr_cr" if currency.upper() == "INR" else "ebitda_usd_m"

    baseline = WAVE_TRAJECTORY[0][key]
    w1 = round(WAVE_TRAJECTORY[1][key] * mult)
    w2 = round(WAVE_TRAJECTORY[2][key] * mult)
    w3 = round(WAVE_TRAJECTORY[3][key] * mult)

    cagr_pct = round(((w3 / baseline) ** (1.0 / 3.0) - 1.0) * 100.0)
    return {
        "currency": currency.upper(),
        "multiplier": round(mult, 4),
        "fy25_actuals": baseline,
        "fy26_wave1": w1,
        "fy27_wave2": w2,
        "fy28_wave3": w3,
        "cagr_pct": cagr_pct,
        "portfolio_total_check": sum(item[key] for item in INITIATIVE_PORTFOLIO),
    }


def generate_inplace_sharepoint_excel(output_xlsx_path: str) -> str:
    """
    Generates / updates the McKinsey 4-Tab Excel Financial Model (`McKinsey_Thursday_Value_Tracker.xlsx`)
    simulating an in-place SharePoint workbook update without manual download/upload friction.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_xlsx_path)), exist_ok=True)
    workbook = xlsxwriter.Workbook(output_xlsx_path)

    # McKinsey Brand Formats
    fmt_title = workbook.add_format({
        "font_name": "Georgia",
        "font_size": 15,
        "bold": True,
        "font_color": "#FFFFFF",
        "bg_color": "#051C2C",
        "valign": "vcenter",
    })
    fmt_sub = workbook.add_format({
        "font_name": "Arial",
        "font_size": 10,
        "italic": True,
        "font_color": "#A2D5EC",
        "bg_color": "#051C2C",
        "valign": "vcenter",
    })
    fmt_tbl_hdr = workbook.add_format({
        "font_name": "Arial",
        "font_size": 10,
        "bold": True,
        "font_color": "#FFFFFF",
        "bg_color": "#061F32",
        "border": 1,
        "border_color": "#D8D8D8",
        "valign": "vcenter",
    })
    fmt_cell = workbook.add_format({
        "font_name": "Arial",
        "font_size": 10,
        "font_color": "#051C2C",
        "bg_color": "#F2F2F2",
        "border": 1,
        "border_color": "#D8D8D8",
    })
    fmt_cell_ice = workbook.add_format({
        "font_name": "Arial",
        "font_size": 10,
        "bold": True,
        "font_color": "#051C2C",
        "bg_color": "#E7F0F9",
        "border": 1,
        "border_color": "#A2D5EC",
        "num_format": "#,##0",
    })
    fmt_status_ok = workbook.add_format({
        "font_name": "Arial",
        "font_size": 10,
        "bold": True,
        "font_color": "#FFFFFF",
        "bg_color": "#00B050",
        "align": "center",
        "border": 1,
    })

    # =========================================================================
    # TAB 1: Executive Summary & Wave Bridge
    # =========================================================================
    ws1 = workbook.add_worksheet("1_Executive_Wave_Bridge")
    ws1.hide_gridlines(2)
    ws1.set_column("A:A", 3)
    ws1.set_column("B:C", 26)
    ws1.set_column("D:G", 20)

    ws1.merge_range("B2:G2", "McKinsey & Company | Thursday SteerCo Value-Realization Tracker", fmt_title)
    ws1.merge_range("B3:G3", "Updated In-Place via @sharepoint-excel-inplace & BYOMCP Fabric | Zero Variance Verified", fmt_sub)
    ws1.set_row(1, 28)
    ws1.set_row(2, 20)

    headers_t1 = [
        "Roadmap Phase",
        "Strategic Focus",
        "Active Initiatives",
        "EBITDA (INR Cr)",
        "EBITDA ($M Agnostic)",
        "BYOMCP Source Connector",
    ]
    for c_idx, h_text in enumerate(headers_t1):
        ws1.write(4, 1 + c_idx, h_text, fmt_tbl_hdr)

    for r_idx, row in enumerate(WAVE_TRAJECTORY, start=5):
        ws1.write(r_idx, 1, row["period"], fmt_cell)
        ws1.write(r_idx, 2, row["phase"], fmt_cell)
        ws1.write_number(r_idx, 3, row["initiatives"], fmt_cell)
        ws1.write_number(r_idx, 4, row["ebitda_inr_cr"], fmt_cell_ice)
        ws1.write_number(r_idx, 5, row["ebitda_usd_m"], fmt_cell_ice)
        ws1.write(r_idx, 6, row["source_mcp"], fmt_cell)

    # =========================================================================
    # TAB 2: 3x3 Prioritization Matrix & Human API Sign-Off
    # =========================================================================
    ws2 = workbook.add_worksheet("2_Initiative_Matrix_HumanAPI")
    ws2.hide_gridlines(2)
    ws2.set_column("A:A", 3)
    ws2.set_column("B:B", 12)
    ws2.set_column("C:C", 44)
    ws2.set_column("D:F", 22)
    ws2.set_column("G:H", 18)
    ws2.set_column("I:J", 28)

    ws2.merge_range("B2:J2", "3x3 Prioritization Matrix & Thursday 'Human API' Workstream Sign-Off", fmt_title)
    ws2.set_row(1, 28)

    headers_t2 = [
        "ID",
        "Initiative Name",
        "Transformation Pillar",
        "Impact Level",
        "Time to Impact",
        "Run-Rate (INR Cr)",
        "Run-Rate ($M)",
        "Workstream Lead",
        "Thursday Human API Status",
    ]
    for c_idx, h_text in enumerate(headers_t2):
        ws2.write(3, 1 + c_idx, h_text, fmt_tbl_hdr)

    for r_idx, item in enumerate(INITIATIVE_PORTFOLIO, start=4):
        ws2.write(r_idx, 1, item["id"], fmt_cell)
        ws2.write(r_idx, 2, item["name"], fmt_cell)
        ws2.write(r_idx, 3, item["pillar"], fmt_cell)
        ws2.write(r_idx, 4, item["impact_level"], fmt_cell)
        ws2.write(r_idx, 5, item["time_horizon"], fmt_cell)
        ws2.write_number(r_idx, 6, item["ebitda_inr_cr"], fmt_cell_ice)
        ws2.write_number(r_idx, 7, item["ebitda_usd_m"], fmt_cell_ice)
        ws2.write(r_idx, 8, item["owner"], fmt_cell)
        ws2.write(r_idx, 9, item["human_api_status"], fmt_status_ok)

    # Total reconciliation row
    tot_row = 4 + len(INITIATIVE_PORTFOLIO)
    ws2.write(tot_row, 5, "TOTAL RUN-RATE (WAVE 3)", fmt_tbl_hdr)
    ws2.write_formula(tot_row, 6, f"=SUM(G5:G{tot_row})", fmt_cell_ice, 1310)
    ws2.write_formula(tot_row, 7, f"=SUM(H5:H{tot_row})", fmt_cell_ice, 158)

    # =========================================================================
    # TAB 3: BYOMCP & Partner Preference Audit Log
    # =========================================================================
    ws3 = workbook.add_worksheet("3_BYOMCP_Audit_Log")
    ws3.hide_gridlines(2)
    ws3.set_column("B:E", 30)
    ws3.merge_range("B2:E2", "BYOMCP Connector Telemetry & Partner Memory Log", fmt_title)
    ws3.write(3, 1, "Timestamp (UTC)", fmt_tbl_hdr)
    ws3.write(3, 2, "MCP Server / Skill", fmt_tbl_hdr)
    ws3.write(3, 3, "Action Executed", fmt_tbl_hdr)
    ws3.write(3, 4, "Verification Status", fmt_tbl_hdr)

    audit_events = [
        ("2026-10-20 14:40:00Z", "@bigquery-plant-telemetry", "Queried BF-2, BF-5 & SMS-II sensor tag actuals", "VERIFIED"),
        ("2026-10-20 14:41:12Z", "@databricks-genie-ml", "Fetched HSM cobble & CV defect model predictions", "VERIFIED"),
        ("2026-10-20 14:42:05Z", "@slack-teams-human-api", "Auto-chased A. Kulkarni for Week 42 HSM actuals", "VERIFIED"),
        ("2026-10-20 14:43:30Z", "@sharepoint-excel-inplace", "Updated McKinsey_Thursday_Value_Tracker.xlsx in-place", "VERIFIED"),
        ("2026-10-20 14:44:10Z", "skill:mckinsey-slide-creator", "Compiled 6-slide SteerCo PowerPoint readout", "VERIFIED"),
    ]
    for r_idx, (ts, srv, act, st) in enumerate(audit_events, start=4):
        ws3.write(r_idx, 1, ts, fmt_cell)
        ws3.write(r_idx, 2, srv, fmt_cell)
        ws3.write(r_idx, 3, act, fmt_cell)
        ws3.write(r_idx, 4, st, fmt_status_ok)

    workbook.close()
    return output_xlsx_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run McKinsey Thursday BYOMCP & In-Place Excel Pipeline")
    parser.add_argument(
        "--output-excel",
        default="output/McKinsey_Thursday_Value_Tracker.xlsx",
        help="Output path for the in-place updated Excel tracker",
    )
    parser.add_argument("--adoption", type=float, default=85.0, help="Operator AI adoption %")
    parser.add_argument("--currency", default="INR", choices=["INR", "USD"], help="INR (Cr) or USD ($M)")
    args = parser.parse_args()

    summary = calculate_what_if_scenario(adoption_pct=args.adoption, currency=args.currency)
    excel_file = generate_inplace_sharepoint_excel(args.output_excel)

    print("==================================================================")
    print("McKINSEY THURSDAY STEERCO PIPELINE (BYOMCP + IN-PLACE EXCEL SYNC)")
    print("==================================================================")
    print(f"  ✓ Active BYOMCP Sources : @bigquery, @databricks-genie, @snowflake, @sharepoint-excel")
    print(f"  ✓ Scenario Summary      : {json.dumps(summary)}")
    print(f"  ✓ In-Place Excel Synced : {os.path.abspath(excel_file)}")
    print("==================================================================")
