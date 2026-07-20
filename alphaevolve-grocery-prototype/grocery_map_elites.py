"""MAP-Elites Behavioral Archive for Enterprise AlphaEvolve.

Maintains a 5x5 grid (25 behavioral niches) across two axes:
  Axis 1: Price Pacing Index (non-premium item ratio)
  Axis 2: Nutrient Density vs Diversity Ratio (Category entropy & protein density)
"""

import math
import random
from typing import Any, Dict, List, Optional, Tuple

from grocery_enterprise_evaluator import is_pareto_dominant


class MapElitesArchive:
  """5x5 MAP-Elites Behavioral Archive Grid (25 niches)."""

  def __init__(self, grid_size: int = 5):
    self.grid_size = grid_size
    # Grid dictionary keyed by (row, col) tuple (0..4, 0..4)
    self.grid: Dict[Tuple[int, int], Dict[str, Any]] = {}

  def compute_behavioral_descriptor(
      self, cart_state: Dict[str, Any]
  ) -> Tuple[float, float]:
    """Computes (Axis 1: Price Pacing Index, Axis 2: Diversity & Nutrition Density)."""
    items = cart_state.get("items", [])
    total_items = len(items)
    if total_items == 0:
      return (0.5, 0.5)

    # Axis 1: Price Pacing Index (Ratio of non-premium / budget items in cart)
    non_premium_cnt = sum(1 for item in items if not item.get("is_premium", False))
    axis1 = non_premium_cnt / total_items

    # Axis 2: Diversity & Nutrition Ratio
    cat_counts = cart_state.get("category_counts", {})
    entropy = 0.0
    for cnt in cat_counts.values():
      p = cnt / total_items
      entropy -= p * math.log(p)
    norm_entropy = min(1.0, entropy / math.log(12.0))

    total_cost = max(0.1, cart_state.get("total_cost", 0.0))
    total_protein = cart_state.get("total_protein_g", 0.0)
    protein_per_dollar = min(1.0, (total_protein / total_cost) / 10.0)

    axis2 = 0.5 * norm_entropy + 0.5 * protein_per_dollar

    axis1 = max(0.0, min(1.0, axis1))
    axis2 = max(0.0, min(1.0, axis2))
    return (round(axis1, 3), round(axis2, 3))

  def _get_cell_coords(self, descriptor: Tuple[float, float]) -> Tuple[int, int]:
    """Maps continuous descriptor (axis1, axis2) to discrete (row, col) grid coordinates."""
    axis1, axis2 = descriptor
    col = min(self.grid_size - 1, max(0, int(axis1 * self.grid_size)))
    row = min(self.grid_size - 1, max(0, int(axis2 * self.grid_size)))
    return (row, col)

  def try_insert(
      self,
      program_code: str,
      fitness_vector: Tuple[float, float, float, float],
      cart_state: Dict[str, Any],
      metadata: Optional[Dict[str, Any]] = None,
  ) -> bool:
    """Attempts to insert candidate into its behavioral niche."""
    descriptor = self.compute_behavioral_descriptor(cart_state)
    coords = self._get_cell_coords(descriptor)
    agg_score = round(sum(fitness_vector) / len(fitness_vector), 2)

    candidate_entry = {
        "code": program_code,
        "fitness_vector": fitness_vector,
        "aggregate_score": agg_score,
        "descriptor": descriptor,
        "coords": coords,
        "cart_state": cart_state,
        "metadata": metadata or {},
    }

    if coords not in self.grid:
      self.grid[coords] = candidate_entry
      return True

    existing = self.grid[coords]
    # Replace if candidate Pareto dominates or has higher aggregate score
    if is_pareto_dominant(fitness_vector, existing["fitness_vector"]):
      self.grid[coords] = candidate_entry
      return True
    elif not is_pareto_dominant(existing["fitness_vector"], fitness_vector) and agg_score > existing["aggregate_score"]:
      self.grid[coords] = candidate_entry
      return True

    return False

  def sample_parents(self, num_parents: int = 2) -> List[Dict[str, Any]]:
    """Samples num_parents randomly from non-empty archive niches."""
    elites = list(self.grid.values())
    if not elites:
      return []
    if len(elites) < num_parents:
      return random.choices(elites, k=num_parents)
    return random.sample(elites, k=num_parents)

  def get_coverage(self) -> float:
    """Returns archive coverage percentage (0.0 to 100.0)."""
    total_niches = self.grid_size * self.grid_size
    occupied = len(self.grid)
    return round((occupied / total_niches) * 100.0, 2)

  def get_pareto_front(self) -> List[Dict[str, Any]]:
    """Returns non-dominated Pareto frontier programs across the entire archive."""
    elites = list(self.grid.values())
    if not elites:
      return []

    frontier = []
    for i, e_i in enumerate(elites):
      v_i = e_i["fitness_vector"]
      dominated = False
      for j, e_j in enumerate(elites):
        if i != j:
          v_j = e_j["fitness_vector"]
          if is_pareto_dominant(v_j, v_i):
            dominated = True
            break
      if not dominated:
        frontier.append(e_i)

    return sorted(frontier, key=lambda x: x["aggregate_score"], reverse=True)

  def to_dict(self) -> Dict[str, Any]:
    """Returns serializable dictionary representation of archive grid for visualization."""
    serialized_grid = {}
    for (r, c), cell in self.grid.items():
      serialized_grid[f"{r}_{c}"] = {
          "row": r,
          "col": c,
          "descriptor": cell["descriptor"],
          "fitness_vector": cell["fitness_vector"],
          "aggregate_score": cell["aggregate_score"],
          "code": cell["code"],
          "item_count": len(cell["cart_state"].get("items", [])),
          "total_cost": cell["cart_state"].get("total_cost", 0.0),
      }

    return {
        "grid_size": self.grid_size,
        "coverage": self.get_coverage(),
        "total_elites": len(self.grid),
        "cells": serialized_grid,
    }
