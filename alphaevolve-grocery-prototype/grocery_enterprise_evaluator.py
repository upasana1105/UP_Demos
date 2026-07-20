"""Enterprise Evaluator for AlphaEvolve.

Implements Three-Tier Evaluation and 4D Pareto Vector Scoring:
  F1: Macro & Micro Nutrient Alignment [0-100]
  F2: Category Balance & Diversity [0-100]
  F3: Financial Efficiency [0-100]
  F4: Spoilage & Prep Time Efficiency [0-100]
"""

import math
import types
from typing import Any, Dict, List, Tuple

from grocery_enterprise_dataset import ENTERPRISE_GROCERY_CATALOG, HOUSEHOLD_SCENARIOS


def is_pareto_dominant(v1: Tuple[float, ...], v2: Tuple[float, ...]) -> bool:
  """Returns True if vector v1 Pareto-dominates v2."""
  if len(v1) != len(v2):
    return False
  at_least_one_strictly_better = False
  for a, b in zip(v1, v2):
    if a < b:
      return False
    if a > b:
      at_least_one_strictly_better = True
  return at_least_one_strictly_better


def extract_pareto_frontier(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  """Extracts non-dominated frontier from a list of candidate dictionaries.

  Each candidate dict must contain a 'fitness_vector' key (tuple of floats).
  """
  frontier = []
  for i, cand_i in enumerate(candidates):
    v_i = cand_i["fitness_vector"]
    dominated = False
    for j, cand_j in enumerate(candidates):
      if i != j:
        v_j = cand_j["fitness_vector"]
        if is_pareto_dominant(v_j, v_i):
          dominated = True
          break
    if not dominated:
      frontier.append(cand_i)
  return frontier


class EnterpriseEvaluator:
  """Three-Tier Evaluator with 4D Pareto Fitness Vector scoring."""

  def __init__(self, catalog: List[Any] = None):
    raw_catalog = catalog if catalog is not None else ENTERPRISE_GROCERY_CATALOG
    self.catalog: List[Dict[str, Any]] = [
        item.to_dict() if hasattr(item, "to_dict") else item for item in raw_catalog
    ]

  def filter_catalog_for_scenario(
      self, scenario: Dict[str, Any]
  ) -> List[Dict[str, Any]]:
    """Tier 2 Verification: Filter catalog according to strict dietary restrictions."""
    filtered = []
    for item in self.catalog:
      if scenario.get("is_gluten_free") and not item.get("is_gluten_free", False):
        continue
      if scenario.get("is_vegan") and not item.get("is_vegan", False):
        continue
      if item.get("shelf_life_days", 0) < scenario.get("min_shelf_life_days", 0):
        continue
      filtered.append(item)
    return filtered

  def assemble_cart(
      self,
      score_fn: Any,
      scenario: Dict[str, Any],
      max_items: int = 15,
  ) -> Dict[str, Any]:
    """Tier 3 Simulation: Greedy cart selection using candidate score_fn."""
    filtered_catalog = self.filter_catalog_for_scenario(scenario)
    if not filtered_catalog:
      filtered_catalog = self.catalog  # Fallback if over-constrained

    budget = scenario["budget"]
    cart_state = {
        "items": [],
        "total_cost": 0.0,
        "category_counts": {},
        "total_protein_g": 0.0,
        "total_carbs_g": 0.0,
        "total_fats_g": 0.0,
        "total_iron_mg": 0.0,
        "total_calcium_mg": 0.0,
        "total_fiber_g": 0.0,
        "total_vitamin_d_mcg": 0.0,
        "total_sodium_mg": 0.0,
        "total_prep_time_mins": 0,
        "min_shelf_life_days": 999,
    }

    remaining_items = list(filtered_catalog)

    for _ in range(max_items):
      best_item = None
      best_score = -float("inf")
      best_idx = -1

      for idx, item in enumerate(remaining_items):
        if cart_state["total_cost"] + item["price"] > budget:
          continue

        try:
          score = float(score_fn(item, cart_state, scenario))
        except Exception:
          score = -999.0

        if score > best_score and score > 0.0:
          best_score = score
          best_item = item
          best_idx = idx

      if best_item is None or best_idx < 0:
        break

      # Add item to cart
      cart_state["items"].append(best_item)
      cart_state["total_cost"] += best_item["price"]
      cat = best_item["category"]
      cart_state["category_counts"][cat] = cart_state["category_counts"].get(cat, 0) + 1
      cart_state["total_protein_g"] += best_item.get("protein_g", 0.0)
      cart_state["total_carbs_g"] += best_item.get("carbs_g", 0.0)
      cart_state["total_fats_g"] += best_item.get("fats_g", 0.0)
      cart_state["total_iron_mg"] += best_item.get("iron_mg", 0.0)
      cart_state["total_calcium_mg"] += best_item.get("calcium_mg", 0.0)
      cart_state["total_fiber_g"] += best_item.get("fiber_g", 0.0)
      cart_state["total_vitamin_d_mcg"] += best_item.get("vitamin_d_mcg", 0.0)
      cart_state["total_sodium_mg"] += best_item.get("sodium_mg", 0.0)
      cart_state["total_prep_time_mins"] += best_item.get("prep_time_mins", 0)
      cart_state["min_shelf_life_days"] = min(
          cart_state["min_shelf_life_days"], best_item.get("shelf_life_days", 999)
      )
      remaining_items.pop(best_idx)

    return cart_state

  def compute_fitness_vector(
      self, cart_state: Dict[str, Any], scenario: Dict[str, Any]
  ) -> Tuple[float, float, float, float]:
    """Computes 4D fitness vector (F1, F2, F3, F4)."""
    targets = scenario.get("targets", scenario)
    budget = scenario["budget"]

    # F1: Nutrient Alignment [0 - 100]
    p_ratio = min(1.0, cart_state["total_protein_g"] / max(targets.get("target_protein_g", targets.get("protein_g", 1.0)), 1.0))
    c_ratio = min(1.0, cart_state["total_carbs_g"] / max(targets.get("target_carbs_g", targets.get("carbs_g", 1.0)), 1.0))
    f_ratio = min(1.0, cart_state["total_fats_g"] / max(targets.get("target_fats_g", targets.get("fats_g", 1.0)), 1.0))
    fe_ratio = min(1.0, cart_state["total_iron_mg"] / max(targets.get("target_iron_mg", targets.get("iron_mg", 1.0)), 1.0))
    ca_ratio = min(1.0, cart_state["total_calcium_mg"] / max(targets.get("target_calcium_mg", targets.get("calcium_mg", 1.0)), 1.0))
    fib_ratio = min(1.0, cart_state["total_fiber_g"] / max(targets.get("target_fiber_g", targets.get("fiber_g", 1.0)), 1.0))
    vd_ratio = min(1.0, cart_state["total_vitamin_d_mcg"] / max(targets.get("target_vitamin_d_mcg", targets.get("vitamin_d_mcg", 1.0)), 1.0))

    f1 = ((p_ratio + c_ratio + f_ratio + fe_ratio + ca_ratio + fib_ratio + vd_ratio) / 7.0) * 100.0

    # F2: Category Balance & Diversity (Shannon Entropy) [0 - 100]
    counts = list(cart_state["category_counts"].values())
    total_items = len(cart_state["items"])
    if total_items > 0:
      entropy = 0.0
      for cnt in counts:
        p = cnt / total_items
        entropy -= p * math.log(p)
      max_entropy = math.log(12.0)  # 12 categories total
      f2 = min(100.0, (entropy / max_entropy) * 100.0)
    else:
      f2 = 0.0

    # F3: Financial Efficiency [0 - 100]
    cost = cart_state["total_cost"]
    if cost > budget or cost <= 0.0:
      f3 = 0.0
    else:
      f3 = (cost / budget) * 100.0

    # F4: Spoilage & Prep Overhead Efficiency [0 - 100]
    f4 = 100.0
    max_prep = scenario.get("max_prep_time_mins", 30)
    if max_prep and cart_state["total_prep_time_mins"] > max_prep:
      excess_prep = cart_state["total_prep_time_mins"] - max_prep
      f4 -= min(40.0, excess_prep * 2.0)

    max_sod = scenario.get("max_sodium_mg", 3000.0)
    if max_sod and cart_state["total_sodium_mg"] > max_sod:
      excess_sod = cart_state["total_sodium_mg"] - max_sod
      f4 -= min(40.0, (excess_sod / 100.0) * 5.0)

    min_shelf = scenario.get("min_shelf_life_days", 3)
    if min_shelf and cart_state["min_shelf_life_days"] < min_shelf:
      f4 -= 20.0

    f4 = max(0.0, min(100.0, f4))

    return (round(f1, 2), round(f2, 2), round(f3, 2), round(f4, 2))

  def evaluate_code_string(
      self, code_str: str, scenario: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Three-Tier Evaluation Pipeline."""
    # Tier 1: Syntax & Signature Validation
    try:
      mod = types.ModuleType("evolved_module")
      exec(code_str, mod.__dict__)
      score_fn = getattr(mod, "score_grocery_item", None)
      if not callable(score_fn):
        return {
            "valid": False,
            "error": "score_grocery_item function not found",
            "fitness_vector": (0.0, 0.0, 0.0, 0.0),
            "aggregate_score": 0.0,
        }
    except Exception as e:
      return {
          "valid": False,
          "error": f"Tier 1 Syntax Error: {e}",
          "fitness_vector": (0.0, 0.0, 0.0, 0.0),
          "aggregate_score": 0.0,
      }

    # Tier 2 & Tier 3: Cart Assembly & 4D Fitness Vector
    try:
      cart_state = self.assemble_cart(score_fn, scenario)
      vector = self.compute_fitness_vector(cart_state, scenario)
      agg = round(sum(vector) / 4.0, 2)
      return {
          "valid": True,
          "error": None,
          "cart_state": cart_state,
          "fitness_vector": vector,
          "aggregate_score": agg,
      }
    except Exception as e:
      return {
          "valid": False,
          "error": f"Tier 3 Evaluation Error: {e}",
          "fitness_vector": (0.0, 0.0, 0.0, 0.0),
          "aggregate_score": 0.0,
      }


def evaluate_code_string(
    code_str: str,
    catalog: List[Any] = None,
    scenario: Any = None,
) -> Dict[str, Any]:
  """Convenience top-level function for evaluating code string."""
  if catalog is None:
    catalog = ENTERPRISE_GROCERY_CATALOG
  if scenario is None:
    scenario = HOUSEHOLD_SCENARIOS["Single Student"]

  if hasattr(scenario, "to_dict"):
    sc_dict = scenario.to_dict()
  elif isinstance(scenario, dict):
    sc_dict = scenario
  else:
    sc_dict = dict(scenario)

  evaluator = EnterpriseEvaluator(catalog=catalog)
  res = evaluator.evaluate_code_string(code_str, sc_dict)
  res["aggregate_fitness"] = res.get("aggregate_score", 0.0)
  if "cart_state" in res and res["cart_state"]:
    res["total_cost"] = res["cart_state"].get("total_cost", 0.0)
    res["item_count"] = len(res["cart_state"].get("items", []))
  else:
    res["total_cost"] = 0.0
    res["item_count"] = 0
  return res
