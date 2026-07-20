"""Enterprise LLM Mutator for AlphaEvolve.

Extracts code strictly inside EVOLVE-BLOCK tags for mutation, keeping surrounding template immutable.
Provides live Gemini 2.5 API prompt composition + multi-objective offline mutation strategies
with dynamic parameter variations to explore the MAP-Elites behavioral archive.
"""

import os
import random
import re
from typing import Dict, List, Optional

START_TAG = "# EVOLVE-BLOCK START"
END_TAG = "# EVOLVE-BLOCK END"


def extract_evolve_block(full_code: str) -> str:
  """Extracts code block strictly between # EVOLVE-BLOCK START and # EVOLVE-BLOCK END."""
  pattern = rf"{re.escape(START_TAG)}(.*?){re.escape(END_TAG)}"
  match = re.search(pattern, full_code, re.DOTALL)
  if not match:
    raise ValueError("Code does not contain valid EVOLVE-BLOCK annotations.")
  return match.group(1).strip()


def replace_evolve_block(full_code: str, new_block_code: str) -> str:
  """Replaces code block strictly inside EVOLVE-BLOCK tags with new_block_code."""
  pattern = rf"({re.escape(START_TAG)}).*?({re.escape(END_TAG)})"
  replacement = rf"\1\n  {new_block_code.strip()}\n  \2"
  return re.sub(pattern, replacement, full_code, flags=re.DOTALL)


OFFLINE_STRATEGY_BLOCKS = {
    "macro_focused": "Macro-focused Strategy",
    "variety_focused": "Variety-focused Strategy",
    "budget_pacing": "Budget-pacing Strategy",
    "spoilage_minimization": "Spoilage-minimization Strategy",
}


def _generate_dynamic_offline_block(strategy: str) -> str:
  """Generates offline candidate code block with random parameter variations."""
  p_weight = round(random.uniform(0.8, 3.5), 2)
  c_weight = round(random.uniform(0.1, 1.5), 2)
  iron_w = round(random.uniform(0.1, 1.0), 2)
  calc_w = round(random.uniform(0.005, 0.03), 4)
  vitd_w = round(random.uniform(0.5, 2.5), 2)
  div_exp = round(random.uniform(0.5, 2.5), 2)
  price_denom = round(random.uniform(0.05, 0.5), 2)
  premium_mult = round(random.uniform(0.4, 1.2), 2)

  if strategy == "macro_focused":
    return f"""
  remaining = scenario_constraints['budget'] - cart_state.get('total_cost', 0.0)
  if item['price'] > remaining:
    return -1.0

  protein_eff = (item.get('protein_g', 0.0) * {p_weight}) / max(item['price'], {price_denom})
  micros = (item.get('iron_mg', 0.0) * {iron_w} + item.get('calcium_mg', 0.0) * {calc_w} + item.get('vitamin_d_mcg', 0.0) * {vitd_w}) / max(item['price'], {price_denom})

  if not item.get('is_premium', False):
    protein_eff *= {premium_mult}

  cat_cnt = cart_state.get('category_counts', dict()).get(item['category'], 0)
  penalty = 1.0 / ((cat_cnt ** {div_exp}) + 1.0)
  return (protein_eff + micros) * penalty
"""
  elif strategy == "variety_focused":
    bonus_unseen = round(random.uniform(1.5, 5.0), 2)
    return f"""
  remaining = scenario_constraints['budget'] - cart_state.get('total_cost', 0.0)
  if item['price'] > remaining:
    return -1.0

  cat_cnt = cart_state.get('category_counts', dict()).get(item['category'], 0)
  diversity_score = 50.0 / ((cat_cnt ** {div_exp}) + 1.0)
  if cat_cnt == 0:
    diversity_score *= {bonus_unseen}

  nutrition = (item.get('protein_g', 0.0) * {p_weight} + item.get('fiber_g', 0.0) * {c_weight}) / max(item['price'], {price_denom})
  return nutrition + diversity_score
"""
  elif strategy == "budget_pacing":
    threshold_pct = round(random.uniform(0.3, 0.7), 2)
    return f"""
  remaining = scenario_constraints['budget'] - cart_state.get('total_cost', 0.0)
  if item['price'] > remaining:
    return -1.0

  budget_pct = remaining / max(scenario_constraints['budget'], 1.0)
  if budget_pct > {threshold_pct}:
    val = (item.get('protein_g', 0.0) * {p_weight} + item.get('fiber_g', 0.0) * 1.2) / max(item['price'], {price_denom})
  else:
    val = (item.get('protein_g', 0.0) + item.get('carbs_g', 0.0) * {c_weight}) / max(item['price'], {price_denom})

  if not item.get('is_premium', False):
    val *= 1.3

  cat_cnt = cart_state.get('category_counts', dict()).get(item['category'], 0)
  return val / ((cat_cnt ** {div_exp}) + 1.0)
"""
  else:  # spoilage_minimization
    sodium_limit = round(random.uniform(300.0, 800.0), 1)
    return f"""
  remaining = scenario_constraints['budget'] - cart_state.get('total_cost', 0.0)
  if item['price'] > remaining:
    return -1.0

  shelf_life = item.get('shelf_life_days', 7)
  if shelf_life < scenario_constraints.get('min_shelf_life_days', 3):
    return -1.0

  prep_time = item.get('prep_time_mins', 0)
  max_prep = scenario_constraints.get('max_prep_time_mins', 30)
  prep_penalty = 1.0 if prep_time <= max_prep else 0.3

  sodium = item.get('sodium_mg', 0.0)
  sodium_penalty = 1.0 if sodium <= {sodium_limit} else 0.4

  val = (item.get('protein_g', 0.0) * {p_weight} + item.get('calcium_mg', 0.0) * {calc_w}) / max(item['price'], {price_denom})
  cat_cnt = cart_state.get('category_counts', dict()).get(item['category'], 0)
  return (val * prep_penalty * sodium_penalty) / ((cat_cnt ** {div_exp}) + 1.0)
"""


def _mutate_via_live_gemini(
    current_block: str, parent_blocks: List[str], strategy: str
) -> Optional[str]:
  """Attempt mutation using live Gemini 2.5 API if key & client are available."""
  api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
  if not api_key:
    return None

  try:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""You are an AlphaEvolve LLM Mutator optimizing a grocery item scoring function.
Focus Strategy: {strategy}

Parent EVOLVE-BLOCK Code Snippets:
{chr(10).join(parent_blocks)}

Current EVOLVE-BLOCK Code:
{current_block}

Requirements:
- Output ONLY valid Python code to replace inside # EVOLVE-BLOCK START and # EVOLVE-BLOCK END.
- Must evaluate 'item', 'cart_state', and 'scenario_constraints' dicts.
- Return a single float score. Return -1.0 if item cannot be afforded.
- Keep cyclomatic complexity M <= 10. No imports or forbidden builtins.
- Do NOT include markdown formatting or extra commentary. Output pure code lines only.
"""
    response = model.generate_content(prompt)
    mutated_code = response.text.replace("```python", "").replace("```", "").strip()
    return mutated_code
  except Exception:
    return None


def mutate_program(
    full_code: str,
    parent_programs: Optional[List[Dict[str, str]]] = None,
    strategy: Optional[str] = None,
    use_live_api: bool = False,
) -> str:
  """Mutates EVOLVE-BLOCK using Live Gemini API or Multi-Objective Offline Fallback Strategies."""
  current_block = extract_evolve_block(full_code)

  if strategy is None:
    strategy = random.choice(list(OFFLINE_STRATEGY_BLOCKS.keys()))

  parent_blocks = []
  if parent_programs:
    for p in parent_programs:
      try:
        parent_blocks.append(extract_evolve_block(p["code"]))
      except Exception:
        pass

  new_block = None
  if use_live_api:
    new_block = _mutate_via_live_gemini(current_block, parent_blocks, strategy)

  if not new_block:
    new_block = _generate_dynamic_offline_block(strategy)

  return replace_evolve_block(full_code, new_block)
