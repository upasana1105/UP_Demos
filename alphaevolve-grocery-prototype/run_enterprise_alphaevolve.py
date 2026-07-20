"""Unified Orchestrator & Dashboard Generator for Enterprise AlphaEvolve.

Runs multi-generation evolutionary search across all 3 household scenarios,
maintains MAP-Elites behavioral archives and Pareto frontiers, and renders
the interactive `grocery_sota_dashboard.html` visual analytics dashboard.
"""

import json
import os
import sys
import unittest

from grocery_enterprise_ast_validator import validate_ast
from grocery_enterprise_dataset import HOUSEHOLD_SCENARIOS
from grocery_enterprise_evaluator import EnterpriseEvaluator
from grocery_enterprise_llm_mutator import OFFLINE_STRATEGY_BLOCKS, extract_evolve_block, mutate_program
import grocery_enterprise_test
from grocery_map_elites import MapElitesArchive

NUM_GENERATIONS = 15
MUTATIONS_PER_GEN = 6


def run_unit_test_suite() -> bool:
  """Run unit test suite prior to launching evolutionary search."""
  print("🧪 Executing Enterprise AlphaEvolve Unit Test Suite...")
  suite = unittest.TestLoader().loadTestsFromModule(grocery_enterprise_test)
  runner = unittest.TextTestRunner(verbosity=1)
  result = runner.run(suite)
  return result.wasSuccessful()


def load_baseline_code() -> str:
  with open("grocery_evolve_program.py", "r", encoding="utf-8") as f:
    return f.read()


def run_evolution_for_scenario(
    scenario_id: str, scenario: dict, baseline_code: str
) -> dict:
  """Runs multi-generation MAP-Elites search for a single scenario."""
  evaluator = EnterpriseEvaluator()
  archive = MapElitesArchive(grid_size=5)

  # Evaluate baseline
  base_res = evaluator.evaluate_code_string(baseline_code, scenario)
  if base_res["valid"]:
    archive.try_insert(
        baseline_code,
        base_res["fitness_vector"],
        base_res["cart_state"],
        {"strategy": "baseline", "gen": 0},
    )

  trajectory = []
  strategies = list(OFFLINE_STRATEGY_BLOCKS.keys())

  print(f"\n🚀 Running AlphaEvolve for Scenario: {scenario['name']}")

  for gen in range(1, NUM_GENERATIONS + 1):
    parents = archive.sample_parents(num_parents=2)
    if not parents:
      parents = [{
          "code": baseline_code,
          "fitness_vector": base_res["fitness_vector"],
      }]

    for m in range(MUTATIONS_PER_GEN):
      parent = parents[m % len(parents)]
      strategy = strategies[(gen + m) % len(strategies)]

      mutated_code = mutate_program(
          parent["code"], parent_programs=parents, strategy=strategy
      )

      # AST Validation
      ast_res = validate_ast(mutated_code)
      if not ast_res["valid"]:
        continue

      # Tier 3 Evaluation
      eval_res = evaluator.evaluate_code_string(mutated_code, scenario)
      if not eval_res["valid"]:
        continue

      archive.try_insert(
          mutated_code,
          eval_res["fitness_vector"],
          eval_res["cart_state"],
          {"strategy": strategy, "gen": gen},
      )

    pareto_front = archive.get_pareto_front()
    best_elite = (
        pareto_front[0]
        if pareto_front
        else {
            "fitness_vector": (0, 0, 0, 0),
            "aggregate_score": 0,
            "cart_state": {},
        }
    )

    trajectory.append({
        "generation": gen,
        "coverage": archive.get_coverage(),
        "best_f1_nutrition": best_elite["fitness_vector"][0],
        "best_f2_diversity": best_elite["fitness_vector"][1],
        "best_f3_cost_eff": best_elite["fitness_vector"][2],
        "best_f4_spoilage": best_elite["fitness_vector"][3],
        "best_agg_score": best_elite["aggregate_score"],
    })

    print(
        f"  Gen {gen:2d}/{NUM_GENERATIONS} | Coverage: {archive.get_coverage():5.1f}%"
        f" | Best Agg Score: {best_elite['aggregate_score']:5.2f} | F1:"
        f" {best_elite['fitness_vector'][0]:.1f} F3:"
        f" {best_elite['fitness_vector'][2]:.1f}"
    )

  return {
      "scenario_id": scenario_id,
      "scenario_name": scenario["name"],
      "archive": archive,
      "trajectory": trajectory,
      "best_elite": archive.get_pareto_front()[0] if archive.get_pareto_front() else None,
      "baseline_result": base_res,
  }


def generate_html_dashboard(results: dict, baseline_code: str):
  """Generates single-page responsive HTML SOTA dashboard artifact."""
  output_html_path = "grocery_sota_dashboard.html"

  # Build aggregated Pareto points & grid data for JS
  pareto_points = []
  all_grid_data = {}

  for sc_id, res in results.items():
    archive = res["archive"]
    front = archive.get_pareto_front()
    for p in front:
      items_summary = [
          f"{i['name']} (${i['price']})" for i in p["cart_state"].get("items", [])
      ]
      pareto_points.append({
          "scenario": res["scenario_name"],
          "f1_nutrition": p["fitness_vector"][0],
          "f2_diversity": p["fitness_vector"][1],
          "f3_cost_eff": p["fitness_vector"][2],
          "f4_spoilage": p["fitness_vector"][3],
          "agg_score": p["aggregate_score"],
          "strategy": p["metadata"].get("strategy", "evolved"),
          "items_count": len(items_summary),
          "items_list": items_summary[:5],
      })
    all_grid_data[sc_id] = archive.to_dict()

  # Find global best elite
  best_overall = None
  best_score = -1.0
  best_sc_name = ""
  for sc_id, res in results.items():
    if res["best_elite"] and res["best_elite"]["aggregate_score"] > best_score:
      best_score = res["best_elite"]["aggregate_score"]
      best_overall = res["best_elite"]
      best_sc_name = res["scenario_name"]

  baseline_block = extract_evolve_block(baseline_code)
  sota_block = (
      extract_evolve_block(best_overall["code"])
      if best_overall
      else "return 0.0"
  )

  html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AlphaEvolve Grocery SOTA Analytics Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Fira+Code:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-gradient: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #030712 100%);
      --card-bg: rgba(17, 24, 39, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --accent-blue: #38bdf8;
      --accent-purple: #a855f7;
      --accent-green: #34d399;
      --accent-gold: #fbbf24;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', sans-serif;
      background: var(--bg-gradient);
      color: var(--text-main);
      min-height: 100vh;
      padding: 24px;
      line-height: 1.5;
    }}
    .dashboard-container {{
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}
    header {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 24px;
      backdrop-filter: blur(12px);
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .header-title h1 {{
      font-size: 26px;
      font-weight: 800;
      background: linear-gradient(90deg, #38bdf8, #a855f7, #34d399);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .header-title p {{ font-size: 14px; color: var(--text-muted); margin-top: 4px; }}
    .badge {{
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: var(--accent-blue);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 20px;
      backdrop-filter: blur(8px);
    }}
    .kpi-card .label {{ font-size: 13px; color: var(--text-muted); font-weight: 600; }}
    .kpi-card .val {{ font-size: 32px; font-weight: 800; margin-top: 6px; color: #fff; }}
    .kpi-card .sub {{ font-size: 12px; color: var(--accent-green); margin-top: 4px; }}

    .grid-2col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }}
    @media (max-width: 1024px) {{ .grid-2col {{ grid-template-columns: 1fr; }} }}

    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 24px;
      backdrop-filter: blur(12px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }}
    .card-header h2 {{ font-size: 18px; font-weight: 700; color: #fff; }}

    /* MAP-Elites Heatmap Matrix */
    .map-grid {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 8px;
      aspect-ratio: 1;
      max-width: 480px;
      margin: 0 auto;
    }}
    .grid-cell {{
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      font-weight: 700;
      color: #fff;
      transition: all 0.2s ease;
      cursor: pointer;
      position: relative;
      border: 1px solid rgba(255,255,255,0.05);
    }}
    .grid-cell:hover {{ transform: scale(1.05); z-index: 10; border-color: var(--accent-blue); }}
    .grid-cell.empty {{ background: rgba(255,255,255,0.03); color: var(--text-muted); }}

    /* Code Diff Comparison */
    .code-diff-container {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }}
    @media (max-width: 768px) {{ .code-diff-container {{ grid-template-columns: 1fr; }} }}
    .code-box {{
      background: #0d1117;
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 10px;
      padding: 16px;
      font-family: 'Fira Code', monospace;
      font-size: 12px;
      color: #e6edf3;
      white-space: pre-wrap;
      overflow-x: auto;
      max-height: 320px;
    }}
    .code-box.sota {{ border-color: rgba(52, 211, 153, 0.4); background: #061a14; }}
    .code-title {{ font-size: 13px; font-weight: 700; margin-bottom: 8px; color: var(--accent-blue); }}
    .code-box.sota .code-title {{ color: var(--accent-green); }}
  </style>
</head>
<body>
  <div class="dashboard-container">
    <header>
      <div class="header-title">
        <h1>🧬 AlphaEvolve SOTA Analytics Dashboard</h1>
        <p>Enterprise Multi-Objective Evolutionary Algorithm & MAP-Elites Behavioral Archive Analysis</p>
      </div>
      <div class="badge">Live Production SOTA</div>
    </header>

    <!-- KPI Summary Row -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="label">SOTA Aggregate Score</div>
        <div class="val" style="color: var(--accent-green);">{best_score:.1f} / 100</div>
        <div class="sub">Top scenario: {best_sc_name}</div>
      </div>
      <div class="kpi-card">
        <div class="label">2D MAP-Elites Archive Coverage</div>
        <div class="val" style="color: var(--accent-blue);">{results['single_student']['archive'].get_coverage():.0f}%</div>
        <div class="sub">{results['single_student']['archive'].to_dict()['total_elites']} / 25 Niches Explored</div>
      </div>
      <div class="kpi-card">
        <div class="label">Nutrient Alignment (F1)</div>
        <div class="val">{best_overall['fitness_vector'][0] if best_overall else 0:.1f}</div>
        <div class="sub">Macro & Micro Target Match</div>
      </div>
      <div class="kpi-card">
        <div class="label">Financial Efficiency (F3)</div>
        <div class="val" style="color: var(--accent-gold);">{best_overall['fitness_vector'][2] if best_overall else 0:.1f}</div>
        <div class="sub">Budget Utilization Rate</div>
      </div>
    </div>

    <!-- Charts Row 1: Pareto Frontier & MAP-Elites Heatmap -->
    <div class="grid-2col">
      <div class="card">
        <div class="card-header">
          <h2>🎯 2D Non-Dominated Pareto Frontier</h2>
          <span style="font-size: 12px; color: var(--text-muted);">Nutrition Alignment (F1) vs Cost Efficiency (F3)</span>
        </div>
        <canvas id="paretoChart" height="280"></canvas>
      </div>

      <div class="card">
        <div class="card-header">
          <h2>🗺️ 5x5 MAP-Elites Behavioral Archive Grid</h2>
          <span style="font-size: 12px; color: var(--text-muted);">Price Pacing vs Diversity & Nutrition Ratio</span>
        </div>
        <div class="map-grid" id="mapGrid"></div>
      </div>
    </div>

    <!-- Charts Row 2: Scenario Trajectories & Code Diff -->
    <div class="grid-2col">
      <div class="card">
        <div class="card-header">
          <h2>📈 Multi-Scenario Evolutionary Convergence</h2>
          <span style="font-size: 12px; color: var(--text-muted);">Fitness Trajectory Across {NUM_GENERATIONS} Generations</span>
        </div>
        <canvas id="trajectoryChart" height="280"></canvas>
      </div>

      <div class="card">
        <div class="card-header">
          <h2>💡 Seed Baseline vs Evolved SOTA Program</h2>
          <span style="font-size: 12px; color: var(--accent-green);">Inside # EVOLVE-BLOCK</span>
        </div>
        <div class="code-diff-container">
          <div>
            <div class="code-title">Original Seed Code (Baseline)</div>
            <div class="code-box">{baseline_block.strip()}</div>
          </div>
          <div>
            <div class="code-title">AlphaEvolve Discovered SOTA</div>
            <div class="code-box sota">{sota_block.strip()}</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    // Data passed from Python AlphaEvolve Orchestrator
    const paretoPoints = {json.dumps(pareto_points)};
    const gridData = {json.dumps(all_grid_data['single_student'])};
    const trajectoryData = {json.dumps(results['single_student']['trajectory'])};

    // Render Pareto Scatter Chart
    const ctxPareto = document.getElementById('paretoChart').getContext('2d');
    new Chart(ctxPareto, {{
      type: 'scatter',
      data: {{
        datasets: [{{
          label: 'Non-Dominated SOTA Candidates',
          data: paretoPoints.map(p => ({{ x: p.f3_cost_eff, y: p.f1_nutrition, info: p }})),
          backgroundColor: '#38bdf8',
          borderColor: '#34d399',
          borderWidth: 2,
          pointRadius: 7,
          pointHoverRadius: 10
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{
          tooltip: {{
            callbacks: {{
              label: (ctx) => `Score: ${{ctx.raw.info.agg_score}} | Scenario: ${{ctx.raw.info.scenario}}`
            }}
          }}
        }},
        scales: {{
          x: {{ title: {{ display: true, text: 'Financial Efficiency F3 [0-100]', color: '#9ca3af' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
          y: {{ title: {{ display: true, text: 'Nutrient Alignment F1 [0-100]', color: '#9ca3af' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
        }}
      }}
    }});

    // Render MAP-Elites 5x5 Heatmap Matrix
    const mapGridContainer = document.getElementById('mapGrid');
    for (let r = 4; r >= 0; r--) {{
      for (let c = 0; c < 5; c++) {{
        const key = `${{r}}_${{c}}`;
        const cell = gridData.cells[key];
        const div = document.createElement('div');
        div.className = 'grid-cell ' + (cell ? '' : 'empty');

        if (cell) {{
          const score = cell.aggregate_score;
          const hue = (score / 100) * 120; // 0 (red) to 120 (green)
          div.style.background = `hsla(${{hue}}, 70%, 40%, 0.65)`;
          div.innerHTML = `<span>${{score.toFixed(0)}}</span><span style="font-size:9px;opacity:0.8;">Niche [${{r}},${{c}}]</span>`;
          div.title = `Niche [${{r}},${{c}}] | Agg Score: ${{score}} | Cost: $${{cell.total_cost.toFixed(2)}}`;
        }} else {{
          div.innerHTML = `<span style="font-size:9px;color:#4b5563;">[${{r}},${{c}}]</span>`;
        }}
        mapGridContainer.appendChild(div);
      }}
    }}

    // Render Evolutionary Convergence Trajectory Line Chart
    const ctxTraj = document.getElementById('trajectoryChart').getContext('2d');
    new Chart(ctxTraj, {{
      type: 'line',
      data: {{
        labels: trajectoryData.map(t => 'Gen ' + t.generation),
        datasets: [
          {{ label: 'SOTA Agg Score', data: trajectoryData.map(t => t.best_agg_score), borderColor: '#34d399', backgroundColor: 'rgba(52, 211, 153, 0.1)', fill: true, tension: 0.3 }},
          {{ label: 'Nutrient Alignment (F1)', data: trajectoryData.map(t => t.best_f1_nutrition), borderColor: '#38bdf8', borderDash: [4, 4], tension: 0.3 }},
          {{ label: 'Cost Efficiency (F3)', data: trajectoryData.map(t => t.best_f3_cost_eff), borderColor: '#fbbf24', borderDash: [2, 2], tension: 0.3 }}
        ]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ labels: {{ color: '#f3f4f6' }} }} }},
        scales: {{
          x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#9ca3af' }} }},
          y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#9ca3af' }}, min: 0, max: 100 }}
        }}
      }}
    }});
  </script>
</body>
</html>
"""

  with open(output_html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

  print(f"\n✨ SOTA Analytics Dashboard rendered at: {os.path.abspath(output_html_path)}")


def main():
  if not run_unit_test_suite():
    print("❌ Unit test suite failed. Aborting evolutionary search.")
    sys.exit(1)

  baseline_code = load_baseline_code()
  all_results = {}

  for sc_id, sc in HOUSEHOLD_SCENARIOS.items():
    res = run_evolution_for_scenario(sc_id, sc, baseline_code)
    all_results[sc_id] = res

  generate_html_dashboard(all_results, baseline_code)
  print("\n🎉 Enterprise AlphaEvolve Execution Completed Successfully!")


if __name__ == "__main__":
  main()
