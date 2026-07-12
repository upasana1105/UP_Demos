"""AST Static Code Sanitizer & Guardrails for AlphaEvolve Grocery Prototype.

Statically validates LLM-generated Python code before compilation and execution.
"""

import ast
from typing import Tuple

FORBIDDEN_BUILTINS = {
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "globals",
    "locals",
    "getattr",
    "setattr",
    "delattr",
}
FORBIDDEN_MODULES = {"os", "sys", "subprocess", "shutil", "requests", "urllib"}


def validate_code_ast(code_str: str) -> Tuple[bool, str]:
  """Statically inspects candidate Python code AST for safety and compliance.

  Returns:
    Tuple of (is_valid: bool, status_message: str)
  """
  try:
    tree = ast.parse(code_str)
  except SyntaxError as e:
    return False, f"Syntax Error: {e}"

  has_target_func = False
  for node in ast.walk(tree):
    # Check for forbidden module imports
    if isinstance(node, ast.Import):
      for alias in node.names:
        if alias.name in FORBIDDEN_MODULES:
          return False, f"Forbidden import module: {alias.name}"

    if isinstance(node, ast.ImportFrom):
      if node.module in FORBIDDEN_MODULES:
        return False, f"Forbidden import from module: {node.module}"

    # Check for forbidden builtin calls
    if isinstance(node, ast.Call):
      if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_BUILTINS:
        return False, f"Forbidden builtin function call: {node.func.id}"

    # Validate function definition
    if isinstance(node, ast.FunctionDef):
      if node.name == "score_grocery_item":
        has_target_func = True
        arg_names = [arg.arg for arg in node.args.args]
        expected_args = [
            "price",
            "nutrition_score",
            "category",
            "current_budget_left",
            "category_counts",
        ]
        if arg_names != expected_args:
          return (
              False,
              f"Function args mismatch: expected {expected_args}, got"
              f" {arg_names}",
          )

  if not has_target_func:
    return False, "Missing required function 'score_grocery_item'"

  return True, "AST Validation Passed (Safe)"
