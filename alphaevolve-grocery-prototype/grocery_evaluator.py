"""Evaluator harness and multi-factor fitness calculator for AlphaEvolve grocery prototype."""

import types
from typing import Callable
from grocery_dataset import ALL_CATEGORIES, DEFAULT_SCENARIO, GROCERY_CATALOG, GroceryItem, ShoppingScenario

ScoringFuncType = Callable[[float, float, str, float, dict[str, int]], float]


def assemble_cart(
    scoring_func: ScoringFuncType,
    catalog: list[GroceryItem],
    budget: float,
) -> list[GroceryItem]:
  """Simulates assembling a shopping cart using the provided item scoring heuristic.

  Applies greedy selection: repeatedly evaluates all unselected affordable items
  with `scoring_func`, adding the highest-scoring item until no item has a
  positive score or budget is exhausted.
  """
  cart: list[GroceryItem] = []
  current_budget_left = budget
  category_counts: dict[str, int] = {cat: 0 for cat in ALL_CATEGORIES}
  remaining_catalog = list(catalog)

  while remaining_catalog and current_budget_left > 0:
    best_item = None
    best_score = -float("inf")
    best_idx = -1

    for idx, item in enumerate(remaining_catalog):
      if item.price > current_budget_left:
        continue

      try:
        score = scoring_func(
            item.price,
            item.nutrition_score,
            item.category,
            current_budget_left,
            category_counts,
        )
      except Exception:
        score = -1.0

      if score > 0 and score > best_score:
        best_score = score
        best_item = item
        best_idx = idx

    # If no item receives a positive heuristic score, stop shopping
    if best_item is None or best_score <= 0:
      break

    # Add best item to cart
    cart.append(best_item)
    current_budget_left -= best_item.price
    category_counts[best_item.category] += 1
    remaining_catalog.pop(best_idx)

  return cart


def calculate_fitness(
    cart: list[GroceryItem],
    scenario: ShoppingScenario = DEFAULT_SCENARIO,
) -> dict[str, float]:
  """Calculates the multi-factor fitness score for a given grocery cart.

  Fitness = Nutrition Points + Category Diversity Bonus - Unspent Budget Penalty
  Disqualified (Score = 0.0) if total cost > budget.
  """
  total_cost = sum(item.price for item in cart)
  if total_cost > scenario.budget:
    # Disqualified due to budget overrun
    return {
        "fitness": 0.0,
        "total_cost": total_cost,
        "total_nutrition": 0.0,
        "diversity_bonus": 0.0,
        "unspent_penalty": 100.0,
        "items_count": len(cart),
    }

  # 1. Total Nutrition
  total_nutrition = sum(item.nutrition_score for item in cart)

  # 2. Category Diversity Bonus (encourages representation across all categories)
  cats_present = set(item.category for item in cart)
  diversity_bonus = len(cats_present) * 5.0

  # Additional bonus if minimum target per category is met
  cat_counts = {
      cat: sum(1 for item in cart if item.category == cat)
      for cat in ALL_CATEGORIES
  }
  well_balanced_cats = sum(
      1
      for cat, count in cat_counts.items()
      if count >= scenario.target_diversity_min_per_category
  )
  diversity_bonus += well_balanced_cats * 4.0

  # 3. Unspent Budget Efficiency Penalty (penalizes leaving excess unspent money)
  unspent_budget = scenario.budget - total_cost
  unspent_penalty = min(unspent_budget * 0.5, 30.0)

  fitness = max(0.0, total_nutrition + diversity_bonus - unspent_penalty)

  return {
      "fitness": round(fitness, 2),
      "total_cost": round(total_cost, 2),
      "total_nutrition": round(total_nutrition, 2),
      "diversity_bonus": round(diversity_bonus, 2),
      "unspent_penalty": round(unspent_penalty, 2),
      "items_count": len(cart),
  }


def evaluate_code_string(
    code_str: str,
    catalog: list[GroceryItem] = GROCERY_CATALOG,
    scenario: ShoppingScenario = DEFAULT_SCENARIO,
) -> dict[str, float]:
  """Safely compiles and evaluates candidate code string for fitness."""
  try:
    module = types.ModuleType("candidate_module")
    exec(code_str, module.__dict__)
    if not hasattr(module, "score_grocery_item"):
      return {"fitness": 0.0, "error": "Missing score_grocery_item function"}

    func = getattr(module, "score_grocery_item")
    cart = assemble_cart(func, catalog, scenario.budget)
    res = calculate_fitness(cart, scenario)
    res["error"] = None
    return res
  except Exception as e:
    return {
        "fitness": 0.0,
        "total_cost": 0.0,
        "total_nutrition": 0.0,
        "diversity_bonus": 0.0,
        "unspent_penalty": 0.0,
        "items_count": 0,
        "error": str(e),
    }
