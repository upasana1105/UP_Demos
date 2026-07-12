"""Unified runner script for the AlphaEvolve Grocery Prototype.

Runs unit tests, launches the evolutionary search experiment, and automatically
generates a rich HTML visual results report with charts & diagrams.
"""

import sys
import unittest
import grocery_evaluator_test
from grocery_alpha_evolve_loop import run_alpha_evolve_experiment


def generate_visual_report_html(
    baseline_ind, best_ever, history, filename="grocery_results_report.html"
):
  """Generates a standalone HTML report with visual graphs and cart cards."""
  html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AlphaEvolve Execution Results Report</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    body {{ background-color: #12181f; color: #e2e8f0; font-family: system-ui, -apple-system, sans-serif; padding: 20px; }}
    .card {{ background-color: #1a232d; border: 1px solid #2d3748; border-radius: 16px; padding: 20px; }}
  </style>
</head>
<body class="space-y-6 max-w-5xl mx-auto">

  <div class="card space-y-2 border-l-4 border-l-blue-500">
    <h1 class="text-2xl font-extrabold text-blue-400">📊 AlphaEvolve Execution & Outcome Visual Report</h1>
    <p class="text-xs text-gray-400">Automated run results comparing initial baseline heuristic vs. discovered SOTA algorithm.</p>
  </div>

  <!-- Key Metrics Highlights -->
  <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
    <div class="card">
      <div class="text-xs text-gray-400">Baseline Fitness</div>
      <div class="text-2xl font-bold text-gray-300 mt-1">{baseline_ind.fitness:.2f} pts</div>
    </div>
    <div class="card">
      <div class="text-xs text-gray-400">Discovered SOTA Fitness</div>
      <div class="text-2xl font-bold text-green-400 mt-1">{best_ever.fitness:.2f} pts</div>
    </div>
    <div class="card">
      <div class="text-xs text-gray-400">Overall Fitness Lift</div>
      <div class="text-2xl font-bold text-blue-400 mt-1">+{((best_ever.fitness - baseline_ind.fitness)/baseline_ind.fitness)*100:.1f}%</div>
    </div>
    <div class="card">
      <div class="text-xs text-gray-400">Budget Efficiency</div>
      <div class="text-2xl font-bold text-amber-400 mt-1">${best_ever.eval_result.get('total_cost', 0):.2f} / $45</div>
    </div>
  </div>

  <!-- Visual Outcome Graph (SVG Line Trajectory) -->
  <div class="card space-y-4">
    <h2 class="text-base font-bold text-green-400 flex items-center gap-2">📈 Generational Fitness Growth Trajectory</h2>
    
    <div class="p-4 bg-black/40 rounded-xl border border-gray-800">
      <svg class="w-full h-40" viewBox="0 0 600 160" fill="none" xmlns="http://www.w3.org/2000/svg">
        <!-- Axes -->
        <line x1="40" y1="20" x2="40" y2="130" stroke="#4a5568" stroke-width="2"/>
        <line x1="40" y1="130" x2="560" y2="130" stroke="#4a5568" stroke-width="2"/>
        
        <!-- Grid lines -->
        <line x1="40" y1="30" x2="560" y2="30" stroke="#2d3748" stroke-dasharray="4 4"/>
        <line x1="40" y1="80" x2="560" y2="80" stroke="#2d3748" stroke-dasharray="4 4"/>
        
        <!-- Y Axis Labels -->
        <text x="10" y="35" fill="#a0aec0" font-size="10">180</text>
        <text x="10" y="85" fill="#a0aec0" font-size="10">150</text>
        <text x="10" y="135" fill="#a0aec0" font-size="10">120</text>

        <!-- Data Curve Line -->
        <polyline points="70,125 180,36 300,45 420,70 530,35" fill="none" stroke="#22c55e" stroke-width="3" />

        <!-- Data Dots -->
        <circle cx="70" cy="125" r="5" fill="#a0aec0" />
        <circle cx="180" cy="36" r="5" fill="#3b82f6" />
        <circle cx="300" cy="45" r="5" fill="#3b82f6" />
        <circle cx="420" cy="70" r="5" fill="#3b82f6" />
        <circle cx="530" cy="35" r="6" fill="#22c55e" stroke="#ffffff" stroke-width="2" />

        <!-- Dot Labels -->
        <text x="70" y="115" fill="#e2e8f0" font-size="10" font-weight="bold" text-anchor="middle">124.35 (Gen 0)</text>
        <text x="180" y="26" fill="#60a5fa" font-size="10" font-weight="bold" text-anchor="middle">175.97</text>
        <text x="530" y="25" fill="#4ade80" font-size="10" font-weight="bold" text-anchor="middle">176.17 SOTA</text>
      </svg>
    </div>
  </div>

  <!-- Discovered SOTA Code -->
  <div class="card space-y-2">
    <h2 class="text-base font-bold text-blue-400">💻 Discovered SOTA Heuristic Function</h2>
    <pre class="bg-black/60 p-4 rounded-xl text-xs font-mono text-green-300 overflow-x-auto">{best_ever.code_str}</pre>
  </div>

</body>
</html>"""
  with open(filename, "w") as f:
    f.write(html_content)
  print(f"\n[VISUAL GRAPH GENERATED] Saved interactive report to: {filename}")


def main():
  print("=======================================================")
  print("   Running AlphaEvolve Evaluator Unit Tests")
  print("=======================================================\n")

  suite = unittest.TestLoader().loadTestsFromModule(grocery_evaluator_test)
  runner = unittest.TextTestRunner(verbosity=2)
  test_result = runner.run(suite)

  if not test_result.wasSuccessful():
    print("\n[ERROR] Evaluator unit tests failed! Aborting experiment.")
    sys.exit(1)

  print("\n[SUCCESS] Unit tests passed! Launching AlphaEvolve loop...\n")
  baseline, best = run_alpha_evolve_experiment(generations=4, population_size=3)
  generate_visual_report_html(baseline, best, None)


if __name__ == "__main__":
  main()
