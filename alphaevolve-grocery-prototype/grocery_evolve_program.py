"""Baseline Evolving Program for AlphaEvolve.

Contains official EVOLVE-BLOCK tags for LLM mutation.
"""

def score_grocery_item(
    item: dict,
    cart_state: dict,
    scenario_constraints: dict,
) -> float:
  """Heuristic scoring function evolved by AlphaEvolve."""
  # EVOLVE-BLOCK START
  remaining_budget = scenario_constraints['budget'] - cart_state.get('total_cost', 0.0)
  if item['price'] > remaining_budget:
    return -1.0

  cat_count = cart_state.get('category_counts', {}).get(item['category'], 0)
  protein_eff = item.get('protein_g', 0.0) / max(item['price'], 0.1)
  category_penalty = 1.0 / (cat_count + 1)
  return protein_eff * category_penalty
  # EVOLVE-BLOCK END
