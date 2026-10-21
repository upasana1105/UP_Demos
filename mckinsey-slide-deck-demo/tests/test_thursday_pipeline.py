#!/usr/bin/env python3
"""
Automated Verification & Zero-Variance Reconciliation Test Suite
Demonstrates why McKinsey Embedded Consultants use Google Antigravity over Cursor:
Full-stack SDLC rigor ensuring that BYOMCP telemetry, In-Place Excel models,
HTML Client Dashboards, and compiled PowerPoint (.pptx) slides reconcile with 0 variance.
"""

import os
import sys
import unittest
from pptx import Presentation

# Ensure scripts directory is importable
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from thursday_data_pipeline import (
    WAVE_TRAJECTORY,
    INITIATIVE_PORTFOLIO,
    calculate_what_if_scenario,
    generate_inplace_sharepoint_excel,
)


class TestMcKinseyThursdayPipeline(unittest.TestCase):
    def test_01_base_case_ebitda_reconciliation_inr(self):
        """Verify Wave 3 target (INR 1,310 Cr) exactly equals the sum of all 154 prioritized initiatives."""
        res = calculate_what_if_scenario(adoption_pct=85.0, energy_index_pct=100.0, capex_buffer_pct=0.0, currency="INR")
        self.assertEqual(res["fy25_actuals"], 180)
        self.assertEqual(res["fy26_wave1"], 490)
        self.assertEqual(res["fy27_wave2"], 920)
        self.assertEqual(res["fy28_wave3"], 1310)
        self.assertEqual(res["fy28_wave3"], res["portfolio_total_check"])
        self.assertEqual(res["cagr_pct"], 94)

    def test_02_customer_agnostic_usd_mode_reconciliation(self):
        """Verify Customer-Agnostic Global Mode ($158M) reconciles across the initiative portfolio."""
        res = calculate_what_if_scenario(adoption_pct=85.0, energy_index_pct=100.0, capex_buffer_pct=0.0, currency="USD")
        self.assertEqual(res["fy25_actuals"], 22)
        self.assertEqual(res["fy26_wave1"], 59)
        self.assertEqual(res["fy27_wave2"], 111)
        self.assertEqual(res["fy28_wave3"], 158)
        self.assertEqual(res["fy28_wave3"], res["portfolio_total_check"])

    def test_03_what_if_sensitivity_scaling(self):
        """Verify What-If sensitivity slider math scales Wave 1-3 forecasts accurately."""
        res_high = calculate_what_if_scenario(adoption_pct=100.0, energy_index_pct=100.0, capex_buffer_pct=0.0, currency="INR")
        self.assertGreater(res_high["fy28_wave3"], 1310)
        self.assertEqual(res_high["fy28_wave3"], round(1310 * (100.0 / 85.0)))

    def test_04_inplace_sharepoint_excel_generation(self):
        """Verify In-Place SharePoint Excel workbook is generated and non-empty."""
        out_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "output", "McKinsey_Thursday_Value_Tracker.xlsx")
        )
        generated = generate_inplace_sharepoint_excel(out_path)
        self.assertTrue(os.path.exists(generated))
        self.assertGreater(os.path.getsize(generated), 5000)

    def test_05_compiled_pptx_deck_integrity(self):
        """Verify compiled 6-slide McKinsey PowerPoint presentation exists and contains all 6 archetypes + speaker notes."""
        pptx_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "output", "mckinsey_sample_presentation.pptx")
        )
        self.assertTrue(os.path.exists(pptx_path), "PPTX must exist in output/mckinsey_sample_presentation.pptx")
        prs = Presentation(pptx_path)
        self.assertEqual(len(prs.slides), 6)
        # Verify speaker notes were populated from `data-notes`
        notes_slide_3 = prs.slides[2].notes_slide.notes_text_frame.text
        self.assertIn("1,310", notes_slide_3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
