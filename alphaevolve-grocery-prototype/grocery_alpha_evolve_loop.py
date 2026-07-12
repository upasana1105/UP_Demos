"""AlphaEvolve local evolutionary loop runner for Grocery Planner prototype.

Demonstrates AST safety validation, live LLM API mutation/crossover, and generational fitness lift.
"""

import inspect
import time
from grocery_ast_validator import validate_code_ast
from grocery_dataset import DEFAULT_SCENARIO, GROCERY_CATALOG
from grocery_evaluator import assemble_cart, calculate_fitness, evaluate_code_string
from grocery_llm_mutator import LLMMutator
from grocery_seed_program import score_grocery_item


class ProgramIndividual:
  """Represents a candidate program in the AlphaEvolve evolutionary database."""

  def __init__(
      self,
      code_str: str,
      generation: int = 0,
      name: str = "Candidate",
      mutation_mode: str = "Baseline",
  ):
    self.code_str = code_str
    self.generation = generation
    self.name = name
    self.mutation_mode = mutation_mode

    # 1. AST Safety & Guardrails Verification
    self.ast_valid, self.ast_msg = validate_code_ast(code_str)

    # 2. Evaluation
    if self.ast_valid:
      self.eval_result: dict[str, float] = evaluate_code_string(code_str)
      self.fitness: float = self.eval_result.get("fitness", 0.0)
    else:
      self.eval_result = {"fitness": 0.0, "error": self.ast_msg}
      self.fitness = 0.0

  def __repr__(self) -> str:
    return (
        f"<{self.name} Mode={self.mutation_mode} AST={self.ast_valid} "
        f"Fitness={self.fitness:.2f} Cost=${self.eval_result.get('total_cost', 0):.2f}>"
    )


def run_alpha_evolve_experiment(
    generations: int = 4, population_size: int = 3, use_live_api: bool = False
):
  """Runs the sophisticated AlphaEvolve evolutionary optimization loop."""
  print("\n=======================================================")
  print("   ALPHAEVOLVE PROTOTYPE: Grocery Planner Engine")
  print("=======================================================")
  print(f"Scenario: {DEFAULT_SCENARIO.name}")
  print(f"Budget Cap: ${DEFAULT_SCENARIO.budget:.2f}")
  print(f"Catalog Size: {len(GROCERY_CATALOG)} items")
  print("-------------------------------------------------------\n")

  mutator = LLMMutator(use_live_api=use_live_api)

  # Step 1: Baseline Seed Initialization
  seed_code = inspect.getsource(score_grocery_item)
  baseline_ind = ProgramIndividual(
      seed_code, generation=0, name="Baseline Seed", mutation_mode="Baseline"
  )

  print("[GEN 0] Initializing Seed Program Baseline:")
  print(f"  -> {baseline_ind}")
  print(f"  -> AST Validation: {baseline_ind.ast_msg}")
  print(f"  -> Cart Items Selected: {baseline_ind.eval_result['items_count']}")
  print(
      f"  -> Total Nutrition: {baseline_ind.eval_result['total_nutrition']}"
  )
  print(
      f"  -> Diversity Bonus: {baseline_ind.eval_result['diversity_bonus']}\n"
  )

  population: list[ProgramIndividual] = [baseline_ind]
  best_ever: ProgramIndividual = baseline_ind

  # Step 2: Generational Loop
  for gen in range(1, generations + 1):
    print(
        f"--- [GENERATION {gen}] Evolving Candidates via AST Guardrails &"
        " LLM ---"
    )
    time.sleep(0.2)

    # Perform Crossover every 2nd generation if population has >= 2 candidates
    if gen % 2 == 0 and len(population) >= 2:
      parent_a = population[0]
      parent_b = population[1]
      candidate_code, mode_label = mutator.crossover_two_parents(
          parent_a.code_str, parent_b.code_str, gen
      )
    else:
      parent = max(population, key=lambda ind: ind.fitness)
      candidate_code, mode_label = mutator.mutate_single_parent(
          parent.code_str, parent.fitness, gen
      )

    # Instantiate and evaluate
    candidate_ind = ProgramIndividual(
        candidate_code,
        generation=gen,
        name=f"Evolved_Variant_G{gen}",
        mutation_mode=mode_label,
    )

    print(f"  Mutation Mode:  {candidate_ind.mutation_mode}")
    print(f"  AST Safety:     {candidate_ind.ast_msg}")
    print(f"  Evaluated Score: {candidate_ind}")

    # Add to database
    if candidate_ind.ast_valid:
      population.append(candidate_ind)
      population.sort(key=lambda ind: ind.fitness, reverse=True)
      population = population[:population_size]

      if candidate_ind.fitness > best_ever.fitness:
        best_ever = candidate_ind
        print(
            "  *** NEW SOTA HEURISTIC DISCOVERED! Fitness:"
            f" {best_ever.fitness:.2f} ***"
        )

    print()

  # Step 3: Summary
  print("=======================================================")
  print("               ALPHAEVOLVE SUMMARY RESULTS")
  print("=======================================================")
  print(f"Initial Baseline Fitness: {baseline_ind.fitness:.2f}")
  print(f"Best Discovered Fitness:   {best_ever.fitness:.2f}")
  lift = (
      ((best_ever.fitness - baseline_ind.fitness) / baseline_ind.fitness) * 100
  )
  print(f"Overall Fitness Lift:      +{lift:.1f}%\n")

  return baseline_ind, best_ever


if __name__ == "__main__":
  run_alpha_evolve_experiment(generations=4, population_size=3)
