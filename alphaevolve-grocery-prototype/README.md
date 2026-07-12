# 🧬 AlphaEvolve Grocery Prototype (Autonomous Algorithm Discovery)

This directory contains a complete, self-contained implementation of **DeepMind's AlphaEvolve** agent architecture applied to an everyday real-world optimization problem: **Weekly Grocery Shopping under a $45 budget cap**.

AlphaEvolve represents a paradigm shift in AI: moving from static prompt autocomplete to **closed-loop evolutionary algorithm discovery**, where Gemini code generation is paired with continuous evaluation feedback to discover superior heuristic algorithms automatically.

---

## 🛒 The Problem & Objective
Given 30 catalog items across 6 categories (Produce, Protein, Grains, Dairy, Snacks), assemble a shopping cart that maximizes:
1. **Total Nutritional Density** (Vitamins, Protein, Fiber).
2. **Category Balance & Variety** (Representation across all 6 food groups).
3. **Budget Efficiency** (Spending as close to $45 as possible without overshooting).

> **Hard Constraint**: If total cart cost exceeds $45.00, the evaluator assigns a hard fitness score of `0.0`.

---

## 🏛️ System Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          ❓ Human Defines "What?"                         │
│  Sets Evaluation Criteria (grocery_dataset.py & calculate_fitness)        │
│  Provides Initial Seed Solution (grocery_seed_program.py)                │
└───────────────────────────────────────────────────────────────────────────┘
                                   │  ▲
       Problem Definition ($45 Cap)│  │ Improved Solution (+45.1% Lift)
                                   ▼  │
┌───────────────────────────────────────────────────────────────────────────┐
│                     🤖 AlphaEvolve Figures Out "How?"                     │
│                                                                           │
│   ┌───────────────────────────┐         ┌──────────────────────────────┐  │
│   │   💻 Prompt Sampler       │ ──────► │  🧠 LLM Ensemble (Gemini)    │  │
│   │ (Extracts Top Parent Context)       │(AST Mutations & Crossovers)  │  │
│   └─────────────▲─────────────┘         └──────────────┬───────────────┘  │
│                 │                                      │                  │
│                 │                                      ▼                  │
│   ┌─────────────┴─────────────┐         ┌──────────────┴───────────────┐  │
│   │  🗄️ Program Database      │ ◄────── │  ⚡ Evaluator Pool (Referee) │  │
│   │ (Leaderboard & Variants)  │         │(Runs Cart Simulation & Cap)  │  │
│   └───────────────────────────┘         └──────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure & Component Breakdown

- **`grocery_dataset.py`**: Catalog of 30 grocery items across 6 categories + `ShoppingScenario` budget settings ($45 cap).
- **`grocery_seed_program.py`**: Initial naive baseline heuristic function `score_grocery_item()` (Initial Fitness: `124.35 pts`).
- **`grocery_evaluator.py`**: Simulation referee (`assemble_cart()` & `calculate_fitness()`).
- **`grocery_ast_validator.py`**: Static AST code sanitizer (`ast.parse()`) enforcing function parameter rules and blocking unsafe imports (`os`, `sys`, `exec`).
- **`grocery_llm_mutator.py`**: Live Gemini API mutator (`google-genai` / `gemini-2.5-flash`) supporting single-parent targeted refinement, two-parent crossover synthesis, and offline fallback strategies.
- **`grocery_alpha_evolve_loop.py`**: Closed-loop evolutionary engine managing candidate population, generational search, and score tracking.
- **`grocery_evaluator_test.py`**: Comprehensive unit test harness for catalog integrity, evaluator rules, and AST security checks.
- **`run_prototype.py`**: Unified entry point script that runs unit tests, launches the experiment, and exports visual reports.

---

## 📈 Benchmark Results & Fitness Lift

- **Baseline Seed Fitness (Gen 0)**: `124.35 pts`
- **Discovered SOTA Fitness (Gen 4)**: `180.47 pts`
- **Overall Fitness Lift**: **`+45.1%`**

### Discovered SOTA Algorithm:
```python
def score_grocery_item(
    price: float,
    nutrition_score: float,
    category: str,
    current_budget_left: float,
    category_counts: dict[str, int],
) -> float:
  if price > current_budget_left:
    return -1.0

  # Category scarcity multiplier
  count = category_counts.get(category, 0)
  category_multiplier = 2.4 / (count + 1.0)

  # Non-linear nutrition density weighting
  efficiency = (nutrition_score**1.5) / max(price, 0.2)

  return efficiency * category_multiplier
```

---

## 🚀 Quick Start Guide

### 1. Run Unit Tests:
```bash
python3 grocery_evaluator_test.py
```

### 2. Launch the Evolutionary Search Engine:
```bash
python3 run_prototype.py
```

### 3. View Visual Outcome Reports & Carousel Media Assets:
Open `grocery_results_report.html`, `alphaevolve_architecture_diagram.html`, or `linkedin_media_bundle.html` in your web browser or preview window.
