"""Verification test script for Phase 1 - Phase 4 AlphaEvolve deliverables."""

import grocery_enterprise_dataset as ds
import grocery_evolve_program as ep
import grocery_enterprise_evaluator as ev
import grocery_enterprise_ast_validator as astv


def test_dataset():
  print("=== 1. DATASET TESTS ===")
  print("Catalog Items:", len(ds.ENTERPRISE_GROCERY_CATALOG))
  print("Categories:", len(ds.ALL_CATEGORIES))
  print("Scenarios:", list(ds.HOUSEHOLD_SCENARIOS.keys()))
  assert len(ds.ENTERPRISE_GROCERY_CATALOG) >= 250
  assert len(ds.ALL_CATEGORIES) == 12
  assert len(ds.HOUSEHOLD_SCENARIOS) >= 3
  print("Dataset tests PASSED!")


def test_evolve_program():
  print("\n=== 2. EVOLVE PROGRAM TESTS ===")
  item_sample = ds.ENTERPRISE_GROCERY_CATALOG[0].to_dict()
  cart_state_sample = {"total_cost": 0.0, "category_counts": {}}
  sc_obj = ds.HOUSEHOLD_SCENARIOS["Single Student"]
  scenario_sample = sc_obj.to_dict() if hasattr(sc_obj, "to_dict") else sc_obj
  score = ep.score_grocery_item(item_sample, cart_state_sample, scenario_sample)
  print("Sample item score:", score)
  assert isinstance(score, float)
  print("Evolve program tests PASSED!")


def test_ast_validator():
  print("\n=== 3. AST VALIDATOR TESTS ===")
  with open("grocery_evolve_program.py") as f:
    code_str = f.read()

  valid, msg = astv.validate_code_ast(code_str)
  print("Baseline code AST validation:", valid, "|", msg)
  assert valid

  # Test M > 10 failure
  complex_code = code_str.replace(
      "return protein_eff * category_penalty",
      "if item['price'] > 1: pass\n  if item['price'] > 2: pass\n  if item['price'] > 3: pass\n  if item['price'] > 4: pass\n  if item['price'] > 5: pass\n  if item['price'] > 6: pass\n  if item['price'] > 7: pass\n  if item['price'] > 8: pass\n  if item['price'] > 9: pass\n  if item['price'] > 10: pass\n  return 1.0",
  )
  valid_c, msg_c = astv.validate_code_ast(complex_code)
  print("Complex code AST validation (M > 10):", valid_c, "|", msg_c)
  assert not valid_c and "Cyclomatic complexity" in msg_c

  # Test self-recursion failure
  recursive_code = code_str.replace(
      "return protein_eff * category_penalty",
      "return score_grocery_item(item, cart_state, scenario_constraints)",
  )
  valid_r, msg_r = astv.validate_code_ast(recursive_code)
  print("Recursive code AST validation:", valid_r, "|", msg_r)
  assert not valid_r and "Self-recursion" in msg_r

  print("AST validator tests PASSED!")


def test_evaluator():
  print("\n=== 4. THREE-TIER EVALUATOR TESTS ===")
  with open("grocery_evolve_program.py") as f:
    code_str = f.read()

  for sc_name, sc in ds.HOUSEHOLD_SCENARIOS.items():
    res = ev.evaluate_code_string(code_str, ds.ENTERPRISE_GROCERY_CATALOG, sc)
    print(
        f"Scenario [{sc_name}]: Valid={res['valid']}, Error={res.get('error')},"
        f" FitnessVector={res['fitness_vector']}, Aggregate={res['aggregate_fitness']},"
        f" Items={res['item_count']}, Cost=${res['total_cost']}"
    )
    assert res["valid"]

  print("Evaluator tests PASSED!")


def test_pareto_engine():
  print("\n=== 5. PARETO ENGINE TESTS ===")
  v1 = (80.0, 70.0, 90.0, 60.0)
  v2 = (75.0, 65.0, 85.0, 55.0)
  v3 = (85.0, 60.0, 80.0, 50.0)
  print("v1 dominates v2:", ev.is_pareto_dominant(v1, v2))
  print("v2 dominates v1:", ev.is_pareto_dominant(v2, v1))
  assert ev.is_pareto_dominant(v1, v2)
  assert not ev.is_pareto_dominant(v2, v1)

  candidates = [
      {"name": "c1", "fitness_vector": v1},
      {"name": "c2", "fitness_vector": v2},
      {"name": "c3", "fitness_vector": v3},
  ]
  frontier = ev.extract_pareto_frontier(candidates)
  print("Pareto frontier candidates:", [c["name"] for c in frontier])
  assert len(frontier) == 2  # c1 and c3 non-dominated
  print("Pareto engine tests PASSED!")


if __name__ == "__main__":
  test_dataset()
  test_evolve_program()
  test_ast_validator()
  test_evaluator()
  test_pareto_engine()
  print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
