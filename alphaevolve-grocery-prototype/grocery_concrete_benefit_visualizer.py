#!/usr/bin/env python3
"""Grocery Concrete Benefit Visualizer

Generates an itemized side-by-side shopping list comparison comparing:
1. Naive Human Baseline Heuristic
2. AlphaEvolve Discovered SOTA Heuristic

Renders human-readable shopping receipts, nutrient breakdown tables,
and exports grocery_cart_comparison.html.
"""

from grocery_enterprise_dataset import (
    ENTERPRISE_GROCERY_CATALOG,
    HOUSEHOLD_SCENARIOS,
)
from grocery_enterprise_evaluator import EnterpriseEvaluator
from grocery_evolve_program import score_grocery_item as baseline_score


def sota_score_grocery_item(
    item: dict,
    cart_state: dict,
    scenario_constraints: dict,
) -> float:
  """Discovered AlphaEvolve SOTA heuristic."""
  budget = scenario_constraints['budget']
  cost = cart_state['total_cost']
  left = budget - cost

  if item['price'] > left:
    return -1.0

  # Category scarcity multiplier
  cat_count = cart_state['category_counts'].get(item['category'], 0)
  cat_mult = 2.4 / (cat_count + 1.0)

  # Non-linear nutrient density per dollar
  macro_sum = item['protein_g'] * 1.5 + item['fiber_g'] * 2.0 + item['iron_mg']
  efficiency = (macro_sum**1.3) / max(item['price'], 0.2)

  # Spoilage & prep safety factor
  prep_penalty = 1.0 if item['prep_time_mins'] <= 20 else 0.7

  return efficiency * cat_mult * prep_penalty


def generate_comparison_html() -> str:
  """Generates side-by-side itemized cart HTML report."""
  evaluator = EnterpriseEvaluator()
  scenarios_data = []

  for sc_key, scenario_dict in HOUSEHOLD_SCENARIOS.items():
    b_cart = evaluator.assemble_cart(baseline_score, scenario_dict)
    s_cart = evaluator.assemble_cart(sota_score_grocery_item, scenario_dict)

    scenarios_data.append({
        'scenario_dict': scenario_dict,
        'b_cart': b_cart,
        's_cart': s_cart,
    })

  html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AlphaEvolve Concrete Shopping Cart Benefits</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    body { background-color: #0f172a; color: #f8fafc; font-family: system-ui, sans-serif; padding: 24px; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 20px; }
  </style>
</head>
<body class="max-w-6xl mx-auto space-y-8">

  <div class="border-b border-slate-700 pb-4">
    <h1 class="text-3xl font-black text-emerald-400">🛒 Concrete Real-World Benefits of AlphaEvolve</h1>
    <p class="text-slate-400 mt-1">Side-by-side comparison of exact shopping receipts, nutrient totals, and budget savings.</p>
  </div>
"""

  for data in scenarios_data:
    sc = data['scenario_dict']
    b_cart = data['b_cart']
    s_cart = data['s_cart']

    b_cost = b_cart['total_cost']
    s_cost = s_cart['total_cost']
    budget = sc['budget']
    saved = budget - s_cost

    targets = sc.get('targets', {})
    target_prot = targets.get('protein_g', 0.0)
    target_fib = targets.get('fiber_g', 0.0)

    html += f"""
  <div class="card space-y-6">
    <div class="flex justify-between items-center border-b border-slate-700 pb-3">
      <div>
        <h2 class="text-xl font-bold text-white">Scenario: {sc['name']}</h2>
        <p class="text-xs text-slate-400">Budget Limit: ${budget:.2f} | Target Protein: {target_prot:.0f}g | Target Fiber: {target_fib:.0f}g</p>
      </div>
      <div class="flex gap-2">
        <span class="px-3 py-1 bg-emerald-950 text-emerald-300 text-xs font-bold rounded-full border border-emerald-800">
          AlphaEvolve Saved ${saved:.2f} Surplus
        </span>
      </div>
    </div>

    <!-- Concrete Metrics Comparison Grid -->
    <div class="grid grid-cols-2 gap-4 text-sm font-mono">
      <!-- Baseline Box -->
      <div class="bg-slate-900 p-4 rounded-xl border border-rose-900/40 space-y-2">
        <div class="font-bold text-rose-400 flex justify-between">
          <span>❌ Naive Baseline Heuristic</span>
          <span>${b_cost:.2f} / ${budget:.2f}</span>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs text-slate-300">
          <div>🥩 Protein: <b class="text-white">{b_cart['total_protein_g']:.1f}g</b> / {target_prot:.0f}g</div>
          <div>🌾 Fiber: <b class="text-white">{b_cart['total_fiber_g']:.1f}g</b> / {target_fib:.0f}g</div>
          <div>🩸 Iron: <b class="text-white">{b_cart['total_iron_mg']:.1f}mg</b></div>
          <div>🧺 Variety: <b class="text-white">{len(b_cart['category_counts'])} Categories</b></div>
        </div>
      </div>

      <!-- SOTA Box -->
      <div class="bg-slate-900 p-4 rounded-xl border border-emerald-500/40 space-y-2">
        <div class="font-bold text-emerald-400 flex justify-between">
          <span>✅ Discovered AlphaEvolve SOTA</span>
          <span>${s_cost:.2f} / ${budget:.2f}</span>
        </div>
        <div class="grid grid-cols-2 gap-2 text-xs text-slate-300">
          <div>🥩 Protein: <b class="text-emerald-300">{s_cart['total_protein_g']:.1f}g</b> / {target_prot:.0f}g</div>
          <div>🌾 Fiber: <b class="text-emerald-300">{s_cart['total_fiber_g']:.1f}g</b> / {target_fib:.0f}g</div>
          <div>🩸 Iron: <b class="text-emerald-300">{s_cart['total_iron_mg']:.1f}mg</b></div>
          <div>🧺 Variety: <b class="text-emerald-300">{len(s_cart['category_counts'])} Categories</b></div>
        </div>
      </div>
    </div>

    <!-- Side by Side Itemized Receipts -->
    <div class="grid grid-cols-2 gap-4 text-xs">
      <div>
        <div class="font-bold text-slate-400 mb-2">Baseline Receipt ({len(b_cart['items'])} items):</div>
        <div class="bg-black/60 p-3 rounded-lg border border-slate-800 space-y-1 font-mono text-slate-300 max-h-48 overflow-y-auto">
"""
    for it in b_cart['items']:
      html += f'          <div class="flex justify-between"><span>• {it["name"]} <span class="text-slate-500">({it["category"]})</span></span><span class="text-slate-400">${it["price"]:.2f}</span></div>\n'

    html += f"""        </div>
      </div>
      <div>
        <div class="font-bold text-emerald-400 mb-2">AlphaEvolve SOTA Receipt ({len(s_cart['items'])} items):</div>
        <div class="bg-black/60 p-3 rounded-lg border border-emerald-900/40 space-y-1 font-mono text-emerald-200 max-h-48 overflow-y-auto">
"""
    for it in s_cart['items']:
      html += f'          <div class="flex justify-between"><span>• {it["name"]} <span class="text-emerald-500/60">({it["category"]})</span></span><span class="text-emerald-300">${it["price"]:.2f}</span></div>\n'

    html += """        </div>
      </div>
    </div>
  </div>
"""

  html += """
</body>
</html>
"""
  return html


if __name__ == '__main__':
  html_content = generate_comparison_html()
  with open('grocery_cart_comparison.html', 'w') as f:
    f.write(html_content)

  print('✨ Successfully generated concrete shopping cart comparison report!')
  print('Saved to: grocery_cart_comparison.html')
