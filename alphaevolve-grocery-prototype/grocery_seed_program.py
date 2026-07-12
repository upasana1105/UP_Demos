"""Seed baseline program for AlphaEvolve grocery heuristic optimization."""


def score_grocery_item(
    price: float,
    nutrition_score: float,
    category: str,
    current_budget_left: float,
    category_counts: dict[str, int],
) -> float:
  """Calculates heuristic priority score for adding an item to the grocery cart.

  AlphaEvolve mutates this heuristic function to maximize total cart fitness
  (nutrition + category diversity - budget inefficiency).

  Args:
    price: Cost of the item in dollars.
    nutrition_score: Health & nutrient rating (1.0 to 10.0).
    category: Category label ('vegetable', 'fruit', 'protein', 'grain',
      'dairy', 'snack').
    current_budget_left: Unspent budget remaining in dollars.
    category_counts: Dictionary mapping category name -> count of items already
      selected.

  Returns:
    Float priority score. Returns negative value if item cannot be afforded.
  """
  if price > current_budget_left:
    return -1.0

  # Naive baseline heuristic: pick items purely by raw nutrition score
  return nutrition_score

