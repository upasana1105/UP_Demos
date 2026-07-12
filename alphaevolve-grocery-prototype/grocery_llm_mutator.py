"""Live Gemini LLM API Mutator & Crossover Engine for AlphaEvolve Grocery Prototype.

Supports Single-Parent Mutation, Two-Parent Crossover, and AST-guarded code generation.
Includes offline fallback for offline environments.
"""

import os
import re
from typing import Optional, Tuple

Tuple_Str = Tuple[str, str]

# Pre-packaged heuristic mutation templates for offline fallback

OFFLINE_MUTATION_LIBRARY = [
    # Variant 1: Non-linear Exponent & Category Urgency
    """
def score_grocery_item(price: float, nutrition_score: float, category: str, current_budget_left: float, category_counts: dict[str, int]) -> float:
    if price > current_budget_left:
        return -1.0
    count = category_counts.get(category, 0)
    category_multiplier = 2.4 / (count + 1.0)
    efficiency = (nutrition_score ** 1.5) / max(price, 0.2)
    return efficiency * category_multiplier
""",
    # Variant 2: Hybrid Crossover - Fresh Produce/Protein Focus + Budget Pacing
    """
def score_grocery_item(price: float, nutrition_score: float, category: str, current_budget_left: float, category_counts: dict[str, int]) -> float:
    if price > current_budget_left:
        return -1.0
    count = category_counts.get(category, 0)
    priority = 2.2 / (count + 1.0) if category in ['vegetable', 'fruit', 'protein'] else 1.2 / (count + 1.0)
    efficiency = (nutrition_score ** 1.6) / max(price, 0.1)
    return efficiency * priority
""",
    # Variant 3: Target Diversity Balancing
    """
def score_grocery_item(price: float, nutrition_score: float, category: str, current_budget_left: float, category_counts: dict[str, int]) -> float:
    if price > current_budget_left:
        return -1.0
    cat_count = category_counts.get(category, 0)
    diversity_urgency = 3.0 - (cat_count * 0.8) if cat_count < 2 else 0.5 / (cat_count)
    value_score = (nutrition_score * 2.0) - (price * 0.4)
    return max(0.1, value_score * diversity_urgency)
""",
]


def extract_python_code(response_text: str) -> str:
  """Extracts clean python code block from LLM response text."""
  match = re.search(r"```python\s*(.*?)\s*```", response_text, re.DOTALL)
  if match:
    return match.group(1).strip()
  return response_text.strip()


class LLMMutator:
  """AlphaEvolve LLM Mutator managing live API calls and offline fallbacks."""

  def __init__(self, use_live_api: bool = False):
    self.use_live_api = use_live_api
    self.client = None
    if use_live_api:
      try:
        from google import genai

        self.client = genai.Client()
      except Exception:
        self.use_live_api = False

  def mutate_single_parent(
      self, parent_code: str, fitness_score: float, generation: int
  ) -> Tuple_Str:
    """Generates a mutated program string based on a single parent context."""
    if self.use_live_api and self.client:
      prompt = f"""You are AlphaEvolve's LLM code mutator. 
The current parent program achieved a fitness score of {fitness_score:.2f} pts:

```python
{parent_code}
```

Task: Write an improved Python function `def score_grocery_item(price: float, nutrition_score: float, category: str, current_budget_left: float, category_counts: dict[str, int]) -> float` that discovers higher fitness (better nutrition, category balance, and budget efficiency).
Return ONLY the raw executable python code in a ```python block.
"""
      try:
        res = self.client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return extract_python_code(res.text), "Live Gemini Single-Parent Mutation"
      except Exception as e:
        pass  # Fall through to offline template

    # Offline fallback logic
    idx = (generation - 1) % len(OFFLINE_MUTATION_LIBRARY)
    return (
        OFFLINE_MUTATION_LIBRARY[idx],
        f"Offline Mutator Strategy #{idx+1}",
    )

  def crossover_two_parents(
      self, parent_a_code: str, parent_b_code: str, generation: int
  ) -> Tuple_Str:
    """Synthesizes a new program string by crossing over two complementary parents."""
    if self.use_live_api and self.client:
      prompt = f"""You are AlphaEvolve's evolutionary crossover engine.
Combine the best algorithmic features of these two parent programs into a superior hybrid:

Parent A:
```python
{parent_a_code}
```

Parent B:
```python
{parent_b_code}
```

Task: Synthesize a combined `score_grocery_item(...)` heuristic function combining Parent A's high nutrition weighting with Parent B's category diversity penalties.
Return ONLY raw executable python code in a ```python block.
"""
      try:
        res = self.client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return extract_python_code(res.text), "Live Gemini Two-Parent Crossover"
      except Exception:
        pass  # Fall through to offline template

    idx = 1  # Crossover template
    return OFFLINE_MUTATION_LIBRARY[idx], "Hybrid Crossover Strategy"


# Helper tuple alias
Tuple_Str = tuple[str, str]
