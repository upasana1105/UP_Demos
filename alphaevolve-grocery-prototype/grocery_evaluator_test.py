"""Unit tests for AlphaEvolve grocery evaluator and seed program baseline."""

import unittest
from grocery_ast_validator import validate_code_ast
from grocery_dataset import DEFAULT_SCENARIO, GROCERY_CATALOG

from grocery_evaluator import assemble_cart, calculate_fitness, evaluate_code_string
from grocery_seed_program import score_grocery_item


class GroceryEvaluatorTest(unittest.TestCase):

  def test_catalog_has_items(self):
    self.assertGreaterEqual(len(GROCERY_CATALOG), 25)

  def test_seed_program_execution(self):
    cart = assemble_cart(score_grocery_item, GROCERY_CATALOG, DEFAULT_SCENARIO.budget)
    self.assertGreater(len(cart), 0)
    fitness_res = calculate_fitness(cart, DEFAULT_SCENARIO)
    self.assertGreater(fitness_res["fitness"], 0.0)
    self.assertLessEqual(fitness_res["total_cost"], DEFAULT_SCENARIO.budget)

  def test_evaluate_code_string(self):
    code_str = """
def score_grocery_item(price, nutrition_score, category, current_budget_left, category_counts):
    if price > current_budget_left:
        return -1.0
    return nutrition_score * 2.0
"""
    result = evaluate_code_string(code_str)
    self.assertIsNone(result["error"])
    self.assertGreater(result["fitness"], 0.0)

  def test_overbudget_disqualification(self):
    # Artificially created oversized cart
    cart = GROCERY_CATALOG  # Total cost > $100
    res = calculate_fitness(cart, DEFAULT_SCENARIO)
    self.assertEqual(res["fitness"], 0.0)

  def test_ast_validation_valid(self):
    code = "def score_grocery_item(price, nutrition_score, category, current_budget_left, category_counts):\n    return 1.0"
    valid, msg = validate_code_ast(code)
    self.assertTrue(valid)

  def test_ast_validation_forbidden_import(self):
    code = "import os\ndef score_grocery_item(price, nutrition_score, category, current_budget_left, category_counts):\n    return 1.0"
    valid, msg = validate_code_ast(code)
    self.assertFalse(valid)
    self.assertIn("Forbidden import", msg)



if __name__ == "__main__":
  unittest.main()
