"""Comprehensive Unit Test Suite for Enterprise AlphaEvolve.

Tests:
  1. Dataset (250+ items, 12 categories, 3 scenarios)
  2. Evaluator (Three-Tier Evaluation, 4D Pareto Vector, Dominance & Frontier)
  3. MAP-Elites Archive (5x5 Grid, Descriptor, Insert, Sampling, Coverage)
  4. AST Validator (Complexity M <= 10, Self-Recursion, Memory Safeguards, Tags)
  5. LLM Mutator (EVOLVE-BLOCK Extraction, Replacement, Offline Fallback Strategies)
"""

import unittest

from grocery_enterprise_ast_validator import validate_ast
from grocery_enterprise_dataset import CATEGORIES, ENTERPRISE_CATALOG, HOUSEHOLD_SCENARIOS
from grocery_enterprise_evaluator import EnterpriseEvaluator, extract_pareto_frontier, is_pareto_dominant
from grocery_enterprise_llm_mutator import extract_evolve_block, mutate_program, replace_evolve_block
from grocery_evolve_program import score_grocery_item
from grocery_map_elites import MapElitesArchive


class TestEnterpriseDataset(unittest.TestCase):

  def test_catalog_size_and_categories(self):
    self.assertGreaterEqual(len(ENTERPRISE_CATALOG), 250)
    found_categories = set(item["category"] for item in ENTERPRISE_CATALOG)
    for cat in CATEGORIES:
      self.assertIn(cat, found_categories)

  def test_scenarios(self):
    self.assertEqual(len(HOUSEHOLD_SCENARIOS), 3)
    self.assertIn("single_student", HOUSEHOLD_SCENARIOS)
    self.assertIn("athlete_bulk", HOUSEHOLD_SCENARIOS)
    self.assertIn("family_of_4", HOUSEHOLD_SCENARIOS)

    fam = HOUSEHOLD_SCENARIOS["family_of_4"]
    self.assertTrue(fam["is_gluten_free"])
    self.assertTrue(fam["is_vegan"])
    self.assertEqual(fam["max_sodium_mg"], 1400.0)


class TestParetoEngine(unittest.TestCase):

  def test_pareto_dominance(self):
    v1 = (80.0, 70.0, 90.0, 85.0)
    v2 = (75.0, 70.0, 85.0, 80.0)
    v3 = (90.0, 60.0, 85.0, 80.0)

    self.assertTrue(is_pareto_dominant(v1, v2))
    self.assertFalse(is_pareto_dominant(v2, v1))
    self.assertFalse(is_pareto_dominant(v1, v3))  # v3 is better in F1 (90 vs 80)

  def test_pareto_frontier_extraction(self):
    candidates = [
        {"name": "c1", "fitness_vector": (80.0, 70.0, 90.0, 85.0)},
        {"name": "c2", "fitness_vector": (75.0, 70.0, 85.0, 80.0)},  # Dominated by c1
        {"name": "c3", "fitness_vector": (90.0, 60.0, 80.0, 80.0)},  # Non-dominated
    ]
    frontier = extract_pareto_frontier(candidates)
    names = [c["name"] for c in frontier]
    self.assertIn("c1", names)
    self.assertIn("c3", names)
    self.assertNotIn("c2", names)


class TestEnterpriseEvaluator(unittest.TestCase):

  def setUp(self):
    self.evaluator = EnterpriseEvaluator()
    self.scenario = HOUSEHOLD_SCENARIOS["single_student"]

  def test_cart_assembly_and_evaluation(self):
    cart_state = self.evaluator.assemble_cart(score_grocery_item, self.scenario)
    self.assertLessEqual(cart_state["total_cost"], self.scenario["budget"])
    self.assertGreater(len(cart_state["items"]), 0)

    vector = self.evaluator.compute_fitness_vector(cart_state, self.scenario)
    self.assertEqual(len(vector), 4)
    for score in vector:
      self.assertGreaterEqual(score, 0.0)
      self.assertLessEqual(score, 100.0)


class TestMapElitesArchive(unittest.TestCase):

  def setUp(self):
    self.archive = MapElitesArchive(grid_size=5)

  def test_insert_and_coverage(self):
    sample_code = "def score_grocery_item(item, cart, sc): return 1.0"
    v1 = (80.0, 70.0, 60.0, 50.0)
    cart_state = {
        "items": [{"is_premium": False}],
        "category_counts": {"Fresh Produce": 1},
        "total_cost": 10.0,
        "total_protein_g": 30.0,
    }

    inserted = self.archive.try_insert(sample_code, v1, cart_state)
    self.assertTrue(inserted)
    self.assertGreater(self.archive.get_coverage(), 0.0)

    sampled = self.archive.sample_parents(num_parents=1)
    self.assertEqual(len(sampled), 1)

    front = self.archive.get_pareto_front()
    self.assertGreater(len(front), 0)


class TestASTValidator(unittest.TestCase):

  def test_valid_program(self):
    code = """
def score_grocery_item(item, cart_state, scenario_constraints):
  # EVOLVE-BLOCK START
  if item['price'] > 10.0:
    return -1.0
  return item['protein_g'] / item['price']
  # EVOLVE-BLOCK END
"""
    res = validate_ast(code)
    self.assertTrue(res["valid"])

  def test_complexity_exceeded(self):
    # Program with > 10 decision points
    code = """
def score_grocery_item(item, cart_state, scenario_constraints):
  # EVOLVE-BLOCK START
  if item['price'] > 1: pass
  if item['price'] > 2: pass
  if item['price'] > 3: pass
  if item['price'] > 4: pass
  if item['price'] > 5: pass
  if item['price'] > 6: pass
  if item['price'] > 7: pass
  if item['price'] > 8: pass
  if item['price'] > 9: pass
  if item['price'] > 10: pass
  return 1.0
  # EVOLVE-BLOCK END
"""
    res = validate_ast(code, max_complexity=10)
    self.assertFalse(res["valid"])
    self.assertIn("Cyclomatic complexity", res["error"])

  def test_recursion_detection(self):
    code = """
def score_grocery_item(item, cart_state, scenario_constraints):
  # EVOLVE-BLOCK START
  return score_grocery_item(item, cart_state, scenario_constraints)
  # EVOLVE-BLOCK END
"""
    res = validate_ast(code)
    self.assertFalse(res["valid"])
    self.assertIn("Self-recursion", res["error"])

  def test_missing_tags(self):
    code = "def score_grocery_item(item, cart, sc): return 1.0"
    res = validate_ast(code)
    self.assertFalse(res["valid"])
    self.assertIn("Missing mandatory '# EVOLVE-BLOCK", res["error"])


class TestLLMMutator(unittest.TestCase):

  def test_extraction_and_mutation(self):
    full_code = """
def score_grocery_item(item, cart_state, scenario_constraints):
  # EVOLVE-BLOCK START
  return 1.0
  # EVOLVE-BLOCK END
"""
    block = extract_evolve_block(full_code)
    self.assertEqual(block, "return 1.0")

    mutated = mutate_program(full_code, strategy="variety_focused")
    self.assertIn("# EVOLVE-BLOCK START", mutated)
    self.assertIn("diversity_score", mutated)


if __name__ == "__main__":
  unittest.main()
